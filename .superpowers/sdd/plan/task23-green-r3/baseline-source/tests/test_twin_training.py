"""Private twin training contract; sources are never rewritten."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from datasets import load_from_disk
from tests.fakes import FakeWordTokenizer


def sources():
    d, h = {}, {}
    for split in ('train', 'validation', 'test'):
        row = dict(instance_id=split + '-1', task='far_v2', pressure_id='p1',
                   entity='Acme', item_1='beams', item_2='joints', clean_item_d='beams',
                   desig='failing', desig_inv='passing', template_variant='audit',
                   item_polarity=1, designation_polarity='inversion',
                   condition='deceptive', pressure='Lie now', target='joints',
                   distractor='beams', clean_prompt='System beams failing. Lie now<|eot_id|> user question readout',
                   corrupt_prompt='System joints failing. Lie now<|eot_id|> user question readout',
                   neutral_text='File now', honest_twin_kind=None)
        twin = dict(row, condition='honest', pressure='File now', honest_twin_kind='neutral_clause',
                    target='beams', distractor='joints',
                    clean_prompt=row['clean_prompt'].replace('Lie now', 'File now'),
                    corrupt_prompt=row['corrupt_prompt'].replace('Lie now', 'File now'))
        d[split], h[split] = [row], [twin]
    return d, h


def builder():
    from dataset import build_twin_training
    return build_twin_training


def test_validates_real_reference_and_keeps_sources_unchanged():
    d, h = sources()
    before = copy.deepcopy((d, h))
    result = builder().validate_sources(d, h, tokenizer=FakeWordTokenizer(), max_length=30)
    assert result['ids']['train'] == ['train-1']
    assert result['pairs']['train']['train-1']['reference_prompt'] == h['train'][0]['clean_prompt']
    assert (d, h) == before


@pytest.mark.parametrize('case', ['duplicate', 'leak', 'missing', 'item', 'designation', 'question',
                                 'condition', 'twin', 'donor_corrupt', 'length', 'outside',
                                 'multiple', 'overlength', 'label'])
def test_rejects_invalid_sources(case):
    d, h = sources()
    if case == 'duplicate': d['train'] *= 2
    elif case == 'leak': d['test'].append(dict(d['train'][0]))
    elif case == 'missing': h['train'] = []
    elif case == 'item': h['train'][0]['item_1'] = 'changed'
    elif case == 'designation': h['train'][0]['desig'] = 'changed'
    elif case == 'question': h['train'][0]['clean_prompt'] += ' question'
    elif case == 'condition': h['train'][0]['condition'] = 'deceptive'
    elif case == 'twin': h['train'][0]['honest_twin_kind'] = 'harvested'
    elif case == 'donor_corrupt': h['train'][0]['clean_prompt'] = h['train'][0]['corrupt_prompt']
    elif case == 'length': h['train'][0]['clean_prompt'] = h['train'][0]['clean_prompt'].replace('File now', 'File')
    elif case == 'outside': h['train'][0]['clean_prompt'] = h['train'][0]['clean_prompt'].replace('beams', 'joints')
    elif case == 'multiple': d['train'][0]['clean_prompt'] += ' Lie now<|eot_id|>'
    elif case == 'label': d['train'][0]['target'] = 'two words'
    with pytest.raises(ValueError):
        builder().validate_sources(d, h, tokenizer=FakeWordTokenizer(), max_length=2 if case == 'overlength' else 30)


def write_sources(tmp_path, d, h):
    from dataset.build_deception_dataset import save_splits
    roots = {}
    for kind, rows, condition in [('D', d, 'deceptive'), ('H', h, 'honest')]:
        path = tmp_path / kind / ('far_v2_honest' if kind == 'H' else 'far_v2')
        save_splits(rows, str(path))
        config = dict(task='far_v2', condition=condition, margin_thresh=.3 if kind == 'H' else .7,
                      model='fake', honest_twin_kind='neutral_clause' if kind == 'H' else None)
        (path / 'dataset_config.json').write_text(json.dumps(config))
        roots[kind] = str(path.parent)
    return roots


def build(tmp_path, **kwargs):
    d, h = sources()
    roots = write_sources(tmp_path, d, h)
    args = dict(root_d=roots['D'], root_h=roots['H'], root_i=None, root_i_neutral=None,
                output_root=str(tmp_path / 'out'), tasks=['far_v2'], cohort='timing-d-only',
                tokenizer=FakeWordTokenizer(), max_length=30)
    args.update(kwargs)
    return builder().materialize(**args), args, d, h


def test_arrow_roundtrip_and_existing_training_loader(tmp_path):
    manifest, args, d, h = build(tmp_path)
    assert manifest['fleet_ready'] is False
    path = Path(args['output_root']) / 'D' / 'far_v2'
    row = dict(load_from_disk(str(path))['train'][0])
    assert row['clean_prompt'] == d['train'][0]['clean_prompt']
    assert row['corrupt_prompt'] == h['train'][0]['clean_prompt']
    assert row['target'] == d['train'][0]['target']
    assert row['source_recipient']['corrupt_prompt'] == d['train'][0]['corrupt_prompt']
    assert row['source_reference']['corrupt_prompt'] == h['train'][0]['corrupt_prompt']
    assert row['orientation'] == 'clean'
    from dataset.deception_common import DeceptionDatasetLlama, load_or_generate_deception_data
    loaded = load_or_generate_deception_data(str(path), split='train')
    ds = DeceptionDatasetLlama(loaded, args['tokenizer'], max_length=30)
    batch = ds[0]
    assert len(ds) == 1
    assert batch['attention_mask'].equal(batch['corrupted_attention_mask'])
    cfg = json.loads((path / 'dataset_config.json').read_text())
    assert cfg['condition'] == 'deceptive'
    assert cfg['recipient_condition'] == 'deceptive'
    assert cfg['label_semantics']['reference_expected'] == 'distractor'
    assert manifest['tasks']['far_v2']['sources']['H']['config']['margin_thresh'] == .3
    with pytest.raises(FileExistsError): builder().materialize(**args)


def test_validate_only_writes_nothing(tmp_path):
    result, args, _, _ = build(tmp_path, validate_only=True)
    assert not Path(args['output_root']).exists()
    assert result['fleet_ready'] is False


def test_modes_fail_closed(tmp_path):
    with pytest.raises(ValueError): build(tmp_path, cohort='matched')


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def byte_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_score_evidence(mapping, mutate=None, receipt_mutate=None):
    from dataset.build_user_inversion_v2 import score_pairs
    tok = FakeWordTokenizer()
    tok.encode('beams joints')
    score_files = {}
    blobs = {}
    for split in ('train', 'validation', 'test'):
        rows = {arm: dict(load_from_disk(mapping[kind])[split][0])
                for arm, kind in [('inversion', 'I'), ('baseline', 'I_neutral')]}
        pair = dict(instance_id=rows['inversion']['instance_id'], **rows)
        def native_score(prompts, words):
            return [dict(choice='b', margin=-.8, logit_a=0., logit_b=.8,
                         argmax_id=tok.encode(opposite)[0], argmax=tok.decode(tok.encode(opposite)))
                    for honest, opposite in words]
        records = score_pairs([pair], native_score)
        # Baseline deliberately fails competence; it must remain diagnostic.
        if mutate:
            mutate(split, records)
        blob = ''.join(json.dumps(r)+'\n' for r in records).encode()
        name = 'scores/'+split+'.jsonl'
        blobs[name] = blob
        score_files[split] = dict(path=name, sha256=hashlib.sha256(blob).hexdigest())
    receipt = dict(schema_version=1, kind='user_inversion_scored', source_commit='b'*40,
                   model='fake', model_revision='fake-model-revision', tokenizer='FakeWordTokenizer',
                   tokenizer_revision='fake-tokenizer-revision', request_pool_hash='c'*64,
                   scorer='dataset.deception_common.score_prompts', dtype='float32', score_files=score_files)
    if receipt_mutate:
        receipt_mutate(receipt)
    for root in mapping.values():
        path = Path(root)
        for name, blob in blobs.items():
            target = path/name
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(blob)
        target = path/'scoring_provenance.json'
        target.write_text(json.dumps(receipt))
        cfgpath = path/'dataset_config.json'
        cfg = json.loads(cfgpath.read_text())
        cfg['scoring_provenance'] = dict(path=target.name, sha256=byte_hash(target))
        cfgpath.write_text(json.dumps(cfg))


def matched_inputs(tmp_path):
    from dataset.build_deception_dataset import save_splits
    d, h = sources()
    # D/H include one row that is dropped by the smaller A1 cohort.
    for split in d:
        d[split].append(dict(d[split][0], instance_id=split+'-0'))
        h[split].append(dict(h[split][0], instance_id=split+'-0'))
    roots = write_sources(tmp_path, d, h)
    mapping = {'far_v2': {}}
    for kind, condition in [('I', 'user_inversion'), ('I_neutral', 'user_neutral')]:
        rows = {}
        for split in d:
            row = dict((d if kind == 'I' else h)[split][0], condition=condition,
                       baseline_kind='matched_frame_neutral_request', request_id='request-1',
                       request_text='Wrong please' if kind == 'I' else 'Right please',
                       pressure='File now', honest_twin_kind=None)
            row['clean_prompt'] = h[split][0]['clean_prompt'].replace('user question', 'user '+row['request_text']+'<|eot_id|>')
            row['corrupt_prompt'] = h[split][0]['corrupt_prompt'].replace('user question', 'user '+row['request_text']+'<|eot_id|>')
            row['request_spans'] = {'clean': [6, 8], 'corrupt': [6, 8]}
            row['source_row_hashes'] = {key: canonical_hash(original[split][0])
                                        for key, original in [('D', d), ('H', h)]}
            rows[split] = [row]
        path = tmp_path / ('explicit-'+kind)
        save_splits(rows, str(path))
        (path/'dataset_config.json').write_text(json.dumps(dict(task='far_v2', condition=condition,
            baseline_kind='matched_frame_neutral_request', model='fake',
            margin_thresh=.5 if kind == 'I' else .3)))
        mapping['far_v2'][kind] = str(path)
    write_score_evidence(mapping['far_v2'])
    tokenizer = FakeWordTokenizer()
    tokenizer.encode('beams joints')
    return dict(root_d=roots['D'], root_h=roots['H'], root_i=None, root_i_neutral=None,
                output_root=str(tmp_path/'matched'), tasks=['far_v2'], cohort='matched',
                tokenizer=tokenizer, max_length=30, commit='a'*40, input_paths=mapping)


def test_matched_explicit_paths_sorted_ids_and_attrition(tmp_path):
    args = matched_inputs(tmp_path)
    manifest = builder().materialize(**args)
    assert manifest['fleet_ready'] is True
    summary = manifest['tasks']['far_v2']
    assert summary['split_ids']['train'] == ['train-1']
    assert summary['attrition']['D']['train']['dropped_ids'] == ['train-0']
    d = load_from_disk(str(Path(args['output_root'])/'D'/'far_v2'))
    i = load_from_disk(str(Path(args['output_root'])/'I'/'far_v2'))
    assert d['train']['instance_id'] == i['train']['instance_id']
    assert i['train'][0]['corrupt_prompt'].endswith('user Right please<|eot_id|> readout')
    assert i['train'][0]['target'] == 'joints'
    assert i['train'][0]['source_recipient']['request_spans']['clean'] == [6, 8]
    assert i['train'][0]['source_reference']['source_row_hashes']['H'] == canonical_hash(sources()[1]['train'][0])


@pytest.mark.parametrize('case', ['commit', 'threshold', 'config_condition', 'baseline', 'dropped_leak',
                                 'cross_source_leak', 'cohort_identity'])
def test_matched_rejects_incomplete_or_leaking_inputs(tmp_path, case):
    from dataset.build_deception_dataset import save_splits
    args = matched_inputs(tmp_path)
    if case == 'commit': args['commit'] = None
    elif case in ('threshold', 'config_condition', 'baseline'):
        path = Path(args['input_paths']['far_v2']['I'])/'dataset_config.json'
        cfg = json.loads(path.read_text())
        if case == 'threshold': del cfg['margin_thresh']
        if case == 'config_condition': cfg['condition'] = 'inversion'
        if case == 'baseline': del cfg['baseline_kind']
        path.write_text(json.dumps(cfg))
    else:
        path = Path(args['root_d'])/'far_v2'
        rows = {s: list(load_from_disk(str(path))[s]) for s in ('train', 'validation', 'test')}
        cfg = (path/'dataset_config.json').read_text()
        if case == 'dropped_leak': rows['test'].append(dict(rows['train'][1]))
        if case == 'cross_source_leak': rows['test'][1]['instance_id'] = 'train-1'; rows['train'] = rows['train'][1:]
        if case == 'cohort_identity':
            # Both I rows can agree with each other while disagreeing with D.
            for kind in ('I', 'I_neutral'):
                ipath = Path(args['input_paths']['far_v2'][kind])
                ir = {s: list(load_from_disk(str(ipath))[s]) for s in rows}
                icfg = (ipath/'dataset_config.json').read_text()
                ir['train'][0]['item_1'] = 'changed'
                import shutil
                shutil.rmtree(ipath)
                save_splits(ir, str(ipath)); (ipath/'dataset_config.json').write_text(icfg)
        else:
            import shutil
            shutil.rmtree(path)
            save_splits(rows, str(path)); (path/'dataset_config.json').write_text(cfg)
    with pytest.raises(ValueError): builder().materialize(**args)


def test_optimized_python_still_rejects_invalid_alignment():
    import os
    import subprocess
    import sys
    script = '''from tests.test_twin_training import sources
from tests.fakes import FakeWordTokenizer
from dataset.build_twin_training import validate_sources
d,h=sources()
h['train'][0]['clean_prompt']=h['train'][0]['clean_prompt'].replace('beams','joints')
try:
 validate_sources(d,h,tokenizer=FakeWordTokenizer(),max_length=30)
except ValueError:
 pass
else:
 raise RuntimeError('optimized validation silently accepted invalid pair')
'''
    result = subprocess.run([sys.executable, '-O', '-c', script], capture_output=True, text=True,
                            env=dict(os.environ, OPENBLAS_NUM_THREADS='1'))
    assert result.returncode == 0, result.stderr


def test_rejects_unequal_masks_without_truncation():
    class UnequalMaskTokenizer(FakeWordTokenizer):
        def __call__(self, text, **kwargs):
            result = super().__call__(text, **kwargs)
            if 'File now' in text:
                result['attention_mask'][0, 0] = 0
            return result
    d, h = sources()
    with pytest.raises(ValueError, match='attention masks'):
        builder().validate_sources(d, h, tokenizer=UnequalMaskTokenizer(), max_length=30)


def test_source_bytes_unchanged_and_timing_forbids_peers(tmp_path):
    d, h = sources()
    roots = write_sources(tmp_path, d, h)
    before = {str(p): p.read_bytes() for root in roots.values() for p in Path(root).rglob('*') if p.is_file()}
    args = dict(root_d=roots['D'], root_h=roots['H'], root_i=None, root_i_neutral=None,
                output_root=str(tmp_path/'out'), tasks=['far_v2'], cohort='timing-d-only',
                tokenizer=FakeWordTokenizer(), max_length=30)
    builder().materialize(**args)
    assert all(Path(p).read_bytes() == data for p, data in before.items())
    args.update(root_i='peer', output_root=str(tmp_path/'forbidden'))
    with pytest.raises(ValueError, match='forbids peer'): builder().materialize(**args)


def test_neutral_config_kind_must_be_explicit(tmp_path):
    d, h = sources()
    roots = write_sources(tmp_path, d, h)
    path = Path(roots['H'])/'far_v2_honest'/'dataset_config.json'
    cfg = json.loads(path.read_text()); del cfg['honest_twin_kind']
    path.write_text(json.dumps(cfg))
    with pytest.raises(ValueError, match='twin kind'):
        builder().materialize(roots['D'], roots['H'], root_i=None, root_i_neutral=None,
            output_root=str(tmp_path/'out'), tasks=['far_v2'], cohort='timing-d-only',
            tokenizer=FakeWordTokenizer(), max_length=30)


def test_local_real_tokenizer_d_only_alignment():
    from transformers import AutoTokenizer
    from dataset import deception_common as dc
    try:
        tokenizer = AutoTokenizer.from_pretrained(dc.DEFAULT_MODEL, local_files_only=True)
    except (OSError, ValueError):
        pytest.skip('local Llama tokenizer unavailable')
    task = 'far_v2'
    root = Path(__file__).resolve().parents[1]/'data'/'datasets'
    if not (root/task/'dataset_config.json').exists(): pytest.skip('source dataset unavailable')
    d = {s: dc.load_or_generate_deception_data(str(root/task), split=s)[:2] for s in ('train','validation','test')}
    hrows = {s: dc.load_or_generate_deception_data(str(root/(task+'_honest')), split=s) for s in d}
    wanted = {s: set(r['instance_id'] for r in d[s]) for s in d}
    h = {s: [r for r in hrows[s] if r['instance_id'] in wanted[s]] for s in d}
    summary = builder().validate_sources(d,h,tokenizer=tokenizer,max_length=120)
    assert summary['counts'] == dict(train=2,validation=2,test=2)


def test_rejects_stale_request_spans(tmp_path):
    args = matched_inputs(tmp_path)
    from dataset.build_deception_dataset import save_splits
    import shutil
    path = Path(args['input_paths']['far_v2']['I'])
    cfg = (path/'dataset_config.json').read_text()
    rows = {s: list(load_from_disk(str(path))[s]) for s in ('train','validation','test')}
    rows['train'][0]['request_spans']['clean'] = [0, 8]
    shutil.rmtree(path)
    save_splits(rows,str(path)); (path/'dataset_config.json').write_text(cfg)
    with pytest.raises(ValueError, match='request span'):
        builder().materialize(**args)


@pytest.mark.parametrize('case', [
    'unscored', 'zero_margin', 'neutral_margin', 'model', 'h_model', 'tokenizer',
    'receipt_digest', 'receipt_escape', 'receipt_missing', 'receipt_difference',
    'commit', 'revision', 'request_hash', 'scorer', 'dtype', 'score_digest',
    'score_missing', 'score_escape', 'duplicate', 'cross_split_extra', 'missing_id',
    'prompt', 'baseline_prompt', 'canonical', 'nan', 'nan_logit', 'bool_argmax',
    'choice', 'weak_clean', 'weak_corrupt', 'wrong_argmax', 'signed_margin',
    'd_hash', 'h_hash',
])
def test_matched_requires_actual_scored_contract(tmp_path, case):
    # Removing any corresponding validation would admit this invalid scored input.
    args = matched_inputs(tmp_path)
    mapping = args['input_paths']['far_v2']
    ipath = Path(mapping['I'])
    if case in ('unscored', 'zero_margin', 'neutral_margin', 'model', 'h_model',
                'receipt_digest', 'receipt_escape', 'receipt_missing'):
        kind = 'I_neutral' if case == 'neutral_margin' else 'I'
        path = Path(mapping[kind])/'dataset_config.json'
        if case == 'h_model': path = Path(args['root_h'])/'far_v2_honest'/'dataset_config.json'
        cfg = json.loads(path.read_text())
        if case == 'unscored': del cfg['scoring_provenance']
        elif case in ('zero_margin', 'neutral_margin'): cfg['margin_thresh'] = 0
        elif case in ('model', 'h_model'): cfg['model'] = 'different'
        elif case == 'receipt_digest': cfg['scoring_provenance']['sha256'] = '0'*64
        elif case == 'receipt_escape': cfg['scoring_provenance']['path'] = '../scoring_provenance.json'
        elif case == 'receipt_missing': (ipath/'scoring_provenance.json').unlink()
        path.write_text(json.dumps(cfg))
    elif case == 'receipt_difference':
        path = ipath/'scoring_provenance.json'
        receipt = json.loads(path.read_text()); receipt['dtype'] = 'bfloat16'
        path.write_text(json.dumps(receipt))
        cfgpath = ipath/'dataset_config.json'
        cfg = json.loads(cfgpath.read_text()); cfg['scoring_provenance']['sha256'] = byte_hash(path)
        cfgpath.write_text(json.dumps(cfg))
    elif case in ('d_hash', 'h_hash'):
        from dataset.build_deception_dataset import save_splits
        import shutil
        cfg = (ipath/'dataset_config.json').read_text()
        rows = {s: list(load_from_disk(str(ipath))[s]) for s in ('train','validation','test')}
        rows['train'][0]['source_row_hashes']['D' if case == 'd_hash' else 'H'] = 'f'*64
        shutil.rmtree(ipath)
        save_splits(rows, str(ipath)); (ipath/'dataset_config.json').write_text(cfg)
        write_score_evidence(mapping)
    else:
        def mutate(split, records):
            if split != 'train': return
            score = records[0]['inversion']['clean']
            if case == 'duplicate': records.append(copy.deepcopy(records[0]))
            elif case == 'cross_split_extra':
                extra = copy.deepcopy(records[0]); extra['instance_id'] = 'test-1'; records.append(extra)
            elif case == 'missing_id': records.clear()
            elif case == 'prompt': score['prompt_hash'] = '0'*64
            elif case == 'baseline_prompt': records[0]['baseline']['corrupt']['prompt_hash'] = '0'*64
            elif case == 'canonical': score['expected_honest'] = 'wrong'
            elif case == 'nan': score['margin'] = float('nan')
            elif case == 'nan_logit': score['logit_a'] = float('inf')
            elif case == 'bool_argmax': score['argmax_id'] = True
            elif case == 'choice': score['choice'] = 'a'
            elif case in ('weak_clean', 'weak_corrupt'):
                weak = records[0]['inversion']['clean' if case == 'weak_clean' else 'corrupt']
                weak.update(margin=-.4, honest_minus_opposite=-.4, opposite_minus_honest=.4)
            elif case == 'wrong_argmax': score['argmax_id'] = 999
            elif case == 'signed_margin': score['opposite_minus_honest'] = 50
        def receipt_mutate(receipt):
            if case == 'tokenizer': receipt['tokenizer'] = 'other-tokenizer'
            elif case == 'commit': receipt['source_commit'] = 'short'
            elif case == 'revision': receipt['model_revision'] = ''
            elif case == 'request_hash': receipt['request_pool_hash'] = 'short'
            elif case == 'scorer': receipt['scorer'] = 'unknown'
            elif case == 'dtype': del receipt['dtype']
            elif case == 'score_digest': receipt['score_files']['train']['sha256'] = '0'*64
            elif case == 'score_escape': receipt['score_files']['train']['path'] = '../scores/train.jsonl'
        write_score_evidence(mapping, mutate, receipt_mutate)
        if case == 'score_missing': (ipath/'scores/train.jsonl').unlink()
    args['validate_only'] = True
    with pytest.raises(ValueError): builder().materialize(**args)
    assert not Path(args['output_root']).exists()


def test_matched_accepts_point_seven_with_baseline_failure(tmp_path):
    args = matched_inputs(tmp_path)
    path = Path(args['input_paths']['far_v2']['I'])/'dataset_config.json'
    cfg = json.loads(path.read_text()); cfg['margin_thresh'] = .7
    path.write_text(json.dumps(cfg))
    assert builder().materialize(**args)['fleet_ready'] is True


def test_score_id_cannot_borrow_an_unselected_other_split_source(tmp_path):
    args = matched_inputs(tmp_path)
    def mutate(split, records):
        if split == 'train':
            extra = copy.deepcopy(records[0])
            extra['instance_id'] = 'test-0'  # D/H test id dropped by A1 matching.
            records.append(extra)
    write_score_evidence(args['input_paths']['far_v2'], mutate)
    with pytest.raises(ValueError, match='score.*split'):
        builder().materialize(**args)


def test_extra_rejected_scores_and_native_rounded_margins_are_allowed(tmp_path):
    args = matched_inputs(tmp_path)
    def mutate(split, records):
        for arm in ('inversion', 'baseline'):
            for stream in ('clean', 'corrupt'):
                # Native low-precision subtraction need not equal promoted logits.
                records[0][arm][stream]['logit_b'] = .7999
        extra = copy.deepcopy(records[0])
        extra['instance_id'] = split+'-rejected'
        records.append(extra)
    write_score_evidence(args['input_paths']['far_v2'], mutate)
    args['validate_only'] = True
    manifest = builder().materialize(**args)
    assert manifest['tasks']['far_v2']['counts'] == dict(train=1, validation=1, test=1)
    assert not Path(args['output_root']).exists()
