"""Actual container cgroup visibility barrier; immutable worker follows by exec."""
import argparse,json,os,sys,time
from pathlib import Path
import proof_guards as g
from host_supervisor import observe_cgroup,select_cgroup
P=Path(__file__).resolve().parent
def observe_effective_readonly(inner):
 """Fresh lookup of the selected frozen worker path; never write a counter."""
 path=Path(inner['frozen_worker_path']);assert path.is_absolute() and inner['same_as_frozen_worker_path'] is True
 expected=inner['live_directory_stat']
 before=path.stat();assert [before.st_dev,before.st_ino,before.st_mode]==expected,'native path replaced before readonly lookup'
 assert path.samefile(inner['path']),'selected/native path no longer samefile'
 flags=os.statvfs(str(path)).f_flag;bit=os.ST_RDONLY
 assert type(flags) is int and type(bit) is int and bit>0,'missing/invalid actual readonly flags'
 after=path.stat();assert [after.st_dev,after.st_ino,after.st_mode]==expected and path.samefile(inner['path']),'native path replaced during readonly lookup'
 return dict(path=str(path),f_flag=flags,ST_RDONLY=bit,read_only=bool(flags & bit),live_directory_stat=expected)
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--deadline-monotonic',required=True,type=float);a=ap.parse_args()
out=Path(a.output);stage='entry-cgroup'
try:
 assert out.is_absolute() and out.is_dir();g.packet(a.manifest_sha256);assert g.sha(P/'proof_worker.py')=='4dfb62711dfe598041db9e836e8f1589dc05c54c3b649f007b625f8a1a34669e'
 assert os.environ['A2_CPU_PACKET_SHA256']==a.manifest_sha256;g.current_catalogues()
 before=g.read(out/'host-cgroup-before.json');actual=observe_cgroup();g.write(out/'container-cgroup-observation.json',actual);job=os.environ['SLURM_JOB_ID'];host=select_cgroup(before,job);inner=select_cgroup(actual,job)
 assert inner['controller']==host['controller'] and inner['membership']==host['membership'] and inner['live_directory_stat']==host['live_directory_stat'],'actual host/container cgroup object differs'
 stage='entry-effective-readonly';readonly=observe_effective_readonly(inner);g.write(out/'container-cgroup-readonly.json',readonly)
 assert readonly['read_only'] is True,'actual frozen worker path is not effectively readonly'
 assert time.monotonic()<a.deadline_monotonic
 g.write(out/'container-cgroup-entry.json',dict(worker_entry_permitted=True,job=job,packet_manifest_sha256=a.manifest_sha256,controller=inner['controller'],membership=inner['membership'],same_actual_directory_stat=True,effective_readonly=readonly,no_graph_yet=True,no_model=True,GPU_ADMITTED=False))
 os.execv(sys.executable,[sys.executable,'-B',str(P/'proof_worker.py'),'--output',str(out),'--manifest-sha256',a.manifest_sha256,'--deadline-monotonic',str(a.deadline_monotonic)])
except BaseException as e:
 if out.is_dir():g.write(out/'FAILED-container-entry.json',dict(complete=False,stage=stage,error=repr(e),MODEL_LOADED=False,GPU_ADMITTED=False))
 raise
