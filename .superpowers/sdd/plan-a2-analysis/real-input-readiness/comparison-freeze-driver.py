from pathlib import Path
import os,sys,json,hashlib,time,subprocess
D=Path(__file__).parent;B=json.loads((D/'source-binding.json').read_text());R=Path(B['analysis_runtime']);C=B['analysis_execution_commit'];O=Path(B['fresh_output_dir']);started=time.time();created=False
assert os.environ.get('SLURM_JOB_ID'),'root must submit this substantial step as Slurm CPU'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def publish(path,value):
 with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def source_check():
 assert sha(B['analysis_snapshot'])==B['analysis_snapshot_sha256'];s=json.loads(Path(B['analysis_snapshot']).read_text());assert s['source_commit']==C
 for name,value in s['source_sha256'].items():
  p=R/name;assert p.is_file() and not p.is_symlink() and p.stat().st_mode&0o222==0 and sha(p)==value,name
 for name,target in s['input_links'].items():assert (R/name).is_symlink() and (R/name).resolve()==Path(target).resolve()
 for name,value in B['used_source_sha256'].items():assert sha(R/name)==value
try:
 r=subprocess.run(['scontrol','show','job',os.environ['SLURM_JOB_ID'],'-o'],check=True,capture_output=True,text=True);fields=dict(x.split('=',1) for x in r.stdout.split() if '=' in x);assert fields['JobState']=='RUNNING' and fields['Account']=='beto-delta-cpu' and fields['Partition'].startswith('cpu') and 'gres/gpu' not in fields.get('AllocTRES','');source_check()
 assert sha(D/'source-records.json')==B['source_records_sha256'];assert not O.exists() and not O.is_symlink();O.mkdir(parents=True,exist_ok=False);created=True;publish(O/'allocation.json',{'job_id':os.environ['SLURM_JOB_ID'],'node':os.uname().nodename,'scontrol':r.stdout,'gpus':0})
 for path,value in B['input_static_metadata_sha256'].items():assert sha(path)==value
 for path,value in B['migration_appendix_references'].items():assert sha(path)==value
 cfg=B['model_config_metadata'];assert sha(cfg['reference_path'])==cfg['reference_sha256'] and Path(cfg['config_path']).stat().st_size==cfg['bytes'] and sha(cfg['config_path'])==cfg['file_sha256']
 with (O/'source-records.json').open('xb') as stream:stream.write((D/'source-records.json').read_bytes())
 os.chdir(R);sys.path.insert(0,str(R))
 from component_analysis import a2_mask_comparison as comparison
 records=comparison._read(O/'source-records.json')['records'];assert len(records)==18
 comp=comparison.compare_masks(records);assert comp['status']=='complete_cpu_audit' and len(comp['sources'])==18
 reference=comparison.write_comparison(comp,O/'comparison.json')
 command=['bash',str(R/'scripts/jobs/specificity_a2.sh'),'--stage','freeze','--design',B['a1_design'],'--selected',B['a1_selected'],'--work-dir',str(O),'--commit',C,'--comparison',str(O/'comparison.json'),'--source-records',str(O/'source-records.json'),'--registry','/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/held_out.json']
 with (O/'freeze.stdout').open('x') as stdout,(O/'freeze.stderr').open('x') as stderr:result=subprocess.run(command,cwd=R,env=os.environ.copy(),stdout=stdout,stderr=stderr)
 publish(O/'freeze-command.json',{'command':command,'cwd':str(R),'exit_code':result.returncode});assert result.returncode==0
 from component_analysis import a2_pipeline as pipeline,ladder_pipeline as a1
 receipt=a1.read_artifact(O/'groups.json');pipeline.validate_receipt(receipt);assert len(receipt['groups'])==9 and not receipt['injected'] and receipt['execution_commit']==C and receipt['a1_ancestor_commit']==B['a1_ancestor_commit'];assert receipt['comparison_sha256']==comp['comparison_sha256'] and receipt['operations']==list(pipeline.PRIMARY_OPERATIONS) and receipt['independent_donor_seeds']==[]
 assert receipt['model_geometry']['source']['file_sha256']==cfg['file_sha256'] and receipt['model_geometry']['source']['model_revision']==cfg['revision']
 assert all(sha(ref['path'])==ref['file_sha256'] for ref in receipt['file_references'].values());source_check()
 modules={n:m.__file__ for n,m in sys.modules.items() if n.split('.')[0] in ('component_analysis','dataset','scripts','evaluation','models') and getattr(m,'__file__',None)};assert all(Path(p).resolve().is_relative_to(R) for p in modules.values())
 publish(O/'COMPLETE.json',{'kind':'CPU_all18_comparison_and_prospective_groups_only','source_commit':C,'source_binding_sha256':sha(D/'source-binding.json'),'job_id':os.environ['SLURM_JOB_ID'],'elapsed_seconds':time.time()-started,'comparison_reference':reference,'groups_file_sha256':sha(O/'groups.json'),'group_receipt_sha256':receipt['receipt_sha256'],'source_records_sha256':sha(O/'source-records.json'),'source_count':18,'group_aliases':9,'project_imports':modules,'migration_appendix_references':B['migration_appendix_references'],'pretrained_weights_loaded':False,'assay_outcomes_scored':False,'execution_admitted':False})
 print('COMPLETE_CPU_COMPARISON_AND_PROSPECTIVE_FREEZE_ONLY',flush=True)
except BaseException as error:
 if created and not (O/'FAILED.json').exists():publish(O/'FAILED.json',{'error':repr(error),'elapsed_seconds':time.time()-started,'partial_artifacts_preserved':True,'automatic_retry':False})
 raise
