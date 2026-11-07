#!/usr/bin/env python3
"""Root full_score trigger and once-only composite producer; stdlib only.

No reservation/mapping creation, scheduler mutation, private RS writes, model,
scientific score, retry or renewal. Root supplies completed native cutover.
"""
import argparse
import copy
import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
import cache_gate

SOURCE='50e947bb852613e3a270082651f2bd1b7bb0c525'
ROOT=Path('/projects/beto/swong2/Alignment')
IMMUTABLE_FIELDS=('id','job_id','cluster','account','partition','gpus','requested_minutes',
                  'reserved_gpu_hours','source_commit','output_dir','manifest_hash')
PROJECTS=('component_analysis','models','dataset','evaluation','scripts','config')
class Rejected(ValueError):pass

def need(ok,msg):
    if not ok:raise Rejected(msg)

def pairs(items):
    out={}
    for k,v in items:
        need(k not in out,'duplicate JSON key');out[k]=v
    return out

def decode(raw):
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(Rejected('nonfinite JSON')))
def encoded(value):return (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
    return h.hexdigest()
def read(path):return decode(Path(path).read_bytes())
def exclusive(path,raw):
    with Path(path).open('xb') as stream:stream.write(raw)
def atomic_new(path,raw):
    path=Path(path);pending=path.with_name(path.name+'.pending');exclusive(pending,raw)
    try:os.link(str(pending),str(path))
    finally:pending.unlink()
def decimal(value):
    need(type(value) in (int,float,str),'invalid numeric type')
    try:result=Decimal(str(value))
    except InvalidOperation:raise Rejected('invalid decimal')
    need(result.is_finite() and result>=0,'finite nonnegative number required');return result

def ordinary(path):
    path=Path(path);need(path.is_absolute() and '..' not in path.parts and not path.is_symlink() and path.is_file(),'ordinary absolute file required: '+str(path))
    return path

def bound(ref):
    need(type(ref) is dict and set(ref)=={'path','sha256'},'closed pinned reference')
    path=ordinary(ref['path']);raw=path.read_bytes()
    need(sha_bytes(raw)==ref['sha256'] and sha(path)==ref['sha256'],'bound reference changed: '+str(path))
    return decode(raw)

def construct_request(w,c,g,gsha,marker,msha,now):
    need(w['phase']==c['phase']==g['phase']=='full_score','full_score only')
    need(g['commit']==c['source_commit']==w['source_commit']==SOURCE,'accepted source identity')
    need(w['job_id']==g['actual_job_id'] and w['bound_config_sha256']==gsha,'WAITING actual job/config')
    for key in ('groups_file_sha256','bank_file_sha256','bank_manifest_sha256','bank_internal_payload_sha256','launch_packet_manifest_sha256','resources'):
        need(w[key]==g[key],'WAITING actual binding: '+key)
    for ck,gk in (('frozen_G3_sha256','groups_file_sha256'),('bank_file_sha256','bank_file_sha256'),
                  ('bank_manifest_sha256','bank_manifest_sha256'),('GPU_packet_manifest_sha256','launch_packet_manifest_sha256')):
        need(c[ck]==g[gk],'standing/GPU binding: '+ck)
    need(re.fullmatch('[0-9]+',g['actual_job_id']) and re.fullmatch('[0-9]+',c['standing_CPU_job_id']),'actual numeric jobs')
    requested=decimal(w['requested_at']);end=decimal(w['publication_deadline']);clock=decimal(now)
    need(requested<=clock<end and 0<end-requested<=300,'finite WAITING publication window')
    need(sha(marker)==msha and read(marker)==w,'actual immutable WAITING bytes')
    return dict(phase='full_score',standing_CPU_job_id=c['standing_CPU_job_id'],
        standing_packet_manifest_sha256=c['packet_manifest_sha256'],accepted_source_commit=SOURCE,
        frozen_G3_sha256=g['groups_file_sha256'],bank_file_sha256=g['bank_file_sha256'],
        bank_manifest_sha256=g['bank_manifest_sha256'],GPU_packet_manifest_sha256=g['launch_packet_manifest_sha256'],
        actual_future_GPU_job_id=g['actual_job_id'],final_GPU_bound_config_sha256=gsha,
        root_trigger_issued_at=now,GPU_WAITING_requested_at=w['requested_at'],
        GPU_WAITING_marker_path=str(marker),GPU_WAITING_marker_sha256=msha)

def check_request_fresh(r,now):
    need(r['phase']=='full_score' and 0<=decimal(now)-decimal(r['root_trigger_issued_at'])<=15
         and decimal(r['GPU_WAITING_requested_at'])<=decimal(r['root_trigger_issued_at']),'request stale/future')

def validate_complete(q,r,rsha,g,gsha,now):
    for key in ('complete','timely_window','actual_Delta_owning_guards_passed','stable_Delta_catalogues_before_after','full_domain_support_audit_complete'):
        need(q.get(key) is True,'CPU did not complete '+key)
    need(q['kind']=='Delta_actual_full_score_preflight' and q['phase']==r['phase']=='full_score' and q['status']=='PASS','new full-score CPU proof required')
    need(q['source_commit']==SOURCE and q['groups_file_sha256']==g['groups_file_sha256'],'CPU source/G3')
    for qk,rk in (('actual_CPU_job_id','standing_CPU_job_id'),('actual_future_GPU_job_id','actual_future_GPU_job_id'),
        ('standing_packet_manifest_sha256','standing_packet_manifest_sha256'),('GPU_packet_manifest_sha256','GPU_packet_manifest_sha256')):
        need(q[qk]==r[rk],'CPU immutable binding: '+qk)
    need(q['actual_future_GPU_job_id']==g['actual_job_id'] and q['request_sha256']==rsha
        and q['final_GPU_bound_config_sha256']==q['bound_gpu_config_sha256']==gsha,'CPU request/config/jobs')
    for key in ('bank_file_sha256','bank_manifest_sha256','launch_packet_manifest_sha256'):
        need(q[key]==g[key],'CPU actual bank/packet: '+key)
    need(q['waiting_sha256']==r['GPU_WAITING_marker_sha256'],'CPU immutable WAITING')
    need(q['full_rows']==59652 and q['full_controls']==3396 and re.fullmatch('[0-9a-f]{64}',q['support_reason_mask_sha256']),'CPU full domain/support')
    for key in ('model_loaded','GPU_admitted','freeze_executed','automatic_retry'):
        need(q.get(key) is False,'unexpected CPU work/authority/retry')
    marker=ordinary(r['GPU_WAITING_marker_path']);need(sha(marker)==r['GPU_WAITING_marker_sha256'],'WAITING changed')
    waiting=read(marker)
    need(decimal(q['supervisor_finished_unix'])<decimal(q['deadline_unix']) and decimal(q['supervisor_finished_unix'])<=decimal(now)
        and decimal(now)<decimal(waiting['publication_deadline']),'CPU completion/publication deadline')

def validate_cutover(value,now=None):
    now=time.time() if now is None else now
    need(type(value) is dict and 0<=decimal(now)-decimal(value['observed_unix'])<=15,'fresh root cutover attestation required')
    need(value.get('active_readers')==[] and value.get('quiescent') is True,'active reader; defer without changing reader')
    for key in ('root_cutover_attested','originals_preserved','new_reservation_complete','native_successor_complete','native_normalization_complete'):
        need(value.get(key) is True,'incomplete reader-safe native pair: '+key)
    need(value.get('readers_released') is False,'readers released before completed native validation')
    return copy.deepcopy(value)

def authenticate_cutover(b,g,normalized=None):
    value=bound(b['cutover_attestation'])
    # Freshness belongs to finalization of the no-reader transition. Reusing a
    # sealed historical proof later cannot authorize a new reservation/lineage.
    finalized=decimal(value['finalized_unix'])
    need(finalized<=decimal(time.time()),'future cutover finalization')
    validate_cutover(value,now=value['finalized_unix'])
    need(value['actual_job_id']==g['actual_job_id'] and value['reservation_id']==g['reservation_id']
        and value['mapping_origin_sha256']==g['mapping_origin_sha256'],'cutover actual transition identity')
    if normalized is not None:
        need(value['active_mapping_reference']==normalized['active_mapping_reference']
            and value['mapping_lineage_references']==normalized['mapping_lineage_references']
            and value['ledger_sha256']==sha(normalized['original_snapshot_path']),
            'unauthorized new transition or changed preserved native lineage')
    return value

def validate_heldout(value,proof=None):
    need(type(value) is dict and type(value.get('sets')) is list,'unknown protection catalogue')
    if value['sets']:
        need(type(proof) is dict and proof.get('complete') is True and proof.get('independently_accepted') is True
            and proof.get('nonempty_heldout_closure_reviewed') is True,'nonempty protected closure needs owning independent review')

def validate_usage(u,status,session):
    need(type(u) is dict and u.get('status')=='ok' and u.get('should_pause') is False,'usage unavailable/pause')
    first=status.splitlines()[0] if status.splitlines() else ''
    need((first=='session '+session or first.startswith('session '+session+' ')) and re.search(r'^freeze: none;',status,re.M),'session mismatch/frozen')
    match=re.search(r'seven-day ([0-9.]+)%',status);need(match,'cached session percentage unknown')
    weekly=u.get('weekly');need(type(weekly) is dict and type(weekly.get('used_percent')) in (int,float),'invalid live percentage')
    cached=decimal(match.group(1));live=decimal(weekly['used_percent'])
    need(cached<=100 and live>=cached and live<80,'ordinary80 cap or meter rollback')
    counters=re.search(r'session points ([0-9.]+) \(([0-9.]+) since register\); cadence ([0-9.]+); next checkpoint ([0-9]+) at \+([0-9.]+)',status)
    need(counters,'unknown targeted checkpoint counters')
    points,since,cadence,index,next_at=map(decimal,counters.groups())
    need(points>=since and cadence>0 and index>=1 and next_at==cadence*index and since<next_at,'inconsistent native checkpoint counters')
    need(since+(live-cached)<next_at,'live usage reaches native checkpoint')
    reset=re.search(r'^weekly cap exception: ([a-z_-]+) \(last observed\); captured reset ([0-9]+)$',status,re.M)
    need(reset and reset.group(1) in ('active','expired'),'unknown reset status')
    captured=int(reset.group(2));actual=weekly.get('resets_at')
    need(type(actual) is int and captured>0 and actual>time.time(),'reset unknown/expired')
    telemetry=re.search(r'last reading:[^\n]* at (\S+) \(([^)]*)\)',status)
    def timestamp(value):
        try:
            parsed=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
            need(parsed.utcoffset() is not None,'timezone-aware usage timestamp required')
            result=parsed.timestamp();need(math.isfinite(result),'finite usage timestamp');return result
        except (AttributeError,ValueError,TypeError,OverflowError,OSError):raise Rejected('invalid usage timestamp')
    # Live meter age is authoritative. Stored labels remain telemetry. An
    # expired old exception can retain its captured epoch after observed reset,
    # but cannot grant cap authority or admit ambiguous timestamp ordering.
    checked=timestamp(u.get('checked_at'));now=time.time()
    need(0<=now-checked<=60,'stale/future live timestamp')
    route='matching_reset'
    if captured!=actual:
        route='expired_post_reset'
        need(reset.group(1)=='expired' and captured<actual and telemetry is not None,'unknown/active/backward reset mismatch')
        cached_epoch=timestamp(telemetry.group(1))
        need(captured<=cached_epoch<=checked<=now<actual,'post-reset timestamp order')
    return dict(cadence=str(cadence),next_at_plus=str(next_at),projected_points=str(points+(live-cached)),
        next_checkpoint_points=str(points-since+next_at),points_since_register=str(since),
        live_used_percent=str(live),cached_used_percent=str(cached),captured_reset=captured,live_reset=actual,
        stored_freshness_label=telemetry.group(2) if telemetry else None,cache_label_authority=False,
        read_only_interfaces=True,ordinary_cap_percent=80,route=route)

def validate_budget(ledger,mapping,g):
    need(not ledger.get('legacy_totals') and mapping['ledger_path']==g['canonical_ledger'],'canonical native ledger required')
    need(ledger['caps']['max_concurrent_gpu_jobs']==99 and decimal(ledger['caps']['reserved_gpu_hours'])==125,'unchanged ledger caps')
    rows=ledger['reservations'];entries={r['id']:r for r in rows};items=mapping['entries']
    need(len(entries)==len(rows) and len(items)==len(entries) and {e['reservation_id'] for e in items}==set(entries),'mapping incomplete/duplicate')
    need(sum(r['status'] in ('PENDING','RUNNING') and r['gpus']>0 for r in rows)<=99,'concurrency99 exceeded')
    rounded={k:Decimal('0') for k in ('A1','A2','A3')};exact=rounded.copy()
    for item in items:
        row=entries[item['reservation_id']];phase=item['experiment'];need(phase in rounded,'phase unknown')
        need(all(row.get(k)==item['actual_entry'].get(k) for k in IMMUTABLE_FIELDS),'immutable charge drift')
        need(row['reserved_gpu_hours']==round(row['gpus']*row['requested_minutes']/60,4)==item['original_reserved_gpu_hours'],'original native rounded charge')
        rounded[phase]+=decimal(row['reserved_gpu_hours']);exact[phase]+=decimal(row['gpus'])*decimal(row['requested_minutes'])*60
    need(round(float(sum(rounded.values())),4)==ledger['totals']['reserved_gpu_hours'],'native ledger total')
    need(g['experiment_limits']=={'A1':25,'A2':60,'A3':40} and g['global_limit']==125,'phase/global limits changed')
    need(sum(rounded.values())<=125 and sum(exact.values())<=450000,'global exact/rounded cap')
    for phase,limit in g['experiment_limits'].items():need(rounded[phase]<=limit and exact[phase]<=limit*3600,'phase exact/rounded cap '+phase)
    row=entries[g['reservation_id']];item=next(x for x in items if x['reservation_id']==row['id'])
    need(item['experiment']=='A2' and row['job_id']==g['actual_job_id'] and row['cluster']=='bridges2'
        and row['account']==g['expected_account'] and row['partition'] in g['allowed_partitions'],'actual A2 row placement')
    need(row['source_commit']==SOURCE and Path(row['output_dir']).resolve()==Path(g['main_root']).resolve(),'actual A2 source/output')
    need(row['gpus']==g['resources']['GPU_count']==1 and decimal(row['requested_minutes'])*60==g['resources']['duration_seconds']
        and row['status'] in ('PENDING','RUNNING'),'exact reviewed duration/GPU, no old hour default')
    return dict(phase_reserved={k:str(v) for k,v in rounded.items()},exact_requested_GPU_seconds_by_phase={k:str(v) for k,v in exact.items()},
        exact_requested_GPU_seconds_total=format(sum(exact.values()).normalize(),'f'),all_original_charges_retained=True)

def call(argv,**kwargs):
    return subprocess.run(argv,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=25,**kwargs)

def usage(b,work,label):
    u=decode(call(['/u/swong2/.local/bin/codex-usage','--pause-at','80']).stdout)
    status=call(['/u/swong2/.local/bin/research-session','status','--session',b['session']]).stdout
    projection=validate_usage(u,status,b['session'])
    exclusive(Path(work)/(label+'-usage.json'),encoded(dict(live=u,session_status=status,projection=projection,checked_unix=time.time())))
    return projection

def check_manifest(path,expected):
    path=ordinary(path);need(sha(path)==expected,'packet manifest changed');value=read(path)
    files=value.get('files',value.get('files_sha256',value))
    need(type(files) is dict and files,'nonempty packet members required')
    result={}
    for name,digest in files.items():
        rel=Path(name);need('..' not in rel.parts,'unsafe packet path')
        member=rel if rel.is_absolute() else path.parent/rel
        ordinary(member);need(sha(member)==digest,'packet member changed: '+str(member));result[str(member)]=digest
    return result

def collect_reference_closure(refs):
    snapshot={};pins={};pending=list(refs)
    while pending:
        ref=pending.pop();path=str(ref['path'])
        if path in pins:
            need(pins[path]==ref['sha256'],'conflicting immutable reference');continue
        need(Path(path).suffix=='.json','proof closure only reads JSON, never model/weight files')
        value=bound(ref);raw=Path(path).read_bytes();need(sha_bytes(raw)==ref['sha256'],'proof changed during capture')
        pins[path]=ref['sha256'];snapshot[path]=raw
        def visit(item):
            if type(item) is dict:
                if set(item)=={'path','sha256'}:pending.append(item)
                else:
                    for child in item.values():visit(child)
            elif type(item) is list:
                for child in item:visit(child)
        visit(value)
    need(all(Path(path).read_bytes()==raw for path,raw in snapshot.items()),'reference closure changed')
    return snapshot

def collect_packet_files(b,g,c):
    snapshot={}
    refs=[b['helper_manifest'],dict(path=g['packet_manifest'],sha256=g['packet_manifest_sha256']),c['packet_manifest']]
    for ref in refs:
        files=check_manifest(ref['path'],ref['sha256'])
        snapshot[ref['path']]=Path(ref['path']).read_bytes()
        for path,digest in files.items():
            raw=ordinary(path).read_bytes();need(sha_bytes(raw)==digest,'packet changed during capture');snapshot[path]=raw
    return snapshot

def source_export(g):
    snapshot=bound(dict(path=g['snapshot'],sha256=g['snapshot_sha256']));runtime=Path(g['runtime'])
    need(snapshot['source_commit']==SOURCE and Path(snapshot['runtime_root'])==runtime,'original source namespace')
    files,links=snapshot['source_sha256'],snapshot['input_links']
    need(len(files)==511 and len(links)==4 and not snapshot['source_code_symlinks'] and not set(files)&set(links),'closed511+4 source identity')
    actual_files=set();actual_links=set()
    for path in runtime.rglob('*'):
        if path.is_symlink():actual_links.add(str(path.relative_to(runtime)))
        elif path.is_file():actual_files.add(str(path.relative_to(runtime)))
    need(actual_files==set(files) and actual_links==set(links),'source inventory drift')
    for name,digest in files.items():
        rel=Path(name);need(not rel.is_absolute() and '..' not in rel.parts and str(rel)==name,'unsafe source key')
        ordinary(runtime/rel);need((runtime/rel).resolve().is_relative_to(runtime.resolve()) and sha(runtime/rel)==digest,'source bytes changed')
    for name,target in links.items():
        rel=Path(name);path=runtime/rel;need(not rel.is_absolute() and '..' not in rel.parts and str(rel)==name,'unsafe source alias')
        need(path.is_symlink() and os.readlink(str(path))==target and path.exists() and path.resolve()==Path(target).resolve(),'literal source input alias drift')
    return snapshot

def native_runtime(g):
    source_export(g);root=Path(g['runtime']).resolve()
    for name,module in list(sys.modules.items()):
        path=getattr(module,'__file__',None)
        if path and name.split('.')[0] in PROJECTS:need(Path(path).resolve().is_relative_to(root),'project import fallback')
    sys.path.insert(0,str(root));module=importlib.import_module('component_analysis.a3_direction_runtime')
    for name,item in list(sys.modules.items()):
        path=getattr(item,'__file__',None)
        if path and name.split('.')[0] in PROJECTS:need(Path(path).resolve().is_relative_to(root),'native normalization source fallback')
    return module

def collect_native_closure(g):
    ar=native_runtime(g)
    identity=dict(purpose='A2 original source50e full scoring',source_commit=SOURCE,groups_sha256=g['groups_file_sha256'],main_root=g['main_root'])
    normalized=ar.normalize_ledger(g['mapping_origin'],identity=identity,include_envelope=False,refresh_deadline=time.time()+20)
    ledger_raw=ordinary(g['canonical_ledger']).read_bytes();need(sha_bytes(ledger_raw)==normalized['current_snapshot_sha256'],'native ledger changed during normalization')
    mapping=ar.read_object(normalized['active_mapping_reference']['path']);budget=validate_budget(decode(ledger_raw),mapping,g)
    refs=normalized['mapping_lineage_references']
    need(refs and refs[0]==normalized['original_mapping_reference'] and refs[-1]==normalized['active_mapping_reference'],'complete native lineage origin/active closure')
    snapshot={g['canonical_ledger']:ledger_raw}
    for ref in refs:
        path=Path(ref['path']);need(ar.object_reference(path)==ref,'native mapping reference changed')
        value=ar.read_object(path)
        for root in [path]+[Path(p) for p in value['original_admission_paths']]:
            for filename in ('payload.json','COMPLETE.json'):
                member=ordinary(root/filename);snapshot[str(member)]=member.read_bytes()
        frozen=ordinary(value['ledger_snapshot_path']);need(sha(frozen)==value['ledger_sha256'],'preserved original ledger snapshot changed')
        snapshot[str(frozen)]=frozen.read_bytes()
    need(sha(g['canonical_ledger'])==normalized['current_snapshot_sha256'],'ledger changed after lineage capture')
    return snapshot,normalized,budget

def wait_cpu_complete(c,waiting,deadline_observer=None):
    """Wait only within the original immutable GPU window; never renew it.

    The optional observer is a read-only allocation observation used by Producer,
    not a proof/model/source injection. It can only shorten the original bound.
    COMPLETE is parsed and authenticated separately after this bounded wait.
    """
    root=Path(c['evidence_output']);need(root.is_dir() and not root.is_symlink(),'actual CPU evidence root')
    requested=decimal(waiting['requested_at']);bound_end=decimal(waiting['publication_deadline'])
    need(0<bound_end-requested<=300,'one finite immutable GPU WAITING window')
    complete=root/'COMPLETE.json';next_observation=Decimal('0')
    while True:
        now=decimal(time.time());need(requested<=now<bound_end,'CPU wait reached fixed publication/entry deadline')
        present=complete.exists() or complete.is_symlink()
        if deadline_observer is not None and (now>=next_observation or present):
            bound_end=min(bound_end,decimal(deadline_observer()))
            now=decimal(time.time());next_observation=now+2
            need(requested<=now<bound_end,'CPU wait reached shortened actual allocation bound')
        for name in ('FAILED.json','FAILED-full_score.json'):
            failed=root/name;need(not failed.exists() and not failed.is_symlink(),'actual CPU failure supersedes COMPLETE')
        need(not complete.is_symlink(),'CPU COMPLETE must be ordinary')
        if present:
            ordinary(complete);need(decimal(time.time())<bound_end,'CPU COMPLETE observed at/after deadline')
            return complete
        left=bound_end-decimal(time.time());need(left>0,'CPU wait deadline elapsed before sleep')
        time.sleep(float(min(Decimal('0.2'),left)))

def capture_cpu(c,r,g,gsha,rsha,now=None):
    now=time.time() if now is None else now
    root=Path(c['evidence_output']);need(root.is_dir() and not root.is_symlink(),'actual CPU evidence directory')
    need(not any((root/n).exists() for n in ('FAILED.json','FAILED-full_score.json')),'CPU failure supersedes partial COMPLETE')
    files={str(ordinary(p)):p.read_bytes() for p in root.iterdir() if p.is_file()}
    need(not any(p.is_symlink() for p in root.iterdir()),'CPU evidence symlink')
    def body(name):
        key=str(root/name);need(key in files,'missing actual CPU evidence: '+name);return decode(files[key])
    q=body('COMPLETE.json');validate_complete(q,r,rsha,g,gsha,now)
    guard=body('guard-result.json');run=body('child-execution.json');parameters=body('parameters.json')
    need(sha_bytes(files[str(root/'guard-result.json')])==q['guard_result_sha256']==run['guard_result_sha256']
        and sha_bytes(files[str(root/'child-execution.json')])==q['child_execution_sha256']
        and sha_bytes(files[str(root/'parameters.json')])==q['parameters_sha256'],'CPU immutable member hashes')
    need(body('request.json')==r and sha_bytes(files[str(root/'request.json')])==rsha and run['request_sha256']==rsha,'CPU immutable request')
    need(sha_bytes(files[str(root/'WAITING.json')])==r['GPU_WAITING_marker_sha256'],'CPU immutable WAITING copy')
    need(run['exit_code']==0 and run['term_sent_at'] is None and run['started_unix']<=run['finished_unix']<run['deadline_unix'],'normal timely actual CPU child')
    need(parameters['phase']=='full_score' and parameters['phase_request_sha256']==rsha
        and parameters['actual_CPU_job_id']==c['standing_CPU_job_id'] and parameters['actual_future_GPU_job_id']==g['actual_job_id'],'actual child parameters')
    need(guard['complete'] is False and guard['source_before']==guard['source_after']==q['source_after']
        and q['source_before']==q['source_after'],'CPU stable source identity')
    need(q['catalogues']==guard['catalogues'] and len(q['catalogues'])==4
        and {x['virtual_path'] for x in q['catalogues']}==set(g['minimum_registry_paths']),'complete CPU catalogue identity')
    captures=q['catalogue_capture_files'];need(len(captures)==4 and {x['virtual_path'] for x in captures}==set(g['minimum_registry_paths']),'four actual CPU catalogue captures')
    for row in captures:
        path=Path(row['captured_bytes_path']);need(path.parent==root and str(path) in files
            and len(files[str(path)])==row['bytes'] and sha_bytes(files[str(path)])==row['sha256']==q['source_after']['catalogues'][row['virtual_path']],'actual CPU catalogue snapshot changed')
    need(all(Path(path).read_bytes()==raw for path,raw in files.items()),'CPU bytes changed during capture')
    return q,files

def physical(g,virtual):
    rel=Path(virtual).relative_to(ROOT);need(Path(virtual).is_absolute() and '..' not in rel.parts,'remote namespace traversal')
    return str(Path(g['physical_Alignment_root'])/rel)

def duration_seconds(text):
    match=re.fullmatch(r'(?:(\d+)-)?(\d+):(\d+):(\d+)',text)
    if match:
        day,hour,minute,second=(int(x or 0) for x in match.groups());return day*86400+hour*3600+minute*60+second
    match=re.fullmatch(r'(\d+):(\d+)',text)
    need(match is not None,'invalid Slurm duration');return int(match.group(1))*60+int(match.group(2))

def memory_bytes(text):
    match=re.fullmatch(r'([0-9]+(?:[.][0-9]+)?)([KMGT]?)',text);need(match is not None,'invalid TRES memory')
    return decimal(match.group(1))*{'':1,'K':1024,'M':1024**2,'G':1024**3,'T':1024**4}[match.group(2)]

def epoch(text):return datetime.datetime.strptime(text,'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp()

def gpu_facts(raw,g,remote_uid):
    f=dict(x.split('=',1) for x in raw.split() if '=' in x);r=g['resources']
    need(f['JobId']==g['actual_job_id'] and f['JobState']=='RUNNING' and f['Account']==g['expected_account']
        and f['QOS']==g['expected_qos'] and f['Partition'] in g['allowed_partitions'],'actual GPU placement/state')
    need(type(remote_uid) is int and remote_uid>=0 and '('+str(remote_uid)+')' in f['UserId'] and f['NumNodes']=='1' and f['Requeue']=='0' and f['Restarts']=='0','actual remote owner/single nonrequeued allocation')
    tres=dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x)
    need(int(f['NumCPUs'])==r['CPUs']==int(tres['cpu']) and memory_bytes(tres['mem'])==r['RAM_bytes']
        and duration_seconds(f['TimeLimit'])==r['duration_seconds'],'exact reviewed actual GPU resources')
    need(tres.get('gres/gpu')==str(r['GPU_count'])=='1' and
        (tres.get('gres/gpu:h100-80')=='1' or f.get('TresPerNode')=='gres:gpu:h100-80:1'),'typed actual H100 allocation')
    need(epoch(f['EndTime'])-time.time()-r['finish_margin_seconds']>=r['minimum_entry_seconds'],'actual GPU entry deadline/floor')
    return f

def cpu_facts(raw,c):
    f=dict(x.split('=',1) for x in raw.split() if '=' in x);t=dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x)
    need(f['JobId']==c['standing_CPU_job_id'] and f['JobState']=='RUNNING' and f['Account']==c['expected_account']
        and f['Account'].endswith('-cpu') and f['Partition'] in c['allowed_partitions'] and f['QOS']==c['expected_qos'],'actual CPU placement/state')
    need('('+str(os.getuid())+')' in f['UserId'] and f['NumNodes']=='1' and f['Requeue']=='0' and f['Restarts']=='0','actual CPU owner/no retry')
    need(int(f['NumCPUs'])==c['CPUs']==int(t['cpu']) and memory_bytes(t['mem'])==c['RAM_bytes']
        and duration_seconds(f['TimeLimit'])==c['duration_seconds'] and not any(k.startswith('gres/gpu') for k in t),'exact reviewed CPU-only allocation')
    need(time.time()<epoch(f['EndTime'])-c['CPU_finish_margin_seconds'],'actual CPU deadline')
    return f

def inspection_program(payload):
    return '\n'.join(['import json,hashlib,subprocess,os,time','from pathlib import Path',
        'p=json.loads('+repr(json.dumps(payload))+')',
        "h=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()",
        "r={'files':{x:(h(x) if Path(x).is_file() and not Path(x).is_symlink() else None) for x in p['files']},'waiting_sha256':h(p['waiting']),'release_exists':Path(p['final']).exists() or Path(p['final']).is_symlink(),'pending_exists':Path(p['final']+'.pending').exists() or Path(p['final']+'.pending').is_symlink(),'raw_scontrol':subprocess.check_output(['scontrol','show','job',p['job'],'-o'],universal_newlines=True,timeout=15,env=dict(os.environ,TZ='UTC')),'captured_unix':time.time(),'remote_uid':os.getuid()}",
        "r['aliases']={}",
        "for name in p['files']:",
        " path=Path(name)",
        " if path.is_symlink():",
        "  literal=os.readlink(str(path));target=Path(literal) if Path(literal).is_absolute() else path.parent/literal",
        "  if p.get('virtual_root'):",
        "   try:target=Path(p['physical_root'])/target.relative_to(p['virtual_root'])",
        "   except ValueError:pass",
        "  target=target.resolve();kind='file' if target.is_file() else ('directory' if target.is_dir() else 'missing')",
        "  r['aliases'][name]={'literal_target':literal,'resolved_target':str(target),'target_kind':kind,'target_sha256':h(target) if kind=='file' else None}",
        'print(json.dumps(r))',''])

def remote_publish_program(payload):
    # Entire final barrier executes remotely before atomic publication; compatible
    # with Python3.6 and independent of local Slurm/cache observations.
    return '\n'.join([
        'import json,hashlib,os,time,subprocess,re,datetime','from pathlib import Path','from decimal import Decimal',
        'p=json.loads('+repr(json.dumps(payload))+')',
        "h=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()",
        "raw=subprocess.check_output(['scontrol','show','job',p['job'],'-o'],universal_newlines=True,timeout=15,env=dict(os.environ,TZ='UTC'))",
        "f=dict(x.split('=',1) for x in raw.split() if '=' in x);r=p['resources']",
        "assert f['JobId']==p['job'] and f['JobState']=='RUNNING' and f['Account']==p['account'] and f['QOS']==p['expected_qos'] and f['Partition'] in p['allowed_partitions']",
        "assert '('+str(os.getuid())+')' in f['UserId'] and f['NumNodes']=='1' and f['Requeue']=='0' and f['Restarts']=='0'",
        "t=dict(x.split('=',1) for x in f.get('AllocTRES',f.get('TRES','')).split(',') if '=' in x)",
        "assert int(f['NumCPUs'])==r['CPUs']==int(t['cpu']) and t.get('gres/gpu')==str(r['GPU_count'])=='1' and (t.get('gres/gpu:h100-80')=='1' or f.get('TresPerNode')=='gres:gpu:h100-80:1')",
        "match=re.fullmatch(r'([0-9]+(?:[.][0-9]+)?)([KMGT]?)',t['mem']);assert match is not None",
        "assert Decimal(match.group(1))*{'':1,'K':1024,'M':1024**2,'G':1024**3,'T':1024**4}[match.group(2)]==r['RAM_bytes']",
        "match=re.fullmatch(r'(?:(\\d+)-)?(\\d+):(\\d+):(\\d+)',f['TimeLimit'])",
        "if match:",
        " day,hour,minute,second=(int(x or 0) for x in match.groups());duration=day*86400+hour*3600+minute*60+second",
        "else:",
        " match=re.fullmatch(r'(\\d+):(\\d+)',f['TimeLimit']);assert match is not None;duration=int(match.group(1))*60+int(match.group(2))",
        "assert duration==r['duration_seconds']",
        "end=datetime.datetime.strptime(f['EndTime'],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=datetime.timezone.utc).timestamp();deadline=min(end,p['initial_end_epoch'])-r['finish_margin_seconds']",
        "assert p['phase']=='full_score' and time.time()<p['publication_deadline'] and time.time()<p['expiry'] and deadline-time.time()>=r['minimum_entry_seconds']",
        "assert not Path(p['pending']).is_symlink() and not Path(p['waiting']).is_symlink() and h(p['pending'])==p['sha'] and h(p['waiting'])==p['waiting_sha'] and not Path(p['final']).exists() and not Path(p['final']).is_symlink()",
        "body=json.loads(Path(p['pending']).read_text());waiting=json.loads(Path(p['waiting']).read_text())",
        "assert body.get('phase')=='full_score'",
        "if p.get('strict_payload'):",
        " assert body['phase']=='full_score' and body['full_scoring_admitted'] is True and body['actual_job_id']==p['job'] and body['source_commit']==p['source_commit'] and body['resources']==r",
        " assert waiting['job_id']==p['job'] and waiting['phase']=='full_score' and waiting['resources']==r and waiting['bound_config_sha256']==body['bound_config_sha256'] and waiting['publication_deadline']==p['publication_deadline']",
        " assert body['issued_at']>=waiting['requested_at'] and body['expires_at']==body['issued_at']+300 and body['issued_at']<=time.time()<body['expires_at']",
        "now=time.time();assert now<p['expiry'] and now<p['publication_deadline'] and deadline-now>=r['minimum_entry_seconds']",
        "assert h(p['pending'])==p['sha'] and h(p['waiting'])==p['waiting_sha']",
        "os.link(p['pending'],p['final']);Path(p['pending']).unlink()",
        "print(json.dumps({'published':True,'sha256':h(p['final']),'actual_scontrol':raw,'deadline_epoch':deadline}))",''])

class Transport:
    def __init__(self,b,g):self.b=b;self.g=g
    def remote(self,script):return decode(call(self.b['ssh_argv']+['python3 -'],input=script).stdout)
    def inspect(self,paths,waiting,final):return self.remote(inspection_program(dict(files=paths,waiting=waiting,final=final,job=self.g['actual_job_id'],virtual_root=str(ROOT),physical_root=self.g['physical_Alignment_root'])))
    def fetch(self,remote,local):
        need(not Path(local).exists(),'fetch destination already exists')
        call(['rsync','-rl','--no-perms','--no-times','-e',shlex.join(self.b['rsync_ssh_argv']),'--',self.b['dtn_host']+':'+remote,str(local)])
    def stage(self,files,work):
        tree=Path(work)/'transfer-tree';tree.mkdir();names=[]
        for route,raw in sorted(files.items()):
            rel=Path(route).relative_to(ROOT);need('..' not in rel.parts,'unsafe stage route')
            path=tree/rel;path.parent.mkdir(parents=True,exist_ok=True);exclusive(path,raw);names.append(str(rel))
        listing=Path(work)/'transfer-files.txt';exclusive(listing,''.join(n+'\n' for n in names).encode())
        parents=sorted({str(Path(physical(self.g,route)).parent) for route in files})
        self.remote('import json\nfrom pathlib import Path\nfor p in json.loads('+repr(json.dumps(parents))+'):Path(p).mkdir(parents=True,exist_ok=True)\nprint(\'{}\')\n')
        call(['rsync','-rl','--no-perms','--no-times','--checksum','--files-from='+str(listing),'-e',shlex.join(self.b['rsync_ssh_argv']),
            '--',str(tree)+'/',self.b['dtn_host']+':'+self.g['physical_Alignment_root']+'/'])
    def cache_check(self):
        need(Path(cache_gate.__file__).resolve()==Path(__file__).resolve().parent/'cache_gate.py','exact reviewed cache gate origin')
        proof=bound(dict(path=self.g['model_cache_proof'],sha256=self.g['model_cache_proof_sha256']))
        ref=self.b['remote_model_cache_reference'];full=proof['original_full_proof']
        need(ref['sha256']==proof['reference']['sha256']==cache_gate.REFERENCE_SHA and full['sha256']==cache_gate.FULL_PROOF_SHA,'accepted complete cache proof/reference pins')
        script=Path(cache_gate.__file__).read_text()+'\nprint(json.dumps(check_cache('+repr(ref['path'])+','+repr(physical(self.g,full['path']))+','+repr(self.g['physical_HF_cache'])+')))\n'
        return self.remote(script)
    def publish(self,local,final,waiting,waiting_sha,expiry,initial_end_epoch=None):
        # Exclusive remote creation prevents rsync from overwriting a pending
        # release that appeared after the last inspection.
        body=read(local);r=self.g['resources'];marker=read(self.b['_local_waiting'])
        raw=Path(local).read_bytes()
        self.remote('import json\nfrom pathlib import Path\np=Path('+repr(final+'.pending')+')\nwith p.open(\'xb\') as f:f.write('+repr(raw)+')\nprint(\'{}\')\n')
        payload=dict(pending=final+'.pending',final=final,sha=sha_bytes(raw),waiting=waiting,waiting_sha=waiting_sha,expiry=expiry,
            job=self.g['actual_job_id'],account=self.g['expected_account'],phase='full_score',resources=r,
            expected_qos=self.g['expected_qos'],allowed_partitions=self.g['allowed_partitions'],
            source_commit=SOURCE,strict_payload=True,initial_end_epoch=initial_end_epoch,
            publication_deadline=marker['publication_deadline'])
        return self.remote(remote_publish_program(payload))

def load_module(path,name):
    spec=importlib.util.spec_from_file_location(name,str(path));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    need(Path(module.__file__).resolve()==Path(path).resolve(),'pinned module origin');return module

def packet_module(files,basename):
    paths=[Path(p) for p in files if Path(p).name==basename]
    need(len(paths)==1,'exact owning packet member required: '+basename);return paths[0]

def verify_runtime_pins(b,g,c):
    need(bound(b['gpu_config'])==g and bound(b['standing_config'])==c,'bound config changed')
    helper_files=check_manifest(b['helper_manifest']['path'],b['helper_manifest']['sha256'])
    here=Path(__file__).resolve().parent
    need({str(here/'helper.py'),str(here/'cache_gate.py'),str(here/'bindings.template.json')}<=set(helper_files),'root implementation member closure')
    need(sha(here/'cache_gate.py')=='55d6517228832e0254c10086d03d3b5e3534ad91bf8ddbe54d96e9913fa3fa06','unchanged accepted cache algorithm')
    gpu_files=check_manifest(g['packet_manifest'],g['packet_manifest_sha256'])
    cpu_files=check_manifest(c['packet_manifest']['path'],c['packet_manifest']['sha256'])
    need(c['packet_manifest']['sha256']==c['packet_manifest_sha256'] and c['GPU_packet_manifest_sha256']==g['launch_packet_manifest_sha256']==g['packet_manifest_sha256'],'new owning CPU/GPU packet binding')
    gpu=load_module(packet_module(gpu_files,'common.py'),'full_score_root_gpu_guard')
    cpu=load_module(packet_module(cpu_files,'supervisor.py'),'full_score_root_cpu_guard')
    gpu.validate_config(g);cpu.validate_config(c)
    gpu.C=g;gpu.CONFIG=Path(b['gpu_config']['path'])
    gpu.packet();gpu.source();gpu.input_closure();gpu.verify_existing_bank(g);gpu.reviewed_admission();gpu.protection()
    admission=read(g['operational_admission'])
    need(admission.get('kind')!='a3_root_pilot_admission_v1' and 'pilot_root' not in admission and 'bank_and_prefix4_only' not in admission,'A2 full admission cannot inherit old authority kind/scope')
    need(g['phase']==c['phase']==b['phase']=='full_score' and b['usage_pause_percent']==80,'closed full-only ordinary80 bindings')
    need(g['main_root']==c['frozen_G3_root'] and g['groups_file_sha256']==c['frozen_G3_sha256']
        and g['bank_file_sha256']==c['bank_file_sha256'] and g['bank_manifest_sha256']==c['bank_manifest_sha256'],'actual original G3/bank CPU/GPU identity')
    authenticate_cutover(b,g)
    return gpu,cpu

def load_bindings(path,digest):
    b=bound(dict(path=str(path),sha256=digest));template=read(Path(__file__).resolve().parent/'bindings.template.json')
    need(set(b)==set(template),'closed root bindings')
    def nonnull(value):
        need(value is not None,'unbound root bindings')
        if isinstance(value,dict):
            for v in value.values():nonnull(v)
        elif isinstance(value,list):
            for v in value:nonnull(v)
    nonnull(b);g=bound(b['gpu_config']);c=bound(b['standing_config'])
    need(b['phase']=='full_score' and b['usage_pause_percent']==80 and b['session'],'full-only hard80 session binding')
    need(Path(b['state_directory']).is_absolute() and Path(b['state_directory']).resolve().is_relative_to(ROOT),'root state namespace')
    need(not Path(b['state_directory']).resolve().is_relative_to(Path(c['evidence_output']).resolve())
        and not Path(c['evidence_output']).resolve().is_relative_to(Path(b['state_directory']).resolve()),'root state cannot overlap immutable CPU evidence')
    need(b['GPU_execution_output']==g['evidence_root'] and b['GPU_release_directory']==g['release_directory'],'actual GPU evidence/release namespace')
    need(b['ssh_argv'][0]=='ssh' and b['rsync_ssh_argv'][0]=='ssh' and b['dtn_host']=='b2dtn'
        and not any('HostName=' in arg for arg in b['rsync_ssh_argv']),'explicit approved SSH/DTN transport')
    verify_runtime_pins(b,g,c);return b,g,c

class Producer:
    def __init__(self,b,g,c,phase):
        need(phase=='full_score','full_score only')
        self.b=b;self.g=g;self.c=c;self.phase=phase
        self.transport=Transport(b,g);self.work=Path(b['state_directory'])/g['actual_job_id']/phase
    def waiting_paths(self):
        return (physical(self.g,Path(self.b['GPU_execution_output'])/'WAITING-full_score.json'),
            physical(self.g,Path(self.b['GPU_release_directory'])/(self.g['actual_job_id']+'-full_score.json')))
    def inspect(self,paths):
        waiting,final=self.waiting_paths();result=self.transport.inspect(paths,waiting,final)
        gpu_facts(result['raw_scontrol'],self.g,result['remote_uid'])
        need(not result['release_exists'] and not result['pending_exists'],'release/pending collision; no renewal')
        return result
    def trigger(self):
        self.work.mkdir(parents=True,exist_ok=False)
        verify_runtime_pins(self.b,self.g,self.c);usage(self.b,self.work,'trigger')
        # No ledger or reader mutation: observe completed root cutover and run
        # the original normalizer before issuing the only CPU request.
        _,normalized,_=collect_native_closure(self.g)
        authenticate_cutover(self.b,self.g,normalized)
        waiting,final=self.waiting_paths();marker=self.work/'fetched-GPU-WAITING.json'
        self.transport.fetch(waiting,marker);w=read(marker);observed=self.inspect([])
        need(observed['waiting_sha256']==sha(marker),'actual fetched WAITING changed')
        initial_end=epoch(gpu_facts(observed['raw_scontrol'],self.g,observed['remote_uid'])['EndTime'])
        ready_path=Path(self.c['evidence_output'])/'READY.json';ready=read(ordinary(ready_path))
        need(ready['phase']=='full_score' and ready['actual_CPU_job_id']==self.c['standing_CPU_job_id']
            and ready['source_commit']==SOURCE and ready['packet_manifest_sha256']==self.c['packet_manifest_sha256']
            and ready['GPU_admitted'] is False,'standing actual CPU READY')
        cpu_raw=call(['scontrol','show','job',self.c['standing_CPU_job_id'],'-o'],env=dict(os.environ,TZ='UTC')).stdout;cpu_facts(cpu_raw,self.c)
        verify_runtime_pins(self.b,self.g,self.c)
        r=construct_request(w,self.c,self.g,self.b['gpu_config']['sha256'],marker,sha(marker),time.time());check_request_fresh(r,time.time())
        request_path=Path(self.c['request_path']);need(not request_path.is_symlink(),'ordinary new CPU request')
        atomic_new(request_path,encoded(r))
        exclusive(self.work/'trigger-record.json',encoded(dict(actual_GPU_job_id=self.g['actual_job_id'],
            GPU_config_sha256=self.b['gpu_config']['sha256'],request=str(request_path),request_sha256=sha(request_path),
            marker=str(marker),marker_sha256=sha(marker),CPU_READY_sha256=sha(ready_path),
            initial_GPU_end_epoch=initial_end,actual_GPU_scontrol=observed['raw_scontrol'],actual_CPU_scontrol=cpu_raw)))
        return dict(triggered=True,request=str(request_path),phase='full_score')
    def publish(self):
        need(self.work.is_dir(),'trigger required first');verify_runtime_pins(self.b,self.g,self.c)
        exclusive(self.work/'publish-once.claim',encoded(dict(claimed_unix=time.time())))
        usage(self.b,self.work,'publish-start')
        record=read(self.work/'trigger-record.json');request_path=ordinary(record['request']);marker=ordinary(record['marker'])
        need(sha(request_path)==record['request_sha256'] and sha(marker)==record['marker_sha256'],'immutable request/WAITING changed')
        r=read(request_path);w=read(marker)
        need(r['phase']=='full_score' and r['actual_future_GPU_job_id']==record['actual_GPU_job_id']==self.g['actual_job_id']
            and r['final_GPU_bound_config_sha256']==record['GPU_config_sha256']==self.b['gpu_config']['sha256'],'trigger immutable actual binding')
        need(record['marker_sha256']==r['GPU_WAITING_marker_sha256'],'trigger WAITING reference changed')
        def waiting_bound():
            need(sha(request_path)==record['request_sha256'] and sha(marker)==record['marker_sha256'],'request/WAITING changed during CPU wait')
            observed=self.inspect([])
            need(observed['waiting_sha256']==record['marker_sha256'],'actual remote WAITING changed during CPU wait')
            facts=gpu_facts(observed['raw_scontrol'],self.g,observed['remote_uid'])
            return min(epoch(facts['EndTime']),record['initial_GPU_end_epoch'])-self.g['resources']['finish_margin_seconds']-self.g['resources']['minimum_entry_seconds']
        wait_cpu_complete(self.c,w,deadline_observer=waiting_bound)
        q,cpu_files=capture_cpu(self.c,r,self.g,self.b['gpu_config']['sha256'],record['request_sha256'])
        complete_path=Path(self.c['evidence_output'])/'COMPLETE.json'
        need(q['CPU_bound_config_sha256']==self.b['standing_config']['sha256'],'actual CPU config proof binding')
        snapshot,normalized,budget=collect_native_closure(self.g)
        authenticate_cutover(self.b,self.g,normalized)
        snapshot.update(cpu_files)
        snapshot.update(collect_packet_files(self.b,self.g,self.c))
        proof=bound(dict(path=self.g['protection_proof'],sha256=self.g['protection_proof_sha256']))
        rows=q['catalogues'];need(proof['catalogues']==rows,'current reviewed protection closure differs from CPU proof')
        for row in rows:
            path=ordinary(row['virtual_path']);raw=path.read_bytes()
            need(sha_bytes(raw)==row['sha256'],'actual Delta catalogue changed since CPU proof')
            if path.name=='held_out.json':validate_heldout(decode(raw),proof)
            snapshot[str(path)]=raw
        # Stage immutable operational references, not a rewritten CPU COMPLETE.
        for key in ('snapshot','input_manifest','model_cache_proof','resource_proof','capacity_proof',
                    'operational_admission','protection_proof','delta_G3_receipt','bridges_G3_receipt','source_plan','packet_manifest'):
            path=Path(self.g[key]);path=path/'COMPLETE.json' if path.is_dir() else path
            need(sha(path)==self.g[key+'_sha256'],'operational proof drift: '+key);snapshot[str(path)]=path.read_bytes()
        snapshot.update(collect_reference_closure([self.b['gpu_config'],self.b['standing_config'],self.b['helper_manifest'],self.b['cutover_attestation'],self.c['packet_manifest'],self.c['base_parameters'],self.c['resource_proof'],dict(path=self.g['model_cache_proof'],sha256=self.g['model_cache_proof_sha256'])]))
        cache=self.transport.cache_check()
        need(cache['reference_sha256']==cache_gate.REFERENCE_SHA and cache['original_full_weight_proof_sha256']==cache_gate.FULL_PROOF_SHA
            and cache['revision']==cache_gate.REVISION and cache['full_weights_rehashed'] is False and cache['model_loaded'] is False,'actual accepted per-start cache proof')
        cache.update(actual_job_id=self.g['actual_job_id'],phase='full_score',source_commit=SOURCE)
        cache_path=self.work/'actual-cache-check.json';exclusive(cache_path,encoded(cache))
        composite=dict(kind='root_composite_model_phase_preflight',complete=True,phase='full_score',source_commit=SOURCE,
            actual_GPU_job_id=self.g['actual_job_id'],actual_CPU_job_id=q['actual_CPU_job_id'],groups_file_sha256=self.g['groups_file_sha256'],
            actual_Delta_owning_guards_passed=True,stable_Delta_catalogues_before_after=True,immutable_CPU_proof_not_rewritten=True,
            continuous_live_Delta=False,catalogues=rows,ledger_sha256=normalized['current_snapshot_sha256'],
            active_mapping_reference=normalized['active_mapping_reference'],budget=budget,
            actual_CPU_COMPLETE=dict(path=str(complete_path),sha256=sha_bytes(cpu_files[str(complete_path)])),
            actual_per_start_cache_check=dict(path=str(cache_path),sha256=sha(cache_path)))
        composite_path=self.work/'composite-preflight.json';exclusive(composite_path,encoded(composite))
        snapshot[str(cache_path)]=cache_path.read_bytes();snapshot[str(composite_path)]=composite_path.read_bytes()
        # Files already provisioned remotely must be checked, never replaced.
        expected={self.g[k]:self.g[k+'_sha256'] for k in ('image','bank_file','bank_manifest')}
        expected[self.g['groups']]=self.g['groups_file_sha256']
        source=source_export(self.g)
        expected.update({str(Path(self.g['runtime'])/k):v for k,v in source['source_sha256'].items()})
        inputs=read(self.g['input_manifest']);expected.update(inputs['ordinary_sha256'])
        for path,raw in snapshot.items():
            if path in expected:need(expected[path]==sha_bytes(raw),'conflicting local closure proof')
        alias_expected={}
        aliases={str(Path(self.g['runtime'])/name):target for name,target in source['input_links'].items()}
        aliases.update(inputs['aliases'])
        for path,target in aliases.items():
            real=Path(path).resolve();kind='file' if real.is_file() else 'directory'
            alias_expected[physical(self.g,path)]=dict(literal_target=target,resolved_target=physical(self.g,real),
                target_kind=kind,target_sha256=sha(real) if kind=='file' else None)
        all_paths=set(snapshot)|set(expected)|set(aliases)
        remote=self.inspect([physical(self.g,p) for p in sorted(all_paths)])
        need(remote['waiting_sha256']==record['marker_sha256'] and remote['aliases']==alias_expected,'actual WAITING/source alias changed before transfer')
        mutable={self.g['canonical_ledger']}|{row['virtual_path'] for row in rows}
        for path,raw in snapshot.items():
            found=remote['files'][physical(self.g,path)]
            need(path in mutable or found is None or found==sha_bytes(raw),'immutable remote object differs; preserve original')
        need(all(remote['files'][physical(self.g,p)]==h for p,h in expected.items()),'actual remote source/bank/SIF/input proof changed')
        self.transport.stage(snapshot,self.work)
        checked=self.inspect([physical(self.g,p) for p in sorted(all_paths)])
        need(checked['waiting_sha256']==record['marker_sha256'] and checked['aliases']==alias_expected,'WAITING/source alias changed during transfer')
        need(all(checked['files'][physical(self.g,p)]==sha_bytes(raw) for p,raw in snapshot.items())
            and all(checked['files'][physical(self.g,p)]==h for p,h in expected.items()),'actual remote transfer/source mismatch')
        need(all(Path(p).read_bytes()==raw for p,raw in snapshot.items()),'actual Delta bytes changed during transfer')
        verify_runtime_pins(self.b,self.g,self.c)
        final_files,final_normalized,_=collect_native_closure(self.g)
        need(final_normalized['current_snapshot_sha256']==normalized['current_snapshot_sha256']
            and final_normalized['active_mapping_reference']==normalized['active_mapping_reference']
            and all(snapshot.get(p)==raw for p,raw in final_files.items()),'native chain changed before publication')
        authenticate_cutover(self.b,self.g,final_normalized)
        # Recheck actual cache after transfer; its original result stays immutable.
        final_cache=self.transport.cache_check()
        need({k:v for k,v in cache.items() if k not in ('checked_at_unix','actual_job_id','phase','source_commit')}
            =={k:v for k,v in final_cache.items() if k!='checked_at_unix'},'cache changed during transfer')
        final=self.inspect([physical(self.g,p) for p in sorted(all_paths)])
        need(final['waiting_sha256']==record['marker_sha256'] and final['aliases']==alias_expected and all(final['files'][physical(self.g,p)]==sha_bytes(raw) for p,raw in snapshot.items())
            and all(final['files'][physical(self.g,p)]==h for p,h in expected.items()),'actual remote final closure changed')
        current=gpu_facts(final['raw_scontrol'],self.g,final['remote_uid'])
        need(min(epoch(current['EndTime']),record['initial_GPU_end_epoch'])-self.g['resources']['finish_margin_seconds']-time.time()
            >=self.g['resources']['minimum_entry_seconds'],'shortened actual final entry floor')
        need(all(Path(p).read_bytes()==raw for p,raw in snapshot.items()) and sha(request_path)==record['request_sha256']
            and sha(marker)==record['marker_sha256'],'actual Delta immutable final closure changed')
        need(time.time()<w['publication_deadline'],'fixed WAITING publication window expired')
        final_cpu,final_cpu_files=capture_cpu(self.c,r,self.g,self.b['gpu_config']['sha256'],record['request_sha256'])
        need(final_cpu==q and final_cpu_files==cpu_files,'CPU final proof members/failure state changed')
        usage(self.b,self.work,'publish-final')
        need(not (Path(self.c['evidence_output'])/'FAILED.json').exists(),'CPU failed after final freshness check')
        release={k:copy.deepcopy(v) for k,v in self.g.items() if k.endswith('_sha256')}
        now=time.time();release.update(phase='full_score',full_scoring_admitted=True,actual_job_id=self.g['actual_job_id'],
            reservation_id=self.g['reservation_id'],source_commit=SOURCE,main_root=self.g['main_root'],
            resources=copy.deepcopy(self.g['resources']),bound_config_sha256=self.b['gpu_config']['sha256'],
            issued_at=now,expires_at=now+300,current_usage_pass=True,delta_fresh_preflight_passed=True,
            waiting_sha256=record['marker_sha256'],catalogues=rows,ledger_sha256=normalized['current_snapshot_sha256'],
            active_mapping_reference=normalized['active_mapping_reference'],delta_preflight_receipt=str(composite_path),
            delta_preflight_receipt_sha256=sha(composite_path))
        local=self.work/'root-release.json';exclusive(local,encoded(release))
        waiting,final_path=self.waiting_paths();self.b['_local_waiting']=str(marker)
        published=self.transport.publish(local,final_path,waiting,record['marker_sha256'],min(now+300,w['publication_deadline']),record['initial_GPU_end_epoch'])
        need(published['published'] is True and published['sha256']==sha(local),'remote publication identity')
        exclusive(self.work/'publication.json',encoded(dict(release_sha256=sha(local),published_unix=time.time(),remote=published,phase='full_score',once_only=True)))
        return published

def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('trigger','publish','run-phase'))
    parser.add_argument('--phase',required=True,choices=('full_score',));parser.add_argument('--bindings',required=True)
    parser.add_argument('--bindings-sha256',required=True);parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    b,g,c=load_bindings(args.bindings,args.bindings_sha256)
    if not args.execute:print(json.dumps(dict(status='VALIDATED_BINDINGS_ONLY_NO_EXECUTION',phase='full_score')));return
    producer=Producer(b,g,c,'full_score')
    if args.action=='run-phase':producer.trigger();result=producer.publish()
    else:result=getattr(producer,args.action)()
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
