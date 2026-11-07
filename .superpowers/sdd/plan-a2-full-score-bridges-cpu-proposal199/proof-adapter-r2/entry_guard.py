"""Actual container cgroup visibility barrier; immutable worker follows by exec."""
import argparse,json,os,sys,time
from pathlib import Path
import proof_guards as g
from host_supervisor import observe_cgroup,select_cgroup
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--manifest-sha256',required=True);ap.add_argument('--deadline-monotonic',required=True,type=float);a=ap.parse_args()
out=Path(a.output);stage='entry-cgroup'
try:
 assert out.is_absolute() and out.is_dir();g.packet(a.manifest_sha256);assert g.sha(P/'proof_worker.py')=='4dfb62711dfe598041db9e836e8f1589dc05c54c3b649f007b625f8a1a34669e'
 before=g.read(out/'host-cgroup-before.json');actual=observe_cgroup();g.write(out/'container-cgroup-observation.json',actual);job=os.environ['SLURM_JOB_ID'];host=select_cgroup(before,job);inner=select_cgroup(actual,job)
 assert inner['controller']==host['controller'] and inner['membership']==host['membership'] and inner['live_directory_stat']==host['live_directory_stat'],'actual host/container cgroup object differs'
 assert time.monotonic()<a.deadline_monotonic
 g.write(out/'container-cgroup-entry.json',dict(worker_entry_permitted=True,job=job,packet_manifest_sha256=a.manifest_sha256,controller=inner['controller'],membership=inner['membership'],same_actual_directory_stat=True,no_graph_yet=True,no_model=True,GPU_ADMITTED=False))
 os.execv(sys.executable,[sys.executable,'-B',str(P/'proof_worker.py'),'--output',str(out),'--manifest-sha256',a.manifest_sha256,'--deadline-monotonic',str(a.deadline_monotonic)])
except BaseException as e:
 if out.is_dir():g.write(out/'FAILED-container-entry.json',dict(complete=False,stage=stage,error=repr(e),MODEL_LOADED=False,GPU_ADMITTED=False))
 raise
