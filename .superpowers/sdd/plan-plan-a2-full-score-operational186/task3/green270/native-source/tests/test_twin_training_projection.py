"""Synthetic timing fixtures test arithmetic only; these are not measurements."""
import itertools
import json
import subprocess
import sys

import pytest

from scripts import twin_training_projection as projection
from scripts.twin_training import GATE_FLAGS, expected_config


def fixture():
    config = json.loads(projection.CONFIG.read_text())
    manifest = dict(schema_version=1, fleet_ready=True, cohort='matched', source_commit='a'*40,
                    max_seq_length=120, tokenizer={'name': 'llama'}, tasks={})
    for task in config['tasks']:
        ids = {s: [s+str(i) for i in range(n)] for s, n in config['sample_caps'].items()}
        manifest['tasks'][task] = dict(split_ids=ids, counts={s: len(v) for s,v in ids.items()},
            sources={k: {'config': {'margin_thresh': .5 if k == 'I' else .3,
                'model': 'llama', 'baseline_kind': 'matched_frame_neutral_request'}} for k in ('D','H','I','I_neutral')},
            a1_scoring={'provenance': 'recorded'})
    manifest['build_hash'] = projection.digest(manifest)
    hardware = dict(gpu_devices=['NVIDIA H200, 143771 MiB'], gpu_count=1, cluster='delta')
    plan = dict(config=config, build_manifest=manifest, hardware=hardware,
                source_hashes={'train.py': 'b'*64}, execution_commit='e'*40)
    receipts = []
    for task, condition, seed in itertools.product(config['tasks'], config['conditions'], config['seeds']):
        selected = manifest['tasks'][task]['split_ids']
        receipts.append(dict(task=task, condition=condition, seed=seed, model=config['model'],
            status='success', exit_code=0, errors=[], total_seconds=1200, pruning_seconds=600,
            actual_epochs=20, planned_epochs=500, purpose='timing-only', fleet_ready=True, cohort='matched',
            source_commit=manifest['source_commit'], execution_commit='e'*40, build_hash=manifest['build_hash'],
            build_manifest_sha256=projection.digest(manifest), frozen_config_sha256=projection.digest(config),
            source_hashes=plan['source_hashes'], resolved_config_sha256='c'*64,
            dataset_config_sha256={'D':'d'*64,'I':'e'*64}, selected_ids=selected,
            counts={s:len(v) for s,v in selected.items()}, max_seq_length=120, granularity='heads-mlp',
            gpu_devices=hardware['gpu_devices'], gpu_count=1, environment={'SLURM_CLUSTER_NAME':'delta','SLURM_JOB_ID':'1'},
            artifact_sha256={name:'f'*64 for name in projection.ARTIFACTS}))
    for r in receipts:
        values = dict(model=config['model'], task=r['task'], seed=r['seed'], node_epochs=20,
            data_dir='/private/'+r['condition'], deception_condition='deceptive',
            max_seq_length=120, train_samples=200, val_samples=200, test_samples=1000,
            **{k:config[k] for k in ('node_lambda_sparsity','lr','batch_size','faithfulness_weight','deception_margin_loss')})
        r['argv'] = ['python','train.py'] + [x for k,v in values.items() for x in ('--'+k.replace('_','-'),str(v))] + GATE_FLAGS
        r['resolved_config_sha256'] = projection.digest(expected_config(r['argv']))
    return plan, receipts


def test_full_process_extrapolation_and_rounding():
    plan, receipts = fixture()
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=2)
    assert result['cells'][0]['estimated_seconds'] == 15600
    assert result['cells'][0]['reserved_minutes'] == 312
    assert result['total_reserved_gpu_hours'] == pytest.approx(95.6)
    assert result['single_mask_over_6h'] is False
    assert not result['within_60h'] and not result['fleet_reservation_allowed']


def test_exact_cap_passes_and_pilot_cost_includes_failures():
    plan, receipts = fixture()
    for receipt in receipts:
        receipt.update(total_seconds=500, pruning_seconds=100)  # 2900s -> 58 minutes
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=42.6)
    assert result['total_reserved_gpu_hours'] == pytest.approx(60)
    assert result['fleet_reservation_allowed']
    failed = dict(receipts[0], status='failed', exit_code=1)
    assert projection.project_reserved(receipts+[failed], plan, pilot_reserved_gpu_hours=43)['within_60h'] is False


@pytest.mark.parametrize('key,value', [('total_seconds',0), ('pruning_seconds',-1), ('total_seconds',float('nan')),
    ('pruning_seconds',float('inf')), ('pruning_seconds',1300), ('actual_epochs',9), ('test_runner_injected',True),
    ('status','failed'), ('exit_code',1), ('gpu_devices',['A40']), ('source_hashes',{}),
    ('resolved_config_sha256',None), ('dataset_config_sha256',{}), ('artifact_sha256',{}),
    ('max_seq_length',119), ('counts',{'train':1}), ('selected_ids',{}), ('granularity','heads-only')])
def test_invalid_receipt_cannot_cover_cell(key, value):
    plan, receipts = fixture()
    receipts = [r for r in receipts if r['seed']==42]
    receipts[0][key] = value
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert not result['fleet_reservation_allowed']
    assert len(result['coverage_gaps']) == 3
    assert result['rejected_receipts']


def test_missing_condition_receipt_leaves_three_seed_gaps():
    plan, receipts = fixture()
    result = projection.project_reserved([r for r in receipts if not (r['task']=='ser_v2' and r['condition']=='I')]+[receipts[0]], plan, pilot_reserved_gpu_hours=1)
    assert len(result['coverage_gaps']) == 3
    assert not result['fleet_reservation_allowed']


def test_seed_only_reuse_is_reported_for_all_18_cells():
    plan, receipts = fixture()
    result = projection.project_reserved([r for r in receipts if r['seed']==42], plan, pilot_reserved_gpu_hours=1)
    assert len(result['cells']) == 18 and not result['coverage_gaps']
    assert all(r['coverage_source_receipt']['seed'] == 42 for r in result['cells'])


@pytest.mark.parametrize('amount', [None,0,-1,float('nan'),float('inf'),True])
def test_invalid_pilot_reserve_rejected(amount):
    plan, receipts = fixture()
    with pytest.raises(ValueError, match='pilot'):
        projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=amount)


def test_missing_pilot_reserve_cannot_default():
    with pytest.raises(TypeError):
        projection.project_reserved([], {})


@pytest.mark.parametrize('field,value', [('seeds',[42,1]), ('conditions',['D']), ('tasks',['far_v2']), ('deception_margin_loss',.5)])
def test_plan_must_freeze_full_18_cells_and_common_margin(field,value):
    plan, receipts = fixture()
    plan['config'][field] = value
    with pytest.raises(ValueError):
        projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)


def test_d_only_can_show_estimates_but_never_fleet_approval():
    plan, receipts = fixture()
    manifest = plan['build_manifest']
    manifest.update(fleet_ready=False, cohort='timing-d-only')
    manifest['build_hash'] = projection.digest({k:v for k,v in manifest.items() if k != 'build_hash'})
    receipts = [dict(r, fleet_ready=False, cohort='timing-d-only', build_hash=manifest['build_hash'],
                     build_manifest_sha256=projection.digest(manifest)) for r in receipts if r['condition']=='D']
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert len(result['cells']) == 9 and len(result['coverage_gaps']) == 9
    assert not result['fleet_reservation_allowed']


def test_six_hour_trigger_uses_unbuffered_time_and_requires_separate_fallback():
    plan, receipts = fixture()
    for r in receipts:
        r.update(total_seconds=900, pruning_seconds=900, actual_epochs=20)
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert result['single_mask_over_6h']
    assert result['recommendation'] == 'measure-heads-only-pilot'
    assert not result['fleet_reservation_allowed']
    plan['granularity'] = 'heads-only'
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert not result['cells'] and not result['fleet_reservation_allowed']


def test_cli_requires_pilot_reserve():
    run = subprocess.run([sys.executable, '-m', 'scripts.twin_training_projection', '--help'], capture_output=True, text=True)
    assert run.returncode == 0 and '--pilot-reserved-gpu-hours' in run.stdout


@pytest.mark.parametrize('change', ['batch','hash','gate','no-argv'])
def test_resolved_argv_must_match_training_plan(change):
    plan, receipts = fixture()
    receipts = [r for r in receipts if r['seed']==42]
    r = receipts[0]
    if change=='batch':
        r['argv'][r['argv'].index('--batch-size')+1] = '1'
        r['resolved_config_sha256'] = projection.digest(expected_config(r['argv']))
    elif change=='hash':
        r['resolved_config_sha256'] = 'a'*64
    elif change=='gate':
        r['argv'].remove('--prune-mlp-blocks')
    else:
        r.pop('argv')
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert len(result['coverage_gaps'])==3 and not result['fleet_reservation_allowed']


def test_heads_only_has_separate_measured_coverage_and_budget():
    plan, receipts = fixture()
    plan['granularity'] = 'heads-only'
    for r in receipts:
        r['granularity'] = 'heads-only'
        r['argv'] = ['--no-prune-mlp-blocks' if x=='--prune-mlp-blocks' else x for x in r['argv']]
        resolved = expected_config(r['argv'])
        resolved['node_config']['prune_mlp_blocks'] = False
        r['resolved_config_sha256'] = projection.digest(resolved)
        r.update(total_seconds=500, pruning_seconds=100)
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert result['fleet_reservation_allowed'] and result['granularity']=='heads-only'
    assert not projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=60)['fleet_reservation_allowed']


def test_six_hour_boundary_does_not_trigger_from_buffer():
    plan, receipts = fixture()
    for r in receipts:
        r.update(total_seconds=864, pruning_seconds=864)
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert result['cells'][0]['estimated_seconds']==21600
    assert result['cells'][0]['reserved_minutes']==432
    assert not result['single_mask_over_6h'] and not result['within_60h']


@pytest.mark.parametrize('fraction', [-.1,float('nan'),float('inf'),True])
def test_invalid_buffer_rejected(fraction):
    plan, receipts = fixture()
    with pytest.raises(ValueError):
        projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1, buffer_fraction=fraction)


@pytest.mark.parametrize('entry', [('scripts.twin_training_projection',), ('scripts.twin_training','--stage','project')])
@pytest.mark.parametrize('ruling_mode', ['none','valid','stale','malformed','missing'])
def test_cli_offline_json_gate(tmp_path, entry, ruling_mode):
    plan, receipts = fixture() if ruling_mode=='none' else reviewed_fixture()
    config = plan['config']
    config['data_root'] = str(tmp_path)
    repo = projection.CONFIG.parents[2]
    for r in receipts:
        r['source_hashes'] = {s:projection.hashlib.sha256((repo/s).read_bytes()).hexdigest() for s in projection.SOURCES}
        r['frozen_config_sha256'] = projection.digest(config)
        r['argv'][r['argv'].index('--data-dir')+1] = str(tmp_path/r['condition'])
        r['resolved_config_sha256'] = projection.digest(expected_config(r['argv']))
        r.update(total_seconds=500, pruning_seconds=100)
    cp, mp, rp = [tmp_path/name for name in ('config.json','manifest.json','receipts.json')]
    cp.write_text(json.dumps(config))
    mp.write_text(json.dumps(plan['build_manifest']))
    # CLI reads one wrapper receipt per path, and seed-only coverage requires six.
    paths = []
    for i,r in enumerate(receipts):
        if r['seed']==42:
            path = tmp_path/('receipt'+str(i)+'.json')
            path.write_text(json.dumps(r))
            paths.append(str(path))
    ruling_args = []
    if ruling_mode != 'none':
        ruling_path = tmp_path/'ruling.json'
        ruling = plan['cohort_ruling']
        if ruling_mode == 'stale':
            ruling['build_hash'] = 'a'*64
        if ruling_mode != 'missing':
            ruling_path.write_text('{' if ruling_mode == 'malformed' else json.dumps(ruling))
        ruling_args = ['--cohort-ruling', str(ruling_path)]
    before = set(tmp_path.iterdir())
    run = subprocess.run([sys.executable,'-m',*entry,*ruling_args,'--receipts',*paths,
        '--config',str(cp),'--build-manifest',str(mp),'--pilot-reserved-gpu-hours','1'], capture_output=True,text=True)
    expected = ruling_mode in ('none','valid')
    assert run.returncode == (0 if expected else 2), run.stderr+run.stdout
    result = json.loads(run.stdout)
    assert result['fleet_reservation_allowed'] == expected
    if expected:
        assert len(result['cells']) == 18
    else:
        assert result['recommendation'] == 'hold' and result['error']
    assert set(tmp_path.iterdir())==before


def test_above_cap_even_by_tiny_amount_blocks():
    plan, receipts = fixture()
    for r in receipts:
        r.update(total_seconds=500, pruning_seconds=100)
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=42.60000000001)
    assert not result['within_60h'] and not result['fleet_reservation_allowed']


def test_unicode_build_metadata_uses_materializer_hash_and_wrapper_receipt_hash():
    plan, receipts = fixture()
    manifest = plan['build_manifest']
    manifest['tasks']['far_v2']['sources']['D']['config']['description'] = 'neutral twin — source metadata'
    body = {k:v for k,v in manifest.items() if k != 'build_hash'}
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    manifest['build_hash'] = projection.hashlib.sha256(canonical).hexdigest()
    # The wrapper uses a separate ASCII-escaped digest for the entire receipt
    # manifest; preserving this distinction prevents a global hash migration.
    wrapper_hash = projection.digest(manifest)
    assert wrapper_hash != projection.hashlib.sha256(json.dumps(
        manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    for r in receipts:
        r.update(build_hash=manifest['build_hash'], build_manifest_sha256=wrapper_hash,
                 total_seconds=500, pruning_seconds=100)
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert result['fleet_reservation_allowed'] and not result['coverage_gaps']
    receipts[0]['build_manifest_sha256'] = projection.hashlib.sha256(json.dumps(
        manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert not result['fleet_reservation_allowed']
    assert result['rejected_receipts'][0]['reason']=='receipt mismatch: build_manifest_sha256'


def reviewed_fixture():
    plan, receipts = fixture()
    manifest = plan['build_manifest']
    counts = {'far_v2': (177,177,891), 'sdr_v2': (187,187,952), 'ser_v2': (168,167,835)}
    for task, sizes in counts.items():
        info = manifest['tasks'][task]
        info['split_ids'] = {s:info['split_ids'][s][:n] for s,n in zip(projection.SPLITS,sizes)}
        info['counts'] = {s:len(ids) for s,ids in info['split_ids'].items()}
    manifest['build_hash'] = projection.build_digest({k:v for k,v in manifest.items() if k!='build_hash'})
    plan['cohort_ruling'] = dict(schema_version=1, ruling_id='a2-matched-cohort-01',
        session='codex-01a1987e', decision='accept_exact_matched_cohort',
        scope='cohort_size_only', selection_rule='all_matched_survivors_no_baseline_competence_filter',
        conditions=['D','I'], build_hash=manifest['build_hash'],
        selected_ids_sha256=projection.digest({t:v['split_ids'] for t,v in manifest['tasks'].items()}),
        counts={t:v['counts'] for t,v in manifest['tasks'].items()}, rationale='Accept all matched survivors.')
    for r in receipts:
        selected = manifest['tasks'][r['task']]['split_ids']
        r.update(selected_ids=selected, counts={s:len(v) for s,v in selected.items()},
                 build_hash=manifest['build_hash'], build_manifest_sha256=projection.digest(manifest),
                 total_seconds=500, pruning_seconds=100)
        for flag,split in (('--train-samples','train'),('--val-samples','validation'),('--test-samples','test')):
            r['argv'][r['argv'].index(flag)+1] = str(len(selected[split]))
        r['resolved_config_sha256'] = projection.digest(expected_config(r['argv']))
    return plan, receipts


def test_exact_cohort_ruling_clears_only_review_requirement():
    plan, receipts = reviewed_fixture()
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert result['fleet_reservation_allowed']
    assert result['train_under_200'] is True
    assert result['train_under_200_requires_lead_review'] is False
    assert result['cohort_ruling_sha256'] == projection.digest(plan['cohort_ruling'])
    plan.pop('cohort_ruling')
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert result['train_under_200_requires_lead_review'] is True
    assert result['cohort_ruling_sha256'] is None
    assert not result['fleet_reservation_allowed']


@pytest.mark.parametrize('field,value', [
    ('schema_version',True), ('schema_version',2), ('decision','approve'),
    ('scope','all_gates'), ('build_hash','a'*64), ('selected_ids_sha256','a'*64),
    ('counts',{}), ('conditions',['I','D']), ('session',''),
    ('ruling_id',''), ('selection_rule','baseline_competence'),
    ('rationale',''), ('extra','plausible'), ('counts',{'far_v2':{'train':True}})])
def test_malformed_or_foreign_cohort_ruling_fails_closed(field,value):
    plan, receipts = reviewed_fixture()
    plan['cohort_ruling'][field] = value
    with pytest.raises(ValueError, match='cohort ruling'):
        projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)


@pytest.mark.parametrize('change', ['order','count','build','not-matched'])
def test_cohort_ruling_cannot_follow_changed_plan(change):
    plan, receipts = reviewed_fixture()
    manifest = plan['build_manifest']
    if change=='order':
        manifest['tasks']['far_v2']['split_ids']['train'].reverse()
    elif change=='count':
        info = manifest['tasks']['far_v2']
        info['split_ids']['train'].pop()
        info['counts']['train'] -= 1
    elif change=='build':
        manifest['max_seq_length'] += 1
    else:
        manifest['fleet_ready'] = False
    manifest['build_hash'] = projection.build_digest({k:v for k,v in manifest.items() if k!='build_hash'})
    # Even a plausible updated build binding cannot hide changed ordered IDs/counts.
    if change in ('order','count'):
        plan['cohort_ruling']['build_hash'] = manifest['build_hash']
    with pytest.raises(ValueError, match='cohort ruling'):
        projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)


@pytest.mark.parametrize('gate', ['coverage','receipt','budget','six-hour','hardware'])
def test_cohort_ruling_never_clears_other_gates(gate):
    plan, receipts = reviewed_fixture()
    reserve = 1
    if gate=='coverage':
        receipts = receipts[:1]
    elif gate=='receipt':
        receipts[0]['status'] = 'failed'
    elif gate=='budget':
        reserve = 60
    elif gate=='six-hour':
        for r in receipts:
            r.update(total_seconds=900, pruning_seconds=900)
    else:
        receipts[0]['gpu_devices'] = ['A40']
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=reserve)
    assert not result['fleet_reservation_allowed']
    assert not result['train_under_200_requires_lead_review']


@pytest.mark.parametrize('value', [None, 'short', 'a'*39, 'A'*40, 'f'*40])
def test_execution_revision_missing_or_foreign_blocks_projection(value):
    plan, receipts = fixture()
    for r in receipts:
        r.update(total_seconds=500, pruning_seconds=100)
    receipts[0]['execution_commit'] = value
    result = projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)
    assert not result['fleet_reservation_allowed']
    assert result['rejected_receipts']


def test_mixed_execution_revisions_hold_even_without_plan_revision():
    plan, receipts = fixture()
    plan.pop('execution_commit')
    for r in receipts:
        r.update(total_seconds=500, pruning_seconds=100)
    receipts[0]['execution_commit'] = 'f'*40
    assert not projection.project_reserved(receipts, plan, pilot_reserved_gpu_hours=1)['fleet_reservation_allowed']
