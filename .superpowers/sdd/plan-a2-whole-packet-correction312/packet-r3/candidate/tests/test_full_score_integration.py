"""Task4 synthetic whole-chain joins; root Slurm CPU only, never GPU authority.

No production code is copied. Accepted fixture builders isolate owning child I/O;
actual request/normal COMPLETE constructors, producer, generated remote publisher,
consumer, postactivation guard, native normalizer/protection/domain/stage writers
remain the originals. The only Popen is an observed fake score boundary.
"""
import copy
import gc
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest

PACKET = Path(__file__).resolve().parents[2]
META = json.loads((PACKET / 'dependencies.json').read_text())
FROZEN = Path(META['frozen_task3_packet'])
CANDIDATE = FROZEN / 'closure/sdd/plan-a2-full-score-operational186/candidate'
SOURCE = Path(META['original_runtime'])
os.environ['A2_ROOT_UNDER_TEST'] = str(CANDIDATE / 'root')
os.environ['A2_TASK3_ACCEPTED'] = str(CANDIDATE)
os.environ['A2_CPU_UNDER_TEST'] = str(CANDIDATE / 'cpu')
os.environ['A2_TASK3_FIXTURES'] = str(FROZEN / 'closure/sdd/plan-plan-a2-full-score-operational186/task1')
sys.path.insert(0, str(CANDIDATE / 'tests'))
from test_full_score_release import chain, gpu_c, module, t1, t2, budget_fixture
from test_full_score_root_integration import publish_fixture
from test_full_score_cache import fixture as cache_fixture
import test_full_score_usage as usage_fixtures


def native_modules(monkeypatch):
    # Match the unchanged CPU validate-phase and GPU host original cwd contract.
    # Native prepared artifacts retain relative source keys; never rewrite them.
    monkeypatch.chdir(str(SOURCE))
    assert Path.cwd().resolve()==SOURCE.resolve()
    monkeypatch.syspath_prepend(str(SOURCE))
    p = importlib.import_module('component_analysis.a2_pipeline')
    ar = importlib.import_module('component_analysis.a3_direction_runtime')
    assert Path(p.__file__).resolve() == SOURCE / 'component_analysis/a2_pipeline.py'
    assert Path(ar.__file__).resolve() == SOURCE / 'component_analysis/a3_direction_runtime.py'
    model_calls=[]
    monkeypatch.setattr(p,'_TASK4_MODEL_CALLS',model_calls,raising=False)
    def forbidden(*a, **kw):
        model_calls.append((a,kw))
        raise AssertionError('MODEL ENTRY FORBIDDEN IN SYNTHETIC CPU FIXTURES')
    monkeypatch.setattr(p.a1, 'load_model', forbidden)
    return p, ar


def native_lineage(m, producer, tmp_path, monkeypatch, ar):
    """Same reviewed two-generation native fixture, now joined to producer config."""
    g = producer.g
    ledger, mapping, _ = budget_fixture(m, 7200)
    ledger['reservations'][1].update(job_id=g['actual_job_id'], output_dir=g['main_root'])
    mapping['entries'][1]['actual_entry'] = copy.deepcopy(ledger['reservations'][1])
    root = tmp_path / 'native'; root.mkdir()
    canonical = root / 'ledger.json'; old_file = root / 'old.json'; new_file = root / 'new.json'
    old = dict(reservations=[ledger['reservations'][0]], totals={'reserved_gpu_hours': .75}, caps=ledger['caps'])
    for path, value in [(canonical, ledger), (old_file, old), (new_file, ledger)]: t1.save(path, value)
    monkeypatch.setattr(ar, 'CANONICAL_LEDGER', canonical)
    admission = {'id': 'SYNTHETIC-ORIGINAL-ADMISSION', 'purpose': 'fixture only'}
    admission['admission_sha256'] = ar.workload.digest(admission)
    admission_path = root / 'admission'; ar.publish_object(admission_path, admission)
    successors = root / 'successors'; successors.mkdir()
    original = dict(kind='a3_root_ledger_mapping_v1', generation=0, ledger_path=str(canonical),
        ledger_snapshot_path=str(old_file), ledger_sha256=m.sha(old_file), max_age_seconds=900,
        refresh_wait_seconds=0, successor_directory=str(successors), expected_entry_ids=['old'],
        entries=[mapping['entries'][0]], original_admission_paths=[str(admission_path)],
        original_admission_references={str(admission_path): ar.object_reference(admission_path)},
        storage_capacities={'synthetic_fixture': True}, contingency_gpu_hours=0)
    origin = root / 'origin'; ar.publish_object(origin, original)
    current = copy.deepcopy(original)
    current.update(generation=1, predecessor_reference=ar.object_reference(origin),
        ledger_snapshot_path=str(new_file), ledger_sha256=m.sha(new_file),
        expected_entry_ids=['old', 'new'], entries=mapping['entries'])
    successor = successors / 'mapping-000001'; ar.publish_object(successor, current)
    g.update(canonical_ledger=str(canonical), mapping_origin=str(origin), mapping_origin_sha256=m.sha(origin/'COMPLETE.json'))
    monkeypatch.setattr(m, 'native_runtime', lambda g: ar)
    captured, normalized, budget = m.collect_native_closure(g)
    assert budget['exact_requested_GPU_seconds_total'] == '9900'
    assert normalized['expected_identity'] == dict(purpose='A2 original source50e full scoring',
        source_commit=m.SOURCE, groups_sha256=g['groups_file_sha256'], main_root=g['main_root'])
    attestation = m.read(producer.b['cutover_attestation']['path'])
    attestation.update(mapping_origin_sha256=g['mapping_origin_sha256'],
        active_mapping_reference=normalized['active_mapping_reference'],
        mapping_lineage_references=normalized['mapping_lineage_references'], ledger_sha256=m.sha(old_file))
    t1.save(producer.b['cutover_attestation']['path'], attestation)
    producer.b['cutover_attestation']['sha256'] = m.sha(producer.b['cutover_attestation']['path'])
    return normalized


def rebind(m, x, producer, cpu):
    """Bind only temporary synthetic bytes before request and normal COMPLETE."""
    g, c = producer.g, producer.c
    t1.save(x.guard.CONFIG, g)
    producer.b['gpu_config']['sha256'] = m.sha(x.guard.CONFIG)
    os.environ['A2_FULL_SCORE_BOUND_CONFIG']=str(x.guard.CONFIG)
    os.environ['A2_FULL_SCORE_BOUND_CONFIG_SHA256']=m.sha(x.guard.CONFIG)
    w = m.read(x.marker)
    w.update(resources=g['resources'], bound_config_sha256=m.sha(x.guard.CONFIG),
        groups_file_sha256=g['groups_file_sha256'], bank_file_sha256=g['bank_file_sha256'],
        bank_manifest_sha256=g['bank_manifest_sha256'], bank_internal_payload_sha256=g['bank_internal_payload_sha256'],
        launch_packet_manifest_sha256=g['launch_packet_manifest_sha256'])
    t1.save(x.marker, w)
    # Acquire the actual stored marker once, before request hash/signing.
    # Never serialize the earlier insertion-ordered object as its byte copy.
    marker_bytes=x.marker.read_bytes();w=m.decode(marker_bytes)
    c.update(frozen_G3_sha256=g['groups_file_sha256'], bank_file_sha256=g['bank_file_sha256'],
        bank_manifest_sha256=g['bank_manifest_sha256'], GPU_packet_manifest_sha256=g['launch_packet_manifest_sha256'])
    t1.save(producer.b['standing_config']['path'], c)
    producer.b['standing_config']['sha256'] = m.sha(producer.b['standing_config']['path'])
    r = m.construct_request(w,c,g,m.sha(x.guard.CONFIG),str(x.marker),m.sha(x.marker),1005.)
    x.supervisor.validate_request(c,r,w,now=1010.)
    record = m.read(producer.work/'trigger-record.json')
    request_path = Path(record['request']); request_path.write_bytes(m.encoded(r)); rsha=m.sha(request_path)
    child = m.read(cpu/'child-execution.json'); result=m.read(cpu/'guard-result.json')
    child['request_sha256']=rsha
    result.update(request_sha256=rsha, groups_file_sha256=g['groups_file_sha256'])
    # COMPLETE receives bank identity from the actual closed CPU configuration.
    for name,value in [('request.json',r),('guard-result.json',result)]:
        (cpu/name).write_bytes(m.encoded(value))
    assert m.sha_bytes(marker_bytes)==r['GPU_WAITING_marker_sha256']
    (cpu/'WAITING.json').write_bytes(marker_bytes)
    assert (cpu/'WAITING.json').read_bytes()==x.marker.read_bytes()==marker_bytes
    params=m.read(cpu/'parameters.json'); params['phase_request_sha256']=rsha
    (cpu/'parameters.json').write_bytes(m.encoded(params))
    child['guard_result_sha256']=m.sha(cpu/'guard-result.json');t1.save(cpu/'child-execution.json',child)
    q=x.supervisor.validate_child_completion(c,r,child,result,now=1201.)
    q.update(CPU_bound_config_sha256=producer.b['standing_config']['sha256'],
        parameters_sha256=m.sha(cpu/'parameters.json'),child_execution_sha256=m.sha(cpu/'child-execution.json'))
    t1.save(cpu/'COMPLETE.json',q)
    record.update(GPU_config_sha256=m.sha(x.guard.CONFIG),request_sha256=rsha,marker_sha256=m.sha(x.marker))
    t1.save(producer.work/'trigger-record.json',record)
    assert q['complete'] and q['timely_window'] and child['exit_code']==0 and child['term_sent_at'] is None
    return r


def source_join(m,producer,remote,monkeypatch):
    """Use original closed source and namespace, never a new source identity."""
    g=producer.g;g['runtime']=str(SOURCE)
    # Both original namespace and temporary fixture paths live under Alignment.
    # Restore the production mapper's real root, and rebase the fake remote FS.
    temporary_root=m.ROOT
    alignment=Path(META['alignment_root'])
    assert temporary_root.is_relative_to(alignment), 'root runner must keep basetemp under Alignment'
    remote_root=Path(g['physical_Alignment_root'])
    rebased={}
    for name,data in remote.items():
        virtual=temporary_root/Path(name).relative_to(remote_root)
        rebased[str(remote_root/virtual.relative_to(alignment))]=data
    remote.clear();remote.update(rebased)
    monkeypatch.setattr(m,'ROOT',alignment)
    snapshot=json.loads((FROZEN/'native-snapshot.json').read_text())
    t1.save(g['snapshot'],snapshot);g['snapshot_sha256']=m.sha(g['snapshot'])
    m.source_export(g)  # real source511+four literal alias and byte inventory
    for name in snapshot['source_sha256']:
        path=SOURCE/name;remote[m.physical(g,path)]=path.read_bytes()
    original=producer.transport.inspect
    def inspect(paths,waiting,final):
        result=original(paths,waiting,final)
        result['waiting_sha256']=m.sha(m.read(producer.work/'trigger-record.json')['marker'])
        aliases={m.physical(g,SOURCE/name):dict(literal_target=target,
            resolved_target=m.physical(g,Path(target).resolve()),
            target_kind='file' if Path(target).resolve().is_file() else 'directory',
            target_sha256=m.sha(Path(target).resolve()) if Path(target).resolve().is_file() else None)
            for name,target in snapshot['input_links'].items()}
        for name,target in m.read(g['input_manifest'])['aliases'].items():
            aliases[m.physical(g,name)]=dict(literal_target=target,
                resolved_target=m.physical(g,Path(target).resolve()),target_kind='file',target_sha256=m.sha(target))
        result['aliases']={k:v for k,v in aliases.items() if k in paths}
        return result
    monkeypatch.setattr(producer.transport,'inspect',inspect)



def route_main(guard,g,monkeypatch):
    """Route only the test filesystem identity; fixed scientific S stays exact."""
    assert guard.S==str(SOURCE) and guard.SOURCE==META['original_source_commit']
    monkeypatch.setattr(guard,'MAIN',g['main_root'])
    assert guard.MAIN==guard.C['main_root']==g['main_root']
    assert guard.full_score_command(g)[-1]==g['main_root']


def closed_evidence(m,producer,tmp_path,remote):
    """Materialize complete, explicitly SYNTHETIC evidence for actual gates.

    Reuse reviewed source/CPU closure builders and fixture resource tuple; no
    evidence here is operational authority or a real resource/capacity claim.
    """
    g,c,b=producer.g,producer.c,producer.b
    def packet(path,directory):
        files={str(p):m.sha(p) for p in sorted(directory.iterdir()) if p.is_file()}
        t1.save(path,dict(files=files,synthetic_fixture=True))
        return m.sha(path)
    g['packet_manifest_sha256']=packet(Path(g['packet_manifest']),CANDIDATE/'gpu')
    g['launch_packet_manifest_sha256']=g['packet_manifest_sha256']
    c['packet_manifest']['sha256']=packet(Path(c['packet_manifest']['path']),CANDIDATE/'cpu')
    c['packet_manifest_sha256']=c['packet_manifest']['sha256']
    b['helper_manifest']['sha256']=packet(Path(b['helper_manifest']['path']),CANDIDATE/'root')
    # The accepted closure builder supplies exactly 418 ordinary files and 11
    # aliases. Route only its four current catalogues to this temporary fixture.
    closure_root=tmp_path/'input-closure';closure_root.mkdir()
    manifest,current,files=t2.closure.__wrapped__(closure_root)
    ordinary={}
    for name,row in manifest['ordinary_files'].items():
        if name in t2.CATALOGUES:continue
        path=Path(name);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(files[name])
        ordinary[name]=m.sha(path)
    for name in g['minimum_registry_paths']:ordinary[name]=m.sha(name)
    aliases=manifest['namespace_aliases']
    assert len(ordinary)==422 and len(aliases)==11
    roles={name:'synthetic-ordinary' for name in ordinary}
    roles.update({name:'synthetic-alias' for name in aliases})
    t1.save(g['input_manifest'],dict(ordinary_sha256=ordinary,aliases=aliases,
        alias_role_proof=dict(complete=True,expected_aliases=aliases,roles=roles),synthetic_fixture=True))
    g['input_manifest_sha256']=m.sha(g['input_manifest'])
    for name in ordinary:remote[m.physical(g,name)]=Path(name).read_bytes()
    previous_resource=m.read(g['resource_proof'])
    resource=dict(complete=True,independently_accepted=True,proof181_accepted=True,
        resources=copy.deepcopy(g['resources']),synthetic_fixture=True,
        reviewed_components={key:True for key in ('host_memory','gpu_memory','storage','work_ratio','cost')})
    if 'full_domain_reference' in previous_resource:resource['full_domain_reference']=previous_resource['full_domain_reference']
    t1.save(g['resource_proof'],resource);g['resource_proof_sha256']=m.sha(g['resource_proof'])
    capacity=dict(complete=True,independently_accepted=True,resources=copy.deepcopy(g['resources']),
        actual_job_id=g['actual_job_id'],synthetic_fixture=True)
    t1.save(g['capacity_proof'],capacity);g['capacity_proof_sha256']=m.sha(g['capacity_proof'])
    template=json.loads((CANDIDATE/'cpu/config.template.json').read_text());template.update(c)
    template.update(frozen_G3_root=g['main_root'],runtime=str(SOURCE),duration_seconds=3600,CPUs=2,RAM_bytes=8*1024**3,
        resource_review_accepted=True,kill_grace_seconds=5,expected_account='synthetic-cpu',expected_qos='normal',
        python='/u/swong2/.conda/envs/mgnp/bin/python',request_path=str(tmp_path/'request.json'))
    c.clear();c.update(template)
    cpu_resources={key:c[key] for key in ('CPUs','RAM_bytes','duration_seconds','child_cap_seconds',
        'CPU_finish_margin_seconds','publication_margin_seconds','kill_grace_seconds')}
    t1.save(c['resource_proof']['path'],dict(complete=True,independent_review_accepted=True,phase='full_score',
        resources=cpu_resources,synthetic_fixture=True))
    c['resource_proof']['sha256']=m.sha(c['resource_proof']['path'])
    c['GPU_packet_manifest_sha256']=g['packet_manifest_sha256']
    # Bind all admission hash dependencies only after the underlying temporary
    # resource/capacity/input/packet evidence is final.
    seal_admission(m,g)
    bindings=json.loads((CANDIDATE/'root/bindings.template.json').read_text());bindings.update(b)
    bindings.update(phase='full_score',usage_pause_percent=80,session='exact',
        remote_model_cache_reference=dict(path=str(tmp_path/'tiny-cache/reference.json'),
            sha256=m.sha(tmp_path/'tiny-cache/reference.json')))
    b.clear();b.update(bindings)
    assert set(c)==set(json.loads((CANDIDATE/'cpu/config.template.json').read_text()))
    assert all(value is not None for value in c.values())
    assert set(b)==set(json.loads((CANDIDATE/'root/bindings.template.json').read_text()))
    assert g['main_root']==c['frozen_G3_root']


def seal_admission(m,g,overrides=None):
    admission=dict(kind='synthetic_a2_full_score_fixture',accepted=True,complete=True,phase='full_score',
        source_commit=META['original_source_commit'],actual_job_id=g['actual_job_id'],reservation_id=g['reservation_id'],
        main_root=g['main_root'],resources=copy.deepcopy(g['resources']),reader_safe_cutover_complete=True,
        native_successor_complete=True,synthetic_fixture=True)
    for key in ('packet_manifest_sha256','groups_file_sha256','bank_file_sha256','bank_manifest_sha256',
        'input_manifest_sha256','model_cache_proof_sha256','resource_proof_sha256','capacity_proof_sha256'):
        admission[key]=g[key]
    if overrides:admission.update(overrides)
    t1.save(g['operational_admission'],admission);g['operational_admission_sha256']=m.sha(g['operational_admission'])


def restore_root_gates(m,producer,events,real_verify,monkeypatch):
    """Spies delegate to original functions, including every freshly loaded GPU."""
    real_load=m.load_module
    def load_module(path,name):
        loaded=real_load(path,name)
        if Path(path).name=='common.py':
            # verify_runtime_pins binds C to g immediately after this load.
            route_main(loaded,producer.g,monkeypatch)
            original=loaded.reviewed_admission
            def reviewed_admission():
                events.append('root-reviewed-admission')
                return original()
            monkeypatch.setattr(loaded,'reviewed_admission',reviewed_admission)
        return loaded
    monkeypatch.setattr(m,'load_module',load_module)
    def verify_runtime_pins(b,g,c):
        events.append('root-verify-runtime-pins')
        result=real_verify(b,g,c)
        assert result[0].MAIN==g['main_root']==c['frozen_G3_root']
        assert result[0].S==str(SOURCE)
        return result
    monkeypatch.setattr(m,'verify_runtime_pins',verify_runtime_pins)

def joined(chain,tmp_path,monkeypatch,full=False):
    m=module();real_verify_runtime_pins=m.verify_runtime_pins
    p,ar=native_modules(monkeypatch)
    producer,events,cpu,remote,_=publish_fixture(m,chain,tmp_path,monkeypatch)
    source_join(m,producer,remote,monkeypatch)
    # Keep the unchanged protection validator: missing explicit closure flags
    # must not be hidden by the root fixture's independently reviewed proof.
    proof=m.read(producer.g['protection_proof']);proof['nonempty_heldout']=False
    t1.save(producer.g['protection_proof'],proof);producer.g['protection_proof_sha256']=m.sha(producer.g['protection_proof'])
    scored=None
    if full:
        scored=full_native_score(m,p,producer.g,tmp_path,monkeypatch)
        for key in ('bank_file','bank_manifest','groups'):remote[m.physical(producer.g,producer.g[key])]=Path(producer.g[key]).read_bytes()
    # Accepted cache algorithm on tiny files, never actual full weight reads.
    cache_root=tmp_path/'tiny-cache';cache_root.mkdir()
    ref,proof,hub,snapshot,weight,pins=cache_fixture(m.cache_gate,cache_root)
    monkeypatch.setattr(m.cache_gate,'REFERENCE_SHA',pins['reference_sha256'])
    monkeypatch.setattr(m.cache_gate,'FULL_PROOF_SHA',pins['full_proof_sha256'])
    original_cache=producer.transport.cache_check
    def cache_check():
        prior=original_cache()
        if prior['revision']!=m.cache_gate.REVISION:(snapshot/'tokenizer.json').write_text('[]')
        return m.cache_gate.check_cache(ref,proof,hub,**pins)
    monkeypatch.setattr(producer.transport,'cache_check',cache_check)
    producer.g['model_cache_proof']=str(proof);producer.g['model_cache_proof_sha256']=m.sha(proof)
    monkeypatch.setattr(usage_fixtures,'NOW',1202)
    monkeypatch.setattr(usage_fixtures,'RESET',87602)
    usage_payload,usage_status=usage_fixtures.fixture(live=47,cached=46,since=100)
    usage_observation=dict(payload=usage_payload,status=usage_status)
    def ordinary_usage(b,work,label):
        events.append('usage:'+label)
        return m.validate_usage(usage_observation['payload'],usage_observation['status'],'exact')
    monkeypatch.setattr(m,'usage',ordinary_usage)
    normalized=native_lineage(m,producer,tmp_path,monkeypatch,ar)
    closed_evidence(m,producer,tmp_path,remote)
    rebind(m,chain,producer,cpu)
    restore_root_gates(m,producer,events,real_verify_runtime_pins,monkeypatch)
    m.verify_runtime_pins(producer.b,producer.g,producer.c)
    return SimpleNamespace(m=m,p=p,ar=ar,producer=producer,events=events,cpu=cpu,remote=remote,
        normalized=normalized,scored=scored,x=chain,usage=usage_observation)


def full_native_score(m,p,g,tmp_path,monkeypatch):
    """Full native keys/support/control/manifest, synthetic numerical values only."""
    owning=json.loads((CANDIDATE/'gpu/config.template.json').read_text())
    receipt=p.a1.read_artifact(owning['groups'])
    # Authentic groups are copied byte for byte. No original MAIN write occurs.
    shutil.copyfile(owning['groups'],g['groups'])
    g['groups_file_sha256']=m.sha(g['groups']);g['groups_receipt_sha256']=receipt['receipt_sha256']
    args=p.parser().parse_args([
        '--stage','score','--design',g['a1_design'],'--selected',g['a1_selected'],
        '--work-dir',g['main_root'],'--commit',m.SOURCE,'--batch-size','8','--registry',g['registry']])
    prepared,_,_=p._load_context(args);p._validate_live(args,receipt,prepared)
    banks=p.a1.read_artifact(owning['bank_file'])
    banks=copy.deepcopy(banks);banks['synthetic_fixture']=True
    banks['execution_provenance']['synthetic_fixture']=True
    numeric=p.numeric_environment();g['bank_numeric_environment']=numeric
    for value in banks['banks'].values():value['contract']['numeric_environment']=numeric
    p.validate_banks(receipt,prepared,banks)
    Path(g['bank_file']).unlink()  # only the temporary tiny fixture, never the authentic bank
    p.a1.write_artifact(Path(g['bank_file']),banks)
    bank_args=copy.copy(args);bank_args.stage='bank'
    t1.save(g['bank_manifest'],p._manifest(bank_args,receipt,banks))
    g.update(bank_file_sha256=m.sha(g['bank_file']),bank_manifest_sha256=m.sha(g['bank_manifest']),
        bank_internal_payload_sha256=p.hash_content(banks))
    boundary=t2.module('validate-phase')
    mask,controls=boundary.reconstruct_domain(p,prepared,receipt)
    keys=p.expected_keys(receipt,0);assert len(keys)==len(mask)==59652 and len(controls)==3396
    bank_references={task:p.bank_reference(banks,Path(g['bank_file']),task) for task in p.TASKS}
    rows=[]
    for key in keys:
        row=dict(zip(('task','instance_id','condition','stream','group','operation','donor_seed'),key))
        group=receipt['groups'][row['group']];supported,reason=mask[tuple(key)]
        row.update(group_members=group['members'],group_source=p.GROUP_SOURCE,
            a2_group_sha256=group['membership_sha256'],a2_receipt_sha256=receipt['receipt_sha256'],
            supported=supported,unsupported_reason=reason,synthetic_fixture=True)
        if row['operation']=='h_mean' and supported:
            row['mean_bank_provenance']=bank_references[group['task']]
        rows.append(row)
    positive=[dict(zip(('mechanism_task','task','instance_id','condition','stream'),key),valid=True,synthetic_fixture=True)
              for key in p.a1.positive_keys(p._prepared_domain(receipt),0)]
    p.validate_a2_scope(receipt,rows,limit=0,banks=banks,bank_path=Path(g['bank_file']))
    p.a1.validate_positive_controls(positive,p._prepared_domain(receipt),0)
    domain=dict(complete=True,source_commit=m.SOURCE,groups_file_sha256=g['groups_file_sha256'],
        rows=[dict(key=list(key),supported=mask[tuple(key)][0],unsupported_reason=mask[tuple(key)][1]) for key in keys],
        positive_control_keys=[list(k) for k in p.a1.positive_keys(p._prepared_domain(receipt),0)],synthetic_fixture=True)
    reference=tmp_path/'SYNTHETIC-full-domain.json';t1.save(reference,domain)
    resource=m.read(g['resource_proof']);resource['full_domain_reference']=dict(path=str(reference),sha256=m.sha(reference))
    t1.save(g['resource_proof'],resource);g['resource_proof_sha256']=m.sha(g['resource_proof'])
    execution=dict(gpu_name=t1.NAME,dtype=g['dtype'],device='cuda:0',slurm_job_id=g['actual_job_id'],synthetic_fixture=True)
    return dict(kind='a2_scored',limit=0,pilot=False,injected=False,synthetic_fixture=True,
        expected=[list(k) for k in keys],bank_artifact_sha256=p.hash_content(banks),rows=rows,
        positive_controls=positive,counts=dict(rows=59652,expected=59652,positive_controls=3396),execution_provenance=execution)


def consumer(j,monkeypatch,child_fault=None,entry_fault=None):
    g=j.producer.g;m=j.m
    controller=t1.require_module('controller',monkeypatch,g);guard=controller.common
    route_main(guard,g,monkeypatch)
    assert controller.entry_release is guard.entry_release
    # New module, no patched Task1 marker-construction guard survives this load.
    monkeypatch.setattr(guard,'imports',lambda:(j.p,j.ar))
    real_reviewed_admission=guard.reviewed_admission
    def reviewed_admission():
        j.events.append('consumer-reviewed-admission')
        return real_reviewed_admission()
    monkeypatch.setattr(guard,'reviewed_admission',reviewed_admission)
    monkeypatch.setattr(guard,'cache',j.producer.transport.cache_check)
    monkeypatch.setattr(guard,'allocation',lambda **kw:dict(facts={'EndTime':'1970-01-01T02:30:00'}))
    def probe(config,name,script,env,deadline):
        j.events.append('postactivation:'+name)
        if entry_fault=='postactivation':raise ValueError('synthetic postactivation failure')
        return dict(gpu_name=t1.NAME,device='cuda:0',dtype=g['dtype'],numeric_environment=g['bank_numeric_environment'],
            gpu_uuid='GPU-SYNTHETIC-NEW',total_memory_bytes=90000000000,free_memory_bytes=85000000000)
    monkeypatch.setattr(controller,'_probe',probe)
    calls=[]
    def popen(argv,**kwargs):
        calls.append((argv,kwargs));j.events.append('original-score-CLI')
        assert (Path(g['evidence_root'])/'CONSUMED-full_score.json').is_file()
        assert argv==guard.full_score_command(g) and argv[:2]==['bash',str(SOURCE/'scripts/jobs/specificity_a2.sh')]
        assert '--limit' not in argv and argv[argv.index('--stage')+1]=='score' and kwargs['cwd']==str(SOURCE)
        assert argv[argv.index('--batch-size')+1]=='8' and argv[argv.index('--work-dir')+1]==g['main_root']
        class Child:
            pid=289;returncode=None
            def poll(self):return self.returncode
            def wait(self,timeout=None):
                assert timeout>0
                if child_fault=='partial':
                    scratch=Path(g['main_root'])/'.score-SYNTHETIC-partial';scratch.mkdir();(scratch/'partial.json').write_text('{}')
                    self.returncode=7;return 7
                payload=j.scored
                assert payload is not None
                if child_fault=='unsupported':payload['rows'][0]['unsupported_reason']='drift'
                args=j.p.parser().parse_args(argv[2:])
                j.p._publish_stage(Path(g['main_root'])/'score','score.json',payload,j.p._manifest(args,j.p.a1.read_artifact(g['groups']),payload))
                self.returncode=0;return 0
        return Child()
    monkeypatch.setattr(controller.subprocess,'Popen',popen)
    final=j.producer.waiting_paths()[1]
    r=m.read(final);r.update(_release_path=final,_release_sha256=m.sha(final))
    guard.validate_release(r);guard._lease(r)
    if entry_fault=='catalogue':Path(r['catalogues'][0]['virtual_path']).write_text('{}')
    if entry_fault=='bank':Path(g['bank_file']).write_text('{}')
    if entry_fault=='release':Path(final).write_text('{}')
    if entry_fault=='existing-score':(Path(g['main_root'])/'score').mkdir()
    if entry_fault=='null-resource':g['resources']['CPUs']=None
    if entry_fault=='config':guard.CONFIG.write_bytes(guard.CONFIG.read_bytes()+b' ')
    if entry_fault=='WAITING':Path(r['_waiting_path']).write_text('{}')
    if entry_fault=='expired':monkeypatch.setattr(guard.time,'time',lambda:1602.)
    if entry_fault=='old-authority':r['phase']='prefix4'
    if entry_fault=='short-allocation':monkeypatch.setattr(guard,'allocation',lambda **kw:dict(facts={'EndTime':'1970-01-01T00:21:40'}))
    return controller,guard,r,calls


def test_whole_chain_normal_native_full_publication(chain,tmp_path,monkeypatch):
    j=joined(chain,tmp_path,monkeypatch,full=True)
    before=(j.cpu/'COMPLETE.json').read_bytes()
    assert j.producer.publish()['published']
    controller,guard,r,calls=consumer(j,monkeypatch)
    result=controller.run_full_score(j.producer.g,r)
    assert len(calls)==1 and result['complete'] and result['assessment_effects_inspected'] is False
    assert not j.p._TASK4_MODEL_CALLS
    assert result['audit']['counts']==dict(rows=59652,expected=59652,positive_controls=3396)
    assert result['audit']['support_mask_audit']['reasons_preserved']
    assert j.events.count('root-verify-runtime-pins')>=3
    assert j.events.count('root-reviewed-admission')>=3 and j.events.count('consumer-reviewed-admission')==1
    assert (j.cpu/'COMPLETE.json').read_bytes()==before
    assert j.events.count('publish')==1 and j.events.index('publish')<j.events.index('postactivation:imports-before-full-score')<j.events.index('original-score-CLI')
    manifest=j.m.read(Path(j.producer.g['main_root'])/'score/run_manifest.json')
    assert manifest['kind']=='a2_score' and manifest['execution_commit']==j.m.SOURCE and manifest['execution']['synthetic_fixture']
    assert manifest['counts']==dict(rows=59652,expected=59652,positive_controls=3396)
    with pytest.raises((ValueError,FileExistsError)):controller.run_full_score(j.producer.g,r)
    with pytest.raises(FileExistsError):j.producer.publish()
    assert len(calls)==1 and j.events.count('publish')==1
    # A native, hash-consistent artifact still cannot change the support mask
    # or control domain after the full CLI boundary. No new CLI is permitted.
    score=Path(j.producer.g['main_root'])/'score'
    payload=copy.deepcopy(j.scored)
    unsupported=next((row for row in payload['rows'] if row['supported'] is False),payload['rows'][0])
    unsupported.update(supported=False,unsupported_reason='SYNTHETIC-DIAGNOSTIC-DRIFT')
    args=j.p.parser().parse_args(guard.full_score_command(j.producer.g)[2:])
    receipt=j.p.a1.read_artifact(j.producer.g['groups'])
    def replace_fixture_score(value):
        (score/'score.json').unlink();j.p.a1.write_artifact(score/'score.json',value)
        t1.save(score/'run_manifest.json',j.p._manifest(args,receipt,value))
    replace_fixture_score(payload)
    with pytest.raises(ValueError,match='support mask'):controller.audit_score_result(j.producer.g)
    del payload;gc.collect()
    payload=copy.deepcopy(j.scored);payload['positive_controls'][0]['instance_id']='SYNTHETIC-CONTROL-DRIFT'
    replace_fixture_score(payload)
    with pytest.raises(ValueError,match='positive controls'):controller.audit_score_result(j.producer.g)
    del payload;gc.collect()
    replace_fixture_score(j.scored)
    manifest_path=score/'run_manifest.json';manifest_before=manifest_path.read_bytes();manifest_path.write_text('{}')
    with pytest.raises(ValueError,match='completion manifest'):controller.audit_score_result(j.producer.g)
    manifest_path.write_bytes(manifest_before);gc.collect()
    assert len(calls)==1


@pytest.mark.parametrize('fault',['catalogue','CPU','SIF','ledger','WAITING','cache'])
def test_transfer_failure_cannot_cross_score_boundary(chain,tmp_path,monkeypatch,fault):
    j=joined(chain,tmp_path,monkeypatch);j.producer.transport.attack=fault
    calls=[]
    monkeypatch.setattr(j.m.subprocess,'Popen',lambda *a,**kw:calls.append(a))
    with pytest.raises((ValueError,AssertionError,KeyError)):j.producer.publish()
    assert 'stage' in j.events  # intended mutation boundary must actually run
    assert not calls and not j.p._TASK4_MODEL_CALLS and 'publish' not in j.events
    with pytest.raises(FileExistsError):j.producer.publish()


@pytest.mark.parametrize('fault',['postactivation','catalogue','bank','release','existing-score','null-resource','config','WAITING','expired','old-authority','short-allocation'])
def test_entry_failure_has_zero_score_calls(chain,tmp_path,monkeypatch,fault):
    j=joined(chain,tmp_path,monkeypatch);assert j.producer.publish()['published']
    controller,guard,r,calls=consumer(j,monkeypatch,entry_fault=fault)
    with pytest.raises((ValueError,AssertionError,KeyError)):controller.run_full_score(j.producer.g,r)
    assert not calls and not j.p._TASK4_MODEL_CALLS and not (Path(j.producer.g['evidence_root'])/'COMPLETE.json').exists()


def test_consumed_partial_is_preserved_and_never_retried(chain,tmp_path,monkeypatch):
    j=joined(chain,tmp_path,monkeypatch);j.producer.publish()
    controller,guard,r,calls=consumer(j,monkeypatch,child_fault='partial')
    with pytest.raises(ValueError):controller.run_full_score(j.producer.g,r)
    evidence=Path(j.producer.g['evidence_root']);scratch=Path(j.producer.g['main_root'])/'.score-SYNTHETIC-partial/partial.json'
    assert len(calls)==1 and scratch.is_file() and (evidence/'CONSUMED-full_score.json').is_file()
    assert not (evidence/'COMPLETE.json').exists()
    prior=scratch.read_bytes()
    with pytest.raises((ValueError,FileExistsError)):controller.run_full_score(j.producer.g,r)
    assert len(calls)==1 and not j.p._TASK4_MODEL_CALLS and scratch.read_bytes()==prior


def test_native_sibling_publication_and_mount_policy(chain,tmp_path,monkeypatch):
    # Reuse the accepted mount policy assertions, then join real native stage
    # writer+manifest+read_stage; no Apptainer or model process is started.
    t1.test_atomic_score_mount_policy(chain.g,monkeypatch,tmp_path)
    p,_=native_modules(monkeypatch)
    owning=json.loads((CANDIDATE/'gpu/config.template.json').read_text())
    receipt=p.a1.read_artifact(owning['groups'])
    args=p.parser().parse_args(['--stage','score','--design',chain.g['a1_design'],'--selected',chain.g['a1_selected'],
        '--work-dir',chain.g['main_root'],'--commit',t1.COMMIT,'--batch-size','8','--registry',chain.g['registry']])
    target=tmp_path/'publication-parent/score';target.parent.mkdir()
    payload=dict(kind='SYNTHETIC-publication-only',synthetic_fixture=True,counts={'rows':0})
    manifest=p._manifest(args,receipt,payload)
    p._publish_stage(target,'score.json',payload,manifest)
    assert p.read_stage(target,'score.json','score',args,receipt)==payload
    before={str(f):f.read_bytes() for f in target.iterdir()}
    with pytest.raises(ValueError):p._publish_stage(target,'score.json',payload,manifest)
    assert all(Path(f).read_bytes()==raw for f,raw in before.items())
    assert not list(target.parent.glob('.score-*'))


@pytest.mark.parametrize('fault',['ordinary-cap','freeze','checkpoint','old-charge','missing-successor'])
def test_current_authority_failure_stops_before_remote_publication(chain,tmp_path,monkeypatch,fault):
    j=joined(chain,tmp_path,monkeypatch)
    if fault=='ordinary-cap':j.usage['payload']['weekly']['used_percent']=80
    elif fault=='freeze':j.usage['status']=j.usage['status'].replace('freeze: none;','freeze: crossed;')
    elif fault=='checkpoint':j.usage['payload']['weekly']['used_percent']=66
    elif fault=='old-charge':
        ledger=j.m.read(j.producer.g['canonical_ledger']);ledger['reservations'][0]['reserved_gpu_hours']=0
        t1.save(j.producer.g['canonical_ledger'],ledger)
    elif fault=='missing-successor':
        path=Path(j.normalized['active_mapping_reference']['path'])
        (path/'COMPLETE.json').unlink()
    calls=[];monkeypatch.setattr(j.m.subprocess,'Popen',lambda *a,**kw:calls.append(a))
    with pytest.raises((ValueError,AssertionError,KeyError,FileNotFoundError)):j.producer.publish()
    assert not calls and not j.p._TASK4_MODEL_CALLS and 'publish' not in j.events


@pytest.mark.parametrize('fault,reason',[
    ('resource-review','genuine independently reviewed resource'),
    ('capacity-job','actual reviewed placement/capacity'),
    ('admission-scope','new root operational admission'),
    ('reader-cutover','completed reader-safe native mapping transition'),
    ('CPU-resource','fresh accepted owning CPU resource decision'),
    ('root-scope','closed full-only ordinary80 bindings')])
def test_actual_root_pin_and_admission_gates_reject_synthetic_semantic_damage(chain,tmp_path,monkeypatch,fault,reason):
    j=joined(chain,tmp_path,monkeypatch);m=j.m;g=j.producer.g;c=j.producer.c
    baseline_root=j.events.count('root-verify-runtime-pins')
    baseline_admission=j.events.count('root-reviewed-admission')
    overrides={}
    if fault=='resource-review':
        value=m.read(g['resource_proof']);value['independently_accepted']=False
        t1.save(g['resource_proof'],value);g['resource_proof_sha256']=m.sha(g['resource_proof'])
    elif fault=='capacity-job':
        value=m.read(g['capacity_proof']);value['actual_job_id']='SYNTHETIC-WRONG-JOB'
        t1.save(g['capacity_proof'],value);g['capacity_proof_sha256']=m.sha(g['capacity_proof'])
    elif fault=='admission-scope':overrides['phase']='prefix4'
    elif fault=='reader-cutover':overrides['native_successor_complete']=False
    elif fault=='CPU-resource':
        value=m.read(c['resource_proof']['path']);value['independent_review_accepted']=False
        t1.save(c['resource_proof']['path'],value);c['resource_proof']['sha256']=m.sha(c['resource_proof']['path'])
    elif fault=='root-scope':j.producer.b['usage_pause_percent']=81
    seal_admission(m,g,overrides)
    rebind(m,j.x,j.producer,j.cpu)
    calls=[];monkeypatch.setattr(m.subprocess,'Popen',lambda *a,**kw:calls.append(a))
    with pytest.raises(ValueError,match=reason):j.producer.publish()
    assert j.events.count('root-verify-runtime-pins')==baseline_root+1
    if fault not in ('CPU-resource',):assert j.events.count('root-reviewed-admission')==baseline_admission+1
    assert not calls and not j.p._TASK4_MODEL_CALLS and 'publish' not in j.events


def test_actual_consumer_rejects_wrong_temporary_MAIN_before_CLI(chain,tmp_path,monkeypatch):
    j=joined(chain,tmp_path,monkeypatch);j.producer.publish()
    controller,guard,r,calls=consumer(j,monkeypatch)
    assert guard.MAIN==guard.C['main_root']==j.producer.g['main_root']
    r['main_root']=str(tmp_path/'SYNTHETIC-wrong-MAIN')
    with pytest.raises(ValueError,match='release actual binding'):
        controller.run_full_score(j.producer.g,r)
    assert not calls and not j.p._TASK4_MODEL_CALLS



def test_original_capture_requires_exact_authenticated_WAITING_bytes(chain,tmp_path,monkeypatch):
    j=joined(chain,tmp_path,monkeypatch);m=j.m
    assert Path.cwd().resolve()==SOURCE.resolve()
    record=m.read(j.producer.work/'trigger-record.json')
    request_path=Path(record['request']);request_bytes=request_path.read_bytes();request=m.decode(request_bytes)
    marker=Path(request['GPU_WAITING_marker_path']);marker_bytes=marker.read_bytes()
    copy_path=j.cpu/'WAITING.json';complete_bytes=(j.cpu/'COMPLETE.json').read_bytes()
    assert copy_path.read_bytes()==marker_bytes
    assert m.sha_bytes(marker_bytes)==request['GPU_WAITING_marker_sha256']==record['marker_sha256']
    calls=[];monkeypatch.setattr(m.subprocess,'Popen',lambda *a,**kw:calls.append(a))
    proof,captured=m.capture_cpu(j.producer.c,request,j.producer.g,j.producer.b['gpu_config']['sha256'],record['request_sha256'],now=1202.)
    assert captured[str(copy_path)]==marker_bytes and proof['complete'] is True
    # Retain the original raw hash. Even semantically identical JSON cannot
    # replace an authenticated byte copy; no resealing or renewal is performed.
    copy_path.write_bytes(marker_bytes+b' ')
    assert m.read(copy_path)==m.decode(marker_bytes)
    with pytest.raises(ValueError,match='CPU immutable WAITING copy'):
        m.capture_cpu(j.producer.c,request,j.producer.g,j.producer.b['gpu_config']['sha256'],record['request_sha256'],now=1202.)
    assert marker.read_bytes()==marker_bytes and request_path.read_bytes()==request_bytes
    assert (j.cpu/'COMPLETE.json').read_bytes()==complete_bytes
    assert not calls and not j.p._TASK4_MODEL_CALLS and 'publish' not in j.events
