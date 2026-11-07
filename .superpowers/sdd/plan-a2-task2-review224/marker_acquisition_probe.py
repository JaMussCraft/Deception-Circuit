"""Real supervisor orchestration with external metadata/process seams only."""
import hashlib,importlib.util,json,pathlib,tempfile
from unittest import mock
S=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd');C=S/'plan-a2-full-score-operational186/candidate/cpu'
sp=importlib.util.spec_from_file_location('marker224',str(C/'supervisor.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x));return dict(path=str(p),sha256=sha(p))
class NoActualProcess(Exception):pass
with tempfile.TemporaryDirectory() as td:
 root=pathlib.Path(td);marker=root/'WAITING.json';request=root/'request.json';runtime=m.W+'/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime';main=m.W+'/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1'
 waiting=dict(phase='full_score',job_id='456',source_commit=m.SOURCE,bound_config_sha256='6'*64,packet_manifest_sha256='5'*64,groups_file_sha256='2'*64,bank_file_sha256='3'*64,bank_manifest_sha256='4'*64,requested_at=1000.,deadline_unix=1140.)
 save(marker,waiting);marker_sha=sha(marker)
 base=json.loads((C/'parameters.template.json').read_text());base.update(phase='full_score',accepted_source_commit=m.SOURCE,accepted_runtime=runtime,new_g3_output=main,frozen_G3_sha256='2'*64,bank_file_sha256='3'*64,bank_manifest_sha256='4'*64)
 base_ref=save(root/'base.json',base)
 c=dict(phase='full_score',source_commit=m.SOURCE,standing_CPU_job_id='123',packet_manifest_sha256='1'*64,GPU_packet_manifest_sha256='5'*64,frozen_G3_sha256='2'*64,bank_file_sha256='3'*64,bank_manifest_sha256='4'*64,child_cap_seconds=240,CPU_finish_margin_seconds=20,publication_margin_seconds=15,kill_grace_seconds=5,duration_seconds=1000,evidence_output=str(root/'evidence'),base_parameters=base_ref,runtime=runtime,frozen_G3_root=main,python='/no/process/started')
 r=dict(phase='full_score',standing_CPU_job_id='123',standing_packet_manifest_sha256='1'*64,accepted_source_commit=m.SOURCE,frozen_G3_sha256='2'*64,bank_file_sha256='3'*64,bank_manifest_sha256='4'*64,GPU_packet_manifest_sha256='5'*64,actual_future_GPU_job_id='456',final_GPU_bound_config_sha256='6'*64,root_trigger_issued_at=1005.,GPU_WAITING_requested_at=1000.,GPU_WAITING_marker_path=str(marker),GPU_WAITING_marker_sha256=marker_sha)
 save(request,r);config_ref=save(root/'config.json',c);real_read=pathlib.Path.read_bytes;captured={}
 def swapped_read(path):
  raw=real_read(path)
  if path==marker:
   swapped=dict(waiting,deadline_unix=1300.);return json.dumps(swapped).encode()
  return raw
 def stop(command,**kwargs):captured.update(json.loads(pathlib.Path(command[3]).read_text()));raise NoActualProcess()
 with mock.patch.object(m,'validate_config',lambda c:None),mock.patch.object(m,'packet',lambda c:None),mock.patch.object(m,'allocation',lambda c:dict(job_id='123',end_epoch=5000.)),mock.patch.object(m.time,'time',lambda:1010.),mock.patch.object(pathlib.Path,'read_bytes',swapped_read),mock.patch.object(m.subprocess,'Popen',stop):
  try:m.supervise_once(c,request,config_ref)
  except NoActualProcess:pass
 assert captured['phase_deadline_unix']==1250. and sha(marker)==marker_sha
 print(json.dumps(dict(actual_original_marker_deadline=1140.,original_deadline_minus_publication_margin=1125.,parameter_deadline_at_Popen_boundary=captured['phase_deadline_unix'],original_marker_hash_still_matches=True,actual_processes_started=0,scope='Guard/allocation metadata seams replaced; demonstrates hash/read split only, no genuine proof or source/model execution'),indent=2))
