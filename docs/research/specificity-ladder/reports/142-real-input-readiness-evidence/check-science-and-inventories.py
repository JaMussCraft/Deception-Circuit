from pathlib import Path
import sys,os,json,hashlib,time,resource
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');O=W/'outputs/_analyses/specificity-ladder/a3-source-cost-pilots-40fe57289405';R=W/'outputs/_analyses/specificity-ladder/a3-source-cost-runtime-40fe57289405/runtime';E=Path(__file__).parent;sys.path.insert(0,str(R));os.chdir(R)
from component_analysis import ladder_pipeline as ladder,a3_direction_runtime as a,a3_edge_pipeline as edge,a3_edge_workload as ew,a3_mask_workload as mw
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest();started=time.perf_counter();mode=sys.argv[1];d=ladder.read_artifact(O/'canonical/design.json');assert d['direction_protocol']['commit']=='40fe57289405fd53a3fce02e5d4e47a0ebf78b64' and d['injected'] is False
if mode=='science':
 old=ladder.read_artifact(W/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/canonical/design.json');changed=[k for k in d if d[k]!=old[k]];assert set(changed)<=set(('a1_repo_root','direction_protocol','direction_protocol_sha256','registry_hashes','mmlu_validation_candidates_manifest'))
 def science(x):
  value={k:v for k,v in x.items() if k not in ('a1_repo_root','direction_protocol','direction_protocol_sha256')};value['registry_hashes']=sorted(str(Path(p).resolve()) for p in x['registry_hashes']);value['mmlu_validation_candidates_manifest']=dict(x['mmlu_validation_candidates_manifest'],grader_registry=sorted(str(Path(p).resolve()) for p in x['mmlu_validation_candidates_manifest']['grader_registry']));return value
 assert science(d)==science(old);assert d['direction_protocol']['numeric_profile']==old['direction_protocol']['numeric_profile'] and d['direction_protocol']['workload']==old['direction_protocol']['workload'];del old
 pre=a.read_object(O/'edge/prepared');live=edge.validate_prepared(pre,d,registry_paths=[str(W/'docs/research/held_out.json')]);assert pre['commit']==d['direction_protocol']['commit'] and not pre['injected']
 before=json.loads((O/'evidence/ancestry-before.json').read_text());after=json.loads((O/'evidence/ancestry-after.json').read_text());static=0
 for p,r in before.items():
  if Path(p).name in ('held_out.json','directions.json'):continue
  assert r==after[p] and Path(p).stat().st_size==r['bytes'] and sha(p)==r['sha256'];static+=1
 snapshot=json.loads((R.parent/'snapshot.json').read_text());assert len(snapshot['source_sha256'])==511
 for p,h in snapshot['source_sha256'].items():assert sha(R/p)==h and not (R/p).is_symlink() and (R/p).stat().st_mode&0o222==0
 assert sha(R.parent/'source.tar')==snapshot['source_archive_sha256']
 for p,target in snapshot['input_links'].items():assert (R/p).is_symlink() and (R/p).resolve()==Path(target).resolve()
 result={'science_payload_equal_to_original_canonical':True,'changed_operational_fields':changed,'original_numeric_profile_workload_equal':True,'actual_full_edge_validate_prepared_pass':True,'current_protection_grader':live,'static_ancestry_files_rehashed':static,'source_files_rehashed':511,'original_assessment_ids':{t:len(s['assessment_ids']) for t,s in d['tasks'].items()},'utilities':{t:len(d['utility'][t]) for t in ('ioi','mmlu')},'validation_utilities':{t:len(d[t+'_validation']) for t in ('ioi','mmlu')},'mask_Hbank_guard_count':2*sum(sum(r['condition']=='H' and r['split']=='validation' and r['instance_id'] in s['selection_ids'] for r in d['access_rows'][t]) for t,s in d['tasks'].items()),'edge_graphs':{t:{'edges':len(g['edges']),'receivers':len(set(tuple(e['receiver']) for e in g['edges']))} for t,g in pre['graphs'].items()}}
else:
 owner,stage=mode.split(':');name=('inventory-'+stage);inv=a.read_object(O/owner/name);(ew if owner=='edge' else mw).validate_inventory(inv)
 if owner=='edge':
  pre=a.read_object(O/'edge/prepared');assert inv['identity']==edge._stage_identity(d,pre)
  for task,scope in inv['tasks'].items():
   assert all(scope[k]==d['tasks'][task][k] for k in ('fit_ids','selection_ids','assessment_ids'));assert scope['source_sha256']==pre['graphs'][task]['source_sha256'] and scope['bank_source_ids']==pre['bank_sources'][task]['source_ids'] and scope['bank_source_sha256']==pre['bank_sources'][task]['source_sha256']
  if stage=='pilot':assert inv['measurement_target']==a.read_object(O/'edge/inventory-fit-target')
 else:
  pre=a.read_object(O/'mask/prepared');assert inv['identity']==pre['identity'] and inv['chunk_size']==pre['chunk_size']==4
  assert inv['scope']['widths']==pre['widths'] and inv['scope']['hbank_sources']==pre['hbank_sources'] and inv['scope']['new30_reference']==pre['new30']
  for task,scope in inv['scope']['tasks'].items():assert all(scope[k]==d['tasks'][task][k] for k in ('fit_ids','selection_ids','assessment_ids'))
  assert inv['scope']['ioi_validation']==[r['instance_id'] for r in d['ioi_validation']] and inv['scope']['mmlu_validation']==[r['instance_id'] for r in d['mmlu_validation']]
 result={'owner':owner,'stage':inv['stage'],'owning_complete_validator_pass':True,'identity_actual_prepared_match':True,'scope_actual_canonical_and_banks_match':True,'expected_keys':len(inv['expected_keys']),'inventory_sha256':inv['inventory_sha256'],'requirements':len(inv.get('requirements',[])),'physical_calls':sum(r['count'] for r in inv.get('requirements',[])),'storage_requirements':inv['storage_requirements'],'control_inventory':inv.get('control_inventory'),'model_loads':inv.get('model_loads'),'finish_reserve_seconds':inv['finish_reserve_seconds']}
result.update(mode=mode,wall_seconds=time.perf_counter()-started,host_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,models_loaded=False,authority_exercised=False);(E/('checked-'+mode.replace(':','-')+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('current_protection_grader','storage_requirements','control_inventory')},indent=2))
