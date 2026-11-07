"""Genuine candidate CPU preparation child; project imports occur after binding checks."""
import argparse,gc,json,os,resource,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import common as c
S=P.parent.parent
ADAPTER=P.parent/'prepared-resource-runner278-r2'/'runner.py'


def run_steps(cfg,runtime,adapter,emit,check):
 for name,argv in c.commands(cfg):
  check('before-'+name)
  try:
   def observed(row):
    record=dict(row);record['operation']=name;emit(record)
   result=adapter.produce_native(runtime,argv,observed)
   assert result==0,'nonzero native operation'
  finally:check('after-'+name)


def main(argv=None):
 ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--config-sha256',required=True);a=ap.parse_args(argv)
 path=Path(a.config);assert c.sha(path)==a.config_sha256
 cfg=c.read(path)
 try:c.validate(cfg)
 except ValueError as error:ap.error(str(error))
 assert os.environ.get('SLURM_JOB_ID')==cfg['job_id'] and os.environ.get('SLURM_CLUSTER_NAME')==cfg['cluster']
 assert os.environ.get('SLURM_CPUS_PER_TASK')==str(cfg['cpus'])
 began=time.time();monotonic=time.monotonic();output=Path(cfg['run_root'])/'child';assert output.is_dir()
 canonical=Path(cfg['canonical']);assert not canonical.exists(),'fresh canonical namespace required'
 adapter=c.load(ADAPTER,'candidate311_measurement_adapter')
 c.durable(output/'child-start.json',dict(pid=os.getpid(),argv=sys.argv,python=sys.executable,version=sys.version,
  wrapper_start_seconds=os.environ.get('A3_WRAPPER_START_SECONDS'),child_start_seconds=began,
  process=adapter.process_snapshot(),candidate_only=True,execution_authorized=False))
 records=(output/'native-phases.jsonl').open('x')
 def emit(row):
  records.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n');records.flush();os.fsync(records.fileno())
 result=dict(kind='PROVISIONAL_CANDIDATE_CPU_PRODUCER',candidate_commit=cfg['candidate_commit'],candidate_only=True,
  status='failed',execution_authorized=False,model_loaded=False,config_sha256=a.config_sha256,actual_job_id=cfg['job_id'],actual_cluster=cfg['cluster'])
 runtime=None;source_before=None;native_source=None
 try:
  c.check_packet(cfg);source_before=c.check_sources(cfg)
  sys.path.insert(0,cfg['export']);os.chdir(cfg['export'])
  assert os.environ.get('HF_HOME')=='/work/nvme/beto/swong2' and os.environ.get('HF_HUB_CACHE')=='/work/nvme/beto/swong2/hub'
  from huggingface_hub import constants as hf_constants
  assert hf_constants.HF_HOME==os.environ['HF_HOME'] and hf_constants.HF_HUB_CACHE==os.environ['HF_HUB_CACHE'],'unexpected cache fallback'
  c.durable(output/'cache-namespace.json',dict(HF_HOME=os.environ['HF_HOME'],HF_HUB_CACHE=os.environ['HF_HUB_CACHE'],loaded_HF_HOME=hf_constants.HF_HOME,loaded_HF_HUB_CACHE=hf_constants.HF_HUB_CACHE,constants_origin=hf_constants.__file__))
  from component_analysis import a3_direction_runtime as runtime
  assert runtime._freeze_json is runtime.workload._freeze_json
  native_source=runtime.artifacts.code_hashes()
  c.durable(output/'source-before.json',dict(export=source_before,origins=c.check_origins(cfg['export']),native_code_hashes=native_source,software=dict(numpy=runtime.np.__version__,torch=runtime.torch.__version__)))
  def check(label):
   assert time.time()<float(os.environ['A3_PRODUCER_DEADLINE']),'original whole-child deadline reached'
   c.check_packet(cfg);c.check_sources(cfg,include_inputs=False);c.check_origins(cfg['export'])
   assert runtime.artifacts.code_hashes()==native_source,'native source changed'
   if label=='after-freeze':
    design=runtime.ladder.read_artifact(canonical/'design.json');protocol=design['direction_protocol']
    assert design['injected'] is False and protocol['commit']==cfg['candidate_commit']
    assert design['direction_protocol_sha256']==runtime.ladder.design._hash(protocol)
    del design,protocol;gc.collect()
  run_steps(cfg,runtime,adapter,emit,check)
  start=time.monotonic();inventory=c.inventory_outputs(cfg)
  descriptor=inventory['descriptor']
  assert descriptor['design_reference']==runtime._prepared_file_reference(canonical/'design.json')
  assert descriptor['protocol_reference']==runtime._prepared_file_reference(canonical/'direction_protocol.json')
  assert descriptor['pilot_inventory_reference']==runtime.object_reference(canonical/'inventory'/'prefit')
  c.durable(output/'saved-objects.json',dict(inventory=inventory,wall_seconds=time.monotonic()-start))
  result.update(status='candidate_producer_completed',saved_objects_sha256=c.sha(output/'saved-objects.json'))
 except BaseException as error:
  result.update(error_type=type(error).__name__,error=str(error));raise
 finally:
  records.close();post_error=None
  try:
   c.check_packet(cfg);source_after=c.check_sources(cfg)
   assert source_before is None or source_before==source_after
   if runtime is not None and native_source is not None:
    assert runtime.artifacts.code_hashes()==native_source
    c.durable(output/'source-after.json',dict(export=source_after,origins=c.check_origins(cfg['export']),native_code_hashes=native_source))
   assert c.sha(path)==a.config_sha256 and time.time()<float(os.environ['A3_PRODUCER_DEADLINE'])
  except BaseException as error:post_error=repr(error);result['status']='failed'
  result.update(postcheck_error=post_error,wall_seconds=time.monotonic()-monotonic,process=adapter.process_snapshot(),
   user_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_utime,system_seconds=resource.getrusage(resource.RUSAGE_SELF).ru_stime,
   scope='child lifetime includes imports, fresh freeze/pilot, guards, native publication, independent full reread and final source checks; outer host terminal cost separate')
  c.durable(output/'run_manifest.json',result)
  if post_error:raise RuntimeError(post_error)

if __name__=='__main__':main()
