import ast,copy,json
from pathlib import Path
b=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd')
current=b/'plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py'
old=b/'plan/task23-green-r3-source-snapshot/component_analysis/a3_direction_runtime.py'
def require(ok,message):
 if not ok:raise ValueError(message)
env=dict(require=require)
t=ast.parse(current.read_text());helper=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_reconcile_prepared_observation_scopes')
exec(compile(ast.Module(body=[helper],type_ignores=[]),str(current),'exec'),env)
t=ast.parse(old.read_text());loader=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='load_prepared_pilot_target')
start=next(i for i,n in enumerate(loader.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='process')
oldcheck=compile(ast.Module(body=loader.body[start:start+4],type_ignores=[]),str(old),'exec')
scope='entire current cgroup, including other processes; lifetime peak';process_scope='process lifetime high-water RSS on Linux'
for measured,current_app in ((False,True),(True,False)):
 process=dict(process_peak_scope=process_scope,process_peak_rss_bytes=10,cgroup_scope=scope if current_app else None,cgroup_peak_bytes=10 if current_app else None)
 record=dict(process_peak_rss_bytes_bound=1000,cgroup_peak_bytes_bound=1000,measurement=dict(phases={
  label:dict(process={'scope':process_scope},cgroup=dict(applicable=measured,scope=scope if measured else 'not applicable')) for label in ('cold','warm')}))
 exec(oldcheck,dict(require=require,observed={'process_after':process},record=record))
 try:env['_reconcile_prepared_observation_scopes'](record,process)
 except ValueError:pass
 else:raise AssertionError('mismatch accepted')
# Comparable scopes accept different job path literals.
process=dict(process_peak_scope=process_scope,cgroup_scope=scope,cgroup_path='/current-job')
record=dict(measurement=dict(phases={label:dict(process={'scope':process_scope},cgroup=dict(applicable=True,scope=scope,path='/measurement-job')) for label in ('cold','warm')}))
env['_reconcile_prepared_observation_scopes'](record,process)
record['measurement']['phases']['warm']['cgroup'].update(applicable=False,scope='not applicable')
try:env['_reconcile_prepared_observation_scopes'](record,process)
except ValueError:pass
else:raise AssertionError('cold/warm disagreement accepted')
print(json.dumps(dict(status='PASS',r3_mismatch_directions_admitted=2,r4_mismatch_directions_rejected=2,
 equal_scope_different_job_paths_accepted=True,cold_warm_disagreement_rejected=True,model_loaded=False,scope='AST-extracted stdlib-only comparability probe')))
