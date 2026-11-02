import copy
import json
import operator
import sys
from pathlib import Path
import pytest
sys.path.insert(0,'/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
from component_analysis import a3_direction_runtime as r
from tests.test_a3_direction_runtime import _authority_case


def context_fixture(tmp_path,key):
    inv=dict(identity={'injected':True,'commit':'a'*40},inventory_sha256='c'*64,phase='M2',expected_keys=[key],finish_reserve_seconds=10)
    _,ledger,inv,path,_,_=_authority_case(tmp_path,inventory=inv)
    before=json.loads(json.dumps(inv));calls=[]
    context=r.make_authority_context(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,inventory_validator=lambda _:calls.append(1))
    return ledger,inv,path,context,before,calls

@pytest.mark.parametrize('target',['dict','same_length_list','empty_dict','empty_list'])
def test_full_api_reinitialization_rejects_and_unchanged_reuse_survives(tmp_path,target):
    key={} if target=='empty_dict' else {'ids':[]} if target=='empty_list' else {'id':'original'}
    ledger,inv,path,context,before,calls=context_fixture(tmp_path,key)
    container=inv['expected_keys'] if target=='same_length_list' else inv['expected_keys'][0]['ids'] if target=='empty_list' else inv['expected_keys'][0]
    replacement=[{'id':'outside'}] if target=='same_length_list' else ['outside'] if target=='empty_list' else {'id':'outside'}
    with pytest.raises(TypeError):container.__init__(replacement)
    assert json.loads(json.dumps(inv))==before
    result=r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context,inventory_validator=lambda _:pytest.fail('full immutable proof reconstructed'))
    assert result['execution_authorized'] is True and calls==[1]

@pytest.mark.parametrize('value',[{},[],{'id':'original'},[{'id':'original'}]])
@pytest.mark.parametrize('attack',['setattr','delattr','reinit_empty','reinit_data'])
def test_sealed_container_initialization_and_attribute_reset_reject(value,attack):
    frozen=r._freeze_json(value);before=json.loads(json.dumps(frozen))
    assert frozen._initialized is True and not hasattr(frozen,'__dict__')
    with pytest.raises(TypeError):
        if attack=='setattr':frozen._initialized=False
        elif attack=='delattr':del frozen._initialized
        elif attack=='reinit_empty':frozen.__init__()
        else:frozen.__init__({'outside':1} if isinstance(frozen,dict) else ['outside'])
    assert json.loads(json.dumps(frozen))==before

@pytest.mark.parametrize('constructor',['direct_dict','direct_list','mapping_subclass','sequence_subclass','tuple'])
def test_construction_owns_nested_json_and_preserves_serialization(constructor):
    original={'id':'original','nested':[{'values':[1,2]}]}
    if constructor=='direct_dict':frozen=r._FrozenJSONDict(child=original)
    elif constructor=='direct_list':frozen=r._FrozenJSONList([original])
    elif constructor=='mapping_subclass':
        class Mapping(dict):pass
        frozen=r._freeze_json(Mapping(child=original))
    elif constructor=='sequence_subclass':
        class Sequence(list):pass
        frozen=r._freeze_json(Sequence([original]))
    else:frozen=r._freeze_json((original,))
    child=frozen['child'] if isinstance(frozen,dict) else frozen[0]
    original['id']='outside';original['nested'][0]['values'][0]=999
    assert child['id']=='original' and child['nested'][0]['values']==[1,2]
    with pytest.raises(TypeError):child.__init__(id='outside')
    with pytest.raises(TypeError):child['nested'][0]['values'].append(3)
    assert copy.copy(frozen) is frozen and copy.deepcopy(frozen) is frozen
    assert json.loads(json.dumps(frozen))==({'child':{'id':'original','nested':[{'values':[1,2]}]}} if isinstance(frozen,dict) else [{'id':'original','nested':[{'values':[1,2]}]}])

@pytest.mark.parametrize('typ',[r._FrozenJSONDict,r._FrozenJSONList])
def test_uninitialized_exact_frozen_inputs_are_normalized_and_sealed(typ):
    raw=typ.__new__(typ)
    frozen=r._freeze_json(raw)
    assert frozen is not raw and frozen._initialized is True
    with pytest.raises(TypeError):frozen.__init__({'outside':1} if typ is r._FrozenJSONDict else ['outside'])
    raw.__init__({'outside':1} if typ is r._FrozenJSONDict else ['outside'])
    assert frozen==({} if typ is r._FrozenJSONDict else [])

@pytest.mark.parametrize('field,value',[('expected_keys',[{'id':'outside'}]),('phase','M4'),('extra',1)])
def test_top_level_replacement_still_rejects(tmp_path,field,value):
    ledger,inv,path,context,_,_=context_fixture(tmp_path,{'id':'original'});inv[field]=value
    with pytest.raises(ValueError):r.validate_reservation(path,ledger=ledger,inventory=inv,work_dir='/output',injected=True,authority_context=context)

@pytest.mark.parametrize('target',['dict_update','dict_ior','dict_setitem','list_iadd','list_imul','list_slice','list_append'])
def test_common_public_mutators_remain_blocked(target):
    frozen=r._freeze_json({'k':[{'id':'original'}]})
    with pytest.raises(TypeError):
        if target=='dict_update':frozen['k'][0].update(id='outside')
        elif target=='dict_ior':operator.ior(frozen['k'][0],{'id':'outside'})
        elif target=='dict_setitem':frozen['k'][0]['id']='outside'
        elif target=='list_iadd':operator.iadd(frozen['k'],[{}])
        elif target=='list_imul':operator.imul(frozen['k'],0)
        elif target=='list_slice':frozen['k'][:]=[]
        else:frozen['k'].append({})
