from pathlib import Path
import json,os,subprocess,time
D=Path('/projects/beto/swong2/Alignment/Deception-Circuit');O=D/'docs/research/specificity-ladder/wrapup';v=json.loads((O/'remote-discovery.json').read_text());base=v['base'];suffix='/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder'
roots=[base+'/'+n+suffix for n in v['top'] if n.startswith('specificity-ladder')]
plans=[]
for i,root in enumerate(roots):
 profile=O/('bridges-profile-'+str(i)+'.env');profile.write_text('source '+str(D/'scripts/cluster/bridges2.env')+'\nexport DC_REPO_ROOT='+root+'\n')
 paths=['outputs/_analyses/specificity-ladder']
 if 'a2-assay' in root:paths+=['.superpowers/sdd','data','dataset']
 if 'a3-producer' in root:paths+=['.superpowers/sdd']
 plans.append(dict(remote_root=root,profile=str(profile),paths=paths))
(O/'fetch-plan.json').write_text(json.dumps(plans,indent=2)+'\n')
for i,item in enumerate(plans):
 env=dict(os.environ,DC_DELTA_REPO_ROOT=str(D),DC_B2_PROFILE=item['profile'])
 args=['bash',str(D/'scripts/remote/b2.sh'),'fetch']+item['paths']
 start=time.time()
 with(O/('fetch-'+str(i)+'.log')).open('w') as log:r=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT)
 (O/('fetch-'+str(i)+'-receipt.json')).write_text(json.dumps(dict(argv=args,remote_root=item['remote_root'],returncode=r.returncode,elapsed_seconds=time.time()-start),indent=2)+'\n')
 print('Fetched',item['remote_root'],'wrapper exit',r.returncode,flush=True)
 assert r.returncode==0
