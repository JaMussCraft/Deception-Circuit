"""Remote Slurm ownership uses observed remote UID, never Delta UID."""
import contextlib,io,json,os,subprocess
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_full_score_release import module,remote_fixture,rejects


def test_root_remote_inspection_accepts_different_cluster_UID_and_rejects_wrong_owner(tmp_path,monkeypatch):
    m=module();monkeypatch.setattr(m,'ROOT',tmp_path);monkeypatch.setattr(m.time,'time',lambda:1202.)
    p,f=remote_fixture(m,tmp_path);f['UserId']='swong2(12345)';f['EndTime']='1970-01-01T02:30:00'
    monkeypatch.setattr(m.os,'getuid',lambda:99999)
    g=dict(actual_job_id='456',resources=p['resources'],expected_account=p['account'],expected_qos=p['expected_qos'],
           allowed_partitions=p['allowed_partitions'],physical_Alignment_root=str(tmp_path/'remote'))
    b=dict(state_directory=str(tmp_path/'state'),GPU_execution_output=str(tmp_path/'evidence'),GPU_release_directory=str(tmp_path/'releases'))
    producer=m.Producer(b,g,{},'full_score')
    observed=dict(raw_scontrol=' '.join(k+'='+v for k,v in f.items()),remote_uid=12345,
                  release_exists=False,pending_exists=False,waiting_sha256='a'*64,files={})
    producer.transport=SimpleNamespace(inspect=lambda *args:observed)
    assert producer.inspect([])['remote_uid']==12345
    observed['remote_uid']=54321
    with pytest.raises(rejects(m)):producer.inspect([])


def test_generated_inspection_records_actual_remote_UID(tmp_path,monkeypatch):
    m=module();waiting=tmp_path/'WAITING.json';waiting.write_text('{}')
    monkeypatch.setattr(subprocess,'check_output',lambda *args,**kwargs:'JobId=456')
    out=io.StringIO()
    with contextlib.redirect_stdout(out):exec(compile(m.inspection_program(dict(files=[],waiting=str(waiting),final=str(tmp_path/'release'),job='456')),'fake-remote','exec'),{})
    assert json.loads(out.getvalue()).get('remote_uid')==os.getuid()
