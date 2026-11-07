def _batch_for_timing(design,profile,inputs):
    require(inputs and all(r['analysis_split']=='validation' for r in inputs),'timing requires validation-only actual source inputs')
    first=inputs[0];require(all((r['source_task'],r['condition'],r['stream'])==(first['source_task'],first['condition'],first['stream']) for r in inputs),'heterogeneous timing input batch')
    dummies={r['instance_id']:r['source_instance_id'] for r in inputs if 'source_instance_id' in r}
    return source_batches(design,first['source_task'],'validation',[r['instance_id'] for r in inputs],first['condition'],first['stream'],profile,dummy_sources=dummies)[0]
