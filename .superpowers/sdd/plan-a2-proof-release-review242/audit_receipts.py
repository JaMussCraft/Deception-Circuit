"""Pure local reconciliation of new50316939 release receipts; no remote calls."""
import hashlib,importlib.util,json
from pathlib import Path
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');B=W/'.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199';O=B/'root-genuine-proof-r5-ops';J=B/'root-genuine-proof-r2/job-50316939';R=W/'.superpowers/sdd/plan-a2-proof-release-review242';P=B/'proof-adapter-r5';VIRT='/projects/beto/swong2/Alignment';PHYS='/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment';PACKET='f12141b3b301d359dd7cf952ee47445b3bc637c31e9c4020c17da81cf268b26f';DISPATCH='9631dbf0c26f3576bda79787d1f1b6b8de89ffd8b19cfced0cf156bf917e5862';JOB='50316939';REVIEW='8c684e2dca9a2ff49cb7842daad401d89720fe2bf1b5c79492edd80d10e6d7ba'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={}
def read(p):
 pins[str(p)]=dict(sha256=sha(p),bytes=p.stat().st_size);return json.loads(p.read_text())
def receipt(n):
 x=read(O/n);assert x['exit_code']==0,n;return json.loads(x['stdout'])
def main():
 assert sha(P/'manifest.json')==PACKET
 manifest=read(P/'manifest.json');assert len(manifest)==37
 stage=receipt('stage-readback.json');inventory=read(O/'deployment-inventory.json');assert len(stage['files'])==len(inventory)==41
 staged={v['virtual']:v for v in stage['files']};assert len(staged)==41
 for row in inventory:
  v=staged[row['virtual']];assert v['physical']==row['physical'] and v['sha256']==row['sha256'] and v['bytes']==row['bytes'];local=Path(row['virtual']);assert sha(local)==v['sha256'] and local.stat().st_size==v['bytes']
 expected={str(P/n) for n in list(manifest)+['manifest.json']}|{str(B/'root-proof-dispatch237'/n) for n in ('dispatch.sh','test_dispatch.py')}|{str(W/'.superpowers/sdd/plan-a2-proof-resource-review238/verdict.json')};assert set(staged)==expected
 host=receipt('host-and-scheduler-checks.json');assert host['source']==dict(source_commit='50e947bb852613e3a270082651f2bd1b7bb0c525',source_files=511,literal_source_links=4,snapshot_sha256='68cc15073e383d0943620cab4271a9ee859ae51203e69704b83cca8ac7770f77');assert host['review_sha256']==REVIEW and sha(W/'.superpowers/sdd/plan-a2-proof-resource-review238/verdict.json')==REVIEW
 checks=host['tests_and_scheduler'];assert len(checks)==4 and all(v['exit_code']==0 for v in checks);assert 'Ran 7 tests' in checks[0]['stderr'] and 'Ran 9 tests' in checks[1]['stderr']
 namespace=read(B/'root-proof-transfer-r2/namespace-preflight.json');expected_files={v['virtual']:v for v in namespace['files']};assert len(expected_files)==1151 and len(namespace['aliases'])==11
 immutable=receipt('immutable-readback.json');verified={v['virtual']:v for v in immutable['verified']};assert immutable['complete'] is True and immutable['expected_count']==len(verified)==1151 and immutable['aliases_verified']==11 and set(verified)==set(expected_files)
 for n,v in verified.items():e=expected_files[n];assert all(v[k]==e[k] for k in ('resolved_physical','bytes','sha256'))
 closure=read(P/'transfer-closure.json');routes={v['virtual']:v for v in closure['files']};cats={v['virtual'] for v in closure['fresh_catalogues']};assert set(verified)==set(routes)-cats
 for n,e in expected_files.items():assert e['sha256']==routes[n]['sha256'] and e['physical']==routes[n]['physical']
 submitted=receipt('held-submission.json');assert submitted['exit_code']==0 and submitted['stdout'].strip()==JOB and '--hold' in submitted['argv'];assert submitted['argv'][-1]==PHYS+'/'+str((B/'root-proof-dispatch237/dispatch.sh').relative_to(VIRT))
 for option in ('--account=cis260361p','--partition=RM-shared','--qos=rm','--nodes=1','--ntasks=1','--cpus-per-task=26','--mem=48G','--time=00:45:00','--no-requeue','--export=ALL,CUDA_VISIBLE_DEVICES='):assert option in submitted['argv']
 catstage=receipt('catalogue-readback.json');assert catstage['remote_catalogues_not_rewritten'] is True;assert catstage['actual_job_id']==JOB and catstage['spooled_sha256']==DISPATCH;fields=dict(v.split('=',1) for v in catstage['held_state'].split() if '=' in v)
 for k,v in dict(JobId=JOB,JobState='PENDING',Reason='JobHeldUser',RunTime='00:00:00',Requeue='0',Restarts='0',Account='cis260361p',QOS='rm',Partition='RM-shared',TimeLimit='00:45:00',NumCPUs='26',NumTasks='1').items():assert fields[k]==v
 assert fields['CPUs/Task']=='26' and 'gres/gpu' not in fields['TRES'] and fields['Command'].endswith('/root-proof-dispatch237/dispatch.sh');tres=dict(v.split('=',1) for v in fields['TRES'].split(','));assert tres['cpu']=='26' and tres['mem']=='48G' and tres['node']=='1' and fields['NumNodes'] in ('1','1-1') and '(105853)' in fields['UserId'];assert fields['WorkDir']==PHYS+'/'+str((W/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime').relative_to(VIRT))
 binding=read(J/'bindings.json');att=read(J/'transfer-attestation.json');side=(J/'bindings.sha256').read_bytes();assert sha(J/'bindings.json')=='5a055aeff26499b3afc05901e2084e722e29deeaac6f18ce3172fdf33ce84188' and side==sha(J/'bindings.json').encode()+b'\n';assert sha(J/'transfer-attestation.json')=='f4d4d143cd171bd116b989922720175364352f029524230959aa37677e1cbe30';assert binding['actual_job_id']==att['actual_job_id']==JOB and binding['adapter_manifest_sha256']==att['adapter_manifest_sha256']==PACKET
 assert all(old not in json.dumps(binding)+json.dumps(att) for old in ('50313499','50315944'))
 spec=importlib.util.spec_from_file_location('actual_witness_guard',P/'proof_guards.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);rows=g.catalogue_expectations(dict(path=str(J/'transfer-attestation.json'),sha256=sha(J/'transfer-attestation.json')),PACKET,JOB);capture=read(O/'catalogue-capture.json');assert set(rows)==cats and set(catstage['current_catalogues'])==cats
 for n,row in rows.items():
  assert row['delta_capture']==capture['current_catalogues'][n]['delta_capture'];assert row['remote']==catstage['current_catalogues'][n];assert Path(n).stat().st_size==row['bytes'] and sha(n)==row['sha256']
 assert att['immutable_readback']['sha256']==sha(O/'immutable-readback.json') and att['immutable_readback']['immutable_routes']==1151 and att['immutable_readback']['aliases']==11;assert att['source_before_activation_evidence']==host['source']
 sealed=receipt('binding-stage-readback.json');assert sealed['job_id']==JOB and sealed['actual_running_allocation_claimed'] is False and all(sealed[k] is True for k in ('held_job_confirmed','binding_schema_validated_against_actual_held_job','all_external_references_match','all_four_remote_catalogues_match','output_absent'))
 for n,v in sealed['files'].items():assert v['path']==PHYS+'/'+str((J/n).relative_to(VIRT)) and v['sha256']==sha(J/n) and v['bytes']==(J/n).stat().st_size
 assert set(sealed['files'])=={'bindings.json','bindings.sha256','transfer-attestation.json'};assert binding['independent_review']['sha256']==REVIEW and binding['independent_review']['path']==PHYS+'/'+str((W/'.superpowers/sdd/plan-a2-proof-resource-review238/verdict.json').relative_to(VIRT))
 assert binding['transfer_attestation']['path']==PHYS+'/'+str((J/'transfer-attestation.json').relative_to(VIRT));assert binding['transfer_attestation']['sha256']==sha(J/'transfer-attestation.json');assert binding['output_physical']==PHYS+'/'+str((J/'execution').relative_to(VIRT)) and not(J/'execution').exists()
 probe=B/'root-preflight-ops-r5/actual-50311864/execution'
 for k,n in [('probe_result','probe-result.json'),('probe_host','host-cgroup.json'),('probe_container','container-cgroup.json'),('probe_command','command.json')]:assert binding[k]['sha256']==sha(probe/n) and binding[k]['path'].endswith('/root-cgroup199-r5/execution/'+n)
 assert read(probe/'probe-result.json')['container_exit']==0
 # Runtime continuity is inherited actual evidence, not a new login numerical pass.
 environment=read(B/'root-genuine-proof-r3-ops/environment-readback.json');env=json.loads(environment['stdout']);assert environment['exit_code']==0 and env['sif_sha256']=='f50c8e39dd5e2ac1c1a4bdfd443351cb970513fdb10a572725eb53d7396f8697' and env['packed_python_sha256']=='5c8e75cf8a297c6bd47595539e4696efb2d2662a9e3afb9741541d155ca9e5fd' and env['HF_hub_exists'] is True and env['available_bytes']>=12*1024**3 and env['numeric_environment_verified_here'] is False
 for n in ('bindings.json','bindings.sha256','transfer-attestation.json'):pins[str(J/n)]=dict(sha256=sha(J/n),bytes=(J/n).stat().st_size)
 result=dict(status='READY_RELEASE_EXISTING_HELD_CPU_JOB50316939_ONLY',job=JOB,packet_manifest_sha256=PACKET,dispatcher_sha256=DISPATCH,binding_sha256=sha(J/'bindings.json'),witness_sha256=sha(J/'transfer-attestation.json'),fresh_immutable_routes=1151,aliases_checked=11,immutable_wall_seconds=immutable['wall_seconds'],source_files=511,literal_links=4,fresh_current_catalogues=4,current_Delta_still_matches=True,source238_review_bound=True,successful_R5_probe_refs_bound=True,failed50313499_and50315944_not_authority=True,exact_held_spooled_dispatcher=True,output_absent=True,all_sealed_files_remote_readback_match=True,runtime_evidence='Inherited actual SIF/Python/cache/space readback plus prior native-owning path; no fresh login numerical claim. New job repeats actual SIF and native environment checks.',actual_running_allocation_claimed=False,resource_result_claimed=False,evidence_pins=pins)
 (R/'audit-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence_pins'},indent=2))
if __name__=='__main__':main()
