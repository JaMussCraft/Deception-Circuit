import copy
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0,'/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
from component_analysis import a3_direction_runtime as r
from tests.test_a3_direction_runtime import _authority_case

def scheduler_text(**changes):
    start=int(time.time())-30
    stamp=lambda n:datetime.fromtimestamp(n,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    fields=dict(JobId='100',JobState='RUNNING',Account='a',Partition='p',TimeLimit='00:12:00',StartTime=stamp(start),EndTime=stamp(start+720),AllocTRES='cpu=8,mem=64G,node=1,billing=1,gres/gpu=1,gres/gpu:h200=1',NumCPUs='8',MinMemoryNode='64G',WorkDir='/output')
    fields.update(changes)
    return ' '.join(k+'='+v for k,v in fields.items())

def production_lease(monkeypatch,text):
    import subprocess
    def transport(argv,**kw):
        assert argv==['scontrol','-o','show','job','100']
        assert kw['env']['TZ']=='UTC'
        return SimpleNamespace(stdout=text)
    monkeypatch.setattr(subprocess,'run',transport)
    monkeypatch.setenv('SLURM_JOB_ID','100');monkeypatch.setenv('DC_CLUSTER','delta')
    return r.read_current_allocation({'actual_entry':{'job_id':'100'}},injected=False)

def actual():return dict(job_id='100',cluster='delta',account='a',partition='p',gpus=1,requested_minutes=12,output_dir='/output')
def inventory():return dict(hardware={'gpu':'h200','count':1},storage_requirements={'tiers':{'host_ram':32*1024**3}})

def test_real_parser_transport_positive(monkeypatch):
    lease=production_lease(monkeypatch,scheduler_text())
    assert lease['gpu_types']==['h200']
    r.validate_allocation(lease,actual(),inventory(),'/output',injected=False)

@pytest.mark.parametrize('change',[{'WorkDir':'/wrong'},{'AllocTRES':'cpu=8,mem=64G,node=1,gres/gpu=1,gres/gpu:a40=1'},{'AllocTRES':'cpu=1,mem=1M,node=1,gres/gpu=1,gres/gpu:h200=1','NumCPUs':'1','MinMemoryNode':'1M'}])
def test_observed_resource_mismatch_is_accepted(monkeypatch,change):
    lease=production_lease(monkeypatch,scheduler_text(**change))
    assert r.validate_allocation(lease,actual(),inventory(),'/output',injected=False) is lease

@pytest.mark.parametrize('change',[{'JobState':'PENDING'},{'TimeLimit':'UNLIMITED'},{'AllocTRES':'cpu=8,mem=64G,node=1'}])
def test_real_parser_rejects_invalid(monkeypatch,change):
    with pytest.raises(ValueError):production_lease(monkeypatch,scheduler_text(**change))

def test_production_rejects_injected_reader():
    with pytest.raises(ValueError):r.read_current_allocation({'actual_entry':actual()},injected=False,reader=lambda _:None)

def test_observed_cached_key_mutation_is_accepted(tmp_path):
    inv=dict(identity={'injected':True,'commit':'a'*40},inventory_sha256='c'*64,phase='M2',expected_keys=[{'id':'original'}],finish_reserve_seconds=10)
    _,ledger,inv,reservation,_,_=_authority_case(tmp_path,inventory=inv)
    context=r.make_authority_context(reservation,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)
    inv['expected_keys'][0]['id']='not-in-original-upper-inventory'
    result=r.validate_reservation(reservation,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context)
    assert result['execution_authorized'] is True

def test_observed_symlink_directory_child_edit_is_accepted(tmp_path):
    target=tmp_path/'target';target.mkdir();child=target/'payload.json';child.write_text('old')
    link=tmp_path/'immutable';link.symlink_to(target,target_is_directory=True)
    witness=r._make_file_witness([link]);old=child.stat();child.write_text('new');os.utime(child,ns=(old.st_atime_ns,old.st_mtime_ns))
    r._check_file_witness(witness)

def test_observed_full_context_symlink_upper_corruption_is_accepted(tmp_path):
    _,ledger,inv,reservation,_,_=_authority_case(tmp_path)
    link=tmp_path/'upper-link';link.symlink_to(tmp_path/'upper',target_is_directory=True)
    payload=r.read_object(reservation);payload['upper_inventory_path']=str(link)
    reservation=tmp_path/'linked-reservation';r.publish_object(reservation,payload)
    context=r.make_authority_context(reservation,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)
    child=tmp_path/'upper'/'payload.json';old=child.stat();text=child.read_text();child.write_text(text.replace('"phase": "M2"','"phase": "M4"'));os.utime(child,ns=(old.st_atime_ns,old.st_mtime_ns))
    with pytest.raises(ValueError):r.read_object(tmp_path/'upper')
    result=r.validate_reservation(reservation,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context)
    assert result['execution_authorized'] is True
