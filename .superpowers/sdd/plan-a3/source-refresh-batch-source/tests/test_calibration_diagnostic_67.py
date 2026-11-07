"""CPU diagnostic plumbing only; injected evidence is never 8B/GPU evidence."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch
from component_analysis.specificity_ladder import LadderBatch

PATH = Path(__file__).resolve().parents[1]/'docs/research/specificity-ladder/tools/67-calibration-diagnostic.py'
spec = importlib.util.spec_from_file_location('diagnostic67', PATH)
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)


def batch(width=6, stream='clean'):
    return LadderBatch(['fake'], 'D', stream,
                       torch.tensor([[1,2,3]+[0]*(width-3)]),
                       torch.tensor([[1,1,1]+[0]*(width-3)]),
                       torch.tensor([2]), torch.tensor([4]), torch.tensor([5]),
                       torch.tensor([4]), [{}], 'far_v2')


def test_resize_preserves_unmasked_tokens_masks_and_readouts():
    original = batch()
    for width in (3,6,9):
        got = diag.resize(original,width)
        assert diag.geometry(got)['padded_width'] == width
        assert got.input_ids[0,:3].tolist() == [1,2,3]
        assert got.attention_mask.sum() == 3
        assert got.readout.tolist() == [2]
    with pytest.raises(ValueError,match='truncation'):
        diag.resize(original,2)
    assert original.input_ids.shape[1] == 6


def test_nonfinite_evidence_is_json_safe_and_not_a_pass():
    got = diag.comparison(torch.tensor([[float('nan'),float('inf'),1.]]), torch.zeros(1,3))
    assert not got['finite'] and not got['allclose']
    assert got['max_abs_error'] == 1
    json.dumps(got, allow_nan=False)
    assert diag.comparison(torch.ones(1,3),torch.ones(1,3))['allclose']
    assert not diag.comparison(torch.ones(1,3),torch.ones(1,3)+0.001)['allclose']


def test_injected_control_failure_is_retained_and_noops_continue(monkeypatch):
    """Fake seam intentionally creates geometry drift, not empirical evidence."""
    from component_analysis import hooks, specificity_ladder as runner
    key = hooks.EMBED_KEY
    monkeypatch.setattr(hooks,'all_component_keys',lambda model:[key])
    calls = []
    def capture(model,b,keys,replacements=None):
        calls.append((b.stream,b.input_ids.shape[1],bool(replacements)))
        width = b.input_ids.shape[1]
        value = 1. if b.stream=='clean' else 2.
        # Fake failure depends only on width; common width removes it.
        if replacements and key in replacements:
            value = float(replacements[key].value[0,int(b.readout[0]),0])
        outputs = {key:torch.full((1,width,2),value)}
        residual = torch.full((1,2,2),value)
        logits = torch.tensor([[value+width*.01,0.,0.,0.,1.,0.]])
        return SimpleNamespace(outputs=outputs,residual=residual,logits=logits),logits
    monkeypatch.setattr(runner,'_capture',capture)
    recipient, donor = batch(6), batch(9,'corrupt')
    mapping = dict(recipient_positions=[2],donor_positions=[2])
    result,_ = diag.evaluate_pair(object(),recipient,donor,mapping)
    assert not result['donor_recovery']['fp32']['allclose']
    assert result['donor_recovery']['final_residual']['allclose']
    assert len(result['noops']) == 4
    assert all(x['production_valid'] for x in result['noops'].values())
    common,_ = diag.evaluate_pair(object(),diag.resize(recipient,9),donor,mapping)
    assert common['donor_recovery']['fp32']['allclose']
    assert len(calls) == 14


def test_pair_inventory_matches_production_order_and_parent_widths(monkeypatch):
    from component_analysis import ladder_pipeline as p
    rows = [dict(instance_id='fake',streams={s:dict(readout=2) for s in ('clean','corrupt')})]
    prepared = dict(rows={'far_v2':{'D':rows}}, designs={'far_v2':dict(assessment_ids=['fake'],donors=[
        dict(recipient_condition='D',recipient_id='fake',recipient_stream=s,
             donor_condition='D',donor_id='fake',donor_stream=('corrupt' if s=='clean' else 'clean'),operation='item_swap')
        for s in ('clean','corrupt')])})
    monkeypatch.setattr(p.design,'CONDITIONS',('D',))
    # Source lists include full pool marker to distinguish recipient/donor call.
    original_rows = prepared['rows']['far_v2']['D']
    monkeypatch.setattr(p,'batches',lambda rows,stream,batch_size:[batch(9 if rows is original_rows else 6,stream)])
    pairs = list(diag.pair_inventory(SimpleNamespace(tasks=['far_v2'],limit=4,batch_size=8),prepared))
    assert [r.stream for _,r,_,_ in pairs] == ['clean','corrupt']
    assert [(r.input_ids.shape[1],d.input_ids.shape[1]) for _,r,d,_ in pairs] == [(6,9),(6,9)]


def test_dry_run_writes_nothing_and_never_loads_weights(monkeypatch,tmp_path,capsys):
    """Injected CPU preflight tests behavior only; all identities here are fake."""
    from component_analysis import ladder_pipeline as p
    monkeypatch.setattr(p,'read_artifact',lambda path:{'rows':{},'utility':{}})
    monkeypatch.setattr(p,'validate_prepared',lambda *args:None)
    monkeypatch.setattr(p,'read_selection',lambda *args:{})
    monkeypatch.setattr(p,'validate_tokenization',lambda *args:None)
    monkeypatch.setattr(p.common,'load_tokenizer',lambda args:object())
    monkeypatch.setattr(p.common,'file_hash',lambda path:'FAKE_CPU_TEST_HASH')
    monkeypatch.setattr(p,'code_hashes',lambda:{})
    monkeypatch.setattr(p,'registries',lambda *args:{})
    monkeypatch.setattr(p,'utility_registries',lambda *args:{})
    monkeypatch.setattr(p,'grader_registry',lambda:{})
    monkeypatch.setattr(diag,'pair_inventory',lambda *args:iter([('far_v2',batch(),batch(9,'corrupt'),{})]))
    def forbidden(*args,**kwargs):
        raise AssertionError('dry-run must not load weights or write artifacts')
    monkeypatch.setattr(p,'load_model',forbidden)
    monkeypatch.setattr(p.common,'write_json',forbidden)
    out = tmp_path/'never-created'
    argv = ['--stage','score','--tasks',*p.TASKS,'--commit',diag.COMMIT,
            '--limit','4','--batch-size','8','--dry-run','--result-dir',str(out),
            '--job-stdout','fake.out','--job-stderr','fake.err']
    for name in ('artifact-root','data-root','user-control-root','work-dir','design','groups'):
        argv += ['--'+name,str(tmp_path/name)]
    assert diag.main(argv) == 0
    assert not out.exists()
    logged = json.loads(capsys.readouterr().out)
    assert logged['event']=='dry_run' and len(logged['pairs'])==1
    assert logged['manifest']['diagnostic_source_sha256']=='FAKE_CPU_TEST_HASH'
