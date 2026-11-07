"""CPU contracts for the additive position study; never load a model or notebook."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / '.superpowers/sdd/plan-sdr-cue-circuits/freeze-final-ca41bfd/protocol.json'
SPEC = Path('/projects/beto/swong2/Alignment/.scratch/sdr-cue-followup/spec.md')

@pytest.fixture
def pos():
    path = ROOT / 'scripts/sdr_cue_positions.py'
    assert path.exists(), 'position-study runner is not implemented'
    spec = importlib.util.spec_from_file_location('position_test_module', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def frozen(pos, monkeypatch):
    parent = json.loads(PARENT.read_text())
    rows = parent['payload']['main'] + parent['payload']['calibration_pool']
    lookup = {}
    for r in rows:
        lookup[r['prompt']] = r['ids']
        for marker in ('<|start_header_id|>assistant<|end_header_id|>', '<|start_header_id|>user<|end_header_id|>'):
            cut = r['prompt'].index(marker)
            lookup[r['prompt'][:cut]] = [t for t, (a,b) in zip(r['ids'],r['offsets']) if b <= cut]
    tokenizer = SimpleNamespace(encode=lambda text, **kw: list(lookup[text]))
    monkeypatch.setattr(pos.cc, 'verify_protocol', lambda p: None)
    monkeypatch.setattr(pos.n, 'load_tokenizer', lambda cache: tokenizer)
    monkeypatch.setattr(pos.n, 'cache_hashes', lambda cache: {'fixture':'f'*64})
    monkeypatch.setattr(pos.n, 'software', lambda: {'fixture':'cpu'})
    monkeypatch.setattr(pos, 'source_hashes', lambda: {'fixture':'e'*64})
    return pos.build_protocol(PARENT, SPEC, 'd'*40)

def test_exact_parent_identity_and_new_commit(pos, frozen):
    parent = json.loads(PARENT.read_text())
    for name in ('main','pairs'):
        assert frozen['payload'][name] == parent['payload'][name]
    assert frozen['payload']['families'] == {k:parent['payload']['families'][k] for k in ('S','C_S')}
    assert all('.THE DAMAGING' in r['system'] for r in frozen['payload']['main'])
    assert frozen['provenance']['parent_commit'] == 'ca41bfdb2fd4e4c4c784eabd321ea75e41a45299'
    assert frozen['provenance']['code_commit'] == 'd'*40
    pos.verify_protocol(frozen)
    for field in ('scientific_hash','provenance_hash'):
        bad=deepcopy(frozen); bad[field]='0'*64
        with pytest.raises(ValueError): pos.verify_protocol(bad)
    with pytest.raises(ValueError): pos.build_protocol(PARENT,SPEC,frozen['provenance']['parent_commit'])

def test_exact_4224_schedule_ids_and_order(pos, frozen):
    p=frozen['payload']; assert [len(p[k]) for k in ('main','pairs','interventions','batches')]==[384,640,3840,528]
    assert [b['id'] for b in p['batches']]==[f'pb-{i:06d}' for i in range(528)]
    assert [i['id'] for i in p['interventions']]==[q['id']+':'+f+':'+s for f in ('S','C_S') for s in ('early','tail','full') for a,t in (('E','report'),('T','report'),('T','retrieval')) for q in p['pairs'] if (q['axis'],q['task'])==(a,t)]
    assert [x for b in p['batches'] for x in b['row_ids']]==[r['id'] for r in p['main']+p['interventions']]

def test_header_cut_token_alignment_and_ambiguity(pos, frozen):
    r=frozen['payload']['main'][0]; b=frozen['payload']['positions'][r['id']]
    assert r['ids'][b['b']]==128006 and r['prompt'][b['char_boundary']:].startswith('<|start_header_id|>assistant')
    token=SimpleNamespace(encode=lambda text,**kw:r['ids'][:b['b']])
    bad=deepcopy(r); bad['prompt'] += '<|start_header_id|>assistant<|end_header_id|>'
    with pytest.raises(ValueError):pos.freeze_positions(bad,token)
    bad=deepcopy(r);bad['offsets'][b['b']]=[b['char_boundary']-1,b['char_boundary']+1]
    with pytest.raises(ValueError):pos.freeze_positions(bad,token)

def test_pair_boundary_and_unchanged_prefix_contract(pos, frozen):
    p=frozen['payload']; main={r['id']:r for r in p['main']}
    for pair in p['pairs']:
        a,b=[main[pair[k+'_id']] for k in ('recipient','donor')]
        ma,mb=[p['positions'][r['id']] for r in (a,b)]
        assert (ma['b'],ma['n'])==(mb['b'],mb['n'])
        changed=[i for i,(x,y) in enumerate(zip(a['ids'],b['ids'])) if x!=y]
        assert changed==pair['changed_positions'] and len(changed)==2
        assert a['ids'][:changed[0]]==b['ids'][:changed[0]]
    bad=deepcopy(frozen);bad['payload']['positions'][p['main'][0]['id']]['b']+=1
    bad['scientific_hash']=pos.cc.digest(bad['payload'])
    with pytest.raises(ValueError):pos.verify_protocol(bad)

def test_position_partition_excludes_dummy_padding_generated(pos, frozen):
    p=frozen['payload']; rows=[{**r,'position':p['positions'][r['id']]} for r in p['main'][:3]]
    early,tail,full=[pos.position_mask(rows,s,'cpu') for s in ('early','tail','full')]
    assert torch.equal(early|tail,full) and not (early&tail).any()
    assert early[:3].any(1).all() and tail[:3].any(1).all() and not full[3:].any()
    for i,r in enumerate(rows): assert full[i].sum()==r['length'] and not full[i,r['length']:].any()

def small_rows(n=2):
    result=[]
    for i in range(n):
        indices={'early':[0,1],'tail':[2],'full':[0,1,2],'system':[0]}
        result.append(dict(id=f'r{i}',ids=[1,2,3],length=3,stem='S',family='S',position={'indices':indices,'hashes':{s:__import__('hashlib').sha256(json.dumps(x,separators=(',',':')).encode()).hexdigest() for s,x in indices.items()}}))
    return result

@pytest.fixture
def fake_forward(pos,monkeypatch):
    from component_analysis import hooks
    from scripts import sdr_routing_pilot
    calls=[]; key=('head',1,2)
    monkeypatch.setattr(hooks,'device_and_dtype',lambda m:(torch.device('cpu'),torch.float32))
    monkeypatch.setattr(hooks,'_hf',lambda m:m)
    def capture(model,ids,mask,*,components,replacements=None):
        calls.append((ids.clone(),mask.clone(),replacements))
        logits=torch.zeros(8,7)
        for i in range(8): logits[i,6 if int(mask[i].sum()) >= 3+i else 2]=1
        outputs={key:ids.float().unsqueeze(-1).expand(8,224,128).clone()}
        if replacements:
            assert hooks.READOUT_KEY not in replacements
            assert not replacements[key].positions[2:].any()
        return SimpleNamespace(outputs=outputs,logits=logits)
    monkeypatch.setattr(hooks,'capture_forward',capture)
    monkeypatch.setattr(sdr_routing_pilot,'capture_logits',lambda m,c:c.logits)
    model=SimpleNamespace(config=SimpleNamespace(use_cache=True))
    protocol={'scientific_hash':'f'*64,'payload':{'vocab_size':7,'eos':[6]},'_tokenizer':SimpleNamespace(decode=lambda ids,**kw:','.join(map(str,ids)))}
    return model,protocol,calls,key

def test_pack_write_selected_and_untouched_coordinates(pos):
    rows=small_rows(); key=('head',1,2); backing=torch.arange(8*224*256).reshape(8,224,256).float()
    capture=SimpleNamespace(outputs={key:backing[:,:,:128]})
    mask=pos.position_mask(rows,'tail','cpu'); bank=pos.pack_bank(capture,[key],rows,mask)
    value=bank[key].value
    assert value.is_contiguous() and value.untyped_storage().nbytes()==8*224*128*4
    assert value.data_ptr()!=backing.data_ptr()
    current=torch.full_like(value,-7); result=pos.cc.checked_assignment(current,bank[key])
    assert torch.equal(result[mask],value[mask]) and (result[~mask]==-7).all()
    assert (current==-7).all() and not bank[key].positions[2:].any()
    with pytest.raises(ValueError):pos.pack_bank(capture,[('readout',)],rows,mask)

def test_decode_mask_frozen_every_step_and_independent_eos(pos,fake_forward):
    model,p,calls,key=fake_forward; rows=small_rows()
    state=pos.decode_batch(model,rows,p,donor_rows=rows,family_keys=[key],site='tail')
    assert [r['generated_ids'] for r in state['rows']]==[[6],[2,6]]
    assert [r['logical_readouts'] for r in state['rows']]==[[2],[2,3]]
    assert len(state['controls'])==3 and model.config.use_cache is True
    expected=pos.position_mask(rows,'tail','cpu')
    assert all(torch.equal(c[2][key].positions,expected) for c in calls if c[2])
    assert state['captures'][0]['site']=='tail' and state['captures'][0]['position_ids']==[r['position']['hashes']['tail'] for r in rows]

def test_baseline_repeat_empty_and_per_step_patch_repeat(pos,fake_forward):
    m,p,calls,key=fake_forward; rows=small_rows()
    state=pos.decode_batch(m,rows,p)
    assert Counter(c['control'] for c in state['controls'])=={'repeat':2,'empty':2}
    assert len(calls)==4

from collections import Counter

def test_fullcap_controls_first_last_capture_self_empty(pos,fake_forward):
    m,p,calls,key=fake_forward; rows=small_rows()
    state=pos.decode_batch(m,rows,p,donor_rows=rows,family_keys=[key],site='early',stress=True)
    assert all(r['generated_ids']==[1296]*64 and r['finish']=='stress' for r in state['rows'])
    assert len(calls)==263
    assert Counter(c['control'] for c in state['controls'])=={'repeat':128,'patched_repeat':128,'empty':4,'self':4,'capture':4}
    assert [(x['step'],x['bank']) for x in state['captures']]==[(-1,'donor'),(0,'self-current'),(63,'self-current')]
    assert state['captures'][-1]['history_lengths']==[66,66]
    for c in calls:
        if c[2]: assert not c[2][key].positions[:,3:].any()

def test_system_E_noop_and_failure_stops_release(pos,fake_forward,monkeypatch):
    m,p,calls,key=fake_forward;rows=small_rows()
    receipt=pos.system_noop(m,rows,rows,p,[key])
    assert receipt['passed'] is True and len(receipt['controls'])==2
    from component_analysis import hooks
    original=hooks.capture_forward
    def broken(*a,**kw):
        c=original(*a,**kw);c.logits[0,0]=float('nan');return c
    monkeypatch.setattr(hooks,'capture_forward',broken)
    state={}
    with pytest.raises(ValueError,match='finite'):pos.decode_batch(m,rows,p,donor_rows=rows,family_keys=[key],site='full',state=state)
    assert state['error'] and len(state['rows'])==2 and m.config.use_cache is True

def test_calibration_natural_timing_excluded(pos,frozen):
    p=frozen['payload']
    assert Counter(b['phase'] for b in p['calibration_batches'])=={'forced':6,'natural':7}
    assert {(b['family'],b['site']) for b in p['calibration_batches'] if b['phase']=='natural'}=={(None,None)}|{(f,s) for f in ('S','C_S') for s in ('early','tail','full')}
    assert not {r['id'] for r in p['calibration']} & {r['id'] for r in p['main']+p['interventions']}

def baseline_terminal(pos,p,batch,binding,run_hash='a'*64,attempt_hash='b'*64,number=1):
    main={r['id']:r for r in p['payload']['main']}; rows=[];controls=[]
    for slot,identifier in enumerate(batch['row_ids']):
        original=main[identifier];r=pos.cc.generation(original,p['scientific_hash'],slot,'completed')
        r.update(generated_ids=[128009],logical_readouts=[original['length']-1],finish='eos',text=original['stem'],raw_text=original['stem'],error='')
        rows.append(r)
        for name in ('repeat','empty'):
            controls.append(dict(row_id=identifier,control=name,step=0,family='',finite=True,bitwise=True,max_abs_error=0.,identical_greedy=True,tolerance=1e-5,expected_sha256='c'*64,observed_sha256='c'*64))
    state=dict(rows=rows,controls=controls,captures=[],timings={pos.digest('baseline'):{'count':3,'cold':.1,'warm_max':.1}},error='',elapsed_seconds=1.,forward_seconds=.9,packing_seconds=0.)
    return pos.make_terminal(p,batch,state,dict(number=number,sha256=attempt_hash),binding,run_hash)

def test_corrupt_terminal_ids_masks_controls_hash_rejected(pos,frozen):
    p=frozen;b=p['payload']['batches'][0];binding={'cpu':'test'}
    terminal=baseline_terminal(pos,p,b,binding);pos.audit_batch(p,b,terminal)
    for mutation in ('hash','id','controls','extra'):
        bad=deepcopy(terminal)
        if mutation=='hash':bad['sha256']='0'*64
        else:
            v=bad['payload']
            if mutation=='id':v['rows'][0]['id']='foreign'
            elif mutation=='controls':v['controls'].pop()
            else:v['unexpected']=1
            bad['sha256']=pos.digest(v)
        with pytest.raises(ValueError):pos.audit_batch(p,b,bad)

def prepare_run(pos,p,path):
    binding={'cpu':'test'}
    run=pos.initialize_run(p,path,binding)
    batch=p['payload']['batches'][0]
    pos.publish(path/'invocations'/'invocation-test.json',pos.seal(dict(id='invocation-test',run_hash=run['sha256'],binding=binding,operations=operations(),allocation=pos._allocation(operations()),accepted={},remaining_ids=[b['id'] for b in p['payload']['batches']],forecast={},incomplete_attempts=0,wasted_attempts=[])))
    attempt=pos.begin_attempt(p,path,batch,binding,run['sha256'],'invocation-test')
    return binding,run,batch,attempt

def test_completed_terminal_skipped_only_after_full_audit(pos,frozen,tmp_path):
    directory=tmp_path/'run';binding,run,batch,attempt=prepare_run(pos,frozen,directory)
    terminal=baseline_terminal(pos,frozen,batch,binding,run['sha256'],attempt['sha256'])
    pos.commit_terminal(frozen,directory,batch,terminal)
    state=pos.verify_completed_batches(frozen,directory,binding)
    assert state['remaining_ids']==[b['id'] for b in frozen['payload']['batches'][1:]]
    assert state['accepted']=={batch['id']:terminal['sha256']}
    with pytest.raises(ValueError):pos.commit_terminal(frozen,directory,batch,terminal)
    with pytest.raises(ValueError):pos.assemble(frozen,directory)

def test_killed_attempt_resumed_as_next_number_without_overwrite(pos,frozen,tmp_path):
    path=tmp_path/'run';binding,run,batch,first=prepare_run(pos,frozen,path)
    with pytest.raises(ValueError,match='interruption'):pos.verify_completed_batches(frozen,path,binding)
    pos.record_interruption(path,batch['id'],1,'preemption',{'job_id':'CPU','state':'PREEMPTED','end_utc':'2026-01-01T00:00:00+00:00'})
    state=pos.verify_completed_batches(frozen,path,binding)
    pos.publish(path/'invocations'/'invocation-next.json',pos.seal(dict(id='invocation-next',run_hash=run['sha256'],binding=binding,operations=operations(),allocation=pos._allocation(operations()),accepted={},remaining_ids=state['remaining_ids'],forecast={},incomplete_attempts=1,wasted_attempts=[])))
    second=pos.begin_attempt(frozen,path,batch,binding,run['sha256'],'invocation-next')
    assert second['payload']['number']==2 and second['payload']['supersedes']==first['sha256']
    assert pos.read_json(path/'attempts'/f'{batch["id"]}.0001.json')==first
    pos.record_interruption(path,batch['id'],2,'numerical',{'error':'nonfinite'})
    with pytest.raises(ValueError,match='hard stop'):pos.verify_completed_batches(frozen,path,binding)

def test_atomic_terminal_crash_boundary(pos,frozen,tmp_path,monkeypatch):
    path=tmp_path/'run';binding,run,batch,attempt=prepare_run(pos,frozen,path)
    terminal=baseline_terminal(pos,frozen,batch,binding,run['sha256'],attempt['sha256'])
    monkeypatch.setattr(pos.os,'link',lambda *a,**kw:(_ for _ in ()).throw(OSError('crash before commit')))
    with pytest.raises(OSError):pos.commit_terminal(frozen,path,batch,terminal)
    assert not list((path/'terminals').glob('*.json'))

def test_flock_exclusion_and_release_after_process_exit(pos):
    import subprocess,tempfile
    with tempfile.TemporaryDirectory(dir=ROOT/'.superpowers/sdd/plan-sdr-cue-followup') as d:
        lock=Path(d)/'run.lock'
        code='import fcntl,sys; f=open(sys.argv[1],"a+"); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)'
        with pos.run_lock(lock,{'owner':'parent'}):
            child=subprocess.run([sys.executable,'-c',code,str(lock)],capture_output=True)
            assert child.returncode!=0 and b'BlockingIOError' in child.stderr
        assert subprocess.run([sys.executable,'-c',code,str(lock)]).returncode==0
        with pos.run_lock(lock,{'owner':'after-child-exit'}): pass

import sys

def fake_calibration(pos,p):
    natural={pos.cell_key(b):{'elapsed_seconds':2.,'publication_seconds':.1,'seal_seconds':.01,'forwards':5,'lengths':[2]*8} for b in p['payload']['calibration_batches'] if b['phase']=='natural'}
    return {'status':'completed','numerical_pass':True,'scientific_hash':p['scientific_hash'],'provenance_hash':p['provenance_hash'],'binding':{'cpu':'test'},'natural':natural,'forced_max_seconds':20.,'audit_seconds':.2,'startup_seconds':.5,'premodel_seconds':.2,'peak_memory_bytes':1,'terminal_hashes':{},'system_noop_passed':True}

def operations():
    from datetime import datetime,timezone,timedelta
    return dict(hardware_class='H200',reserved_seconds=10000,deadline_utc=(datetime.now(timezone.utc)+timedelta(seconds=10000)).isoformat(),startup_buffer_seconds=2,premodel_headroom_seconds=2,shutdown_buffer_seconds=2,safety_margin_seconds=2)

def test_observed_forecast_keeps_full_cap_and_all_controls(pos,frozen):
    ids=[b['id'] for b in frozen['payload']['batches']]
    f=pos.forecast_remaining(frozen,fake_calibration(pos,frozen),ids,operations())
    assert f['expected_seconds'] < f['full_cap_ceiling_seconds']
    assert f['remaining_rows']==4224 and f['remaining_batches']==528 and f['cap']==64
    assert f['full_cap_forwards']==48*66+480*129
    assert f['safe_batch_seconds']>=20
    with pytest.raises(ValueError):pos.forecast_remaining(frozen,fake_calibration(pos,frozen),ids+[ids[0]],operations())

def test_resume_binding_rejected_before_model_load(pos,frozen,tmp_path,monkeypatch):
    path=tmp_path/'run';binding,run,batch,attempt=prepare_run(pos,frozen,path)
    with pytest.raises(ValueError,match='binding'):pos.verify_completed_batches(frozen,path,{'cpu':'other'})
    assert len(list((path/'attempts').glob('*.json')))==1

def test_deadline_stop_before_batch_and_no_outcome_retry(pos,frozen,tmp_path):
    assert pos.batch_fits({'safe_batch_seconds':20}, {**operations(),'deadline_utc':'2000-01-01T00:00:00+00:00'}) is False
    path=tmp_path/'run';binding,run,batch,attempt=prepare_run(pos,frozen,path)
    term=baseline_terminal(pos,frozen,batch,binding,run['sha256'],attempt['sha256'])
    term['payload']['rows'][0]['generated_ids']=[1296]*64
    term['payload']['rows'][0]['logical_readouts']=list(range(frozen['payload']['main'][0]['length']-1,frozen['payload']['main'][0]['length']+63))
    term['payload']['rows'][0]['finish']='capped';term['payload']['timings'][pos.digest('baseline')]['count']=66;term['sha256']=pos.digest(term['payload'])
    pos.commit_terminal(frozen,path,batch,term)
    assert batch['id'] not in pos.verify_completed_batches(frozen,path,binding)['remaining_ids']

def synthetic_state(pos,p,batch):
    rows,donors=pos.batch_inputs(p,batch);state=dict(rows=[],controls=[],captures=[],timings={pos.digest(['timing',pos.cell_key(batch)]):{'count':263 if batch['phase']=='forced' else 3,'cold':.001,'warm_max':.001}},error='',elapsed_seconds=.01,forward_seconds=.005,packing_seconds=.001)
    for i,r in enumerate(rows):
        g=pos.cc.generation(r,p['scientific_hash'],i,'completed');count=64 if batch['phase']=='forced' else 1
        g.update(generated_ids=[1296]*64 if count==64 else [128009],logical_readouts=list(range(r['length']-1,r['length']-1+count)),finish='stress' if count==64 else 'eos')
        state['rows'].append(g)
        controls=[(name,step) for step in range(64) for name in ('repeat','patched_repeat')]+[(name,step) for step in (0,63) for name in ('empty','self','capture')] if count==64 else [('patched_repeat',0)] if batch['family'] else [('repeat',0),('empty',0)]
        for name,step in controls:state['controls'].append(dict(row_id=r['id'],control=name,step=step,family=batch['family'] or '',finite=True,bitwise=True,max_abs_error=0.,identical_greedy=True,tolerance=1e-5,expected_sha256='d'*64,observed_sha256='d'*64))
    if batch['family']:
        groups=[('donor',-1,donors)]+([('self-current',0,rows),('self-current',63,rows)] if batch['phase']=='forced' else [])
        for label,step,source in groups:
            site=batch['site'];mask=pos.position_mask(rows,site,'cpu')
            state['captures'].append(dict(bank=label,step=step,site=site,row_ids=[r['id'] for r in source],position_ids=[r['position']['hashes'][site] for r in source],indices=[r['position']['indices'][site] for r in source],history_lengths=[r['length']+(step if label=='self-current' else 0) for r in rows],values=[dict(key=k,shape=[8,224,128],dtype='torch.bfloat16',sha256='a'*64,positions_sha256=pos.cc.tensor_sha(mask)) for k in sorted(p['payload']['families'][batch['family']]['heads'])]))
    return state

def test_small_fake_calibration_main_resume_assembly(pos,frozen,tmp_path,monkeypatch):
    p=deepcopy(frozen);p['payload']['main']=p['payload']['main'][:16];p['payload']['interventions']=[];p['payload']['pairs']=[];p['payload']['batches']=p['payload']['batches'][:2];p['scientific_hash']=pos.digest(p['payload'])
    monkeypatch.setattr(pos,'verify_protocol',lambda p:None)
    binding={'hardware':{'class':'H200','name':'H200','memory':999999999999},'cpu':'fixture'}
    monkeypatch.setattr(pos,'preflight',lambda p,op,**kw:(op,binding))
    model=SimpleNamespace(config=SimpleNamespace(use_cache=True,vocab_size=128256))
    monkeypatch.setattr(pos.cue,'_load_model',lambda p:(model,model))
    monkeypatch.setattr(pos.n,'load_tokenizer',lambda cache:object())
    monkeypatch.setattr(pos,'peak_memory',lambda:1)
    monkeypatch.setattr(pos,'system_noop',lambda m,rows,donors,p,keys:synthetic_noop(pos,p,rows,donors,keys))
    all_batches=p['payload']['batches']+p['payload']['calibration_batches'];by_ids={tuple(b['row_ids']):b for b in all_batches}
    def decode(m,rows,protocol,**kw):
        state=synthetic_state(pos,p,by_ids[tuple(r['id'] for r in rows)])
        if kw.get('state') is not None:kw['state'].update(state)
        return state
    monkeypatch.setattr(pos,'decode_batch',decode)
    caldir=tmp_path/'cal';result=pos.calibrate(p,operations(),caldir)
    assert result['status']=='completed' and set(result['natural'])=={'intact','S/early','S/tail','S/full','C_S/early','C_S/tail','C_S/full'}
    # Allow exactly one batch; the next allocation must retain it without retry.
    calls=[0]
    def fit(*args):calls[0]+=1;return calls[0]<=3
    monkeypatch.setattr(pos,'batch_fits',fit)
    run=tmp_path/'main';partial=pos.run_main(p,caldir,operations(),run)
    assert partial['status']=='stopped' and len(partial['accepted'])==1
    first=(run/'terminals/pb-000000.json').read_bytes()
    monkeypatch.setattr(pos,'batch_fits',lambda *a:True)
    complete=pos.run_main(p,caldir,operations(),run,resume=True)
    assert complete['status']=='completed' and len(pos.assemble(p,run))==16
    assert (run/'terminals/pb-000000.json').read_bytes()==first
    assert len(list((run/'attempts').glob('*.json')))==2
    assert len(list((run/'invocations').glob('*.json')))==2
    receipt=pos.read_json(caldir/'calibration.json');receipt['payload']['extra_unbounded_field']='x';receipt['sha256']=pos.digest(receipt['payload']);(caldir/'calibration.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError):pos.validate_calibration(p,caldir,binding)

def scientific_generations(pos,p):
    rows=pos.cc.planned_rows(p);generations=[]
    for i,r in enumerate(rows):
        g=pos.cc.generation(r,p['scientific_hash'],i%8,'completed');name=r['pair'][0]
        g.update(finish='eos',generated_ids=[128009],logical_readouts=[r['length']-1],continuation=' '+name,raw_continuation=' '+name,text=r['stem']+' '+name,raw_text=r['stem']+' '+name)
        generations.append(g)
    return generations

def synthetic_joined(pos,p):
    joined={'protocol_hash':p['scientific_hash'],'rubric_sha256':pos.cue.BRIEF_SHA,'rows':[]}
    for r in pos.cc.planned_rows(p):
        candidate=0
        if 'site' in r:candidate=int((r['family']=='S' and r['site'] in ('early','tail')) or (r['family']=='C_S' and r['site'] in ('tail','full')))
        joined['rows'].append(dict(id=r['id'],candidate=candidate,kind='commitment',format_ok=True,view_id=pos.digest(r['id']),finish='eos',text='answer',raw_text='answer'))
    return joined

def test_blind_exact_view_join_all_multiplicities(pos,frozen,tmp_path):
    generations=scientific_generations(pos,frozen);views=pos.export_views(frozen,generations)
    assert len(views)<4224 and all(set(v)=={'view_id','text','options','finish'} for v in views)
    paths=[]
    for person in ('one','two'):
        doc=dict(annotator=person,independent=True,fresh=True,protocol_hash=frozen['scientific_hash'],views_hash=pos.digest(views),rubric_sha256=pos.cue.BRIEF_SHA,labels=[dict(view_id=v['view_id'],kind='commitment',candidate=0,format_ok=True) for v in views])
        path=tmp_path/(person+'.json');path.write_text(json.dumps(doc));paths.append(path)
    joined=pos.join_annotations(frozen,generations,paths)
    assert len(joined['rows'])==4224 and len({r['id'] for r in joined['rows']})==4224
    assert {r['candidate'] for r in joined['rows']}=={0}

def test_annotation_provenance_coverage_disagreement_finish_override(pos,frozen,tmp_path):
    gens=scientific_generations(pos,frozen);gens[0]['finish']='capped';views=pos.export_views(frozen,gens);paths=[]
    for index in range(2):
        labels=[dict(view_id=v['view_id'],kind='commitment',candidate=0,format_ok=True) for v in views]
        if index:labels[0]['candidate']=1
        doc=dict(annotator=str(index),independent=True,fresh=True,protocol_hash=frozen['scientific_hash'],views_hash=pos.digest(views),rubric_sha256=pos.cue.BRIEF_SHA,labels=labels)
        path=tmp_path/f'{index}.json';path.write_text(json.dumps(doc));paths.append(path)
    with pytest.raises(ValueError):pos.join_annotations(frozen,gens,paths)
    doc['annotator']='third';doc['labels']=[dict(view_id=views[0]['view_id'],kind='commitment',candidate=1,format_ok=True)]
    path=tmp_path/'third.json';path.write_text(json.dumps(doc));paths.append(path)
    joined=pos.join_annotations(frozen,gens,paths)
    assert joined['rows'][0]['kind']=='capped' and joined['rows'][0]['candidate'] is None
    doc['protocol_hash']='0'*64;path.write_text(json.dumps(doc))
    with pytest.raises(ValueError):pos.join_annotations(frozen,gens,paths)

@pytest.fixture
def analyzed(pos,frozen):return pos.analyze_panel(frozen,synthetic_joined(pos,frozen))

def test_every_pair_family_has_base_donor_three_sites(pos,frozen,analyzed):
    audit=analyzed['row_audit'];assert len(audit)==3840
    cells=Counter((r['family'],r['pair_id']) for r in audit)
    assert len(cells)==1280 and set(cells.values())=={3}
    assert all({'recipient_category','donor_category','patch_category','position_hash','position_indices','indicators'}<=set(r) for r in audit)
    for family in ('S','C_S'):
        for site in ('early','tail','full'):
            for axis,n in (('E/report',256),('T/report',256),('T/retrieval',128)):
                assert analyzed['inventory'][family][site][axis]['overall']['n']==n

def test_factorial_components_and_outside_contrasts(pos,frozen,analyzed):
    f=analyzed['factorial']['E/report']['overall']['indicators']['X1']
    assert f['S']=={'base':0.,'early':1.,'tail':1.,'full':0.,'early-alone':1.,'tail-alone':1.,'early-given-tail':-1.,'tail-given-early':-1.,'joint':-2.}
    assert f['C_S']['joint']==0. and f['difference']['joint']==-2.
    assert f['difference']['early-alone']==1. and f['difference']['tail-given-early']==-2.
    assert analyzed['matched_outside']['early']['E/report']['overall']['X1']['difference']==1.

def test_fixture_equal_strata_reciprocal_and_alignment(pos,frozen,analyzed):
    keys=analyzed['factorial']['E/report']
    assert all(k in keys for k in ('direction=0','direction=1','template=audit','template=lab','truth=0','truth=1','example_truth_agree=True:example_X0_agree=True'))
    items=[{'recipient':{'fixture_id':'a'},'value':1},{'recipient':{'fixture_id':'a'},'value':1},{'recipient':{'fixture_id':'b'},'value':0}]
    assert pos.cc._mean_by_fixture(items,lambda x:x['value'])==.5
    assert keys['direction=0']['n']==128 and keys['direction=1']['n']==128

def test_all_nine_categories_zero_filled_transitions_triples(pos,frozen,analyzed):
    report=analyzed['inventory']['S']['early']['E/report']['overall']
    assert len(report['transitions'])==81 and len(report['triples'])==729
    assert sum(report['triples'].values())==256 and report['triples']['identity0|identity0|identity1']==256
    assert report['transitions']['capped|error_missing']==0
    joined=synthetic_joined(pos,frozen);joined['rows'][384].update(candidate=None,kind='explicit_refusal')
    result=pos.analyze_panel(frozen,joined);row=result['row_audit'][0]
    assert row['indicators']['patch']['X0']==row['indicators']['patch']['X1']==0 and row['indicators']['patch']['residual']==1

def test_natural_pairs_and_parent_full_reference_descriptive_only(pos,frozen,analyzed):
    assert [analyzed['natural'][k]['n'] for k in ('example_report','truth_report','truth_retrieval')]==[128,128,64]
    parent=json.loads((ROOT/'outputs/_analyses/sdr-cue-circuits/postprocessing-ca41bfd/joined.json').read_text())
    result=pos.analyze_panel(frozen,synthetic_joined(pos,frozen),parent_reference=parent)
    assert len(result['parent_reproducibility']['rows'])==1664
    assert result['row_audit']==analyzed['row_audit']
    parent['protocol_hash']='0'*64
    with pytest.raises(ValueError):pos.analyze_panel(frozen,synthetic_joined(pos,frozen),parent_reference=parent)

def test_actual_wrapper_dryrun_calibration_main_resume(pos,frozen,tmp_path):
    import os,subprocess
    wrapper=ROOT/'scripts/jobs/run_sdr_cue_positions.sh'
    assert wrapper.exists(),'new wrapper not implemented'
    approved=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot')
    if ROOT.resolve()!=approved:
        # Relocated checkouts exercise the actual guard; archival dryrun mode
        # remains covered below only in its explicitly approved worktree.
        result=subprocess.run(['bash',str(wrapper),'--help'],cwd=ROOT,
            env={**os.environ,'SDR_POS_PYTHON':sys.executable},capture_output=True,text=True)
        assert result.returncode!=0 and 'explicitly approved worktree cwd' in result.stderr
        assert list(tmp_path.iterdir())==[]
        return
    protocol_path=tmp_path/'protocol.json';protocol_path.write_text(json.dumps(frozen))
    op=tmp_path/'operations.json';op.write_text(json.dumps(operations()))
    shim=tmp_path/'python-shim'
    shim.write_text('#!'+sys.executable+'\nimport importlib.util,sys\ns=importlib.util.spec_from_file_location("runner",sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nm.verify_protocol=lambda p:None\nm.main(sys.argv[2:])\n')
    shim.chmod(0o700)
    env={**os.environ,'SDR_POS_PYTHON':str(shim),'SLURM_JOB_ID':'123','SLURM_JOB_START_TIME':'1792900000','SLURM_JOB_END_TIME':'1992900000'}
    for mode in ('calibration','main'):
        destination=tmp_path/(mode+'-dry')
        args=['bash',str(wrapper),mode,'--protocol',str(protocol_path),'--operations',str(op),'--output',str(destination),'--dry-run']
        if mode=='main':args+=['--calibration',str(tmp_path/'cal')]
        result=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)['status']=='cpu_dry_run' and not destination.exists()
    run=tmp_path/'resume';pos.initialize_run(frozen,run,{'cpu':'test'})
    before={str(p.relative_to(run)):p.read_bytes() for p in run.rglob('*') if p.is_file()}
    args=['bash',str(wrapper),'main','--protocol',str(protocol_path),'--operations',str(op),'--output',str(run),'--calibration',str(tmp_path/'cal'),'--dry-run','--resume']
    result=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert {str(p.relative_to(run)):p.read_bytes() for p in run.rglob('*') if p.is_file()}==before

def test_wrapper_wrong_cwd_rejected(pos,tmp_path):
    import os,subprocess
    wrapper=ROOT/'scripts/jobs/run_sdr_cue_positions.sh'
    assert wrapper.exists(),'new wrapper not implemented'
    result=subprocess.run(['bash',str(wrapper),'--help'],cwd=tmp_path,env={**os.environ,'SDR_POS_PYTHON':sys.executable},capture_output=True,text=True)
    assert result.returncode!=0 and 'approved worktree' in result.stderr

def test_allocation_deadline_binding_and_nonfit_before_model(pos,frozen,monkeypatch):
    monkeypatch.setattr(pos,'verify_protocol',lambda p:None)
    monkeypatch.setattr(pos.cue,'_load_model',lambda p:pytest.fail('nonfit must reject before model'))
    with pytest.raises(ValueError,match='cannot fit'):pos.preflight(frozen,{**operations(),'reserved_seconds':1})
    with pytest.raises(ValueError,match='Slurm'):pos.preflight(frozen,operations())
    op=operations();bound=pos.cc.bind_allocation_operations(op,allocation_start=__import__('time').time()-10,allocation_end=__import__('time').time()+30)
    assert bound['deadline_utc']==bound['allocation_end_utc'] and bound['reserved_seconds']<41
    assert bound['proposal_hash']==pos.digest(op)

def test_missing_forward_coverage_and_boolean_control_step_rejected(pos,frozen):
    batch=frozen['payload']['batches'][0];terminal=baseline_terminal(pos,frozen,batch,{'cpu':'test'})
    terminal['payload']['timings']={};terminal['sha256']=pos.digest(terminal['payload'])
    with pytest.raises(ValueError,match='forward'):pos.audit_batch(frozen,batch,terminal)
    terminal=baseline_terminal(pos,frozen,batch,{'cpu':'test'});terminal['payload']['controls'][0]['step']=False;terminal['sha256']=pos.digest(terminal['payload'])
    with pytest.raises(ValueError):pos.audit_batch(frozen,batch,terminal)

def test_empty_bank_mask_rejected(pos):
    rows=small_rows();key=('head',1,2)
    with pytest.raises(ValueError):pos.pack_bank(SimpleNamespace(outputs={key:torch.ones(8,224,128)}),[key],rows,torch.zeros(8,224,dtype=torch.bool))

def test_failed_invocation_hard_stops_resume(pos,frozen,tmp_path):
    path=tmp_path/'run';binding,run,batch,attempt=prepare_run(pos,frozen,path)
    pos.record_interruption(path,batch['id'],1,'deadline',{'error':'deadline'})
    pos.publish(path/'invocations'/'invocation-test.failure',pos.seal({'error':'nonfinite','operational':False,'partial':{}}))
    with pytest.raises(ValueError,match='hard stop'):pos.verify_completed_batches(frozen,path,binding)

def test_scheduler_receipt_must_bind_prior_job_and_eligible_state(pos,frozen,tmp_path):
    path=tmp_path/'run';binding,run,batch,attempt=prepare_run(pos,frozen,path)
    for evidence in ({'job_id':'other','state':'PREEMPTED','end_utc':'2026-01-01T00:00:00+00:00'}, {'job_id':'CPU','state':'OUT_OF_MEMORY','end_utc':'2026-01-01T00:00:00+00:00'}, {'job_id':'CPU','state':'TIMEOUT','end_utc':'2099-01-01T00:00:00+00:00'}):
        with pytest.raises(ValueError):pos.record_interruption(path,batch['id'],1,'preemption',evidence)

def test_source_parent_and_zero_offset_corruptions_fail_closed(pos,frozen,tmp_path,monkeypatch):
    original=deepcopy(frozen);monkeypatch.setattr(pos,'source_hashes',lambda:{'fixture':'0'*64})
    with pytest.raises(ValueError):pos.verify_protocol(original)
    badparent=tmp_path/'parent.json';badparent.write_text(PARENT.read_text()+' ')
    with pytest.raises(ValueError):pos.build_protocol(badparent,SPEC,'d'*40)
    row=deepcopy(frozen['payload']['main'][0]);b=frozen['payload']['positions'][row['id']]['b'];row['offsets'][b]=[0,0]
    tok=SimpleNamespace(encode=lambda text,**kw:row['ids'][:b] if text.endswith('<|eot_id|>') and 'assistant' not in text else [])
    # Complete fake prefix map for both structural headers.
    prefixes={row['prompt'][:row['prompt'].index(marker)]:row['ids'][:frozen['payload']['positions'][row['id']][key]] for marker,key in ((pos.HEADER,'b'),(pos.USER_HEADER,'user_b'))}
    tok.encode=lambda text,**kw:prefixes[text]
    assert pos.freeze_positions(row,tok)['b']==b
    row['offsets'][b+1]=[0,0]
    with pytest.raises(ValueError):pos.freeze_positions(row,tok)

def test_calibration_causal_null_cannot_be_replaced_by_pass_flag(pos,frozen):
    with pytest.raises(ValueError):pos.audit_system_noops(frozen,{f:{'passed':True} for f in ('S','C_S')})

def test_analysis_equal_fixture_weight_with_unequal_variant_counts(pos,frozen):
    p=deepcopy(frozen);fixtures=p['payload']['fixtures'][:2];ids={f['id'] for f in fixtures};first=fixtures[0]['id']
    selected=[r for r in p['payload']['main'] if r['fixture_id'] in ids and (r['fixture_id']!=first or (r['factors']['record_order']==r['factors']['question_order']==0))]
    keep={r['id'] for r in selected};pairs=[q for q in p['payload']['pairs'] if q['recipient_id'] in keep and q['donor_id'] in keep];pairids={q['id'] for q in pairs}
    p['payload'].update(main=selected,pairs=pairs,interventions=[a for a in p['payload']['interventions'] if a['pair_id'] in pairids],fixtures=fixtures)
    p['payload']['analysis']['denominators']={'E/report':40,'T/report':40,'T/retrieval':20};p['scientific_hash']=pos.digest(p['payload'])
    joined=synthetic_joined(pos,p);inputs={r['id']:r for r in pos.cc.planned_rows(p)}
    for label in joined['rows']:
        r=inputs[label['id']];label['candidate']=int(r.get('family')=='S' and r.get('site')=='early' and r['fixture_id']==first)
    result=pos.analyze_panel(p,joined)
    assert result['factorial']['E/report']['overall']['indicators']['X1']['S']['early-alone']==.5
    assert result['inventory']['S']['early']['E/report']['overall']['indicators']['X1']['patch']==.5


def synthetic_noop(pos,p,rows,donors,keys):
    mask=pos.position_mask(rows,'system','cpu');captures=[]
    for source,label in ((rows,'recipient'),(donors,'donor')):
        captures.append(dict(bank=label,step=-1,site='system',row_ids=[r['id'] for r in source],position_ids=[r['position']['hashes']['system'] for r in source],indices=[r['position']['indices']['system'] for r in source],history_lengths=[r['length'] for r in rows],values=[dict(key=k,shape=[8,224,128],dtype='torch.bfloat16',sha256='a'*64,positions_sha256=pos.cc.tensor_sha(mask)) for k in sorted(keys)]))
    return dict(passed=True,site='system',captures=captures,selected=[dict(key=k,recipient_sha256='a'*64,donor_sha256='a'*64) for k in sorted(keys)],controls=[dict(row_id=r['id'],finite=True,bitwise=True,max_abs_error=0.,identical_greedy=True,tolerance=1e-5,expected_sha256='c'*64,observed_sha256='c'*64) for r in rows])

def test_attempt_requires_bound_immutable_invocation(pos,frozen,tmp_path):
    path=tmp_path/'run';binding,run,batch,attempt=prepare_run(pos,frozen,path)
    pos.record_interruption(path,batch['id'],1,'deadline',{'error':'deadline'})
    bad=deepcopy(attempt);bad['payload']['invocation_id']='foreign';bad['sha256']=pos.digest(bad['payload'])
    # A new attempt cannot claim a nonexistent invocation, regardless of lock metadata.
    with pytest.raises(ValueError,match='invocation'):pos.begin_attempt(frozen,path,batch,binding,run['sha256'],'foreign')

def test_exact_mask_donor_head_and_current_history_receipts(pos,frozen):
    batch=frozen['payload']['batches'][48];binding={'cpu':'test'}
    terminal=pos.make_terminal(frozen,batch,synthetic_state(pos,frozen,batch),{'number':1,'sha256':'b'*64},binding,'a'*64)
    pos.audit_batch(frozen,batch,terminal)
    for field in ('indices','position_ids','row_ids','positions_sha256','head'):
        bad=deepcopy(terminal);capture=bad['payload']['captures'][0]
        if field=='indices':capture[field][0].pop()
        elif field in ('position_ids','row_ids'):capture[field][0]='foreign'
        elif field=='head':capture['values'][0]['key']=['head',31,31]
        else:capture['values'][0][field]='0'*64
        bad['sha256']=pos.digest(bad['payload'])
        with pytest.raises(ValueError):pos.audit_batch(frozen,batch,bad)
    batch=frozen['payload']['calibration_batches'][0];terminal=pos.make_terminal(frozen,batch,synthetic_state(pos,frozen,batch),{'number':1,'sha256':'b'*64},binding,'a'*64)
    terminal['payload']['captures'][-1]['history_lengths'][0]-=63;terminal['sha256']=pos.digest(terminal['payload'])
    with pytest.raises(ValueError,match='current-history'):pos.audit_batch(frozen,batch,terminal)

def test_full_vocabulary_failures_never_widen_tolerance(pos):
    expected=torch.zeros(7,dtype=torch.float32)
    for observed in (torch.zeros(8),torch.zeros(7,dtype=torch.float64),torch.tensor([float('inf')]*7),torch.tensor([float('nan')]*7),torch.tensor([0.,0.,0.,0.,0.,0.,1e-4]),torch.tensor([0.,0.,0.,0.,0.,0.,1e-6])):
        with pytest.raises(ValueError):pos.cc.compare_full(expected,observed)

def test_bounded_worst_batch_and_streamed_assembly_size(pos,frozen,tmp_path):
    batch=frozen['payload']['batches'][0];term=baseline_terminal(pos,frozen,batch,{'cpu':'test'});limits=frozen['payload']['record_bounds']['limits']
    for row in term['payload']['rows']:
        stem=row['text'];continuation='\0'*(limits['text_bytes']-len(stem.encode()))
        row.update(continuation=continuation,raw_continuation=continuation,text=stem+continuation,raw_text=stem+continuation)
    term['sha256']=pos.digest(term['payload']);pos.audit_batch(frozen,batch,term)
    assert len(pos.encoded(term))<frozen['payload']['record_bounds']['terminal_bytes']
    pos.publish(tmp_path/'bounded-batch.json',term,frozen['payload']['record_bounds']['terminal_bytes'])
    assert pos.read_json(tmp_path/'bounded-batch.json')==term
    # Count a repeated maximum generation without constructing or writing a full panel.
    size=len(pos.encoded(term['payload']['rows'][0]))
    assert 4224*(size+1)+1<=frozen['payload']['record_bounds']['generation_bytes_upper_bound']

def test_accepted_resumed_attempt_still_requires_operational_supersession_reason(pos,frozen,tmp_path):
    path=tmp_path/'run';binding,run,batch,first=prepare_run(pos,frozen,path)
    pos.record_interruption(path,batch['id'],1,'deadline',{'error':'deadline'})
    invocation=pos.read_json(path/'invocations/invocation-test.json');invocation['payload']['id']='invocation-next';invocation['sha256']=pos.digest(invocation['payload'])
    pos.publish(path/'invocations/invocation-next.json',invocation)
    second=pos.begin_attempt(frozen,path,batch,binding,run['sha256'],'invocation-next')
    second['payload']['reason']='numerical';second['sha256']=pos.digest(second['payload'])
    (path/'attempts'/f'{batch["id"]}.0002.json').write_text(json.dumps(second))
    terminal=baseline_terminal(pos,frozen,batch,binding,run['sha256'],second['sha256'],number=2)
    pos.commit_terminal(frozen,path,batch,terminal)
    with pytest.raises(ValueError,match='supersession'):pos.verify_completed_batches(frozen,path,binding)

def test_invalid_mask_preflight_preserves_use_cache(pos,fake_forward):
    model,p,calls,key=fake_forward;rows=small_rows();rows[0]['position']['indices']['tail']=[]
    with pytest.raises(ValueError):pos.decode_batch(model,rows,p,donor_rows=rows,family_keys=[key],site='tail')
    assert model.config.use_cache is True and not calls

def test_publication_measures_serialization_separately_from_write(pos,tmp_path):
    receipt=pos.publish(tmp_path/'record.json',{'bounded':'record'})
    assert set(receipt)=={'serialization_seconds','write_seconds','bytes'}
    assert receipt['serialization_seconds']>=0 and receipt['write_seconds']>=0
    assert receipt['bytes']==len((tmp_path/'record.json').read_bytes())

@pytest.mark.parametrize('entrypoint', ['preflight', 'calibration'])
def test_actual_allocation_buffers_rechecked_before_model(pos,frozen,tmp_path,monkeypatch,entrypoint):
    import time
    from datetime import datetime,timezone,timedelta
    monkeypatch.setattr(pos,'verify_protocol',lambda p:None)
    monkeypatch.setattr(pos.n,'runtime_identity',lambda op:{'class':'A100','name':'A100','memory':10**12})
    monkeypatch.setattr(pos.n,'load_tokenizer',lambda cache:object())
    monkeypatch.setattr(pos,'_device_uuid',lambda:'CPU-regression')
    calls=[]
    monkeypatch.setattr(pos.cue,'_load_model',lambda p:calls.append(p) or pytest.fail('short actual allocation reached model loader'))
    now=time.time();monkeypatch.setenv('SDR_POS_ALLOCATION_START',str(now-1110));monkeypatch.setenv('SDR_POS_ALLOCATION_END',str(now+90))
    op=dict(hardware_class='A100',reserved_seconds=1200,deadline_utc=(datetime.now(timezone.utc)+timedelta(seconds=1200)).isoformat(),startup_buffer_seconds=60,premodel_headroom_seconds=180,shutdown_buffer_seconds=60,safety_margin_seconds=60)
    with pytest.raises(ValueError,match='allocation cannot fit'):
        if entrypoint=='preflight':pos.preflight(frozen,op)
        else:pos.calibrate(frozen,op,tmp_path/'must-not-load')
    assert not calls and not(tmp_path/'must-not-load').exists()

@pytest.fixture
def final_terminal_panel(pos,frozen,tmp_path,monkeypatch):
    p=deepcopy(frozen);p['payload'].update(main=p['payload']['main'][:8],batches=p['payload']['batches'][:1],pairs=[],interventions=[]);p['scientific_hash']=pos.digest(p['payload'])
    op=operations();binding={'cpu':'final-terminal-regression','hardware':{'memory':10**12}}
    monkeypatch.setattr(pos,'preflight',lambda *a,**kw:(op,binding))
    cal=fake_calibration(pos,p);cal['binding']=binding
    monkeypatch.setattr(pos,'validate_calibration',lambda *a,**kw:cal)
    monkeypatch.setattr(pos,'batch_fits',lambda *a:True)
    monkeypatch.setattr(pos,'_allocation',lambda *a:{'job_id':'CPU-final-terminal'})
    path=tmp_path/'run';run=pos.initialize_run(p,path,binding);batch=p['payload']['batches'][0]
    pos.publish(path/'invocations/initial.json',pos.seal(dict(id='initial',run_hash=run['sha256'],binding=binding,operations=op,allocation={'job_id':'CPU-final-terminal'},accepted={},remaining_ids=[batch['id']],forecast={},incomplete_attempts=0,wasted_attempts=[])))
    attempt=pos.begin_attempt(p,path,batch,binding,run['sha256'],'initial')
    terminal=baseline_terminal(pos,p,batch,binding,run['sha256'],attempt['sha256']);pos.commit_terminal(p,path,batch,terminal)
    original={str(f.relative_to(path)):f.read_bytes() for sub in ('attempts','terminals') for f in (path/sub).glob('*.json')}
    def forbidden(*a,**kw):pytest.fail('completed resume attempted model/decoding/attempt work')
    monkeypatch.setattr(pos.cue,'_load_model',forbidden);monkeypatch.setattr(pos,'decode_batch',forbidden);monkeypatch.setattr(pos,'begin_attempt',forbidden);monkeypatch.setattr(pos.n,'load_tokenizer',forbidden);monkeypatch.setattr(pos,'peak_memory',forbidden)
    return SimpleNamespace(protocol=p,path=path,operations=op,original=original)

@pytest.mark.parametrize('assembly_published', [False,True])
def test_final_terminal_before_assembly_resume_recovers_outputs(pos,final_terminal_panel,assembly_published):
    f=final_terminal_panel;assert not(f.path/'generations.json').exists()
    if assembly_published:pos.publish(f.path/'generations.json',pos.assemble(f.protocol,f.path))
    result=pos.run_main(f.protocol,f.path/'unused-calibration',f.operations,f.path,resume=True)
    assert result['status']=='completed' and result['remaining_ids']==[] and result['numerical_pass'] is True
    assert pos.read_json(f.path/'generations.json')==pos.assemble(f.protocol,f.path)
    receipts=[pos.unseal(pos.read_json(path)) for path in (f.path/'invocations').glob('*.result')]
    assert receipts==[result] and result['invocation_hash'] and result['peak_memory_bytes']==0
    assert {str(path.relative_to(f.path)):path.read_bytes() for sub in ('attempts','terminals') for path in (f.path/sub).glob('*.json')}==f.original

def test_completed_resume_is_idempotent_and_validates_existing_assembly(pos,final_terminal_panel):
    f=final_terminal_panel
    first=pos.run_main(f.protocol,f.path/'unused-calibration',f.operations,f.path,resume=True)
    assert (f.path/'generations.json').exists()
    assembly=pos.read_json(f.path/'generations.json');(f.path/'generations.json').write_text(json.dumps(assembly,indent=2))
    before=(f.path/'generations.json').read_bytes()
    second=pos.run_main(f.protocol,f.path/'unused-calibration',f.operations,f.path,resume=True)
    assert first['status']==second['status']=='completed' and first['accepted']==second['accepted']
    assert (f.path/'generations.json').read_bytes()==before
    assert len(list((f.path/'invocations').glob('*.result')))==2
    assert {str(path.relative_to(f.path)):path.read_bytes() for sub in ('attempts','terminals') for path in (f.path/sub).glob('*.json')}==f.original

@pytest.mark.parametrize('conflict_kind', ['foreign_row','boolean_slot'])
def test_completed_resume_rejects_conflicting_assembly_without_overwrite(pos,final_terminal_panel,conflict_kind):
    f=final_terminal_panel
    if conflict_kind=='foreign_row':conflict=b'[{"id":"foreign scientific row"}]'
    else:
        rows=pos.assemble(f.protocol,f.path);rows[1]['physical_slot']=True;conflict=pos.encoded(rows)
    (f.path/'generations.json').write_bytes(conflict)
    with pytest.raises(ValueError,match='assembly'):pos.run_main(f.protocol,f.path/'unused-calibration',f.operations,f.path,resume=True)
    assert (f.path/'generations.json').read_bytes()==conflict
    assert not list((f.path/'invocations').glob('*.result'))
    assert {str(path.relative_to(f.path)):path.read_bytes() for sub in ('attempts','terminals') for path in (f.path/sub).glob('*.json')}==f.original
