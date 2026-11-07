def _completed_pilot_index(design,protocol,target,paths,*,ledger_path,host_capacity_bytes=None,output_root=None):
    """Same fresh process-local construction for completed intake and scoring."""
    import resource
    start=time.perf_counter();packed={};serials={};numeric={}
    require(host_capacity_bytes is not None or design.get('injected') is True,'frozen admitted host capacity required')
    require(host_capacity_bytes is None or type(host_capacity_bytes) is int and host_capacity_bytes>0,'positive frozen admitted host capacity required')
    require(paths and len(paths)==len({str(Path(p).resolve()) for p in paths}),'unique complete pilot source paths required')
    def packed_reader(path,*,expected_reference=None):
        key=str(Path(path).absolute())
        if key not in packed:packed[key]=_CompletedPackingProof(path,numeric_cache=numeric)
        proof=packed[key];proof.refresh()
        require(expected_reference is None or proof.reference==expected_reference,'completed packed source reference changed');return proof
    def serial_reader(path):
        key=str(Path(path).absolute())
        if key not in serials:serials[key]=_SerialNumericProof(path,numeric_cache=numeric)
        return serials[key]
    receipts,sources=_authenticated_pilot_receipts(design,protocol,target,paths,ledger_path=ledger_path,
        proof_reader=packed_reader,serial_reader=serial_reader)
    witnesses=[_make_file_witness([path]) for path in paths]+[s.witness for s in serials.values()]
    index=_PackingCandidateIndex(list(packed.values()),extra_witnesses=witnesses)
    samples=[];volume=None
    for _ in range(3):
        began=time.perf_counter();volume=index.refresh_dependencies();samples.append(time.perf_counter()-began)
    _validate_completed_pilot_footprints(design,receipts,paths,packed_reader=packed_reader,serial_reader=serial_reader)
    scenarios=[r['verification_scenario_reference'] for r in receipts if r.get('verification_scenario_reference') is not None]
    output_root=Path(output_root) if output_root is not None else Path(paths[0]).parents[1]
    profile=_host_startup_profile([*index.forest.paths,output_root]);index.refresh_dependencies()
    retained=index.retained_bytes
    temporary=_retained_json_bytes([receipts,[s.__dict__ for s in serials.values()],numeric,[s.value for s in sources],profile])[0]
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    require(host_capacity_bytes is None or max(retained+temporary,peak)<=host_capacity_bytes,'completed source/index exceeds frozen admitted host RAM')
    evidence=dict(kind='a3_completed_host_startup_cost_v1',target_inventory_sha256=target['inventory_sha256'],
        pilot_references=[object_reference(p) for p in paths],host_profile=profile,
        process_local_cold=True,os_cache_cold_claimed=False,conditional=True,execution_authorized=False,
        portability='unestablished across host/CPU/thread/filesystem conditions; allocated-host bound required',
        guard_seconds=samples,dependency_roots=volume['roots'],dependency_bytes_per_refresh=volume['verified_bytes'],construction_dependency_refreshes=index.forest.refreshes,
        retained_bytes=retained,construction_working_bytes=retained+temporary,peak_host_bytes=peak,frozen_host_capacity_bytes=host_capacity_bytes)
    evidence['seconds']=time.perf_counter()-start
    record=dict(kind='a3_completed_host_startup_record_v1',execution_authorized=False,injected=design['injected'],source_identity=target['identity'],
        target_inventory_sha256=target['inventory_sha256'],design_sha256=workload.digest(design),protocol_sha256=workload.digest(protocol),
        process=dict(pid=os.getpid(),job_id=os.environ.get('SLURM_JOB_ID','injected-cpu' if design['injected'] else 'host-cpu'),scenario_references=scenarios),construction=evidence)
    require(_object_payload_size(record)<=_STARTUP_RECORD_PAYLOAD_BYTES,'startup record exceeds priced file bound')
    destination=output_root/'runtime-startup'/(str(os.getpid())+'-'+str(time.time_ns()))
    bounds={name:min(r['guard_dependency_measurement']['startup_record_file_upper_bytes'][name] for r in receipts)
        for name in ('payload.json','COMPLETE.json')}
    before=time.perf_counter();_publish_bounded_object(destination,record,bounds);reference=object_reference(destination);publication=time.perf_counter()-before
    witnesses=[_make_file_witness([p]) for p in index.forest.paths]+[_make_file_witness([destination])]+[_make_file_witness([r['path']]) for r in scenarios]
    forest=_DependencyForest(witnesses);previous=index.forest.refreshes;object.__setattr__(index,'forest',forest)
    samples=[]
    for _ in range(3):
        began=time.perf_counter();volume=index.refresh_dependencies();samples.append(time.perf_counter()-began)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    require(host_capacity_bytes is None or peak<=host_capacity_bytes,'startup publication exceeds frozen admitted host RAM')
    evidence.update(seconds=time.perf_counter()-start,publication_seconds=publication,startup_record_reference=reference,
        guard_seconds=samples,dependency_roots=volume['roots'],dependency_bytes_per_refresh=volume['verified_bytes'],
        construction_dependency_refreshes=previous+forest.refreshes,peak_host_bytes=peak)
    added=_retained_json_bytes([reference,forest.expected,evidence])[0]
    evidence.update(retained_bytes=retained+added,construction_working_bytes=retained+temporary+added)
    require(host_capacity_bytes is None or max(evidence['construction_working_bytes'],peak)<=host_capacity_bytes,'startup record/index retention exceeds frozen host RAM')
    object.__setattr__(index,'retained_bytes',evidence['retained_bytes'])
    object.__setattr__(index,'startup_seconds',evidence['seconds']);object.__setattr__(index,'startup_evidence',_freeze_json(evidence))
    object.__setattr__(index,'startup_reference',_freeze_json(reference));object.__setattr__(index,'startup_publication_seconds',publication)
    return index,receipts,sources
