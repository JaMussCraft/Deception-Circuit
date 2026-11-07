"""Small candidate producer configuration and ordinary byte checks; no native imports."""
import hashlib,importlib.util,json,os,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()

def read(path):return json.loads(Path(path).read_text())
def durable(path,value):
 with Path(path).open('x') as stream:
  json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False);stream.write('\n');stream.flush();os.fsync(stream.fileno())
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,str(path));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def validate(c):
 if c.get('kind')!='ROOT_BOUND_PROVISIONAL_CPU_PRODUCER':raise ValueError('unbound candidate-only configuration')
 fields=('candidate_commit','export','canonical','run_root','job_id','cluster','account','partition','qos','cpus','memory_bytes',
  'allocation_seconds','child_cap_seconds','physical_alignment','virtual_alignment','image','image_sha256','packed_env','python',
  'candidate_source','inputs','input_files','input_aliases','packet_manifest','storage_free_bytes_required')
 if any(c.get(k) is None for k in fields):raise ValueError('unbound actual candidate configuration fields')
 assert c['candidate_only'] is True and c['execution_authorized'] is False
 assert not set(c)&{'admission','reservation','ledger_snapshot','source_publication','final_source_publication','receiver'}
 assert re.fullmatch('[0-9a-f]{40}',c['candidate_commit']) and re.fullmatch('[0-9]+',c['job_id'])
 assert (c['cluster'],c['account'],c['partition'],c['qos'])==('bridges2','cis260361p','RM','rm')
 assert c['cpus']==128 and c['memory_bytes']==192*1024**3
 assert c['allocation_seconds'] in (4500,5400) and c['child_cap_seconds']==c['allocation_seconds']-360
 for key in ('export','canonical','run_root','physical_alignment','virtual_alignment','image','packed_env','python'):
  path=Path(c[key]);assert path.is_absolute() and '..' not in path.parts and str(path)==c[key]
 assert Path(c['canonical'])==Path(c['run_root'])/'child'/'canonical'
 assert c['input_files'] and c['input_aliases'] and type(c['storage_free_bytes_required']) is int and c['storage_free_bytes_required']>0
 required_aliases={str(Path(c['export'])/name) for name in ('data','dataset/names.json','outputs/_analyses/specificity-ladder/a1-control-77b6487-m07')}
 assert required_aliases<={row['path'] for row in c['input_aliases']},'missing native cwd/data/IOI/parent input aliases'
 required={c['inputs'][k] for k in ('a1_design','a1_selected','historical_csv','root_ruling','execution_settings')}
 required.update(c['inputs']['registries']);required.add(str(Path(c['inputs']['matched_root'])/'build_manifest.json'))
 assert required<={row['path'] for row in c['input_files']},'incomplete original direct input closure'
 for row in c['input_files']:assert Path(row['path']).is_absolute() and re.fullmatch('[0-9a-f]{64}',row['sha256'])


def commands(c):
 root=Path(c['canonical']);inv=str(root/'inventory'/'prefit')
 base=['--experiment','directions','--design',str(root/'design.json'),'--commit',c['candidate_commit'],'--work-dir',str(root)]
 for path in c['inputs']['registries']:base+=['--registry',path]
 freeze=base+['--stage','prepare','--action','freeze']
 for key in ('a1_design','a1_selected','matched_root','historical_csv','root_ruling','execution_settings'):
  freeze+=['--'+key.replace('_','-'),c['inputs'][key]]
 return [('freeze',freeze),('prefit-inventory',base+['--stage','prepare','--action','inventory','--inventory',inv,'--inventory-stage','prefit']),
  ('pilot-target',base+['--inventory',inv,'--stage','prepare','--action','pilot-target','--pilot-part','prefit'])]


def check_sources(c,mapper=lambda value:value,include_inputs=True):
 ref=c['candidate_source'];manifest_path=Path(mapper(ref['path']));assert sha(manifest_path)==ref['sha256']
 m=read(manifest_path)
 assert m['kind']=='PROVISIONAL_CANDIDATE_EXECUTION_SOURCE_NOT_PUBLICATION_OR_ADMISSION'
 assert m['commit']==c['candidate_commit'] and m['export_root']==c['export'] and m['source_publication'] is False
 root=Path(mapper(c['export']));assert root.is_dir() and not root.is_symlink()
 expected=set()
 for row in m['files']:
  name=row['relative'];assert not Path(name).is_absolute() and '..' not in Path(name).parts
  path=root/name;expected.add(name)
  assert not path.is_symlink() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],name
 ordinary=set();aliases=set()
 for folder,dirs,files in os.walk(str(root),followlinks=False):
  for name in dirs+files:
   path=Path(folder)/name
   if path.is_symlink():aliases.add(str(path))
   elif path.is_file():ordinary.add(str(path.relative_to(root)))
 assert ordinary==expected,'undeclared/missing export members'
 declared=set()
 for row in c['input_aliases']:
  path=Path(mapper(row['path']));assert path.is_symlink() and os.readlink(str(path))==row['literal_target']
  try:path.relative_to(root);declared.add(str(path))
  except ValueError:pass
 assert aliases==declared,'undeclared/missing export aliases'
 for row in m.get('registry_aliases',[]):
  path=root/row['relative']
  assert path.is_symlink() and os.readlink(str(path))==row['literal_target']
  assert sha(mapper(row['literal_target']))==row['target_sha256'],'source snapshot registry changed'
 if include_inputs:
  for row in c['input_files']:
   path=Path(mapper(row['path']));assert path.is_file() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],row['path']
 return dict(candidate_commit=m['commit'],export=c['export'],files=len(expected),aliases=len(aliases),manifest_sha256=ref['sha256'])


def check_origins(export,modules=None):
 root=Path(export).resolve();result={}
 project_roots={'component_analysis','dataset','evaluation','models','scripts','tasks','tests'}|{path.stem for path in root.glob('*.py')}
 for name,module in (sys.modules if modules is None else modules).items():
  if name.split('.')[0] not in project_roots:continue
  origin=getattr(module,'__file__',None)
  if origin:
   path=Path(origin).resolve()
   try:path.relative_to(root)
   except ValueError:raise AssertionError('foreign native origin: '+name+' '+str(path))
   result[name]=str(path)
 return result


def object_inventory(root):
 root=Path(root);assert root.is_dir() and not root.is_symlink()
 assert {p.name for p in root.iterdir()}=={'payload.json','COMPLETE.json'}
 files={}
 for name in ('payload.json','COMPLETE.json'):
  path=root/name;assert path.is_file() and not path.is_symlink();before=path.stat()
  files[name]=dict(sha256=sha(path),nbytes=before.st_size)
  after=path.stat();assert (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
 marker=read(root/'COMPLETE.json');payload=files['payload.json']
 assert marker['schema_version']==1 and marker['kind']=='a3_complete'
 assert marker['files']=={'payload.json':dict(sha256=payload['sha256'],bytes=payload['nbytes'])}
 return dict(path=str(root.resolve()),files=files)


def inventory_outputs(c):
 root=Path(c['canonical']);target=object_inventory(root/'pilot-target-inventory'/'prefit')
 preparation=object_inventory(root/'pilot-target-preparation'/'prefit');descriptor=read(Path(preparation['path'])/'payload.json')
 assert descriptor['kind']=='a3_pilot_target_preparation_v1' and descriptor['part']=='prefit' and descriptor['target_stage']=='fit-select'
 assert descriptor['injected'] is False and descriptor['execution_authorized'] is False and descriptor['model_loaded'] is False
 assert descriptor['selected_reference'] is None and descriptor['source_identity']['commit']==c['candidate_commit']
 assert descriptor['provenance']['normal_completion'] is True and descriptor['provenance']['exit_code']==0
 payload=target['files']['payload.json']
 assert descriptor['target_reference']==target
 assert descriptor['emitted_payload_sha256']==payload['sha256'] and descriptor['emitted_payload_bytes']==payload['nbytes']
 return dict(target_reference=target,preparation_reference=preparation,target_payload_sha256=payload['sha256'],target_payload_bytes=payload['nbytes'],descriptor=descriptor,
  scope='independent streamed raw payload/marker inventory after native publication; full target reread charged',execution_authorized=False)


def check_packet(c,mapper=lambda value:value):
 ref=c['packet_manifest'];path=Path(mapper(ref['path']));assert sha(path)==ref['sha256']
 manifest=read(path)
 for row in manifest['files']:
  actual=Path(mapper(row['path']));assert actual.stat().st_size==row['bytes'] and sha(actual)==row['sha256'],row['path']
