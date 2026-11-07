"""Pure contract tests; synthetic terminal evidence never native acceptance."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

HERE = Path(__file__).resolve().parent

def module(name):
    path = HERE / (name + '.py')
    assert path.is_file(), 'missing required ' + name
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result

def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))
    import hashlib
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

def contract():
    return json.loads((HERE/'partition.json').read_text())

def test_frozen_original_partition():
    a = module('aggregate'); p = contract(); a.validate_partition(p)
    assert len(p['full_collection']) == 223
    assert [len(p['shards'][str(i)]['members']) for i in (0,1)] == [112,111]
    for i in (0,1):
        row=p['shards'][str(i)]
        assert row['members']==p['full_collection'][i::2]
        assert row['execution_order']==sorted(row['members'], key=lambda n: n.split('::')[1].split('[')[0] not in p['repaired_families'])

@pytest.mark.parametrize('damage', ['duplicate','omit','substitute','count','order'])
def test_partition_rejects_damage(damage):
    a=module('aggregate'); p=contract()
    if damage=='duplicate':p['full_collection'][1]=p['full_collection'][0]
    if damage=='omit':p['shards']['0']['members'].pop()
    if damage=='substitute':p['shards']['0']['members'][0]='wrong.py::test_substitute'
    if damage=='count':p['per_function_counts'][next(iter(p['per_function_counts']))]+=1
    if damage=='order':p['shards']['0']['execution_order'].reverse()
    with pytest.raises((AssertionError,ValueError)):a.validate_partition(p)

def terminal(tmp_path):
    a=module('aggregate'); p=contract(); source={'revision':'r8-sharded','runtime_sha256':'runtime','fixture_sha256':'fixture','partition_sha256':a.digest(HERE/'partition.json'),'source_pins_sha256':'pins'}
    bindings={}; records=[]
    for env,py in a.ENVS.items():
        bindings[py]={}
        for shard in ('0','1'):
            job=str(100+len(records)); out=tmp_path/env/('job-'+job)/'child/execution'; out.mkdir(parents=True)
            host_root=out.parent.parent
            cluster='delta' if env=='base' else 'bridges2'
            nodes=p['shards'][shard]['execution_order']
            events=[dict(event='start',collected=p['full_collection'],requested=nodes,python=py,executable=py)]
            for n in nodes:
                events.append(dict(event='item-start',nodeid=n))
                events.extend(dict(event='phase-report',nodeid=n,when=w,outcome='passed') for w in ('setup','call','teardown'))
                events.append(dict(event='item-finish',nodeid=n))
            events.append(dict(event='finished',requested_count=len(nodes)))
            ep=out/'events.jsonl'; ep.write_text(''.join(json.dumps(e)+'\n' for e in events))
            import xml.etree.ElementTree as ET
            xml=ET.Element('testsuite')
            for n in nodes:
                file,name=n.split('::',1); ET.SubElement(xml,'testcase',classname=file[:-3],name=name)
            xp=out/'junit.xml'; ET.ElementTree(xml).write(str(xp))
            baseline=put(out/'baseline.json',dict(status='CORRECTION_RED_EXPECTED',normal_completion=True,exit_code=0,pytest_exit_code=1,observed_cases=5,expected_cases=5,failures=5,errors=0,skipped=0,per_function_case_counts=a.BASELINE_COUNTS))
            oracle=put(out/'oracle.json',dict(complete=True,exit_code=0,model_loaded=False,execution_authorized=False))
            preflight=put(out/'preflight.json',dict(status='FIXTURE_PREFLIGHT_COMPLETE',normal_completion=True,exit_code=0,source_pins_before_after_equal=True))
            config=put(out/'config.json',dict(job_id=job,cluster=cluster,environment=env,shard=int(shard),cpus=2 if env=='base' else 18,memory_gib=32,allocation_seconds=4800))
            stages={stage:put(host_root/(stage+'-terminal.json'),dict(normal_completion=True,exit_code=0,started=.5,finished=2.5,deadline=3)) for stage in ('baseline','oracle','suite')}
            host=put(host_root/'host-after.json',dict(status='HOST_COMPLETE',normal_completion=True,exit_code=0,job_id=job,cluster=cluster,output=str(out),source_checks_complete=True,allocation_checks_complete=True,config_sha256=config['sha256'],stages=stages))
            accounting=put(out/'accounting.json',dict(job_id=job,cluster=cluster,state='COMPLETED',exit_code='0:0',gpus=0))
            m=dict(status='SHARD_GREEN',full_suite_accepted=False,execution_authorized=False,model_loaded=False,normal_completion=True,exit_code=0,environment=env,shard=int(shard),python=py,executable=py,job_id=job,cluster=cluster,output=str(out),source_before=source,source_after=source,child_exit_code=0,child_normal_completion=True,child_started=1,child_finished=2,child_deadline=3,collected=p['full_collection'],executed=nodes,artifacts=dict(events=dict(path=str(ep),sha256=a.digest(ep)),junit=dict(path=str(xp),sha256=a.digest(xp)),baseline=baseline,oracle=oracle,preflight=preflight))
            ref=put(out/'run_manifest.json',m); records.append(ref)
            bindings[py][shard]=dict(job_id=job,cluster=cluster,output=str(out),manifest=ref,config=config,host=host,accounting=accounting)
    return a,p,source,bindings,records

def test_complete_and_partial_are_separate(tmp_path):
    a,p,s,b,r=terminal(tmp_path)
    result=a.verify_shards(r,p,s,b)
    assert result['full_suite_accepted'] is True and result['complete_environments']==['base','mgnp']
    assert a.verify_shards(r[:2],p,s,b)['full_suite_accepted'] is False

@pytest.mark.parametrize('damage',['duplicate','omit','substitute','phase','fail','skip','setup-error','teardown-error','late','nonzero','source','source-after','interpreter','job','baseline','oracle','preflight','host','partition-after','old-r5','config','accounting','overlap-binding'])
def test_aggregate_fails_closed(tmp_path,damage):
    a,p,s,b,records=terminal(tmp_path); ref=records[0]; m=json.loads(Path(ref['path']).read_text())
    if damage in ('duplicate','omit','substitute'):
        if damage=='duplicate':m['executed'][1]=m['executed'][0]
        if damage=='omit':m['executed'].pop()
        if damage=='substitute':m['executed'][0]='wrong.py::test_wrong'
    elif damage in ('phase','fail','skip','setup-error','teardown-error'):
        ep=Path(m['artifacts']['events']['path']); events=[json.loads(x) for x in ep.read_text().splitlines()]
        if damage=='phase':events.pop(2)
        else:
            phase={'fail':'call','skip':'call','setup-error':'setup','teardown-error':'teardown'}[damage]
            next(x for x in events if x.get('when')==phase)['outcome']='skipped' if damage=='skip' else 'failed'
        ep.write_text(''.join(json.dumps(e)+'\n' for e in events)); m['artifacts']['events']['sha256']=a.digest(ep)
    elif damage=='late':m['child_finished']=m['child_deadline']
    elif damage=='nonzero':m['child_exit_code']=1
    elif damage=='source':m['source_before']={}
    elif damage=='source-after':m['source_after']={}
    elif damage=='partition-after':s['partition_sha256']='changed'
    elif damage=='interpreter':m['executable']='/wrong/python'
    elif damage=='job':m['job_id']='999'
    elif damage in ('baseline','oracle','preflight'):m['artifacts'].pop(damage)
    elif damage in ('host','config','accounting'):b[a.ENVS['base']]['0'][damage]=None
    elif damage=='old-r5':m['status']='GREEN_EXPECTED'
    elif damage=='overlap-binding':b[a.ENVS['base']]['1']['job_id']=m['job_id']
    new=put(Path(ref['path']),m); records[0]=new; b[a.ENVS['base']]['0']['manifest']=new
    with pytest.raises((AssertionError,ValueError,KeyError,TypeError)):a.verify_shards(records,p,s,b)

def test_selector_real_pytest_keeps_full_collection(tmp_path):
    module('selector')
    suite=tmp_path/'mini'; suite.mkdir()
    (suite/'test_mini.py').write_text('def test_a(): pass\ndef test_b(): pass\ndef test_c(): pass\n')
    (suite/'conftest.py').write_text('def pytest_collection_finish(session):\n assert len(session.items)==3\ndef pytest_sessionfinish(session,exitstatus):\n assert len(session.items)==3\n')
    nodes=['test_mini.py::test_'+x for x in 'abc']; order=[nodes[2],nodes[0]]
    part=put(tmp_path/'mini-partition.json',dict(full_collection=nodes,shards={'0':dict(execution_order=order)}))
    ep=tmp_path/'events.jsonl'; env=dict(os.environ,PYTHONPATH=str(HERE),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONDONTWRITEBYTECODE='1',A3_SHARD_PARTITION=part['path'],A3_SHARD='0',A3_SHARD_EVENTS=str(ep))
    result=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider','-p','selector','--rootdir='+str(suite),'--confcutdir='+str(suite),str(suite)],env=env,capture_output=True,text=True,timeout=8)
    assert result.returncode==0,result.stdout+result.stderr
    events=[json.loads(x) for x in ep.read_text().splitlines()]
    assert events[0]['collected']==nodes
    assert events[0]['python_version']==sys.version
    assert events[0]['pytest_version'] and Path(events[0]['pytest_origin']).is_file()
    assert [x['nodeid'] for x in events if x['event']=='item-start']==order
    assert len([x for x in events if x['event']=='phase-report'])==6
    # Exclusive event output must not overwrite a previous attempt.
    again=subprocess.run(result.args,env=env,capture_output=True,text=True,timeout=8)
    assert again.returncode!=0

def test_deadline_caps_and_late_success():
    h=module('supervisor')
    assert h.stage_bound(0,4800,4700,3600)==3600
    with pytest.raises(AssertionError):h.stage_bound(1000,4800,4700,3600)
    assert not h.timely(0,10,10)
    assert h.timely(0,9,10)

def test_host_rejects_absent_or_nonzero_stage_terminal(tmp_path):
    a,p,s,b,records=terminal(tmp_path)
    py=a.ENVS['base']; binding=b[py]['0']; host=json.loads(Path(binding['host']['path']).read_text())
    host['stages']={}
    binding['host']=put(Path(binding['host']['path']),host)
    with pytest.raises((ValueError,KeyError)):a.verify_shards(records,p,s,b)

def test_supervisor_cleans_tiny_timed_out_process_group(tmp_path):
    h=module('supervisor'); h.enable_subreaper()
    import time
    end=time.time()+300
    def allocation(timeout=15):return {},end
    with (tmp_path/'out').open('wb') as out,(tmp_path/'err').open('wb') as err:
        row=h.execute([sys.executable,'-c','import time;time.sleep(10)'],out,err,.05,end,allocation)
    assert row['normal_completion'] is False and 'deadline' in row['error']
    assert 'cleanup_error' not in row
