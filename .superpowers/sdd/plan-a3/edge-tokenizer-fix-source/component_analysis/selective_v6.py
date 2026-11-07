"""Frozen V6 readout-only honest-donor pilot. No path engine or API calls.

All metrics use the existing fp32 final-norm/unembedding readout. Native model
logits are retained separately for actual-backend identity checks.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time

from component_analysis import hooks


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def conditions(masks, split):
    keys = lambda name: tuple(('head', int(l), int(h)) for l, h in masks[name])
    panel = {'intact': ()}
    panel.update({name: keys(name) for name in ('new23', 'new30', 'oldD69', 'random30')})
    if split == 'discovery':
        for key in keys('new30'):
            panel[f'single_L{key[1]}H{key[2]}'] = (key,)
        added = sorted(set(keys('new30')) - set(keys('new23')))
        if len(keys('new30')) != 30 or len(added) != 7:
            raise ValueError('requires frozen New30 and exact seven additions')
        for key in added:
            panel[f'release_L{key[1]}H{key[2]}'] = tuple(k for k in keys('new30') if k != key)
    return panel


def last_nonpad(mask):
    import torch
    if mask.ndim != 2 or not torch.all((mask == 0) | (mask == 1)) or not torch.all(mask.bool().any(-1)):
        raise ValueError('attention mask must contain a nonpad token in each row')
    indices = torch.arange(mask.shape[1], device=mask.device).expand_as(mask)
    return indices.masked_fill(~mask.bool(), -1).max(-1).values


def final_replacements(bank, donor_mask, recipient_mask):
    """One donor row to the corresponding recipient row, own final tokens."""
    import torch
    donor_pos, recipient_pos = last_nonpad(donor_mask), last_nonpad(recipient_mask)
    if len(donor_pos) != len(recipient_pos):
        raise ValueError('donor/recipient row mismatch')
    rows = torch.arange(len(donor_pos), device=donor_pos.device)
    positions = torch.zeros_like(recipient_mask, dtype=torch.bool)
    positions[rows, recipient_pos] = True
    result = {}
    for key, value in bank.items():
        if key[0] != 'head' or value.shape[:2] != donor_mask.shape:
            raise ValueError('only donor head banks with matching token axes are allowed')
        # Broadcast only the donor's own last-token slice; the mask controls
        # writes. No donor/recipient sequence alignment is introduced.
        final = value[rows, donor_pos].unsqueeze(1)
        result[key] = hooks.Replacement(final, positions)
    return result


def metrics(logits, intact, targets, alternatives, truthful):
    import torch
    logits, intact = logits.float(), intact.float()
    if not torch.isfinite(logits).all() or not torch.isfinite(intact).all():
        raise ValueError('non-finite logits')
    rows = torch.arange(len(logits), device=logits.device)
    target = torch.as_tensor(targets, device=logits.device)
    alternate = torch.as_tensor(alternatives, device=logits.device)
    truth = torch.as_tensor(truthful, device=logits.device)
    logp, clean_logp = logits.log_softmax(-1), intact.log_softmax(-1)
    margin = logits[rows, target] - logits[rows, alternate]
    clean_margin = intact[rows, target] - intact[rows, alternate]
    kl = (clean_logp.exp() * (clean_logp - logp)).sum(-1)
    argmax = logits.argmax(-1)
    return [dict(requested_margin=float(margin[i]), intact_requested_margin=float(clean_margin[i]),
                 margin_drop=float(clean_margin[i]-margin[i]), target_probability=float(logp[i,target[i]].exp()),
                 alternate_probability=float(logp[i,alternate[i]].exp()), truthful_probability=float(logp[i,truth[i]].exp()),
                 target_logit=float(logits[i,target[i]]), alternate_logit=float(logits[i,alternate[i]]),
                 argmax_id=int(argmax[i]), requested_correct=bool(argmax[i] == target[i]),
                 truthful_correct=bool(argmax[i] == truth[i]), kl_intact_to_condition=float(kl[i]))
            for i in range(len(logits))]


def select_cases(cases, mode):
    if mode == 'discovery':
        return [c for c in cases if c['split'] == 'discovery' and c['family'] == 'sdr']
    if mode == 'validation':
        return [c for c in cases if c['split'] != 'discovery']
    if mode == 'dry-run':
        return list(cases)
    if mode != 'smoke':
        raise ValueError('unknown mode')
    selected = {}
    for c in sorted(cases, key=lambda c: (c['scenario_key'], c['case_id'])):
        if c['family'] == 'sdr' and c['split'] == 'discovery':
            cell = (c['stratum']['designation_polarity'], c['stratum']['item_polarity'])
            selected.setdefault(cell, c['scenario_key'])
    if len(selected) != 4:
        raise ValueError('smoke requires four balanced SDR discovery cells')
    return [c for c in cases if c['family'] == 'sdr' and c['split'] == 'discovery' and c['scenario_key'] in selected.values()]


def validate_receipt(receipt, manifest_hash, runner_hash, mode, code_hashes, output_dir):
    for key, expected in [('manifest_sha256',manifest_hash), ('runner_sha256',runner_hash), ('mode',mode), ('review_status','approved'), ('code_hashes',code_hashes)]:
        if receipt.get(key) != expected:
            raise ValueError(f'execution receipt mismatch: {key}')
    if Path(receipt.get('output_dir','')).resolve() != Path(output_dir).resolve():
        raise ValueError('execution receipt output directory mismatch')
    limits = {'smoke':.25, 'discovery':1.0, 'validation':.75}
    reserved = receipt.get('reserved_gpu_hours', 0)
    remaining = receipt.get('remaining_gpu_hours_before', 0)
    if (type(reserved) not in (int,float) or type(remaining) not in (int,float)
            or not math.isfinite(reserved) or not math.isfinite(remaining)
            or not 0 < remaining <= 2.9 or not 0 < reserved <= min(limits[mode], remaining)):
        raise ValueError('invalid reservation budget')
    if not receipt.get('reservation_id'):
        raise ValueError('missing reservation identity')


def claim_receipt(path, receipt_hash):
    # Exclusive create makes a receipt one-use even with concurrent invocations.
    _write_json(str(path)+'.consumed.json', dict(receipt_sha256=receipt_hash, slurm_job_id=os.environ.get('SLURM_JOB_ID')))


def identity_controls(model, ids, mask, keys):
    import torch
    pos = last_nonpad(mask)
    # Only the production baseline reaches the raw HF model; all causal
    # capture/replacement remains in the shared hooks implementation.
    with torch.no_grad():
        output = hooks._hf(model)(input_ids=ids, attention_mask=mask, use_cache=False)
        rows = torch.arange(len(ids), device=ids.device)
        plain_logits = output.logits[rows, pos].detach()
        del output
    bare = hooks.capture_forward(model, ids, mask, components=[], positions=pos)
    clean = hooks.capture_forward(model, ids, mask, components=keys, positions=pos, replacements={})
    logits = hooks.readout_logits(model, clean.residual[:, -1])
    self_bank = final_replacements(clean.outputs, mask, mask)
    identity = hooks.capture_forward(model, ids, mask, components=[], positions=pos, replacements=self_bank)
    identity_logits = hooks.readout_logits(model, identity.residual[:, -1])
    bare_logits = hooks.readout_logits(model, bare.residual[:, -1])
    proof = dict(plain_native_exact=torch.equal(plain_logits, bare.logits),
                 plain_native_max_abs=float((plain_logits.float()-bare.logits.float()).abs().max()),
                 native_noop_exact=torch.equal(bare.logits, clean.logits), native_self_exact=torch.equal(clean.logits, identity.logits),
                 fp32_noop_exact=torch.equal(bare_logits, logits), fp32_self_exact=torch.equal(logits, identity_logits),
                 native_noop_max_abs=float((bare.logits.float()-clean.logits.float()).abs().max()),
                 fp32_self_max_abs=float((logits-identity_logits).abs().max()))
    if not all(proof[k] for k in ('plain_native_exact','native_noop_exact','native_self_exact','fp32_noop_exact','fp32_self_exact')):
        raise RuntimeError(f'actual backend identity failure: {proof}')
    return clean, logits, proof


def padded(rows, pad_id, device):
    import torch
    width = max(map(len, rows))
    ids = torch.full((len(rows), width), pad_id, dtype=torch.long, device=device)
    mask = torch.zeros_like(ids)
    for i, row in enumerate(rows):
        ids[i,:len(row)] = torch.as_tensor(row, device=device)
        mask[i,:len(row)] = 1
    return ids, mask


def _write_json(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def run(args):
    from component_analysis.selective_v6_manifest import load_manifest
    process_started = time.monotonic()
    manifest = load_manifest(args.manifest, verify_sources=True)
    manifest_hash, runner_hash = sha256(args.manifest), sha256(__file__)
    cases = select_cases(manifest['cases'], args.mode)
    planned = []
    for c in cases:
        panel = conditions(manifest['masks'], c['split'])
        if args.mode == 'smoke':
            representatives = ['intact','new23','new30','oldD69','random30', next(n for n in panel if n.startswith('single_')), next(n for n in panel if n.startswith('release_'))]
            panel = {n:panel[n] for n in representatives}
        planned.append((c, panel))
    # Dry run validates all source hashes and fixed panels, with no torch,
    # nnsight, transformers model construction, CUDA allocation or API.
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=False)
    plan = dict(schema_version=1, mode=args.mode, manifest_sha256=manifest_hash, runner_sha256=runner_hash,
                source_hashes=manifest['sources'], model_identity=manifest['model_identity'], code_hashes={str(Path(p).resolve()):sha256(p) for p in (__file__, hooks.__file__, str(Path(__file__).with_name('selective_v6_manifest.py')))}, model_name=manifest['model_name'], tokenizer_id=manifest['tokenizer_id'],
                cases=len(cases), condition_rows=sum(len(p) for _,p in planned),
                case_ids=[c['case_id'] for c in cases], candidate_validation_effects=False,
                intervention='donor own final nonpad to recipient own final nonpad; o_proj input head slices',
                release_semantics='released head computes in current perturbed context; no cached-clean rescue')
    _write_json(out/'plan.json', plan)
    if args.mode == 'dry-run':
        print(json.dumps(plan, sort_keys=True))
        return
    if not args.execution_receipt:
        raise ValueError('live mode requires root reviewed --execution-receipt')
    receipt = json.loads(Path(args.execution_receipt).read_text())
    validate_receipt(receipt, manifest_hash, runner_hash, args.mode, plan['code_hashes'], out)
    import torch
    if not os.environ.get('SLURM_JOB_ID') or not torch.cuda.is_available():
        raise RuntimeError('live pretrained execution requires a Slurm GPU allocation')
    if importlib.metadata.version('nnsight') != '0.7.0':
        raise RuntimeError('pinned nnsight 0.7.0 required')
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    claim_receipt(args.execution_receipt, sha256(args.execution_receipt))
    started = time.monotonic()
    snapshot = Path(manifest['model_identity']['snapshot'])
    if not snapshot.is_absolute() or snapshot.name != manifest['model_identity']['revision'] or str(snapshot) != manifest['tokenizer_id']:
        raise ValueError('frozen model/tokenizer snapshot identity mismatch')
    for name, expected in manifest['model_identity']['files'].items():
        if sha256(snapshot/name) != expected:
            raise ValueError(f'frozen model file hash mismatch: {name}')
    integrity_seconds = time.monotonic()-started
    load_started = time.monotonic()
    model = hooks.load_analysis_model(str(snapshot), device='cuda')
    hooks._hf(model).eval()
    shape = hooks.geometry(model)
    for name in ('num_layers','num_heads','head_dim'):
        if shape[name] != manifest['geometry'][name]:
            raise ValueError(f'model geometry mismatch: {name}')
    backend = dict(description=hooks.describe(model), geometry=shape,
                   versions={n:importlib.metadata.version(n) for n in ('torch','transformers','nnsight')},
                   attention=hooks.attention_implementation(model), device=torch.cuda.get_device_name(),
                   model_config=hooks._hf(model).config.to_dict(),
                   tokenizer_id=manifest['tokenizer_id'], pad_token_id=manifest['pad_token_id'],
                   slurm_job_id=os.environ['SLURM_JOB_ID'], execution_receipt=receipt,
                   execution_receipt_sha256=sha256(args.execution_receipt))
    _write_json(out/'header.json', dict(plan, backend=backend))
    torch.cuda.synchronize()
    model_load_seconds = time.monotonic()-load_started
    scoring_started = time.monotonic()
    identity_donor_seconds = condition_seconds = 0.0
    completed = 0
    # Each batch shares the exact condition panel; never mix discovery and
    # validation. Cases retain one-to-one independently frozen donor rows.
    groups = {}
    for c,panel in planned:
        groups.setdefault(tuple(panel), []).append((c,panel))
    with (out/'rows.jsonl').open('x') as sink, (out/'controls.jsonl').open('x') as controls:
        for grouped in groups.values():
            for start in range(0, len(grouped), args.batch_size):
                batch = grouped[start:start+args.batch_size]
                cs, panel = [c for c,_ in batch], batch[0][1]
                ids, mask = padded([c['recipient_token_ids'] for c in cs], manifest['pad_token_id'], 'cuda')
                donor_ids, donor_mask = padded([c['donor_token_ids'] for c in cs], manifest['pad_token_id'], 'cuda')
                keys = sorted(set(k for selected in panel.values() for k in selected))
                torch.cuda.synchronize()
                control_started = time.monotonic()
                clean, clean_logits, proof = identity_controls(model, ids, mask, keys)
                donor = hooks.capture_forward(model, donor_ids, donor_mask, components=keys, positions=last_nonpad(donor_mask))
                replacements = final_replacements(donor.outputs, donor_mask, mask)
                controls.write(json.dumps(dict(kind='identity', case_ids=[c['case_id'] for c in cs], recipient_positions=last_nonpad(mask).tolist(), donor_positions=last_nonpad(donor_mask).tolist(), **proof))+'\n')
                controls.flush(); os.fsync(controls.fileno())
                torch.cuda.synchronize()
                identity_donor_seconds += time.monotonic()-control_started
                condition_started = time.monotonic()
                for name, selected in panel.items():
                    if not selected:
                        logits = clean_logits
                    else:
                        # In smoke capture earliest selected layer plus sibling:
                        # no upstream intervention can confound write isolation.
                        check = []
                        if args.mode == 'smoke':
                            layer = min(k[1] for k in selected)
                            check = [('head',layer,h) for h in range(shape['num_heads'])]
                        capture = hooks.capture_forward(model, ids, mask, components=check, positions=last_nonpad(mask), replacements={k:replacements[k] for k in selected})
                        if check:
                            # An extra unpatched capture only in smoke proves all
                            # nonselected slices/positions at the write site.
                            before = hooks.capture_forward(model, ids, mask, components=check, positions=last_nonpad(mask))
                            for k in check:
                                expected = hooks._write(before.outputs[k], replacements[k]) if k in selected else before.outputs[k]
                                if not torch.equal(expected, capture.outputs[k]):
                                    raise RuntimeError(f'selected-write isolation failed: {name} {k}')
                            controls.write(json.dumps(dict(kind='selected_write_isolation', case_ids=[c['case_id'] for c in cs], condition=name, checked_head_keys=check, exact=True, positions='all'))+'\n')
                            controls.flush(); os.fsync(controls.fileno())
                        logits = hooks.readout_logits(model, capture.residual[:, -1])
                    values = metrics(logits, clean_logits, [c['requested_target_id'] for c in cs], [c['alternate_answer_id'] for c in cs], [c['truthful_id'] for c in cs])
                    for c,value in zip(cs,values):
                        row = {k:c[k] for k in ('case_id','scenario_key','family','split','variant','stratum','source_id','donor_source_id','donor_scenario_key','donor_stream','provenance','requested_target_id','alternate_answer_id','truthful_id')}
                        row.update(condition=name, replaced_heads=[list(k[1:]) for k in selected], donor_token_sha256=hashlib.sha256(json.dumps(c['donor_token_ids']).encode()).hexdigest(), metrics=value,
                                   target_semantics='instructed_false' if c['variant']=='D' else 'transparent_requested' if c['variant']=='I' else 'truthful',
                                   manifest_sha256=manifest_hash, runner_sha256=runner_hash)
                        sink.write(json.dumps(row, allow_nan=False, sort_keys=True)+'\n')
                        completed += 1
                    sink.flush(); os.fsync(sink.fileno())
                torch.cuda.synchronize()
                condition_seconds += time.monotonic()-condition_started
                del clean, donor, replacements
                torch.cuda.empty_cache()
    torch.cuda.synchronize()
    _write_json(out/'completion.json', dict(completed_rows=completed, expected_rows=plan['condition_rows'], elapsed_seconds=time.monotonic()-started,
        model_integrity_seconds=integrity_seconds, model_load_seconds=model_load_seconds,
        identity_donor_seconds=identity_donor_seconds, condition_seconds=condition_seconds,
        scoring_seconds=time.monotonic()-scoring_started, total_process_seconds=time.monotonic()-process_started,
        peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(), manifest_sha256=manifest_hash, runner_sha256=runner_hash,
        candidate_validation_effects=False, validation_case_ids=[c['case_id'] for c in cases if c['split']=='validation']))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--mode', choices=['dry-run','smoke','discovery','validation'], required=True)
    parser.add_argument('--execution-receipt')
    parser.add_argument('--batch-size', type=int, default=4)
    args = parser.parse_args(argv)
    if args.batch_size < 1:
        parser.error('--batch-size must be positive')
    run(args)


if __name__ == '__main__':
    main()
