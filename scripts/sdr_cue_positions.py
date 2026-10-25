#!/usr/bin/env python3
"""Complementary original-prefix head-output transplants. CPU readiness is not GPU release."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from scripts import sdr_cue_circuits as cc
from scripts import sdr_native_controls as n
from scripts import sdr_cue_probe as cue

PARENT_COMMIT = 'ca41bfdb2fd4e4c4c784eabd321ea75e41a45299'
PARENT_SHA = 'e0fc2da612fe08d29a9f913976e6e83341ef91b18405325356b6e49ad7ceeae8'
PARENT_SCIENCE = '9a3a3b645fa91ad7b7e84f19288919b5fbcc98aec7c9ecf6452713561f4fb9a9'
SPEC_SHA = 'b06fc61df13c9c64563d7043fd06502658fc32539cb659639038812b6c1a0cbe'
NEW_SOURCES = ['scripts/sdr_cue_positions.py', 'scripts/jobs/run_sdr_cue_positions.sh', 'tests/test_sdr_cue_positions.py']
SITES = ('early', 'tail', 'full')
FAMILIES = ('S', 'C_S')
AXES = (('E', 'report'), ('T', 'report'), ('T', 'retrieval'))
HEADER = '<|start_header_id|>assistant<|end_header_id|>'
USER_HEADER = '<|start_header_id|>user<|end_header_id|>'
canonical, digest, encoded = cc.canonical, cc.digest, cc.encoded
read_json, file_hash = cc.read_json, cc.file_hash


def source_hashes():
    names = set(cc.source_hashes()) | set(NEW_SOURCES) | {'analysis.py', 'config.py', 'l0.py'}
    return {name: file_hash(ROOT / name) for name in sorted(names)}


def _boundary(row, tokenizer, marker):
    prompt = row['prompt']
    if prompt.count(marker) != 1: raise ValueError('ambiguous structural header')
    char = prompt.index(marker)
    prefix = list(tokenizer.encode(prompt[:char], add_special_tokens=False))
    b = len(prefix)
    if prefix != row['ids'][:b] or not 0 < b < row['length']: raise ValueError('header prefix encode alignment')
    if row['ids'][b] != 128006: raise ValueError('header must begin at start_header token')
    offsets = row['offsets']
    if len(offsets) != row['length']: raise ValueError('offset geometry')
    for i, (a, z) in enumerate(offsets):
        if (a, z) == (0, 0):
            # Special-token offsets can be zero. Token prefix equality assigns
            # them by index, never by treating offset zero as a character span.
            if row['ids'][i] not in (128000, 128006, 128007, 128009): raise ValueError('unresolved zero token offset')
        elif not (0 <= a < z <= len(prompt)) or a < char < z or (i < b and z > char) or (i >= b and a < char):
            raise ValueError('crossing or misaligned header token offset')
    return char, b


def freeze_positions(row, tokenizer):
    char, b = _boundary(row, tokenizer, HEADER)
    user_char, user_b = _boundary(row, tokenizer, USER_HEADER)
    length = row['length']
    if length != len(row['ids']) or length + 64 > 224: raise ValueError('original prefix geometry')
    positions = {'early': list(range(b)), 'tail': list(range(b, length)), 'full': list(range(length)), 'system': list(range(user_b))}
    return {'char_boundary': char, 'b': b, 'n': length, 'user_char_boundary': user_char, 'user_b': user_b,
            'indices': positions, 'hashes': {s: digest(v) for s, v in positions.items()}}


def _payload(parent, spec_path, tokenizer):
    old = parent['payload']
    main, pairs = deepcopy(old['main']), deepcopy(old['pairs'])
    pool = deepcopy(old['calibration_pool'])
    positions = {r['id']: freeze_positions(r, tokenizer) for r in main + pool}
    by_id = {r['id']: r for r in main}
    for pair in pairs:
        a, b = [by_id[pair[e + '_id']] for e in ('recipient', 'donor')]
        pa, pb = positions[a['id']], positions[b['id']]
        if any(pa[k] != pb[k] for k in ('b', 'n', 'user_b')) or a['segments'] != b['segments'] or a['token_roles'] != b['token_roles']:
            raise ValueError('pair structural boundary mismatch')
        changed = [i for i, (x,y) in enumerate(zip(a['ids'], b['ids'])) if x != y]
        if changed != pair['changed_positions'] or len(changed) != 2 or pair['position_map'] != list(range(a['length'])):
            raise ValueError('pair changed-token correspondence')
        if a['ids'][:changed[0]] != b['ids'][:changed[0]]: raise ValueError('pair causal prefix mismatch')
        role = 'user' if pair['axis'] == 'E' else 'system'
        if any(a['token_roles'][i] != role for i in changed): raise ValueError('pair changed wrong role')
    interventions, batches = [], []
    def batch(group, phase, family=None, site=None, axis=None, task=None):
        for start in range(0, len(group), 8):
            batches.append(dict(id=f'pb-{len(batches):06d}', row_ids=[r['id'] for r in group[start:start+8]], phase=phase, family=family, site=site, axis=axis, task=task))
    batch(main, 'baseline')
    for family in FAMILIES:
        for site in SITES:
            for axis, task in AXES:
                group = [dict(id=p['id']+':'+family+':'+site, pair_id=p['id'], recipient_id=p['recipient_id'], donor_id=p['donor_id'], family=family, site=site, axis=axis, task=task) for p in pairs if (p['axis'],p['task']) == (axis,task)]
                interventions.extend(group); batch(group,'intervention',family,site,axis,task)
    slots = [r for r in old['calibration'] if r['family'] == 'S']
    if len(slots) != 8 or set(r['recipient_id'] for r in slots) & set(by_id): raise ValueError('disjoint eight calibration slots')
    calibration, cal_batches = [], []
    for mode in ('forced', 'natural'):
        for family in FAMILIES:
            for site in SITES:
                rows = [{**r, 'id':f'cp-cal:{mode}:{family}:{site}:slot{i}', 'family':family, 'site':site, 'position':positions[r['recipient_id']]} for i,r in enumerate(slots)]
                calibration.extend(rows)
                cal_batches.append(dict(id=f'cal-{mode}-{family}-{site}', row_ids=[r['id'] for r in rows], phase=mode, family=family, site=site, axis=None, task=None))
    intact = [{**r, 'id':f'cp-cal:natural:intact:slot{i}', 'family':None, 'site':None, 'position':positions[r['recipient_id']]} for i,r in enumerate(slots)]
    calibration.extend(intact)
    cal_batches.append(dict(id='cal-natural-intact',row_ids=[r['id'] for r in intact],phase='natural',family=None,site=None,axis=None,task=None))
    noop = [{**r, 'id':f'cp-cal:system-E:slot{i}', 'position':positions[r['recipient_id']]} for i,r in enumerate(slots) if r['axis']=='E']
    if [len(main),len(pairs),len(interventions),len(batches)] != [384,640,3840,528]: raise ValueError('complete position panel counts')
    limits = deepcopy(old['record_bounds']['limits'])
    limits.update(id_bytes=max(len(r['id'].encode()) for r in main+interventions+calibration+noop),max_rows=4224,max_controls=1072,max_capture_heads=32)
    return dict(schema='sdr-cue-positions-v1', main=main,pairs=pairs,fixtures=deepcopy(old['fixtures']),families={k:deepcopy(old['families'][k]) for k in FAMILIES},positions=positions,interventions=interventions,batches=batches,
        calibration=calibration,calibration_batches=cal_batches,calibration_pool=pool,calibration_noop=noop,
        batch_size=8,sequence_length=224,max_new_tokens=64,padding_id=0,eos=deepcopy(old['eos']),forced_token=1296,
        parent={'sha256':PARENT_SHA,'scientific_hash':PARENT_SCIENCE,'commit':PARENT_COMMIT},
        boundary_rule='Exact assistant marker; independent prefix encode; no crossing offsets; zero-offset special tokens assigned by matching token-index prefix. early=[0,b),tail=[b,n),full=[0,n); system=[0,user-header).',
        spec={'sha256':file_hash(spec_path),'text':Path(spec_path).read_text()},rubric=deepcopy(old['rubric']),
        numerical={'max_abs_error':1e-5,'main_baseline':['repeat','empty'],'main_patch':['patched_repeat'],'forced_each_step':['repeat','patched_repeat'],'forced_extra_steps':[0,63],'forced_extra':['empty','self','capture'],'exclude_readout':True},
        analysis={'categories':cc.CATEGORIES,'all_rows':True,'equal_fixture_weight':True,'denominators':{'E/report':256,'T/report':256,'T/retrieval':128},'contrasts':['early-alone','tail-alone','early-given-tail','tail-given-early','joint'],'no_inference':True},
        record_bounds={'limits':limits,'terminal_bytes':32*1024*1024,'attempt_bytes':16384,'generation_bytes_upper_bound':len(main+interventions)*(6*limits['text_bytes']*4+8192)})


def build_protocol(parent_path: Path, spec_path: Path, code_commit: str) -> dict:
    parent_path, spec_path = Path(parent_path).resolve(), Path(spec_path).resolve()
    if code_commit != 'UNCOMMITTED' and (re.fullmatch('[0-9a-f]{40}',code_commit) is None or code_commit == PARENT_COMMIT): raise ValueError('new source commit must differ from parent')
    if file_hash(parent_path) != PARENT_SHA or file_hash(spec_path) != SPEC_SHA: raise ValueError('immutable parent/spec bytes mismatch')
    parent = read_json(parent_path)
    if parent['scientific_hash'] != PARENT_SCIENCE or digest(parent['payload']) != PARENT_SCIENCE or parent['provenance']['code_commit'] != PARENT_COMMIT: raise ValueError('immutable parent identity')
    cc.verify_protocol(parent)
    tokenizer = n.load_tokenizer(parent['provenance']['cache'])
    payload = _payload(parent,spec_path,tokenizer)
    provenance = dict(parent_path=str(parent_path),parent_sha256=PARENT_SHA,parent_commit=PARENT_COMMIT,parent_sources=parent['provenance']['source_hashes'],spec_path=str(spec_path),code_commit=code_commit,source_hashes=source_hashes(),cache=parent['provenance']['cache'],cache_hashes=n.cache_hashes(parent['provenance']['cache']),software=n.software())
    return dict(payload=payload,scientific_hash=digest(payload),provenance=provenance,provenance_hash=digest(provenance))


def verify_protocol(protocol: dict) -> None:
    if set(protocol) != {'payload','scientific_hash','provenance','provenance_hash'} or digest(protocol['payload']) != protocol['scientific_hash'] or digest(protocol['provenance']) != protocol['provenance_hash']: raise ValueError('protocol hash/schema mismatch')
    v = protocol['provenance']
    expected = build_protocol(v['parent_path'],v['spec_path'],v['code_commit'])
    if expected != protocol: raise ValueError('literal frozen inputs/source/software/cache mismatch')


def position_mask(rows: list, site: str, device: str):
    import torch
    if site not in SITES+('system',): raise ValueError('frozen site required')
    if not 0 < len(rows) <= 8: raise ValueError('physical row count')
    mask = torch.zeros((8,224),dtype=torch.bool,device=device)
    for slot,row in enumerate(rows):
        boundary=row['position']; indices=boundary['indices'][site]
        if not indices or sorted(set(indices)) != indices or any(type(i) is not int or not 0 <= i < row['length'] for i in indices) or digest(indices) != boundary['hashes'][site]: raise ValueError('frozen nonempty positions/hash')
        mask[slot,indices]=True
    return mask


def pack_bank(capture, keys: list, rows: list, expected_mask) -> dict:
    import torch
    from component_analysis import hooks
    if expected_mask.shape != (8,224) or expected_mask.dtype != torch.bool: raise ValueError('explicit Boolean positions required')
    if not bool(expected_mask[:len(rows)].any(dim=1).all()): raise ValueError('empty position masks prohibited')
    if bool((expected_mask & ~cc.prefix_positions(rows,expected_mask.device)).any()): raise ValueError('dummy/padding/generated positions prohibited')
    result = {}
    for key in keys:
        key = tuple(key)
        if len(key) != 3 or key[0] != 'head' or key == hooks.READOUT_KEY: raise ValueError('only selected head outputs may be replaced')
        value = capture.outputs[key].detach().to(expected_mask.device).contiguous().clone()
        if value.shape != (8,224,128) or not bool(torch.isfinite(value).all()): raise ValueError('finite compact head bank geometry required')
        replacement = hooks.Replacement(value,expected_mask.clone())
        cc.checked_assignment(torch.full_like(value,-.125),replacement)
        result[key] = replacement
    if len(result) != len(keys): raise ValueError('duplicate bank key')
    return result


def _capture_receipt(bank, rows, site, label, step, history_lengths):
    return dict(bank=label,step=step,site=site,row_ids=[r['id'] for r in rows],position_ids=[r['position']['hashes'][site] for r in rows],indices=[r['position']['indices'][site] for r in rows],history_lengths=history_lengths,
        values=[dict(key=list(k),shape=list(v.value.shape),dtype=str(v.value.dtype),sha256=cc.tensor_sha(v.value),positions_sha256=cc.tensor_sha(v.positions)) for k,v in sorted(bank.items())])


def decode_batch(model, rows: list, protocol: dict, *, donor_rows=None, family_keys=(), site=None, stress=False, state=None) -> dict:
    """Fixed B8/L224 same-path kernel, with masks frozen before the first forward."""
    import torch
    from component_analysis import hooks
    from scripts.sdr_routing_pilot import capture_logits
    state = state if state is not None else {}
    p=protocol['payload']; device,_=hooks.device_and_dtype(model); keys=[tuple(k) for k in family_keys]; readout=[hooks.READOUT_KEY]
    ids,attention,_=n.make_batch(rows,batch_size=8,sequence_length=224,device=str(device))
    state.update(rows=[cc.generation(r,protocol['scientific_hash'],i,'attempted') for i,r in enumerate(rows)],controls=[],captures=[],timings={},forward_seconds=0.,packing_seconds=0.,elapsed_seconds=0.,error='')
    started=time.monotonic(); hf=hooks._hf(model); previous_cache=hf.config.use_cache
    expected=position_mask(rows,site,str(device)) if keys else None
    timer=cc.Timings(); frozen=[]
    def forward(capture_keys, replacements=None, *, input_ids=None, mask=None):
        n.check_deadline(protocol)
        for replacement,version,mask_version in frozen:
            if replacement.value._version!=version or replacement.positions._version!=mask_version or not torch.equal(replacement.positions,expected): raise ValueError('immutable frozen bank changed')
        if replacements:
            for key,value in replacements.items():
                if key==hooks.READOUT_KEY or not torch.equal(value.positions,expected) or bool((value.positions & ~attention.bool()).any()): raise ValueError('frozen mask scope changed')
        tick=time.monotonic()
        with torch.inference_mode():
            capture=hooks.capture_forward(model,ids if input_ids is None else input_ids,attention if mask is None else mask,components=capture_keys,replacements=replacements)
            logits=capture_logits(model,capture)
        if logits.dtype!=torch.float32 or logits.shape!=(8,p.get('vocab_size',128256)) or not bool(torch.isfinite(logits).all()): raise ValueError('finite full FP32 vocabulary required')
        if ids.is_cuda: torch.cuda.synchronize()
        elapsed=time.monotonic()-tick;state['forward_seconds']+=elapsed
        signature=digest({'capture':[list(k) for k in sorted(capture_keys)],'replace':[list(k) for k in sorted(replacements or {})],'mode':'plain' if replacements is None else 'replace' if replacements else 'empty','positions':site,'mask':cc.tensor_sha(expected) if expected is not None else None,'shape':[8,224],'dtype':str(logits.dtype)})
        timer.record(signature,elapsed)
        return capture,logits
    def bank(capture,source,label,step):
        tick=time.monotonic();result=pack_bank(capture,keys,rows,expected)
        state['captures'].append(_capture_receipt(result,source,site,label,step,[int(attention[i].sum()) for i in range(len(rows))]))
        state['packing_seconds']+=time.monotonic()-tick
        return result
    def checks(name,expected_logits,observed,step,active):
        for i in active: state['controls'].append(dict(row_id=rows[i]['id'],control=name,step=step,family=rows[i].get('family') or '',**cc.compare_full(expected_logits[i],observed[i])))
    try:
        hf.config.use_cache=False
        donor_bank=None
        if donor_rows is not None:
            if not keys or len(donor_rows)!=len(rows) or not torch.equal(position_mask(donor_rows,site,str(device)),expected): raise ValueError('donor position correspondence')
            di,dm,_=n.make_batch(donor_rows,batch_size=8,sequence_length=224,device=str(device))
            capture,_=forward(keys+readout,input_ids=di,mask=dm)
            donor_bank=bank(capture,donor_rows,'donor',-1); del capture
            frozen.extend((v,v.value._version,v.positions._version) for v in donor_bank.values())
        elif keys: raise ValueError('selected heads require natural donor rows')
        tokenizer=protocol.get('_tokenizer') or n.load_tokenizer(protocol['provenance']['cache'])
        for step in range(64):
            active=[i for i,r in enumerate(state['rows']) if stress or r['status']=='attempted']
            if not active: break
            if stress:
                _,intact=forward(readout); _,repeat=forward(readout);checks('repeat',intact,repeat,step,active)
                _,patched=forward(readout,donor_bank); _,repeat=forward(readout,donor_bank);checks('patched_repeat',patched,repeat,step,active)
                if step in (0,63):
                    _,empty=forward(readout,{});checks('empty',intact,empty,step,active)
                    capture,captured_logits=forward(keys+readout)
                    own=bank(capture,rows,'self-current',step); del capture
                    checks('capture',intact,captured_logits,step,active)
                    _,self_logits=forward(readout,own);checks('self',intact,self_logits,step,active);del own
                logits=patched
            else:
                _,logits=forward(readout,donor_bank)
                if donor_bank is not None:
                    _,repeat=forward(readout,donor_bank);checks('patched_repeat',logits,repeat,step,active)
                elif step==0:
                    _,repeat=forward(readout);checks('repeat',logits,repeat,step,active)
                    _,empty=forward(readout,{});checks('empty',logits,empty,step,active)
            for slot in active:
                row=state['rows'][slot];logical=int(attention[slot].sum())-1;token=1296 if stress else int(logits[slot].argmax())
                row['generated_ids'].append(token);row['logical_readouts'].append(logical)
                finish=('stress' if step==63 else 'error_missing') if stress else ('eos' if token in p.get('eos',cc.EOS) else 'capped' if step==63 else 'error_missing')
                row['finish']=finish
                if finish in ('stress','eos','capped'): row['status']='completed'
                else:
                    if logical+1>=224: raise ValueError('logical append overflow')
                    ids[slot,logical+1]=token;attention[slot,logical+1]=1
        for source,row in zip(rows,state['rows']):
            for raw in (False,True):
                text=tokenizer.decode(row['generated_ids'],skip_special_tokens=not raw,clean_up_tokenization_spaces=False)
                row['raw_continuation' if raw else 'continuation']=text
                row['raw_text' if raw else 'text']=source['stem']+text
        return state
    except BaseException as error:
        state['error']=cc._bounded_error(error)
        for row in state['rows']: row.update(status='error',finish='error_missing',error=state['error'])
        raise
    finally:
        hf.config.use_cache=previous_cache;state['timings']=timer.values;state['elapsed_seconds']=time.monotonic()-started


def system_noop(model, rows, donor_rows, protocol, keys):
    """Calibration-only E causal-prefix equality; no scientific rows are added."""
    import torch
    from component_analysis import hooks
    from scripts.sdr_routing_pilot import capture_logits
    device,_=hooks.device_and_dtype(model); mask=position_mask(rows,'system',str(device))
    if not torch.equal(mask,position_mask(donor_rows,'system',str(device))): raise ValueError('system mask correspondence')
    for r,d in zip(rows,donor_rows):
        indices=r['position']['indices']['system']
        if [r['ids'][i] for i in indices] != [d['ids'][i] for i in indices]: raise ValueError('E system prefix not identical')
    hf=hooks._hf(model);previous=hf.config.use_cache;hf.config.use_cache=False
    try:
        captures=[]
        for source in (rows,donor_rows):
            n.check_deadline(protocol);ids,attention,_=n.make_batch(source,batch_size=8,sequence_length=224,device=str(device))
            with torch.inference_mode(): capture=hooks.capture_forward(model,ids,attention,components=list(keys)+[hooks.READOUT_KEY])
            captures.append((capture,capture_logits(model,capture)))
        own=pack_bank(captures[0][0],list(keys),rows,mask);donor=pack_bank(captures[1][0],list(keys),rows,mask)
        for k in own:
            if not torch.equal(own[k].value[mask],donor[k].value[mask]): raise ValueError('E system selected activations differ')
        ids,attention,_=n.make_batch(rows,batch_size=8,sequence_length=224,device=str(device))
        with torch.inference_mode(): patched=hooks.capture_forward(model,ids,attention,components=[hooks.READOUT_KEY],replacements=donor)
        logits=capture_logits(model,patched)
        return {'passed':True,'site':'system','captures':[_capture_receipt(own,rows,'system','recipient',-1,[r['length'] for r in rows]),_capture_receipt(donor,donor_rows,'system','donor',-1,[r['length'] for r in rows])],'selected':[dict(key=list(k),recipient_sha256=cc.tensor_sha(own[k].value[mask]),donor_sha256=cc.tensor_sha(donor[k].value[mask])) for k in sorted(own)],'controls':[dict(row_id=r['id'],**cc.compare_full(captures[0][1][i],logits[i])) for i,r in enumerate(rows)]}
    finally: hf.config.use_cache=previous


def seal(payload): return {'payload':payload,'sha256':digest(payload)}


def unseal(record):
    if set(record)!={'payload','sha256'} or digest(record['payload'])!=record['sha256']: raise ValueError('immutable record hash/schema mismatch')
    return record['payload']


def publish(path, value, maximum=None):
    """Exclusive durable link commit with unique temporary files, safe after SIGKILL."""
    path=Path(path)
    if path.exists(): raise ValueError('occupied immutable journal path: '+str(path))
    tick=time.monotonic();data=encoded(value);serialization_seconds=time.monotonic()-tick
    if maximum is not None and len(data)>maximum: raise ValueError('record byte ceiling exceeded')
    temp=path.with_name(path.name+f'.{os.getpid()}.{time.time_ns()}.tmp');tick=time.monotonic()
    try:
        with temp.open('xb') as stream: stream.write(data);stream.flush();os.fsync(stream.fileno())
        try: os.link(temp,path)
        except FileExistsError: raise ValueError('occupied immutable journal path: '+str(path))
        fd=os.open(str(path.parent),os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        if temp.exists(): temp.unlink()
    return dict(serialization_seconds=serialization_seconds,write_seconds=time.monotonic()-tick,bytes=len(data))


@contextmanager
def run_lock(path, owner):
    """Only the held flock establishes ownership; metadata is retained evidence."""
    path=Path(path)
    with path.open('a+') as stream:
        try: fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: raise ValueError('run already held by another process')
        try:
            stream.seek(0);stream.truncate();stream.write(canonical(owner));stream.flush();os.fsync(stream.fileno())
            yield
        finally: fcntl.flock(stream,fcntl.LOCK_UN)


def initialize_run(protocol,path,binding):
    path=Path(path)
    if path.exists(): raise ValueError('fresh run directory required')
    path.mkdir(parents=True)
    for name in ('attempts','terminals','interruptions','invocations'): (path/name).mkdir()
    run=seal(dict(schema='position-run-v1',scientific_hash=protocol['scientific_hash'],provenance_hash=protocol['provenance_hash'],binding=binding,batches=[b['id'] for b in protocol['payload']['batches']]))
    publish(path/'run.json',run);publish(path/'protocol.json',protocol)
    return run


def _attempt_paths(path,batch_id): return sorted((Path(path)/'attempts').glob(batch_id+'.*.json'))


def record_interruption(path,batch_id,number,reason,evidence,partial=None):
    if reason not in ('deadline','preemption','numerical','provenance','failure'): raise ValueError('interruption class')
    attempt_path=Path(path)/'attempts'/f'{batch_id}.{number:04d}.json'
    attempt=read_json(attempt_path);v=unseal(attempt)
    if reason=='preemption':
        if set(evidence)!={'job_id','state','end_utc'} or evidence['state'] not in ('PREEMPTED','TIMEOUT') or evidence['job_id']!=v['allocation']['job_id']:
            raise ValueError('bound scheduler preemption evidence required')
        end=datetime.fromisoformat(evidence['end_utc'])
        if end.tzinfo is None or end.timestamp()>time.time(): raise ValueError('scheduler actual end must be past')
    record=seal(dict(batch_id=batch_id,number=number,attempt_hash=attempt['sha256'],reason=reason,evidence=evidence,partial=partial))
    publish(Path(path)/'interruptions'/f'{batch_id}.{number:04d}.json',record,32*1024*1024)
    return record


def begin_attempt(protocol,path,batch,binding,run_hash,invocation_id,allocation=None):
    invocation_path=Path(path)/'invocations'/(invocation_id+'.json')
    if not invocation_path.is_file(): raise ValueError('bound immutable invocation required')
    invocation=unseal(read_json(invocation_path))
    if invocation['id']!=invocation_id or invocation['run_hash']!=run_hash or invocation['binding']!=binding: raise ValueError('attempt invocation binding mismatch')
    allocation=allocation or invocation['allocation']
    if allocation!=invocation['allocation']: raise ValueError('attempt allocation differs from invocation')
    previous=_attempt_paths(path,batch['id']);number=len(previous)+1;supersedes=None;reason=None
    if previous:
        old=read_json(previous[-1]);v=unseal(old)
        interrupted=unseal(read_json(Path(path)/'interruptions'/f'{batch["id"]}.{v["number"]:04d}.json'))
        if interrupted['attempt_hash']!=old['sha256'] or interrupted['reason'] not in ('deadline','preemption'): raise ValueError('hard stop: ineligible prior attempt')
        supersedes=old['sha256'];reason=interrupted['reason']
    if (Path(path)/'terminals'/f'{batch["id"]}.json').exists(): raise ValueError('completed batch cannot be retried')
    payload=dict(schema='position-attempt-v1',batch_id=batch['id'],row_ids=batch['row_ids'],number=number,scientific_hash=protocol['scientific_hash'],provenance_hash=protocol['provenance_hash'],binding_hash=digest(binding),run_hash=run_hash,invocation_id=invocation_id,supersedes=supersedes,reason=reason,allocation=allocation or {'job_id':'CPU'},created_utc=datetime.now(timezone.utc).isoformat())
    result=seal(payload);publish(Path(path)/'attempts'/f'{batch["id"]}.{number:04d}.json',result,protocol['payload']['record_bounds']['attempt_bytes'])
    return result


def make_terminal(protocol,batch,state,attempt,binding,run_hash):
    number=attempt.get('number',attempt.get('payload',{}).get('number'))
    return seal(dict(schema='position-terminal-v1',batch_id=batch['id'],row_ids=batch['row_ids'],number=number,attempt_hash=attempt['sha256'],run_hash=run_hash,binding_hash=digest(binding),scientific_hash=protocol['scientific_hash'],provenance_hash=protocol['provenance_hash'],**{k:state[k] for k in ('rows','controls','captures','timings','error','elapsed_seconds','forward_seconds','packing_seconds')}))


def batch_inputs(protocol,batch):
    p=protocol['payload'];main={r['id']:r for r in p['main']};pool={r['id']:r for r in p['calibration_pool']}
    if batch['phase'] in ('forced','natural'):
        cal={r['id']:r for r in p['calibration']};rows=[deepcopy(cal[x]) for x in batch['row_ids']]
        donors=[{**pool[r['donor_id']],'position':p['positions'][r['donor_id']]} for r in rows] if batch['family'] else None
    elif batch['phase']=='baseline': rows=[{**main[x],'position':p['positions'][x]} for x in batch['row_ids']];donors=None
    else:
        interventions={r['id']:r for r in p['interventions']}
        rows=[{**main[interventions[x]['recipient_id']],**interventions[x],'position':p['positions'][interventions[x]['recipient_id']]} for x in batch['row_ids']]
        donors=[{**main[r['donor_id']],'position':p['positions'][r['donor_id']]} for r in rows]
    return rows,donors


TERMINAL_FIELDS={'schema','batch_id','row_ids','number','attempt_hash','run_hash','binding_hash','scientific_hash','provenance_hash','rows','controls','captures','timings','error','elapsed_seconds','forward_seconds','packing_seconds'}
ATTEMPT_FIELDS={'schema','batch_id','row_ids','number','scientific_hash','provenance_hash','binding_hash','run_hash','invocation_id','supersedes','reason','allocation','created_utc'}


def audit_batch(protocol: dict, batch: dict, terminal: dict) -> None:
    import torch
    v=unseal(terminal);p=protocol['payload']; bounds=p['record_bounds']
    if set(v)!=TERMINAL_FIELDS or v['schema']!='position-terminal-v1' or v['batch_id']!=batch['id'] or v['row_ids']!=batch['row_ids'] or v['scientific_hash']!=protocol['scientific_hash'] or v['provenance_hash']!=protocol['provenance_hash'] or v['error']:
        raise ValueError('terminal schema/batch/provenance/error mismatch')
    for k in ('attempt_hash','run_hash','binding_hash'): cc._hex(v[k])
    if type(v['number']) is not int or not 1<=v['number']<=9999: raise ValueError('attempt number')
    for k in ('elapsed_seconds','forward_seconds','packing_seconds'): cc._finite(v[k])
    if len(encoded(terminal))>bounds['terminal_bytes']: raise ValueError('terminal byte ceiling')
    cc._validate_timings(v['timings'])
    if [r['id'] for r in v['rows']]!=batch['row_ids']: raise ValueError('exact terminal row coverage/order')
    inputs,donors=batch_inputs(protocol,batch); expected=[]
    for slot,(source,row) in enumerate(zip(inputs,v['rows'])):
        cc.validate_generation(row,bounds)
        if row['protocol_hash']!=protocol['scientific_hash'] or row['physical_slot']!=slot or row['status']!='completed' or row['error']: raise ValueError('generation binding/status')
        count=len(row['generated_ids'])
        if count<1 or row['logical_readouts']!=list(range(source['length']-1,source['length']-1+count)): raise ValueError('logical readout sequence')
        if row['text']!=source['stem']+row['continuation'] or row['raw_text']!=source['stem']+row['raw_continuation']: raise ValueError('forced stem continuity')
        if batch['phase']=='forced':
            if row['finish']!='stress' or row['generated_ids']!=[1296]*64: raise ValueError('full-cap numerical stress required')
            expected.extend((source['id'],name,step) for step in range(64) for name in ('repeat','patched_repeat'))
            expected.extend((source['id'],name,step) for step in (0,63) for name in ('empty','self','capture'))
        else:
            if row['finish']=='eos':
                if row['generated_ids'][-1] not in p['eos'] or any(t in p['eos'] for t in row['generated_ids'][:-1]): raise ValueError('first EOS stop')
            elif row['finish']=='capped':
                if count!=64 or any(t in p['eos'] for t in row['generated_ids']): raise ValueError('complete capped outcome')
            else: raise ValueError('incomplete generation cannot be accepted')
            expected.extend((source['id'],name,step) for name,steps in ([('patched_repeat',range(count))] if batch['family'] else [('repeat',[0]),('empty',[0])]) for step in steps)
    expected_forwards=263 if batch['phase']=='forced' else (1+2*max(len(r['generated_ids']) for r in v['rows']) if batch['family'] else 2+max(len(r['generated_ids']) for r in v['rows']))
    if sum(t['count'] for t in v['timings'].values())!=expected_forwards: raise ValueError('exact physical forward coverage')
    observed=[]
    for c in v['controls']:
        if set(c)!=cc.CONTROL_FIELDS or type(c['step']) is not int or not 0<=c['step']<64 or c['family']!=(batch['family'] or '') or c['finite'] is not True or c['identical_greedy'] is not True or type(c['bitwise']) is not bool or c['tolerance']!=1e-5: raise ValueError('required numerical control schema/identity')
        cc._finite(c['max_abs_error'])
        if c['max_abs_error']>1e-5: raise ValueError('numerical hard stop')
        for k in ('expected_sha256','observed_sha256'): cc._hex(c[k])
        if c['bitwise'] and (c['max_abs_error']!=0 or c['expected_sha256']!=c['observed_sha256']): raise ValueError('inconsistent bitwise receipt')
        observed.append((c['row_id'],c['control'],c['step']))
    if Counter(observed)!=Counter(expected): raise ValueError('exact required control schedule')
    expected_banks=[]
    if batch['family']:
        expected_banks=[('donor',-1,donors)]
        if batch['phase']=='forced': expected_banks += [('self-current',step,inputs) for step in (0,63)]
    if len(v['captures'])!=len(expected_banks): raise ValueError('capture bank coverage')
    for receipt,(label,step,source) in zip(v['captures'],expected_banks):
        if set(receipt)!={'bank','step','site','row_ids','position_ids','indices','history_lengths','values'} or receipt['bank']!=label or receipt['step']!=step or receipt['site']!=batch['site'] or receipt['row_ids']!=[r['id'] for r in source]: raise ValueError('capture identity')
        site=batch['site'];positions=position_mask(inputs,site,'cpu')
        if receipt['position_ids']!=[r['position']['hashes'][site] for r in source] or receipt['indices']!=[r['position']['indices'][site] for r in source]: raise ValueError('capture exact frozen positions')
        if receipt['history_lengths']!=[r['length']+(step if label=='self-current' else 0) for r in inputs]: raise ValueError('current-history self provenance')
        expected_keys=sorted(p['families'][batch['family']]['heads'])
        if [v['key'] for v in receipt['values']]!=expected_keys: raise ValueError('capture family head membership')
        for value in receipt['values']:
            if set(value)!={'key','shape','dtype','sha256','positions_sha256'} or value['shape']!=[8,224,128] or value['dtype']!='torch.bfloat16' or value['positions_sha256']!=cc.tensor_sha(positions): raise ValueError('capture geometry/dtype/mask hash')
            cc._hex(value['sha256'])


def commit_terminal(protocol,path,batch,terminal):
    tick=time.monotonic();audit_batch(protocol,batch,terminal);audit_seconds=time.monotonic()-tick
    receipt=publish(Path(path)/'terminals'/f'{batch["id"]}.json',terminal,protocol['payload']['record_bounds']['terminal_bytes'])
    return {**receipt,'audit_seconds':audit_seconds}


def verify_completed_batches(protocol: dict, run_dir: Path, binding: dict) -> dict:
    path=Path(run_dir);run=read_json(path/'run.json');r=unseal(run)
    expected=dict(schema='position-run-v1',scientific_hash=protocol['scientific_hash'],provenance_hash=protocol['provenance_hash'],binding=binding,batches=[b['id'] for b in protocol['payload']['batches']])
    if r!=expected or read_json(path/'protocol.json')!=protocol: raise ValueError('resume run/source/hardware binding mismatch')
    batches={b['id']:b for b in protocol['payload']['batches']};accepted={};rows=[];attempts={};interruptions={};invocations={}
    for file in (path/'invocations').glob('*.json'):
        invocation=unseal(read_json(file))
        if set(invocation)!={'id','run_hash','binding','operations','allocation','accepted','remaining_ids','forecast','incomplete_attempts','wasted_attempts'} or invocation['id']!=file.stem or invocation['run_hash']!=run['sha256'] or invocation['binding']!=binding: raise ValueError('invocation provenance/schema hard stop')
        invocations[file.stem]=invocation
    for file in (path/'invocations').glob('*.failure'):
        failure=unseal(read_json(file))
        if failure.get('operational') is not True: raise ValueError('hard stop: prior failed invocation requires root investigation')
    for file in sorted((path/'attempts').glob('*.json')):
        doc=read_json(file);a=unseal(doc);bid=a.get('batch_id')
        if set(a)!=ATTEMPT_FIELDS or a['schema']!='position-attempt-v1' or bid not in batches or file.name!=f'{bid}.{a["number"]:04d}.json' or a['row_ids']!=batches[bid]['row_ids'] or a['run_hash']!=run['sha256'] or a['binding_hash']!=digest(binding) or a['scientific_hash']!=protocol['scientific_hash'] or a['provenance_hash']!=protocol['provenance_hash']: raise ValueError('attempt provenance/schema hard stop')
        if a['invocation_id'] not in invocations or a['allocation']!=invocations[a['invocation_id']]['allocation'] or bid not in invocations[a['invocation_id']]['remaining_ids']: raise ValueError('attempt invocation/remaining/allocation hard stop')
        group=attempts.setdefault(bid,[])
        if a['number']!=len(group)+1 or a['supersedes']!=(group[-1]['sha256'] if group else None): raise ValueError('attempt sequence hard stop')
        group.append(doc)
    for file in sorted((path/'interruptions').glob('*.json')):
        doc=read_json(file);v=unseal(doc);bid=v.get('batch_id');num=v.get('number')
        if set(v)!={'batch_id','number','attempt_hash','reason','evidence','partial'} or bid not in attempts or type(num) is not int or not 1<=num<=len(attempts[bid]) or file.name!=f'{bid}.{num:04d}.json' or v['attempt_hash']!=attempts[bid][num-1]['sha256']: raise ValueError('interruption provenance hard stop')
        if v['reason'] not in ('deadline','preemption'): raise ValueError('hard stop: prior numerical/provenance/failure')
        if v['reason']=='preemption':
            e=v['evidence'];a=attempts[bid][num-1]['payload']
            if set(e)!={'job_id','state','end_utc'} or e['job_id']!=a['allocation']['job_id'] or e['state'] not in ('TIMEOUT','PREEMPTED') or datetime.fromisoformat(e['end_utc']).tzinfo is None or datetime.fromisoformat(e['end_utc']).timestamp()>time.time(): raise ValueError('scheduler interruption binding')
        interruptions[bid,num]=v
    for file in sorted((path/'terminals').glob('*.json')):
        terminal=read_json(file);v=unseal(terminal);bid=v.get('batch_id')
        if bid not in batches or file.name!=bid+'.json' or bid in accepted: raise ValueError('foreign/duplicate terminal')
        audit_batch(protocol,batches[bid],terminal)
        if bid not in attempts or v['number']!=len(attempts[bid]) or v['attempt_hash']!=attempts[bid][-1]['sha256'] or v['binding_hash']!=digest(binding) or v['run_hash']!=run['sha256'] or (bid,v['number']) in interruptions: raise ValueError('terminal attempt/run binding')
        accepted[bid]=terminal['sha256'];rows.extend(v['rows'])
    for bid,group in attempts.items():
        for index,doc in enumerate(group,1):
            if index==1 and doc['payload']['reason'] is not None: raise ValueError('first attempt supersession reason must be absent')
            if index>1 and doc['payload']['reason']!=interruptions[bid,index-1]['reason']: raise ValueError('supersession reason mismatch')
            if bid in accepted and index==len(group): continue
            if (bid,index) not in interruptions: raise ValueError('explicit operational interruption evidence required before resume')
    order=[b['id'] for b in protocol['payload']['batches']]
    for invocation in invocations.values():
        snapshot=invocation['accepted']
        if any(accepted.get(bid)!=sha for bid,sha in snapshot.items()) or invocation['remaining_ids']!=[bid for bid in order if bid not in snapshot]: raise ValueError('invocation accepted-terminal/remaining binding')
    return {'run_hash':run['sha256'],'accepted':accepted,'remaining_ids':[bid for bid in order if bid not in accepted],'rows':rows,'incomplete_attempts':sum(len(v) for v in attempts.values())-len(accepted)}


def assemble(protocol: dict, run_dir: Path) -> list:
    run=unseal(read_json(Path(run_dir)/'run.json'));state=verify_completed_batches(protocol,run_dir,run['binding'])
    if state['remaining_ids']: raise ValueError('incomplete panel cannot be called complete')
    mapped={r['id']:r for r in state['rows']};planned=cc.planned_rows(protocol)
    if len(mapped)!=len(planned) or len(state['rows'])!=len(planned) or set(mapped)!={r['id'] for r in planned}: raise ValueError('exact planned row coverage required')
    return [mapped[r['id']] for r in planned]


def cell_key(batch): return 'intact' if batch['family'] is None else batch['family']+'/'+batch['site']


def forecast_remaining(protocol: dict, calibration: dict, remaining_ids: list, operations: dict) -> dict:
    cc.validate_operations(operations);p=protocol['payload'];batches={b['id']:b for b in p['batches']}
    if len(remaining_ids)!=len(set(remaining_ids)) or set(remaining_ids)-set(batches): raise ValueError('exact remaining batch identities')
    if calibration.get('status')!='completed' or calibration.get('numerical_pass') is not True or calibration.get('system_noop_passed') is not True or calibration.get('scientific_hash')!=protocol['scientific_hash'] or calibration.get('provenance_hash')!=protocol['provenance_hash']: raise ValueError('matching complete calibration required')
    needed={'intact'}|{f+'/'+s for f in FAMILIES for s in SITES}
    if set(calibration['natural'])!=needed: raise ValueError('all six natural arms plus intact required')
    counts=Counter(cell_key(batches[x]) for x in remaining_ids);measured=0.
    for key,count in counts.items():
        timing=calibration['natural'][key]
        for field in ('elapsed_seconds','publication_seconds','seal_seconds'): cc._finite(timing[field])
        measured+=count*(timing['elapsed_seconds']+timing['seal_seconds']+timing['publication_seconds'])
    fullcap=calibration['forced_max_seconds'];cc._finite(fullcap)
    if fullcap<=0: raise ValueError('measured forced-cap batch bound required')
    shutdown=operations['shutdown_buffer_seconds']+operations['safety_margin_seconds']
    safe=fullcap*1.5+shutdown
    buffers=sum(operations[k] for k in ('startup_buffer_seconds','premodel_headroom_seconds','shutdown_buffer_seconds','safety_margin_seconds'))+calibration['audit_seconds']*2
    expected=measured*1.5+buffers
    forward_budget=sum(66 if batches[x]['family'] is None else 129 for x in remaining_ids)
    return dict(method='observed natural per-cell physical-batch elapsed+publication; uncertainty50%; forced64 remains safe-start bound',remaining_batches=len(remaining_ids),remaining_rows=sum(len(batches[x]['row_ids']) for x in remaining_ids),cell_counts=dict(counts),cap=64,full_cap_forwards=forward_budget,measured_seconds=measured,uncertainty_multiplier=1.5,buffers_seconds=buffers,expected_seconds=expected,requested_seconds=operations['reserved_seconds'],safe_batch_seconds=safe,full_cap_ceiling_seconds=len(remaining_ids)*fullcap*1.5+buffers,all_remaining_fit=expected<=min(operations['reserved_seconds'],datetime.fromisoformat(operations['deadline_utc']).timestamp()-time.time()))


def batch_fits(forecast,operations): return time.time()+forecast['safe_batch_seconds'] < datetime.fromisoformat(operations['deadline_utc']).timestamp()


def preflight(protocol,operations,*,dry_run=False):
    verify_protocol(protocol);cc.validate_operations(operations)
    minimum=sum(operations[k] for k in ('startup_buffer_seconds','premodel_headroom_seconds','shutdown_buffer_seconds','safety_margin_seconds'))
    if min(operations['reserved_seconds'],datetime.fromisoformat(operations['deadline_utc']).timestamp()-time.time())<=minimum: raise ValueError('allocation cannot fit preflight/startup/shutdown buffers')
    if dry_run: return operations,None
    if protocol['provenance']['code_commit']=='UNCOMMITTED': raise ValueError('root committed source required')
    try: start,end=[float(os.environ['SDR_POS_ALLOCATION_'+k]) for k in ('START','END')]
    except (KeyError,ValueError): raise ValueError('actual Slurm allocation start/end from wrapper required')
    if not start < time.time() < end: raise ValueError('invalid actual allocation bounds')
    operations=cc.bind_allocation_operations(operations,allocation_start=start,allocation_end=end)
    if min(operations['reserved_seconds'],datetime.fromisoformat(operations['deadline_utc']).timestamp()-time.time())<=minimum: raise ValueError('actual allocation cannot fit preflight/startup/shutdown buffers')
    hardware=n.runtime_identity(operations)
    binding=dict(scientific_hash=protocol['scientific_hash'],provenance_hash=protocol['provenance_hash'],source_hashes=protocol['provenance']['source_hashes'],software=protocol['provenance']['software'],cache_hashes=protocol['provenance']['cache_hashes'],hardware=hardware,shape=[8,224],cap=64,precision='BF16 SDPA eval; use_cache=False; actual FP32 full vocabulary')
    return operations,binding


def peak_memory():
    import torch
    return torch.cuda.max_memory_allocated()


def _runtime(protocol,operations):
    return {**protocol,'_stop':{'requested':False},'_deadline':datetime.fromisoformat(operations['deadline_utc']).timestamp()-operations['shutdown_buffer_seconds'],'_tokenizer':n.load_tokenizer(protocol['provenance']['cache'])}


@contextmanager
def termination_handlers(runtime):
    previous={}
    for sig in (signal.SIGINT,signal.SIGTERM): previous[sig]=signal.signal(sig,lambda signum,frame:runtime['_stop'].update(requested=True))
    try: yield
    finally:
        for sig,handler in previous.items(): signal.signal(sig,handler)


def _allocation(operations):
    return dict(job_id=os.environ.get('SLURM_JOB_ID','CPU'),start_utc=operations.get('allocation_start_utc'),end_utc=operations.get('allocation_end_utc'),wrapper_entry=os.environ.get('SDR_POS_WRAPPER_ENTRY'),device_uuid=_device_uuid(),node=os.environ.get('SLURMD_NODENAME'))


def _device_uuid():
    import torch
    return str(getattr(torch.cuda.get_device_properties(0),'uuid','unavailable')) if torch.cuda.is_available() else 'CPU'


def calibrate(protocol: dict, operations: dict, output: Path, *, dry_run=False) -> dict:
    entered=time.monotonic();operations,binding=preflight(protocol,operations,dry_run=dry_run)
    if dry_run:
        if Path(output).exists(): raise ValueError('fresh calibration path required')
        return dict(status='cpu_dry_run',phase='calibration',batches=13,forced_arms=6,natural_arms=7,numerical_pass=False,mutates_run=False)
    output=Path(output)
    if output.exists(): raise ValueError('fresh calibration path required')
    output.mkdir(parents=True)
    for name in ('attempts','terminals','measurements'): (output/name).mkdir()
    publish(output/'protocol.json',protocol)
    metadata=seal({'binding':binding,'operations':operations,'allocation':_allocation(operations)})
    publish(output/'metadata.json',metadata)
    runtime=_runtime(protocol,operations);hf=None;previous_cache=None;natural={};forced=[];hashes={};active=None;state={}
    receipt=dict(status='initializing',numerical_pass=False,scientific_hash=protocol['scientific_hash'],provenance_hash=protocol['provenance_hash'],binding=binding,natural=natural,forced_max_seconds=0.,audit_seconds=0.,startup_seconds=0.,premodel_seconds=time.monotonic()-entered,peak_memory_bytes=0,terminal_hashes=hashes,system_noop_passed=False)
    with run_lock(output/'run.lock',metadata),termination_handlers(runtime):
        try:
            n.check_deadline(runtime);tick=time.monotonic();model,hf=cue._load_model(protocol);receipt['startup_seconds']=time.monotonic()-tick
            previous_cache=hf.config.use_cache;hf.config.use_cache=False
            runtime['payload']={**protocol['payload'],'vocab_size':int(hf.config.vocab_size)}
            for batch in protocol['payload']['calibration_batches']:
                active=batch;state={};n.check_deadline(runtime)
                attempt=seal(dict(batch_id=batch['id'],row_ids=batch['row_ids'],number=1,scientific_hash=protocol['scientific_hash'],provenance_hash=protocol['provenance_hash'],binding_hash=digest(binding),run_hash=metadata['sha256'],allocation=_allocation(operations)))
                publish(output/'attempts'/f'{batch["id"]}.json',attempt)
                rows,donors=batch_inputs(protocol,batch);keys=protocol['payload']['families'][batch['family']]['heads'] if batch['family'] else []
                state=decode_batch(model,rows,runtime,donor_rows=donors,family_keys=keys,site=batch['site'],stress=batch['phase']=='forced',state=state)
                tick=time.monotonic();terminal=make_terminal(protocol,batch,state,attempt,binding,metadata['sha256']);seal_seconds=time.monotonic()-tick
                tick=time.monotonic();io=commit_terminal(protocol,output,batch,terminal)
                publication=time.monotonic()-tick;hashes[batch['id']]=terminal['sha256']
                elapsed=state['elapsed_seconds']+seal_seconds+publication
                publish(output/'measurements'/f'{batch["id"]}.json',seal(dict(terminal_hash=terminal['sha256'],elapsed_seconds=state['elapsed_seconds'],publication_seconds=publication,seal_seconds=seal_seconds,serialization_seconds=seal_seconds+io['serialization_seconds'],write_seconds=io['write_seconds'],audit_seconds=io['audit_seconds'],forward_seconds=state['forward_seconds'],packing_seconds=state['packing_seconds'])))
                if batch['phase']=='forced': forced.append(elapsed)
                else: natural[cell_key(batch)]=dict(elapsed_seconds=state['elapsed_seconds'],publication_seconds=publication,seal_seconds=seal_seconds,serialization_seconds=seal_seconds+io['serialization_seconds'],write_seconds=io['write_seconds'],audit_seconds=io['audit_seconds'],forwards=sum(v['count'] for v in state['timings'].values()),lengths=[len(r['generated_ids']) for r in state['rows']],packing_seconds=state['packing_seconds'],forward_seconds=state['forward_seconds'])
                active=None
            p=protocol['payload'];pool={r['id']:r for r in p['calibration_pool']};noop_rows=p['calibration_noop'];donors=[{**pool[r['donor_id']],'position':p['positions'][r['donor_id']]} for r in noop_rows]
            noops={family:system_noop(model,noop_rows,donors,runtime,p['families'][family]['heads']) for family in FAMILIES}
            audit_system_noops(protocol,noops)
            publish(output/'system-noop.json',seal(noops));receipt['system_noop_passed']=all(v['passed'] is True for v in noops.values())
            receipt.update(status='completed',numerical_pass=True,forced_max_seconds=max(forced),peak_memory_bytes=peak_memory())
            tick=time.monotonic()
            for batch in p['calibration_batches']: audit_batch(protocol,batch,read_json(output/'terminals'/f'{batch["id"]}.json'))
            receipt['audit_seconds']=time.monotonic()-tick
            publish(output/'calibration.json',seal(receipt));validate_calibration(protocol,output,binding)
            return receipt
        except BaseException as error:
            publish(output/'failure.json',seal({'error':cc._bounded_error(error),'batch_id':active['id'] if active else None,'state':state,'operational':isinstance(error,TimeoutError)}),32*1024*1024)
            raise
        finally:
            if hf is not None and previous_cache is not None: hf.config.use_cache=previous_cache


def validate_calibration(protocol,directory,binding):
    directory=Path(directory);doc=read_json(directory/'calibration.json');receipt=unseal(doc)
    cc._keys(receipt,{'status','numerical_pass','scientific_hash','provenance_hash','binding','natural','forced_max_seconds','audit_seconds','startup_seconds','premodel_seconds','peak_memory_bytes','terminal_hashes','system_noop_passed'})
    if receipt['status']!='completed' or receipt['numerical_pass'] is not True or receipt['binding']!=binding or receipt['scientific_hash']!=protocol['scientific_hash'] or receipt['provenance_hash']!=protocol['provenance_hash'] or read_json(directory/'protocol.json')!=protocol: raise ValueError('calibration binding/completion mismatch')
    metadata_doc=read_json(directory/'metadata.json');metadata=unseal(metadata_doc);cc._keys(metadata,{'binding','operations','allocation'})
    if metadata['binding']!=binding or (directory/'failure.json').exists(): raise ValueError('calibration metadata/failure hard stop')
    batches=protocol['payload']['calibration_batches'];expected={b['id'] for b in batches}
    if set(receipt['terminal_hashes'])!=expected or {f.stem for f in (directory/'terminals').glob('*.json')}!=expected or len(batches)!=13: raise ValueError('exact calibration terminal schedule')
    forced_bounds=[]
    for batch in batches:
        terminal=read_json(directory/'terminals'/f'{batch["id"]}.json');audit_batch(protocol,batch,terminal)
        attempt_doc=read_json(directory/'attempts'/f'{batch["id"]}.json');attempt=unseal(attempt_doc);t=terminal['payload']
        cc._keys(attempt,{'batch_id','row_ids','number','scientific_hash','provenance_hash','binding_hash','run_hash','allocation'})
        if attempt['batch_id']!=batch['id'] or attempt['number']!=1 or attempt['run_hash']!=metadata_doc['sha256'] or attempt['allocation']!=metadata['allocation']: raise ValueError('calibration attempt identity/allocation')
        if terminal['sha256']!=receipt['terminal_hashes'][batch['id']] or t['binding_hash']!=digest(binding) or t['run_hash']!=metadata_doc['sha256'] or t['attempt_hash']!=attempt_doc['sha256'] or attempt['row_ids']!=batch['row_ids'] or attempt['binding_hash']!=digest(binding) or attempt['scientific_hash']!=protocol['scientific_hash'] or attempt['provenance_hash']!=protocol['provenance_hash']: raise ValueError('calibration terminal/attempt/hash mismatch')
        measurement=unseal(read_json(directory/'measurements'/f'{batch["id"]}.json'))
        if set(measurement)!={'terminal_hash','elapsed_seconds','publication_seconds','seal_seconds','serialization_seconds','write_seconds','audit_seconds','forward_seconds','packing_seconds'} or measurement['terminal_hash']!=terminal['sha256'] or any(measurement[k]!=t[k] for k in ('elapsed_seconds','forward_seconds','packing_seconds')): raise ValueError('calibration measurement/terminal binding')
        for key in ('publication_seconds','seal_seconds','serialization_seconds','write_seconds','audit_seconds'): cc._finite(measurement[key])
        if batch['phase']=='forced': forced_bounds.append(measurement['elapsed_seconds']+measurement['seal_seconds']+measurement['publication_seconds'])
        count=sum(v['count'] for v in t['timings'].values())
        if batch['phase']=='forced' and count!=263: raise ValueError('exact forced-cap numerical forwards')
        if batch['phase']=='natural':
            natural=receipt['natural'][cell_key(batch)]
            cc._keys(natural,{'elapsed_seconds','publication_seconds','seal_seconds','serialization_seconds','write_seconds','audit_seconds','forwards','lengths','packing_seconds','forward_seconds'})
            if natural['lengths']!=[len(r['generated_ids']) for r in t['rows']] or natural['elapsed_seconds']!=t['elapsed_seconds'] or natural['forwards']!=count or any(natural[k]!=measurement[k] for k in ('publication_seconds','seal_seconds','serialization_seconds','write_seconds','audit_seconds')) or natural['packing_seconds']!=measurement['packing_seconds'] or natural['forward_seconds']!=measurement['forward_seconds']: raise ValueError('natural timing/row binding')
    if receipt['forced_max_seconds']!=max(forced_bounds): raise ValueError('measured forced-cap bound drift')
    for k in ('audit_seconds','startup_seconds','premodel_seconds'): cc._finite(receipt[k])
    if set(receipt['natural'])!={'intact'}|{f+'/'+s for f in FAMILIES for s in SITES}: raise ValueError('exact natural calibration arm coverage')
    noops=unseal(read_json(directory/'system-noop.json'));audit_system_noops(protocol,noops)
    if set(noops)!=set(FAMILIES) or any(v.get('passed') is not True for v in noops.values()) or receipt['system_noop_passed'] is not True: raise ValueError('calibration E system no-op required')
    return receipt


def _finish_main_invocation(protocol,output,verified,invocation,invocation_id,peak_memory_bytes):
    status='stopped' if verified['remaining_ids'] else 'completed'
    if status=='completed':
        assembly=assemble(protocol,output);path=output/'generations.json'
        if path.exists():
            if encoded(read_json(path))!=encoded(assembly): raise ValueError('existing generation assembly conflicts with verified terminal rows')
        else: publish(path,assembly,protocol['payload']['record_bounds']['generation_bytes_upper_bound'])
    receipt=dict(status=status,accepted=verified['accepted'],remaining_ids=verified['remaining_ids'],numerical_pass=status=='completed',invocation_hash=invocation['sha256'],peak_memory_bytes=peak_memory_bytes)
    publish(output/'invocations'/f'{invocation_id}.result',seal(receipt))
    return receipt


def run_main(protocol: dict, calibration_dir: Path, operations: dict, output: Path, *, resume=False, dry_run=False) -> dict:
    operations,binding=preflight(protocol,operations,dry_run=dry_run);output=Path(output)
    if dry_run:
        if resume:
            if not output.is_dir(): raise ValueError('resume requires existing run directory')
            frozen_binding=unseal(read_json(output/'run.json'))['binding']
            verified=verify_completed_batches(protocol,output,frozen_binding)
        else:
            if output.exists(): raise ValueError('fresh main path required')
            verified={'accepted':{},'remaining_ids':[b['id'] for b in protocol['payload']['batches']]}
        if calibration_dir is not None and (Path(calibration_dir)/'calibration.json').exists():
            c=unseal(read_json(Path(calibration_dir)/'calibration.json'));validate_calibration(protocol,calibration_dir,c['binding']);forecast_remaining(protocol,c,verified['remaining_ids'],operations)
        return dict(status='cpu_dry_run',phase='main',resume=resume,accepted=verified['accepted'],remaining_ids=verified['remaining_ids'],numerical_pass=False,mutates_run=False)
    if calibration_dir is None: raise ValueError('fresh matching calibration required')
    calibration=validate_calibration(protocol,calibration_dir,binding)
    if calibration['peak_memory_bytes']>=binding['hardware']['memory']: raise ValueError('calibrated memory exceeds device')
    forecast=forecast_remaining(protocol,calibration,[b['id'] for b in protocol['payload']['batches']],operations)
    if not batch_fits(forecast,operations): raise ValueError('measured full-cap batch plus shutdown does not fit before model load')
    if resume:
        if not output.is_dir(): raise ValueError('resume requires existing run')
    else: initialize_run(protocol,output,binding)
    owner={'pid':os.getpid(),'job_id':os.environ.get('SLURM_JOB_ID','CPU'),'entered_utc':datetime.now(timezone.utc).isoformat()}
    with run_lock(output/'run.lock',owner):
        verified=verify_completed_batches(protocol,output,binding)
        forecast=forecast_remaining(protocol,calibration,verified['remaining_ids'],operations)
        invocation_id=f'inv-{len(list((output/"invocations").glob("*.json"))):04d}'
        invocation=seal(dict(id=invocation_id,run_hash=verified['run_hash'],binding=binding,operations=operations,allocation=_allocation(operations),accepted=verified['accepted'],remaining_ids=verified['remaining_ids'],forecast=forecast,incomplete_attempts=verified['incomplete_attempts'],wasted_attempts=[dict(attempt_hash=v['attempt_hash'],reason=v['reason'],observed_decode_seconds=(v['partial'] or {}).get('elapsed_seconds'),evidence=v['evidence']) for v in (unseal(read_json(f)) for f in sorted((output/'interruptions').glob('*.json')))]))
        publish(output/'invocations'/f'{invocation_id}.json',invocation)
        if not verified['remaining_ids']:
            return _finish_main_invocation(protocol,output,verified,invocation,invocation_id,0)
        runtime=_runtime(protocol,operations);hf=None;previous_cache=None;active=None;attempt=None;state={}
        with termination_handlers(runtime):
            try:
                if not batch_fits(forecast,operations): raise TimeoutError('batch no longer fits after preflight')
                n.check_deadline(runtime);model,hf=cue._load_model(protocol);previous_cache=hf.config.use_cache;hf.config.use_cache=False
                runtime['payload']={**protocol['payload'],'vocab_size':int(hf.config.vocab_size)}
                batches={b['id']:b for b in protocol['payload']['batches']}
                for identifier in verified['remaining_ids']:
                    if runtime['_stop']['requested'] or not batch_fits(forecast,operations): break
                    active=batches[identifier];state={}
                    attempt=begin_attempt(protocol,output,active,binding,verified['run_hash'],invocation_id,_allocation(operations))
                    rows,donors=batch_inputs(protocol,active);keys=protocol['payload']['families'][active['family']]['heads'] if active['family'] else []
                    state=decode_batch(model,rows,runtime,donor_rows=donors,family_keys=keys,site=active['site'],state=state)
                    terminal=make_terminal(protocol,active,state,attempt,binding,verified['run_hash']);commit_terminal(protocol,output,active,terminal)
                    active=None;attempt=None
                verified=verify_completed_batches(protocol,output,binding)
                return _finish_main_invocation(protocol,output,verified,invocation,invocation_id,peak_memory())
            except BaseException as error:
                if active is not None and attempt is not None:
                    record_interruption(output,active['id'],attempt['payload']['number'],'deadline' if isinstance(error,TimeoutError) else 'numerical' if isinstance(error,ValueError) else 'failure',{'error':cc._bounded_error(error),'allocation':_allocation(operations)},state)
                publish(output/'invocations'/f'{invocation_id}.failure',seal({'error':cc._bounded_error(error),'operational':isinstance(error,TimeoutError),'partial':state}),32*1024*1024)
                if isinstance(error,TimeoutError): return {'status':'stopped','numerical_pass':False,'error':cc._bounded_error(error)}
                raise
            finally:
                if hf is not None and previous_cache is not None: hf.config.use_cache=previous_cache


def export_views(protocol: dict, generations: list) -> list:
    return cc.export_blind_views(protocol,generations)


def join_annotations(protocol: dict, generations: list, annotation_paths: list) -> dict:
    return cc.join_annotations(protocol,generations,annotation_paths)


def _indicators(label,recipient,donor):
    values=cc.indicators(label,recipient,donor)
    values.update({category:int(cc.category(label)==category) for category in cc.CATEGORIES})
    return values


def _factorial(cells,key):
    b,e,t,f=[cells[k][key] for k in ('base','early','tail','full')]
    return dict(base=b,early=e,tail=t,full=f,**{'early-alone':e-b,'tail-alone':t-b,'early-given-tail':f-t,'tail-given-early':f-e,'joint':f-e-t+b})


def analyze_panel(protocol: dict, joined: dict, *, parent_reference=None) -> dict:
    p=protocol['payload'];planned=cc.planned_rows(protocol)
    if joined.get('protocol_hash')!=protocol['scientific_hash'] or joined.get('rubric_sha256')!=cue.BRIEF_SHA: raise ValueError('joined protocol/rubric mismatch')
    labels={r['id']:r for r in joined['rows']}
    if len(labels)!=len(joined['rows']) or set(labels)!={r['id'] for r in planned}: raise ValueError('exact planned analysis coverage; calibration excluded')
    for label in labels.values(): cue._label(label)
    main={r['id']:r for r in p['main']};pairs={r['id']:r for r in p['pairs']};items=[];lookup={}
    for arm in p['interventions']:
        pair=pairs[arm['pair_id']];recipient,donor=[main[pair[x+'_id']] for x in ('recipient','donor')]
        f=recipient['factors'];item=dict(id=arm['id'],pair_id=pair['id'],family=arm['family'],site=arm['site'],axis=pair['axis'],task=pair['task'],direction=f['example_order'] if pair['axis']=='E' else f['truth'],recipient=recipient,donor=donor,recipient_label=labels[recipient['id']],donor_label=labels[donor['id']],patch_label=labels[arm['id']])
        for endpoint in ('recipient','donor','patch'): item[endpoint+'_indicators']=_indicators(item[endpoint+'_label'],recipient,donor)
        key=(arm['site'],arm['family'],pair['id'])
        if key in lookup: raise ValueError('duplicate site/family/pair')
        lookup[key]=item;items.append(item)
    if set(lookup)!={(s,f,q['id']) for s in SITES for f in FAMILIES for q in p['pairs']}: raise ValueError('complete complementary panel required')
    inventory={};matched={s:{} for s in SITES};factorial={}
    for family in FAMILIES:
        inventory[family]={}
        for site in SITES:
            inventory[family][site]={}
            for axis,task in AXES:
                selected=[x for x in items if (x['family'],x['site'],x['axis'],x['task'])==(family,site,axis,task)]
                if len(selected)!=p['analysis']['denominators'][axis+'/'+task]: raise ValueError('all-row arm denominator')
                inventory[family][site][axis+'/'+task]={tag:cc._summary(group) for tag,group in cc._strata(selected,p['fixtures'][:8]).items()}
    contrasts=p['analysis']['contrasts']
    for axis,task in AXES:
        name=axis+'/'+task
        reference=[x for x in items if (x['family'],x['site'],x['axis'],x['task'])==('S','full',axis,task)]
        factorial[name]={}
        for tag,group in cc._strata(reference,p['fixtures'][:8]).items():
            result={};keys=sorted({k for x in group for k in x['patch_indicators']})
            for key in keys:
                values={}
                for family in FAMILIES:
                    cells={s:{key:cc._mean_by_fixture(group,lambda x,s=s,fa=family,k=key:lookup[s,fa,x['pair_id']]['patch_indicators'][k])} for s in SITES}
                    cells['base']={key:cc._mean_by_fixture(group,lambda x,k=key:x['recipient_indicators'][k])}
                    values[family]=_factorial(cells,key)
                values['difference']={contrast:values['S'][contrast]-values['C_S'][contrast] for contrast in contrasts}
                result[key]=values
            factorial[name][tag]={'n':len(group),'fixtures':len({x['recipient']['fixture_id'] for x in group}),'indicators':result}
        for site in SITES:
            matched[site][name]={}
            for tag in inventory['S'][site][name]:
                target=inventory['S'][site][name][tag]['indicators'];outside=inventory['C_S'][site][name][tag]['indicators']
                matched[site][name][tag]={k:dict(target_delta=v['delta'],outside_delta=outside[k]['delta'],difference=v['delta']-outside[k]['delta']) for k,v in target.items()}
    audit=[]
    for item in items:
        r=item['recipient'];position=p['positions'][r['id']];site=item['site']
        row={k:item[k] for k in ('id','pair_id','family','site','axis','task','direction')}
        row.update(fixture_id=r['fixture_id'],template=r['template'],factors=r['factors'],recipient_id=r['id'],donor_id=item['donor']['id'],position_hash=position['hashes'][site],position_indices=position['indices'][site],indicators={e:item[e+'_indicators'] for e in ('recipient','donor','patch')},delta={k:v-item['recipient_indicators'][k] for k,v in item['patch_indicators'].items()})
        for endpoint in ('recipient','donor','patch'):
            label=item[endpoint+'_label']
            for name,value in (('category',cc.category(label)),('view_id',label['view_id']),('finish',label['finish'])): row[endpoint+'_'+name]=value
        audit.append(row)
    result=dict(protocol_hash=protocol['scientific_hash'],planned_baselines=len(p['main']),planned_interventions=len(items),row_audit=audit,inventory=inventory,factorial=factorial,matched_outside=matched,
        natural={'example_report':cc._natural_pairs(p['main'],labels,'example_order','report'),'truth_report':cc._natural_pairs(p['main'],labels,'truth','report'),'truth_retrieval':cc._natural_pairs(p['main'],labels,'truth','retrieval')},
        caveats=['Query/head-output coordinates, not attention source/key/value positions.','Conditional replacement effects do not identify natural mediation, intent, deception or encoding preference.','Tail-alone sufficiency does not establish upstream irrelevance; early effects permit propagated influence.','Joint contrasts can reflect overwrite and readout nonlinearity.','E/T differ in location, amplitude and intact responsiveness; raw amplitudes cannot rank encoding.','One fixed layer/count comparator does not form a general null or match activation importance.','All residuals and capped/error outcomes remain in fixed denominators.','Only the reused eight-fixture neutral scaffold; no OOD or pressure inference.'])
    if parent_reference is not None:
        if parent_reference.get('protocol_hash')!=PARENT_SCIENCE or parent_reference.get('rubric_sha256')!=cue.BRIEF_SHA or digest(parent_reference)!='8970633e8d63a3ba063196feec3e1c26b09e2fd2a21ed27c64a10a88be5bce2f': raise ValueError('immutable descriptive parent reference mismatch')
        old={r['id']:r for r in parent_reference['rows']}
        if len(old)!=9344 or len(parent_reference['rows'])!=9344: raise ValueError('complete archived parent reference')
        rows=[]
        for row in p['main']+[a for a in p['interventions'] if a['site']=='full']:
            identifier=row['id'];old_id=identifier[:-5] if row.get('site')=='full' else identifier
            fresh,prior=labels[identifier],old[old_id]
            rows.append(dict(id=identifier,parent_id=old_id,fresh_category=cc.category(fresh),parent_category=cc.category(prior),same_category=cc.category(fresh)==cc.category(prior),same_format=fresh['format_ok']==prior['format_ok'],same_finish=fresh['finish']==prior['finish'],same_text=fresh['text']==prior['text'],same_raw_text=fresh['raw_text']==prior['raw_text']))
        result['parent_reproducibility']=dict(descriptive_only=True,parent_hash=digest(parent_reference),rows=rows,counts={key:sum(row[key] for row in rows) for key in ('same_category','same_format','same_finish','same_text','same_raw_text')})
    return result


def reconstruct(protocol,journal):
    path=Path(journal);run=unseal(read_json(path/'run.json'));batches={b['id']:b for b in protocol['payload']['batches']};rows=[];accepted={}
    if read_json(path/'protocol.json')!=protocol or run['scientific_hash']!=protocol['scientific_hash'] or run['provenance_hash']!=protocol['provenance_hash']: raise ValueError('reconstruction provenance mismatch')
    for file in sorted((path/'terminals').glob('*.json')):
        terminal=read_json(file);v=unseal(terminal);bid=v['batch_id']
        if bid not in batches or file.stem!=bid: raise ValueError('foreign terminal')
        audit_batch(protocol,batches[bid],terminal)
        if v['binding_hash']!=digest(run['binding']): raise ValueError('reconstruction terminal binding')
        attempt=read_json(path/'attempts'/f'{bid}.{v["number"]:04d}.json')
        if v['attempt_hash']!=attempt['sha256']: raise ValueError('terminal attempt binding')
        unseal(attempt);accepted[bid]=terminal['sha256'];rows.extend(v['rows'])
    complete=len(accepted)==len(batches)
    if complete: rows=assemble(protocol,path)
    return dict(status='completed' if complete else 'partial',complete=complete,accepted=accepted,remaining_ids=[b for b in batches if b not in accepted],rows=rows,incomplete_attempt_files=[f.name for f in (path/'attempts').glob('*.json') if unseal(read_json(f))['batch_id'] not in accepted])


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='mode',required=True)
    freeze=sub.add_parser('freeze')
    for key in ('parent','spec','output'): freeze.add_argument('--'+key,type=Path,required=True)
    freeze.add_argument('--code-commit',required=True)
    for mode in ('verify','calibration','forecast','main','reconstruct','export','join','analyze'):
        cmd=sub.add_parser(mode);cmd.add_argument('--protocol',type=Path,required=True)
        if mode!='verify': cmd.add_argument('--output',type=Path,required=True)
        if mode in ('calibration','forecast','main'): cmd.add_argument('--operations',type=Path,required=True)
        if mode in ('main','forecast'): cmd.add_argument('--calibration',type=Path,required=True)
        if mode=='forecast': cmd.add_argument('--run-dir',type=Path,required=True)
        if mode in ('main','calibration'): cmd.add_argument('--dry-run',action='store_true')
        if mode=='main': cmd.add_argument('--resume',action='store_true')
        if mode=='reconstruct': cmd.add_argument('--journal',type=Path,required=True)
        if mode in ('export','join'): cmd.add_argument('--generations',type=Path,required=True)
        if mode=='join': cmd.add_argument('--annotations',type=Path,nargs='+',required=True)
        if mode=='analyze':
            cmd.add_argument('--joined',type=Path,required=True);cmd.add_argument('--parent-reference',type=Path)
    args=parser.parse_args(argv)
    if args.mode=='freeze':
        protocol=build_protocol(args.parent,args.spec,args.code_commit)
        if args.output.exists(): raise ValueError('fresh freeze output required')
        args.output.mkdir(parents=True);publish(args.output/'protocol.json',protocol)
        publish(args.output/'freeze-audit.json',dict(status='CPU_FROZEN_NOT_RELEASED',scientific_hash=protocol['scientific_hash'],provenance_hash=protocol['provenance_hash'],counts={k:len(protocol['payload'][k]) for k in ('main','pairs','interventions','batches','calibration','calibration_batches')},source_hashes=protocol['provenance']['source_hashes']))
        print(canonical(dict(status='CPU_FROZEN_NOT_RELEASED',scientific_hash=protocol['scientific_hash'],provenance_hash=protocol['provenance_hash'])));return
    protocol=read_json(args.protocol)
    if args.mode in ('calibration','main'):
        if args.mode=='calibration': result=calibrate(protocol,read_json(args.operations),args.output,dry_run=args.dry_run)
        else: result=run_main(protocol,args.calibration,read_json(args.operations),args.output,resume=args.resume,dry_run=args.dry_run)
        print(canonical(result));return
    verify_protocol(protocol)
    if args.mode=='verify': print('CPU protocol verified; GPU release pending');return
    if args.output.exists(): raise ValueError('occupied output')
    if args.mode=='forecast':
        doc=unseal(read_json(args.calibration/'calibration.json'));cal=validate_calibration(protocol,args.calibration,doc['binding'])
        remaining=verify_completed_batches(protocol,args.run_dir,doc['binding'])['remaining_ids'] if args.run_dir.exists() else [b['id'] for b in protocol['payload']['batches']]
        result=forecast_remaining(protocol,cal,remaining,read_json(args.operations))
    elif args.mode=='reconstruct': result=reconstruct(protocol,args.journal)
    elif args.mode=='export': result=export_views(protocol,read_json(args.generations))
    elif args.mode=='join': result=join_annotations(protocol,read_json(args.generations),args.annotations)
    else: result=analyze_panel(protocol,read_json(args.joined),parent_reference=read_json(args.parent_reference) if args.parent_reference else None)
    publish(args.output,result)


def audit_system_noops(protocol,noops):
    p=protocol['payload'];rows=p['calibration_noop'];pool={r['id']:r for r in p['calibration_pool']}
    donors=[{**pool[r['donor_id']],'position':p['positions'][r['donor_id']]} for r in rows]
    if set(noops)!=set(FAMILIES): raise ValueError('complete causal-null families')
    expected_fields={'passed','site','captures','selected','controls'}
    for family,receipt in noops.items():
        if set(receipt)!=expected_fields or receipt['passed'] is not True or receipt['site']!='system': raise ValueError('causal-null schema')
        keys=sorted(p['families'][family]['heads']);mask=position_mask(rows,'system','cpu')
        if len(receipt['captures'])!=2: raise ValueError('causal-null capture coverage')
        for capture,(source,label) in zip(receipt['captures'],((rows,'recipient'),(donors,'donor'))):
            if set(capture)!={'bank','step','site','row_ids','position_ids','indices','history_lengths','values'} or capture['bank']!=label or capture['step']!=-1 or capture['site']!='system' or capture['row_ids']!=[r['id'] for r in source] or capture['history_lengths']!=[r['length'] for r in rows]: raise ValueError('causal-null capture identity/history')
            if capture['position_ids']!=[r['position']['hashes']['system'] for r in source] or capture['indices']!=[r['position']['indices']['system'] for r in source] or [v['key'] for v in capture['values']]!=keys: raise ValueError('causal-null exact mask/family')
            for value in capture['values']:
                if set(value)!={'key','shape','dtype','sha256','positions_sha256'} or value['shape']!=[8,224,128] or value['dtype']!='torch.bfloat16' or value['positions_sha256']!=cc.tensor_sha(mask): raise ValueError('causal-null shape/dtype/mask')
                cc._hex(value['sha256'])
        if [v['key'] for v in receipt['selected']]!=keys: raise ValueError('causal-null selected head coverage')
        for selected in receipt['selected']:
            if set(selected)!={'key','recipient_sha256','donor_sha256'} or selected['recipient_sha256']!=selected['donor_sha256']: raise ValueError('causal-null selected activations differ')
            cc._hex(selected['recipient_sha256'])
        if [v['row_id'] for v in receipt['controls']]!=[r['id'] for r in rows]: raise ValueError('causal-null full control coverage')
        for control in receipt['controls']:
            if set(control)!=cc.CONTROL_FIELDS-{'control','step','family'} or control['finite'] is not True or control['identical_greedy'] is not True or control['tolerance']!=1e-5 or type(control['bitwise']) is not bool: raise ValueError('causal-null numerical schema')
            cc._finite(control['max_abs_error'])
            if control['max_abs_error']>1e-5: raise ValueError('causal-null numerical error')
            for key in ('expected_sha256','observed_sha256'): cc._hex(control[key])
            if control['bitwise'] and (control['max_abs_error']!=0 or control['expected_sha256']!=control['observed_sha256']): raise ValueError('causal-null bitwise receipt')


if __name__=='__main__': main()
