def summarize_runtime(design,protocol,selected,rows,calibration_rows,references,calibration_references,*,root,inventory,final,guard):
    from component_analysis import a3_direction_reporting as reporting
    guard()
    if final:require(design.get('injected') is False,'injected lineage cannot finalize')
    artifacts._coverage(rows+calibration_rows,inventory['expected_keys'])
    validate_primary_interpretability(rows+calibration_rows)
    probes=assessment_probe_results(design,protocol,selected,inventory,root=root,guard=guard)
    inputs=dict(design=design,selected=selected,rows=rows,calibration_rows=calibration_rows,probe_results=probes)
    refs={name:dict(sha256=hashlib.sha256(reporting._bytes(value)).hexdigest(),nbytes=len(reporting._bytes(value))) for name,value in inputs.items()}
    refs['rows']['artifact_reference']=references;refs['calibration_rows']['artifact_reference']=calibration_references
    result=reporting.assemble_direction_summary(design,selected,rows,input_references=refs,calibration_rows=calibration_rows,
        probe_results=probes,final=False,n_boot=protocol['bootstrap']['assessment'],seed=protocol['bootstrap']['assessment_seed'],
        n_rep=protocol['bootstrap']['power'],power_seed=protocol['bootstrap']['power_seed'])
    identity=dict(inventory['identity'],injected=design['injected'],pilot=False,complete=True)
    artifacts.validate_final_identity(identity,final=final)
    if final:
        require(set(design['tasks'])=={'far_v2','ser_v2','sdr_v2'} and design['seeds']==[42,1,123]
            and len(design['utility']['ioi'])==100 and len(design['utility']['mmlu'])==32
            and len(design['ioi_validation'])==100 and len(design['mmlu_validation'])==32
            and all(len(s['assessment_ids'])==100 for s in design['tasks'].values()),'complete original production counts required for final')
        require(result['diagnostic_readiness'] is True and all(r.get('supported') is True and r.get('replay_valid') is True
            and r.get('gate_valid') is True and r.get('positive_control',{}).get('valid') is True for r in rows+calibration_rows),
            'complete actual utility/control/secondary/steering/probe evidence required for final')
    result.update(finalized=bool(final),runtime_identity=identity,execution_evidence=dict(complete=True,actual_execution=True,
        observed_rows=len(rows)+len(calibration_rows),expected_rows=len(inventory['expected_keys']),
        inventory_sha256=inventory['inventory_sha256'],assessment_references=references,calibration_references=calibration_references,
        selection_reference=object_reference(Path(root)/'selected'),source_guard=guard()),continuation_authorized=False)
    publish_object(Path(root)/'summary',result)
    return result
