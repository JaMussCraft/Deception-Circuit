"""Tiny reviewer fixtures only; no worker main, native context, model or remote calls."""
import ast,copy,hashlib,importlib,json,os,runpy,sys,tempfile,types,unittest
from pathlib import Path
from unittest import mock
P=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/proof-adapter-r2')
sys.path.insert(0,str(P));import host_supervisor as h
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
class IndependentTests(unittest.TestCase):
 def test_exact_manifest_and_inherited_files(self):
  self.assertEqual(sha(P/'manifest.json'),'0329fde965ddcc6d35c93f8da33187dbb44f25c17d00fbf97e6a024e26de5a85')
  for n,d in json.loads((P/'manifest.json').read_text()).items():self.assertEqual(sha(P/n),d)
  old=P.parents[1]/'plan-a2-full-score-resource-proof194-r2'
  for n in ('proof_worker.py','proof_schema.py','proof_guards.py','input-pins.json','native-schema-contract.json'):self.assertEqual(sha(P/n),sha(old/n))
  for n in ('cgroup_probe.py','guards.py'):self.assertEqual(sha(P/n),sha(P.parent/'preflight-r3'/n))
 def test_host_python36_syntax_and_apis(self):
  # Grammar/API scan only: a real Python3.6 runtime is not available locally.
  for n in ('host_supervisor.py','guards.py','cgroup_probe.py'):
   text=(P/n).read_text();ast.parse(text,feature_version=(3,6))
   for banned in ('capture_output=','text=','fromisoformat(','.is_relative_to(','.removeprefix('):self.assertNotIn(banned,text)
 def test_declared_fixed_input_closure(self):
  c=json.loads((P/'transfer-closure.json').read_text());routes={v['virtual']:v for v in c['files']};self.assertEqual(len(routes),1155)
  for key in ('base_inventory','historical_exact_role_proof'):self.assertEqual(sha(c[key]['path']),c[key]['sha256'])
  for n,d in json.loads((P/'input-pins.json').read_text()).items():self.assertIn(n,routes);self.assertEqual(routes[n]['sha256'],d)
  R=h.R;s=json.loads((R.parent/'snapshot.json').read_text())
  for n,d in s['source_sha256'].items():self.assertEqual(routes[str(R/n)]['sha256'],d)
  cfg=json.loads((h.VIRT/h.REL/'.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/root-H100-R5/job-50189932/config.json').read_text());inputs=json.loads(Path(cfg['input_manifest']).read_text())
  self.assertEqual(len(inputs['ordinary_files']),422)
  for n,v in inputs['ordinary_files'].items():self.assertEqual(routes[n]['sha256'],v['sha256'])
  aliases={v['virtual']:v['literal_target'] for v in c['all_required_namespace_aliases']}
  for n,t in inputs['namespace_aliases'].items():self.assertEqual(aliases[n],t)
  for n,t in s['input_links'].items():self.assertEqual(aliases[str(R/n)],t)
  self.assertEqual(set((P/'data-files-from.txt').read_text().splitlines()),{str(Path(n).relative_to(h.VIRT)) for n in routes})
  manifest=json.loads((P/'manifest.json').read_text());self.assertEqual(set((P/'packet-files-from.txt').read_text().splitlines()),{str((P/n).relative_to(h.VIRT)) for n in list(manifest)+['manifest.json']})
  self.assertEqual({v['virtual'] for v in c['fresh_catalogues']},{str(h.VIRT/'Deception-Circuit/docs/research'/n) for n in ('held_out.json','directions.json')}|{str(h.VIRT/h.REL/'docs/research'/n) for n in ('held_out.json','directions.json')})
 def test_cgroup_selection_requires_unique_actual_same_path(self):
  record=dict(controller='v1',job_scoped=True,same_as_frozen_worker_path=True,values={n:'0' for n in ('memory.max_usage_in_bytes','memory.failcnt','memory.oom_control')},live_directory_stat=[1,2,16877])
  value=dict(job='123',required_194_counter_visible=True,records=[record]);self.assertIs(h.select_cgroup(value,'123'),record)
  for bad in (dict(value,job='1234'),dict(value,required_194_counter_visible=False),dict(value,records=[record,record]),dict(value,records=[dict(record,same_as_frozen_worker_path=False)]),dict(value,records=[dict(record,values={})])):
   with self.assertRaises(AssertionError):h.select_cgroup(bad,'123')
 def test_bindings_reject_missing_failed_or_mismatched_prerequisites(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);documents={'probe_result':dict(complete=True,host_exit=0,container_exit=0,no_graph=True,no_model=True,proof_admitted=False),'probe_host':dict(required_194_counter_visible=True,job='99'),'probe_container':dict(required_194_counter_visible=True,job='99'),'probe_command':dict(argv=['/fixture/preflight-r3/inner.sh']),'independent_review':dict(packet_manifest_sha256='ADAPTER_FIXTURE',verdict='ACCEPT_FIXTURE'),'transfer_attestation':dict(adapter_manifest_sha256='ADAPTER_FIXTURE',complete=True,source_files=511,ordinary_inputs=422,literal_source_links=4)}
   b=dict(status='ROOT_BOUND_FOR_ONE_CPU_PROOF',actual_job_id='123',adapter_manifest_sha256='ADAPTER_FIXTURE',diagnostic_packet_manifest_sha256=h.PREFLIGHT_MANIFEST,independent_review_accepted=True,transfer_closure_verified=True,catalogues_are_snapshots_not_continuous_Delta=True,output_physical='/fixture/execution')
   def save():
    for k,v in documents.items():
     path=root/(k+'.json');path.write_text(json.dumps(v));b[k]=dict(path=str(path),sha256=sha(path))
    path=root/'binding.json';path.write_text(json.dumps(b));return path
   with mock.patch.dict(os.environ,{'SLURM_JOB_ID':'123'}):
    path=save();self.assertEqual(h.load_bindings(path,sha(path))['actual_job_id'],'123')
    variants=[('status','UNBOUND_NOT_EXECUTABLE'),('actual_job_id','124'),('diagnostic_packet_manifest_sha256','WRONG'),('independent_review_accepted',False),('transfer_closure_verified',False),('output_physical',None)]
    for key,value in variants:
     old=b[key];b[key]=value;path=save()
     with self.assertRaises((AssertionError,TypeError,KeyError)):h.load_bindings(path,sha(path))
     b[key]=old
    for key,field,value in [('probe_result','container_exit',1),('probe_result','proof_admitted',True),('probe_container','job','88'),('probe_host','required_194_counter_visible',False),('probe_command','argv',['/fixture/preflight-r2/inner.sh']),('independent_review','verdict','BLOCKED'),('independent_review','packet_manifest_sha256','OTHER'),('transfer_attestation','ordinary_inputs',421),('transfer_attestation','complete',False)]:
     old=documents[key][field];documents[key][field]=value;path=save()
     with self.assertRaises(AssertionError):h.load_bindings(path,sha(path))
     documents[key][field]=old
    path=save();b['probe_result']['sha256']='0'*64;path.write_text(json.dumps(b))
    with self.assertRaises(AssertionError):h.load_bindings(path,sha(path))
 def test_entry_requires_actual_membership_object_and_deadline(self):
  record=dict(controller='v1',job_scoped=True,same_as_frozen_worker_path=True,membership='/slurm/job_123/step_batch',values={n:'0' for n in ('memory.max_usage_in_bytes','memory.failcnt','memory.oom_control')},live_directory_stat=[1,2,16877])
  before=dict(job='123',required_194_counter_visible=True,records=[record]);events=[]
  class ExecReached(Exception):pass
  with tempfile.TemporaryDirectory() as td:
   out=Path(td);fake=types.ModuleType('proof_guards');fake.packet=lambda d:events.append('packet');fake.sha=lambda p:'4dfb62711dfe598041db9e836e8f1589dc05c54c3b649f007b625f8a1a34669e';fake.read=lambda p:before;fake.write=lambda p,v:events.append((Path(p).name,v))
   def execute(*a):events.append('exec');raise ExecReached()
   for mutation in ('none','membership','inode','controller','deadline'):
    events.clear();actual=copy.deepcopy(before)
    if mutation=='membership':actual['records'][0]['membership']='/slurm/job_123/step_other'
    if mutation=='inode':actual['records'][0]['live_directory_stat']=[1,99,16877]
    if mutation=='controller':actual['records'][0]['controller']='v2';actual['records'][0]['values']={'memory.peak':'0','memory.events':'oom 0'}
    with mock.patch.dict(sys.modules,{'proof_guards':fake}),mock.patch.object(h,'observe_cgroup',lambda:actual),mock.patch.object(os,'execv',execute),mock.patch.dict(os.environ,{'SLURM_JOB_ID':'123'}),mock.patch.object(sys,'argv',['entry_guard.py','--output',td,'--manifest-sha256','FIXTURE','--deadline-monotonic','0' if mutation=='deadline' else '999999999999']):
     with self.assertRaises(ExecReached if mutation=='none' else AssertionError):runpy.run_path(str(P/'entry_guard.py'),run_name='__review_fixture__')
    self.assertEqual('exec' in events,mutation=='none')
if __name__=='__main__':unittest.main(verbosity=2)
