from pathlib import Path
import hashlib,json,time
s=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd')
p=s/'plan-a2-fresh-cpu-timing239-r2';d=p/'root-deployment261';e=d/'execution'
read=lambda path:json.loads(path.read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
start=time.monotonic()
assert sha(p/'manifest.json')=='c43d084973d38dbb2367b269879f23cc2d42383784f65d9abde937d4232573e6'
assert sha(d/'config.json')=='77457adc29fb92488a79c215e0a16c9755ff97c9dcca37dc71afb80cccc31ebc'
inv=read(d/'terminal-evidence285/root-terminal-inventory.json')
for row in inv['files']:
 path=Path(row['path']);assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256']
manifest=read(p/'manifest.json')
for name,h in manifest['files'].items():
 assert sha(Path(name))==h,name
 assert time.monotonic()-start<25
report=read(e/'DIAGNOSTIC-REPORT.json');witness=read(d/'current-catalogue-witness.json');summary=[]
assert report['actual_CPU_job_id']==witness['actual_job_id']==inv['job_id']=='23624978'
assert report['prime']['pid']!=report['fresh']['pid']
for phase in ('prime','fresh'):
 pipe=read(e/phase/'pipeline-observation.json');child=read(e/phase/'child-observation.json');r=report[phase]
 assert {k:v for k,v in r.items() if k!='wall_seconds_through_evidence'}==pipe
 assert child['pid']==r['pid'] and child['actual_CPU_job_id']=='23624978'
 assert r['exit_code']==0 and r['term_sent_at'] is None and r['finished_unix']<r['deadline_unix']
 assert child['finished_unix']<child['deadline_unix'] and child['source_before']==child['source_after']
 assert child['counts']['rows']==child['counts']['reconstructed_rows']==59652
 assert child['counts']['positive_controls']==child['counts']['reconstructed_controls']==3396
 assert child['native_observations']['model_loaded'] is False and child['native_observations']['GPU_admitted'] is False
 assert len(child['catalogue_capture_files'])==4
 for row in child['catalogue_capture_files']:
  path=Path(row['captured_bytes_path']);ref=witness['current_catalogues'][row['virtual_path']]
  assert path.stat().st_size==row['bytes']==ref['bytes']
  assert sha(path)==row['sha256']==ref['sha256']==child['source_before']['catalogues'][row['virtual_path']]
 runtime=read(d/'data-parameters.json')['accepted_runtime']
 assert all(Path(v).is_relative_to(runtime) for v in child['module_origins'].values())
 summary.append(dict(stage=phase,pid=r['pid'],child_wall=child['wall_seconds'],pipeline_wall=r['wall_seconds_through_evidence'],peak_RSS_bytes=child['peak_RSS_bytes'],rows=59652,controls=3396))
assert report['fresh']['wall_seconds_through_evidence']<240
assert report['orientation']['operational_feasible'] is None and report['operational_admission'] is False
assert abs(report['orientation']['local_component_headroom_seconds']-(300-report['fresh']['wall_seconds_through_evidence']-45))<1e-8
result=dict(status='ACCEPT_LOCAL_TIMING_FACTS_ONLY',sealed_files=len(inv['files']),manifest_files=len(manifest['files']),observations=summary,local_publication_seconds=report['local_publication_seconds'],orientation_headroom_seconds=report['orientation']['local_component_headroom_seconds'],elapsed_check_seconds=time.monotonic()-start)
Path(__file__).with_name('checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
