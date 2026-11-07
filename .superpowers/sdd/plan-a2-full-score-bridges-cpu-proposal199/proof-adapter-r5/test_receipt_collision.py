import ast,json,tempfile,unittest
from pathlib import Path
import host_supervisor as host
import proof_guards as child_guards
P=Path(__file__).resolve().parent

def receipt_call(filename,owner):
 tree=ast.parse((P/filename).read_text())
 matches=[]
 for n in ast.walk(tree):
  if not isinstance(n,ast.Call) or len(n.args)!=2:continue
  if owner=='child':
   selected=isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='g' and n.func.attr=='write'
  else:
   selected=isinstance(n.func,ast.Name) and n.func.id=='write' and isinstance(n.args[1],ast.Call) and isinstance(n.args[1].func,ast.Name) and n.args[1].func.id=='source_before_activation'
  if selected and isinstance(n.args[0],ast.BinOp) and isinstance(n.args[0].right,(getattr(ast,'Constant',None) or ast.Str)) and str(n.args[0].right.value if hasattr(n.args[0].right,'value') else n.args[0].right.s).startswith('source-after'):matches.append(n)
 if len(matches)!=1:raise AssertionError((filename,len(matches)))
 return compile(ast.Expression(body=matches[0]),filename,'eval')

class Receipts(unittest.TestCase):
 def test_child_and_host_receipts_are_both_preserved(self):
  with tempfile.TemporaryDirectory() as td:
   out=Path(td);after={'layer':'child','source':'original'};host_value={'layer':'host','source':'activation'}
   eval(receipt_call('proof_worker.py','child'),{'g':child_guards,'out':out,'after':after})
   child=out/'source-after.json';before=child.read_bytes()
   eval(receipt_call('host_supervisor.py','host'),{'write':host.write,'out':out,'source_before_activation':lambda:host_value})
   self.assertEqual(child.read_bytes(),before);self.assertEqual(json.loads(child.read_text()),after)
   self.assertEqual(json.loads((out/'source-after-activation.json').read_text()),host_value)
if __name__=='__main__':unittest.main()
