"""Complete genuine-input CPU algorithm oracle; no model/admission/source rewrite."""
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,json,os,sys,time
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--packet-sha256',required=True);ap.add_argument('--config',required=True);ap.add_argument('--config-sha256',required=True);ap.add_argument('--mode',choices=('original','candidate'),required=True);ap.add_argument('--environment',choices=('mgnp','base'),required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for part in iter(lambda:f.read(1048576),b''):h.update(part)
 return h.hexdigest()
assert sha(P/'manifest.json')==a.packet_sha256
for name,digest in json.loads((P/'manifest.json').read_text()).items():assert sha(P/name)==digest,name
assert sha(a.config)==a.config_sha256;c=json.loads(Path(a.config).read_text());B=Path(c['runtime']);OUT=Path(a.output);assert OUT.is_dir()
def write(name,value):
 with (OUT/name).open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
def sources():
 assert sha(c['snapshot'])==c['snapshot_sha256'];s=json.loads(Path(c['snapshot']).read_text());assert s['source_commit']==c['source_commit'] and len(s['source_sha256'])==511 and len(s['input_links'])==4 and not s['source_code_symlinks']
 files=set();links=set()
 for item in B.rglob('*'):
  name=str(item.relative_to(B))
  if item.is_symlink():links.add(name)
  elif item.is_file():files.add(name)
 assert files==set(s['source_sha256']) and links==set(s['input_links'])
 for n,digest in s['source_sha256'].items():assert not (B/n).is_symlink() and sha(B/n)==digest,n
 for n,target in s['input_links'].items():assert (B/n).is_symlink() and os.readlink(B/n)==target and (B/n).resolve()==Path(target).resolve(),n
 for n,digest in c['source13'].items():assert sha(Path(c['W'])/n)==digest,n
 for pin in c['pinned_files']:assert sha(pin['path'])==pin['sha256']
 assert sha(Path(c['canonical'])/'design.json')==c['canonical_design_sha256']
 return dict(source_commit=c['source_commit'],source_files=511,literal_links=4,canonical_design_sha256=c['canonical_design_sha256'],snapshot_sha256=c['snapshot_sha256'])
pre=sources();os.chdir(B);sys.path.insert(0,str(B))
from component_analysis import a3_direction_runtime as r
assert Path(r.__file__).resolve()==B/'component_analysis/a3_direction_runtime.py'
design=r.ladder.read_artifact(Path(c['canonical'])/'design.json');protocol=design['direction_protocol'];assert not design['injected'] and protocol['commit']==c['source_commit']
args=r.parser().parse_args(['--experiment','directions','--stage','prepare','--action','inventory','--inventory-stage','fit-select','--design',str(Path(c['canonical'])/'design.json'),'--commit',c['source_commit'],'--work-dir',c['canonical'],'--registry',str(Path(c['W'])/'docs/research/held_out.json')])
started=time.perf_counter();guard_before=r.live_guard(design,protocol,args);guard_before_seconds=time.perf_counter()-started
oracle=None;module=r.workload
if a.mode=='candidate':
 assert c['candidate_workload'] and c['candidate_workload_sha256'] and sha(c['candidate_workload'])==c['candidate_workload_sha256']
 assert c['complete_original_oracle'] and sha(c['complete_original_oracle'])==c['complete_original_oracle_sha256']
 oracle=json.loads(Path(c['complete_original_oracle']).read_text());assert oracle['complete'] is True and oracle['kind']=='option_A_complete_original_oracle' and oracle['source_commit']==c['source_commit'] and oracle['environment']==a.environment and oracle['input_design_sha256']==c['canonical_design_sha256']
 spec=importlib.util.spec_from_file_location('option_A_candidate_metadata_builder',c['candidate_workload']);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert a.mode!='original' or Path(module.__file__).resolve()==B/'component_analysis/a3_direction_workload.py'
write('BUILD_STARTED.json',dict(mode=a.mode,environment=a.environment,started_unix=time.time(),builder_path=str(Path(module.__file__).resolve()),builder_sha256=sha(module.__file__),input_design_sha256=c['canonical_design_sha256'],model_requested=False))
start=time.perf_counter();inv=module.build_inventory(design,protocol,stage='fit-select');build_seconds=time.perf_counter()-start
assert inv['stage']=='fit-select' and inv['injected'] is False and inv['identity']==r.workload.inventory_identity(design,protocol)
summary=dict(inventory_sha256=inv['inventory_sha256'],raw_keys=len(inv['expected_keys']),shards=len(inv['shards']),capture_shards=len(inv['capture_shards']),requirements=len(inv['requirements']),captures=len(inv['captures']),forward_counts=inv['forward_counts'],operation_counts=inv['operation_counts'],storage_requirements=inv['storage_requirements'])
assert summary['raw_keys']==246486 and summary['shards']==81904 and summary['capture_shards']==4256
write('BUILD_FINISHED_NOT_ORACLE.json',dict(complete=False,build_seconds=build_seconds,summary=summary,reason='Full publisher-format byte stream and postguards must still complete.'))
class Sink:
 def __init__(self):self.hash=hashlib.sha256();self.bytes=0
 def write(self,text):
  body=text.encode('utf-8');self.hash.update(body);self.bytes+=len(body);return len(text)
sink=Sink();write('STREAM_STARTED.json',dict(started_unix=time.time(),format='untouched json.dump(sort_keys=True,allow_nan=False) defaults plus LF'))
start=time.perf_counter();json.dump(inv,sink,sort_keys=True,allow_nan=False);sink.write('\n');stream_seconds=time.perf_counter()-start
write('STREAM_FINISHED_NOT_ORACLE.json',dict(complete=False,sha256=sink.hash.hexdigest(),bytes=sink.bytes,seconds=stream_seconds,postguards_still_required=True))
start=time.perf_counter();guard_after=r.live_guard(design,protocol,args);guard_after_seconds=time.perf_counter()-start
post=sources();assert pre==post
origins={n:str(Path(m.__file__).resolve()) for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','models','dataset','evaluation','scripts','config') and getattr(m,'__file__',None)};assert all(Path(path).is_relative_to(B) for path in origins.values())
if a.mode=='candidate':
 assert sha(c['candidate_workload'])==c['candidate_workload_sha256']
 assert summary==oracle['summary'] and sink.hash.hexdigest()==oracle['full_publisher_stream_sha256'] and sink.bytes==oracle['full_publisher_stream_bytes']
result=dict(kind='option_A_oracle_child_pending_supervisor',complete=False,mode=a.mode,environment=a.environment,source_commit=c['source_commit'] if a.mode=='original' else None,frozen_input_source_commit=c['source_commit'],unpublished_candidate_source_commit=None,input_design_sha256=c['canonical_design_sha256'],builder_path=str(Path(module.__file__).resolve()),builder_sha256=sha(module.__file__),summary=summary,full_publisher_stream_sha256=sink.hash.hexdigest(),full_publisher_stream_bytes=sink.bytes,build_seconds=build_seconds,stream_seconds=stream_seconds,guard_before_seconds=guard_before_seconds,guard_after_seconds=guard_after_seconds,source_before=pre,source_after=post,module_origins=origins,actual_CPU_job_id=os.environ['SLURM_JOB_ID'],python=sys.executable,python_version=sys.version,complete_original_reference=c['complete_original_oracle'] if a.mode=='candidate' else None,complete_original_reference_sha256=c['complete_original_oracle_sha256'] if a.mode=='candidate' else None,exact_comparison_passed=True if a.mode=='candidate' else None,model_loaded=False,GPU_admitted=False,algorithm_equivalence_only_not_production_lineage=True)
assert sha(P/'manifest.json')==a.packet_sha256
for name,digest in json.loads((P/'manifest.json').read_text()).items():assert sha(P/name)==digest,name
result['test_harness_manifest_sha256']=a.packet_sha256
write('RESULT.json',result)
