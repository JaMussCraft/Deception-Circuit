"""CPU metadata validation and nonadmissible two-part M1 count worksheet."""
from pathlib import Path
import copy,gc,json,os,sys,time
P=Path(__file__).resolve().parent
cfg=json.loads((P/'config.json').read_text());B=Path(cfg['runtime']).resolve();O=Path(cfg['canonical']).parent;E=Path(cfg['output'])/'evidence';sys.path.insert(0,str(B))
from component_analysis import a3_direction_runtime as r

def write(name,value):
    with (E/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')

def science(design):
    value=copy.deepcopy(design)
    for key in ('direction_protocol','direction_protocol_sha256','registry_hashes'):value.pop(key,None)
    value['mmlu_validation_candidates_manifest'].pop('grader_registry',None)
    return value

new=r.ladder.read_artifact(O/'canonical/design.json');old=r.ladder.read_artifact(Path(cfg['prior_canonical'])/'design.json');protocol=new['direction_protocol']
assert not new['injected'] and not protocol['injected'] and protocol['commit']==cfg['source_commit']
assert r.workload.digest(science(new))==r.workload.digest(science(old)),'Scientific/core inputs changed'
assert set(new['registry_hashes'])==set(old['registry_hashes'])
assert set(new['mmlu_validation_candidates_manifest']['grader_registry'])==set(old['mmlu_validation_candidates_manifest']['grader_registry'])
assert new['a1_identity']['grader_sha256']==old['a1_identity']['grader_sha256']
work=protocol['workload'];assert work['axis_tile_size']==2 and work['axis_tile_sizes']=={'prefit':2,'fit-select':2,'selected-pilot':32,'remaining':32}
assert new['seeds']==[42,1,123] and protocol['assessment_orientations']==199 and protocol['calibration_orientations']==32
assert protocol['confirmatory_tasks']==['far_v2','ser_v2'] and protocol['descriptive_tasks']==['sdr_v2']
assert protocol['numeric_profile']['dtype']=='torch.bfloat16' and protocol['numeric_profile']['backend']=='sdpa'
assert work['hardware']=={'count':1,'gpu':'h200'} and work['finish_reserve_seconds']==90
registry=[str(Path(cfg['W'])/'docs/research/held_out.json')]
current=r.artifacts.validate_live(new,protocol,registry_paths=registry)
write('science-and-current-protection.json',dict(science_core_equal=True,operational_exclusions=['direction_protocol','direction_protocol_sha256'],live_certificate_exclusions=['registry_hashes','mmlu_validation_candidates_manifest.grader_registry'],old_registry_hashes=old['registry_hashes'],new_registry_hashes=new['registry_hashes'],current_live_validation=current,source_commit=cfg['source_commit'],execution_authorized=False))
del old;gc.collect();summaries={}
for stage in ('prefit','fit-select'):
    inv=r.read_object(cfg['inventory_paths'][stage])
    if stage=='fit-select':r.workload._validate_inventory(inv)
    assert inv['stage']==stage and not inv['injected'] and inv['identity']==r.workload.inventory_identity(new,protocol)
    assert inv['frozen_inputs']['selected'] is None and inv['frozen_inputs']['fits'] is None
    summaries[stage]=dict(inventory_sha256=inv['inventory_sha256'],stage=stage,phase=inv['phase'],forward_counts=inv['forward_counts'],shards=len(inv['shards']),captures=len(inv['captures']),packing_invocations=len(inv['packing_invocations']),raw_expected_keys=len(inv['expected_keys']),jobs=len(inv['jobs']),storage_requirements=inv['storage_requirements'],serialization_shapes=sum(len(q['profile'].get('serialization_shapes',[])) for q in inv['requirements'] if q['operation']=='serialization'),guard_refresh_batches=sum(q['batches'] for q in inv['requirements'] if q['operation']=='guard_refresh'))
    del inv;gc.collect()
write('genuine-inventory-summaries.json',summaries)
log=(E/'prefit-dry-run-without-authority.log').read_text().splitlines();dry=[json.loads(line) for line in log if line.startswith('{')][-1]
assert dry['model_loaded'] is False and dry['writes'] is False and dry['execution_authorized'] is False
assert set(dry['missing_prerequisites'])=={'ledger_snapshot','reservation'}
write('dry-run-result.json',dry)
timing={task:r.workload._timing_ids(r.workload._source_rows(new,task,'validation')) for task in list(new['tasks'])+['ioi','mmlu']}
assert all(len(ids)==4 for ids in timing.values()),'Four frozen timing IDs per real source must be confirmed'
sites={task:len(value['direction_sites']) for task,value in new['tasks'].items()};assert sum(sites.values())==43
prefit_min=sum(sites.values())*3*5*(20+2+4);selected_min=9*(200+33)*5*(20+2+4)
finish=2*work['finish_reserve_seconds']
write('two-part-M1-budget-worksheet.json',dict(status='NOT_ADMITTED_feasible_split_unestablished',required_sequence=['prefit M1','M2 fitting and validation plus CPU selection','separate selected M1','remaining admission then calibration/assessment'],direction_M1_total_reserved_GPU_hours=.5,total_minutes=30,mask_original_plus_replacement_reserved_GPU_hours=1.5,N5_additional_attempt_already_consumed=True,all_A3_GPU_hours=40,minimum_finish_seconds=finish,model_startups_required=2,prefit_candidate_sites=sites,frozen_timing_ids=timing,prefit_serial_forward_lower_bound=prefit_min,selected_serial_forward_lower_bound=selected_min,excluded_from_lower_bound=['packed forwards','dummy comparisons','optional nuisance/secondary/steering','tail batches','captures/positives/warmup','proof construction/serialization/live guards/startup'],max_average_serial_forward_ms_if_all_other_work_zero=1000*(1800-finish)/(prefit_min+selected_min),illustrative_only_not_GPU_request=dict(prefit_minutes=10,selected_minutes=20,rounded_reserved_total=.5,prefit_max_ms_if_other_work_zero=1000*(600-90)/prefit_min,selected_max_ms_if_other_work_zero=1000*(1200-90)/selected_min),matched_two_part_H200_bound_supplied=False,budget_feasibility_established=False))
args=r.parser().parse_args(['--experiment','directions','--stage','pilot','--pilot-part','prefit','--design',str(O/'canonical/design.json'),'--commit',cfg['source_commit'],'--work-dir',str(O/'canonical'),'--inventory',str(O/'canonical/inventory/prefit'),'--registry',registry[0],'--dry-run'])
guard=[]
for _ in range(3):
    began=time.perf_counter();r.live_guard(new,protocol,args);guard.append(time.perf_counter()-began)
write('source-protection-component-cost.json',dict(actual_CPU_seconds=guard,scope='source/protection/model metadata only; no ledger/reservation/allocation validation or model/GPU timing',host=os.uname().nodename,conditional_for_other_hosts=True,execution_authorized=False))
origins={name:str(Path(module.__file__).resolve()) for name,module in sys.modules.items() if getattr(module,'__file__',None) and name.split('.')[0] in ('component_analysis','dataset','evaluation','models')}
assert all(Path(path).is_relative_to(B) for path in origins.values()),'Active-source import fallback'
write('module-origins.json',origins)
print(json.dumps(dict(genuine_CPU_preparation_validated=True,budget_feasibility_established=False,execution_authorized=False)),flush=True)
