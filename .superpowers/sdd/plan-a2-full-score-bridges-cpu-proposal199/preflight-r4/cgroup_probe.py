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
 out={'job':job,'memory_membership_lines':[],'memory_mount_lines':[],'records':[]}
 if mountinfo is not None:
  for line in mountinfo.splitlines():
   try:
    right=line.split(' - ',1)[1].split()
    if right[0]=='cgroup2' or (right[0]=='cgroup' and 'memory' in right[2].split(',')):out['memory_mount_lines'].append(line)
   except (IndexError,ValueError):continue
 for line in proc_text.splitlines():
  f=line.split(':',2)
  if len(f)!=3:continue
  if f[0]=='0':kind='v2';names=('memory.current','memory.peak','memory.events')
  elif 'memory' in f[1].split(','):kind='v1';names=('memory.usage_in_bytes','memory.max_usage_in_bytes','memory.failcnt','memory.oom_control')
  else:continue
  out['memory_membership_lines'].append(line)
  rec={'controller':kind,'membership':f[2],'job_scoped':job_scoped(job,f[2]),'values':{},'candidate_path_errors':{}}
  try:
   base=controller_path(kind,f[2],mountinfo,cgroup_root);rec['path']=str(base)
  except (AssertionError,ValueError,OSError) as e:
   rec['path_error']=str(e);base=None
  try:worker_base=controller_path(kind,f[2],None,cgroup_root);rec['frozen_worker_path']=str(worker_base)
  except (AssertionError,ValueError,OSError) as e:rec['worker_path_error']=str(e);worker_base=None
  try:rec['same_as_frozen_worker_path']=bool(base is not None and worker_base is not None and base.samefile(worker_base))
  except OSError as e:rec['same_as_frozen_worker_path']=False;rec['candidate_path_errors']['samefile']=str(e)
  for n in names:
   try:
    if base is not None:rec['values'][n]=(base/n).read_text()
   except OSError as e:rec['candidate_path_errors'][n]=str(e)
  out['records'].append(rec)
 def required(r):
  keys=('memory.peak','memory.events') if r['controller']=='v2' else ('memory.max_usage_in_bytes','memory.failcnt','memory.oom_control')
  return r['job_scoped'] and r.get('same_as_frozen_worker_path',False) and all(k in r['values'] for k in keys)
 out['required_194_counter_visible']=any(required(r) for r in out['records']);return out

def main():
 job=os.environ.get('SLURM_JOB_ID','');errors={}
 try:proc=Path('/proc/self/cgroup').read_text()
 except OSError as e:proc='';errors['membership']=str(e)
 try:mountinfo=Path('/proc/self/mountinfo').read_text()
 except OSError as e:mountinfo='';errors['mountinfo']=str(e)
 out=collect(job,proc,mountinfo=mountinfo);out['read_errors']=errors;print(json.dumps(out,indent=2,allow_nan=False));return 0 if out['required_194_counter_visible'] else 2
if __name__=='__main__':sys.exit(main())
