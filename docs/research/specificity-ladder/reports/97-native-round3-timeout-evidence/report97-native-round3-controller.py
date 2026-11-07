from pathlib import Path
import json,subprocess,time
root=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/unit-f-cpu-evidence/native-round3-b66c2d8')
driver='/tmp/report97-native-round3-phase.sh'
state=dict(kind='cpu_verification_orchestration',injected=True,execution_authorized=False,completed=[],stopped=False)
def save():
 (root/'controller-state.json').write_text(json.dumps(state,indent=2)+'\n')
def phase(name,start=0,count=32):
 print(json.dumps(dict(event='start',phase=name,start=start,count=count)),flush=True)
 began=time.perf_counter();result=subprocess.run(['bash',driver,str(root),name,str(start),str(count)])
 entry=dict(phase=name,start=start,count=count,exit_code=result.returncode,orchestration_wall_seconds=time.perf_counter()-began)
 if result.returncode:
  state.update(stopped=True,failed=entry);save();print(json.dumps(dict(event='failure',**entry)),flush=True);raise SystemExit(result.returncode)
 state['completed'].append(entry);save();print(json.dumps(dict(event='complete',**entry)),flush=True)
def count(stage,field):
 path=root/'inventory'/stage/'payload.json'
 return len(json.loads(path.read_text())[field])
# init and the first four genuine prefit cases already completed successfully.
for start in range(4,count('prefit','packing_invocations'),4):phase('prefit',start,4)
phase('prefit-aggregate')
phase('fit',0,4)
for start in range(4,count('fit-select','capture_shards'),4):phase('fit',start,4)
phase('validation',0,32)
validation_count=len(json.loads((root/'validation-inventory'/'payload.json').read_text())['shards'])
for start in range(32,validation_count,32):phase('validation',start,32)
phase('select')
selected_count=count('selected-pilot','packing_invocations');assert selected_count==63
for start in range(0,selected_count,4):phase('selected-pilot',start,4)
phase('selected-pilot-aggregate')
phase('calibration',0,32)
state.update(stopped=True,checkpoint='first calibration chunk complete; report startup/per-shard timing to root before later chunk sizing');save()
print(json.dumps(dict(event='calibration_checkpoint',selected_cases=63,initial_calibration_shards=32)),flush=True)
