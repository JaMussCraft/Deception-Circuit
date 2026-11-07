"""Small stdlib AST/source/failure-receipt checks; no native imports or graph."""
import ast,copy,hashlib,json,sys,unittest
from pathlib import Path
B=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199');P=B/'proof-adapter-r4';OLD=B/'proof-adapter-r3';sys.path.insert(0,str(P));import proof_schema as s
SHA='94a104fa5db26251b1f565baea61cf59b6e632ea453a0232ace01903ef8fecc0';OLD_SHA='4e4b4bcf1ddcd6481fac1eccd966a2a1cbfa385b2bd16a9a00504cfaa05def3f';R=P.parents[3]/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime/component_analysis'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def fns(p):return {n.name:ast.dump(n) for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
class Review(unittest.TestCase):
 def test_exact_source_inheritance_dispatch_and_host_reachability(self):
  self.assertEqual(sha(P/'manifest.json'),SHA);manifest=read(P/'manifest.json');self.assertEqual(len(manifest),32)
  for n,d in manifest.items():self.assertEqual(sha(P/n),d)
  for n in ('proof_worker.py','proof_guards.py','guards.py','cgroup_probe.py','entry_guard.py','input-pins.json','native-schema-contract.json','request.json','data-files-from.txt','test_catalogues.py','test_entry_readonly.py'):self.assertEqual(sha(P/n),sha(OLD/n),n)
  for n in ('host_supervisor.py','inner.sh','launch.sh','test_host.py'):self.assertEqual((P/n).read_text().replace('proof-adapter-r4','proof-adapter-r3'),(OLD/n).read_text(),n)
  old,new=fns(OLD/'proof_schema.py'),fns(P/'proof_schema.py');self.assertEqual(set(new)-set(old),{'normalize_empty_type_params'});self.assertEqual({n for n in old if old[n]!=new[n]},{'verify_function_pins'})
  dispatch=B/'root-proof-dispatch227/dispatch.sh';self.assertEqual(sha(dispatch),'da3fd6aac9356a685410afd3800c824988ac90c4e0a60dfcbe63707382f9cddb');self.assertEqual(dispatch.read_text().replace('proof-adapter-r4','proof-adapter-r3').replace(SHA,OLD_SHA),(B/'root-proof-dispatch220/dispatch.sh').read_text());self.assertEqual((B/'root-proof-dispatch227/test_dispatch.py').read_text().replace('proof-adapter-r4','proof-adapter-r3').replace(SHA,OLD_SHA),(B/'root-proof-dispatch220/test_dispatch.py').read_text())
  for n in ('host_supervisor.py','proof_guards.py','guards.py','cgroup_probe.py'):ast.parse((P/n).read_text(),feature_version=(3,6))
  self.assertNotIn('proof_schema',(P/'host_supervisor.py').read_text());self.assertNotIn('proof_schema',(P/'proof_guards.py').read_text())
 def test_independently_reproduces20_original_dumps_and_22_only_empty_insertions(self):
  contract=read(P/'native-schema-contract.json')['function_AST_sha256'];a=read(B/'proof-ast-diagnosis226/ast-py39.json');b=read(B/'proof-ast-diagnosis226/ast-py312.json');self.assertEqual(len(a['functions']),20);self.assertEqual(set(a['functions']),set(b['functions']));count=0;current=a if sys.version_info[:2]==(3,9) else b
  for file,names in contract.items():
   text=(R/file).read_text();self.assertEqual(sha(R/file),a['files'][file]['sha256']);self.assertEqual(a['files'][file],b['files'][file])
   for name,pin in names.items():
    key=file+':'+name;left=a['functions'][key];right=b['functions'][key];self.assertEqual(left['raw_sha256'],pin);self.assertNotEqual(right['raw_sha256'],pin);self.assertEqual(right['dump'].replace(', type_params=[]',''),left['dump']);count+=right['dump'].count(', type_params=[]');node=s.function(text,name);raw=ast.dump(node,include_attributes=False);self.assertEqual(raw,current['functions'][key]['dump']);normalized=ast.dump(s.normalize_empty_type_params(node),include_attributes=False);self.assertEqual(normalized,left['dump']);self.assertEqual(hashlib.sha256(normalized.encode()).hexdigest(),pin)
  self.assertEqual(count,22)
 def test_known_empty_only_while_unknown_semantic_fields_remain_hashed(self):
  node=ast.parse('def outer(x: int=3) -> int:\n async def inner():\n  return x\n class C:\n  pass\n return x+1\n').body[0];before=ast.dump(node,include_attributes=False).replace(', type_params=[]','');result=s.normalize_empty_type_params(copy.deepcopy(node));self.assertEqual(ast.dump(result,include_attributes=False),before)
  node=ast.parse('def f():\n return 1\n').body[0];node._fields=node._fields+('new_semantic_field',);node.new_semantic_field=ast.Constant(value=17);self.assertIn('new_semantic_field',ast.dump(s.normalize_empty_type_params(node),include_attributes=False))
  for owner in (ast.parse('x=1'),ast.parse('x=1').body[0]):
   owner._fields=owner._fields+('type_params',);owner.type_params=[]
   with self.assertRaises(ValueError):s.normalize_empty_type_params(owner)
 def test_failed_actual_run_receipt_is_not_resource_or_model_evidence(self):
  root=B/'root-genuine-proof-r3-ops';receipt=read(root/'fetch-50313499.json');self.assertEqual(len(receipt['files']),14)
  for n,v in receipt['files'].items():p=root/'actual-50313499'/n;self.assertEqual(sha(p),v['sha256']);self.assertEqual(p.stat().st_size,v['bytes'])
  self.assertIn('50313499|FAILED|1:0|00:07:31|',receipt['accounting']);failed=read(root/'actual-50313499/FAILED-child.json');self.assertIn('a2_pipeline.py:_groups_for_compute',failed['error']);self.assertIn('verify_function_pins',failed['traceback']);self.assertFalse(failed['complete']);self.assertFalse(failed['MODEL_LOADED']);self.assertFalse(failed['NUMERICAL_CONTROLS_TESTED']);self.assertFalse(failed['GPU_ADMITTED']);self.assertFalse((root/'actual-50313499/COMPLETE-PROOF.json').exists())
if __name__=='__main__':unittest.main(verbosity=2)
