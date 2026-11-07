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
