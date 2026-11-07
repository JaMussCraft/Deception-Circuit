import copy
import json
from types import SimpleNamespace
import pytest

from evaluation.benchmarks.base import BenchmarkItem, DECEPTIVE, HONEST, UNPARSED
from evaluation.fixed_benchmark_cohort import import_dataset, load_fixed_cohort, import_judge_caches, IMPORT_VERSION, SUITES, RELATIVE_RESULT, _fingerprint
from evaluation.frozen_head_masks import binding, digest


class Bench:
    def parse_judgement(self, item, response, judge_text):
        return (UNPARSED, 'evasive:D') if judge_text == 'D' else (DECEPTIVE, 'B')
    def judge_request(self, item, response): return None
    def honest_twin(self, item): return None


def historical():
    selected = [BenchmarkItem('selected-é'+str(i), [{'role':'user','content':'Café Ω '+str(i)}], DECEPTIVE, belief='yes', meta={'π':['雪',i]}).to_json() for i in range(3)]
    donors = [BenchmarkItem('donor-'+str(i), [{'role':'user','content':'Safe donor '+str(i)}], HONEST) for i in range(2)]
    h = dict(items=selected, n_items=3, prompts=['rendered-é'+str(i) for i in range(3)],
             partner_ids=['donor-0','donor-1','donor-0'], new_tokens=512,
             reference=dict(pool='honest', pairing='derangement',pool_size=4),
             configs={'full':dict(generations=['false']*3,
                        labels=[dict(label=DECEPTIVE,raw=x,judge_prompt=None,judge_text=x,judge_error=None) for x in ['B','D','B']])})
    return h, [BenchmarkItem(**r) for r in selected] + donors


def manifest(tmp_path):
    h, source_items = historical()
    source = tmp_path/'original.json'
    source.write_text(json.dumps({'datasets':{'mask:fixture':h}},ensure_ascii=False))
    sb = binding(source)
    dataset = import_dataset('mask:fixture',h,Bench(),source_items,sb,{'device':'NVIDIA A40'})
    data = dict(schema_version=1, import_version=IMPORT_VERSION,
                purpose='historical_selected_fixed_cohort_not_screen_cache',no_refill=True,
                fresh_intact_required=True,source_bindings=[sb],datasets={'mask:fixture':dataset})
    data['content_sha256'] = digest(data)
    path = tmp_path/'cohort.json'
    path.write_text(json.dumps(data,ensure_ascii=False))
    return path, data, h


def test_offline_correction_unicode_full_metadata_and_exact_donors(tmp_path):
    path,data,h = manifest(tmp_path)
    row = load_fixed_cohort(path,'mask:fixture')
    assert row['items'] == [h['items'][0],h['items'][2]]
    assert row['partner_index'] == [0,0]
    assert row['pool_items'][0]['item_id'] == 'donor-0'
    assert row['excluded'][0]['original_label']['raw'] == 'D'
    assert row['excluded'][0]['corrected_label'] == UNPARSED
    assert row['excluded'][0]['exclusion_reason'] == 'corrected_historical_intact_not_deceptive:evasive:D'
    assert row['selection_provenance']['historical_pool_size'] == 4
    assert row['selection_provenance']['used_donor_count'] == 1
    assert row['items'][0]['meta']['π'] == ['雪',0]
    assert data['source_bindings'][0]['sha256'] == binding(data['source_bindings'][0]['path'])['sha256']


@pytest.mark.parametrize('bad', ['length','source','judge_error','missing_donor','duplicate','prompt_drift'])
def test_import_fails_closed(bad):
    h,src = historical()
    if bad == 'length': h['partner_ids'].pop()
    if bad == 'source': src = src[1:]
    if bad == 'judge_error': h['configs']['full']['labels'][0]['judge_error'] = 'HTTP 402'
    if bad == 'missing_donor': src = src[:3]
    if bad == 'duplicate': h['items'][1] = h['items'][0]
    if bad == 'prompt_drift': src[0] = src[0].replace(messages=[{'role':'user','content':'different'}])
    with pytest.raises(ValueError): import_dataset('mask:fixture',h,Bench(),src,{}, {'device':'A40'})


@pytest.mark.parametrize('kind', ['content','source_bytes','partner','item_source'])
def test_manifest_tampering_fails(tmp_path,kind):
    path,data,h = manifest(tmp_path)
    if kind == 'source_bytes':
        with open(data['source_bindings'][0]['path'],'a') as f:f.write(' ')
    else:
        row=data['datasets']['mask:fixture']
        if kind == 'content':row['items'][0]['meta']['π']=['changed']
        if kind == 'partner':row['partner_index'][0]=42
        if kind == 'item_source':row['items'][0]['belief']='forged'
        if kind != 'content':data['content_sha256']=digest({k:v for k,v in data.items() if k!='content_sha256'})
        path.write_text(json.dumps(data,ensure_ascii=False))
    with pytest.raises(ValueError):load_fixed_cohort(path,'mask:fixture')


def test_cache_version_records_old_duplicates_and_excludes_cross_source_conflicts(tmp_path):
    a,b,c='a'*64,'b'*64,'c'*64
    rows = [[(a,'old'),(a,'last'),(b,'consistent')],[(a,'other-suite'),(b,'consistent'),(c,'new')]]
    for suite, entries in zip(SUITES,rows):
        p=tmp_path/'outputs'/suite/'judge_cache.jsonl';p.parent.mkdir(parents=True)
        p.write_text(''.join(json.dumps(dict(key=k,text=v))+'\n' for k,v in entries))
    result=import_judge_caches(tmp_path,tmp_path/'import.jsonl')
    assert result['imported_bytes'] == (tmp_path/'import.jsonl').stat().st_size
    assert result['sources'][0]['differing_duplicate_occurrences']==1
    assert result['cross_source_conflicting_keys']==[a]
    assert [json.loads(r) for r in (tmp_path/'import.jsonl').read_text().splitlines()] == [dict(key=b,text='consistent'),dict(key=c,text='new')]


def test_exact_request_fingerprint_is_official_unicode_contract():
    from evaluation.benchmarks.base import JudgeRequest
    from evaluation.benchmarks.judge import request_key
    request=JudgeRequest('openrouter','judge', [{'role':'user','content':'é 雪 Ω'}],kwargs={'temperature':0},schema=None)
    assert _fingerprint(request)==request_key(request)
    changed=JudgeRequest('openrouter','other',request.messages,kwargs=request.kwargs)
    assert _fingerprint(request)!=_fingerprint(changed)


@pytest.mark.parametrize('kind', ['missing', 'negative', 'bool', 'short', 'changed_prefix', 'valid_append'])
def test_imported_cache_byte_prefix_receipt(tmp_path, kind):
    import hashlib
    path, data, _ = manifest(tmp_path)
    cache = tmp_path/'study-cache.jsonl'
    prefix = (json.dumps(dict(key='e'*64, text='é 雪'), ensure_ascii=False)+'\n').encode('utf-8')
    cache.write_bytes(prefix)
    receipt = dict(sources=[], output=binding(cache), imported_bytes=len(prefix))
    data['judge_cache_import'] = receipt
    if kind == 'missing': del receipt['imported_bytes']
    if kind == 'negative': receipt['imported_bytes'] = -1
    if kind == 'bool': receipt['imported_bytes'] = True
    if kind == 'short': receipt['imported_bytes'] -= 1
    if kind == 'changed_prefix': cache.write_bytes(prefix.replace(b'e', b'f', 1))
    if kind == 'valid_append':
        with cache.open('ab') as handle: handle.write((json.dumps(dict(key='f'*64,text='new'))+'\n').encode('utf-8'))
    data['content_sha256'] = digest({k:v for k,v in data.items() if k!='content_sha256'})
    path.write_text(json.dumps(data,ensure_ascii=False))
    if kind == 'valid_append':
        assert len(load_fixed_cohort(path,'mask:fixture')['items']) == 2
    else:
        with pytest.raises(ValueError): load_fixed_cohort(path,'mask:fixture')
