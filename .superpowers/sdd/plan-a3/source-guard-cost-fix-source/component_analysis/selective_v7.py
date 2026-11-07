"""Frozen V7 position bridge. Readout choices are not generation/refusal outcomes."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time
from component_analysis import hooks, selective_v6 as core
from component_analysis.selective_v6_followup import code_bindings
from component_analysis.selective_v6_manifest import load_manifest

STATES=('intact','new30_final','single17_final','release17_final','new30_prompt','single17_prompt','release17_prompt')
MAPPING='right-aligned-intersection-keep-clean-prefix'


def position_map(donor_mask, recipient_mask):
    """Actual nonpad indices; supports either padding side and heterogeneous rows."""
    import torch
    core.last_nonpad(donor_mask);core.last_nonpad(recipient_mask)
    if len(donor_mask)!=len(recipient_mask):raise ValueError('donor/recipient row mismatch')
    source=torch.zeros_like(recipient_mask,dtype=torch.long)
    positions=torch.zeros_like(recipient_mask,dtype=torch.bool)
    maps=[]
    for row,(dm,rm) in enumerate(zip(donor_mask,recipient_mask)):
        ds=torch.where(dm.bool())[0];rs=torch.where(rm.bool())[0];n=min(len(ds),len(rs))
        source[row,rs[-n:]]=ds[-n:];positions[row,rs[-n:]]=True
        maps.append(dict(recipient_length=len(rs),donor_length=len(ds),recipient_indices=rs[-n:].tolist(),donor_indices=ds[-n:].tolist(),
                         recipient_ordinals=list(range(len(rs)-n,len(rs))),donor_ordinals=list(range(len(ds)-n,len(ds))),recipient_final_index=int(rs[-1]),donor_final_index=int(ds[-1]),mapped_count=n,unmapped_count=len(rs)-n,mapped_fraction=n/len(rs)))
    return source,positions,maps


def aligned_replacements(bank, donor_mask, recipient_mask):
    source,positions,_=position_map(donor_mask,recipient_mask)
    result={}
    for key,value in bank.items():
        if key[0]!='head' or value.shape[:2]!=donor_mask.shape:raise ValueError('invalid donor head bank')
        gathered=value.gather(1,source.unsqueeze(-1).expand(-1,-1,value.shape[-1]))
        result[key]=hooks.Replacement(gathered,positions)
    return result


def replacements(bank, donor_mask, recipient_mask, support):
    if support=='final':return core.final_replacements(bank,donor_mask,recipient_mask)
    if support=='prompt':return aligned_replacements(bank,donor_mask,recipient_mask)
    raise ValueError('unknown support')


def self_replacements(clean_bank, donor_replacements):
    """Keep recipient own coordinates; only the write mask comes from donors."""
    return {k:hooks.Replacement(clean_bank[k],r.positions) for k,r in donor_replacements.items()}


def prepare(manifest_path, selection_path):
    manifest=load_manifest(manifest_path,verify_sources=True)
    selection=json.loads(Path(selection_path).read_text())
    if selection.get('status')!='frozen' or selection.get('conditions')!=list(STATES) or selection.get('mapping')!=MAPPING or selection.get('batch_size')!=4:raise ValueError('frozen design mismatch')
    if Path(selection['manifest_path']).resolve()!=Path(manifest_path).resolve() or selection['manifest_sha256']!=core.sha256(manifest_path):raise ValueError('manifest binding mismatch')
    if core.sha256(selection['design_path'])!=selection['design_sha256']:raise ValueError('design binding mismatch')
    cases=[c for c in manifest['cases'] if c['family']=='sdr' and c['split']=='validation']
    if len(cases)!=64 or [c['case_id'] for c in cases]!=selection['case_ids']:raise ValueError('fixed case coverage/order mismatch')
    masks=selection['masks'];new=[tuple(h) for h in manifest['masks']['new30']]
    if len(set(new))!=30 or masks['new30']!=manifest['masks']['new30'] or masks['single17']!=[[17,27]] or masks['release17']!=[list(h) for h in new if h!=(17,27)]:raise ValueError('fixed support mismatch')
    smoke=[c for c in cases if c['case_id'] in selection['smoke_case_ids']]
    if len(smoke)!=16 or [c['case_id'] for c in smoke]!=selection['smoke_case_ids']:raise ValueError('smoke coverage mismatch')
    first={}
    for c in cases:
        cell=(c['stratum']['designation_polarity'],c['stratum']['item_polarity'])
        first.setdefault(cell,c['scenario_key'])
    if len(first)!=4 or {c['scenario_key'] for c in smoke}!=set(first.values()):raise ValueError('smoke stratum mismatch')
    # Recover original honest-donor answer labels only from manifest-bound V5 sources.
    from tokenizers import Tokenizer
    proposals=[p for p in manifest['sources'] if Path(p).name=='v2-inputs-proposal.json']
    if len(proposals)!=1:raise ValueError('original donor provenance source missing')
    pool=json.loads(Path(proposals[0]).read_text())['families']['sdr']['neutral_h_donors']
    tokenizer=Tokenizer.from_file(str(Path(manifest['tokenizer_id'])/'tokenizer.json'))
    cases=[dict(c) for c in cases]
    for c in cases:
        d=pool[c['donor_source_id']]
        if d['clean_prompt']!=c['donor_text'] or tokenizer.encode(d['clean_prompt'],add_special_tokens=False).ids!=c['donor_token_ids']:raise ValueError('original donor join mismatch')
        labels=[tokenizer.encode(' '+d[k],add_special_tokens=False).ids for k in ('target','distractor')]
        if any(len(t)!=1 for t in labels):raise ValueError('multitoken donor label')
        c['donor_requested_target_id']=labels[0][0];c['donor_alternate_answer_id']=labels[1][0]
    return manifest,selection,cases


def validate_receipt(receipt, plan, mode, output_dir):
    expected={k:plan[k] for k in ('manifest_sha256','selection_sha256','runner_sha256','code_hashes','batch_size')}
    expected.update(review_status='approved',mode=mode,gpu_type='A40',gpu_count=1)
    for k,value in expected.items():
        if receipt.get(k)!=value:raise ValueError('execution receipt mismatch: '+k)
    if Path(receipt.get('output_dir','')).resolve()!=Path(output_dir).resolve():raise ValueError('receipt output mismatch')
    limit=600 if mode=='smoke' else 900
    reserved=receipt.get('reserved_gpu_hours',0);remaining=receipt.get('remaining_gpu_hours_before',0);wall=receipt.get('max_wall_seconds',0)
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in (reserved,remaining,wall)) or not 0<wall<=limit or not 0<reserved<=min(limit/3600,remaining) or reserved*3600<wall or not 0<remaining<=1.9833333334:raise ValueError('invalid reservation budget')
    if not receipt.get('reservation_id') or not receipt.get('source_commit'):raise ValueError('missing reservation/provenance')
    wrapper=Path(receipt.get('wrapper_path',''))
    if not wrapper.is_absolute() or not wrapper.is_file() or core.sha256(wrapper)!=receipt.get('wrapper_sha256'):raise ValueError('wrapper binding mismatch')


def control_proofs(model, ids, mask, clean, base, replacement, clean_bank):
    """Exact backend self/false identities and earliest-layer full-head writes."""
    import torch
    pos=core.last_nonpad(mask);proof={}
    def capture(repl,components=()):
        return hooks.capture_forward(model,ids,mask,positions=pos,components=list(components),replacements=repl)
    def compare(name,cap):
        fp=hooks.readout_logits(model,cap.residual[:,-1])
        for backend,a,b in [('native',cap.logits,clean.logits),('fp32',fp,base)]:
            proof[name+'_'+backend+'_exact']=torch.equal(a,b)
            proof[name+'_'+backend+'_max_abs']=float((a.float()-b.float()).abs().max())
            if not torch.equal(a,b):raise RuntimeError('identity failure: '+name+' '+backend)
    compare('self',capture(self_replacements(clean_bank,replacement)))
    compare('false_mask',capture({k:hooks.Replacement(r.value,torch.zeros_like(r.positions)) for k,r in replacement.items()}))
    earliest=min(k[1] for k in replacement)
    siblings=[('head',earliest,h) for h in range(hooks.geometry(model)['num_heads'])]
    initial=capture({},siblings);patched=capture(replacement,siblings)
    differences=[]
    for k in siblings:
        expected=hooks._write(initial.outputs[k],replacement[k]) if k in replacement else initial.outputs[k]
        actual=patched.outputs[k];differences.append(float((actual.float()-expected.float()).abs().max()))
        if not torch.equal(expected,actual):raise RuntimeError('head/row/pad/prefix write isolation failure')
    proof.update(write_isolation_exact=True,write_isolation_max_abs=max(differences),write_layer=earliest,write_checked_heads=len(siblings),write_checked_positions=int(mask.numel()))
    return proof


def score_batch(model,manifest,selection,cases,device='cuda',smoke=False):
    import torch
    ids,mask=core.padded([c['recipient_token_ids'] for c in cases],manifest['pad_token_id'],device)
    di,dm=core.padded([c['donor_token_ids'] for c in cases],manifest['pad_token_id'],device)
    keys=[('head',*h) for h in selection['masks']['new30']]
    clean,base,proof=core.identity_controls(model,ids,mask,keys)
    donor=hooks.capture_forward(model,di,dm,components=keys,positions=core.last_nonpad(dm))
    _,_,maps=position_map(dm,mask)
    for c,m in zip(cases,maps):m['donor_token_sha256']=hashlib.sha256(json.dumps(c['donor_token_ids'],separators=(',',':')).encode()).hexdigest()
    states={'intact':(base,clean.logits)};controls={}
    for name in STATES[1:]:
        set_name,support=name.rsplit('_',1);selected={('head',*h) for h in selection['masks'][set_name]}
        rep=replacements({k:v for k,v in donor.outputs.items() if k in selected},dm,mask,support)
        if smoke or set_name=='new30':controls[name]=control_proofs(model,ids,mask,clean,base,rep,clean.outputs)
        cap=hooks.capture_forward(model,ids,mask,components=[],positions=core.last_nonpad(mask),replacements=rep)
        states[name]=(hooks.readout_logits(model,cap.residual[:,-1]),cap.logits)
    targets=[c['requested_target_id'] for c in cases];alternates=[c['alternate_answer_id'] for c in cases];truths=[c['truthful_id'] for c in cases]
    rows=[]
    for name in STATES:
        logits,native=states[name]
        values=core.metrics(logits,base,targets,alternates,truths)
        for c,value,n,l,m in zip(cases,values,native,logits,maps):
            truth=c['truthful_id'];other=c['alternate_answer_id'] if truth==c['requested_target_id'] else c['requested_target_id']
            value['truth_oriented_margin']=float(l[truth]-l[other])
            rows.append(dict(case_id=c['case_id'],source_id=c['source_id'],scenario_key=c['scenario_key'],variant=c['variant'],stratum=c['stratum'],condition=name,metrics=value,
                requested_target_id=c['requested_target_id'],alternate_answer_id=c['alternate_answer_id'],truthful_id=truth,donor_source_id=c['donor_source_id'],
                native_argmax_id=int(n.argmax()),native_requested_correct=bool(n.argmax()==c['requested_target_id']),native_truthful_correct=bool(n.argmax()==truth),native_fp32_argmax_agree=bool(n.argmax()==l.argmax()),
                native_requested_margin=float(n[c['requested_target_id']]-n[c['alternate_answer_id']]),native_truth_oriented_margin=float(n[truth]-n[other]),
                selected_heads=[] if name=='intact' else selection['masks'][name.rsplit('_',1)[0]],position_support='none' if name=='intact' else name.rsplit('_',1)[1],mapping=m))
    # Frozen original donor labels are explicit manifest fields, independently of recipient labels.
    dl=hooks.readout_logits(model,donor.residual[:,-1])
    dt=[c['donor_requested_target_id'] for c in cases];da=[c['donor_alternate_answer_id'] for c in cases]
    dv=core.metrics(dl,dl,dt,da,dt)
    capability=[dict(case_id=c['case_id'],donor_source_id=c['donor_source_id'],requested_target_id=t,alternate_answer_id=a,truthful_id=t,metrics=v,
        native_argmax_id=int(n.argmax()),native_requested_correct=bool(n.argmax()==t),native_truthful_correct=bool(n.argmax()==t),native_requested_margin=float(n[t]-n[a])) for c,t,a,v,n in zip(cases,dt,da,dv,donor.logits)]
    return rows,dict(case_ids=[c['case_id'] for c in cases],baseline=proof,conditions=controls),capability


def run(args):
    manifest,selection,cases=prepare(args.manifest,args.selection)
    if args.batch_size!=4:raise ValueError('frozen batch size is four')
    if args.mode=='smoke':cases=[c for c in cases if c['case_id'] in selection['smoke_case_ids']]
    hashes=code_bindings();out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=False)
    plan=dict(schema_version=1,mode=args.mode,manifest_sha256=core.sha256(args.manifest),selection_sha256=core.sha256(args.selection),runner_sha256=core.sha256(__file__),code_hashes=hashes,batch_size=4,
        padding_side='right',batch_case_ids=[[c['case_id'] for c in cases[i:i+4]] for i in range(0,len(cases),4)],cases=len(cases),expected_rows=len(cases)*7,case_ids=[c['case_id'] for c in cases],reported_conditions=list(STATES),source_hashes=manifest['sources'],model_identity=manifest['model_identity'],mapping=MAPPING,
        no_generation=True,no_paid_api=True,smoke_cases_reappear_in_main=True,release_semantics='recompute released head in perturbed network',historical_anchor_dir=selection['historical_anchor_dir'],
        metrics_semantics='fp32 requested-minus-alternative; drop=intact-condition; KL(intact||condition); native numerical margins use native subtraction',historical_full_vocab_available=False)
    core._write_json(out/'plan.json',plan)
    if args.mode=='dry-run':print(json.dumps(dict(cases=len(cases),expected_rows=plan['expected_rows'],output_dir=str(out))));return
    if not args.execution_receipt:raise ValueError('execution receipt required')
    receipt=json.loads(Path(args.execution_receipt).read_text());validate_receipt(receipt,plan,args.mode,out)
    import torch
    if not os.environ.get('SLURM_JOB_ID') or not torch.cuda.is_available():raise RuntimeError('Slurm GPU required')
    if importlib.metadata.version('nnsight')!='0.7.0' or 'A40' not in torch.cuda.get_device_name() or torch.cuda.device_count()!=1:raise RuntimeError('one A40 and pinned nnsight required')
    core.claim_receipt(args.execution_receipt,core.sha256(args.execution_receipt))
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    started=time.monotonic();snapshot=Path(manifest['model_identity']['snapshot'])
    if not snapshot.is_absolute() or str(snapshot)!=manifest['tokenizer_id'] or snapshot.name!=manifest['model_identity']['revision']:raise ValueError('snapshot identity mismatch')
    for name,expected in manifest['model_identity']['files'].items():
        if core.sha256(snapshot/name)!=expected:raise ValueError('model hash mismatch: '+name)
    model=hooks.load_analysis_model(str(snapshot),device='cuda');hooks._hf(model).eval()
    if hooks.attention_implementation(model)!='sdpa' or next(hooks._hf(model).parameters()).dtype!=torch.bfloat16:raise RuntimeError('requires BF16 SDPA')
    for k in ('num_layers','num_heads','head_dim'):
        if hooks.geometry(model)[k]!=manifest['geometry'][k]:raise ValueError('geometry mismatch')
    core._write_json(out/'header.json',dict(plan,backend=hooks.describe(model),device=torch.cuda.get_device_name(),versions={n:importlib.metadata.version(n) for n in ('torch','transformers','nnsight')},execution_receipt=receipt,execution_receipt_sha256=core.sha256(args.execution_receipt),slurm_job_id=os.environ['SLURM_JOB_ID']))
    load_seconds=time.monotonic()-started;completed=0;batch_seconds=[]
    with (out/'rows.jsonl').open('x') as sink,(out/'controls.jsonl').open('x') as controls,(out/'donor-capability.jsonl').open('x') as donors:
        for start in range(0,len(cases),4):
            began=time.monotonic();rows,proof,capability=score_batch(model,manifest,selection,cases[start:start+4],smoke=args.mode=='smoke')
            for stream,items in [(sink,rows),(controls,[proof]),(donors,capability)]:
                for row in items:
                    row.update(manifest_sha256=plan['manifest_sha256'],selection_sha256=plan['selection_sha256'],runner_sha256=plan['runner_sha256'])
                    stream.write(json.dumps(row,allow_nan=False,sort_keys=True)+'\n')
                stream.flush();os.fsync(stream.fileno())
            torch.cuda.synchronize();batch_seconds.append(time.monotonic()-began);completed+=len(rows)
            print(json.dumps(dict(completed_rows=completed,batch_seconds=batch_seconds[-1])),flush=True)
    if completed!=plan['expected_rows']:raise RuntimeError('incomplete row coverage')
    core._write_json(out/'completion.json',dict(mode=args.mode,completed_rows=completed,expected_rows=plan['expected_rows'],elapsed_seconds=time.monotonic()-started,model_integrity_load_seconds=load_seconds,batch_seconds=batch_seconds,peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),manifest_sha256=plan['manifest_sha256'],selection_sha256=plan['selection_sha256'],runner_sha256=plan['runner_sha256'],unique_donor_count=len({c['donor_source_id'] for c in cases}),artifact_sha256={name:core.sha256(out/name) for name in ('plan.json','header.json','rows.jsonl','controls.jsonl','donor-capability.jsonl')}))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','selection','output-dir'):parser.add_argument('--'+name,required=True)
    parser.add_argument('--mode',choices=['dry-run','smoke','main'],required=True)
    parser.add_argument('--execution-receipt');parser.add_argument('--batch-size',type=int,default=4)
    run(parser.parse_args(argv))

if __name__=='__main__':main()
