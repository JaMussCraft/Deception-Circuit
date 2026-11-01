"""CPU acceptance tests for user-turn transparent inversion construction."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tests.fakes import FakeWordTokenizer

REPO = Path(__file__).resolve().parents[1]


def builder():
    from dataset import build_user_inversion_v2
    return build_user_inversion_v2


def pool():
    return json.loads((REPO / 'dataset/user_inversion_requests_v2.json').read_text())


def source():
    shell = ('<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n'
             'Review beams and joints. The {item} result failed. {clause}<|eot_id|>'
             '<|start_header_id|>user<|end_header_id|>\n\n'
             'Which failed? Use the stated format.<|eot_id|>'
             '<|start_header_id|>assistant<|end_header_id|>\n\nThe result is')
    d = dict(instance_id='a', task='far_v2', pressure_id='p', pressure='Answer falsely.',
             clean_item_d='beams', corrupt_item_d='joints', target='joints',
             distractor='beams', clean_margin=2, h_pressure_clean=-2, prior_margin=0)
    for stream, item in [('clean', 'beams'), ('corrupt', 'joints')]:
        d[stream + '_prompt'] = shell.format(item=item, clause=d['pressure'])
    d['neutral_prompt'] = 'old prior prompt'
    h = dict(d, pressure='Paperwork is filed.', target='beams', distractor='joints',
             honest_twin_kind='neutral_clause')
    for stream in ('clean', 'corrupt'):
        h[stream + '_prompt'] = d[stream + '_prompt'].replace(d['pressure'], h['pressure'])
    return d, h


def test_roles_and_original_twins_unchanged():
    d, h = source()
    before = copy.deepcopy((d, h))
    pairs, report = builder().derive_pairs(FakeWordTokenizer(), 'far_v2', [d], [h], pool())
    assert (d, h) == before
    assert report['accepted'] == 1
    pair = pairs[0]
    for arm, labels in [('inversion', d), ('baseline', h)]:
        row = pair[arm]
        assert row['target'] == labels['target']
        assert row['distractor'] == labels['distractor']
        assert row['pressure'] == h['pressure']
        assert row['source_neutral_prompt'] == labels['neutral_prompt']
        assert 'neutral_prompt' not in row
        assert not any(k.endswith('_margin') or k.startswith('h_') for k in row)
        prompt = row['clean_prompt']
        system, user = prompt.split('<|eot_id|>', 1)
        assert d['pressure'] not in system
        assert row['request_text'] not in system
        assert user.count(row['request_text']) == 1
        assert row['baseline_kind'] == 'matched_frame_neutral_request'
    assert pair['source_row_hashes']['D'] != pair['source_row_hashes']['H']


def test_task_aware_requests():
    entries = {r['task']: r for r in pool()}
    assert set(entries) == {'far_v2', 'sdr_v2', 'ser_v2'}
    for task, entry in entries.items():
        assert 'For this quiz' in entry['inversion_request']
        assert 'I understand' in entry['neutral_request']
        assert 'honestly' not in entry['neutral_request']
        if task != 'far_v2':
            assert 'wrong' not in entry['inversion_request']
    assert 'harmless result instead of the critical' in entries['sdr_v2']['inversion_request']
    assert 'favorable result instead of the unfavorable' in entries['ser_v2']['inversion_request']


def test_both_streams_align_only_in_request():
    tok = FakeWordTokenizer()
    d, h = source()
    pairs, report = builder().derive_pairs(tok, 'far_v2', [d], [h], pool())
    pair = pairs[0]
    for stream in ('clean', 'corrupt'):
        a, b = [tok.encode(pair[arm][stream + '_prompt']) for arm in ('inversion', 'baseline')]
        start, end = pair['stream_metadata'][stream]['request_span']
        assert len(a) == len(b) <= 256
        assert a[:start] == b[:start] and a[end:] == b[end:]
        assert end <= len(a) - 1
        assert pair['stream_metadata'][stream]['readout'] == len(a) - 1
    assert builder().derive_pairs(tok, 'far_v2', [d], [h], pool()) == (pairs, report)


@pytest.mark.parametrize('bad', ['duplicate_d', 'duplicate_h', 'missing_h', 'extra_h', 'pressure', 'kind', 'prompt', 'labels'])
def test_duplicate_missing_or_wrong_pressure_id_rejected(bad):
    d, h = source()
    ds, hs = [d], [h]
    if bad == 'duplicate_d': ds.append(dict(d))
    if bad == 'duplicate_h': hs.append(dict(h))
    if bad == 'missing_h': hs.clear()
    if bad == 'extra_h': hs.append(dict(h, instance_id='extra'))
    if bad == 'pressure': h['pressure_id'] = 'other'
    if bad == 'kind': h['honest_twin_kind'] = 'instruction'
    if bad == 'prompt': h['corrupt_prompt'] += 'changed'
    if bad == 'labels': h['target'] = d['target']
    with pytest.raises(ValueError):
        builder().derive_pairs(FakeWordTokenizer(), 'far_v2', ds, hs, pool())


def test_rejections_are_explicit_and_optimized_python_refused():
    d, h = source()
    pairs, report = builder().derive_pairs(FakeWordTokenizer(), 'far_v2', [d], [h], pool(), max_seq_length=5)
    assert not pairs and report['rejected'][0]['instance_id'] == 'a'
    code = ('from dataset.build_user_inversion_v2 import derive_pairs; '
            'derive_pairs(None,"far_v2",[],[],[])')
    p = subprocess.run([sys.executable, '-O', '-c', code], cwd=str(REPO), capture_output=True, text=True)
    assert p.returncode != 0 and 'without -O' in p.stderr


def test_real_tokenizer_all_source_rows():
    from datasets import load_from_disk
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained('meta-llama/Llama-3.1-8B-Instruct', local_files_only=True)
    counts = {}
    for task in ('far_v2', 'sdr_v2', 'ser_v2'):
        ds = load_from_disk(str(REPO / 'data/datasets' / task))
        hs = load_from_disk(str(REPO / 'data/datasets' / (task + '_honest')))
        counts[task] = {}
        seen = set()
        for split in ds:
            pairs, report = builder().derive_pairs(tok, task, list(ds[split]), list(hs[split]), pool())
            assert report['source_count'] == len(ds[split])
            assert len(pairs) + len(report['rejected']) == len(ds[split])
            assert len(pairs) > 0
            ids = {p['instance_id'] for p in pairs}
            assert not (seen & ids)
            seen.update(ids)
            counts[task][split] = report
    print('REAL_TOKENIZER_DERIVATION=' + json.dumps(counts, sort_keys=True))


def test_padding_prefers_fewer_repetitions_at_equal_added_tokens():
    d, h = source()
    requests = [dict(id='short', task='far_v2', inversion_request='Quizzical',
                     neutral_request='Quizzical b c d e f g')]
    pairs, _ = builder().derive_pairs(FakeWordTokenizer(), 'far_v2', [d], [h], requests)
    assert pairs[0]['padding']['inversion'] == [1, 0]
    assert pairs[0]['padding']['baseline'] == [0, 0]
    assert pairs[0]['padding']['total_added_tokens'] == 6


def test_ser_wording_a_is_rejected_before_true_selection_claim():
    d, h = source()
    for row in (d, h):
        row['task'] = 'ser_v2'
        row['ser_wording'] = 'A'
    with pytest.raises(ValueError, match='SER wording B'):
        builder().derive_pairs(FakeWordTokenizer(), 'ser_v2', [d], [h], pool())


def test_source_argmax_choice_and_answer_tokens_are_metadata_only():
    d, h = source()
    old = dict(clean_argmax='beams', corrupt_choice='b', target_token=7,
               distractor_token=8, clean_readout=99, score=2.5)
    d.update(old)
    h.update(old)
    pairs, _ = builder().derive_pairs(FakeWordTokenizer(), 'far_v2', [d], [h], pool())
    for arm in ('inversion', 'baseline'):
        assert not (set(old) & pairs[0][arm].keys())
    for label in ('D', 'H'):
        assert all(pairs[0]['source_behavior'][label][k] == v for k, v in old.items())


@pytest.mark.parametrize('noun', ['result', 'reading'])
def test_ser_wording_b_supports_both_stored_template_stems(noun):
    d, h = source()
    for row in (d, h):
        row.update(task='ser_v2', ser_wording='B')
        for stream in ('clean', 'corrupt'):
            row[stream + '_prompt'] = row[stream + '_prompt'].rsplit('The result is', 1)[0] + 'The ' + noun + ' you should check is'
    requests = [dict(id='ser-test', task='ser_v2', inversion_request='quiz choose other',
                     neutral_request='quiz answer question')]
    pairs, _ = builder().derive_pairs(FakeWordTokenizer(), 'ser_v2', [d], [h], requests)
    assert len(pairs) == 1


def test_duplicate_unpadded_request_cannot_be_hidden_by_padding():
    d, h = source()
    text = pool()[0]['inversion_request']
    for row in (d, h):
        for stream in ('clean', 'corrupt'):
            prompt = row[stream + '_prompt']
            before, assistant = prompt.rsplit('<|eot_id|>', 1)
            row[stream + '_prompt'] = before + ' ' + text + '<|eot_id|>' + assistant
    pairs, report = builder().derive_pairs(FakeWordTokenizer(), 'far_v2', [d], [h], pool())
    assert not pairs
    assert 'duplicate request text' in str(report['rejected'])
