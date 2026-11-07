"""Offline manifest, immutable cache and differentiable next-token contracts."""
import copy
import hashlib
import importlib
import math

import pytest
import torch


def api():
    # A missing implementation is an assertion failure during the initial RED run.
    import importlib.util
    assert importlib.util.find_spec('evaluation.selective_wikitext') is not None
    return importlib.import_module('evaluation.selective_wikitext')


class Tokenizer:
    bos_token_id = 0
    def __call__(self, text, add_special_tokens):
        assert add_special_tokens is False
        return {'input_ids': [int(x) for x in text.split()]}


@pytest.fixture
def manifest_inputs(tmp_path):
    from datasets import Dataset
    paths, hashes = {}, {}
    for i, split in enumerate(('train', 'validation', 'test')):
        path = tmp_path / (split + '.arrow')
        # Real Arrow IPC files, distinct token streams per split.
        Dataset.from_dict({'text': ['', ' = Article %s A = ' % split, ' = = Section = = ', ' '.join([str(i + 1)] * 128), '', ' = Article %s B = ' % split, ' '.join([str(i + 4)] * 128)]}).save_to_disk(str(tmp_path / split))
        source = next((tmp_path / split).glob('*.arrow'))
        path.write_bytes(source.read_bytes())
        paths[split] = str(path)
        hashes[split] = hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(arrow_paths=paths, expected_arrow_sha256=hashes,
                tokenizer_identity={'name': 'test', 'vocab_size': 8},
                n_blocks={s: 2 for s in paths})


def test_manifest_separates_splits_and_nonself_donors(manifest_inputs):
    m = api().build_manifest(Tokenizer(), **manifest_inputs)
    api().validate_manifest(m)
    assert m == api().build_manifest(Tokenizer(), **manifest_inputs)
    for i, split in enumerate(('train', 'validation', 'test')):
        blocks = list(api().iter_blocks(m, split))
        assert len(blocks) == 2
        assert blocks[0]['n_tokens'] == 127
        assert blocks[0]['input_ids'].shape == (1, 128)
        assert blocks[0]['input_ids'].device.type == 'cpu'
        assert blocks[0]['input_ids'].dtype == torch.long
        assert blocks[0]['input_ids'][0, 0] == 0
        assert blocks[0]['input_ids'][0, 1:].tolist() == [i + 1] * 127
        assert torch.equal(blocks[0]['corrupted_input_ids'], blocks[1]['input_ids'])
        assert m['splits'][split]['donor_permutation'] == [1, 0]
        assert m['splits'][split]['blocks'][0]['doc_id'] != m['splits'][split]['blocks'][1]['doc_id']
        assert m['splits'][split]['blocks'][0]['source_doc_index'] == 0
        assert blocks[0]['attention_mask'].eq(1).all()
    blocks[0]['input_ids'].fill_(7)
    assert list(api().iter_blocks(m, 'test'))[0]['input_ids'][0, 1] == 3


def test_manifest_rejects_source_mutation_and_split_mixing(manifest_inputs):
    args = copy.deepcopy(manifest_inputs)
    args['arrow_paths']['validation'] = args['arrow_paths']['train']
    with pytest.raises(ValueError):
        api().build_manifest(Tokenizer(), **args)
    path = manifest_inputs['arrow_paths']['train']
    with open(path, 'ab') as out:
        out.write(b'mutation')
    with pytest.raises(ValueError, match='hash|SHA'):
        api().build_manifest(Tokenizer(), **manifest_inputs)


def test_manifest_mutations_are_rejected(manifest_inputs):
    m = api().build_manifest(Tokenizer(), **manifest_inputs)
    for mutate in (lambda x: x['splits']['train']['blocks'][0]['input_ids'].__setitem__(1, 7),
                   lambda x: x['splits']['train'].__setitem__('donor_permutation', [0, 1]),
                   lambda x: x['splits'].__setitem__('validation', x['splits']['train'])):
        bad = copy.deepcopy(m)
        mutate(bad)
        with pytest.raises(ValueError):
            api().validate_manifest(bad)
    assert api().cache_fingerprint(m, {'model': 'a'}) != api().cache_fingerprint(m, {'model': 'b'})


def test_manifest_insufficient_tokens_and_bounds(manifest_inputs):
    args = copy.deepcopy(manifest_inputs)
    args['n_blocks']['train'] = 3
    with pytest.raises(ValueError):
        api().build_manifest(Tokenizer(), **args)
    args = copy.deepcopy(manifest_inputs)
    args['tokenizer_identity']['vocab_size'] = 2
    with pytest.raises(ValueError):
        api().build_manifest(Tokenizer(), **args)


def test_cache_roundtrip_detaches_owns_data_and_refuses_overwrite(tmp_path):
    mod = api()
    logits = torch.zeros(1, 128, 4, requires_grad=True)
    ids = torch.ones(1, 128, dtype=torch.long)
    fingerprint = 'a' * 64
    payload = mod.write_reference_block(tmp_path, fingerprint=fingerprint, block_id='train-000000', logits=logits, input_ids=ids)
    assert payload['reference_log_probs'].shape == (1, 127, 4)
    assert payload['reference_log_probs'].dtype == torch.float32
    assert not payload['reference_log_probs'].requires_grad
    assert payload['reference_log_probs'].device.type == 'cpu'
    assert payload['base_nll_sum'] == pytest.approx(127 * math.log(4))
    payload['reference_log_probs'].fill_(99)
    ids.fill_(2)
    read = mod.read_reference_block(tmp_path, fingerprint=fingerprint, block_id='train-000000')
    assert torch.allclose(read['reference_log_probs'], torch.full((1, 127, 4), -math.log(4)))
    read['reference_log_probs'].fill_(88)
    assert mod.read_reference_block(tmp_path, fingerprint=fingerprint, block_id='train-000000')['reference_log_probs'].max() < 0
    with pytest.raises(FileExistsError):
        mod.write_reference_block(tmp_path, fingerprint=fingerprint, block_id='train-000000', logits=logits, input_ids=ids)
    assert len(list((tmp_path / fingerprint).iterdir())) == 1


def test_cache_detects_tensor_and_identity_corruption(tmp_path):
    mod = api()
    fingerprint = 'b' * 64
    block_id = 'test-000000'
    mod.write_reference_block(tmp_path, fingerprint=fingerprint, block_id=block_id,
                              logits=torch.zeros(1, 128, 3), input_ids=torch.zeros(1, 128, dtype=torch.long))
    path = tmp_path / fingerprint / (block_id + '.pt')
    original = path.read_bytes()
    for field, value in [('fingerprint', 'c' * 64), ('block_id', 'train-000000'),
                         ('n_tokens', 128), ('reference_log_probs', torch.zeros(1, 127, 3))]:
        path.write_bytes(original)
        data = torch.load(path, weights_only=True)
        data[field] = value
        torch.save(data, path)
        with pytest.raises(ValueError):
            mod.read_reference_block(tmp_path, fingerprint=fingerprint, block_id=block_id)
    path.write_bytes(b'broken file')
    with pytest.raises(ValueError):
        mod.read_reference_block(tmp_path, fingerprint=fingerprint, block_id=block_id)


def test_loss_analytic_kl_nll_and_all_predictive_positions():
    mod = api()
    logits = torch.tensor([math.log(0.25), math.log(0.75)]).repeat(1, 128, 1).requires_grad_()
    ref = torch.tensor([math.log(0.5), math.log(0.5)]).repeat(1, 127, 1)
    saved = ref.clone()
    ids = torch.zeros(1, 128, dtype=torch.long)
    loss = mod.block_loss(logits, ref, ids)
    assert loss.n_tokens == 127
    assert loss.kl_sum.shape == loss.nll_sum.shape == ()
    assert loss.kl_sum.item() == pytest.approx(127 * 0.5 * math.log(4 / 3), rel=1e-5)
    assert loss.nll_sum.item() == pytest.approx(127 * math.log(4), rel=1e-5)
    loss.kl_sum.backward()
    assert torch.isfinite(logits.grad).all()
    assert logits.grad[:, :-1].abs().sum(-1).gt(0).all()
    assert logits.grad[:, -1].eq(0).all()
    assert torch.equal(ref, saved)
    identity = mod.block_loss(torch.zeros(1, 128, 2), ref, ids)
    assert identity.kl_sum.item() == 0


@pytest.mark.parametrize('bad', ['reference_grad', 'shape', 'tokens', 'nan'])
def test_loss_rejects_invalid_inputs(bad):
    logits = torch.zeros(1, 128, 2, requires_grad=True)
    ref = torch.full((1, 127, 2), -math.log(2))
    ids = torch.zeros(1, 128, dtype=torch.long)
    if bad == 'reference_grad':
        ref.requires_grad_()
    elif bad == 'shape':
        ref = ref[:, :-1]
    elif bad == 'tokens':
        ids[0, -1] = 2
    else:
        logits = logits.detach()
        logits[0, 0, 0] = float('nan')
    with pytest.raises(ValueError):
        api().block_loss(logits, ref, ids)


def test_article_windows_never_join_short_articles(tmp_path, manifest_inputs):
    from datasets import Dataset
    path = tmp_path / 'short.arrow'
    staging = tmp_path / 'short-source'
    Dataset.from_dict({'text': [' = Tiny A = ', ' '.join(['1'] * 100),
                               ' = Tiny B = ', ' '.join(['2'] * 100)]}).save_to_disk(str(staging))
    path.write_bytes(next(staging.glob('*.arrow')).read_bytes())
    manifest_inputs['arrow_paths']['train'] = str(path)
    manifest_inputs['expected_arrow_sha256']['train'] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='insufficient'):
        api().build_manifest(Tokenizer(), **manifest_inputs)


def test_crosssplit_article_overlap_rejected_even_with_valid_hashes(manifest_inputs):
    from datasets import Dataset
    from pathlib import Path
    # Different source bytes do not make the same article a held-out document.
    path = Path(manifest_inputs['arrow_paths']['validation'])
    staging = path.parent / 'overlap'
    Dataset.from_dict({'text': [' = Article train A = ', ' '.join(['2'] * 128),
                               ' = Article validation B = ', ' '.join(['5'] * 128)]}).save_to_disk(str(staging))
    path.write_bytes(next(staging.glob('*.arrow')).read_bytes())
    manifest_inputs['expected_arrow_sha256']['validation'] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='overlap'):
        api().build_manifest(Tokenizer(), **manifest_inputs)


def test_manifest_semantics_checked_even_when_hash_recomputed(manifest_inputs):
    import json
    m = api().build_manifest(Tokenizer(), **manifest_inputs)
    m['splits']['train']['donor_permutation'] = [0, 1]
    m['manifest_hash'] = hashlib.sha256(json.dumps({k: v for k, v in m.items() if k != 'manifest_hash'},
                                                 sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    with pytest.raises(ValueError, match='permutation'):
        api().validate_manifest(m)


@pytest.mark.parametrize('bad', ['nan', 'shape', 'float_tokens', 'tokens', 'traversal'])
def test_cache_write_rejects_invalid_or_unsafe_inputs(tmp_path, bad):
    logits = torch.zeros(1, 128, 2)
    ids = torch.zeros(1, 128, dtype=torch.long)
    block_id = 'train-000000'
    if bad == 'nan':
        logits[0, 0, 0] = float('nan')
    elif bad == 'shape':
        logits = logits[:, 0]
    elif bad == 'float_tokens':
        ids = ids.float()
    elif bad == 'tokens':
        ids[0, -1] = -1
    else:
        block_id = '../escape'
    with pytest.raises(ValueError):
        api().write_reference_block(tmp_path, fingerprint='d' * 64, block_id=block_id,
                                    logits=logits, input_ids=ids)
    assert not list(tmp_path.rglob('*.pt'))
