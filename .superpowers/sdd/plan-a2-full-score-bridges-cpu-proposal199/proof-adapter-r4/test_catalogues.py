"""Pure catalogue-role contracts. No native imports, graph, model or remote I/O."""
import copy, hashlib, importlib.util, json, os, pathlib, tempfile, unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('catalogue_guard213',P/'proof_guards.py');g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)
sp=importlib.util.spec_from_file_location('catalogue_host213',P/'host_supervisor.py');h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h)
PACKET='a'*64;JOB='123';PHYS='/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment'
VIRT='/projects/beto/swong2/Alignment'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def witness():
 rows={}
 for p in g.REG:
  n=str(p);physical=PHYS+n[len(VIRT):];size=p.stat().st_size;digest=sha(p)
  def record(cluster,path,at):return dict(cluster=cluster,path=path,bytes=size,sha256=digest,observed_unix=at)
  rows[n]=dict(virtual=n,physical=physical,bytes=size,sha256=digest,delta_capture=record('delta',n,1000),remote=record('bridges2',physical,1001),delta_reread=record('delta',n,1002))
 return dict(complete=True,adapter_manifest_sha256=PACKET,actual_job_id=JOB,source_files=511,ordinary_inputs=422,immutable_original_inputs=418,current_catalogue_inputs=4,literal_source_links=4,catalogues_are_snapshots_not_continuous_Delta=True,current_catalogues=rows)
class CatalogueTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=pathlib.Path(self.tmp.name)
  for name in ('catalogue_expectations','verify_input_rows','current_catalogues'):
   self.assertTrue(callable(getattr(g,name,None)),'CATALOGUE_CORRECTION_MISSING: '+name)
 def save(self,value):
  p=self.root/'transfer.json';p.write_text(json.dumps(value));return dict(path=str(p),sha256=sha(p))
 def load(self,value):
  self.assertTrue(callable(getattr(g,'catalogue_expectations',None)),'CATALOGUE_CORRECTION_MISSING: authenticated expectations')
  return g.catalogue_expectations(self.save(value),PACKET,JOB)
 def inputs(self):
  rows={}
  for i in range(418):
   p=self.root/('input-%d'%i);p.write_bytes(b'original');rows[str(p)]=dict(path=str(p),bytes=8,sha256=sha(p))
  for p in g.REG:rows[str(p)]=dict(path=str(p),bytes=1,sha256='0'*64)
  return dict(ordinary_files=rows)
 def verify(self,inputs,expected):
  self.assertTrue(callable(getattr(g,'verify_input_rows',None)),'CATALOGUE_CORRECTION_MISSING: exact role split')
  return g.verify_input_rows(inputs,expected)
 def test_four_fresh_rows_replace_only_historical_byte_expectations(self):
  expected=self.load(witness());result=self.verify(self.inputs(),expected)
  self.assertEqual(result,dict(ordinary_count=422,immutable_original_count=418,current_catalogue_count=4))
 def test_actual_catalogue_conflict_is_resolved_by_bound_current_bytes(self):
  expected=self.load(witness());inputs=self.inputs();n=str(g.REG[1]);self.assertNotEqual(inputs['ordinary_files'][n]['sha256'],expected[n]['sha256']);self.verify(inputs,expected)
 def test_wrong_job_packet_flags_or_counts_reject(self):
  for key,value in [('actual_job_id','999'),('adapter_manifest_sha256','b'*64),('complete',False),('source_files',510),('ordinary_inputs',421),('immutable_original_inputs',417),('current_catalogue_inputs',5),('literal_source_links',3),('catalogues_are_snapshots_not_continuous_Delta',False)]:
   with self.subTest(key=key):
    data=witness();data[key]=value
    with self.assertRaises((AssertionError,ValueError)):self.load(data)
 def test_exact_four_lexical_paths_not_basename_or_prefix(self):
  for kind in ['missing','extra','renamed','resolved_alias']:
   with self.subTest(kind=kind):
    data=witness();rows=data['current_catalogues'];n=str(g.REG[0])
    if kind=='missing':del rows[n]
    elif kind=='extra':rows[n+'.extra']=copy.deepcopy(rows[n])
    else:rows[n.replace('/docs/research/','/elsewhere/')]=rows.pop(n)
    with self.assertRaises((AssertionError,ValueError)):self.load(data)
 def test_malformed_or_inconsistent_capture_records_reject(self):
  variants=[('bytes',True),('bytes',-1),('sha256','x'*64),('physical','/other'),('virtual','/other')]
  for key,value in variants:
   data=witness();next(iter(data['current_catalogues'].values()))[key]=value
   with self.subTest(key=key,value=value),self.assertRaises((AssertionError,ValueError)):self.load(data)
  for stage in ['delta_capture','remote','delta_reread']:
   for key,value in [('bytes',999),('sha256','b'*64),('cluster','wrong'),('path','/wrong'),('observed_unix',float('nan')),('observed_unix',True),('observed_unix',-1)]:
    data=witness();next(iter(data['current_catalogues'].values()))[stage][key]=value
    with self.subTest(stage=stage,key=key),self.assertRaises((AssertionError,ValueError)):self.load(data)
  data=witness();next(iter(data['current_catalogues'].values()))['remote']['observed_unix']=999
  with self.assertRaises((AssertionError,ValueError)):self.load(data)
 def test_pinned_same_buffer_and_duplicate_keys_reject(self):
  self.assertTrue(callable(getattr(g,'catalogue_expectations',None)),'CATALOGUE_CORRECTION_MISSING')
  ref=self.save(witness());path=pathlib.Path(ref['path']);path.write_text(path.read_text()+' ')
  with self.assertRaises((AssertionError,ValueError)):g.catalogue_expectations(ref,PACKET,JOB)
  path.write_text('{"complete":true,"complete":true}');ref['sha256']=sha(path)
  with self.assertRaises((AssertionError,ValueError)):g.catalogue_expectations(ref,PACKET,JOB)
  ref=self.save(witness());real_read=pathlib.Path.read_bytes
  def race(p):
   raw=real_read(p)
   if p==path:p.write_bytes(raw+b' ')
   return raw
  with mock.patch.object(pathlib.Path,'read_bytes',race),self.assertRaises((AssertionError,ValueError)):g.catalogue_expectations(ref,PACKET,JOB)
 def test_missing_witness_environment_never_adopts_current_hashes(self):
  self.assertTrue(callable(getattr(g,'current_catalogues',None)),'CATALOGUE_CORRECTION_MISSING: mandatory environment')
  with mock.patch.dict(os.environ,{},clear=True),self.assertRaises((AssertionError,ValueError,KeyError)):g.current_catalogues()
 def test_ordinary_mutation_and_same_basename_still_reject(self):
  expected=self.load(witness());inputs=self.inputs();old=next(iter(inputs['ordinary_files']));path=self.root/'directions.json';path.write_bytes(b'original');row=inputs['ordinary_files'].pop(old);row['path']=str(path);inputs['ordinary_files'][str(path)]=row
  self.verify(inputs,expected);path.write_bytes(b'mutated!')
  with self.assertRaises((AssertionError,ValueError)):self.verify(inputs,expected)
 def test_current_catalogue_mutation_rejects_without_hash_adoption(self):
  expected=self.load(witness());inputs=self.inputs();real_sha=g.sha;n=str(g.REG[0])
  with mock.patch.object(g,'sha',lambda p:'c'*64 if str(p)==n else real_sha(p)),self.assertRaises((AssertionError,ValueError)):self.verify(inputs,expected)
 def test_historical_rows_and_expected_map_unchanged(self):
  expected=self.load(witness());inputs=self.inputs();before=copy.deepcopy(inputs);saved=copy.deepcopy(expected);self.verify(inputs,expected);self.assertEqual(inputs,before);self.assertEqual(expected,saved)
 def test_host_forwards_pinned_transfer_reference_through_clean_environment(self):
  ref=self.save(witness())
  with mock.patch.dict(os.environ,{},clear=True):
   self.assertIn('catalogue_ref',h.container_command.__code__.co_varnames,'CATALOGUE_CORRECTION_MISSING: forwarding')
   cmd=h.container_command(h.PHYS/h.REL/'packet',h.PHYS/h.REL/'out',PACKET,123,dict(controller='v1'),catalogue_ref=ref)
  self.assertIn('A2_CPU_TRANSFER_ATTESTATION='+ref['path'],cmd);self.assertIn('A2_CPU_TRANSFER_ATTESTATION_SHA256='+ref['sha256'],cmd);self.assertIn('A2_CPU_PACKET_SHA256='+PACKET,cmd);self.assertIn('--cleanenv',cmd)
 def test_environment_witness_is_revalidated_on_every_capture_read(self):
  ref=self.save(witness());env=dict(SLURM_JOB_ID=JOB,A2_CPU_PACKET_SHA256=PACKET,A2_CPU_TRANSFER_ATTESTATION=ref['path'],A2_CPU_TRANSFER_ATTESTATION_SHA256=ref['sha256'])
  self.assertTrue(callable(getattr(g,'current_catalogues',None)),'CATALOGUE_CORRECTION_MISSING')
  with mock.patch.dict(os.environ,env,clear=True):
   self.assertEqual(set(g.current_catalogues()),set(str(p) for p in g.REG));pathlib.Path(ref['path']).write_text('{}')
   with self.assertRaises((AssertionError,ValueError)):g.current_catalogues()
 def test_real_capture_uses_witness_and_keeps_before_ready_after_identity(self):
  runtime=self.root/'runtime';runtime.mkdir();snapshot={}
  for i in range(511):
   p=runtime/('source%d'%i);p.write_bytes(b'x');snapshot[p.name]=sha(p)
  links={}
  for i in range(4):
   target=self.root/('target%d'%i);target.write_bytes(b'alias');p=runtime/('alias%d'%i);p.symlink_to(target);links[p.name]=str(target)
  (self.root/'snapshot.json').write_text(json.dumps(dict(source_commit='50e947bb852613e3a270082651f2bd1b7bb0c525',source_sha256=snapshot,input_links=links)))
  inputs=self.inputs();inputs['namespace_aliases']={str(runtime/n):t for n,t in links.items()};manifest=self.root/'inputs.json';manifest.write_text(json.dumps(inputs))
  historical=self.root/'historical';historical.mkdir();(historical/'config.json').write_text(json.dumps(dict(input_manifest=str(manifest),input_manifest_sha256=sha(manifest))))
  bank=self.root/'MAIN';(bank/'bank').mkdir(parents=True)
  for n in ['groups.json','bank/banks.json','bank/run_manifest.json']:(bank/n).write_bytes(b'preserved')
  ref=self.save(witness());env=dict(SLURM_JOB_ID=JOB,A2_CPU_PACKET_SHA256=PACKET,A2_CPU_TRANSFER_ATTESTATION=ref['path'],A2_CPU_TRANSFER_ATTESTATION_SHA256=ref['sha256'])
  with mock.patch.multiple(g,R=runtime,H=historical,G=bank),mock.patch.dict(os.environ,env,clear=True):
   before=g.capture();ready=g.capture();after=g.capture();self.assertEqual(before,ready);self.assertEqual(ready,after);self.assertEqual(before['input_roles'],dict(ordinary_count=422,immutable_original_count=418,current_catalogue_count=4));self.assertEqual(before['current_catalogue_witness_sha256'],ref['sha256'])
   real_sha=g.sha;n=str(g.REG[0])
   with mock.patch.object(g,'sha',lambda p:'c'*64 if str(p)==n else real_sha(p)),self.assertRaises((AssertionError,ValueError)):g.capture()
 def test_host_binding_authenticates_exact_witness_before_launch(self):
  def saved(name,value):
   p=self.root/name;p.write_text(json.dumps(value));return dict(path=str(p),sha256=sha(p))
  b=dict(status='ROOT_BOUND_FOR_ONE_CPU_PROOF',actual_job_id=JOB,adapter_manifest_sha256=PACKET,diagnostic_packet_manifest_sha256=h.PREFLIGHT_MANIFEST,independent_review_accepted=True,transfer_closure_verified=True,catalogues_are_snapshots_not_continuous_Delta=True,output_physical='/owned/output')
  b['probe_result']=saved('result',dict(complete=True,host_exit=0,container_exit=0,no_graph=True,no_model=True,proof_admitted=False))
  for key in ['probe_host','probe_container']:b[key]=saved(key,dict(required_194_counter_visible=True,job='probe-job'))
  b['probe_command']=saved('command',dict(argv=['/path/preflight-r5/inner.sh']));b['independent_review']=saved('review',dict(packet_manifest_sha256=PACKET,verdict='ACCEPT_FIXTURE'))
  b['transfer_attestation']=self.save(witness());ref=saved('binding',b)
  with mock.patch.dict(os.environ,dict(SLURM_JOB_ID=JOB),clear=True):
   self.assertEqual(h.load_bindings(ref['path'],ref['sha256']),b)
   invalid=witness();invalid['current_catalogues'].pop(str(g.REG[0]));b['transfer_attestation']=self.save(invalid);ref=saved('binding',b)
   with self.assertRaises((AssertionError,ValueError)):h.load_bindings(ref['path'],ref['sha256'])
 def test_successor_roles_and_wrappers_are_not_predecessor_routes(self):
  data=json.loads((P/'transfer-closure.json').read_text());roles=data.get('input_role_partition',{})
  self.assertEqual(roles.get('immutable_original'),418,'CATALOGUE_CORRECTION_MISSING: flattened roles')
  self.assertEqual(set(roles['exact_live_virtual_paths']),set(str(p) for p in g.REG))
  for row in data['files']:
   if row['virtual'] in roles['exact_live_virtual_paths']:self.assertEqual(row['role'],'historical_catalogue_provenance')
  for n in ['launch.sh','inner.sh']:
   self.assertIn('proof-adapter-r4', (P/n).read_text());self.assertNotIn('proof-adapter-r2', (P/n).read_text())
if __name__=='__main__':unittest.main(verbosity=2)
