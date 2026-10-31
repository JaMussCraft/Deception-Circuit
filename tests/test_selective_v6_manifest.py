"""CPU contract tests: catch panel drift, incorrect joins, labels and donor reuse."""
import copy
import json
from collections import Counter
from pathlib import Path

import pytest

from component_analysis import selective_v6_manifest as manifest_module
from component_analysis.selective_v6_manifest import build_manifest, load_manifest, validate_manifest

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parent
PREPARED = ROOT / '.scratch/selective-deception/transfer-v5/v2-prepared-frozen.json'
PROPOSAL = PREPARED.with_name('v2-inputs-proposal.json')
MASKS = PREPARED.with_name('frozen-masks.json')
INVERSION = REPO / 'data/datasets/sdr_v2_inversion/test/data-00000-of-00001.arrow'
DOC = INVERSION.parents[4] / 'docs/research/mechanism-analysis/inversion-control.md'


@pytest.fixture(scope='module', autouse=True)
def relocated_inversion_config():
    # Decode a test-local copy; retain original config bytes and derivation hashes.
    config_path = INVERSION.parents[1] / 'dataset_config.json'
    read_json = manifest_module._json

    def read_relocated(path):
        value = read_json(path)
        if Path(path) == config_path:
            value = copy.deepcopy(value)
            value['pool_path'] = str(REPO / 'dataset/deception_pools/v2/inversion_v2.json')
            value['clause_forms_path'] = str(REPO / 'docs/research/mechanism-analysis/clause-forms.csv')
        return value

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(manifest_module, '_json', read_relocated)
        yield


@pytest.fixture(scope='module')
def panel(relocated_inversion_config):
    return build_manifest(prepared_path=PREPARED, proposal_path=PROPOSAL, masks_path=MASKS,
                          inversion_path=INVERSION, inversion_doc_path=DOC)


def test_balanced_disjoint_panel_and_shared_fixed_donors(panel):
    rows = panel['cases']
    assert len(rows) == 176
    sdr = [r for r in rows if r['family'] == 'sdr']
    assert Counter(r['split'] for r in sdr) == {'discovery': 64, 'validation': 64}
    for split in ('discovery', 'validation'):
        subset = [r for r in sdr if r['split'] == split and r['variant'] == 'D']
        assert Counter((r['stratum']['designation_polarity'], r['stratum']['item_polarity']) for r in subset) == {
            ('identity', 1): 4, ('identity', 2): 4, ('inversion', 1): 4, ('inversion', 2): 4}
    assert len({r['scenario_key'] for r in sdr}) == 32
    for family, scenario in {(r['family'], r['scenario_key']) for r in rows}:
        group = [r for r in rows if r['family'] == family and r['scenario_key'] == scenario]
        assert len({r['split'] for r in group}) == 1
        assert len({tuple(r['donor_token_ids']) for r in group}) == 1
        assert len({r['donor_source_id'] for r in group}) == 1
        assert all(r['donor_scenario_key'] != scenario for r in group)
    assert panel['exposure']['previously_exposed'] is True
    assert panel['selection']['sdr_intersection_ids'] == 84
    assert panel['selection']['sdr_intersection_scenarios'] == 80


def test_deterministic_selection_and_requested_labels(panel):
    second = build_manifest(prepared_path=PREPARED, proposal_path=PROPOSAL, masks_path=MASKS,
                            inversion_path=INVERSION, inversion_doc_path=DOC)
    assert second == panel
    for r in panel['cases']:
        assert r['requested_target_id'] != r['alternate_answer_id']
        assert (r['requested_target_id'] == r['truthful_id']) == (r['variant'] in ('H', 'F'))
    assert {tuple(h) for h in panel['added_heads']} == {(7,31),(8,10),(13,15),(13,23),(17,27),(19,13),(20,19)}


@pytest.mark.parametrize('change', ['duplicate', 'labels', 'donor', 'mask', 'missing_variant'])
def test_rejects_corrupted_panel(panel, change):
    x = copy.deepcopy(panel)
    if change == 'duplicate': x['cases'].append(copy.deepcopy(x['cases'][0]))
    if change == 'labels': x['cases'][0]['requested_target_id'] = x['cases'][0]['alternate_answer_id']
    if change == 'donor': x['cases'][1]['donor_source_id'] = 'different'
    if change == 'mask': x['masks']['new30'].append([32, 0])
    if change == 'missing_variant': x['cases'].pop()
    with pytest.raises(ValueError): validate_manifest(x)


def test_hash_binding_detects_modified_source(panel, tmp_path):
    source = tmp_path / 'source.json'
    source.write_text('{}')
    x = copy.deepcopy(panel)
    x['sources'][str(source)] = '0' * 64
    path = tmp_path / 'panel.json'
    path.write_text(json.dumps(x))
    with pytest.raises(ValueError, match='hash'): load_manifest(path)


def test_duplicate_source_ids_rejected(tmp_path):
    prepared = json.loads(PREPARED.read_text())
    prepared['recipients'].append(prepared['recipients'][0])
    path = tmp_path / 'prepared.json'
    path.write_text(json.dumps(prepared))
    with pytest.raises(ValueError, match='duplicate'):
        build_manifest(prepared_path=path, proposal_path=PROPOSAL, masks_path=MASKS,
                       inversion_path=INVERSION, inversion_doc_path=DOC)


def test_missing_proposal_source_rejected(tmp_path):
    proposal = json.loads(PROPOSAL.read_text())
    proposal['families']['sdr']['recipients'] = []
    path = tmp_path / 'proposal.json'
    path.write_text(json.dumps(proposal))
    with pytest.raises(ValueError, match='missing'):
        build_manifest(prepared_path=PREPARED, proposal_path=path, masks_path=MASKS,
                       inversion_path=INVERSION, inversion_doc_path=DOC)


def test_donor_identity_must_match_source_key(tmp_path):
    prepared = json.loads(PREPARED.read_text())
    for donor in prepared['donors']['sdr'].values():
        donor['source_id'] = 'incorrect-source-id'
    path = tmp_path / 'prepared.json'
    path.write_text(json.dumps(prepared))
    with pytest.raises(ValueError, match='donor'):
        build_manifest(prepared_path=path, proposal_path=PROPOSAL, masks_path=MASKS,
                       inversion_path=INVERSION, inversion_doc_path=DOC)
