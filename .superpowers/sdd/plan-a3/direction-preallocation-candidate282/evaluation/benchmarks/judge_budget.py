"""Opt-in, process-safe paid-attempt ledger for the frozen EVAL 5 pilot.

Root creates the reviewed header; this module never authorizes a run. Unknown
charges (including failed transports) retain their entire reservation. Bounds
use the full supported context, rather than a guessed local token count, and
the full model output ceiling for hidden reasoning. Provider unit-price caps
are also required on every live request. No prompt or credential is logged.
"""
import fcntl
import json
import math
import os
from contextlib import contextmanager


class BudgetExceeded(RuntimeError):
    """Fail closed; callers must never convert this into a judge verdict."""


# Pinned OpenRouter model pages (2026-10-24), USD/million. Reserve full
# context as input AND full output independently, deliberately overbounding.
# Sonnet's context may be 1M; the price cap rejects higher-priced long context.
MODEL_BOUNDS = {
    'anthropic/claude-sonnet-4.5': (3.0, 15.0, 1000000, 64000),
    'anthropic/claude-haiku-4.5': (1.0, 5.0, 200000, 64000),
    'openai/gpt-4o': (2.5, 10.0, 128000, 16384),
    'openai/o3-mini': (1.1, 4.4, 200000, 100000),
}


def request_bound(request):
    if request.provider != 'openrouter' or request.model not in MODEL_BOUNDS:
        raise BudgetExceeded('budget guard only supports the four pinned OpenRouter judges')
    # Restrict to the official benchmark requests: no tools, routing overrides,
    # images, multiple completions, or billable server-side plugins.
    allowed = {'max_tokens', 'max_completion_tokens', 'temperature', 'reasoning_effort'}
    if set(request.kwargs) - allowed or request.schema not in (None, 'numerical_range'):
        raise BudgetExceeded('unsupported guarded judge request parameters/schema')
    for message in request.messages:
        if set(message) != {'role', 'content'} or not isinstance(message['content'], str):
            raise BudgetExceeded('only plain text benchmark judge messages are bounded')
    for name in ('max_tokens', 'max_completion_tokens'):
        value = request.kwargs.get(name)
        if value is not None and (type(value) is not int or value <= 0):
            raise BudgetExceeded('invalid output token limit')
    inp, out, context, ceiling = MODEL_BOUNDS[request.model]
    # Explicit maxima bound nonreasoning models; o3 uses its full output ceiling
    # because max_tokens may exclude billable reasoning on some routes.
    if request.model != 'openai/o3-mini':
        ceiling = min([ceiling] + [request.kwargs[k] for k in
                       ('max_tokens', 'max_completion_tokens') if k in request.kwargs])
    return (inp * context + out * ceiling) / 1000000.0


def routing_body(request):
    inp, out, _, _ = MODEL_BOUNDS[request.model]
    return {'provider': {'require_parameters': True,
                         'max_price': {'prompt': inp, 'completion': out, 'request': 0, 'image': 0}}}


class JudgeBudget:
    def __init__(self, path):
        self.path = os.fspath(path)
        with self._locked() as handle:
            self._state(handle)

    @contextmanager
    def _locked(self):
        # r+ deliberately refuses absent ledgers. The orchestrator must create
        # the reviewed authorization receipt before any client can be used.
        try:
            handle = open(self.path, 'r+')
        except OSError as exc:
            raise BudgetExceeded('reviewed budget ledger is unavailable') from exc
        try:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield handle
        except OSError as exc:
            raise BudgetExceeded('budget ledger persistence failed; stop for reconciliation') from exc
        finally:
            handle.close()

    def _state(self, handle):
        handle.seek(0)
        try:
            rows = [json.loads(line) for line in handle if line.strip()]
            header = rows[0]
            if (header.get('schema') != 1 or header.get('reviewed') is not True
                    or not 0 < header['max_usd'] <= 20
                    or type(header['max_paid_attempts']) is not int
                    or not 0 < header['max_paid_attempts'] <= 5000):
                raise ValueError('invalid header')
            charges = {}
            for row in rows[1:]:
                if row['event'] == 'reserve':
                    if row['attempt'] in charges:
                        raise ValueError('duplicate attempt')
                    charges[row['attempt']] = row['reserved_usd']
                elif row['event'] == 'settle':
                    reserved = charges[row['attempt']]
                    cost = row.get('actual_cost_usd')
                    if cost is not None:
                        if not isinstance(cost, (int,float)) or not math.isfinite(cost) or cost < 0:
                            raise ValueError('invalid actual cost')
                        charges[row['attempt']] = cost
                else:
                    raise ValueError('unknown event')
            if any(not math.isfinite(c) or c < 0 for c in charges.values()):
                raise ValueError('invalid reservation')
            return header, charges
        except (KeyError, ValueError, IndexError, TypeError) as exc:
            raise BudgetExceeded('invalid/torn budget ledger; reconcile before continuing') from exc

    @staticmethod
    def _append(handle, row):
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(row, sort_keys=True, allow_nan=False) + '\n')
        handle.flush()
        os.fsync(handle.fileno())

    def reserve(self, request, key):
        bound = request_bound(request)
        with self._locked() as handle:
            header, charges = self._state(handle)
            if (len(charges) >= header['max_paid_attempts'] or
                    sum(charges.values()) + bound > header['max_usd']):
                raise BudgetExceeded('global paid-attempt or USD cap reached (including pending/unknown charges)')
            attempt = len(charges) + 1
            self._append(handle, dict(event='reserve', attempt=attempt,
                         request_key=key, model=request.model, reserved_usd=bound))
        return attempt

    def settle(self, attempt, usage=None, response_id=None):
        cost = usage.get('cost') if isinstance(usage, dict) else None
        if cost is not None and (type(cost) not in (int,float) or not math.isfinite(cost) or cost < 0):
            cost = None
        with self._locked() as handle:
            _, charges = self._state(handle)
            self._append(handle, dict(event='settle', attempt=attempt,
                         actual_cost_usd=cost, usage=usage, response_id=response_id))
            if cost is not None and cost > charges[attempt]:
                raise BudgetExceeded('provider charge exceeded conservative reservation; stop for reconciliation')

    def stats(self):
        with self._locked() as handle:
            header, charges = self._state(handle)
        return dict(paid_attempts=len(charges), charged_or_reserved_usd=sum(charges.values()),
                    max_usd=header['max_usd'], max_paid_attempts=header['max_paid_attempts'],
                    ledger_path=self.path)
