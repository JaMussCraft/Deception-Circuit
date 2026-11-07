#!/usr/bin/env python3
"""Record actual membership and readable job-specific memory counters; no graph."""
import json,os,sys
from pathlib import Path
from guards import job_scoped

def controller_path(kind,membership,mountinfo,cgroup_root):
 path=Path(membership);assert path.is_absolute() and '..' not in path.parts
 if mountinfo is None:return cgroup_root/('memory' if kind=='v1' else '')/membership.lstrip('/')
 candidates=[]
 for line in mountinfo.splitlines():
  left,right=line.split(' - ',1);l=left.split();r=right.split()
  if not ((kind=='v2' and r[0]=='cgroup2') or (kind=='v1' and r[0]=='cgroup' and 'memory' in r[2].split(','))):continue
  root=Path(l[3]);mount=Path(l[4])
  try:relative=path.relative_to(root)
  except ValueError:continue
  candidates.append((len(root.parts),mount/relative))
 assert candidates,'actual cgroup memory mount unavailable'
 return max(candidates,key=lambda x:x[0])[1]

def collect(job,proc_text,cgroup_root=Path('/sys/fs/cgroup'),mountinfo=None):
 out={'job':job,'proc_self_cgroup':proc_text,'records':[]}
 for line in proc_text.splitlines():
  f=line.split(':',2)
  if len(f)!=3:raise ValueError('malformed cgroup membership')
  if f[0]=='0':kind='v2';base=controller_path(kind,f[2],mountinfo,cgroup_root);names=('memory.current','memory.peak','memory.events');kind='v2'
  elif 'memory' in f[1].split(','):kind='v1';base=controller_path(kind,f[2],mountinfo,cgroup_root);names=('memory.usage_in_bytes','memory.max_usage_in_bytes','memory.failcnt','memory.oom_control');kind='v1'
  else:continue
  worker_base=controller_path(kind,f[2],None,cgroup_root)
  try:same_path=base.samefile(worker_base)
  except OSError:same_path=False
  rec={'controller':kind,'path':str(base),'frozen_worker_path':str(worker_base),'same_as_frozen_worker_path':same_path,'membership':f[2],'job_scoped':job_scoped(job,f[2]),'values':{}}
  for n in names:
   p=base/n
   if p.is_file():rec['values'][n]=p.read_text()
  out['records'].append(rec)
 def required(r):
  keys=('memory.peak','memory.events') if r['controller']=='v2' else ('memory.max_usage_in_bytes','memory.failcnt','memory.oom_control')
  return r['job_scoped'] and r['same_as_frozen_worker_path'] and all(k in r['values'] for k in keys)
 out['required_194_counter_visible']=any(required(r) for r in out['records']);return out

def main():
 out=collect(os.environ.get('SLURM_JOB_ID',''),Path('/proc/self/cgroup').read_text(),mountinfo=Path('/proc/self/mountinfo').read_text());print(json.dumps(out,indent=2,allow_nan=False));return 0 if out['required_194_counter_visible'] else 2
if __name__=='__main__':sys.exit(main())
