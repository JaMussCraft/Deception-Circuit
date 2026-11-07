from pathlib import Path
import json,hashlib,collections
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');D=W/'.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103';R=D/'data-closure-supplement/result-23486081';O=D/'data-closure-exact-role-audit';O.mkdir(exist_ok=True);ROOT=Path('/projects/beto/swong2/Alignment')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((R/'supplement-manifest.json').read_text());old=json.loads((D/'data-inventory-result-r2/canonical-transfer-manifest.json').read_text())['ordinary_files'];keys=json.loads((R/'hash-key-references.json').read_text());C=json.loads((D/'data-closure-supplement/config.json').read_text());datarefs={k['resolved']:k for k in keys if k['field'] in ('source_hashes','selection_hashes')};source={};source_receipts={}
for parent,mapkey in [(Path(C['runtime']).parent,'source_sha256'),(W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5','source_files_sha256')]:
 s=json.loads((parent/'snapshot.json').read_text());runtime=Path(s['runtime_root'])
 for name,h in s[mapkey].items():source[str((runtime/name).resolve())]={'snapshot':str(parent/'snapshot.json'),'sha256':h}
 source_receipts[str((parent/'snapshot.json').resolve())]='exact source snapshot'
 for name in ['application.tar','source.tar']:
  if (parent/name).exists():source_receipts[str((parent/name).resolve())]='exact source archive'
controls={str((base/'docs/research'/name).resolve()) for base in (ROOT/'Deception-Circuit',W) for name in ('held_out.json','directions.json')}
bound={str(Path(C['G3']).resolve()),str(Path(C['Delta_G3_proof']).resolve()),str(Path(C['historical_G2']['path']).resolve())}
audit={str((D/'data-closure-supplement'/n).resolve()) for n in ['audit.py','config.json']}
credentials={'/work/nvme/beto/swong2/stored_tokens','/work/nvme/beto/swong2/token'}
operational={'/work/nvme/beto/swong2/.agent_harnesses.json'}
cache_ref=json.loads((W/'outputs/_analyses/specificity-ladder/a2-bridges2-20261102/model-cache-reference.json').read_text());hub=Path('/work/nvme/beto/swong2/models--meta-llama--Llama-3.1-8B-Instruct');cache={str(hub/'blobs'/row['sha256']):'declared cached metadata blob' for row in cache_ref['metadata']};cache[str(hub/'refs/main')]='declared cached revision reference'
metadata_by_name={row['name']:row for row in cache_ref['metadata']}
for lexical,target in m['namespace_aliases'].items():
 if lexical.startswith('/work/') and Path(lexical).name in metadata_by_name:
  resolved=str((Path(lexical).parent/target).resolve());expected=metadata_by_name[Path(lexical).name]
  assert m['external_metadata'][resolved]['sha256']==expected['sha256'] and m['external_metadata'][resolved]['bytes']==expected['nbytes']
  cache[resolved]='exact HF snapshot literal alias + declared metadata name and SHA256'
observed=set(m['ordinary_files'])|set(m['excluded'])|set(m['external_metadata']);rows={};unknown=[];newstate={};newexisting=dict(m['supplement_files']);state_fingerprints={}
# Bounded metadata accounting only: inspect bytes for the small state records already traced and owner-hashed.
small_candidates=[p for p in observed if p in datarefs or p in old]
state_candidates=[p for p in small_candidates if m['excluded'].get(p)=='root-current control/catalogue excluded' and p not in controls]
assert sum(Path(p).stat().st_size for p in state_candidates)<1024**2
for p in state_candidates:
 actual={'path':p,'bytes':Path(p).stat().st_size,'sha256':sha(p)};expected=old[p]['sha256'] if p in old else datarefs[p]['sha256'];assert actual['sha256']==expected,(p,'state bytes differ from original/owning hash')
 state_fingerprints[p]=actual
 if p not in old and p not in newexisting:newstate[p]=actual
for p in sorted(observed):
 if p in controls:role='root_current_catalogue_exact_route';authority='actual owning-proof before/after catalogue map; root refresh separately'
 elif p in source:role='exact_source_snapshot_member';authority=source[p]['snapshot']
 elif p in source_receipts:role='exact_source_export_receipt';authority=source_receipts[p]
 elif p in bound:role='separately_root_bound_G3_G2_or_CPU_proof';authority='exact config/proof identities'
 elif p in audit:role='exact_audit_operational_file';authority='executed audit packet'
 elif p in credentials:role='exact_credential_route_NOT_COPY';authority='explicit cache token routes; no contents read by role audit'
 elif p in operational:role='exact_external_operational_route_NOT_COPY';authority='agent harness metadata is not scientific input'
 elif p in cache:role='existing_declared_HF_cache_metadata';authority=cache[p]
 elif p in old:role='original_manifest_data_input';authority='original389'
 elif p in newexisting:role='previous_24_data_supplement';authority='actual23486081'
 elif p in newstate:role='newly_restored_required_data_input';authority='actual read trace plus exact prepared hash-key digest'
 else:role='UNRESOLVED';authority='none';unknown.append(p)
 rows[p]={'role':role,'authority':authority,'previous_filter':m['excluded'].get(p)}
coverage=[]
for key in keys:
 p=key['resolved'];role=rows.get(p,{}).get('role','UNRESOLVED');valid=role in ['exact_source_snapshot_member','original_manifest_data_input','previous_24_data_supplement','newly_restored_required_data_input'];coverage.append({**key,'role':role,'covered_by_exact_role':valid})
assert len(coverage)==227
uncovered=[q for q in coverage if not q['covered_by_exact_role']]
newfull=dict(newexisting);newfull.update(newstate);assert len(newfull)==33
result={'status':'PASS_EXACT_ROLE_ACCOUNTING' if not unknown and not uncovered else 'BLOCKED_UNRESOLVED_ROLES','read_trace_job':'23486081','failed_validation_job':'50188685','source_commit':C['source_commit'],'groups_sha256':C['G3_sha256'],'root_cause':'Broad basename state.json exclusion confused dataset state metadata with RS operational state. Prior successful owning trace remains valid; filtered supplemental transfer closure was incomplete. Prior assertion required frozen keys to be traced but did not require them to remain in transfer closure or exact justified role.','observed_role_counts':dict(collections.Counter(v['role'] for v in rows.values())),'all_observed_resolved_files':rows,'unresolved_observed_files':unknown,'all_frozen_hash_key_count':len(coverage),'all_frozen_hash_key_coverage':coverage,'uncovered_frozen_hash_keys':uncovered,'excluded_dataset_state_count':len(state_fingerprints),'excluded_state_already_original_count':sum(p in old for p in state_fingerprints),'new_missing_state_count':len(newstate),'new_missing_state_bytes':sum(v['bytes'] for v in newstate.values()),'new_missing_state_files':newstate,'corrected_supplement_files':newfull,'corrected_supplement_count':len(newfull),'corrected_supplement_bytes':sum(v['bytes'] for v in newfull.values()),'all_required_state_fingerprints':state_fingerprints,'original_manifest_count':len(old),'combined_count':len(set(old)|set(newfull)),'source_inventory_count':len(source),'grouping_only_no_owning_rerun':True,'no_transfer':True,'no_source_G3_changes':True,'external_operational_copy_forbidden':list(operational),'provenance_sha256':{str(p):sha(p) for p in [R/'supplement-manifest.json',R/'hash-key-references.json',R/'python-read-events.json',R/'owning-proof.json',D/'data-inventory-result-r2/canonical-transfer-manifest.json']}}
result['unresolved_observed_count']=len(unknown);result['uncovered_frozen_hash_key_count']=len(uncovered)
(O/'exact-role-coverage.json').write_text(json.dumps(result,indent=2)+'\n');(O/'new-missing-state-files.txt').write_text(''.join(str(Path(p).relative_to(ROOT))+'\n' for p in sorted(newstate)));(O/'corrected-full-supplement-files.txt').write_text(''.join(str(Path(p).relative_to(ROOT))+'\n' for p in sorted(newfull)));print(json.dumps({k:result[k] for k in ['status','observed_role_counts','unresolved_observed_files','all_frozen_hash_key_count','uncovered_frozen_hash_keys','excluded_dataset_state_count','excluded_state_already_original_count','new_missing_state_count','new_missing_state_bytes','corrected_supplement_count','corrected_supplement_bytes','combined_count']},indent=2))
