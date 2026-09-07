"""
judge.py — the one place EVAL 5 talks to a judge API.

Patterned on `dataset/mechanism_purity_check.py:78-104`, which established the
two properties that matter for a paid grading run in this repo:

- **per-item error tolerance.** A refusal, a content filter or a transport
  error costs one example, never the run. An exception here would throw away
  every generation the GPU already produced.
- **incremental persistence.** Verdicts land on disk as they arrive, so a crash
  at example 250 of 300 does not re-buy the first 249.

Two things are new. Concurrency is bounded rather than serial, because EVAL 5
judges roughly `n_items x n_configs` responses per dataset instead of one pass.
And there is a real cache, keyed by a hash of the *entire* request — provider,
model, every message, kwargs and the structured-output schema — because the
developer turn and the response format change the answer as surely as the user
turn does, and a (model, prompt) key would silently serve a binary verdict for
a numerical one.

**Errors are never cached.** A cached 429 would make every re-run instant, free
and permanently `unparsed` — the single most expensive failure mode available
here, since it looks exactly like success.
"""

import asyncio
import hashlib
import json
import os
import sys


BASE_URLS = {"openai": None,                                # library default
             "openrouter": "https://openrouter.ai/api/v1"}

KEY_ENV = {"openai": "OPENAI_API_KEY",
           "openrouter": "OPENROUTER_API_KEY"}


class JudgeResult(object):
    """One judge verdict. `text` is None exactly when `error` is set."""

    __slots__ = ("text", "error", "cached", "model", "provider")

    def __init__(self, text=None, error=None, cached=False,
                 model=None, provider=None):
        self.text = text
        self.error = error
        self.cached = cached
        self.model = model
        self.provider = provider

    @property
    def ok(self):
        return self.error is None

    def to_json(self):
        return {"text": self.text, "error": self.error, "cached": self.cached,
                "model": self.model, "provider": self.provider}

    def __repr__(self):
        if self.error:
            return "JudgeResult(error=%r)" % (self.error,)
        return "JudgeResult(%r%s)" % (
            (self.text or "")[:60], ", cached" if self.cached else "")


def request_key(request):
    """SHA-256 over the whole request, not over (model, prompt).

    `sort_keys` makes the key stable across dict orderings, so a cache written
    by one run is readable by the next.
    """
    blob = json.dumps(request.cache_payload(), sort_keys=True,
                      ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class JudgeCache(object):
    """An append-only JSONL cache of successful verdicts.

    Append-only rather than rewritten, so an interrupted run keeps everything
    it had already paid for. Later lines win on reload, which makes a manual
    correction a matter of appending one line.
    """

    def __init__(self, path):
        self.path = path
        self.entries = {}
        self.hits = 0
        self.writes = 0
        if path and os.path.exists(path):
            with open(path) as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except ValueError:
                        continue            # a torn last line from a kill -9
                    if "key" in row and "text" in row:
                        self.entries[row["key"]] = row["text"]

    def get(self, key):
        text = self.entries.get(key)
        if text is not None:
            self.hits += 1
        return text

    def put(self, key, text):
        # Callers must not reach here with a failure; see JudgeClient._one.
        assert text is not None, "refusing to cache a failed judge call"
        self.entries[key] = text
        self.writes += 1
        if not self.path:
            return
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.path, "a") as handle:
            handle.write(json.dumps({"key": key, "text": text},
                                    ensure_ascii=False) + "\n")
            handle.flush()


class JudgeClient(object):
    """Runs `JudgeRequest`s with bounded concurrency, caching and retries.

    `run()` is synchronous — EVAL 5 is a synchronous evaluation that happens to
    need an async fan-out for one step, and burying `asyncio.run` here keeps
    that from leaking into the evaluation's control flow.
    """

    def __init__(self, cache_path=None, concurrency=8, max_retries=6,
                 initial_delay=2.0, verbose=True, transport=None):
        self.cache = JudgeCache(cache_path)
        self.concurrency = max(1, int(concurrency))
        self.max_retries = max(1, int(max_retries))
        self.initial_delay = initial_delay
        self.verbose = verbose
        # `transport` is the single seam the tests substitute: an async
        # callable (request) -> text that stands in for the whole OpenAI
        # client. Everything above it — cache keys, retries, error tolerance,
        # ordering — is then exercised for real rather than mocked around.
        self._transport = transport
        self._clients = {}

    # ---- provider plumbing ----------------------------------------------
    def _client(self, provider):
        if provider in self._clients:
            return self._clients[provider]
        from openai import AsyncOpenAI                     # lazy: import only
        key = os.environ.get(KEY_ENV[provider])            # when a call is made
        if not key:
            raise RuntimeError(
                "%s is not set; it is required to judge with provider %r"
                % (KEY_ENV[provider], provider))
        kwargs = {"api_key": key}
        if BASE_URLS[provider]:
            kwargs["base_url"] = BASE_URLS[provider]
        client = AsyncOpenAI(**kwargs)
        self._clients[provider] = client
        return client

    async def _call(self, request):
        """One API call. Returns the verdict text; raises on failure."""
        if self._transport is not None:
            return await self._transport(request)
        client = self._client(request.provider)
        kwargs = dict(request.kwargs)
        if request.schema is not None:
            return await _structured_call(client, request, kwargs)
        completion = await client.chat.completions.create(
            model=request.model, messages=request.messages, **kwargs)
        text = completion.choices[0].message.content
        return (text or "").strip()

    async def _one(self, request, semaphore):
        key = request_key(request)
        cached = self.cache.get(key)
        if cached is not None:
            return JudgeResult(text=cached, cached=True,
                               model=request.model, provider=request.provider)
        delay = self.initial_delay
        last = None
        for attempt in range(self.max_retries):
            try:
                async with semaphore:
                    text = await self._call(request)
                if not text:
                    # An empty completion is a failure, not a verdict: parsed
                    # as text it would fall through to `unparsed` and look like
                    # a model-behaviour result instead of an API one.
                    raise RuntimeError("empty judge completion")
                self.cache.put(key, text)
                return JudgeResult(text=text, model=request.model,
                                   provider=request.provider)
            except Exception as exc:                # noqa: BLE001 — reported
                last = "%s: %s" % (type(exc).__name__, exc)
                if attempt == self.max_retries - 1:
                    break
                await asyncio.sleep(delay)
                delay *= 2
        if self.verbose:
            sys.stderr.write("  judge call failed after %d attempts: %s\n"
                             % (self.max_retries, last))
        # Not cached. A cached failure would be served instantly on every
        # re-run and would never be retried.
        return JudgeResult(error=last, model=request.model,
                           provider=request.provider)

    async def _run(self, requests):
        semaphore = asyncio.Semaphore(self.concurrency)
        # gather preserves input order, which is what lets the caller zip the
        # results straight back onto its items.
        return await asyncio.gather(*[self._one(r, semaphore)
                                      for r in requests])

    def run(self, requests):
        """-> list[JudgeResult], one per request, in input order.

        A None in `requests` (an item whose grader is local, or one already
        resolved) passes through as a None so the caller's zip stays aligned.
        """
        requests = list(requests)
        live = [(i, r) for i, r in enumerate(requests) if r is not None]
        if not live:
            return [None] * len(requests)
        results = _run_sync(self._run([r for _, r in live]))
        out = [None] * len(requests)
        for (index, _), result in zip(live, results):
            out[index] = result
        return out

    def stats(self):
        return {"cache_hits": self.cache.hits, "cache_writes": self.cache.writes,
                "cache_path": self.cache.path, "concurrency": self.concurrency}


def _run_sync(coro):
    """asyncio.run, but survives being called from a notebook or any other
    context that already owns a running loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import threading
    box = {}

    def target():
        box["value"] = asyncio.run(coro)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join()
    return box["value"]


# ---- structured output ---------------------------------------------------
#
# MASK's numerical archetype asks o3-mini for a {lower_bound, upper_bound} pair
# through `client.beta.chat.completions.parse` (mask/mask/evaluate.py:36-56).
# That method only exists in openai >= 1.40; the environments this repo runs in
# are older or do not have the library at all, so the call degrades to a plain
# completion that asks for the same JSON in words. Which path ran is recorded,
# because "we approximated the official judge" is a caveat a reader of the
# numbers is entitled to.

STRUCTURED_FALLBACK_INSTRUCTION = (
    'Respond with a JSON object and nothing else, with exactly the keys '
    '"lower_bound" and "upper_bound", each a number or null.')


def supports_structured_parse(client):
    beta = getattr(client, "beta", None)
    chat = getattr(beta, "chat", None) if beta is not None else None
    completions = getattr(chat, "completions", None) if chat is not None else None
    return completions is not None and hasattr(completions, "parse")


async def _structured_call(client, request, kwargs):
    if request.schema != "numerical_range":
        raise ValueError("unknown judge schema %r" % (request.schema,))
    if supports_structured_parse(client):
        from pydantic import BaseModel
        from typing import Optional

        class NumericalRange(BaseModel):
            lower_bound: Optional[float]
            upper_bound: Optional[float]

        completion = await client.beta.chat.completions.parse(
            model=request.model, messages=request.messages,
            response_format=NumericalRange, **kwargs)
        parsed = completion.choices[0].message.parsed
        return json.dumps({"lower_bound": parsed.lower_bound,
                           "upper_bound": parsed.upper_bound})
    messages = list(request.messages)
    messages.append({"role": "user",
                     "content": STRUCTURED_FALLBACK_INSTRUCTION})
    plain = dict(kwargs)
    plain.pop("reasoning_effort", None)      # rejected by non-reasoning models
    completion = await client.chat.completions.create(
        model=request.model, messages=messages, **plain)
    return (completion.choices[0].message.content or "").strip()
