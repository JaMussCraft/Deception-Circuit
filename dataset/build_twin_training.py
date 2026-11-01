"""Build private, clean-orientation same-item neutral-reference datasets.

No scoring, sampling or behavioral filtering occurs here. Source margins remain
historical values; recipient labels define the unchanged clean training loss.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Optional

from dataset import deception_common as dc
from dataset.build_deception_dataset import save_splits
from dataset.matched_honest import assert_clause_aligned_pair, clause_span

SPLITS = ('train', 'validation', 'test')
TASKS = ('far_v2', 'sdr_v2', 'ser_v2')
IDENTITY = ('task', 'pressure_id', 'entity', 'item_1', 'item_2', 'clean_item_d',
            'desig', 'desig_inv', 'template_variant', 'item_polarity',
            'designation_polarity', 'question')
LABELS = {'recipient_expected': 'target', 'reference_expected': 'distractor',
          'training_target': 'recipient.target', 'training_distractor': 'recipient.distractor',
          'reference_labels_used_for_loss': False}


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def _require(ok, message):
    if not ok:
        raise ValueError(message)


def _index(source):
    _require(set(source) == set(SPLITS), 'all train/validation/test splits required')
    maps, seen = {}, set()
    for split in SPLITS:
        maps[split] = {}
        for row in source[split]:
            ident = row.get('instance_id')
            _require(isinstance(ident, str) and bool(ident), 'missing instance_id')
            _require(ident not in seen, 'duplicate or cross-split instance_id: ' + ident)
            seen.add(ident)
            maps[split][ident] = row
    return maps


def _pair(recipient, neutral, tokenizer, max_length):
    condition = recipient.get('condition')
    if condition == 'deceptive':
        _require(neutral.get('condition') == 'honest' and
                 neutral.get('honest_twin_kind') == 'neutral_clause', 'wrong neutral twin condition/kind')
        old, new = recipient.get('pressure'), neutral.get('pressure')
    else:
        _require(condition == 'user_inversion' and neutral.get('condition') == 'user_neutral',
                 'wrong user-turn condition')
        _require(all(r.get('baseline_kind') == 'matched_frame_neutral_request'
                     for r in (recipient, neutral)), 'wrong user-turn baseline_kind')
        _require(recipient.get('request_id') == neutral.get('request_id') and
                 bool(recipient.get('request_id')), 'request identities differ or absent')
        old, new = recipient.get('request_text'), neutral.get('request_text')
    for key in IDENTITY:
        _require(recipient.get(key) == neutral.get(key), 'twin identity differs: ' + key)
    _require(recipient.get('target') == neutral.get('distractor') and
             recipient.get('distractor') == neutral.get('target'), 'neutral labels do not reverse recipient labels')
    for row in (recipient, neutral):
        for key in ('target', 'distractor'):
            _require(isinstance(row.get(key), str) and
                     len(dc.encode_answer_token(tokenizer, row[key])) == 1,
                     'non-single-token answer: ' + key)
    _require(recipient['target'] != recipient['distractor'], 'target equals distractor')
    prompt, reference = recipient['clean_prompt'], neutral['clean_prompt']
    _require(isinstance(old, str) and bool(old) and isinstance(new, str) and bool(new) and old != new,
             'missing or identical replacement literals')
    _require(prompt.count(old) == 1 and reference.count(new) == 1,
             'replacement must occur exactly once')
    _require(prompt.replace(old, new, 1) == reference, 'prompt differs outside replacement span')
    ids = tokenizer.encode(prompt, add_special_tokens=False)
    other = tokenizer.encode(reference, add_special_tokens=False)
    _require(0 < len(ids) == len(other) <= max_length, 'unequal token counts or overlength prompt')
    if condition == 'deceptive':
        span = clause_span(tokenizer, prompt, old)
        # Reuse the established assertion, while independently enforcing its
        # invariants below so python -O cannot remove validation.
        try:
            assert_clause_aligned_pair(tokenizer, prompt, reference, old, max_length)
        except AssertionError as exc:
            raise ValueError(str(exc)) from exc
    else:
        span = clause_span(tokenizer, prompt, old)
        reference_span = clause_span(tokenizer, reference, new)
        _require(span == reference_span, 'request spans differ between twins')
        for source in (recipient, neutral):
            _require(source.get('request_spans', {}).get('clean') == list(span),
                     'stale or missing request span')
    start, end = span
    _require(0 <= start < end <= len(ids)-1, 'replacement touches readout')
    _require(end-start == len(tokenizer.encode(' ' + old, add_special_tokens=False)),
             'replacement crosses token boundary')
    _require(end-start == len(tokenizer.encode(' ' + new, add_special_tokens=False)),
             'neutral replacement crosses token boundary')
    _require(all(x == y for pos, (x, y) in enumerate(zip(ids, other))
                 if not start <= pos < end), 'tokens differ outside replacement span')
    _require(ids[-1] == other[-1], 'readout token differs')
    row = dict(recipient, corrupt_prompt=reference)
    with contextlib.redirect_stdout(io.StringIO()):
        loader = dc.DeceptionDatasetLlama([row], tokenizer, max_length=max_length)
    _require(len(loader) == 1, 'loader dropped row')
    encoded = loader[0]
    _require(encoded['attention_mask'].equal(encoded['corrupted_attention_mask']), 'unequal attention masks')
    _require(int(encoded['prefix_length']) == len(ids), 'loader readout differs')
    return {'reference_prompt': reference, 'replacement_span': list(span),
            'token_length': len(ids), 'readout': len(ids)-1,
            'recipient_prompt_hash': _hash(prompt), 'reference_prompt_hash': _hash(reference),
            'replacement_from': old, 'replacement_to': new}


def validate_sources(recipient: dict, neutral: dict, *, tokenizer, max_length: int) -> dict:
    """Validate every source row before any cross-condition intersection."""
    _require(isinstance(max_length, int) and max_length > 0, 'max_length must be positive')
    r, n = _index(recipient), _index(neutral)
    pairs, ids = {}, {}
    for split in SPLITS:
        _require(set(r[split]) == set(n[split]), 'missing twin ids in ' + split)
        ids[split] = sorted(r[split])
        pairs[split] = {ident: _pair(r[split][ident], n[split][ident], tokenizer, max_length)
                        for ident in ids[split]}
    return {'recipient': r, 'neutral': n, 'ids': ids, 'pairs': pairs,
            'counts': {s: len(ids[s]) for s in SPLITS}}


def _load(path):
    path = Path(path).resolve()
    config = dc.load_dataset_config(str(path))
    records = {s: dc.load_or_generate_deception_data(str(path), split=s) for s in SPLITS}
    files = {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(path.rglob('*')) if p.is_file()}
    schema = {s: {key: sorted({type(row.get(key)).__name__ for row in records[s]})
                  for key in sorted({key for row in records[s] for key in row})} for s in SPLITS}
    return records, {'path': str(path), 'config': config, 'content_hash': _hash(files),
                     'file_hashes': files, 'row_hash': _hash(records), 'schema': schema}


def _hex(value, length):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{%d}' % length, value) is not None


def _evidence_file(root, descriptor):
    """Read hashed evidence only from a file within the source dataset root."""
    _require(isinstance(descriptor, dict), 'missing scoring evidence descriptor')
    name = descriptor.get('path')
    _require(isinstance(name, str) and bool(name) and not Path(name).is_absolute(),
             'scoring evidence path must be dataset-relative')
    root = Path(root).resolve()
    path = (root/name).resolve()
    _require(path.is_relative_to(root) and path.is_file(), 'missing or escaped scoring evidence file')
    blob = path.read_bytes()
    _require(_hex(descriptor.get('sha256'), 64) and
             hashlib.sha256(blob).hexdigest() == descriptor['sha256'], 'scoring evidence byte digest differs')
    return blob


def _json_evidence(blob):
    try:
        return json.loads(blob)
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError('invalid scoring evidence JSON') from exc


def _scoring_receipt(meta, tokenizer):
    cfg, root = meta['config'], meta['path']
    descriptor = cfg.get('scoring_provenance')
    # This name is the shared A1 contract, not a caller-selected arbitrary file.
    _require(isinstance(descriptor, dict) and descriptor.get('path') == 'scoring_provenance.json',
             'missing scoring_provenance.json receipt')
    blob = _evidence_file(root, descriptor)
    receipt = _json_evidence(blob)
    _require(isinstance(receipt, dict) and type(receipt.get('schema_version')) is int and
             receipt['schema_version'] == 1 and receipt.get('kind') == 'user_inversion_scored',
             'invalid scoring receipt schema/kind')
    _require(_hex(receipt.get('source_commit'), 40), 'invalid scoring source commit')
    _require(_hex(receipt.get('request_pool_hash'), 64), 'invalid scoring request pool hash')
    _require(receipt.get('model') == cfg['model'], 'scoring model differs')
    name = getattr(tokenizer, 'name_or_path', type(tokenizer).__name__)
    _require(receipt.get('tokenizer') == name, 'scoring tokenizer differs')
    for key in ('model_revision', 'tokenizer_revision', 'dtype'):
        _require(isinstance(receipt.get(key), str) and bool(receipt[key].strip()),
                 'missing scoring ' + key)
    revision = getattr(tokenizer, 'init_kwargs', {}).get('_commit_hash')
    if revision:
        _require(receipt['tokenizer_revision'] == revision, 'scoring tokenizer revision differs')
    for key in ('request_pool_hash', 'model_revision', 'tokenizer_revision'):
        if cfg.get(key) is not None:
            _require(cfg[key] == receipt[key], 'source config/scoring ' + key + ' differs')
    _require(receipt.get('scorer') == 'dataset.deception_common.score_prompts', 'invalid scorer identity')
    files = receipt.get('score_files')
    _require(isinstance(files, dict) and set(files) == set(SPLITS), 'missing scoring splits')
    records, evidence, seen = {}, {'scoring_provenance.json': blob}, set()
    for split in SPLITS:
        data = _evidence_file(root, files[split])
        name = files[split]['path']
        _require(name != 'scoring_provenance.json', 'score path collides with receipt')
        evidence[name] = data
        records[split] = {}
        for line in data.splitlines():
            record = _json_evidence(line)
            _require(isinstance(record, dict), 'invalid score record')
            ident = record.get('instance_id')
            _require(isinstance(ident, str) and bool(ident) and ident not in seen,
                     'duplicate or cross-split score instance_id')
            seen.add(ident)
            records[split][ident] = record
    return receipt, records, evidence


def _validate_native_score(score, tokenizer):
    _require(isinstance(score, dict), 'missing native score')
    for key in ('margin', 'logit_a', 'logit_b', 'honest_minus_opposite', 'opposite_minus_honest'):
        value = score.get(key)
        _require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value),
                 'nonfinite or missing score ' + key)
    _require(score['honest_minus_opposite'] == score['margin'] and
             score['opposite_minus_honest'] == -score['margin'], 'inconsistent signed margins')
    _require(score.get('choice') in ('a', 'b', 'other') and isinstance(score.get('argmax'), str) and
             type(score.get('argmax_id')) is int and score['argmax_id'] >= 0,
             'invalid native argmax')
    words = []
    for key in ('expected_honest', 'expected_opposite'):
        word = score.get(key)
        _require(isinstance(word, str) and bool(word.strip()) and score.get(key+'_token') == ' '+word,
                 'missing or inconsistent canonical word/token')
        encoded = dc.encode_answer_token(tokenizer, word)
        _require(len(encoded) == 1, 'non-single-token scoring answer')
        words.append(encoded[0])
    _require(words[0] != words[1] and _hex(score.get('prompt_hash'), 64), 'invalid score words/prompt hash')
    expected_choice = 'a' if score['argmax_id'] == words[0] else 'b' if score['argmax_id'] == words[1] else 'other'
    _require(score['choice'] == expected_choice and tokenizer.decode(score['argmax_id']) == score['argmax'],
             'native argmax disagrees with choice/tokenizer')
    # Keep the scorer's native-dtype subtraction: promoted logits may differ by
    # an ulp, so recomputing margin from logit_a/logit_b would reject real scores.


def _validate_scored_control(rows, meta, selected, tokenizer):
    models = [m['config']['model'] for m in meta.values()]
    _require(all(model == models[0] for model in models), 'source model identities differ')
    _require(meta['I']['config']['margin_thresh'] in (.7, .5), 'unsupported inversion threshold')
    _require(meta['I_neutral']['config']['margin_thresh'] == .3, 'neutral diagnostic threshold must be 0.3')
    receipts = [_scoring_receipt(meta[k], tokenizer) for k in ('I', 'I_neutral')]
    _require(receipts[0][2] == receipts[1][2], 'scoring receipts/files differ between arms')
    receipt, scores, evidence = receipts[0]
    source_splits = {row['instance_id']: split for source in rows.values()
                     for split, records in source.items() for row in records}
    # All scored ids, even rejected ids, must have native finite scores and
    # cannot borrow an unselected original source id from another split.
    for split, records in scores.items():
        for ident, record in records.items():
            _require(ident not in source_splits or source_splits[ident] == split,
                     'score id crosses source split')
            for arm in ('inversion', 'baseline'):
                _require(isinstance(record.get(arm), dict), 'missing score arm')
                for stream in ('clean', 'corrupt'):
                    _validate_native_score(record[arm].get(stream), tokenizer)
    indexed = {k: {s: {r['instance_id']: r for r in source[s]} for s in SPLITS}
               for k, source in rows.items()}
    for split in SPLITS:
        for ident in selected[split]:
            _require(ident in scores[split], 'retained id missing score record')
            drow, hrow = indexed['D'][split][ident], indexed['H'][split][ident]
            hashes = {'D': _hash(drow), 'H': _hash(hrow)}
            for kind, arm in (('I', 'inversion'), ('I_neutral', 'baseline')):
                row = indexed[kind][split][ident]
                _require(row.get('source_row_hashes') == hashes, 'A1 source D/H row hashes differ')
                for stream in ('clean', 'corrupt'):
                    score = scores[split][ident][arm][stream]
                    honest, opposite = ((drow['distractor'], drow['target']) if stream == 'clean'
                                        else (drow['target'], drow['distractor']))
                    _require(score['prompt_hash'] == _hash(row[stream+'_prompt']), 'scoring prompt hash differs')
                    _require(score['expected_honest'] == honest and score['expected_opposite'] == opposite,
                             'scoring canonical words differ')
                    if kind == 'I':
                        _require(score['choice'] == 'b' and -score['margin'] >= meta['I']['config']['margin_thresh'],
                                 'retained inversion fails threshold/argmax')
    return {'receipt': receipt, 'sha256': hashlib.sha256(evidence['scoring_provenance.json']).hexdigest()}, evidence



def _strata(rows):
    keys = ('pressure_id', 'template_variant', 'item_polarity', 'designation_polarity')
    return {key: dict(sorted(Counter(str(r.get(key)) for r in rows).items())) for key in keys}


def materialize(root_d: str, root_h: str, *, root_i: Optional[str],
                root_i_neutral: Optional[str], output_root: str, tasks: list,
                cohort: str, tokenizer, max_length: int, commit: Optional[str] = None,
                input_paths: Optional[dict] = None, validate_only: bool = False) -> dict:
    """Validate completely, then write ordinary train.py-compatible Arrow roots.

    input_paths is {task: {D: path, H: path, I: path, I_neutral: path}}.
    Every mapped path is literal; roots otherwise expose the documented names.
    """
    output = Path(output_root)
    if output.exists():
        raise FileExistsError(str(output))
    _require(cohort in ('timing-d-only', 'matched'), 'unknown cohort')
    matched = cohort == 'matched'
    paths = input_paths or {}
    _require(bool(tasks) and len(set(tasks)) == len(tasks) and all(t in TASKS for t in tasks), 'invalid tasks')
    _require(not (set(paths)-set(tasks)), 'mapping has unknown tasks')
    if matched:
        _require(bool(root_i and root_i_neutral) or all(
            'I' in paths.get(t, {}) and 'I_neutral' in paths.get(t, {}) for t in tasks), 'matched requires both I inputs')
        _require(isinstance(commit, str) and re.fullmatch(r'[0-9a-f]{40}', commit) is not None,
                 'matched requires full caller --commit provenance')
    else:
        _require(root_i is None and root_i_neutral is None and
                 all(not ({'I', 'I_neutral'} & set(v)) for v in paths.values()), 'timing-d-only forbids peer inputs')
    manifest = dict(schema_version=1, cohort=cohort, fleet_ready=matched, source_commit=commit,
                    max_seq_length=max_length, tokenizer={'name': getattr(tokenizer, 'name_or_path', type(tokenizer).__name__),
                    'class': type(tokenizer).__name__, 'vocab_size': getattr(tokenizer, 'vocab_size', None)},
                    label_semantics=LABELS, tasks={})
    pending = []
    for task in tasks:
        overrides = paths.get(task, {})
        _require(not (set(overrides)-{'D', 'H', 'I', 'I_neutral'}), 'unknown mapping source')
        defaults = {'D': str(Path(root_d)/task), 'H': str(Path(root_h)/(task+'_honest'))}
        if matched:
            defaults.update(I=str(Path(root_i)/task) if root_i else None,
                            I_neutral=str(Path(root_i_neutral)/task) if root_i_neutral else None)
        rows, meta = {}, {}
        for kind, default in defaults.items():
            rows[kind], meta[kind] = _load(overrides.get(kind, default))
            cfg = meta[kind]['config']
            expected = {'D': 'deceptive', 'H': 'honest', 'I': 'user_inversion', 'I_neutral': 'user_neutral'}[kind]
            _require(cfg.get('task') == task and cfg.get('condition') == expected,
                     'source config task/condition mismatch: ' + kind)
            if kind == 'H':
                _require(cfg.get('honest_twin_kind') == 'neutral_clause', 'missing neutral twin kind')
            margin = cfg.get('margin_thresh')
            _require(isinstance(margin, (float, int)) and not isinstance(margin, bool) and
                     math.isfinite(margin) and margin >= 0, 'missing source threshold: ' + kind)
            if matched:
                _require(isinstance(cfg.get('model'), str) and bool(cfg['model'].strip()),
                         'missing source model identity')
                if kind in ('I', 'I_neutral'):
                    _require(cfg.get('baseline_kind') == 'matched_frame_neutral_request', 'missing A1 control identity')
        validated = {'D': validate_sources(rows['D'], rows['H'], tokenizer=tokenizer, max_length=max_length)}
        if matched:
            validated['I'] = validate_sources(rows['I'], rows['I_neutral'], tokenizer=tokenizer, max_length=max_length)
        # Cross-source split leakage must fail even for rows later dropped.
        ownership = {}
        for source in rows.values():
            for split, records in source.items():
                for row in records:
                    ident = row['instance_id']
                    _require(ident not in ownership or ownership[ident] == split,
                             'cross-source cross-split leakage: ' + ident)
                    ownership[ident] = split
        selected = {s: sorted(set.intersection(*(set(v['ids'][s]) for v in validated.values()))) for s in SPLITS}
        _require(all(selected.values()), 'empty matched split')
        if matched:
            for split in SPLITS:
                for ident in selected[split]:
                    drow = validated['D']['recipient'][split][ident]
                    irow = validated['I']['recipient'][split][ident]
                    for key in IDENTITY + ('target', 'distractor'):
                        _require(drow.get(key) == irow.get(key), 'D/I cohort identity differs: ' + key)
        scoring = None
        if matched:
            scoring, _ = _validate_scored_control(rows, meta, selected, tokenizer)
        summary = dict(sources=meta, split_ids=selected, counts={s: len(selected[s]) for s in SPLITS},
                       original_counts={k: {s: len(v[s]) for s in SPLITS} for k, v in rows.items()}, attrition={})
        if scoring is not None:
            summary['a1_scoring'] = scoring
        for kind, source in rows.items():
            summary['attrition'][kind] = {s: {'original': len(source[s]), 'matched': len(selected[s]),
                'dropped_ids': sorted(set(r['instance_id'] for r in source[s])-set(selected[s])),
                'original_strata': _strata(source[s]),
                'matched_strata': _strata([r for r in source[s] if r['instance_id'] in selected[s]])} for s in SPLITS}
        for kind, pairset in validated.items():
            donor = 'H' if kind == 'D' else 'I_neutral'
            built = {}
            proofs = {}
            for split in SPLITS:
                built[split], proofs[split] = [], {}
                for ident in selected[split]:
                    recipient, reference = pairset['recipient'][split][ident], pairset['neutral'][split][ident]
                    proof = pairset['pairs'][split][ident]
                    built[split].append(dict(recipient, corrupt_prompt=reference['clean_prompt'],
                        source_recipient=dict(recipient), source_reference=dict(reference), orientation='clean',
                        corruption_kind='neutral_twin_same_item', recipient_condition=recipient['condition'],
                        donor_identity={'instance_id': ident, 'condition': reference['condition'], 'stream': 'clean'},
                        label_semantics=LABELS, token_proof=proof))
                    proofs[split][ident] = proof
            cfg = dict(meta[kind]['config'], recipient_condition=meta[kind]['config']['condition'],
                       corruption_kind='neutral_twin_same_item', label_semantics=LABELS,
                       fleet_ready=matched, cohort=cohort, max_seq_length=max_length,
                       split_ids=selected, source_provenance={kind: meta[kind], donor: meta[donor]},
                       source_commit=commit, token_proofs=proofs, source_margins_are_historical=True,
                       train_samples=len(selected['train']), val_samples=len(selected['validation']),
                       test_samples=len(selected['test']))
            if scoring is not None:
                # This receipt describes the original A1 prompts, retained in
                # source_recipient/reference, not the new neutral corruption.
                cfg.pop('scoring_provenance', None)
                cfg['a1_scoring'] = scoring
            pending.append((output/kind/task, built, cfg))
        manifest['tasks'][task] = summary
    manifest['build_hash'] = _hash(manifest)
    if not validate_only:
        output.mkdir(parents=True, exist_ok=False)
        for path, splits, cfg in pending:
            save_splits(splits, str(path))
            (path/'dataset_config.json').write_text(json.dumps(cfg, indent=2)+'\n')
        (output/'build_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('d-root', 'h-root'):
        parser.add_argument('--'+name, default='data/datasets')
    for name in ('i-root', 'i-neutral-root', 'commit', 'input-paths'):
        parser.add_argument('--'+name)
    parser.add_argument('--output-root', required=True)
    parser.add_argument('--cohort', required=True, choices=('timing-d-only', 'matched'))
    parser.add_argument('--tasks', nargs='+', default=list(TASKS))
    parser.add_argument('--max-seq-length', type=int, default=120)
    parser.add_argument('--model', default=dc.DEFAULT_MODEL)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args(argv)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True)
    mapping = json.loads(Path(args.input_paths).read_text()) if args.input_paths else None
    result = materialize(args.d_root, args.h_root, root_i=args.i_root, root_i_neutral=args.i_neutral_root,
                         output_root=args.output_root, tasks=args.tasks, cohort=args.cohort,
                         tokenizer=tokenizer, max_length=args.max_seq_length, commit=args.commit,
                         input_paths=mapping, validate_only=args.validate_only)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
