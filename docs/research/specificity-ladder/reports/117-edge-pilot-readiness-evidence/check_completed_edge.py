import collections,copy,hashlib,json,os,pathlib,sys,time
W=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');B=W/'outputs/_analyses/specificity-ladder/a3-edge-runtime-87fceb28b3b4/runtime';O=W/'outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4';E=W/'docs/research/specificity-ladder/reports/117-edge-pilot-readiness-evidence';C='87fceb28b3b46f4a406c0280db785697a0bbd3fc'
sys.path.insert(0,str(B));start=time.perf_counter()
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
 return h.hexdigest()
def cg():
 p=pathlib.Path('/sys/fs/cgroup/user.slice/user-78031.slice');return {n:(p/n).read_text().strip() for n in ('memory.current','memory.max','memory.events')}
before=cg();assert int(before['memory.max'])-int(before['memory.current'])>12*1024**3
manifest=json.loads((O/'run_manifest.json').read_text());receipt=json.loads((O/'evidence/publication-receipt.json').read_text());assert manifest['complete_cpu_preparation'] is True and manifest['execution_authorized'] is False and manifest['commit']==C;assert sha(O/'run_manifest.json')==receipt['run_manifest_sha256']=='3a580b14d222bf78e0f8fa3c187b40d2341406c92ae321c99336e62b8ace9e53'
from component_analysis import a3_direction_runtime as a,a3_direction_artifacts as artifacts,a3_edge_pipeline as edge,a3_edge_workload as work,a3_pipeline as canonical,a3_design as design_api,ladder_pipeline as ladder
# Excluded direction execution/admission paths are not part of these checks.
def forbidden(*aa,**kw):raise AssertionError('excluded direction numerical/admission seam reached')
for name in ('run_pilot','_cost_packing_proofs','_completed_packing_proof','read_runtime_rows','dispatch'):setattr(a,name,forbidden)
design=ladder.read_artifact(O/'canonical/design.json');protocol=ladder.read_artifact(O/'canonical/direction_protocol.json');assert protocol==design['direction_protocol'] and protocol['commit']==C
assert sha(O/'canonical/design.json')==receipt['canonical_design_sha256']
registry=[str(W/'docs/research/held_out.json')];live=artifacts.validate_live(design,protocol,registry_paths=registry)
parent,selected,evidence=canonical.load_a1_parents(design['parent_evidence']['prepared_path'],design['parent_evidence']['selected_path']);assert evidence==design['parent_evidence'];canonical.validate_assessment_membership(design,parent);edge.validate_original_streams(design,parent)
prepared=a.read_object(O/'edge/prepared');assert a.object_reference(O/'edge/prepared')==receipt['prepared_reference'];assert prepared['commit']==C and prepared['design_sha256']==edge.digest(design);assert prepared['prepared_sha256']==edge.digest({k:v for k,v in prepared.items() if k!='prepared_sha256'})
assert prepared['design_reference']['path']==str((O/'canonical/design.json').resolve()) and prepared['design_reference']['sha256']==sha(O/'canonical/design.json')
assert prepared['code_hashes']==edge.code_hashes() and prepared['ruling']==edge.ruling_reference() and prepared['rules']==edge.RULES
assert prepared['bank_sources']==edge.ancestral_bank_sources(design)
source_digest=edge.source_rows_digest(design);prior=json.loads((W/'docs/research/specificity-ladder/reports/115-edge-tokenizer-review-evidence/mgnp.json').read_text());assert source_digest==prior['admission']['source_sha256']==prepared['source_admission']['source_sha256']
extended=dict(design);extended['access_rows']={t:list(rows)+prepared['bank_sources'][t]['rows'] for t,rows in design['access_rows'].items()};bank_protection=design_api.validate_access(extended,registry)
receiver_groups={}
for task,graph in prepared['graphs'].items():
 geometry={k:v for k,v in graph['geometry'].items() if k!='position_cells'};assert graph==edge.prepare_graph(design,task,geometry)
 receivers=sorted({tuple(x['receiver']) for x in graph['edges']});receiver_groups[task]=dict(graph_edges=len(graph['edges']),receiver_count=len(receivers),by_kind=dict(collections.Counter(x[0] for x in receivers)),cached_pilot_keys=64*len(receivers))
owner_groups=json.loads((O/'evidence/receiver-groups.json').read_text())
assert all(all(receiver_groups[t][k]==owner_groups[t][k] for k in receiver_groups[t]) for t in receiver_groups)
identity=edge._stage_identity(design,prepared)
fit=a.read_object(O/'edge/inventory-fit-target');work.validate_inventory(fit);assert a.object_reference(O/'edge/inventory-fit-target')==receipt['inventories']['inventory-fit-target']
expected_fit=work.freeze_inventory(design,prepared['graphs'],stage='fit',identity=identity,steps=8,bank_sources=prepared['bank_sources']);assert fit==expected_fit;del expected_fit
pilot=a.read_object(O/'edge/inventory-pilot');work.validate_inventory(pilot);assert a.object_reference(O/'edge/inventory-pilot')==receipt['inventories']['inventory-pilot'];assert pilot['measurement_target']==fit
expected_pilot=work.freeze_inventory(design,prepared['graphs'],stage='pilot',identity=identity,steps=8,bank_sources=prepared['bank_sources'],measurement_target=fit);assert pilot==expected_pilot;del expected_pilot
assert set(r['profile']['operation'] for r in fit['requirements'])=={'attribute_receiver'};assert all(r['profile']['integration_nodes']==8 for r in fit['requirements'])
assert {r['profile']['integration_nodes'] for r in pilot['requirements']}=={8,16};assert pilot['control_inventory']['profile_shapes']==[r['profile_id'] for r in fit['requirements']]
summary={name:dict(stage=v['stage'],phase=v['phase'],inventory_sha256=v['inventory_sha256'],keys=len(v['expected_keys']),requirements=len(v['requirements']),physical_calls=sum(r['count'] for r in v['requirements']),model_loads=v['model_loads'],finish_reserve_seconds=v['finish_reserve_seconds'],storage_requirements=v['storage_requirements'],shared_disk_pool_required=sum(n for k,n in v['storage_requirements']['tiers'].items() if k!='host_ram')) for name,v in [('pilot',pilot),('fit',fit)]}
ancestry=json.loads((O/'evidence/ancestry-before.json').read_text());after_ancestry=json.loads((O/'evidence/ancestry-after.json').read_text());assert ancestry==after_ancestry
current={str(p):dict(sha256=sha(p),bytes=pathlib.Path(p).stat().st_size) for p in ancestry};assert current==ancestry
imports={n:str(pathlib.Path(m.__file__).resolve()) for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','dataset','scripts','models','evaluation') and getattr(m,'__file__',None)};assert all(os.path.commonpath([p,str(B)])==str(B) for p in imports.values())
result=dict(kind='independent_edge_successor_artifact_check',commit=C,exit_code=0,elapsed_seconds=time.perf_counter()-start,actual_completed_object_hashes_match=True,owning_inventory_validators_and_exact_rebuilds=True,prepared_constituent_checks=True,owner_full_validate_prepared_timing_reused=True,accepted115_actual_producer_replay_reused=True,source_rows_digest=source_digest,cohorts={t:{k:len(v[k]) for k in ('fit_ids','selection_ids','assessment_ids')} for t,v in design['tasks'].items()},utilities={t:len(design['utility'][t]) for t in ('ioi','mmlu')},validation_utilities={t:len(design[t+'_validation']) for t in ('ioi','mmlu')},receiver_groups=receiver_groups,inventories=summary,runtime_signature=edge.runtime_signature(),numeric_profile=protocol['numeric_profile'],source_evidence=live,bank_protection=bank_protection,ancestry_files=len(ancestry),ancestry_bytes_unchanged=True,project_imports=imports,cgroup_before=before,cgroup_after=cg(),weights_loaded=False,execution_authorized=False,readiness_admission='BLOCKED: CPU source guard cost and staged M1 timing budget')
(E/'artifact-check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('project_imports','source_evidence','bank_protection')},indent=2))
