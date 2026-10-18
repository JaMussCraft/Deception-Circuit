"""Execute frozen SDR diagnostic rows using existing evaluation machinery.

No source selection depends on model outcomes. A subset selects work against
one full manifest; it never creates a second experiment or resume fingerprint.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import random
from collections import Counter

import torch

from evaluation.selective_diagnostics import canonical_json, content_hash, validate_manifest

ROOT = Path('/projects/beto/swong2/Alignment/Deception-Circuit')
ARTIFACT_ROOT = ROOT / 'outputs/llama-8b-instruct_sdr_coarse'
DEFAULT_BINDINGS = {
    'D': str(ARTIFACT_ROOT / 'nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742'),
    'H': str(ARTIFACT_ROOT / 'nls0.3_honest_noedge_noan_nomh_nomo_nomb_260922-092743'),
    'F': str(ARTIFACT_ROOT / 'nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-204850'),
    'm': str(ARTIFACT_ROOT / '_allmlp_nomb'),
}


def select_work(manifest, subset='all'):
    if subset not in ('all', 'smoke'):
        raise ValueError('subset must be all or smoke')
    clusters = {c['cluster_id'] for c in manifest['clusters'][:2]}
    rows = [r for r in manifest['rows'] if subset == 'all' or r['cluster_id'] in clusters]
    needed = {r['donor']['reference_row_id'] for r in rows
              if r['kind'] == 'generation' and r['donor']}
    refs = [r for r in manifest['donor_reference_rows'] if r['row_id'] in needed]
    return rows, refs


def donor_diagnostics(manifest, rows=None):
    """Deduplicate intact forwards; labels always belong to the donor source."""
    clusters = {c['cluster_id']: c for c in manifest['clusters']}
    endpoints = [r['donor'] for r in (manifest['rows'] if rows is None else rows) if r['donor']]
    result = {}
    for p in endpoints:
        labels = clusters[p['cluster_id']]['labels']
        row = {'kind': 'donor_score', 'recipient': p, 'donor': None, 'labels': labels,
               'intended_label': p['intended_label'], 'intended_answer': p['intended_answer']}
        # Exact tokens plus local semantic labels; endpoint provenance remains in the row.
        row['row_id'] = 'donor-score-' + content_hash({'input_ids': p['input_ids'],
                                                    'attention_mask': p['attention_mask'], 'labels': labels})
        result.setdefault(row['row_id'], row)
    return sorted(result.values(), key=lambda r: r['row_id'])


def work_plan(manifest, subset='all'):
    rows, refs = select_work(manifest, subset)
    score = sum(r['kind'] == 'score' for r in rows)
    generation = sum(r['kind'] == 'generation' for r in rows)
    donors = donor_diagnostics(manifest, rows)
    return {'manifest_hash': manifest['manifest_hash'], 'subset': subset,
            'score_passes': score, 'donor_score_passes': len(donors),
            'total_score_passes': score + len(donors),
            'target_completions': generation, 'donor_reference_completions': len(refs),
            'total_completions': generation + len(refs),
            'worst_case_new_tokens': (generation + len(refs)) * manifest['config']['max_new_tokens'],
            'target_row_ids': [r['row_id'] for r in rows],
            'donor_reference_row_ids': [r['row_id'] for r in refs],
            'donor_score_row_ids': [r['row_id'] for r in donors]}


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w') as f:
        f.write(canonical_json(value) + '\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(temporary, path)


class ResultStore:
    """One process writer. Row records are appended with fsync at boundaries.

    An unterminated final line is discarded after interruption; malformed
    newline-terminated records, duplicates and changed row contents fail closed.
    """
    def __init__(self, output_dir, manifest, provenance):
        self.path = Path(output_dir)
        self.path.mkdir(parents=True, exist_ok=True)
        self.expected = {r['row_id']: r for r in
                         manifest['rows'] + manifest['donor_reference_rows'] + donor_diagnostics(manifest)}
        self.fingerprint = content_hash({'manifest': manifest['manifest_hash'], 'provenance': provenance})
        run = {'fingerprint': self.fingerprint, 'manifest_hash': manifest['manifest_hash'],
               'provenance': provenance, 'manifest': manifest}
        run_file = self.path / 'run.json'
        if run_file.exists():
            if json.loads(run_file.read_text()) != run:
                raise ValueError('run fingerprint mismatch; use a new output directory')
        else:
            if (self.path / 'results.jsonl').exists():
                raise ValueError('results without run fingerprint')
            atomic_json(run_file, run)
        self.results = {}
        log = self.path / 'results.jsonl'
        if log.exists():
            data = log.read_bytes()
            end = data.rfind(b'\n') + 1
            if end != len(data):
                with log.open('r+b') as f:
                    f.truncate(end)
                    f.flush()
                    os.fsync(f.fileno())
            for line in data[:end].splitlines():
                try:
                    record = json.loads(line)
                    rid = record['row_id']
                    if rid in self.results:
                        raise ValueError('duplicate row in persisted results')
                    expected = self.expected[rid]
                    if record['fingerprint'] != self.fingerprint or record['row_hash'] != content_hash(expected):
                        raise ValueError('record fingerprint or row mismatch')
                    check = {k: v for k, v in record.items() if k != 'result_hash'}
                    if record['result_hash'] != content_hash(check):
                        raise ValueError('record content hash mismatch')
                except (KeyError, TypeError, json.JSONDecodeError) as exc:
                    raise ValueError('invalid complete result record') from exc
                self.results[rid] = record

    def append(self, row, payload):
        rid = row['row_id']
        if rid not in self.expected or content_hash(row) != content_hash(self.expected[rid]):
            raise ValueError('result row differs from frozen row')
        if rid in self.results:
            raise ValueError('duplicate row result')
        record = {'row_id': rid, 'kind': row['kind'], 'fingerprint': self.fingerprint,
                  'row_hash': content_hash(row), 'inputs': row, 'payload': payload}
        record['result_hash'] = content_hash(record)
        data = (canonical_json(record) + '\n').encode()
        fd = os.open(str(self.path / 'results.jsonl'), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            while data:
                data = data[os.write(fd, data):]
            os.fsync(fd)
        finally:
            os.close(fd)
        self.results[rid] = record


def safe_knockout(masks):
    from evaluation.masks import knockout_masks
    for key in ('mlp_hidden', 'mlp_output', 'mlp_blocks'):
        values = masks.get(key, {})
        values = values.values() if isinstance(values, dict) else [values]
        if any(torch.as_tensor(v).bool().any().item() for v in values):
            raise ValueError('heads-only mask must have zero MLP membership')
    ko = knockout_masks(masks, 'finest')
    for key in ('mlp_hidden', 'mlp_output', 'mlp_blocks'):
        values = ko.get(key, {})
        values = values.values() if isinstance(values, dict) else [values]
        if not all(torch.as_tensor(v).bool().all().item() for v in values):
            raise ValueError('knockout must retain all MLPs')
    return ko


def resolve_masks(bindings=None):
    from evaluation.circuits import resolve_circuit_specs
    from evaluation.masks import as_lists, count_masks, sample_random_masks
    specs, bound, _, configs, geometry = resolve_circuit_specs(
        circuit=[k + '=' + v for k, v in (bindings or DEFAULT_BINDINGS).items()],
        expr=['core=(D&H)-m', 'd_minus_f=(D-F)-m'], compose_granularity='leaf')
    masks = {s.label.split('__')[0]: s.masks for s in specs}
    for name, expected in (('core', 43), ('d_minus_f', 33)):
        safe_knockout(masks[name])
        if count_masks(masks[name])['attention_heads']['active'] != expected:
            raise ValueError(f'{name} must have exactly {expected} heads')
    masks['random_core_seed0'] = sample_random_masks(
        masks['core'], num_heads=geometry['num_heads'], head_dim=geometry['head_dim'],
        seed=0, index=0)
    safe_knockout(masks['random_core_seed0'])
    provenance = {name: {'mask': as_lists(mask), 'mask_hash': content_hash(as_lists(mask)),
                         'counts': count_masks(mask)} for name, mask in masks.items()}
    return masks, provenance, (specs, bound, configs, geometry)


def aligned_inputs(recipient, donor=None):
    from evaluation.gen_engine import require_left_padding
    ids = torch.tensor([recipient['input_ids']], dtype=torch.long)
    attention = torch.tensor([recipient['attention_mask']], dtype=torch.long)
    if ids.shape != attention.shape:
        raise ValueError('recipient mask alignment mismatch')
    require_left_padding(attention)
    if donor is not None:
        if len(donor['input_ids']) != ids.shape[1] or donor['attention_mask'] != recipient['attention_mask']:
            raise ValueError('donor prompt alignment/padding mismatch')
    return ids, attention


class FrozenTask:
    """The existing prediction evaluator's three-method task surface."""
    name = 'frozen_sdr'

    def pred_spec(self, batch):
        return {'pred_pos': torch.full_like(batch['target'], batch['input_ids'].shape[1] - 1),
                'target': batch['target'], 'distractor': batch['distractor']}

    def model_inputs(self, batch):
        return {k: batch[k] for k in ('input_ids', 'attention_mask', 'corrupted_input_ids') if k in batch}


def score_row(ctx, row, masks):
    from evaluation.metrics import evaluate_pred_position
    ids, attention = aligned_inputs(row['recipient'], row['donor'])
    batch = {'input_ids': ids, 'attention_mask': attention,
             'target': torch.tensor([row['labels']['D']['token_id']]),
             'distractor': torch.tensor([row['labels']['H']['token_id']])}
    if row['donor'] is not None:
        batch['corrupted_input_ids'] = torch.tensor([row['donor']['input_ids']])
    with (ctx.all_gates_open() if masks is None else ctx.circuit(masks)):
        out = evaluate_pred_position(ctx, [batch], use_reference=False,
                                     collect_per_example=True, desc='Frozen score')
    p = out['per_example'][0]
    a = p['argmax_id']
    return {'D_logit': p['target_logit'], 'H_logit': p['distractor_logit'],
            'D_probability': p['target_probability'], 'H_probability': p['distractor_probability'],
            'label_probability_mass': p['label_probability_mass'], 'D_minus_H': p['logit_diff'],
            'pairwise_D_preferred': p['target_logit'] > p['distractor_logit'],
            'argmax_token_id': a, 'argmax_text': ctx.tokenizer.decode([a]),
            'argmax_category': 'D' if a == p['target_id'] else 'H' if a == p['distractor_id'] else 'other'}


def reference_stream(prompt, reference, new_tokens, pad_id):
    from evaluation.benchmark_eval import pack_reference
    tokens = list(reference['token_ids'])
    if reference['termination'] == 'eos':
        tokens.append(reference['eos_token_id'])
    width = len(prompt['input_ids'])
    prefix_padding = width - sum(prompt['attention_mask'])
    prompt_tokens = prompt['input_ids'][prefix_padding:]
    length = len(prompt_tokens) + new_tokens
    packed, tiled = pack_reference(prompt_tokens, tokens, length, pad_id)
    flags = {'tiled': tiled, 'truncated': len(prompt_tokens) + len(tokens) > length,
             'early_eos': reference['termination'] == 'eos',
             'empty_continuation': not reference['token_ids'],
             'filler': 'continuation' if tokens else 'prompt',
             'padding_columns': prefix_padding, 'prompt_aligned': True}
    return torch.tensor([[pad_id] * prefix_padding + packed]), flags


def generate_row(ctx, row, masks, reference, *, eos_ids):
    from evaluation.gen_engine import generate, resolve_pad_id
    ids, attention = aligned_inputs(row['recipient'], row.get('donor'))
    cap = row['decode']['max_new_tokens']
    pad = resolve_pad_id(ctx.tokenizer, eos_ids)
    flags = None
    if reference is not None:
        corrupt, flags = reference_stream(row['donor'], reference, cap, pad)
    else:
        from evaluation.benchmark_eval import placeholder_corrupt
        corrupt = placeholder_corrupt(ids, attention, cap, pad)
    with (ctx.all_gates_open() if masks is None else ctx.circuit(masks)):
        generated = generate(ctx, clean_ids=ids, corrupt_ids=corrupt,
                             attention_mask=attention, new_tokens=cap, eos_ids=eos_ids,
                             use_cache=True)
    block = generated[0, ids.shape[1]:].tolist()
    stop = next((i for i, token in enumerate(block) if token in eos_ids), None)
    tokens = block if stop is None else block[:stop]
    repeated = 0 if len(tokens) < 2 else (len(tokens) - len(set(tokens))) / len(tokens)
    text = ctx.tokenizer.decode(tokens, skip_special_tokens=True)
    return {'text': text, 'token_ids': tokens,
            'termination': 'cap' if stop is None else 'eos',
            'eos_token_id': None if stop is None else block[stop],
            'prompt_length': int(attention.sum()), 'completion_length': len(tokens),
            'empty': not text.strip(), 'cap_hit': stop is None, 'repetition_fraction': repeated,
            'donor_reference': reference, 'donor_continuation': flags}


def execute(manifest, store, ctx, masks, subset='all'):
    from evaluation.benchmark_eval import eos_ids_for
    rows, refs = select_work(manifest, subset)
    eos = eos_ids_for(ctx.node_model)
    ko = {label: safe_knockout(mask) for label, mask in masks.items()}
    for row in donor_diagnostics(manifest, rows):
        if row['row_id'] not in store.results:
            payload = score_row(ctx, row, None)
            payload['intended_answer_argmax_valid'] = payload['argmax_category'] == row['intended_label']
            store.append(row, payload)
    # Every donor continuation is generated intact before any target intervention.
    for row in refs:
        if row['row_id'] not in store.results:
            request = {'recipient': row['prompt'], 'donor': None, 'decode': row['decode']}
            store.append(row, generate_row(ctx, request, None, None, eos_ids=eos))
    clusters = {c['cluster_id']: c for c in manifest['clusters']}
    for row in rows:
        if row['row_id'] in store.results:
            continue
        selected = ko.get(row['mask_label'])
        if row['kind'] == 'score':
            payload = score_row(ctx, row, selected)
        else:
            ref = None if not row['donor'] else store.results[row['donor']['reference_row_id']]['payload']
            request = dict(row, decode=manifest['config']['decode'])
            payload = generate_row(ctx, request, selected, ref, eos_ids=eos)
        if row['donor']:
            donor = row['donor']
            labels = clusters[donor['cluster_id']]['labels']
            diagnostic_id = 'donor-score-' + content_hash({'input_ids': donor['input_ids'],
                                                          'attention_mask': donor['attention_mask'], 'labels': labels})
            diagnostic = store.results[diagnostic_id]['payload']
            actual = diagnostic.get('argmax_token_id')
            payload['donor_intact_score_row_id'] = diagnostic_id
            payload['donor_argmax_relation_to_recipient'] = next(
                (label for label in ('D', 'H') if actual == row['labels'][label]['token_id']), 'other')
        payload['identity_sanity_check'] = row['identity_sanity_check']
        store.append(row, payload)
    summary = summarize(manifest, store)
    atomic_json(store.path / 'summary.json', summary)
    return summary


def summarize(manifest, store):
    missing = sorted(set(store.expected) - set(store.results))
    rows = {r['row_id']: r for r in manifest['rows']}
    counts, quality, sanity = Counter(), Counter(), []
    for rid, record in store.results.items():
        r = rows.get(rid)
        if r is None:
            continue
        p = record['payload']
        counts[(r['kind'], r['view'], r['policy'], r['condition'])] += 1
        if r['kind'] == 'generation':
            for flag in ('empty', 'cap_hit'):
                quality[flag] += bool(p.get(flag))
        if r['identity_sanity_check']:
            baseline = next((b for b in manifest['rows'] if b['kind'] == r['kind'] and
                             b['cluster_id'] == r['cluster_id'] and b['view'] == r['view'] and
                             b['policy'] == r['policy'] and b['condition'] == 'intact'), None)
            if baseline and baseline['row_id'] in store.results:
                b = store.results[baseline['row_id']]['payload']
                passed = (p['token_ids'] == b['token_ids'] if r['kind'] == 'generation' else
                          max(abs(p[k] - b[k]) for k in ('D_logit', 'H_logit')) <= 0.02)
                sanity.append({'row_id': rid, 'passed': passed,
                               'tolerance': 'exact_tokens' if r['kind'] == 'generation' else 0.02})
    return {'complete': not missing, 'manifest_hash': manifest['manifest_hash'],
            'completed_outputs': len(store.results), 'declared_outputs': len(store.expected),
            'missing_ids': missing, 'quality': dict(quality), 'identity_sanity': sanity,
            'routing_counts': [{'kind': k[0], 'view': k[1], 'policy': k[2], 'condition': k[3], 'n': v}
                               for k, v in sorted(counts.items())],
            'generated_deception_endpoint': 'incomplete_pending_blinded_semantic_annotation',
            'selectivity_interpretation': 'conditional_on_nonself_mismatched_content_interchange',
            'paired_H_identity_role': 'sanity_only_not_utility_retention_evidence'}


def export_blind(manifest, store, output_dir):
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    clusters = {c['cluster_id']: c for c in manifest['clusters']}
    rows = [r for r in manifest['rows'] if r['kind'] == 'generation' and r['row_id'] in store.results]
    random.Random(0).shuffle(rows)
    public, private = [], []
    for i, r in enumerate(rows):
        anonymous = 'response-%04d' % i
        p = store.results[r['row_id']]['payload']
        public.append({'anonymous_id': anonymous, 'prompt': r['recipient']['text'],
                       'ground_truth': {'scenario': clusters[r['cluster_id']]['scenario'],
                                        'truthful_answer': r['labels']['H']['text'],
                                        'deceptive_answer': r['labels']['D']['text']},
                       'output': p['text'], 'quality': {k: p.get(k) for k in
                               ('empty', 'cap_hit', 'termination', 'repetition_fraction')}})
        private.append({'anonymous_id': anonymous, 'row_id': r['row_id'], 'condition': r['condition'],
                        'donor': r['donor'], 'manifest_hash': manifest['manifest_hash']})
    for name, records in (('responses.jsonl', public), ('private_mapping.jsonl', private)):
        path = directory / name
        with path.open('w') as f:
            os.chmod(path, 0o600)
            for record in records:
                f.write(canonical_json(record) + '\n')
