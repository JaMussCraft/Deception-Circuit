"""Prospective, model-independent utility samples for the specificity ladder.

Only clean rows are utility assessments. IOI repeated-B prompts are donors,
not a second truth-labelled assessment. MMLU has no native item-swap task.
The manifest is preparation provenance, never authorization to score MMLU.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import random

NEUTRAL_SYSTEM = 'Answer the multiple-choice question. Respond with only the correct letter.'
MMLU_REVISION = 'c30699e8356da336a370243923dbaf21066bb9fe'


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _file_hash(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _encode(tokenizer, text, special=False):
    return list(map(int, tokenizer.encode(text, add_special_tokens=special)))


def _context_token(tokenizer, prefix, answer, tokens, special=False):
    """Require an exact prefix extension, not merely standalone name length."""
    extended = _encode(tokenizer, prefix + ' ' + answer, special)
    if extended[:-1] != tokens or len(extended) != len(tokens) + 1:
        raise ValueError('answer is not one contextual token')
    return extended[-1]


def _stream(tokenizer, prefix, answers, special=False, raw_layout=False):
    tokens = _encode(tokenizer, prefix, special)
    if not tokens:
        raise ValueError('empty prefix')
    choices = [_context_token(tokenizer, prefix, answer, tokens, special) for answer in answers]
    if len(set(choices)) != len(choices):
        raise ValueError('answer token collision')
    # Raw IOI is a single text span. Chat MMLU has no fabricated role map:
    # only its readout calibration is supported, regardless of equal lengths.
    layout = dict(role_spans=[['text', 0, len(tokens)]],
                  content_spans=[['text', 0, len(tokens)]]) if raw_layout else None
    return dict(prompt=prefix, prompt_utf8_hex=prefix.encode().hex(), tokens=tokens,
                attention_mask=[1] * len(tokens), readout=len(tokens)-1,
                layout=layout, answer_tokens=choices)


def _generate_ioi(tokenizer, count, seed):
    from dataset import ioi_llama
    # Upstream load_names uses set order, which otherwise defeats seed replay
    # across Python processes. Preserve its vocabulary, canonically order it.
    names = ioi_llama.filter_single_token_names(sorted(ioi_llama.load_names()), tokenizer)
    state = random.getstate()
    try:
        return ioi_llama.generate_ioi_data_llama(count, tokenizer, seed=seed, name_pool=names)
    finally:
        random.setstate(state)


def _remove_answer(sentence, name):
    suffix = ' ' + name
    if not sentence.endswith(suffix):
        raise ValueError('final answer name mismatch or word boundary')
    return sentence[:-len(suffix)]


def _ioi_candidates(tokenizer, *, count, seed):
    from dataset import ioi_llama
    source_hash = _hash(dict(generator=_file_hash(ioi_llama.__file__),
                             names=_file_hash(Path(ioi_llama.__file__).with_name('names.json')),
                             name_order='sorted', seed=seed, count=count))
    seen = set()
    for index, item in enumerate(_generate_ioi(tokenizer, count, seed)):
        try:
            a, b = item['a'], item['b']
            clean_prefix = _remove_answer(item['sentence'], a)
            corrupt_prefix = _remove_answer(item['corrupted_sentence'], b)
            signature = (clean_prefix, corrupt_prefix, a, b)
            if signature in seen:
                continue
            seen.add(signature)
            clean = _stream(tokenizer, clean_prefix, [a,b], True, True)
            corrupt = _stream(tokenizer, corrupt_prefix, [a,b], True, True)
        except (ValueError, KeyError, TypeError):
            continue
        rid = f'ioi:seed={seed}:row={index}'
        yield dict(instance_id=rid, source_id=rid, task='ioi', condition='IOI',
                   source_condition='IOI', split='generated', source_hash=source_hash,
                   a=a, b=b, template_order=item.get('template_order'),
                   expected_token=clean['answer_tokens'][0], honest_token=clean['answer_tokens'][0],
                   opposite_token=clean['answer_tokens'][1],
                   streams=dict(clean=clean, corrupt=corrupt),
                   sampling=dict(seed=seed, generated=count, selection='first eligible unique prefixes; no model filtering',
                                 names_order='sorted'))


def ioi_rows(tokenizer, *, n=100, seed=1):
    if n < 1:
        raise ValueError('n must be positive')
    # Consume the fixed 1000 generator rows even for a pilot; no outcome filter.
    candidates = list(_ioi_candidates(tokenizer, count=1000, seed=seed))
    if len(candidates) < n:
        raise ValueError(f'insufficient eligible IOI rows: {len(candidates)} < {n}')
    return candidates[:n]


def _cached_mmlu():
    """Inspect the same sorted parquet order used by local-only hf_config."""
    from evaluation.benchmarks.sources import hf_snapshot, hf_config
    snapshot = Path(hf_snapshot('cais/mmlu'))
    frame = hf_config('cais/mmlu', 'all', split='test')
    paths = sorted((snapshot / 'all').glob('test-*.parquet'))
    if not paths:
        raise FileNotFoundError('MMLU test parquet missing from local snapshot')
    import pyarrow.parquet as pq
    records, offset, hashes = [], 0, {}
    for path in paths:
        relative = str(path.relative_to(snapshot))
        digest = _file_hash(path)
        hashes[relative] = digest
        size = pq.ParquetFile(path).metadata.num_rows
        for local_index in range(size):
            record = frame.iloc[offset + local_index].to_dict()
            record.update(source_id=f'{relative}:{local_index:08d}', source_hash=digest)
            records.append(record)
        offset += size
    if offset != len(frame):
        raise ValueError('cached parquet row count changed during inspection')
    return records, dict(dataset='cais/mmlu', config='all', split='test', revision=snapshot.name,
                         snapshot=str(snapshot), parquet_hashes=hashes)


def mmlu_rows(tokenizer, *, n=32, seed=1, max_length=1024):
    from evaluation.benchmarks.sandbagging import format_question
    if n < 1 or max_length < 1:
        raise ValueError('positive sample size and max_length required')
    items, provenance = _cached_mmlu()
    ids = [item['source_id'] for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate MMLU source ids')
    rejected = dict(malformed=0, overlength=0, contextual_tokens=0)
    eligible = []
    for item in sorted(items, key=lambda row: row['source_id']):
        choices = item.get('choices')
        answer = item.get('answer')
        try:
            choices = list(choices)
            valid = (len(choices)==4 and all(isinstance(c,str) and c.strip() for c in choices)
                     and isinstance(item.get('question'),str) and bool(item['question'].strip())
                     and not isinstance(answer, bool) and int(answer)==answer and 0 <= int(answer) < 4)
        except (TypeError, ValueError, OverflowError):
            valid = False
        if not valid:
            rejected['malformed'] += 1
            continue
        messages = [dict(role='system',content=NEUTRAL_SYSTEM),
                    dict(role='user',content=format_question(item['question'], choices))]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True) + 'Answer:'
        if len(_encode(tokenizer,prompt)) > max_length:
            rejected['overlength'] += 1
            continue
        try:
            clean = _stream(tokenizer,prompt,list('ABCD'))
        except ValueError:
            rejected['contextual_tokens'] += 1
            continue
        gold = int(answer)
        expected = clean['answer_tokens'][gold]
        eligible.append(dict(instance_id='mmlu:'+item['source_id'], source_id=item['source_id'],
                             task='mmlu', condition='MMLU', source_condition='MMLU', split='test',
                             source_hash=item['source_hash'], source_revision=provenance['revision'],
                             gold_letter='ABCD'[gold], question_hash=_hash(item['question']),
                             expected_token=expected, honest_token=expected,
                             opposite_token=clean['answer_tokens'][(gold+1)%4],
                             opposite_semantics='arbitrary diagnostic only; use four-option margin',
                             choice_tokens=clean['answer_tokens'], streams=dict(clean=clean)))
    if len(eligible) < n:
        raise ValueError(f'insufficient eligible MMLU rows: {len(eligible)} < {n}; rejected={rejected}')
    rows = random.Random(seed).sample(eligible,n)
    manifest = dict(provenance, seed=seed,n=n,max_length=max_length,eligible=len(eligible),rejected=rejected,
                    sample_ids=[r['source_id'] for r in rows],sample_hash=_hash(rows),
                    prompt_format_hash=hashlib.sha256(inspect.getsource(format_question).encode()).hexdigest(),
                    adapter_source_hash=_file_hash(__file__), grader_registry=None,
                    tokenizer_identity=dict(name_or_path=getattr(tokenizer,'name_or_path',None),
                                            init_commit=getattr(tokenizer,'init_kwargs',{}).get('_commit_hash'),
                                            chat_template_hash=_hash(getattr(tokenizer,'chat_template',None)),
                                            loading=getattr(tokenizer,'_user_inversion_loading',None)),
                    status='prospective preparation only; frozen grader registry required before scoring',
                    grading='full-vocabulary expected-letter argmax; restricted option accuracy/margin diagnostic')
    return rows, manifest


def task_batches(rows, *, batch_size=16, stream='clean', pad_token_id=0):
    """Right-pad normalized rows, with corrupt IOI exposed only on request as donors."""
    import torch
    from component_analysis.specificity_ladder import LadderBatch, validate_batch
    if batch_size < 1 or not rows:
        raise ValueError('positive batch size and nonempty rows required')
    if len({r['instance_id'] for r in rows}) != len(rows):
        raise ValueError('duplicate task row ids')
    if len({(r['task'],r['condition']) for r in rows})!=1:
        raise ValueError('cannot mix tasks/conditions in batch')
    output=[]
    for offset in range(0,len(rows),batch_size):
        chunk=rows[offset:offset+batch_size]
        streams=[r['streams'][stream] for r in chunk]
        width=max(len(s['tokens']) for s in streams)
        tokens=torch.tensor([s['tokens']+[pad_token_id]*(width-len(s['tokens'])) for s in streams])
        masks=torch.tensor([[1]*len(s['tokens'])+[0]*(width-len(s['tokens'])) for s in streams])
        records=[dict(r, tokens=s['tokens'],layout=s['layout'],utility_assessment=(stream=='clean')) for r,s in zip(chunk,streams)]
        choice=torch.tensor([r['choice_tokens'] for r in chunk]) if chunk[0]['task']=='mmlu' else None
        batch=LadderBatch(ids=[r['instance_id'] for r in chunk], condition=chunk[0]['condition'],stream=stream,
                          input_ids=tokens,attention_mask=masks,readout=torch.tensor([s['readout'] for s in streams]),
                          opposite_token=torch.tensor([r['opposite_token'] for r in chunk]),
                          honest_token=torch.tensor([r['honest_token'] for r in chunk]),
                          expected_token=torch.tensor([r['expected_token'] for r in chunk]),
                          records=records,task=chunk[0]['task'],choice_tokens=choice)
        validate_batch(batch)
        output.append(batch)
    return output


def _map(recipient, donor, *, donor_stream, operation, readout_only=False, seed=None):
    left=recipient['streams']['clean']; right=donor['streams'][donor_stream]
    supported=readout_only or (left['layout'] is not None and left['layout']==right['layout']
                               and len(left['tokens'])==len(right['tokens']))
    no_op=supported and left['tokens']==right['tokens']
    requested=1 if readout_only else len(left['tokens'])
    return dict(requested_positions=requested,covered_positions=requested if supported else 0,
                no_op=no_op,degenerate=no_op,gate_valid=supported and not no_op,
                recipient_id=recipient['instance_id'],recipient_condition=recipient['condition'],recipient_stream='clean',
                donor_id=donor['instance_id'],donor_condition=donor['condition'],donor_stream=donor_stream,
                operation=operation,seed=seed,supported=supported,
                unsupported_reason=None if supported else 'unequal or missing validated full token layouts',
                recipient_positions=([left['readout']] if readout_only else list(range(len(left['tokens'])))) if supported else [],
                donor_positions=([right['readout']] if readout_only else list(range(len(right['tokens'])))) if supported else [],
                donor_source_hash=donor['source_hash'], donor_source_id=donor['source_id'],donor_split=donor['split'])


def ioi_item_swap_maps(rows):
    return [_map(r,r,donor_stream='corrupt',operation='item_swap') for r in rows]


def ioi_task_resample(tokenizer, rows, *, donor_seeds=(101,102,103), count=20000):
    """Optional own-task donor pools, never H donors or outcome-selected rows."""
    donors, maps = [], []
    assessment_prefixes={r['streams']['clean']['prompt'] for r in rows}
    for seed in donor_seeds:
        pool=list(_ioi_candidates(tokenizer,count=count,seed=seed))
        for recipient in rows:
            left=recipient['streams']['clean']
            eligible=[d for d in pool if d['a']==recipient['a'] and d['b']==recipient['b']
                      and d['streams']['clean']['prompt'] not in assessment_prefixes
                      and d['streams']['clean']['layout']==left['layout']
                      and len(d['streams']['clean']['tokens'])==len(left['tokens'])]
            if eligible:
                chosen=random.Random(_hash([recipient['instance_id'],seed])).choice(eligible)
                donors.append(chosen)
                maps.append(_map(recipient,chosen,donor_stream='clean',operation='task_resample',seed=seed))
            else:
                maps.append(dict(recipient_id=recipient['instance_id'],recipient_condition='IOI',recipient_stream='clean',
                                 operation='task_resample',seed=seed,supported=False,
                                 requested_positions=len(left['tokens']),covered_positions=0,
                                 gate_valid=False,no_op=False,degenerate=False,
                                 unsupported_reason='no separate different-prefix same-name layout-matched IOI donor',
                                 recipient_positions=[],donor_positions=[]))
    return list({d['instance_id']:d for d in donors}.values()),maps


def mmlu_calibration_maps(rows):
    """Frozen cyclic different-question readout calibration, never item swap."""
    if len(rows)<2:
        raise ValueError('calibration needs at least two MMLU questions')
    result=[]
    for index,recipient in enumerate(rows):
        cyclic=[r for r in rows[index+1:]+rows[:index] if r['instance_id']!=recipient['instance_id']
                and r['question_hash']!=recipient['question_hash']]
        if not cyclic:
            raise ValueError('calibration needs a genuinely different question')
        donor=next((r for r in cyclic if r['gold_letter']!=recipient['gold_letter']),cyclic[0])
        result.append(_map(recipient,donor,donor_stream='clean',operation='positive_calibration',readout_only=True))
    return result
