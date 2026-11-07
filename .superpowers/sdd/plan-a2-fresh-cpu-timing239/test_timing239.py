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
