import copy
import json
import operator
import os
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
import pytest
sys.path.insert(0,'/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
from component_analysis import a3_direction_runtime as r
from tests.test_a3_direction_runtime import _authority_case,_production_allocation_fixture


def lease_transport(monkeypatch,*,generic=False,memory='64G',nodefacts=None,**changes):
    _,contract,_,actual,inv=_production_allocation_fixture()
    start=int(time.time())-30;stamp=lambda n:datetime.fromtimestamp(n,timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    fields=dict(JobId='100',JobState='RUNNING',Account='a',Partition='p',TimeLimit='00:12:00',StartTime=stamp(start),EndTime=stamp(start+720),AllocTRES='cpu=8,mem='+memory+',gres/gpu=1'+('' if generic else ',gres/gpu:h200=1'),NumCPUs='8',WorkDir=contract['scheduler_work_dir'],NodeList='node01')
    fields.update(changes);calls=[]
    def transport(argv,**kw):
        calls.append(argv);assert kw['env']['TZ']=='UTC'
        if argv==['scontrol','-o','show','job','100']:return SimpleNamespace(stdout=' '.join(k+'='+v for k,v in fields.items()))
        assert argv==['scontrol','-o','show','node','node01']
        return SimpleNamespace(stdout=nodefacts or 'NodeName=node01 Gres=gpu:h200:8(S:0-3) CfgTRES=cpu=128,mem=1000G,gres/gpu=8')
    import subprocess
    monkeypatch.setattr(subprocess,'run',transport);monkeypatch.setenv('SLURM_JOB_ID','100');monkeypatch.setenv('DC_CLUSTER','delta')
    lease=r.read_current_allocation({'actual_entry':actual},injected=False)
    return lease,contract,actual,inv,calls

@pytest.mark.parametrize('generic',[False,True])
@pytest.mark.parametrize('memory,expected',[('64G',64*1024**3),('65536M',64*1024**3),('1T',1024**4),('65536',65536*1024**2)])
def test_production_transport_positive_and_memory_units(monkeypatch,generic,memory,expected):
    lease,contract,actual,inv,calls=lease_transport(monkeypatch,generic=generic,memory=memory)
    assert lease['memory_bytes']==expected
    assert r.validate_allocation(lease,actual,inv,'/output',injected=False,allocation_contract=contract) is lease
    assert len(calls)==(2 if generic else 1)

@pytest.mark.parametrize('changes',[{'WorkDir':'/wrong'},{'AllocTRES':'cpu=8,mem=64G,gres/gpu=1,gres/gpu:a40=1'},{'AllocTRES':'cpu=1,mem=64G,gres/gpu=1,gres/gpu:h200=1','NumCPUs':'1'},{'AllocTRES':'cpu=8,mem=1M,gres/gpu=1,gres/gpu:h200=1'},{'AllocTRES':'cpu=8,gres/gpu=1,gres/gpu:h200=1'},{'NumCPUs':'4'},{'WorkDir':'relative'}])
def test_original_production_resource_gaps_reject(monkeypatch,changes):
    with pytest.raises(ValueError):
        lease,contract,actual,inv,_=lease_transport(monkeypatch,**changes)
        r.validate_allocation(lease,actual,inv,'/output',injected=False,allocation_contract=contract)

@pytest.mark.parametrize('nodefacts',['NodeName=node01 Gres=gpu:a40:4','NodeName=node01 Gres=gpu:8','NodeName=node01 Gres=gpu:h200:4,gpu:a40:4','NodeName=node01 Gres=gpu:h200:8\nNodeName=node02 Gres=gpu:a40:4'])
def test_generic_wrong_untyped_heterogeneous_gpu_reject(monkeypatch,nodefacts):
    with pytest.raises(ValueError):
        lease,contract,actual,inv,_=lease_transport(monkeypatch,generic=True,nodefacts=nodefacts)
        r.validate_allocation(lease,actual,inv,'/output',injected=False,allocation_contract=contract)


def inventory_context(tmp_path):
    inv=dict(identity={'injected':True,'commit':'a'*40},inventory_sha256='c'*64,phase='M2',expected_keys=[{'id':'original'}],finish_reserve_seconds=10,shards=[{'ids':['original']}],hardware={'gpu':'injected-cpu','count':1},storage_requirements={'tiers':{'host_ram':0}})
    _,ledger,inv,path,_,_=_authority_case(tmp_path,inventory=inv)
    context=r.make_authority_context(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)
    return ledger,inv,path,context

DICT_MUTATORS=[lambda d:d.__setitem__('id','outside'),lambda d:d.__delitem__('id'),lambda d:d.clear(),lambda d:d.pop('id'),lambda d:d.popitem(),lambda d:d.setdefault('outside',1),lambda d:d.update(id='outside'),lambda d:operator.ior(d,{'id':'outside'})]
LIST_MUTATORS=[lambda v:v.__setitem__(0,{'id':'outside'}),lambda v:v.__setitem__(slice(None),[]),lambda v:v.__delitem__(0),lambda v:v.append({}),lambda v:v.extend([{}]),lambda v:v.insert(0,{}),lambda v:v.pop(),lambda v:v.remove(v[0]),lambda v:v.clear(),lambda v:v.reverse(),lambda v:v.sort(key=str),lambda v:operator.iadd(v,[{}]),lambda v:operator.imul(v,0)]
@pytest.mark.parametrize('mutate',DICT_MUTATORS)
def test_frozen_nested_dict_public_mutators_reject(tmp_path,mutate):
    ledger,inv,path,context=inventory_context(tmp_path)
    with pytest.raises(TypeError):mutate(inv['expected_keys'][0])
    assert r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context)['execution_authorized']
@pytest.mark.parametrize('mutate',LIST_MUTATORS)
def test_frozen_key_list_public_mutators_reject(tmp_path,mutate):
    _,inv,_,_=inventory_context(tmp_path)
    with pytest.raises(TypeError):mutate(inv['expected_keys'])
@pytest.mark.parametrize('field,value',[('expected_keys',[{'id':'outside'}]),('shards',[]),('hardware',{'gpu':'a40','count':1}),('storage_requirements',{}),('extra','outside')])
def test_replaced_or_extended_top_level_inventory_rejects(tmp_path,field,value):
    ledger,inv,path,context=inventory_context(tmp_path);inv[field]=value
    with pytest.raises(ValueError):r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context)

@pytest.mark.parametrize('mode',['child','external','missing','replace','cycle','same_tick'])
def test_byte_witness_symlink_tree_and_external_content_reject(tmp_path,monkeypatch,mode):
    root=tmp_path/'root';root.mkdir();target=tmp_path/'target';target.mkdir();external=tmp_path/'external.npy';external.write_bytes(b'12345678')
    child=target/'payload';child.write_bytes(b'12345678');(root/'directory').symlink_to(target,target_is_directory=True);(root/'array.npy').symlink_to(external)
    if mode=='same_tick':
        # Hold all observed metadata constant to isolate the streamed byte witness.
        original=r._stat_identity;cache={}
        monkeypatch.setattr(r,'_stat_identity',lambda p:cache.setdefault(str(p),original(p)))
    witness=r._make_file_witness([root]);r._check_file_witness(witness)
    if mode in ('child','same_tick'):changed=child;old=changed.stat();changed.write_bytes(b'87654321');os.utime(changed,ns=(old.st_atime_ns,old.st_mtime_ns))
    elif mode=='external':external.write_bytes(b'87654321')
    elif mode=='missing':external.unlink()
    elif mode=='replace':replacement=tmp_path/'replacement';replacement.write_bytes(b'12345678');replacement.replace(external)
    else:(target/'cycle').symlink_to(root,target_is_directory=True)
    with pytest.raises(ValueError):r._check_file_witness(witness)

def test_full_context_symlink_corrupted_upper_rejects(tmp_path):
    _,ledger,inv,path,_,_=_authority_case(tmp_path);link=tmp_path/'upper-link';link.symlink_to(tmp_path/'upper',target_is_directory=True)
    reservation=r.read_object(path);reservation['upper_inventory_path']=str(link);path=tmp_path/'linked-reservation';r.publish_object(path,reservation)
    context=r.make_authority_context(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None)
    child=tmp_path/'upper'/'payload.json';old=child.stat();child.write_text(child.read_text().replace('"phase": "M2"','"phase": "M4"'));os.utime(child,ns=(old.st_atime_ns,old.st_mtime_ns))
    with pytest.raises(ValueError):r.read_object(tmp_path/'upper')
    with pytest.raises(ValueError):r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context)

@pytest.mark.parametrize('target',['dict','list'])
def test_residual_public_reinitialization_mutates_cached_inventory(tmp_path,target):
    ledger,inv,path,context=inventory_context(tmp_path)
    if target=='dict':inv['expected_keys'][0].__init__(id='outside')
    else:inv['expected_keys'].__init__([{'id':'outside'}])
    assert inv['expected_keys'][0]['id']=='outside'
    result=r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context)
    assert result['execution_authorized'] is True

@pytest.mark.parametrize('damage',['missing','replaced','modified'])
def test_external_numeric_backing_cache_rejects_change(tmp_path,damage):
    import numpy as np
    backing=tmp_path/'numeric';backing.mkdir();path=backing/'axis.npy';np.save(path,np.eye(2,dtype=np.float32),allow_pickle=False);r.artifacts._finish(backing)
    profile=dict(model='tiny',model_revision='tiny-revision',source_sha256='a'*64)
    reference=r.pipeline._bundle_byte_reference(backing)
    proof=r._numeric_backing_proof(backing,reference,profile,injected=True)
    assert proof is r._numeric_backing_proof(backing,reference,profile,injected=True)
    if damage=='missing':path.unlink()
    elif damage=='replaced':replacement=tmp_path/'replacement.npy';replacement.write_bytes(path.read_bytes());replacement.replace(path)
    else:
        old=path.stat();data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data);os.utime(path,ns=(old.st_atime_ns,old.st_mtime_ns))
    with pytest.raises(ValueError):r._numeric_backing_proof(backing,reference,profile,injected=True)

@pytest.mark.parametrize('mode',['valid','lower_cpu','lower_memory'])
def test_full_admission_anchored_contract_rejects_reservation_lowering(tmp_path,mode):
    _,contract,lease,actual,base=_production_allocation_fixture()
    inv=dict(kind='a3_direction_inventory',identity={'injected':True,'commit':'a'*40},inventory_sha256='c'*64,phase='M2',expected_keys=[],finish_reserve_seconds=10,hardware=base['hardware'],storage_requirements=base['storage_requirements'])
    _,ledger,inv,path,_,_=_authority_case(tmp_path,inventory=inv)
    admission=r.read_object(tmp_path/'admission');admission.pop('admission_sha256');admission['allocation_contract']=contract;admission['admission_sha256']=r.workload.digest(admission)
    a=tmp_path/'contract-admission';r.publish_object(a,admission)
    mapping=r.read_object(tmp_path/'current-map');mapping['original_admission_paths']=[str(a)];mapping['entries'][0]['reservation_lineage']['admission_sha256']=admission['admission_sha256'];mp=tmp_path/'contract-map';r.publish_object(mp,mapping)
    ledger=r.normalize_ledger(mp,identity=inv['identity'],injected=True)
    reservation=r.read_object(path);reservation.update(admission_path=str(a),admission_reference=r.object_reference(a),admission_sha256=admission['admission_sha256'],allocation_contract=copy.deepcopy(contract))
    if mode=='lower_cpu':reservation['allocation_contract']['cpus']=1
    if mode=='lower_memory':reservation['allocation_contract']['memory_bytes']=1
    path=tmp_path/'contract-reservation';r.publish_object(path,reservation)
    def validate():return r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:None,require_allocation=False)
    if mode=='valid':assert validate()['execution_authorized'] is False
    else:
        with pytest.raises(ValueError):validate()

@pytest.mark.parametrize('value,replacement',[({}, {'outside':1}),([], [{'id':'outside'}])])
def test_residual_empty_frozen_container_can_be_reinitialized(value,replacement):
    frozen=r._freeze_json(value)
    frozen.__init__(replacement)
    assert frozen==replacement
