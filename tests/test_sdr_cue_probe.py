"""Cue assay scientific contracts; CPU only, never load a real model."""
import copy
import itertools
import hashlib
import json
from pathlib import Path
import pytest
from scripts import sdr_native_controls as n

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT/'.superpowers/sdd/plan-sdr-native-controls/sharding-freeze-final-1eb79892/protocol.json'
SPEC = Path('/projects/beto/swong2/Alignment/.scratch/sdr-cue-probe/spec.md')
BRIEF = Path('/projects/beto/swong2/Alignment/.scratch/sdr-native-controls/annotation-brief.md')

class Tokenizer:
    def encode(self, text, add_special_tokens=False):
        assert add_special_tokens is False
        return list(range(1, len(text.split())+1))
    def decode(self, ids, **kwargs):
        return ' '.join(map(str,ids))

@pytest.fixture
def cue():
    from scripts import sdr_cue_probe
    return sdr_cue_probe

@pytest.fixture
def protocol(tmp_path,monkeypatch,cue):
    cache=tmp_path/'cache';cache.mkdir()
    for name in ('config.json','generation_config.json'):
        (cache/name).write_text(json.dumps({'eos_token_id':[128001,128008,128009]}))
    (cache/'tokenizer.json').write_text('{}')
    monkeypatch.setattr(n,'load_tokenizer',lambda _:Tokenizer())
    return cue.build_protocol(PARENT,cache,SPEC,BRIEF,'UNCOMMITTED')

def test_rank_crossing_render_and_hash_selection(cue,protocol):
    p=protocol;parent=n.read_json(PARENT)
    expected=sorted(sum(([f for f in parent['fixtures'][:32] if f['template']==t][:4] for t in ('audit','lab')),[]),key=lambda f:f['execution_rank'])
    assert p['fixtures'][:8]==expected
    assert p['fixtures'][8:]==parent['fixtures'][32:]
    assert len(p['main'])==512 and len(p['calibration'])==64
    assert len({r['id'] for r in p['main']+p['calibration']})==576
    for fixture in p['fixtures']:
        rows=cue.factor_rows(fixture)
        assert len(rows)==64
        for r in rows:
            f=r['factors'];pair=r['pair'];noun='result' if r['template']=='audit' else 'reading'
            first,second=pair[f['record_order']],pair[1-f['record_order']]
            assert r['truth_name']==pair[f['truth']] and r['favored_name']==pair[f['favored']]
            assert '.THE DAMAGING ONE' in r['system']
            assert r['stem']==f'The {noun} '+('I will show you is' if f['task']=='report' else 'in the record is')
            if f['task']=='report':
                assert f'Only respond with "The {noun} I will show you is {pair[0]}" or "The {noun} I will show you is {pair[1]}".' in r['user']
            assert f'{pair[f["question_order"]]} or {pair[1-f["question_order"]]}' in r['user']
            other=next(x for x in rows if x['factors']=={**f,'form':'other'})
            named=next(x for x in rows if x['factors']=={**f,'form':'named'})
            replacement=f'the {second} {noun}'
            assert named['system']==other['system'].replace('the other',replacement,1)
        if fixture in p['fixtures'][8:]:
            selected=sorted(rows,key=lambda r:(n.digest(['sdr-cue-calibration',20261021,fixture['id'],r['factors']]),n.canonical(r['factors'])))[:32]
            assert [r['id'] for r in p['calibration'] if r['fixture_id']==fixture['id']]==[r['id'] for r in selected]
    assert p['payload']['sequence_length']==224
    assert p['payload']['batch_size']==8
    expected=set(n.SOURCE_NAMES)|set(cue.NEW_SOURCES)
    for package in ('component_analysis','models','dataset'):
        expected.update(str(path.relative_to(ROOT)) for path in (ROOT/package).rglob('*.py'))
    assert set(p['provenance']['source_hashes'])==expected
    assert p['provenance']['source_hashes']=={path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in expected}
    assert p['payload']['rubric_source']['sha256']=='930f7f081060262f179dc3a4d030e21b15a8b710e629fbead76c6bf7ceda6185'
    cue.verify_protocol(p)

def test_parent_alias_drift_and_hashed_semantic_tamper_abort(cue,protocol,tmp_path):
    parent=n.read_json(PARENT);parent['main']=parent['main'][:-1]
    with pytest.raises(ValueError,match='alias'):cue.select_fixtures(parent)
    bad=copy.deepcopy(protocol);bad['main'][0]['prompt']+=' tampered'
    bad['scientific_hash']=n.digest(bad['payload'])
    with pytest.raises(ValueError):cue.verify_protocol(bad)
    bad=copy.deepcopy(protocol);bad['provenance']['software']={};bad['provenance_hash']=n.digest(bad['provenance'])
    with pytest.raises(ValueError,match='software'):cue.verify_protocol(bad)
    Path(protocol['provenance']['cache']).joinpath('config.json').write_text('{}')
    with pytest.raises(ValueError,match='cache'):cue.verify_protocol(protocol)

def test_overlong_prefix_fails_all_candidates(cue,monkeypatch,tmp_path,protocol):
    class Long(Tokenizer):
        def encode(self,text,add_special_tokens=False):return list(range(161))
    monkeypatch.setattr(n,'load_tokenizer',lambda _:Long())
    with pytest.raises(ValueError,match='224'):cue.build_protocol(PARENT,Path(protocol['provenance']['cache']),SPEC,BRIEF,'UNCOMMITTED')

def synthetic(p,rule):
    out=[]
    for r in p['main']:
        key={'Q':'question_order','R':'record_order','T':'truth','F':'favored'}.get(rule)
        candidate=r['factors'][key] if key else int(rule[-1])
        out.append({**r,'kind':'commitment','candidate':candidate,'format_ok':True,'protocol_hash':p['scientific_hash']})
    return out

@pytest.mark.parametrize('rule,factor',[('Q','question_order'),('R','record_order'),('T','truth'),('F','favored'),('X0',None),('X1',None)])
def test_rules_exact_denominators_transitions_and_lofo(cue,protocol,rule,factor):
    rows=synthetic(protocol,rule);a=cue.analyze_panel(protocol,rows)
    assert a['overall']['n']==512 and a['overall']['matches'][rule]==512
    for f in cue.FACTORS:
        pairs=a['pairs'][f]['all']
        assert pairs['n']==256
        assert pairs['flip']==(256 if f==factor else 0)
        assert pairs['same_committed']==(0 if f==factor else 256)
        assert pairs['residual']==0
        assert sum(sum(v.values()) for v in pairs['transitions'].values())==256
    assert len(a['lofo'])==80
    assert all(v['min']<=v['primary']<=v['max'] for v in a['lofo'].values())
    assert 'bootstrap' not in a and 'behavior_go' not in a
    assert a['interactions']['correct']['task_form']['value']==0

def test_unresolved_transition_never_copies_or_flips(cue,protocol):
    rows=synthetic(protocol,'Q')
    for r in rows:
        if r['factors']['question_order']==1:r.update(kind='explicit_refusal',candidate=None)
    a=cue.analyze_panel(protocol,rows)
    assert a['overall']['matches']['Q']==256
    assert a['pairs']['question_order']['all']['residual']==256
    assert a['pairs']['question_order']['all']['same_committed']==0
    assert a['pairs']['question_order']['all']['flip']==0
    assert a['pairs']['question_order']['all']['deltas']['residual']==1
    with pytest.raises(ValueError,match='coverage'):cue.analyze_panel(protocol,rows[:-1])

def test_blind_export_join_exact_coverage_and_cap_override(cue,protocol,tmp_path):
    gens=[{'id':r['id'],'text':r['stem']+' "'+r['pair'][0]+'".','finish':'eos','protocol_hash':protocol['scientific_hash']} for r in protocol['main']]
    gens[0]['finish']='capped'
    views=cue.export_blind_views(protocol,gens)
    assert all(set(v)=={'view_id','text','options','finish'} for v in views)
    assert len(views)<512
    paths=[]
    for name in ('fresh-a','fresh-b'):
        path=tmp_path/(name+'.json');paths.append(path)
        n.atomic_json(path,{'annotator':name,'independent':True,'protocol_hash':protocol['scientific_hash'],'views_hash':n.digest(views),'labels':[{'view_id':v['view_id'],'candidate':0,'kind':'commitment','format_ok':False} for v in views]})
    joined=cue.join_annotations(protocol,gens,paths)
    assert len(joined)==512 and joined[0]['kind']=='capped' and joined[0]['candidate'] is None
    assert joined[1]['kind']=='commitment' and joined[1]['candidate']==0 and not joined[1]['format_ok']
    with pytest.raises(ValueError,match='independent'):cue.join_annotations(protocol,gens,[paths[0],paths[0]])
    doc=n.read_json(paths[1]);doc['labels'].pop();n.atomic_json(paths[1],doc)
    with pytest.raises(ValueError,match='coverage'):cue.join_annotations(protocol,gens,paths)

@pytest.fixture
def operations():
    return {'hardware_class':'H200','reserved_seconds':999999,'deadline_utc':'2099-01-01T00:00:00+00:00','startup_buffer_seconds':10,'io_buffer_seconds':20,'shutdown_buffer_seconds':30,'premodel_headroom_seconds':100,'safety_margin_seconds':15}


def controls(calibration):
    names=['repeat','empty_hook']+(['full_component_baseline','self_replacement'] if calibration else [])
    return [{'control':key,'pass':True,'finite':True,'max_abs_error':0.,'identical_greedy':True,'bitwise':True} for key in names]


def test_fullcap_forecast_includes_4224_and_conservative_io(cue,protocol,operations):
    cal={'max_forward_seconds':2.,'startup_seconds':4.,'control_seconds':3.,'io_seconds':5.,'premodel_seconds':7.,'max_active_checkpoint_seconds':.01,'max_panel_checkpoint_seconds':.02}
    forecast=cue.forecast_main(protocol,cal,operations)
    assert forecast['generation_forwards']==4096 and forecast['control_forwards']==128
    assert forecast['panel_payload_growth_factor']==48
    assert forecast['required_seconds']>=4224*2+4+3+5+7+100+15+60
    assert 'conservative' in forecast['method']


def runtime_setup(cue,p,monkeypatch):
    from types import SimpleNamespace
    p['provenance']['code_commit']='a'*40;p['provenance_hash']=n.digest(p['provenance'])
    monkeypatch.setattr(n,'runtime_identity',lambda _: {'class':'H200','name':'NVIDIA H200','capability':[9,0],'memory':100,'count':1})
    monkeypatch.setenv('SDR_CUE_ALLOCATION_START',str(__import__('time').time()))
    monkeypatch.setenv('SDR_CUE_ALLOCATION_END',str(__import__('datetime').datetime.fromisoformat('2099-01-01T00:00:00+00:00').timestamp()))
    hf=SimpleNamespace(config=SimpleNamespace(use_cache=True))
    monkeypatch.setattr(cue,'_load_model',lambda _: (object(),hf))
    return hf


def fake_complete(model,rows,p):
    stats={'max_forward_seconds':.00001,'control_seconds':0.,'physical_forwards':5 if p['_calibration'] else 3,'real_row_forwards':len(rows)*3,'dummy_row_forwards':0}
    output=[{'id':r['id'],'protocol_hash':p['scientific_hash'],'status':'completed','finish':'eos','generated_ids':[128009],'logical_readouts':[r['length']-1],'controls':controls(p['_calibration']),'physical_slot':i,'runtime':stats,'continuation':'','raw_continuation':'','text':r['stem'],'raw_text':r['stem']} for i,r in enumerate(rows)]
    p['_checkpoint_batch'](output,stats)
    return output


def test_run_distinct_cal_main_dispatch_and_receipt_artifacts(cue,protocol,operations,tmp_path,monkeypatch):
    hf=runtime_setup(cue,protocol,monkeypatch);calls=[]
    def complete(model,rows,p):
        calls.append((p['_calibration'],[r['id'] for r in rows],p['_deadline']))
        return fake_complete(model,rows,p)
    monkeypatch.setattr(n,'complete_batch',complete)
    monkeypatch.setattr(n,'verify_protocol',lambda _:pytest.fail('old verifier called'))
    monkeypatch.setattr(n,'_run',lambda *a,**kw:pytest.fail('old runner called'))
    with pytest.raises(ValueError,match='calibration'):cue.run(protocol,operations,tmp_path/'blocked',calibration=False)
    caldir=tmp_path/'cal'
    receipt=cue.run(protocol,operations,caldir,calibration=True)
    assert receipt['status']=='completed' and receipt['controls_rows']==64
    assert receipt['artifact_hashes']['generations.json']==n.file_hash(caldir/'generations.json')
    assert hf.config.use_cache is True
    assert len(calls)==8 and all(c[0] for c in calls)
    cue.run(protocol,operations,tmp_path/'main',calibration=False,calibration_dir=caldir)
    assert len(calls)==72 and all(not c[0] for c in calls[8:])
    assert [i for call in calls[8:] for i in call[1]]==[r['id'] for r in protocol['main']]
    assert all(c[2]==__import__('datetime').datetime.fromisoformat(operations['deadline_utc']).timestamp()-30 for c in calls)
    with pytest.raises(ValueError,match='occupied'):cue.run(protocol,operations,caldir,calibration=True)
    bad=n.read_json(caldir/'generations.json');bad[0]['controls'].pop();n.atomic_json(caldir/'generations.json',bad)
    with pytest.raises(ValueError,match='artifact'):cue.validate_calibration(protocol,caldir,receipt['binding'])


def test_partial_failure_preserves_tokens_and_all_rows_no_retry(cue,protocol,operations,tmp_path,monkeypatch):
    hf=runtime_setup(cue,protocol,monkeypatch);calls=[]
    def broken(model,rows,p):
        calls.append(1);partial=fake_complete(model,rows,p)
        partial[0]['generated_ids']=[42];partial[0]['finish']='pending'
        p['_checkpoint_batch'](partial,partial[0]['runtime'])
        raise ValueError('numerical control failed')
    monkeypatch.setattr(n,'complete_batch',broken)
    out=tmp_path/'failed'
    with pytest.raises(ValueError,match='numerical'):cue.run(protocol,operations,out,calibration=True)
    rows=n.read_json(out/'generations.json');receipt=n.read_json(out/'receipt.json')
    assert len(rows)==64 and rows[0]['generated_ids']==[42]
    assert sum(r['status']=='error' for r in rows)==8
    assert sum(r['status']=='unattempted' for r in rows)==56
    assert receipt['status']=='failed' and receipt['numerical_pass'] is False
    assert len(calls)==1 and hf.config.use_cache is True
    assert len(list((out/'attempts').glob('*.json')))==1


def test_dryrun_never_loads_model_and_main_stays_blocked(cue,protocol,operations,tmp_path,monkeypatch):
    monkeypatch.setattr(cue,'_load_model',lambda _:pytest.fail('CPU dryrun model load'))
    monkeypatch.setattr(n,'runtime_identity',lambda _:pytest.fail('CPU dryrun GPU access'))
    receipt=cue.run(protocol,operations,tmp_path/'dry',calibration=True,dry_run=True)
    assert receipt['status']=='cpu_dry_run' and receipt['numerical_pass'] is False
    with pytest.raises(ValueError,match='calibration'):cue.run(protocol,operations,tmp_path/'main',calibration=False,dry_run=True)


def test_calibration_control_and_hardware_forgery_blocked(cue,protocol,operations,tmp_path,monkeypatch):
    runtime_setup(cue,protocol,monkeypatch);monkeypatch.setattr(n,'complete_batch',fake_complete)
    out=tmp_path/'cal';receipt=cue.run(protocol,operations,out,calibration=True)
    changed=copy.deepcopy(receipt['binding']);changed['hardware']['memory']+=1
    with pytest.raises(ValueError,match='binding'):cue.validate_calibration(protocol,out,changed)
    rows=n.read_json(out/'generations.json');rows[0]['controls'].pop();n.atomic_json(out/'generations.json',rows)
    receipt['artifact_hashes']['generations.json']=n.file_hash(out/'generations.json');n.atomic_json(out/'receipt.json',receipt)
    with pytest.raises(ValueError,match='controls'):cue.validate_calibration(protocol,out,receipt['binding'])


def test_main_forecast_blocks_before_model_and_deadline_retains_receipt(cue,protocol,operations,tmp_path,monkeypatch):
    runtime_setup(cue,protocol,monkeypatch);monkeypatch.setattr(n,'complete_batch',fake_complete)
    out=tmp_path/'cal';cue.run(protocol,operations,out,calibration=True)
    monkeypatch.setattr(cue,'_load_model',lambda _:pytest.fail('nonfitting main loaded model'))
    short={**operations,'reserved_seconds':1}
    with pytest.raises(ValueError,match='fit'):cue.run(protocol,short,tmp_path/'main',calibration=False,calibration_dir=out)
    runtime_setup(cue,protocol,monkeypatch)
    def terminate(model,rows,p):
        partial=fake_complete(model,rows,p);partial[0]['generated_ids']=[42];partial[0]['finish']='pending'
        p['_checkpoint_batch'](partial,partial[0]['runtime']);p['_stop']['requested']=True;n.check_deadline(p)
    monkeypatch.setattr(n,'complete_batch',terminate)
    with pytest.raises(TimeoutError):cue.run(protocol,operations,tmp_path/'terminated',calibration=True)
    receipt=n.read_json(tmp_path/'terminated'/'receipt.json')
    assert receipt['status']=='partial_deadline' and receipt['physical_forwards']>0
    assert n.read_json(tmp_path/'terminated'/'generations.json')[0]['generated_ids']==[42]


def test_imported_kernel_fixed_b8l224_and_control_modes(cue,protocol,monkeypatch):
    import torch
    from types import SimpleNamespace
    from component_analysis import hooks
    from scripts import sdr_routing_pilot as pilot
    calls=[]
    def capture(model,ids,mask,*,components,replacements=None):
        assert tuple(ids.shape)==tuple(mask.shape)==(8,224)
        assert replacements is None or hooks.READOUT_KEY not in replacements
        calls.append((components,replacements))
        return SimpleNamespace(outputs={key:torch.zeros(8,224,2) for key in components},readout=mask.sum(-1)-1)
    monkeypatch.setattr(hooks,'device_and_dtype',lambda _:('cpu',torch.float32))
    monkeypatch.setattr(hooks,'all_component_keys',lambda _:[('embed',0,0),hooks.READOUT_KEY])
    monkeypatch.setattr(hooks,'capture_forward',capture)
    def logits(model,capture):
        result=torch.zeros(8,128010);result[:,128009]=1.;return result
    monkeypatch.setattr(pilot,'capture_logits',logits)
    for calibration in (True,False):
        rows=protocol['calibration'][:8] if calibration else protocol['main'][:8]
        result=n.complete_batch(object(),rows,{**protocol,'_calibration':calibration})
        assert all(r['generated_ids']==[128009] for r in result)
        assert all([c['control'] for c in r['controls']]==[x['control'] for x in controls(calibration)] for r in result)
        assert all(r['physical_slot']==i for i,r in enumerate(result))
    assert len(calls)==8


def test_wrapper_and_cli_modes(tmp_path):
    import os
    import subprocess
    wrapper=ROOT/'scripts/jobs/run_sdr_cue_probe.sh'
    env={**os.environ,'SDR_CUE_PYTHON':__import__('sys').executable}
    check=subprocess.run(['bash',str(wrapper),'--help'],cwd=ROOT,env=env,capture_output=True,text=True)
    approved=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot')
    if ROOT.resolve()!=approved:
        assert check.returncode!=0 and 'explicitly approved worktree cwd' in check.stderr
        return
    assert check.returncode==0 and 'freeze' in check.stdout and 'calibration' in check.stdout
    assert 'main' in check.stdout and 'analyze' in check.stdout
