import asyncio
import json
import pytest
from evaluation.benchmarks.base import JudgeRequest
from evaluation.benchmarks.judge import JudgeClient


def ledger(tmp_path, dollars=20, attempts=5000):
    path = tmp_path / 'budget.jsonl'
    path.write_text(json.dumps(dict(schema=1, reviewed=True, max_usd=dollars,
                                    max_paid_attempts=attempts)) + '\n')
    return str(path)


def req(model='anthropic/claude-haiku-4.5', **kwargs):
    return JudgeRequest('openrouter', model, [{'role':'user','content':'grade'}], kwargs)


def test_cap_blocks_transport_and_counts_unknown_retry(tmp_path):
    from evaluation.benchmarks.judge_budget import JudgeBudget, BudgetExceeded
    budget = JudgeBudget(ledger(tmp_path, attempts=1))
    calls = []
    async def transport(request):
        calls.append(request)
        raise ConnectionError('retry')
    client = JudgeClient(transport=transport, budget=budget, initial_delay=0)
    with pytest.raises(BudgetExceeded):
        client.run([req()])
    assert len(calls) == 1
    assert budget.stats()['paid_attempts'] == 1
    assert budget.stats()['charged_or_reserved_usd'] > 0


def test_cached_hit_is_free_even_at_cap(tmp_path):
    from evaluation.benchmarks.judge_budget import JudgeBudget
    calls=[]
    async def transport(request):
        calls.append(request)
        return 'yes'
    budget=JudgeBudget(ledger(tmp_path, attempts=1))
    client=JudgeClient(transport=transport,budget=budget)
    assert client.run([req()])[0].text == 'yes'
    assert client.run([req()])[0].cached
    assert len(calls)==1


def test_pending_concurrency_never_overruns_attempt_cap(tmp_path):
    from evaluation.benchmarks.judge_budget import JudgeBudget, BudgetExceeded
    calls=[]
    async def transport(request):
        calls.append(request)
        await asyncio.sleep(.01)
        return 'yes'
    budget=JudgeBudget(ledger(tmp_path, attempts=2))
    client=JudgeClient(transport=transport,budget=budget,concurrency=8)
    with pytest.raises(BudgetExceeded):
        client.run([req(max_tokens=i+1) for i in range(8)])
    assert len(calls)==2
    assert budget.stats()['paid_attempts']==2


def test_completion_metadata_and_actual_cost_persist(tmp_path):
    from evaluation.benchmarks.judge_budget import JudgeBudget
    from evaluation.benchmarks.judge import JudgeCompletion
    async def transport(request):
        return JudgeCompletion('yes', usage={'cost':.0001,'prompt_tokens':10,
                                            'completion_tokens':1}, response_id='gen-123')
    path=ledger(tmp_path)
    budget=JudgeBudget(path)
    result=JudgeClient(transport=transport,budget=budget).run([req()])[0]
    assert result.to_json()['response_id']=='gen-123'
    assert budget.stats()['charged_or_reserved_usd']==pytest.approx(.0001)
    assert 'gen-123' in open(path).read()
    assert 'prompt_tokens' in open(path).read()


def test_unknown_and_unsupported_requests_fail_without_transport(tmp_path):
    from evaluation.benchmarks.judge_budget import JudgeBudget, BudgetExceeded
    async def transport(request):
        pytest.fail('transport forbidden')
    client=JudgeClient(transport=transport,budget=JudgeBudget(ledger(tmp_path)))
    for request in [req('unknown'),req(n=2),req(extra_body={'models':['other']})]:
        with pytest.raises(BudgetExceeded):
            client.run([request])


def test_dollar_cap_and_unreviewed_ledger(tmp_path):
    from evaluation.benchmarks.judge_budget import JudgeBudget, BudgetExceeded
    async def transport(request):
        pytest.fail('transport forbidden')
    client=JudgeClient(transport=transport,budget=JudgeBudget(ledger(tmp_path,dollars=.0001)))
    with pytest.raises(BudgetExceeded):
        client.run([req()])
    path=tmp_path/'bad.jsonl'
    path.write_text('{}\n')
    with pytest.raises(BudgetExceeded):
        JudgeBudget(str(path))


def test_identical_pending_requests_share_one_paid_verdict(tmp_path):
    from evaluation.benchmarks.judge_budget import JudgeBudget
    calls=[]
    async def transport(request):
        calls.append(request)
        await asyncio.sleep(.01)
        return 'yes'
    budget=JudgeBudget(ledger(tmp_path))
    results=JudgeClient(transport=transport,budget=budget).run([req(),req(),req()])
    assert [r.text for r in results]==['yes']*3
    assert len(calls)==1
    assert budget.stats()['paid_attempts']==1


def test_failed_attempt_and_retry_success_both_charged(tmp_path):
    from evaluation.benchmarks.judge_budget import JudgeBudget, request_bound
    from evaluation.benchmarks.judge import JudgeCompletion
    calls=[]
    async def transport(request):
        calls.append(request)
        if len(calls)==1:
            raise ConnectionError('uncertain charge')
        return JudgeCompletion('yes',usage={'cost':.001},response_id='retry-ok')
    budget=JudgeBudget(ledger(tmp_path))
    client=JudgeClient(transport=transport,budget=budget,initial_delay=0)
    assert client.run([req()])[0].text=='yes'
    assert budget.stats()['paid_attempts']==2
    assert budget.stats()['charged_or_reserved_usd']==pytest.approx(request_bound(req())+.001)


def test_sdk_retries_disabled_and_provider_caps_sent(monkeypatch,tmp_path):
    import sys
    from types import SimpleNamespace
    from evaluation.benchmarks.judge_budget import JudgeBudget
    calls=[]
    created=[]
    class Completions:
        async def create(self,**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(id='gen-live',usage=SimpleNamespace(model_dump=lambda **k:{'cost':.001}),
                    choices=[SimpleNamespace(message=SimpleNamespace(content='yes'))])
    class FakeClient:
        def __init__(self,**kwargs):
            created.append(kwargs)
            self.chat=SimpleNamespace(completions=Completions())
        async def close(self):
            pass
    monkeypatch.setitem(sys.modules,'openai',SimpleNamespace(AsyncOpenAI=FakeClient))
    monkeypatch.setenv('OPENROUTER_API_KEY','test-placeholder')
    result=JudgeClient(budget=JudgeBudget(ledger(tmp_path))).run([req(max_tokens=100)])[0]
    assert result.response_id=='gen-live'
    assert created[0]['max_retries']==0
    provider=calls[0]['extra_body']['provider']
    assert provider['require_parameters'] is True
    assert provider['max_price']=={'prompt':1,'completion':5,'request':0,'image':0}


def test_separate_clients_share_atomic_attempt_cap(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from evaluation.benchmarks.judge_budget import JudgeBudget, BudgetExceeded
    path=ledger(tmp_path,attempts=3)
    def reserve(i):
        try:
            return JudgeBudget(path).reserve(req(),str(i))
        except BudgetExceeded:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        reservations=list(pool.map(reserve,range(20)))
    assert len([r for r in reservations if r is not None])==3
    assert JudgeBudget(path).stats()['paid_attempts']==3


def test_reasoning_reservation_uses_full_billable_model_ceiling():
    from evaluation.benchmarks.judge_budget import request_bound
    assert request_bound(req('openai/o3-mini',max_tokens=1))==pytest.approx(.66)


def test_settlement_disk_failure_stops_without_rebuying(tmp_path,monkeypatch):
    from evaluation.benchmarks.judge_budget import JudgeBudget, BudgetExceeded
    budget=JudgeBudget(ledger(tmp_path))
    append=budget._append
    def write(handle,row):
        if row['event']=='settle':
            raise OSError('disk full')
        append(handle,row)
    monkeypatch.setattr(budget,'_append',write)
    calls=[]
    async def transport(request):
        calls.append(request)
        return 'yes'
    with pytest.raises(BudgetExceeded,match='persistence failed'):
        JudgeClient(budget=budget,transport=transport,initial_delay=0).run([req()])
    assert len(calls)==1
    assert budget.stats()['paid_attempts']==1


def test_guarded_schema_never_uses_prompt_appending_fallback(monkeypatch,tmp_path):
    from types import SimpleNamespace
    from evaluation.benchmarks.judge_budget import JudgeBudget, BudgetExceeded
    client=JudgeClient(budget=JudgeBudget(ledger(tmp_path)))
    class Completions:
        async def create(self,**kwargs):
            pytest.fail('unsupported schema must never reach transport')
    monkeypatch.setattr(client,'_client',lambda provider:SimpleNamespace(chat=SimpleNamespace(completions=Completions())))
    request=req('openai/o3-mini',reasoning_effort='low')
    request.schema='numerical_range'
    with pytest.raises(BudgetExceeded,match='structured'):
        client.run([request])


def test_study_cache_binding_allows_only_verified_import_prefix_and_appends(tmp_path):
    import hashlib
    from evaluation.benchmarks.judge import validate_study_cache
    from evaluation.benchmarks.judge_budget import BudgetExceeded
    from evaluation.frozen_head_masks import digest
    cache=tmp_path/'cache.jsonl'
    initial=json.dumps({'key':'a'*64,'text':'old'})+'\n'
    cache.write_text(initial)
    source=tmp_path/'historical.jsonl'
    source.write_text(initial)
    manifest={'judge_cache_import':{'output':{'path':str(cache),'sha256':hashlib.sha256(initial.encode()).hexdigest()},
                'imported_bytes':len(initial.encode()),'sources':[{'source':{'path':str(source)}}]}}
    manifest['content_sha256']=digest(manifest)
    cohort=tmp_path/'cohort.json'
    cohort.write_text(json.dumps(manifest))
    validate_study_cache(str(cohort),str(cache))
    with cache.open('a') as h:
        h.write(json.dumps({'key':'b'*64,'text':'new'})+'\n')
    validate_study_cache(str(cohort),str(cache))
    with pytest.raises(BudgetExceeded):
        validate_study_cache(str(cohort),str(source))
    cache.write_text(initial.replace('old','bad'))
    with pytest.raises(BudgetExceeded):
        validate_study_cache(str(cohort),str(cache))


def test_structured_refusal_keeps_available_billing_metadata(monkeypatch,tmp_path):
    from types import SimpleNamespace
    from evaluation.benchmarks.judge_budget import JudgeBudget
    budget=JudgeBudget(ledger(tmp_path))
    class Parse:
        async def parse(self,**kwargs):
            return SimpleNamespace(id='refused-123',usage={'cost':.001},
                choices=[SimpleNamespace(message=SimpleNamespace(parsed=None))])
    sdk=SimpleNamespace(beta=SimpleNamespace(chat=SimpleNamespace(completions=Parse())))
    client=JudgeClient(budget=budget)
    monkeypatch.setattr(client,'_client',lambda provider:sdk)
    request=req('openai/o3-mini',reasoning_effort='low')
    request.schema='numerical_range'
    assert not client.run([request])[0].ok
    assert budget.stats()['charged_or_reserved_usd']==pytest.approx(.001)
    assert 'refused-123' in open(budget.path).read()
