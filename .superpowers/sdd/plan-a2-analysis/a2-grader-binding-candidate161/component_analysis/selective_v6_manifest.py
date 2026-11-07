"""Build the CPU-only, previously exposed V6 mechanism panel from frozen inputs.

Only JSON and Arrow streams are read. No model inference or network access occurs.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

ADDED = {(7, 31), (8, 10), (13, 15), (13, 23), (17, 27), (19, 13), (20, 19)}
CELLS = [('identity', 1), ('identity', 2), ('inversion', 1), ('inversion', 2)]


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path):
    return json.loads(Path(path).read_text())


def _unique(rows, key):
    result = {}
    for row in rows:
        value = key(row)
        if value in result:
            raise ValueError('duplicate source ID: ' + str(value))
        result[value] = row
    return result


def _scenario(value):
    return json.dumps([value[0], sorted(value[1])], ensure_ascii=False, separators=(',', ':'))


def _cell(row):
    return row['strata']['designation_polarity'], row['strata']['item_polarity']


def _select(rows, per_cell, used):
    selected = []
    for cell in CELLS:
        candidates = sorted((r for r in rows if _cell(r) == cell),
                            key=lambda r: (_scenario(r['scenario']), r['source_id']))
        group = []
        for row in candidates:
            key = _scenario(row['scenario'])
            if key not in used:
                group.append(row)
                used.add(key)
            if len(group) == per_cell:
                break
        if len(group) != per_cell:
            raise ValueError('insufficient unique scenarios for cell ' + str(cell))
        selected.extend(group)
    return selected


def validate_manifest(manifest, verify_sources=True):
    """Reject malformed support, paired cases, labels and stale source bytes."""
    if manifest['schema_version'] != 1:
        raise ValueError('unsupported schema')
    if verify_sources:
        for path, expected in manifest['sources'].items():
            if _sha(path) != expected:
                raise ValueError('source hash mismatch: ' + path)
    masks = manifest['masks']
    geometry = manifest['geometry']
    supports = {}
    for name, count in [('new23', 23), ('new30', 30), ('oldD69', 69), ('random30', 30)]:
        support = masks[name]
        if len(support) != count or len({tuple(h) for h in support}) != count:
            raise ValueError('invalid mask count/duplicate: ' + name)
        if any(len(h) != 2 or any(type(i) is not int for i in h) or
               not (0 <= h[0] < geometry['num_layers'] and 0 <= h[1] < geometry['num_heads'])
               for h in support):
            raise ValueError('invalid head support: ' + name)
        supports[name] = {tuple(h) for h in support}
    if not supports['new23'] <= supports['new30'] or supports['new30'] - supports['new23'] != ADDED:
        raise ValueError('New23/New30 difference mismatch')
    if {tuple(h) for h in manifest['added_heads']} != ADDED:
        raise ValueError('added heads mismatch')
    rows = manifest['cases']
    _unique(rows, lambda r: r['case_id'])
    groups = defaultdict(list)
    for row in rows:
        if row['variant'] not in ('D', 'H', 'F', 'I') or row['family'] not in ('sdr', 'far'):
            raise ValueError('unknown case variant/family')
        for key in ('recipient_token_ids', 'donor_token_ids'):
            if not row[key] or any(type(t) is not int or t < 0 for t in row[key]):
                raise ValueError('invalid token IDs')
        target, alternate, truth = (row[k] for k in ('requested_target_id', 'alternate_answer_id', 'truthful_id'))
        if any(type(t) is not int or t < 0 for t in (target, alternate, truth)) or target == alternate:
            raise ValueError('invalid answer labels')
        if truth not in (target, alternate) or (target == truth) != (row['variant'] in ('H', 'F')):
            raise ValueError('requested/truth label mismatch')
        if row['scenario_key'] == row['donor_scenario_key']:
            raise ValueError('donor scenario overlap')
        groups[(row['family'], row['scenario_key'])].append(row)
    counts = Counter()
    for (family, scenario), group in groups.items():
        expected = {'D', 'H', 'F', 'I'} if family == 'sdr' else {'D', 'H', 'F'}
        if len(group) != len(expected) or {r['variant'] for r in group} != expected:
            raise ValueError('missing/duplicate scenario variant')
        signatures = {(r['split'], r['source_id'], r['donor_source_id'], r['donor_scenario_key'],
                       tuple(r['donor_token_ids']), r['truthful_id']) for r in group}
        if len(signatures) != 1:
            raise ValueError('variant donor/source/split mismatch')
        row = group[0]
        counts[(family, row['split'], row['stratum']['designation_polarity'], row['stratum']['item_polarity'])] += 1
    expected_counts = {(f, s, d, i): 4 for f, splits in [('sdr', ('discovery', 'validation')),
                                                       ('far', ('supplementary',))]
                       for s in splits for d, i in CELLS}
    if counts != expected_counts or len(rows) != 176:
        raise ValueError('panel count/stratum mismatch')
    if manifest['exposure']['previously_exposed'] is not True:
        raise ValueError('exposed-data declaration missing')


def load_manifest(path, verify_sources=True):
    manifest = _json(path)
    validate_manifest(manifest, verify_sources=verify_sources)
    return manifest


def build_manifest(*, prepared_path, proposal_path, masks_path, inversion_path, inversion_doc_path):
    """Select 32 SDR scenarios plus 16 FAR scenarios without new model outcomes."""
    import pyarrow as pa
    from tokenizers import Tokenizer

    prepared, proposal, frozen = map(_json, (prepared_path, proposal_path, masks_path))
    recipients = _unique(prepared['recipients'], lambda r: (r['family'], r['source_id']))
    with pa.memory_map(str(inversion_path), 'r') as stream:
        inversion = _unique(pa.ipc.open_stream(stream).read_all().to_pylist(), lambda r: r['instance_id'])
    filter_rows = _unique(_json(Path(inversion_path).parents[1] / 'filter_report.json')['rows'], lambda r: r['instance_id'])
    for sid, inv in inversion.items():
        record = filter_rows.get(sid)
        if record is None or record['kept'] is not True or record['choice'] != ['b', 'b'] or min(inv['clean_margin'], inv['corrupt_margin']) < 0.7:
            raise ValueError('inversion capable-ID/filter mismatch')
        if record['h'] != [inv['h_instructed_inversion_clean'], inv['h_instructed_inversion_corrupt']]:
            raise ValueError('inversion capability margin mismatch')
    inversion_config = _json(Path(inversion_path).parents[1] / 'dataset_config.json')
    builder_path = Path(inversion_path).parents[4] / 'dataset/build_inversion_v2.py'
    if _sha(builder_path) != inversion_config['builder_sha256']:
        raise ValueError('inversion builder hash mismatch')
    snapshot = Path(prepared['model_snapshot'])
    tokenizer = Tokenizer.from_file(str(snapshot / 'tokenizer.json'))
    source_paths = [prepared_path, proposal_path, masks_path, inversion_path, inversion_doc_path,
                    Path(inversion_path).parents[1] / 'filter_report.json',
                    Path(inversion_path).parents[1] / 'dataset_config.json',
                    snapshot / 'tokenizer.json', snapshot / 'tokenizer_config.json', snapshot / 'config.json',
                    snapshot / 'generation_config.json']
    source_paths.extend([builder_path, inversion_config['pool_path'], inversion_config['clause_forms_path']])
    for key in ('pool', 'clause_forms'):
        if _sha(inversion_config[key + '_path']) != inversion_config[key + '_sha256']:
            raise ValueError('inversion derivation source hash mismatch')
    for name in ('new-allW23', 'new-allW30'):
        origin = frozen['conditions'][name]['origin']
        if _sha(origin['path']) != origin['sha256']:
            raise ValueError('mask origin hash mismatch')
        source_paths.append(origin['path'])
    sources = {str(Path(p).resolve()): _sha(p) for p in source_paths}
    for binding in prepared['model_metadata']:
        if _sha(binding['path']) != binding['sha256']:
            raise ValueError('tokenizer/model metadata hash mismatch')
    masks = {name: frozen['conditions'][origin]['removed_heads'] for name, origin in
             [('new23', 'new-allW23'), ('new30', 'new-allW30'), ('oldD69', 'oldD69'), ('random30', 'random30')]}
    proposals = {f: _unique(v['recipients'], lambda r: r['source_id']) for f, v in proposal['families'].items()}
    eligible = [r for (f, sid), r in recipients.items() if f == 'sdr' and sid in inversion]
    used = set()
    discovery = _select(eligible, 4, used)
    validation = _select(eligible, 4, used)
    supplement = _select([r for (f, _), r in recipients.items() if f == 'far'], 4, set())
    selected = [('discovery', r) for r in discovery] + [('validation', r) for r in validation] + [('supplementary', r) for r in supplement]
    cases = []
    for split, row in selected:
        family, sid, donor_id = row['family'], row['source_id'], row['donor_source_id']
        if sid not in proposals[family] or donor_id not in prepared['donors'][family]:
            raise ValueError('missing source ID in proposal/donor join')
        original = proposals[family][sid]
        donor = prepared['donors'][family][donor_id]
        if original['donor_source_id'] != donor_id or _scenario(original['scenario']) != _scenario(row['scenario']):
            raise ValueError('proposal recipient/donor join mismatch')
        donor_stream = donor['streams']['clean']
        original_donor = proposal['families'][family]['neutral_h_donors'].get(donor_id)
        if donor['source_id'] != donor_id or original_donor is None or original_donor['instance_id'] != donor_id:
            raise ValueError('donor source ID mismatch')
        if donor_stream['text'] != original_donor['clean_prompt'] or _scenario(donor['scenario']) != _scenario([original_donor['entity'], [original_donor['item_1'], original_donor['item_2']]]):
            raise ValueError('donor prompt/scenario join mismatch')
        variants = ('D', 'H', 'F', 'I') if family == 'sdr' else ('D', 'H', 'F')
        for variant in variants:
            base = row['conditions']['D' if variant == 'I' else variant]['clean']
            labels = base['label_ids']
            truth, false = labels['truth'], labels['deceptive']
            text, ids = base['text'], base['ids']
            evidence = ({k: inversion[sid][k] for k in ('h_pressure_clean', 'h_pressure_corrupt',
                        'h_neutral_clean', 'h_neutral_corrupt', 'h_nopressure_clean', 'h_nopressure_corrupt')}
                        if family == 'sdr' else {'availability': 'V5 preserved baseline provenance; no capable-I claim'})
            if variant == 'I':
                inv = inversion[sid]
                if inv['condition'] != 'inversion' or inv['slot_kind'] != 'transparent':
                    raise ValueError('incorrect inversion condition')
                text = inv['clean_prompt']
                ids = tokenizer.encode(text, add_special_tokens=False).ids
                token = tokenizer.encode(' ' + inv['target'], add_special_tokens=False).ids
                if token != [false] or tokenizer.encode(' ' + inv['distractor'], add_special_tokens=False).ids != [truth]:
                    raise ValueError('inversion target labels mismatch')
                if (inv['designation_polarity'], inv['item_polarity']) != _cell(row):
                    raise ValueError('inversion stratum mismatch')
                if min(inv['clean_margin'], inv['corrupt_margin']) < 0.7:
                    raise ValueError('saved inversion capability below eligibility threshold')
                evidence.update({k: inv[k] for k in ('instructed_inversion_id', 'instructed_inversion_form',
                            'clean_margin', 'corrupt_margin', 'h_instructed_inversion_clean',
                            'h_instructed_inversion_corrupt', 'h_pressure_clean', 'h_pressure_corrupt',
                            'h_neutral_clean', 'h_neutral_corrupt', 'h_nopressure_clean', 'h_nopressure_corrupt')})
                evidence['saved_filter_record'] = filter_rows[sid]
            elif text != original['conditions'][variant]['clean_prompt']:
                raise ValueError('proposal prompt mismatch')
            if tokenizer.encode(text, add_special_tokens=False).ids != ids:
                raise ValueError('recipient token/text mismatch')
            if tokenizer.encode(donor_stream['text'], add_special_tokens=False).ids != donor_stream['ids']:
                raise ValueError('donor token/text mismatch')
            target = false if variant in ('D', 'I') else truth
            if variant != 'I' and labels['target'] != target:
                raise ValueError('frozen target mismatch')
            cases.append(dict(case_id=f'{family}:{sid}:{variant}', scenario_key=_scenario(row['scenario']),
                              family=family, split=split, variant=variant, recipient_token_ids=ids,
                              donor_token_ids=donor_stream['ids'], requested_target_id=target,
                              alternate_answer_id=truth if target == false else false, truthful_id=truth,
                              recipient_text=text, donor_text=donor_stream['text'], source_id=sid,
                              donor_source_id=donor_id, donor_scenario_key=_scenario(donor['scenario']),
                              donor_stream='clean', stratum=row['strata'],
                              provenance={'recipient_stream': 'clean', 'original_test_id': sid,
                                          'original_donor_split': 'validation', 'saved_capability': evidence}))
    all_sdr = {sid for (f, sid) in recipients if f == 'sdr'}
    chosen = {r['source_id'] for r in discovery + validation}
    manifest = dict(schema_version=1, status='candidate_not_frozen', sources=sources, masks=masks,
                    geometry=frozen['geometry'], added_heads=[list(h) for h in sorted(ADDED)], cases=cases,
                    model_name='meta-llama/Llama-3.1-8B-Instruct', tokenizer_id=str(snapshot), pad_token_id=128009,
                    model_identity=prepared['model_identity'], tokenizer=prepared['tokenizer'],
                    exposure={'previously_exposed': True, 'description': 'V5 exposed mechanism development/internal validation; no pristine heldout claim'},
                    selection={'rule': 'lexicographic canonical scenario then source_id, discovery then validation; four per cell',
                               'sdr_intersection_ids': len(eligible),
                               'sdr_intersection_scenarios': len({_scenario(r['scenario']) for r in eligible}),
                               'sdr_intersection_cell_counts': {str(c): sum(_cell(r) == c for r in eligible) for c in CELLS},
                               'excluded_sdr_ids': {sid: 'not_in_capable_directive_I' if sid not in inversion else 'not_selected_fixed_quota_or_scenario_duplicate'
                                                    for sid in sorted(all_sdr - chosen)},
                               'cross_family_scenario_overlap': sorted({_scenario(r['scenario']) for r in discovery + validation} &
                                                                      {_scenario(r['scenario']) for r in supplement}),
                               'excluded_far_ids': sorted(r['source_id'] for (f, _), r in recipients.items()
                                                          if f == 'far' and r['source_id'] not in {v['source_id'] for v in supplement}),
                               'no_refill_after_fresh_outcomes': True},
                    provenance={'base_commit': 'c24b5d946d4b7411bfa16a0732948d934fd70b7d',
                                'inversion_builder': str(builder_path),
                                'inversion_builder_sha256': inversion_config['builder_sha256'],
                                'inversion_source_commit_root_verified': 'a0fae76f0f131bd3e125111982ee98b0e0dd5306',
                                'source_worktree_clean_claim': False,
                                'inversion_filter': 'saved directive I target argmax and margin >=0.7 in both streams',
                                'donor_policy': 'unchanged V5 independent validation neutral-H clean stream',
                                'intervention': 'recipient last nonpad <- donor own last nonpad; head slices only'})
    validate_manifest(manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('prepared', 'proposal', 'masks', 'inversion', 'inversion-doc'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    manifest = build_manifest(prepared_path=args.prepared, proposal_path=args.proposal, masks_path=args.masks,
                              inversion_path=args.inversion, inversion_doc_path=args.inversion_doc)
    with Path(args.output).open('x') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')
    print(json.dumps({'cases': len(manifest['cases']), 'sources': len(manifest['sources']), 'status': manifest['status']}))


if __name__ == '__main__':
    main()
