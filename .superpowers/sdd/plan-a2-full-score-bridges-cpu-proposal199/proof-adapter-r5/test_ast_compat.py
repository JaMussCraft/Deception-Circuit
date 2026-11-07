import ast,copy,hashlib,json,sys,unittest
from pathlib import Path
import proof_schema as s
P=Path(__file__).resolve().parent
R=P.parents[3]/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime/component_analysis'
CONTRACT=json.loads((P/'native-schema-contract.json').read_text())['function_AST_sha256']
TEXTS={name:(R/name).read_text() for name in CONTRACT}

class AstCompat(unittest.TestCase):
 def test_all_20_frozen_functions(self):
  self.assertEqual(sum(len(x) for x in CONTRACT.values()),20)
  snapshot=json.loads((R.parent.parent/'snapshot.json').read_text())
  for name in CONTRACT:self.assertEqual(hashlib.sha256((R/name).read_bytes()).hexdigest(),snapshot['source_sha256']['component_analysis/'+name])
  s.verify_function_pins(TEXTS,CONTRACT)
 def test_semantic_body_mutation_rejected(self):
  texts=dict(TEXTS);old='def _groups_for_compute('
  self.assertEqual(texts['a2_pipeline.py'].count(old),1)
  text=texts['a2_pipeline.py'];i=text.index(old);line_end=text.index('\n',i)
  texts['a2_pipeline.py']=text[:line_end+1]+'    __proof_test_mutation = 1\n'+text[line_end+1:]
  with self.assertRaises(ValueError):s.verify_function_pins(texts,CONTRACT)
 def test_real_branch_mutation_rejected(self):
  texts=dict(TEXTS);old='        if key in seen:\n';self.assertEqual(texts['a2_pipeline.py'].count(old),1)
  texts['a2_pipeline.py']=texts['a2_pipeline.py'].replace(old,'        if key not in seen:\n',1)
  with self.assertRaises(ValueError):s.verify_function_pins(texts,CONTRACT)
 @unittest.skipUnless(sys.version_info >= (3,12),'generic syntax requires Python 3.12')
 def test_real_generic_function_rejected(self):
  node=ast.parse('def f[T](x: T):\n return x\n').body[0]
  with self.assertRaises(ValueError):s.normalize_empty_type_params(node)
 def test_reject_nonempty_type_params(self):
  node=ast.parse('def f():\n pass\n').body[0]
  node._fields=node._fields+(() if 'type_params' in node._fields else ('type_params',));node.type_params=[ast.Name(id='T',ctx=ast.Load())]
  with self.assertRaises(ValueError):s.normalize_empty_type_params(node)
 def test_reject_unexpected_representation(self):
  for value in (None,(),'',0):
   node=ast.parse('def f():\n pass\n').body[0];node._fields=node._fields+(() if 'type_params' in node._fields else ('type_params',));node.type_params=value
   with self.assertRaises(ValueError):s.normalize_empty_type_params(node)
  node=ast.parse('x=1');node.type_params=[]
  with self.assertRaises(ValueError):s.normalize_empty_type_params(node)
  node=ast.parse('x=1');node._fields=node._fields+('type_params',);node.type_params=[]
  with self.assertRaises(ValueError):s.normalize_empty_type_params(node)
 def test_preserves_other_ast_fields(self):
  node=ast.parse('@decorate\ndef f(x: int=3) -> int:\n return x+2\n').body[0];before=ast.dump(node,include_attributes=False)
  result=s.normalize_empty_type_params(copy.deepcopy(node));after=ast.dump(result,include_attributes=False)
  self.assertEqual(before.replace(', type_params=[]',''),after)
if __name__=='__main__':unittest.main()
