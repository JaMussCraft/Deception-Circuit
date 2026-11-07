"""Pure diagnostic policy tests; no native imports, allocation or scientific data."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
P=Path(__file__).resolve().parent


def module(name):
    path=P/(name+'.py');assert path.is_file(),'DIAGNOSTIC239_MISSING '+str(path)
    spec=importlib.util.spec_from_file_location('timing239_'+name,str(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


@pytest.mark.parametrize('stage,initial,current,want',[
    ('prime',2000.,1900.,1480.),('fresh',2000.,1900.,1240.),('fresh',1200.,1900.,1140.),
    ('fresh',2000.,1150.,1090.),('prime',1700.,1900.,1355.)])
def test_fixed_deadlines_reserve_finish_and_fresh_pipeline(stage,initial,current,want):
    m=module('runner');assert m.diagnostic_deadline(stage,1000.,initial,current)==want


@pytest.mark.parametrize('stage',['bank','score','full_score','prefix4'])
def test_operational_phase_cannot_be_a_diagnostic_stage(stage):
    m=module('runner')
    with pytest.raises(ValueError):m.diagnostic_deadline(stage,1000.,2000.,2000.)


@pytest.mark.parametrize('key',['complete','phase','actual_future_GPU_job_id','waiting_sha256','timely_window'])
def test_diagnostic_record_cannot_carry_operational_authority(key):
    m=module('runner');value=dict(kind='A2_DATA_TIMING_DIAGNOSTIC_V1',diagnostic_only=True,operational_admission=False)
    m.ensure_nonoperational(value);value[key]=True
    with pytest.raises(ValueError):m.ensure_nonoperational(value)


def test_prime_and_fresh_require_distinct_normal_processes():
    m=module('runner');a=dict(pid=11,exit_code=0,term_sent_at=None);b=dict(pid=12,exit_code=0,term_sent_at=None)
    m.distinct_normal_processes(a,b,10)
    for bad in (dict(b,pid=11),dict(b,pid=10),dict(b,exit_code=1),dict(b,term_sent_at=1000.)):
        with pytest.raises(ValueError):m.distinct_normal_processes(a,bad,10)


def test_child_command_uses_new_bank_matching_interpreter_without_request():
    m=module('runner');c=dict(python='/u/swong2/.conda/envs/mgnp/bin/python')
    commands=[m.child_command(c,'/bound.json','a'*64,stage,'/evidence/'+stage,1200.) for stage in ('prime','fresh')]
    assert commands[0]!=commands[1]
    for cmd in commands:
        assert cmd[:3]==[c['python'],'-B',str(P/'child.py')]
        assert not any(x in ' '.join(cmd) for x in ('WAITING','--request','--limit','--stage score'))


def test_relocated_launcher_uses_absolute_packet(tmp_path):
    wrapper=P/'launch.sh';assert wrapper.is_file(),'DIAGNOSTIC239_MISSING launch'
    moved=tmp_path/'slurm_script';moved.write_bytes(wrapper.read_bytes());bindir=tmp_path/'bin';bindir.mkdir();capture=tmp_path/'args.json'
    stub=bindir/'python3';stub.write_text('#!'+sys.executable+'\nimport json,os,sys\nopen(os.environ["CAPTURE"],"w").write(json.dumps(sys.argv[1:]))\n');stub.chmod(0o755)
    done=subprocess.run(['bash',str(moved),'--config','unbound','--config-sha256','a'*64],env=dict(os.environ,PATH=str(bindir)+':'+os.environ['PATH'],CAPTURE=str(capture)),capture_output=True,timeout=5)
    assert done.returncode==0,done.stderr
    assert json.loads(capture.read_text())==[str(P/'runner.py'),'--config','unbound','--config-sha256','a'*64]


def test_external_factor_reuses_complete_guard_chain_without_operational_entry():
    m=module('data_path');tree=ast.parse(Path(m.__file__).read_text())
    calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
    for required in ('v.capture_identities','v.validate_native_context','v.origins','v.reconstruct_domain',
                     'v.validate_domain_identity','p.hash_content','p.a1.read_artifact','p._validate_live'):
        assert required in calls,required
    assert calls.count('v.capture_identities')==3
    assert all(x not in calls for x in ('v.validate_full_score','s.supervise_once','p.score','p.freeze','p.load_model'))
    text=Path(m.__file__).read_text()
    for required in ('SCIENCE_FIELDS','grader_binding','support_reason_mask_sha256','current_catalogue_witness','catalogue_capture_files'):
        assert required in text,required
    assert 'actual_future_GPU_job_id' not in text and 'phase_request_sha256' not in text


def test_publication_is_separate_and_remote_costs_cannot_be_invented():
    m=module('runner');value=m.local_orientation(230.,2.)
    assert value['fixed_GPU_window_seconds']==300 and value['proposed_publication_margin_seconds']==45
    assert value['local_component_headroom_seconds']==25
    assert value['operational_feasible'] is None and value['request_transfer_remote_publication_measured'] is False
    assert m.local_orientation(260.,2.)['local_component_headroom_seconds']==-5

# R244-A: real run_stage around its final metadata/process boundary.
from types import SimpleNamespace


def boundary_fixture(tmp_path,monkeypatch,stage,preentry_now,current_end,late_reap=False):
    m=module('runner');clock={'now':1000.};calls=[];allocation_calls={'n':0}
    c=dict(actual_CPU_job_id='123',expected_account='fixture-cpu',expected_qos='fixture',python='/u/swong2/.conda/envs/mgnp/bin/python')
    def allocation(_):
        allocation_calls['n']+=1
        # The actual current end can later increase; entry's shorter bound sticks.
        end=1900. if allocation_calls['n']!=2 else current_end
        return dict(end_epoch=end)
    def packet(_):clock['now']=preentry_now
    real_read=m.read_ref
    monkeypatch.setattr(m.time,'time',lambda:clock['now']);monkeypatch.setattr(m.time,'monotonic',lambda:clock['now'])
    monkeypatch.setattr(m,'metrics',lambda *a:{})
    monkeypatch.setattr(m,'parameters',lambda c,out,deadline:dict(bound_diagnostic_deadline=deadline))
    monkeypatch.setattr(m,'read_ref',lambda ref:c if ref['path']=='/fixture' else real_read(ref))
    monkeypatch.setattr(m,'packet',packet)
    class Child:
        pid=42
        returncode=0
        def poll(self):
            if late_reap:clock['now']=1250.
            return 0
        def wait(self,timeout=None):return 0
    def popen(command,**kwargs):
        calls.append(dict(command=command,now=clock['now']))
        if stage=='prime' and preentry_now>=1480. or stage=='fresh' and (preentry_now>=1240. or current_end-60<=preentry_now):
            raise AssertionError('Popen reached after final bound expired')
        out=tmp_path/stage;params=out/'data-parameters.json';catalogues=[];hashes={}
        for n in range(4):
            path=out/('catalogue-%d.json'%n);path.write_bytes(('fixture%d'%n).encode());h=m.sha(path)
            catalogues.append(dict(virtual_path='catalogue%d'%n,sha256=h,bytes=path.stat().st_size,captured_bytes_path=str(path)))
            hashes['catalogue%d'%n]=h
        record=dict(kind='A2_DATA_TIMING_DIAGNOSTIC_V1',diagnostic_only=True,operational_admission=False,pid=42,parent_pid=os.getpid(),diagnostic_stage=stage,
                    source_after=dict(catalogues=hashes),catalogue_capture_files=catalogues,data_parameters_sha256=m.sha(params))
        m.write(out/'child-observation.json',record)
        return Child()
    monkeypatch.setattr(m.subprocess,'Popen',popen)
    source_supervisor=P.parent/'plan-a2-full-score-operational186/candidate/cpu/supervisor.py'
    sup=m.load_module('r244_real_observer',source_supervisor)
    s=SimpleNamespace(allocation=allocation,terminate=lambda *a:None,observe_child=sup.observe_child)
    v=SimpleNamespace(capture_identities=lambda _:dict(catalogues={row['virtual_path']:row['sha256'] for row in json.loads((tmp_path/stage/'child-observation.json').read_text())['catalogue_capture_files']}))
    return m,c,dict(path='/fixture',sha256='a'*64),v,s,calls


@pytest.mark.parametrize('stage,now,current_end',[
    ('fresh',1250.,1900.),('prime',1490.,1900.),('fresh',1240.,1900.),('fresh',1010.,1050.)])
def test_review244_final_authentication_or_current_end_expiry_prevents_Popen(tmp_path,monkeypatch,stage,now,current_end):
    m,c,ref,v,s,calls=boundary_fixture(tmp_path,monkeypatch,stage,now,current_end)
    with pytest.raises(TimeoutError):m.run_stage(c,ref,stage,tmp_path,2000.,v,s)
    assert calls==[], 'No process boundary after original or current allocation expiry'


@pytest.mark.parametrize('current_end,want',[(1900.,1240.),(1160.,1100.)])
def test_review244_valid_normal_child_starts_once_with_nonincreasing_bound(tmp_path,monkeypatch,current_end,want):
    m,c,ref,v,s,calls=boundary_fixture(tmp_path,monkeypatch,'fresh',1010.,current_end)
    result=m.run_stage(c,ref,'fresh',tmp_path,2000.,v,s)
    assert len(calls)==1 and result['exit_code']==0 and result['term_sent_at'] is None
    assert result['deadline_unix']==want
    command=calls[0]['command'];assert float(command[command.index('--deadline')+1])==want
    assert json.loads((tmp_path/'fresh/data-parameters.json').read_text())['bound_diagnostic_deadline']==want
    assert (tmp_path/'fresh/pipeline-observation.json').is_file()


def test_review244_actual_observer_rejects_late_reaped_zero(tmp_path,monkeypatch):
    m,c,ref,v,s,calls=boundary_fixture(tmp_path,monkeypatch,'fresh',1010.,1900.,late_reap=True)
    with pytest.raises(TimeoutError):m.run_stage(c,ref,'fresh',tmp_path,2000.,v,s)
    assert len(calls)==1 and not (tmp_path/'fresh/pipeline-observation.json').exists()
