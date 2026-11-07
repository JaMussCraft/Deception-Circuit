from pathlib import Path
import os,sys,json,hashlib,subprocess,time
P=Path(__file__).resolve().parent;c=json.loads((P/'expected-source.json').read_text());C=Path(c['candidate'])
def check():
 for name,digest in c['files'].items():assert hashlib.sha256((C/name).read_bytes()).hexdigest()==digest,name
 for name,target in c['input_links'].items():assert (C/name).is_symlink() and os.readlink(C/name)==target,name
check();job=os.environ['SLURM_JOB_ID'];raw=subprocess.check_output(['scontrol','show','job',job,'-o'],text=True,timeout=15);facts=dict(x.split('=',1) for x in raw.split() if '=' in x)
assert facts['JobState']=='RUNNING' and facts['Partition'] in ('cpu','cpu-interactive') and facts['NumCPUs']=='4' and facts['NumNodes']=='1'
tres=dict(x.split('=',1) for x in facts.get('AllocTRES',facts.get('TRES','')).split(',') if '=' in x);assert tres['mem'] in ('32G','32768M') and not any(k.startswith('gres/gpu') for k in tres)
assert os.uname().nodename.split('.')[0] in subprocess.check_output(['scontrol','show','hostnames',facts['NodeList']],text=True,timeout=15).split();assert os.environ.get('CUDA_VISIBLE_DEVICES','')==''
sys.path.insert(0,str(C));os.chdir(C)
from component_analysis import a3_direction_workload as workload
assert Path(workload.__file__).resolve()==C/'component_analysis/a3_direction_workload.py'
import pytest
reports=[]
durable=(P/('outcomes-'+job+'-'+sys.argv[1]+'.jsonl')).open('x')
class Outcomes:
 def pytest_runtest_logreport(self,report):
  row=dict(nodeid=report.nodeid,when=report.when,outcome=report.outcome,text=str(report.longrepr) if report.failed else None);reports.append(row)
  if report.when=='call' or report.failed:durable.write(json.dumps(row)+'\n');durable.flush()
started=time.monotonic();code=pytest.main(['--confcutdir='+str(C),'--import-mode=importlib','-q','-p','no:cacheprovider','--basetemp='+str(P/('temp-'+job+'-'+sys.argv[1])),str(C/'tests/test_a3_direction_workload.py'),*[str(C/'tests/test_a3_direction_runtime.py')+'::'+name for name in ('test_validated_inventory_is_deeply_immutable_and_replacement_rejects','test_unsupported_allocation_inventory_or_device_rejects','test_bounded_scenario_rejects_changed_frozen_inventory_before_resume')]],plugins=[Outcomes()])
durable.close()
origins={n:str(Path(m.__file__).resolve()) for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','models','dataset','evaluation','scripts','tests','config') and getattr(m,'__file__',None)}
assert all(Path(path).is_relative_to(C) for path in origins.values()),origins
check();failed={x['nodeid'].split('::')[-1] for x in reports if x['outcome']=='failed' and x['when']=='call'};setup_errors=[x for x in reports if x['outcome']=='failed' and x['when']!='call']
expected={'test_option_a_never_copies_target_only_rows_for_lengths','test_option_a_source_rows_scanned_at_most_three_times_per_group','test_option_a_sender_constant_encoded_and_bounded_once'}
result=dict(kind='option_A_focused_GREEN_evidence',job_id=job,allocation=raw,python=sys.executable,baseline_commit=c['baseline_commit'],pytest_exit=int(code),failed_call_names=sorted(failed),expected_failed_call_names=[],baseline_RED_failure_names=sorted(expected),setup_errors=setup_errors,outcomes=reports,module_origins=origins,source_unchanged=True,production_only_expected_changes=True,elapsed_seconds=time.monotonic()-started,no_scientific_model_stage_requested=True)
(P/('result-'+job+'-'+sys.argv[1]+'.json')).write_text(json.dumps(result,indent=2)+'\n');assert int(code)==0 and not setup_errors and not failed,(code,failed,setup_errors)
print('FOCUSED_OPTION_A_GREEN_COMPLETE',flush=True)
