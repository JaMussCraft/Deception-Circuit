"""Pure specificity-ladder sample, group and donor specifications.

Normalized row contract (the CLI must normalize raw builder rows, not guess):
``instance_id`` is a nonempty string, ``condition`` is one of CONDITIONS,
``split`` is test/train/validation, and balanced factors live at row level.
There is one row per condition/id, even across splits. ``streams`` has clean
and corrupt (designation-swapped) records. Each contains unpadded ``tokens``
(list[int]), exact ``honest_word``, ``opposite_word`` and ``honest_item``.
A supported token map additionally requires ``layout`` with nonempty
``role_spans`` and ``content_spans``: ordered [name, start, end] lists, using
half-open absolute token boundaries. These boundaries include role/content
regions as emitted by the tokenizer adapter, never positions inferred from
padding or equal tensor sizes. Full unpadded lengths and both boundary lists
must match for the absolute-index map. Content inside a span may differ.
I and user_neutral carry row-level ``request_id`` and per-stream
``user_request_span`` [start, end]. The adapter must retain source hashes and
builder alignment assertions in its input manifest; these pure functions do
not certify source model screening or tokenization provenance.

``selection_ids`` is the union of all original selection stages/tasks loaded
from their actual selection artifacts, not from historical assessment samples.
The caller must validate that provenance before invoking freeze_design.
The required ordered ``mover_selection_ids`` list contains THIS task's exact
selection artifact IDs, independently of the cross-task exclusion union. Rows
are never filtered on baseline outcomes or optional donor availability here.
This module performs no I/O, inference or empirical assessment by itself.
"""
from __future__ import annotations

import hashlib
import json
import random

from component_analysis.sampling import DEFAULT_FACTORS, draw_sample

CONDITIONS = ('D', 'H', 'F', 'I', 'user_neutral')
STREAMS = ('clean', 'corrupt')
INDEPENDENT_DONOR_SEEDS = (101, 102, 103)


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def _index(rows, *, condition=None):
    result = {}
    for row in rows:
        rid = row.get('instance_id')
        if not isinstance(rid, str) or not rid.strip():
            raise ValueError('missing or invalid instance_id')
        if rid in result:
            raise ValueError(f'duplicate instance_id (including across splits): {rid}')
        if row.get('condition') not in CONDITIONS or (condition and row['condition'] != condition):
            raise ValueError(f'condition mismatch for {rid}')
        if row.get('split') not in ('train', 'validation', 'test'):
            raise ValueError(f'missing or invalid split for {rid}')
        result[rid] = row
    return result


def _stream(row, stream):
    if stream not in STREAMS:
        raise ValueError(f'unknown stream: {stream}')
    return row.get('streams', {}).get(stream, {})


def _layout(record):
    """Return supported explicit boundaries, or None; never map padding."""
    tokens, layout = record.get('tokens'), record.get('layout')
    if not isinstance(tokens, list) or not tokens or any(type(t) is not int for t in tokens):
        return None
    if not isinstance(layout, dict):
        return None
    result = {}
    for field in ('role_spans', 'content_spans'):
        spans = layout.get(field)
        if not isinstance(spans, list) or not spans:
            return None
        previous = 0
        names = set()
        for span in spans:
            if (not isinstance(span, (list, tuple)) or len(span) != 3
                    or not isinstance(span[0], str) or not span[0] or span[0] in names
                    or type(span[1]) is not int or type(span[2]) is not int
                    or not 0 <= span[1] < span[2] <= len(tokens)
                    or span[1] < previous):
                return None
            names.add(span[0])
            previous = span[2]
        result[field] = [list(s) for s in spans]
    return result


def _aligned(recipient, donor):
    left, right = _layout(recipient), _layout(donor)
    return (left is not None and right is not None
            and len(recipient['tokens']) == len(donor['tokens']) and left == right)


def _request_matches(recipient, donor, stream):
    rs, ds = _stream(recipient, stream), _stream(donor, stream)
    span = rs.get('user_request_span')
    return (recipient.get('request_id') is not None
            and donor.get('request_id') == recipient['request_id']
            and isinstance(span, list) and len(span) == 2
            and all(type(p) is int for p in span)
            and 0 <= span[0] < span[1] <= len(rs.get('tokens', []))
            and ds.get('user_request_span') == span)


def donor_plan(recipient: dict, donor_rows: list[dict], *, operation: str,
               stream: str, seed: int) -> dict:
    """Describe one full-unpadded cell; unsupported cells carry no fake map.

    Independent donors must already be an assessment-excluded bank. Their IDs
    are sorted before seeded selection. The draw seed hashes the recorded donor
    seed with recipient condition/id/stream so recipients draw independently.
    Same-id twins use the recipient stream;
    item_swap takes its own opposite stream in its own condition. Equal-token
    replacement is explicitly degenerate, including H to itself. It never
    supplies evidence of H preservation. h_mean/zero have no individual donor.
    """
    if operation not in ('item_swap', 'h_twin', 'independent_resample',
                         'self_replay', 'empty', 'zero', 'h_mean'):
        raise ValueError(f'unknown operation: {operation}')
    _index([recipient])
    # Validate even donors outside a join; a duplicate/missing id cannot hide.
    seen = set()
    for row in donor_rows:
        _index([row])
        key = (row['condition'], row['instance_id'])
        if key in seen:
            raise ValueError(f'duplicate donor id: {key}')
        seen.add(key)
    rs = _stream(recipient, stream)
    rid, condition = recipient['instance_id'], recipient['condition']
    result = dict(operation=operation, recipient_id=rid, recipient_condition=condition,
                  recipient_stream=stream, donor_id=None, donor_condition=None,
                  donor_stream=None, donor_split=None, recipient_positions=[],
                  donor_positions=[], requested_positions=len(rs.get('tokens', [])),
                  covered_positions=0, supported=False, unsupported_reason=None,
                  eligible_ids=[], degenerate=False, no_op=False, gate_valid=False,
                  seed=seed if operation == 'independent_resample' else None)

    def unsupported(reason):
        result['unsupported_reason'] = reason
        return result

    if _layout(rs) is None:
        return unsupported('recipient lacks validated unpadded token layout')
    if operation in ('empty', 'zero', 'h_mean'):
        result.update(supported=True, gate_valid=True,
                      recipient_positions=[] if operation == 'empty' else list(range(len(rs['tokens']))),
                      covered_positions=0 if operation == 'empty' else len(rs['tokens']),
                      no_op=operation == 'empty', degenerate=operation == 'empty')
        return result
    donor_stream = stream
    if operation == 'independent_resample':
        result['draw_seed'] = int(_hash([seed, condition, rid, stream]), 16)
    if operation == 'item_swap':
        donor, donor_stream = recipient, STREAMS[1 - STREAMS.index(stream)]
    elif operation == 'self_replay' or (operation == 'h_twin' and condition in ('H', 'user_neutral')):
        donor = recipient
    else:
        target_condition = 'user_neutral' if condition in ('I', 'user_neutral') else 'H'
        candidates = [d for d in donor_rows if d['condition'] == target_condition]
        required = ('honest_word', 'opposite_word', 'honest_item')
        candidates = [d for d in candidates
                      if all(rs.get(k) is not None and _stream(d, stream).get(k) == rs[k]
                             for k in required)]
        if condition in ('I', 'user_neutral'):
            candidates = [d for d in candidates if _request_matches(recipient, d, stream)]
        if operation == 'h_twin':
            candidates = [d for d in candidates if d['instance_id'] == rid
                          and d['split'] == recipient['split']]
        else:
            candidates = [d for d in candidates if d['instance_id'] != rid
                          and d['split'] in ('train', 'validation')]
            candidates = [d for d in candidates
                          if recipient.get('template_variant') is not None
                          and d.get('template_variant') == recipient['template_variant']
                          and all(rs.get(k) is not None and _stream(d, stream).get(k) == rs[k]
                                  for k in required)
                          and _aligned(rs, _stream(d, stream))]
        candidates.sort(key=lambda d: d['instance_id'])
        result['eligible_ids'] = [d['instance_id'] for d in candidates]
        if not candidates:
            return unsupported('no eligible H-derived donor')
        donor = candidates[0] if operation == 'h_twin' else random.Random(result['draw_seed']).choice(candidates)
    ds = _stream(donor, donor_stream)
    result.update(donor_id=donor['instance_id'], donor_condition=donor['condition'],
                  donor_stream=donor_stream, donor_split=donor['split'], donor_hash=_hash(donor))
    if not _aligned(rs, ds):
        return unsupported('full unpadded length or explicit role/content boundaries unsupported')
    positions = list(range(len(rs['tokens'])))
    no_op = rs['tokens'] == ds['tokens']
    result.update(supported=True, recipient_positions=positions, donor_positions=positions,
                  covered_positions=len(positions), degenerate=no_op, no_op=no_op,
                  gate_valid=not no_op)
    return result


def freeze_design(condition_rows: dict[str, list[dict]], selection_ids: set[str], *,
                  mover_selection_ids: list[str], seed: int = 1, n: int = 100) -> dict:
    """Freeze a pure prospective design, not an empirical competence verdict.

    Input rows can include all source splits. Assessment uses test intersection;
    mover selection uses original H test rows in mover_selection_ids; H bank uses
    train+validation. Missing optional donors do not change sample membership.
    Hash domains deliberately separate selection, assessment and H bank inputs.
    Sample positions refer only to its recorded ordered eligible pool, never
    raw source-loader positions. instance_id is the authoritative join key.
    """
    if set(condition_rows) != set(CONDITIONS):
        raise ValueError(f'require exactly conditions {CONDITIONS}')
    if (not selection_ids or any(not isinstance(i, str) or not i.strip() for i in selection_ids)):
        raise ValueError('original selection ids/provenance are required')
    if type(n) is not int or n <= 0:
        raise ValueError('n must be a positive integer')
    indexed = {c: _index(condition_rows[c], condition=c) for c in CONDITIONS}
    splits = {}
    for rows in indexed.values():
        for rid, row in rows.items():
            if rid in splits and splits[rid] != row['split']:
                raise ValueError(f'source id crosses splits: {rid}')
            splits[rid] = row['split']
    test = {c: {i: r for i, r in indexed[c].items() if r['split'] == 'test'} for c in CONDITIONS}
    common = set.intersection(*(set(rows) for rows in test.values())) - set(selection_ids)
    if len(common) < n:
        raise ValueError(f'insufficient assessment ids: {len(common)} available, {n} requested')
    records = [test['D'][rid] for rid in sorted(common)]
    # Matched nuisance factors must have identical meaning across conditions.
    for rid in common:
        for factor in DEFAULT_FACTORS:
            if len({json.dumps(test[c][rid].get(factor), sort_keys=True) for c in CONDITIONS}) != 1:
                raise ValueError(f'matched factor mismatch for {rid}: {factor}')
    sample = draw_sample(records, n=n, seed=seed)
    if sample.n_drawn != n:
        raise ValueError('insufficient fixed-size assessment draw')
    assessment_ids = sample.ids
    sample_metadata = sample.as_json()
    sample_metadata['eligible_pool_indices'] = sample_metadata.pop('split_indices')
    sample_metadata['eligible_pool_ids'] = [record['instance_id'] for record in records]
    sample_metadata['join_on'] = 'instance_id'
    mover_ids = list(mover_selection_ids)
    if (not mover_ids or len(set(mover_ids)) != len(mover_ids)
            or any(not isinstance(i, str) or not i.strip() for i in mover_ids)
            or not set(mover_ids) <= set(selection_ids)
            or not set(mover_ids) <= set(test['H'])):
        raise ValueError('mover selection ids must be unique, excluded, and present in H test rows')
    banned = set(selection_ids) | set(assessment_ids)
    pools = {c: [indexed[c][rid] for rid in sorted(indexed[c])
                 if indexed[c][rid]['split'] in ('train', 'validation') and rid not in banned]
             for c in CONDITIONS}
    # Cross-split reuse would contaminate donor/bank provenance, even if excluded.
    test_union = set.union(*(set(rows) for rows in test.values()))
    for c in CONDITIONS:
        if any(r['instance_id'] in test_union for r in pools[c]):
            raise ValueError('source id crosses test and bank splits')
    donors = []
    for rid in assessment_ids:
        for c in CONDITIONS:
            recipient = test[c][rid]
            for stream in STREAMS:
                for op in ('item_swap', 'h_twin', 'zero', 'h_mean', 'self_replay', 'empty'):
                    donors.append(donor_plan(recipient, [test[k][rid] for k in CONDITIONS],
                                             operation=op, stream=stream, seed=seed))
                for donor_seed in INDEPENDENT_DONOR_SEEDS:
                    donors.append(donor_plan(recipient, pools['H'] + pools['user_neutral'],
                                             operation='independent_resample', stream=stream,
                                             seed=donor_seed))
    selection_rows = [test['H'][rid] for rid in mover_ids]
    assessment_rows = {c: [test[c][rid] for rid in assessment_ids] for c in CONDITIONS}
    return dict(schema_version=1, seed=seed, n=n, assessment_ids=assessment_ids,
                mover_selection_ids=mover_ids, selection_exclusion_ids=sorted(selection_ids),
                sample=sample_metadata, bank_ids=[r['instance_id'] for r in pools['H']],
                independent_donor_seeds=list(INDEPENDENT_DONOR_SEEDS), donors=donors,
                label_convention={c: {'canonical_direction': 'opposite-minus-honest',
                                     'condition_correct': 'opposite' if c in ('D', 'I') else 'honest',
                                     'streams': {s: {'positive_word_field': 'opposite_word',
                                                     'negative_word_field': 'honest_word'} for s in STREAMS}}
                                  for c in CONDITIONS},
                hashes={'selection': _hash({'domain': 'selection', 'ids': sorted(selection_ids), 'rows': selection_rows}),
                        'assessment': _hash({'domain': 'assessment', 'rows': assessment_rows}),
                        'bank': _hash({'domain': 'bank', 'rows': pools['H']}),
                        'donor_sources': _hash(pools), 'donors': _hash(donors)})


def choose_mover_candidates(keys: list[tuple], clean_dla, swap_dla,
                            selection_ids: list[str]) -> dict:
    """Screen heads using correct-minus-other DLA in BOTH H streams.

    Arrays are [selection ids, heads], columns following head keys in their
    input order. MLP keys are retained without screening. Zero ties fail.
    A qualifying row is positive in both streams, with >=75% such rows and
    strictly positive mean clean DLA required. This is not a copying assay.
    """
    import numpy as np

    keys = [tuple(k) for k in keys]
    if any(len(k) != 3 or k[0] not in ('head', 'mlp')
           or any(type(i) is not int or i < 0 for i in k[1:])
           or (k[0] == 'mlp' and k[2] != 0) for k in keys):
        raise ValueError('invalid component key')
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate component keys')
    heads = [k for k in keys if k[0] == 'head']
    if (not selection_ids or len(set(selection_ids)) != len(selection_ids)
            or any(not isinstance(i, str) or not i for i in selection_ids)):
        raise ValueError('selection ids must be nonempty and unique')
    clean, swap = np.asarray(clean_dla, dtype=float), np.asarray(swap_dla, dtype=float)
    shape = (len(selection_ids), len(heads))
    if clean.shape != shape or swap.shape != shape or not np.isfinite(clean).all() or not np.isfinite(swap).all():
        raise ValueError(f'finite DLA arrays must have shape {shape}')
    n = len(selection_ids)
    rankings = []
    for col, key in enumerate(heads):
        count = int(((clean[:, col] > 0) & (swap[:, col] > 0)).sum())
        mean = float(clean[:, col].mean())
        rankings.append(dict(key=list(key), clean_mean=mean,
                             clean_positive_count=int((clean[:, col] > 0).sum()),
                             corrupt_positive_count=int((swap[:, col] > 0).sum()),
                             both_positive_count=count, n_rows=n,
                             candidate=mean > 0 and count * 4 >= n * 3))
    rankings.sort(key=lambda r: (-r['clean_mean'], tuple(r['key'])))
    for rank, entry in enumerate(rankings, 1):
        entry['rank'] = rank
    removed = [r['key'] for r in rankings if r['candidate']]
    return dict(selection_ids=list(selection_ids), rankings=rankings, removed_keys=removed,
                remaining_keys=[list(k) for k in keys if list(k) not in removed],
                duplicate_group=not removed, threshold=0.75,
                interpretation='answer-contribution candidates; copying not validated')


def recorded_groups(readings: dict) -> dict:
    """Read exact recorded memberships, without reselecting or transcribing."""
    groups = {}
    try:
        for task in ('far', 'sdr', 'ser'):
            members = readings['rab'][task]['deciding_numbers']['members']
            parsed = []
            for member in members:
                kind, layer, index = member.split('.')
                key = [kind, int(layer), int(index)]
                if kind not in ('head', 'mlp') or min(key[1:]) < 0 or (kind == 'mlp' and key[2] != 0):
                    raise ValueError(f'invalid component: {member}')
                parsed.append(key)
            if not parsed or len({tuple(k) for k in parsed}) != len(parsed):
                raise ValueError('empty or duplicate recorded group')
            groups[task] = dict(members=parsed, source_members=list(members),
                                descriptive=task == 'sdr', source_hash=_hash(members))
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError('missing or invalid recorded deciding group') from exc
    return groups
