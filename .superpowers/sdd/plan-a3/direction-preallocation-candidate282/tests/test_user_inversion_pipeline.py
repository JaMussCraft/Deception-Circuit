"""CPU staged artifact and cache integrity tests; never load model weights."""
import json
import sys
from pathlib import Path

import pytest

from tests.fakes import FakeWordTokenizer
from tests.test_user_inversion_v2 import source, pool


def pipeline():
    from dataset import user_inversion_pipeline
    return user_inversion_pipeline


@pytest.fixture
def stage(tmp_path, monkeypatch):
    p = pipeline()
    data = tmp_path / 'data'
    rows = {}
    for arm in ('far_v2', 'far_v2_honest'):
        directory = data / arm
        directory.mkdir(parents=True)
        (directory / 'dataset_config.json').write_text(json.dumps({'model': p.dc.DEFAULT_MODEL, 'task': 'far_v2', 'honest_twin_kind': 'neutral_clause' if arm.endswith('honest') else None, 'margin_thresh': .3 if arm.endswith('honest') else .7, 'condition': 'honest' if arm.endswith('honest') else 'deceptive'}))
        for split in p.SPLITS:
            d, h = source()
            row = dict(h if arm.endswith('honest') else d, instance_id=split,
                       condition='honest' if arm.endswith('honest') else 'deceptive')
            if arm.endswith('honest'):
                row['pressure'] = 'Paperwork filed.'
                for stream in ('clean', 'corrupt'):
                    row[stream + '_prompt'] = row[stream + '_prompt'].replace('Paperwork is filed.', row['pressure'])
            rows[str(directory), split] = [row]
    original_load = p.dc.load_or_generate_deception_data
    monkeypatch.setattr(p.dc, 'load_or_generate_deception_data',
                        lambda directory, split: rows[(str(directory), split)] if (str(directory), split) in rows
                        else original_load(directory, split))
    tok = FakeWordTokenizer()
    request = tmp_path / 'requests.json'
    request.write_text(json.dumps(pool()))
    base = ['--tasks', 'far_v2', '--data-dir', str(data), '--work-dir', str(tmp_path / 'derive'),
            '--score-dir', str(tmp_path / 'scores'), '--request-pool', str(request),
            '--commit', 'a' * 40, '--model-revision', 'model-snapshot', '--tokenizer-revision', 'tok-snapshot']
    calls = []
    def loader(args):
        calls.append('load')
        def score(prompts, words):
            calls.append(len(prompts))
            return [dict(choice='b' if 'knowingly' in prompt else 'a',
                         margin=-.6 if 'knowingly' in prompt else 1.,
                         logit_a=0., logit_b=.6 if 'knowingly' in prompt else -1.,
                         argmax=tok.decode(tok.encode(' ' + word_pair[1 if 'knowingly' in prompt else 0])[0]),
                         argmax_id=tok.encode(' ' + word_pair[1 if 'knowingly' in prompt else 0])[0])
                    for prompt, word_pair in zip(prompts, words)]
        return score
    def run(stage_name, extra=(), load=loader):
        return p.main(['--stage', stage_name] + base + list(extra), tokenizer=tok, model_loader=load)
    run.tokenizer = tok
    run.base = base
    return p, tmp_path, rows, run, calls


def test_derive_never_loads_model(stage):
    p, root, rows, run, calls = stage
    assert run('derive') == 0
    assert calls == []
    for split in p.SPLITS:
        directory = root / 'derive/far_v2' / split
        assert len(p.read_jsonl(directory / 'pairs.jsonl')) == 1
        assert p.read_json(directory / 'derivation_report.json')['accepted'] == 1
    with pytest.raises(ValueError, match='exist'):
        run('derive')


def test_score_round_trip_and_reordered_or_stale_cache_refused(stage):
    p, root, rows, run, calls = stage
    run('derive'); run('score')
    assert calls.count('load') == 1
    assert calls.count(4) == 3
    manifest = p.read_json(root / 'scores/far_v2/test/run_manifest.json')
    assert manifest['command'][0] == sys.executable
    target = root / 'derive/far_v2/train/pairs.jsonl'
    pairs = p.read_jsonl(target)
    pairs[0]['inversion']['clean_prompt'] += ' changed'
    target.write_text(json.dumps(pairs[0]) + '\n')
    with pytest.raises(ValueError, match='hash'):
        run('assemble', ['--output-dir', str(root / 'out')])
    assert not (root / 'out').exists()


def test_threshold_fallback_reuses_scores(stage):
    p, root, rows, run, calls = stage
    run('derive'); run('score')
    run('assemble', ['--output-dir', str(root / 'high')])
    run('assemble', ['--margin', '.5', '--output-dir', str(root / 'low')])
    assert calls.count('load') == 1
    inv = root / 'low/far_v2_user_inversion'
    baseline = root / 'low/far_v2_user_neutral'
    assert (inv / 'scoring_provenance.json').read_bytes() == (baseline / 'scoring_provenance.json').read_bytes()
    from datasets import load_from_disk
    assert len(load_from_disk(str(inv))['test']) == 1
    assert len(load_from_disk(str(root / 'high/far_v2_user_inversion'))['test']) == 0
    config = p.read_json(inv / 'dataset_config.json')
    assert config['margin_thresh'] == .5
    assert config['scoring_provenance']['sha256'] == p.file_hash(inv / 'scoring_provenance.json')
    assert p.read_json(baseline / 'dataset_config.json')['margin_thresh'] == .3


def test_limited_pilot_cannot_assemble_full_pool(stage):
    p, root, rows, run, calls = stage
    run('derive')
    run('score', ['--splits', 'test', '--limit', '32'])
    with pytest.raises(ValueError, match='limited|scope|missing'):
        run('assemble', ['--output-dir', str(root / 'out')])


def test_assemble_uses_no_git_helper(stage, monkeypatch):
    p, root, rows, run, calls = stage
    import subprocess
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: pytest.fail('external command invoked'))
    run('derive'); run('score')
    assert run('assemble', ['--output-dir', str(root / 'out')]) == 0


def test_cross_split_ids_rejected_before_split_filtering(stage):
    p, root, rows, run, calls = stage
    for (directory, split), records in rows.items():
        records[0]['instance_id'] = 'duplicate'
    with pytest.raises(ValueError, match='cross.split'):
        run('derive', ['--splits', 'test'])


def test_score_protected_registry_and_native_allocation_guard(stage, monkeypatch):
    p, root, rows, run, calls = stage
    run('derive')
    monkeypatch.delenv('SLURM_JOB_ID', raising=False)
    with pytest.raises(ValueError, match='Slurm'):
        run('score', load=None)
    assert calls == []


def test_partial_assembly_refused(stage):
    p, root, rows, run, calls = stage
    run('derive'); run('score')
    with pytest.raises(ValueError, match='scope|splits'):
        run('assemble', ['--splits', 'test', '--output-dir', str(root / 'out')])


def test_registered_ids_are_checked_from_primary_and_worktree(stage, monkeypatch):
    p, root, rows, run, calls = stage
    run('derive')
    registered = root / 'primary/data/heldout/frozen.json'
    registered.parent.mkdir(parents=True)
    registered.write_text(json.dumps(['test']))
    registry = root / 'primary/docs/research/held_out.json'
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({'schema': 1, 'sets': [{'task': 'far_v2', 'path': 'data/heldout/frozen.json',
                                                        'sha256': p.file_hash(registered), 'n': 1}]}))
    monkeypatch.setattr(p, 'PRIMARY_REGISTRY', registry)
    with pytest.raises(ValueError, match='protected.*overlap'):
        run('score')
    assert calls == []


def test_score_reordering_detected_even_with_updated_file_hash(stage):
    p, root, rows, run, calls = stage
    for key, records in rows.items():
        records.append(dict(records[0], instance_id=records[0]['instance_id'] + '-second'))
    run('derive'); run('score')
    score_file = root / 'scores/far_v2/test/scores.jsonl'
    p.write_jsonl(score_file, list(reversed(p.read_jsonl(score_file))))
    manifest_path = score_file.with_name('run_manifest.json')
    manifest = p.read_json(manifest_path)
    manifest['files']['scores.jsonl'] = p.file_hash(score_file)
    p.write_json(manifest_path, manifest)
    with pytest.raises(ValueError, match='reordered'):
        run('assemble', ['--output-dir', str(root / 'out')])


def test_mismatched_source_hash_and_tokenizer_revision_fail_before_load(stage):
    p, root, rows, run, calls = stage
    run('derive')
    with pytest.raises(ValueError, match='tokenizer'):
        run('score', ['--tokenizer-revision', 'another-snapshot'])
    rows[next(iter(rows))][0]['pressure'] = 'Changed source'
    with pytest.raises(ValueError, match='source hash'):
        run('score')
    assert calls == []


def test_assembled_receipt_passes_actual_a2_consumer(stage):
    p, root, rows, run, calls = stage
    run('derive'); run('score')
    run('assemble', ['--margin', '.5', '--output-dir', str(root / 'assembled')])
    from dataset.build_twin_training import materialize
    result = materialize(root_d=str(root / 'data'), root_h=str(root / 'data'), root_i=None,
                         root_i_neutral=None, input_paths={'far_v2': {
                             'I': str(root / 'assembled/far_v2_user_inversion'),
                             'I_neutral': str(root / 'assembled/far_v2_user_neutral')}},
                         output_root=str(root / 'consumer'), tasks=['far_v2'], cohort='matched',
                         tokenizer=run.tokenizer, max_length=256, commit='a' * 40, validate_only=True)
    assert result['fleet_ready'] is True


def test_pilot_repeats_native_baseline_scores_without_new_model(stage):
    p, root, rows, run, calls = stage
    run('derive'); run('score', ['--splits', 'test', '--limit', '32'])
    assert calls == ['load', 4, 2]
    manifest = p.read_json(root / 'scores/far_v2/test/run_manifest.json')
    assert manifest['baseline_repeat']['compared'] == 2
    assert manifest['baseline_repeat']['choice_agreement'] == 2
    assert manifest['baseline_repeat']['within_tolerance'] == 2


def test_filter_report_preserves_strata_and_test_gate(stage):
    p, root, rows, run, calls = stage
    run('derive'); run('score')
    run('assemble', ['--margin', '.5', '--output-dir', str(root / 'out')])
    report = p.read_json(root / 'out/far_v2_user_inversion/filter_report.json')['test']
    assert report['raw_count'] == report['derived_count'] == 1
    assert report['by_pressure_id']['p']['retained'] == 1
    assert report['pool_gate']['unique_ids'] == 1
    assert report['pool_gate']['required'] == 300
    assert report['pool_gate']['passes'] is False


def test_score_dry_run_checks_inputs_without_loading_or_writing(stage):
    p, root, rows, run, calls = stage
    run('derive')
    assert run('score', ['--dry-run']) == 0
    assert calls == []
    assert not (root / 'scores').exists()
    pairs = root / 'derive/far_v2/test/pairs.jsonl'
    pairs.write_text(pairs.read_text() + '\n')
    with pytest.raises(ValueError, match='hash'):
        run('score', ['--dry-run'])
    assert calls == []


def test_base_tokenizer_loader_is_local_and_records_canonical_normalization(monkeypatch, tmp_path):
    p = pipeline()
    from types import SimpleNamespace
    import transformers
    import huggingface_hub
    snapshot = tmp_path / ('b' * 40)
    snapshot.mkdir()
    (snapshot / 'tokenizer_config.json').write_text('{}')
    monkeypatch.setattr(transformers, '__version__', '4.57.3')
    monkeypatch.setattr(huggingface_hub, 'model_info', lambda *a, **k: pytest.fail('online heuristic called'))
    def cached(model, filename, **kwargs):
        assert kwargs['local_files_only'] is True
        return str(snapshot / filename)
    monkeypatch.setattr(huggingface_hub, 'hf_hub_download', cached)
    def load(identifier, **kwargs):
        assert identifier == str(snapshot), 'must bypass broken canonical-ID heuristic on base4.57.3'
        assert kwargs['local_files_only'] is True
        return SimpleNamespace(name_or_path=identifier, pad_token='pad')
    monkeypatch.setattr(transformers.AutoTokenizer, 'from_pretrained', load)
    tok = p.load_tokenizer(SimpleNamespace(model=p.dc.DEFAULT_MODEL, tokenizer_revision='b' * 40))
    assert tok.name_or_path == p.dc.DEFAULT_MODEL
    assert tok._user_inversion_loading['actual_load_path'] == str(snapshot)
    assert tok._user_inversion_loading['identity_normalized'] is True
