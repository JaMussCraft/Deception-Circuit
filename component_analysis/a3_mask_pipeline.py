"""Standalone A3 matched-mask execution. CPU preparation never loads weights.

Scientific selection consumes validation only. Model stages require current root
reservation evidence; numerical updates/export remain in the reviewed core.
Checkpoints contain gate/Adam/RNG data as authenticated JSON, never pickle/weights.
"""
from __future__ import annotations
import argparse
import base64
import copy
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import random
import re
import time
_MODULE_STARTED=time.perf_counter()

import numpy as np
import torch
from component_analysis import a3_mask as core
from dataset import user_inversion_pipeline as common
from component_analysis import a3_source_validation as source_validation
_SOURCE_VALIDATOR_SEAL=object()
_MODULE_IMPORTED=time.perf_counter()


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()



NATIVE_BANK_GEOMETRY=dict(num_layers=32,num_heads=32,hidden_size=4096,intermediate_size=14336,vocab_size=128256)


def actual_model_geometry(model):
    cfg=model.config
    return dict(num_layers=cfg.num_hidden_layers,num_heads=cfg.num_attention_heads,hidden_size=cfg.hidden_size,
        intermediate_size=cfg.intermediate_size,vocab_size=cfg.vocab_size)


def _bank_geometry(geometry):
    require(isinstance(geometry,dict) and set(geometry)==set(NATIVE_BANK_GEOMETRY)
        and all(type(value) is int and value>0 for value in geometry.values())
        and geometry['hidden_size']%geometry['num_heads']==0,'invalid authenticated bank geometry')
    return geometry


def _bank_keys(keys,geometry):
    _bank_geometry(geometry);result=[]
    for key in keys:
        require(isinstance(key,(list,tuple)) and len(key)==3,'invalid typed bank support key')
        kind,layer,index=key
        require(kind in ('head','mlp') and type(layer) is int and type(index) is int
            and 0<=layer<geometry['num_layers'] and (0<=index<geometry['num_heads'] if kind=='head' else index==0),
            'invalid typed bank support geometry')
        result.append((kind,layer,index))
    require(len(result)==len(set(result)),'duplicate typed bank support')
    return tuple(sorted(result))


def _bank_vector(value,key,geometry,*,dtype=torch.float32):
    width=geometry['hidden_size']//geometry['num_heads'] if key[0]=='head' else geometry['hidden_size']
    if isinstance(value,torch.Tensor):
        require(value.ndim==1 and value.numel()==width and value.dtype!=torch.bool and not value.is_complex(),
            'bank vector must have exact flat typed width')
        require(bool(torch.isfinite(value).all()),'bank vector must be finite')
    else:
        require(isinstance(value,list) and len(value)==width and all(type(x) in (int,float) and math.isfinite(x) for x in value),
            'bank vector must have exact flat typed width and finite numeric values')
    try:result=torch.as_tensor(value,dtype=dtype)
    except (TypeError,ValueError,OverflowError,RuntimeError) as error:raise ValueError('invalid numeric bank vector') from error
    require(result.ndim==1 and result.numel()==width and bool(torch.isfinite(result).all()),'bank vector is not finite in the actual numeric profile')
    return result


def required_bank_support(prepared,task,geometry):
    candidates=_bank_keys(prepared['candidates'],geometry)
    reference=prepared.get('new30',{})
    extra=_bank_keys(reference['removed'],geometry) if task=='far_v2' and reference.get('status')=='available' else ()
    require(candidates,'empty required bank support')
    return tuple(sorted(set(candidates)|set(extra)))


def _bank_domain(rows,*,timing=False):
    require(rows and all(r['condition']=='H' and r['split'] in (('validation',) if timing else ('train','validation')) for r in rows),
        'invalid original H-bank source domain')
    ids=[r['instance_id'] for r in rows]
    require(all(isinstance(i,str) and i for i in ids) and len(ids)==len(set(ids)),'duplicate/invalid H-bank source ids')
    require(all(set(r['streams'])=={'clean','corrupt'} for r in rows),'both H-bank source streams required')
    tokens=sum(validate_source_stream(record) for row in rows for record in row['streams'].values())
    return dict(ids=ids,rows_sha256=digest(rows),n_tokens=tokens)


def actual_bank_model_proof(model):
    return dict(model_geometry=actual_model_geometry(model),runtime_identity=core._computation_identity(model),
        base_identity=core._base_identity(model),dtype=str(next(model.parameters()).dtype))


def _expected_bank_model_proof(prepared,*,model=None,proof=None):
    if model is not None:proof=actual_bank_model_proof(model)
    require(isinstance(proof,dict) and set(proof)=={'model_geometry','runtime_identity','base_identity','dtype'},
        'authenticated current bank model proof required')
    geometry=_bank_geometry(proof['model_geometry'])
    if prepared.get('injected'):
        expected=prepared.get('_injected_bank_model_proof')
        require(isinstance(expected,dict) and proof==expected,'current bank geometry/profile differs from independent actual-model proof')
        declared=prepared['identity'].get('model_geometry',geometry)
    else:
        declared=prepared['identity'].get('model_geometry')
        require(declared==NATIVE_BANK_GEOMETRY,'bank geometry is not bound to authenticated native preparation')
    require(geometry==declared,'bank model proof differs from authenticated preparation geometry')
    require(all(isinstance(proof[k],str) and re.fullmatch('[0-9a-f]{64}',proof[k]) for k in ('runtime_identity','base_identity')),
        'invalid bank numeric/base identity proof')
    require(proof['dtype'] in ('torch.float32','torch.bfloat16','torch.float16','torch.float64'),'invalid bank numeric profile dtype')
    profile_dtype=prepared['identity'].get('numeric_profile',{}).get('dtype')
    if profile_dtype is not None:
        require(proof['dtype']=='torch.'+profile_dtype,'bank model dtype differs from authenticated numeric profile')
    return proof


def validate_h_bank(bank,prepared,*,task,model=None,model_proof=None,design=None,purpose='scientific_H_bank',source_domain=None):
    """Validate values against independent model/source evidence, never bank claims."""
    proof=_expected_bank_model_proof(prepared,model=model,proof=model_proof);geometry=proof['model_geometry']
    expected=required_bank_support(prepared,task,geometry)
    if purpose=='scientific_H_bank':domain=prepared['hbank_sources'][task];kind='a3_mask_H_bank_v1'
    else:
        require(purpose=='validation_timing','unknown bank purpose')
        if source_domain is None:
            require(design is not None,'timing bank source evidence required')
            source_domain=_bank_domain([r for r in design['access_rows'][task] if r['condition']=='H' and r['split']=='validation'],timing=True)
        domain=source_domain;kind='a3_mask_H_bank_timing_v1'
    require(isinstance(domain.get('ids'),list) and domain['ids'] and len(domain['ids'])==len(set(domain['ids']))
        and type(domain['n_tokens']) is int and domain['n_tokens']>0,'invalid authenticated bank source domain/counts')
    require(bank.get('kind')==kind and bank.get('purpose')==purpose and bank.get('source_task')==task
        and bank.get('identity')==prepared['identity'],'changed H-bank source/profile identity')
    require(bank.get('source_rows_sha256')==domain['rows_sha256'] and bank.get('source_ids')==domain['ids']
        and type(bank.get('n_instances')) is int and bank['n_instances']==len(domain['ids'])
        and type(bank.get('n_tokens')) is int and bank['n_tokens']==domain['n_tokens'],'changed original H-bank source domain/counts')
    require(bank.get('model_geometry')==geometry and bank.get('runtime_identity')==proof['runtime_identity']
        and bank.get('base_identity')==proof['base_identity'],'changed H-bank geometry/runtime/base identity')
    require(bank.get('pooling')=='both streams; unpadded token-weighted mean'
        and bank.get('execution_geometry')==dict(physical_batch=1,padded_width=prepared['widths'][task]['H'],
            readout='last unpadded token',pooling='unpadded tokens from both streams'),'changed H-bank execution profile')
    entries=bank.get('values')
    require(isinstance(entries,list) and all(isinstance(e,dict) and set(e)=={'key','value'} for e in entries),'invalid typed bank vector entries')
    keys=_bank_keys([e['key'] for e in entries],geometry)
    require(keys==expected,'missing or extra typed bank support')
    dtype=getattr(torch,proof['dtype'].split('.',1)[1]);values={}
    for entry in entries:
        key=tuple(entry['key']);_bank_vector(entry['value'],key,geometry,dtype=dtype);values[key]=entry['value']
    return values

def _encode(value):
    if isinstance(value,torch.Tensor):
        value=value.detach().cpu().contiguous()
        return {'tensor':str(value.dtype),'shape':list(value.shape),
                'bytes':base64.b64encode(value.reshape(-1).view(torch.uint8).numpy().tobytes()).decode()}
    if isinstance(value,dict):
        return {'map':[[_encode(k),_encode(v)] for k,v in value.items()]}
    if isinstance(value,tuple): return {'tuple':[_encode(v) for v in value]}
    if isinstance(value,list): return [_encode(v) for v in value]
    require(value is None or type(value) in (str,int,float,bool),'unsupported checkpoint value')
    return value


def _decode(value):
    if isinstance(value,list): return [_decode(v) for v in value]
    if not isinstance(value,dict): return value
    if set(value)=={'map'}: return {_decode(k):_decode(v) for k,v in value['map']}
    if set(value)=={'tuple'}: return tuple(_decode(v) for v in value['tuple'])
    require(set(value)=={'tensor','shape','bytes'},'unexpected checkpoint type')
    types={str(t):t for t in (torch.float16,torch.bfloat16,torch.float32,torch.float64,torch.int8,
                            torch.uint8,torch.int16,torch.int32,torch.int64,torch.bool)}
    require(value['tensor'] in types,'unsupported checkpoint tensor dtype')
    data=base64.b64decode(value['bytes'],validate=True)
    dtype=types[value['tensor']]; shape=value['shape']
    require(all(type(n) is int and n>=0 for n in shape),'invalid tensor shape')
    expected=math.prod(shape)*torch.empty((),dtype=dtype).element_size()
    require(len(data)==expected,'checkpoint tensor byte length differs')
    if not data: return torch.empty(shape,dtype=dtype)
    return torch.from_numpy(np.frombuffer(data,dtype=np.uint8).copy()).view(dtype).reshape(shape)


def write_checkpoint(path,state):
    require(state.get('schema')=='a3-mask-checkpoint-v1','core checkpoint schema required')
    # A strict allowlist prevents callers accidentally publishing full state_dict.
    require(set(state)=={'schema','boundary','purpose','update','identity','chunks','update_spec','support','base','optimizer','gates','rng'},
            'checkpoint contains unexpected state (weights forbidden)')
    payload=_encode(state)
    def writer(root):
        (root/'state.json').write_text(json.dumps(payload,allow_nan=False,separators=(',',':'))+'\n')
        (root/'COMPLETE.json').write_text(json.dumps({'sha256':common.file_hash(root/'state.json')})+'\n')
    common.publish(Path(path),writer)


def read_checkpoint(path):
    path=Path(path)
    require(path.is_dir() and {p.name for p in path.iterdir()}=={'state.json','COMPLETE.json'},'incomplete checkpoint')
    require(json.loads((path/'COMPLETE.json').read_text())=={'sha256':common.file_hash(path/'state.json')},'checkpoint digest differs')
    state=_decode(json.loads((path/'state.json').read_text()))
    require(state['schema']=='a3-mask-checkpoint-v1','unexpected checkpoint schema')
    require(state.get('purpose') in ('scientific_training','validation_timing'),'unknown checkpoint purpose')
    rng=state['rng']
    require(set(rng)=={'cpu','cuda'} and rng['cpu'].dtype==torch.uint8 and rng['cpu'].ndim==1 and rng['cpu'].numel()==torch.get_rng_state().numel()
            and all(t.dtype==torch.uint8 and t.ndim==1 for t in rng['cuda']),'malformed checkpoint RNG')
    return state


@contextmanager
def binary_mode(model,removed=None):
    """Scoped native binary gate modes, optionally an exact exported removal set."""
    support=core.support_for(model)
    modes={name:module.training for name,module in model.named_modules()}
    alphas={name:g.log_alpha.detach().clone() for name,g in support.gates.items()}
    if removed is not None:
        removed=set(map(tuple,removed)); require(removed<=set(support.candidates),'removal outside frozen support')
    try:
        model.eval()
        if removed is not None:
            with torch.no_grad():
                for key in support.candidates:
                    _,gate=core._candidate_gate(model,key)
                    gate.log_alpha[key[2]]=-100 if key in removed else 100
        yield
    finally:
        with torch.no_grad():
            for name,g in support.gates.items(): g.log_alpha.copy_(alphas[name])
        for name,module in model.named_modules(): module.training=modes[name]


def binary_parity(model,chunks):
    """Actual native eval equals its exact binary complement under own donors."""
    exported=core.export_removal_mask(model,provenance={})
    with binary_mode(model),torch.no_grad():
        expected=[core.native_chunk_forward(model,c)['logits'].detach() for c in chunks]
    with binary_mode(model,exported['removed']),torch.no_grad():
        actual=[exported_forward(model,c,exported['removed']).detach() for c in chunks]
    errors=[float((a-b).abs().max()) for a,b in zip(expected,actual)]
    require(all(torch.allclose(a,b,atol=1e-5,rtol=1e-5) for a,b in zip(expected,actual)),'native binary complement parity failed')
    return dict(max_abs_error=max(errors,default=0),rows=sum(len(c.ids)*2 for c in chunks),export=exported)


def select_checkpoint(validations):
    require([r['update'] for r in validations]==list(range(20,201,20)),'complete fixed validation schedule required')
    require(all(r.get('split','validation')=='validation' for r in validations),'assessment forbidden in checkpoint selection')
    require(all(not r.get('timing_only') and r.get('purpose','scientific_training')=='scientific_training' for r in validations),'disposable timing records cannot select scientific masks')
    require(all(type(r.get('eligible')) is bool and isinstance(r.get('removed'),list) for r in validations),'incomplete validation gates')
    passing=[r for r in validations if r['eligible']]
    chosen=min(passing,key=lambda r:(r['update'],len(r['removed']))) if passing else validations[-1]
    return dict(copy.deepcopy(chosen),selection_passed=bool(passing))


def schedule(update,validate,*,start=0,previous=(),injected=False):
    """Fixed loop; injectable callbacks are a nonproduction schedule test seam."""
    require(injected,'callbacks permitted only for explicit nonproduction tests')
    require(type(start) is int and 0<=start<=200,'invalid completed update boundary')
    records=copy.deepcopy(list(previous))
    require([r['update'] for r in records]==list(range(20,start+1,20)),'resume validation history differs')
    for index in range(start+1,201):
        update(index)
        if index%20==0: records.append(validate(index))
    return dict(completed_updates=200,validations=records,selected=select_checkpoint(records),injected=True)


def random_controls(candidates,removed,*,seed):
    candidates=sorted(map(tuple,candidates)); removed=set(map(tuple,removed))
    require(len(candidates)==len(set(candidates)) and removed<=set(candidates),'invalid random control support')
    require(seed in (42,1,123),'unregistered mask seed')
    require(all(k[0] in ('head','mlp') for k in candidates),'typed candidate support required')
    generator=torch.Generator(device='cpu').manual_seed(20000+seed)
    controls=[]
    for _ in range(19):
        selected=[]
        for kind in ('head','mlp'):
            universe=[k for k in candidates if k[0]==kind]; count=sum(k[0]==kind for k in removed)
            selected += [universe[i] for i in torch.randperm(len(universe),generator=generator).tolist()[:count]]
        controls.append(sorted(selected))
    return controls


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage',required=True,choices=('prepare','pilot','fit','assess','summarize'))
    for name in ('design','commit','work-dir'): p.add_argument('--'+name,required=True)
    for name in ('a1-design','a1-selected','ledger-snapshot','reservation','admission','inventory','checkpoint','selected','root-bundle'):
        p.add_argument('--'+name)
    p.add_argument('--action',choices=('freeze','inventory','admit'))
    p.add_argument('--target-inventory');p.add_argument('--prepared');p.add_argument('--task',choices=('far_v2','ser_v2','sdr_v2'));p.add_argument('--group')
    p.add_argument('--inventory-stage',choices=('full','pilot'),default='full')
    p.add_argument('--finish-reserve-seconds',type=float)
    p.add_argument('--pilot-receipts',nargs='+')
    p.add_argument('--seed',type=int,choices=(42,1,123),default=42)
    p.add_argument('--arm',choices=('constrained','unconstrained'),default='constrained')
    p.add_argument('--chunk-size',type=int,default=1)
    p.add_argument('--registry',action='append',default=[])
    p.add_argument('--dry-run',action='store_true'); p.add_argument('--resume',action='store_true')
    return p



def source_chunks(design,task,split,condition,*,chunk_size,device,fitting=True,donor='neutral'):
    """Exact ordered source rows; each own twin has a builder-proven token map."""
    require(split in ('train','validation','test') and (not fitting or split=='train'),'test/selection rows forbidden for fitting')
    names={'train':'fit_ids','validation':'selection_ids','test':'assessment_ids'}
    ids=design['tasks'][task][names[split]]
    rows=[r for r in design['access_rows'][task] if r['split']==split]
    indexed={(r['condition'],r['instance_id']):r for r in rows}
    require(len(indexed)==len(rows),'duplicate source row')
    peer={'D':'H','I':'user_neutral','H':'H','F':'F','user_neutral':'user_neutral'}[condition]
    maps={(m['recipient_condition'],m['instance_id'],m['stream']):m for m in design['semantic_twin_maps'][task]}
    chunks=[]
    for start in range(0,len(ids),chunk_size):
        batch=ids[start:start+chunk_size]; recipients=[]; donors=[]; expected=[]; opposite=[]; honest=[]
        for rid in batch:
            require((condition,rid) in indexed and (peer,rid) in indexed,'incomplete matched source cohort')
            row=indexed[condition,rid]; reference=indexed[peer,rid]
            rs=[]; ds=[]; es=[]; os=[]; hs=[]
            for stream,other in [('clean','corrupt'),('corrupt','clean')]:
                left=row['streams'][stream]
                right=row['streams'][other] if donor=='opposite' else reference['streams'][stream]
                validate_source_stream(left);validate_source_stream(right)
                if donor=='neutral' and condition in ('D','I'):
                    mapping=maps.get((condition,rid,stream),{})
                    require(mapping.get('supported') is True and mapping.get('donor_condition')==peer
                        and mapping.get('recipient_positions')==list(range(len(left['tokens'])))
                        and mapping.get('donor_positions')==list(range(len(right['tokens']))),'unsupported own neutral map')
                require(len(left['tokens'])==len(right['tokens']),'own donor token geometry differs')
                if donor=='opposite':
                    require(left.get('layout') is not None and left['layout']==right.get('layout'),'opposite designation role map differs')
                rs.append(left['tokens']); ds.append(right['tokens'])
                os.append(left.get('opposite_token',row.get('opposite_token')))
                hs.append(left.get('honest_token',row.get('honest_token')))
                es.append(left.get('expected_token',row.get('expected_token')))
            recipients.append(rs); donors.append(ds); opposite.append(os); honest.append(hs); expected.append(es)
        width=max(len(s) for row in recipients for s in row)
        frozen=design.get('_mask_widths',{}).get(task,{}).get(condition,width)
        require(frozen>=width,'frozen physical width truncates actual source')
        width=frozen
        lengths=torch.tensor([[len(s) for s in row] for row in recipients],device=device)
        pad=lambda data:torch.tensor([[s+[0]*(width-len(s)) for s in row] for row in data],device=device)
        payload=dict(input_ids=pad(recipients),neutral_input_ids=pad(donors),
            attention_mask=torch.arange(width,device=device)[None,None,:]<lengths[:,:,None],
            opposite_ids=torch.tensor(opposite,device=device),honest_ids=torch.tensor(honest,device=device),
            expected_ids=torch.tensor(expected,device=device),condition=condition,donor_convention=donor)
        chunks.append(core.MaskChunk(tuple(batch),torch.zeros(len(batch),2,device=device),None,payload,lengths,split=split))
    require(chunks,'empty matched source cohort')
    return chunks


def validation_gates(rows,*,epsilon):
    """A1 ratio-of-means, then H/F/IOI full-vocabulary accuracy gates."""
    conditions=('D','I','H','F','user_neutral','IOI')
    require(all(any(r['condition']==c for r in rows) for c in conditions),'incomplete validation conditions')
    mechanism_keys=[{(r['instance_id'],r['stream']) for r in rows if r['condition']==c} for c in ('D','I','H','F','user_neutral')]
    require(all(keys==mechanism_keys[0] for keys in mechanism_keys),'changed validation condition membership/streams')
    require(all({s for rid,s in mechanism_keys[0] if rid==instance}=={'clean','corrupt'} for instance in {rid for rid,s in mechanism_keys[0]}),'paired validation streams required')
    means={}
    for c in conditions:
        values=[r for r in rows if r['condition']==c]
        require(len({(r['instance_id'],r['stream']) for r in values})==len(values),'duplicate validation rows')
        fields=('intact_margin','patched_margin','intact_accuracy','patched_accuracy')
        require(all(math.isfinite(r[f]) for r in values for f in fields),'nonfinite validation result')
        means[c]={f:sum(r[f] for r in values)/len(values) for f in fields}
    result={'means':means}
    for condition,neutral in [('D','H'),('I','user_neutral')]:
        gap=means[condition]['intact_margin']-means[neutral]['intact_margin']
        require(gap>epsilon,'validation gap is nonpositive/epsilon-small')
        for stream in ('clean','corrupt'):
            stream_values={c:[r['intact_margin'] for r in rows if r['condition']==c and r['stream']==stream] for c in (condition,neutral)}
            stream_gap=sum(stream_values[condition])/len(stream_values[condition])-sum(stream_values[neutral])/len(stream_values[neutral])
            require(stream_gap>epsilon,'validation per-stream gap is nonpositive/epsilon-small')
        result[condition+'_fraction']=(means[condition]['intact_margin']-means[condition]['patched_margin'])/gap
    result['collateral']={c:abs(means[c]['patched_accuracy']-means[c]['intact_accuracy']) for c in ('H','F','IOI')}
    result['eligible']=bool(result['D_fraction']>=.5 and result['I_fraction']<.25 and all(v<.05-1e-12 for v in result['collateral'].values()))
    return result


def _single_logits(model,ids,mask,*,return_native=False):
    saved=[]
    handle=model.model.norm.register_forward_pre_hook(lambda module,args:saved.append(args[0]))
    try:
        output=model(input_ids=ids,attention_mask=mask,use_cache=False)
        positions=torch.arange(ids.shape[-1],device=ids.device).expand_as(ids).masked_fill(~mask.bool(),-1).max(-1).values
        from component_analysis.a3_native import differentiable_readout
        index=torch.arange(len(ids),device=ids.device)
        logits=differentiable_readout(model,saved[0][index,positions])
        return (logits,output.logits[index,positions]) if return_native else logits
    finally: handle.remove()


def exported_forward(model,chunk,removed,*,operation='interchange',mean_bank=None,return_native=False):
    """Independent single-stream native hooks; no gate forward defines removal."""
    p=chunk.payload; n,streams,width=p['input_ids'].shape
    valid=p['attention_mask'].bool();counts=valid.sum(-1)
    require(torch.equal(valid,torch.arange(width,device=valid.device)[None,None,:]<counts[:,:,None]),'native mask driver requires canonical right padding')
    ids=p['input_ids'].reshape(-1,width); neutral=p['neutral_input_ids'].reshape(-1,width);mask=p['attention_mask'].reshape(-1,width)
    require(operation in ('interchange','zero','h_mean'),'unsupported exported operation')
    geometry=actual_model_geometry(model)
    removed=_bank_keys(removed,geometry)
    if operation=='h_mean':
        require(isinstance(mean_bank,dict) and mean_bank,'missing typed H bank for export')
        keys=_bank_keys(list(mean_bank),geometry)
        require(set(removed)<=set(keys),'missing typed bank support for export')
        for key,value in mean_bank.items():_bank_vector(value,key,geometry,dtype=next(model.parameters()).dtype)
    donors={};handles=[]
    head_width=model.config.hidden_size//model.config.num_attention_heads
    try:
        if operation=='interchange':
            for key in removed:
                kind,layer,index=key; block=model.model.layers[layer]
                if kind=='head':
                    def capture(module,args,key=key,index=index):donors[key]=args[0][...,index*head_width:(index+1)*head_width].detach().clone()
                    handles.append(block.attn.original_attention.o_proj.register_forward_pre_hook(capture))
                elif kind=='mlp':
                    def capture(module,args,out,key=key):donors[key]=out.detach().clone()
                    handles.append(block.mlp.register_forward_hook(capture))
                else: raise ValueError('only typed heads/whole MLPs can be exported')
            _single_logits(model,neutral,mask)
            for h in handles:h.remove()
            handles=[]
        for key in removed:
            kind,layer,index=key; block=model.model.layers[layer]
            def replacement(original,key=key):
                if operation=='interchange': return donors[key]
                if operation=='zero': return torch.zeros_like(original)
                require(mean_bank is not None and key in mean_bank,'missing frozen H mean for export')
                value=_bank_vector(mean_bank[key],key,geometry,dtype=original.dtype).to(original.device)
                require(value.numel()==original.shape[-1],'bank vector differs from actual native contribution width')
                return value.reshape(1,1,value.numel()).expand_as(original)
            if kind=='head':
                def patch(module,args,index=index,replacement=replacement):
                    value=args[0].clone(); value[...,index*head_width:(index+1)*head_width]=replacement(value[...,index*head_width:(index+1)*head_width]);return (value,)
                handles.append(block.attn.original_attention.o_proj.register_forward_pre_hook(patch))
            else:
                def patch(module,args,out,replacement=replacement):return replacement(out)
                handles.append(block.mlp.register_forward_hook(patch))
        result=_single_logits(model,ids,mask,return_native=return_native)
        return tuple(t.reshape(n,streams,-1) for t in result) if return_native else result.reshape(n,streams,-1)
    finally:
        for h in handles:h.remove()


def score_chunks(model,chunks,removed,*,operation='interchange',mean_bank=None):
    records=[]
    with binary_mode(model,[]),torch.no_grad():
        for chunk in chunks:
            n,streams,width=chunk.payload['input_ids'].shape
            base,native_base=_single_logits(model,chunk.payload['input_ids'].reshape(-1,width),chunk.payload['attention_mask'].reshape(-1,width),return_native=True)
            base=base.reshape(n,streams,-1);native_base=native_base.reshape(n,streams,-1)
            patched,native_patched=exported_forward(model,chunk,removed,operation=operation,mean_bank=mean_bank,return_native=True)
            for i,rid in enumerate(chunk.ids):
                for s,stream in enumerate(('clean','corrupt')):
                    opposite=int(chunk.payload['opposite_ids'][i,s]);honest=int(chunk.payload['honest_ids'][i,s]);expected=int(chunk.payload['expected_ids'][i,s])
                    record=dict(instance_id=rid,stream=stream,condition=chunk.payload['condition'],split=chunk.split,
                        expected_token=expected,opposite_token=opposite,honest_token=honest)
                    for name,logits in [('intact',base),('patched',patched)]:
                        record[name+'_margin']=float(logits[i,s,opposite]-logits[i,s,honest])
                        record[name+'_accuracy']=float(int(logits[i,s].argmax())==expected)
                        record[name+'_target_choice']=float(logits[i,s,opposite]>logits[i,s,honest])
                        sign=1 if expected==opposite else -1
                        record[name+'_raw_margin']=record[name+'_margin']*sign
                        record[name+'_argmax']=int(logits[i,s].argmax())
                        record[name+'_binary_win']=float(record[name+'_raw_margin']>0)
                        if 'choice_tokens' in chunk.payload:
                            choices=chunk.payload['choice_tokens'];competitors=[t for t in choices if t!=expected]
                            record[name+'_choice_margin']=float(logits[i,s,expected]-logits[i,s,competitors].max())
                            record[name+'_choice_correct']=float(max(choices,key=lambda t:float(logits[i,s,t]))==expected)
                    for name,logits in [('intact',native_base),('patched',native_patched)]:
                        record[name+'_native_margin']=float(logits[i,s,opposite].float()-logits[i,s,honest].float())
                        record[name+'_native_accuracy']=float(int(logits[i,s].argmax())==expected)
                        record[name+'_native_argmax']=int(logits[i,s].argmax())
                    records.append(record)
    return records


def new30_reference():
    """Read only the PRIMARY archived JSON lineage; never open checkpoint files."""
    primary=Path('/projects/beto/swong2/Alignment/Deception-Circuit')
    study=primary/'outputs/_studies/selective-deception/study'
    receipt=study/'sparse-optimization-v4/comparison/selection-receipt.json'
    if not receipt.is_file(): return dict(status='missing_comparison',reason='New30 selection receipt unavailable')
    source=json.loads(receipt.read_text());matches=[m for m in source['masks'] if m['label']=='new-allW30']
    require(len(matches)==1,'ambiguous New30 selection receipt')
    selected=matches[0];proposal=selected['source_proposal']
    require(proposal['run']=='all-W-init10' and proposal['update']==832 and selected['selection_tier']=='WT_only','changed New30 ancestry')
    def resolve(path):
        marker='selective-deception/'
        require(marker in path,'New30 reference outside archived selective study')
        actual=(study/path.split(marker,1)[1]).resolve()
        require(actual.is_relative_to(study.resolve()),'New30 reference escapes archive')
        return actual
    files={str(receipt.resolve()):common.file_hash(receipt)}; values={}
    links={'heads':selected['head_list']}
    for name in ('export','manifest','run_identity'):
        links[name]=dict(path=proposal[name+'_path'],sha256=proposal[name+'_sha256'])
    for name,link in links.items():
        path=resolve(link['path'])
        if not path.is_file():return dict(status='missing_comparison',reason='missing New30 '+name,files=files)
        require(path.suffix=='.json' and common.file_hash(path)==link['sha256'],'changed New30 linked '+name)
        files[str(path)]=link['sha256'];values[name]=json.loads(path.read_text())
    removed=sorted(('head',int(layer),int(head)) for layer,head in values['heads']['removed_heads'])
    require(len(removed)==30 and len(set(removed))==30,'invalid New30 frozen head list')
    return dict(status='available',removed=[list(k) for k in removed],files=files,
        ancestry=dict(run=proposal['run'],update=proposal['update'],selection_tier=selected['selection_tier'],
            search_universe='all query heads',training='SDR all-query-head ancestry; WT-only preservation',
            checkpoint_sha256=proposal['checkpoint_sha256']),comparison='same permitted A1 rows only; no retraining or closed assay')


def mask_code_hashes():
    root=Path(__file__).resolve().parents[1]
    paths=['component_analysis/a3_mask_pipeline.py','component_analysis/a3_source_validation.py','component_analysis/a3_mask_workload.py',
        'component_analysis/a3_mask.py','component_analysis/a3_native.py','models/llama_node.py','models/_compat.py','l0.py',
        'scripts/jobs/specificity_a3_mask.sh','scripts/cluster/delta.env','scripts/cluster/bridges2.env',
        'component_analysis/a3_direction_runtime.py',
        'component_analysis/a3_direction_artifacts.py','component_analysis/a3_direction_workload.py',
        'component_analysis/a3_design.py','component_analysis/a3_pipeline.py','component_analysis/ladder_pipeline.py',
        'component_analysis/ladder_design.py','component_analysis/ladder_tasks.py','component_analysis/ladder_metrics.py',
        'dataset/user_inversion_pipeline.py']
    result={str(root/p):common.file_hash(root/p) for p in paths}
    import sys
    executable=Path(sys.executable).resolve()
    result[str(executable)]=common.file_hash(executable)
    import os
    launch=os.environ.get('SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE')
    if launch:
        path=Path(launch).resolve();require(path.is_file(),'missing explicit wrapper interpreter/launcher')
        result[str(path)]=common.file_hash(path)
    return result


def prepare_mask(design_path,*,commit,chunk_size,registry_paths,root_bundle=None):
    from component_analysis import a3_pipeline,a3_direction_artifacts as artifacts,ladder_pipeline as ladder
    design=ladder.read_artifact(design_path)
    require(design.get('kind')=='specificity_ladder_a3_design' and not design.get('injected'),'canonical non-injected A3 design required')
    require(design['direction_protocol']['commit']==commit,'canonical design source differs from mask execution commit')
    artifacts.validate_live(design,design['direction_protocol'],registry_paths=registry_paths)
    evidence=design['parent_evidence'];parent,selected,current=a3_pipeline.load_a1_parents(evidence['prepared_path'],evidence['selected_path'])
    require(current==evidence,'changed A1 parent/completion evidence')
    require(parent['commit']=='5f450dc93dac707af649dee8c8ca60888b2831db','historical A1 design is not current audited parent')
    require(len(design['ioi_validation'])==100 and len(design['utility']['ioi'])==100 and len(design['utility']['mmlu'])==32,
        'unchanged full utility cohorts required')
    candidates=sorted(set(map(tuple,selected['groups']['far_v2']['full']))|{('head',17,i) for i in range(24,28)})
    require(all(k=='head' and 0<=l<32 and 0<=i<32 or k=='mlp' and 0<=l<32 and i==0 for k,l,i in candidates),'invalid typed candidate universe')
    root=Path(__file__).resolve().parents[1]
    ruling=root/'docs/research/specificity-ladder/a3-mask-operational-ruling.json'
    rule=json.loads(ruling.read_text())
    pilot_ruling=root/'docs/research/specificity-ladder/a3-mask-pilot-ruling.json'
    pilot_rule=json.loads(pilot_ruling.read_text())
    require(pilot_rule['parent_ruling_file_sha256']==common.file_hash(ruling),'pilot ruling parent bytes differ')
    require(rule['kind']=='a3_mask_operational_ruling_v1' and rule['validation']['mechanism_donor']=='same condition opposite designation'
        and rule['random_controls']['match_counts_separately']==['head','whole_mlp'],'unsupported operational root ruling')
    for task,spec in design['tasks'].items():
        require(len(spec['assessment_ids'])==100,'unchanged A1 assessment100 required')
        cohorts=[set(spec[k]) for k in ('fit_ids','selection_ids','assessment_ids')]
        require(not (cohorts[0]&cohorts[1] or cohorts[0]&cohorts[2] or cohorts[1]&cohorts[2]),'split collision')
    # Validate actual adapters without model/weights before freezing the contract.
    for condition in ('D','I'):
        source_chunks(design,'far_v2','train',condition,chunk_size=chunk_size,device='cpu')
        source_chunks(design,'far_v2','validation',condition,chunk_size=chunk_size,device='cpu',fitting=False)
    from component_analysis.a3_direction_runtime import read_object,object_reference
    require(root_bundle is not None,'completed root mask execution bundle required')
    root_settings=read_object(root_bundle)
    require(root_settings.get('kind')=='a3_mask_root_execution_bundle_v1' and root_settings.get('commit')==commit
        and root_settings.get('design_file_sha256')==common.file_hash(design_path),'source-bound root mask bundle required')
    profile=root_settings['numeric_profile']
    require(profile['model']==parent['model'] and profile['model_revision']==parent['model_revision']
        and profile['tokenizer_revision']==parent['tokenizer_revision'] and profile['dtype']=='bfloat16'
        and profile['backend'] in ('eager','sdpa') and profile['hardware']=='H200','explicit pinned native mask numeric profile required')
    domains=hbank_sources(parent,selected)
    _protect_bank_sources(design,parent,domains,registry_paths)
    bank_rows={t:[r for r in parent['rows'][t]['H'] if r['instance_id'] in set(domain['ids'])] for t,domain in domains.items()}
    widths=execution_widths(design,hbank_rows=bank_rows)
    require(root_settings.get('padding_policy')=='max_profile_source_length_plus_one_masked','root bundle must freeze the right-padding policy')
    require(profile.get('chunk_size')==chunk_size and profile.get('vocab_size')==128256,'explicit native batch/vocabulary profile required')
    identity=dict(model_geometry=copy.deepcopy(NATIVE_BANK_GEOMETRY),commit=commit,design_path=str(Path(design_path).resolve()),design_file_sha256=common.file_hash(design_path),
        design_sha256=ladder.design._hash(design),a1_parent_evidence=copy.deepcopy(evidence),
        code_hashes=mask_code_hashes(),operational_ruling_path=str(ruling),operational_ruling_sha256=common.file_hash(ruling),
        pilot_ruling_path=str(pilot_ruling),pilot_ruling_sha256=common.file_hash(pilot_ruling),
        numeric_profile=copy.deepcopy(profile),physical_widths=copy.deepcopy(widths),root_bundle_reference=object_reference(root_bundle))
    prepared=dict(kind='a3_mask_prepared_v1',identity=identity,candidates=[list(k) for k in candidates],chunk_size=chunk_size,
        seeds=[42,1,123],arms=['constrained','unconstrained'],updates=200,validation_every=20,
        validation_donors='primary opposite designation; IOI frozen item swap',root_ruling=rule,
        random_controls=dict(count=19,typed=True,seed_offset=20000,reset_per_arm=True,retain_duplicate_subsets=True),
        timing_protocol=dict(purpose='validation_timing',source_split='validation',
            update_ids=copy.deepcopy(design['tasks']['far_v2']['selection_ids']),
            checkpoint_validation_ids=copy.deepcopy(design['tasks']['far_v2']['selection_ids']),
            crossed_ids={t:copy.deepcopy(v['selection_ids'][:100]) for t,v in design['tasks'].items()},
            policy='first min(100, eligible validation count); all update/checkpoint validation rows retained; no outcomes used'),
        new30=new30_reference(),hbank_sources=domains,widths=widths,injected=False,status='prepared_cpu_only',execution_authorized=False)
    identity['mask_protocol_sha256']=digest(mask_protocol(prepared))
    return prepared


def _validate_mask_source(prepared,args,inventory=None,*,design=None,extra_rows=None):
    from component_analysis import a3_direction_runtime as authority,a3_direction_artifacts as artifacts,ladder_pipeline as ladder
    from component_analysis import a3_mask_workload as workload
    require(prepared.get('kind')=='a3_mask_prepared_v1' and prepared.get('injected') is False,'canonical mask preparation required')
    identity=prepared['identity']
    require(identity['mask_protocol_sha256']==digest(mask_protocol(prepared)),'changed frozen mask scientific/operational protocol')
    require(prepared['new30']==new30_reference(),'changed actual New30 lineage or frozen node list')
    require(args.commit==identity['commit'],'changed mask source commit')
    require(common.file_hash(identity['design_path'])==identity['design_file_sha256'],'changed canonical A3 design file')
    require(identity['code_hashes']==mask_code_hashes(),'changed mask source closure')
    require(common.file_hash(identity['operational_ruling_path'])==identity['operational_ruling_sha256'],'changed root ruling')
    require(common.file_hash(identity['pilot_ruling_path'])==identity['pilot_ruling_sha256'],'changed pilot context ruling')
    if design is None:design=ladder.read_artifact(identity['design_path'])
    evidence=artifacts.validate_live(design,design['direction_protocol'],registry_paths=args.registry)
    from component_analysis.a3_pipeline import load_a1_parents
    parent,selected,_=load_a1_parents(design['parent_evidence']['prepared_path'],design['parent_evidence']['selected_path'])
    require(hbank_sources(parent,selected)==prepared['hbank_sources'],'changed original H-bank source domains')
    evidence['H_bank_protection']=_protect_bank_sources(design,parent,prepared['hbank_sources'],args.registry)
    bank_rows={t:[r for r in parent['rows'][t]['H'] if r['instance_id'] in set(domain['ids'])] for t,domain in prepared['hbank_sources'].items()}
    require(prepared['widths']==identity['physical_widths']==execution_widths(design,hbank_rows=bank_rows),'changed actual source/donor physical profile')
    if extra_rows is not None:extra_rows.update(bank_rows)
    require(authority.object_reference(identity['root_bundle_reference']['path'])==identity['root_bundle_reference'],'changed completed root mask bundle')
    for path,sha in prepared['new30'].get('files',{}).items():require(common.file_hash(path)==sha,'changed New30 frozen reference')
    if inventory is not None:
        if getattr(args,'_mask_authority_context',None) is None:
            workload.validate_inventory(inventory)
            expected=workload.build_inventory(design,identity=identity,chunk_size=prepared['chunk_size'],
                finish_reserve_seconds=inventory['finish_reserve_seconds'],hbank_sources=prepared['hbank_sources'],
                stage=inventory['stage'],widths=prepared['widths'],new30=prepared['new30'])
            require(inventory['inventory_sha256']==expected['inventory_sha256'],'runtime inventory differs from complete canonical mask workload')
        evidence['reservation']=mask_reservation(args,inventory)
    return execution_design(design,prepared['widths']),evidence



def _make_mask_source_state(prepared,args):
    from component_analysis import a3_direction_runtime as authority,ladder_pipeline as ladder
    started=getattr(args,'_mask_source_started',None)
    if started is None:started=time.perf_counter()
    if prepared.get('injected') is not False:return None
    path=getattr(args,'prepared',None)
    if path is None and getattr(args,'work_dir',None):path=Path(args.work_dir)/'prepared'
    if path is None or not (Path(path)/'COMPLETE.json').is_file():return None
    # Preserve the original early rejection before ancestry discovery.
    require(prepared.get('kind')=='a3_mask_prepared_v1','canonical mask preparation required')
    actual_design=prepared['identity']['design_path']
    lexical=getattr(args,'design',None) or actual_design
    require(Path(lexical).resolve()==Path(actual_design).resolve(),'mask canonical source path differs')
    design=ladder.read_artifact(lexical)
    def dependencies(owned):
        identity=owned['prepared']['identity']
        paths=list(mask_code_hashes())+[identity['operational_ruling_path'],identity['pilot_ruling_path'],identity['root_bundle_reference']['path']]
        import os,sys
        paths.append(sys.executable)
        if os.environ.get('SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE'):paths.append(os.environ['SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE'])
        source,missing,watched=source_validation.source_dependencies(owned['design'],root=Path(__file__).resolve().parents[1],owner_paths=paths)
        archive,absent=source_validation.new30_dependencies()
        return source+archive,missing+absent,watched
    def semantic(owned):
        extra={}
        _,evidence=_validate_mask_source(owned['prepared'],args,design=owned['design'],extra_rows=extra)
        return evidence,extra
    return source_validation.build_state(owner='mask',originals={'prepared':prepared,'design':design},
        artifacts={'prepared':('object',path),'design':('artifact',lexical)},dependencies=dependencies,semantic=semantic,
        registry_paths=args.registry,scope=_mask_source_scope(args),started=started,owner_seal=_SOURCE_VALIDATOR_SEAL,
        precheck=lambda owned:require(owned['prepared']['identity']['mask_protocol_sha256']==digest(mask_protocol(owned['prepared'])),'changed frozen mask scientific/operational protocol'))


def _mask_source_scope(args):
    import os,sys
    result={key:str(getattr(args,key,None)) for key in ('commit','stage','seed','arm','task','group','chunk_size')}
    result.update({key:(str(Path(getattr(args,key)).absolute()) if getattr(args,key,None) is not None else None) for key in ('design','prepared','work_dir')})
    launch=os.environ.get('SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE')
    result.update(interpreter=str(Path(sys.executable).absolute()),launcher=str(Path(launch).absolute()) if launch else None)
    return result


def _live_mask(prepared,args,inventory=None):
    from component_analysis import a3_mask_workload as workload
    state=getattr(args,'_mask_source_context',None)
    if state is None:
        state=_make_mask_source_state(prepared,args)
        if state is None:return _validate_mask_source(prepared,args,inventory)
        args._mask_source_context=state
    source_validation.checked_state(state,'mask',_SOURCE_VALIDATOR_SEAL)
    evidence=state.refresh(owner='mask',bound_inputs={'prepared':prepared},registry_paths=args.registry,scope=_mask_source_scope(args))
    design=execution_design(state.view('design'),state.view('prepared')['widths'])
    if inventory is not None:
        if getattr(args,'_mask_authority_context',None) is None:
            workload.validate_inventory(inventory)
            expected=workload.build_inventory(design,identity=prepared['identity'],chunk_size=prepared['chunk_size'],
                finish_reserve_seconds=inventory['finish_reserve_seconds'],hbank_sources=prepared['hbank_sources'],
                stage=inventory['stage'],widths=prepared['widths'],new30=prepared['new30'])
            require(inventory['inventory_sha256']==expected['inventory_sha256'],'runtime inventory differs from complete canonical mask workload')
        evidence['reservation']=mask_reservation(args,inventory)
    return design,evidence


def _source_startup_seconds(seconds,args):
    state=getattr(args,'_mask_source_context',None)
    if state is not None:source_validation.checked_state(state,'mask',_SOURCE_VALIDATOR_SEAL)
    return source_validation.startup_seconds(seconds,state)


def utility_chunks(rows,maps,*,device,task,padded_width=None):
    """Utility readouts use their frozen task map, never mechanism label defaults."""
    mapped={m['recipient_id']:m for m in maps};result=[]
    for row in rows:
        clean=row['streams']['clean'];validate_source_stream(clean)
        rid=row['instance_id'];left=clean['tokens']
        if task=='ioi':
            mapping=mapped.get(rid,{})
            require(mapping.get('supported') and mapping.get('donor_stream')=='corrupt','unsupported frozen IOI map')
            validate_source_stream(row['streams']['corrupt'])
            right=row['streams']['corrupt']['tokens']
            require(mapping['recipient_positions']==list(range(len(left))) and mapping['donor_positions']==list(range(len(right))),
                'non-full IOI item-swap map')
        else:right=left
        require(len(left)==len(right),'utility donor geometry differs')
        width=padded_width or len(left)
        require(width>=len(left),'frozen utility width truncates source/donor')
        ids=torch.tensor([[left+[0]*(width-len(left))]*2],device=device)
        donor=torch.tensor([[right+[0]*(width-len(right))]*2],device=device)
        mask=torch.tensor([[[1]*len(left)+[0]*(width-len(left))]*2],device=device)
        payload=dict(input_ids=ids,neutral_input_ids=donor,attention_mask=mask,
            opposite_ids=torch.full((1,2),row['opposite_token'],device=device),
            honest_ids=torch.full((1,2),row['honest_token'],device=device),
            expected_ids=torch.full((1,2),row['expected_token'],device=device),condition='IOI' if task=='ioi' else 'MMLU')
        if task=='mmlu':payload['choice_tokens']=list(row['choice_tokens'])
        result.append(core.MaskChunk((rid,),torch.zeros(1,2,device=device),None,payload,torch.full((1,2),len(left),device=device),
            split=row.get('analysis_split',row['split'])))
    return result


def evaluate_validation(model,design,removed,*,chunk_size,epsilon):
    device=next(model.parameters()).device;rows=[];controls=[];errors=[]
    collections=[]
    for condition in ('D','I','H','F','user_neutral'):
        collections.append(source_chunks(design,'far_v2','validation',condition,chunk_size=chunk_size,
            device=device,fitting=False,donor='opposite'))
    collections.append(utility_chunks(design['ioi_validation'],design['ioi_validation_maps'],device=device,task='ioi',
        padded_width=design.get('_mask_widths',{}).get('ioi')))
    for chunks in collections:
        for chunk in chunks:
            records=score_chunks(model,[chunk],removed)
            # Replay uses the actual exported intervention path with intact same-stream donors.
            replay=copy.deepcopy(chunk);replay.payload['neutral_input_ids']=replay.payload['input_ids'].clone()
            replay_rows=score_chunks(model,[replay],removed)
            for record in replay_rows:
                error=abs(record['intact_margin']-record['patched_margin']);errors.append(error)
                require(error<=1e-5,'validation self-replay failed')
            controls.append(_primary_positive(model,chunk))
            if chunk.payload['condition']=='IOI':records=[r for r in records if r['stream']=='clean']
            rows.extend(records)
    validation_epsilon=max(1e-6,10*max(errors,default=0))
    result=validation_gates(rows,epsilon=validation_epsilon)
    result.update(split='validation',removed=[list(k) for k in removed],rows=rows,positive_controls=controls,
        epsilon=validation_epsilon,fit_epsilon=epsilon,self_replay_margin_error=max(errors,default=0),
        donor_convention='A1 opposite designation / frozen IOI swap')
    return result


def intact_targets(model,ds,ins,hs):
    """Detached targets and replay-derived A1 epsilon from the actual native path."""
    errors=[]
    with binary_mode(model,[]),torch.no_grad():
        h=[]
        for chunks,condition in [(ds,'D'),(ins,'I'),(hs,'H')]:
            for chunk in chunks:
                first=core.native_chunk_forward(model,chunk)
                second=core.native_chunk_forward(model,chunk)
                errors.append(float((first['margin']-second['margin']).abs().max()))
                chunk.baseline_margin=first['margin'].detach().clone()
                chunk.baseline_logits=first['logits'].detach().clone() if condition=='I' else None
                if condition=='H':h.append(first['margin'].detach().double())
    epsilon=max(1e-6,10*max(errors,default=0))
    gap=torch.cat([c.baseline_margin.double() for c in ds]).mean()-torch.cat(h).mean()
    core._gap(gap,epsilon)
    return gap.detach(),epsilon,dict(self_replay_margin_error=max(errors,default=0),g_d_fit=float(gap),epsilon=epsilon)


def _publish_boundary(path,state,driver):
    if Path(path).exists():
        previous,metadata=_read_boundary(path)
        require(core._fingerprint(previous)==core._fingerprint(state) and metadata==driver,'existing optimizer boundary differs from exact resumed computation')
        return
    def writer(root):
        write_checkpoint(root/'core',state)
        (root/'driver.json').write_text(json.dumps(driver,sort_keys=True,allow_nan=False)+'\n')
        files={str(p.relative_to(root)):common.file_hash(p) for p in root.rglob('*') if p.is_file()}
        (root/'COMPLETE.json').write_text(json.dumps(files,sort_keys=True)+'\n')
    common.publish(Path(path),writer)


def _read_boundary(path):
    path=Path(path);files=json.loads((path/'COMPLETE.json').read_text())
    actual={str(p.relative_to(path)):common.file_hash(p) for p in path.rglob('*') if p.is_file() and p!=path/'COMPLETE.json'}
    require(files==actual,'incomplete/changed atomic mask boundary')
    return read_checkpoint(path/'core'),json.loads((path/'driver.json').read_text())


def train_constrained(model,design,prepared,*,seed,arm,checkpoint_dir,guard,resume=None):
    """Both arms complete200 updates; selection stays frozen before assessment."""
    require(not getattr(model,'_a3_disposable_timing_model',False),'disposable validation timing model cannot fit scientific masks')
    design=execution_design(design,prepared.get('widths',{}))
    require(seed in (42,1,123) and arm in ('constrained','unconstrained'),'unregistered mask run')
    require(prepared['updates']==200 and prepared['validation_every']==20,'changed fixed mask schedule')
    started=time.perf_counter();initial_guard=guard()
    support=core.configure_candidates(model,prepared['candidates']);device=next(model.parameters()).device
    args=dict(chunk_size=prepared['chunk_size'],device=device)
    ds=source_chunks(design,'far_v2','train','D',**args)
    ins=source_chunks(design,'far_v2','train','I',**args)
    hs=source_chunks(design,'far_v2','train','H',**args)
    gap,epsilon,replay=intact_targets(model,ds,ins,hs)
    identity=dict(source=prepared['identity'],seed=seed,arm=arm,candidates=prepared['candidates'],
        chunk_identity=core._chunks_identity(ds,ins),g_d_fit=float(gap),epsilon=epsilon)
    optimizer=torch.optim.Adam(support.parameters(),lr=.01)
    torch.manual_seed(seed)
    if torch.cuda.is_available():torch.cuda.manual_seed_all(seed)
    pristine_base=core._base_identity(model)
    start=0;validations=[];root=Path(checkpoint_dir)
    if resume:
        guard();state,driver=_read_boundary(resume)
        require(driver['identity']==identity,'changed resumed driver identity')
        start=core.restore_checkpoint(state,model,support,optimizer,ds,ins,identity=identity)
        validations=driver['validations'];require([v['update'] for v in validations]==list(range(20,start+1,20)),'resume validation history incomplete')
    require(0<=start<=200,'invalid resume boundary')
    for update in range(start+1,201):
        guard()
        core.streamed_update(model,support,optimizer,ds,ins,core.native_chunk_forward,
            g_d_fit=gap,epsilon=epsilon,identity=identity,constrained=arm=='constrained')
        if update%20==0:
            removed=core.export_removal_mask(model,provenance=identity)['removed']
            parity=binary_parity(model,ds+ins)
            validation=evaluate_validation(model,design,removed,chunk_size=prepared['chunk_size'],epsilon=epsilon)
            validation.update(update=update,parity=parity)
            from component_analysis.a3_direction_runtime import publish_object,object_reference
            validation_path=root/'validation'/f'update-{update:06d}'
            publish_validation(validation_path,dict(kind='a3_mask_validation_v1',identity=identity,result=validation))
            record={k:v for k,v in validation.items() if k not in ('rows','positive_controls')}
            record['rows_reference']=object_reference(validation_path)
            record['rows_sha256']=digest(validation['rows'])
            record['positive_controls_sha256']=digest(validation['positive_controls'])
            validations.append(record)
        checkpoint=core.make_checkpoint(model,support,optimizer,ds,ins,identity=identity,update=update)
        require(checkpoint['base']==pristine_base,'base weights/computation changed during mask fitting')
        _publish_boundary(root/f'update-{update:06d}',checkpoint,dict(identity=identity,validations=validations,replay=replay))
    selected=select_checkpoint(validations)
    selected_path=root/f"update-{selected['update']:06d}"
    state,_=_read_boundary(selected_path)
    core.restore_checkpoint(state,model,support,optimizer,ds,ins,identity=identity)
    exported=core.export_removal_mask(model,provenance=identity)
    require(exported['removed']==selected['removed'],'selected checkpoint export changed')
    result=dict(kind='a3_mask_selected_v1',identity=identity,completed_updates=200,selection=selected,
        checkpoint_path=str(selected_path.resolve()),checkpoint_sha256=common.file_hash(selected_path/'COMPLETE.json'),
        completed_checkpoint_path=str((root/'update-000200').resolve()),
        completed_checkpoint_sha256=common.file_hash(root/'update-000200'/'COMPLETE.json'),
        export=exported,random_controls=[[list(k) for k in row] for row in random_controls(prepared['candidates'],exported['removed'],seed=seed)],
        random_degeneracy=dict(unique_subsets=len({tuple(map(tuple,row)) for row in random_controls(prepared['candidates'],exported['removed'],seed=seed)}),
            empty_support=not exported['removed'],all_candidate_support=len(exported['removed'])==len(prepared['candidates']),
            type_counts={kind:sum(k[0]==kind for k in exported['removed']) for kind in ('head','mlp')},
            sample_count=19,duplicate_subsets_retained=True),
        assessment_accessed=False)
    result['run_manifest_reference']=publish_run_manifest(root/'run-manifests',prepared,stage='fit',
        evidence=dict(seed=seed,arm=arm,completed_updates=200,updates_this_invocation=200-start,
            n_train_ids=sum(len(c.ids) for c in ds),n_streams=2,validation_checkpoints=len(validations),
            baseline_replay_error=replay['self_replay_margin_error'],baseline_tolerance=1e-5,
            resumed_from=str(resume) if resume else None,initial_guard=initial_guard,final_guard=guard(),
            wall_seconds=time.perf_counter()-started))
    from component_analysis.a3_direction_runtime import publish_object
    publish_object(root/'selected',result)
    return result


def hbank_sources(parent,selected):
    """Reconstruct A1's exact source domain; no new H sample or assessment row."""
    domains={}
    for task,bank in selected['banks'].items():
        provenance=bank['provenance'];records=provenance['provenance']
        ids=sorted({entry['clean']['instance_id'] for entry in records})
        require(len(ids)==provenance['n_instances'],'H bank source identity count differs')
        indexed={r['instance_id']:r for r in parent['rows'][task]['H']}
        require(set(ids)<=set(indexed),'H bank source row absent in parent')
        rows=[indexed[rid] for rid in ids]
        require(all(r['split'] in ('train','validation') for r in rows),'assessment forbidden in H-bank source')
        tokens=sum(len(r['streams'][s]['tokens']) for r in rows for s in ('clean','corrupt'))
        require(tokens==provenance['n_tokens'],'original H-bank token-weighted source count differs')
        domains[task]=dict(ids=ids,rows_sha256=digest(rows),n_tokens=tokens)
    return domains


def collect_h_bank(model,rows,candidates,*,guard,padded_width=None):
    """Entire union recollected in one current profile; token-weighted both streams."""
    candidates=_bank_keys(candidates,actual_model_geometry(model));_bank_domain(rows)
    require(candidates,'empty typed H-bank support')
    sums={};n_tokens=0
    device=next(model.parameters()).device;head_width=model.config.hidden_size//model.config.num_attention_heads
    with binary_mode(model,[]),torch.no_grad():
        for row in rows:
            require(row['condition']=='H' and row['split'] in ('train','validation'),'non-H/assessment bank source rejected')
            for stream in ('clean','corrupt'):
                guard();validate_source_stream(row['streams'][stream])
                tokens=row['streams'][stream]['tokens'];width=padded_width or len(tokens)
                require(width>=len(tokens),'frozen bank width truncates source')
                ids=torch.tensor([tokens+[0]*(width-len(tokens))],device=device)
                mask=torch.tensor([[1]*len(tokens)+[0]*(width-len(tokens))],device=device);handles=[];captured={}
                try:
                    for key in candidates:
                        kind,layer,index=key;block=model.model.layers[layer]
                        if kind=='head':
                            def capture(module,args,key=key,index=index):captured[key]=args[0][...,index*head_width:(index+1)*head_width].detach()
                            handles.append(block.attn.original_attention.o_proj.register_forward_pre_hook(capture))
                        else:
                            def capture(module,args,out,key=key):captured[key]=out.detach()
                            handles.append(block.mlp.register_forward_hook(capture))
                    _single_logits(model,ids,mask)
                    require(set(captured)==set(candidates),'missing current native H bank captures')
                    for key,value in captured.items():
                        total=(value.double()*mask[...,None]).sum((0,1)).cpu()
                        sums[key]=sums.get(key,torch.zeros_like(total))+total
                    n_tokens+=int(mask.sum())
                finally:
                    for handle in handles:handle.remove()
    require(n_tokens>0,'empty H mean source domain')
    return dict(kind='a3_mask_H_bank_v1',values=[dict(key=list(k),value=(sums[k]/n_tokens).float().tolist()) for k in candidates],
        n_tokens=n_tokens,n_instances=len(rows),source_ids=[r['instance_id'] for r in rows],pooling='both streams; unpadded token-weighted mean',source_rows_sha256=digest(rows))


def assessment_groups(prepared,selections):
    """Freeze all six arms and typed random memberships before opening test rows."""
    require(len(selections)==6,'all six complete fitted mask runs required')
    expected={(seed,arm) for seed in (42,1,123) for arm in ('constrained','unconstrained')}
    seen=set();groups={'intact':[],'all_candidates':prepared['candidates']}
    for selected in selections:
        identity=selected['identity'];key=(identity['seed'],identity['arm'])
        require(key in expected and key not in seen and identity['source']==prepared['identity'],'changed/duplicate fitted source')
        require(read_run_manifest(selected['run_manifest_reference'])['identity']==prepared['identity'],'selected run manifest source differs')
        require(selected['kind']=='a3_mask_selected_v1' and selected['completed_updates']==200 and not selected['assessment_accessed'],
            'partial or assessment-selected mask cannot assess')
        path=Path(selected['checkpoint_path'])
        require(common.file_hash(path/'COMPLETE.json')==selected['checkpoint_sha256'],'changed selected checkpoint')
        state,driver=_read_boundary(path)
        require(state['purpose']=='scientific_training' and state['identity']==identity and driver['identity']==identity,'selected checkpoint source/purpose changed')
        chosen=select_checkpoint(frozen_validation_history(selected))
        require(chosen==selected['selection'] and chosen['removed']==selected['export']['removed'],'changed frozen selection policy/result')
        seed,arm=key;seen.add(key);groups[f'{arm}:{seed}:selected']=selected['export']['removed']
        randoms=random_controls(prepared['candidates'],selected['export']['removed'],seed=seed)
        require(selected['random_controls']==[[list(k) for k in row] for row in randoms],'changed fixed random memberships')
        for index,removed in enumerate(randoms):groups[f'{arm}:{seed}:random:{index}']=[list(k) for k in removed]
    if prepared['new30']['status']=='available':groups['New30']=prepared['new30']['removed']
    return groups


def _assessment_metadata(records,source_rows,*,task,group,removed,operation,donor_maps=None):
    indexed={r['instance_id']:r for r in source_rows};maps=donor_maps or {}
    for record in records:
        rid=record['instance_id'];source=indexed[rid]
        mapping=maps.get((source.get('condition',record['condition']),rid,record['stream']))
        record.update(task=task,group=group,group_members=copy.deepcopy(removed),operation=operation,
            intact_correct=record['intact_accuracy'],patched_correct=record['patched_accuracy'],
            pressure_id=source.get('pressure_text',source.get('pressure',source.get('pressure_id',rid))),
            supported=True,assay_valid=True,gate_valid=bool(removed) and operation not in ('empty','self_replay'),
            degenerate=not removed or operation in ('empty','self_replay'),donor_provenance=mapping,
            self_replay_margin_error=record.get('self_replay_margin_error',0.),source_provenance=dict(instance_id=rid,source_hash=source['source_hash'],split=source['split']))
        if mapping is not None:
            record.update(supported=mapping['supported'],gate_valid=record['gate_valid'] and mapping['gate_valid'],
                degenerate=record['degenerate'] or mapping['degenerate'])
    return records


def _primary_positive(model,chunk):
    p=chunk.payload;n,streams,width=p['input_ids'].shape
    result=positive_readout(model,p['input_ids'].reshape(-1,width),p['attention_mask'].reshape(-1,width),
        p['neutral_input_ids'].reshape(-1,width),p['attention_mask'].reshape(-1,width))
    result.update(instance_ids=list(chunk.ids),condition=p.get('condition'),source_split=chunk.split,
        streams=['clean','clean_execution_duplicate'] if p.get('condition') in ('IOI','MMLU') else ['clean','corrupt'],
        unpadded_lengths=chunk.token_counts.cpu().tolist(),operation='all_sender_readout_calibration')
    return result


def assess_group(model,design,prepared,*,task,name,removed,bank,parent,guard,split='test',purpose='assessment'):
    """All A1 crossed operations and utility floors on unchanged assessment rows."""
    from component_analysis.ladder_design import donor_plan
    require((split,purpose) in (('test','assessment'),('validation','validation_timing')),'wrong assessment/timing source purpose')
    require(task in design['tasks'] and (name!='New30' or task=='far_v2'),'unapproved reference transfer')
    device=next(model.parameters()).device; rows=[];controls=[]
    bank_values=validate_h_bank(bank,prepared,task=task,model=model,design=design,
        purpose='scientific_H_bank' if purpose=='assessment' else 'validation_timing')
    source_rows=design['access_rows'][task]
    assessment=set(design['tasks'][task]['assessment_ids' if split=='test' else 'selection_ids'])
    actual_sources=[r for r in source_rows if r['instance_id'] in assessment]
    for operation in ('item_swap','h_twin','zero','h_mean','self_replay','empty'):
        for condition in ('D','I','H','F','user_neutral'):
            guard()
            chunks=source_chunks(design,task,split,condition,chunk_size=1,device=device,fitting=False,
                donor='opposite' if operation=='item_swap' else 'neutral')
            mapping={}
            for chunk in chunks:
                source=next(r for r in actual_sources if r['condition']==condition and r['instance_id']==chunk.ids[0])
                maps=[donor_plan(source,source_rows,operation=operation,stream=stream,seed=1) for stream in ('clean','corrupt')]
                mapping.update({(condition,source['instance_id'],m['recipient_stream']):m for m in maps})
                if operation=='h_twin':
                    # A1 F can be unsupported; it is retained explicitly, with no invented score.
                    if not all(m['supported'] for m in maps):
                        for m in maps:rows.append(dict(task=task,group=name,group_members=removed,operation=operation,
                            instance_id=source['instance_id'],condition=condition,stream=m['recipient_stream'],supported=False,
                            assay_valid=False,gate_valid=False,degenerate=m['degenerate'],donor_provenance=m,status='blocked_unsupported_donor'))
                        continue
                    indexed={(r['condition'],r['instance_id']):r for r in source_rows}
                    replacements=[]
                    for m in maps:
                        donor=indexed[m['donor_condition'],m['donor_id']]['streams'][m['donor_stream']]['tokens']
                        require(m['recipient_positions']==m['donor_positions']==list(range(len(donor))),'partial A1 map needs explicit native position adapter')
                        replacements.append(donor)
                    width=chunk.payload['input_ids'].shape[-1]
                    require(all(len(t)<=width for t in replacements),'frozen width truncates H-twin donor')
                    chunk.payload['neutral_input_ids']=torch.tensor([[t+[0]*(width-len(t)) for t in replacements]],device=device)
                if operation=='self_replay':chunk.payload['neutral_input_ids']=chunk.payload['input_ids'].clone()
                active=[] if operation=='empty' else removed
                native_op=operation if operation in ('zero','h_mean') else 'interchange'
                records=score_chunks(model,[chunk],active,operation=native_op,mean_bank=bank_values)
                if operation=='self_replay':
                    require(all(abs(r['intact_margin']-r['patched_margin'])<=1e-5 for r in records),'assessment self-replay failed')
                    for r in records:r['self_replay_margin_error']=abs(r['intact_margin']-r['patched_margin'])
                rows.extend(_assessment_metadata(records,[source],task=task,group=name,removed=removed,operation=operation,donor_maps=mapping))
                if operation=='item_swap':controls.append(_primary_positive(model,chunk))
    for utility in ('ioi','mmlu'):
        sources=design['utility'][utility] if split=='test' else design[utility+'_validation']
        maps=design['utility'][utility+'_maps'] if split=='test' else design[utility+'_validation_maps']
        chunks=utility_chunks(sources,maps,device=device,task=utility,padded_width=design.get('_mask_widths',{}).get(utility))
        for operation in (('item_swap','zero','h_mean','self_replay','empty') if utility=='ioi' else ('zero','h_mean','self_replay','empty')):
            guard()
            for chunk in chunks:
                current=copy.deepcopy(chunk)
                if operation=='self_replay':current.payload['neutral_input_ids']=current.payload['input_ids'].clone()
                records=[r for r in score_chunks(model,[current],[] if operation=='empty' else removed,
                    operation=operation if operation in ('zero','h_mean') else 'interchange',mean_bank=bank_values) if r['stream']=='clean']
                rows.extend(_assessment_metadata(records,sources,task=utility,group=name,removed=removed,operation=operation))
                if utility=='ioi' and operation=='item_swap':controls.append(_primary_positive(model,current))
                if utility=='mmlu' and operation=='zero':
                    rid=current.ids[0];mapping=next(m for m in maps if m['recipient_id']==rid)
                    require(mapping['supported'],'unsupported frozen MMLU readout calibration')
                    donor_row=next(r for r in sources if r['instance_id']==mapping['donor_id'])
                    donor_tokens=donor_row['streams'][mapping['donor_stream']]['tokens']
                    width=current.payload['input_ids'].shape[-1]
                    require(width>=len(donor_tokens),'frozen MMLU positive profile truncates donor')
                    donor_ids=torch.tensor([donor_tokens+[0]*(width-len(donor_tokens))],device=device)
                    donor_mask=torch.tensor([[1]*len(donor_tokens)+[0]*(width-len(donor_tokens))],device=device)
                    recipient=current.payload['input_ids'][:,0];recipient_mask=current.payload['attention_mask'][:,0]
                    control=positive_readout(model,recipient,recipient_mask,donor_ids,donor_mask)
                    control.update(instance_ids=[rid],condition='MMLU',streams=['clean'],source_split=current.split,
                        donor_id=mapping['donor_id'],operation='all_sender_readout_calibration')
                    controls.append(control)
    expected_mechanism=len(assessment)*5*2*6
    require(len([r for r in rows if r['task']==task])==expected_mechanism,'incomplete mechanism crossed assessment')
    ioi_count=len(design['utility']['ioi'] if split=='test' else design['ioi_validation'])
    mmlu_count=len(design['utility']['mmlu'] if split=='test' else design['mmlu_validation'])
    require(design.get('injected') or ioi_count==100 and mmlu_count==32,'unchanged full original utility membership required')
    require(len([r for r in rows if r['task']=='ioi'])==ioi_count*5 and len([r for r in rows if r['task']=='mmlu'])==mmlu_count*4,
        'incomplete original utility rows/floors')
    return dict(kind='a3_mask_timing_assessment_group_v1' if purpose=='validation_timing' else 'a3_mask_assessment_group_v1',purpose=purpose,split=split,identity=prepared['identity'],task=task,group=name,removed=removed,rows=rows,
        positive_controls=controls,H_bank_identity=bank['identity'],new30_reference=prepared['new30'] if name=='New30' else {'status':'not_reference'},
        complete=True,expected_mechanism_rows=expected_mechanism)


def load_native_model(prepared):
    """Lazy, cached, revision-pinned native weights; only safetensors are accepted."""
    from models.llama_node import PrunableLlamaForCausalLM,PruningConfig,apply_pruning_wrappers
    profile=prepared['identity']['numeric_profile']
    require(torch.cuda.is_available(),'native production masks require reserved H200 CUDA device')
    require('H200' in torch.cuda.get_device_name(),'mask training/gradient execution requires H200')
    model=PrunableLlamaForCausalLM.from_pretrained(profile['model'],revision=profile['model_revision'],
        local_files_only=True,use_safetensors=True,torch_dtype=torch.bfloat16,attn_implementation=profile['backend'])
    require(model.config.num_hidden_layers==32 and model.config.num_attention_heads==32
        and model.config.num_key_value_heads==8 and model.config.hidden_size==4096 and model.config.intermediate_size==14336,
        'changed native Llama geometry')
    require(getattr(model.config,'_commit_hash',None)==profile['model_revision'],'loaded native model revision differs')
    require(model.config.vocab_size==profile['vocab_size'],'loaded native vocabulary differs')
    apply_pruning_wrappers(model,PruningConfig())
    return model.to('cuda').eval().requires_grad_(False)


def mask_pilot(model,design,prepared,*,output,guard,startup_seconds=0,injected=False,target_inventory=None,pilot_inventory=None,target_read_seconds=0):
    """Execute both real arms and every required adapter on validation sources only.

    Union-support inference measures a conservative workload envelope. Source,
    width, batch and backend reuse assumptions are explicit in the receipt.
    No timing checkpoint or model can enter scientific fitting/selection.
    """
    from component_analysis.a3_direction_runtime import publish_object
    require(bool(prepared.get('injected'))==bool(injected),'explicit injected pilot identity required')
    require(not getattr(model,'_a3_disposable_timing_model',False),'timing model cannot be reused')
    require(injected or target_inventory is not None,'completed exact full target inventory required for timing reuse')
    if target_inventory is not None:
        from component_analysis.a3_mask_workload import validate_inventory
        validate_inventory(target_inventory)
        require(target_inventory['identity']==prepared['identity'] and target_inventory['stage']=='full','pilot target inventory source/stage differs')
    model._a3_disposable_timing_model=True
    design=execution_design(design,prepared['widths'])
    device=next(model.parameters()).device
    require(injected or device.type=='cuda' and 'H200' in torch.cuda.get_device_name(),'production mask pilot requires reserved H200')
    measurements={};arms=[];guard_samples=[];base_identities=[];output=Path(output)
    guard_evidence=[]
    def guarded():
        before=time.perf_counter();value=guard();guard_samples.append(time.perf_counter()-before);guard_evidence.append(value);return value
    def measure(name,fn,*,rows=1,scope=None):
        if device.type=='cuda':torch.cuda.synchronize()
        guard_before=math.fsum(guard_samples)
        started=time.perf_counter();value=fn()
        if device.type=='cuda':torch.cuda.synchronize()
        elapsed=time.perf_counter()-started
        nested_guard_seconds=math.fsum(guard_samples)-guard_before
        record=dict(seconds=max(elapsed-nested_guard_seconds,1e-12),guard_seconds=nested_guard_seconds,rows=rows,numeric_profile=prepared['identity']['numeric_profile'],
            widths=prepared['widths'],source_split='validation',scope=scope or {})
        measurements.setdefault(name,[]).append(record)
        return value
    guarded()
    initial_proof_seconds=guard_samples[-1]
    if target_inventory is not None:
        # Price the complete target proof once, including serialization/structural validation.
        before=time.perf_counter()
        from component_analysis.a3_mask_workload import validate_inventory
        validate_inventory(target_inventory)
        frozen=frozenset(map(__import__('component_analysis.a3_direction_workload',fromlist=['_freeze'])._freeze,target_inventory['expected_keys']))
        require(frozen<=frozen,'target key proof failed')
        initial_proof_seconds=time.perf_counter()-before+target_read_seconds+max(guard_samples)
        del frozen
    core.configure_candidates(model,prepared['candidates'])
    measured_base=measure('base_proof',lambda:core._base_identity(model),scope={'full_intact_model_hash':True})
    for arm in ('constrained','unconstrained'):
        guarded();support=core.configure_candidates(model,prepared['candidates'])
        args=dict(chunk_size=prepared['chunk_size'],device=device,fitting=False)
        ds=source_chunks(design,'far_v2','validation','D',**args)
        ins=source_chunks(design,'far_v2','validation','I',**args)
        hs=source_chunks(design,'far_v2','validation','H',**args)
        gap,epsilon,replay=measure('targets',lambda:intact_targets(model,ds,ins,hs),rows=len(ds),scope={'arm':arm,'chunks':len(ds)})
        identity=dict(source=prepared['identity'],arm=arm,purpose='validation_timing',pilot=True)
        optimizer=torch.optim.Adam(support.parameters(),lr=.01);torch.manual_seed(42)
        measure('update',lambda:core.streamed_update(model,support,optimizer,ds,ins,core.native_chunk_forward,
            g_d_fit=gap,epsilon=epsilon,identity=identity,constrained=arm=='constrained',purpose='validation_timing'),
            rows=len(ds),scope={'arm':arm,'chunks':len(ds),'D_passes':2,'I_backward':True})
        removed=core.export_removal_mask(model,provenance=identity)['removed']
        def validation_stage():
            result=evaluate_validation(model,design,removed,chunk_size=prepared['chunk_size'],epsilon=epsilon)
            publish_object(output/('timing-validation-'+arm),dict(kind='a3_mask_timing_validation_v1',purpose='validation_timing',
                identity=identity,result=result))
            return result
        validation=measure('validation',validation_stage,scope={'arm':arm,'full_validation':True})
        parity=measure('binary_parity',lambda:binary_parity(model,ds+ins),rows=len(ds),scope={'arm':arm})
        # Price the actual atomic driver publisher with its largest ten-record history.
        summary={k:v for k,v in validation.items() if k not in ('rows','positive_controls')}
        summary.update(purpose='validation_timing',timing_only=True,rows_sha256=digest(validation['rows']))
        history=[dict(copy.deepcopy(summary),update=i) for i in range(20,201,20)]
        def checkpoint():
            state=core.make_checkpoint(model,support,optimizer,ds,ins,identity=identity,update=1,purpose='validation_timing')
            base_identities.append(state['base'])
            _publish_boundary(output/('timing-checkpoint-'+arm),state,
                dict(identity=identity,validations=history,replay=replay,purpose='validation_timing',timing_only=True))
        measure('checkpoint',checkpoint,scope={'arm':arm,'maximum_history_records':10})
        def restore_boundary():
            state,driver=_read_boundary(output/('timing-checkpoint-'+arm))
            core.restore_checkpoint(state,model,support,optimizer,ds,ins,identity=identity,purpose='validation_timing')
            export=core.export_removal_mask(model,provenance=identity)
            randoms=random_controls(prepared['candidates'],prepared['candidates'],seed=42)
            publish_object(output/('timing-selection-serialization-'+arm),dict(kind='a3_mask_timing_selection_v1',
                purpose='validation_timing',final=False,may_select=False,export=export,random_controls=randoms))
        measure('selection',restore_boundary,rows=len(ds),scope={'arm':arm,'purpose':'validation_timing'})
        arms.append(dict(arm=arm,source_split='validation',purpose='validation_timing',
            row_ids=[rid for c in ds for rid in c.ids],chunks=len(ds),chunk_identity=core._chunks_identity(ds,ins),
            replay=replay,export_parity=parity['max_abs_error'],validation_rows=len(validation['rows'])))
    union=sorted(set(map(tuple,prepared['candidates']))|set(map(tuple,prepared.get('new30',{}).get('removed',[]))))
    for task in design['tasks']:
        guarded()
        timing_design=dict(design,tasks=copy.deepcopy(design['tasks']))
        timing_ids=design['tasks'][task]['selection_ids'][:100]
        timing_design['tasks'][task]['selection_ids']=timing_ids
        rows=[r for r in design['access_rows'][task] if r['condition']=='H' and r['split']=='validation'
            and r['instance_id'] in set(design['tasks'][task]['selection_ids'])]
        support=union if task=='far_v2' else sorted(map(tuple,prepared['candidates']))
        bank=measure('H_bank:'+task,lambda:collect_publish_bank(model,rows,support,guard=guarded,
            prepared=prepared,task=task,output=output/'timing-H-banks'/task,purpose='validation_timing'),
            rows=len(rows)*2,scope={'task':task,'support':[list(k) for k in support]})
        # Actual crossed, positive and utility-floor adapters; validation sources stay explicit.
        measure('assessment:'+task,lambda:assess_group(model,timing_design,prepared,task=task,name='timing_union',
            removed=[list(k) for k in support],bank=bank,parent=None,guard=guarded,
            split='validation',purpose='validation_timing'),scope={'task':task,'support':[list(k) for k in support],
                'mechanism_ids':timing_ids,'IOI':len(design['ioi_validation']),
                'MMLU':len(design['mmlu_validation']),'operations':['item_swap','h_twin','zero','h_mean','self_replay','empty']})
    measurements['guard_initial']=[dict(seconds=initial_proof_seconds,rows=1,numeric_profile=prepared['identity']['numeric_profile'],
        widths=prepared['widths'],source_split='validation',scope={'proof':'complete target inventory plus original root refresh'})]
    measurements['guard']=[dict(seconds=max(guard_samples),rows=1,numeric_profile=prepared['identity']['numeric_profile'],
        widths=prepared['widths'],source_split='validation',scope={'refreshes':len(guard_samples)})]
    require(len(set(base_identities))==1 and base_identities[0]==measured_base,'native base weights/computation changed across matched timing arms')
    import resource
    receipt=dict(kind='a3_mask_pilot_v2',identity=prepared['identity'],complete=True,exit_code=0,
        hardware='injected_cpu' if injected else torch.cuda.get_device_name(),injected=injected,
        arms=['constrained','unconstrained'],arm_measurements=arms,measurements=measurements,
        base_identity=base_identities[0],startup_seconds=startup_seconds,validation_measured=True,two_D_passes_measured=True,
        timing_only=True,final=False,purpose='validation_timing',may_select_checkpoint=False,
        padding_policy='all profile sources/donors max unpadded length plus one masked token',widths=prepared['widths'],
        reuse_policy='same hardware/model/backend/dtype/width/batch; at least one measured cohort with exact count ratios and extra update cohort-hash factor; union-support inference; walltimes rounded upward',
        allocation_job_id=__import__('os').environ.get('SLURM_JOB_ID'),
        reservation_id=None if injected else guard_evidence[-1]['reservation']['reservation']['reservation_id'],
        pilot_inventory_sha256=None if pilot_inventory is None else pilot_inventory['inventory_sha256'],output_dir=str(output.resolve()),
        peak_memory_bytes=torch.cuda.max_memory_allocated() if device.type=='cuda' else 0,
        host_peak_bytes=source_validation.host_peak_bytes(guard),
        gpu_capacity_bytes=(torch.cuda.mem_get_info()[0]+torch.cuda.memory_allocated()) if device.type=='cuda' else 0,
        target_inventory_sha256=target_inventory['inventory_sha256'] if target_inventory is not None else None,
        boundary_bytes=max(sum(p.stat().st_size for p in (output/('timing-checkpoint-'+arm)).rglob('*') if p.is_file()) for arm in ('constrained','unconstrained')))
    publish_object(output/'pilot-receipt',receipt)
    return receipt


def _load_selections(path):
    from component_analysis.a3_direction_runtime import read_object
    root=Path(path)
    return [read_object(root/f'{arm}-{seed}'/'selected') for seed in (42,1,123) for arm in ('constrained','unconstrained')]


def main(argv=None,*,model_loader=None):
    from component_analysis import a3_direction_runtime as authority,a3_mask_workload as workload,ladder_pipeline as ladder
    args=parser().parse_args(argv)
    require(re.fullmatch('[0-9a-f]{40}',args.commit) is not None,'full immutable source commit required')
    require(args.chunk_size>0,'positive mask chunk size required')
    require(args.stage=='prepare' or args.action is None,'action belongs only to CPU preparation')
    require(args.stage=='assess' or args.task is None and args.group is None,'assessment task/group flags belong only to assessment')
    if args.dry_run:
        print(json.dumps(dict(module='component_analysis.a3_mask_pipeline',stage=args.stage,weights_loaded=False,writes=False,
            execution_authorized=False,allocation_verified=False,live_allocation_admission='deferred/unverified')))
        return 0
    root=Path(args.work_dir)
    if args.stage=='prepare' and args.action is None:args.action='freeze'
    if args.stage=='prepare' and args.action=='freeze':
        prepared=prepare_mask(args.design,commit=args.commit,chunk_size=args.chunk_size,registry_paths=args.registry,root_bundle=args.root_bundle)
        authority.publish_object(root/'prepared',prepared)
        return 0
    args._mask_source_started=time.perf_counter()
    prepared=authority.read_object(args.prepared or root/'prepared')
    design,evidence=_live_mask(prepared,args)
    if args.stage=='prepare':
        require(args.action in ('inventory','admit'),'unknown CPU preparation action')
        if args.action=='inventory':
            require(args.finish_reserve_seconds is not None,'explicit finish reserve required')
            inventory=workload.build_inventory(design,identity=prepared['identity'],chunk_size=prepared['chunk_size'],
                finish_reserve_seconds=args.finish_reserve_seconds,hbank_sources=prepared['hbank_sources'],stage=args.inventory_stage,widths=prepared['widths'],new30=prepared['new30'])
            authority.publish_object(root/('inventory-'+args.inventory_stage),inventory)
        else:
            require(args.inventory and args.pilot_receipts and args.ledger_snapshot,'cost proposal requires complete measured pilots/inventory/current ledger')
            inventory=authority.read_object(args.inventory)
            ledger=authority.normalize_ledger(args.ledger_snapshot,identity=prepared['identity'])
            proposal=workload.project_cost([authority.read_object(p) for p in args.pilot_receipts],inventory,ledger)
            authority.publish_object(root/'cost-proposal',proposal)
        return 0
    if args.stage=='summarize':
        groups=assessment_groups(prepared,_load_selections(args.selected or root))
        require(prepared['new30']['status']=='available','blocked: missing New30 reference comparison')
        cells=[]
        from component_analysis.ladder_metrics import summarize_ladder
        for task in design['tasks']:
            for name,removed in groups.items():
                if name=='New30' and task!='far_v2':continue
                path=root/'assessment'/task/name.replace(':','-')
                require(path.is_dir(),'blocked: missing required assessment group '+str(path))
                result=authority.read_object(path)
                validate_assessment_result(result,design,prepared,task=task,name=name,removed=removed)
                rows=[dict(row,group=task+':'+name) for row in result['rows']]
                joined=summarize_ladder(rows,bootstrap_seed=9001,n_boot=2000)
                for cell in joined['cells']:
                    cell['descriptive']=task!='far_v2'
                    cell['raw_target_choice']=raw_choice_rates(result['rows'],operation=cell['operation'])
                    cell['confirmatory']=False
                    cell['point_specificity_qualified']=bool(cell['operation']=='item_swap' and cell['point_pass']
                        and cell['complete_assay_ready'] and cell['assay_readiness']['MMLU']['passed'])
                    cell['specificity_qualified']=bool(cell['point_specificity_qualified'] and cell['strong'])
                cells.extend(joined['cells'])
        summary=dict(kind='a3_mask_summary_v1',identity=prepared['identity'],cells=cells,
            bootstrap=dict(seed=9001,n_boot=2000),
            interpretation='local numerical gates, complete assay readiness and joined MMLU floors are separate; FAR exports transfer descriptively',
            complete_required_groups=True,qualified_primary_cells=[dict(task=c['task'],group=c['group']) for c in cells if c['specificity_qualified']])
        authority.publish_object(root/'summary',summary)
        return 0
    require(args.inventory,'source-bound current inventory required before loading weights')
    inventory=authority.read_object(args.inventory)
    if args.stage=='fit':
        require(inventory['phase']=='M5' and (args.resume==(args.checkpoint is not None)),'fit requires M5 and an exact requested resume boundary')
    elif args.stage=='pilot':
        require(inventory['phase']=='M1' and args.target_inventory,'pilot requires M1 and the full target inventory before loading weights')
        target_started=time.perf_counter();target_inventory=authority.read_object(args.target_inventory)
        workload.validate_inventory(target_inventory)
        expected_target=workload.build_inventory(design,identity=prepared['identity'],chunk_size=prepared['chunk_size'],
            finish_reserve_seconds=target_inventory['finish_reserve_seconds'],hbank_sources=prepared['hbank_sources'],
            stage='full',widths=prepared['widths'],new30=prepared['new30'])
        require(target_inventory['inventory_sha256']==expected_target['inventory_sha256'],'pilot target is not the exact canonical full workload')
        del expected_target
        target_read_seconds=time.perf_counter()-target_started
    elif args.stage=='assess':
        require(inventory['phase']=='M5' and args.task in design['tasks'] and args.group=='all','assessment requires one source task, --group all and its M5 inventory')
        require(prepared['new30']['status']=='available','blocked: missing New30 reference comparison')
        groups=assessment_groups(prepared,_load_selections(args.selected or root))
    guard=lambda:_live_mask(prepared,args,inventory)[1]
    guard._source_state=getattr(args,'_mask_source_context',None)
    execution_evidence=guard()
    if args.stage in ('fit','assess'):
        reservation=execution_evidence['reservation']['reservation']
        require(authority.object_reference(reservation['admission_path'])==reservation['admission_reference'],'changed root model admission bytes')
        admission=authority.read_object(reservation['admission_path']);expected_base=admission.get('measured_base_identity')
        require(isinstance(expected_base,str) and re.fullmatch('[0-9a-f]{64}',expected_base),'M5 root admission must bind its completed pilot model hash')
    started=time.perf_counter()
    require(model_loader is None,'injected model loaders are forbidden for canonical production execution')
    model=load_native_model(prepared)
    startup_seconds=_source_startup_seconds(time.perf_counter()-started+(_MODULE_IMPORTED-_MODULE_STARTED),args)
    if args.stage in ('fit','assess'):
        core.configure_candidates(model,prepared['candidates'])
        require(core._base_identity(model)==expected_base,'current native model differs from measured pilot computation')
    if args.stage=='fit':
        require(args.action is None,'fit has no alternate action')
        train_constrained(model,design,prepared,seed=args.seed,arm=args.arm,checkpoint_dir=root/f'{args.arm}-{args.seed}',
            guard=guard,resume=args.checkpoint if args.resume else None)
    elif args.stage=='pilot':
        require(inventory['phase']=='M1','pilot requires bounded original M1 reservation')
        require(args.target_inventory,'pilot requires completed full target inventory for measured reuse')
        mask_pilot(model,design,prepared,output=root,guard=guard,startup_seconds=startup_seconds,target_inventory=target_inventory,pilot_inventory=inventory,target_read_seconds=target_read_seconds)
        discard_pilot_model(model)
        del model  # A pilot state cannot become a scientific training state.
    elif args.stage=='assess':
        require(args.task in design['tasks'],'one explicit unchanged transfer task required')
        core.configure_candidates(model,prepared['candidates'])
        parent,selected,_=__import__('component_analysis.a3_pipeline',fromlist=['load_a1_parents']).load_a1_parents(
            design['parent_evidence']['prepared_path'],design['parent_evidence']['selected_path'])
        task=args.task;domain=prepared['hbank_sources'][task];indexed={r['instance_id']:r for r in parent['rows'][task]['H']}
        source=[indexed[i] for i in domain['ids']]
        require(digest(source)==domain['rows_sha256'],'changed original H-bank source rows')
        source=source_validation.freeze(source)
        required=sorted(set(map(tuple,prepared['candidates']))|({tuple(k) for k in prepared['new30'].get('removed',[])} if task=='far_v2' else set()))
        bank_path=root/'H-banks'/task
        if bank_path.exists():
            bank=authority.read_object(bank_path)
            validate_h_bank(bank,prepared,task=task,model=model)
        else:
            bank=collect_publish_bank(model,source,required,guard=guard,prepared=prepared,task=task,output=bank_path,purpose='scientific_H_bank')
        for name,removed in groups.items():
            if name=='New30' and task!='far_v2':continue
            guard();target=root/'assessment'/task/name.replace(':','-')
            if target.exists():
                require(args.resume,'assessment output exists; exact group resume must be explicit')
                validate_assessment_result(authority.read_object(target),design,prepared,task=task,name=name,removed=removed)
                continue
            result=assess_group(model,design,prepared,task=task,name=name,removed=removed,bank=bank,parent=parent,guard=guard)
            result['H_bank_reference']=authority.object_reference(bank_path)
            result['run_manifest_reference']=publish_run_manifest(root/'run-manifests',prepared,stage='assess',
                evidence=dict(task=task,group=name,rows=len(result['rows']),expected_mechanism_rows=result['expected_mechanism_rows'],
                    positive_controls=len(result['positive_controls']),startup_seconds=startup_seconds,guard=guard(),
                    H_bank_reference=result['H_bank_reference'],model_proof=actual_bank_model_proof(model)))
            authority.publish_object(target,result)
    else:raise ValueError('unknown mask stage')
    return 0





def positive_readout(model,ids,mask,donor_ids,donor_mask):
    """Independent all-sender readout overwrite, including donor embeddings."""
    require(ids.shape[0]==donor_ids.shape[0],'positive-control donor batch differs')
    head_width=model.config.hidden_size//model.config.num_attention_heads
    rows=torch.arange(len(ids),device=ids.device)
    position=mask.sum(-1)-1;donor_position=donor_mask.sum(-1)-1
    saved={};handles=[]
    with binary_mode(model,[]),torch.no_grad():
        base_logits=_single_logits(model,ids,mask)
        try:
            def capture_embedding(module,args,out):saved['embedding']=out[rows,donor_position].detach().clone()
            handles.append(model.model.embed_tokens.register_forward_hook(capture_embedding))
            for layer,block in enumerate(model.model.layers):
                def capture_head(module,args,layer=layer):saved['head',layer]=args[0][rows,donor_position].detach().clone()
                def capture_mlp(module,args,out,layer=layer):saved['mlp',layer]=out[rows,donor_position].detach().clone()
                handles.append(block.attn.original_attention.o_proj.register_forward_pre_hook(capture_head))
                handles.append(block.mlp.register_forward_hook(capture_mlp))
            donor_logits=_single_logits(model,donor_ids,donor_mask)
        finally:
            for h in handles:h.remove()
        handles=[]
        try:
            def patch_embedding(module,args,out):
                value=out.clone();value[rows,position]=saved['embedding'];return value
            handles.append(model.model.embed_tokens.register_forward_hook(patch_embedding))
            for layer,block in enumerate(model.model.layers):
                def patch_head(module,args,layer=layer):
                    value=args[0].clone();value[rows,position]=saved['head',layer];return (value,)
                def patch_mlp(module,args,out,layer=layer):
                    value=out.clone();value[rows,position]=saved['mlp',layer];return value
                handles.append(block.attn.original_attention.o_proj.register_forward_pre_hook(patch_head))
                handles.append(block.mlp.register_forward_hook(patch_mlp))
            patched=_single_logits(model,ids,mask)
        finally:
            for h in handles:h.remove()
    error=float((patched-donor_logits).abs().max())
    require(torch.allclose(patched,donor_logits,atol=1e-5,rtol=1e-5),'native all-sender positive control failed')
    return dict(passed=True,max_abs_logit_error=error,recipient_rows=len(ids),donor_rows=len(donor_ids),
        donor_choice_differs=(base_logits.argmax(-1)!=donor_logits.argmax(-1)).cpu().tolist(),
        intact_donor_max_abs_logit_difference=float((base_logits-donor_logits).abs().max()))


def _protect_bank_sources(design,parent,domains,registry_paths):
    from component_analysis.a3_design import validate_access
    access=dict(design,access_rows={task:list(rows) for task,rows in design['access_rows'].items()})
    for task,domain in domains.items():
        indexed={r['instance_id']:r for r in parent['rows'][task]['H']}
        access['access_rows'][task].extend(indexed[rid] for rid in domain['ids'])
    return validate_access(access,list(registry_paths))




def execution_widths(design,*,hbank_rows):
    """One masked pad after every actual profile source/donor's longest sequence."""
    widths={}
    for task,rows in design['access_rows'].items():
        extra=hbank_rows.get(task,[])
        for row in list(rows)+list(extra):
            for record in row['streams'].values():validate_source_stream(record)
        widths[task]={condition:1+max(len(s['tokens']) for row in list(rows)+list(extra)
            if row['condition']==condition for s in row['streams'].values()) for condition in ('D','I','H','F','user_neutral')}
        for pair in [('D','H'),('I','user_neutral')]:
            largest=max(widths[task][c] for c in pair)
            for c in pair:widths[task][c]=largest
    for task in ('ioi','mmlu'):
        rows=list(design['utility'][task])+list(design[task+'_validation'])
        for row in rows:
            for record in row['streams'].values():validate_source_stream(record)
        widths[task]=1+max(len(s['tokens']) for row in rows for s in row['streams'].values())
    return widths


def execution_design(design,widths):
    """Runtime-only physical profile, separate from canonical frozen A3 bytes."""
    result=dict(design,_mask_widths=copy.deepcopy(widths))
    return source_validation.freeze(result) if source_validation.is_view(design) else result


def frozen_validation_history(selected):
    """The completed200 boundary, separate from an earlier selected checkpoint."""
    from component_analysis.a3_direction_runtime import read_object,object_reference
    path=Path(selected['completed_checkpoint_path'])
    require(common.file_hash(path/'COMPLETE.json')==selected['completed_checkpoint_sha256'],'changed completed200 boundary')
    state,driver=_read_boundary(path)
    require(state['purpose']=='scientific_training' and state['update']==200 and state['identity']==selected['identity']
        and driver['identity']==selected['identity'],'incomplete/wrong-purpose final training boundary')
    history=driver['validations'];select_checkpoint(history)
    for record in history:
        reference=record['rows_reference'];require(object_reference(reference['path'])==reference,'changed validation artifact bytes')
        evidence=read_object(reference['path'])
        require(evidence['kind']=='a3_mask_validation_v1' and evidence['identity']==selected['identity'],'changed frozen validation identity')
        result=evidence['result']
        require(digest(result['positive_controls'])==record['positive_controls_sha256']
            and all(p['passed'] for p in result['positive_controls']),'changed/failed frozen validation positive controls')
        require(result['split']=='validation' and result['update']==record['update'] and digest(result['rows'])==record['rows_sha256'],
            'assessment/wrong scheduled validation in selection history')
        gates=validation_gates(result['rows'],epsilon=result['epsilon'])
        require(all(gates[k]==record[k] for k in ('eligible','D_fraction','I_fraction','collateral','means')),
            'frozen validation gates differ from their observations')
    return history


def collect_publish_bank(model,rows,candidates,*,guard,prepared,task,output,purpose):
    from component_analysis.a3_direction_runtime import publish_object
    require(purpose in ('validation_timing','scientific_H_bank'),'unknown H-bank purpose')
    if purpose=='validation_timing':require(all(r['split']=='validation' for r in rows),'timing H bank may access validation only')
    proof=actual_bank_model_proof(model)
    if prepared.get('injected') and '_injected_bank_model_proof' not in prepared:
        prepared['_injected_bank_model_proof']=copy.deepcopy(proof)
    _expected_bank_model_proof(prepared,proof=proof)
    require(_bank_keys(candidates,proof['model_geometry'])==required_bank_support(prepared,task,proof['model_geometry']),'incomplete typed bank collection support')
    domain=_bank_domain(rows,timing=purpose=='validation_timing')
    if purpose=='scientific_H_bank':require(domain==prepared['hbank_sources'][task],'original H-bank collection source changed')
    bank=collect_h_bank(model,rows,candidates,guard=guard,padded_width=prepared['widths'][task]['H'])
    bank.update(kind='a3_mask_H_bank_timing_v1' if purpose=='validation_timing' else 'a3_mask_H_bank_v1',purpose=purpose,
        identity=prepared['identity'],runtime_identity=proof['runtime_identity'],base_identity=proof['base_identity'],
        model_geometry=copy.deepcopy(proof['model_geometry']),
        execution_geometry=dict(physical_batch=1,padded_width=prepared['widths'][task]['H'],readout='last unpadded token',
            pooling='unpadded tokens from both streams'),source_task=task)
    validate_h_bank(bank,prepared,task=task,model=model,purpose=purpose,source_domain=domain)
    publish_object(output,bank)
    return bank


def discard_pilot_model(model):
    """Remove live timing state from the device; the object remains permanently barred."""
    require(getattr(model,'_a3_disposable_timing_model',False),'only a disposable timing model may be discarded')
    for parameter in model.parameters():parameter.grad=None
    model.to('cpu')
    model._a3_timing_state_discarded=True
    if torch.cuda.is_available():torch.cuda.empty_cache()


def publish_validation(path,evidence):
    from component_analysis.a3_direction_runtime import publish_object,read_object
    if Path(path).exists():
        require(read_object(path)==evidence,'existing immutable validation differs from exact resumed computation')
    else:publish_object(path,evidence)


def publish_run_manifest(root,prepared,*,stage,evidence):
    """Immutable per-invocation source and execution evidence; no weights."""
    import os
    commit=prepared['identity'].get('commit')
    require(prepared.get('injected') or isinstance(commit,str) and re.fullmatch('[0-9a-f]{40}',commit),'full production execution commit required')
    payload=dict(kind='a3_mask_run_manifest_v1',stage=stage,identity=prepared['identity'],commit=commit,
        injected=bool(prepared.get('injected')),job_id=os.environ.get('SLURM_JOB_ID','injected-cpu'),
        cluster=os.environ.get('DC_CLUSTER','injected-cpu'),exit_code=0,evidence=evidence)
    target=Path(root)/(stage+'-'+str(time.time_ns()))
    def writer(directory):
        (directory/'run_manifest.json').write_text(json.dumps(payload,sort_keys=True,allow_nan=False)+'\n')
        (directory/'COMPLETE.json').write_text(json.dumps({'sha256':common.file_hash(directory/'run_manifest.json')})+'\n')
    common.publish(target,writer)
    return dict(path=str(target.resolve()),sha256=common.file_hash(target/'run_manifest.json'))


def read_run_manifest(reference):
    path=Path(reference['path']);require({p.name for p in path.iterdir()}=={'run_manifest.json','COMPLETE.json'},'incomplete execution manifest')
    require(json.loads((path/'COMPLETE.json').read_text())=={'sha256':reference['sha256']}
        and common.file_hash(path/'run_manifest.json')==reference['sha256'],'changed run manifest bytes')
    value=json.loads((path/'run_manifest.json').read_text())
    require(value['kind']=='a3_mask_run_manifest_v1' and value['exit_code']==0,'failed/wrong execution manifest')
    return value


def mask_protocol(prepared):
    """Scientific controls are source identity, not free caller dictionaries."""
    fields=('candidates','chunk_size','seeds','arms','updates','validation_every','validation_donors','root_ruling',
        'random_controls','timing_protocol','new30','hbank_sources','widths','injected')
    return {name:copy.deepcopy(prepared[name]) for name in fields}


def mask_reservation(args,inventory,*,injected=False):
    """Shared genuine root authority; one nonserializable proof context per process."""
    from component_analysis import a3_direction_runtime as authority,a3_mask_workload as workload
    require(args.ledger_snapshot and args.reservation,'fresh root ledger mapping/reservation required before model access')
    scope={name:getattr(args,name,None) for name in ('stage','seed','arm','task','group','ledger_snapshot','reservation','inventory','work_dir','admission')}
    scope['experiment']='masks';scope['inventory_sha256']=inventory['inventory_sha256']
    context=getattr(args,'_mask_authority_context',None)
    if context is None:
        ledger=authority.normalize_ledger(args.ledger_snapshot,identity=inventory['identity'],injected=injected)
        context=authority.make_authority_context(args.reservation,ledger=ledger,inventory=inventory,work_dir=args.work_dir,
            injected=injected,subphase='masks',inventory_validator=workload.validate_inventory,subphase_limits={'M1':1.5,'M5':10},
            requested_scope=scope,inventory_path=args.inventory)
        args._mask_authority_context=context;args._mask_initial_ledger=ledger
    result=authority.validate_reservation(args.reservation,ledger=args._mask_initial_ledger,inventory=inventory,work_dir=args.work_dir,
        injected=injected,subphase='masks',inventory_validator=workload.validate_inventory,subphase_limits={'M1':1.5,'M5':10},
        authority_context=context,requested_scope=scope,inventory_path=args.inventory)
    if getattr(args,'admission',None):
        require(result['reservation']['admission_path']==str(Path(args.admission).resolve()),'CLI admission differs from original root reservation')
    return result


def validate_assessment_result(result,design,prepared,*,task,name,removed):
    """Check exact frozen row/control keys; a completion boolean is insufficient."""
    from component_analysis.a3_direction_runtime import read_object,object_reference
    require(result['kind']=='a3_mask_assessment_group_v1' and result['purpose']=='assessment' and result['split']=='test'
        and result['identity']==prepared['identity'] and result['task']==task and result['group']==name
        and result['removed']==removed and result['complete'],'changed/wrong-purpose assessment group')
    expected=set()
    for rid in design['tasks'][task]['assessment_ids']:
        for condition in ('D','I','H','F','user_neutral'):
            for stream in ('clean','corrupt'):
                for operation in ('item_swap','h_twin','zero','h_mean','self_replay','empty'):
                    expected.add((task,rid,condition,stream,operation))
    for utility,operations in [('ioi',('item_swap','zero','h_mean','self_replay','empty')),('mmlu',('zero','h_mean','self_replay','empty'))]:
        for row in design['utility'][utility]:
            for operation in operations:expected.add((utility,row['instance_id'],utility.upper(),'clean',operation))
    actual=[(r['task'],r['instance_id'],r['condition'],r['stream'],r['operation']) for r in result['rows']]
    require(len(actual)==len(set(actual)) and set(actual)==expected,'blocked: incomplete/duplicate original crossed assessment membership')
    for row in result['rows']:
        require(row['group']==name and row['group_members']==removed,'changed row intervention support')
        if not row['supported']:
            require(row['condition']=='F' and row['operation']=='h_twin' and row.get('status')=='blocked_unsupported_donor',
                'blocked: unsupported required primary/crossed assessment')
            continue
        fields=['intact_margin','patched_margin','intact_correct','patched_correct','intact_native_margin','patched_native_margin']
        if row['condition']=='MMLU':fields+=['intact_choice_margin','patched_choice_margin','intact_choice_correct','patched_choice_correct']
        require(row['assay_valid'] and all(type(row.get(f)) in (int,float) and math.isfinite(row[f]) for f in fields),
            'blocked: missing/nonfinite required assessment diagnostics')
    positive_keys=[]
    for control in result['positive_controls']:
        require(control['passed'] and math.isfinite(control['max_abs_logit_error']),'blocked: failed/missing positive controls')
        positive_keys.extend((control['condition'],rid,stream) for rid in control['instance_ids'] for stream in control['streams']
            if stream!='clean_execution_duplicate')
    expected_positive={(condition,rid,stream) for rid in design['tasks'][task]['assessment_ids']
        for condition in ('D','I','H','F','user_neutral') for stream in ('clean','corrupt')}
    expected_positive.update((utility.upper(),r['instance_id'],'clean') for utility in ('ioi','mmlu') for r in design['utility'][utility])
    require(len(positive_keys)==len(set(positive_keys)) and set(positive_keys)==expected_positive,'blocked: incomplete source-bound positive controls')
    reference=result['H_bank_reference'];require(object_reference(reference['path'])==reference,'changed assessment H-bank bytes')
    bank=read_object(reference['path'])
    manifest=read_run_manifest(result['run_manifest_reference'])
    require(manifest['identity']==prepared['identity'],'missing/changed execution source manifest')
    if prepared.get('injected'):proof=prepared.get('_injected_bank_model_proof')
    else:
        proof=manifest['evidence'].get('model_proof')
        reservation=manifest['evidence']['guard']['reservation']['reservation']
        require(object_reference(reservation['admission_path'])==reservation['admission_reference'],'changed authenticated bank model admission')
        admission=read_object(reservation['admission_path'])
        require(isinstance(proof,dict) and proof.get('base_identity')==admission.get('measured_base_identity'),
            'bank proof differs from authenticated measured model identity')
    validate_h_bank(bank,prepared,task=task,model_proof=proof)
    return result




def raw_choice_rates(rows,*,operation):
    """Native and canonical raw choices remain separate from fractional removal."""
    result={}
    for condition in ('D','I','H','F','user_neutral'):
        records=[r for r in rows if r['operation']==operation and r['condition']==condition and r['supported']]
        if not records:
            result[condition]=dict(status='blocked_unsupported_secondary',n_rows=0)
            continue
        result[condition]=dict(status='observed',n_rows=len(records))
        for prefix in ('intact','patched'):
            result[condition][prefix+'_opposite_over_honest']=sum(r[prefix+'_target_choice'] for r in records)/len(records)
            result[condition][prefix+'_native_opposite_over_honest']=sum(r[prefix+'_native_margin']>0 for r in records)/len(records)
            result[condition][prefix+'_full_vocab_opposite']=sum(r[prefix+'_argmax']==r['opposite_token'] for r in records)/len(records)
            result[condition][prefix+'_native_full_vocab_opposite']=sum(r[prefix+'_native_argmax']==r['opposite_token'] for r in records)/len(records)
    return result





def validate_source_stream(record):
    """A1 stores unpadded tokens/readouts/layouts; a mask is optional evidence."""
    tokens=record.get('tokens')
    require(isinstance(tokens,list) and tokens and all(type(token) is int and token>=0 for token in tokens),'invalid authenticated source tokens')
    require(record.get('readout')==len(tokens)-1,'source readout conflicts with unpadded token length')
    if 'attention_mask' in record:
        mask=record['attention_mask']
        require(isinstance(mask,list) and mask==[1]*len(tokens),'source attention mask conflicts with authenticated unpadded tokens')
    return len(tokens)


if __name__=='__main__':raise SystemExit(main())
