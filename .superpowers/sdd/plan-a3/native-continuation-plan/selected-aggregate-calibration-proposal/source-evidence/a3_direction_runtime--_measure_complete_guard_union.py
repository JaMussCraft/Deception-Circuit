def _measure_complete_guard_union(receipt,reconciliation,root,guard):
    """Read all real dependencies plus an explicitly inert final-receipt byte bound."""
    import tempfile
    footprint=dict(kind='a3_complete_guard_union_timing_v1',dependency_roots=list(reconciliation._paths),
        repeated_samples=3,envelope_is_inert_not_execution=True,final_metadata_byte_allowance=4096)
    receipt['guard_dependency_measurement']=footprint
    # The current content contains only actual observed data. The fixed space
    # covers the small timing/counter fields added below; actual final serialized
    # size is independently checked against this limit before publication.
    bound=_object_payload_size(receipt)+footprint['final_metadata_byte_allowance']
    parent=Path(root)/'pilot-scratch';parent.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='final-receipt-envelope-',dir=parent) as tmp:
        path=Path(tmp)/'envelope'
        publish_object(path,dict(inert_final_receipt_byte_envelope='x'*bound,execution_authorized=False))
        startup=Path(tmp)/'startup-envelope'
        publish_object(startup,dict(inert_startup_record_byte_envelope='x'*_STARTUP_RECORD_PAYLOAD_BYTES,execution_authorized=False))
        startup_bounds={name:value['nbytes'] for name,value in object_reference(startup)['files'].items()}
        file_bounds={name:value['nbytes'] for name,value in object_reference(path)['files'].items()}
        witnesses=[_make_file_witness([p]) for p in reconciliation._paths]+[_make_file_witness([path]),_make_file_witness([startup])]
        forest=_DependencyForest(witnesses);setup=time.perf_counter()-start
        samples=[];result=None
        for _ in range(3):
            began=time.perf_counter();result=forest.refresh();guard();reconciliation.check_deadline();samples.append(time.perf_counter()-began)
        for measurement in receipt['measurements']:
            if measurement['operation']=='guard_refresh':measurement['batch_seconds']=samples
        footprint.update(final_receipt_payload_upper_bytes=bound,measured_bytes_per_refresh=result['verified_bytes'],
            measured_roots=result['roots'],setup_seconds=setup,final_receipt_file_upper_bytes=file_bounds,
            startup_record_payload_upper_bytes=_STARTUP_RECORD_PAYLOAD_BYTES,startup_record_file_upper_bytes=startup_bounds)
        receipt['proof_validation_seconds']+=setup
