"""Owning CPU workload producers; never invoke an execution guard or model."""
import os,json,pathlib
from component_analysis import ladder_pipeline as ladder,a3_direction_runtime as authority
from component_analysis import a3_edge_pipeline as edge,a3_edge_workload as workload
w=pathlib.Path(os.environ['W']);o=pathlib.Path(os.environ['O']);commit=os.environ['C']
design=ladder.read_artifact(o/'canonical/design.json');prepared=authority.read_object(o/'edge/prepared')
edge.validate_prepared(prepared,design,registry_paths=[str(w/'docs/research/held_out.json')])
assert prepared['commit']==design['direction_protocol']['commit']==commit
identity=edge._stage_identity(design,prepared)
target=workload.freeze_inventory(design,prepared['graphs'],stage='fit',identity=identity,steps=8,bank_sources=prepared['bank_sources'])
pilot=workload.freeze_inventory(design,prepared['graphs'],stage='pilot',identity=identity,steps=8,bank_sources=prepared['bank_sources'],measurement_target=target)
for name,inventory in [('inventory-fit-target',target),('inventory-pilot',pilot)]:
 workload.validate_inventory(inventory)
 assert inventory['identity']==identity and inventory['gradient_nodes']==[8,16]
 authority.publish_object(o/'edge'/name,inventory)
 print(json.dumps(dict(name=name,stage=inventory['stage'],expected_keys=len(inventory['expected_keys']),requirements=len(inventory['requirements']),physical_calls=sum(r['count'] for r in inventory['requirements']),inventory_sha256=inventory['inventory_sha256'],storage_requirements=inventory['storage_requirements'],model_loads=inventory['model_loads'],finish_reserve_seconds=inventory['finish_reserve_seconds']),indent=2))
assert authority.read_object(o/'edge/inventory-pilot')['measurement_target']==authority.read_object(o/'edge/inventory-fit-target')
