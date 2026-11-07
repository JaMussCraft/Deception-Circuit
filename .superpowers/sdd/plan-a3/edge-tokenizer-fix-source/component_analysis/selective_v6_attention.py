"""Bounded descriptive V6 attention. No head selection or causal claims.

Only last-actual-query rows survive the shared hook call. Segment annotations
are unavailable: the frozen manifest does not contain verified token spans.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time

from component_analysis import hooks
from component_analysis import selective_v6 as core


def select_cases(cases):
    """Lexicographic two scenarios per frozen discovery cell; D/H/I only."""
    eligible = [c for c in cases if c['family'] == 'sdr' and c['split'] == 'discovery']
    scenarios = {}
    seen = set()
    for case in eligible:
        if case['case_id'] in seen:
            raise ValueError('duplicate case ID')
        seen.add(case['case_id'])
        cell = (case['stratum']['designation_polarity'], case['stratum']['item_polarity'])
        entry = scenarios.setdefault(case['scenario_key'], (cell, {}))
        if cell != entry[0] or case['variant'] in entry[1]:
            raise ValueError('inconsistent scenario cell or duplicate variant')
        entry[1][case['variant']] = case
    cells = {}
    for scenario, (cell, variants) in sorted(scenarios.items()):
        if not {'D', 'H', 'I'} <= variants.keys():
            raise ValueError('each scenario requires D/H/I')
        cells.setdefault(cell, []).append(scenario)
    if len(cells) != 4 or any(len(v) < 2 for v in cells.values()):
        raise ValueError('requires four cells with at least two scenarios each')
    selected = sorted(s for values in cells.values() for s in values[:2])
    return [scenarios[s][1][v] for s in selected for v in ('D', 'H', 'I')]


@contextmanager
def eager_backend(model):
    """All eager identity controls use the same backend, restored on errors."""
    hf = hooks._hf(model)
    previous = hf.config._attn_implementation
    try:
        hf.set_attn_implementation(hooks.EAGER)
        if hf.config._attn_implementation != hooks.EAGER:
            raise RuntimeError('eager backend did not take')
        yield
    finally:
        hf.set_attn_implementation(previous)


def token_rows(weights, ids, mask, cases, *, layer, heads, tokenizer, geometry):
    """Validate and immediately serialize CPU rows, excluding masked keys."""
    import torch
    positions = core.last_nonpad(mask)
    if ids.shape != mask.shape or weights.shape != (len(cases), len(heads), 1, ids.shape[1]):
        raise ValueError('attention/token shape mismatch')
    if not (geometry['num_heads'] % geometry['num_kv_heads'] == 0 and
            geometry['heads_per_group'] == geometry['num_heads'] // geometry['num_kv_heads']):
        raise ValueError('invalid GQA geometry')
    if any(h < 0 or h >= geometry['num_heads'] for h in heads):
        raise ValueError('query head outside geometry')
    weights = weights.detach().float().cpu()
    ids, mask, positions = ids.cpu(), mask.cpu().bool(), positions.cpu()
    if not torch.isfinite(weights).all() or torch.any(weights < 0):
        raise ValueError('nonfinite or negative attention mass')
    if not torch.allclose(weights.sum(-1), torch.ones_like(weights.sum(-1)), atol=.005, rtol=0):
        raise ValueError('attention row mass must sum to one')
    if torch.any(weights.masked_select(~mask[:, None, None, :]) > 1e-6):
        raise ValueError('attention mass on masked padding')
    result = []
    for i, case in enumerate(cases):
        key_positions = torch.where(mask[i])[0].tolist()
        token_ids = ids[i, mask[i]].tolist()
        token_strings = tokenizer.convert_ids_to_tokens(token_ids)
        if len(token_strings) != len(token_ids) or any(not isinstance(t, str) for t in token_strings):
            raise ValueError('tokenizer did not supply exact token strings')
        for j, head in enumerate(heads):
            result.append(dict(case_id=case['case_id'], scenario_key=case['scenario_key'],
                               variant=case['variant'], layer=layer, head=head,
                               kv_group=head // geometry['heads_per_group'], backend='eager',
                               query_position=int(positions[i]), key_positions=key_positions,
                               token_ids=token_ids, token_strings=token_strings,
                               weights=weights[i, j, 0, mask[i]].tolist(),
                               row_mass=float(weights[i, j, 0].sum()),
                               segments=dict(status='unavailable', reason='frozen manifest has no verified token boundaries'),
                               interpretation='descriptive attention only; no causal or specificity claim'))
    return result


def backend_drift(sdpa, eager, case):
    import torch
    a, b = sdpa.float(), eager.float()
    if a.shape != b.shape or a.ndim != 2 or len(a) != 1 or not torch.isfinite(a).all() or not torch.isfinite(b).all():
        raise ValueError('invalid full vocabulary logits')
    target, other = case['requested_target_id'], case['alternate_answer_id']
    ap, bp = a.log_softmax(-1), b.log_softmax(-1)
    return dict(full_vocab_max_abs=float((a-b).abs().max()),
                full_vocab_mean_abs=float((a-b).abs().mean()),
                kl_sdpa_to_eager=float((ap.exp()*(ap-bp)).sum()),
                sdpa_requested_margin=float(a[0,target]-a[0,other]),
                eager_requested_margin=float(b[0,target]-b[0,other]),
                sdpa_argmax_id=int(a.argmax(-1)[0]), eager_argmax_id=int(b.argmax(-1)[0]),
                argmax_changed=bool(a.argmax(-1)[0] != b.argmax(-1)[0]))


def validate_receipt(receipt, plan, output_dir):
    for key in ('mode', 'manifest_sha256', 'runner_sha256', 'code_hashes', 'source_hashes', 'model_identity'):
        if receipt.get(key) != plan[key]:
            raise ValueError(f'execution receipt mismatch: {key}')
    if receipt.get('review_status') != 'approved' or Path(receipt.get('output_dir', '')).resolve() != Path(output_dir).resolve():
        raise ValueError('execution receipt review/output mismatch')
    reserved, remaining = receipt.get('reserved_gpu_hours', 0), receipt.get('remaining_gpu_hours_before', 0)
    if (type(reserved) not in (int,float) or type(remaining) not in (int,float) or
            not math.isfinite(reserved) or not math.isfinite(remaining) or
            not 0 < remaining <= 2.9 or not 0 < reserved <= min(.25, remaining)):
        raise ValueError('invalid attention reservation budget')
    if not receipt.get('reservation_id'):
        raise ValueError('missing reservation identity')


def run(args):
    from component_analysis import selective_v6_manifest as manifest_module
    started = time.monotonic()
    manifest = manifest_module.load_manifest(args.manifest, verify_sources=True)
    cases = select_cases(manifest['cases'])
    heads = sorted(tuple(pair) for pair in manifest['masks']['new30'])
    if len(heads) != 30 or len(set(heads)) != 30:
        raise ValueError('requires all 30 unique frozen heads')
    dependencies = (__file__, core.__file__, hooks.__file__, manifest_module.__file__)
    plan = dict(schema_version=1, mode=args.mode, manifest_sha256=core.sha256(args.manifest),
                runner_sha256=core.sha256(__file__),
                code_hashes={str(Path(p).resolve()): core.sha256(p) for p in dependencies},
                source_hashes=manifest['sources'], model_identity=manifest['model_identity'],
                case_ids=[c['case_id'] for c in cases], cases=len(cases), scenarios=8,
                heads=heads, attention_rows=len(cases)*len(heads),
                selection='lexicographic two SDR discovery scenarios per cell; D/H/I only',
                query='own last actual prompt token', segments='unavailable: no verified boundaries',
                interpretation='descriptive only; no causal claims, candidate selection, or targeted paths')
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=False)
    core._write_json(out/'plan.json', plan)
    if args.mode == 'dry-run':
        print(json.dumps(plan, sort_keys=True))
        return
    if not args.execution_receipt:
        raise ValueError('live attention requires root reviewed execution receipt')
    receipt = json.loads(Path(args.execution_receipt).read_text())
    validate_receipt(receipt, plan, out)
    import torch
    if not os.environ.get('SLURM_JOB_ID') or not torch.cuda.is_available():
        raise RuntimeError('live pretrained execution requires Slurm GPU allocation')
    if importlib.metadata.version('nnsight') != '0.7.0':
        raise RuntimeError('pinned nnsight 0.7.0 required')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    core.claim_receipt(args.execution_receipt, core.sha256(args.execution_receipt))
    snapshot = Path(manifest['model_identity']['snapshot'])
    if not snapshot.is_absolute() or snapshot.name != manifest['model_identity']['revision'] or str(snapshot) != manifest['tokenizer_id']:
        raise ValueError('frozen model/tokenizer snapshot identity mismatch')
    for name, expected in manifest['model_identity']['files'].items():
        if core.sha256(snapshot/name) != expected:
            raise ValueError(f'frozen model file hash mismatch: {name}')
    model = hooks.load_analysis_model(str(snapshot), device='cuda')
    hooks._hf(model).eval()
    geometry = hooks.geometry(model)
    for name in ('num_layers', 'num_heads', 'head_dim'):
        if geometry[name] != manifest['geometry'][name]:
            raise ValueError(f'model geometry mismatch: {name}')
    if hooks.attention_implementation(model) != hooks.SDPA:
        raise ValueError('requires production SDPA initial backend')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(snapshot), local_files_only=True)
    header = dict(plan, geometry=geometry, device=torch.cuda.get_device_name(),
                  versions={n:importlib.metadata.version(n) for n in ('torch','transformers','nnsight')},
                  execution_receipt=receipt, execution_receipt_sha256=core.sha256(args.execution_receipt),
                  description=hooks.describe(model), model_config=hooks._hf(model).config.to_dict(),
                  tokenizer_id=manifest['tokenizer_id'], pad_token_id=manifest['pad_token_id'],
                  production_backend=hooks.attention_implementation(model),
                  slurm_job_id=os.environ['SLURM_JOB_ID'], backend='eager rows; separately controlled SDPA baseline')
    core._write_json(out/'header.json', header)
    layers = {}
    for layer, head in heads:
        if not 0 <= layer < geometry['num_layers']:
            raise ValueError('layer outside geometry')
        layers.setdefault(layer, []).append(head)
    keys = [('head', layer, head) for layer, head in heads]
    completed = 0
    with (out/'rows.jsonl').open('x') as sink, (out/'controls.jsonl').open('x') as controls:
        for case in cases:
            ids, mask = core.padded([case['recipient_token_ids']], manifest['pad_token_id'], 'cuda')
            sdpa_capture, sdpa, sdpa_proof = core.identity_controls(model, ids, mask, keys)
            sdpa_native = sdpa_capture.logits.detach().float().cpu()
            sdpa = sdpa.detach().cpu()
            del sdpa_capture
            with eager_backend(model):
                eager_capture, eager, eager_proof = core.identity_controls(model, ids, mask, keys)
                eager_native = eager_capture.logits.detach().float().cpu()
                eager = eager.detach().cpu()
                del eager_capture
            control = dict(case_id=case['case_id'], sdpa_identity=sdpa_proof, eager_identity=eager_proof,
                           fp32_drift=backend_drift(sdpa, eager, case),
                           native_drift=backend_drift(sdpa_native, eager_native, case))
            controls.write(json.dumps(control, allow_nan=False)+'\n')
            controls.flush()
            # Keep CPU full-vocabulary baselines, not full attention matrices.
            with (out/f"baseline-{completed:02d}.pt").open('xb') as f:
                torch.save(dict(case_id=case['case_id'], sdpa_fp32=sdpa, eager_fp32=eager,
                                sdpa_native=sdpa_native, eager_native=eager_native), f)
            for layer, selected_heads in layers.items():
                weights = hooks.attention_weights(model, ids, mask, layer=layer, heads=selected_heads,
                                                  query_positions=core.last_nonpad(mask)[:,None])
                # Shared hook has discarded its full matrix; detach final rows
                # onto CPU before validation/serialization and the next pass.
                weights = weights.detach().cpu()
                rows = token_rows(weights, ids, mask, [case], layer=layer, heads=selected_heads,
                                  tokenizer=tokenizer, geometry=geometry)
                del weights
                for row in rows:
                    sink.write(json.dumps(row, allow_nan=False)+'\n')
                sink.flush()
                if hooks.attention_implementation(model) != hooks.SDPA:
                    raise RuntimeError('attention backend was not restored')
            completed += 1
            os.fsync(sink.fileno())
            os.fsync(controls.fileno())
    torch.cuda.synchronize()
    core._write_json(out/'complete.json', dict(cases=completed, attention_rows=completed*30,
                     elapsed_seconds=time.monotonic()-started,
                     max_memory_allocated_bytes=torch.cuda.max_memory_allocated(),
                     restored_backend=hooks.attention_implementation(model)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--mode', choices=('dry-run', 'attention'), default='dry-run')
    parser.add_argument('--execution-receipt')
    run(parser.parse_args(argv))


if __name__ == '__main__':
    main()
