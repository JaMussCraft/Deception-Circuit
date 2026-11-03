from pathlib import Path
import json,hashlib,collections,subprocess,math
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');E=W/'docs/research/specificity-ladder/reports/154-a2-timing-audit-evidence';G=W/'.superpowers/sdd/plan-a2-analysis/real-input-readiness/bank-scoring-timing/launch-g2';R=G/'gpu-result';cfg=json.loads((G/'config.json').read_text());root=Path(cfg['main_root']);pilot=Path(cfg['pilot_root']);B=Path(cfg['runtime']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();digest=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();complete=json.loads((R/'COMPLETE.json').read_text());assert complete['complete'] and not complete['full_scoring_admitted'] and complete['job_id']=='23473669'
snapshot=json.loads(Path(cfg['snapshot']).read_text());assert sha(Path(cfg['snapshot']))==cfg['snapshot_sha256'];assert snapshot['source_commit']==cfg['commit'] and len(snapshot['source_sha256'])==511
for n,h in snapshot['source_sha256'].items():assert sha(B/n)==h,n
for file in ('source-before.json','source-after.json'):
 s=json.loads((R/file).read_text());assert s['source_commit']==cfg['commit'] and s['snapshot_sha256']==cfg['snapshot_sha256'] and s['groups_file_sha256']==cfg['groups_file_sha256'] and s['source_count']==511
assert sha(root/'groups.json')==sha(pilot/'groups.json')==cfg['groups_file_sha256']
files={};payloads={}
for name,p in [('score',pilot/'score/score.json'),('bank',root/'bank/banks.json')]:
 envelope=json.loads(p.read_text());assert envelope['sha256']==digest(envelope['payload']);payloads[name]=envelope['payload'];files[str(p)]=sha(p)
score=payloads['score'];bank=payloads['bank'];sm=json.loads((pilot/'score/run_manifest.json').read_text());bm=json.loads((root/'bank/run_manifest.json').read_text());assert sha(pilot/'score/run_manifest.json')==complete['score_manifest_sha256'];assert sha(root/'bank/run_manifest.json')==complete['bank_binding']['bank_manifest_sha256'];assert sha(root/'bank/banks.json')==complete['bank_binding']['bank_file_sha256']
assert not score['injected'] and not bank['injected'] and score['pilot'] and score['limit']==4
assert score['receipt_sha256']==bank['receipt_sha256']==cfg['groups_receipt_sha256'];assert score['bank_artifact_sha256']==digest(bank)
for m in (sm,bm):
 assert m['execution_commit']==cfg['commit'] and m['a1_ancestor_commit']=='5f450dc93dac707af649dee8c8ca60888b2831db'
 for n,h in m['runtime_code_hashes'].items():assert sha(B/n)==h,n
 for p,h in m['registry_hashes'].items():assert sha(Path(p))==h,p
 for p,h in m['grader_registry'].items():assert sha(Path(p))==h,p
 assert m['model_identity']['dtype']=='bfloat16'
 for v in m['source_artifacts'].values():assert sha(Path(v['path']))==v['file_sha256']
rows=score['rows'];controls=score['positive_controls'];keys=[tuple(r.get(k) for k in ('task','instance_id','condition','stream','group','operation','donor_seed')) for r in rows];expected=list(map(tuple,score['expected']));assert len(rows)==len(expected)==2484 and len(set(keys))==2484 and set(keys)==set(expected)
assert len(controls)==144 and all(c['valid'] for c in controls);ck=[tuple(c[k] for k in ('mechanism_task','task','instance_id','condition','stream')) for c in controls];assert len(set(ck))==144
aliases=sorted({r['group'] for r in rows});assert len(aliases)==9 and aliases==sorted(a for task in cfg['scope'].values() for a in task['aliases'])
assert set(r['operation'] for r in rows)=={'item_swap','zero','h_mean','h_twin','self_replay','empty'}
banks={}
for t,b in bank['banks'].items():
 c=b['contract'];assert c['n_instances']==400 and len(c['source_ids'])==400 and len(set(c['source_ids']))==400 and c['source_condition']=='H';assert len(b['values'])==cfg['scope'][t]['bank_keys'];banks[t]=dict(instances=400,keys=len(b['values']),source_id_order_sha256=digest(c['source_id_order']))
devices=[json.loads((R/n).read_text()) for n in ('gpu-before-bank.json','gpu-before-score.json')];assert devices[0]['gpu_uuid']==devices[1]['gpu_uuid']==complete['gpu_uuid'] and all(d['gpu_name']=='NVIDIA H200' and d['job_id']=='23473669' for d in devices)
for ex in (sm['execution'],bm['execution']):assert ex['gpu_name']=='NVIDIA H200' and ex['device']=='cuda:0' and ex['dtype']=='torch.bfloat16' and ex['slurm_job_id']=='23473669'
ledger=json.loads(Path(cfg['canonical_ledger']).read_text());entry=next(e for e in ledger['reservations'] if str(e['job_id'])=='23473669');assert entry['id']=='r-039' and entry['gpus']==1 and entry['reserved_gpu_hours']==.4167 and entry['requested_minutes']==25 and entry['source_commit']==cfg['commit']
phase=collections.defaultdict(float)
mapping_paths=[p for p in (Path(cfg['mapping_origin']).parent/'mapping-successors').glob('mapping-*') if (p/'COMPLETE.json').is_file()]
active=max(mapping_paths,key=lambda p:json.loads((p/'payload.json').read_text())['generation']);mapping=json.loads((active/'payload.json').read_text());assert set(mapping['expected_entry_ids'])=={e['id'] for e in ledger['reservations']}
for e in mapping['entries']:phase[e['experiment']]+=e['original_reserved_gpu_hours']
assert math.isclose(sum(phase.values()),sum(e['reserved_gpu_hours'] for e in ledger['reservations']))
for k,v in cfg['experiment_limits'].items():assert phase[k]<=v
assert sum(phase.values())<=125
accounting=subprocess.check_output(['sacct','-n','-P','-j','23473669','--format=JobIDRaw,State,ExitCode,Elapsed,AllocTRES,MaxRSS'],text=True);(E/'sacct-terminal.txt').write_text(accounting);assert '23473669|COMPLETED|0:0|' in accounting
ratio=59652/2484;estimate=sm['execution']['scoring_compute_seconds']*ratio;bounded=math.ceil((estimate*1.5+420)/1800)*1800
assert bounded==27000
full=list(cfg['score_command']);idx=full.index('--work-dir');full[idx+1]=str(root);i=full.index('--limit');del full[i:i+2]
proposal=dict(status='RESOURCE_PROPOSAL_ONLY_NOT_EXECUTION_ADMISSION',source_commit=cfg['commit'],command=full,groups_sha256=cfg['groups_file_sha256'],completed_bank_file_sha256=sha(root/'bank/banks.json'),full_rows=59652,pilot_rows=2484,row_ratio=ratio,measured_H200_compute_seconds=sm['execution']['scoring_compute_seconds'],row_scaled_compute_seconds=estimate,uncertainty_multiplier=1.5,fixed_allowance_seconds=420,requested_seconds=bounded,minutes=bounded//60,gpu_hours=bounded/3600,gpus=1,gpu_type='h200',cpus=4,memory_gib=64,batch_size=8,dtype='bfloat16',backend='sdpa',no_bank_rebuild=True,coherent_scope='all nine frozen groups and full original assessment/utility coverage',basis='ceil to half-hour of1.5xrow-scaled measured compute+420seconds; bounded request, not guaranteed fit; prefix/sequence-length/caches uncontrolled',required_before_submission=['fresh root cap/reservation/mapping/release review','fresh original source/registry/grader/protection preflight immediately before model','actual single H200/live lease and matching bank numerical/architecture profile','fresh full score directory; no overwrite/resign timing receipt','bound same source/model/backend/batch; preserve all controls; no automatic retry','review remaining lease/cleanup and complete owning output before downstream finalization'],current_phase_reserved=dict(phase),prospective_A2_reserved=phase['A2']+bounded/3600,prospective_global_reserved=sum(phase.values())+bounded/3600,execution_authorized=False)
assert proposal['prospective_A2_reserved']<=60 and proposal['prospective_global_reserved']<=125
(E/'full-scoring-resource-proposal.json').write_text(json.dumps(proposal,indent=2)+'\n')
verdict=dict(status='PASS_SCOPED_MEASURED_BANK_AND_PREFIX4_TIMING',source_commit=cfg['commit'],job_id='23473669',source_file_count=511,source_unchanged_now=True,rows=2484,expected=2484,unique_expected_keys=2484,positive_controls=144,all_controls_valid=True,group_aliases=aliases,original_H_banks=banks,gpu_uuid=complete['gpu_uuid'],same_bank_score_UUID=True,execution=sm['execution'],budget_reservation=entry,current_phase_reserved=dict(phase),budget_old_charges_retained=True,complete_file_sha256=sha(R/'COMPLETE.json'),score_manifest_sha256=sha(pilot/'score/run_manifest.json'),payload_file_sha256=files,full_resource_proposal_sha256=sha(E/'full-scoring-resource-proposal.json'),assessment_effects_inspected=False,model_or_execution_authority_granted=False,limitations=['prefix4 timing is not an upper bound or hardware drift test','same-H200 bank/score established; no Bridges2 hardware transfer claim','full expected-key builder/complete full-artifact validation and real fresh protection/lease remain owning CLI duties'])
(E/'audit-verdict.json').write_text(json.dumps(verdict,indent=2)+'\n');print('AUDIT_PASS',sha(E/'audit-verdict.json'));print('PROPOSAL',sha(E/'full-scoring-resource-proposal.json'));print('MEASURED_COMPUTE',estimate,'REQUEST_HOURS',bounded/3600,'BUDGET',dict(phase))
