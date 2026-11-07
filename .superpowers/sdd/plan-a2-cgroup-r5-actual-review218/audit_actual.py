"""Read-only local audit of fetched actual50311864; no Slurm or remote calls."""
import hashlib,importlib.util,json,sys
from pathlib import Path
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');B=W/'.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199';ROOT=B/'root-preflight-ops-r5';ACTUAL=ROOT/'actual-50311864';P=B/'preflight-r5';REVIEW=W/'.superpowers/sdd/plan-a2-cgroup-r5-actual-review218'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def main():
 receipt=read(ROOT/'fetch-50311864.json');assert len(receipt['files'])==8;pins={}
 for n,v in receipt['files'].items():
  p=ACTUAL/n;assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],n;pins[str(p)]=v
 expected_sha='889ee0c986fd392ba1cf00300d93ae46f6714cae10a58175862a3a9ba7a88db7';assert sha(P/'manifest.json')==expected_sha
 for n,d in read(P/'manifest.json').items():assert sha(P/n)==d,n
 intent=read(ACTUAL/'submission-intent.json');submission=read(ACTUAL/'submission-result.json');assert submission['argv']==intent['argv'] and submission['returncode']==0 and submission['output'].strip()=='50311864';argv=submission['argv'];assert argv[-1]==expected_sha and argv[-3].endswith('/preflight-r5/launch.sh') and argv[-2].endswith('/root-cgroup199-r5/execution')
 for option in ('--account=cis260361p','--partition=RM-shared','--qos=rm','--cpus-per-task=26','--mem=48G','--time=00:05:00','--no-requeue'):assert option in argv
 accounting=receipt['accounting'];assert accounting['exit_code']==0 and not accounting['stderr'];rows=[v.split('|') for v in accounting['stdout'].splitlines()[1:]];job=next(v for v in rows if v[0]=='50311864');assert job[1:4]==['COMPLETED','0:0','00:00:05']
 out=ACTUAL/'execution';result=read(out/'probe-result.json');assert result==dict(complete=True,host_exit=0,container_exit=0,host_stderr='',container_stderr='',no_graph=True,no_model=True,proof_admitted=False)
 allocation=read(out/'allocation.json');f=allocation['fields'];cmd=read(out/'command.json')['argv'];assert '--nv' not in cmd and cmd[-1].endswith('/preflight-r5/inner.sh');assert cmd[:2]==['apptainer','exec']
 binds=[cmd[i+1] for i,v in enumerate(cmd) if v=='--bind'];expected_bind='/sys/fs/cgroup:/sys/fs/cgroup:ro,/sys/fs/cgroup/memory:/sys/fs/cgroup/memory:ro';assert expected_bind in binds;assert not any(v.startswith('/sys/fs/cgroup') and v!=expected_bind for v in binds)
 env=dict(cmd[i+1].split('=',1) for i,v in enumerate(cmd) if v=='--env');spec=importlib.util.spec_from_file_location('actual_allocation_helper',P/'allocation_helper.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper);physical_workdir=str(helper.PHYS/helper.R.relative_to(helper.VIRT));helper.validate_allocation(f,env,105853,allocation['host'],physical_workdir,expected_minutes=5);assert f['NumTasks']=='1' and f['JobId']=='50311864'
 host=read(out/'host-cgroup.json');inner=read(out/'container-cgroup.json');assert host['job']==inner['job']=='50311864';assert host['required_194_counter_visible'] is True and inner['required_194_counter_visible'] is True
 assert host['memory_membership_lines']==inner['memory_membership_lines'];assert host['read_errors']==inner['read_errors']=={};assert len(host['records'])==len(inner['records'])==1
 for value in (host,inner):
  record=value['records'][0];assert record['controller']=='v1' and record['membership']=='/slurm/uid_105853/job_50311864/step_batch/task_0' and record['job_scoped'] is True and record['same_as_frozen_worker_path'] is True and record['candidate_path_errors']=={}
  native='/sys/fs/cgroup/memory'+record['membership'];assert record['path']==record['frozen_worker_path']==native
  vals=record['values'];assert int(vals['memory.max_usage_in_bytes'])>=int(vals['memory.usage_in_bytes'])>=0 and int(vals['memory.failcnt'])==0;oom=dict(v.split() for v in vals['memory.oom_control'].splitlines());assert oom['under_oom']==oom['oom_kill']=='0'
 def parse(line):
  left,right=line.split(' - ',1);a=left.split();b=right.split();return dict(id=int(a[0]),parent=int(a[1]),dev=a[2],root=a[3],mountpoint=a[4],mount_options=a[5].split(','),filesystem=b[0],super_options=b[2].split(','),raw=line)
 mounts=[parse(line) for line in inner['memory_mount_lines']];assert len(mounts)==2 and all(v['mountpoint']=='/sys/fs/cgroup/memory' and v['root']=='/' and v['dev']=='0:35' and v['filesystem']=='cgroup' and 'memory' in v['super_options'] for v in mounts)
 parents={v['parent'] for v in mounts};top=[v for v in mounts if v['id'] not in parents];assert len(top)==1;top=top[0];lower=next(v for v in mounts if v['id']==top['parent']);assert top['id']==1682 and lower['id']==1676;assert 'ro' in top['mount_options'] and 'rw' not in top['mount_options'] and 'rw' in lower['mount_options'];assert all('rw' in v['super_options'] for v in mounts)
 summary=dict(status='ACTUAL_R5_DIAGNOSTIC_AUDIT_PASS',job='50311864',packet_manifest_sha256=expected_sha,receipt_sha256=sha(ROOT/'fetch-50311864.json'),all8_fetched_files_match=True,all8_source_members_match=True,actual_account=f['Account'],actual_partition=f['Partition'],actual_qos=f['QOS'],actual_host=allocation['host'],actual_UID=105853,actual_CPUs=26,actual_memory='48G',terminal_state='COMPLETED',terminal_exit='0:0',elapsed_seconds=5,probe_host_exit=0,probe_container_exit=0,command_ordered_parent_then_child_bind=expected_bind,host_container_same_job_and_membership=True,native_worker_path=inner['records'][0]['frozen_worker_path'],host_container_individual_samefile_checks=True,cross_context_directory_inode_recorded=False,required_counters_visible=True,allocation_failure_or_oom_observed=False,container_memory_mount_stack=mounts,top_readonly_mount_id=1682,hidden_writable_mount_id=1676,readonly_interpretation='topmost mount1682 is not parent of another same-location mount; its parent1676 is the hidden lower rw mount; per-superblock rw is distinct',future_live_statvfs_check_observed_in_probe=False,MODEL_LOADED=False,proof_admitted=False,GPU_ADMITTED=False,files=pins)
 (REVIEW/'audit-result.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ('files','container_memory_mount_stack')},indent=2))
if __name__=='__main__':main()
