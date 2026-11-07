#!/usr/bin/env python3
"""Inspect effective cgroup mounts before replacing self with unchanged pytest."""
import json,os,sys
from pathlib import Path

def mount_for(target,lines):
 matches=[]
 for line in lines:
  fields=line.split(); point=fields[4].replace('\\040',' '); options=fields[5].split(',')
  if target==point or target.startswith(point.rstrip('/')+'/'):matches.append((len(point),point,options))
 assert matches
 return max(matches)

def main():
 kind,out=sys.argv[1:3]; assert kind in ('v1','v2')
 lines=Path('/proc/self/mountinfo').read_text().splitlines()
 paths=['/sys/fs/cgroup']+(['/sys/fs/cgroup/memory'] if kind=='v1' else [])
 # Stat the declared readonly bind targets, not unrelated controllers.
 relevant=[line for line in lines if line.split()[4].replace('\\040',' ')==('/sys/fs/cgroup') or line.split()[4].replace('\\040',' ').startswith('/sys/fs/cgroup/')]
 targets=set(paths)
 flags={p:os.statvfs(p).f_flag for p in sorted(targets)}
 assert all(flag & os.ST_RDONLY for flag in flags.values()),flags
 with (Path(out)/'inner-mounts.json').open('x') as f:
  json.dump({'status':'DIAGNOSTIC_PARTIAL','mountinfo':relevant,'statvfs_flags':flags,'pid':os.getpid(),'argv':sys.argv[3:]},f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 os.execvpe(sys.argv[3],sys.argv[3:],os.environ)
if __name__=='__main__':main()
