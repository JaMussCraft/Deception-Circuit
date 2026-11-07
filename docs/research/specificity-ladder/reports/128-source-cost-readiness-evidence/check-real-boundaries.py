from pathlib import Path
import os,sys,json,shutil,tempfile,time,hashlib
from types import SimpleNamespace
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');O=W/'outputs/_analyses/specificity-ladder/a3-source-cost-pilots-f5a5687ec120';R=W/'outputs/_analyses/specificity-ladder/a3-source-cost-runtime-f5a5687ec120/runtime';E=Path(__file__).parent;sys.path.insert(0,str(R));os.chdir(R)
from component_analysis import a3_mask_pipeline as mask,a3_direction_runtime as authority
assert Path(mask.__file__)==R/'component_analysis/a3_mask_pipeline.py'
started=time.perf_counter()
with tempfile.TemporaryDirectory(prefix='review128-real-boundaries-') as temp:
 T=Path(temp);prepared_path=T/'prepared';prepared_path.mkdir()
 for source in (O/'mask/prepared').iterdir():shutil.copyfile(source,prepared_path/source.name)
 registry=T/'registry.json';registry.write_text(json.dumps({'schema':1,'sets':[]}))
 args=SimpleNamespace(commit='f5a5687ec12091f0d148b38b301598e9c7cb98cd',registry=[str(W/'docs/research/held_out.json'),str(registry)],design=str(O/'canonical/design.json'),prepared=str(prepared_path),work_dir=str(O/'mask'),stage='pilot',seed=None,arm=None,task=None,group=None,chunk_size=4)
 prepared=authority.read_object(prepared_path);design,evidence=mask._live_mask(prepared,args,inventory=None);state=args._mask_source_context;rid=state._protection.contexts['far_v2']['rows']['D']['test'][0]['instance_id']
 updated=registry.with_suffix('.new');updated.write_text(json.dumps({'schema':1,'sets':[{'ids':['independent-review-unrelated-id']}]}));updated.replace(registry);mask._live_mask(prepared,args,inventory=None)
 registry.write_text(json.dumps({'schema':1,'sets':[{'task':'far_v2','ids':[rid]}]}));errors={}
 try:mask._live_mask(prepared,args,inventory=None)
 except ValueError as error:errors['real_source_protected_overlap']=str(error)
 else:raise AssertionError('real protected overlap accepted')
 registry.write_text(json.dumps({'schema':1,'sets':[]}));mask._live_mask(prepared,args,inventory=None)
 payload=prepared_path/'payload.json';before=payload.read_bytes();stamp=payload.stat().st_mtime_ns;assert before[-1:]==b'\n';payload.write_bytes(before[:-1]+b' ');os.utime(payload,ns=(stamp,stamp));assert len(payload.read_bytes())==len(before)
 try:mask._live_mask(prepared,args,inventory=None)
 except ValueError as error:errors['same_size_valid_json_byte_change_restored_mtime']=str(error)
 else:raise AssertionError('changed copied prepared bytes accepted')
 result={'kind':'independent_genuine_input_boundaries_on_temporary_copies','source_commit':args.commit,'source_module':mask.__file__,'actual_genuine_initialization_pass':True,'unrelated_atomic_current_registry_update_pass':True,'real_source_instance_overlap_rejected':True,'same_size_valid_json_bytes_restored_mtime_rejected':True,'errors':errors,'execution_authority_exercised':False,'models_loaded':False,'original_artifacts_or_registries_modified':False,'wall_seconds':time.perf_counter()-started}
(E/'real-boundary-check.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
