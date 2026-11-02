#!/usr/bin/env python
"""Slurm-only, calibration-only shape diagnostic; never scores candidate cells.

Pass the production score CLI unchanged, plus --result-dir, --job-stdout and
--job-stderr. --dry-run validates frozen parents/tokenization, prints the ordered
pair inventory and source hashes, writes nothing and loads no model weights.
Real runs preserve incremental finite JSON evidence even when calibration fails.
"""
from __future__ import annotations
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
COMMIT = '0253f494af007f93b2a00cb1e63cb3cdf1a8b519'
ATOL = RTOL = 1e-5


def pair_inventory(args, prepared):
    """Mirror score/calibrate/positive_control order and singleton geometry."""
    from component_analysis import ladder_pipeline as p, specificity_ladder as r
    for task in args.tasks:
        frozen = prepared['designs'][task]
        ids = frozen['assessment_ids'][:args.limit]
        source = prepared['rows'][task]
        recipients = [b for c in p.design.CONDITIONS for stream in p.design.STREAMS
                      for b in p.batches([x for x in source[c] if x['instance_id'] in ids],
                                         stream, batch_size=args.batch_size)]
        donor_batches = [b for c in p.design.CONDITIONS for stream in p.design.STREAMS
                         for b in p.batches(source[c], stream, batch_size=args.batch_size)]
        donors = {(one.condition, one.ids[0], one.stream): one
                  for b in donor_batches for one in r._rows(b)}
        maps = {}
        for m in frozen['donors']:
            if m['recipient_id'] not in ids or m['operation'] != 'item_swap':
                continue
            row = next(x for x in source[m['recipient_condition']] if x['instance_id'] == m['recipient_id'])
            m = dict(m, supported=True,
                     recipient_positions=[row['streams'][m['recipient_stream']]['readout']],
                     donor_positions=[row['streams'][m['donor_stream']]['readout']])
            maps[(m['recipient_condition'], m['recipient_id'], m['recipient_stream'])] = m
        for b in recipients:
            r.validate_batch(b)
            for one in r._rows(b):
                m = maps[(one.condition, one.ids[0], one.stream)]
                donor = donors[(m['donor_condition'], m['donor_id'], m['donor_stream'])]
                r.validate_batch(donor)
                if m['recipient_positions'] != one.readout.tolist() or m['donor_positions'] != donor.readout.tolist():
                    raise ValueError('non-readout calibration map')
                yield task, one, donor, m


def geometry(batch):
    return dict(task=batch.task, condition=batch.condition, instance_id=batch.ids[0],
                stream=batch.stream, padded_width=int(batch.input_ids.shape[1]),
                unpadded_width=int(batch.attention_mask.sum()), readout=batch.readout.tolist(),
                input_ids=batch.input_ids.tolist(), attention_mask=batch.attention_mask.tolist())


def resize(batch, width):
    """Right pad or strip masked suffix only; preserve absolute token positions."""
    import torch
    from component_analysis.specificity_ladder import validate_batch
    validate_batch(batch)
    used = int(batch.attention_mask.sum())
    if width < used:
        raise ValueError('refusing truncation of unmasked tokens')
    old = batch.input_ids.shape[1]
    if width <= old:
        ids, mask = batch.input_ids[:, :width].clone(), batch.attention_mask[:, :width].clone()
    else:
        ids = torch.nn.functional.pad(batch.input_ids, (0, width-old), value=0)
        mask = torch.nn.functional.pad(batch.attention_mask, (0, width-old), value=0)
    out = dataclasses.replace(batch, input_ids=ids, attention_mask=mask)
    validate_batch(out)
    assert torch.equal(out.input_ids[:, :used], batch.input_ids[:, :used])
    assert torch.equal(out.readout, batch.readout)
    return out


def comparison(actual, expected):
    import torch
    a, b = actual.detach().float(), expected.detach().float()
    finite = bool(torch.isfinite(a).all() and torch.isfinite(b).all())
    # Do not emit NaN/Inf into evidence; preserve finite subset and counts.
    delta = (a-b).abs()
    finite_delta = delta[torch.isfinite(delta)]
    return dict(finite=finite, nonfinite_actual=int((~torch.isfinite(a)).sum()),
                nonfinite_expected=int((~torch.isfinite(b)).sum()),
                max_abs_error=float(finite_delta.max()) if finite_delta.numel() else None,
                allclose=finite and bool(torch.allclose(a,b,atol=ATOL,rtol=RTOL)),
                argmax_equal=bool(torch.equal(a.argmax(-1),b.argmax(-1))))


def compare_capture(actual, logits, expected, expected_logits):
    return dict(fp32=comparison(logits, expected_logits),
                native=comparison(actual.logits, expected.logits),
                final_residual=comparison(actual.residual[:, -1], expected.residual[:, -1]),
                layer_residual=[comparison(actual.residual[:, i], expected.residual[:, i])
                                for i in range(actual.residual.shape[1])])


def evaluate_pair(model, recipient, donor, mapping):
    """Same full sender replacement as production, plus independently logged noops."""
    from component_analysis import hooks, specificity_ladder as r
    keys = hooks.all_component_keys(model)
    assert hooks.READOUT_KEY not in keys
    intact, base = r._capture(model, recipient, keys)
    dc, dl = r._capture(model, donor, keys)
    replacements = {k:r.mapped_replacement(intact.outputs[k], dc.outputs[k], [mapping],
                                           recipient.attention_mask, donor.attention_mask) for k in keys}
    patched, pl = r._capture(model, recipient, keys, replacements)
    result = dict(recipient=geometry(recipient), donor=geometry(donor),
                  donor_recovery=compare_capture(patched, pl, dc, dl), noops={},
                  donor_choice_differs=bool(base.argmax(-1) != dl.argmax(-1)),
                  sender_keys=[list(k) for k in keys])
    # Return small CPU readout snapshots only, not all sender activations.
    snapshots = {name:value.detach().float().cpu() for name,value in
                 [('donor_fp32',dl), ('donor_native',dc.logits),
                  ('donor_residual',dc.residual[:, -1]), ('recipient_fp32',base),
                  ('recipient_native',intact.logits), ('recipient_residual',intact.residual[:, -1])]}
    for who, batch, captured, logits in [('recipient',recipient,intact,base), ('donor',donor,dc,dl)]:
        for label, replacement in [('empty', {}), ('self_replay',
                {k:hooks.Replacement(captured.outputs[k], batch.attention_mask.to(logits.device).bool()) for k in keys})]:
            other, ol = r._capture(model, batch, keys, replacement)
            check = compare_capture(other, ol, captured, logits)
            try:
                check['production_margin_error'] = r._noop_error(logits, ol, batch)
                check['production_valid'] = True
            except ValueError as exc:
                check.update(production_valid=False, failure=str(exc))
            result['noops'][who+'_'+label] = check
    return result, snapshots


def emit(path, payload):
    text = json.dumps(payload, sort_keys=True, allow_nan=False)
    print(text, flush=True)
    if path is not None:
        with Path(path).open('a') as handle:
            handle.write(text+'\n')
            handle.flush()
            os.fsync(handle.fileno())


def main(argv=None):
    from component_analysis import ladder_pipeline as p
    parser = p.parser()
    parser.add_argument('--result-dir', required=True)
    parser.add_argument('--job-stdout', required=True)
    parser.add_argument('--job-stderr', required=True)
    args = parser.parse_args(argv)
    args.injected = False
    p.require(args.stage == 'score' and args.limit == 4 and args.batch_size == 8,
              'diagnostic requires original score pilot --limit 4 --batch-size 8')
    p.require(args.commit == COMMIT and tuple(args.tasks) == p.TASKS, 'exact original commit/task order required')
    os.environ.update(PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1')
    prepared = p.read_artifact(args.design)
    p.validate_prepared(args, prepared)
    selected = p.read_selection(args, prepared)
    tokenizer = p.common.load_tokenizer(args)
    p.validate_tokenization(prepared, tokenizer)
    pairs = list(pair_inventory(args, prepared))
    manifest = dict(kind='calibration_geometry_diagnostic', scientific_scoring=False,
                    supplied_production_commit=args.commit,
                    diagnostic_source=str(Path(__file__).resolve()),
                    diagnostic_source_sha256=p.common.file_hash(__file__),
                    production_code_hashes=p.code_hashes(),
                    design_file=str(Path(args.design).resolve()), design_file_sha256=p.common.file_hash(args.design),
                    selection_file=str(Path(args.groups).resolve()), selection_file_sha256=p.common.file_hash(args.groups),
                    selection_manifest=str(p.selection_manifest_path(args.groups).resolve()),
                    selection_manifest_sha256=p.common.file_hash(p.selection_manifest_path(args.groups)),
                    registries=p.registries(args, prepared['rows']),
                    utility_registries=p.utility_registries(args, prepared['utility']), grader_registry=p.grader_registry(),
                    model=args.model, model_revision=args.model_revision, tokenizer_revision=args.tokenizer_revision,
                    argv=vars(args), atol=ATOL, rtol=RTOL, expected_pairs=len(pairs),
                    slurm_job_id=os.environ.get('SLURM_JOB_ID'), cluster=os.environ.get('DC_CLUSTER','delta'),
                    job_stdout=str(Path(args.job_stdout).resolve()), job_stderr=str(Path(args.job_stderr).resolve()),
                    result_dir=str(Path(args.result_dir).resolve()), injected=False)
    if args.dry_run:
        emit(None, dict(event='dry_run', manifest=manifest,
                        pairs=[dict(ordinal=i, task=t, recipient=geometry(r), donor=geometry(d), mapping=m)
                               for i,(t,r,d,m) in enumerate(pairs)]))
        return 0
    import torch
    p.require(bool(os.environ.get('SLURM_JOB_ID')) and torch.cuda.is_available(), 'real diagnostic requires Slurm CUDA')
    out = Path(args.result_dir)
    p.require(not out.exists(), 'result directory already exists')
    out.mkdir(parents=True)
    manifest.update(commit=args.commit, torch_version=torch.__version__, cuda_version=torch.version.cuda,
                    gpu_name=torch.cuda.get_device_name(), dtype='torch.bfloat16',
                    evidence_file=str((out/'pairs.jsonl').resolve()), summary_file=str((out/'summary.json').resolve()))
    p.common.write_json(out/'run_manifest.json', manifest)
    events = out/'pairs.jsonl'
    status = dict(status='started', original_pairs_observed=0, expected_pairs=len(pairs), first_failure=None)
    try:
        model = p.load_model(args)
        for i,(task,recipient,donor,mapping) in enumerate(pairs):
            context = dict(ordinal=i, task=task, condition=recipient.condition,
                           instance_id=recipient.ids[0], stream=recipient.stream, mapping=mapping)
            emit(events, dict(event='pair_started', **context, recipient=geometry(recipient), donor=geometry(donor)))
            original, baseline = evaluate_pair(model, recipient, donor, mapping)
            emit(events, dict(event='original', **context, diagnostics=original))
            status['original_pairs_observed'] += 1
            if original['donor_recovery']['fp32']['allclose']:
                continue
            status['first_failure'] = context
            for label,width in [('common_parent_width', max(recipient.input_ids.shape[1],donor.input_ids.shape[1])),
                                ('common_unpadded_width', max(int(recipient.attention_mask.sum()),int(donor.attention_mask.sum())))]:
                r,d = resize(recipient,width),resize(donor,width)
                diagnostic, snapshots = evaluate_pair(model,r,d,mapping)
                drift = {name:comparison(value,baseline[name]) for name,value in snapshots.items()}
                emit(events, dict(event=label, **context, diagnostics=diagnostic, vs_original=drift))
            status['status'] = 'first_original_failure_diagnosed'
            break
        else:
            status['status'] = 'all_original_pairs_passed'
    except BaseException as exc:
        status.update(status='execution_error', error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
        emit(events, dict(event='execution_error', **status))
        raise
    finally:
        p.common.write_json(out/'summary.json', status)
        emit(events, dict(event='summary', **status))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
