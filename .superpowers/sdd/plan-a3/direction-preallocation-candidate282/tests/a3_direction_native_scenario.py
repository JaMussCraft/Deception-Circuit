"""Test-only bounded native scenario; never a production admission or dataset."""
from __future__ import annotations
import argparse
import copy
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import time
from types import SimpleNamespace
import numpy as np
import torch
from component_analysis import a3_direction_runtime as r
from tests.test_a3_direction_runtime import _real_injected_design
from tests.helpers import tiny_config


def tiny_model():
    from nnsight import NNsight
    from transformers import LlamaForCausalLM
    torch.manual_seed(91)
    plain=LlamaForCausalLM(tiny_config(num_hidden_layers=1,attn_implementation='sdpa')).eval()
    with torch.no_grad():
        for p in plain.parameters():p.zero_()
        plain.model.embed_tokens.weight.normal_(mean=0,std=.2)
        plain.model.embed_tokens.weight[:,0]=1
        plain.model.embed_tokens.weight[:,1]=torch.arange(101)/5
        plain.model.norm.weight.fill_(1)
        for layer in plain.model.layers:
            layer.input_layernorm.weight.fill_(1);layer.post_attention_layernorm.weight.fill_(1)
            for j in range(layer.self_attn.v_proj.weight.shape[0]):layer.self_attn.v_proj.weight[j,j]=1
            layer.self_attn.o_proj.weight.copy_(torch.eye(64)*.1)
        plain.lm_head.weight[1,0]=1;plain.lm_head.weight[2,1]=1
    return NNsight(plain),plain


def model_identity(plain):
    digest=hashlib.sha256()
    tensors=dict(plain.state_dict())
    tensors.update({'buffer:'+k:v for k,v in plain.named_buffers()})
    for name,value in sorted(tensors.items()):
        array=value.detach().cpu().contiguous().numpy()
        digest.update(name.encode());digest.update(str(array.dtype).encode());digest.update(str(array.shape).encode());digest.update(array.tobytes())
    return dict(state_sha256=digest.hexdigest(),configuration=json.loads(json.dumps(plain.config.to_dict(),sort_keys=True)),attention_implementation=plain.config._attn_implementation,
        parameters=sum(p.numel() for p in plain.parameters()),device=str(next(plain.parameters()).device),dtype=str(next(plain.parameters()).dtype))


def source_identity():
    result=r.artifacts.code_hashes()
    for name in ('tests/a3_direction_native_scenario.py','tests/test_a3_direction_runtime.py','tests/helpers.py'):
        result[name]=r.common.file_hash(r.ladder.REPO/name)
    return result


def scenario_init(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    r.require(not (root/'scenario').exists(),'scenario initialization is immutable')
    design,protocol=_real_injected_design()
    r.ladder.write_artifact(root/'design.json',design);r.ladder.write_artifact(root/'direction_protocol.json',protocol)
    _,plain=tiny_model();identity=model_identity(plain)
    model_path=root/'tiny-model'
    def writer(path):
        np.savez(path/'state.npz',**{k:v.detach().cpu().numpy() for k,v in plain.state_dict().items()})
        (path/'config.json').write_text(json.dumps(plain.config.to_dict(),sort_keys=True)+'\n')
        r.artifacts._finish(path)
    r.common.publish(model_path,writer)
    r.publish_object(root/'scenario',dict(kind='a3_injected_native_verification_v1',injected=True,scientific_execution=False,execution_authorized=False,
        source_hashes=source_identity(),model_identity=identity,model_reference=r.pipeline._bundle_byte_reference(model_path),
        design_sha256=r.workload.digest(design),protocol_sha256=r.workload.digest(protocol)))


def verify_scenario(root,*,load_model=True):
    root=Path(root);scenario=r.read_object(root/'scenario')
    r.require(scenario['source_hashes']==source_identity(),'verification source changed')
    r.require(r.pipeline._bundle_byte_reference(root/'tiny-model')==scenario['model_reference'],'tiny base model backing changed')
    design=r.ladder.read_artifact(root/'design.json');protocol=r.ladder.read_artifact(root/'direction_protocol.json')
    r.require(r.workload.digest(design)==scenario['design_sha256'] and r.workload.digest(protocol)==scenario['protocol_sha256'],'frozen scenario inputs changed')
    if not load_model:return design,protocol,None,None
    model,plain=tiny_model()
    with np.load(root/'tiny-model'/'state.npz',allow_pickle=False) as arrays:
        plain.load_state_dict({k:torch.from_numpy(np.array(arrays[k],copy=True)) for k in arrays.files},strict=True)
    r.require(model_identity(plain)==scenario['model_identity'],'full tiny model state/config differs across process')
    return design,protocol,model,plain


def inventory(root,design,protocol,stage,*,fits=None,selected=None):
    value=r.workload.build_inventory(design,protocol,stage=stage,fits=fits,selected=selected)
    path=Path(root)/'inventory'/stage
    if path.exists():r.require(r.workload.digest(r.read_object(path))==r.workload.digest(value),'frozen inventory changed')
    else:r.publish_object(path,value)
    return value


def complete_ids(root,panel):
    ids=[]
    for path in (Path(root)/'runtime-shards').glob('*'):
        if not (path/'COMPLETE.json').exists():continue
        value=json.loads((path/'rows.jsonl').open().readline())
        if value['panel']==panel:ids.append(path.name)
    return ids


def _case_invocations(design,inv,part):
    r.require(design.get('injected') is True,'pilot verification batching is injected-only')
    r.workload._validate_inventory(inv)
    r.require(inv['stage']==('prefit' if part=='prefit' else 'selected-pilot'),'pilot verification stage differs')
    return inv['packing_invocations'] or r._serial_invocations(inv)


def _case_binding(design,protocol,inv,invocation,part,binding,selected_path):
    return dict(kind='a3_injected_verification_pilot_case_v1',injected=True,execution_authorized=False,
        scenario_binding=binding,design_sha256=r.workload.digest(design),protocol_sha256=r.workload.digest(protocol),
        inventory_sha256=inv['inventory_sha256'],invocation=invocation,part=part,
        selected_reference=None if selected_path is None else r.pipeline._bundle_byte_reference(selected_path))


def _read_pilot_case(path,model,design,protocol,inv,invocation,part,binding,selected_path):
    r.artifacts._complete(path)
    record=r.artifacts._strict_json(path/'case.json')
    r.require(record['binding']==json.loads(json.dumps(_case_binding(design,protocol,inv,invocation,part,binding,selected_path))),
        'verification pilot case source/model/inventory/scope changed')
    payload=r.read_object(path/'numeric');scope=r._pilot_scope_measurement(design,invocation)
    r.require(payload['injected'] is True and payload['source_commit']==protocol['commit']
        and payload['timing_only'] is (part=='prefit'),'verification numeric source/stage differs')
    r.require(payload['runtime_profile']==r.runtime_kernel_identity(model),'verification original runtime differs')
    if payload.get('evidence') is not None:
        proof=r._CompletedPackingProof(path/'numeric');proof.proof.check(scope)
        r._exact_pilot_scope(proof.proof._rows,list(proof.proof._specs.values()),scope)
        receipt=payload['evidence']['runner_receipt']
    else:
        proof=r._SerialNumericProof(path/'numeric');proof.check_scope(scope)
        r._exact_pilot_scope(proof.rows,proof.specs,scope);receipt=payload['receipt']
    if selected_path is not None:
        r.require(payload['numeric_backing_references']=={str(Path(selected_path).absolute()):r.pipeline._bundle_byte_reference(selected_path)},
            'verification selected numeric backing differs')
    samples=record['samples']
    r.require(samples and all(x.get('synchronized') is True and x.get('seconds',0)>0 for x in samples),'verification original actual timers missing')
    positives=payload['positive_controls'];keys={(x['task'],x['condition'],x['stream'],x['instance_id']) for x in positives}
    wanted={(x['source_task'],x['condition'],x['stream'],x['instance_id']) for x in scope['timing_inputs']}
    r.require(len(keys)==len(positives) and keys==wanted and all(x.get('valid') is True for x in positives),'verification actual own controls incomplete')
    batches=r._expected_pilot_batches(design,invocation);identity=dict(injected=True,numeric_profile=invocation['profile'])
    for batch in batches:
        for i in range(len(batch.ids)):
            r.runner._positive_reference({'positive_controls':positives},batch,i,r.runner.profile_identity(identity),identity,model)
    cells=[dict(x) for values in (receipt['scope']['batches'] if 'scope' in receipt else receipt['batches']).values() for x in values]
    return dict(evidence=payload.get('evidence'),receipt=receipt,samples=samples,positive_controls=positives,
        positive_samples=record['positive_samples'],lookup_scope_seconds=record['lookup_scope_seconds'],
        packing_overhead=record.get('packing_overhead'),batches=batches,cells=cells,
        local_axes={},axis_count=len({x['axis_sha256'] for x in cells}))


def pilot_cases(model,design,protocol,inv,*,root,part,case_ids,binding,selected_path=None,resume=False):
    """Execute selected original cases; this never publishes a whole pilot receipt."""
    invocations=_case_invocations(design,inv,part);ids=list(case_ids);wanted={x['invocation_id'] for x in invocations}
    r.require(ids and len(ids)==len(set(ids)) and set(ids)<=wanted,'unique known verification pilot case IDs required')
    paths=[];axes=None
    if selected_path is not None:
        selected,_=r.read_bundle(selected_path);axes=r.load_selected_axes(selected_path,selected)
    for invocation in invocations:
        if invocation['invocation_id'] not in ids:continue
        path=Path(root)/'pilot-verification-cases'/part/invocation['invocation_id']
        if path.exists():
            r.require(resume,'existing verification pilot case requires resume')
            _read_pilot_case(path,model,design,protocol,inv,invocation,part,binding,selected_path);paths.append(path);continue
        start=time.perf_counter()
        from component_analysis import hooks
        original=hooks.capture_forward;forward_calls=[0]
        def counted(*args,**kwargs):forward_calls[0]+=1;return original(*args,**kwargs)
        try:
            hooks.capture_forward=counted
            result=r._pilot_invocation(model,design,protocol,invocation,axes=axes,root=root,guard=lambda:None)
        finally:hooks.capture_forward=original
        scope=r._pilot_scope_measurement(design,invocation)
        numeric=dict(injected=True,timing_only=part=='prefit',source_commit=protocol['commit'],runtime_profile=r.runtime_kernel_identity(model),
            positive_controls=result['positive_controls'],numeric_backing_references={} if selected_path is None else
                {str(Path(selected_path).absolute()):r.pipeline._bundle_byte_reference(selected_path)})
        if result['evidence'] is not None:numeric.update(evidence=result['evidence'],measurement=scope)
        else:numeric.update(kind='a3_serial_numeric_invocation_v1',actual_execution=True,receipt=result['receipt'])
        record=dict(binding=_case_binding(design,protocol,inv,invocation,part,binding,selected_path),samples=result['samples'],
            positive_samples=result['positive_samples'],lookup_scope_seconds=result['lookup_scope_seconds'],packing_overhead=result.get('packing_overhead'),
            original_case_seconds=time.perf_counter()-start,original_case_forward_calls=forward_calls[0],
            original_samples_are_actual=True,aggregate_reexecutes_case=False)
        def writer(directory):
            r.publish_object(directory/'numeric',numeric);r.common.write_json(directory/'case.json',record);r.artifacts._finish(directory)
        r.common.publish(path,writer)
        _read_pilot_case(path,model,design,protocol,inv,invocation,part,binding,selected_path);paths.append(path)
    return [r.object_reference(path) for path in paths]


def aggregate_pilot_cases(model,design,protocol,inv,*,root,part,binding,selected_path=None,startup_seconds=0,prepared_target=None):
    """Replay exact authenticated case numbers; all new reconciliation work executes."""
    invocations=_case_invocations(design,inv,part);base=Path(root)/'pilot-verification-cases'/part
    wanted=[x['invocation_id'] for x in invocations]
    r.require(base.is_dir() and {x.name for x in base.iterdir()}==set(wanted),'full original pilot case coverage required before aggregate')
    values={x['invocation_id']:_read_pilot_case(base/x['invocation_id'],model,design,protocol,inv,x,part,binding,selected_path) for x in invocations}
    references=[r.object_reference(base/x) for x in wanted];replayed=[];original=r._pilot_invocation
    def replay(_model,_design,_protocol,invocation,**kwargs):
        r.require(_model is model and r.workload.digest(_design)==r.workload.digest(design) and r.workload.digest(_protocol)==r.workload.digest(protocol),
            'verification replay target differs')
        r.require(invocation==next(x for x in invocations if x['invocation_id']==invocation['invocation_id']),'verification replay scope differs')
        replayed.append(invocation['invocation_id']);return values[invocation['invocation_id']]
    selected=None if selected_path is None else r.read_bundle(selected_path)[0]
    began=time.perf_counter()
    args=SimpleNamespace(pilot_part=part,selected=selected_path) if prepared_target is None else prepared_target.args
    guard=(lambda:None) if prepared_target is None else ((lambda:verify_scenario(root,load_model=False) and None)
        if isinstance(prepared_target,_InjectedPreparedPilotTarget) else (lambda:r.live_guard(design,protocol,args,inv)))
    try:
        r._pilot_invocation=replay
        result=r.run_pilot(model,design,protocol,inv,root=root,args=args,
            guard=guard,startup_seconds=startup_seconds,selected=selected,prepared_target=prepared_target)
    finally:r._pilot_invocation=original
    r.require(replayed==wanted and [r.object_reference(base/x) for x in wanted]==references,'verification aggregate source/order changed')
    r.publish_object(Path(root)/'pilot-verification-aggregate'/part,dict(injected=True,execution_authorized=False,case_references=references,
        case_order=replayed,original_case_samples_replayed=True,case_forwards_reexecuted=False,new_reconciliation_work_is_actual=True,
        original_case_forward_calls=sum(r.artifacts._strict_json(base/x/'case.json')['original_case_forward_calls'] for x in wanted),
        new_reconciliation_seconds=time.perf_counter()-began,aggregate_receipt_reference=r.object_reference(Path(root)/'pilot'/part)))
    return result


_NATIVE_PREPARED_SEAL=object()


class _InjectedPreparedPilotTarget(r._PreparedPilotTarget):
    """Test-only immutable transport, with source guards and NO root authority.

    Production run_pilot admits the exact runtime type, never this subclass.
    This adapter is the explicit injected numerical reference path only.
    """
    def __init__(self,args,design,protocol,inv,result,namespace,root):
        r.require(design.get('injected') is True,'native prepared adapter is injected-only')
        self._seal=_NATIVE_PREPARED_SEAL;self._pid=r.os.getpid();self.args=args
        self.design=design;self.protocol=protocol;self.pilot=inv;self.root=Path(root)
        self.inventory,self.entry_references,self.namespace,self.witness,self.observed_io,self.observed_resources=result
        self._inventory=self.inventory;self._references=self.entry_references
        self._binding=r._freeze_json(dict(namespace_policy=namespace,receiver_resources_reference=None))
        self._scope=(id(args),id(design),id(protocol),id(inv),args.pilot_part)
        self._sealed=True
    def assert_scope(self,args,design,protocol,pilot_inventory):
        r.require(self._seal is _NATIVE_PREPARED_SEAL and self._pid==r.os.getpid() and design.get('injected') is True,
            'native prepared adapter cannot cross process or production boundary')
        r.require((id(args),id(design),id(protocol),id(pilot_inventory),args.pilot_part)==self._scope
            and self.inventory is self._inventory and self.entry_references is self._references,'native prepared graph/scope replaced')
    def final_publication_barrier(self,reconciliation,receipt):
        self.assert_scope(self.args,self.design,self.protocol,self.pilot)
        began=time.perf_counter();self._cheap_identity();r._check_file_witness(self.witness)
        verify_scenario(self.root,load_model=False);reconciliation.check_deadline();self._cheap_identity()
        if receipt:
            elapsed=time.perf_counter()-began;receipt['proof_validation_seconds']+=elapsed
            receipt['prepared_target_transport']['final_barrier_seconds']=elapsed


def receive_native_prepared_target(root,design,protocol,inv,*,part,selected_path=None,selected=None):
    """Materialize deterministic fixture DATA and receive it before model entry."""
    root=Path(root);r.require(design.get('injected') is True,'native receiver is injected-only')
    verify_scenario(root,load_model=False)
    target_path=root/'pilot-target-inventory'/part;preparation_path=root/'pilot-target-preparation'/part
    if not preparation_path.exists():
        target=r.workload.build_inventory(design,protocol,stage='fit-select' if part=='prefit' else 'remaining',selected=selected)
        r.workload._validate_inventory(target)
        if target_path.exists():
            r.require(r.read_object(target_path)==target,'native pre-existing target conflict')
            reference=r.object_reference(target_path)
        else:reference=r._publish_prepared_target_object(target_path,target)['reference']
        verify_scenario(root,load_model=False)
        r.publish_object(preparation_path,dict(kind='a3_injected_native_prepared_data_v1',injected=True,execution_authorized=False,
            target_reference=reference,pilot_inventory_sha256=inv['inventory_sha256'],part=part,source=source_identity()))
    descriptor=r.read_object(preparation_path)
    r.require(descriptor.get('kind')=='a3_injected_native_prepared_data_v1' and descriptor['part']==part
        and descriptor['pilot_inventory_sha256']==inv['inventory_sha256'] and descriptor['source']==source_identity(),
        'native prepared source/part differs')
    policy=dict(work_dir=str(root),target_root=str(target_path),preparation_root=str(preparation_path),allowed_aliases=(),
        expected_resolved=dict(work_dir=str(root.resolve()),target_root=str(target_path.resolve()),preparation_root=str(preparation_path.resolve())))
    result=r._read_prepared_target_object(descriptor['target_reference'],r.object_reference(preparation_path),policy)
    verify_scenario(root,load_model=False)
    args=SimpleNamespace(pilot_part=part,selected=selected_path)
    return _InjectedPreparedPilotTarget(args,design,protocol,inv,result,policy,root)


def run_phase(root,phase,*,start=0,count=32,resume=False):
    root=Path(root);began=time.perf_counter()
    if phase=='init':scenario_init(root);return dict(phase=phase,injected=True,scientific_execution=False)
    prepared_target=None;prepared_inv=None
    if phase in ('prefit-aggregate','selected-pilot-aggregate'):
        design,protocol,_,_=verify_scenario(root,load_model=False)
        part='prefit' if phase.startswith('prefit') else 'selected'
        selected_path=None if part=='prefit' else root/'selected'
        selected=None if selected_path is None else r.read_bundle(selected_path)[0]
        prepared_inv=inventory(root,design,protocol,'prefit' if part=='prefit' else 'selected-pilot',selected=selected)
        prepared_target=receive_native_prepared_target(root,design,protocol,prepared_inv,part=part,selected_path=selected_path,selected=selected)
        loaded_design,loaded_protocol,model,plain=verify_scenario(root)
        r.require(loaded_design==design and loaded_protocol==protocol,'native inputs changed during model entry')
    else:design,protocol,model,plain=verify_scenario(root)
    model_load_seconds=time.perf_counter()-began
    from component_analysis import hooks
    original=hooks.capture_forward;forwards=[0]
    def observed(*a,**kw):forwards[0]+=1;return original(*a,**kw)
    hooks.capture_forward=observed
    result={};target_ids=[]
    try:
        if phase in ('prefit','prefit-aggregate','selected-pilot','selected-pilot-aggregate'):
            part='prefit' if phase.startswith('prefit') else 'selected'
            selected_path=None if part=='prefit' else root/'selected'
            selected=None if selected_path is None else r.read_bundle(selected_path)[0]
            inv=prepared_inv if prepared_inv is not None else inventory(root,design,protocol,'prefit' if part=='prefit' else 'selected-pilot',selected=selected)
            invocations=_case_invocations(design,inv,part)
            if part=='selected':r.require(len(invocations)==63,'exact selected pilot cases required')
            binding=r.read_object(root/'scenario')
            if phase.endswith('-aggregate'):
                aggregate_pilot_cases(model,design,protocol,inv,root=root,part=part,binding=binding,selected_path=selected_path,startup_seconds=model_load_seconds,prepared_target=prepared_target)
                result['original_case_forward_calls_replayed']=r.read_object(root/'pilot-verification-aggregate'/part)['original_case_forward_calls']
                result['completed_pilot_cases']=len(invocations)
            else:
                r.require(start>=0 and count>0,'positive bounded pilot case range required')
                case_ids=[x['invocation_id'] for x in invocations[start:start+count]]
                result['case_references']=pilot_cases(model,design,protocol,inv,root=root,part=part,case_ids=case_ids,
                    binding=binding,selected_path=selected_path,resume=resume)
                result['completed_cases_in_process']=len(case_ids)
        elif phase=='fit':
            inv=inventory(root,design,protocol,'fit-select');r.require(start>=0 and count>0,'positive bounded capture range required')
            targets=inv['capture_shards'][start:start+count];r.require(targets,'empty verification capture chunk')
            for shard in targets:r.run_fit_capture(model,design,protocol,inv,root=root,guard=lambda:None,shard_id=shard['shard_id'],resume=resume)
            target_ids=[x['shard_id'] for x in targets]
            result['stage_complete']=(root/'cache'/'fit-completion'/'COMPLETE.json').is_file()
            if result['stage_complete']:
                fits=r.pipeline.fit_from_cache(design,root/'cache'/'fit-selection',protocol=protocol,output=root/'fits')
                r.require(not fits['blocked_task_seeds'],'full tiny fit unexpectedly blocked')
        elif phase=='validation':
            fits,_=r.read_bundle(root/'fits');inv=r.workload.build_inventory(design,protocol,stage='fit-select',fits=fits)
            r.publish_object(root/'validation-inventory',inv) if not (root/'validation-inventory').exists() else r.require(r.read_object(root/'validation-inventory')==json.loads(json.dumps(inv)),'validation inventory changed')
            if not (root/'test-admission').exists():r.publish_object(root/'test-admission',{'pilot_receipt_paths':[str(root/'pilot'/'prefit')]})
            if not (root/'test-reservation').exists():r.publish_object(root/'test-reservation',{'admission_path':str(root/'test-admission')})
            args=SimpleNamespace(stage='select',panel=None,selected=None,fits=str(root/'fits'),reservation=str(root/'test-reservation'),shard_id=None,resume=resume)
            r.require(start>=0 and count>0,'positive bounded validation range required')
            target_ids=[x['shard_id'] for x in inv['shards'][start:start+count]];r.require(target_ids,'empty verification validation chunk')
            r.run_scoring(model,design,protocol,inv,root=root,args=args,guard=lambda:None,fits=fits,shard_ids=target_ids)
        elif phase=='select':
            selected=r.pipeline.freeze_selection(design,root/'fits',root/'validation',protocol=protocol,output=root/'selected',protocol_path=root/'direction_protocol.json')
            r.require(not selected['blocked_task_seeds'] and len(selected['selected_records'])==9,'full selected source coverage')
            inventory(root,design,protocol,'selected-pilot',selected=selected);inventory(root,design,protocol,'remaining',selected=selected)
        elif phase in ('calibration','assessment'):
            selected,_=r.read_bundle(root/'selected');inv=inventory(root,design,protocol,'remaining',selected=selected)
            if phase=='assessment':r.require((root/'calibration-summary'/'COMPLETE.json').is_file(),'calibration/power must precede assessment')
            shard_list=[s for s in inv['shards'] if s['panel']==phase]
            r.require(len(shard_list)==(630 if phase=='calibration' else 3978),'original complete verification shard counts changed')
            r.require(start>=0 and count>0,'positive bounded scoring range required')
            target_ids=[s['shard_id'] for s in shard_list[start:start+count]];r.require(target_ids,'empty verification chunk')
            if not (root/'test-admission-remaining').exists():r.publish_object(root/'test-admission-remaining',{'pilot_receipt_paths':[str(root/'pilot'/'selected')]})
            if not (root/'test-reservation-remaining').exists():r.publish_object(root/'test-reservation-remaining',{'admission_path':str(root/'test-admission-remaining')})
            args=SimpleNamespace(stage='assess',panel=phase,selected=str(root/'selected'),fits=None,reservation=str(root/'test-reservation-remaining'),shard_id=None,resume=resume)
            r.run_scoring(model,design,protocol,inv,root=root,args=args,guard=lambda:None,selected=selected,shard_ids=target_ids)
            r.require(set(target_ids)<=set(complete_ids(root,phase)),'verification chunk missing completed shard')
        elif phase in ('calibration-summary','summary'):
            selected,_=r.read_bundle(root/'selected');inv=inventory(root,design,protocol,'remaining',selected=selected)
            calibration,crefs=r.read_runtime_rows(design,protocol,inv,root/'runtime-shards',panel='calibration')
            if phase=='calibration-summary':r.summarize_calibration(design,protocol,selected,calibration,crefs,root=root,inventory=inv,guard=lambda:None)
            else:
                rows,refs=r.read_runtime_rows(design,protocol,inv,root/'runtime-shards',panel='assessment')
                summary=r.summarize_runtime(design,protocol,selected,rows,calibration,refs,crefs,root=root,inventory=inv,final=False,guard=lambda:None)
                r.require(summary['diagnostic_readiness'] and not summary['finalized'],'complete diagnostic readiness required')
                r.require(len(rows)+len(calibration)==len(inv['expected_keys'])==165834,'full raw-row coverage changed')
                result.update(assessment_rows=len(rows),calibration_rows=len(calibration),raw_rows=len(rows)+len(calibration),baseline_margin=rows[0]['intact_margin'],empty_replay_error=rows[0]['replay_errors']['empty'])
                try:r.summarize_runtime(design,protocol,selected,rows,calibration,refs,crefs,root=root,inventory=inv,final=True,guard=lambda:None)
                except ValueError:result['injected_finality_rejected']=True
                else:raise AssertionError('injected finalization unexpectedly accepted')
        else:raise ValueError('unknown verification phase')
    finally:hooks.capture_forward=original
    r.require(model_identity(plain)==r.read_object(root/'scenario')['model_identity'],'tiny model mutated during phase')
    verify_scenario(root,load_model=False)
    result.update(phase=phase,start=start,count=count,shard_ids=target_ids,native_forward_calls=forwards[0],wall_seconds=time.perf_counter()-began,
        peak_host_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,model_load_seconds=model_load_seconds,
        injected=True,scientific_execution=False,execution_authorized=False,complete=True)
    name=phase+'-'+str(start)+'-'+str(count)+('-resume' if resume else '')+'-'+str(r.os.getpid())
    r.publish_object(root/'process-evidence'/name,result)
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--phase',required=True)
    parser.add_argument('--start',type=int,default=0);parser.add_argument('--count',type=int,default=32);parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();print(json.dumps(run_phase(args.root,args.phase,start=args.start,count=args.count,resume=args.resume)),flush=True)


if __name__=='__main__':main()
