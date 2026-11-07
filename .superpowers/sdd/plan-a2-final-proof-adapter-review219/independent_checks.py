"""Pure final-adapter review fixtures; no native context, worker main or remote I/O."""
import ast,copy,hashlib,importlib.util,json,os,runpy,sys,tempfile,types,unittest
from pathlib import Path
from unittest import mock
P=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/proof-adapter-r3');OLD=P.parent/'proof-adapter-r2';sys.path.insert(0,str(P));import proof_guards as g;import host_supervisor as h
SHA='4e4b4bcf1ddcd6481fac1eccd966a2a1cbfa385b2bd16a9a00504cfaa05def3f'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def functions(p):return {n.name:ast.dump(n) for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
def witness():
 data=json.loads((P/'transfer-attestation.template.json').read_text());data.update(complete=True,adapter_manifest_sha256=SHA,actual_job_id='123')
 for n,row in data['current_catalogues'].items():
  path=Path(n);row.update(bytes=path.stat().st_size,sha256=sha(path))
  for stage,at in [('delta_capture',1000),('remote',1001),('delta_reread',1002)]:row[stage].update(bytes=row['bytes'],sha256=row['sha256'],observed_unix=at)
 return data
class Review(unittest.TestCase):
 def test_exact_source_and_inherited_native_semantics(self):
  self.assertEqual(sha(P/'manifest.json'),SHA);m=json.loads((P/'manifest.json').read_text());self.assertEqual(len(m),31)
  for n,d in m.items():self.assertEqual(sha(P/n),d)
  for n in ('proof_worker.py','proof_schema.py','input-pins.json','native-schema-contract.json','request.json','data-files-from.txt'):self.assertEqual(sha(P/n),sha(OLD/n))
  for n in ('guards.py','cgroup_probe.py'):self.assertEqual(sha(P/n),sha(P.parent/'preflight-r5'/n))
  old,new=functions(OLD/'proof_guards.py'),functions(P/'proof_guards.py');self.assertEqual(old['owning'],new['owning']);self.assertEqual(old['packet'],new['packet'])
  old,new=functions(OLD/'host_supervisor.py'),functions(P/'host_supervisor.py')
  for n in ('validate_allocation','allocation','normal_child','observe_cgroup','select_cgroup','owned_output','source_before_activation'):self.assertEqual(old[n],new[n],n)
 def test_declared_transfer_identity_and_exact_catalogue_roles(self):
  old=json.loads((OLD/'transfer-closure.json').read_text());new=json.loads((P/'transfer-closure.json').read_text());a={v['virtual']:v for v in old['files']};b={v['virtual']:v for v in new['files']};self.assertEqual(set(a),set(b));self.assertEqual(len(b),1155)
  for n in a:
   for key in ('virtual','physical','sha256'):self.assertEqual(a[n][key],b[n][key])
   self.assertEqual(b[n]['role'],'historical_catalogue_provenance' if n in g.CATALOGUE_ROUTES else a[n]['role'])
  self.assertEqual(new['all_required_namespace_aliases'],old['all_required_namespace_aliases']);self.assertEqual(set(new['input_role_partition']['exact_live_virtual_paths']),g.CATALOGUE_ROUTES);self.assertEqual(new['input_role_partition']['immutable_original'],418)
  manifest=json.loads((P/'manifest.json').read_text());root=Path('/projects/beto/swong2/Alignment');self.assertEqual(set((P/'packet-files-from.txt').read_text().splitlines()),{str((P/n).relative_to(root)) for n in list(manifest)+['manifest.json']})
 def test_new_witness_rejects_nested_duplicates_and_parse_time_replacement(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'attestation.json';body=json.dumps(witness());p.write_text(body.replace('"observed_unix": 1000','"observed_unix": 1000, "observed_unix": 1000',1));ref=dict(path=str(p),sha256=sha(p))
   with self.assertRaises(AssertionError):g.catalogue_expectations(ref,SHA,'123')
   p.write_text(body);ref['sha256']=sha(p);original=g._unique_pairs;changed=[]
   def mutate(pairs):
    value=original(pairs)
    if not changed:p.write_text(body+' ');changed.append(True)
    return value
   with mock.patch.object(g,'_unique_pairs',mutate),self.assertRaises(AssertionError):g.catalogue_expectations(ref,SHA,'123')
 def test_combined_real_witness_barrier_before_entry_and_exec(self):
  for kind in ('valid-ro','valid-rw','missing-witness','wrong-job','changed-witness'):
   with self.subTest(kind=kind),tempfile.TemporaryDirectory() as td:
    out=Path(td);native=out/'native';native.mkdir();st=native.stat();record=dict(controller='v1',membership='/slurm/job_123/step_batch',path=str(native),frozen_worker_path=str(native),job_scoped=True,same_as_frozen_worker_path=True,live_directory_stat=[st.st_dev,st.st_ino,st.st_mode],values={'memory.max_usage_in_bytes':'0','memory.failcnt':'0','memory.oom_control':'0'});observation=dict(job='123',required_194_counter_visible=True,records=[record]);(out/'host-cgroup-before.json').write_text(json.dumps(observation))
    data=witness()
    if kind=='wrong-job':data['actual_job_id']='999'
    p=out/'attestation.json';p.write_text(json.dumps(data));env=dict(SLURM_JOB_ID='123',A2_CPU_PACKET_SHA256=SHA,A2_CPU_TRANSFER_ATTESTATION=str(p),A2_CPU_TRANSFER_ATTESTATION_SHA256=sha(p))
    if kind=='changed-witness':p.write_text(p.read_text()+' ')
    if kind=='missing-witness':env.pop('A2_CPU_TRANSFER_ATTESTATION')
    events=[];fakehost=types.SimpleNamespace(observe_cgroup=lambda:observation,select_cgroup=h.select_cgroup);argv=['entry_guard.py','--output',td,'--manifest-sha256',SHA,'--deadline-monotonic','999999999999']
    with mock.patch.dict(sys.modules,{'proof_guards':g,'host_supervisor':fakehost}),mock.patch.object(g,'packet',lambda _:None),mock.patch.dict(os.environ,env,clear=True),mock.patch.object(sys,'argv',argv),mock.patch.object(os,'statvfs',return_value=types.SimpleNamespace(f_flag=0 if kind=='valid-rw' else os.ST_RDONLY)),mock.patch.object(os,'execv',lambda *args:events.append('exec')):
     try:runpy.run_path(str(P/'entry_guard.py'),run_name='__review_fixture__')
     except (AssertionError,KeyError,OSError,AttributeError):pass
    self.assertEqual('exec' in events,kind=='valid-ro');self.assertEqual((out/'container-cgroup-entry.json').exists(),kind=='valid-ro')
    if kind!='valid-ro':self.assertTrue((out/'FAILED-container-entry.json').exists())
 def test_host_import_graph_python36_syntax(self):
  for n in ('host_supervisor.py','proof_guards.py','guards.py','cgroup_probe.py'):ast.parse((P/n).read_text(),feature_version=(3,6))
  # capture/owning are container-only and retain Python3.9+ APIs unchanged.
  for name in ('catalogue_expectations','_unique_pairs','_digest'):
   source=ast.get_source_segment((P/'proof_guards.py').read_text(),next(n for n in ast.parse((P/'proof_guards.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name))
   for banned in ('capture_output=','text=','fromisoformat(','.is_relative_to(','.removeprefix('):self.assertNotIn(banned,source)
if __name__=='__main__':unittest.main(verbosity=2)
