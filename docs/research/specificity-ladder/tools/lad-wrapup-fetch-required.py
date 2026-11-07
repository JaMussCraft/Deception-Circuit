from pathlib import Path
import os,json,subprocess,time
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');O=D/'docs/research/specificity-ladder/wrapup';v=json.loads((O/'remote-discovery.json').read_text());plans=json.loads((O/'fetch-plan.json').read_text());revised=[]
for i,p in enumerate(plans):
 root=p['remote_root'];paths=[]
 for q in v['output_roots']:
  try:rel=str(Path(q).relative_to(root))
  except ValueError:continue
  if not any(rel==old or rel.startswith(old+'/') for old in paths):paths.append(rel)
 if 'a2-assay' in root:paths+=['data','dataset']
 env=dict(os.environ,DC_DELTA_REPO_ROOT=str(D),DC_B2_PROFILE=p['profile']);args=['bash',str(D/'scripts/remote/b2.sh'),'fetch']+paths
 start=time.time()
 with(O/('fetch-required-'+str(i)+'.log')).open('w') as log:r=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT)
 row=dict(remote_root=root,paths=paths,returncode=r.returncode,elapsed_seconds=time.time()-start);revised.append(row);(O/'required-fetch-receipts.json').write_text(json.dumps(revised,indent=2)+'\n');assert r.returncode==0;print('Required roots collected',i,flush=True)
