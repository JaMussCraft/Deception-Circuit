def aggregate_pilot_cases(model,design,protocol,inv,*,root,part,binding,selected_path=None,startup_seconds=0):
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
    try:
        r._pilot_invocation=replay
        result=r.run_pilot(model,design,protocol,inv,root=root,args=SimpleNamespace(pilot_part=part,selected=selected_path),
            guard=lambda:None,startup_seconds=startup_seconds,selected=selected)
    finally:r._pilot_invocation=original
    r.require(replayed==wanted and [r.object_reference(base/x) for x in wanted]==references,'verification aggregate source/order changed')
    r.publish_object(Path(root)/'pilot-verification-aggregate'/part,dict(injected=True,execution_authorized=False,case_references=references,
        case_order=replayed,original_case_samples_replayed=True,case_forwards_reexecuted=False,new_reconciliation_work_is_actual=True,
        original_case_forward_calls=sum(r.artifacts._strict_json(base/x/'case.json')['original_case_forward_calls'] for x in wanted),
        new_reconciliation_seconds=time.perf_counter()-began,aggregate_receipt_reference=r.object_reference(Path(root)/'pilot'/part)))
    return result
