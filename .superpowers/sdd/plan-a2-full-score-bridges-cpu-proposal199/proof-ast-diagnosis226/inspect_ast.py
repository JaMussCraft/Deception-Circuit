import ast,copy,hashlib,json,sys
from pathlib import Path
B=Path(__file__).resolve().parent.parent
R=B.parent.parent.parent.parent.parent / 'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime'
# Pass the absolute runtime explicitly to avoid deriving it from the packet location.
R=Path(sys.argv[1]);out=Path(sys.argv[2]); contract=json.loads((B/'proof-adapter-r3/native-schema-contract.json').read_text())['function_AST_sha256'];snapshot=json.loads((R.parent/'snapshot.json').read_text());report={'version':sys.version,'source_commit':snapshot['source_commit'],'files':{},'functions':{}}
for file, funcs in contract.items():
 p=R/'component_analysis'/file;raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest();expected=snapshot['source_sha256']['component_analysis/'+file];assert sha==expected
 report['files'][file]={'sha256':sha,'bytes':len(raw),'snapshot_match':True};tree=ast.parse(raw.decode());top={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
 for name,pin in funcs.items():
  node=top[name];dump=ast.dump(node,include_attributes=False);flat=copy.deepcopy(node);params=[]
  for n in ast.walk(flat):
   if hasattr(n,'type_params'):
    params.append(len(n.type_params));del n.type_params
  norm=ast.dump(flat,include_attributes=False)
  report['functions'][file+':'+name]={'pin':pin,'raw_sha256':hashlib.sha256(dump.encode()).hexdigest(),'normalized_sha256':hashlib.sha256(norm.encode()).hexdigest(),'type_params_lengths':params,'dump':dump,'normalized_dump':norm}
out.write_text(json.dumps(report,indent=2)+'\n')
