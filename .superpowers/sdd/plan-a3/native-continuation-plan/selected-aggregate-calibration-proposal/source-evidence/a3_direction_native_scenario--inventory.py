def inventory(root,design,protocol,stage,*,fits=None,selected=None):
    value=r.workload.build_inventory(design,protocol,stage=stage,fits=fits,selected=selected)
    path=Path(root)/'inventory'/stage
    if path.exists():r.require(r.workload.digest(r.read_object(path))==r.workload.digest(value),'frozen inventory changed')
    else:r.publish_object(path,value)
    return value
