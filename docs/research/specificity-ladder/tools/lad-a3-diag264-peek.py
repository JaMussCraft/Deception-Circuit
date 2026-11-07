from pathlib import Path
import subprocess,json,shlex,time
O=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-deployment264')
code='''import json,subprocess,time
from pathlib import Path
root=Path('/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-transport254-r3/jobs/job-50318613')
out={'sacct':subprocess.check_output(['sacct','-j','50318613','-X','-n','-P','--format=JobID,State,Elapsed,ExitCode,NodeList'],universal_newlines=True),'observed_unix':time.time(),'files':{}}
for n in ['host-before.json','host-after.json','phase-0.json','phase-1.json','six-failure-traces/diagnostic-events/events.jsonl','six-failure-traces/pytest.stdout','six-failure-traces/pytest.stderr','six-failure-traces/fixture-preflight/stages.jsonl','six-failure-traces/fixture-preflight/run_manifest.json','next-122/diagnostic-events/events.jsonl','next-122/pytest.stdout','next-122/pytest.stderr']:
 p=root/n
 if p.is_file():
  b=p.read_bytes();out['files'][n]={'bytes':len(b),'text':b[-80000:].decode(errors='replace'),'tail_only':len(b)>80000}
out['phase_directory_entries']={name:[p.name for p in (root/name).iterdir()] for name in ['six-failure-traces','next-122'] if (root/name).is_dir()}
print(json.dumps(out))
'''
a=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)]
r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=25);r.check_returncode();x=json.loads(r.stdout);f=O/('progress-%d.json'%int(time.time()));f.write_text(json.dumps(x,indent=2)+'\n');print('saved',f);print(x['sacct']);print(x.get('phase_directory_entries'))
for n,v in x['files'].items():
 print(n,v['bytes'])
 if n.endswith('events.jsonl'):
  rows=[json.loads(z) for z in v['text'].splitlines() if z]
  print('completed call reports',[(e['nodeid'].split('::')[-1],e['outcome'],round(e['duration_seconds'],2)) for e in rows if e.get('when')=='call'])
  print('last event',rows[-1] if rows[-1].get('event')!='phase-report' else {k:rows[-1].get(k) for k in ['event','nodeid','when','outcome']})
 elif n.endswith('stages.jsonl'):
  rows=[json.loads(z) for z in v['text'].splitlines() if z];print('latest stage',{k:rows[-1].get(k) for k in ['active_case','event','stage','wall_seconds']})
 elif n.endswith('run_manifest.json'):
  r=json.loads(v['text']);print('preflight status',r.get('status'))
 elif n.endswith('stderr') or n in ['host-after.json','phase-0.json','phase-1.json']:print(v['text'][-3000:])
