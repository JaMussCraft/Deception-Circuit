from pathlib import Path
import json,subprocess,shlex
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');O=D/'docs/research/specificity-ladder/wrapup';v=json.loads((O/'remote-discovery.json').read_text())
code=r'''import os,json,shutil,time
from pathlib import Path
base=Path('/ocean/projects/cis260361p/swong2');archive=base/'_specificity-ladder-wrapup-20261107';archive.mkdir(exist_ok=True);rows=[]
def save(src,dst,kind):
 dst.parent.mkdir(parents=True,exist_ok=True)
 if src.is_symlink():
  if not dst.exists() and not dst.is_symlink():os.symlink(os.readlink(str(src)),str(dst))
  rows.append(dict(source=str(src),destination=str(dst.relative_to(archive)),kind='symlink',target=os.readlink(str(src))));return
 if not dst.exists():os.link(str(src),str(dst))
 rows.append(dict(source=str(src),destination=str(dst.relative_to(archive)),kind=kind,bytes=src.stat().st_size))
for name in LOGS:
 p=Path(name)
 if p.is_file() or p.is_symlink():save(p,archive/'logs/bridges2'/p.relative_to(base),'job_log')
for n in NAMES:
 ns=base/n;w=ns/'Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder'
 skips=[w/x for x in ('outputs','.superpowers/sdd','data','dataset')]
 for root,dirs,files in os.walk(str(ns),followlinks=False):
  rp=Path(root);dirs[:]=[d for d in dirs if d not in ('containers','hf','envs','.git','__pycache__','.cache') and rp/d not in skips]
  for d in list(dirs):
   p=rp/d
   if p.is_symlink():save(p,archive/'outputs/_analyses/specificity-ladder/bridges2-staging'/p.relative_to(base),'staging');dirs.remove(d)
  for f in files:
   if f=='token' or f.endswith('.lock'):continue
   p=rp/f;save(p,archive/'outputs/_analyses/specificity-ladder/bridges2-staging'/p.relative_to(base),'staging')
(archive/'manifest.json').write_text(json.dumps(dict(files=rows,observed_unix=time.time()),indent=2)+'\n')
print(json.dumps(dict(archive=str(archive),files=rows,observed_unix=time.time())))
'''.replace('LOGS',repr(v['logs'])).replace('NAMES',repr([x for x in v['top'] if x.startswith('specificity-ladder')]))
r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2','python3 -B -c '+shlex.quote(code)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=180)
(O/'remote-archive-manifest.json').write_text(r.stdout);(O/'remote-archive.stderr').write_text(r.stderr);assert r.returncode==0,r.stderr
x=json.loads(r.stdout);print(json.dumps(dict(archive=x['archive'],files=len(x['files']),bytes=sum(q.get('bytes',0) for q in x['files']))))
profile=O/'bridges-profile-archive.env';profile.write_text('source '+str(D/'scripts/cluster/bridges2.env')+'\nexport DC_REPO_ROOT='+x['archive']+'\n')
