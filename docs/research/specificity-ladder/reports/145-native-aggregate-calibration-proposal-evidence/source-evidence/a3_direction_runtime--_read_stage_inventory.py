def _read_stage_inventory(args,design,protocol,*,fits=None,selected=None):
    require(args.inventory,'completed frozen inventory required')
    inv=read_object(args.inventory);workload._validate_inventory(inv)
    require(inv['identity']==workload.inventory_identity(design,protocol),'inventory differs from canonical design/protocol')
    if fits is not None: require(inv['frozen_inputs'].get('fits') in (None,fits),'inventory fit bytes differ')
    if selected is not None: require(inv['frozen_inputs'].get('selected')==selected,'inventory selection differs')
    return inv
