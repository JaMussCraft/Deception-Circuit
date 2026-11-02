"""CPU-only audit of existing A2 timing artifacts; never starts training."""
import argparse
from pathlib import Path
import hashlib
import json
import math
import re
import subprocess
import sys
from datetime import datetime


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    sys.path.insert(0, str(repo))
    from scripts import twin_training as tw
    from scripts import twin_training_projection as projection
    receipt_path = repo/'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/far-D-seed42.json'
    receipt = json.loads(receipt_path.read_text())
    failed_path = repo/'outputs/_analyses/specificity-ladder/a2-timing-224823f-a40/far-D-seed42.json'
    failed = json.loads(failed_path.read_text())
    config_path = repo/'outputs/_analyses/specificity-ladder/a2-timing-h200-config.json'
    config = json.loads(config_path.read_text())
    assert sha(config_path) == receipt['config_file_sha256']
    config['data_root'] = str(repo/'outputs/_analyses/specificity-ladder/a2-matched-77b6487-m07')
    manifest_path = Path(config['data_root'])/'build_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert sha(manifest_path) == receipt['build_manifest_file_sha256']
    assert receipt['status'] == 'success' and receipt['exit_code'] == 0 and receipt['errors'] == []
    assert receipt['test_runner_injected'] is False and receipt['test_clock_injected'] is False
    execution = '6bd8bf5334f2e83613a129d2fcfeacf83e762191'
    assert receipt['execution_commit'] == execution
    assert receipt['source_commit'] == manifest['source_commit'] != execution
    assert {name:sha(repo/name) for name in receipt['source_hashes']} == receipt['source_hashes']
    fresh = tw.plan_run(config, manifest, task='far_v2', condition='D', seed=42,
                        timing_epochs=20, execution_commit=execution)
    for key in ('source_hashes','frozen_config_sha256','resolved_config_sha256','dataset_config_sha256',
                'registry_sha256','counts','selected_ids','build_hash','build_manifest_sha256'):
        assert fresh[key] == receipt[key], key
    out = repo/receipt['output_dir']
    assert {name:sha(repo/path) for name,path in receipt['artifacts'].items()} == receipt['artifact_sha256']
    native = tw._validate_artifacts(out, receipt['argv'], receipt)
    tw._check_subset(json.loads((out/'config.json').read_text()), tw.expected_config(receipt['argv']))
    assert native['execution_commit'] == native['orchestrator_source_commit'] == execution
    assert native['build_source_commit'] == manifest['source_commit']
    assert native['slurm_job_id'] == receipt['environment']['SLURM_JOB_ID'] == '23414611'
    for name,value in native['code_sha256'].items():
        assert sha(repo/name) == value
    for name,value in native['dataset_files'].items():
        assert sha(repo/name) == value
    results = json.loads((out/'results.json').read_text())
    history = json.loads((out/'history.json').read_text())['node']
    assert history['epochs'] == list(range(1,21))
    assert [e['epoch'] for e in history['evals']] == [0,10,20]
    summaries = {}
    for key in ('baseline','node_eval'):
        rows = results[key]['outputs']; ids = [r['instance_id'] for r in rows]
        assert ids == receipt['selected_ids']['test'] and len(rows) == 891
        accuracy = sum(r['chosen_word'] == r['target'] for r in rows)/len(rows)
        margin = sum(r['logit_difference'] for r in rows)/len(rows)
        assert accuracy == results[key]['accuracy']
        assert abs(margin-results[key]['logit_diff']) < 1e-12
        summaries[key] = dict(rows=len(rows), accuracy=accuracy, logit_diff=margin)
    for e in history['evals']:
        assert [r['instance_id'] for r in e['outputs']] == receipt['selected_ids']['validation']
    preflight = json.loads((receipt_path.parent/'preflight.json').read_text())
    cache = Path('/work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct')
    revision = (cache/'refs/main').read_text().strip()
    assert revision == native['model_revision'] == preflight['model_cache_preflight']['cached_main_revision']
    snapshot = cache/'snapshots'/revision
    assert sha(snapshot/'config.json') == preflight['model_cache_preflight']['config_sha256']
    assert sha(snapshot/'model.safetensors.index.json') == preflight['model_cache_preflight']['weight_index_sha256']
    index = json.loads((snapshot/'model.safetensors.index.json').read_text())
    assert all((snapshot/name).is_file() for name in set(index['weight_map'].values()))
    model_config = json.loads((snapshot/'config.json').read_text())
    assert model_config['architectures'] == ['LlamaForCausalLM']
    assert model_config['num_hidden_layers'] == 32 and model_config['hidden_size'] == 4096
    ruling = json.loads((repo/'docs/research/specificity-ladder/a2-cohort-ruling.json').read_text())
    plan = dict(config=config, build_manifest=manifest, source_hashes=receipt['source_hashes'],
                hardware=dict(gpu_devices=receipt['gpu_devices'],gpu_count=1,cluster='delta'),
                execution_commit=execution, cohort_ruling=ruling)
    accounting_cmd = ['sacct','-j','23414611,23414452','--format=JobIDRaw,State,ExitCode,ElapsedRaw,TimelimitRaw,AllocTRES,MaxRSS,Start,End','-P']
    accounting = subprocess.run(accounting_cmd,check=True,capture_output=True,text=True).stdout
    rows = [line.split('|') for line in accounting.strip().splitlines()]
    fields = rows[0]
    account = {r[0]:dict(zip(fields,r)) for r in rows[1:]}
    assert account['23414611']['State'] == 'COMPLETED' and account['23414611']['ExitCode'] == '0:0'
    assert account['23414452']['State'] == 'FAILED' and account['23414452']['ExitCode'] == '1:0'
    assert failed['status'] == 'failed' and failed['exit_code'] == 1 and failed['pruning_seconds'] is None
    minutes = sum(int(account[j]['TimelimitRaw']) for j in ('23414611','23414452'))
    assert minutes == 32
    ledger = json.loads(Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/ledger.json').read_text())
    ledger_rows = {v['job_id']:v for v in ledger['reservations']}
    for job in ('23414611','23414452'):
        assert ledger_rows[job]['status'] == account[job]['State']
        assert ledger_rows[job]['actual_seconds'] == int(account[job]['ElapsedRaw'])
        assert ledger_rows[job]['requested_minutes'] == int(account[job]['TimelimitRaw'])
    result = projection.project_reserved([receipt],plan,pilot_reserved_gpu_hours=minutes/60)
    assert not result['rejected_receipts'] and len(result['cells']) == 3 and len(result['coverage_gaps']) == 15
    assert result['fleet_reservation_allowed'] is False and result['recommendation'] == 'hold'
    fixed = receipt['total_seconds']-receipt['pruning_seconds']
    scaled = receipt['pruning_seconds']*500/receipt['actual_epochs']
    estimate = fixed+scaled
    assert abs(result['cells'][0]['estimated_seconds']-estimate)<1e-9
    buffered = estimate*1.2
    reserved = math.ceil(buffered/60)
    assert reserved == result['cells'][0]['reserved_minutes'] == 62
    assert estimate<6*3600
    log=(repo/receipt['stdout_stderr_log']).read_text()
    assert 'Node pruning time: 119.7s' in log and 'Overall peak:      51.610 GB' in log
    wall=(datetime.fromisoformat(receipt['finished_utc'])-datetime.fromisoformat(receipt['started_utc'])).total_seconds()
    assert abs(wall-receipt['total_seconds'])<.01
    summary = dict(status='all-audit-assertions-passed',receipt=str(receipt_path),
        execution_commit=execution,build_source_commit=manifest['source_commit'],
        native_manifest=str(out/'run_manifest.json'),model_revision=revision,
        model_identity='meta-llama/Llama-3.1-8B-Instruct',weight_shards_present=len(set(index['weight_map'].values())),
        source_hash_count=len(receipt['source_hashes']),artifact_count=len(receipt['artifact_sha256']),
        native_dataset_file_count=len(native['dataset_files']),counts=receipt['counts'],
        epochs_observed=len(history['epochs']),epochs_expected=20,validation_epochs=[0,10,20],
        eval_summaries=summaries,baseline_log_accuracy=1.0,baseline_result_accuracy=results['baseline']['accuracy'],
        independent_baseline_replay=False,slurm_accounting=account,
        total_seconds=receipt['total_seconds'],pruning_seconds=receipt['pruning_seconds'],
        fixed_seconds=fixed,scaled_pruning_seconds=scaled,full_500_epoch_seconds=estimate,
        full_500_epoch_minutes=estimate/60,buffer_fraction=.2,buffered_seconds=buffered,
        rounded_reservation_minutes=reserved,pilot_reserved_minutes=minutes,pilot_reserved_gpu_hours=minutes/60,
        successful_allocation_seconds=int(account['23414611']['ElapsedRaw']),
        failed_allocation_seconds=int(account['23414452']['ElapsedRaw']),
        both_allocations_seconds=sum(int(account[j]['ElapsedRaw']) for j in ('23414611','23414452')),
        allocation_minus_process_seconds=int(account['23414611']['ElapsedRaw'])-receipt['total_seconds'],
        allocation_anchored_full_seconds=int(account['23414611']['ElapsedRaw'])-receipt['pruning_seconds']+scaled,
        allocation_anchored_buffered_minutes=math.ceil((int(account['23414611']['ElapsedRaw'])-receipt['pruning_seconds']+scaled)*1.2/60),
        primary_ledger_reconciled=True,
        wall_clock_receipt_seconds=wall,peak_allocated_gib=51.610,peak_allocated_decimal_gb=51.610*1024**3/1e9,
        peak_reserved_gib=53.49,receipt_peak_field_gib=receipt['peak_memory_gb'],
        projection=result,failed_receipt_preserved=str(failed_path),weight_byte_hashing_performed=False)
    output=Path(args.output);output.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ('status','counts','epochs_observed','fixed_seconds','scaled_pruning_seconds','full_500_epoch_seconds','rounded_reservation_minutes','pilot_reserved_minutes')},indent=2))
    print('projection: 3 of 18 seed cells covered, 15 gaps, hold')


if __name__ == '__main__':
    main()
