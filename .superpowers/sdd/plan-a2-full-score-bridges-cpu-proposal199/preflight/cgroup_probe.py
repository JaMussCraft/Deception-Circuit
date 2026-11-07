#!/usr/bin/env python3
"""Record actual membership and readable job-specific memory counters; no graph."""
import json,os,sys
from pathlib import Path
job=os.environ.get('SLURM_JOB_ID','');out={'job':job,'proc_self_cgroup':Path('/proc/self/cgroup').read_text(),'records':[]}
for line in out['proc_self_cgroup'].splitlines():
 f=line.split(':',2)
 if f[0]=='0':base=Path('/sys/fs/cgroup')/f[2].lstrip('/');names=('memory.current','memory.peak','memory.events');kind='v2'
 elif 'memory' in f[1].split(','):base=Path('/sys/fs/cgroup/memory')/f[2].lstrip('/');names=('memory.usage_in_bytes','memory.max_usage_in_bytes','memory.failcnt','memory.oom_control');kind='v1'
 else:continue
 rec={'controller':kind,'path':str(base),'job_scoped':bool(job and job in str(base)),'values':{}}
 for n in names:
  p=base/n
  if p.is_file():rec['values'][n]=p.read_text()
 out['records'].append(rec)
required=lambda r:r['job_scoped'] and (all(k in r['values'] for k in ('memory.peak','memory.events')) if r['controller']=='v2' else all(k in r['values'] for k in ('memory.max_usage_in_bytes','memory.failcnt','memory.oom_control')))
out['required_194_counter_visible']=any(required(r) for r in out['records']);print(json.dumps(out,indent=2,allow_nan=False));sys.exit(0 if out['required_194_counter_visible'] else 2)
