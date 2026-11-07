def run_phase(root,phase,*,start=0,count=32,resume=False):
    root=Path(root);began=time.perf_counter()
    if phase=='init':scenario_init(root);return dict(phase=phase,injected=True,scientific_execution=False)
    design,protocol,model,plain=verify_scenario(root);model_load_seconds=time.perf_counter()-began
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
            inv=inventory(root,design,protocol,'prefit' if part=='prefit' else 'selected-pilot',selected=selected)
            invocations=_case_invocations(design,inv,part)
            if part=='selected':r.require(len(invocations)==63,'exact selected pilot cases required')
            binding=r.read_object(root/'scenario')
            if phase.endswith('-aggregate'):
                aggregate_pilot_cases(model,design,protocol,inv,root=root,part=part,binding=binding,selected_path=selected_path,startup_seconds=model_load_seconds)
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
