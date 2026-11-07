def _admitted_candidate_index(args,design,protocol):
    if not getattr(args,'reservation',None):return _PackingCandidateIndex([])
    reservation=read_object(args.reservation);admission=read_object(reservation['admission_path'])
    paths=admission.get('pilot_receipt_paths',[]);require(paths,'completed admitted pilot sources required')
    target=read_object(reservation['upper_inventory_path']) if reservation.get('upper_inventory_path') else read_object(Path(paths[0]).parents[1]/'pilot-target-inventory'/read_object(paths[0])['part'])
    capacity=reservation.get('allocation_contract',{}).get('memory_bytes')
    index,_,_=_completed_pilot_index(design,protocol,target,paths,ledger_path=getattr(args,'ledger_snapshot',None),host_capacity_bytes=capacity,
        output_root=Path(getattr(args,'work_dir',None) or Path(paths[0]).parents[1]))
    forecast=admission.get('completed_host_startup_cost')
    comparison=dict(actual_seconds=index.startup_seconds,forecast_seconds=None,forecast_conditional=True,
        forecast_status='absent; host portability remains conditional',retroactive_authorization=False)
    if forecast is not None:
        require(forecast.get('kind')=='a3_completed_host_startup_cost_v1' and forecast.get('target_inventory_sha256')==target['inventory_sha256']
            and type(forecast.get('seconds')) in (int,float) and math.isfinite(forecast['seconds']) and forecast['seconds']>=0,'startup forecast source/target/time differs')
        comparison.update(forecast_seconds=forecast['seconds'],observed_exceeds_forecast=index.startup_seconds>forecast['seconds'],
            host_profile_equal=forecast.get('host_profile')==index.startup_evidence['host_profile'],forecast_status='recorded; portability not granted by this comparison')
    object.__setattr__(index,'startup_reconciliation',_freeze_json(comparison))
    return index
