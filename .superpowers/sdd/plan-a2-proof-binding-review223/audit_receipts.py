"""Pure local receipt reconciliation for one held CPU proof; no remote/scheduler calls."""
import hashlib,importlib.util,json,re,sys
from pathlib import Path
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');B=W/'.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199';P=B/'proof-adapter-r3';R=W/'.superpowers/sdd/plan-a2-proof-binding-review223';VIRT='/projects/beto/swong2/Alignment';PHYS='/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment';JOB='50313499';PACKET='4e4b4bcf1ddcd6481fac1eccd966a2a1cbfa385b2bd16a9a00504cfaa05def3f';DISPATCH='8abf86b1295addd5cd8b41f13176199fb0fcf753cf6f1c40c044a073fa05e6aa'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
pins={}
def receipt(rel):
 p=B/rel;pins[str(p)]=dict(sha256=sha(p),bytes=p.stat().st_size);return read(p)
def remote(rel):
 v=receipt(rel);assert v['exit_code']==0,rel;return json.loads(v['stdout'])
def main():
 assert sha(P/'manifest.json')==PACKET
 closure=read(P/'transfer-closure.json');catroutes={v['virtual'] for v in closure['fresh_catalogues']};declared={v['virtual']:v for v in closure['files']};assert len(declared)==1155
 namespace=receipt('root-proof-transfer-r2/namespace-preflight.json');assert namespace['complete'] is True and not namespace['mismatches'];expected={v['virtual']:v for v in namespace['files']};assert len(expected)==1151 and set(expected)==set(declared)-catroutes
 local=receipt('root-proof-transfer-r2/local-immutable-route-verification.json');assert local['immutable_verified_routes']==1151 and {v['virtual'] for v in local['files']}==set(expected) and all(all(v[k]==expected[v['virtual']][k] for k in ('virtual','physical','sha256','bytes','role','historical_sha256')) for v in local['files'])
 for n,v in expected.items():assert v['sha256']==declared[n]['sha256'] and v['physical']==declared[n]['physical'] and v['historical_sha256']==declared[n]['sha256']
 first=remote('root-proof-transfer-r2/remote-immutable-verification-attempt1.json');second=remote('root-proof-transfer-r2/remote-immutable-verification-attempt2.json');prior={};physical={v['resolved_physical']:n for n,v in expected.items()};assert len(physical)==1151
 for result in (first,second):
  for n,v in result['files'].items():
   assert n in expected and v['physical']==expected[n]['resolved_physical'] and v['expected_sha256']==expected[n]['sha256'] and v['expected_bytes']==expected[n]['bytes']
   if v.get('status')=='MATCH':assert v['sha256']==expected[n]['sha256'] and v['bytes']==expected[n]['bytes'];prior[n]=v
 assert len(prior)==1144 and second['errors']==[]
 aliases={v['virtual']:v for v in namespace['aliases']};assert len(aliases)==11 and set(second['aliases'])==set(aliases)
 for n,v in second['aliases'].items():assert v['physical']==aliases[n]['physical'] and v['literal']==aliases[n]['literal_target']
 inventory=receipt('root-proof-deployment-r3/deployment-inventory.json');stage=remote('root-proof-deployment-r3/stage-readback.json');assert stage['verified'] is True and stage['count']==len(inventory)==42
 staged={v['physical']:v for v in stage['files']};assert len(staged)==42
 for v in inventory:
  s=staged[v['physical']];assert all(s[k]==v[k] for k in ('physical','sha256','bytes','role'));assert sha(v['local'])==v['sha256'] and Path(v['local']).stat().st_size==v['bytes']
 missing={physical[v['physical']]:v for v in inventory if v['role']=='missing_immutable'};assert len(missing)==7 and not(set(missing)&set(prior)) and set(prior)|set(missing)==set(expected)
 for n,v in missing.items():assert v['sha256']==expected[n]['sha256'] and v['bytes']==expected[n]['bytes']
 expected_packet={str(Path(PHYS)/str((P/n).relative_to(VIRT))) for n in list(read(P/'manifest.json'))+['manifest.json']};assert {v['physical'] for v in inventory if v['role']=='packet'}==expected_packet
 summary=receipt('root-proof-deployment-r3/immutable-deployment-summary.json');assert summary['counts']==dict(prior_match=1144,staged_readback=7) and summary['immutable_routes']==1151 and summary['aliases_checked']==11
 for row in summary['evidence']:assert sha(B/row['path'])==row['sha256']
 host=remote('root-proof-deployment-r3/remote-packet-host-checks.json');assert host['packet_verified'] is True and host['source_members']==31 and host['host_python'].startswith('3.6.8');assert len(host['tests'])==3 and all(v['exit_code']==0 for v in host['tests']);assert 'Ran 7 tests' in host['tests'][0]['stderr'] and 'Ran 9 tests' in host['tests'][1]['stderr']
 source=remote('root-proof-deployment-r3/source-and-probe-remote-check.json');assert source['source']==dict(source_commit='50e947bb852613e3a270082651f2bd1b7bb0c525',source_files=511,literal_source_links=4,snapshot_sha256='68cc15073e383d0943620cab4271a9ee859ae51203e69704b83cca8ac7770f77') and source['uid']==105853
 dry=remote('root-genuine-proof-r3-ops/scheduler-dry-run.json');held=remote('root-genuine-proof-r3-ops/held-submission.json');assert dry['exit_code']==held['exit_code']==0 and held['stdout'].strip()==JOB and '--hold' in held['argv'];assert [v for v in dry['argv'] if v!='--test-only']==[v for v in held['argv'] if v!='--hold']
 for v in ('--account=cis260361p','--partition=RM-shared','--qos=rm','--nodes=1','--ntasks=1','--cpus-per-task=26','--mem=48G','--time=00:45:00','--no-requeue','--export=ALL,CUDA_VISIBLE_DEVICES='):assert v in held['argv']
 catalogue_stage=remote('root-genuine-proof-r3-ops/catalogue-stage.json');assert catalogue_stage['job_id']==JOB and catalogue_stage['spooled_sha256']==DISPATCH
 raw=catalogue_stage['held_state'];fields=dict(v.split('=',1) for v in raw.split() if '=' in v);assert fields['JobId']==JOB and fields['JobState']=='PENDING' and fields['Reason']=='JobHeldUser' and fields['RunTime']=='00:00:00' and fields['Requeue']==fields['Restarts']=='0';assert fields['Account']=='cis260361p' and fields['QOS']=='rm' and fields['Partition']=='RM-shared' and fields['TimeLimit']=='00:45:00';assert fields['NumCPUs']==fields['CPUs/Task']=='26' and fields['NumTasks']=='1' and 'gres/gpu' not in fields['TRES'];assert fields['Command'].endswith('/root-proof-dispatch220/dispatch.sh') and fields['WorkDir']==PHYS+'/'+str((W/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime').relative_to(VIRT))
 capture=receipt('root-genuine-proof-r3-ops/catalogue-capture.json');reread=receipt('root-genuine-proof-r3-ops/catalogue-capture-stage-reread.json');job=B/'root-genuine-proof-r2'/('job-'+JOB);binding=read(job/'bindings.json');att=read(job/'transfer-attestation.json');assert binding['actual_job_id']==att['actual_job_id']==JOB and binding['adapter_manifest_sha256']==att['adapter_manifest_sha256']==PACKET
 digest=sha(job/'bindings.json');assert (job/'bindings.sha256').read_bytes() in (digest.encode(),digest.encode()+b'\n');assert binding['transfer_attestation']['sha256']==sha(job/'transfer-attestation.json')
 spec=importlib.util.spec_from_file_location('bound_catalogue_guard',P/'proof_guards.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);rows=g.catalogue_expectations(dict(path=str(job/'transfer-attestation.json'),sha256=sha(job/'transfer-attestation.json')),PACKET,JOB);assert set(rows)==catroutes
 for n,v in rows.items():
  assert v['delta_capture']==capture['current_catalogues'][n]['delta_capture'];assert v['remote']==catalogue_stage['current_catalogues'][n];assert v==reread['current_catalogues'][n];assert Path(n).stat().st_size==v['bytes'] and sha(n)==v['sha256']
 assert att['immutable_deployment_evidence']['sha256']==sha(B/'root-proof-deployment-r3/immutable-deployment-summary.json');assert att['source_before_activation_evidence']==source['source']
 environment=remote('root-genuine-proof-r3-ops/environment-readback.json');assert att['external_runtime_evidence']==environment and environment['sif_sha256']=='f50c8e39dd5e2ac1c1a4bdfd443351cb970513fdb10a572725eb53d7396f8697' and environment['packed_python_sha256']=='5c8e75cf8a297c6bd47595539e4696efb2d2662a9e3afb9741541d155ca9e5fd' and environment['HF_hub_exists'] is True and environment['available_bytes']>=12*1024**3 and environment['numeric_environment_verified_here'] is False and environment['numeric_environment_native_guard_required'] is True
 readback=remote('root-genuine-proof-r3-ops/binding-stage-readback.json');assert readback['job_id']==JOB and all(readback[k] is True for k in ('held_job_confirmed','binding_schema_validated_against_actual_held_job','all_external_references_match','all_four_remote_catalogues_match','output_absent'));assert readback['actual_running_allocation_claimed'] is False
 for n,v in readback['files'].items():assert v['path']==PHYS+'/'+str((job/n).relative_to(VIRT)) and v['sha256']==sha(job/n) and v['bytes']==(job/n).stat().st_size
 assert binding['output_physical']==PHYS+'/'+str((job/'execution').relative_to(VIRT)) and not(job/'execution').exists();assert binding['independent_review']['sha256']=='4baa8564e39248d6c8a5ce32ba8be6d2dde06b69acc78dfc0dd6c5d859347d3a';assert sha(W/'.superpowers/sdd/plan-a2-final-proof-adapter-review219/verdict.json')==binding['independent_review']['sha256']
 for key,name in [('probe_result','probe-result.json'),('probe_host','host-cgroup.json'),('probe_container','container-cgroup.json'),('probe_command','command.json')]:assert binding[key]['path']==source['probe_files'][name]['path'] and binding[key]['sha256']==source['probe_files'][name]['sha256']
 probe=B/'root-preflight-ops-r5/actual-50311864/execution';assert read(probe/'probe-result.json')['container_exit']==0
 for name,v in source['probe_files'].items():assert sha(probe/name)==v['sha256']
 for n in ('bindings.json','bindings.sha256','transfer-attestation.json'):pins[str(job/n)]=dict(sha256=sha(job/n),bytes=(job/n).stat().st_size)
 result=dict(status='READY_ONE_HELD_CPU_SCHEMA_PROOF_RELEASE_ONLY',job=JOB,packet_manifest_sha256=PACKET,dispatcher_sha256=DISPATCH,binding_sha256=digest,transfer_attestation_sha256=sha(job/'transfer-attestation.json'),immutable_routes=1151,prior_match_routes=1144,staged_missing_routes=7,aliases=11,source_files=511,literal_source_links=4,current_catalogues=4,catalogue_snapshots_not_continuous_Delta=True,actual_held_job=True,actual_running_allocation_claimed=False,spooled_dispatch_exact=True,all_remote_binding_files_readback_exact=True,output_absent=True,available_bytes=environment['available_bytes'],numeric_environment_deferred_to_native_job_guards=True,CPU_request=dict(cpus=26,memory_GiB=48,minutes=45,gpus=0,child_seconds=2400,termination_grace_seconds=15),evidence_pins=pins)
 (R/'audit-result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='evidence_pins'},indent=2))
if __name__=='__main__':main()
