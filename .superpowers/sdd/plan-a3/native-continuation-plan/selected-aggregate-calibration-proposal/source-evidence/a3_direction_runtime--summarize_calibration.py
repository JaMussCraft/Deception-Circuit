def summarize_calibration(design,protocol,selected,rows,references,*,root,inventory,guard):
    from component_analysis import a3_direction_reporting as reporting,a3_statistics
    guard();require(all(r.get('split')=='validation' and r.get('panel')=='calibration' for r in rows),'conditional power requires validation-only calibration rows')
    panel=reporting.pack_statistics_panel(design,selected,rows,split='validation')
    result=a3_statistics.simulate_conditional_power(panel,n_rep=protocol['bootstrap']['power'],seed=protocol['bootstrap']['power_seed'])
    payload=dict(kind='a3_direction_conditional_power_summary_v1',complete=True,injected=design['injected'],source_split='validation',
        inventory_sha256=inventory['inventory_sha256'],design_sha256=workload.digest(design),protocol_sha256=workload.digest(protocol),
        selected_reference=object_reference(Path(root)/'selected'),raw_row_references=references,
        raw_rows_sha256=hashlib.sha256(reporting._bytes(rows)).hexdigest(),conditional_power=result,
        continuation_authorized=False,assessment_outcomes_read=False,source_guard=guard())
    publish_object(Path(root)/'calibration-summary',a3_statistics._json(payload))
    return payload
