"""Diagnostic-only exact job identity and fresh output confinement."""
import os,re
from pathlib import Path

def job_scoped(job,membership):
 if not re.fullmatch(r'[0-9]+',job or ''):return False
 components=[p for p in Path(membership).parts if re.fullmatch(r'job_?[0-9]+',p)]
 return bool(components and all(p in ('job_'+job,'job'+job) for p in components))

def fresh_output(value,evidence_root,uid):
 assert isinstance(value,str) and value.startswith('/') and os.path.normpath(value)==value,'output not normalized absolute path'
 out=Path(value);root=Path(evidence_root);assert out==root/'execution','output differs from exact evidence namespace'
 assert root.is_dir() and root.stat().st_uid==uid,'evidence namespace must already exist and be owned by user'
 for path in [root]+list(root.parents):assert not path.is_symlink(),'symlink ancestor forbidden'
 assert root.resolve()==root and out.parent.resolve()==root,'output resolved outside evidence root'
 assert not os.path.lexists(str(out)),'occupied or dangling output forbidden'
 return out

def cgroup_bind(kind):
 if kind=='v1':path='/sys/fs/cgroup/memory'
 elif kind=='v2':path='/sys/fs/cgroup'
 else:raise ValueError('unsupported actual memory controller')
 return path+':'+path+':ro'
