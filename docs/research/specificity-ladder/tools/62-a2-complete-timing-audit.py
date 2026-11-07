"""Audit existing complete H200 timing coverage on CPU; never run training."""
import argparse
from pathlib import Path
import hashlib
import itertools
import json
import math
import re
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--repo', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    sys.path.insert(0, str(repo))
    from scripts import twin_training as tw
    from scripts import twin_training_projection as projection
    folder = repo/'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200'
    paths = sorted(folder.glob('*-seed42.json'))
    receipts = [json.loads(p.read_text()) for p in paths]
    config_path = folder.parent/'a2-timing-h200-config.json'
    config = json.loads(config_path.read_text())
    config['data_root'] = str(folder.parent/'a2-matched-77b6487-m07')
    manifest_path = Path(config['data_root'])/'build_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    ruling = json.loads((repo/'docs/research/specificity-ladder/a2-cohort-ruling.json').read_text())
    execution = '6bd8bf5334f2e83613a129d2fcfeacf83e762191'
    expected_cells = set(itertools.product(config['tasks'],config['conditions']))
    assert {(r['task'],r['condition']) for r in receipts} == expected_cells and len(receipts)==6
    preflight = json.loads((folder/'preflight.json').read_text())
    cache = Path('/work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct')
    revision = (cache/'refs/main').read_text().strip()
    snapshot = cache/'snapshots'/revision
    assert revision == preflight['model_cache_preflight']['cached_main_revision']
    assert sha(snapshot/'config.json') == preflight['model_cache_preflight']['config_sha256']
    assert sha(snapshot/'model.safetensors.index.json') == preflight['model_cache_preflight']['weight_index_sha256']
    weight_index = json.loads((snapshot/'model.safetensors.index.json').read_text())
    assert all((snapshot/p).is_file() for p in set(weight_index['weight_map'].values()))
    summaries=[]
    for path,r in zip(paths,receipts):
        task,condition=r['task'],r['condition']
        log=(repo/r['stdout_stderr_log']).read_text()
        assert float(re.findall(r'Node pruning time:\s*([0-9.]+)s',log)[-1])==r['pruning_seconds']
        assert float(re.findall(r'Overall peak:\s*([0-9.]+) GB',log)[-1])==r['peak_memory_gb']
        assert r['status']=='success' and r['exit_code']==0 and r['errors']==[]
        assert not r['test_runner_injected'] and not r['test_clock_injected']
        assert r['execution_commit']==execution and r['source_commit']==manifest['source_commit']!=execution
        assert sha(config_path)==r['config_file_sha256'] and sha(manifest_path)==r['build_manifest_file_sha256']
        assert {p:sha(repo/p) for p in r['source_hashes']}==r['source_hashes']
        assert r['source_hashes']==receipts[0]['source_hashes']
        assert r['gpu_devices']==receipts[0]['gpu_devices']==['NVIDIA H200, 143771 MiB']
        assert r['gpu_count']==1 and r['environment']['SLURM_CLUSTER_NAME']=='delta'
        assert r['environment']['SLURM_JOB_ID']==('23414611' if (task,condition)==('far_v2','D') else '23415106')
        fresh=tw.plan_run(config,manifest,task=task,condition=condition,seed=42,timing_epochs=20,execution_commit=execution)
        for key in ('source_hashes','frozen_config_sha256','resolved_config_sha256','dataset_config_sha256',
                    'registry_sha256','counts','selected_ids','build_hash','build_manifest_sha256'):
            assert fresh[key]==r[key],(task,condition,key)
        assert r['counts']==ruling['counts'][task]
        assert r['purpose']=='timing-only' and r['actual_epochs']==20 and r['planned_epochs']==500
        assert {n:sha(repo/p) for n,p in r['artifacts'].items()}==r['artifact_sha256']
        out=repo/r['output_dir']
        native=tw._validate_artifacts(out,r['argv'],r)
        tw._check_subset(json.loads((out/'config.json').read_text()),tw.expected_config(r['argv']))
        assert native['execution_commit']==native['orchestrator_source_commit']==execution
        assert native['build_source_commit']==manifest['source_commit'] and native['model_revision']==revision
        assert native['slurm_job_id']==r['environment']['SLURM_JOB_ID']
        for p,value in native['code_sha256'].items(): assert sha(repo/p)==value
        for p,value in native['dataset_files'].items(): assert sha(repo/p)==value
        history=json.loads((out/'history.json').read_text())['node']
        assert history['epochs']==list(range(1,21))
        assert [e['epoch'] for e in history['evals']]==[0,10,20]
        for e in history['evals']:
            assert [x['instance_id'] for x in e['outputs']]==r['selected_ids']['validation']
        results=json.loads((out/'results.json').read_text())
        metrics={}
        baseline=results['baseline']['outputs']
        for key in ('baseline','node_eval'):
            rows=results[key]['outputs']
            assert [x['instance_id'] for x in rows]==r['selected_ids']['test']
            assert len(rows)==r['counts']['test']
            positives=sum(x['logit_difference']>0 for x in rows)
            mean=sum(x['logit_difference'] for x in rows)/len(rows)
            assert positives/len(rows)==results[key]['accuracy']
            assert abs(mean-results[key]['logit_diff'])<1e-12
            metrics[key]=dict(rows=len(rows),correct=positives,accuracy=positives/len(rows),
                              logit_diff=mean,ties=sum(x['logit_difference']==0 for x in rows))
        # Decoded words are not sufficient to attest full-vocabulary token identity.
        # The saved exact-match metric is retained, not independently re-derived.
        fixed=r['total_seconds']-r['pruning_seconds']
        full=fixed+r['pruning_seconds']*500/20
        wall=(datetime.fromisoformat(r['finished_utc'])-datetime.fromisoformat(r['started_utc'])).total_seconds()
        assert abs(wall-r['total_seconds'])<.01
        summaries.append(dict(task=task,condition=condition,receipt=str(path),native_manifest=str(out/'run_manifest.json'),
            counts=r['counts'],epochs_observed=len(history['epochs']),validation_epochs=[0,10,20],
            total_seconds=r['total_seconds'],pruning_seconds=r['pruning_seconds'],fixed_seconds=fixed,
            estimated_full_seconds=full,contract_reserved_minutes=math.ceil(full*1.2/60),
            metrics=metrics,peak_allocated_gib=r['peak_memory_gb']))
    driver_plan=json.loads((folder/'remaining-timing-plan.json').read_text())
    assert driver_plan['application_commit']==execution
    assert sha(repo/driver_plan['driver_path'])==driver_plan['driver_sha256']
    accounting_cmd=['sacct','-j','23415106,23414611,23414452',
        '--format=JobIDRaw,State,ExitCode,ElapsedRaw,TimelimitRaw,AllocTRES,MaxRSS,Start,End','-P']
    raw=subprocess.run(accounting_cmd,check=True,capture_output=True,text=True).stdout
    lines=[x.split('|') for x in raw.strip().splitlines()]
    accounting={row[0]:dict(zip(lines[0],row)) for row in lines[1:]}
    for job in ('23415106','23414611'):
        assert accounting[job]['State']=='COMPLETED' and accounting[job]['ExitCode']=='0:0'
    assert accounting['23414452']['State']=='FAILED' and accounting['23414452']['ExitCode']=='1:0'
    minutes=sum(int(accounting[j]['TimelimitRaw']) for j in ('23415106','23414611','23414452'))
    assert minutes==58 and int(accounting['23415106']['ElapsedRaw'])==974
    failed=json.loads((folder.parent/'a2-timing-224823f-a40/far-D-seed42.json').read_text())
    assert failed['status']=='failed' and failed['pruning_seconds'] is None
    plan=dict(config=config,build_manifest=manifest,source_hashes=receipts[0]['source_hashes'],
        hardware=dict(gpu_devices=receipts[0]['gpu_devices'],gpu_count=1,cluster='delta'),
        execution_commit=execution,cohort_ruling=ruling)
    projected=projection.project_reserved(receipts,plan,pilot_reserved_gpu_hours=minutes/60)
    assert projected['fleet_reservation_allowed'] and not projected['coverage_gaps']
    assert not projected['rejected_receipts'] and len(projected['cells'])==18
    assert not projected['single_mask_over_6h'] and projected['within_60h']
    saved=json.loads((folder/'projection-complete.json').read_text())
    assert saved==projected,'saved tool projection differs from independently recomputed projection'
    without_ruling=dict(plan);without_ruling.pop('cohort_ruling')
    assert not projection.project_reserved(receipts,without_ruling,pilot_reserved_gpu_hours=minutes/60)['fleet_reservation_allowed']
    assert not projection.project_reserved(receipts,plan,pilot_reserved_gpu_hours=60)['fleet_reservation_allowed']
    assert not projection.project_reserved(receipts[:-1],plan,pilot_reserved_gpu_hours=minutes/60)['fleet_reservation_allowed']
    foreign=[dict(r) for r in receipts];foreign[0]['gpu_devices']=['NVIDIA A40']
    assert not projection.project_reserved(foreign,plan,pilot_reserved_gpu_hours=minutes/60)['fleet_reservation_allowed']
    long=[dict(r,total_seconds=900,pruning_seconds=900) for r in receipts]
    long_result=projection.project_reserved(long,plan,pilot_reserved_gpu_hours=minutes/60)
    assert long_result['single_mask_over_6h'] and not long_result['fleet_reservation_allowed']
    batch=sorted([r for r in receipts if r['environment']['SLURM_JOB_ID']=='23415106'],key=lambda r:r['started_utc'])
    batch_sum=sum(r['total_seconds'] for r in batch)
    batch_outer=int(accounting['23415106']['ElapsedRaw'])-batch_sum
    standalone_outer=int(accounting['23414611']['ElapsedRaw'])-receipts[0]['total_seconds']
    previous=datetime.fromisoformat(accounting['23415106']['Start']).replace(tzinfo=ZoneInfo('America/Chicago'))
    gaps=[]
    for r in batch:
        start=datetime.fromisoformat(r['started_utc'])
        gaps.append(dict(task=r['task'],condition=r['condition'],seconds=(start-previous).total_seconds()))
        previous=datetime.fromisoformat(r['finished_utc'])
    single_start=datetime.fromisoformat(accounting['23414611']['Start']).replace(tzinfo=ZoneInfo('America/Chicago'))
    standalone_initial=(datetime.fromisoformat(receipts[0]['started_utc'])-single_start).total_seconds()
    outer_allowance=math.ceil(max(standalone_outer,standalone_initial,max(g['seconds'] for g in gaps)))
    assert outer_allowance==20 and outer_allowance>=standalone_outer
    conservative=[]
    for s in summaries:
        reserve=math.ceil((s['estimated_full_seconds']+outer_allowance)*1.2/60)
        s['outer_allowance_seconds']=outer_allowance
        s['conservative_reserved_minutes']=reserve
        for seed in config['seeds']:
            conservative.append(dict(task=s['task'],condition=s['condition'],seed=seed,reserved_minutes=reserve))
    full_minutes=minutes+sum(c['reserved_minutes'] for c in conservative)
    assert full_minutes==1153 and full_minutes/60<=60
    assert all(s['estimated_full_seconds']+outer_allowance<=6*3600 for s in summaries)
    result=dict(status='all-audit-assertions-passed',execution_commit=execution,build_source_commit=manifest['source_commit'],
        model_revision=revision,receipt_count=len(receipts),cells=summaries,projection=projected,
        saved_tool_projection_matches=True,slurm_accounting=accounting,pilot_reserved_minutes=minutes,
        pilot_reserved_gpu_hours=minutes/60,batch_child_sum_seconds=batch_sum,batch_elapsed_seconds=974,
        batch_outer_seconds=batch_outer,batch_average_outer_seconds=batch_outer/len(batch),
        batch_launch_gaps=gaps,standalone_outer_seconds=standalone_outer,
        standalone_initial_seconds=standalone_initial,outer_allowance_seconds=outer_allowance,
        conservative_cells=conservative,conservative_total_reserved_minutes=full_minutes,
        conservative_total_reserved_gpu_hours=full_minutes/60,
        measured_task_condition_count=6,planned_seed_cell_count=18,buffer_fraction=.2,
        failed_a40_preserved=True,cohort_ruling_digest=projection.digest(ruling),
        independent_baseline_replay_performed=False,exact_match_token_replay_performed=False,
        full_seed_runs_performed=0,all_gate_negative_controls_passed=True)
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','receipt_count','batch_child_sum_seconds','batch_outer_seconds',
        'standalone_outer_seconds','outer_allowance_seconds','pilot_reserved_minutes',
        'conservative_total_reserved_minutes','conservative_total_reserved_gpu_hours')},indent=2))
    for s in summaries:
        print(s['task'],s['condition'],s['contract_reserved_minutes'],s['conservative_reserved_minutes'])


if __name__=='__main__':
    main()
