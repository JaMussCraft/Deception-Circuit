import json,os,pathlib,shutil,subprocess,sys
import pytest
B=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-pilot-runtime-74efb4d04819/runtime')
sys.path.insert(0,str(B))

def test_tiny_pilot_excludes_unaccepted_direction_execution_seams(tmp_path,monkeypatch):
    from component_analysis import a3_direction_runtime as runtime,a3_direction_workload as workload
    from tests.test_a3_mask_pipeline import test_actual_validation_only_pilot_covers_all_classes_and_is_nonfinal
    def forbidden(*args,**kwargs):pytest.fail('mask pilot reached excluded direction numerical/admission seam')
    for name in ('run_pilot','_cost_packing_proofs','_completed_packing_proof','read_runtime_rows','dispatch'):
        monkeypatch.setattr(runtime,name,forbidden)
    monkeypatch.setattr(workload,'project_cost',forbidden)
    test_actual_validation_only_pilot_covers_all_classes_and_is_nonfinal(tmp_path)
    for name,module in list(sys.modules.items()):
        if name.split('.')[0] in ('component_analysis','dataset','models','evaluation') and getattr(module,'__file__',None):assert pathlib.Path(module.__file__).resolve().is_relative_to(B)

def test_actual_spooled_wrapper_is_parser_only_and_pins_selected_interpreter(tmp_path):
    script=B/'scripts/jobs/specificity_a3_mask.sh';spool=tmp_path/'spool';spool.mkdir();launched=spool/'slurm_script';shutil.copy2(script,launched)
    env=dict(os.environ,SPECIFICITY_A3_MASK_REPO_ROOT=str(B),A3_MASK_PYTHON=sys.executable,DC_CLUSTER='delta',PYTHONDONTWRITEBYTECODE='1')
    before=set(tmp_path.rglob('*'))
    result=subprocess.run(['bash',str(launched),'--stage','pilot','--design','missing','--commit','74efb4d0481968a1d0138eb1a79b97f302fd3c3b','--work-dir',str(tmp_path/'unused'),'--dry-run'],cwd=tmp_path,env=env,capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stderr
    assert result.stdout.startswith(sys.executable+' -B -m component_analysis.a3_mask_pipeline')
    payload=json.loads(result.stdout.strip().splitlines()[-1]);assert payload['execution_authorized'] is False and payload['allocation_verified'] is False and payload['weights_loaded'] is False and payload['writes'] is False
    assert set(tmp_path.rglob('*'))==before

def test_mask_inventory_uses_accepted_actual_allocation_contract():
    from tests.test_a3_direction_runtime import test_allocation_contract_uses_own_validated_consumer_resource_shape
    test_allocation_contract_uses_own_validated_consumer_resource_shape('mask')

def test_shared_context_rejects_initializer_and_reuses_original_proof(tmp_path):
    from tests.test_a3_direction_runtime import test_cached_authority_rejects_public_reinitialization_including_empty_containers
    test_cached_authority_rejects_public_reinitialization_including_empty_containers(tmp_path,'empty_dict')
