"""Genuine complete mask-only owner validation; no model or admission."""
import os,sys,json,pathlib,copy,gc,resource
from types import SimpleNamespace
from component_analysis import a3_pipeline as canonical,a3_direction_artifacts as artifacts,a3_direction_runtime as authority,a3_direction_workload as dw,ladder_pipeline as ladder,a3_mask_pipeline as mask,a3_mask_workload as mw
from dataset import user_inversion_pipeline as common
W=pathlib.Path(os.environ['W']);B=pathlib.Path(os.environ['B']);O=pathlib.Path(os.environ['O']);C=os.environ['C'];reg=[str(W/'docs/research/held_out.json')]
def save(name,value):(O/'evidence'/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
d=ladder.read_artifact(O/'canonical/design.json');protocol=ladder.read_artifact(O/'canonical/direction_protocol.json')
assert protocol==d['direction_protocol'] and protocol['commit']==C and d.get('injected') is False
parent,selected,parent_evidence=canonical.load_a1_parents(W/'outputs/_analyses/specificity-ladder/ladder-5f450dc/design.json',W/'outputs/_analyses/specificity-ladder/ladder-5f450dc/selected.json')
canonical._validate_parent_files(parent,a1_repo_root=W);canonical.validate_assessment_membership(d,parent);assert parent_evidence==d['parent_evidence']
live=artifacts.validate_live(d,protocol,registry_paths=reg)
prior=W/'outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819';old=ladder.read_artifact(prior/'canonical/design.json')
assert set(d)==set(old)
allowed={'direction_protocol','direction_protocol_sha256','a1_repo_root','registry_hashes','mmlu_validation_candidates_manifest'}
changed=[k for k in d if d[k]!=old[k]];assert set(changed)<=allowed
assert protocol['numeric_profile']==old['direction_protocol']['numeric_profile'] and protocol['workload']==old['direction_protocol']['workload']
def normalized_science(x):
    result={k:v for k,v in x.items() if k not in {'direction_protocol','direction_protocol_sha256','a1_repo_root'}}
    result['registry_hashes']=sorted({str(pathlib.Path(p).resolve()) for p in x['registry_hashes']})
    meta=dict(x['mmlu_validation_candidates_manifest']);meta['grader_registry']=sorted({str(pathlib.Path(p).resolve()) for p in meta['grader_registry']});result['mmlu_validation_candidates_manifest']=meta
    return result
assert normalized_science(d)==normalized_science(old)
assert d['utility']==parent['utility'] and d['a1_repo_root']==str(B)
assert all(len(s['assessment_ids'])==100 and not(set(s['fit_ids'])&set(s['selection_ids']) or set(s['fit_ids'])&set(s['assessment_ids']) or set(s['selection_ids'])&set(s['assessment_ids'])) for s in d['tasks'].values())
comparison=dict(original_canonical=str(prior/'canonical/design.json'),changed_operational_fields=changed,scientific_payload_exact=True,numeric_profile_workload_exact=True,source_rows_sha256=dw.digest(d['access_rows']),assessment_ids={t:len(s['assessment_ids']) for t,s in d['tasks'].items()},IOI=len(d['utility']['ioi']),MMLU=len(d['utility']['mmlu']),IOI_validation=len(d['ioi_validation']),MMLU_validation=len(d['mmlu_validation']),protected_evidence=live)
save('scientific-comparison.json',comparison);del old;gc.collect()
mp=authority.read_object(O/'mask/prepared');args=SimpleNamespace(commit=C,registry=reg,stage='prepare',design=str(O/'canonical/design.json'),prepared=str(O/'mask/prepared'),work_dir=str(O/'mask'),chunk_size=4,seed=42,arm=None,task=None,group=None)
md,source=mask._live_mask(mp,args)
assert mp['identity']['commit']==C and mp['identity']['code_hashes']==mask.mask_code_hashes() and mp['execution_authorized'] is False and mp['chunk_size']==4
expected_scope=dict(tasks={t:{k:s[k] for k in ('fit_ids','selection_ids','assessment_ids')} for t,s in d['tasks'].items()},ioi_validation=[r['instance_id'] for r in d['ioi_validation']],mmlu_validation=[r['instance_id'] for r in d['mmlu_validation']],ioi=[r['instance_id'] for r in d['utility']['ioi']],mmlu=[r['instance_id'] for r in d['utility']['mmlu']],task_order=list(d['tasks']),hbank_sources=mp['hbank_sources'],widths=mp['widths'],new30_reference=mp['new30'])
inventories={}
for stage,count in [('pilot',31191),('full',3437966)]:
    path=O/'mask'/('inventory-'+stage);inv=authority.read_object(path);mw.validate_inventory(inv)
    assert inv['identity']==mp['identity'] and inv['scope']==expected_scope and inv['chunk_size']==4 and inv['finish_reserve_seconds']==300 and len(inv['expected_keys'])==count
    inventories[stage]=dict(expected_keys=count,inventory_sha256=inv['inventory_sha256'],phase=inv['phase'],object_reference=authority.object_reference(path),storage_requirements=inv['storage_requirements'])
    del inv;gc.collect()
assert inventories['pilot']['phase']=='M1' and inventories['full']['phase']=='M5'
imports={name:m.__file__ for name,m in list(sys.modules.items()) if name.split('.')[0] in ('component_analysis','dataset','models','evaluation','scripts') and getattr(m,'__file__',None)}
assert all(pathlib.Path(f).resolve().is_relative_to(B) for f in imports.values())
save('mask-validation.json',dict(commit=C,prepared=authority.object_reference(O/'mask/prepared'),source_evidence=source,inventories=inventories,science=comparison,project_imports=imports,host_peak_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,models_loaded=False,execution_authorized=False))
print('GENUINE_MASK_COMPLETE_VALIDATION_PASS')
