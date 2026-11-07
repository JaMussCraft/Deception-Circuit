"""Supplemental Task3 guards. Frozen RED259 originals remain unchanged."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_full_score_release import module,require,rejects,chain,gpu_c,request,remote_fixture,execute_remote,t1,t2
from test_full_score_usage import fixture as usage_fixture,NOW


@pytest.mark.parametrize('fault',[None,'future','stale','reservation','successor','normalization','running-reader','released'])
def test_cutover_complete_pair_and_fresh_no_reader_interval(fault):
    m=module();validate=require(m,'validate_cutover')
    value=dict(observed_unix=1000.,quiescent=True,active_readers=[],root_cutover_attested=True,
        originals_preserved=True,new_reservation_complete=True,native_successor_complete=True,
        native_normalization_complete=True,readers_released=False)
    validate(value,now=1001.)
    if fault is None:return
    if fault=='future':value['observed_unix']=1002.
    elif fault=='stale':value['observed_unix']=900.
    elif fault=='reservation':value['new_reservation_complete']=False
    elif fault=='successor':value['native_successor_complete']=False
    elif fault=='normalization':value['native_normalization_complete']=False
    elif fault=='running-reader':value.update(active_readers=['A3-running'],quiescent=False)
    elif fault=='released':value['readers_released']=True
    with pytest.raises(rejects(m)):validate(value,now=1001.)


def test_nonzero_points_offset_does_not_shift_checkpoint_backward(monkeypatch):
    m=module();monkeypatch.setattr(m.time,'time',lambda:NOW)
    u,s=usage_fixture(live=20.5,cached=20,since=119)
    result=m.validate_usage(u,s,'exact')
    assert result['projected_points']=='124.5' and result['next_checkpoint_points']=='125'
    u['weekly']['used_percent']=21
    with pytest.raises(rejects(m)):m.validate_usage(u,s,'exact')


@pytest.mark.parametrize('fault',['publication','entry-floor'])
def test_remote_publication_deadline_and_entry_floor_are_independent(tmp_path,monkeypatch,fault):
    m=module();control=tmp_path/'control';control.mkdir();p,f=remote_fixture(m,control)
    execute_remote(m,p,f,monkeypatch)
    case=tmp_path/'case';case.mkdir();p,f=remote_fixture(m,case)
    if fault=='publication':p['publication_deadline']=1
    else:p['resources']['minimum_entry_seconds']=7201
    with pytest.raises((ValueError,AssertionError)):execute_remote(m,p,f,monkeypatch)
    assert not Path(p['final']).exists() and Path(p['pending']).exists()


def test_cpu_capture_helper_is_required_before_any_composite():
    require(module(),'capture_cpu')


def test_native_lineage_capture_helper_is_required_before_transfer():
    require(module(),'collect_native_closure')


@pytest.mark.parametrize('fault',[None,'modified-proof','changed-lineage','new-transition','future-finalization'])
def test_sealed_cutover_later_reuse_requires_same_authorized_native_pair(tmp_path,monkeypatch,fault):
    m=module();authenticate=require(m,'authenticate_cutover')
    snapshot=tmp_path/'original-ledger.json';snapshot.write_text('{}')
    ref=dict(path=str(tmp_path/'mapping'),files={'payload.json':{'sha256':'a'*64,'nbytes':1}})
    normalized=dict(active_mapping_reference=ref,mapping_lineage_references=[ref],original_snapshot_path=str(snapshot))
    g=dict(actual_job_id='456',reservation_id='new',mapping_origin_sha256='b'*64)
    value=dict(observed_unix=1000.,finalized_unix=1001.,quiescent=True,active_readers=[],
        root_cutover_attested=True,originals_preserved=True,new_reservation_complete=True,native_successor_complete=True,
        native_normalization_complete=True,readers_released=False,actual_job_id='456',reservation_id='new',
        mapping_origin_sha256='b'*64,active_mapping_reference=ref,mapping_lineage_references=[ref],ledger_sha256=m.sha(snapshot))
    proof=tmp_path/'cutover.json';proof.write_bytes(m.encoded(value))
    b=dict(cutover_attestation=dict(path=str(proof),sha256=m.sha(proof)))
    monkeypatch.setattr(m.time,'time',lambda:1202.)
    assert authenticate(b,g,normalized)['finalized_unix']==1001.
    if fault is None:return
    if fault=='modified-proof':proof.write_bytes(proof.read_bytes()+b' ')
    elif fault=='changed-lineage':normalized['mapping_lineage_references']=[]
    elif fault=='new-transition':normalized['active_mapping_reference']=dict(path='/new',files={})
    elif fault=='future-finalization':
        value['finalized_unix']=1203.;proof.write_bytes(m.encoded(value));b['cutover_attestation']['sha256']=m.sha(proof)
    with pytest.raises(rejects(m)):authenticate(b,g,normalized)


def publish_fixture(m,x,tmp_path,monkeypatch):
    """Fake external boundaries; real root CPU/lineage/staging/remote functions."""
    from test_full_score_release import budget_fixture
    monkeypatch.setattr(m,'ROOT',tmp_path)
    monkeypatch.setattr(m.time,'time',lambda:1202.)
    g=x.g;c=x.c
    ledger,mapping,budget_g=budget_fixture(m,7200)
    for key in ('actual_job_id','reservation_id','expected_account','allowed_partitions','experiment_limits','global_limit','resources'):
        g[key]=copy.deepcopy(budget_g[key])
    g['actual_job_id']=x.r['actual_future_GPU_job_id'];g['expected_qos']='gpu'
    ledger['reservations'][1].update(job_id=g['actual_job_id'],output_dir=g['main_root'])
    mapping['entries'][1]['actual_entry']=copy.deepcopy(ledger['reservations'][1])
    g['physical_Alignment_root']=str(tmp_path/'remote');g['canonical_ledger']=str(tmp_path/'ledger.json')
    mapping['ledger_path']=g['canonical_ledger'];t1.save(g['canonical_ledger'],ledger)
    frozen=tmp_path/'original-ledger.json';t1.save(frozen,ledger)
    def bundle(name,payload):
        root=tmp_path/name;root.mkdir();t1.save(root/'payload.json',payload);t1.save(root/'COMPLETE.json',{'complete':True});return str(root)
    admission=bundle('original-admission',{'id':'old','preserved':True})
    mapping.update(ledger_snapshot_path=str(frozen),ledger_sha256=m.sha(frozen),original_admission_paths=[admission])
    origin=bundle('mapping-origin',mapping);successor=bundle('mapping-successor',mapping)
    g['mapping_origin']=origin;g['mapping_origin_sha256']=m.sha(Path(origin)/'COMPLETE.json')
    def object_reference(path):
        path=Path(path);return dict(path=str(path),files={f.name:dict(sha256=m.sha(f),nbytes=f.stat().st_size) for f in path.iterdir()})
    refs=[object_reference(origin),object_reference(successor)]
    normalized=dict(current_snapshot_sha256=m.sha(g['canonical_ledger']),original_snapshot_path=str(frozen),
        active_mapping_reference=refs[-1],original_mapping_reference=refs[0],mapping_lineage_references=refs)
    events=[]
    def normalize(path,**kwargs):
        assert path==origin and kwargs['include_envelope'] is False and kwargs['identity']['purpose']=='A2 original source50e full scoring'
        assert 'injected' not in kwargs
        events.append('native-normalize');return copy.deepcopy(normalized)
    facade=SimpleNamespace(normalize_ledger=normalize,read_object=lambda path:m.read(Path(path)/'payload.json'),object_reference=object_reference)
    monkeypatch.setattr(m,'native_runtime',lambda g:facade)
    monkeypatch.setattr(m,'verify_runtime_pins',lambda *args:events.append('all-packet-pins'))
    monkeypatch.setattr(m,'usage',lambda b,work,label:events.append('usage:'+label))
    # Fully captured closed source511+4; no native source is imported here.
    runtime=tmp_path/'source';runtime.mkdir();source={};links={}
    for n in range(511):
        p=runtime/('m%03d.py'%n);p.write_text('# tiny source fixture\n');source[p.name]=m.sha(p)
    for n in range(4):
        target=tmp_path/('alias-target-%d'%n);target.write_text('fixture input')
        p=runtime/('input%d'%n);p.symlink_to(target);links[p.name]=str(target)
    g['runtime']=str(runtime);t1.save(g['snapshot'],dict(source_commit=m.SOURCE,runtime_root=str(runtime),source_sha256=source,input_links=links,source_code_symlinks=False))
    g['snapshot_sha256']=m.sha(g['snapshot'])
    t1.save(g['input_manifest'],dict(ordinary_sha256={},aliases={}))
    g['input_manifest_sha256']=m.sha(g['input_manifest'])
    catalogues=[];captures=[];cpu_root=tmp_path/'CPU';cpu_root.mkdir();c['evidence_output']=str(cpu_root)
    for n in range(4):
        path=tmp_path/('catalogue%d'%n)/('held_out.json' if n%2==0 else 'directions.json');t1.save(path,{'sets':[]})
        row=dict(virtual_path=str(path),sha256=m.sha(path));catalogues.append(row)
        captured=cpu_root/('catalogue%d.json'%n);captured.write_bytes(path.read_bytes())
        captures.append(dict(row,bytes=captured.stat().st_size,captured_bytes_path=str(captured)))
    g['minimum_registry_paths']=[r['virtual_path'] for r in catalogues]
    t1.save(g['protection_proof'],dict(complete=True,independently_accepted=True,catalogues=catalogues,nonempty_heldout_closure_reviewed=False))
    g['protection_proof_sha256']=m.sha(g['protection_proof'])
    source_plan=tmp_path/'source-plan.json';source_plan.write_bytes(Path(g['source_plan']).read_bytes())
    g['source_plan']=str(source_plan);g['source_plan_sha256']=m.sha(source_plan)
    for name,path in [('GPU',Path(g['packet_manifest'])),('CPU',tmp_path/'CPU-packet_manifest.json')]:
        member=tmp_path/(name+'-member.py');member.write_text('# fixture owning source\n')
        t1.save(path,{'files':{str(member):m.sha(member)}})
        if name=='GPU':g['packet_manifest_sha256']=m.sha(path);g['launch_packet_manifest_sha256']=m.sha(path)
        else:c['packet_manifest']=dict(path=str(path),sha256=m.sha(path));c['packet_manifest_sha256']=m.sha(path)
    c['GPU_packet_manifest_sha256']=g['launch_packet_manifest_sha256']
    # Parameters, guard, child and COMPLETE serialize exactly as actual Task2.
    t1.save(x.guard.CONFIG,g)
    r=copy.deepcopy(x.r);r['final_GPU_bound_config_sha256']=t1.sha(x.guard.CONFIG)
    r['standing_packet_manifest_sha256']=c['packet_manifest_sha256'];r['GPU_packet_manifest_sha256']=c['GPU_packet_manifest_sha256']
    rpath=tmp_path/'request.json';rpath.write_bytes(m.encoded(r));rsha=m.sha(rpath)
    w=copy.deepcopy(x.w);w['resources']=g['resources'];w['bound_config_sha256']=r['final_GPU_bound_config_sha256'];w['launch_packet_manifest_sha256']=g['launch_packet_manifest_sha256'];x.marker.write_bytes(m.encoded(w))
    r['GPU_WAITING_marker_sha256']=m.sha(x.marker);rpath.write_bytes(m.encoded(r));rsha=m.sha(rpath)
    x.supervisor.validate_request(c,r,w,now=1010.)
    child,result=t2.completion();child['request_sha256']=rsha
    result.update(request_sha256=rsha,groups_file_sha256=g['groups_file_sha256'],
        actual_Delta_owning_guards_passed=True,stable_Delta_catalogues_before_after=True,
        catalogue_capture_files=captures,catalogues=catalogues)
    result['source_before']['catalogues']={r['virtual_path']:r['sha256'] for r in catalogues}
    result['source_after']=copy.deepcopy(result['source_before'])
    params=dict(phase='full_score',phase_request_sha256=rsha,actual_CPU_job_id=c['standing_CPU_job_id'],actual_future_GPU_job_id=g['actual_job_id'])
    for n,value in [('request.json',r),('WAITING.json',w),('parameters.json',params),('guard-result.json',result)]:(cpu_root/n).write_bytes(m.encoded(value))
    child['guard_result_sha256']=m.sha(cpu_root/'guard-result.json');t1.save(cpu_root/'child-execution.json',child)
    # Actual supervisor insists on original catalogue path set. The normal CPU
    # side already passed in chain; namespace-only fixture changes are confined
    # to the owning constant while its COMPLETE constructor remains unchanged.
    monkeypatch.setattr(x.supervisor,'CATALOGUES',tuple(g['minimum_registry_paths']))
    q=x.supervisor.validate_child_completion(c,r,child,result,now=1201.)
    gpu_ref=dict(path=str(x.guard.CONFIG),sha256=r['final_GPU_bound_config_sha256'])
    cpu_config=tmp_path/'CPU-bound.json';t1.save(cpu_config,c);cpu_ref=dict(path=str(cpu_config),sha256=m.sha(cpu_config))
    q.update(CPU_bound_config_sha256=cpu_ref['sha256'],parameters_sha256=m.sha(cpu_root/'parameters.json'),child_execution_sha256=m.sha(cpu_root/'child-execution.json'))
    t1.save(cpu_root/'COMPLETE.json',q)
    for key in ('base_parameters','resource_proof'):
        path=tmp_path/('CPU-'+key+'.json');t1.save(path,{'fixture':key});c[key]=dict(path=str(path),sha256=m.sha(path))
    # Bind after all prospective CPU config fields are present.
    t1.save(cpu_config,c);cpu_ref['sha256']=m.sha(cpu_config);q['CPU_bound_config_sha256']=cpu_ref['sha256'];t1.save(cpu_root/'COMPLETE.json',q)
    attestation=dict(observed_unix=1000.,finalized_unix=1001.,quiescent=True,active_readers=[],root_cutover_attested=True,
        originals_preserved=True,new_reservation_complete=True,native_successor_complete=True,native_normalization_complete=True,
        readers_released=False,actual_job_id=g['actual_job_id'],reservation_id=g['reservation_id'],mapping_origin_sha256=g['mapping_origin_sha256'],
        active_mapping_reference=refs[-1],mapping_lineage_references=refs,ledger_sha256=m.sha(frozen))
    cut=tmp_path/'cutover.json';t1.save(cut,attestation)
    hm=tmp_path/'helper-manifest.json';hm_member=tmp_path/'root-member.py';hm_member.write_text('# tiny root fixture')
    t1.save(hm,{'files':{str(hm_member):m.sha(hm_member)}})
    b=dict(state_directory=str(tmp_path/'root-state'),GPU_execution_output=g['evidence_root'],GPU_release_directory=g['release_directory'],
        gpu_config=gpu_ref,standing_config=cpu_ref,cutover_attestation=dict(path=str(cut),sha256=m.sha(cut)),
        helper_manifest=dict(path=str(hm),sha256=m.sha(hm)))
    producer=m.Producer(b,g,c,'full_score');producer.work.mkdir(parents=True)
    record=dict(actual_GPU_job_id=g['actual_job_id'],GPU_config_sha256=gpu_ref['sha256'],request=str(rpath),request_sha256=rsha,
        marker=str(x.marker),marker_sha256=m.sha(x.marker),initial_GPU_end_epoch=9000.)
    t1.save(producer.work/'trigger-record.json',record)
    cache=dict(reference_sha256=m.cache_gate.REFERENCE_SHA,original_full_weight_proof_sha256=m.cache_gate.FULL_PROOF_SHA,
        revision=m.cache_gate.REVISION,full_weights_rehashed=False,model_loaded=False,checked_at_unix=1202.,metadata=[],weights=[])
    remote_files={}
    f=dict(JobId=g['actual_job_id'],JobState='RUNNING',Account=g['expected_account'],QOS='gpu',Partition='GPU-shared',
        UserId='test('+str(__import__('os').getuid())+')',NumNodes='1',NumCPUs='2',Requeue='0',Restarts='0',TimeLimit='02:00:00',
        EndTime='1970-01-01T02:30:00',AllocTRES='cpu=2,mem=32G,node=1,gres/gpu=1,gres/gpu:h100-80=1',TresPerNode='gres:gpu:h100-80:1')
    raw=' '.join(k+'='+v for k,v in f.items())
    existing=[Path(g[k]) for k in ('image','bank_file','bank_manifest','groups')]+list(runtime.glob('*.py'))
    for path in existing:remote_files[m.physical(g,path)]=path.read_bytes()
    alias_reports={m.physical(g,str(runtime/name)):dict(literal_target=target,resolved_target=m.physical(g,Path(target).resolve()),target_kind='file',target_sha256=m.sha(target)) for name,target in links.items()}
    class FakeTransport:
        attack=None
        def inspect(self,paths,waiting,final):
            events.append('remote-inspect')
            return dict(files={path:m.sha_bytes(remote_files[path]) if path in remote_files else None for path in paths},
                waiting_sha256=record['marker_sha256'],release_exists=False,pending_exists=False,raw_scontrol=raw,aliases={k:v for k,v in alias_reports.items() if k in paths})
        def stage(self,files,work):
            events.append('stage')
            for path,data in files.items():remote_files[m.physical(g,path)]=data
            if self.attack=='catalogue':Path(catalogues[0]['virtual_path']).write_text('changed')
            elif self.attack=='CPU':(cpu_root/'COMPLETE.json').write_text('{}')
            elif self.attack=='SIF':remote_files[m.physical(g,g['image'])]=b'changed SIF'
            elif self.attack=='ledger':Path(g['canonical_ledger']).write_text('{}')
            elif self.attack=='WAITING':x.marker.write_text('{}')
        def cache_check(self):
            events.append('cache')
            result=copy.deepcopy(cache)
            if self.attack=='cache' and 'stage' in events:result['revision']='changed'
            return result
        def publish(self,local,final,waiting,waiting_sha,expiry,initial_end_epoch):
            events.append('publish')
            pending=Path(final+'.pending');pending.parent.mkdir(parents=True,exist_ok=True);pending.write_bytes(Path(local).read_bytes())
            remote_waiting=Path(waiting);remote_waiting.parent.mkdir(parents=True,exist_ok=True);remote_waiting.write_bytes(x.marker.read_bytes())
            payload=dict(pending=str(pending),final=final,sha=m.sha(local),waiting=waiting,waiting_sha=waiting_sha,
                expiry=expiry,job=g['actual_job_id'],account=g['expected_account'],phase='full_score',resources=g['resources'],
                expected_qos=g['expected_qos'],allowed_partitions=g['allowed_partitions'],source_commit=m.SOURCE,
                strict_payload=True,initial_end_epoch=initial_end_epoch,publication_deadline=w['publication_deadline'])
            execute_remote(m,payload,f,monkeypatch)
            assert Path(final).read_bytes()==Path(local).read_bytes() and not pending.exists()
            return dict(published=True,sha256=m.sha(final))
    producer.transport=FakeTransport()
    return producer,events,cpu_root,remote_files,normalized


@pytest.mark.parametrize('fault',[None,'catalogue','CPU','SIF','ledger','WAITING','cache'])
def test_full_fake_transport_keeps_CPU_immutable_and_fails_closed_on_transfer_drift(chain,tmp_path,monkeypatch,fault):
    m=module();require(m,'capture_cpu');require(m,'collect_native_closure');require(m,'authenticate_cutover')
    producer,events,cpu,remote,normalized=publish_fixture(m,chain,tmp_path,monkeypatch)
    before=(cpu/'COMPLETE.json').read_bytes();producer.transport.attack=fault
    if fault:
        with pytest.raises((ValueError,AssertionError,KeyError)):producer.publish()
        assert 'stage' in events and 'publish' not in events
    else:
        assert producer.publish()['published'] is True
        release=m.read(producer.work/'root-release.json')
        assert release['resources']==producer.g['resources'] and release['full_scoring_admitted'] is True
        assert 'pilot_root' not in release and 'bank_and_prefix4_only' not in release
        assert release['active_mapping_reference']==normalized['active_mapping_reference']
        assert (cpu/'COMPLETE.json').read_bytes()==before
        composite=m.read(release['delta_preflight_receipt'])
        assert composite['continuous_live_Delta'] is False
        assert composite['actual_CPU_COMPLETE']['sha256']==m.sha(cpu/'COMPLETE.json')
        monkeypatch.setattr(chain.guard,'MAIN',producer.g['main_root'])
        monkeypatch.setattr(chain.guard,'C',producer.g)
        assert chain.guard.validate_release(release)==composite
        assert events.count('native-normalize')==2 and events.count('cache')==2
        with pytest.raises(FileExistsError):producer.publish()
        assert events.count('publish')==1


@pytest.mark.parametrize('fault',[None,'old-snapshot','old-charge','original-admission','missing-successor'])
def test_original_native_normalizer_preserves_full_mapping_chain(tmp_path,monkeypatch,fault):
    """CPU-allocation-only test: imports exact source50e native normalizer.

    Fixture changes only its canonical ledger constant, never injected=True or
    scientific loader/geometry. No native/model/GPU work runs on the login node.
    """
    import importlib
    import os
    import sys
    from test_full_score_release import budget_fixture
    source=Path(os.environ['A2_TASK3_NATIVE_SOURCE'])
    monkeypatch.syspath_prepend(str(source))
    ar=importlib.import_module('component_analysis.a3_direction_runtime')
    assert Path(ar.__file__).resolve()==source/'component_analysis/a3_direction_runtime.py'
    m=module();ledger,mapping,g=budget_fixture(m,7200)
    canonical=tmp_path/'ledger.json';frozen_old=tmp_path/'old-ledger.json';frozen_new=tmp_path/'new-ledger.json'
    g['canonical_ledger']=str(canonical);mapping['ledger_path']=str(canonical)
    old=dict(reservations=[copy.deepcopy(ledger['reservations'][0])],totals={'reserved_gpu_hours':.75},caps=ledger['caps'])
    for path,value in [(canonical,ledger),(frozen_old,old),(frozen_new,ledger)]:t1.save(path,value)
    monkeypatch.setattr(ar,'CANONICAL_LEDGER',canonical)
    successors=tmp_path/'successors';successors.mkdir()
    admission=dict(id='original-admission-fixture',purpose='immutable test receipt')
    admission['admission_sha256']=ar.workload.digest(admission)
    admission_path=tmp_path/'original-admission';ar.publish_object(admission_path,admission)
    old_mapping=dict(kind='a3_root_ledger_mapping_v1',generation=0,ledger_path=str(canonical),
        ledger_snapshot_path=str(frozen_old),ledger_sha256=m.sha(frozen_old),max_age_seconds=900,
        refresh_wait_seconds=0,successor_directory=str(successors),expected_entry_ids=['old'],
        entries=[mapping['entries'][0]],original_admission_paths=[str(admission_path)],
        original_admission_references={str(admission_path):ar.object_reference(admission_path)},
        storage_capacities={'fixture':True},contingency_gpu_hours=0)
    origin=tmp_path/'mapping-origin';ar.publish_object(origin,old_mapping)
    new_mapping=copy.deepcopy(old_mapping)
    new_mapping.update(generation=1,predecessor_reference=ar.object_reference(origin),
        ledger_snapshot_path=str(frozen_new),ledger_sha256=m.sha(frozen_new),
        expected_entry_ids=['old','new'],entries=mapping['entries'])
    successor=successors/'mapping-000001';ar.publish_object(successor,new_mapping)
    g['mapping_origin']=str(origin)
    monkeypatch.setattr(m,'native_runtime',lambda g:ar)
    before={str(path):path.read_bytes() for root in (origin,successor,admission_path) for path in root.iterdir()}
    captured,normalized,budget=m.collect_native_closure(g)
    assert normalized['original_mapping_reference']==ar.object_reference(origin)
    assert normalized['active_mapping_reference']==ar.object_reference(successor)
    assert len(normalized['mapping_lineage_references'])==2
    assert budget['exact_requested_GPU_seconds_total']=='9900'
    assert str(frozen_old) in captured and str(frozen_new) in captured
    assert all(captured[path]==raw and Path(path).read_bytes()==raw for path,raw in before.items())
    if fault is None:return
    if fault=='old-snapshot':frozen_old.write_text('{}')
    elif fault=='old-charge':
        ledger['reservations'][0]['reserved_gpu_hours']=0;t1.save(canonical,ledger)
    elif fault=='original-admission':(admission_path/'payload.json').write_text('{}')
    elif fault=='missing-successor':
        # Remove only this test's completed successor, preserving on-disk origin.
        for path in successor.iterdir():path.unlink()
        successor.rmdir()
    with pytest.raises((ValueError,AssertionError)):m.collect_native_closure(g)


def test_every_operational_packet_member_is_in_transfer_closure(tmp_path):
    m=module();capture=require(m,'collect_packet_files');refs=[];expected={}
    for name in ('root','GPU','CPU'):
        member=tmp_path/(name+'.py');member.write_text('# actual pinned member\n');expected[str(member)]=member.read_bytes()
        manifest=tmp_path/(name+'-manifest.json');manifest.write_bytes(m.encoded({'files':{str(member):m.sha(member)}}))
        refs.append(dict(path=str(manifest),sha256=m.sha(manifest)));expected[str(manifest)]=manifest.read_bytes()
    b=dict(helper_manifest=refs[0]);g=dict(packet_manifest=refs[1]['path'],packet_manifest_sha256=refs[1]['sha256']);c=dict(packet_manifest=refs[2])
    assert capture(b,g,c)==expected
    member.write_text('# changed')
    with pytest.raises(rejects(m)):capture(b,g,c)


def test_remote_inspection_reports_literal_alias_target_and_resolved_file(tmp_path,monkeypatch):
    import contextlib,io,os,subprocess
    m=module();target=tmp_path/'data';target.write_bytes(b'input');alias=tmp_path/'alias';alias.symlink_to(target)
    waiting=tmp_path/'WAITING.json';waiting.write_text('{}')
    payload=dict(files=[str(alias)],waiting=str(waiting),final=str(tmp_path/'release'),job='456')
    monkeypatch.setattr(subprocess,'check_output',lambda *args,**kwargs:'JobId=456')
    output=io.StringIO()
    with contextlib.redirect_stdout(output):exec(compile(m.inspection_program(payload),'fake-remote','exec'),{})
    result=json.loads(output.getvalue())
    assert result.get('aliases')=={str(alias):dict(literal_target=str(target),resolved_target=str(target),target_kind='file',target_sha256=m.sha(target))}


def test_proof_reference_closure_captures_original_cache_and_CPU_sidecars(tmp_path):
    m=module();capture=require(m,'collect_reference_closure')
    leaf=tmp_path/'original-proof.json';leaf.write_text('{"weight_paths": ["never-read.safetensors"]}')
    reference=dict(path=str(leaf),sha256=m.sha(leaf))
    parent=tmp_path/'wrapper.json';parent.write_bytes(m.encoded({'reference':reference,'original_full_proof':reference}))
    root=dict(path=str(parent),sha256=m.sha(parent))
    assert capture([root])=={str(parent):parent.read_bytes(),str(leaf):leaf.read_bytes()}
    leaf.write_text('{}')
    with pytest.raises(rejects(m)):capture([root])


@pytest.mark.parametrize('fault',[None,'active-mismatch','backward-reset','cached-before-reset',
    'future-checked','stale-live','naive-timestamp','at80','rollback'])
def test_expired_post_reset_metadata_never_grants_above80_authority(monkeypatch,fault):
    import datetime
    m=module();monkeypatch.setattr(m.time,'time',lambda:NOW)
    u,s=usage_fixture(live=45,cached=44,since=100)
    old=NOW-1000;s=s.replace('captured reset '+str(u['weekly']['resets_at']),'captured reset '+str(old))
    result=m.validate_usage(u,s,'exact')
    assert result['route']=='expired_post_reset' and result['ordinary_cap_percent']==80
    if fault is None:return
    stamp=lambda epoch:datetime.datetime.fromtimestamp(epoch,datetime.timezone.utc).isoformat()
    if fault=='active-mismatch':s=s.replace('exception: expired','exception: active')
    elif fault=='backward-reset':u['weekly']['resets_at']=old-1
    elif fault=='cached-before-reset':s=s.replace(stamp(NOW),stamp(old-1))
    elif fault=='future-checked':u['checked_at']=stamp(NOW+1)
    elif fault=='stale-live':u['checked_at']=stamp(NOW-61)
    elif fault=='naive-timestamp':u['checked_at']=datetime.datetime.fromtimestamp(NOW).isoformat()
    elif fault=='at80':u['weekly']['used_percent']=80
    elif fault=='rollback':u['weekly']['used_percent']=43
    with pytest.raises(rejects(m)):m.validate_usage(u,s,'exact')
