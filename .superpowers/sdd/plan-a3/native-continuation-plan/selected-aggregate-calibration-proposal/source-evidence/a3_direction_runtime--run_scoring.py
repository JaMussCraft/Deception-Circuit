def run_scoring(model,design,protocol,inventory,*,root,args,guard,fits=None,selected=None,shard_ids=None):
    requested=None
    if shard_ids is not None:
        require(design.get('injected') is True,'bounded shard_ids is injected verification only')
        require(getattr(args,'shard_id',None) is None,'mixed shard_id/shard_ids selectors')
        chosen=list(shard_ids);require(chosen and len(chosen)==len(set(chosen)),'unique nonempty verification shard IDs required')
        workload._validate_inventory(inventory)
        stage='validation' if args.stage=='select' else getattr(args,'panel',None)
        allowed={s['shard_id'] for s in inventory['shards'] if s['panel']==stage}
        require(set(chosen)<=allowed,'unknown or wrong-stage verification shard IDs');requested=frozenset(chosen)
    root=Path(root);axes={}
    candidate_index=getattr(args,'_candidate_index',None) or _admitted_candidate_index(args,design,protocol)
    paths=[p.path for p in candidate_index.proofs]
    if type(guard) is not _DependencyGuard:guard=_DependencyGuard(guard,candidate_index)
    if args.stage=='select':
        require(fits is not None and args.fits,'completed fits required for validation scoring')
        fitmeta,fitarrays,_,_=pipeline._read_selection_fits(design,protocol,args.fits)
        for record in fitmeta['fit_records']:
            if record['valid']:
                name=workload.digest([record['task'],record['site'],record['seed']])
                axes[name]=pipeline._loaded_fit_axis(fitmeta,fitarrays,record,'dom')
    else: axes=load_selected_axes(args.selected,selected)
    for original in inventory['shards']:
        if requested is not None and original['shard_id'] not in requested:continue
        if args.stage=='assess' and original['panel']!=args.panel:continue
        if args.shard_id is not None and original['shard_id']!=args.shard_id:continue
        guard();shard=copy.deepcopy(original);target=root/'runtime-shards'/shard['shard_id']
        if target.exists():
            require(args.resume,'existing scientific shard requires resume')
            manifest=artifacts._strict_json(target/'run_manifest.json')
            identity=_runtime_shard_identity(design,protocol,shard,manifest['execution']['capture_reference']['path'])
            artifacts.read_completed_shards(dict(shards=[shard]),root/'runtime-shards',identity=identity);continue
        if args.stage=='select':
            for cell in shard['cells']:cell['axis']=workload.digest([shard['expected_keys'][0][1],cell['site'],cell['seed']])
        rows,execution,identity=score_runtime_shard(model,design,protocol,shard,axes=axes,
            output=root/'runtime-execution'/shard['shard_id'],guard=guard,measured_paths=paths,
            axis_class=args.stage=='select',shared_root=root,measured_index=candidate_index)
        if args.stage=='select':execution['fit_reference']=pipeline._bundle_byte_reference(args.fits)
        guard();artifacts.publish_shard(target,identity=identity,expected_keys=shard['expected_keys'],rows=rows,execution=execution)
    if args.stage=='select' and all((root/'runtime-shards'/s['shard_id']/'COMPLETE.json').is_file() for s in inventory['shards']):
        assemble_selection_cache(design,protocol,fits,inventory,root=root,fits_path=args.fits,guard=guard)
