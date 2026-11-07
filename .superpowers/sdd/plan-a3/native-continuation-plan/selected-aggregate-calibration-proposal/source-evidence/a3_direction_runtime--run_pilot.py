def run_pilot(model,design,protocol,inventory,*,root,args,guard,startup_seconds,selected=None):
    """Measure every target requirement from the frozen validation scope only."""
    root=Path(root);part=args.pilot_part
    target=workload.build_inventory(design,protocol,stage='fit-select' if part=='prefit' else 'remaining',selected=selected)
    selected_reference=None;selected_witness=None
    if part=='prefit':axes=None
    else:
        selected_reference=pipeline._bundle_byte_reference(args.selected)
        axes=load_selected_axes(args.selected,selected);selected_witness=_make_file_witness([args.selected])
        require(pipeline._bundle_byte_reference(args.selected)==selected_reference,'selected numeric backing changed during pilot load')
    invocations=inventory['packing_invocations'] or _serial_invocations(inventory)
    measured=[];packing={};packing_refs={};serial_refs={};serial_witnesses=[];invocation_results=[];seen_measurements=set();proof_validation_seconds=0;proof_retained_bytes=0;packing_overheads=[]
    for invocation in invocations:
        if selected_witness is not None:_check_file_witness(selected_witness)
        guard();result=_pilot_invocation(model,design,protocol,invocation,axes=axes,root=root,guard=guard)
        if selected_witness is not None:_check_file_witness(selected_witness)
        guard();result['invocation']=invocation;result['packing_id']=None
        if result.get('packing_overhead') is not None:
            packing_overheads.append(result['packing_overhead']);proof_validation_seconds+=result['packing_overhead']['setup_seconds']
        if result['evidence'] is not None:
            general=dict(profile=invocation['profile'],timing_inputs=_timing_inputs_from_batches(result['batches'],invocation['profile']),
                axis_scope=[{k:v for k,v in s.items() if k!='donors'} for specs in result['evidence']['runner_receipt']['scope']['batches'].values() for s in specs])
            path=root/'pilot-evidence'/part/invocation['invocation_id']
            payload=dict(evidence=result['evidence'],measurement=general,not_target_observations=True,
                source_commit=protocol['commit'],timing_only=part=='prefit',injected=design['injected'],runtime_profile=runtime_kernel_identity(model),
                positive_controls=result['positive_controls'],numeric_backing_references={} if part=='prefit' else
                    {str(Path(args.selected).absolute()):selected_reference})
            if path.exists():require(read_object(path)==payload,'pilot evidence output conflict')
            else:publish_object(path,payload)
            proof=_completed_packing_proof(path)
            packing_refs[str(path.resolve())]=proof.reference
            result['packing_id']=invocation['invocation_id']
            packing[result['packing_id']]=dict(kind='a3_packing_proof_reference_v1',evidence_sha256=proof.proof.source_digest,
                measured_path=str(path.resolve()),measured_reference=proof.reference)
            proof_validation_seconds+=proof.validation_seconds;proof_retained_bytes+=proof.retained_bytes
            compact=dict(invocation=invocation,packing_id=result['packing_id'],proof=proof,batches=result['batches'],
                samples=_compact_operation_samples(result['samples']),axis_count=proof.proof.distinct_axes,lookup_scope_seconds=result['lookup_scope_seconds'])
            result=compact
        else:
            path=root/'serial-pilot-evidence'/part/invocation['invocation_id']
            serial_payload=dict(kind='a3_serial_numeric_invocation_v1',injected=design['injected'],actual_execution=True,
                timing_only=part=='prefit',
                source_commit=protocol['commit'],runtime_profile=runtime_kernel_identity(model),receipt=result['receipt'],
                positive_controls=result['positive_controls'],numeric_backing_references={} if part=='prefit' else {str(Path(args.selected).absolute()):selected_reference})
            start=time.perf_counter();publish_object(path,serial_payload)
            serial=_SerialNumericProof(path);proof_validation_seconds+=time.perf_counter()-start
            serial_refs[invocation['invocation_id']]=dict(path=str(path.resolve()),reference=object_reference(path),source_digest=serial.source_digest)
            serial_witnesses.append(serial.witness)
        invocation_results.append(result)
    lookup_index=_PackingCandidateIndex([r['proof'] for r in invocation_results if r.get('proof') is not None])
    proof_validation_seconds+=lookup_index.index_seconds;proof_retained_bytes+=lookup_index.retained_bytes
    serialization_bytes=0
    scenario_reference=object_reference(root/'scenario') if design['injected'] and (root/'scenario').exists() else None
    scenario_witnesses=() if scenario_reference is None else (_make_file_witness([root/'scenario']),)
    reconciliation=_PilotReconciliationPass([r['proof'] for r in invocation_results if r.get('proof') is not None],target,guard=guard,
        injected=design['injected'],extra_witnesses=tuple(serial_witnesses)+scenario_witnesses+(() if selected_witness is None else (selected_witness,)))
    with reconciliation:
        target=reconciliation.inventory
        for req in target['requirements']:
            signature=workload.digest({k:req[k] for k in ('operation','profile','timing_keys','axis_ids','axis_scope','timing_inputs','donor_convention')})
            if signature in seen_measurements:continue
            seen_measurements.add(signature)
            reconciliation.check_deadline();op=req['operation'];profile=req['profile'];resources=_measurement_resources(model,root)
            measurement=dict(profile=copy.deepcopy(profile),operation=op,expected_keys=req['timing_keys'],observed_keys=[],
                axis_ids=req['axis_ids'],axis_scope=copy.deepcopy(req['axis_scope']),source_split='validation',synchronized=True,
                timing_inputs=req['timing_inputs'],donor_convention=req['donor_convention'],axis_class=req['axis_class'],
                nonzero_axis_count=0,cache_fit=True,cache_bytes=0,**{k:v for k,v in resources.items() if k!='host_peak_bytes'})
            if op=='guard_refresh':
                samples=[]
                for _ in range(3):
                    start=time.perf_counter();reconciliation.model_guard();samples.append(time.perf_counter()-start)
                measurement['batch_seconds']=samples
            elif op=='packing_lookup':
                start=time.perf_counter();candidates=lookup_index.candidates(profile,req['axis_scope'],axis_class=part=='prefit',runtime_profile=runtime_kernel_identity(model))
                elapsed=time.perf_counter()-start;require(candidates,'measured target lookup scope missing')
                scope_cost=max(r['lookup_scope_seconds'] for r in invocation_results if r.get('proof') in candidates)
                measurement['batch_seconds']=[elapsed+scope_cost]
                measurement['packing_id']=Path(candidates[0].path).name
                measurement['nonzero_axis_count']=candidates[0].proof.distinct_axes
                measurement['observed_keys']=candidates[0].proof.observed_requirement(req)
            elif op=='serialization':
                samples,shape_ids,nbytes=_time_serialization(profile['serialization_shapes'],design,protocol,root,reconciliation.model_guard)
                measurement.update(batch_seconds=samples,serialization_shape_ids=shape_ids);serialization_bytes+=nbytes
            elif op=='warmup':
                reconciliation.model_guard()
                example=next(x for x in target['requirements'] if x['timing_inputs'])
                warm_profile=dict(profile)
                inputs=example['timing_inputs'][:warm_profile['physical_batch_size']]
                b=_batch_for_timing(design,warm_profile,inputs);start=time.perf_counter()
                for _ in range(req['batches']):runner._capture_readouts(model,[b],sites=profile['sites'],sink=lambda _:None,
                    identity=dict(injected=True,numeric_profile=warm_profile),measuring=True)
                if runner.hooks.device_and_dtype(model)[0].type=='cuda':torch.cuda.synchronize()
                measurement['batch_seconds']=[time.perf_counter()-start]
            else:
                candidates=_pilot_candidates(invocation_results,req) if req['timing_inputs'] else []
                if op.startswith('capture_'):
                    reconciliation.model_guard()
                    b=_batch_for_timing(design,profile,req['timing_inputs']);chunks=[]
                    capture_run,samples=measure_runner_operations(model,lambda:runner._capture_readouts(model,[b],sites=profile['sites'],sink=chunks.append,
                        identity=dict(injected=True,numeric_profile=profile),measuring=True))
                    observed=[r for c in chunks for r in c['rows'] if not r['instance_id'].startswith('a3-dummy:')]
                    measurement['observed_keys']=[[r['task'],'validation',r['condition'],r['stream'],r['instance_id']] for r in observed]
                    require(Counter(map(workload._freeze,measurement['observed_keys']))==Counter(map(workload._freeze,req['timing_keys'])),'capture timing source coverage mismatch')
                    measurement['batch_seconds']=[s['seconds'] for s in samples]
                    if profile['axis_tile_size']>1:
                        measurement['capture_lane_equivalence']=capture_lane_evidence(capture_run,chunks,[b],req['timing_inputs'])
                        workload._capture_lane_evidence(measurement['capture_lane_equivalence'],measurement)
                    measurement['cache_bytes']=sum(h['value'].numel()*h['value'].element_size() for c in chunks for r in c['rows'] for h in r['heads'])
                elif op=='positive_control':
                    reconciliation.model_guard()
                    b=_batch_for_timing(design,profile,req['timing_inputs']);pid=runner.profile_identity({'numeric_profile':profile})
                    if b.task=='mmlu':ds,ms=_mmlu_positive(design,'validation',b,profile,{})
                    else:
                        donor=source_batches(design,b.task,'validation',b.ids,b.condition,'corrupt' if b.stream=='clean' else 'clean',profile)[0]
                        ds=[donor];ms=_maps(b,donor,pid)
                    controls,positive_times=measure_positive_operations(model,lambda:runner.run_positive_controls(model,[b],donor_batches=ds,donor_maps=ms,identity=dict(injected=True,numeric_profile=profile)))
                    measurement['batch_seconds']=positive_times
                    measurement['observed_keys']=[[r['task'],'validation',r['condition'],r['stream'],r['instance_id']] for r in controls['rows']]
                else:
                    require(candidates,'missing actual pilot operation profile')
                    result=next((x for x in candidates if _pilot_axes_covered(x,req['axis_scope'])),None)
                    # Prefit target scope freezes named attainable classes, without
                    # numeric axes; serial-only records carry the same named cells.
                    if result is None and part=='prefit':result=candidates[0]
                    require(result is not None,'actual selected timing axes/operations not covered')
                    measurement['observed_keys']=result['proof'].proof.observed_requirement(req) if result.get('proof') is not None else _observed_requirement(result['receipt'],req)
                    actual=[s['seconds'] for s in result['samples'] if s['profile']==profile and s['operation']==op and not s['dummy']]
                    require(actual,'actual synchronized operation timing missing')
                    measurement['batch_seconds']=[max(actual)];measurement['nonzero_axis_count']=result.get('axis_count',len(result.get('local_axes',{})))
                if profile['axis_tile_size']>1 and not op.startswith('capture_'):
                    coverage=next((x for x in candidates if x.get('packing_id') is not None and _pilot_axes_covered(x,req['axis_scope'])),None)
                    require(coverage is not None,'packed capture/operation lacks actual measured equivalence')
                    measurement['packing_id']=coverage['packing_id']
                    reconciliation.check(coverage['proof'],req,measurement)
            measured.append(measurement)
    final_authority=guard();resources=_measurement_resources(model,root)
    target_path=root/'pilot-target-inventory'/part
    if not target_path.exists():publish_object(target_path,target)
    require(workload.digest(read_object(target_path))==workload.digest(target),'pilot target output conflict')
    origin=_pilot_origin(args,root,inventory,target_path,final_authority,injected=design['injected'])
    receipt=dict(kind='a3_direction_timing_v1',status='completed',exit_code=0,complete=True,injected=design['injected'],
        identity=target['identity'],hardware=target['hardware'],inventory_sha256=target['inventory_sha256'],pilot_inventory_sha256=inventory['inventory_sha256'],
        startup_seconds=startup_seconds,proof_validation_seconds=proof_validation_seconds,proof_retained_bytes=proof_retained_bytes,host_peak_bytes=resources['host_peak_bytes'],measurements=measured,packing_evidence=packing,
        packing_references=packing_refs,serial_numeric_references=serial_refs,packing_overhead_measurements=packing_overheads,
        serialization_bytes=serialization_bytes,part=part,runtime=runtime_environment(model),
        job_id=os.environ.get('SLURM_JOB_ID','injected-cpu'),source_split='validation',actual_execution=True,
        origin=origin,runtime_profile=runtime_kernel_identity(model))
    if scenario_reference is not None:receipt['verification_scenario_reference']=scenario_reference
    receipt.update(proof_verified_bytes=reconciliation.verified_bytes,proof_verification_seconds=reconciliation.verification_seconds)
    _measure_complete_guard_union(receipt,reconciliation,root,guard)
    reconciliation.before_publication()
    receipt.update(proof_verified_bytes=reconciliation.verified_bytes,proof_verification_seconds=reconciliation.verification_seconds)
    _publish_measured_pilot_receipt(root/'pilot'/part,receipt)
    target_path=root/'pilot-target-inventory'/part
    if not target_path.exists():publish_object(target_path,target)
    return receipt
