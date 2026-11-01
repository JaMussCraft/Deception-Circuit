"""Deterministic user-turn inversion / matched neutral-request construction.

CPU tokenizer work only. Original H remains an independent collateral condition.
The two new arms match each other, not the shorter original D/H conditions.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Sequence

from dataset import deception_common as dc
from dataset import matched_honest as mh

REQUEST_POOL_PATH = str(Path(__file__).with_name('user_inversion_requests_v2.json'))
TASKS = ('far_v2', 'sdr_v2', 'ser_v2')
SELECT_SALT = 'user-inversion-v2:'
PADDING = (' Please use the stated response format.', ' Please proceed.')
PADDING_BOUND = 12
EOT = '<|eot_id|>'
HEADERS = tuple('<|start_header_id|>' + role + '<|end_header_id|>\n\n'
                for role in ('system', 'user', 'assistant'))
BASELINE_KIND = 'matched_frame_neutral_request'
WORDING_CONFOUND = ('Inversion and neutral requests differ in selection wording and neutral '
                    'format padding; both retain quiz and awareness framing.')


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False).encode()).hexdigest()


class _CachedEncoding:
    """Share full, unpadded encodings between the pinned assertion helpers."""
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.cache = {}

    def encode(self, text, add_special_tokens=False):
        if text not in self.cache:
            self.cache[text] = self.tokenizer.encode(text, add_special_tokens=False)
        return self.cache[text]


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _parts(prompt):
    _require(prompt.count(EOT) == 2, 'expected exactly two role terminators')
    for header in HEADERS:
        _require(prompt.count(header) == 1, 'missing or duplicate role header')
    system, user, assistant = prompt.split(EOT)
    _require(system.startswith('<|begin_of_text|>' + HEADERS[0]), 'invalid system role')
    _require(user.startswith(HEADERS[1]), 'invalid user role')
    _require(assistant.startswith(HEADERS[2]), 'invalid assistant role')
    return system, user, assistant


def _append(prompt, request):
    system, user, assistant = _parts(prompt)
    _require(request not in prompt, 'duplicate request text in source prompt')
    return EOT.join((system, user + ' ' + request, assistant))


def _indexed(rows, label):
    out = {}
    for row in rows:
        iid = row['instance_id']
        _require(isinstance(iid, str) and bool(iid), label + ' invalid instance id')
        _require(iid not in out, label + ' duplicate instance id: ' + iid)
        out[iid] = row
    return out


def _variants(tokenizer, text):
    base_length = len(tokenizer.encode(' ' + text, add_special_tokens=False))
    variants = []
    for a in range(PADDING_BOUND + 1):
        for b in range(PADDING_BOUND + 1):
            padded = text + PADDING[0] * a + PADDING[1] * b
            n = len(tokenizer.encode(' ' + padded, add_special_tokens=False))
            variants.append((n, n - base_length, padded, (a, b)))
    return variants


def _padding_pairs(tokenizer, entry):
    """Length-indexed search: added tokens, repetitions, then lexical/count ties.

    Full-prompt assertions below remain authoritative: standalone lengths only
    index candidates, and physical pad tokens are never introduced.
    """
    neutral_by_length = defaultdict(list)
    for variant in _variants(tokenizer, entry['neutral_request']):
        neutral_by_length[variant[0]].append(variant)
    choices = []
    for inv in _variants(tokenizer, entry['inversion_request']):
        for neutral in neutral_by_length[inv[0]]:
            choices.append((inv[1] + neutral[1], inv[2], neutral[2],
                            inv[3], neutral[3]))
    return sorted(choices, key=lambda c: (c[0], sum(c[3]) + sum(c[4]), c[1:]))


def _validate_source(d, h, task):
    iid = d['instance_id']
    for row in (d, h):
        _require(row.get('task') == task, iid + ': task mismatch')
        if task == 'ser_v2':
            _require(row.get('ser_wording') == 'B' and all(
                row[s + '_prompt'].endswith(('The result you should check is', 'The reading you should check is'))
                for s in ('clean', 'corrupt')), iid + ': only SER wording B is supported')
    _require(d.get('pressure_id') == h.get('pressure_id') and bool(d.get('pressure_id')),
             iid + ': pressure id mismatch')
    _require(h.get('honest_twin_kind') == 'neutral_clause', iid + ': H is not neutral_clause')
    for key in ('clean_item_d', 'corrupt_item_d'):
        _require(d[key] == h[key], iid + ': designation metadata mismatch')
    _require(d['target'] == h['distractor'] and d['distractor'] == h['target'],
             iid + ': H labels must reverse D labels')
    for stream in ('clean', 'corrupt'):
        dp, hp = d[stream + '_prompt'], h[stream + '_prompt']
        system, user, assistant = _parts(dp)
        _parts(hp)
        marker = ' ' + d['pressure']
        _require(system.endswith(marker) and system.count(marker) == 1,
                 iid + ': source pressure not unique at system terminator')
        expected = EOT.join((system[:-len(marker)] + ' ' + h['pressure'], user, assistant))
        _require(expected == hp, iid + ': H differs outside source pressure')


def _behavior_column(key):
    return (key.endswith('_margin') or key.startswith('h_') or
            any(part in key for part in ('argmax', 'choice', 'logit', 'score', 'readout')) or
            key.endswith(('_token', '_token_id', '_token_ids')))


def _new_row(source, h, request, condition):
    # All old behavioral readouts refer to other prompts. Preserve only under
    # explicit source metadata, never as active scoring columns.
    row = {k: v for k, v in source.items()
           if not (_behavior_column(k) or k.startswith('honest_instruction_') or
                   k == 'neutral_prompt')}
    row.update(condition=condition, pressure=h['pressure'], slot_kind='neutral',
               honest_twin_kind=None, baseline_kind=BASELINE_KIND,
               request_text=request, source_neutral_prompt=source.get('neutral_prompt'))
    for stream in ('clean', 'corrupt'):
        row[stream + '_prompt'] = _append(h[stream + '_prompt'], request)
    return row


def _prove(tokenizer, d, h, choice, max_seq_length):
    _, inv_text, neutral_text, inv_padding, neutral_padding = choice
    inv = _new_row(d, h, inv_text, 'user_inversion')
    neutral = _new_row(h, h, neutral_text, 'user_neutral')
    metadata = {}
    for stream in ('clean', 'corrupt'):
        ip, np = inv[stream + '_prompt'], neutral[stream + '_prompt']
        a, b, span = mh.assert_clause_aligned_pair(tokenizer, ip, np, inv_text, max_seq_length)
        _, _, baseline_span = mh.assert_clause_aligned_pair(tokenizer, np, ip, neutral_text,
                                                           max_seq_length)
        _require(span == baseline_span, 'request spans differ')
        metadata[stream] = {'request_span': list(span), 'readout': len(a) - 1,
                            'inversion_length': len(a), 'baseline_length': len(b),
                            'inversion_prompt_hash': _hash(ip), 'baseline_prompt_hash': _hash(np)}
    for row in (inv, neutral):
        _, _, pos = dc.assert_aligned_pair(tokenizer, row['clean_prompt'], row['corrupt_prompt'],
                                           row['clean_item_d'], row['corrupt_item_d'], max_seq_length)
        row['request_spans'] = {s: m['request_span'] for s, m in metadata.items()}
        row['designation_position'] = pos
    return inv, neutral, metadata, {'inversion': list(inv_padding), 'baseline': list(neutral_padding),
                                   'total_added_tokens': choice[0]}


def derive_pairs(tokenizer, task: str, d_rows: Sequence[dict], h_rows: Sequence[dict],
                 requests: Sequence[dict], max_seq_length: int = 256) -> tuple[list[dict], dict]:
    """Construct matched user requests in D order, retaining every rejection.

    Invalid source pairing fails the entire call. A valid row with no bounded
    padding solution is rejected and counted. Request selection uses salted SHA1
    over sorted fitting request ids, before any behavioral output exists.
    """
    if not __debug__:
        raise RuntimeError('run without -O: pinned token alignment checks use assertions')
    _require(task in TASKS, 'unsupported task')
    _require(isinstance(max_seq_length, int) and max_seq_length > 0, 'invalid max_seq_length')
    ds, hs = _indexed(d_rows, 'D'), _indexed(h_rows, 'H')
    _require(ds.keys() == hs.keys(), 'D/H instance ids missing or extra')
    entries, seen, texts = [], set(), set()
    for entry in requests:
        _require(entry['id'] not in seen, 'duplicate request id')
        seen.add(entry['id'])
        for field in ('inversion_request', 'neutral_request'):
            text = entry[field]
            _require(isinstance(text, str) and bool(text.strip()) and '<|' not in text,
                     'invalid request text')
            _require((entry['task'], text) not in texts, 'duplicate request text')
            texts.add((entry['task'], text))
        if entry['task'] == task:
            entries.append(entry)
    _require(bool(entries), 'no requests for task')
    entries.sort(key=lambda e: e['id'])
    cached = _CachedEncoding(tokenizer)
    choices = {e['id']: _padding_pairs(cached, e) for e in entries}
    # Request encodings reused across rows; full prompt encodings are row-local.
    request_cache = dict(cached.cache)
    pairs, rejected = [], []
    by_pressure, by_request, padding_counts = Counter(), Counter(), Counter()
    for d in d_rows:
        h = hs[d['instance_id']]
        _validate_source(d, h, task)
        cached.cache = dict(request_cache)
        fits, failures = [], Counter()
        for entry in entries:
            if any(entry[field] in h[stream + '_prompt']
                   for field in ('inversion_request', 'neutral_request')
                   for stream in ('clean', 'corrupt')):
                failures['duplicate request text in source prompt'] += 1
                continue
            for choice in choices[entry['id']]:
                try:
                    proof = _prove(cached, d, h, choice, max_seq_length)
                except (AssertionError, ValueError) as exc:
                    failures[str(exc)] += 1
                    continue
                fits.append((entry, proof))
                break
        if not fits:
            rejected.append({'instance_id': d['instance_id'], 'pressure_id': d['pressure_id'],
                             'reason': 'no_aligned_request_within_bound',
                             'alignment_failures': dict(failures)})
            continue
        index = int(hashlib.sha1((SELECT_SALT + d['instance_id']).encode()).hexdigest(), 16) % len(fits)
        entry, (inv, neutral, metadata, padding) = fits[index]
        source_hashes = {'D': _hash(d), 'H': _hash(h)}
        for row in (inv, neutral):
            row.update(request_id=entry['id'], source_row_hashes=source_hashes,
                       token_lengths={s: m['inversion_length'] for s, m in metadata.items()},
                       readouts={s: m['readout'] for s, m in metadata.items()})
        pair = {'instance_id': d['instance_id'], 'inversion': inv, 'baseline': neutral,
                'request_inversion': inv['request_text'], 'request_neutral': neutral['request_text'],
                'request_id': entry['id'], 'request_span': metadata['clean']['request_span'],
                'source_pressure_id': d['pressure_id'], 'source_pressure': d['pressure'],
                'source_row_hashes': source_hashes,
                'source_behavior': {label: {k: v for k, v in row.items()
                                          if _behavior_column(k)}
                                    for label, row in (('D', d), ('H', h))},
                'stream_metadata': metadata, 'padding': padding,
                'request_hash': _hash(entry), 'baseline_kind': BASELINE_KIND,
                'wording_confound': WORDING_CONFOUND,
                'source_relevance_suffix': d.get('suffix'),
                'relevance_suffix_caveat': 'Original relevance suffix is unchanged and may compete with the user request.'}
        pairs.append(pair)
        by_pressure[d['pressure_id']] += 1
        by_request[entry['id']] += 1
        padding_counts[json.dumps(padding, sort_keys=True)] += 1
    source_pressure_counts = Counter(d['pressure_id'] for d in d_rows)
    pressure_counts = {pid: {'source': n, 'accepted': by_pressure[pid],
                             'rejected': n - by_pressure[pid]}
                       for pid, n in sorted(source_pressure_counts.items())}
    return pairs, {'pressure_counts': pressure_counts, 'task': task, 'source_count': len(d_rows), 'accepted': len(pairs),
                   'rejected': rejected, 'by_pressure_id': dict(sorted(by_pressure.items())),
                   'by_request_id': dict(sorted(by_request.items())),
                   'padding_counts': dict(sorted(padding_counts.items())),
                   'max_seq_length': max_seq_length, 'request_pool_hash': _hash(requests),
                   'baseline_kind': BASELINE_KIND, 'wording_confound': WORDING_CONFOUND}
