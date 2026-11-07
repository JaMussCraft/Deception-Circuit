"""Actual run_stage boundary with external metadata/process I/O replaced."""
import importlib.util,json,pathlib,tempfile,types
from unittest import mock
P=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239')
spec=importlib.util.spec_from_file_location('review244runner',str(P/'runner.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
clock={'now':1000.};observed=[]
c=dict(actual_CPU_job_id='123',expected_account='fixture-cpu',expected_qos='fixture',python='/no-process')
s=types.SimpleNamespace(allocation=lambda _:dict(end_epoch=1900.),terminate=lambda *a:None)
class StopAtPopen(Exception):pass
def packet(_):clock['now']=1250.
def popen(*a,**kw):observed.append(clock['now']);raise StopAtPopen()
with tempfile.TemporaryDirectory() as td:
 root=pathlib.Path(td)
 with mock.patch.object(m.time,'time',lambda:clock['now']),mock.patch.object(m.time,'monotonic',lambda:clock['now']),mock.patch.object(m,'metrics',lambda *a:{}),mock.patch.object(m,'parameters',lambda *a:{}),mock.patch.object(m,'child_command',lambda *a:['NO_PROCESS']),mock.patch.object(m,'read_ref',lambda _:c),mock.patch.object(m,'packet',packet),mock.patch.object(m.subprocess,'Popen',popen):
  try:m.run_stage(c,dict(path='/fixture',sha256='a'*64),'fresh',root,2000.,None,s)
  except StopAtPopen:pass
assert observed==[1250.]
print(json.dumps(dict(reviewed_fresh_deadline=1240.,clock_after_final_preflight=1250.,Popen_boundary_reached=observed,actual_processes_started=0,scope='Actual run_stage; only external readonly metadata and process seams replaced. No native/scientific data/model run.'),indent=2))
