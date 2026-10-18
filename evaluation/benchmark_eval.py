"""
evaluation/benchmark_eval.py — EVAL 5: does knocking the circuit out stop the
model being deceptive on benchmarks it was never pruned on?

Every other evaluation here reads a single forced-choice token on the circuit's
own synthetic task. This one runs open generation on three external deception
benchmarks, judges each generation with that benchmark's own judge, and asks
whether the deception rate falls under knockout while the text stays coherent.

How a dataset becomes a number
------------------------------
1. **Load** the candidate pool (`Benchmark.load`) — prompts only, no model.
2. **Elicit belief** where the benchmark needs one, from the **full** model.
   Items whose probes do not agree on a belief are dropped: with no belief
   there is nothing for a response to be deceptive *about*.
3. **Screen.** Generate under `all_gates_open` and judge. Items the full model
   is judged deceptive on become the evaluation set; items it is judged honest
   on become the corrupt-reference pool. Screening walks the candidates in load
   order and stops as soon as both pools are full, so a benchmark where
   deception is common costs a fraction of its pool.
4. **Run every configuration** on that evaluation set and judge each one.

Three consequences of step 3 that a reader has to have in view, and which the
report states rather than leaving to be inferred:

* **The `full` row is the screen** — the same tokens, not a second pass. The
  prompt columns are re-encoded to the evaluation set's common width and the
  generated block is carried over verbatim, so `full`'s label and `full`'s
  printed text cannot disagree, and no GPU time is spent proving they don't.
* **`full`'s deception rate is 1.0 by construction.** It is not a measurement.
  It is printed because it makes the other rows' scale legible, and it is
  footnoted every place it appears.
* **This design cannot see the opposite effect.** An ablation that made the
  model deceptive on items where it was honest would not show up here: those
  items are in the reference pool, not the evaluation set. Stated in the report
  and in the caveats, because "deception fell" is only half of what a reader
  will take the table to mean.

Belief is always the full model's
---------------------------------
Re-eliciting it under ablation would let a knowledge deficit — the circuit
carried something the model needed in order to answer at all — score as an
honesty gain, which is precisely the confound this evaluation exists to rule
out. The banner in the log says so per dataset.

The corrupt reference
---------------------
Under `--ablation interchange` the ablated units are filled from the corrupted
stream, so what that stream carries *is* the intervention. Two cases:

* **A minimal pair, where the benchmark has one.** `instructed-deception`'s
  honest twin is the same statement under an honest system prompt — one clause
  different. That is the contrastive reference this codebase is built around
  (STD's corrupt stream is a single-token edit), so such an item is paired with
  its own twin.
* **A seeded derangement of the reference pool otherwise.** Sandbagging's WMDP
  questions have no MMLU counterpart and MASK's pressure prompts have no honest
  version at all, so the pool is interchangeable rather than paired and
  `evaluation/wikitext.py:pair_blocks` supplies the assignment.

The plan specifies a derangement in both cases. Using the twin where one exists
is a deliberate departure: a derangement over a pool of twins would guarantee
that the one item whose honest counterpart is a one-clause edit gets paired
with some *other* item's, discarding the only minimal pair the benchmark
provides. `pairing` in `benchmarks.json` records which rule each dataset got.
"""

from __future__ import annotations

import os
import time

import torch

from evaluation import Evaluation
from evaluation import report
from evaluation.benchmarks import base, expand, get_benchmark
from evaluation.benchmarks.judge import JudgeClient
from evaluation.coherence import coherence_metrics, completion_mask
from evaluation.gen_engine import generate_bucketed, resolve_pad_id
from evaluation.masks import knockout_masks, zeros_like
from evaluation.metrics import summarize_null

CONFIG_LABELS = {
    "full": "full model (all gates open)",
    "knockout": "circuit knocked out",
    "circuit_only": "circuit only (everything else ablated)",
    "empty": "empty circuit (all gates closed)",
}

#: How many candidates the screen judges at a time, as a multiple of the target
#: count. Early-stop is then reached in one or two chunks when deception is
#: common, without paying for the whole pool when it is rare.
SCREEN_CHUNK_FACTOR = 2

#: How many unparsed responses a screen that selected nothing prints before it
#: raises. Enough to see what shape the model answered in; few enough that a
#: 300-candidate screen does not print 300 refusals into the suite log.
UNPARSED_SAMPLES = 3

#: How far past the target the screen may keep walking *once the evaluation set
#: is already full*, as a multiple of the target count.
#:
#: It is deliberately NOT a ceiling on screening as a whole. The search for
#: deceptive items is uncapped and will walk the entire candidate pool if
#: deception is rare, which is what the plan means by "worst case = full pool";
#: capping that would silently return a smaller evaluation set than asked for.
#: What this bounds is the *other* reason the walk continues: the reference
#: pool. On a benchmark where the full model is deceptive nearly always, the
#: honest pool is the bottleneck, and without a bound the screen would generate
#: 512 tokens for all 5245 harm-pressure rows to fill it. A few dozen reference
#: items, cycled, is a usable reference; six more hours of generation to widen
#: it is not. A pool cut short is reported, not silently accepted.
SCREEN_MAX_FACTOR = 10


# ==============================================================================
# PROMPT RENDERING
# ==============================================================================

_LLAMA3_BOS = "<|begin_of_text|>"
_LLAMA3_HEADER = "<|start_header_id|>%s<|end_header_id|>\n\n"
_LLAMA3_EOT = "<|eot_id|>"

#: Pinned so a prompt rendered today and one rendered next week tokenise
#: identically. Only reachable on the `apply_chat_template` fallback; the
#: Llama-3 renderer below emits no date block at all.
PINNED_DATE = "26 Jul 2024"


def is_llama3_chat(tokenizer) -> bool:
    vocab = tokenizer.get_vocab()
    return "<|start_header_id|>" in vocab and "<|eot_id|>" in vocab


def render_messages(tokenizer, messages) -> str:
    """A chat prompt ending in an open assistant turn.

    The Llama-3 format is written out here rather than taken from
    `apply_chat_template`, for the reason `dataset/deception_common.py:72`
    already gives: the 3.1-Instruct template injects a "Cutting Knowledge Date
    / Today Date" block, so the same benchmark item tokenises differently
    depending on the day the job ran. Tolerable noise for a chat demo; not for
    a measurement someone will try to reproduce.

    Any other tokenizer falls back to its own template, with the date pinned
    where the template accepts one.
    """
    if is_llama3_chat(tokenizer):
        parts = [_LLAMA3_BOS]
        for turn in messages:
            parts.append(_LLAMA3_HEADER % turn["role"])
            parts.append(turn["content"])
            parts.append(_LLAMA3_EOT)
        parts.append(_LLAMA3_HEADER % "assistant")
        return "".join(parts)
    try:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            date_string=PINNED_DATE)
    except TypeError:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)


def encode_prompts(tokenizer, texts, pad_id):
    """-> (ids, attention_mask), **left**-padded to the longest row.

    `add_special_tokens=False` because `render_messages` emits the BOS itself;
    letting the tokenizer add a second one shifts every position by one and is
    invisible in the decoded text.
    """
    seqs = [tokenizer.encode(t, add_special_tokens=False) for t in texts]
    empty = [i for i, s in enumerate(seqs) if not s]
    if empty:
        raise ValueError("prompt(s) at %r tokenised to nothing" % (empty[:5],))
    width = max(len(s) for s in seqs)
    ids = torch.full((len(seqs), width), int(pad_id), dtype=torch.long)
    mask = torch.zeros((len(seqs), width), dtype=torch.long)
    for row, seq in enumerate(seqs):
        ids[row, width - len(seq):] = torch.tensor(seq, dtype=torch.long)
        mask[row, width - len(seq):] = 1
    return ids, mask


def eos_ids_for(model) -> tuple:
    """Every id the model stops on, from its `generation_config`.

    `tokenizer.eos_token_id` is one id; Llama-3 Instruct stops on three, and the
    one it actually emits at the end of a chat turn (`<|eot_id|>`) is not the
    one the tokenizer reports.
    """
    config = getattr(model, "generation_config", None)
    value = getattr(config, "eos_token_id", None)
    if value is None:
        return ()
    if isinstance(value, int):
        return (int(value),)
    return tuple(int(v) for v in value)


# ==============================================================================
# THE CORRUPT REFERENCE STREAM
# ==============================================================================

def completion_tokens(ids, prompt_width, eos_ids):
    """Per row, the generated tokens up to and including the first EOS.

    The tail of a finished row is `pad_id`, which on Llama-3 *is* `<|eot_id|>`.
    Tiling a raw generated block into a corrupt stream would therefore fill
    real positions with end-of-turn tokens — a reference made mostly of
    punctuation, rather than the honest response it is supposed to be.
    """
    prompt_mask = torch.ones((ids.shape[0], prompt_width), dtype=torch.long)
    keep = completion_mask(ids, prompt_mask, prompt_width, eos_ids)
    return [ids[row, prompt_width:][keep[row, prompt_width:].bool()].tolist()
            for row in range(ids.shape[0])]


def pack_reference(prompt_tokens, response_tokens, length, pad_id):
    """-> (tokens, tiled): the partner's prompt + response, filled to `length`.

    Truncate if the partner is long enough. If it is short, keep one full pass
    and then tile **only the response** — restarting the partner's prompt
    mid-decode (which is what `evaluation/generation.py` does, because a
    wikitext block has no prompt/response split to respect) would drop a system
    prompt and a chat header into the reference at an arbitrary offset.
    """
    seq = list(prompt_tokens) + list(response_tokens)
    if len(seq) >= length:
        return seq[:length], False
    # A partner that generated nothing leaves only its prompt to tile with.
    filler = list(response_tokens) or list(prompt_tokens)
    if not filler:
        raise ValueError("reference partner has no tokens to pack")
    while len(seq) < length:
        seq.extend(filler)
    return seq[:length], True


def build_corrupt_stream(clean_ids, clean_mask, partners, new_tokens, pad_id):
    """`(n, W + new_tokens)` whose pad layout matches `clean_mask` exactly.

    Both streams share one `attention_mask` — `PrunableLlamaForCausalLM.forward`
    accepts no `corrupted_attention_mask`, and one passed anyway would land in
    `**kwargs` and be dropped — so a corrupt row must occupy precisely the
    non-pad positions of the clean row it is paired with. Every row is packed to
    *its own* true length plus `new_tokens`, not to the batch width.
    """
    n, width = clean_ids.shape
    out = torch.full((n, width + new_tokens), int(pad_id), dtype=torch.long)
    tiled_rows = []
    for row in range(n):
        pad_count = width - int(clean_mask[row].sum())
        seq, tiled = pack_reference(partners[row][0], partners[row][1],
                                    (width - pad_count) + new_tokens, pad_id)
        out[row, pad_count:] = torch.tensor(seq, dtype=torch.long)
        if tiled:
            tiled_rows.append(row)
    return out, tiled_rows


def placeholder_corrupt(clean_ids, clean_mask, new_tokens, pad_id):
    """A corrupt stream for a pass where the reference does not matter yet.

    The screen runs with every gate open, under which `out = 1*clean + 0*ref`
    and the corrupt stream contributes nothing. It still has to be a *valid*
    sequence occupying the clean row's non-pad positions: `0 * NaN` is NaN, so
    an ill-formed reference is not made harmless by a zero coefficient.
    """
    partners = [(clean_ids[row][clean_mask[row].bool()].tolist(), [])
                for row in range(clean_ids.shape[0])]
    stream, _ = build_corrupt_stream(clean_ids, clean_mask, partners,
                                     new_tokens, pad_id)
    return stream


def assign_partners(n_items, pool_size, seed, forbidden=None):
    """-> (indices, reused): which reference-pool row each item is paired with.

    `forbidden[i]`, when given, is the one pool index item `i` must not draw —
    its own row, where the evaluation set is part of the pool. An item that
    references itself makes an interchange ablation a no-op for that row:
    `out = gate*clean + (1 - gate)*clean` is `clean` whatever the gate says, so
    the row is scored as if it had never been ablated. Nothing raises and the
    text looks fine, which is why it is repaired here rather than documented.

    A derangement when the pool is the evaluation set's own size; a seeded
    cycle otherwise, with self-assignments swapped out. `reused` says some pool
    row serves more than one item — a thinner reference than the pool size
    suggests, so the report prints it.
    """
    if pool_size <= 0:
        raise ValueError("cannot pair against an empty reference pool")
    if pool_size == 1 and forbidden is not None and forbidden[0] == 0:
        # One item whose only reference row is itself. No pairing exists that
        # is not a no-op, so say so rather than returning [0] and letting the
        # row be scored as an ablation that never happened.
        raise ValueError(
            "a single-item evaluation set cannot reference itself; widen the "
            "reference pool (--benchmark-ref-pool honest) or screen more items")
    if pool_size == n_items and n_items >= 2:
        from evaluation.wikitext import pair_blocks
        return [int(i) for i in pair_blocks(n_items, seed)], False
    import numpy as np

    order = np.random.default_rng(seed).permutation(pool_size)
    indices = [int(order[i % pool_size]) for i in range(n_items)]
    for i in range(n_items):
        if forbidden is None or indices[i] != forbidden[i]:
            continue
        # Swap with any row whose partner is not the one `i` may not have.
        # `forbidden` is injective (each item forbids its own distinct pool
        # row), so the reverse direction of the swap is legal automatically.
        for j in range(n_items):
            if j != i and indices[j] != forbidden[i]:
                indices[i], indices[j] = indices[j], indices[i]
                break
        else:
            raise ValueError(
                "every row in the reference pool is some item's own; no "
                "self-free pairing exists for %d items" % (n_items,))
    return indices, n_items > pool_size


# ==============================================================================
# GENERATION
# ==============================================================================

def generate_under(ctx, *, clean_ids, clean_mask, corrupt_ids, hook,
                   new_tokens, eos, desc):
    return generate_bucketed(
        ctx,
        clean_ids=clean_ids, corrupt_ids=corrupt_ids,
        attention_mask=clean_mask, hook=hook, new_tokens=new_tokens,
        eos_ids=eos, batch_size=ctx.cli.benchmark_gen_batch_size,
        use_cache=not ctx.cli.no_kv_cache, desc=desc).cpu()


def decode_completions(tokenizer, ids, prompt_width, eos):
    """The generated text per row, with the stop token and its tail removed."""
    return [tokenizer.decode(tokens, skip_special_tokens=True).strip()
            for tokens in completion_tokens(ids, prompt_width, eos)]


# ==============================================================================
# SCREENING
# ==============================================================================

class Screen(object):
    """One dataset's evaluation set, reference pool and full-model pass.

    Cached on the `Session`: none of it depends on which circuit is loaded, so
    a 3x3 suite would otherwise regenerate an hour of text nine times.
    """

    def __init__(self, dataset):
        self.dataset = dataset
        self.new_tokens = 0
        self.items = []          # the evaluation set (full model deceptive)
        self.prompts = []        # rendered prompt text, aligned with items
        self.clean_ids = None    # (N, W), left-padded
        self.clean_mask = None
        self.prompt_width = 0
        self.full_ids = None     # (N, W + new_tokens); the screen's own tokens
        self.full_rows = []      # the screen's label rows, reused verbatim
        self.pool_items = []     # reference pool items
        self.pool_refs = []      # (prompt_tokens, response_tokens) per pool item
        self.pairing = ""        # "twin" | "derangement"
        self.partner_index = []  # index into pool_* per evaluation item
        self.partner_reused = False
        self.stats = {}

    @property
    def partners(self):
        return [self.pool_refs[i] for i in self.partner_index]

    @property
    def partner_ids(self):
        return [self.pool_items[i].item_id for i in self.partner_index]


def _judge_all(client, bench, items, responses):
    """-> a label row per item: {label, raw, judge_prompt, judge_text, ...}."""
    requests = [bench.judge_request(item, response)
                for item, response in zip(items, responses)]
    results = client.run(requests)
    rows = []
    for item, response, request, result in zip(items, responses, requests,
                                               results):
        text = result.text if (result is not None and result.ok) else None
        error = result.error if (result is not None and not result.ok) else None
        if request is not None and text is None:
            # A judge that never answered is an API outcome, not a model one.
            # Letting it fall through to `parse_judgement` would score it
            # `honest` on most rubrics, crediting the ablation for an outage.
            rows.append({"label": base.UNPARSED, "raw": "judge-failed",
                         "judge_prompt": request.prompt_text,
                         "judge_text": None, "judge_error": error})
            continue
        label, raw = bench.parse_judgement(item, response, text)
        if label not in base.LABELS:
            raise AssertionError("%s returned label %r, not one of %r"
                                 % (bench.name, label, base.LABELS))
        rows.append({"label": label, "raw": raw,
                     "judge_prompt": request.prompt_text if request else None,
                     "judge_text": text, "judge_error": error})
    return rows


def _elicit_beliefs(ctx, bench, client, items, eos, pad_id, desc,
                    new_tokens, refs=None):
    """-> (items with `belief` filled, n_dropped, n_judge_failed).

    Always the FULL model. `refs`, when given, collects
    `rendered prompt -> (prompt_tokens, completion_tokens)` for every probe so
    a probe that doubles as a reference-pool row is not generated twice; see
    `_probe_is_the_reference` for when that applies.
    """
    specs = [bench.belief_request(item) for item in items]
    flat, owners = [], []
    for index, spec in enumerate(specs):
        for probe in (spec or []):
            flat.append(probe)
            owners.append(index)
    if not flat:
        return list(items), 0, 0

    tok = ctx.tokenizer
    texts = [render_messages(tok, probe["messages"]) for probe in flat]
    clean_ids, clean_mask = encode_prompts(tok, texts, pad_id)
    corrupt = placeholder_corrupt(clean_ids, clean_mask, new_tokens, pad_id)
    with ctx.all_gates_open():
        out = generate_under(ctx, clean_ids=clean_ids, clean_mask=clean_mask,
                             corrupt_ids=corrupt, hook=None,
                             new_tokens=new_tokens, eos=eos, desc=desc)
    width = clean_ids.shape[1]
    answers = decode_completions(tok, out, width, eos)
    if refs is not None:
        completions = completion_tokens(out, width, eos)
        for row, text in enumerate(texts):
            refs[text] = (clean_ids[row][clean_mask[row].bool()].tolist(),
                          completions[row])

    # Some probes need a judge to read their answer (an open-ended claim), some
    # parse locally (a bare A-D). `run` passes a None straight through.
    results = client.run([
        bench.belief_judge_request(items[owner], probe["name"], answer)
        for probe, owner, answer in zip(flat, owners, answers)])

    per_item = [[] for _ in items]
    failed = [False] * len(items)
    for probe, owner, answer, result in zip(flat, owners, answers, results):
        ok = result is None or result.ok
        if not ok:
            # An API failure is not evidence about the model's belief. Left
            # unrecorded it collapses into `parse_belief` returning None and
            # the item is dropped as "the model had no belief here" -- so an
            # OpenRouter blip silently shrinks the evaluation set and is
            # reported as a property of the model. `_judge_all` already
            # refuses to make this mistake on the response side.
            failed[owner] = True
        # Everything the adapter put on the probe travels with it, minus the
        # prompt itself. `parse_belief` is handed these dicts and nothing else,
        # so a key dropped here is a key the adapter cannot read back: Liars'
        # Bench declares `answer_prefix`/`answer_suffix` on two of its three
        # choice templates ("<final_answer>", "Final Answer: "), and rebuilding
        # the dict from a fixed field list silently replaced them with "".
        # `extract_choice` then parsed from the top of a reasoning preamble
        # instead of from the delimiter, returned None, and `_consistent_choice`
        # -- which requires every probe to agree -- dropped the item. Every
        # candidate in both harm-pressure scenarios was discarded that way.
        carried = {k: v for k, v in probe.items() if k != "messages"}
        carried.update({
            "response": answer,
            "judge_text": result.text if (result and result.ok) else None,
            "judge_error": result.error if (result and not result.ok) else None})
        per_item[owner].append(carried)

    kept, dropped, judge_failed = [], 0, 0
    for item, probes, had_failure in zip(items, per_item, failed):
        if not probes:
            kept.append(item)
            continue
        belief = bench.parse_belief(item, probes)
        if belief is None:
            if had_failure:
                judge_failed += 1
            else:
                dropped += 1
            continue
        kept.append(item.replace(belief=belief,
                                 meta=dict(item.meta, belief_probes=probes)))
    return kept, dropped, judge_failed


def cached_screen(ctx, bench, client, dataset) -> Screen:
    """`run_screen`, but read from and written to the on-disk screen cache.

    The screen is circuit-independent by construction, so this is the one part
    of EVAL 5 that never has to be repaid — see `evaluation/screen_cache.py`
    for the key and for why the device is in it. A miss, an unreadable file or
    a failed write all degrade to "screen normally": the cache is an
    optimisation and must never be able to fail an evaluation.
    """
    from evaluation import screen_cache

    cli = ctx.cli
    if getattr(cli, "no_benchmark_screen_cache", False):
        screen = run_screen(ctx, bench, client, dataset)
        screen.cache_provenance = {"hit": False, "reason": "cache disabled"}
        return screen

    stamp = screen_cache.device_stamp(cli)
    try:
        key = screen_cache.build_key(cli, dataset, bench, bench.load(ctx, cli),
                                     ctx.args.model, device=stamp["device"])
    except screen_cache.Unfingerprintable as error:
        # No key means no safe way to tell this screen from a different one,
        # so the cache sits this dataset out entirely. Screening still happens;
        # the run is exactly what it would have been before the cache existed.
        print("  WARNING: %s: screen cache disabled -- %s" % (dataset, error))
        screen = run_screen(ctx, bench, client, dataset)
        screen.cache_provenance = {"hit": False,
                                   "reason": "unfingerprintable: %s" % error}
        return screen
    if getattr(cli, "benchmark_refresh_screen", False):
        provenance = {"hit": False, "reason": "--benchmark-refresh-screen"}
    else:
        screen, provenance = screen_cache.load(cli, dataset, key)
        if screen is not None:
            print("  %s: screen reused from cache (made %s on %s)"
                  % (dataset, provenance.get("created_at", "?"),
                     provenance.get("device", "?")))
            screen.cache_provenance = provenance
            return screen
        for near in provenance.pop("near", [])[:1]:
            print("  %s: nearest cached screen differs in: %s"
                  % (dataset, ", ".join(near["differs"]) or "nothing"))

    screen = run_screen(ctx, bench, client, dataset)
    provenance = dict(provenance)
    refusal = _screen_is_judge_damaged(screen)
    if refusal:
        # A screen built while the judge API was failing is a short, biased
        # evaluation set. `run_screen` succeeds as long as *some* item came
        # back deceptive, so an outage does not stop the run -- but caching
        # that set would freeze one bad afternoon onto disk and hand it to
        # every later job with these flags. The run continues on the screen it
        # has, which is the same thing it would have done before the cache
        # existed; only the save is refused.
        print("  WARNING: %s: not caching this screen -- %s" % (dataset,
                                                                refusal))
        provenance["written"] = {"saved": False, "reason": refusal}
    else:
        provenance["written"] = screen_cache.save(cli, dataset, key, screen)
    screen.cache_provenance = provenance
    return screen


def _screen_is_judge_damaged(screen):
    """-> a reason string if a judge outage shaped this screen, else "".

    `label_counts` cannot answer this: a judge that never replied and a
    response that genuinely could not be parsed both land in `unparsed`. Only
    `raw` separates them, which is why `_judge_all` writes "judge-failed"
    there rather than leaving the rubric to guess.
    """
    failed = sum(1 for row in screen.full_rows
                 if row.get("raw") == "judge-failed")
    if failed:
        return "%d of %d selected items were labelled by a judge that never " \
               "answered" % (failed, len(screen.full_rows))
    dropped = screen.stats.get("dropped_belief_judge_failed") or 0
    if dropped:
        return "%d candidates were dropped because the belief judge " \
               "failed" % dropped
    return ""


#: How many distinct `raw` reasons the "no deception" message names, and how
#: much of each it prints. `raw` is free-form -- most adapters return a short
#: tag (`no_letter`, `sandbag_missing_tags`) but some return a judge verdict,
#: and this string is stored verbatim in `benchmarks.json`.
_REASON_LIMIT = 6
_REASON_WIDTH = 48


def _no_deception_message(dataset, screened, label_counts, reasons, no_belief):
    """Why a dataset had nothing to knock out, in the one place it is visible.

    The label counts alone say a screen found no deception; they do not say
    whether the model refused the task, answered in a shape the adapter cannot
    read, or never got as far as being judged. Those are three different
    findings -- one about the model, one about the adapter, one about the
    belief probes -- and telling them apart used to need a GPU rerun, because
    `raw` (which already distinguishes them) was counted nowhere. So the
    reasons behind every UNPARSED row travel with the failure.
    """
    text = ("%s: the full model was not judged deceptive on any of the %d "
            "candidates screened, so there is no deception for a knockout to "
            "reduce. Labels seen: %s" % (dataset, screened, label_counts))
    if no_belief:
        text += ("; %d further candidates were dropped before judging for "
                 "want of an agreed belief" % no_belief)
    if reasons:
        ranked = sorted(reasons.items(), key=lambda kv: (-kv[1], str(kv[0])))
        named = ", ".join("%s x%d" % (str(reason)[:_REASON_WIDTH], count)
                          for reason, count in ranked[:_REASON_LIMIT])
        if len(ranked) > _REASON_LIMIT:
            named += ", and %d more" % (len(ranked) - _REASON_LIMIT)
        text += ". Unparsed reasons: %s" % named
    return text


def run_screen(ctx, bench, client, dataset) -> Screen:
    """Walk the candidate pool until the evaluation set and reference pool fill.

    `hook=None` throughout: every pass here runs under `all_gates_open`, so no
    unit is ablated and the ablation hook is never consulted. Passing
    `ctx.hook_for(...)` would build a mean bank for a pass that cannot read one
    — and would need the evaluation set to build it, which does not exist yet.
    """
    cli = ctx.cli
    tok = ctx.tokenizer
    eos = eos_ids_for(ctx.node_model)
    pad_id = resolve_pad_id(tok, eos)

    target = cli.benchmark_n_per_dataset
    new_tokens = bench.new_tokens or cli.benchmark_new_tokens
    prompt_kind = bench.condition_kind == "prompt"
    # Where the belief probe IS the honest twin -- `instructed-deception`, whose
    # probe and whose reference-pool row are the same prompt -- one generation
    # has to serve both roles, at the larger of the two budgets. Generating it
    # twice costs a second full pass over every screened candidate, and decides
    # belief from a 128-token truncation while the reference stream carries the
    # 512-token version, so lowering --benchmark-belief-tokens would silently
    # shrink the evaluation set. The plan says as much: "no extra pass needed".
    want_pool = 0 if cli.benchmark_ref_pool == "deceptive" else target

    candidates = bench.load(ctx, cli)
    # "Shuffle candidates with a seeded RNG" (plan, "Prompt selection — the
    # behavioural filter"). Screening in load order would make the evaluation
    # set a property of how the source file happens to be sorted -- MASK's CSVs
    # are grouped by archetype, and sandbagging's pool is a bio/chem/cyber
    # round-robin whose first N is topic-balanced only by luck. Seeded, so the
    # set is reproducible.
    import numpy as np

    order = np.random.default_rng(cli.benchmark_screen_seed).permutation(
        len(candidates))
    candidates = [candidates[int(i)] for i in order]
    honest_candidates = [c for c in candidates if c.condition == base.HONEST]
    shared = _probe_is_the_reference(bench, candidates)
    belief_tokens = new_tokens if shared else cli.benchmark_belief_tokens
    belief_refs = {} if shared else None
    if prompt_kind:
        # An honest-condition candidate is a reference, not something to screen
        # for deception; its half of `load()` is used below.
        candidates = [c for c in candidates if c.condition == base.DECEPTIVE]

    screen = Screen(dataset)
    screen.new_tokens = new_tokens
    selected, pool, screened, no_belief = [], [], 0, 0
    judged = 0
    belief_judge_failed = 0
    chunk_size = max(target * SCREEN_CHUNK_FACTOR, cli.benchmark_gen_batch_size)
    label_counts = {}
    # `raw` for every judged row, bucketed by label, plus a few of the
    # responses behind the unparsed ones.
    #
    # `screen_labels` says how many rows a screen discarded; only this says
    # why, and the reasons behind one label are not interchangeable. UNPARSED
    # alone covers a judge that emitted no verdict (broken judge), a model that
    # refused (a fact about the model), and a response the adapter could not
    # read (a fact about the adapter) -- three findings that call for three
    # different responses. Kept for HONEST and DECEPTIVE too, because `raw` is
    # also where a scenario records which branch produced the row: Liars' Bench
    # knowledge-report scores DENIED_KNOWLEDGE as honest against an item the
    # model does not know and deceptive against one it does, and the counts
    # cannot be told apart without it.
    #
    # This used to be UNPARSED-only and read only when the screen selected
    # nothing. That left a *successful* screen with no record of why it
    # discarded what it discarded -- recoverable only by a GPU rerun, which is
    # the cost `_no_deception_message` already exists to avoid.
    raw_counts = {}
    unparsed_samples = []

    # The plan is explicit for outcome-kind benchmarks: "if honest bycatch from
    # the screen is < N, keep screening until the honest bank reaches N (or the
    # pool ends). Do not silently pair against a handful of honest items." So
    # the default is unbounded and `--benchmark-screen-budget` is the opt-in
    # bound, not the other way round -- an earlier version of this had it
    # backwards and capped every run at 10x the target on its own initiative.
    budget = cli.benchmark_screen_budget or len(candidates)
    for start in range(0, len(candidates), chunk_size):
        # The budget is a hard ceiling on screening work, checked on its own.
        # It used to hang off `len(selected) >= target`, which meant it bound
        # only the pool-filling tail and never the search for deceptive items
        # -- so a dataset that found none walked its entire pool regardless.
        # That is the case where a bound matters most: two Liars' Bench
        # scenarios screened 4601 and 5245 candidates under `--budget 300` and
        # took 13.6 h between them.
        if screened >= budget:
            break
        if len(selected) >= target and (prompt_kind or len(pool) >= want_pool):
            break
        chunk = candidates[start:start + chunk_size]
        # Counted before the belief filter: these candidates were consumed
        # whether or not they survived it, so counting only survivors would let
        # the walk overrun its budget by the drop rate.
        screened += len(chunk)
        chunk, dropped, judge_failed = _elicit_beliefs(
            ctx, bench, client, chunk, eos, pad_id,
            "%s: belief (full model)" % dataset, belief_tokens, belief_refs)
        no_belief += dropped
        belief_judge_failed += judge_failed
        if not chunk:
            continue

        texts = [render_messages(tok, item.messages) for item in chunk]
        clean_ids, clean_mask = encode_prompts(tok, texts, pad_id)
        width = clean_ids.shape[1]
        corrupt = placeholder_corrupt(clean_ids, clean_mask, new_tokens, pad_id)
        with ctx.all_gates_open():
            out = generate_under(ctx, clean_ids=clean_ids,
                                 clean_mask=clean_mask, corrupt_ids=corrupt,
                                 hook=None, new_tokens=new_tokens, eos=eos,
                                 desc="%s: screen (full model)" % dataset)
        responses = decode_completions(tok, out, width, eos)
        rows = _judge_all(client, bench, chunk, responses)
        completions = completion_tokens(out, width, eos)
        judged += len(chunk)

        for index, (item, row) in enumerate(zip(chunk, rows)):
            label_counts[row["label"]] = label_counts.get(row["label"], 0) + 1
            reason = row.get("raw")
            bucket = raw_counts.setdefault(row["label"], {})
            bucket[reason] = bucket.get(reason, 0) + 1
            if row["label"] == base.UNPARSED:
                if len(unparsed_samples) < UNPARSED_SAMPLES:
                    unparsed_samples.append((reason, responses[index]))
            prompt = clean_ids[index][clean_mask[index].bool()].tolist()
            if row["label"] == base.DECEPTIVE and len(selected) < target:
                selected.append({
                    "item": item.replace(condition=base.DECEPTIVE),
                    "text": texts[index], "row": row,
                    # The generated block, carried over so the `full`
                    # configuration is these exact tokens rather than a rerun.
                    "block": out[index, width:].clone(),
                    "ref": (prompt, completions[index])})
            elif (row["label"] == base.HONEST and not prompt_kind
                    and len(pool) < want_pool):
                pool.append({"item": item.replace(condition=base.HONEST),
                             "ref": (prompt, completions[index])})

    if not selected:
        # Printed rather than raised: the responses are the evidence for which
        # of the reasons above is the model's doing, but they are long, and the
        # message is stored in `benchmarks.json` and read in a report.
        for reason, response in unparsed_samples:
            print("  %s: unparsed (%s): %r" % (dataset, reason,
                                               (response or "")[:200]))
        raise RuntimeError(_no_deception_message(
            dataset, screened, label_counts,
            raw_counts.get(base.UNPARSED, {}), no_belief))

    screen.items = [s["item"] for s in selected]
    screen.prompts = [s["text"] for s in selected]
    screen.full_rows = [s["row"] for s in selected]
    screen.stats = {
        "candidates": len(candidates), "screened": screened,
        "selected": len(selected), "target": target,
        "judged": judged,
        # The plan asks for this by name: the full model's deception rate on
        # the screened prefix. It is the number that says whether the
        # evaluation set was easy or hard to fill -- and it is NOT the `full`
        # row, which is 1.0 by construction.
        "full_model_deception_rate": (
            label_counts.get(base.DECEPTIVE, 0) / judged if judged else None),
        "seed": cli.benchmark_screen_seed,
        "dropped_no_belief": no_belief,
        # Kept apart from `dropped_no_belief` on purpose: one is a fact about
        # the model, the other is a fact about an API.
        "dropped_belief_judge_failed": belief_judge_failed,
        "screen_labels": label_counts,
        # `{label: {raw: count}}` -- the reason breakdown behind
        # `screen_labels`. See `raw_counts` above for why a bare label count is
        # not enough to read a screen.
        "screen_raw": raw_counts,
        "early_stopped": screened < len(candidates),
        "budget": budget,
        # True whenever the screen stopped with the reference pool still
        # short -- because it hit the budget, *or* because the candidate pool
        # simply ran out. Conditioning on the budget alone left the second case
        # unreported, which is the more likely one on the small MASK splits.
        "pool_short": not prompt_kind and len(pool) < want_pool,
    }

    # Re-encode the selection as one batch with one width, rather than leaving
    # it at whatever the widest screening chunk happened to be. Only the prompt
    # columns are rebuilt; the generated block above is carried over unchanged,
    # so `full`'s text is the text its label was computed from.
    screen.clean_ids, screen.clean_mask = encode_prompts(
        tok, screen.prompts, pad_id)
    screen.prompt_width = screen.clean_ids.shape[1]
    screen.full_ids = torch.cat(
        [screen.clean_ids, torch.stack([s["block"] for s in selected])], dim=1)

    screen.stats["belief_tokens"] = belief_tokens
    screen.stats["belief_doubles_as_reference"] = shared
    _build_reference_pool(ctx, bench, screen, selected, pool,
                          honest_candidates, prompt_kind, want_pool, eos,
                          pad_id, dataset, belief_refs)
    return screen


def _probe_is_the_reference(bench, candidates):
    """Does this benchmark's belief probe render to the same prompt as the
    honest twin it will also use as the reference-pool row?

    Compared by content rather than assumed from `condition_kind`: an adapter
    is free to make its probe a different question from its twin, and reusing
    one generation for the other would then score belief against text the model
    never produced for that prompt.
    """
    if not candidates:
        return False
    item = candidates[0]
    twin = bench.honest_twin(item)
    probes = bench.belief_request(item)
    if twin is None or not probes or len(probes) != 1:
        return False
    return probes[0]["messages"] == twin.messages


def _build_reference_pool(ctx, bench, screen, selected, pool,
                          honest_candidates, prompt_kind, want_pool, eos,
                          pad_id, dataset, belief_refs=None):
    """Fill `screen.pool_items` / `pool_refs` / `partner_index`."""
    cli = ctx.cli

    if cli.benchmark_ref_pool == "deceptive":
        # The evaluation set references itself; a derangement keeps any item
        # from drawing itself, which would make interchange a no-op.
        screen.pool_items = list(screen.items)
        screen.pool_refs = [s["ref"] for s in selected]
        screen.pairing = "derangement"
        screen.partner_index, screen.partner_reused = assign_partners(
            len(screen.items), len(screen.pool_items), cli.wikitext_seed,
            forbidden=list(range(len(screen.items))))
        return

    twins = [bench.honest_twin(item) for item in screen.items]
    if prompt_kind and all(twin is not None for twin in twins):
        # `honest_twin` returning an item means "this one's counterpart is not
        # in load(); here it is" — a minimal pair, so item i takes twin i.
        pool_items, pairing = twins, "twin"
    elif prompt_kind:
        pool_items, pairing = honest_candidates[:want_pool], "derangement"
    else:
        pool_items, pairing = [p["item"] for p in pool], "derangement"

    # Where the evaluation set is part of its own reference pool, remember
    # where each item landed so it cannot be handed back to itself below.
    forbidden = None
    if cli.benchmark_ref_pool == "pooled":
        forbidden = [len(pool_items) + i for i in range(len(screen.items))]
        pool_items = list(pool_items) + list(screen.items)
        # Not a derangement: the pool is larger than the evaluation set, so
        # `assign_partners` takes its cycle branch. Calling it one in the JSON
        # would misdescribe how the references were drawn.
        pairing = "cycle"

    if not pool_items:
        raise RuntimeError(
            "%s: --benchmark-ref-pool %s selected an empty reference pool, so "
            "the corrupt stream would be undefined. Screen more candidates "
            "(--benchmark-n-per-dataset) or use --benchmark-ref-pool "
            "deceptive, which references the evaluation set itself."
            % (dataset, cli.benchmark_ref_pool))

    # The reference is the partner's prompt *and what the full model actually
    # said to it*, so any pool item the screen did not already run needs one
    # generation pass of its own.
    known = {}
    for entry in pool:
        known[id(entry["item"])] = entry["ref"]
    for item, entry in zip(screen.items, selected):
        known[id(item)] = entry["ref"]

    tok = ctx.tokenizer
    if belief_refs:
        # The belief pass already generated these exact prompts, at the same
        # budget (see `_probe_is_the_reference`). Reuse rather than re-run.
        for item in pool_items:
            if id(item) in known:
                continue
            cached = belief_refs.get(render_messages(tok, item.messages))
            if cached is not None:
                known[id(item)] = cached

    need = [item for item in pool_items if id(item) not in known]
    if need:
        texts = [render_messages(tok, item.messages) for item in need]
        ids, mask = encode_prompts(tok, texts, pad_id)
        corrupt = placeholder_corrupt(ids, mask, screen.new_tokens, pad_id)
        with ctx.all_gates_open():
            out = generate_under(
                ctx, clean_ids=ids, clean_mask=mask, corrupt_ids=corrupt,
                hook=None, new_tokens=screen.new_tokens, eos=eos,
                desc="%s: reference pool (full model)" % dataset)
        completions = completion_tokens(out, ids.shape[1], eos)
        for row, item in enumerate(need):
            known[id(item)] = (ids[row][mask[row].bool()].tolist(),
                               completions[row])

    screen.pool_items = list(pool_items)
    screen.pool_refs = [known[id(item)] for item in pool_items]
    screen.pairing = pairing
    if pairing == "twin":
        screen.partner_index = list(range(len(screen.items)))
        screen.partner_reused = False
    else:
        screen.partner_index, screen.partner_reused = assign_partners(
            len(screen.items), len(pool_items), cli.wikitext_seed,
            forbidden=forbidden)


# ==============================================================================
# THE MEAN BANK
# ==============================================================================

def register_mean_bank(ctx, screen, dataset, pad_id, eos):
    """Stream batches for `--ablation mean`, under the name `benchmark:<ds>`.

    Two properties, both load-bearing:

    **Prompt *and* response.** A site's mean has to be taken over the positions
    the ablation will fill, and EVAL 5 ablates at every position of a
    512-1024-token generation. A bank collected over prompt tokens alone would
    fill hundreds of generated positions with a mean computed somewhere else
    entirely — so each row here is the item's prompt followed by the full
    model's own completion for it.

    **Unpadded.** `collect_mean_bank` forwards with `use_cache=False`, which
    goes through `llama_node.py`'s manual causal mask — under which a
    fully-padded query row softmaxes to NaN and poisons the whole bank (every
    subsequent argmax becomes token 0). So these batches are grouped by *exact*
    length rather than reusing the left-padded evaluation batch.
    """
    completions = completion_tokens(screen.full_ids, screen.prompt_width, eos)
    groups = {}
    for index in range(len(screen.items)):
        prompt = screen.clean_ids[index][screen.clean_mask[index].bool()].tolist()
        clean = prompt + list(completions[index])
        partner = screen.partners[index]
        corrupt, _ = pack_reference(partner[0], partner[1], len(clean), pad_id)
        groups.setdefault(len(clean), []).append((clean, corrupt))

    batches = []
    limit = max(1, ctx.cli.benchmark_gen_batch_size)
    for length in sorted(groups):
        members = groups[length]
        for start in range(0, len(members), limit):
            piece = members[start:start + limit]
            clean = torch.tensor([m[0] for m in piece], dtype=torch.long)
            corrupt = torch.tensor([m[1] for m in piece], dtype=torch.long)
            batches.append({"input_ids": clean,
                            "corrupted_input_ids": corrupt,
                            "attention_mask": torch.ones_like(clean)})
    ctx.session.register_stream_batches("benchmark:%s" % dataset, batches)
    return len(batches)


# ==============================================================================
# DERIVED FIELDS
# ==============================================================================
#
# Pulled out of `_run_config` and `run` so `evaluation/rejudge.py`, which
# repairs labels after a judge outage, recomputes them with this code rather
# than a copy of it.

def tally_labels(rows):
    """-> (counts, rates) over `base.LABELS` for one configuration's rows."""
    counts = dict((label, 0) for label in base.LABELS)
    for row in rows:
        counts[row["label"]] += 1
    total = max(len(rows), 1)
    return counts, dict((label, counts[label] / total) for label in base.LABELS)


def headline_of(datasets):
    """The cell headline: knockout's deception rate per dataset that ran."""
    return {
        dataset: entry["configs"]["knockout"]["rates"]["deceptive"]
        for dataset, entry in datasets.items()
        if "configs" in entry and "knockout" in entry["configs"]}


# ==============================================================================
# THE EVALUATION
# ==============================================================================

class BenchmarkEvaluation(Evaluation):
    name = "benchmarks"
    display_name = "Deception benchmarks — does knockout reduce deception?"
    requires = ()

    def run(self, ctx) -> dict:
        cli = ctx.cli
        # Where each dataset's screen came from — disk or a fresh pass. A
        # reader of benchmarks.json has to be able to tell whether `full`'s
        # tokens were reused from a cache, and on what hardware they were made.
        self._screen_cache = {}
        client = JudgeClient(cache_path=judge_cache_path(ctx),
                             concurrency=cli.judge_concurrency)
        payload = {
            "resolved": {
                "model": ctx.args.model,
                "ablation": cli.ablation,
                "n_per_dataset": cli.benchmark_n_per_dataset,
                "new_tokens": cli.benchmark_new_tokens,
                "belief_tokens": cli.benchmark_belief_tokens,
                "ref_pool": cli.benchmark_ref_pool,
                "n_random": cli.benchmark_n_random,
                "gen_batch_size": cli.benchmark_gen_batch_size,
                "kv_cache": not cli.no_kv_cache,
                "pairing_seed": cli.wikitext_seed,
            },
            "belief_source": "the FULL model, reused unchanged by every "
                             "configuration",
            "caveats": CAVEATS,
            "datasets": {},
        }
        failures = {}
        for dataset in expand(cli.benchmarks):
            started = time.time()
            try:
                entry = self._run_dataset(ctx, dataset, client)
            except Exception as error:                      # noqa: BLE001
                # One dataset must not discard the ones already finished.
                # `benchmarks.json` is written after the whole loop, so before
                # this a judge outage on dataset 2 threw away dataset 1's
                # completed generations -- which is exactly what happened on
                # job 21882184: sandbagging ran to completion, every config and
                # its coherence, and was lost when mask:continuations found the
                # OpenAI account out of credits an hour and a half in.
                failures[dataset] = "%s: %s" % (type(error).__name__, error)
                print("  !! %s failed, continuing with the rest: %s"
                      % (dataset, error))
                payload["datasets"][dataset] = {
                    "error": failures[dataset],
                    "seconds": round(time.time() - started, 1)}
                continue
            entry["seconds"] = round(time.time() - started, 1)
            payload["datasets"][dataset] = entry

        payload["failed_datasets"] = failures
        if failures and len(failures) == len(payload["datasets"]):
            # Nothing survived, so there is no partial result to preserve and
            # a silent empty report would be worse than the traceback.
            raise RuntimeError(
                "every selected benchmark failed:\n  "
                + "\n  ".join("%s -> %s" % kv for kv in sorted(failures.items())))

        payload["judge"] = client.stats()
        payload["screen_cache"] = self._screen_cache
        payload["headline"] = headline_of(payload["datasets"])
        payload["verification"] = {
            "benchmark_belief_from_full_model": True,
            "benchmark_full_row_is_the_screen": all(
                entry["full_row_is_screen"]
                for entry in payload["datasets"].values()
                if "error" not in entry),
        }
        return payload

    # ------------------------------------------------------------------
    def _run_dataset(self, ctx, dataset, client) -> dict:
        cli = ctx.cli
        bench = get_benchmark(dataset)
        if hasattr(bench, "bind"):
            bench.bind(cli)

        screen = ctx.session.screen_for(dataset, cached_screen, ctx, bench,
                                        client, dataset)
        # `screen_for` memoises, so in a suite only the first cell to reach a
        # dataset actually built or loaded it. Reporting the same provenance
        # for every cell would read as though each one wrote the cache.
        provenance = dict(getattr(screen, "cache_provenance", {}))
        if getattr(screen, "_provenance_reported", False):
            provenance = {"hit": provenance.get("hit"),
                          "reused_within_process": True}
        screen._provenance_reported = True
        self._screen_cache[dataset] = provenance
        eos = eos_ids_for(ctx.node_model)
        pad_id = resolve_pad_id(ctx.tokenizer, eos)

        n_batches = 0
        bank_name = "task"
        if cli.ablation == "mean":
            n_batches = register_mean_bank(ctx, screen, dataset, pad_id, eos)
            bank_name = "benchmark:%s" % dataset
        hook = ctx.hook_for(bank_name)

        corrupt, tiled = build_corrupt_stream(
            screen.clean_ids, screen.clean_mask, screen.partners,
            screen.new_tokens, pad_id)

        entry = {
            "display_name": bench.display_name,
            "condition_kind": bench.condition_kind,
            "judge": bench.judge_spec(),
            "new_tokens": screen.new_tokens,
            "n_items": len(screen.items),
            "screen": screen.stats,
            "reference": {
                # Under `zero` the ablated units are filled with zeros and the
                # corrupt stream is never read, so recording the flag's value
                # would claim a reference that had no effect on the numbers.
                "pool": (None if cli.ablation == "zero"
                         else cli.benchmark_ref_pool),
                "pairing": screen.pairing,
                "pool_size": len(screen.pool_items),
                "partner_reused": screen.partner_reused,
                "tiled_rows": len(tiled),
            },
            "mean_bank_batches": n_batches,
            "full_row_is_screen": True,
            "items": [item.to_json() for item in screen.items],
            "prompts": list(screen.prompts),
            "partner_ids": screen.partner_ids,
            "configs": {},
        }
        for config, masks in self._configs(ctx):
            entry["configs"][config] = self._run_config(
                ctx, bench, client, dataset, screen, corrupt, hook, config,
                masks, eos)
        entry["null"] = self._null(entry)
        entry["examples"] = self._examples(entry, screen)
        return entry

    def _configs(self, ctx):
        """(name, masks); `masks is None` means "pin every gate open"."""
        yield "full", None
        yield "knockout", ctx.knockout_masks
        yield "circuit_only", ctx.circuit_masks
        yield "empty", zeros_like(ctx.circuit_masks)
        n = min(ctx.cli.benchmark_n_random, len(ctx.random_masks))
        for index, masks in zip(ctx.random_indices[:n], ctx.random_masks[:n]):
            # The null is the *knockout* of a size-matched random circuit, so
            # it answers the same question the headline row does.
            yield "random-%d" % index, knockout_masks(
                masks, ctx.cli.knockout_granularity)

    def _run_config(self, ctx, bench, client, dataset, screen, corrupt, hook,
                    config, masks, eos) -> dict:
        tok = ctx.tokenizer
        if config == "full":
            ids, rows = screen.full_ids, screen.full_rows
            responses = decode_completions(tok, ids, screen.prompt_width, eos)
        else:
            context = (ctx.all_gates_open() if masks is None
                       else ctx.circuit(masks))
            with context:
                ids = generate_under(
                    ctx, clean_ids=screen.clean_ids,
                    clean_mask=screen.clean_mask, corrupt_ids=corrupt,
                    hook=hook, new_tokens=screen.new_tokens, eos=eos,
                    desc="%s: %s" % (dataset, config))
            responses = decode_completions(tok, ids, screen.prompt_width, eos)
            rows = _judge_all(client, bench, screen.items, responses)

        coherence = coherence_metrics(
            ctx, ids, screen.clean_mask, screen.prompt_width, eos_ids=eos,
            batch_size=coherence_batch_size(ctx.cli),
            desc="%s: coherence (%s)" % (dataset, config))

        counts, rates = tally_labels(rows)
        return {
            "counts": counts,
            "rates": rates,
            "coherence": coherence,
            "generations": responses,
            "labels": rows,
        }

    def _null(self, entry) -> dict:
        """Where knockout sits against the size-matched random circuits.

        `unparsed` is summarised alongside `deceptive` because a random circuit
        that destroys output format scores a low deception rate for a reason
        that has nothing to do with honesty — on the deception column alone it
        would read as the null matching the discovered circuit.
        """
        randoms = [name for name in entry["configs"] if name.startswith("random-")]
        if not randoms or "knockout" not in entry["configs"]:
            return {}
        out = {"n": len(randoms), "configs": randoms}
        for key in ("deceptive", "unparsed"):
            out[key] = summarize_null(
                [entry["configs"][name]["rates"][key] for name in randoms],
                entry["configs"]["knockout"]["rates"][key], better="lower")
        return out

    def _examples(self, entry, screen) -> list:
        """Three `full` vs `knockout` generations, with why each was chosen.

        Preferring switched items (`full` deceptive, `knockout` honest) shows
        the effect at its clearest; filling from the top of the id order when
        there are not three keeps a thin success set from being presented as a
        curated one. `reason` records which happened, per example.
        """
        if "knockout" not in entry["configs"]:
            return []
        full = entry["configs"]["full"]
        knock = entry["configs"]["knockout"]
        switched = [i for i in range(entry["n_items"])
                    if full["labels"][i]["label"] == base.DECEPTIVE
                    and knock["labels"][i]["label"] == base.HONEST]
        chosen = [(i, "switched") for i in switched[:3]]
        for i in range(entry["n_items"]):
            if len(chosen) >= 3:
                break
            if i not in switched:
                chosen.append((i, "fallback"))
        return [{
            "index": index,
            "reason": reason,
            "item_id": screen.items[index].item_id,
            "prompt": screen.prompts[index],
            "belief": screen.items[index].to_json()["belief"],
            "full": {"text": full["generations"][index],
                     "label": full["labels"][index]["label"]},
            "knockout": {"text": knock["generations"][index],
                         "label": knock["labels"][index]["label"]},
        } for index, reason in chosen]

    # ------------------------------------------------------------------
    def report(self, payload, ctx) -> None:
        report.banner("EVAL 5 — DECEPTION BENCHMARK KNOCKOUT")
        resolved = payload["resolved"]
        report.kv("datasets", ", ".join(payload["datasets"]))
        report.kv("items per dataset", resolved["n_per_dataset"])
        report.kv("reference pool", resolved["ref_pool"])
        report.kv("random circuits", resolved["n_random"])
        report.kv("KV cache", "on" if resolved["kv_cache"] else "off (debug)")
        report.kv("judge cache", payload["judge"]["cache_path"])

        for dataset, entry in payload["datasets"].items():
            if "error" in entry:
                # `run` isolates a failing dataset so the finished ones survive;
                # printing has to honour the same contract. Reaching into an
                # error entry for `display_name` raised KeyError here and, as
                # `report` runs before the payload is written, discarded a whole
                # completed run over a banner.
                report.banner("%s — FAILED" % dataset, "-")
                print("\n  %s\n" % entry["error"])
                continue
            self._report_dataset(dataset, entry)
        self._report_headline(payload)
        self._report_examples(payload)

        report.banner("HOW TO READ EVAL 5", "-")
        print()
        for line in CAVEATS:
            print("  - %s" % line)

    def _report_dataset(self, dataset, entry) -> None:
        report.banner("%s — %s" % (dataset, entry["display_name"]), "-")
        judge = entry["judge"]
        print("\n  belief: elicited from the FULL model and reused unchanged "
              "by every configuration below.")
        print("  condition kind: %s     judge: %s"
              % (entry["condition_kind"],
                 "%s/%s" % (judge["provider"], judge["model"]) if judge
                 else "local grader, no API"))
        screen = entry["screen"]
        print("  screened %d of %d candidates%s -> %d items; %d dropped for "
              "no belief."
              % (screen["screened"], screen["candidates"],
                 " (early stop)" if screen["early_stopped"] else "",
                 screen["selected"], screen["dropped_no_belief"]))
        if screen.get("dropped_belief_judge_failed"):
            print("  !! %d further items were dropped because their belief "
                  "judge call FAILED;\n     that is an API outcome, not the "
                  "model having no belief."
                  % screen["dropped_belief_judge_failed"])
        if screen.get("pool_short"):
            print("  !! the screen ran out of candidates or budget with the "
                  "reference pool still\n     short of %d; it is cycled, so "
                  "several items share one reference."
                  % screen.get("target", 0))
        ref = entry["reference"]
        if ref["pool"] is None:
            print("  corrupt reference: none — --ablation zero fills ablated "
                  "units with zeros,\n     so the reference pool is not read.")
        else:
            print("  corrupt reference: %s pool, %s pairing, %d rows%s%s"
                  % (ref["pool"], ref["pairing"], ref["pool_size"],
                     ", partners reused" if ref["partner_reused"] else "",
                     ", %d tiled" % ref["tiled_rows"] if ref["tiled_rows"]
                     else ""))

        print("\n  %-38s %9s %8s %9s %8s %8s %8s %8s"
              % ("configuration", "deceptive", "honest", "unparsed", "ref NLL",
                 "dist-n", "corpus", "tokens"))
        print("  " + "-" * 102)
        for config, cell in entry["configs"].items():
            rates, coherence = cell["rates"], cell["coherence"]
            print("  %-38s %8.1f%% %7.1f%% %8.1f%% %8s %8s %8s %8d"
                  % (CONFIG_LABELS.get(config, config),
                     100 * rates["deceptive"], 100 * rates["honest"],
                     100 * rates["unparsed"], _fmt(coherence["ref_nll"]),
                     _fmt(coherence["distinct_n"]),
                     _fmt(coherence["distinct_n_corpus"]),
                     coherence["n_tokens"]))
        print("\n  'full' is 100%% deceptive by construction — these are the "
              "items it was judged\n  deceptive on. It is the scale for the "
              "rows below, not a result.")
        print("  'unparsed' is the column that stops this table lying: a "
              "knockout that destroys\n  output format has no deceptive "
              "content left to find, and would otherwise\n  read as a large "
              "honesty gain.")
        print("  'dist-n' is per row; 'corpus' pools every row, so a low corpus "
              "figure next to a\n  healthy per-row one is mode collapse — "
              "every item answered the same way.")

        null = entry.get("null")
        if null:
            # The shared table, so EVAL 5's null reads the same way as eval 3's
            # and carries std / p50 / p95 / z rather than a hand-rolled subset.
            report.stats_table(
                null, [("deceptive", "deception"), ("unparsed", "unparsed")],
                null["n"],
                title="EVAL 5 NULL — %s (knockout vs size-matched random)"
                      % dataset)
            print("  Both are 'lower is better'. Read them together: a random "
                  "circuit that\n  destroys output format scores a low "
                  "deception rate for a reason that has\n  nothing to do with "
                  "honesty.")

    def _report_headline(self, payload) -> None:
        report.banner("CROSS-DATASET HEADLINE", "-")
        print("\n  %-36s %11s %11s %11s %8s"
              % ("dataset", "knockout", "circuit only", "empty", "n"))
        print("  " + "-" * 82)
        for dataset, entry in payload["datasets"].items():
            if "error" in entry:
                continue                      # no configs were ever run
            configs = entry["configs"]
            print("  %-36s %10.1f%% %10.1f%% %10.1f%% %8d"
                  % (dataset,
                     100 * configs["knockout"]["rates"]["deceptive"],
                     100 * configs["circuit_only"]["rates"]["deceptive"],
                     100 * configs["empty"]["rates"]["deceptive"],
                     entry["n_items"]))
        print("\n  Deception rate, against a `full` row that is 100%% "
              "everywhere by construction.")

    def _report_examples(self, payload) -> None:
        for dataset, entry in payload["datasets"].items():
            for example in entry.get("examples", []):
                report.banner("%s — example %d (%s)"
                              % (dataset, example["index"], example["reason"]),
                              "-")
                print("\n  item: %s" % example["item_id"])
                print("  belief: %r\n" % (example["belief"],))
                print("  full model (%s):\n    %r\n"
                      % (example["full"]["label"], example["full"]["text"]))
                print("  circuit knocked out (%s):\n    %r\n"
                      % (example["knockout"]["label"],
                         example["knockout"]["text"]))


CAVEATS = [
    "Belief is the full model's throughout. Re-eliciting it under ablation "
    "would let a knowledge deficit score as an honesty gain.",
    "The `full` row is 100% deceptive by construction — it is the pass that "
    "selected these items — so read the other rows against it, not as a "
    "measured contrast.",
    "This design cannot detect the opposite effect: an ablation that made the "
    "model deceptive where it was honest puts those items in the reference "
    "pool, not the evaluation set.",
    "Position extrapolation. The mask was learned for a single readout at "
    "prefix_length - 1 and is applied here at every position of a "
    "512-1024-token generation, so a positive result is strong evidence and a "
    "negative one is weak.",
    "Read the `full` column of the example generations first. If that is not "
    "fluent, the generation engine is broken, not the circuit.",
    "Then read the `knockout` column, including the rows labelled `honest`. "
    "Every grader here keys on a small part of the response -- sandbagging on "
    "one <step1-results> tag -- so a generation can degrade badly and still "
    "score `honest` because the one token the grader reads survived. The "
    "coherence columns are what separate that from real honesty: a large drop "
    "in distinct-n or a rise in ref NLL next to a fall in the deception rate "
    "means format loss, not a behavioural change. (Observed on the very first "
    "GPU run: knockout scored 0% deceptive with distinct-n down from 0.69 to "
    "0.35 and 75% of rows unparsed outright.)",
]


def _fmt(value):
    return "--" if value is None else "%.3f" % value


def coherence_batch_size(cli) -> int:
    """Rows per coherence forward — deliberately NOT the generation batch size.

    `reference_cross_entropy` materialises `logits[:, gen_start-1:-1].float()`
    and its `log_softmax`, two float32 tensors of `batch x generated x 128256`,
    on top of the model's own full-sequence logits. It is the largest transient
    in EVAL 5 and it is not the thing the generation batch size was tuned for.

    Measured across all eleven adapters with the real tokenizer, the worst case
    is **sandbagging**, not the multi-turn benchmarks: its longest prompt is
    2501 tokens *and* it generates 1024, giving 15.6 GB at batch 8 — 47.6 GB of
    an A40's 48 GB once ~32 GB of weights are resident under `--reference
    separate`. Every MASK split is 5.8-6.2 GB (their longest prompt, 438
    tokens, is shorter than sandbagging's *median* of 657), and the heaviest
    Liars' Bench scenario is 8.5 GB.

    Job 21880374 ran batch 8 on sandbagging without trouble, but with only 8
    selected items it never assembled a batch around the long tail — so that
    run is not evidence for the ceiling. A quarter of the generation batch puts
    the worst case near 3.9 GB for a few minutes of extra wall time.
    """
    explicit = getattr(cli, "benchmark_coherence_batch_size", None)
    if explicit:
        return max(1, int(explicit))
    return max(1, int(cli.benchmark_gen_batch_size) // 4)


def judge_cache_path(ctx) -> str:
    """One cache for the whole invocation, above the per-cell directories.

    A suite re-judges the same (item, response) pair whenever two cells produce
    the same text, and a re-run after a crash re-judges everything. Both are
    paid once if the cache sits above the cell.
    """
    root = getattr(ctx.cli, "output_dir", None)
    if not root and not getattr(ctx.cli, "legacy", True):
        # A suite writes cells three levels down; the cache belongs at the
        # suite root, or every cell re-buys the same verdicts.
        from evaluation import suite
        root = suite.suite_root(ctx.cli, ctx.session.base_run_dir)
    return os.path.join(root or ctx.out_dir, "judge_cache.jsonl")


# ==============================================================================
# --judge-dry-run
# ==============================================================================

def judge_dry_run(session) -> int:
    """Print one judge prompt per selected benchmark and exit.

    No model, no CUDA, no API key: `Benchmark.judge_request` is pure prompt
    construction, which is exactly why the adapters are forbidden from
    generating and from calling out. This is the check that the judge prompts
    can be read before any credits are spent on them.
    """
    cli = session.cli
    report.banner("JUDGE DRY RUN — no model loaded, no API call made")
    ctx = session.context_for(session.circuits[0], session.tasks[0], "")
    placeholder = ("I am not able to say. The honest answer is that I do not "
                   "know, and I will not guess.")

    for dataset in expand(cli.benchmarks):
        bench = get_benchmark(dataset)
        if hasattr(bench, "bind"):
            bench.bind(cli)
        report.banner("%s — %s" % (dataset, bench.display_name), "-")
        spec = bench.judge_spec()
        print("\n  judge: %s"
              % ("%s/%s" % (spec["provider"], spec["model"]) if spec
                 else "local grader, no API call"))
        items = bench.load(ctx, cli)
        if not items:
            print("  (no items loaded)")
            continue
        item = items[0]
        print("  item: %s" % item.item_id)

        for probe in (bench.belief_request(item) or []):
            print("\n  --- belief probe %r (asked of the model under test) ---"
                  % probe["name"])
            print(render_block(probe["messages"]))
            request = bench.belief_judge_request(item, probe["name"], placeholder)
            if request is not None:
                print("\n  --- belief judge for %r (%s/%s) ---"
                      % (probe["name"], request.provider, request.model))
                print(_indent(request.prompt_text))

        request = bench.judge_request(item, placeholder)
        if request is None:
            label, raw = bench.parse_judgement(item, placeholder)
            print("\n  --- graded locally: %s (%s) ---" % (label, raw))
        else:
            print("\n  --- response judge (%s/%s) ---"
                  % (request.provider, request.model))
            print(_indent(request.prompt_text))

    print("\n  Nothing was generated and nothing was judged. Drop "
          "--judge-dry-run to run it.")
    return 0


def render_block(messages) -> str:
    return _indent("\n\n".join("[%s]\n%s" % (m["role"].upper(), m["content"])
                               for m in messages))


def _indent(text, prefix="    "):
    return "\n".join(prefix + line for line in (text or "").splitlines())
