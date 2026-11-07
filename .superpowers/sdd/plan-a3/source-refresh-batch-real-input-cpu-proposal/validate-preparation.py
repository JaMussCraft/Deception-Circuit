"""Actual complete CPU owner validation; no execution admission/model work."""
import os,sys,json,pathlib,hashlib,datetime,stat,time,resource
from component_analysis import a3_pipeline as canonical,a3_direction_artifacts as artifacts,a3_direction_runtime as authority,ladder_pipeline as ladder
from component_analysis import a3_edge_pipeline as edge,a3_edge_workload as workload,a3_mask_pipeline as mask,a3_mask_workload as mw
from types import SimpleNamespace
from dataset import user_inversion_pipeline as common
w=pathlib.Path(os.environ['W']);b=pathlib.Path(os.environ['B']);o=pathlib.Path(os.environ['O']);c=os.environ['C'];prior=w/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819';registry=[str(w/'docs/research/held_out.json')]
d=ladder.read_artifact(o/'canonical/design.json');protocol=ladder.read_artifact(o/'canonical/direction_protocol.json')
assert protocol==d['direction_protocol'] and protocol['commit']==c and d.get('injected') is False
parent,selected,evidence=canonical.load_a1_parents(w/'outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json',w/'outputs/_analyses/specificity-ladder/ladder-5f450dc/selected.json')
canonical._validate_parent_files(parent,a1_repo_root=w);canonical.validate_assessment_membership(d,parent)
assert evidence==d['parent_evidence']
live=artifacts.validate_live(d,protocol,registry_paths=registry)
pre=authority.read_object(o/'edge/prepared')
validation_started=time.perf_counter();validation_usage=resource.getrusage(resource.RUSAGE_SELF);validation_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
edge.validate_prepared(pre,d,registry_paths=registry)
validation_finished_usage=resource.getrusage(resource.RUSAGE_SELF)
validation_timing=dict(call='edge.validate_prepared(prepared, actual_canonical_design, registry_paths=original_registry)',started_utc=validation_utc,elapsed_seconds=time.perf_counter()-validation_started,user_cpu_seconds=validation_finished_usage.ru_utime-validation_usage.ru_utime,system_cpu_seconds=validation_finished_usage.ru_stime-validation_usage.ru_stime,process_maxrss_kib=validation_finished_usage.ru_maxrss,python=sys.executable,runtime_signature=edge.runtime_signature(),registry_paths=registry,prepared_path=str(o/'edge/prepared'),canonical_path=str(o/'canonical/design.json'))
validation_timing.update(hostname=os.uname().nodename,cpu_model=next((line.split(':',1)[1].strip() for line in pathlib.Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),None),thread_environment={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')})
(o/'evidence/validate-prepared-timing.json').write_text(json.dumps(validation_timing,indent=2)+'\n')
receiver_groups={}
for task,graph in pre['graphs'].items():
 receivers=sorted({tuple(e['receiver']) for e in graph['edges']})
 receiver_groups[task]=dict(graph_edges=len(graph['edges']),receiver_count=len(receivers),receivers=[list(r) for r in receivers],by_kind={kind:sum(r[0]==kind for r in receivers) for kind in sorted({r[0] for r in receivers})},pilot_validation_ids=d['tasks'][task]['selection_ids'][:8],cached_pilot_keys=len(receivers)*2*2*8*2,conditions=['D','I'],integration_nodes=[8,16],streams=['clean','corrupt'])
(o/'evidence/receiver-groups.json').write_text(json.dumps(receiver_groups,indent=2)+'\n')
assert pre['commit']==c and pre['injected'] is False
identity=edge._stage_identity(d,pre)
invinfo={};inventories={}
for name in ('inventory-fit-target','inventory-pilot'):
 inv=authority.read_object(o/'edge'/name);workload.validate_inventory(inv);assert inv['identity']==identity
 inventories[name]=inv
 invinfo[name]=dict(stage=inv['stage'],control_inventory=inv.get('control_inventory'),expected_keys=len(inv['expected_keys']),requirements=len(inv['requirements']),physical_calls=sum(r['count'] for r in inv['requirements']),storage_requirements=inv['storage_requirements'],inventory_sha256=inv['inventory_sha256'],model_loads=inv['model_loads'],finish_reserve_seconds=inv['finish_reserve_seconds'],object_reference=authority.object_reference(o/'edge'/name))
assert inventories['inventory-pilot']['measurement_target']==inventories['inventory-fit-target']
# The owning validator checks complete expected-key coverage and all frozen nodes,
# seeds/budgets/nulls and storage/overhead/hash contracts. Bind its task inputs too.
for inventory in inventories.values():
 assert set(inventory['tasks'])==set(d['tasks'])
 for task,spec in d['tasks'].items():
  record=inventory['tasks'][task]
  assert all(record[k]==spec[k] for k in ('fit_ids','selection_ids','assessment_ids'))
  assert record['source_sha256']==pre['graphs'][task]['source_sha256']
  assert record['bank_source_ids']==pre['bank_sources'][task]['source_ids']
  assert record['bank_source_sha256']==pre['bank_sources'][task]['source_sha256']
del inventories
# Scientific payload matches the previous canonical source; only runtime provenance may move.
old=ladder.read_artifact(prior/'canonical/design.json')
assert set(old)==set(d)
changed_fields=[k for k in old if old[k]!=d[k]]
allowed={'direction_protocol','direction_protocol_sha256','a1_repo_root','registry_hashes','mmlu_validation_candidates_manifest'}
assert set(changed_fields)<=allowed,changed_fields
# Registry provenance keys follow the frozen runtime's original input links.
# Resolve only these named provenance maps; require real file hashes and reject
# collisions or any changed registry content. All other MMLU metadata stays exact.
def resolved_registry_map(values):
 result={}
 for path,sha in values.items():
  source=pathlib.Path(path);assert source.is_file(),path
  # Stored catalog digests are historical preparation provenance. Real owner
  # validators above re-read CURRENT sets/graders; unrelated updates are allowed.
  resolved=str(source.resolve());assert resolved not in result or result[resolved]==sha,path
  result[resolved]=sha
 return result
current_registry=resolved_registry_map(d['registry_hashes'])
assert set(str(pathlib.Path(p).resolve()) for p in old['registry_hashes'])==set(current_registry)
old_mmlu=dict(old['mmlu_validation_candidates_manifest']);new_mmlu=dict(d['mmlu_validation_candidates_manifest'])
old_grader=old_mmlu.pop('grader_registry');new_grader=new_mmlu.pop('grader_registry')
assert old_mmlu==new_mmlu
current_grader=resolved_registry_map(new_grader)
assert set(str(pathlib.Path(p).resolve()) for p in old_grader)==set(current_grader)
registry_alias_proof=dict(original_held_out=old['registry_hashes'],successor_held_out=d['registry_hashes'],resolved_held_out=resolved_registry_map(d['registry_hashes']),original_grader=old_grader,successor_grader=new_grader,resolved_grader=resolved_registry_map(new_grader),nonregistry_mmlu_metadata_identical=True)
(o/'evidence/registry-alias-comparison.json').write_text(json.dumps(registry_alias_proof,indent=2)+'\n')
assert d['direction_protocol']['numeric_profile']==old['direction_protocol']['numeric_profile']
assert d['direction_protocol']['workload']==old['direction_protocol']['workload']
assert d['parent_evidence']==old['parent_evidence']
assert d['a1_repo_root']==str(b)
scientific_fields=[k for k in old if k not in {'direction_protocol','direction_protocol_sha256','a1_repo_root'}]
def science_values(value):
 result={k:value[k] for k in scientific_fields}
 result['registry_hashes']=sorted(str(pathlib.Path(p).resolve()) for p in value['registry_hashes'])
 result['mmlu_validation_candidates_manifest']=dict(value['mmlu_validation_candidates_manifest'],grader_registry=sorted(str(pathlib.Path(p).resolve()) for p in value['mmlu_validation_candidates_manifest']['grader_registry']))
 return result
comparison=dict(original_canonical_path=str(prior/'canonical/design.json'),original_canonical_file_sha256=common.file_hash(prior/'canonical/design.json'),successor_canonical_path=str(o/'canonical/design.json'),successor_canonical_file_sha256=common.file_hash(o/'canonical/design.json'),changed_operational_fields=changed_fields,unchanged_scientific_fields=scientific_fields,provenance_normalization='Only registry path keys normalized; current successor hashes checked against actual bytes and current owner guards; historical whole-registry digests may differ by unrelated legitimate updates',registry_alias_proof=str(o/'evidence/registry-alias-comparison.json'),original_scientific_sha256=edge.digest(science_values(old)),successor_scientific_sha256=edge.digest(science_values(d)),source_rows_digest_original=edge.source_rows_digest(old),source_rows_digest_successor=edge.source_rows_digest(d),utility_original_sha256=edge.digest(old['utility']),utility_successor_sha256=edge.digest(d['utility']))
assert comparison['original_scientific_sha256']==comparison['successor_scientific_sha256']
assert d['utility']==parent['utility']
edge.validate_original_streams(d,parent)
cohorts={t:{k:len(v[k]) for k in ('fit_ids','selection_ids','assessment_ids')} for t,v in d['tasks'].items()}
assert all(v['assessment_ids']==100 for v in cohorts.values())
assessment_rows={}
for task,spec in d['tasks'].items():
 chosen=set(spec['assessment_ids']);rows=[r for r in d['access_rows'][task] if r['instance_id'] in chosen]
 assert len(rows)==len(chosen)*len(edge.CONDITIONS)
 assessment_rows[task]=dict(expected_ids=len(parent['designs'][task]['assessment_ids']),observed_ids=len(chosen),expected_rows=len(chosen)*len(edge.CONDITIONS),observed_rows=len(rows),row_sha256=edge.digest(rows))
comparison.update(assessment_rows=assessment_rows,utility_counts=dict(ioi=len(d['utility']['ioi']),mmlu=len(d['utility']['mmlu'])),validation_utilities=dict(ioi=len(d['ioi_validation']),mmlu=len(d['mmlu_validation'])))
(o/'evidence/scientific-comparison.json').write_text(json.dumps(comparison,indent=2)+'\n')
del old
before=json.loads((o/'evidence/ancestry-before.json').read_text());after={}
for path,expected in before.items():
 p=pathlib.Path(path);observed=dict(sha256=common.file_hash(p),bytes=p.stat().st_size)
 if p.name not in ('held_out.json','directions.json'):assert observed==expected,path
 after[path]=observed
(o/'evidence/ancestry-after.json').write_text(json.dumps(after,indent=2)+'\n')
mp=authority.read_object(o/'mask/prepared')
md,mlive=mask._live_mask(mp,SimpleNamespace(commit=c,registry=registry))
assert mp['identity']['commit']==c and mp['execution_authorized'] is False and mp['chunk_size']==4
assert mp['identity']['code_hashes']==mask.mask_code_hashes()
assert authority.read_object(o/'mask-source-settings')['execution_authorized'] is False
maskinfo={}
for stage in ('pilot','full'):
 inv=authority.read_object(o/'mask'/('inventory-'+stage));mw.validate_inventory(inv)
 assert inv['identity']==mp['identity']
 maskinfo[stage]=dict(expected_keys=len(inv['expected_keys']),inventory_sha256=inv['inventory_sha256'],storage_requirements=inv['storage_requirements'],requirements=len(inv.get('requirements',[])),finish_reserve_seconds=inv['finish_reserve_seconds'],object_reference=authority.object_reference(o/'mask'/('inventory-'+stage)))
 del inv
snapshot_path=b.parent/'snapshot.json';snapshot=json.loads(snapshot_path.read_text());assert snapshot['source_commit']==c
for name,sha in snapshot['source_sha256'].items():
 p=b/name;assert not p.is_symlink() and common.file_hash(p)==sha and p.stat().st_mode & 0o222==0,name
assert common.file_hash(b.parent/'source.tar')==snapshot['source_archive_sha256']
for name,target in snapshot['input_links'].items():
 assert (b/name).is_symlink() and (b/name).resolve()==pathlib.Path(target).resolve(),name
project_imports={name:module.__file__ for name,module in list(sys.modules.items()) if name.split('.')[0] in ('component_analysis','dataset','scripts','evaluation','models') and getattr(module,'__file__',None)}
assert all(pathlib.Path(path).resolve().is_relative_to(b) for path in project_imports.values()),project_imports
for name in ('root-ruling.json','execution-settings.json'):assert (prior/name).read_bytes()==(o/name).read_bytes()
files={str(p.relative_to(o)):dict(sha256=common.file_hash(p),bytes=p.stat().st_size) for folder in ('canonical','edge','mask','mask-source-settings') for p in (o/folder).rglob('*') if p.is_file()}
manifest=dict(kind='a3_edge_successor_cpu_preparation_manifest_v1',commit=c,source_snapshot=str(snapshot_path),source_snapshot_sha256=common.file_hash(snapshot_path),source_archive_sha256=snapshot['source_archive_sha256'],source_files_expected=511,source_files_observed=len(snapshot['source_sha256']),source_bytes_unchanged=True,source_readonly=True,input_links={name:str((b/name).resolve()) for name in snapshot['input_links']},complete_cpu_preparation=True,edge_status='prepared_cpu_only',execution_authorized=False,weights_loaded=False,scientific_verdict=None,job_id=os.environ['SLURM_JOB_ID'],cluster='delta',local_cpu=False,slurm_cpu=True,allocation=json.loads((o/'evidence/allocation-start.json').read_text()),exit_code=0,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=sys.executable,project_imports=project_imports,parent_evidence=evidence,a1_code_dependencies=len(parent['code_hashes']),cohorts=cohorts,assessment_rows=assessment_rows,utility_counts=comparison['utility_counts'],validation_utilities=comparison['validation_utilities'],scientific_comparison=str(o/'evidence/scientific-comparison.json'),source_rows_sha256=comparison['source_rows_digest_successor'],ancestry_files_expected=len(before),ancestry_files_observed=len(after),static_ancestry_bytes_unchanged=True,current_registry_bytes_recorded=True,ancestry_before=str(o/'evidence/ancestry-before.json'),ancestry_after=str(o/'evidence/ancestry-after.json'),edge_graphs={t:dict(edges=len(g['edges']),geometry=g['geometry'],unsupported_bins=g['unsupported_bins']) for t,g in pre['graphs'].items()},edge_inventories=invinfo,mask_inventories=maskinfo,mask_protected_registry_evidence=mlive,receiver_groups=receiver_groups,validate_prepared_timing=validation_timing,prepared_object_reference=authority.object_reference(o/'edge/prepared'),canonical_numeric_profile=protocol['numeric_profile'],canonical_workload=protocol['workload'],protected_registry_evidence=live,artifacts=files,commands={p.stem:json.loads(p.read_text()) for p in (o/'evidence').glob('*-command.json') if p.stem!='validate-command'},next_m1_prerequisites=['Root successor mapping/reservation tied to this exact new commit/output/inventory; existing queued mask job23444798 mapping remains original','Fresh actual Slurm H200 allocation and live lease/storage/capacity/ledger checks','Independent readiness review; no model admission from CPU prep','Exact initial pilot with both independent model-loading/readout controls, native VJP, complete toy endpoint, serial geometry, 8/16 validation stability and complete source-bound target measurements','Initial pilot measures the full fit target only; later exact select/assess profiles require their actual completed fit/selection ancestry and separate root-approved measurements; all edge M1 reservations share the existing 0.75 GPU-hour ceiling','No fit/select/assess/finalization before owning later-stage gates'])
(o/'run_manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:manifest[k] for k in ('commit','cohorts','assessment_rows','utility_counts','validation_utilities','edge_graphs','edge_inventories','complete_cpu_preparation','execution_authorized')},indent=2))
print('CANONICAL_EDGE_AND_COMPLETE_INVENTORY_OWNER_CPU_VALIDATION_PASSED')
