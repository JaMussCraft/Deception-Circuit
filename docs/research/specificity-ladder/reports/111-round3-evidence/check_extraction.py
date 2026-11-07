import ast,copy,hashlib,json
from pathlib import Path
base=Path('.superpowers/sdd/plan-a3/unit-f-review111-round2-source')
def functions(path):return {n.name:n for n in ast.parse(path.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
old=functions(base/'component_analysis/a3_direction_runtime.py')
new=functions(Path('component_analysis/a3_direction_runtime.py'))
old_fn=copy.deepcopy(old['_completed_pilot_index']);new_fn=new['_completed_pilot_index']
position=next(i for i,n in enumerate(old_fn.body) if isinstance(n,ast.For) and isinstance(n.target,ast.Tuple) and [x.id for x in n.target.elts]==['receipt','path'])
loop=old_fn.body[position]
new_loop=next(n for n in new['_validate_completed_pilot_footprints'].body if isinstance(n,ast.For))
assert ast.dump(loop,include_attributes=False)==ast.dump(new_loop,include_attributes=False)
call=next(n for n in new_fn.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='_validate_completed_pilot_footprints')
old_fn.body[position]=copy.deepcopy(call)
assert ast.dump(old_fn,include_attributes=False)==ast.dump(new_fn,include_attributes=False)
old_tests=functions(base/'tests/test_a3_direction_runtime.py');new_tests=functions(Path('tests/test_a3_direction_runtime.py'))
name='test_completed_index_startup_is_measured_conditionally_and_charged_per_job'
assert ast.dump(old_tests[name],include_attributes=False)==ast.dump(new_tests[name],include_attributes=False)
manifest=json.loads(Path('.superpowers/sdd/plan-a3/unit-f-review111-round3.sha256.json').read_text())
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in manifest.items())
print(json.dumps(dict(footprint_loop_AST_identical=True,actual_constructor_AST_identical_after_extraction=True,accepted_startup_test_AST_identical=True,source_files=len(manifest),all_source_hashes_match=True),indent=2))
