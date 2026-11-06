from pathlib import Path
import os,sys,json,hashlib,math,time,argparse,subprocess,collections
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--manifest-sha256',required=True);a=ap.parse_args();OUT=Path(a.output);OUT.mkdir(exist_ok=False,parents=True)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(n,o):
 with (OUT/n).open('x') as f:json.dump(o,f,indent=2,allow_nan=False);f.write('\n')
PACKET=Path(__file__).resolve().parent
def packet():
 assert sha(PACKET/'manifest.json')==a.manifest_sha256
 for n,d in read(PACKET/'manifest.json').items():assert sha(PACKET/n)==d,n
packet()
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');ROOT=Path('/projects/beto/swong2/Alignment');D=W/'.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103';Q=D/'root-H100-R5/job-50189932';F=Q/'actual-completed-20261106';G=read(Q/'config.json');R=Path(G['runtime']) if 'runtime' in G else W/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime'
job=os.environ['SLURM_JOB_ID'];raw=subprocess.check_output(['scontrol','show','job',job,'-o'],text=True,timeout=15,env=dict(os.environ,TZ='UTC'));facts=dict(x.split('=',1) for x in raw.split() if '=' in x);assert facts['JobState']=='RUNNING' and facts['NumCPUs']=='4' and facts['Partition'].startswith('cpu') and facts['Account'].endswith('-cpu') and 'gres/gpu' not in facts.get('AllocTRES','');write('audit-allocation.json',dict(job=job,raw_scontrol=raw))
assert sha(Q/'config.json')=='1d96dd830d0f0bb4bf375ba99af676e8ee7ece322ec87ff5ae317edc1fd4533a'
# Rehash fetched bytes; no assessment metrics are emitted.
table=read(F/'local-output-hashes.json');assert table==read(F/'remote-output-hashes.json')
for row in table:
 base=F/row['label'];p=base/row['path'] if base.is_dir() else base
 if row['kind']=='file':assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],str(p)
 elif row['kind']=='symlink':assert p.is_symlink() and os.readlink(p)==row['target']
 else:raise AssertionError('unknown file kind')
snap=read(R.parent/'snapshot.json');assert snap['source_commit']=='50e947bb852613e3a270082651f2bd1b7bb0c525';assert len(snap['source_sha256'])==511 and len(snap['input_links'])==4
for n,h in snap['source_sha256'].items():assert sha(R/n)==h,n
for n,t in snap['input_links'].items():assert (R/n).is_symlink() and os.readlink(R/n)==t
os.chdir(R);sys.path.insert(0,str(R));from component_analysis import a2_pipeline as p
assert Path(p.__file__).resolve()==R/'component_analysis/a2_pipeline.py'
def origins():
 o={n:str(Path(m.__file__).resolve()) for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','models','dataset','evaluation','scripts','config') and getattr(m,'__file__',None)}
 assert all(Path(v).is_relative_to(R) for v in o.values());return o
origins_before=origins()
raw_bank=p.a1.read_artifact(F/'bank/banks.json');actual_numeric=p.numeric_environment();recorded_numeric={t:b['contract']['numeric_environment'] for t,b in raw_bank['banks'].items()}
write('numeric-environment-comparison.json',dict(current=actual_numeric,recorded=recorded_numeric))
if not all(v==actual_numeric for v in recorded_numeric.values()):
 write('NUMERIC_ENVIRONMENT_MISMATCH.json',dict(status='BLOCKED',reason='Exact native numeric environment differs; no checks weakened.',current=actual_numeric,recorded=recorded_numeric));raise SystemExit(2)
del raw_bank
cmd=read(F/'execution/bank-command.json')['command'];args=p.parser().parse_args(cmd[2:]);prepared,selected,sidecar=p._load_context(args);args.tasks=list(p.TASKS)
for key in ('model','model_revision','tokenizer_revision'):setattr(args,key,prepared[key])
args.injected=False;receipt=p.a1.read_artifact(Path(G['main_root'])/'groups.json');p._validate_live(args,receipt,prepared);assert not prepared.get('injected') and not receipt['injected']
banks=p.read_stage(Path(G['main_root'])/'bank','banks.json','bank',args,receipt);p.validate_banks(receipt,prepared,banks);assert not banks['injected']
scored=p.read_stage(Path(G['pilot_root'])/'score','score.json','score',args,receipt);assert not scored['injected'] and scored['pilot'] and scored['limit']==4
assert scored['expected']==[list(k) for k in p.expected_keys(receipt,4)];p.validate_a2_scope(receipt,scored['rows'],limit=4,banks=banks,bank_path=Path(G['main_root'])/'bank/banks.json');p.a1.validate_positive_controls(scored['positive_controls'],p._prepared_domain(receipt),4)
assert scored['bank_artifact_sha256']==p.hash_content(banks);assert len(scored['rows'])==len(scored['expected'])==2484 and len(scored['positive_controls'])==144
bank_diag={}
for task,b in banks['banks'].items():
 prov=b['provenance'];assert len(prov['source_ids'])==400 and prov['source_condition']=='H' and set(prov['splits'])=={'train','validation'}
 bank_diag[task]=dict(source_count=len(prov['source_ids']),splits=prov['splits'],n_tokens=prov['n_tokens'],typed_vectors=len(b['values']))
controls=scored['positive_controls'];rows=scored['rows'];errors=[abs(float(r['self_replay_margin_error'])) for r in rows];assert all(math.isfinite(x) for x in errors);assert all(r.get('assay_valid') is True for r in rows)
control_diag=dict(row_count=len(rows),expected_count=len(scored['expected']),positive_count=len(controls),positive_failed=sum(c.get('valid') is not True for c in controls),positive_max_abs_logit_error=max(float(c['max_abs_logit_error']) for c in controls),self_replay_margin_error_max=max(errors),assay_invalid_rows=sum(r.get('assay_valid') is not True for r in rows),operation_counts=dict(collections.Counter(r['operation'] for r in rows)),row_field_names=sorted(set().union(*(r.keys() for r in rows))),assessment_effects_inspected=False)
# Phase evidence: historical captured ledger is entry authority; current ledger reconciliation is separate.
phase_diag={}
for phase,release_name in [('bank','root-release.json'),('prefix4','root-release-prefix4.json')]:
 h=D/'root-model-phase-release-helper/r5-r2/executions/50189932'/phase;rel=read(h/'root-release.json');pub=read(h/'publication.json');comp=read(h/'composite-preflight.json')
 assert pub['release_sha256']==sha(h/'root-release.json');assert sha(h/'composite-preflight.json')==rel['delta_preflight_receipt_sha256'];assert comp['actual_CPU_job_id']=='23606524' and comp['actual_GPU_job_id']=='50189932' and comp['complete']
 cpu=read(comp['actual_CPU_COMPLETE']['path']);assert sha(comp['actual_CPU_COMPLETE']['path'])==comp['actual_CPU_COMPLETE']['sha256'];assert cpu['complete'] and cpu['status']=='PASS' and cpu['phase']==phase and cpu['actual_CPU_job_id']=='23606524' and cpu['timely_window']
 assert cpu['actual_Delta_owning_guards_passed'] and cpu['stable_Delta_catalogues_before_after'];assert cpu['model_loaded'] is False
 cache=read(comp['actual_per_start_cache_check']['path']);assert sha(comp['actual_per_start_cache_check']['path'])==comp['actual_per_start_cache_check']['sha256'];assert cache['model_loaded'] is False and len(cache['metadata'])==6 and len(cache['weights'])==4
 consumed=read(F/'execution'/('CONSUMED-'+phase+'.json'));assert consumed['release_sha256']==sha(h/'root-release.json');assert 0<=consumed['consumed_at']-rel['issued_at']<=300 and consumed['consumed_at']<=rel['expires_at'];assert rel['expires_at']==rel['issued_at']+300
 tree=h/'transfer-tree';hist=tree/Path(G['canonical_ledger']).relative_to(ROOT);assert sha(hist)==rel['ledger_sha256'];ledger=read(hist);entry=next(x for x in ledger['reservations'] if x['id']=='r-041');assert entry['reserved_gpu_hours']==1.0 and entry['requested_minutes']==60 and entry['job_id']=='50189932'
 phase_diag[phase]=dict(owning_CPU_COMPLETE_sha256=comp['actual_CPU_COMPLETE']['sha256'],publication_unix=pub['published_unix'],issued_at=rel['issued_at'],consumed_at=consumed['consumed_at'],entry_lease_age_seconds=consumed['consumed_at']-rel['issued_at'],historical_ledger_sha256=sha(hist),cache_check_sha256=comp['actual_per_start_cache_check']['sha256'],CPU_finish_before_deadline=cpu['supervisor_finished_unix']<=cpu['deadline_unix'])
current=read(G['canonical_ledger']);row=next(x for x in current['reservations'] if x['id']=='r-041');assert row['actual_seconds']==2260 and row['reserved_gpu_hours']==1.0 and row['requested_minutes']==60
bm=read(F/'bank/run_manifest.json');sm=read(F/'pilot/score/run_manifest.json');complete=read(F/'execution/COMPLETE.json');assert bm['execution_commit']==sm['execution_commit']==G['commit'];assert complete['counts']==scored['counts'];assert bm['execution']==banks['execution_provenance'] and sm['execution']==scored['execution_provenance'];assert complete['gpu_name']=='NVIDIA H100 80GB HBM3'
for e in [bm['execution'],sm['execution']]:assert e['dtype']=='torch.bfloat16' and e['device']=='cuda:0' and e['slurm_job_id']=='50189932'
result=dict(status='PASS',scope='timing/control audit only',actual_GPU_job='50189932',owning_reader_pass=True,source_commit=G['commit'],source_files=511,literal_links=4,source_G3_sha256=G['groups_file_sha256'],fetched_files_rehashed=len(table),bank=bank_diag,controls=control_diag,bank_execution=bm['execution'],score_execution=sm['execution'],bank_CLI=read(F/'execution/bank-command.json'),score_CLI=read(F/'execution/score-prefix4-command.json'),phases=phase_diag,reconciled_current_r041=row,source_model_weights_loaded=False,assessment_effects_inspected=False,full_score_admitted=False)
result['module_origins_before']=origins_before;result['module_origins_after']=origins();result['numeric_environment']=actual_numeric;packet();write('RESULT.json',result);print('PASS audit structural/controls/timing only',flush=True)
