from pathlib import Path
import datetime, importlib.util, os
from types import SimpleNamespace
import pytest
spec=importlib.util.spec_from_file_location('cpu_aggregation_allocation',Path(__file__).with_name('allocation_facts.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
@pytest.fixture
def allocation(monkeypatch,tmp_path):
 for name in a.ENV_NAMES:monkeypatch.delenv(name,raising=False)
 monkeypatch.setenv('SLURM_JOB_ID','999');monkeypatch.setenv('SLURM_CLUSTER_NAME','delta');monkeypatch.setenv('SLURM_CPUS_PER_TASK','4')
 fields=dict(JobId='999',JobState='RUNNING',UserId='test('+str(os.getuid())+')',AllocTRES='cpu=4,mem=32G,node=1',NumNodes='1',Account='bimc-delta-cpu',Partition='cpu',WorkDir=str(tmp_path),NodeList=os.uname().nodename,TimeLimit='02:05:00',EndTime=(datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=3)).replace(tzinfo=None).isoformat())
 def run(command,**kwargs):return SimpleNamespace(stdout=' '.join(k+'='+v for k,v in fields.items()) if '-o' in command else os.uname().nodename+'\n')
 monkeypatch.setattr(a.subprocess,'run',run);return tmp_path,fields

def test_exact_authorized_normal_cpu_bound_accepts(allocation):
 p,f=allocation;result=a.read_current(p,minimum_remaining_seconds=7275);assert result['time_limit_seconds']==7500 and result['actual_GPU_count']==0

@pytest.mark.parametrize('key,value',[('TimeLimit','02:06:00'),('TimeLimit','02:04:00'),('Partition','cpu-interactive'),('AllocTRES','cpu=4,mem=32G,node=1,gres/gpu=1'),('AllocTRES','cpu=4,mem=64G,node=1'),('JobState','PENDING')])
def test_refuses_wrong_bound_or_resource(allocation,key,value):
 p,f=allocation;f[key]=value
 with pytest.raises(AssertionError):a.read_current(p)
