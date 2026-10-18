"""Bounded runner safety and real tiny-model intervention contracts."""
import copy
import importlib
import json
from types import SimpleNamespace

import numpy as np
import pytest
import torch

from evaluation.selective_diagnostics import build_manifest, content_hash
from tests.test_selective_diagnostics import POOL, Tokenizer, record
from tests.helpers import build_tiny_pair, TINY
from tests.test_generation import StubContext, circuit_masks_for


@pytest.fixture
def api():
    return importlib.import_module('evaluation.selective_runner')


@pytest.fixture
def manifest():
    return build_manifest([record(i) for i in range(8)], POOL, Tokenizer(),
                          n_clusters=4, n_generation_clusters=2, max_new_tokens=3)


def test_smoke_is_work_selection_with_reference_closure(api, manifest):
    rows, refs = api.select_work(manifest, 'smoke')
    selected = {c['cluster_id'] for c in manifest['clusters'][:2]}
    assert rows == [r for r in manifest['rows'] if r['cluster_id'] in selected]
    wanted = {r['donor']['reference_row_id'] for r in rows
              if r['kind'] == 'generation' and r['donor']}
    assert {r['row_id'] for r in refs} == wanted
    assert api.select_work(manifest, 'all')[0] == manifest['rows']


def test_cost_counts_references_and_deduplicated_donor_scores(api, manifest):
    plan = api.work_plan(manifest, 'all')
    assert plan['target_completions'] == 40
    assert plan['donor_reference_completions'] == len(manifest['donor_reference_rows'])
    assert plan['worst_case_new_tokens'] == 3 * (40 + len(manifest['donor_reference_rows']))
    assert plan['donor_score_passes'] == len(api.donor_diagnostics(manifest))
    assert plan['score_passes'] == 72


def test_donor_validity_uses_own_cluster_labels(api, manifest):
    diagnostics = api.donor_diagnostics(manifest)
    clusters = {c['cluster_id']: c for c in manifest['clusters']}
    for d in diagnostics:
        assert d['labels'] == clusters[d['recipient']['cluster_id']]['labels']
    original = [d for d in diagnostics if d['recipient']['view'] == 'original']
    assert len(original) == 4 * len(clusters)


def test_resume_refuses_changed_inputs_and_conflicting_or_duplicate_rows(api, manifest, tmp_path):
    row = manifest['rows'][0]
    store = api.ResultStore(tmp_path, manifest, {'dtype': 'float32'})
    store.append(row, {'value': 1})
    assert row['row_id'] in api.ResultStore(tmp_path, manifest, {'dtype': 'float32'}).results
    with pytest.raises(ValueError, match='fingerprint'):
        api.ResultStore(tmp_path, manifest, {'dtype': 'bfloat16'})
    with pytest.raises(ValueError, match='duplicate'):
        store.append(row, {'value': 1})
    altered = copy.deepcopy(row)
    altered['recipient']['input_ids'][0] += 1
    with pytest.raises(ValueError, match='row'):
        store.append(altered, {})
    with (tmp_path / 'results.jsonl').open('a') as f:
        f.write((tmp_path / 'results.jsonl').read_text().splitlines()[0] + '\n')
    with pytest.raises(ValueError, match='duplicate'):
        api.ResultStore(tmp_path, manifest, {'dtype': 'float32'})


def test_resume_recovers_only_unterminated_tail_and_full_completeness(api, manifest, tmp_path):
    row = manifest['rows'][0]
    store = api.ResultStore(tmp_path, manifest, {})
    store.append(row, {'value': 1})
    with (tmp_path / 'results.jsonl').open('ab') as f:
        f.write(b'{"partial":')
    reopened = api.ResultStore(tmp_path, manifest, {})
    assert list(reopened.results) == [row['row_id']]
    assert (tmp_path / 'results.jsonl').read_bytes().endswith(b'\n')
    summary = api.summarize(manifest, reopened)
    assert not summary['complete']
    assert len(summary['missing_ids']) == len(reopened.expected) - 1


def test_corrupt_complete_record_is_rejected(api, manifest, tmp_path):
    api.ResultStore(tmp_path, manifest, {})
    (tmp_path / 'results.jsonl').write_text('{broken}\n')
    with pytest.raises(ValueError, match='record'):
        api.ResultStore(tmp_path, manifest, {})


def test_resume_refuses_manifest_mismatch(api, manifest, tmp_path):
    api.ResultStore(tmp_path, manifest, {})
    other = copy.deepcopy(manifest)
    other['provenance']['new'] = 'different'
    other['manifest_hash'] = importlib.import_module('evaluation.selective_diagnostics').manifest_hash(other)
    with pytest.raises(ValueError, match='fingerprint'):
        api.ResultStore(tmp_path, other, {})


def test_head_masks_keep_all_mlps_and_random_layer_counts(api):
    _, model = build_tiny_pair()
    masks = circuit_masks_for(model)
    for key in ('mlp_hidden', 'mlp_output'):
        for value in masks[key].values():
            value[:] = 0
    masks['mlp_blocks'][:] = 0
    from evaluation.masks import sample_random_masks
    random = sample_random_masks(masks, num_heads=4, head_dim=16, seed=0, index=0)
    for layer in masks['attention_heads']:
        assert random['attention_heads'][layer].sum() == masks['attention_heads'][layer].sum()
    ko = api.safe_knockout(masks)
    assert all(np.all(v) for key in ('mlp_hidden', 'mlp_output') for v in ko[key].values())
    assert np.all(ko['mlp_blocks'])
    masks['mlp_hidden']['0'][0] = 1
    with pytest.raises(ValueError, match='MLP'):
        api.safe_knockout(masks)


def endpoint(ids, mask=None):
    return {'input_ids': ids, 'attention_mask': mask or [1] * len(ids)}


def test_alignment_accepts_left_padding_rejects_unequal_or_right(api):
    api.aligned_inputs(endpoint([0, 3, 4], [0, 1, 1]), endpoint([0, 6, 7], [0, 1, 1]))
    for donor in (endpoint([6, 7]), endpoint([6, 7, 0], [1, 1, 0])):
        with pytest.raises(ValueError, match='align|padding'):
            api.aligned_inputs(endpoint([0, 3, 4], [0, 1, 1]), donor)


def test_real_tiny_score_self_donor_is_noop_but_nontrivial_donor_changes_logits(api):
    _, model = build_tiny_pair()
    ctx = StubContext(model, torch.tensor([[3, 4, 5]]))
    masks = circuit_masks_for(model)
    for k in ('mlp_hidden', 'mlp_output'):
        for v in masks[k].values(): v[:] = 0
    masks['mlp_blocks'][:] = 0
    row = {'recipient': endpoint([3, 4, 5]), 'donor': None,
           'labels': {'D': {'token_id': 6}, 'H': {'token_id': 7}}}
    ctx.task = api.FrozenTask()
    ctx.cli.reference = 'shared'
    full = api.score_row(ctx, row, None)
    row['donor'] = row['recipient']
    same = api.score_row(ctx, row, api.safe_knockout(masks))
    assert same['D_logit'] == pytest.approx(full['D_logit'], abs=1e-6)
    row['donor'] = endpoint([8, 9, 10])
    changed = api.score_row(ctx, row, api.safe_knockout(masks))
    assert abs(changed['D_logit'] - full['D_logit']) > 1e-6
    assert full['D_probability'] + full['H_probability'] < 0.1
    assert full['D_minus_H'] == pytest.approx(full['D_logit'] - full['H_logit'])
    assert full['argmax_category'] in ('D', 'H', 'other')


def test_metrics_separates_pairwise_preference_from_full_vocab_probability(api):
    from evaluation.metrics import evaluate_pred_position
    class Model(torch.nn.Module):
        def __call__(self, **kwargs):
            return SimpleNamespace(logits=torch.tensor([[[2., 1., 8.]]]))
    ctx = SimpleNamespace(task=api.FrozenTask(), device='cpu', node_model=Model(),
                          reference_model=None, cli=SimpleNamespace(reference='shared'))
    batch = {'input_ids': torch.tensor([[1]]), 'attention_mask': torch.ones(1, 1),
             'target': torch.tensor([0]), 'distractor': torch.tensor([1])}
    out = evaluate_pred_position(ctx, [batch], use_reference=False, collect_per_example=True)
    p = out['per_example'][0]
    assert out['accuracy'] == 1
    assert p['argmax_id'] == 2
    assert p['target_probability'] < .01
    assert p['target_logit'] == 2
    assert p['distractor_logit'] == 1


def test_donor_pack_discloses_eos_tiling_and_no_arbitrary_pad(api):
    stream, flags = api.reference_stream(endpoint([3, 4]), {'token_ids': [7], 'termination': 'eos', 'eos_token_id': 2}, 4, 0)
    assert stream.tolist() == [[3, 4, 7, 2, 7, 2]]
    assert flags['tiled'] and flags['early_eos'] and not flags['truncated']
    assert flags['filler'] == 'continuation'
    stream, flags = api.reference_stream(endpoint([3, 4]), {'token_ids': [], 'termination': 'eos', 'eos_token_id': 2}, 4, 0)
    assert stream.tolist() == [[3, 4, 2, 2, 2, 2]]
    assert flags['empty_continuation']


def test_real_tiny_generation_self_donor_noop(api):
    _, model = build_tiny_pair()
    ctx = StubContext(model, torch.tensor([[3, 4, 5]]))
    masks = circuit_masks_for(model)
    for k in ('mlp_hidden', 'mlp_output'):
        for v in masks[k].values(): v[:] = 0
    masks['mlp_blocks'][:] = 0
    row = {'recipient': endpoint([3, 4, 5]), 'donor': None, 'decode': {'max_new_tokens': 4}}
    full = api.generate_row(ctx, row, None, None, eos_ids=())
    row['donor'] = row['recipient']
    same = api.generate_row(ctx, row, api.safe_knockout(masks), full, eos_ids=())
    assert same['token_ids'] == full['token_ids']
    assert same['termination'] == 'cap'
    assert same['cap_hit'] and not same['empty']
    assert not any(k in same for k in ('deceptive', 'honest', 'failed'))


def test_blind_export_has_no_mask_condition_or_donor_identity(api, manifest, tmp_path):
    store = api.ResultStore(tmp_path / 'run', manifest, {})
    for row in manifest['rows']:
        if row['kind'] == 'generation':
            store.append(row, {'text': 'An answer.', 'token_ids': [3], 'empty': False, 'cap_hit': False,
                               'termination': 'eos', 'repetition_fraction': 0.0, 'donor_secret': 'leak'})
    api.export_blind(manifest, store, tmp_path / 'blind')
    items = [json.loads(s) for s in (tmp_path / 'blind' / 'responses.jsonl').read_text().splitlines()]
    assert len(items) == 40
    assert all(set(i) == {'anonymous_id', 'prompt', 'ground_truth', 'output', 'quality'} for i in items)
    encoded = json.dumps(items)
    for forbidden in ('core_', 'mask_label', 'donor_secret', 'reference_row_id', 'row_id', 'cluster_id'):
        assert forbidden not in encoded
    assert (tmp_path / 'blind' / 'private_mapping.jsonl').exists()


def test_dry_run_does_not_load_model_weights(api, manifest, tmp_path, monkeypatch, capsys):
    cli = importlib.import_module('evaluate_selective_deception')
    frozen = tmp_path / 'manifest.json'
    frozen.write_text(json.dumps(manifest))
    monkeypatch.setattr(cli, 'prepare_identity', lambda args: ({'snapshot': 'fixture'}, Tokenizer(), {}, None))
    monkeypatch.setattr(cli, 'verify_tokenization', lambda *args: None)
    monkeypatch.setattr(cli, 'build_context', lambda *args: pytest.fail('dry-run loaded weights'))
    assert cli.main(['--manifest', str(frozen), '--output-dir', str(tmp_path / 'out'), '--dry-run']) == 0
    assert json.loads(capsys.readouterr().out)['selected_work']['target_completions'] == 40


def test_cached_snapshot_is_required_and_identity_tracks_files(api, tmp_path):
    cli = importlib.import_module('evaluate_selective_deception')
    with pytest.raises(FileNotFoundError):
        cli.cached_snapshot(str(tmp_path / 'missing'))
    (tmp_path / 'config.json').write_text('{}')
    (tmp_path / 'tokenizer.json').write_text('{}')
    (tmp_path / 'generation_config.json').write_text('{"eos_token_id": 2}')
    (tmp_path / 'model.safetensors').write_bytes(b'original')
    before = cli.snapshot_identity(tmp_path)
    (tmp_path / 'tokenizer.json').write_text('{"changed":true}')
    assert before != cli.snapshot_identity(tmp_path)


def test_smoke_then_full_resume_keeps_fingerprint_and_completes_exact_rows(api, manifest, tmp_path, monkeypatch):
    calls = []
    def score(ctx, row, mask):
        calls.append(('score', row['recipient']['input_ids']))
        return {'argmax_category': 'H', 'D_logit': 0., 'H_logit': 1.}
    def generation(ctx, row, mask, reference, **kwargs):
        calls.append(('masked' if mask is not None else 'intact', row['recipient']['input_ids']))
        if mask is not None:
            assert reference is not None
        return {'token_ids': [9], 'text': 'output', 'termination': 'cap', 'cap_hit': True, 'empty': False}
    monkeypatch.setattr(api, 'score_row', score)
    monkeypatch.setattr(api, 'generate_row', generation)
    monkeypatch.setattr(api, 'safe_knockout', lambda mask: mask)
    ctx = SimpleNamespace(node_model=SimpleNamespace(generation_config=SimpleNamespace(eos_token_id=2)))
    store = api.ResultStore(tmp_path, manifest, {'frozen': 1})
    masks = {label: {'fixed': label} for label in ('core', 'd_minus_f', 'random_core_seed0')}
    first = api.execute(manifest, store, ctx, masks, 'smoke')
    assert not first['complete']
    count = len(store.results)
    fingerprint = store.fingerprint
    before = len(calls)
    api.execute(manifest, store, ctx, masks, 'smoke')
    assert len(calls) == before
    reopened = api.ResultStore(tmp_path, manifest, {'frozen': 1})
    final = api.execute(manifest, reopened, ctx, masks, 'all')
    assert final['complete'] and not final['missing_ids']
    assert reopened.fingerprint == fingerprint
    assert len(reopened.results) > count
    assert len(calls) == len(reopened.expected)


def test_cached_weights_do_not_require_unused_hub_readme_files(api, tmp_path, monkeypatch):
    cli = importlib.import_module('evaluate_selective_deception')
    (tmp_path / 'config.json').write_text('{}')
    (tmp_path / 'model.safetensors').write_bytes(b'local')
    import huggingface_hub
    monkeypatch.setattr(huggingface_hub, 'try_to_load_from_cache', lambda *args, **kwargs: str(tmp_path / 'config.json'))
    monkeypatch.setattr(huggingface_hub, 'snapshot_download', lambda *args, **kwargs: pytest.fail('snapshot download attempted'))
    assert cli.cached_snapshot('meta-llama/Llama-3.1-8B-Instruct') == tmp_path


@pytest.mark.parametrize('tail,decode,expected_empty,termination', [
    ([2, 0], 'ignored', True, 'eos'), ([1, 1], '', True, 'cap')])
def test_generation_empty_and_eos_quality_uses_visible_text(api, monkeypatch, tail, decode, expected_empty, termination):
    from contextlib import nullcontext
    from evaluation import gen_engine
    monkeypatch.setattr(gen_engine, 'generate', lambda *args, **kwargs: torch.tensor([[3, 4] + tail]))
    tokenizer = SimpleNamespace(pad_token_id=0, decode=lambda tokens, **kwargs: decode if tokens else '')
    ctx = SimpleNamespace(tokenizer=tokenizer, all_gates_open=nullcontext)
    row = {'recipient': endpoint([3, 4]), 'donor': None, 'decode': {'max_new_tokens': 2}}
    result = api.generate_row(ctx, row, None, None, eos_ids=(2,))
    assert result['empty'] is expected_empty
    assert result['termination'] == termination
    assert result['cap_hit'] == (termination == 'cap')


def test_cli_rejects_concurrent_output_writer_before_loading_model(api, tmp_path):
    import fcntl
    cli = importlib.import_module('evaluate_selective_deception')
    with (tmp_path / 'writer.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ValueError, match='active writer'):
            cli.main(['--manifest', str(tmp_path / 'unused.json'), '--output-dir', str(tmp_path), '--run'])


def test_cli_context_uses_existing_session_and_shared_tiny_model(api, tmp_path, monkeypatch):
    from dataclasses import asdict
    from config import NodePruningConfig
    from evaluation.circuits import CircuitSpec
    from evaluation.context import EvalContext, geometry_from_masks
    from evaluation.masks import count_masks
    from models import ModelAdapter
    cli = importlib.import_module('evaluate_selective_deception')
    _, model = build_tiny_pair()
    model.config._name_or_path = str(tmp_path)
    masks = circuit_masks_for(model)
    for key in ('mlp_hidden', 'mlp_output'):
        for value in masks[key].values(): value[:] = 0
    masks['mlp_blocks'][:] = 0
    spec = CircuitSpec('core__leaf', masks, count_masks(masks), 'leaf')
    config = {'model': 'llama-8b-instruct', 'task': 'sdr', 'node_config': asdict(NodePruningConfig())}
    monkeypatch.setattr(ModelAdapter, 'build_node_model', lambda self, config, device: model)
    ctx = cli.build_context(SimpleNamespace(device='cpu', data_dir=str(tmp_path), output_dir=str(tmp_path)),
                            {'model': {'snapshot': str(tmp_path)}},
                            SimpleNamespace(decode=lambda ids: str(ids)), {'core': masks},
                            ([spec], {'D': str(tmp_path)}, {'D': config}, geometry_from_masks(masks)))
    assert isinstance(ctx, EvalContext)
    assert ctx.session.full_model is None and ctx.cli.reference == 'shared'
    row = {'recipient': endpoint([3, 4, 5]), 'donor': endpoint([8, 9, 10]),
           'labels': {'D': {'token_id': 6}, 'H': {'token_id': 7}}}
    result = api.score_row(ctx, row, api.safe_knockout(masks))
    assert isinstance(result['D_logit'], float)


@pytest.mark.parametrize('activation_status', [0, 23])
def test_slurm_startup_tolerates_rc_failure_but_requires_activation(tmp_path, activation_status):
    import shlex
    import subprocess
    from pathlib import Path

    # A noninteractive rc may contain an incidental failing command before it
    # defines conda. Only successful activation authorizes the runner entry.
    rc = tmp_path / 'fixture.bashrc'
    rc.write_text('false\n'
                  'conda() {\n'
                  '  test "$1" = activate && test "$2" = mgnp || return 97\n'
                  + ('  export SELECTIVE_TEST_ACTIVATED=ready\n' if activation_status == 0 else '')
                  + '  return %d\n}\n' % activation_status)
    original = (Path(__file__).resolve().parents[1] / 'scripts/selective_deception.sbatch').read_text()
    source = 'source ~/.bashrc'
    entry = 'python evaluate_selective_deception.py "$@"'
    assert original.count(source) == original.count(entry) == 1
    probe = ('test "${SELECTIVE_TEST_ACTIVATED:-}" = ready\n'
             'printf "runner-entry:%s\\n" "$*"')
    wrapper = tmp_path / 'startup.sh'
    wrapper.write_text(original.replace(source, 'source ' + shlex.quote(str(rc)), 1).replace(entry, probe, 1))
    result = subprocess.run(['bash', str(wrapper), '--manifest', 'fixture.json'],
                            cwd=tmp_path, capture_output=True, text=True, timeout=10)
    if activation_status == 0:
        assert result.returncode == 0, result.stderr
        assert result.stdout == 'runner-entry:--manifest fixture.json\n'
    else:
        assert result.returncode != 0
        assert 'Environment initialization failed' in result.stderr
        assert 'runner-entry:' not in result.stdout
