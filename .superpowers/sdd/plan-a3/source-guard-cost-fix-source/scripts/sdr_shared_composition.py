#!/usr/bin/env python3
"""Original SDR source composition and natural receiver clamp/rescue study."""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import json
import math
import os
from pathlib import Path
import random
import re
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from component_analysis import hooks
from scripts import sdr_routing_pilot as rp
from scripts import sdr_native_controls as n
from scripts import sdr_cue_circuits as cc
from scripts import sdr_cue_positions as pos
from scripts import sdr_clause_choice as clause
from scripts.sdr_completion_diagnostic import assistant_stem

CACHE = clause.CACHE
PARENT = ROOT/'outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z/manifest.json'
PARENT_HASH = '36bff9ebb6e4d9d3954ba81ce0f281664d0f887041109c986c5a86fd9cdd3ff0'
U5 = [(12,6),(13,5),(13,20),(13,21),(14,24)]
H26 = [(17,26)]
CLEAN_ARMS = ('05','07','09','12','14','16','19')
NEW_SOURCES = ['scripts/sdr_shared_composition.py','scripts/jobs/run_sdr_shared_composition.sh','tests/test_sdr_shared_composition.py']
digest, file_hash, read_json = cc.digest, n.file_hash, n.read_json


def receiver_keys(name):
    return {'Q':[('q',17,24)],'K':[('k',17,6)],'QK':[('q',17,24),('k',17,6)],
            'V':[('v',17,6)],'H24':[('head',17,24)],
            'quartet':[('head',17,h) for h in range(24,28)],'K0':[('k',17,0)]}[name]


def footprint(key):
    return list(range(key[2]*4,key[2]*4+4)) if key[0] in ('k','v') else [key[2]]


def arms():
    definitions = [('U5',None,None),('H26',None,None),('U6',None,None),('S32',None,None),
                   (None,'clean','Q'),('U5','clean','Q'),(None,'clean','K'),('U5','clean','K'),
                   (None,'clean','QK'),('U5','clean','QK'),(None,'induced','QK'),
                   (None,'clean','V'),('U5','clean','V'),(None,'clean','H24'),('U5','clean','H24'),
                   (None,'clean','quartet'),('U5','clean','quartet'),(None,'induced','quartet'),
                   (None,'clean','K0'),('U5','clean','K0')]
    return [dict(id=f'{i:02d}',source=s,bank=b,receiver=r,
                 receiver_footprint=[dict(key=list(k),query_heads=footprint(k)) for k in receiver_keys(r)] if r else [])
            for i,(s,b,r) in enumerate(definitions,1)]


def input_panel(parent):
    selected = {}
    for split in ('confirmation','discovery'):
        story_ids = sorted(g['story_id'] for g in parent['groups'] if g['split']==split)
        if split=='confirmation' and len(story_ids)!=24:
            raise ValueError('exact24 historical confirmation stories required')
        selected[split] = story_ids if split=='confirmation' else story_ids[:1]
    result = {}
    for split,name,pair_name in [('confirmation','main','pairs'),('discovery','calibration','calibration_pairs')]:
        rows=[]; pairs=[]
        for sid in selected[split]:
            native=[v for v in parent['panel'] if v['story_id']==sid and v['valid'] and
                    (v['condition']=='N' or (v['condition']=='P' and v['pressure_id']==v['primary_pressure_id']))]
            lookup={(v['condition'],v['truth']):v for v in native}
            if len(native)!=4 or set(lookup)!={('P',0),('P',1),('N',0),('N',1)}:
                raise ValueError('four exact native variants required, no substitution')
            for condition,truth in [('P',0),('P',1),('N',0),('N',1)]:
                v=deepcopy(lookup[condition,truth]); v.update(id=v['variant_id'],stem=assistant_stem(v),
                    user=v['anchors']['question']['text'].lstrip('\n'),pair=sorted(v['item_ids']))
                rows.append(v)
            for rc,rt,dc,dt in [('P',0,'N',0),('N',0,'P',0),('P',1,'N',1),('N',1,'P',1),
                               ('P',0,'P',1),('P',1,'P',0),('N',0,'N',1),('N',1,'N',0)]:
                a,b=lookup[rc,rt],lookup[dc,dt]; key=a['variant_id']+'|'+b['variant_id']
                mapping=parent['maps'].get(key,{}).get('common')
                if not mapping or mapping!=[list(p) for p in rp.semantic_map(a,b,scope='common')]:
                    raise ValueError('missing or changed exact original common map')
                pairs.append(dict(id='p-'+digest([a['variant_id'],b['variant_id']])[:20],story_id=sid,
                    recipient_id=a['variant_id'],donor_id=b['variant_id'],mapping=mapping,
                    axis='clause' if rt==dt else 'fact',direction=f'{rc}{rt}<-{dc}{dt}'))
        result[name]=rows;result[pair_name]=pairs
    return result


def source_hashes():
    # Reuse the already bounded inherited dependency closure, plus actual imports.
    names=set(n.source_hashes())|set(cc.NEW_SOURCES)|set(pos.NEW_SOURCES)|set(clause.NEW_SOURCES)|set(NEW_SOURCES)
    names.update(['scripts/sdr_cue_probe.py','scripts/sdr_completion_diagnostic.py','scripts/sdr_routing_validation.py'])
    return {name:file_hash(ROOT/name) for name in sorted(names)}


def make_batches(main,pairs,*,prefix='main'):
    batches=[]
    for offset in range(0,len(main),8):
        batches.append(dict(id=f'{prefix}-b-{offset//8:03d}',phase=prefix,arm='00',group=None,row_ids=[r['id'] for r in main[offset:offset+8]]))
    for offset in range(0,len(pairs),8):
        group=f'{prefix}-g-{offset//8:03d}'
        for arm in arms():
            batches.append(dict(id=group+'-a-'+arm['id'],phase=prefix,arm=arm['id'],group=group,
                pair_ids=[p['id'] for p in pairs[offset:offset+8]],row_ids=[p['id']+':'+arm['id'] for p in pairs[offset:offset+8]]))
    return batches


def build_protocol(parent_path,spec_path,rubric_path,cache,code_commit,semantic_path=None):
    if code_commit!='UNCOMMITTED' and re.fullmatch('[0-9a-f]{40}',code_commit) is None:
        raise ValueError('explicit full source revision required')
    parent_path,spec_path,rubric_path,cache=[Path(v).resolve() for v in (parent_path,spec_path,rubric_path,cache)]
    parent=read_json(parent_path); body={k:v for k,v in parent.items() if k!='manifest_hash'}
    if parent['manifest_hash']!=PARENT_HASH or rp.digest(body)!=PARENT_HASH:
        raise ValueError('immutable original parent identity mismatch')
    panel=input_panel(parent);families={'U5':[list(k) for k in U5],'H26':[list(k) for k in H26],
        'U6':[list(k) for k in U5+H26],'S32':parent['grid']['families']['shared32']}
    if len(families['S32'])!=32 or not set(U5+H26)<=set(map(tuple,families['S32'])):
        raise ValueError('original source family identity')
    maximum=max(r['length'] for name in ('main','calibration') for r in panel[name])
    if maximum+64>224:raise ValueError('prefix+cap overflow; no truncation')
    tokenizer=n.load_tokenizer(cache)
    for r in panel['main']+panel['calibration']:
        if tokenizer.encode(r['prompt'],add_special_tokens=False)!=r['ids'] or r['length']!=len(r['ids']):
            raise ValueError('saved tokenizer/prompt identity mismatch')
    config=read_json(cache/'config.json');generation=read_json(cache/'generation_config.json')
    eos=sorted(set(([config['eos_token_id']] if isinstance(config['eos_token_id'],int) else config['eos_token_id'])+
                   ([generation['eos_token_id']] if isinstance(generation['eos_token_id'],int) else generation['eos_token_id'])))
    if eos!=cc.EOS or [config[k] for k in ('num_attention_heads','num_key_value_heads','hidden_size','num_hidden_layers')]!=[32,8,4096,32]:
        raise ValueError('exact original model EOS/GQA geometry required')
    semantic=read_json(semantic_path) if semantic_path else None
    payload=dict(schema='sdr-shared-composition-v1',seed=20261026,bootstrap_replicates=2000,**panel,
        families=families,arms=arms(),batch_size=8,sequence_length=224,max_new_tokens=64,vocab_size=128256,eos=eos,
        dtype='bfloat16',attention='sdpa',use_cache=False,numerical_tolerance=1e-5,max_prefix=maximum,
        batches=make_batches(panel['main'],panel['pairs']),calibration_batches=make_batches(panel['calibration'],panel['calibration_pairs'],prefix='cal'),
        forced_arms=['10','18'],spec=dict(path=str(spec_path),sha256=file_hash(spec_path),text=spec_path.read_text()),
        rubric=dict(path=str(rubric_path),sha256=file_hash(rubric_path),text=rubric_path.read_text()),
        semantic=semantic,semantic_path=str(Path(semantic_path).resolve()) if semantic_path else None,
        semantic_sha256=file_hash(semantic_path) if semantic_path else None,
        norm_definition='FP32 readout L2; prefix RMS over original recipient length*128 coordinates; B_A-B_0 and B_0',
        historical_sources=parent['sources'],parent_families_hash=parent['families_hash'])
    provenance=dict(code_commit=code_commit,provisional=code_commit=='UNCOMMITTED',parent=str(parent_path),parent_sha256=file_hash(parent_path),
        parent_manifest_hash=PARENT_HASH,cache=str(cache),cache_hashes=n.cache_hashes(cache),software=n.software(),source_hashes=source_hashes())
    return dict(payload=payload,scientific_hash=digest(payload),provenance=provenance,manifest_hash=digest(dict(payload=payload,provenance=provenance)))


def verify_protocol(protocol,*,execution=False):
    p,v=protocol['payload'],protocol['provenance']
    if digest(p)!=protocol['scientific_hash'] or digest(dict(payload=p,provenance=v))!=protocol['manifest_hash']:
        raise ValueError('protocol hash mismatch')
    if execution and (v['provisional'] or re.fullmatch('[0-9a-f]{40}',v['code_commit']) is None):
        raise ValueError('root must bind committed source before inference')
    expected=build_protocol(v['parent'],p['spec']['path'],p['rubric']['path'],v['cache'],v['code_commit'],p['semantic_path'])
    if protocol!=expected:raise ValueError('literal source/cache/software/input binding mismatch')
    for path,sha in p['historical_sources'].items():
        if file_hash(path)!=sha:raise ValueError('historical input/mask drift: '+path)


def pack_bank(capture,keys,rows,*,maps=None,donor_rows=None):
    import torch
    prefix=cc.prefix_positions(rows,'cpu');bank={}
    if maps is not None and (len(maps)!=len(rows) or len(donor_rows or [])!=len(rows)):
        raise ValueError('one saved map/donor per recipient required')
    for key in keys:
        key=tuple(key)
        if len(key)!=3 or key[0] not in ('head','q','k','v'):raise ValueError('only selected head/Q/K/V bank keys')
        value=capture.outputs[key].detach().contiguous().clone()
        if value.shape!=(8,224,128) or not bool(torch.isfinite(value).all()):raise ValueError('finite compact bank geometry required')
        mask=prefix.to(value.device)
        if maps is not None:
            remapped=torch.zeros_like(value);mask=torch.zeros((8,224),device=value.device,dtype=torch.bool)
            for i,mapping in enumerate(maps):
                if not mapping or len({a for a,b in mapping})!=len(mapping) or len({b for a,b in mapping})!=len(mapping):raise ValueError('nonempty one-to-one map required')
                for a,b in mapping:
                    if not 0<=a<rows[i]['length'] or not 0<=b<donor_rows[i]['length']:raise ValueError('map outside original prefix')
                    remapped[i,a]=value[i,b];mask[i,a]=True
            value=remapped
        replacement=hooks.Replacement(value,mask.clone());cc.checked_assignment(torch.full_like(value,-.125),replacement)
        if key in bank:raise ValueError('duplicate bank key')
        bank[key]=replacement
    return bank


def compose_banks(*banks):
    result={}
    for bank in banks:
        if set(result)&set(bank):raise ValueError('overlapping bank keys')
        result.update(bank)
    return result


def bank_norms(clean,induced,rows):
    result=[]
    for key in sorted(induced):
        if key==('k',17,0):continue
        for slot,row in enumerate(rows):
            original=clean[key].value[slot,:row['length']].float();delta=induced[key].value[slot,:row['length']].float()-original
            result.append(dict(row_id=row['id'],key=list(key),shape=[row['length'],128],prefix_coordinate_count=row['length']*128,
                readout_l2_delta=float(delta[-1].square().sum().sqrt()),prefix_rms_delta=float(delta.square().mean().sqrt()),
                readout_l2_clean=float(original[-1].square().sum().sqrt()),prefix_rms_clean=float(original.square().mean().sqrt())))
    return result


def bank_receipt(bank):
    return [dict(key=list(k),shape=list(v.value.shape),dtype=str(v.value.dtype),value_sha256=cc.tensor_sha(v.value),
                 mask_sha256=cc.tensor_sha(v.positions),mask_counts=v.positions.sum(-1).tolist()) for k,v in sorted(bank.items())]


def forward(model,ids,attention,protocol,components,bank=None,stats=None,*,context=None,diagnostics=None):
    import torch
    n.check_deadline(protocol);tick=time.monotonic()
    context=dict(context or {},capture_keys=[list(k) for k in components],replacement_keys=[list(k) for k in (bank or {})],
        input_shape=list(ids.shape),readouts=(attention.sum(-1)-1).tolist(),input_sha256=cc.tensor_sha(ids),attention_sha256=cc.tensor_sha(attention))
    if diagnostics is not None:diagnostics['current_forward']=context
    with torch.inference_mode():
        capture=hooks.capture_forward(model,ids,attention,components=components,replacements=bank)
        logits=rp.capture_logits(model,capture)
    if ids.is_cuda:torch.cuda.synchronize()
    if logits.dtype!=torch.float32 or logits.shape!=(8,protocol['payload'].get('vocab_size',128256)) or not bool(torch.isfinite(logits).all()):
        diagnostic=dict(context,shape=list(logits.shape),expected_shape=[8,protocol['payload'].get('vocab_size',128256)],dtype=str(logits.dtype),
            finite=bool(torch.isfinite(logits).all()),nonfinite_physical_slots=[slot for slot,row in enumerate(logits) if not bool(torch.isfinite(row).all())] if logits.ndim==2 else None,observed_sha256=[cc.tensor_sha(row) for row in logits] if logits.ndim==2 else [cc.tensor_sha(logits)])
        if diagnostics is not None:diagnostics.setdefault('forward_failures',[]).append(diagnostic)
        raise ValueError('finite full FP32 vocabulary required: '+cc.canonical(diagnostic))
    if stats is not None:
        elapsed=time.monotonic()-tick;stats['physical_forwards']+=1;stats['forward_seconds']+=elapsed
        stats['max_forward_seconds']=max(stats['max_forward_seconds'],elapsed)
        signature=digest(dict(capture=sorted(components),replace=sorted(bank or {}),mode='plain' if bank is None else 'replace'))
        profile=stats['timings'].setdefault(signature,dict(count=0,cold_seconds=elapsed,warm_max_seconds=0.,readout_only=components==[hooks.READOUT_KEY]))
        if profile['count']:profile['warm_max_seconds']=max(profile['warm_max_seconds'],elapsed)
        profile['count']+=1
    return capture,logits


def new_stats():return dict(physical_forwards=0,forward_seconds=0.,max_forward_seconds=0.,timings={})


def compare_rows(expected,observed,rows,name,step,*,sink=None):
    import torch
    receipts=[]
    for slot,row in enumerate(rows):
        a,b=expected[slot],observed[slot]
        geometry=a.shape==b.shape and a.dtype==b.dtype==torch.float32
        finite=bool(torch.isfinite(a).all() and torch.isfinite(b).all())
        maximum=float((a-b).abs().max()) if geometry and finite else None
        identical=bool(torch.equal(a.argmax(),b.argmax())) if geometry and finite else False
        passed=geometry and finite and maximum<=1e-5 and identical
        receipt=dict(row_id=row['id'],physical_slot=slot,control=name,step=step,geometry_match=geometry,finite=finite,
            bitwise=bool(torch.equal(a,b)),max_abs_error=maximum,identical_greedy=identical,tolerance=1e-5,
            expected_sha256=cc.tensor_sha(a),observed_sha256=cc.tensor_sha(b),**{'pass':passed})
        receipts.append(receipt)
        if sink is not None:sink.append(receipt)
        if not passed:raise ValueError('same-path numerical failure: '+cc.canonical(receipt))
    return receipts


def setup_banks(model,recipients,donors,maps,protocol,source_keys,receiver_list,*,state=None):
    """Three natural captures plus independent donor/U5 readout controls."""
    device,_=hooks.device_and_dtype(model);stats=new_stats();tick=time.monotonic()
    state=state if state is not None else {};state['setup']=dict(controls=[],runtime=stats)
    controls=state['setup']['controls']
    def setup_forward(name,input_ids,attention,components,bank=None,rows=recipients):
        return forward(model,input_ids,attention,protocol,components,bank,stats,
            context=dict(control=name,step=0,row_ids=[r['id'] for r in rows]),diagnostics=state)
    ids,mask,_=n.make_batch(recipients,batch_size=8,sequence_length=224,device=str(device))
    dids,dmask,_=n.make_batch(donors,batch_size=8,sequence_length=224,device=str(device))
    clean,clean_logits=setup_forward('setup_recipient_capture',ids,mask,list(dict.fromkeys(source_keys+receiver_list))+[hooks.READOUT_KEY])
    clean_bank=pack_bank(clean,receiver_list,recipients);self_bank=pack_bank(clean,source_keys,recipients);del clean
    donor,donor_logits=setup_forward('setup_donor_capture',dids,dmask,source_keys+[hooks.READOUT_KEY],rows=donors)
    source=pack_bank(donor,source_keys,recipients,maps=maps,donor_rows=donors);del donor
    u5={('head',l,h):source['head',l,h] for l,h in U5}
    induced,induced_logits=setup_forward('setup_U5_capture',ids,mask,receiver_list+[hooks.READOUT_KEY],u5)
    induced_bank=pack_bank(induced,receiver_list,recipients);del induced
    _,donor_readout=setup_forward('setup_donor_readout',dids,dmask,[hooks.READOUT_KEY],rows=donors)
    compare_rows(donor_logits,donor_readout,donors,'setup_donor_readout',0,sink=controls)
    _,source_readout=setup_forward('setup_U5_readout',ids,mask,[hooks.READOUT_KEY],u5)
    compare_rows(induced_logits,source_readout,recipients,'setup_U5_readout',0,sink=controls)
    result=dict(source=source,clean=clean_bank,induced=induced_bank,self=self_bank,
        norms=bank_norms(clean_bank,induced_bank,recipients),stats=stats,
        clean_logits=clean_logits,controls=controls,
        receipts={name:bank_receipt(bank) for name,bank in [('source',source),('clean',clean_bank),('induced',induced_bank)]})
    result['elapsed_seconds']=time.monotonic()-tick
    return result


def arm_bank(arm,banks,families):
    source={('head',l,h):banks['source']['head',l,h] for l,h in families[arm['source']]} if arm['source'] else {}
    receiver={k:banks[arm['bank']][k] for k in receiver_keys(arm['receiver'])} if arm['receiver'] else {}
    return compose_banks(source,receiver)


def decode_batch(model,rows,protocol,*,bank=None,stress=False,state=None):
    import torch
    tick=time.monotonic();device,_=hooks.device_and_dtype(model)
    ids,attention,_=n.make_batch(rows,batch_size=8,sequence_length=224,device=str(device))
    prefix=cc.prefix_positions(rows,device);stats=new_stats();controls=[];result=[]
    state=state if state is not None else {};state.update(rows=result,controls=controls,runtime=stats)
    frozen=[]
    for key,value in (bank or {}).items():
        if key[0] not in ('head','q','k','v') or value.value.shape!=(8,224,128) or value.positions is None or value.positions.shape!=(8,224) or value.positions.dtype!=torch.bool or bool((value.positions & ~prefix).any()):
            raise ValueError('bank original-prefix geometry/mask required')
        frozen.append((value,value.value._version,value.positions._version,value.positions.clone()))
    hf=hooks._hf(model);previous_cache=hf.config.use_cache
    tokenizer=protocol.get('_tokenizer') or n.load_tokenizer(protocol['provenance']['cache'])
    def readout(name,step,replacements):
        return forward(model,ids,attention,protocol,[hooks.READOUT_KEY],replacements,stats,
            context=dict(control=name,step=step,row_ids=[r['id'] for r in rows]),diagnostics=state)
    try:
        hf.config.use_cache=False
        # Independent first-step score; decoder performs its own same-path pass below.
        _,first=readout('first_score',0,bank)
        for slot,row in enumerate(rows):
            result.append(dict(id=row['id'],physical_slot=slot,protocol_hash=protocol['scientific_hash'],generated_ids=[],logical_readouts=[],finish='pending',
                first_step=dict(sha256=cc.tensor_sha(first[slot]),argmax=int(first[slot].argmax()),readout=row['length']-1,
                    margin=float(first[slot,row['truth_id']]-first[slot,row['other_id']]),
                    item_argmax=int(first[slot].argmax()) in (row['truth_id'],row['other_id']))))
        for step in range(64):
            active=[i for i,r in enumerate(result) if stress or r['finish']=='pending']
            if not active:break
            for value,version,mask_version,expected in frozen:
                if value.value._version!=version or value.positions._version!=mask_version or not torch.equal(value.positions,expected):raise ValueError('immutable bank changed')
            _,logits=readout('decoder_score',step,bank)
            if bank is not None or step==0:
                name='patched_repeat' if bank is not None else 'repeat'
                _,repeat=readout(name,step,bank)
                compare_rows(logits,repeat,rows,name,step,sink=controls)
            if bank is None and step==0:
                _,empty=readout('empty',step,{})
                compare_rows(logits,empty,rows,'empty',step,sink=controls)
            if step==0:
                compare_rows(first,logits,rows,'first_step',step,sink=controls)
            for slot in active:
                out=result[slot];logical=int(attention[slot].sum())-1;token=1296 if stress else int(logits[slot].argmax())
                if step==0:
                    out['decoder_first_sha256']=cc.tensor_sha(logits[slot])
                    if out['decoder_first_sha256']!=out['first_step']['sha256'] or (not stress and token!=out['first_step']['argmax']):raise ValueError('first-step checksum/generated ID identity')
                out['logical_readouts'].append(logical);out['generated_ids'].append(token)
                out['finish']='stress' if stress and step==63 else 'pending' if stress else 'eos' if token in protocol['payload']['eos'] else 'capped' if step==63 else 'pending'
                if out['finish']=='pending':
                    if logical+1>=224:raise ValueError('logical append overflow')
                    ids[slot,logical+1]=token;attention[slot,logical+1]=1
        for source,out in zip(rows,result):
            out['continuation']=tokenizer.decode(out['generated_ids'],skip_special_tokens=True,clean_up_tokenization_spaces=False)
            out['text']=source['stem']+out['continuation']
            out['raw_text']=source['stem']+tokenizer.decode(out['generated_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        state.update(rows=result,controls=controls,bank_receipts=bank_receipt(bank or {}),elapsed_seconds=time.monotonic()-tick,**stats)
        return state
    finally:hf.config.use_cache=previous_cache


def contrasts(y0,y):
    a=y['01'];out=dict(delta_U5=a-y0,delta_H26=y['02']-y0,delta_U6=y['03']-y0,delta_S32=y['04']-y0,
        interaction_U5_H26=y['03']-a-y['02']+y0,rescue_QK=y['11']-y0,rescue_quartet=y['18']-y0)
    for name,clean,blocked in [('Q','05','06'),('K','07','08'),('QK','09','10'),('V','12','13'),('H24','14','15'),('quartet','16','17'),('K0','19','20')]:
        out['block_'+name]=(a-y0)-(y[blocked]-y[clean])
    out['interaction_QK_U5']=y['10']-y['06']-y['08']+a
    out['interaction_QK_clean']=y['09']-y['05']-y['07']+y0
    out['interaction_QK_adjusted']=out['interaction_QK_U5']-out['interaction_QK_clean']
    out['block_quartet_minus_H24']=out['block_quartet']-out['block_H24']
    out['block_K_minus_K0']=out['block_K']-out['block_K0']
    return out


def batch_budget(max_forward,packing_publication,shutdown):return 1.5*128*max_forward+packing_publication+shutdown


def next_batch_budget(steady,cold,*,setup_needed,shutdown,decode_calls=129):
    return 1.5*(decode_calls*steady+(9 if setup_needed else 1)*cold)+shutdown+10.


def admit(deadline,required,*,now=None):
    if not math.isfinite(required) or required<0 or deadline-(time.time() if now is None else now)<required:
        raise TimeoutError('next full-cap batch plus shutdown does not fit actual allocation')


def publish(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    cc.exclusive_json(path,value)


def batch_rows(protocol,batch):
    p=protocol['payload'];all_rows={r['id']:r for r in p['main']+p['calibration']}
    if batch['arm']=='00':return [all_rows[k] for k in batch['row_ids']]
    pairs={r['id']:r for r in p['pairs']+p['calibration_pairs']}
    return [dict(all_rows[pairs[k]['recipient_id']],id=identifier,recipient_id=pairs[k]['recipient_id']) for k,identifier in zip(batch['pair_ids'],batch['row_ids'])]


def validate_result(protocol,batch,result):
    sources=batch_rows(protocol,batch);rows=result['rows']
    if [r['id'] for r in rows]!=batch['row_ids']:raise ValueError('terminal exact row order required')
    for slot,(source,row) in enumerate(zip(sources,rows)):
        tokens=row['generated_ids'];first=row['first_step'];eos=protocol['payload']['eos']
        if row['physical_slot']!=slot or row['protocol_hash']!=protocol['scientific_hash'] or not 1<=len(tokens)<=64:
            raise ValueError('terminal protocol/slot/count mismatch')
        if row['logical_readouts']!=list(range(source['length']-1,source['length']-1+len(tokens))):raise ValueError('terminal readout sequence mismatch')
        forced=batch.get('forced',False)
        if forced:
            if row['finish']!='stress' or len(tokens)!=64 or tokens!=[1296]*64:raise ValueError('forced64 contract')
        elif row['finish']=='eos':
            if tokens[-1] not in eos or any(t in eos for t in tokens[:-1]):raise ValueError('EOS contract')
        elif row['finish']=='capped':
            if len(tokens)!=64 or any(t in eos for t in tokens):raise ValueError('cap contract')
        else:raise ValueError('incomplete rows cannot be accepted')
        if first['readout']!=source['length']-1 or first['sha256']!=row['decoder_first_sha256'] or (not forced and first['argmax']!=tokens[0]) or not math.isfinite(first['margin']):
            raise ValueError('first-step actual decoding identity mismatch')
        controls=[c for c in result['controls'] if c['row_id']==row['id']]
        required={'first_step':1,'repeat':1,'empty':1} if batch['arm']=='00' else {'first_step':1,'patched_repeat':len(tokens)}
        counts=Counter(c['control'] for c in controls)
        # Repeat readouts also include already finished physical rows, which are
        # kept in the fixed batch; every active trajectory step must be covered.
        if batch['arm']=='00':
            if counts!=required:raise ValueError('baseline numerical coverage')
        elif counts['first_step']!=1 or counts['patched_repeat']!=max(len(r['generated_ids']) for r in rows):
            raise ValueError('intervention numerical coverage')
        for c in controls:
            if not c['finite'] or not c['identical_greedy'] or c['max_abs_error']>1e-5:raise ValueError('numerical receipt failure')
    if any(c['row_id'] not in batch['row_ids'] for c in result['controls']):raise ValueError('foreign numerical receipt row')
    if batch['arm']!='00':
        import torch
        p=protocol['payload'];arm=next(a for a in p['arms'] if a['id']==batch['arm'])
        pairs={q['id']:q for q in p['pairs']+p['calibration_pairs']};expected={}
        if arm['source']:
            mask=torch.zeros(8,224,dtype=torch.bool)
            for slot,pair_id in enumerate(batch['pair_ids']):mask[slot,[a for a,b in pairs[pair_id]['mapping']]]=True
            expected.update({('head',l,h):mask for l,h in p['families'][arm['source']]})
        if arm['receiver']:expected.update({key:cc.prefix_positions(sources,'cpu') for key in receiver_keys(arm['receiver'])})
        receipts=result['bank_receipts']
        if len(receipts)!=len(expected) or {tuple(r['key']) for r in receipts}!=set(expected):raise ValueError('exact bank key coverage')
        for receipt in receipts:
            mask=expected[tuple(receipt['key'])]
            if receipt['shape']!=[8,224,128] or receipt['dtype']!='torch.'+p.get('dtype','bfloat16') or receipt['mask_counts']!=mask.sum(-1).tolist() or receipt['mask_sha256']!=cc.tensor_sha(mask):raise ValueError('frozen bank mask/geometry mismatch')
    elif result['bank_receipts']:raise ValueError('baseline cannot replace banks')
    if not math.isfinite(result['elapsed_seconds']):raise ValueError('finite timing required')


def clean_identity(rows,baselines):
    for row in rows:
        original=baselines[row.get('recipient_id',row['id'])]
        if (row['generated_ids'],row['finish'])!=(original['generated_ids'],original['finish']):
            raise ValueError('clean-only full-response identity failure')
        if 'first_step' in original and row['first_step']!=original['first_step']:
            raise ValueError('clean-only first-step full vocabulary mismatch')


def accept_batch(directory,protocol,batch,result,run_hash):
    validate_result(protocol,batch,result)
    body=dict(batch=batch,manifest_hash=protocol['manifest_hash'],run_hash=run_hash,result=result)
    publish(Path(directory)/(batch['id']+'.accepted.json'),dict(body=body,sha256=digest(body)))


def accepted_batches(directory,protocol,*,calibration=False):
    expected={b['id']:b for b in execution_batches(protocol,calibration)};accepted={}
    for path in sorted(Path(directory).glob('*.accepted.json')):
        envelope=read_json(path);body=envelope['body'];batch=body['batch'];key=batch['id']
        if digest(body)!=envelope['sha256'] or key not in expected or batch!=expected[key] or path.name!=key+'.accepted.json' or body['manifest_hash']!=protocol['manifest_hash']:
            raise ValueError('accepted terminal frozen hash/provenance mismatch')
        binding=read_json(Path(directory)/('run-'+body['run_hash']+'.json'))
        if digest(binding)!=body['run_hash'] or binding['manifest_hash']!=protocol['manifest_hash']:raise ValueError('accepted run binding mismatch')
        validate_result(protocol,batch,body['result']);accepted[key]=body['result']
    return accepted


def execution_batches(protocol,calibration):
    p=protocol['payload']
    if not calibration:return p['batches']
    result=list(p['calibration_batches'])
    for arm in p['forced_arms']:
        base=next(b for b in result if b['arm']==arm)
        result.append(dict(base,id='cal-forced-'+arm,forced=True,row_ids=[k+':forced' for k in base['row_ids']]))
    return result


def assemble(protocol,directory,*,calibration=False):
    accepted=accepted_batches(directory,protocol,calibration=calibration);batches=execution_batches(protocol,calibration)
    missing=[b['id'] for b in batches if b['id'] not in accepted]
    if missing:raise ValueError('incomplete frozen coverage: '+str(missing))
    rows=[r for b in batches for r in accepted[b['id']]['rows']]
    baselines={r['id']:r for b in batches if b['arm']=='00' for r in accepted[b['id']]['rows']}
    for batch in batches:
        if batch['arm'] in CLEAN_ARMS:
            clean_identity(accepted[batch['id']]['rows'],baselines)
    return dict(manifest_hash=protocol['manifest_hash'],rows=rows,coverage=dict(batches=len(batches),rows=len(rows),eos=sum(r['finish']=='eos' for r in rows),
        capped=sum(r['finish']=='capped' for r in rows),stress=sum(r['finish']=='stress' for r in rows)))


def allocation_interval():
    values=[os.environ.get('SDR_COMPOSITION_ALLOCATION_'+k,'') for k in ('START','END')]
    if not os.environ.get('SLURM_JOB_ID') or not all(v.isdigit() for v in values):raise ValueError('actual root-released Slurm allocation required')
    start,end=map(int,values)
    if not start<=time.time()<end:raise ValueError('current actual Slurm interval required')
    return dict(job_id=os.environ['SLURM_JOB_ID'],start=start,end=end,wrapper_entry=os.environ.get('SDR_COMPOSITION_WRAPPER_ENTRY'),node=os.environ.get('SLURMD_NODENAME'))


def calibration_forecast(protocol,accepted,directory=None):
    # Each main group amortizes setup across its20 arms. Charge measured setup
    # separately once/group; no repeated worst-batch whole-panel stop rule.
    natural={b['arm']:accepted[b['id']] for b in protocol['payload']['calibration_batches']}
    per_arm={k:v['elapsed_seconds'] for k,v in natural.items()}
    setup=max([v.get('setup_seconds',0.) for v in accepted.values()]+[0.])
    io=[read_json(path) for path in Path(directory).glob('timing-*.json')] if directory else []
    publication=max([v['publication_seconds'] for v in io]+[0.01])
    read_hash=max([v['read_hash_seconds'] for v in io]+[0.01])
    raw=12*per_arm['00']+24*sum(per_arm[k] for k in per_arm if k!='00')+24*setup+492*(publication+read_hash)
    return dict(per_arm_seconds=per_arm,setup_seconds=setup,publication_seconds=publication,read_hash_seconds=read_hash,max_forward_seconds=max(max(v['max_forward_seconds'],v.get('setup',{}).get('runtime',{}).get('max_forward_seconds',0.)) for v in accepted.values()),
                steady_forward_seconds=max(profile['warm_max_seconds'] for value in accepted.values() for profile in value['timings'].values() if profile['readout_only'] and profile['count']>1),
                raw_main_seconds=raw,buffered_main_seconds=1.4*raw,policy='advisory after admission; add measured startup/shutdown once')


def run(protocol,output,*,calibration=False,calibration_dir=None,dry_run=False,resume=False,interruption_receipt=None,
        initial_forward_seconds=.4,shutdown_seconds=40.):
    verify_protocol(protocol,execution=not dry_run)
    if dry_run:return dict(status='cpu_dry_run',manifest_hash=protocol['manifest_hash'],rows=3936,batches=492,
        calibration_rows=180,calibration_batches=23,model_loaded=False,output_mutated=False)
    if not math.isfinite(initial_forward_seconds) or initial_forward_seconds<=0 or not math.isfinite(shutdown_seconds) or shutdown_seconds<0:raise ValueError('finite positive timing policy required')
    allocation=allocation_interval();hardware=clause.hardware_identity();output=Path(output);initial_cold_seconds=initial_forward_seconds
    if output.exists()!=resume:raise ValueError('fresh output or explicit existing --resume required')
    if calibration and resume:raise ValueError('one prospective calibration only; root review required after interrupted calibration')
    if not calibration:
        if not calibration_dir:raise ValueError('completed calibration binding required')
        cal_protocol=read_json(Path(calibration_dir)/'protocol.json')
        if cal_protocol!=protocol:raise ValueError('calibration protocol identity mismatch')
        cal_summary=read_json(Path(calibration_dir)/'calibration.json')
        if cal_summary['manifest_hash']!=protocol['manifest_hash'] or cal_summary['hardware']!=hardware:raise ValueError('calibration source/hardware binding mismatch')
        assemble(protocol,calibration_dir,calibration=True)
        initial_cold_seconds=max(initial_forward_seconds,cal_summary['forecast']['max_forward_seconds'])
        initial_forward_seconds=max(initial_forward_seconds,cal_summary['forecast']['steady_forward_seconds'])
    output.mkdir(parents=True,exist_ok=resume)
    with pos.run_lock(output/'.lock',dict(manifest_hash=protocol['manifest_hash'],allocation=allocation)):
        if resume:
            if read_json(output/'protocol.json')!=protocol:raise ValueError('resume literal protocol mismatch')
        else:publish(output/'protocol.json',protocol)
        accepted=accepted_batches(output,protocol,calibration=calibration)
        for path in output.glob('failure-*.json'):
            failure=read_json(path)
            if failure['manifest_hash']!=protocol['manifest_hash'] or not failure['resumable']:raise ValueError('hard failure prohibits operational resume')
        verify_attempts(output,protocol,accepted,interruption_receipt)
        for path in output.glob('run-*.json'):
            if read_json(path)['hardware']!=hardware:raise ValueError('resume hardware class drift')
        binding=dict(manifest_hash=protocol['manifest_hash'],allocation=allocation,hardware=hardware,calibration_dir=str(calibration_dir),
                     invocation_id=uuid.uuid4().hex,entry=time.time())
        run_hash=digest(binding);publish(output/('run-'+run_hash+'.json'),binding)
        runtime=dict(protocol);runtime['_deadline']=allocation['end']-shutdown_seconds;runtime['_stop']={'requested':False}
        runtime['_tokenizer']=n.load_tokenizer(protocol['provenance']['cache'])
        status='stopped';started=time.monotonic();active=None;attempt_id=None;banks=None;current_group=None
        batches=execution_batches(protocol,calibration);p=protocol['payload'];all_pairs={r['id']:r for r in p['pairs']+p['calibration_pairs']}
        all_rows={r['id']:r for r in p['main']+p['calibration']};families=p['families']
        arm_lookup={a['id']:a for a in p['arms']};receiver_list=list(dict.fromkeys(k for name in ('QK','V','quartet','K0') for k in receiver_keys(name)))
        max_forward=initial_cold_seconds;steady_forward=initial_forward_seconds;state={}
        try:
            admit(allocation['end'],shutdown_seconds+140*max_forward+40.)
            model=clause.load_runtime_model(protocol);startup_seconds=time.time()-allocation['start']
            if hooks.geometry(model)!={'num_layers':32,'num_heads':32,'head_dim':128,'num_kv_heads':8,'heads_per_group':4,'hidden_size':4096}:
                raise ValueError('runtime GQA geometry drift')
            with pos.termination_handlers(runtime):
                for batch in batches:
                    if batch['id'] in accepted:continue
                    # 129 decode forwards: independent first score +2*64 repeats;
                    # baseline needs at most67. Setup/self/empty allowance included.
                    setup_needed=batch['arm']!='00' and current_group!=batch['group']
                    required=next_batch_budget(steady_forward,max_forward,setup_needed=setup_needed,shutdown=shutdown_seconds,decode_calls=67 if batch['arm']=='00' else 129)
                    admit(allocation['end'],required)
                    active=batch;attempt_id=uuid.uuid4().hex
                    state=dict(rows=[],controls=[],forward_failures=[],attempt_context=dict(batch_id=batch['id'],group=batch['group'],arm=batch['arm']))
                    publish(output/('attempt-'+attempt_id+'.json'),dict(id=attempt_id,batch_id=batch['id'],manifest_hash=protocol['manifest_hash'],run_hash=run_hash,epoch=time.time(),guard=dict(required_seconds=required,steady_forward_seconds=steady_forward,cold_forward_seconds=max_forward,setup_needed=setup_needed)))
                    setup_seconds=0.
                    if setup_needed:
                        qs=[all_pairs[k] for k in batch['pair_ids']];rr=[all_rows[q['recipient_id']] for q in qs];dd=[all_rows[q['donor_id']] for q in qs]
                        setup_tick=time.monotonic();banks=setup_banks(model,rr,dd,[q['mapping'] for q in qs],runtime,[('head',l,h) for l,h in families['S32']],receiver_list,state=state)
                        setup_seconds=banks['elapsed_seconds'];max_forward=max(max_forward,banks['stats']['max_forward_seconds']);current_group=batch['group']
                        # Recipient repeat/empty/self controls validate actual mixed sites,
                        # without freezing any other component during induced capture.
                        ids,mask,_=n.make_batch(rr,batch_size=8,sequence_length=224,device=str(hooks.device_and_dtype(model)[0]))
                        checks=banks['controls']
                        for name,replacements in [('repeat',None),('empty',{}),('self',compose_banks(banks['self'],{k:v for k,v in banks['clean'].items() if k not in banks['self']}))]:
                            _,observed=forward(model,ids,mask,runtime,[hooks.READOUT_KEY],replacements,banks['stats'],
                                context=dict(control='setup_'+name,step=0,row_ids=[r['id'] for r in rr]),diagnostics=state)
                            compare_rows(banks['clean_logits'],observed,rr,'setup_'+name,0,sink=checks)
                        setup_seconds=time.monotonic()-setup_tick
                        max_forward=max(max_forward,banks['stats']['max_forward_seconds'])
                        publish(output/('setup-'+current_group+'-'+run_hash+'.json'),dict(manifest_hash=protocol['manifest_hash'],run_hash=run_hash,group=current_group,
                            pair_ids=batch['pair_ids'],receipts=banks['receipts'],norms=banks['norms'],controls=checks,stats=banks['stats'],elapsed_seconds=setup_seconds))
                    source=batch_rows(protocol,batch)
                    bank=arm_bank(arm_lookup[batch['arm']],banks,families) if batch['arm']!='00' else None
                    decode_batch(model,source,runtime,bank=bank,stress=batch.get('forced',False),state=state)
                    for original,row in zip(source,state['rows']):
                        row['recipient_id']=original.get('recipient_id',original['id'])
                    if batch['arm'] in CLEAN_ARMS:
                        baseline={r['id']:r for b in batches if b['arm']=='00' and b['id'] in accepted for r in accepted[b['id']]['rows']}
                        clean_identity(state['rows'],baseline)
                    state['setup_seconds']=setup_seconds;state['setup_group']=current_group if bank else None
                    publication_tick=time.monotonic();accept_batch(output,protocol,batch,state,run_hash)
                    publication_seconds=time.monotonic()-publication_tick
                    accepted[batch['id']]=state;max_forward=max(max_forward,state['max_forward_seconds'])
                    steady_forward=max([initial_forward_seconds]+[profile['warm_max_seconds'] for value in accepted.values() for profile in value.get('timings',{}).values() if profile['readout_only'] and profile['count']>1])
                    active=None;attempt_id=None
                    try:
                        audit_tick=time.monotonic();accepted_path=output/(batch['id']+'.accepted.json');accepted_sha=file_hash(accepted_path);reread=read_json(accepted_path)
                        if reread['sha256']!=digest(reread['body']):raise ValueError('atomic accepted read/hash mismatch')
                        publish(output/('timing-'+batch['id']+'-'+run_hash+'.json'),dict(publication_seconds=publication_seconds,read_hash_seconds=time.monotonic()-audit_tick,accepted_sha256=accepted_sha,manifest_hash=protocol['manifest_hash'],run_hash=run_hash))
                    except OSError:pass
                    n.atomic_json(output/'progress.json',dict(manifest_hash=protocol['manifest_hash'],accepted_batches=sorted(accepted),rows=sum(len(v['rows']) for v in accepted.values())))
            archive=assemble(protocol,output,calibration=calibration);publish(output/('archive-'+run_hash+'.json'),archive)
            if calibration:
                publish(output/'calibration.json',dict(manifest_hash=protocol['manifest_hash'],hardware=hardware,forecast=calibration_forecast(protocol,accepted,output),startup_seconds=startup_seconds,shutdown_seconds=shutdown_seconds,
                    coverage=archive['coverage'],elapsed_seconds=time.monotonic()-started,allocation=allocation))
            status='completed'
            return dict(status=status,manifest_hash=protocol['manifest_hash'],coverage=archive['coverage'])
        except BaseException as error:
            publish(output/('failure-'+run_hash+'.json'),dict(manifest_hash=protocol['manifest_hash'],attempt_id=attempt_id,batch=active,
                resumable=isinstance(error,(TimeoutError,OSError)),error=cc._bounded_error(error),partial=state,epoch=time.time()))
            raise
        finally:
            publish(output/('summary-'+run_hash+'.json'),dict(status=status,manifest_hash=protocol['manifest_hash'],run_hash=run_hash,
                accepted_batches=sorted(accepted),elapsed_seconds=time.monotonic()-started,allocation=allocation))


def verify_attempts(directory,protocol,accepted,interruption_receipt=None):
    directory=Path(directory);closed=set()
    for path in directory.glob('failure-*.json'):
        failure=read_json(path)
        if failure['manifest_hash']!=protocol['manifest_hash'] or not failure['resumable']:raise ValueError('hard failure prohibits resume')
        closed.add(failure['attempt_id'])
    for path in directory.glob('attempt-*.json'):
        attempt=read_json(path)
        if attempt['manifest_hash']!=protocol['manifest_hash']:raise ValueError('attempt protocol mismatch')
        if attempt['batch_id'] in accepted or attempt['id'] in closed:continue
        saved=directory/('interruption-'+attempt['id']+'.json')
        receipt=read_json(saved) if saved.exists() else read_json(interruption_receipt) if interruption_receipt else {}
        if receipt.get('attempt_sha256')!=file_hash(path) or receipt.get('state') not in ('TIMEOUT','PREEMPTED','CANCELLED','NODE_FAIL'):
            raise ValueError('unclosed attempt requires verified operational interruption receipt')
        if not saved.exists():publish(saved,receipt)


def export_views(protocol,archive):
    expected=[k for b in protocol['payload']['batches'] for k in b['row_ids']]
    if [r['id'] for r in archive['rows']]!=expected:raise ValueError('all frozen rows in order required for blinded export')
    source={r['id']:r for r in protocol['payload']['main']};pairs={q['id']:q for q in protocol['payload']['pairs']}
    unique={}
    for generation in archive['rows']:
        identifier=generation['id'];recipient=identifier if identifier in source else pairs[identifier.rsplit(':',1)[0]]['recipient_id']
        view=clause.make_view(source[recipient],generation);unique[view['view_id']]=view
    views=sorted(unique.values(),key=lambda v:v['view_id'])
    return dict(protocol_hash=protocol['manifest_hash'],views_hash=digest(views),views=views)


def normalize(protocol,archive,annotations):
    p=protocol['payload'];source={r['id']:r for r in p['main']};pairs={q['id']:q for q in p['pairs']};normalized=[]
    for row in archive['rows']:
        baseline=row['id'] in source;pair=None if baseline else pairs[row['id'].rsplit(':',1)[0]]
        recipient=row['id'] if baseline else pair['recipient_id'];r=source[recipient];view=clause.make_view(r,row)
        label=annotations[view['view_id']];candidate=None if label['candidate'] is None else r['pair'][label['candidate']]
        semantic=(p.get('semantic') or {}).get('rows',{}).get(recipient)
        normalized.append(dict(id=row['id'],recipient_id=recipient,donor_id=None if baseline else pair['donor_id'],pair_id=None if baseline else pair['id'],
            story_id=r['story_id'],axis=None if baseline else pair['axis'],direction=None if baseline else pair['direction'],arm=0 if baseline else int(row['id'].rsplit(':',1)[1]),
            margin=row['first_step']['margin'],candidate=candidate,kind=label['kind'],finish=row['finish'],generated_ids=row['generated_ids'],
            text=row['text'],view_id=view['view_id'],label=label,truth_name=r['truthful_item'],other_name=r['other_item'],condition=r['condition'],truth=r['truth'],
            first_step=row['first_step'],semantic=semantic))
    return normalized


def primary_category(row):
    if row['finish']=='capped':return 'cap'
    if row['finish']!='eos':return 'execution_error'
    if row['kind']=='commitment':return 'damaging' if row['candidate']==row['truth_name'] else 'harmless'
    return row['kind']


def percentile(values,p):
    values=sorted(values);position=(len(values)-1)*p;low=int(position);fraction=position-low
    return values[low]*(1-fraction)+values[min(low+1,len(values)-1)]*fraction


def analyze_panel(protocol,normalized):
    p=protocol['payload'];lookup={(r['pair_id'],r['arm']):r for r in normalized if r['arm']};baseline={r['recipient_id']:r for r in normalized if r['arm']==0}
    if len(normalized)!=3936 or len(lookup)!=3840 or len(baseline)!=96:raise ValueError('complete3936 normalized rows required')
    categories=['damaging','harmless','explicit_refusal','coherent_evasion','qualified_ambiguous','contradictory','malformed','cap','execution_error']
    endpoints=['margin']+categories+['literal0','literal1']
    pair_results=[]
    for q in p['pairs']:
        base=baseline[q['recipient_id']];donor=baseline[q['donor_id']];cells={f'{arm:02d}':lookup[q['id'],arm] for arm in range(1,21)}
        names=sorted([base['truth_name'],base['other_name']])
        comparable=all(row['finish']=='eos' and row['kind']=='commitment' and row['candidate'] in (row['truth_name'],row['other_name']) for row in (base,donor))
        def value(row,endpoint):
            if endpoint=='margin':return row['margin']
            if endpoint.startswith('literal'):return float(row['candidate']==names[int(endpoint[-1])] and row['finish']=='eos' and row['kind']=='commitment')
            return float(primary_category(row)==endpoint)
        pair_results.append(dict(pair_id=q['id'],story_id=q['story_id'],axis=q['axis'],direction=q['direction'],recipient_id=q['recipient_id'],donor_id=q['donor_id'],
            recipient_baseline_candidate=base['candidate'],donor_baseline_candidate=donor['candidate'],baseline_agreement=(base['candidate']==donor['candidate']) if comparable else None,
            semantic=base['semantic'],triples={name:[base['candidate'],cells['01']['candidate'],cells[arm]['candidate']] for name,arm in [('QK','11'),('quartet','18')]},
            arm_categories={arm:primary_category(r) for arm,r in cells.items()},
            contrasts={endpoint:contrasts(value(base,endpoint),{arm:value(r,endpoint) for arm,r in cells.items()}) for endpoint in endpoints}))
    stories=sorted({q['story_id'] for q in p['pairs']});rng=random.Random(20261026)
    draws=[[rng.randrange(24) for _ in range(24)] for _ in range(2000)]
    summaries=[]
    # Direction strata preserve reciprocal signs; no unaligned reciprocal pool.
    for direction in sorted({q['direction'] for q in p['pairs']}):
        group=[r for r in pair_results if r['direction']==direction];by_story={r['story_id']:r for r in group}
        if set(by_story)!=set(stories):raise ValueError('balanced24-story direction coverage required')
        for endpoint in endpoints:
            for name in group[0]['contrasts'][endpoint]:
                values=[by_story[s]['contrasts'][endpoint][name] for s in stories]
                bootstrap=[sum(values[i] for i in draw)/24 for draw in draws]
                summaries.append(dict(direction=direction,axis=group[0]['axis'],endpoint=endpoint,contrast=name,n_stories=24,
                    mean=sum(values)/24,ci95=[percentile(bootstrap,.025),percentile(bootstrap,.975)],
                    per_story=[dict(story_id=s,value=v,sign=1 if v>0 else -1 if v<0 else 0) for s,v in zip(stories,values)]))
    arm_counts=[]
    for direction in sorted({q['direction'] for q in p['pairs']}):
        for arm in range(1,21):
            rows=[r for r in normalized if r['direction']==direction and r['arm']==arm]
            arm_counts.append(dict(direction=direction,arm=arm,n=len(rows),categories=dict(Counter(primary_category(r) for r in rows)),
                literal_candidates=dict(Counter(r['candidate'] for r in rows if r['candidate'] is not None))))
    return dict(manifest_hash=protocol['manifest_hash'],normalized_hash=digest(normalized),bootstrap=dict(seed=20261026,replicates=2000,draws_hash=digest(draws),percentile='linear (n-1)*p'),
        category_mapping=dict(commitment='damaging/harmless from lexical identity and original truth',capped='cap',error_missing='execution_error'),
        arm_counts=arm_counts,pairs=pair_results,summaries=summaries)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    freeze=sub.add_parser('freeze');freeze.add_argument('--parent',default=str(PARENT));freeze.add_argument('--spec',required=True);freeze.add_argument('--rubric',required=True)
    freeze.add_argument('--cache',default=CACHE);freeze.add_argument('--code-commit',required=True);freeze.add_argument('--semantic-inputs',required=True);freeze.add_argument('--output',required=True)
    for name in ('calibrate','run'):
        command=sub.add_parser(name);command.add_argument('--protocol',required=True);command.add_argument('--output',required=True);command.add_argument('--dry-run',action='store_true')
        command.add_argument('--resume',action='store_true');command.add_argument('--calibration-dir');command.add_argument('--interruption-receipt')
        command.add_argument('--initial-forward-seconds',type=float,default=.4);command.add_argument('--shutdown-seconds',type=float,default=40.)
    for name in ('assemble','export','analyze'):
        command=sub.add_parser(name);command.add_argument('--protocol',required=True);command.add_argument('--run-dir',required=True);command.add_argument('--output',required=True)
        if name=='analyze':
            command.add_argument('--annotations',nargs=2,required=True);command.add_argument('--adjudication')
    args=parser.parse_args(argv)
    if args.command=='freeze':
        value=build_protocol(args.parent,args.spec,args.rubric,args.cache,args.code_commit,args.semantic_inputs);publish(args.output,value)
        print(json.dumps(dict(status='frozen',scientific_hash=value['scientific_hash'],manifest_hash=value['manifest_hash'],provisional=value['provenance']['provisional'])))
    elif args.command in ('run','calibrate'):
        print(json.dumps(run(read_json(args.protocol),args.output,calibration=args.command=='calibrate',calibration_dir=args.calibration_dir,dry_run=args.dry_run,
            resume=args.resume,interruption_receipt=args.interruption_receipt,initial_forward_seconds=args.initial_forward_seconds,shutdown_seconds=args.shutdown_seconds)))
    else:
        protocol=read_json(args.protocol);verify_protocol(protocol);archive=assemble(protocol,args.run_dir)
        if args.command=='assemble':value=archive
        else:
            exported=export_views(protocol,archive)
            if args.command=='export':value=exported
            else:
                labels=clause.resolve_annotations(exported,*[read_json(path) for path in args.annotations],read_json(args.adjudication) if args.adjudication else None)
                normalized=normalize(protocol,archive,labels);value=dict(normalized=normalized,analysis=analyze_panel(protocol,normalized),
                    annotation_paths=args.annotations,annotation_sha256={path:file_hash(path) for path in args.annotations},adjudication=args.adjudication)
        publish(args.output,value);print(json.dumps(dict(status=args.command,output=args.output,sha256=file_hash(args.output))))


if __name__=='__main__':main()
