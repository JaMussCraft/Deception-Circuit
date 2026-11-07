import re
import pytest
from component_analysis import ladder_tasks as tasks


class Tokenizer:
    pad_token_id = 0
    def encode(self, text, add_special_tokens=False):
        pieces = re.findall(r'\S+', text)
        result = [sum(map(ord, p)) for p in pieces]
        return ([1] if add_special_tokens else []) + result
    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        return '<bos> system ' + messages[0]['content'] + ' user ' + messages[1]['content'] + ' assistant '


def source(a='Alice', b='Bob', stem='Then, Bob and Alice met. Bob gave it to'):
    return dict(sentence=stem+' '+a, corrupted_sentence=stem.replace(a,b)+' '+b, a=a,b=b,template_order='baba')


def test_ioi_answer_removed_dedup_and_readout(monkeypatch):
    monkeypatch.setattr(tasks, '_generate_ioi', lambda t,n,s: [source(),source(),source(stem='After Bob and Alice met Bob spoke to')])
    rows = tasks.ioi_rows(Tokenizer(),n=2)
    assert len({r['instance_id'] for r in rows}) == 2
    for row in rows:
        assert not row['streams']['clean']['prompt'].endswith('Alice')
        assert not row['streams']['corrupt']['prompt'].endswith('Bob')
        assert row['streams']['clean']['tokens'][0] == 1
        assert row['streams']['clean']['readout'] == len(row['streams']['clean']['tokens'])-1
    batch = tasks.task_batches(rows,batch_size=2)[0]
    assert batch.stream == 'clean' and batch.task == 'ioi'
    assert batch.expected_token.tolist() == [sum(map(ord,'Alice'))]*2


def test_ioi_word_boundary_and_context_rejection(monkeypatch):
    bad=source(); bad['sentence']='prefix Malice'
    monkeypatch.setattr(tasks,'_generate_ioi',lambda *args:[bad,source()])
    assert len(tasks.ioi_rows(Tokenizer(),n=1))==1
    class Bad(Tokenizer):
        def encode(self,text,add_special_tokens=False):
            ids=super().encode(text,add_special_tokens)
            return ids+[9] if text.endswith(' Alice') else ids
    with pytest.raises(ValueError,match='eligible'):
        tasks.ioi_rows(Bad(),n=1)


def test_ioi_preserves_header_and_suffix(monkeypatch):
    row=source(stem='Header Alice and Bob. Bob said to')
    monkeypatch.setattr(tasks,'_generate_ioi',lambda *args:[row])
    assert tasks.ioi_rows(Tokenizer(),n=1)[0]['streams']['clean']['prompt']=='Header Alice and Bob. Bob said to'


def test_mmlu_missing_cache_has_no_fallback(monkeypatch):
    from evaluation.benchmarks import sources
    def missing(*args,**kwargs): raise FileNotFoundError('offline cache missing')
    monkeypatch.setattr(sources,'hf_snapshot',missing)
    with pytest.raises(FileNotFoundError,match='offline cache'):
        tasks.mmlu_rows(Tokenizer(),n=1)


def test_mmlu_deterministic_ids_validation_and_neutral_prompt(monkeypatch):
    items=[dict(source_id='test.parquet:'+str(i),question='Question '+str(i),choices=['x','y','z','w'],answer=i%4,source_hash='abc') for i in range(8)]
    items += [dict(source_id='bad',question='bad',choices=['x'],answer=0,source_hash='abc')]
    monkeypatch.setattr(tasks,'_cached_mmlu',lambda:(items,{'revision':'revision','parquet_hashes':{'test.parquet':'abc'}}))
    a,ma=tasks.mmlu_rows(Tokenizer(),n=3)
    b,mb=tasks.mmlu_rows(Tokenizer(),n=3)
    assert a==b and ma==mb
    assert all(r['source_id'].startswith('test.parquet:') for r in a)
    assert ma['rejected']['malformed']==1
    assert all(r['streams']['clean']['prompt'].endswith('Answer:') for r in a)
    assert all(tasks.NEUTRAL_SYSTEM in r['streams']['clean']['prompt'] for r in a)
    assert tasks.task_batches(a)[0].choice_tokens.shape[1]==4
    assert all(m['supported'] and len(m['recipient_positions'])==1 for m in tasks.mmlu_calibration_maps(a))
    with pytest.raises(ValueError,match='eligible'):
        tasks.mmlu_rows(Tokenizer(),n=1,max_length=2)


def test_duplicate_source_ids_rejected(monkeypatch):
    item=dict(source_id='same',question='Q',choices=['x']*4,answer=0,source_hash='abc')
    monkeypatch.setattr(tasks,'_cached_mmlu',lambda:([item,item],{'revision':'r'}))
    with pytest.raises(ValueError,match='duplicate'):
        tasks.mmlu_rows(Tokenizer(),n=1)


def test_ioi_explicit_name_pool_replays_and_preserves_default(monkeypatch):
    from dataset import ioi_llama
    import inspect
    assert inspect.signature(ioi_llama.generate_ioi_data_llama).parameters['name_pool'].default is None
    names=['Alice','Bob']
    one=ioi_llama.generate_ioi_data_llama(3,Tokenizer(),seed=1,name_pool=names)
    two=ioi_llama.generate_ioi_data_llama(3,Tokenizer(),seed=1,name_pool=names)
    assert one==two
    monkeypatch.setattr(ioi_llama,'load_names',lambda path=None:names)
    assert ioi_llama.generate_ioi_data_llama(3,Tokenizer(),None,1)==one


def test_ioi_item_swap_unsupported_layout_is_visible(monkeypatch):
    item=source(); item['corrupted_sentence']='Short Bob'
    monkeypatch.setattr(tasks,'_generate_ioi',lambda *args:[item])
    rows=tasks.ioi_rows(Tokenizer(),n=1)
    mapping=tasks.ioi_item_swap_maps(rows)[0]
    assert not mapping['supported'] and mapping['recipient_positions']==[]
    assert tasks.task_batches(rows,stream='corrupt')[0].records[0]['utility_assessment'] is False


def test_ioi_separate_donors_and_missing_support(monkeypatch):
    calls=[]
    def generate(tok,count,seed):
        calls.append((count,seed))
        if seed==1: return [source()]
        return [source(stem='Later Bob and Alice met. Bob gave it to')]
    monkeypatch.setattr(tasks,'_generate_ioi',generate)
    rows=tasks.ioi_rows(Tokenizer(),n=1)
    donors,maps=tasks.ioi_task_resample(Tokenizer(),rows)
    assert calls==[(1000,1),(20000,101),(20000,102),(20000,103)]
    assert len(donors)==3 and all(m['supported'] for m in maps)
    assert all(m['donor_id']!=rows[0]['instance_id'] for m in maps)
    monkeypatch.setattr(tasks,'_generate_ioi',lambda *args:[source()])
    donors,maps=tasks.ioi_task_resample(Tokenizer(),rows)
    assert not donors and all(not m['supported'] for m in maps)


def test_ioi_adapter_restores_rng_and_is_deterministic():
    import random
    state=random.getstate()
    assert tasks._generate_ioi(Tokenizer(),3,1)==tasks._generate_ioi(Tokenizer(),3,1)
    assert random.getstate()==state
