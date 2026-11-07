def verify_scenario(root,*,load_model=True):
    root=Path(root);scenario=r.read_object(root/'scenario')
    r.require(scenario['source_hashes']==source_identity(),'verification source changed')
    r.require(r.pipeline._bundle_byte_reference(root/'tiny-model')==scenario['model_reference'],'tiny base model backing changed')
    design=r.ladder.read_artifact(root/'design.json');protocol=r.ladder.read_artifact(root/'direction_protocol.json')
    r.require(r.workload.digest(design)==scenario['design_sha256'] and r.workload.digest(protocol)==scenario['protocol_sha256'],'frozen scenario inputs changed')
    if not load_model:return design,protocol,None,None
    model,plain=tiny_model()
    with np.load(root/'tiny-model'/'state.npz',allow_pickle=False) as arrays:
        plain.load_state_dict({k:torch.from_numpy(np.array(arrays[k],copy=True)) for k in arrays.files},strict=True)
    r.require(model_identity(plain)==scenario['model_identity'],'full tiny model state/config differs across process')
    return design,protocol,model,plain
