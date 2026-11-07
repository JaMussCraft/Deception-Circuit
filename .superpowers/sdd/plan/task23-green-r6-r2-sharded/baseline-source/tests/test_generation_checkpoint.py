"""Raw-token checkpoints retain original generation batches."""
import subprocess
import sys
from types import SimpleNamespace
import pytest
import torch
from evaluation import gen_engine as G
from evaluation.generation_checkpoint import GenerationCheckpoint, GenerationSegmentComplete


def inputs():
    ids = torch.tensor([[0,0,0,4], [0,3,4,5], [0,0,2,3], [0,6,7,8], [1,2,3,4]])
    return dict(clean_ids=ids, attention_mask=(ids != 0).long(),
                corrupt_ids=torch.cat([ids, torch.ones(5,4,dtype=torch.long)], 1),
                new_tokens=4, eos_ids=(9,), batch_size=2)


def invoke(root, monkeypatch, maximum=20, identity=None, calls=None):
    def fake(ctx, **kw):
        if calls is not None:
            calls.append(kw['clean_ids'].tolist())
        n = len(kw['clean_ids'])
        tail = torch.stack([kw['clean_ids'][:,-1], torch.full((n,),9),
                            torch.zeros(n,dtype=torch.long), torch.zeros(n,dtype=torch.long)],1)
        return torch.cat([kw['clean_ids'], tail],1)
    monkeypatch.setattr(G, 'generate', fake)
    with GenerationCheckpoint(root, maximum) as cp:
        store = cp.phase('data', 'intact', identity or {'runtime':'H200'})
        return G.generate_bucketed(SimpleNamespace(device='cpu', tokenizer=SimpleNamespace(pad_token_id=0),
                node_model=SimpleNamespace(config=SimpleNamespace(vocab_size=20))),
                **inputs(), batch_store=store)


def test_original_bucket_raw_tokens_and_resume(tmp_path, monkeypatch):
    calls=[]
    expected=invoke(tmp_path/'whole', monkeypatch, calls=calls)
    assert [len(c) for c in calls] == [2,2,1]
    assert calls[0] == [[1,2,3,4], [0,3,4,5]]
    with pytest.raises(GenerationSegmentComplete):
        invoke(tmp_path/'split', monkeypatch, maximum=1)
    fresh=[]
    assert torch.equal(expected, invoke(tmp_path/'split',monkeypatch,calls=fresh))
    assert [len(c) for c in fresh] == [2,1]
    hits=[]
    assert torch.equal(expected, invoke(tmp_path/'split',monkeypatch,calls=hits))
    assert hits == []
    assert expected[:,-4:].tolist() == [[4,9,0,0],[5,9,0,0],[3,9,0,0],[8,9,0,0],[4,9,0,0]]


def test_identity_mismatch_and_corruption_fail_closed(tmp_path, monkeypatch):
    invoke(tmp_path,monkeypatch)
    with pytest.raises(ValueError,match='identity'):
        invoke(tmp_path,monkeypatch,identity={'runtime':'A100'})
    next(tmp_path.rglob('batch-*.json')).write_text('{broken')
    with pytest.raises(ValueError,match='checkpoint'):
        invoke(tmp_path,monkeypatch)


def test_cross_process_lock_inode_survives(tmp_path):
    program='from evaluation.generation_checkpoint import GenerationCheckpoint; import sys; GenerationCheckpoint(sys.argv[1],2).__enter__()'
    with GenerationCheckpoint(tmp_path,2):
        inode=(tmp_path/'writer.lock').stat().st_ino
        child=subprocess.run([sys.executable,'-c',program,str(tmp_path)],capture_output=True,text=True)
        assert child.returncode != 0 and 'locked' in child.stderr
    with GenerationCheckpoint(tmp_path,2):
        assert (tmp_path/'writer.lock').stat().st_ino == inode


def test_partial_temp_ignored_and_stop_after_commit(tmp_path,monkeypatch):
    with pytest.raises(GenerationSegmentComplete):
        invoke(tmp_path,monkeypatch,maximum=1)
    records=list(tmp_path.rglob('batch-*.json'))
    assert len(records)==1
    records[0].with_suffix('.tmp').write_text('incomplete')
    invoke(tmp_path,monkeypatch)
    assert len(list(tmp_path.rglob('batch-*.json')))==3


def test_cold_process_resume_matches_uninterrupted(tmp_path, monkeypatch):
    import json
    from pathlib import Path
    expected = invoke(tmp_path/'whole', monkeypatch)
    program = '''import runpy, sys, json
from pathlib import Path
import pytest
ns=runpy.run_path(sys.argv[1])
try:
    out=ns['invoke'](Path(sys.argv[2]),pytest.MonkeyPatch(),maximum=int(sys.argv[3]))
except ns['GenerationSegmentComplete']:
    sys.exit(75)
Path(sys.argv[4]).write_text(json.dumps(out.tolist()))
'''
    command=[sys.executable, '-c', program, str(Path(__file__).resolve()), str(tmp_path/'cold')]
    first=subprocess.run(command+['1',str(tmp_path/'out.json')],capture_output=True,text=True)
    assert first.returncode==75, first.stderr
    second=subprocess.run(command+['20',str(tmp_path/'out.json')],capture_output=True,text=True)
    assert second.returncode==0, second.stderr
    assert torch.equal(expected,torch.tensor(json.loads((tmp_path/'out.json').read_text())))


@pytest.mark.parametrize('field', ['clean_ids','corrupt_ids','attention_mask','new_tokens','eos_ids','batch_size','use_cache'])
def test_plan_changes_fail_even_all_batches_cached(tmp_path, monkeypatch, field):
    invoke(tmp_path,monkeypatch)
    kw=inputs()
    if field in ('clean_ids','corrupt_ids'):
        kw[field]=kw[field].clone(); kw[field][0,-1]+=1
    elif field=='attention_mask':
        kw[field]=kw[field].clone(); kw[field][2,1]=1
    else:
        kw[field]={'new_tokens':3,'eos_ids':(8,9),'batch_size':3,'use_cache':False}[field]
    with GenerationCheckpoint(tmp_path,20) as cp:
        store=cp.phase('data','intact',{'runtime':'H200'})
        with pytest.raises(ValueError,match='identity'):
            G.generate_bucketed(SimpleNamespace(device='cpu',tokenizer=SimpleNamespace(pad_token_id=0),
                node_model=SimpleNamespace(config=SimpleNamespace(vocab_size=20))),**kw,batch_store=store)


@pytest.mark.parametrize('change', ['token','shape','rows','checksum','foreign'])
def test_invalid_records_fail_before_any_new_generation(tmp_path,monkeypatch,change):
    import json
    from evaluation.generation_checkpoint import digest
    with pytest.raises(GenerationSegmentComplete): invoke(tmp_path,monkeypatch,maximum=1)
    record=next(tmp_path.rglob('batch-*.json'))
    data=json.loads(record.read_text())
    if change=='token':data['payload']['tokens'][0][0]=999
    if change=='shape':data['payload']['tokens'][0].pop()
    if change=='rows':data['payload']['batch']['rows'].reverse()
    if change=='checksum':data['sha256']='bad'
    else:data['sha256']=digest(data['payload'])
    record.write_text(json.dumps(data))
    if change=='foreign': record.with_name('batch-999999.json').write_text(record.read_text())
    calls=[]
    with pytest.raises(ValueError,match='checkpoint'):invoke(tmp_path,monkeypatch,calls=calls)
    assert calls==[]


def test_default_generate_bucketed_unchanged(tmp_path,monkeypatch):
    expected=invoke(tmp_path,monkeypatch)
    actual=G.generate_bucketed(SimpleNamespace(device='cpu'),**inputs())
    assert torch.equal(expected,actual)


def test_real_tiny_model_new_process_equivalent_resume(tmp_path):
    from tests.test_gen_engine import _ctx
    expected=G.generate_bucketed(_ctx(seed=4),**inputs())
    for limit in (1,20):
        try:
            with GenerationCheckpoint(tmp_path,limit) as cp:
                actual=G.generate_bucketed(_ctx(seed=4),**inputs(),
                    batch_store=cp.phase('tiny','masked',{'seed':4,'mask':'alternating'}))
        except GenerationSegmentComplete:
            assert limit==1
    assert torch.equal(expected,actual)


def test_fixed_cohort_restores_donors_corrupt_stream_and_full_tokens(tmp_path,monkeypatch):
    from contextlib import nullcontext
    from evaluation import benchmark_eval as B
    from evaluation import generation_checkpoint as C
    from evaluation.benchmarks.base import BenchmarkItem
    import evaluation.fixed_benchmark_cohort as F
    class Tok:
        pad_token_id=0
        def get_vocab(self):return {}
        def apply_chat_template(self,messages,**kwargs):return messages[0]['content']
        def encode(self,text,**kwargs):return [2+ord(c)%18 for c in text]
        def decode(self,tokens,**kwargs):return str(tokens)
    items=[BenchmarkItem(str(i),[{'role':'user','content':t}])
           for i,t in enumerate(['a','abc','ab','def','abcd'])]
    donors=[items[2],BenchmarkItem('d1',[{'role':'user','content':'safe'}]),
            BenchmarkItem('d2',[{'role':'user','content':'yes'}])]
    data={'items':[i.to_json() for i in items],'pool_items':[i.to_json() for i in donors],
          'partner_index':[2,1,0,2,1],'pairing':'fixed','selection_provenance':{'device':'A40'},
          'new_tokens':4,'prompts':[i.messages[0]['content'] for i in items]}
    monkeypatch.setattr(F,'load_fixed_cohort',lambda *args:data)
    monkeypatch.setattr(C,'execution_identity',lambda ctx:{'runtime':'H200','cohort':data})
    import analysis
    monkeypatch.setattr(analysis,'extract_node_masks',lambda model:{'effective':'open'})
    def fake(ctx,**kw):
        tail=torch.cat([kw['clean_ids'][:,-1:],torch.full((len(kw['clean_ids']),1),9),
                        torch.zeros(len(kw['clean_ids']),2,dtype=torch.long)],1)
        return torch.cat([kw['clean_ids'],tail],1)
    monkeypatch.setattr(G,'generate',fake)
    def run(path,limit):
        with GenerationCheckpoint(path,limit) as cp:
            cli=SimpleNamespace(ablation='interchange',
                benchmark_fixed_cohort='frozen',benchmark_new_tokens=4,
                benchmark_gen_batch_size=2,no_kv_cache=False,device='cpu')
            ctx=SimpleNamespace(cli=cli,session=SimpleNamespace(_generation_checkpoint=cp),device='cpu',tokenizer=Tok(),
                node_model=SimpleNamespace(config=SimpleNamespace(vocab_size=20),
                    generation_config=SimpleNamespace(eos_token_id=9)),all_gates_open=nullcontext)
            screen=B.fixed_cohort_screen(ctx,SimpleNamespace(new_tokens=4),None,'fixture')
            corrupt,tiled=B.build_corrupt_stream(screen.clean_ids,screen.clean_mask,screen.partners,4,0)
            # Full config must use reconstructed recipient tokens, with no generation.
            monkeypatch.setattr(B,'coherence_metrics',lambda *a,**k:{'ok':True})
            monkeypatch.setattr(B,'_judge_all',lambda *a:[{'label':'honest'}]*5)
            monkeypatch.setattr(B,'_save_partial',lambda *a,**k:None)
            cli.benchmark_coherence_batch_size=2
            cell=B.BenchmarkEvaluation()._run_config(ctx,None,None,'fixture',screen,corrupt,None,'full',None,(9,))
            assert len(cell['generations'])==5
            return screen,corrupt,tiled
    whole,corrupt,tiled=run(tmp_path/'whole',20)
    # Three recipient batches and then donor batch, stop after recipient phase.
    with pytest.raises(GenerationSegmentComplete):run(tmp_path/'split',3)
    restored,restored_corrupt,restored_tiled=run(tmp_path/'split',20)
    assert torch.equal(whole.full_ids,restored.full_ids)
    assert whole.pool_refs==restored.pool_refs
    assert whole.partner_index==restored.partner_index
    assert torch.equal(corrupt,restored_corrupt) and tiled==restored_tiled
    assert whole.pool_refs[0][1][-1]==9  # early EOS retained; pads removed for tiling


def test_cli_segment_stop_is_incomplete_and_exit75(tmp_path,monkeypatch):
    import json
    import evaluate_circuit as E
    cli=SimpleNamespace(evals=[],dry_run=False,judge_dry_run=False,
        benchmark_generation_checkpoint_dir=str(tmp_path),benchmark_stop_after_generation_batches=1)
    monkeypatch.setattr(E,'build_parser',lambda:SimpleNamespace(parse_args=lambda:cli))
    monkeypatch.setattr(E,'resolve_cli',lambda x:x)
    monkeypatch.setattr(E,'build_session',lambda x:SimpleNamespace())
    def stopped(session):
        assert torch.initial_seed()==0
        json.dumps(vars(cli))  # runtime store must never leak into CLI JSON
        raise GenerationSegmentComplete('saved batch')
    monkeypatch.setattr(E.suite,'run',stopped)
    torch.manual_seed(98765)
    assert E.main()==75
    record=json.loads(next(tmp_path.glob('segment-*.json')).read_text())
    assert record['status']=='segment_complete'
    assert record['evaluation_complete'] is False and record['headline_available'] is False
    assert not hasattr(cli,'_generation_checkpoint')


@pytest.mark.parametrize('kind',['segment','checkpoint'])
def test_real_benchmark_run_propagates_stop_before_next_dataset(tmp_path,monkeypatch,kind):
    from evaluation import benchmark_eval as B
    from tests.test_benchmark_eval import make_cli
    cli=make_cli(benchmarks=['first','second'],benchmark_judge_cache=str(tmp_path/'judge.jsonl'))
    ctx=SimpleNamespace(cli=cli,args=SimpleNamespace(model='tiny'),out_dir=str(tmp_path))
    monkeypatch.setattr(B,'expand',lambda datasets:datasets)
    monkeypatch.setattr(B,'JudgeClient',lambda **kwargs:object())
    from evaluation.generation_checkpoint import GenerationCheckpointError
    exception=GenerationSegmentComplete if kind=='segment' else GenerationCheckpointError
    visited=[]
    def stopped(ctx,dataset,client):
        visited.append(dataset)
        raise exception('durably saved' if kind=='segment' else 'corrupt checkpoint')
    evaluation=B.BenchmarkEvaluation()
    monkeypatch.setattr(evaluation,'_run_dataset',stopped)
    with pytest.raises(exception):evaluation.run(ctx)
    assert visited==['first']


@pytest.mark.parametrize('drift',['source','model','tokenizer','runtime','dtype','mask'])
def test_actual_execution_identity_all_hit_drift(tmp_path,monkeypatch,drift):
    from evaluation import generation_checkpoint as C
    import analysis
    source=tmp_path/'source'/'evaluation'/'generation_checkpoint.py'
    source.parent.mkdir(parents=True);source.write_text('first source')
    monkeypatch.setattr(C,'__file__',str(source))
    artifact=tmp_path/'artifact.json';artifact.write_text('{}')
    state={'source':'first','model':'a'*40,'tokenizer':'original','runtime':'NVIDIA H200',
           'dtype':torch.float32,'mask':{'actual':[1,0]}}
    monkeypatch.setattr(torch.cuda,'is_available',lambda:True)
    monkeypatch.setattr(torch.cuda,'get_device_name',lambda d:state['runtime'])
    monkeypatch.setattr(torch.backends.cudnn,'version',lambda:9000)
    monkeypatch.setattr(torch.cuda,'get_device_capability',lambda d:(9,0))
    monkeypatch.setattr(torch.cuda,'get_device_properties',lambda d:SimpleNamespace(uuid='not-identity'))
    class Config:
        _name_or_path='model';vocab_size=20
        @property
        def _commit_hash(self):return state['model']
        def to_dict(self):return {'vocab_size':20}
    class Model:
        config=Config();training=False
        def modules(self):return [self]
        def parameters(self):return iter([SimpleNamespace(device=SimpleNamespace(type='cuda'),dtype=state['dtype'])])
    tok=SimpleNamespace(pad_token_id=0,chat_template='template',special_tokens_map={},init_kwargs={},
        backend_tokenizer=SimpleNamespace(to_str=lambda:state['tokenizer']))
    cli=SimpleNamespace(benchmark_fixed_cohort=str(artifact),benchmark_frozen_masks=str(artifact),benchmarks=['data'])
    ctx=SimpleNamespace(cli=cli,session=SimpleNamespace(),node_model=Model(),tokenizer=tok,device='cpu')
    monkeypatch.setattr(analysis,'extract_node_masks',lambda m:state['mask'])
    calls=[]
    def fake(ctx,**kw):
        calls.append(1)
        return torch.cat([kw['clean_ids'],torch.zeros(len(kw['clean_ids']),4,dtype=torch.long)],1)
    monkeypatch.setattr(G,'generate',fake)
    def run():
        with GenerationCheckpoint(tmp_path/'cache',20) as cp:
            ctx.session._generation_checkpoint=cp
            return G.generate_bucketed(ctx,**inputs(),batch_store=C.phase_store(ctx,'data','intact'))
    run();assert len(calls)==3;calls.clear()
    if drift=='source':source.write_text('changed source')
    else:state[drift]={'model':'b'*40,'tokenizer':'changed','runtime':'NVIDIA H200 variant',
        'dtype':torch.bfloat16,'mask':{'actual':[0,1]}}[drift]
    with pytest.raises(ValueError,match='identity'):run()
    assert calls==[]


def test_process_death_releases_lock_without_unlink(tmp_path):
    import time
    program='''from evaluation.generation_checkpoint import GenerationCheckpoint
from pathlib import Path
import sys,time
with GenerationCheckpoint(sys.argv[1],2):
    Path(sys.argv[1],'ready').write_text('ready')
    time.sleep(30)
'''
    child=subprocess.Popen([sys.executable,'-c',program,str(tmp_path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for _ in range(300):
            if (tmp_path/'ready').exists():break
            if child.poll() is not None:pytest.fail(child.stderr.read().decode())
            time.sleep(.1)
        assert (tmp_path/'ready').exists()
        inode=(tmp_path/'writer.lock').stat().st_ino
        child.kill();child.wait(timeout=10)
        with GenerationCheckpoint(tmp_path,2):
            assert (tmp_path/'writer.lock').stat().st_ino==inode
    finally:
        if child.poll() is None:child.kill();child.wait(timeout=10)


def test_failed_batch_commit_aborts_without_next_generation(tmp_path,monkeypatch):
    from evaluation import generation_checkpoint as C
    original=C.atomic_json
    def fail(path,value):
        if path.name.startswith('batch-'):raise OSError('disk full')
        return original(path,value)
    monkeypatch.setattr(C,'atomic_json',fail)
    calls=[]
    with pytest.raises(C.GenerationCheckpointError,match='commit failed'):
        invoke(tmp_path,monkeypatch,maximum=1,calls=calls)
    assert len(calls)==1 and not list(tmp_path.rglob('batch-*.json'))


@pytest.mark.parametrize('opt_in',[False,True])
def test_public_main_checkpoint_runtime_settings_leave_stock_untouched(tmp_path,monkeypatch,opt_in):
    import evaluate_circuit as E
    cli=SimpleNamespace(evals=[],dry_run=False,judge_dry_run=False,
        benchmark_generation_checkpoint_dir=str(tmp_path) if opt_in else None,
        benchmark_stop_after_generation_batches=1)
    monkeypatch.setattr(E,'build_parser',lambda:SimpleNamespace(parse_args=lambda:cli))
    monkeypatch.setattr(E,'resolve_cli',lambda x:x)
    monkeypatch.setattr(E,'build_session',lambda x:SimpleNamespace())
    calls=[]
    monkeypatch.setattr(torch,'manual_seed',lambda seed:calls.append(('seed',seed)))
    monkeypatch.setattr(torch,'use_deterministic_algorithms',lambda enabled:calls.append(('deterministic',enabled)))
    monkeypatch.setattr(torch.backends.cuda.matmul,'allow_tf32',True)
    monkeypatch.setattr(torch.backends.cudnn,'allow_tf32',True)
    def checked(session):
        assert calls==([('seed',0),('deterministic',True)] if opt_in else [])
        assert torch.backends.cuda.matmul.allow_tf32 is (not opt_in)
        assert torch.backends.cudnn.allow_tf32 is (not opt_in)
        return 0
    monkeypatch.setattr(E.suite,'run',checked)
    assert E.main()==0
