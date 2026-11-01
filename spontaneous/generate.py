"""Helpers for the B3 generation entrypoint `scripts/b3_generate.py` (plan B3 sections 1.3, 1.4, 3.4; ticket T4).

**Contexts.** One context is one rendered prompt: (split, variant, control, query, condition). `build_contexts` makes
both tiers of every (variant, control, query) through `af_prompts.build_af_pair`, which asserts that the twins have
equal length and differ at exactly one token, the tier tag (`tag_pos`). The prompt ends with the open assistant
header plus the variant's `assistant_prefill` ("" for V-A, "<OUTPUT>\\n" for V-B), so the **Readout**, the first
generated position, is `readout_index == prompt_len == len(prompt_ids)`; its distribution is read from the logits at
`prompt_len - 1`.

**Rows and seeds.** Every context gets `samples` sampled rows (sample 0 to n-1; `control_samples` for C1 and C2) and
one greedy row (sample `GREEDY` = -1). Each row has its own seed, `row_seed(base_seed, split, variant, control,
query_id, condition, sample)`: the first 8 bytes of a sha256, masked to 63 bits, so it is the same on every
interpreter. Sampling is **per row**: HF `generate` runs in greedy mode with `PerRowSampler` as its last logits
processor. The processor applies temperature and top-p (HF's `TopPLogitsWarper` rule) to each row and draws that
row's token from that row's own `torch.Generator`, then returns scores that are finite only at the drawn token, so
greedy selection takes it. A row's tokens therefore depend on its prompt and its seed, not on which rows share its
batch or where it sits (up to the batched-kernel rounding of bf16 on a GPU). Greedy rows pass through unchanged.

**Teacher-forced stems.** For each context the six frozen stem paths (`proxy.stem_id_paths`) are appended to the
prompt and run in right-padded batches through the HF base model; a forward pre-hook on the final norm captures the
residual at the last unpadded position, and `component_analysis.hooks.readout_logits` turns it into fp32 logits
(ADR-0001). The log-softmax of those is the stem's next-token distribution. The `()` stem is the Readout distribution.
P1 and P2 margins are computed in-job on the full vectors (`margins`); the stored record (`sparse_stems`) follows the
`spontaneous.rows` schema, so `rows.row_margins` reproduces them.

**Row schema.** `spontaneous.rows` (ticket T5) owns it. Rows add the fields it allows: `control` (None, "C1", "C2"),
`tag_pos`, `prompt_len`, `readout_index`, `assistant_prefill`, `finish_reason`, `truncated`, `temperature`, `top_p`,
and on greedy rows `margins` and `readout_argmax_id`. `rows.make_row_id` carries the control, so row ids are unique
across controls; base rows and each control's rows still go to separate files (`row_file_name`), so the judge can
read the base file alone.

Nothing here imports nnsight; the dry run uses only `build_contexts`, `plan_jobs`, `batches` and the estimate.
"""
from __future__ import annotations

import hashlib
import inspect
import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence

from spontaneous import af_prompts
from spontaneous import rows as rw

GREEDY = rw.GREEDY
CONDITIONS = af_prompts.TIERS
VARIANT_FLAGS = {"va": ["V-A"], "vb": ["V-B"], "both": ["V-A", "V-B"]}
CONTROL_FLAGS = {"base": None, "c1": "C1", "c2": "C2"}

#: Stored log-probs per stem: the most likely ids (rows.py requires at least 256) plus every id a proxy can read.
TOP_K_EMPTY = 1024
TOP_K_OTHER = 256

# ---- walltime constants (plan B3 section 6): A100 40 GB, bf16 -------------------------------------------------
#: Model load, from the mechanism-analysis 02a sweep (476 s on an H100 node; the Lustre read dominates).
LOAD_S = 476.0
#: Prefill and teacher-forced throughput: about 15 forwards per second at about 800 tokens on an A100.
FORWARD_TOKENS_PER_S = 15 * 800.0
#: One decoding step at batch 32 on an A100, about 25 ms. Every batch is charged the full `max_new_tokens`.
DECODE_STEP_S = 0.025


# ==============================================================================
# Seeds, contexts and jobs
# ==============================================================================

def row_seed(base_seed: int, split: str, variant: str, control: Optional[str], query_id: str, condition: str,
             sample: int) -> int:
    """The per-row torch seed: 63 bits of sha256 over the row's identity."""
    key = "|".join(str(x) for x in (int(base_seed), split, variant, control or "base", query_id, condition,
                                     int(sample)))
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:8], "big") & (2 ** 63 - 1)


@dataclass
class Context:
    split: str
    variant: str
    control: Optional[str]
    query_id: str
    category: str
    query: str
    condition: str
    prompt_ids: List[int] = field(repr=False)
    tag_pos: int

    @property
    def prompt_len(self) -> int:
        return len(self.prompt_ids)

    @property
    def readout_index(self) -> int:
        """The first generated position; its distribution is read from the logits at `prompt_len - 1`."""
        return len(self.prompt_ids)

    @property
    def assistant_prefill(self) -> str:
        return af_prompts.VARIANTS[self.variant]["assistant_prefill"]


def build_contexts(tokenizer, queries: Sequence[dict], split: str, variants: Sequence[str],
                   controls: Sequence[Optional[str]]) -> List[Context]:
    """Both tiers of every (variant, control, query), variant-major so batches share a scaffold length."""
    out = []
    for variant in variants:
        for control in controls:
            for q in queries:
                pair = af_prompts.build_af_pair(tokenizer, q["prompt"], variant=variant, control=control)
                for cond, ids in (("free", pair.free_ids), ("paid", pair.paid_ids)):
                    out.append(Context(split, variant, control, q["id"], q["category"], q["prompt"], cond,
                                       list(ids), pair.tag_pos))
    return out


@dataclass(frozen=True)
class Job:
    context: int
    sample: int
    seed: int


def plan_jobs(contexts: Sequence[Context], samples: int, control_samples: int, base_seed: int) -> List[Job]:
    """Sampled rows then the greedy row, context by context."""
    if not 0 <= samples <= rw.N_SAMPLES or not 0 <= control_samples <= rw.N_SAMPLES:
        raise ValueError("samples must be 0 to %d" % rw.N_SAMPLES)
    jobs = []
    for i, c in enumerate(contexts):
        n = samples if c.control is None else control_samples
        for s in list(range(n)) + [GREEDY]:
            jobs.append(Job(i, s, row_seed(base_seed, c.split, c.variant, c.control, c.query_id, c.condition, s)))
    return jobs


def batches(items: Sequence, batch_size: int) -> List[list]:
    if batch_size < 1:
        raise ValueError("batch size must be at least 1")
    return [list(items[i:i + batch_size]) for i in range(0, len(items), batch_size)]


def row_file_name(control: Optional[str]) -> str:
    return "rows.jsonl" if control is None else "rows_%s.jsonl" % control.lower()


# ==============================================================================
# Sampling
# ==============================================================================

def top_p_filter(scores, top_p: float):
    """HF `TopPLogitsWarper` on one row: drop the low tail whose cumulative probability is at most 1 - top_p,
    keeping at least the most likely token. Returns a copy with dropped ids at -inf."""
    import torch
    out = scores.clone()
    if top_p >= 1.0:
        return out
    sorted_logits, sorted_idx = torch.sort(out, descending=False)
    cum = sorted_logits.softmax(-1).cumsum(-1)
    remove = cum <= (1 - top_p)
    remove[-1] = False
    out[sorted_idx[remove]] = -math.inf
    return out


class PerRowSampler:
    """A logits processor that draws each row's token with that row's generator; None marks a greedy row."""

    def __init__(self, seeds: Sequence[Optional[int]], temperature: float, top_p: float):
        if temperature <= 0:
            raise ValueError("temperature must be positive for sampled rows")
        self.seeds = list(seeds)
        self.temperature = float(temperature)
        self.top_p = float(top_p)
        self.generators = None

    def _init(self, device):
        import torch
        self.generators = []
        for s in self.seeds:
            if s is None:
                self.generators.append(None)
            else:
                g = torch.Generator(device=device)
                g.manual_seed(int(s))
                self.generators.append(g)

    def __call__(self, input_ids, scores):
        import torch
        if scores.shape[0] != len(self.seeds):
            raise ValueError("batch of %d rows for %d seeds" % (scores.shape[0], len(self.seeds)))
        if self.generators is None:
            self._init(scores.device)
        out = scores.clone()
        for i, g in enumerate(self.generators):
            if g is None:
                continue
            row = top_p_filter(scores[i].float() / self.temperature, self.top_p)
            tok = torch.multinomial(row.softmax(-1), 1, generator=g)
            out[i] = -math.inf
            out[i, tok] = 0.0
        return out


def split_generated(sequences: Iterable[Sequence[int]], eos_ids: Sequence[int]) -> List[dict]:
    """Cut each generated sequence at its first EOS: ids before it, why it stopped, ids generated incl. the EOS."""
    eos = set(int(e) for e in eos_ids)
    out = []
    for seq in sequences:
        seq = [int(t) for t in seq]
        stop = next((k for k, t in enumerate(seq) if t in eos), None)
        if stop is None:
            out.append({"ids": seq, "finish_reason": "length", "n_generated": len(seq)})
        else:
            out.append({"ids": seq[:stop], "finish_reason": "eos", "n_generated": stop + 1})
    return out


def _left_pad(prompts, pad_id, device):
    import torch
    width = max(len(p) for p in prompts)
    ids = torch.full((len(prompts), width), int(pad_id), dtype=torch.long)
    mask = torch.zeros((len(prompts), width), dtype=torch.long)
    for i, p in enumerate(prompts):
        ids[i, width - len(p):] = torch.tensor(p, dtype=torch.long)
        mask[i, width - len(p):] = 1
    return ids.to(device), mask.to(device), width


def generate_batch(hf, prompts: Sequence[Sequence[int]], seeds: Sequence[Optional[int]], *, temperature: float,
                   top_p: float, max_new_tokens: int, pad_id: int, eos_ids: Sequence[int]) -> List[dict]:
    """Left-padded HF `generate` in greedy mode with `PerRowSampler`; `seeds[i]` None makes row i greedy."""
    import torch
    from transformers import GenerationConfig, LogitsProcessorList

    device = next(hf.parameters()).device
    ids, mask, width = _left_pad(prompts, pad_id, device)
    # Explicit neutral values: the model's own generation_config (Llama-3.1: do_sample true, 0.6, 0.9) must not
    # leak in. transformers 5.x fills only unset fields; 4.5x overrides default-valued fields with the model's
    # when the model config is >= 4.50, unless `use_model_defaults=False`, which 5.x no longer takes.
    config = GenerationConfig(do_sample=False, num_beams=1, temperature=1.0, top_p=1.0, top_k=0,
                              max_new_tokens=int(max_new_tokens), pad_token_id=int(pad_id),
                              eos_token_id=[int(e) for e in eos_ids])
    extra = {}
    if "use_model_defaults" in inspect.signature(hf.generate).parameters:
        extra["use_model_defaults"] = False
    sampler = PerRowSampler(seeds, temperature, top_p)
    with torch.no_grad():
        out = hf.generate(input_ids=ids, attention_mask=mask, generation_config=config,
                          logits_processor=LogitsProcessorList([sampler]), **extra)
    if hasattr(out, "sequences"):
        out = out.sequences
    return split_generated(out[:, width:].tolist(), eos_ids)


# ==============================================================================
# Teacher-forced stems and margins
# ==============================================================================

def teacher_forced_logprobs(model, sequences: Sequence[Sequence[int]], *, batch_size: int, pad_id: int) -> list:
    """fp32 next-token log-probs after each full sequence, on the CPU, one `[vocab]` tensor per sequence.

    Right padding; the final norm's input is captured at the last unpadded position and read through
    `hooks.readout_logits` in fp32. `model` is the nnsight wrapper or the bare HF model.
    """
    import torch
    from component_analysis import hooks

    hf = hooks._hf(model)
    device = next(hf.parameters()).device
    captured = {}

    def grab(module, args, kwargs=None):
        captured["x"] = args[0] if args else kwargs["hidden_states"]

    handle = hf.model.norm.register_forward_pre_hook(grab)
    out = []
    try:
        for chunk in batches(list(sequences), batch_size):
            width = max(len(s) for s in chunk)
            ids = torch.full((len(chunk), width), int(pad_id), dtype=torch.long)
            mask = torch.zeros((len(chunk), width), dtype=torch.long)
            for i, s in enumerate(chunk):
                ids[i, :len(s)] = torch.tensor(list(s), dtype=torch.long)
                mask[i, :len(s)] = 1
            ids, mask = ids.to(device), mask.to(device)
            with torch.no_grad():
                hf.model(input_ids=ids, attention_mask=mask, use_cache=False)
                pos = hooks.readout_positions(mask)
                resid = captured.pop("x")[torch.arange(len(chunk), device=device), pos]
                logits = hooks.readout_logits(model, resid)
                lp = torch.log_softmax(logits.float(), dim=-1).cpu()
            out.extend(lp[i] for i in range(len(chunk)))
    finally:
        handle.remove()
    return out


def margins(dense: Dict[tuple, object], res) -> Dict[str, float]:
    """P1 and P2 margins on full vectors (`proxy.p1_margin`, `proxy.p2_margin`)."""
    from spontaneous import proxy as px
    return {"P1": float(px.p1_margin(dense[()], res.r1_ids)), "P2": float(px.p2_margin(dense, res))}


def sparse_stems(dense: Dict[tuple, object], res, extra_ids: Iterable[int] = (), top_k_empty: int = TOP_K_EMPTY,
                 top_k_other: int = TOP_K_OTHER) -> List[dict]:
    """The rows.py stem records, in `res.stem_paths` order.

    `top` holds the `top_k` most likely ids, every id `rows._needed_ids` lists at the stem, and at `()` the
    `extra_ids` too (first tokens seen in the run); `rest_logp` is the log of the remaining mass.
    """
    import torch
    need = rw._needed_ids(res)
    out = []
    for path in res.stem_paths:
        lp = torch.as_tensor(dense[path]).double()
        k = min(top_k_empty if path == () else top_k_other, lp.shape[0])
        keep = set(torch.topk(lp, k).indices.tolist()) | set(need[path])
        if path == ():
            keep |= {int(i) for i in extra_ids}
        keep = sorted(keep)
        rest_mask = torch.ones(lp.shape[0], dtype=torch.bool)
        rest_mask[keep] = False
        rest = float(torch.logsumexp(lp[rest_mask], 0)) if bool(rest_mask.any()) else -math.inf
        out.append({"path": list(path), "top": {str(i): float(lp[i]) for i in keep}, "rest_logp": rest})
    return out


# ==============================================================================
# Rows
# ==============================================================================

def assemble_row(ctx: Context, job: Job, gen: dict, tokenizer, vocab_size: int, *, temperature: float,
                 top_p: float) -> dict:
    """One row in the `spontaneous.rows` schema, plus T4's extra fields; validated before it is returned."""
    ids = gen["ids"]
    first = ids[0] if ids else None
    greedy = job.sample == GREEDY
    row = {
        "schema": rw.SCHEMA,
        "row_id": rw.make_row_id(ctx.split, ctx.variant, ctx.query_id, ctx.condition, job.sample, ctx.control),
        "split": ctx.split, "variant": ctx.variant, "control": ctx.control, "query_id": ctx.query_id,
        "category": ctx.category, "condition": ctx.condition, "sample": job.sample, "seed": job.seed,
        "query": ctx.query,
        "response": tokenizer.decode(ids, skip_special_tokens=True),
        "n_generated": gen["n_generated"],
        "first_token_id": first,
        "first_token_text": None if first is None else tokenizer.decode([first]),
        "opening_ids": ids[:rw.OPENING_LEN],
        "vocab_size": int(vocab_size),
        "finish_reason": gen["finish_reason"], "truncated": gen["finish_reason"] == "length",
        "temperature": None if greedy else float(temperature), "top_p": None if greedy else float(top_p),
        "tag_pos": ctx.tag_pos, "prompt_len": ctx.prompt_len, "readout_index": ctx.readout_index,
        "assistant_prefill": ctx.assistant_prefill,
    }
    return row


def attach_readout(row: dict, stems: List[dict], margin: Dict[str, float], *, r1_basis: str, tokens_sha256: str,
                   readout_argmax: int) -> dict:
    row["stems"] = stems
    row["margins"] = dict(margin, r1_basis=r1_basis, proxy_tokens_sha256=tokens_sha256)
    row["readout_argmax_id"] = int(readout_argmax)
    return row


# ==============================================================================
# Dry-run plan
# ==============================================================================

def walltime_estimate(*, n_generations: int, gen_batches: int, prompt_tokens_generated: int, stem_tokens: int,
                      max_new_tokens: int) -> Dict[str, float]:
    """Seconds on an A100 with the plan's section 6 constants; decoding charges every batch the full length."""
    prefill = prompt_tokens_generated / FORWARD_TOKENS_PER_S
    decode = gen_batches * max_new_tokens * DECODE_STEP_S
    stems = stem_tokens / FORWARD_TOKENS_PER_S
    total = LOAD_S + prefill + decode + stems
    return {"load": LOAD_S, "prefill": prefill, "decode": decode, "teacher_forced": stems, "total": total,
            "n_generations": n_generations}


def dry_run_plan(contexts: Sequence[Context], jobs: Sequence[Job], stem_paths: Sequence[Sequence[int]], *,
                 batch_size: int, max_new_tokens: int) -> dict:
    lengths = {}
    for c in contexts:
        lengths.setdefault(c.variant, []).append(c.prompt_len)
    sampled = sum(1 for j in jobs if j.sample != GREEDY)
    greedy = len(jobs) - sampled
    gen_batches = len(batches(jobs, batch_size))
    stem_extra = sum(len(p) for p in stem_paths)
    stem_tokens = sum(len(stem_paths) * c.prompt_len + stem_extra for c in contexts)
    est = walltime_estimate(n_generations=len(jobs), gen_batches=gen_batches,
                            prompt_tokens_generated=sum(contexts[j.context].prompt_len for j in jobs),
                            stem_tokens=stem_tokens, max_new_tokens=max_new_tokens)
    by_control = {}
    for j in jobs:
        key = contexts[j.context].control or "base"
        by_control[key] = by_control.get(key, 0) + 1
    return {
        "contexts": len(contexts),
        "twin_pairs_checked": len(contexts) // 2,
        "prompt_tokens": {v: {"min": min(x), "mean": sum(x) / len(x), "max": max(x)} for v, x in lengths.items()},
        "tag_pos": sorted({(c.variant, c.control or "base", c.tag_pos) for c in contexts}),
        "generations": {"sampled": sampled, "greedy": greedy, "total": len(jobs)},
        "generations_by_control": by_control,
        "generation_batches": gen_batches,
        "teacher_forced_forwards": len(contexts) * len(stem_paths),
        "walltime_estimate_s": est,
        "walltime_assumptions": {"gpu": "A100 40 GB, bf16", "load_s": LOAD_S,
                                 "forward_tokens_per_s": FORWARD_TOKENS_PER_S, "decode_step_s": DECODE_STEP_S,
                                 "decode": "every batch decodes the full max_new_tokens (upper bound)"},
    }
