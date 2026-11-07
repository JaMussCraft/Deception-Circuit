def live_guard(design, protocol, args, inventory=None):
    evidence=artifacts.validate_live(design,protocol,registry_paths=args.registry)
    if not design['injected']:_model_metadata_preflight(design,protocol)
    if inventory is not None:
        require(args.ledger_snapshot and args.reservation,'model execution requires fresh root ledger mapping and reservation')
        scope=('directions',args.stage,args.action,args.panel,args.pilot_part)
        context=getattr(args,'_authority_context',None)
        if context is None:
            ledger=normalize_ledger(args.ledger_snapshot,identity=inventory['identity'],injected=design['injected'],include_envelope=False)
            if not args.dry_run:
                context=make_authority_context(args.reservation,ledger=ledger,inventory=inventory,work_dir=args.work_dir,
                    injected=design['injected'],requested_scope=scope,inventory_path=args.inventory)
                args._authority_context=context;args._authority_ledger_reference=ledger
        else:ledger=args._authority_ledger_reference
        evidence['reservation']=validate_reservation(args.reservation,ledger=ledger,inventory=inventory,work_dir=args.work_dir,injected=design['injected'],
            require_allocation=not args.dry_run,authority_context=context,requested_scope=scope)
        if args.admission:
            require(read_object(args.reservation)['admission_path']==str(Path(args.admission).resolve()),'CLI root admission differs from reservation')
    return evidence
