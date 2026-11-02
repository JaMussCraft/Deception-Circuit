"""Joint sender interventions through the shared hooks, with explicit maps.

LadderBatch is one tokenized stream, right padded without truncation. The CLI
must set task to far_v2/sdr_v2/ser_v2/ioi/mmlu; records preserve source_hash,
split, normalized layout, source_condition, and pressure_id. Canonical answer
IDs are explicit per stream; Batch.target_token is deliberately not inferred.
Only hooks owns model-wrapper access. All ranking uses its fp32 readout.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional
import torch

from component_analysis import hooks

OPERATIONS=('zero','h_mean','h_twin','item_swap','independent_resample','task_resample','self_replay','empty')


@dataclass
class LadderBatch:
    ids: list[str]
    condition: str
    stream: str
    input_ids: torch.Tensor
    attention_mask: torch.Tensor
    readout: torch.Tensor
    opposite_token: torch.Tensor
    honest_token: torch.Tensor
    expected_token: torch.Tensor
    records: list[dict]
    task: str = 'mechanism'
    choice_tokens: Optional[torch.Tensor] = None


def from_batch(batch, *, condition, stream, opposite_token, honest_token,
               expected_token, task, records=None, choice_tokens=None):
    """Reuse native Batch tensors, requiring the caller's explicit labels."""
    if stream not in ('clean','corrupt'): raise ValueError('unknown stream')
    ids=batch.input_ids if stream=='clean' else batch.corrupt_input_ids
    mask=batch.attention_mask if stream=='clean' else batch.corrupt_attention_mask
    # Native Batch has one readout; changed user layouts must supply LadderBatch.
    result=LadderBatch(batch.ids,condition,stream,ids,mask,batch.readout,
                       opposite_token,honest_token,expected_token,
                       batch.records if records is None else records,task,choice_tokens)
    validate_batch(result)
    return result


def validate_batch(batch):
    ids,mask=batch.input_ids,batch.attention_mask
    n=len(batch.ids)
    if ids.ndim!=2 or ids.shape!=mask.shape or ids.shape[0]!=n or n==0:
        raise ValueError('batch tensor shape/ids mismatch')
    if len(set(batch.ids))!=n or len(batch.records)!=n: raise ValueError('duplicate ids or records mismatch')
    if batch.stream not in ('clean','corrupt'): raise ValueError('unknown stream')
    if not torch.all((mask==0)|(mask==1)) or not torch.all(mask[:,0]==1) or torch.any(mask[:,1:]>mask[:,:-1]):
        raise ValueError('only nonempty right padded masks supported')
    readout=torch.as_tensor(batch.readout)
    if readout.shape!=(n,) or torch.any(readout<0) or torch.any(readout>=ids.shape[1]):
        raise ValueError('invalid readout shape/range')
    if torch.any(mask.gather(1,readout.to(mask.device).long()[:,None])!=1):
        raise ValueError('readout points into padding')
    for name in ('opposite_token','honest_token','expected_token'):
        tokens=torch.as_tensor(getattr(batch,name))
        if tokens.shape!=(n,) or torch.any(tokens<0): raise ValueError(f'invalid {name}')
    if torch.any(batch.opposite_token==batch.honest_token): raise ValueError('canonical answer ids must differ')
    if batch.choice_tokens is not None:
        if batch.choice_tokens.shape!=(n,4): raise ValueError('choice_tokens must have four options per row')
        if any(len(set(row))!=4 for row in batch.choice_tokens.tolist()): raise ValueError('duplicate choices')
        if not torch.all((batch.choice_tokens==batch.expected_token[:,None]).any(-1)):
            raise ValueError('expected token is absent from choices')


def mapped_replacement(recipient, donor, maps, recipient_mask, donor_mask):
    """Gather explicit unpadded donor indices into recipient-shaped storage."""
    if len(maps)!=recipient.shape[0] or donor.shape[0]!=recipient.shape[0]:
        raise ValueError('one donor and map required per recipient row')
    value=recipient.clone(); positions=torch.zeros_like(recipient_mask,dtype=torch.bool)
    for row,mapping in enumerate(maps):
        left,right=mapping['recipient_positions'],mapping['donor_positions']
        if len(left)!=len(right) or len(set(left))!=len(left) or len(set(right))!=len(right):
            raise ValueError('invalid or duplicate position map')
        if any(type(p) is not int or p<0 or p>=recipient.shape[1] or not recipient_mask[row,p] for p in left):
            raise ValueError('recipient map must use unpadded positions')
        if any(type(p) is not int or p<0 or p>=donor.shape[1] or not donor_mask[row,p] for p in right):
            raise ValueError('donor map must use unpadded positions')
        if left:
            value[row,left]=donor[row,right].to(device=value.device,dtype=value.dtype)
            positions[row,left]=True
    return hooks.Replacement(value,positions)


def collect_h_mean_bank(model, batches, keys):
    """Original-H train+validation equal-token pooled bank, both streams.

    Explicit provenance is validated here; the generic collector's historical
    'test split' prose is replaced with the actual source domain in this bank.
    """
    from component_analysis.knockout import collect_mean_bank
    from component_analysis.dataloaders import Batch
    batches=list(batches)
    indexed={}
    for b in batches:
        validate_batch(b)
        if b.condition!='H' or any(r.get('source_condition')!='H' or r.get('split') not in ('train','validation')
                                    or not r.get('source_hash') for r in b.records):
            raise ValueError('mean bank requires original H train+validation with source provenance')
        for j,rid in enumerate(b.ids):
            key=(rid,b.stream)
            if key in indexed: raise ValueError('duplicate mean-bank source stream/id')
            indexed[key]=(b,j)
    ids=sorted({rid for rid,stream in indexed})
    if not ids or set(indexed)!={(rid,s) for rid in ids for s in ('clean','corrupt')}:
        raise ValueError('mean bank requires both streams of every original H id')
    native=[]; provenance=[]
    for rid in ids:
        clean,ci=indexed[(rid,'clean')]; corrupt,di=indexed[(rid,'corrupt')]
        a,am=clean.input_ids[ci:ci+1],clean.attention_mask[ci:ci+1]
        b,bm=corrupt.input_ids[di:di+1],corrupt.attention_mask[di:di+1]
        native.append(Batch([rid],[clean.records[ci]],a,am,b,bm,clean.opposite_token[ci:ci+1],
                            clean.honest_token[ci:ci+1],clean.readout[ci:ci+1],None))
        provenance.append(dict(instance_id=rid,clean=clean.records[ci],corrupt=corrupt.records[di]))
    values,info=collect_mean_bank(model,native,keys)
    info.update(source_condition='H',splits=sorted({r[0].records[r[1]]['split'] for r in indexed.values()}),source_ids=ids,
                provenance=provenance,semantics='original H train+validation, both streams, all unpadded tokens, equal-token fp32 pooling')
    return dict(values=values,provenance=info)


def _capture(model,batch,keys,replacements=None):
    device,_=hooks.device_and_dtype(model)
    with torch.no_grad():
        capture=hooks.capture_forward(model,batch.input_ids.to(device),batch.attention_mask.to(device),
                                      components=keys,positions=batch.readout.to(device),replacements=replacements)
        logits=hooks.readout_logits(model,capture.residual[:,-1])
    return capture,logits


def _stats(batch,logits,native):
    idx=torch.arange(len(batch.ids),device=logits.device)
    pos=batch.opposite_token.to(logits.device); neg=batch.honest_token.to(logits.device)
    expected=batch.expected_token.to(logits.device)
    canonical=logits[idx,pos]-logits[idx,neg]
    native_margin=native.float()[idx,pos]-native.float()[idx,neg]
    sign=torch.where(expected==pos,1.,-1.)
    result=dict(margin=canonical,raw_margin=canonical*sign,native_margin=native_margin,
                native_raw_margin=native_margin*sign,argmax=logits.argmax(-1),native_argmax=native.argmax(-1),
                correct=logits.argmax(-1)==expected,binary_win=canonical*sign>0)
    if batch.choice_tokens is not None:
        choice=batch.choice_tokens.to(logits.device)
        scores=logits.gather(1,choice); competitors=scores.masked_fill(choice==expected[:,None],float('-inf'))
        result['choice_margin']=logits[idx,expected]-competitors.max(-1).values
        result['choice_correct']=choice.gather(1,scores.argmax(-1)[:,None]).squeeze(-1)==expected
    return result


def _rows(batch):
    """Singleton views keep arbitrary donor row ordering and padding explicit."""
    for i,rid in enumerate(batch.ids):
        yield LadderBatch([rid],batch.condition,batch.stream,batch.input_ids[i:i+1],batch.attention_mask[i:i+1],
                          batch.readout[i:i+1],batch.opposite_token[i:i+1],batch.honest_token[i:i+1],
                          batch.expected_token[i:i+1],[batch.records[i]],batch.task,
                          None if batch.choice_tokens is None else batch.choice_tokens[i:i+1])


def _map_index(donor_maps,operation):
    result={}
    for m in donor_maps or []:
        if m['operation']!=operation: continue
        key=(m['recipient_condition'],m['recipient_id'],m['recipient_stream'])
        if key in result: raise ValueError('duplicate map: run independent donor seeds separately')
        result[key]=m
    return result


def _check_map(batch,donor,mapping,operation):
    if not mapping.get('supported'): return
    expected=list(range(int(batch.attention_mask.sum())))
    if mapping.get('recipient_positions')!=expected or mapping.get('covered_positions')!=len(expected):
        raise ValueError('whole-sequence map must cover every unpadded recipient position')
    if operation=='item_swap' and (donor.ids!=batch.ids or donor.condition!=batch.condition or donor.stream==batch.stream):
        raise ValueError('item_swap must use same-condition same-id opposite stream')
    if operation=='h_twin':
        target='user_neutral' if batch.condition in ('I','user_neutral') else 'H'
        if donor.ids!=batch.ids or donor.stream!=batch.stream or donor.condition!=target:
            raise ValueError('h_twin requires same-instance same-stream H-derived twin')
    if operation=='independent_resample':
        target='user_neutral' if batch.condition in ('I','user_neutral') else 'H'
        if donor.ids==batch.ids or donor.condition!=target or donor.stream!=batch.stream or donor.records[0].get('split') not in ('train','validation'):
            raise ValueError('independent donor must be different-instance H-derived train/validation')
    if operation=='task_resample':
        source=donor.records[0]; recipient=batch.records[0]
        if (batch.task!='ioi' or donor.task!=batch.task or batch.condition!='IOI'
                or donor.condition!=batch.condition or batch.stream!='clean' or donor.stream!='clean'
                or donor.ids==batch.ids or source.get('source_condition')!='IOI'
                or source.get('split')!='generated' or mapping.get('seed') not in (101,102,103)
                or source.get('sampling',{}).get('seed')!=mapping.get('seed')
                or not source.get('source_hash')
                or any(mapping.get('donor_'+field)!=source.get(field) for field in ('source_hash','source_id','split'))
                or any(source.get(name)!=recipient.get(name) for name in ('a','b'))
                or not source.get('a') or not source.get('b')
                or source['streams']['clean']['prompt']==recipient['streams']['clean']['prompt']):
            raise ValueError('own-task resample requires separate generated same-name IOI donor with frozen source provenance')
    # Never infer maps from equal tensor shapes: verify the explicit layouts.
    left=batch.records[0].get('layout'); right=donor.records[0].get('layout')
    if not left or not right or left!=right or int(donor.attention_mask.sum())!=len(expected):
        raise ValueError('donor map lacks matching explicit token layout')
    if mapping.get('donor_positions')!=expected:
        raise ValueError('whole-sequence donor map must be explicit absolute alignment')


def _noop_error(base,other,batch):
    bs=_stats(batch,base,base); os=_stats(batch,other,other)
    error=float((bs['margin']-os['margin']).abs().max())
    if not torch.equal(bs['argmax'],os['argmax']) or not torch.allclose(bs['margin'],os['margin'],atol=1e-5,rtol=1e-5):
        raise ValueError('assay invalid: empty/self-replay differs from intact readout')
    return error


def score_cell(model, recipient_batches, *, groups: list[tuple[str,list[tuple]]], operation: str,
               donor_batches=None, mean_bank=None, donor_maps=None) -> list[dict]:
    """Patch every group jointly; return explicit per-id/per-stream records.

    A caller runs independent seeds in separate calls with their frozen maps.
    Unsupported maps emit unsupported records with reason; they are never
    silently discarded. All groups use the same union capture and controls.
    """
    if operation not in OPERATIONS: raise ValueError('unknown operation')
    names=[name for name,keys in groups]
    if not groups or len(set(names))!=len(names): raise ValueError('groups must have unique names')
    keys=list(dict.fromkeys(tuple(k) for name,group in groups for k in group))
    donors={}
    for b in donor_batches or []:
        validate_batch(b)
        for one in _rows(b):
            key=(one.condition,one.ids[0],one.stream)
            if key in donors: raise ValueError('duplicate donor stream/id')
            donors[key]=one
    maps=_map_index(donor_maps,operation)
    if operation=='h_mean':
        p=(mean_bank or {}).get('provenance',{})
        if p.get('source_condition')!='H' or not set(p.get('splits',[])) or not set(p.get('splits',[]))<={'train','validation'} or not p.get('source_ids') or not p.get('provenance'):
            raise ValueError('mean bank must carry original H train+validation provenance')
        if any(k not in mean_bank['values'] for k in keys): raise ValueError('mean bank missing group keys')
    result=[]
    for b in recipient_batches:
        validate_batch(b)
        # Singleton execution ensures donor readouts/layouts may differ in
        # padding and also provides the batch-one positive-control seam.
        for batch in _rows(b):
            if operation=='h_mean' and set(batch.ids) & set(mean_bank['provenance']['source_ids']):
                raise ValueError('recipient id occurs in H mean bank source')
            mapping=maps.get((batch.condition,batch.ids[0],batch.stream))
            donor=None
            if operation not in ('zero','h_mean','self_replay','empty'):
                if mapping is None: raise ValueError('explicit frozen donor map required')
                if mapping.get('supported'):
                    donor=donors.get((mapping['donor_condition'],mapping['donor_id'],mapping['donor_stream']))
                    if donor is None: raise ValueError('frozen donor absent from donor batches')
                    _check_map(batch,donor,mapping,operation)
            intact,base=_capture(model,batch,keys)
            intact_stats=_stats(batch,base,intact.logits)
            donor_capture=None
            if donor is not None: donor_capture,_=_capture(model,donor,keys)
            for name,group in groups:
                group=[tuple(k) for k in group]
                empty,empty_logits=_capture(model,batch,keys,{})
                replay={k:hooks.Replacement(intact.outputs[k],batch.attention_mask.to(base.device).bool()) for k in group}
                self_capture,self_logits=_capture(model,batch,keys,replay)
                error=max(_noop_error(base,empty_logits,batch),_noop_error(base,self_logits,batch))
                record=dict(task=batch.task,instance_id=batch.ids[0],condition=batch.condition,stream=batch.stream,
                            group=name,group_members=[list(k) for k in group],operation=operation,expected_token=int(batch.expected_token[0]),
                            opposite_token=int(batch.opposite_token[0]),honest_token=int(batch.honest_token[0]),
                            pressure_id=str(batch.records[0].get('pressure_id',batch.ids[0])),
                            source_provenance=batch.records[0],donor_provenance=mapping,
                            donor_seed=mapping.get('seed') if mapping else None,
                            self_replay_margin_error=error,assay_valid=True,supported=True,
                            degenerate=operation in ('self_replay','empty') or not group,
                            gate_valid=operation not in ('self_replay','empty') and bool(group))
                if donor is not None:
                    rt=batch.input_ids[0,batch.attention_mask[0].bool()]
                    dt=donor.input_ids[0,donor.attention_mask[0].bool()]
                    if torch.equal(rt.cpu(),dt.cpu()):
                        mapping=dict(mapping,degenerate=True,gate_valid=False,no_op=True)
                if mapping is not None:
                    record.update(donor_provenance=mapping,degenerate=mapping.get('degenerate',False) or not group,
                                  gate_valid=mapping.get('gate_valid',False) and bool(group),supported=mapping['supported'])
                if not record['supported']:
                    record['unsupported_reason']=mapping.get('unsupported_reason'); result.append(record); continue
                replacements={}
                for k in group:
                    original=intact.outputs[k]
                    mask=batch.attention_mask.to(original.device).bool()
                    if operation=='empty': continue
                    if operation=='zero': replacements[k]=hooks.Replacement(torch.zeros_like(original),mask)
                    elif operation=='h_mean':
                        value=mean_bank['values'][k].to(device=original.device,dtype=original.dtype).expand_as(original)
                        replacements[k]=hooks.Replacement(value,mask)
                    elif operation=='self_replay': replacements[k]=replay[k]
                    else:
                        replacements[k]=mapped_replacement(original,donor_capture.outputs[k],[mapping],
                                                            mask,donor.attention_mask.to(original.device))
                patched,logits=_capture(model,batch,keys,replacements)
                stats=_stats(batch,logits,patched.logits)
                for prefix,values in [('intact',intact_stats),('patched',stats)]:
                    for field,value in values.items(): record[f'{prefix}_{field}']=value[0].item()
                if mean_bank is not None and operation=='h_mean': record['mean_bank_provenance']=mean_bank['provenance']
                result.append(record)
    return result


def _pad_calibration_batch(batch, width):
    """Right-pad one positive-control row; never trim parent padding or tokens."""
    validate_batch(batch)
    if len(batch.ids)!=1:
        raise ValueError('positive calibration requires singleton geometry')
    if (not isinstance(batch.readout,torch.Tensor)
            or batch.readout.dtype not in (torch.int32,torch.int64)
            or batch.input_ids.dtype not in (torch.int32,torch.int64)):
        raise ValueError('positive calibration requires integer token/readout tensors')
    current=batch.input_ids.shape[1]
    if type(width) is not int or width<current:
        raise ValueError('positive calibration width must be integer and cannot truncate')
    if width==current: return batch
    padded=replace(batch,
                   input_ids=torch.nn.functional.pad(batch.input_ids,(0,width-current),value=0),
                   attention_mask=torch.nn.functional.pad(batch.attention_mask,(0,width-current),value=0))
    validate_batch(padded)
    return padded


def positive_control(model, recipient_batches, *, donor_batches, donor_maps):
    """Batch-one all-sender readout calibration, separate from ladder cells.

    Donor maps must explicitly name readout-to-readout mapping. Native item
    swaps and utility cyclic donors are both permitted; no answer filtering.
    Both singleton inputs retain all original padding and use the same padded
    width before capture: BF16 projection kernels can depend on sequence shape.
    This numerical calibration does not change score_cell's scientific path.
    """
    keys=hooks.all_component_keys(model)
    donors={}
    for b in donor_batches:
        validate_batch(b)
        for one in _rows(b): donors[(one.condition,one.ids[0],one.stream)]=one
    maps={(m['recipient_condition'],m['recipient_id'],m['recipient_stream']):m for m in donor_maps}
    output=[]
    for b in recipient_batches:
        validate_batch(b)
        for batch in _rows(b):
            m=maps[(batch.condition,batch.ids[0],batch.stream)]
            if not m.get('supported'): raise ValueError('positive-control donor map unsupported')
            donor=donors[(m['donor_condition'],m['donor_id'],m['donor_stream'])]
            if m['recipient_positions']!=batch.readout.tolist() or m['donor_positions']!=donor.readout.tolist():
                raise ValueError('positive control requires explicit readout-to-readout map')
            width=max(batch.input_ids.shape[1],donor.input_ids.shape[1])
            batch=_pad_calibration_batch(batch,width)
            donor=_pad_calibration_batch(donor,width)
            intact,base=_capture(model,batch,keys); dc,dl=_capture(model,donor,keys)
            replacements={k:mapped_replacement(intact.outputs[k],dc.outputs[k],[m],batch.attention_mask,donor.attention_mask) for k in keys}
            _,patched=_capture(model,batch,keys,replacements)
            error=float((patched-dl).abs().max())
            valid=torch.allclose(patched,dl,atol=1e-5,rtol=1e-5)
            if not valid: raise ValueError(f'positive control failed donor-logit recovery: {error}')
            output.append(dict(task=batch.task,instance_id=batch.ids[0],stream=batch.stream,
                               max_abs_logit_error=error,valid=bool(valid),
                               donor_choice_differs=bool(base.argmax(-1)!=dl.argmax(-1)),donor_provenance=m,
                               sender_keys=[list(k) for k in keys]))
    return output


def main(argv=None, tokenizer=None, model_loader=None):
    """Delegate staged execution while keeping intervention functions importable."""
    from component_analysis.ladder_pipeline import main as pipeline_main
    return pipeline_main(argv, tokenizer=tokenizer, model_loader=model_loader)


if __name__ == '__main__':
    raise SystemExit(main())
