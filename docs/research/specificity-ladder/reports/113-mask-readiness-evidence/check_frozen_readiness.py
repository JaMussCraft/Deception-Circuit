import argparse,hashlib,json,os,pathlib,stat,sys,time
from types import SimpleNamespace
W=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
B=W/'outputs/_analyses/specificity-ladder/a3-pilot-runtime-74efb4d04819/runtime'
O=W/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819'
C='74efb4d0481968a1d0138eb1a79b97f302fd3c3b'
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def cgroup():
 p=pathlib.Path('/sys/fs/cgroup/user.slice/user-78031.slice')
 return {n:(p/n).read_text().strip() for n in ('memory.current','memory.max','memory.events')}
a=argparse.ArgumentParser();a.add_argument('mode',choices=['source','live','full']);a.add_argument('--output',required=True);args=a.parse_args()
start=time.perf_counter();result={'mode':args.mode,'commit':C,'python':sys.executable,'cgroup_before':cgroup(),'weights_loaded':False,'execution_authorized':False}
if args.mode=='source':
 s=json.loads((B.parent/'snapshot.json').read_text());m=json.loads((O/'run_manifest.json').read_text());assert s['source_commit']==m['commit']==C
 observed=[];links={}
 for directory,dirs,files in os.walk(B,followlinks=False):
  for name in list(dirs)+files:
   p=pathlib.Path(directory)/name
   if p.is_symlink():links[str(p.relative_to(B))]=str(p.resolve())
  for name in files:
   p=pathlib.Path(directory)/name
   if p.is_symlink():continue
   rel=str(p.relative_to(B));data=p.read_bytes();observed.append(rel)
   assert not p.stat().st_mode&0o222,rel
   assert hashlib.sha256(data).hexdigest()==s['source_sha256'][rel],rel
   assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==s['git_blob_sha1'][rel],rel
 assert set(observed)==set(s['source_sha256'])==set(s['git_blob_sha1']) and len(observed)==509
 assert links==s['input_links'],links
 assert sha(B.parent/'source.tar')==s['source_archive_sha256']
 for rel,e in m['artifact_files'].items():assert (O/rel).stat().st_size==e['nbytes'] and sha(O/rel)==e['sha256'],rel
 result.update(source_files=len(observed),source_links=links,archive_sha256=s['source_archive_sha256'],snapshot_sha256=sha(B.parent/'snapshot.json'),manifest_sha256=sha(O/'run_manifest.json'),artifact_file_count=len(m['artifact_files']),all_hashes_match=True)
else:
 assert pathlib.Path(os.environ['PYTHONPATH']).resolve()==B
 from component_analysis import a3_pipeline as canonical,a3_direction_artifacts as artifacts,a3_direction_runtime as authority,ladder_pipeline as ladder,a3_mask_pipeline as mask,a3_mask_workload as mw
 registry=[str(W/'docs/research/held_out.json')]
 design=ladder.read_artifact(O/'canonical/design.json');protocol=ladder.read_artifact(O/'canonical/direction_protocol.json');assert protocol==design['direction_protocol'] and protocol['commit']==C
 mp=authority.read_object(O/'mask/prepared');settings=authority.read_object(O/'mask-source-settings')
 assert mp['identity']['numeric_profile']==settings['numeric_profile'] and settings['execution_authorized'] is False
 if args.mode=='live':
  parent,selected,evidence=canonical.load_a1_parents(design['parent_evidence']['prepared_path'],design['parent_evidence']['selected_path'])
  assert evidence==design['parent_evidence'];canonical._validate_parent_files(parent,a1_repo_root=design['a1_repo_root']);canonical.validate_assessment_membership(design,parent)
  live=artifacts.validate_live(design,protocol,registry_paths=registry)
  assert len(design['utility']['ioi'])==100 and len(design['utility']['mmlu'])==32
  assert len(design['ioi_validation'])==100 and len(design['mmlu_validation'])==32
  for name in ('ioi','mmlu'):
   held=design['utility'][name];val=design[name+'_validation']
   assert not {x['instance_id'] for x in held}&{x['instance_id'] for x in val}
   assert not {tuple(x['streams']['clean']['tokens']) for x in held}&{tuple(x['streams']['clean']['tokens']) for x in val}
  pinned=pathlib.Path('/u/swong2/.conda/envs/mgnp/bin/python').resolve()==pathlib.Path(sys.executable).resolve()
  os.environ['SPECIFICITY_A3_MASK_LAUNCH_EXECUTABLE']=sys.executable
  if pinned:
   actual,evidence=mask._live_mask(mp,SimpleNamespace(commit=C,registry=registry))
   fresh=mask.prepare_mask(O/'canonical/design.json',commit=C,chunk_size=4,registry_paths=registry,root_bundle=O/'mask-source-settings')
   assert fresh==mp,'independent pure preparation differs'
   inv=authority.read_object(O/'mask/inventory-pilot');mw.validate_inventory(inv)
   expected=mw.build_inventory(design,identity=mp['identity'],chunk_size=4,finish_reserve_seconds=300.,hbank_sources=mp['hbank_sources'],stage='pilot',widths=mp['widths'],new30=mp['new30'])
   assert expected==inv and len(inv['expected_keys'])==31191
   try:mask._live_mask(mp,SimpleNamespace(commit=C,registry=registry,ledger_snapshot=None,reservation=None),inv)
   except ValueError as error:assert 'ledger mapping/reservation' in str(error);result['missing_root_authority_rejected']=str(error)
   else:raise AssertionError('missing root authority admitted')
   result['production_mask_live_static']='passes under pinned interpreter'
  else:
   try:mask._live_mask(mp,SimpleNamespace(commit=C,registry=registry))
   except ValueError as error:assert 'source closure' in str(error);result['production_mask_live_static']='correctly rejects nonpinned interpreter: '+str(error)
   else:raise AssertionError('base interpreter impersonated pinned production artifact')
  result.update(canonical_live=True,cohorts={t:{k:len(v[k]) for k in ('fit_ids','selection_ids','assessment_ids')} for t,v in design['tasks'].items()},utility_assessment={'ioi':100,'mmlu':32},utility_validation={'ioi':100,'mmlu':32},mask_profile=mp['identity']['numeric_profile'],mask_code_hashes=mp['identity']['code_hashes'],live_evidence=live)
 elif args.mode=='full':
  # This is the only reviewer process decoding the full target inventory.
  current=int(cgroup()['memory.current']);limit=int(cgroup()['memory.max']);assert limit-current>12*1024**3,'insufficient cgroup headroom'
  inv=authority.read_object(O/'mask/inventory-full');mw.validate_inventory(inv)
  expected=mw.build_inventory(design,identity=mp['identity'],chunk_size=4,finish_reserve_seconds=300.,hbank_sources=mp['hbank_sources'],stage='full',widths=mp['widths'],new30=mp['new30'])
  assert expected==inv and len(inv['expected_keys'])==3437966
  result.update(full_target_validator=True,expected_keys=len(inv['expected_keys']),inventory_sha256=inv['inventory_sha256'],storage_requirements=inv['storage_requirements'],pilot_key_count=31191)
 imports={n:str(pathlib.Path(v.__file__).resolve()) for n,v in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','dataset','evaluation','models','scripts') and getattr(v,'__file__',None)}
 assert all(os.path.commonpath([p,str(B)])==str(B) for p in imports.values()),imports
 result['project_imports']=imports
result.update(exit_code=0,elapsed_seconds=time.perf_counter()-start,cgroup_after=cgroup())
pathlib.Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('mask_code_hashes','live_evidence','project_imports')},indent=2))
