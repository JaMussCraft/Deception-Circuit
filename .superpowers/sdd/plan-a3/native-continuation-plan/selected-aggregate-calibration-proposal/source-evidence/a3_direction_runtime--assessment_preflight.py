def assessment_preflight(design,protocol,selected,inventory,*,root,reservation_path):
    """Root explicitly binds the complete validation power evidence before A."""
    root=Path(root);summary_path=root/'calibration-summary'
    summary=read_object(summary_path)
    require(summary.get('kind')=='a3_direction_conditional_power_summary_v1' and summary.get('complete') is True
        and summary.get('source_split')=='validation' and summary.get('assessment_outcomes_read') is False,
        'complete validation-only conditional power required before assessment')
    require(summary.get('injected') is design['injected'] and summary.get('inventory_sha256')==inventory['inventory_sha256']
        and summary.get('design_sha256')==workload.digest(design) and summary.get('protocol_sha256')==workload.digest(protocol)
        and summary.get('selected_reference')==object_reference(root/'selected'),'calibration summary source/selection bytes differ')
    for reference in summary['raw_row_references']:
        require(object_reference(reference['path'])==reference,'completed calibration source bytes changed')
    require(reservation_path,'root assessment reservation must reference reviewed calibration evidence')
    reservation=read_object(reservation_path)
    require(reservation.get('calibration_summary_reference')==object_reference(summary_path),
        'root assessment reservation lacks the exact complete calibration reference')
    return dict(calibration_summary_reference=object_reference(summary_path),continuation_authorized=False)
