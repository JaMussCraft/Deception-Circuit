"""The three prospectively frozen V6 followups; no candidate selection or API.

Q paths isolate direct residual -> normalization -> pre-RoPE per-head Q under
all-other-component-output clamps. They do not measure all mediated routes.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import time
from component_analysis import hooks, path_patching as pp, selective_v6 as core
from component_analysis.selective_v6_manifest import load_manifest, _scenario

STATES = ('intact','original_New30','release_17','clean_rescue_17','self_rescue_17',
          'ordinal_agree_New30','ordinal_disagree_New30','total_sender_13','path_Q27','path_Q26')
SENDER = ('head',13,23)
RESCUE = ('head',17,27)
RECEIVERS = (('q',17,27), ('q',17,26))


def truth_label(row):
    """Construction truth's item ordinal, explicitly not an answer-token match."""
    if row['target'] not in (row['item_1'], row['item_2']) or row['item_1'] == row['item_2']:
        raise ValueError('invalid construction truth label')
    return 1 if row['target'] == row['item_1'] else 2


def assign_donors(recipients, donors, excluded_scenarios):
    used_ids, used_scenarios, result = set(), set(), {}
    for row in sorted(recipients, key=lambda r:r['source_id']):
        pair = {}
        for arm in ('agree','disagree'):
            label = row['truth_label'] if arm == 'agree' else 3-row['truth_label']
            eligible = [d for d in donors if d['truth_label'] == label
                        and d['scenario_key'] not in excluded_scenarios | used_scenarios
                        and d['source_id'] not in used_ids | {row['donor_source_id']}]
            rank = lambda d:(hashlib.sha256(f"v6-followup-donor|20261026|{arm}|{row['source_id']}|{d['source_id']}".encode('utf-8')).hexdigest(),d['source_id'])
            if not eligible:
                raise ValueError(f'insufficient unique donor bin: {row["source_id"]} {arm}')
            chosen = min(eligible, key=rank)
            pair[arm] = chosen
            used_ids.add(chosen['source_id']); used_scenarios.add(chosen['scenario_key'])
        result[row['source_id']] = pair
    return result


def prepare(manifest_path, selection_path, smoke_path, prepared_path, proposal_path):
    """Read only frozen JSON/tokenizer sources, check feasibility before runtime."""
    from tokenizers import Tokenizer
    manifest = load_manifest(manifest_path)
    selection = json.loads(Path(selection_path).read_text())
    smoke = json.loads(Path(smoke_path).read_text())
    if selection['reported_conditions'] != list(STATES) or selection['receiver_head'] != [17,27] or selection['sender_head'] != [13,23] or selection['matched_receiver_q'] != [17,26] or selection['matched_receiver_is_null']:
        raise ValueError('frozen hypothesis mismatch')
    if not selection['reviewed'] or not smoke['reviewed'] or smoke['followup_selection_sha256'] != selection['bindings'].get(selection.get('supersedes_donor_arm_semantics_only','')):
        raise ValueError('unreviewed or stale selection')
    sources = dict(manifest['sources'])
    for path, expected in selection['bindings'].items():
        if core.sha256(path) != expected: raise ValueError('selection binding mismatch: '+path)
        sources[path] = expected
    for path in (manifest_path, selection_path, smoke_path, prepared_path, proposal_path):
        sources[str(Path(path).resolve())] = core.sha256(path)
    for path in (prepared_path,proposal_path):
        if manifest['sources'].get(str(Path(path).resolve())) != core.sha256(path):
            raise ValueError('donor source not bound by original manifest')
    prepared=json.loads(Path(prepared_path).read_text());proposal=json.loads(Path(proposal_path).read_text())
    tokenizer=Tokenizer.from_file(str(Path(manifest['tokenizer_id'])/'tokenizer.json'))
    original = {r['source_id']:r for r in proposal['families']['sdr']['recipients']}
    pool = proposal['families']['sdr']['neutral_h_donors']
    donors=[]
    def metadata(r, source_order, text, ids):
        item_ids=[tokenizer.encode(' '+r[k],add_special_tokens=False).ids for k in ('item_1','item_2')]
        if any(len(t)!=1 for t in item_ids) or f"{r['item_1']} or {r['item_2']}" not in text:
            raise ValueError('construction/rendered item order mismatch')
        slot=truth_label(r)
        if r['distractor'] != r['item_2' if slot==1 else 'item_1']: raise ValueError('construction alternate mismatch')
        return dict(item_1=r['item_1'],item_2=r['item_2'],item_token_ids=item_ids,truth_slot=slot,
                    truth_text=r['target'],alternate_text=r['distractor'],truth_token_id=item_ids[slot-1][0],
                    alternate_token_id=item_ids[2-slot][0],prompt_length=len(ids),source_order=source_order,
                    source_record_sha256=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())
    for donor_order,(sid, data) in enumerate(prepared['donors']['sdr'].items()):
        r=pool[sid]; stream=data['streams']['clean']; scenario=_scenario(data['scenario'])
        if r['instance_id'] != sid or data['source_id'] != sid or r['condition'] != 'honest' or r['slot_kind'] != 'neutral' or r['honest_twin_kind'] != 'neutral_clause':
            raise ValueError('not a frozen neutral-H source')
        if scenario != _scenario([r['entity'],[r['item_1'],r['item_2']]]) or stream['text'] != r['clean_prompt'] or tokenizer.encode(stream['text'],add_special_tokens=False).ids != stream['ids']:
            raise ValueError('donor source join/token mismatch')
        labels=[tokenizer.encode(' '+r[k],add_special_tokens=False).ids for k in ('target','distractor')]
        if any(len(t)!=1 for t in labels): raise ValueError('multitoken donor answer')
        donors.append(dict(source_id=sid,scenario_key=scenario,truth_label=truth_label(r),
                           truth_text=r['target'],item_1=r['item_1'],item_2=r['item_2'],
                           truthful_id=labels[0][0],alternate_answer_id=labels[1][0],
                           token_ids=stream['ids'],text=stream['text'],construction=metadata(r,donor_order,stream['text'],stream['ids'])))
    cases=[c for c in manifest['cases'] if c['case_id'] in selection['validation_case_ids']]
    if [c['case_id'] for c in cases] != selection['validation_case_ids'] or len(cases)!=64:
        raise ValueError('validation panel ordering mismatch')
    recipients=[]
    source_order={sid:i for i,sid in enumerate(original)}
    for c in cases:
        r=original[c['source_id']]['conditions']['H']
        if tokenizer.encode(' '+r['target'],add_special_tokens=False).ids != [c['truthful_id']]:
            raise ValueError('recipient construction truth join mismatch')
        c['construction']=metadata(r,source_order[c['source_id']],c['recipient_text'],c['recipient_token_ids'])
        if c['variant']=='H': recipients.append(dict(source_id=c['source_id'],truth_label=truth_label(r),donor_source_id=c['donor_source_id']))
    excluded={c['scenario_key'] for c in manifest['cases']}
    pairs=assign_donors(recipients,donors,excluded)
    for c in (c for c in cases if c['variant']=='H'):
        rc=c['construction']; rt={t[0] for t in rc['item_token_ids']}
        for arm,d in pairs[c['source_id']].items():
            dc=d['construction']; dt={t[0] for t in dc['item_token_ids']}
            d['recipient_comparison']=dict(unordered_answer_token_pair_match=rt==dt,truth_token_match=rc['truth_token_id']==dc['truth_token_id'],
                 any_answer_token_overlap=bool(rt & dt),recipient_prompt_length=rc['prompt_length'],donor_prompt_length=dc['prompt_length'])
    if len(pairs)!=16 or len({d['scenario_key'] for pair in pairs.values() for d in pair.values()})!=32:
        raise ValueError('requires exactly 32 unique donor scenarios')
    if len(smoke['case_ids'])!=16 or not set(smoke['case_ids'])<=set(selection['validation_case_ids']):
        raise ValueError('smoke panel mismatch')
    return dict(schema_version=1,status='candidate_not_frozen',sources=sources,manifest_path=str(Path(manifest_path).resolve()),
                selection_sha256=core.sha256(selection_path),smoke_sha256=core.sha256(smoke_path),
                selection=selection,smoke=smoke,donor_pool_count=len(donors),
                donor_truth_label_semantics='construction target item_1/item_2 ordinal, not shared lexical token',
                excluded_scenarios=sorted(excluded),pairs=pairs,cases=cases,
                original_donors={d['source_id']:d for d in donors if d['source_id'] in {c['donor_source_id'] for c in cases}},
                masks=manifest['masks'],model_identity=manifest['model_identity'],geometry=manifest['geometry'],
                tokenizer_id=manifest['tokenizer_id'],pad_token_id=manifest['pad_token_id'])


def synthetic_sender(clean_outputs, donor_outputs, donor_mask, mask, sender=SENDER):
    """Recipient-shaped clone with the sole declared own-final donor write."""
    replacement=core.final_replacements({sender:donor_outputs[sender]},donor_mask,mask)[sender]
    value=clean_outputs[sender].clone()
    return {sender:hooks._write(value,replacement)}


def make_streams(model, ids, mask, clean, donor, donor_mask, sender, targets, alternatives):
    import torch
    keys=set(hooks.all_component_keys(model))
    bank={k:v for k,v in clean.outputs.items() if k != pp.READOUT_KEY}
    if set(bank)!=keys: raise ValueError('clean bank must contain exactly all component keys')
    if any(v.shape[:2] != ids.shape for v in bank.values()): raise ValueError('clean bank shape mismatch')
    corrupt=synthetic_sender(bank,donor.outputs,donor_mask,mask,sender)
    logits=pp._readout_of(model,clean)
    target=torch.as_tensor(targets,device=ids.device);alternate=torch.as_tensor(alternatives,device=ids.device)
    rows=torch.arange(len(ids),device=ids.device); metric=logits[rows,target]-logits[rows,alternate]
    return pp.Streams(ids,mask,core.last_nonpad(mask),target,alternate,bank,corrupt,
                      logits,logits,metric,metric,torch.zeros_like(metric))


def path_states(model, streams, clean, receivers=RECEIVERS, sender=SENDER):
    """Actual per-case empty/self/replay/Q-write controls, native and fp32."""
    import torch
    from dataclasses import replace
    controls={}; results={}
    def check(name,capture,expected=clean):
        native=torch.equal(capture.logits,expected.logits)
        fp32=torch.equal(pp._readout_of(model,capture),pp._readout_of(model,expected))
        controls[name+'_native_exact']=native;controls[name+'_fp32_exact']=fp32
        if not native or not fp32: raise RuntimeError('identity failure: '+name)
    def capture(replacements,components=()):
        return hooks.capture_forward(model,streams.input_ids,streams.attention_mask,
             positions=streams.positions,components=[pp.READOUT_KEY,*components],replacements=replacements)
    check('bank_replay',capture(streams.clean_outputs))
    induced=pp.receiver_inputs(model,streams,senders=[sender],receivers=receivers)
    clean_q=capture({},receivers)
    self_streams=replace(streams,corrupt_outputs={sender:streams.clean_outputs[sender].clone()})
    empty=pp.receiver_inputs(model,streams,senders=[],receivers=receivers)
    self_input=pp.receiver_inputs(model,self_streams,senders=[sender],receivers=receivers)
    position=torch.zeros_like(streams.attention_mask,dtype=torch.bool)
    position[torch.arange(len(position),device=position.device),streams.positions]=True
    for index,q in enumerate(receivers):
        for name,bank in [('empty',empty.outputs),('self_sender',self_input.outputs),('clean_q',clean_q.outputs),('self_q',clean_q.outputs)]:
            check(f'{q[2]}_{name}',capture({q:hooks.Replacement(bank[q],position)}))
        check(f'{q[2]}_false_mask',capture({q:hooks.Replacement(induced.outputs[q],torch.zeros_like(position))}))
        repl=hooks.Replacement(induced.outputs[q],position)
        # Capture all query heads at this layer to verify intended head/position
        # isolation. No write can affect another pre-RoPE Q in the same layer.
        sibling=[('q',q[1],h) for h in range(hooks.geometry(model)['num_heads'])]
        baseline=capture({},sibling)
        patched=capture({q:repl},sibling)
        for k in sibling:
            expected=hooks._write(baseline.outputs[k],repl) if k==q else baseline.outputs[k]
            if not torch.equal(expected,patched.outputs[k]): raise RuntimeError('Q slice isolation failed')
        controls[f'{q[2]}_q_isolation_exact']=True
        # Use the existing free-propagation primitive and verify its saved
        # native capture follows exactly the same intervention.
        logits=pp.readout_from_receivers(model,streams,{q:repl})
        if not torch.equal(logits,pp._readout_of(model,patched)): raise RuntimeError('path composition mismatch')
        results['path_Q27' if index==0 else 'path_Q26']=(logits,patched.logits)
    total=capture({sender:streams.corrupt_outputs[sender]})
    rows=torch.arange(len(position),device=position.device)
    independent=hooks.Replacement(streams.corrupt_outputs[sender][rows,streams.positions].unsqueeze(1),position)
    reproduced=capture({sender:independent})
    check('total_sender_independent',reproduced,total)
    results['total_sender_13']=(pp._readout_of(model,total),total.logits)
    return results,controls


def selected_cases(pack, mode):
    if mode in ('followup','dry-run'): return pack['cases']
    if mode != 'smoke': raise ValueError('unknown followup mode')
    selected=[c for c in pack['cases'] if c['case_id'] in pack['smoke']['case_ids']]
    if [c['case_id'] for c in selected] != pack['smoke']['case_ids']: raise ValueError('smoke order mismatch')
    return selected


def validate_receipt(receipt, pack_hash, selection_hash, runner_hash, code_hashes, mode, output_dir):
    expected=dict(review_status='approved',mode=mode,pack_sha256=pack_hash,selection_sha256=selection_hash,
                  runner_sha256=runner_hash,code_hashes=code_hashes)
    for k,v in expected.items():
        if receipt.get(k)!=v: raise ValueError('execution receipt mismatch: '+k)
    if Path(receipt.get('output_dir','')).resolve()!=Path(output_dir).resolve(): raise ValueError('receipt output mismatch')
    reserved=receipt.get('reserved_gpu_hours',0);remaining=receipt.get('remaining_gpu_hours_before',0)
    ceiling=.25 if mode=='smoke' else 2.4
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in (reserved,remaining)) or not 0 < reserved <= min(ceiling,remaining) or not 0 < remaining <= 2.4 or not receipt.get('reservation_id'):
        raise ValueError('invalid bounded reservation')


def code_bindings():
    # Bind the local source closure conservatively without importing models
    # on CPU dry runs (models registry imports analysis/config transitively).
    root=Path(__file__).resolve().parents[1]
    paths=list(root.glob('*.py'))
    for directory in ('component_analysis','models'):
        paths.extend((root/directory).glob('*.py'))
    return {str(p):core.sha256(p) for p in sorted(paths)}


def load_pack(path):
    pack=json.loads(Path(path).read_text())
    for source,expected in pack['sources'].items():
        if core.sha256(source)!=expected: raise ValueError('pack source mismatch: '+source)
    # Regenerate all deterministic joins/assignments rather than trusting a
    # hand-edited payload. Frozen status is the sole permitted root change.
    inputs=pack['prepare_inputs']
    rebuilt=prepare(**inputs)
    comparable={k:v for k,v in pack.items() if k not in ('status','prepare_inputs')}
    if comparable!={k:v for k,v in rebuilt.items() if k!='status'}: raise ValueError('pack differs from deterministic reconstruction')
    return pack


def score_batch(model, pack, cases, device='cuda'):
    import torch
    ids,mask=core.padded([c['recipient_token_ids'] for c in cases],pack['pad_token_id'],device)
    donor_ids,donor_mask=core.padded([c['donor_token_ids'] for c in cases],pack['pad_token_id'],device)
    keys=[('head',*h) for h in pack['masks']['new30']]
    initial,base,proof=core.identity_controls(model,ids,mask,keys)
    clean=hooks.capture_forward(model,ids,mask,components=hooks.all_component_keys(model)+[pp.READOUT_KEY],positions=core.last_nonpad(mask))
    if not torch.equal(clean.logits,initial.logits) or not torch.equal(pp._readout_of(model,clean),base):
        raise RuntimeError('full clean bank baseline mismatch')
    donor=hooks.capture_forward(model,donor_ids,donor_mask,components=keys,positions=core.last_nonpad(donor_mask))
    replacements=core.final_replacements(donor.outputs,donor_mask,mask)
    def capture(repl,components=()):
        return hooks.capture_forward(model,ids,mask,components=[pp.READOUT_KEY,*components],positions=core.last_nonpad(mask),replacements=repl)
    def pair(c): return pp._readout_of(model,c),c.logits
    new30=capture(replacements,[RESCUE])
    states={'intact':(base,clean.logits),'original_New30':pair(new30)}
    release={k:v for k,v in replacements.items() if k != RESCUE}
    states['release_17']=pair(capture(release))
    position=next(iter(replacements.values())).positions
    states['clean_rescue_17']=pair(capture(release | {RESCUE:hooks.Replacement(clean.outputs[RESCUE],position)}))
    sham=capture(release | {RESCUE:hooks.Replacement(new30.outputs[RESCUE],position)})
    proof['new30_self_native_exact']=torch.equal(sham.logits,new30.logits)
    proof['new30_self_fp32_exact']=torch.equal(pp._readout_of(model,sham),pp._readout_of(model,new30))
    if not proof['new30_self_native_exact'] or not proof['new30_self_fp32_exact']: raise RuntimeError('New30 self rescue identity failed')
    states['self_rescue_17']=pair(sham)
    ods=[pack['original_donors'][c['donor_source_id']] for c in cases]
    odl=hooks.readout_logits(model,donor.residual[:,-1])
    odvalues=core.metrics(odl,odl,[d['truthful_id'] for d in ods],[d['alternate_answer_id'] for d in ods],[d['truthful_id'] for d in ods])
    donor_capability=[dict(case_id=c['case_id'],arm='original',donor_source_id=c['donor_source_id'],metrics=v,native_argmax_id=int(n.argmax()),native_requested_correct=bool(n.argmax()==d['truthful_id'])) for c,d,v,n in zip(cases,ods,odvalues,donor.logits)]
    for arm in ('agree','disagree'):
        ds=[pack['pairs'][c['source_id']][arm] for c in cases]
        di,dm=core.padded([d['token_ids'] for d in ds],pack['pad_token_id'],device)
        dc=hooks.capture_forward(model,di,dm,components=keys+[pp.READOUT_KEY],positions=core.last_nonpad(dm))
        dl=pp._readout_of(model,dc)
        values=core.metrics(dl,dl,[d['truthful_id'] for d in ds],[d['alternate_answer_id'] for d in ds],[d['truthful_id'] for d in ds])
        donor_capability.extend(dict(case_id=c['case_id'],arm=arm,donor_source_id=d['source_id'],metrics=v,native_argmax_id=int(n.argmax()),native_requested_correct=bool(n.argmax()==d['truthful_id'])) for c,d,v,n in zip(cases,ds,values,dc.logits))
        states['ordinal_'+arm+'_New30']=pair(capture(core.final_replacements({k:dc.outputs[k] for k in keys},dm,mask)))
    targets=[c['requested_target_id'] for c in cases];alternates=[c['alternate_answer_id'] for c in cases]
    streams=make_streams(model,ids,mask,clean,donor,donor_mask,SENDER,targets,alternates)
    path,controls=path_states(model,streams,clean,receivers=RECEIVERS,sender=SENDER)
    # Independently reconstruct total sender directly from original donor's
    # own-final slice, without the synthetic recipient-shaped bank.
    independent=capture({SENDER:replacements[SENDER]})
    if not torch.equal(independent.logits,path['total_sender_13'][1]) or not torch.equal(pp._readout_of(model,independent),path['total_sender_13'][0]):
        raise RuntimeError('original donor total sender reconstruction failed')
    controls['original_donor_total_sender_native_exact']=True
    controls['original_donor_total_sender_fp32_exact']=True
    states.update(path)
    rows=[]
    for name in STATES:
        logits,native=states[name]
        values=core.metrics(logits,base,targets,alternates,[c['truthful_id'] for c in cases])
        for c,value,n,logit in zip(cases,values,native,logits):
            truth=c['truthful_id'];other=c['alternate_answer_id'] if truth==c['requested_target_id'] else c['requested_target_id']
            value['truth_oriented_margin']=float(logit[truth]-logit[other])
            rows.append(dict(case_id=c['case_id'],source_id=c['source_id'],scenario_key=c['scenario_key'],variant=c['variant'],stratum=c['stratum'],
                condition=name,metrics=value,native_argmax_id=int(n.argmax()),native_requested_correct=bool(n.argmax()==c['requested_target_id']),
                native_truthful_correct=bool(n.argmax()==truth),native_fp32_argmax_agree=bool(n.argmax()==logit.argmax()),
                recipient_construction=c['construction'],original_donor_source_id=c['donor_source_id'],donor_pair=pack['pairs'][c['source_id']],
                requested_target_id=c['requested_target_id'],alternate_answer_id=c['alternate_answer_id'],truthful_id=truth,
                selected_heads=([list(SENDER[1:])] if name=='total_sender_13' else [list(k[1:]) for k in keys if name!='release_17' or k!=RESCUE] if 'New30' in name or 'rescue' in name or name=='release_17' else []),
                receiver_q=list(RECEIVERS[0 if name=='path_Q27' else 1]) if name.startswith('path_Q') else None))
    return rows,dict(case_ids=[c['case_id'] for c in cases],recipient_positions=core.last_nonpad(mask).tolist(),donor_positions=core.last_nonpad(donor_mask).tolist(),**proof,**controls),donor_capability


def run(args):
    if args.mode=='prepare':
        inputs=dict(manifest_path=args.manifest,selection_path=args.selection,smoke_path=args.smoke_selection,prepared_path=args.prepared,proposal_path=args.proposal)
        pack=prepare(**inputs);pack['prepare_inputs']=inputs
        core._write_json(args.pack,pack)
        print(json.dumps(dict(pack=args.pack,donors=32,cases=64,status=pack['status'])))
        return
    pack=load_pack(args.pack);cases=selected_cases(pack,args.mode)
    hashes=code_bindings();pack_hash=core.sha256(args.pack)
    out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=False)
    plan=dict(mode=args.mode,pack_sha256=pack_hash,selection_sha256=pack['selection_sha256'],code_hashes=hashes,
              cases=len(cases),expected_rows=len(cases)*10,reported_conditions=STATES,case_ids=[c['case_id'] for c in cases],
              sources=pack['sources'],model_identity=pack['model_identity'],candidate_effects_for_selection=False,
              smoke_cases_reappear_in_main=True,no_automatic_retry=True)
    core._write_json(out/'plan.json',plan)
    if args.mode=='dry-run': print(json.dumps(plan,sort_keys=True));return
    if not args.execution_receipt: raise ValueError('reviewed execution receipt required')
    receipt=json.loads(Path(args.execution_receipt).read_text())
    validate_receipt(receipt,pack_hash,pack['selection_sha256'],core.sha256(__file__),hashes,args.mode,out)
    if pack['status']!='frozen': raise ValueError('root must freeze candidate pack before live execution')
    import torch
    if not os.environ.get('SLURM_JOB_ID') or not torch.cuda.is_available(): raise RuntimeError('Slurm GPU required')
    if importlib.metadata.version('nnsight')!='0.7.0': raise RuntimeError('pinned nnsight required')
    if 'A40' not in torch.cuda.get_device_name(): raise RuntimeError('frozen A40 hardware required')
    core.claim_receipt(args.execution_receipt,core.sha256(args.execution_receipt))
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    started=time.monotonic();snapshot=Path(pack['model_identity']['snapshot'])
    if not snapshot.is_absolute() or str(snapshot)!=pack['tokenizer_id'] or snapshot.name!=pack['model_identity']['revision']: raise ValueError('snapshot identity mismatch')
    for name,expected in pack['model_identity']['files'].items():
        if core.sha256(snapshot/name)!=expected: raise ValueError('model hash mismatch: '+name)
    model=hooks.load_analysis_model(str(snapshot),device='cuda');hooks._hf(model).eval()
    if hooks.attention_implementation(model)!='sdpa' or next(hooks._hf(model).parameters()).dtype!=torch.bfloat16: raise RuntimeError('requires BF16 SDPA')
    for k in ('num_layers','num_heads','head_dim'):
        if hooks.geometry(model)[k]!=pack['geometry'][k]: raise ValueError('geometry mismatch')
    core._write_json(out/'header.json',dict(plan,backend=hooks.describe(model),versions={n:importlib.metadata.version(n) for n in ('torch','transformers','nnsight')},
                         slurm_job_id=os.environ['SLURM_JOB_ID'],execution_receipt=receipt,execution_receipt_sha256=core.sha256(args.execution_receipt)))
    load_seconds=time.monotonic()-started;completed=0;batch_seconds=[]
    with (out/'rows.jsonl').open('x') as sink,(out/'controls.jsonl').open('x') as proof_sink,(out/'donor-capability.jsonl').open('x') as donor_sink:
        for start in range(0,len(cases),args.batch_size):
            batch_started=time.monotonic()
            rows,controls,donors=score_batch(model,pack,cases[start:start+args.batch_size])
            for row in rows:
                row.update(pack_sha256=pack_hash,selection_sha256=pack['selection_sha256'],runner_sha256=core.sha256(__file__))
                sink.write(json.dumps(row,allow_nan=False,sort_keys=True)+'\n')
            proof_sink.write(json.dumps(controls,allow_nan=False)+'\n')
            for row in donors: donor_sink.write(json.dumps(row,allow_nan=False)+'\n')
            for stream in (sink,proof_sink,donor_sink):stream.flush();os.fsync(stream.fileno())
            torch.cuda.synchronize();batch_seconds.append(time.monotonic()-batch_started);completed+=len(rows)
            print(json.dumps(dict(completed_rows=completed,batch_seconds=batch_seconds[-1])),flush=True)
    core._write_json(out/'completion.json',dict(completed_rows=completed,expected_rows=plan['expected_rows'],elapsed_seconds=time.monotonic()-started,
        model_integrity_load_seconds=load_seconds,batch_seconds=batch_seconds,peak_cuda_allocated_bytes=torch.cuda.max_memory_allocated(),pack_sha256=pack_hash))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['prepare','dry-run','smoke','followup'],required=True)
    parser.add_argument('--pack',required=True)
    for flag in ('manifest','selection','smoke-selection','prepared','proposal','output-dir','execution-receipt'):
        parser.add_argument('--'+flag)
    parser.add_argument('--batch-size',type=int,default=4)
    args=parser.parse_args(argv)
    if args.batch_size<1: parser.error('positive batch size required')
    required=('manifest','selection','smoke_selection','prepared','proposal') if args.mode=='prepare' else ('output_dir',)
    for key in required:
        if not getattr(args,key):parser.error('missing --'+key.replace('_','-'))
    run(args)


if __name__=='__main__':main()
