"""Private twin training contract; sources are never rewritten."""
import copy
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
            row['source_row_hashes'] = {'D': 'd'*64, 'H': 'e'*64}
            rows[split] = [row]
        path = tmp_path / ('explicit-'+kind)
        save_splits(rows, str(path))
        (path/'dataset_config.json').write_text(json.dumps(dict(task='far_v2', condition=condition,
            baseline_kind='matched_frame_neutral_request', model='fake', margin_thresh=.5)))
        mapping['far_v2'][kind] = str(path)
    return dict(root_d=roots['D'], root_h=roots['H'], root_i=None, root_i_neutral=None,
                output_root=str(tmp_path/'matched'), tasks=['far_v2'], cohort='matched',
                tokenizer=FakeWordTokenizer(), max_length=30, commit='a'*40, input_paths=mapping)


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
    assert i['train'][0]['source_reference']['source_row_hashes']['H'] == 'e'*64


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
