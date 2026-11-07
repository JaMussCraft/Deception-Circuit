from pathlib import Path
import subprocess,json,time
P=Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder');O=P/'wrapup';deadline=json.loads((O/'closure-start.json').read_text())['pending_cancel_after_unix'];jobs=['23636235','23636244']
while jobs:
 for job in list(jobs):
  r=subprocess.run(['scontrol','show','job',job,'-o'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
  f=dict(x.split('=',1) for x in r.stdout.split() if '=' in x)
  if f.get('JobState')=='PENDING' and time.time()>=deadline:
   q=subprocess.run(['scancel',job],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)
   (O/('cancel-'+job+'.json')).write_text(json.dumps(dict(observed_before=f,deadline_unix=deadline,at_unix=time.time(),returncode=q.returncode,stdout=q.stdout,stderr=q.stderr),indent=2)+'\n');assert q.returncode==0
   print('Cancelled unstarted',job,flush=True);jobs.remove(job)
  elif f.get('JobState') not in ('PENDING','RUNNING','CONFIGURING','COMPLETING'):
   print('Terminal or no longer live',job,f.get('JobState'),flush=True);jobs.remove(job)
 if jobs:time.sleep(30)
