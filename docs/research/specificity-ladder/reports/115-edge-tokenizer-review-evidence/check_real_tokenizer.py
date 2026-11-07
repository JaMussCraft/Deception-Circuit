import argparse,hashlib,json,os,pathlib,socket,sys,time
from types import SimpleNamespace
from unittest import mock
W=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
C=W/'.superpowers/sdd/plan-a3/edge-tokenizer-fix-source-v2';sys.path.insert(0,str(C))
a=argparse.ArgumentParser();a.add_argument('--output',required=True);args=a.parse_args();start=time.perf_counter()
from component_analysis import a3_pipeline as canonical,a3_edge_pipeline as edge,ladder_pipeline as ladder
from dataset import user_inversion_pipeline as common
import huggingface_hub,transformers
parent_path=W/'outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json';parent=ladder.read_artifact(parent_path)
design_path=W/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/canonical/design.json'
design=ladder.read_artifact(design_path)
settings=SimpleNamespace(model=parent['model'],tokenizer_revision=parent['tokenizer_revision'])
assert settings.tokenizer_revision=='0e9e39f249a16976918f6564b8830bc894c89659'
factory_calls=[];cache_calls=[];network=[]
original_factory=transformers.AutoTokenizer.from_pretrained;original_cache=huggingface_hub.hf_hub_download

def factory(*aa,**kw):
    assert kw.get('local_files_only') is True
    factory_calls.append({'identifier':str(aa[0]),'revision':kw.get('revision'),'local_files_only':kw['local_files_only']})
    return original_factory(*aa,**kw)
def cache(*aa,**kw):
    assert kw.get('local_files_only') is True
    cache_calls.append({'model':str(aa[0]),'file':str(aa[1]),'revision':kw.get('revision'),'local_files_only':kw['local_files_only']})
    return original_cache(*aa,**kw)
def no_network(self,address):network.append(str(address));raise AssertionError('unexpected network connection '+str(address))

with mock.patch.object(transformers.AutoTokenizer,'from_pretrained',side_effect=factory),mock.patch.object(huggingface_hub,'hf_hub_download',side_effect=cache),mock.patch.object(socket.socket,'connect',no_network):
    tok=common.load_tokenizer(settings)
    assert tok.pad_token==tok.eos_token and common.tokenizer_identity(tok,settings.tokenizer_revision)==parent['tokenizer_identity']
    expected=canonical._validated_prepare_tokenizer(tok,parent)
    assert expected is not tok and common.tokenizer_identity(expected,settings.tokenizer_revision)==parent['tokenizer_identity']
    snapshot=pathlib.Path(common.tokenizer_loading(tok)['resolved_snapshot'])
    raw=transformers.AutoTokenizer.from_pretrained(str(snapshot),revision=settings.tokenizer_revision,local_files_only=True)
    assert raw.pad_token is None
    try:canonical._validated_prepare_tokenizer(raw,parent)
    except ValueError as error:assert str(error)=='production tokenizer configuration differs from pinned standard'
    else:raise AssertionError('raw factory unexpectedly accepted')
    negative={}
    for name in ('padding_side','pad_token','chat_template','encode_override'):
        changed=common.load_tokenizer(settings)
        if name=='padding_side':changed.padding_side='left' if changed.padding_side=='right' else 'right'
        elif name=='pad_token':changed.pad_token=None
        elif name=='chat_template':changed.chat_template+='\nchanged'
        else:changed.encode=lambda *aa,**kw:[0]
        try:canonical._validated_prepare_tokenizer(changed,parent)
        except ValueError as error:negative[name]=str(error)
        else:raise AssertionError('modified tokenizer accepted: '+name)
    try:common.tokenizer_identity(tok,'f'*40)
    except ValueError as error:negative['wrong_revision']=str(error)
    else:raise AssertionError('wrong requested revision accepted')
    # All original mechanism prompts, including both streams, not a sampled prefix.
    records=0;per_task={};token_total=0;prompt_hash=hashlib.sha256()
    for task,conditions in parent['rows'].items():
        per_task[task]=0
        for condition,rows in conditions.items():
            for row in rows:
                for stream,record in row['streams'].items():
                    actual=tok.encode(record['prompt'],add_special_tokens=False)
                    original=raw.encode(record['prompt'],add_special_tokens=False)
                    assert actual==original==record['tokens'],(task,condition,stream,row['instance_id'])
                    records+=1;per_task[task]+=1;token_total+=len(actual)
                    prompt_hash.update(json.dumps([task,condition,stream,row['instance_id'],record['prompt'],actual],ensure_ascii=False).encode())
    print('ALL_PARENT_PROMPTS_IDENTICAL',records,flush=True)
    # Exercise the actual repaired producer-replay call without publishing preparation.
    admission=edge.admit_parent_sources(design,registry_paths=[str(W/'docs/research/held_out.json')])
    assert admission['kind']=='a3_edge_source_admission' and admission['injected'] is False
    assert admission['source_sha256']==edge.source_rows_digest(design)
    assert admission['parent_evidence']==design['parent_evidence']
    assert not network
imports={n:str(pathlib.Path(m.__file__).resolve()) for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','dataset','models','evaluation','scripts') and getattr(m,'__file__',None)}
assert all(os.path.commonpath([str(C),p])==str(C) for p in imports.values()),imports
result=dict(kind='independent_edge_real_tokenizer_repair_check',candidate_root=str(C),baseline_commit='74efb4d0481968a1d0138eb1a79b97f302fd3c3b',candidate_is_uncommitted=True,python=sys.executable,transformers=transformers.__version__,model=settings.model,revision=settings.tokenizer_revision,tokenizer_identity=parent['tokenizer_identity'],loading=common.tokenizer_loading(tok),parent_prompt_streams_checked=records,per_task=per_task,parent_token_count=token_total,parent_prompt_digest=prompt_hash.hexdigest(),negative_rejections=negative,factory_calls=factory_calls,cache_calls=cache_calls,network_connections=network,actual_parent_producer_replay=True,admission=admission,execution_authorized=False,large_weights_loaded=False,scientific_execution=False,exit_code=0,elapsed_seconds=time.perf_counter()-start,project_imports=imports)
pathlib.Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('admission','factory_calls','cache_calls','project_imports')},indent=2))
