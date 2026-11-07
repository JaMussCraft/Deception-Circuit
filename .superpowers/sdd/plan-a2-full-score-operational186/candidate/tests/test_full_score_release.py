"""Task3 RED: real accepted wrapper interfaces, stdlib fixtures only.

Removing full-only identity, immutable COMPLETE, duration equality or atomic
remote revalidation must fail these tests. No fixture grants actual admission.
"""
import ast
import copy
import contextlib
import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

import pytest

ROOT = Path(os.environ.get('A2_ROOT_UNDER_TEST', str(Path(__file__).resolve().parents[1] / 'root')))
ACCEPTED = Path(os.environ.get('A2_TASK3_ACCEPTED', str(Path(__file__).resolve().parents[1])))
sys.path.insert(0, str(ACCEPTED / 'tests'))
import test_full_score_controller as t1
import test_full_score_cpu as t2
if os.environ.get("A2_TASK3_FIXTURES"):
    t1.PACKET = Path(os.environ["A2_TASK3_FIXTURES"])
t1.GPU = ACCEPTED / "gpu"
t2.CPU = ACCEPTED / "cpu"
# Register only the accepted tiny fixture, never accepted suites by star import.
gpu_c = t1.c


def module(name='helper'):
    path = ROOT / (name + '.py')
    assert path.is_file(), 'FULL_SCORE_ROOT_IMPLEMENTATION_MISSING: ' + str(path)
    sys.path.insert(0, str(ROOT))
    sys.modules.pop('cache_gate', None)
    spec = importlib.util.spec_from_file_location('task3_' + name, str(path))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    assert Path(result.__file__).resolve() == path.resolve()
    return result


def require(m, name):
    function = getattr(m, name, None)
    assert callable(function), 'FULL_SCORE_ROOT_IMPLEMENTATION_MISSING: callable ' + name
    return function


def rejects(m):
    return (getattr(m, 'Rejected', ValueError), ValueError, AssertionError)


@pytest.fixture
def chain(gpu_c, monkeypatch):
    guard, marker, waiting = t2.task1_waiting(gpu_c, monkeypatch)
    c, request = t2.task2_from_actual(gpu_c, guard, marker, marker.read_bytes())
    supervisor = t2.module('supervisor')
    supervisor.validate_request(c, request, waiting, now=1010.)
    child, result = t2.completion()
    result.update(groups_file_sha256=c['frozen_G3_sha256'],
                  actual_future_GPU_job_id=gpu_c['actual_job_id'])
    # These are the actual validate-phase child receipt fields retained by the
    # actual supervisor, not new completion authority introduced by this test.
    result.update(actual_Delta_owning_guards_passed=True,
                  stable_Delta_catalogues_before_after=True,
                  immutable_CPU_proof_not_rewritten=True)
    complete = supervisor.validate_child_completion(c, request, child, result, now=1201.)
    return SimpleNamespace(g=gpu_c, c=c, r=request, w=waiting, guard=guard,
                           marker=marker, complete=complete, supervisor=supervisor)


def request(m, x, now=1005.):
    return m.construct_request(x.w, x.c, x.g, t1.sha(x.guard.CONFIG),
                               str(x.marker), t1.sha(x.marker), now)


def test_request_generated_from_actual_Task1_WAITING_accepted_by_actual_Task2(chain):
    m = module(); r = request(m, chain)
    assert set(r) == set(chain.r)
    assert chain.supervisor.validate_request(chain.c, r, chain.w, now=1010.) == r
    assert r['GPU_WAITING_marker_sha256'] == t1.sha(chain.marker)
    assert 'H100_packet_manifest_sha256' not in r


@pytest.mark.parametrize('field,value', [('phase','bank'), ('phase','prefix4'),
    ('job_id','999'), ('source_commit','0'*40), ('bound_config_sha256','0'*64),
    ('groups_file_sha256','0'*64), ('bank_file_sha256','0'*64),
    ('bank_manifest_sha256','0'*64), ('bank_internal_payload_sha256','0'*64),
    ('launch_packet_manifest_sha256','0'*64), ('publication_deadline',1004.)])
def test_request_rejects_wrong_actual_waiting_binding(chain, field, value):
    m = module(); request(m, chain)  # positive control prevents vacuous rejection
    chain.w[field] = value
    with pytest.raises(rejects(m)): request(m, chain)


def test_request_rejects_changed_reviewed_resource_tuple(chain):
    m = module(); request(m, chain)
    chain.w['resources'] = dict(chain.w['resources'], CPUs=99)
    with pytest.raises(rejects(m)): request(m, chain)


@pytest.mark.parametrize('elapsed', [15.001, -0.001])
def test_trigger_freshness_fifteen_seconds_not_old_wait_window(chain, elapsed):
    m = module(); r = request(m, chain)
    m.check_request_fresh(r, r['root_trigger_issued_at'] + 15)
    with pytest.raises(rejects(m)): m.check_request_fresh(r, r['root_trigger_issued_at'] + elapsed)


def test_actual_Task2_COMPLETE_is_read_only_and_valid_full_domain(chain):
    m = module(); before = copy.deepcopy(chain.complete)
    m.validate_complete(chain.complete, chain.r, 'a'*64, chain.g, t1.sha(chain.guard.CONFIG),1202.)
    assert chain.complete == before


@pytest.mark.parametrize('field,value', [('phase','prefix4'), ('complete',False), ('status','PARTIAL'),
    ('full_rows',4), ('full_controls',0), ('full_domain_support_audit_complete',False),
    ('support_reason_mask_sha256','invalid'), ('actual_future_GPU_job_id','999'),
    ('actual_CPU_job_id','999'), ('bank_file_sha256','0'*64), ('bank_manifest_sha256','0'*64),
    ('waiting_sha256','0'*64), ('bound_gpu_config_sha256','0'*64),
    ('launch_packet_manifest_sha256','0'*64), ('timely_window',False),
    ('actual_Delta_owning_guards_passed',False), ('automatic_retry',True), ('model_loaded',True)])
def test_partial_old_or_changed_CPU_COMPLETE_never_admits(chain,field,value):
    m = module(); m.validate_complete(chain.complete,chain.r,'a'*64,chain.g,t1.sha(chain.guard.CONFIG),1202.)
    chain.complete[field] = value
    with pytest.raises(rejects(m)):
        m.validate_complete(chain.complete,chain.r,'a'*64,chain.g,t1.sha(chain.guard.CONFIG),1202.)


def test_existing_composite_schema_passes_actual_Task1_consumer(chain):
    # Interface control independent of missing Task3 production. Original CPU
    # proof is separate and remains immutable after the root composite changes.
    x = chain; cpu = Path(x.g['evidence_root'])/'CPU-COMPLETE.json'; t1.save(cpu,x.complete)
    before = cpu.read_bytes()
    rows = [dict(virtual_path=p,sha256=str(n)*64) for n,p in enumerate(x.g['minimum_registry_paths'])]
    composite = dict(complete=True,phase='full_score',source_commit=t2.SOURCE,
        actual_GPU_job_id=x.g['actual_job_id'],actual_Delta_owning_guards_passed=True,
        stable_Delta_catalogues_before_after=True,immutable_CPU_proof_not_rewritten=True,
        catalogues=rows,ledger_sha256='a'*64,actual_CPU_COMPLETE=dict(path=str(cpu),sha256=t1.sha(cpu)))
    proof = Path(x.g['evidence_root'])/'composite.json'; t1.save(proof,composite)
    release = t1.release(x.g)
    release.update(reservation_id=x.g['reservation_id'],main_root=x.guard.MAIN,current_usage_pass=True,
        delta_fresh_preflight_passed=True,waiting_sha256=t1.sha(x.marker),catalogues=rows,
        ledger_sha256='a'*64,delta_preflight_receipt=str(proof),delta_preflight_receipt_sha256=t1.sha(proof))
    assert x.guard.validate_release(release) == composite
    assert cpu.read_bytes() == before


@pytest.mark.parametrize('collision', ['final','pending'])
def test_atomic_publication_never_overwrites_or_renews(tmp_path,collision):
    m = module(); path = tmp_path/'release.json'
    prior = path if collision == 'final' else path.with_name(path.name+'.pending')
    prior.write_bytes(b'immutable original')
    with pytest.raises(FileExistsError): m.atomic_new(path,b'new authority')
    assert prior.read_bytes() == b'immutable original'


def budget_fixture(m, seconds=7201):
    g = dict(actual_job_id='456',reservation_id='new',expected_account='fixture-account',
        allowed_partitions=['GPU-shared'],main_root='/fixture/MAIN',canonical_ledger='/fixture/ledger',
        experiment_limits={'A1':25,'A2':60,'A3':40},global_limit=125,
        resources=dict(duration_seconds=seconds,CPUs=2,RAM_bytes=32*1024**3,GPU_count=1,
                       minimum_entry_seconds=600,finish_margin_seconds=120,child_cap_seconds=6600),
        maximum_reserved_gpu_hours=round(seconds/3600,4),exact_requested_GPU_seconds=seconds)
    rows = [dict(id='old',job_id='1',cluster='delta',account='old',partition='old',gpus=1,
        requested_minutes=45,reserved_gpu_hours=.75,source_commit='old',output_dir='/old',
        manifest_hash=None,status='CANCELLED'),dict(id='new',job_id='456',cluster='bridges2',
        account='fixture-account',partition='GPU-shared',gpus=1,requested_minutes=seconds/60,
        reserved_gpu_hours=round(seconds/3600,4),source_commit=m.SOURCE,output_dir='/fixture/MAIN',
        manifest_hash=None,status='PENDING')]
    # 7200 seconds exactly representable; fractional seconds case is deliberately
    # separate to expose incorrect float arithmetic or an inherited hour cap.
    ledger = dict(reservations=rows,totals=dict(reserved_gpu_hours=round(.75+seconds/3600,4)),
                  caps=dict(reserved_gpu_hours=125,max_concurrent_gpu_jobs=99))
    mapping = dict(ledger_path=g['canonical_ledger'],entries=[dict(reservation_id=r['id'],
        experiment='A1' if r['id']=='old' else 'A2',original_reserved_gpu_hours=r['reserved_gpu_hours'],
        actual_entry=copy.deepcopy(r)) for r in rows])
    return ledger,mapping,g


def test_budget_retains_cancelled_charge_and_accepts_reviewed_two_hour_duration():
    m = module(); ledger,mapping,g = budget_fixture(m,7200)
    before = copy.deepcopy((ledger,mapping)); result=m.validate_budget(ledger,mapping,g)
    assert result['exact_requested_GPU_seconds_total'] == '9900'
    assert (ledger,mapping) == before


@pytest.mark.parametrize('fault', ['missing-mapping','old-charge','duration','caps','concurrency'])
def test_budget_rejects_incomplete_or_reinterpreted_charge_lineage(fault):
    m = module(); ledger,mapping,g=budget_fixture(m,7200)
    m.validate_budget(ledger,mapping,g)
    if fault=='missing-mapping': mapping['entries'].pop(0)
    elif fault=='old-charge': ledger['reservations'][0]['reserved_gpu_hours']=0
    elif fault=='duration': g['resources']['duration_seconds']=7201
    elif fault=='caps': ledger['caps']['reserved_gpu_hours']=126
    elif fault=='concurrency': ledger['caps']['max_concurrent_gpu_jobs']=100
    with pytest.raises(rejects(m)): m.validate_budget(ledger,mapping,g)


def remote_fixture(m,tmp_path):
    pending=tmp_path/'release.pending'; waiting=tmp_path/'WAITING.json'
    pending.write_text('{"phase":"full_score"}');waiting.write_text('{}')
    end=time.time()+7200
    resources=dict(duration_seconds=7200,CPUs=2,RAM_bytes=32*1024**3,GPU_count=1,
                   minimum_entry_seconds=600,finish_margin_seconds=120,child_cap_seconds=6600)
    p=dict(pending=str(pending),final=str(tmp_path/'release.final'),sha=m.sha(pending),
        waiting=str(waiting),waiting_sha=m.sha(waiting),expiry=time.time()+100,job='456',
        account='fixture-account',phase='full_score',initial_end_epoch=end,
        finish_reserve_seconds=120,score_floor_seconds=600,resources=resources,
        expected_qos='gpu',allowed_partitions=['GPU-shared'],publication_deadline=time.time()+100)
    fields=dict(JobId='456',JobState='RUNNING',Account='fixture-account',QOS='gpu',Partition='GPU-shared',
        UserId='test('+str(os.getuid())+')',NumNodes='1',NumCPUs='2',Requeue='0',Restarts='0',
        TimeLimit='02:00:00',EndTime=datetime.datetime.fromtimestamp(end,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'),
        AllocTRES='cpu=2,mem=32G,node=1,gres/gpu=1,gres/gpu:h100-80=1',TresPerNode='gres:gpu:h100-80:1')
    return p,fields


def execute_remote(m,p,fields,monkeypatch):
    import subprocess
    monkeypatch.setattr(subprocess,'check_output',lambda argv,**kw:' '.join(k+'='+v for k,v in fields.items()))
    program=m.remote_publish_program(p)
    ast.parse(program,feature_version=(3,6))
    with contextlib.redirect_stdout(io.StringIO()): exec(compile(program,'fake-remote','exec'),{})


def test_actual_generated_remote_program_publishes_full_only_reviewed_resources(tmp_path,monkeypatch):
    m=module();p,fields=remote_fixture(m,tmp_path)
    execute_remote(m,p,fields,monkeypatch)
    assert Path(p['final']).read_bytes()==b'{"phase":"full_score"}'
    assert not Path(p['pending']).exists()


@pytest.mark.parametrize('fault',['state','job','account','cpu','memory','duration','waiting','expiry','collision','phase'])
def test_generated_remote_final_guard_rejects_resource_and_publication_races(tmp_path,monkeypatch,fault):
    m=module();control=tmp_path/'control';control.mkdir();p,f=remote_fixture(m,control)
    execute_remote(m,p,f,monkeypatch)  # rejection must not be vacuous
    case=tmp_path/'case';case.mkdir();p,f=remote_fixture(m,case)
    if fault=='state':f['JobState']='CANCELLED'
    elif fault=='job':f['JobId']='999'
    elif fault=='account':f['Account']='other'
    elif fault=='cpu':f['NumCPUs']='4'
    elif fault=='memory':f['AllocTRES']=f['AllocTRES'].replace('mem=32G','mem=64G')
    elif fault=='duration':f['TimeLimit']='01:00:00'
    elif fault=='waiting':Path(p['waiting']).write_text('{"changed":true}')
    elif fault=='expiry':p['expiry']=time.time()-1
    elif fault=='collision':Path(p['final']).write_text('original')
    elif fault=='phase':p['phase']='prefix4'
    with pytest.raises((AssertionError,ValueError,FileExistsError)):execute_remote(m,p,f,monkeypatch)
    assert Path(p['pending']).exists()
    if fault=='collision':assert Path(p['final']).read_text()=='original'
    else:assert not Path(p['final']).exists()


@pytest.mark.parametrize('operation',['trigger','publish'])
def test_each_root_operation_verifies_pinned_packet_before_external_work(tmp_path,monkeypatch,operation):
    m=module();events=[]
    b=dict(state_directory=str(tmp_path),GPU_execution_output='/fixture/evidence',
           GPU_release_directory='/fixture/releases')
    g=dict(actual_job_id='456')
    producer=m.Producer(b,g,{},'full_score')
    if operation=='publish':producer.work.mkdir(parents=True)
    class PinnedMemberChanged(RuntimeError):pass
    def check(*args):events.append('pins');raise PinnedMemberChanged('CPU member changed')
    monkeypatch.setattr(m,'verify_runtime_pins',check)
    monkeypatch.setattr(m,'usage',lambda *args:pytest.fail('usage preceded immutable pin failure'))
    monkeypatch.setattr(producer.transport,'fetch',lambda *args:pytest.fail('fetch preceded pin failure'))
    monkeypatch.setattr(producer.transport,'publish',lambda *args:pytest.fail('publication preceded pin failure'))
    with pytest.raises(PinnedMemberChanged):getattr(producer,operation)()
    assert events==['pins']


def test_pinned_manifest_mutation_rejects_without_adopting_new_digest(tmp_path):
    m=module();member=tmp_path/'supervisor.py';member.write_bytes(b'original CPU member')
    manifest=tmp_path/'manifest.json';manifest.write_bytes(m.encoded({'supervisor.py':m.sha(member)}))
    pin=m.sha(manifest);m.check_manifest(manifest,pin);member.write_bytes(b'changed CPU member')
    with pytest.raises(rejects(m)):m.check_manifest(manifest,pin)


def test_nonempty_protected_closure_without_owning_independent_review_rejects():
    m=module();m.validate_heldout({'sets':[]})
    with pytest.raises(rejects(m)):m.validate_heldout({'sets':[{'id':'fixture-protected'}]})


@pytest.mark.parametrize('fault',['active-reader','stale','not-cutover','released-early',
                                  'missing-mapping','changed-old-admission'])
def test_reader_cutover_requires_fresh_quiescence_and_completed_native_pair(fault):
    # Pure precondition checker only. It neither holds/cancels readers nor writes
    # a reservation/mapping, and introduces no native authority kind.
    m=module();validate=require(m,'validate_cutover')
    attestation=dict(observed_unix=1000.,quiescent=True,active_readers=[],
        root_cutover_attested=True,originals_preserved=True,new_reservation_complete=True,
        native_successor_complete=True,native_normalization_complete=True,readers_released=False)
    validate(attestation,now=1001.)
    if fault=='active-reader':attestation.update(quiescent=False,active_readers=['running-A3'])
    elif fault=='stale':attestation['observed_unix']=900.
    elif fault=='not-cutover':attestation['root_cutover_attested']=False
    elif fault=='released-early':attestation['readers_released']=True
    elif fault=='missing-mapping':attestation['native_successor_complete']=False
    elif fault=='changed-old-admission':attestation['originals_preserved']=False
    with pytest.raises(rejects(m)):validate(attestation,now=1001.)
