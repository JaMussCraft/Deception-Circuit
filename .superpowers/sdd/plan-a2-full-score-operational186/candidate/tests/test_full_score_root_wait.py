"""Task3 asynchronous CPU COMPLETE handoff: pure bounded polling, no daemon."""
from pathlib import Path
import pytest
from test_full_score_release import module,require,rejects


@pytest.mark.parametrize('fault',[None,'already-complete','FAILED','FAILED-with-COMPLETE','deadline','symlink'])
def test_one_finite_CPU_wait_never_renews_or_accepts_failure(tmp_path,monkeypatch,fault):
    m=module();wait=require(m,'wait_cpu_complete');clock=[1200.];sleeps=[]
    c=dict(evidence_output=str(tmp_path));w=dict(requested_at=1000.,publication_deadline=1300.)
    complete=tmp_path/'COMPLETE.json'
    if fault in ('already-complete','FAILED-with-COMPLETE'):complete.write_text('{}')
    elif fault=='symlink':complete.symlink_to(tmp_path/'missing')
    if fault in ('FAILED','FAILED-with-COMPLETE'):(tmp_path/'FAILED.json').write_text('{}')
    if fault=='deadline':clock[0]=1300.
    monkeypatch.setattr(m.time,'time',lambda:clock[0])
    def sleep(seconds):
        sleeps.append(seconds);assert 0<seconds<=.2;clock[0]+=seconds
        complete.write_text('{}')
    monkeypatch.setattr(m.time,'sleep',sleep)
    if fault in ('FAILED','FAILED-with-COMPLETE','deadline','symlink'):
        with pytest.raises((ValueError,AssertionError,TimeoutError)):wait(c,w)
        assert not sleeps
    else:
        assert wait(c,w)==complete
        assert len(sleeps)==(1 if fault is None else 0)
        assert w['publication_deadline']==1300.


@pytest.mark.parametrize('fault',['late','shortened','interrupted'])
def test_CPU_wait_respects_shortening_and_propagates_interruption(tmp_path,monkeypatch,fault):
    m=module();wait=require(m,'wait_cpu_complete');clock=[1200.];calls=[]
    c=dict(evidence_output=str(tmp_path));w=dict(requested_at=1000.,publication_deadline=1300.)
    complete=tmp_path/'COMPLETE.json';monkeypatch.setattr(m.time,'time',lambda:clock[0])
    def observer():
        calls.append('observe')
        if fault=='interrupted':raise InterruptedError('external observation interrupted')
        return 1250. if len(calls)==1 else 1200.
    def sleep(seconds):clock[0]+=seconds;complete.write_text('{}')
    monkeypatch.setattr(m.time,'sleep',sleep)
    if fault=='late':clock[0]=1300.01
    with pytest.raises((ValueError,AssertionError,TimeoutError,InterruptedError)):
        wait(c,w,deadline_observer=observer)
    assert w['publication_deadline']==1300.
    assert len(calls)<=2


def test_timely_CPU_proof_survives_child_deadline_until_original_GPU_publication_window(chain):
    m=module()
    m.validate_complete(chain.complete,chain.r,'a'*64,chain.g,chain.guard.sha(chain.guard.CONFIG),1299.)
    with pytest.raises(rejects(m)):
        m.validate_complete(chain.complete,chain.r,'a'*64,chain.g,chain.guard.sha(chain.guard.CONFIG),1300.)
    chain.complete['supervisor_finished_unix']=chain.complete['deadline_unix']
    with pytest.raises(rejects(m)):
        m.validate_complete(chain.complete,chain.r,'a'*64,chain.g,chain.guard.sha(chain.guard.CONFIG),1299.)


# Use the existing real Task1/Task2 chain fixture by explicit alias only.
from test_full_score_release import chain,gpu_c
from test_full_score_root_integration import publish_fixture


def test_FAILED_after_COMPLETE_during_transfer_supersedes_immutable_CPU_proof(chain,tmp_path,monkeypatch):
    m=module();producer,events,cpu,_,_=publish_fixture(m,chain,tmp_path,monkeypatch)
    original=producer.transport.stage
    def stage(files,work):
        original(files,work);(cpu/'FAILED.json').write_text('{"late_supervisor_failure":true}')
    monkeypatch.setattr(producer.transport,'stage',stage)
    with pytest.raises(rejects(m)):producer.publish()
    assert 'stage' in events and 'publish' not in events
