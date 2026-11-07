from pathlib import Path
import json,hashlib,subprocess,shlex,time,sys
D=Path(__file__).resolve().parent;B=D/'root-Bridge-bindings';c=json.loads((B/'config.json').read_text());job=sys.argv[1];assert job.isdigit();E=Path(c['physical_evidence_parent'])/job;O=B/('job-'+job);O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
SSH=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ControlMaster=no','-o','ControlPath=none','-o','HostName=br013.bridges2.psc.edu','bridges2']
RS=['rsync','-rl','--no-perms','--no-times','-e','ssh -o BatchMode=yes -o ConnectTimeout=15 -o ControlMaster=no -o ControlPath=none','--']
def copy(a,b):subprocess.run(RS+[str(a),str(b)],check=True,timeout=45)
subprocess.run(RS+['b2dtn:'+str(E/n) for n in ['READY.json','allocation-before.json','actual-parameters.json']]+[str(O)+'/'],check=True,timeout=45)
r=json.loads((O/'READY.json').read_text());assert r['state']=='READY' and r['job_id']==job and r['phase']=='existing_G3_validation';assert 0<=time.time()-r['ready_unix']<250
expected={'source_commit':c['source_commit'],'config_sha256':sha(B/'config.json'),'packet_manifest_sha256':c['packet_manifest_sha256'],'proposal_sha256':c['proposal_sha256'],'groups_sha256':c['frozen_G3']['sha256'],'Delta_G3_proof_sha256':c['Delta_G3_proof']['sha256'],'catalogues':c['catalogues']}
for k,v in expected.items():assert r[k]==v,k
assert sha(O/'allocation-before.json')==r['allocation_sha256'] and sha(O/'actual-parameters.json')==r['parameters_sha256']
assert hashlib.sha256(json.dumps(c['namespace_aliases'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==r['namespace_aliases_sha256']
a=json.loads((O/'allocation-before.json').read_text());f=a['fields'];assert f['JobId']==job and f['JobState']=='RUNNING' and f['Account']=='cis260361p' and f['QOS']=='rm' and f['Partition']=='RM-shared' and f['NumCPUs']=='5';assert a['image_sha256']==c['image_sha256'];assert a['end_epoch']-time.time()>120
for row in r['catalogues']:assert sha(row['virtual_path'])==row['sha256']
remote_config=str(Path(c['validator_parameters']['path']).parent/'config.json')
script="import json,hashlib,subprocess\nfrom pathlib import Path\nc=json.loads(Path("+repr(remote_config)+").read_text());v=Path('/projects/beto/swong2/Alignment');p=Path(c['physical_Alignment']);rows=[]\nfor r in c['catalogues']:\n h=hashlib.sha256((p/Path(r['virtual_path']).relative_to(v)).read_bytes()).hexdigest();assert h==r['sha256'];rows.append(dict(virtual_path=r['virtual_path'],sha256=h))\nraw=subprocess.check_output(['scontrol','show','job',"+repr(job)+",'-o'],universal_newlines=True);assert 'JobState=RUNNING' in raw;print(json.dumps(dict(catalogues=rows,scontrol_job=raw)))\n"
x=subprocess.run(SSH+['python3 -'],input=script,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=40);assert x.returncode==0,x.stderr;remote=json.loads(x.stdout);(O/'remote-current-check.json').write_text(x.stdout+chr(10))
for row in r['catalogues']:assert sha(row['virtual_path'])==row['sha256']
proof={'kind':'root_actual_Delta_current_catalogue_recheck','source_commit':c['source_commit'],'job_id':job,'phase':r['phase'],'checked_unix':time.time(),'catalogues':r['catalogues'],'Delta_G3_preflight_job':'23483002','Delta_G3_proof_sha256':r['Delta_G3_proof_sha256'],'actual_Delta_before_and_after_remote_check':True,'remote_actual_check_sha256':sha(O/'remote-current-check.json'),'continuous_live_Delta':False,'model_admitted':False}
trace=D/'data-closure-supplement/result-23486081'
proof['latest_actual_Delta_owning_read_trace']={'job_id':'23486081','proof_sha256':sha(trace/'owning-proof.json'),'supplement_manifest_sha256':sha(trace/'supplement-manifest.json'),'supplement_count':24,'supplement_bytes':13555414,'unchanged_existing_inputs':True}
pf=O/'current-Delta-proof.json';pf.write_text(json.dumps(proof,indent=2)+chr(10));copy(pf,'b2dtn:'+str(E/'current-Delta-proof.json'))
for row in r['catalogues']:assert sha(row['virtual_path'])==row['sha256']
keys=['phase','job_id','source_commit','config_sha256','packet_manifest_sha256','proposal_sha256','groups_sha256','Delta_G3_proof_sha256','catalogues','allocation_sha256','parameters_sha256','namespace_aliases_sha256'];body={k:r[k] for k in keys};now=time.time();assert now-r['ready_unix']<285
body.update(Delta_current_catalogues_rechecked=True,Delta_current_catalogue_proof={'path':str(E/'current-Delta-proof.json'),'sha256':sha(pf)},issued_at=now,expires_at=now+300,model_admitted=False)
f=O/'root-release.json';f.write_text(json.dumps(body,indent=2)+chr(10));copy(f,'b2dtn:'+str(E/'root-release.json.pending'))
cmd='test ! -e '+shlex.quote(str(E/'root-release.json'))+' && mv '+shlex.quote(str(E/'root-release.json.pending'))+' '+shlex.quote(str(E/'root-release.json'))
x=subprocess.run(SSH+[cmd],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=40);assert x.returncode==0,x.stderr
(O/'publication.json').write_text(json.dumps({'job_id':job,'release_sha256':sha(f),'published_unix':time.time(),'phase':r['phase'],'model_admitted':False},indent=2)+chr(10));print('CPU_VALIDATION_RELEASE_PUBLISHED',job,sha(f),flush=True)
