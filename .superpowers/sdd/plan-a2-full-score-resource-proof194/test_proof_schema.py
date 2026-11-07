import ast,copy,hashlib,importlib.util,json,math,pathlib,tempfile,types,unittest
P=pathlib.Path(__file__).resolve().parent
S=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime/component_analysis')
spec=importlib.util.spec_from_file_location('proof_schema',P/'proof_schema.py');core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
class SchemaTests(unittest.TestCase):
 def test_native_added_field_must_not_escape_bound(self):
  source=(S/'specificity_ladder.py').read_text(); changed=source.replace('record=dict(task=batch.task','record=dict(unmodelled_field="UNCOSTED",task=batch.task',1)
  self.assertNotEqual(source,changed)
  with self.assertRaises(ValueError):core.verify_runner_schema(changed)
 def test_alias_shallow_copy_mutation_must_fail(self):
  source=(S/'a2_pipeline.py').read_text();changed=source.replace('copy.deepcopy(group["members"])','group["members"]',1)
  self.assertNotEqual(source,changed)
  with self.assertRaises(ValueError):core.verify_append_schema(changed)
 def test_exact_record_alias_and_unknown_metric_labels(self):
  row={'task':'ioi','instance_id':'id','condition':'IOI','stream':'clean','records':[{'pressure_id':'p','streams':{'clean':{'tokens':[1,2]}}}], 'expected_token':1,'opposite_token':2,'honest_token':1}
  members=[['head',0,0]];group={'members':members,'membership_sha256':'a'*64,'training_seed':42,'task':'far_v2'}
  source={'pressure_id':'p','streams':{'clean':{'tokens':[1,2]}}}
  r=core.bound_row(row,source,None,'zero','alias',group,'compute','b'*64,None,False)
  self.assertIs(r['source_provenance'],source);self.assertIsNot(r['group_members'],members)
  members[0][1]=9;self.assertEqual(r['group_members'][0][1],0)
  core.validate_row_fields(r,False)
  del r['source_provenance']
  with self.assertRaises(ValueError):core.validate_row_fields(r,False)
 def test_control_sender_drop_is_rejected(self):
  row={'task':'ioi','instance_id':'x','stream':'clean','condition':'IOI'};keys=[('embed',0,0),('head',0,0),('mlp',0,0)]
  c=core.bound_control(row,{'supported':True},keys,'far_v2');core.validate_control(c,keys)
  c['sender_keys'].pop()
  with self.assertRaises(ValueError):core.validate_control(c,keys)
 def test_float_slot_and_exact_encoder(self):
  vals=[-1.7976931348623157e308,1.7976931348623157e308,-2.2250738585072014e-308,5e-324,-0.0,1.2345678901234567e-200]
  self.assertTrue(all(len(json.dumps(v,allow_nan=False))<=24 for v in vals));self.assertGreaterEqual(len(json.dumps(core.FLOAT_SLOT)),24)
  for ensure in (True,False):
   value={'unicode':'é😀\n\t\x00','x':vals,'tuple':(1,False,None)}
   self.assertEqual(core.json_size(value,ensure_ascii=ensure),len(json.dumps(value,sort_keys=True,allow_nan=False,ensure_ascii=ensure).encode()))
 def test_no_sharing_bound_and_cycles(self):
  shared=['x'*50];graph=[shared,shared]
  u,n=core.graph_sizes(graph);self.assertGreaterEqual(n,u)
  graph.append(graph)
  with self.assertRaises(ValueError):core.graph_sizes(graph)
 def test_native_stats_fixture_has_exact_metric_slots(self):
  import torch
  tree=ast.parse((S/'specificity_ladder.py').read_text());node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_stats');ns={'torch':torch};exec(compile(ast.Module(body=[node],type_ignores=[]),'<frozen-stats-fixture>','exec'),ns)
  for choice in (None,torch.tensor([[1,2,3,4]])):
   b=types.SimpleNamespace(ids=['SYNTHETIC'],opposite_token=torch.tensor([2]),honest_token=torch.tensor([1]),expected_token=torch.tensor([2]),choice_tokens=choice)
   out=ns['_stats'](b,torch.arange(8,dtype=torch.float32)[None,:],torch.arange(8,dtype=torch.float32)[None,:]);self.assertEqual(set(out),set(core.metric_types(choice is not None)))
   for k,kind in core.metric_types(choice is not None).items():self.assertIs(type(out[k][0].item()),{'float':float,'int':int,'bool':bool}[kind])
 def test_supported_choice_and_unsupported_schema(self):
  row={'task':'mmlu','instance_id':'r','condition':'MMLU','stream':'clean','expected_token':128255,'opposite_token':0,'honest_token':128255};source={'streams':{'clean':{'tokens':[128255]}}};group={'members':[['mlp',0,0]],'membership_sha256':'a'*64,'training_seed':1,'task':'far_v2'}
  mapping={'supported':False,'unsupported_reason':'real frozen layout reason','seed':None}
  r=core.bound_row(row,source,mapping,'h_twin','x',group,'c','b'*64,None,True)
  self.assertEqual(r['unsupported_reason'],mapping['unsupported_reason']);self.assertNotIn('patched_choice_margin',r);self.assertFalse(r['supported'])
  ref={'artifact_reference':'/PINNED','sha256':'c'*64};r=core.bound_row(row,source,None,'h_mean','x',group,'c','b'*64,ref,True)
  self.assertEqual(r['patched_choice_margin'],core.FLOAT_SLOT);self.assertIsNot(r['mean_bank_provenance'],ref);self.assertIsNone(r['donor_provenance']);self.assertEqual(r['assay_valid'],core.BOOL_SLOT)
 def test_native_hash_and_artifact_encoding_exact(self):
  design={};tree=ast.parse((S/'ladder_design.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_hash');exec(compile(ast.Module(body=[node],type_ignores=[]),'<native-hash-fixture>','exec'),{'json':json,'hashlib':hashlib},design)
  ns={'json':json,'Path':pathlib.Path,'require':lambda ok,msg:None if ok else (_ for _ in ()).throw(ValueError(msg)),'design':types.SimpleNamespace(_hash=design['_hash'])};tree=ast.parse((S/'ladder_pipeline.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='write_artifact');exec(compile(ast.Module(body=[node],type_ignores=[]),'<native-writer-fixture>','exec'),ns)
  value={'kind':'SYNTHETIC_ONLY','unicode':'é😀\n\x00','float_slot':core.FLOAT_SLOT,'bool_slot':core.BOOL_SLOT,'nested':[[1,False,None]]}
  with tempfile.TemporaryDirectory() as d:
   path=pathlib.Path(d)/'NOT_A_SCORE.fixture';ns['write_artifact'](path,value);raw=path.read_bytes();self.assertEqual(raw,(json.dumps({'sha256':design['_hash'](value),'payload':value},sort_keys=True,allow_nan=False)+'\n').encode());self.assertEqual(len(raw),core.json_size(value)+len(json.dumps({'sha256':'0'*64,'payload':None},sort_keys=True).encode())-4+1)
 def test_wrapper_uses_absolute_packet_not_spool(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'fakepython';p.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n');p.chmod(0o700)
   import subprocess,os
   r=subprocess.run(['bash',str(P/'run.sh'),'OUT','SHA'],cwd=d,env=dict(os.environ,SLURM_JOB_ID='1',PROOF194_PYTHON=str(p),PROOF194_WRAPPER_TEST='1',SLURM_CLUSTER_NAME=''),stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertIn(str(P/'supervisor.py'),r.stdout)
if __name__=='__main__':unittest.main(verbosity=2)
