"""Offline WikiText article manifests, CPU references and tensor loss primitives.

No model execution or intervention policy lives here. Reference tensors cover
positions 0..S-2 and predict input tokens 1..S-1.
"""
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile

import torch
import torch.nn.functional as F

_SPLITS = ('train', 'validation', 'test')
_DATASET = {'name': 'Salesforce/wikitext', 'config': 'wikitext-2-raw-v1',
            'version': '0.0.0', 'revision': 'b08601e04326c79dfdd32d625aee71d232d685c3'}
_JOIN = 'article-body nonblank nonheading rows joined with \\n\\n; first full window per article'


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def _file_hash(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _articles(rows):
    title, body, index = None, [], -1
    for row in rows:
        text = row.strip()
        heading = text.startswith('=') and text.endswith('=')
        if heading:
            # WikiText serializes levels as '= Title =' / '= = Section = ='.
            inner = text[1:-1].strip()
            if inner and not inner.startswith('=') and not inner.endswith('='):
                if title is not None:
                    yield index, title, '\n\n'.join(body)
                title, body, index = inner, [], index + 1
        elif text:
            _require(title is not None, 'article body precedes first level-one title')
            body.append(text)
    if title is not None:
        yield index, title, '\n\n'.join(body)


def build_manifest(tokenizer, *, arrow_paths: dict, expected_arrow_sha256: dict,
                   tokenizer_identity: dict, n_blocks: dict,
                   block_size: int = 128, pairing_seed: int = 0) -> dict:
    """Read only explicit hash-verified Arrow files; select first eligible articles."""
    import numpy as np
    from datasets import Dataset

    _require(set(arrow_paths) == set(expected_arrow_sha256) == set(n_blocks) == set(_SPLITS),
             'exactly train, validation and test splits required')
    _require(type(block_size) is int and block_size >= 2, 'block_size must be >=2')
    paths = {s: str(Path(arrow_paths[s]).resolve()) for s in _SPLITS}
    _require(len(set(paths.values())) == 3, 'split source paths must be distinct')
    _require(len(set(expected_arrow_sha256.values())) == 3, 'split source hashes must be distinct')
    for split in _SPLITS:
        _require(type(n_blocks[split]) is int and n_blocks[split] >= 2, 'need >=2 blocks per split')
        _require(_file_hash(paths[split]) == expected_arrow_sha256[split], 'Arrow SHA256 hash mismatch: ' + split)
    manifest = dict(version=1, dataset=dict(_DATASET), tokenizer_identity=tokenizer_identity,
                    block_size=block_size, pairing_seed=pairing_seed, text_join_rule=_JOIN,
                    bos_token_id=tokenizer.bos_token_id, splits={})
    rng = np.random.default_rng(pairing_seed)
    for split in _SPLITS:
        blocks = []
        ds = Dataset.from_file(paths[split])
        for doc_index, title, body in _articles(ds['text']):
            ids = list(tokenizer(body, add_special_tokens=False)['input_ids'])
            if len(ids) < block_size:
                continue
            ids = ids[:block_size]
            if tokenizer.bos_token_id is not None:
                ids[0] = tokenizer.bos_token_id
            blocks.append(dict(block_id='%s-%06d' % (split, len(blocks)), input_ids=ids,
                               attention_mask=[1] * block_size, input_ids_hash=_hash(ids),
                               doc_id=hashlib.sha256(' '.join(title.split()).encode()).hexdigest(),
                               source_doc_index=doc_index,
                               content_hash=hashlib.sha256(body.encode()).hexdigest()))
            if len(blocks) == n_blocks[split]:
                break
        _require(len(blocks) == n_blocks[split], 'insufficient eligible articles: ' + split)
        for _ in range(1000):
            perm = rng.permutation(len(blocks)).tolist()
            if all(i != j for i, j in enumerate(perm)):
                break
        else:
            raise ValueError('failed to find donor derangement')
        manifest['splits'][split] = dict(source_path=paths[split], source_sha256=expected_arrow_sha256[split],
                                         n_blocks=len(blocks), blocks=blocks, donor_permutation=perm,
                                         donor_permutation_hash=_hash(perm))
    manifest['manifest_hash'] = _hash(manifest)
    validate_manifest(manifest)
    return manifest


def validate_manifest(manifest: dict) -> None:
    """Validate embedded immutable data without rereading external sources."""
    try:
        _require(manifest['version'] == 1 and manifest['dataset'] == _DATASET, 'unsupported manifest dataset/version')
        _require(manifest['text_join_rule'] == _JOIN, 'unknown preprocessing rule')
        _require(manifest['manifest_hash'] == _hash({k: v for k, v in manifest.items() if k != 'manifest_hash'}),
                 'manifest hash mismatch')
        size = manifest['block_size']
        _require(type(size) is int and size >= 2, 'invalid block size')
        _require(set(manifest['splits']) == set(_SPLITS), 'invalid splits')
        vocab = manifest['tokenizer_identity'].get('vocab_size')
        seen_docs, seen_contents, seen_tokens, paths, sources = set(), set(), set(), set(), set()
        for split in _SPLITS:
            data = manifest['splits'][split]
            blocks, perm = data['blocks'], data['donor_permutation']
            n = len(blocks)
            _require(n >= 2 and data['n_blocks'] == n, 'invalid block count')
            _require(data['source_path'] not in paths and data['source_sha256'] not in sources, 'split source mixing')
            paths.add(data['source_path']); sources.add(data['source_sha256'])
            _require(sorted(perm) == list(range(n)) and all(i != j for i, j in enumerate(perm)), 'invalid donor permutation')
            _require(data['donor_permutation_hash'] == _hash(perm), 'donor permutation hash mismatch')
            docs, contents, tokens = set(), set(), set()
            previous = -1
            for i, block in enumerate(blocks):
                ids = block['input_ids']
                _require(block['block_id'] == '%s-%06d' % (split, i), 'block identity/split mismatch')
                _require(len(ids) == size and all(type(t) is int and t >= 0 and (vocab is None or t < vocab) for t in ids), 'invalid token IDs')
                _require(block['attention_mask'] == [1] * size, 'invalid attention mask')
                _require(block['input_ids_hash'] == _hash(ids), 'input token hash mismatch')
                _require(manifest['bos_token_id'] is None or ids[0] == manifest['bos_token_id'], 'invalid BOS replacement')
                _require(type(block['source_doc_index']) is int and block['source_doc_index'] > previous, 'article source order mismatch')
                previous = block['source_doc_index']
                _require(block['doc_id'] not in docs, 'duplicate selected article')
                _require(block['doc_id'] != blocks[perm[i]]['doc_id'], 'same-document donor')
                docs.add(block['doc_id']); contents.add(block['content_hash']); tokens.add(block['input_ids_hash'])
            _require(not (docs & seen_docs or contents & seen_contents or tokens & seen_tokens), 'selected cross-split article/token overlap')
            seen_docs.update(docs); seen_contents.update(contents); seen_tokens.update(tokens)
    except (KeyError, TypeError, IndexError) as exc:
        raise ValueError('malformed WikiText manifest') from exc


def iter_blocks(manifest: dict, split: str):
    """Yield independent CPU copies in stable source order, with frozen donors."""
    validate_manifest(manifest)
    _require(split in _SPLITS, 'unknown split')
    data = manifest['splits'][split]
    for i, block in enumerate(data['blocks']):
        clean = torch.tensor([block['input_ids']], dtype=torch.long)
        donor = data['blocks'][data['donor_permutation'][i]]
        yield dict(block_id=block['block_id'], input_ids=clean,
                   corrupted_input_ids=torch.tensor([donor['input_ids']], dtype=torch.long),
                   attention_mask=torch.ones_like(clean), n_tokens=manifest['block_size'] - 1)


def cache_fingerprint(manifest: dict, reference_identity: dict) -> str:
    validate_manifest(manifest)
    return _hash(dict(version=1, manifest_hash=manifest['manifest_hash'], reference_identity=reference_identity))


def _cache_path(cache_dir, fingerprint, block_id):
    _require(isinstance(fingerprint, str) and re.fullmatch('[0-9a-f]{64}', fingerprint) is not None, 'invalid fingerprint')
    _require(isinstance(block_id, str) and re.fullmatch('(train|validation|test)-[0-9]{6}', block_id) is not None, 'invalid block ID')
    return Path(cache_dir) / fingerprint / (block_id + '.pt')


def _check_logits(logits, input_ids):
    _require(logits.ndim == 3 and logits.shape[0] == 1 and logits.shape[1] >= 2 and logits.shape[2] >= 1, 'invalid logits shape')
    _require(logits.is_floating_point() and torch.isfinite(logits).all(), 'nonfinite/nonfloating logits')
    _require(input_ids.dtype == torch.long and tuple(input_ids.shape) == tuple(logits.shape[:2]), 'invalid input_ids shape/dtype')
    _require(input_ids.device == logits.device, 'input/logits devices differ')
    _require(((input_ids >= 0) & (input_ids < logits.shape[-1])).all(), 'token outside vocabulary')


def _payload_digest(payload):
    meta = {k: v for k, v in payload.items() if k not in ('payload_digest', 'reference_log_probs')}
    tensor = payload['reference_log_probs']
    digest = hashlib.sha256(_hash(meta).encode())
    digest.update(str(tuple(tensor.shape)).encode())
    digest.update(str(tensor.dtype).encode())
    digest.update(tensor.numpy().tobytes())
    return digest.hexdigest()


def write_reference_block(cache_dir, *, fingerprint: str, block_id: str,
                          logits: torch.Tensor, input_ids: torch.Tensor) -> dict:
    """Detach full intact logits and publish one immutable, atomic CPU reference."""
    path = _cache_path(cache_dir, fingerprint, block_id)
    _check_logits(logits, input_ids)
    with torch.no_grad():
        log_probs = F.log_softmax(logits[:, :-1].detach().float(), -1).cpu().contiguous().clone()
        targets = input_ids[:, 1:].detach().cpu()
        nll = -log_probs.gather(-1, targets.unsqueeze(-1)).double().sum().item()
    payload = dict(version=1, fingerprint=fingerprint, block_id=block_id,
                   input_ids_hash=_hash(input_ids.detach().cpu().tolist()[0]),
                   n_tokens=input_ids.shape[1] - 1, reference_log_probs=log_probs, base_nll_sum=nll)
    payload['payload_digest'] = _payload_digest(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive reservation makes os.replace safe against concurrent writers.
    fd = os.open(str(path) + '.lock', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    temp = None
    try:
        if path.exists():
            raise FileExistsError(str(path))
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + block_id, suffix='.tmp', delete=False) as out:
            temp = out.name
            torch.save(payload, out)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None and os.path.exists(temp):
            os.unlink(temp)
        os.unlink(str(path) + '.lock')
    return payload


def read_reference_block(cache_dir, *, fingerprint: str, block_id: str) -> dict:
    path = _cache_path(cache_dir, fingerprint, block_id)
    if not path.exists():
        raise FileNotFoundError(str(path))
    try:
        payload = torch.load(path, map_location='cpu', weights_only=True)
        _require(payload['version'] == 1 and payload['fingerprint'] == fingerprint and payload['block_id'] == block_id, 'cache identity mismatch')
        ref = payload['reference_log_probs']
        _require(ref.dtype == torch.float32 and ref.device.type == 'cpu' and ref.is_contiguous() and not ref.requires_grad, 'invalid reference tensor')
        _require(ref.ndim == 3 and ref.shape[0] == 1 and ref.shape[1] == payload['n_tokens'] and ref.shape[1] >= 1 and ref.shape[2] >= 1, 'invalid reference shape')
        _require(torch.isfinite(ref).all() and math.isfinite(payload['base_nll_sum']), 'nonfinite cache payload')
        _require(re.fullmatch('[0-9a-f]{64}', payload['input_ids_hash']) is not None, 'invalid input token hash')
        _require(payload['payload_digest'] == _payload_digest(payload), 'cache payload digest mismatch')
        return payload
    except Exception as exc:
        raise ValueError('invalid WikiText cache: ' + str(path)) from exc


@dataclass(frozen=True)
class WikiTextLoss:
    kl_sum: torch.Tensor
    nll_sum: torch.Tensor
    n_tokens: int


def block_loss(masked_logits: torch.Tensor, reference_log_probs: torch.Tensor,
               input_ids: torch.Tensor) -> WikiTextLoss:
    """Sum base||masked KL and empirical NLL over every predictive position."""
    _check_logits(masked_logits, input_ids)
    ref = reference_log_probs
    _require(not ref.requires_grad and ref.grad_fn is None, 'reference must be detached')
    _require(ref.dtype == torch.float32 and ref.device == masked_logits.device and
             tuple(ref.shape) == (1, masked_logits.shape[1] - 1, masked_logits.shape[2]), 'reference shape/dtype/device mismatch')
    _require(torch.isfinite(ref).all(), 'nonfinite reference')
    kl_sum = masked_logits.new_zeros((), dtype=torch.float32)
    nll_sum = masked_logits.new_zeros((), dtype=torch.float32)
    for start in range(0, ref.shape[1], 32):
        stop = min(start + 32, ref.shape[1])
        log_q = F.log_softmax(masked_logits[:, start:stop].float(), -1)
        base = ref[:, start:stop]
        kl_sum = kl_sum + F.kl_div(log_q, base, reduction='sum', log_target=True)
        nll_sum = nll_sum - log_q.gather(-1, input_ids[:, start + 1:stop + 1].unsqueeze(-1)).sum()
    return WikiTextLoss(kl_sum, nll_sum, ref.shape[1])
