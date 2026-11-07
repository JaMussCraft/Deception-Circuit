def dispatch(args, *, tokenizer=None, model_loader=None):
    from component_analysis import a3_pipeline
    root=Path(args.work_dir);design_path=Path(args.design)
    require(design_path.resolve()==(root/'design.json').resolve(),'canonical design must be WORK_DIR/design.json')
    if args.stage=='prepare' and args.action=='freeze':
        for key in ('a1_design','a1_selected','matched_root','historical_csv','root_ruling','execution_settings'):
            require(getattr(args,key),'prepare freeze requires '+key)
        # Canonical prepare independently loads the frozen standard tokenizer;
        # explicit adapters remain available only to injected parent fixtures.
        ruling=artifacts._strict_json(args.root_ruling);settings=artifacts._strict_json(args.execution_settings)
        design=a3_pipeline.prepare(a1_design=args.a1_design,a1_selected=args.a1_selected,matched_root=args.matched_root,
            historical_csv=args.historical_csv,root_ruling=ruling,tokenizer=tokenizer,registry_paths=args.registry,
            output=None if args.dry_run else design_path,commit=args.commit,execution_settings=settings)
        if args.dry_run: return _print_dry(args,design,design['direction_protocol'])
        return 0
    design=ladder.read_artifact(design_path);protocol=design['direction_protocol']
    require(protocol['commit']==args.commit and design['direction_protocol_sha256']==ladder.design._hash(protocol),'CLI execution source differs from frozen protocol')
    require(model_loader is None or design['injected'] is True,'injected loader cannot execute a production lineage')
    require(not args.final or design['injected'] is False,'injected lineage cannot finalize')
    guard=lambda:live_guard(design,protocol,args)
    guard()
    if args.stage=='fit' and args.action=='solve':
        cache=args.fit_cache or root/'cache'/'fit-selection'
        expected,_=pipeline._fit_contract(design,protocol);artifacts.read_bundle(cache,expected=expected)
        if args.dry_run:return _print_dry(args,design,protocol)
        if not design['injected']: require(read_object(root/'cache'/'fit-completion')['cache_reference']==object_reference(cache),'complete capture execution receipt required')
        pipeline.fit_from_cache(design,cache,protocol=protocol,output=root/'fits');return 0
    fits=None;selected=None
    if args.fits: fits,_=read_bundle(args.fits)
    if args.selected: selected,_=read_bundle(args.selected)
    if args.stage=='select' and args.action=='score' and fits is not None:
        require(not fits.get('blocked_task_seeds'),'no valid DOM fit for an original task/seed; validation model access blocked')
    if args.stage=='prepare' and args.action=='inventory':
        inv=workload.build_inventory(design,protocol,stage=args.inventory_stage,fits=fits,selected=selected)
        if args.dry_run:return _print_dry(args,design,protocol,inventory=inv)
        publish_object(args.inventory or root/'inventory'/args.inventory_stage,inv);return 0
    if args.stage=='select' and args.action=='freeze':
        fits_path=args.fits or root/'fits';validation=args.validation_root or root/'validation'
        fits,_=read_bundle(fits_path)
        # All expected validation shard bytes must exist before CPU selection.
        pipeline._read_selection_validation(design,protocol,fits,read_bundle(fits_path)[1],validation,pipeline._bundle_byte_reference(fits_path))
        if args.dry_run:return _print_dry(args,design,protocol)
        pipeline.freeze_selection(design,fits_path,validation,protocol=protocol,output=root/'selected',protocol_path=root/'direction_protocol.json');return 0
    inv=_read_stage_inventory(args,design,protocol,fits=fits,selected=selected)
    if args.finish_reserve_seconds is not None:
        require(args.finish_reserve_seconds==inv['finish_reserve_seconds'],'finish reserve differs from frozen workload')
    if args.stage=='prepare' and args.action=='admit':
        require(args.pilot_receipts and args.ledger_snapshot,'completed pilot receipts and fresh root mapping required')
        ledger=normalize_ledger(args.ledger_snapshot,identity=inv['identity'],injected=design['injected'])
        if args.dry_run:
            receipts,_=_authenticated_pilot_receipts(design,protocol,inv,args.pilot_receipts,ledger_path=args.ledger_snapshot)
            _validate_completed_pilot_footprints(design,receipts,args.pilot_receipts)
            workload.project_cost(receipts,inv,ledger,packing_proofs=_cost_packing_proofs(receipts))
            return _print_dry(args,design,protocol,inventory=inv,missing=['completed authentication/index startup measurement'])
        index,receipts,sources=_completed_pilot_index(design,protocol,inv,args.pilot_receipts,ledger_path=args.ledger_snapshot,
            host_capacity_bytes=ledger['storage_capacities']['host_ram']['available_bytes'],output_root=root)
        proposal=workload.project_cost(receipts,inv,ledger,packing_proofs=_cost_packing_proofs(receipts,candidate_index=index),runtime_cost=index.startup_evidence)
        proposal['completed_pilot_sources']=[dict(s.value) for s in sources]
        publish_object(root/'admission'/(inv['stage']+'.json'),proposal);return 0
    if args.stage=='summarize':
        require(inv['stage']=='remaining' and selected is not None,'summary requires full remaining inventory and selected axes')
        calibration,calibration_refs=read_runtime_rows(design,protocol,inv,root/'runtime-shards',panel='calibration',guard=guard)
        assessment_complete=all((root/'runtime-shards'/s['shard_id']/'COMPLETE.json').is_file() for s in inv['shards'] if s['panel']=='assessment')
        if not assessment_complete:
            require(not args.final,'incomplete original assessment inventory cannot finalize')
            if args.dry_run:return _print_dry(args,design,protocol,inventory=inv,missing=['complete assessment inventory for full summary'])
            summarize_calibration(design,protocol,selected,calibration,calibration_refs,root=root,inventory=inv,guard=guard)
            return 0
        rows,refs=read_runtime_rows(design,protocol,inv,root/'runtime-shards',panel='assessment',guard=guard)
        if args.dry_run:return _print_dry(args,design,protocol,inventory=inv)
        summarize_runtime(design,protocol,selected,rows,calibration,refs,calibration_refs,root=root,inventory=inv,final=args.final,guard=guard)
        return 0
    expected_stage=('prefit' if args.pilot_part=='prefit' else 'selected-pilot') if args.stage=='pilot' else ('fit-select' if args.stage in ('fit','select') else 'remaining')
    require(inv['stage']==expected_stage,'inventory stage incompatible with requested model stage')
    candidates=inv.get('capture_shards',[]) if args.stage=='fit' else inv['shards']
    require(args.shard_id is None or any(s['shard_id']==args.shard_id for s in candidates),'unknown frozen stage shard ID')
    if args.stage=='assess': require(any(s['panel']==args.panel for s in candidates),'inventory does not contain requested panel')
    if args.stage=='assess' and args.panel=='assessment' and not design['injected']:
        assessment_preflight(design,protocol,selected,inv,root=root,reservation_path=args.reservation)
    if not design['injected']:_model_metadata_preflight(design,protocol)
    if args.dry_run:
        missing=[k for k in ('ledger_snapshot','reservation') if not getattr(args,k)]
        if not missing: live_guard(design,protocol,args,inv)
        return _print_dry(args,design,protocol,inventory=inv,missing=missing)
    model_guard=lambda:live_guard(design,protocol,args,inv)
    model_guard()
    if args.stage in ('select','assess'):
        args._candidate_index=_admitted_candidate_index(args,design,protocol)
        model_guard=_DependencyGuard(model_guard,args._candidate_index)
        model_guard()
    if not design['injected']:
        require(os.environ.get('SLURM_JOB_ID') and torch.cuda.is_available(),'model execution requires actual Slurm CUDA allocation')
    load_args=copy.copy(args)
    for k in ('model','model_revision','tokenizer_revision'):setattr(load_args,k,design['a1_identity'][k])
    startup=time.perf_counter();model=(model_loader or ladder.load_model)(load_args)
    if torch.cuda.is_available():torch.cuda.synchronize()
    startup=max(time.perf_counter()-startup,time.time()-float(os.environ.get('A3_WRAPPER_START_SECONDS',_PROCESS_START_TIME)))
    from component_analysis import hooks
    geometry=hooks.geometry(model);cfg=protocol['workload']
    require(all(geometry[k]==cfg[k2] for k,k2 in (('head_dim','head_width'),('hidden_size','hidden_size'),('num_layers','num_layers'))),'actual loaded model geometry differs from frozen operational settings')
    model_guard()
    if args.stage=='pilot': run_pilot(model,design,protocol,inv,root=root,args=args,guard=model_guard,startup_seconds=startup,selected=selected)
    elif args.stage=='fit': run_fit_capture(model,design,protocol,inv,root=root,guard=model_guard,shard_id=args.shard_id,resume=args.resume)
    else:
        require(args.stage in ('select','assess'),'unsupported model stage')
        run_scoring(model,design,protocol,inv,root=root,args=args,guard=model_guard,fits=fits,selected=selected)
    return 0
