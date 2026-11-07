from pathlib import Path
import csv,hashlib,io,json,os,shutil,subprocess,sys
number,job,start,count,chunk=sys.argv[1:];start,count=int(start),int(count)
assert (number,job,start,count,chunk) in [('140','23470779',32,17,'32-48'),('141','23470886',49,14,'49-62')]
w=Path.cwd();primary=Path('/projects/beto/swong2/Alignment/Deception-Circuit');rel=Path('docs/research/specificity-ladder/reports');slug=f'{number}-native-cpu-job{job}';e=w/rel/(slug+'-evidence');e.mkdir(exist_ok=False)
p=w/f'.superpowers/sdd/plan-a3/native-continuation-plan/next-chunk-cpu{chunk}-proposal';d=w/f'outputs/_analyses/specificity-ladder/unit-f-cpu-evidence/native-round3-b66c2d8/diagnostics/cpu-next-cases{chunk}-job{job}'
read=lambda q:json.loads(q.read_text());sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest();save=lambda n,v:(e/n).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
c=read(d/'coordinator-result.json');r=read(d/'result.json');identity=read(d/'driver-identity.json');catalog=read(p.parent/'source-and-cases.json');dm=read(p/'driver-hashes.json');submission=read(p/'submission.json')
assert r['exit_code']==0 and r['term_sent_at'] is None and r['elapsed_seconds']<r['timeout_seconds']
assert c['indices']==list(range(start,start+count)) and c['new_native_case_count']==count and c['preserved_case_references_unchanged'] and len(c['preserved_case_ids'])==start
assert c['new_case_ids']==[x['invocation_id'] for x in catalog['cases'][start:start+count]]
assert not any(c[x] for x in ('full_pilot_complete','aggregate_executed','scientific_execution','execution_authorized'))
assert c['forbidden_auth_model_forwards']==0 and all(x['new_model_forwards']==0 for x in c['authentication'])
assert c['actual_new_forward_calls']==sum(x['actual_forward_calls'] for x in c['native'])==sum(x['original_case_forward_calls'] for x in c['original_case_records'])
assert {n:sha(w/n) for n in catalog['source_hashes']}==catalog['source_hashes']==identity['source_hashes']
assert sha(p/'driver-hashes.json')==submission['driver_manifest_sha256']
assert all(sha(p/n)==v['sha256'] for n,v in dm.get('drivers',dm.get('files')).items())
for f in d.iterdir():
 assert f.is_file();shutil.copy2(f,e/f.name)
for f in p.iterdir():
 if f.is_file() and f.suffix!='.md':shutil.copy2(f,e/f.name)
shutil.copy2(Path('/tmp/report97-review111-round3-frozen-source.json'),e/'frozen-source.json')
for suffix in ('out','err'):shutil.copy2(w/'logs'/f'lad-a3-native-cpu{chunk}-{job}.{suffix}',e/f'slurm-{job}.{suffix}')
cmd=['sacct','-j',job,'--format=JobIDRaw,JobName,State,ExitCode,ElapsedRaw,TimelimitRaw,AllocTRES,MaxRSS,Start,End','-P'];result=subprocess.run(cmd,env=dict(os.environ,TZ='UTC'),capture_output=True,text=True,check=True);(e/'terminal-accounting.txt').write_text(result.stdout);assert not result.stderr
accounting={x['JobIDRaw']:x for x in csv.DictReader(io.StringIO(result.stdout),delimiter='|')};assert len(accounting)==4 and all(x['State']=='COMPLETED' and x['ExitCode']=='0:0' for x in accounting.values())
allocation=read(d/'coordinator-allocation.json');assert allocation['actual_GPU_count']==0 and allocation['allocation_memory_bytes']==34359738368 and allocation['job_id']==job
rows=[]
for i,(n,a,o) in enumerate(zip(c['native'],c['authentication'],c['original_case_records']),start):
 assert n['case_id']==a['case_id']==o['case_id']==catalog['cases'][i]['invocation_id']
 name='slurm-case-'+n['case_id']+'.json';s=read(d/name)
 assert s['case_reference']==o['reference'] and s['native']==n and s['authentication']==a and s['allocation_reference']==c['slurm_allocation_reference']
 assert s['actual_job_id']==job and s['actual_step_id']=='0' and s['host']==allocation['host'] and not s['scientific_execution'] and not s['production_admission']
 assert sha(Path(s['allocation_reference']['path']))==s['allocation_reference']['sha256']
 rows.append(dict(index=i,case_id=n['case_id'],source_task=catalog['cases'][i]['source_task'],panel=catalog['cases'][i]['panel'],native_seconds=n['native_seconds'],actual_forwards=n['actual_forward_calls'],original_case_seconds=o['original_case_seconds'],authentication_seconds=a['authentication_seconds'],auth_new_forwards=0,actual_job_id=job,actual_step_id=s['actual_step_id'],actual_node=s['host'],case_reference=s['case_reference'],sidecar_path=str(d/name),sidecar_sha256=sha(d/name)))
save('per-case-observations.json',rows)
before={x['path']:x for x in read(d/'memory-before.json')};after={x['path']:x for x in read(d/'memory-after.json')};delta={}
for path,b in before.items():
 a=after[path]
 if 'memory.events' not in b or 'memory.events' not in a:delta[path]={'status':'v2 counters unavailable; see unmodified raw fields'};continue
 parse=lambda x:{k:int(v) for k,v in (line.split() for line in x.splitlines())};bv,av=parse(b['memory.events']),parse(a['memory.events']);delta[path]={k:av[k]-v for k,v in bv.items()};assert not any(delta[path].values())
steps=[json.loads(x) for x in (d/'steps.log').read_text().splitlines()];first=next(x['elapsed_seconds'] for x in steps if x['event']=='native_start');pub=[x['actual_publication_and_reference_seconds'] for x in steps if x['event']=='case_allocation_sidecar_published'];assert len(pub)==count
measurement=dict(setup_to_first_native_seconds=first,native_seconds_total=sum(x['native_seconds'] for x in rows),original_case_seconds_total=sum(x['original_case_seconds'] for x in rows),authentication_seconds_total=sum(x['authentication_seconds'] for x in rows),first_authentication_seconds=rows[0]['authentication_seconds'],warm_authentication_max_seconds=max(x['authentication_seconds'] for x in rows[1:]),warm_authentication_min_seconds=min(x['authentication_seconds'] for x in rows[1:]),sidecar_publication_seconds_total=sum(pub),sidecar_publication_max_seconds=max(pub),final_auth_to_child_exit_seconds=r['elapsed_seconds']-next(x['elapsed_seconds'] for x in reversed(steps) if x['event']=='auth_end'),timing_domain='Actual compute-node CPU intervals; native time contained within original case timer; uncontrolled caches; no GPU pricing')
if number=='141':
 gate=read(d/'parent-gate.json');assert gate['parent_job_id']=='23470779' and gate['new_model_forwards']==0 and gate['authenticated_parent_case_ids']==[x['invocation_id'] for x in catalog['cases'][32:49]]
 assert sha(Path(c['parent_gate_reference']['path']))==c['parent_gate_reference']['sha256'];measurement['parent_gate_seconds']=gate['gate_seconds'];measurement['parent_gate_original_reference_scan_reused']=True
save('timing-summary.json',measurement)
manifest=dict(status='completed_actual_Slurm_CPU_chunk_original_injected_semantics',job_id=job,process=r,coordinator=c,per_case=rows,actual_allocation=allocation,terminal_accounting=accounting,cgroup_event_deltas=delta,observed_steps=steps,timings=measurement,counts=dict(new_cases=count,old_cases_preserved=start,known_authenticated_cases=start+count,required_selected_cases=63,remaining_cases=63-start-count,actual_new_forward_calls=c['actual_new_forward_calls'],auth_model_forwards=0,aggregate=False,calibration_shards=0,assessment_shards=0),source_hashes=catalog['source_hashes'],source_and_driver_hashes_unchanged=True,source_check_domain='Original before/after source/model/scenario and old byte references checked on compute node; local author follows compact metadata only',no_local_model_or_heavy_replay=True,no_retry_or_extra_chunk=True,all_owned_processes_of_this_job_terminal=True,commands=[dict(command='Root submission preserved in submission.json',author_submitted=False),dict(command='TZ=UTC '+' '.join(cmd),exit_code=0,output='terminal-accounting.txt')]);save('run_manifest.json',manifest)
table='| Case | Source | Native seconds | Original case seconds | Authentication seconds | Forwards |\n|---|---|---:|---:|---:|---:|\n'+''.join('| {index} | {source_task}{cal} | {native_seconds:.2f} | {original_case_seconds:.2f} | {authentication_seconds:.2f} | {actual_forwards:,} |\n'.format(cal=' calibration' if x['panel']=='calibration_pilot' else '',**x) for x in rows)
acct=accounting[job];slurm_rss=accounting[job+'.0']['MaxRSS'];af=allocation['allocation_fields'];node=allocation['host'].split('.')[0]
gatepara=''
if number=='141':gatepara=f"The genuine completed-parent gate passed before model construction, taking {measurement['parent_gate_seconds']:.3f} seconds and adding zero forwards. It reused the existing original prior-case reference scan, preserved actual accounting observations, and authenticated parent scope and pinned source/scenario/model identity. [Actual gate](parent-gate.json)."
gatepara=gatepara.replace('(parent-gate.json)',f'({slug}-evidence/parent-gate.json)')
report=f'''# Native CPU case chunk completed

Status: handed-back

## What changed

Original contiguous cases {start}–{start+count-1} completed in one unchanged `pilot_cases` call on an actual CPU allocation. All original numerical execution, controls, publication and full authentication ran. The {start} prior case references remain unchanged. No aggregate or retry followed. [Complete scope]({slug}-evidence/run_manifest.json).

## How verified

The compute-node supervisor and coordinator checked genuine allocation/user/node/work directory, CPU memory, absence of GPUs and finish time. Real Slurm environment variables were retained. Original final model/scenario/source checks and prior-case reference comparison passed. Immutable sidecars bind each new case byte reference to its actual allocation, job/step/node/PID and separate numerical/authentication observations. Local author follow-up read compact metadata only. [Allocation]({slug}-evidence/coordinator-allocation.json), [coordinator]({slug}-evidence/coordinator-result.json), [sidecar reconciliation]({slug}-evidence/per-case-observations.json).

{gatepara}

The injected fixture remains nonauthorizing with `scientific_execution=False`. No production admission, old lineage re-signing or cross-process proof cache was introduced. First authentication constructed fresh process-local backing; later checks retained original byte/source/PID validation. Filesystem cache state was uncontrolled. [Original observations]({slug}-evidence/run_manifest.json).

## Execution evidence

Job {job} completed with exit `0:0` in {int(acct['ElapsedRaw']):,} seconds, from `{acct['Start']}` to `{acct['End']} UTC`. Actual placement was `{af['Partition']}`, `{af['Account']}`, {node}, with 4 CPUs, 32 GiB and zero GPUs. All job steps are terminal and successful. [Terminal accounting]({slug}-evidence/terminal-accounting.txt), [actual allocation]({slug}-evidence/coordinator-allocation.json), [submission]({slug}-evidence/submission.json).

The direct fixture child exited successfully after {r['elapsed_seconds']:,.2f} seconds without a timeout signal under its {r['timeout_seconds']:,}-second cap plus {r['kill_grace_seconds']}-second grace. Setup to first native invocation took {first:.2f} seconds. Native timing below is contained within original case timing; full authentication is separate genuine work. [Direct child]({slug}-evidence/result.json), [timing summary]({slug}-evidence/timing-summary.json), [per-case observations]({slug}-evidence/per-case-observations.json).

{table}
Genuine forwards totaled {c['actual_new_forward_calls']:,}; authentication added none and had no forbidden forward. Sidecar publication and reference work took {measurement['sidecar_publication_seconds_total']:.3f} seconds in total, measured separately. [Counters and timings]({slug}-evidence/run_manifest.json).

Direct child peak RSS was {r['peak_child_rss_bytes']:,} bytes. Independent Slurm step MaxRSS was `{slurm_rss}`. Job and step-user memory limits were 34,359,738,368 bytes. Every available memory-event counter was unchanged at leaf, job and ancestor levels; root counters remain explicitly unavailable. [Direct metrics]({slug}-evidence/result.json), [Slurm metrics]({slug}-evidence/terminal-accounting.txt), [cgroup reconciliation]({slug}-evidence/run_manifest.json).

## What is NOT done

The scenario has {start+count} authenticated cases out of 63; {63-start-count} remain. Full pilot aggregation, calibration scoring, assessment, summaries and injected-finality refusal remain unexecuted. Case coverage alone is not whole-pilot completion. No scientific efficacy result, production admission, allocated-GPU cost or controlled host-speed comparison is claimed. [Remaining scope]({slug}-evidence/run_manifest.json).

## Open questions

Root owns accounting and any later operational release. Original failures, source/harness and all scientific counts remain preserved. Further numerical or aggregate work requires a separately bounded authorized step; this job performed no follow-on action.
'''
reportpath=w/rel/(slug+'-handback.md');assert not reportpath.exists();reportpath.write_text(report)
lintcmd=['research-session','lint',str(reportpath)];lint=subprocess.run(lintcmd,capture_output=True,text=True);(e/'lint.txt').write_text(lint.stdout+lint.stderr);assert lint.returncode==0,lint.stdout+lint.stderr
manifest['commands'].append(dict(command=' '.join(lintcmd),exit_code=0,output='lint.txt'));save('run_manifest.json',manifest)
numcmd=['/sw/external/python/anaconda3/bin/python3.9','scripts/check_report_numbers.py',str(reportpath),'--strict','--json'];num=subprocess.run(numcmd,capture_output=True,text=True);(e/'number-check.json').write_text(num.stdout);assert num.returncode==0,num.stdout+num.stderr
manifest['commands'].append(dict(command=' '.join(numcmd),exit_code=0,output='number-check.json'));manifest['artifacts']={f.name:dict(bytes=f.stat().st_size,sha256=sha(f)) for f in sorted(e.iterdir()) if f.name!='run_manifest.json'};save('run_manifest.json',manifest)
pe=primary/rel/e.name;pr=primary/rel/reportpath.name;assert not pe.exists() and not pr.exists();shutil.copytree(e,pe);shutil.copy2(reportpath,pr)
plint=subprocess.run(['research-session','lint',str(pr)],capture_output=True,text=True);assert plint.returncode==0,plint.stdout+plint.stderr
pn=subprocess.run(['/sw/external/python/anaconda3/bin/python3.9',str(primary/'scripts/check_report_numbers.py'),str(pr),'--strict','--json'],capture_output=True,text=True);assert pn.returncode==0,pn.stdout+pn.stderr
assert sha(pr)==sha(reportpath) and {f.name:sha(f) for f in e.iterdir()}=={f.name:sha(f) for f in pe.iterdir()}
print(json.dumps(dict(report=str(pr),raw=str(pe),manifest_sha256=sha(e/'run_manifest.json'),numeric_counts=json.loads(num.stdout)['counts'],counts=manifest['counts'],timings=measurement),indent=2))
