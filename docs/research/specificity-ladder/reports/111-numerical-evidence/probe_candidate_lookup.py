"""Model-free call-count fixture executing the frozen candidate loop AST.

No packing proof is validated or forged here: fake cache entries and witness
callbacks count accesses only. Results establish control flow, not authority.
"""
import ast,inspect,json,os
from pathlib import Path
from types import SimpleNamespace
from component_analysis import a3_direction_runtime as r
from tests.test_a3_direction_workload import fixture

tree=ast.parse(inspect.getsource(r.score_runtime_shard))
loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='path' and isinstance(n.iter,ast.Name) and n.iter.id=='measured_paths')
module=ast.Module(body=[loop],type_ignores=[]);ast.fix_missing_locations(module)
counts={'selected_backing_refreshes':0,'receipt_refreshes':0,'freeze_calls':0}
old_cache=r._MEASURED_PACKING_CACHE;old_check=r._check_file_witness
try:
    r._MEASURED_PACKING_CACHE={}
    paths=[str(Path('/tmp/review111-count-only-candidate-'+str(i)).absolute()) for i in range(63)]
    for i,path in enumerate(paths):
        proof=object.__new__(r._CompletedPackingProof)
        object.__setattr__(proof,'pid',os.getpid())
        object.__setattr__(proof,'metadata',{'measurement':{'profile':{'candidate':i}}})
        object.__setattr__(proof,'witness',SimpleNamespace(paths=(path,'/tmp/review111-count-only-selected')))
        r._MEASURED_PACKING_CACHE[path]=proof
    def check(witness):
        counts['receipt_refreshes']+=1
        assert len(witness.paths)==2
        counts['selected_backing_refreshes']+=1
    r._check_file_witness=check
    def freeze(*a,**kw):
        counts['freeze_calls']+=1
        assert r._validated_measurement(kw['measured_path'])['measurement']['profile']=={'candidate':46}
    scope=dict(measured_paths=paths,profile={'candidate':46},_validated_measurement=r._validated_measurement,
        freeze_profile_reuse=freeze,reused=None,batch=None,cells=None,axes=None,index=None,axis_class=False,model=None,
        protocol={'workload':{'reuse_policy':{}}},runtime_kernel_identity=lambda _:None,errors=[])
    exec(compile(module,'frozen-candidate-loop','exec'),scope)
    assert counts==dict(selected_backing_refreshes=48,receipt_refreshes=48,freeze_calls=1)
    d,p,s=fixture();p['workload']['account_runtime_guards']=True
    inv=r.workload.build_inventory(d,p,stage='fit-select')
    guard=next(x for x in inv['requirements'] if x['operation']=='guard_refresh')
    expected=8*len(inv['shards'])+3*len(inv['captures'])+2*len(inv['jobs'])
    assert guard['batches']==expected
    print(json.dumps(dict(counts,candidate_count=63,matching_candidate_position=47,
        pricing_guard_passes_per_shard=8,common_backing_file_count_from_owner_evidence=8394,
        derived_common_file_visits_before_runner=48*8394,
        fixture_guard_batches=guard['batches'],fixture_expected_guard_batches=expected,
        model_calls=0,actual_backing_file_reads=0,source_edited=False,
        note='Control-flow counts only; no model/GPU/scientific evidence or wall-clock estimate.'),indent=2))
finally:
    r._MEASURED_PACKING_CACHE=old_cache;r._check_file_witness=old_check
