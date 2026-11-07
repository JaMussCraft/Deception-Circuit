from pathlib import Path
import os,sys,json,hashlib,time,resource,shutil
R=Path(os.environ['REVIEW134_RUNTIME']);E=Path(__file__).parent;os.chdir(R);sys.path.insert(0,str(R));shutil.copy2=shutil.copyfile
import pytest
from component_analysis import a3_source_validation as s
assert Path(s.__file__)==R/'component_analysis/a3_source_validation.py'
legacy=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/121-source-cost-review-evidence/test_independent_source_boundaries.py')
# The preserved probe uses its original data fixture; production imports stay R.
args=['-q','-p','no:cacheprovider','--rootdir='+str(R),'--confcutdir='+str(R),'--import-mode=importlib','--basetemp='+os.environ['REVIEW134_BASETEMP'],str(R/'tests/test_a3_source_validation.py'),str(E/'test_independent_batch.py')]
assert legacy.is_file()
assert hashlib.sha256(legacy.read_bytes()).hexdigest()=='54b24e2b56325da734a38a519b3003771494d3a9c25ca29b7c38c42717768202';args.append(str(legacy))
args.extend([str(R/'tests/test_a3_edge_pipeline.py')+'::test_cached_edge_source_keeps_fresh_authority_and_runs_semantics_once',str(R/'tests/test_a3_edge_pipeline.py')+'::test_source_views_preserve_actual_edge_copy_consumers',str(R/'tests/test_a3_edge_pipeline.py')+'::test_edge_source_initialization_reaches_actual_receipt_and_projector',str(R/'tests/test_a3_mask_pipeline.py')+'::test_cached_mask_source_refresh_preserves_current_protection_and_semantic_work_once',str(R/'tests/test_a3_mask_pipeline.py')+'::test_mask_source_initialization_reaches_existing_projector_startup_cost'])
started=time.time();result=int(pytest.main(args));modules={n:m.__file__ for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','dataset','scripts','evaluation','models') and getattr(m,'__file__',None)};assert all(Path(p).resolve().is_relative_to(R) for p in modules.values())
(E/('result-'+sys.argv[1]+'-'+os.environ['SLURM_JOB_ID']+'.json')).write_text(json.dumps({'interpreter':sys.executable,'args':args,'exit_code':result,'wall_seconds':time.time()-started,'host_peak_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'project_imports':modules,'helper_sha256':hashlib.sha256(Path(s.__file__).read_bytes()).hexdigest(),'job_id':os.environ['SLURM_JOB_ID'],'models_or_weights_loaded':False,'fixture_transport':'byte-only copyfile to avoid site ACL copying'},indent=2));raise SystemExit(result)
