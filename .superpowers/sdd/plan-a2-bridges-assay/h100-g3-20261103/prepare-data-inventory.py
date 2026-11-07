"""CPU-only DATA inventory; no group/source freeze, readiness or model grant."""
import os,sys,json,pathlib,hashlib,subprocess,time
P=pathlib.Path(__file__).resolve().parent;C=json.loads((P/'plan.json').read_text());W=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');B=W/'outputs/_analyses/specificity-ladder/a3-source-cost-runtime-40fe57289405/runtime';ALIGN=pathlib.Path('/projects/beto/swong2/Alignment')
assert os.environ.get('SLURM_JOB_ID','').isdigit() and os.environ.get('CUDA_VISIBLE_DEVICES')==''
raw=subprocess.check_output(['scontrol','-o','show','job',os.environ['SLURM_JOB_ID']],universal_newlines=True);facts=dict(x.split('=',1) for x in raw.split() if '=' in x);assert facts['JobState']=='RUNNING'
assert not any(k.startswith('gres/gpu') and float(v)>0 for k,v in (x.split('=',1) for x in facts.get('AllocTRES',facts.get('TRES','')).split(',') if '=' in x))
OUT=pathlib.Path(os.environ['A2_BRIDGES_DATA_INVENTORY_OUTPUT']);OUT.mkdir(parents=True,exist_ok=False)
opened=set();excluded=0
secret_names={'token','stored_tokens','credentials','.netrc','id_rsa','id_ed25519'}
def allowed(path):
 global excluded
 p=pathlib.Path(path)
 if p.name.lower() in secret_names or any(s in p.parts for s in ['.ssh','.aws','.git']):excluded+=1;return False
 return True
def audit(event,args):
 if event=='open' and args and isinstance(args[0],(str,bytes)):
  try:
   p=pathlib.Path(os.fsdecode(args[0]));mode=args[1] if len(args)>1 else None
   if p.is_absolute() and (not isinstance(mode,str) or not any(s in mode for s in ['w','a','+'])) and allowed(p):opened.add(str(p))
  except (ValueError,TypeError):pass
sys.addaudithook(audit);sys.path.insert(0,str(B));os.chdir(B)
from component_analysis import a2_pipeline as a2
args=a2.parser().parse_args(['--stage','freeze','--design',str(W/'outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json'),'--selected',str(W/'outputs/_analyses/specificity-ladder/ladder-5f450dc/selected.json'),'--commit',C['baseline_source_commit'],'--work-dir',C['new_main'],'--comparison',C['comparison'],'--source-records',C['source_records'],'--registry',str(W/'docs/research/held_out.json'),'--batch-size','8'])
prepared,selected,sidecar=a2._load_context(args);assert prepared['injected'] is False
metadata=a2.model_geometry_receipt(prepared)
records=json.loads(pathlib.Path(C['source_records']).read_text())['records'];assert len(records)==18
queue=[];seen=set();files={};outside={};legacy_roots=set()
def add(value):
 if isinstance(value,str) and value.startswith('/'):
  p=pathlib.Path(value)
  if allowed(p) and p.is_file():queue.append(str(p))
def walk(value):
 if isinstance(value,dict):
  for k,v in value.items():add(k);walk(v)
 elif isinstance(value,list):
  for v in value:walk(v)
 elif isinstance(value,str):add(value)
for path in [args.design,args.selected,str(a2.a1.selection_manifest_path(args.selected)),C['comparison'],C['source_records']]:add(path)
for x in [prepared['source_hashes'],prepared['selection_hashes'],prepared['registry_hashes'],prepared['grader_registry'],metadata,records]:walk(x)
for record in records:legacy_roots.add(record['execution_root'])
for p in pathlib.Path(C['matched_root']).rglob('*'):
 if p.is_file():add(str(p))
queue.extend(sorted(opened))
def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
while queue:
 name=queue.pop()
 if name in seen:continue
 seen.add(name);p=pathlib.Path(name)
 if not p.is_file() or not allowed(p):continue
 resolved=p.resolve()
 if resolved.is_relative_to(B) or any(resolved.is_relative_to(pathlib.Path(r)) for r in legacy_roots):continue # final/legacy source archives separately attested; no sourceexport now
 if not (resolved.is_relative_to(ALIGN) or str(resolved).startswith('/work/nvme/beto/swong2/')):continue # thirdparty/system libs are environment, not project data
 if p.suffix.lower() in {'.pt','.pth','.pkl','.pickle','.safetensors','.bin'}:raise RuntimeError('Unexpected referenced model/binary asset needs separate review: '+str(p))
 item=dict(path=name,resolved_path=str(resolved),sha256=sha(p),bytes=p.stat().st_size,symlink_target=os.readlink(p) if p.is_symlink() else None)
 if resolved.is_relative_to(ALIGN):files[name]=item
 else:outside[name]=item # HFmetadata requires explicit original/work mount, not arbitrary project copy
 if p.suffix=='.json' and p.stat().st_size<=64*1024**2:
  try:walk(json.loads(p.read_text()))
  except (UnicodeDecodeError,json.JSONDecodeError):pass
result=dict(kind='a2_bridges_data_only_closure_manifest_v1',job_id=os.environ['SLURM_JOB_ID'],baseline_context_only=C['baseline_source_commit'],final_source_choice_pending=True,source_exported=False,groups_frozen=False,model_loaded=False,production_readiness=False,project_files=files,external_cache_metadata=outside,required_legacy_execution_roots=sorted(legacy_roots),expected_model_geometry=metadata,source_records=18,matched_root=C['matched_root'],excluded_credential_candidate_count=excluded,coverage='Explicit prepared/source/selection/registry/records+recursive existing JSON refs+bounded matched root; supplementary Python read-open audit. Final acceptedsource and genuine remote owning guards still required; no broad project archive copied.')
(OUT/'data-transfer-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'project-files.txt').write_text(''.join(str(pathlib.Path(f).relative_to(ALIGN))+'\n' for f in sorted(files)))
(OUT/'COMPLETE.json').write_text(json.dumps(dict(data_inventory_complete=True,production_readiness=False,project_files=len(files),external_metadata=len(outside),total_project_bytes=sum(v['bytes'] for v in files.values()),model_loaded=False,source_exported=False,groups_frozen=False),indent=2)+'\n')
print('DATA_INVENTORY_ONLY_COMPLETE',len(files),len(outside))
