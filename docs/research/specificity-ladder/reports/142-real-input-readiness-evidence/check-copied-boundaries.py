from pathlib import Path
import os,sys,json,tempfile,shutil,hashlib,time
from types import SimpleNamespace
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');O=W/'outputs/_analyses/specificity-ladder/a3-source-cost-pilots-40fe57289405';R=W/'outputs/_analyses/specificity-ladder/a3-source-cost-runtime-40fe57289405/runtime';E=Path(__file__).parent;sys.path.insert(0,str(R));os.chdir(R);assert os.environ.get('SLURM_JOB_ID') and os.environ.get('CUDA_VISIBLE_DEVICES')==''
from component_analysis import a3_direction_runtime as a,ladder_pipeline as ladder,a3_source_validation as sources,a3_mask_pipeline as mask,a3_edge_pipeline as edge
owner=sys.argv[1];assert owner in ('mask','edge');started=time.time()
with tempfile.TemporaryDirectory(prefix='review142-'+owner+'-') as temp:
 T=Path(temp);prepared_path=T/'prepared';prepared_path.mkdir()
 for file in (O/owner/'prepared').iterdir():shutil.copyfile(file,prepared_path/file.name)
 registry=T/'registry.json';registry.write_text(json.dumps({'schema':1,'sets':[]}));args=SimpleNamespace(commit='40fe57289405fd53a3fce02e5d4e47a0ebf78b64',registry=[str(W/'docs/research/held_out.json'),str(registry)],design=str(O/'canonical/design.json'),prepared=str(prepared_path),work_dir=str(T),stage='pilot',seed=None,arm=None,task=None,group=None,chunk_size=4,steps=8,measure_stage='fit');prepared=a.read_object(prepared_path)
 if owner=='mask':
  mask._live_mask(prepared,args,inventory=None);state=args._mask_source_context
  def refresh():return mask._live_mask(prepared,args,inventory=None)[1]
 else:
  design=ladder.read_artifact(args.design);state=edge._make_edge_source_state(prepared,design,args);assert state is not None
  def refresh():return state.refresh(owner='edge',bound_inputs={'prepared':prepared,'design':design},registry_paths=args.registry,scope=edge._edge_source_scope(args))
 oracle=tuple(a._file_tree_identity(path) for path in state._witness.paths);assert oracle==state._witness.identities==state._scan_plan._rows_now(hash_files=True);expected=[row for tree in oracle for row in tree if row[0]=='file'];reads=[];actual=sources._read_source_file
 def reading(path,identity):reads.append((str(path),identity[3]));return actual(path,identity)
 sources._read_source_file=reading
 try:refresh()
 finally:sources._read_source_file=actual
 assert reads==[(r[1],r[2][3]) for r in expected];rid=next(r['instance_id'] for task in state._protection.contexts.values() for rows in task['rows']['D'].values() for r in rows)
 update=registry.with_suffix('.new');update.write_text(json.dumps({'schema':1,'sets':[{'ids':['review142-unrelated']}]}));update.replace(registry);refresh();registry.write_text(json.dumps({'schema':1,'sets':[{'ids':[rid]}]}));errors={}
 try:refresh()
 except ValueError as error:errors['protected_overlap']=str(error);assert 'overlap' in str(error)
 else:raise AssertionError('real overlap accepted')
 registry.write_text(json.dumps({'schema':1,'sets':[]}));refresh();payload=prepared_path/'payload.json';data=payload.read_bytes();stamp=payload.stat().st_mtime_ns;assert data.endswith(b'\n');payload.write_bytes(data[:-1]+b' ');os.utime(payload,ns=(stamp,stamp))
 try:refresh()
 except ValueError as error:errors['same_size_copied_byte_change']=str(error)
 else:raise AssertionError('changed bytes accepted')
 result={'owner':owner,'source_commit':args.commit,'job_id':os.environ['SLURM_JOB_ID'],'oracle_full_rows_order_equal':True,'every_file_occurrence_hashed':len(reads),'logical_bytes':sum(size for path,size in reads),'unrelated_atomic_update_pass':True,'overlap_rejected':True,'same_size_bytes_restored_mtime_rejected':True,'errors':errors,'original_artifacts_registries_runtime_modified':False,'model_or_authority_exercised':False,'not_a_performance_benchmark':True,'wall_seconds':time.time()-started};(E/('copied-boundaries-'+owner+'.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
