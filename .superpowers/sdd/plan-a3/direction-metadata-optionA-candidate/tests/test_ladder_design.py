"""Pure design contracts: these tests require no model or empirical scoring."""
import copy
import json

import numpy as np
import pytest

from component_analysis import ladder_design as ld


def row(rid='x', condition='D', split='test', variant='audit'):
    streams = {}
    for stream, words in [('clean', ('true', 'false')), ('corrupt', ('false', 'true'))]:
        streams[stream] = {
            'tokens': [1, 2, 3, 4],
            'layout': {'role_spans': [['system', 0, 2], ['user', 2, 4]],
                       'content_spans': [['facts', 2, 3], ['request', 3, 4]]},
            'honest_word': words[0], 'opposite_word': words[1], 'honest_item': 1,
            'user_request_span': [3, 4],
        }
    return {'instance_id': rid, 'condition': condition, 'split': split,
            'template_variant': variant, 'request_id': 'r0', 'streams': streams}


def pools(n=120):
    return {c: [row(str(i), c, variant='a' if i % 2 else 'b') for i in range(n)]
            for c in ld.CONDITIONS}


def test_freeze_is_deterministic_balanced_disjoint_and_records_labels():
    rows = pools()
    design = ld.freeze_design(rows, {'0', '1'}, mover_selection_ids=['0', '1'])
    again = ld.freeze_design({c: list(reversed(rs)) for c, rs in rows.items()}, {'1', '0'}, mover_selection_ids=['0', '1'])
    assert design == again
    assert len(design['assessment_ids']) == 100
    assert not set(design['assessment_ids']) & {'0', '1'}
    assert design['mover_selection_ids'] == ['0', '1']
    assert design['sample']['marginals']['template_variant'] == {'a': 50, 'b': 50}
    assert design['label_convention']['D']['condition_correct'] == 'opposite'
    assert design['label_convention']['H']['condition_correct'] == 'honest'
    assert design['label_convention']['H']['canonical_direction'] == 'opposite-minus-honest'
    assert len({design['hashes'][k] for k in ('selection', 'assessment', 'bank')}) == 3
    json.dumps(design, allow_nan=False)


def test_sampling_intersects_conditions_without_correctness_filtering():
    rows = pools(110)
    rows['I'].pop()
    rows['D'][4]['baseline_correct'] = False
    design = ld.freeze_design(rows, {'0'}, mover_selection_ids=['0'], n=108)
    assert '109' not in design['assessment_ids']
    assert '4' in design['assessment_ids']
    with pytest.raises(ValueError, match='insufficient'):
        ld.freeze_design(rows, {'0'}, mover_selection_ids=['0'], n=109)


@pytest.mark.parametrize('damage', ['missing_id', 'duplicate', 'missing_condition', 'empty_selection'])
def test_invalid_ids_fail_before_any_intersection(damage):
    rows = pools(5)
    selection = {'0'}
    if damage == 'missing_id':
        del rows['D'][-1]['instance_id']
        rows['I'].pop()  # Broken row would be outside the join.
    elif damage == 'duplicate':
        rows['D'].append(copy.deepcopy(rows['D'][-1]))
    elif damage == 'missing_condition':
        del rows['F']
    else:
        selection = set()
    with pytest.raises(ValueError):
        ld.freeze_design(rows, selection, mover_selection_ids=['0'], n=2)


def test_optional_resample_absence_does_not_block_required_twins():
    design = ld.freeze_design(pools(5), {'0'}, mover_selection_ids=['0'], n=2)
    twins = [d for d in design['donors'] if d['operation'] == 'h_twin' and d['recipient_condition'] == 'I']
    assert twins and all(d['supported'] and d['donor_condition'] == 'user_neutral' for d in twins)
    optional = [d for d in design['donors'] if d['operation'] == 'independent_resample']
    assert optional and all(not d['supported'] for d in optional)
    assert design['independent_donor_seeds'] == [101, 102, 103]


def test_mover_screen_boundary_joint_positivity_and_mlps_untouched():
    keys = [('head', 1, 0), ('head', 1, 1), ('head', 1, 2), ('mlp', 2, 0)]
    clean = np.array([[1, 3, 1], [1, 3, 1], [1, 3, 1], [0, -1, -9.]])
    swap = np.array([[1, 0, 1], [1, 3, 1], [1, 3, 1], [0, 3, 1.]])
    out = ld.choose_mover_candidates(keys, clean, swap, ['a', 'b', 'c', 'd'])
    assert out['removed_keys'] == [['head', 1, 0]]
    assert out['rankings'][0]['key'] == ['head', 1, 1]
    assert out['rankings'][0]['both_positive_count'] == 2
    assert out['rankings'][1]['both_positive_count'] == 3
    assert ['mlp', 2, 0] in out['remaining_keys']
    assert out['interpretation'] == 'answer-contribution candidates; copying not validated'


def test_empty_screen_is_explicit_duplicate_and_bad_shapes_rejected():
    out = ld.choose_mover_candidates([('head', 1, 0)], [[0]], [[1]], ['a'])
    assert out['removed_keys'] == [] and out['duplicate_group']
    with pytest.raises(ValueError):
        ld.choose_mover_candidates([('head', 1, 0)], [[1]], [[1]], ['a', 'b'])
    with pytest.raises(ValueError):
        ld.choose_mover_candidates([('head', 1, 0)], [[float('nan')]], [[1]], ['a'])
    with pytest.raises(ValueError):
        ld.choose_mover_candidates([('head', 1, 0)], [[1], [1]], [[1], [1]], ['a', 'a'])


def test_item_swap_uses_own_condition_full_unpadded_opposite_stream():
    r = row(condition='I')
    r['streams']['corrupt']['tokens'] = [5, 6, 7, 8]
    out = ld.donor_plan(r, [row(condition='H')], operation='item_swap', stream='clean', seed=1)
    assert out['donor_condition'] == 'I' and out['donor_stream'] == 'corrupt'
    assert out['recipient_positions'] == out['donor_positions'] == [0, 1, 2, 3]
    assert out['covered_positions'] == out['requested_positions'] == 4


def test_twins_are_same_instance_same_stream_h_derived_and_h_is_noop():
    r = row(condition='I')
    twin = row(condition='user_neutral')
    twin['streams']['clean']['tokens'][0] = 8
    out = ld.donor_plan(r, [twin], operation='h_twin', stream='clean', seed=1)
    assert out == ld.donor_plan(r, [twin], operation='h_twin', stream='clean', seed=999)
    assert out['supported'] and out['donor_condition'] == 'user_neutral' and out['donor_id'] == 'x'
    assert not ld.donor_plan(r, [row(condition='H')], operation='h_twin', stream='clean', seed=1)['supported']
    noop = ld.donor_plan(row(condition='H'), [], operation='h_twin', stream='corrupt', seed=1)
    assert noop['supported'] and noop['degenerate'] and noop['no_op']


@pytest.mark.parametrize('damage', ['absent', 'length', 'boundary'])
def test_equal_padding_or_length_never_invents_alignment(damage):
    r, donor = row(condition='F'), row(condition='H')
    donor['streams']['clean']['tokens'][0] = 99
    if damage == 'absent':
        del donor['streams']['clean']['layout']
    elif damage == 'length':
        donor['streams']['clean']['tokens'].append(0)
    else:
        donor['streams']['clean']['layout']['content_spans'][0][2] = 4
    out = ld.donor_plan(r, [donor], operation='h_twin', stream='clean', seed=1)
    assert not out['supported'] and out['unsupported_reason']
    assert out['covered_positions'] == 0 and out['donor_positions'] == []


def test_f_identity_is_marked_and_valid_changed_prompt_supported():
    r, d = row(condition='F'), row(condition='H')
    assert ld.donor_plan(r, [d], operation='h_twin', stream='clean', seed=1)['degenerate']
    d['streams']['clean']['tokens'][0] = 9
    assert ld.donor_plan(r, [d], operation='h_twin', stream='clean', seed=1)['supported']


def test_independent_resample_sorted_eligibility_excludes_self_and_matches_words():
    r = row(condition='I')
    ds = [row(i, 'user_neutral', 'train') for i in ['x', 'z', 'a', 'bad']]
    ds[-1]['streams']['clean']['honest_word'] = 'wrong'
    out = ld.donor_plan(r, ds, operation='independent_resample', stream='clean', seed=101)
    assert out == ld.donor_plan(r, ds[::-1], operation='independent_resample', stream='clean', seed=101)
    assert out['eligible_ids'] == ['a', 'z'] and out['donor_id'] in ['a', 'z']
    assert not ld.donor_plan(r, ds[:1], operation='independent_resample', stream='clean', seed=101)['supported']
    ds[1]['request_id'] = 'other'
    ds[2]['streams']['clean']['user_request_span'] = [2, 4]
    assert not ld.donor_plan(r, ds, operation='independent_resample', stream='clean', seed=101)['supported']


def test_bank_and_optional_donors_are_disjoint_from_selection_and_assessment():
    ps = pools(5)
    for c in ld.CONDITIONS:
        ps[c].append(row('bank', c, 'train'))
    out = ld.freeze_design(ps, {'0'}, mover_selection_ids=['0'], n=2)
    assert out['bank_ids'] == ['bank']
    for d in out['donors']:
        if d['operation'] == 'independent_resample' and d['supported']:
            assert d['donor_id'] == 'bank'
    ps['H'].append(row('0', 'H', 'validation'))
    with pytest.raises(ValueError, match='duplicate|split'):
        ld.freeze_design(ps, {'0'}, mover_selection_ids=['0'], n=2)


def test_deciding_groups_are_exact_recorded_lists():
    readings = {'rab': {t: {'deciding_numbers': {'members': ['head.9.1', 'mlp.3.0']}}
                        for t in ('far', 'sdr', 'ser')}}
    out = ld.recorded_groups(readings)
    assert out['far']['members'] == [['head', 9, 1], ['mlp', 3, 0]]
    assert out['sdr']['descriptive'] and not out['far']['descriptive']
    with pytest.raises(ValueError):
        ld.recorded_groups({'rab': {'far': {'deciding_numbers': {'members': ['nonsense']}}}})


def test_source_split_conflict_is_rejected_even_on_excluded_ids():
    ps = pools(5)
    ps['I'][0]['split'] = 'train'
    with pytest.raises(ValueError, match='split'):
        ld.freeze_design(ps, {'0'}, mover_selection_ids=['0'], n=2)


def test_twin_labels_and_request_provenance_must_match():
    recipient, donor = row(condition='D'), row(condition='H')
    donor['streams']['clean']['honest_item'] = 2
    assert not ld.donor_plan(recipient, [donor], operation='h_twin', stream='clean', seed=1)['supported']
    recipient, donor = row(condition='I'), row(condition='user_neutral')
    donor['request_id'] = 'another-request'
    assert not ld.donor_plan(recipient, [donor], operation='h_twin', stream='clean', seed=1)['supported']


def test_independent_request_span_must_be_a_valid_unpadded_boundary():
    recipient, donor = row(condition='I'), row('other', 'user_neutral', 'validation')
    recipient['streams']['clean']['user_request_span'] = [3, 99]
    donor['streams']['clean']['user_request_span'] = [3, 99]
    assert not ld.donor_plan(recipient, [donor], operation='independent_resample', stream='clean', seed=101)['supported']


def test_noop_cannot_supply_a_collateral_gate():
    out = ld.donor_plan(row(condition='H'), [], operation='h_twin', stream='clean', seed=1)
    assert out['no_op'] and out['degenerate'] and not out['gate_valid']


def test_d_twin_and_independent_h_donor_keep_the_recipient_stream():
    recipient, donor = row(condition='D'), row(condition='H')
    donor['streams']['corrupt']['tokens'][0] = 9
    out = ld.donor_plan(recipient, [donor], operation='h_twin', stream='corrupt', seed=1)
    assert out['donor_id'] == 'x' and out['donor_stream'] == 'corrupt' and out['donor_condition'] == 'H'
    donor['instance_id'], donor['split'] = 'different', 'validation'
    assert ld.donor_plan(recipient, [donor], operation='independent_resample', stream='corrupt', seed=101)['supported']


def test_bad_component_key_is_rejected_before_screening():
    with pytest.raises(ValueError, match='component'):
        ld.choose_mover_candidates([('unknown', 1, 1)], np.empty((1, 0)), np.empty((1, 0)), ['a'])


def test_mover_selection_can_be_narrower_than_union_assessment_exclusion():
    out = ld.freeze_design(pools(8), {'0', '1', '2'}, n=3, mover_selection_ids=['1', '0'])
    assert out['mover_selection_ids'] == ['1', '0']
    assert not set(out['assessment_ids']) & {'0', '1', '2'}
    with pytest.raises(ValueError, match='selection'):
        ld.freeze_design(pools(8), {'0'}, n=3, mover_selection_ids=['7'])
    with pytest.raises(ValueError, match='selection'):
        ld.freeze_design(pools(8), {'0', 'missing'}, n=3, mover_selection_ids=['missing'])
    with pytest.raises(ValueError, match='selection'):
        ld.freeze_design(pools(8), {'0'}, n=3, mover_selection_ids=['0', '0'])


def test_independent_recipient_draws_do_not_reuse_one_rng_choice():
    donors = [row('donor' + str(i), 'H', 'train') for i in range(10)]
    plans = [ld.donor_plan(row('recipient' + str(i)), donors,
                          operation='independent_resample', stream='clean', seed=101)
             for i in range(20)]
    assert len({p['donor_id'] for p in plans}) > 1
    assert len({p['draw_seed'] for p in plans}) == 20


def test_sample_indices_reconstruct_ids_only_with_recorded_eligible_pool():
    ps = pools(5)
    out = ld.freeze_design(ps, {'0'}, mover_selection_ids=['0'], n=2)
    sample = out['sample']
    assert sample['join_on'] == 'instance_id'
    assert 'split_indices' not in sample
    assert sample['eligible_pool_ids'] == ['1', '2', '3', '4']
    assert [sample['eligible_pool_ids'][i] for i in sample['eligible_pool_indices']] == out['assessment_ids']
    assert all('split_indices' not in s for s in sample['strata'])
    reversed_out = ld.freeze_design({c: rs[::-1] for c, rs in ps.items()}, {'0'},
                                    mover_selection_ids=['0'], n=2)
    assert reversed_out == out
