"""
component_analysis/neuron_attribution.py — attribution patching over every MLP hidden neuron (neuron-partition N1).

The unit is the MLP hidden neuron: the input of `down_proj` after the SwiGLU gate, `act_fn(gate_proj(x)) *
up_proj(x)`, 14,336 per layer in Llama-3.1-8B-Instruct (the `mlp_hidden` leaf of `models/llama_node.py`). It is read
with plain torch hooks on `model.model.layers[L].mlp.down_proj`, as `scripts/d2_premise.py` does, not with nnsight.

**The metric.** m = logit(Target) - logit(Distractor) at the Readout, read through an fp32 recomputation of the
final RMSNorm (the real per-position scale) and an fp32 dot product with the difference of the two unembedding rows
(ADR-0001's fp32 readout, as `hooks.readout_logits` does, but kept in the autograd graph). The clean row's Target
and Distractor are used for both streams (`hooks.target_minus_distractor`), so m > 0 is the deceptive answer under
D and the inverted answer under I, on the clean and on the twin run alike.

**The pairs.** `dh`: the far_v2 (or ser_v2) pressure prompt D against its Neutral-Clause Twin H, through
`dataloaders.neutral_twin_batches`, which asserts the clause alignment. `in`: the user-turn transparent inversion I
against its user-neutral twin N, two HF dataset dicts the specificity-ladder session built (an unmerged Codex pool,
read in place). The loader's twin pairing does not cover them (their condition is `user_inversion`, their twin is not
`<task>_honest`, and the differing text is the user-turn request, not the `pressure` field), so `in_pairs` joins them
by instance id and asserts the same alignment itself: equal length and attention mask, the same Readout, and every
differing token inside `request_spans["clean"]`.

**The scores**, per neuron (layer, index), aggregated over rows as running float64 sums on the device (no per-row
per-neuron tensor is ever kept):

* AtP at the Readout: s = (a_clean - a_twin) * dm_clean/da at the Readout position. It estimates m(clean) minus m(clean
  with this neuron patched to its twin value), so s > 0 means the neuron pushes the clean run toward its Target.
  Aggregates `atp_readout_mean` and `atp_readout_absmean` (the mean of |s|).
* AtP over the clause: the same product summed over the pressure (D) or request (I) clause positions. Rows whose
  clean and twin clause spans differ in length fall back to the Readout only: they are left out of the clause sums
  and listed in `rows.json`. `atp_clause_mean`, `atp_clause_absmean`.
* Activation contrast: the mean over rows of a_clean - a_twin at the Readout (`contrast_readout_mean`) and that mean
  divided by the population standard deviation of a_twin over rows plus 1e-6 (`contrast_readout_std`); the same for
  activations summed over the clause positions (`contrast_clause_mean`, `contrast_clause_std`).
* With `reverse=True`, the twin run is differentiated too and `rev_atp_*` hold (a_twin - a_clean) * dm_twin/da: H as
  clean, D as twin. It costs one more backward per batch.

Nothing here imports nnsight. The model is the unmodified HF `LlamaForCausalLM` (`ModelAdapter.load_full_model`,
bf16 weights, frozen parameters). Gradients reach the captured activations because the embedding output is made to
require grad, so every layer's capture stays in one graph and the gradient into layer L's neurons includes every path
through the later layers.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import torch

#: The specificity-ladder A1 control cell that holds the user-turn I and user-neutral pools (unmerged Codex pool,
#: read in place, never written).
CODEX_POOL_ROOT = ("/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/"
                   "_analyses/specificity-ladder/a1-control-77b6487-m07")
UNMERGED_NOTE = "unmerged Codex pool"

PAIRS = ("dh", "in")
STD_EPS = 1e-6

#: Running sums, each [layers, width] float64. `n_readout` and `n_clause` count the rows each family covers.
READOUT_SUMS = ("atp_ro_sum", "atp_ro_abs", "diff_ro_sum", "twin_ro_sum", "twin_ro_sq")
CLAUSE_SUMS = ("atp_cl_sum", "atp_cl_abs", "diff_cl_sum", "twin_cl_sum", "twin_cl_sq")
REVERSE_SUMS = ("rev_atp_ro_sum", "rev_atp_ro_abs", "rev_atp_cl_sum", "rev_atp_cl_abs")


# ==============================================================================
# PAIRED ROWS
# ==============================================================================

@dataclass
class PairedRow:
    """One instance: the clean prompt, its twin, and where to read them.

    `span` is the half-open clause range shared by both streams, or None when the clean and twin clause spans differ
    in length (the Readout-only fallback). `ref_m_clean` / `ref_m_twin` are the dataset's own stored margins in the
    same orientation as m, for the baseline check; None when the dataset carries none.
    """

    id: str
    split: str
    input_ids: torch.Tensor          # [max_length]
    twin_input_ids: torch.Tensor     # [max_length]
    attention_mask: torch.Tensor     # [max_length], identical for both streams
    readout: int
    span: Optional[Tuple[int, int]]
    target: int
    distractor: int
    ref_m_clean: Optional[float] = None
    ref_m_twin: Optional[float] = None


@dataclass
class PairReport:
    pair: str
    split: str
    source: Dict[str, str]
    n_split: int = 0
    n_rows: int = 0
    without_twin: List[str] = field(default_factory=list)
    dropped_by_tokenization: List[str] = field(default_factory=list)
    clause_fallback: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"pair": self.pair, "split": self.split, "source": self.source, "n_split": self.n_split,
                "n_rows": self.n_rows, "without_twin": self.without_twin,
                "dropped_by_tokenization": self.dropped_by_tokenization, "clause_fallback": self.clause_fallback}


def _neg(value):
    return None if value is None else -float(value)


def dh_pairs(dataset_dir: str, tokenizer, *, split: str) -> Tuple[List[PairedRow], PairReport]:
    """D (the pressure prompt) against its Neutral-Clause Twin H, through the project's loader.

    The loader asserts each twin is clause-aligned (same length, same Readout, every differing token inside the
    clause), so one span serves both streams. The reference margins are the dataset's: D's m is the pressure
    margin with the honest-minus-deceptive sign flipped (`-h_pressure_clean`), H's is `-h_neutral_clean`.
    """
    from component_analysis import dataloaders

    batches = dataloaders.neutral_twin_batches(dataset_dir, tokenizer, split=split, batch_size=10 ** 9)
    report = PairReport(pair="dh", split=split,
                        source={"clean": os.path.abspath(dataset_dir),
                                "twin": batches.report.get("neutral_twin_source") or ""})
    report.n_split = batches.report["n_requested"]
    report.dropped_by_tokenization = list(batches.report["dropped_by_tokenization"])
    report.without_twin = list(batches.report.get("without_neutral_twin", []))
    rows: List[PairedRow] = []
    for batch in batches:
        twin = batch.neutral_twin
        if twin is None:
            continue
        for k, row in enumerate(twin.rows):
            record = batch.records[row]
            start, end = (int(v) for v in twin.clause_span[k])
            rows.append(PairedRow(
                id=batch.ids[row], split=split, input_ids=batch.input_ids[row],
                twin_input_ids=twin.input_ids[k], attention_mask=batch.attention_mask[row],
                readout=int(batch.readout[row]), span=(start, end),
                target=int(batch.target_token[row]), distractor=int(batch.distractor_token[row]),
                ref_m_clean=_neg(record.get("h_pressure_clean")), ref_m_twin=_neg(record.get("h_neutral_clean"))))
    report.n_rows = len(rows)
    return rows, report


def _load_split(directory: str, split: str) -> List[dict]:
    from dataset import deception_common as dc
    return dc.load_or_generate_deception_data(directory, split=split)


def _scores_by_id(directory: str, split: str) -> Dict[str, dict]:
    path = os.path.join(directory, "scores", f"{split}.jsonl")
    out = {}
    if os.path.exists(path):
        with open(path) as handle:
            for line in handle:
                if line.strip():
                    entry = json.loads(line)
                    out[str(entry.get("instance_id"))] = entry
    return out


def in_pairs(inversion_dir: str, neutral_dir: str, tokenizer, *, split: str,
             max_length: Optional[int] = None) -> Tuple[List[PairedRow], PairReport]:
    """The user-turn inversion I against its user-neutral twin N, joined by instance id.

    Asserted per row (a failure raises: a pool that has drifted must stop the run on the login node): equal token
    count and attention mask, Readout = last unpadded position = `readouts["clean"]` of both rows, and every
    differing token inside I's `request_spans["clean"]`. When I's and N's request spans differ in length the row
    keeps the Readout and drops the clause (`clause_fallback`). The labels are I's; the reference margins come from
    the pool's `scores/<split>.jsonl` (`inversion` and `baseline` entries, `opposite_minus_honest`).
    """
    from component_analysis import dataloaders, sampling
    from dataset import deception_common as dc

    config = dc.load_dataset_config(inversion_dir)
    if max_length is None:
        max_length = int(config.get("max_seq_length", dc.MAX_SEQ_LENGTH))
    inv = _load_split(inversion_dir, split)
    neu = {sampling.record_id(r, i): r for i, r in enumerate(_load_split(neutral_dir, split))}
    scores = _scores_by_id(inversion_dir, split)
    report = PairReport(pair="in", split=split,
                        source={"clean": os.path.abspath(inversion_dir), "twin": os.path.abspath(neutral_dir)})
    report.n_split = len(inv)
    rows: List[PairedRow] = []
    for index, record in enumerate(inv):
        one = sampling.record_id(record, index)
        twin = neu.get(one)
        if twin is None:
            report.without_twin.append(one)
            continue
        target = dc.encode_answer_token(tokenizer, record["target"])
        distractor = dc.encode_answer_token(tokenizer, record["distractor"])
        if len(target) != 1 or len(distractor) != 1:
            report.dropped_by_tokenization.append(one)
            continue
        ids, mask = dataloaders._encode(tokenizer, record["clean_prompt"], max_length)
        twin_ids, twin_mask = dataloaders._encode(tokenizer, twin["clean_prompt"], max_length)
        if not torch.equal(mask, twin_mask):
            raise ValueError(f"instance {one}: I and N differ in token count ({int(mask.sum())} vs "
                             f"{int(twin_mask.sum())}); the pair is not aligned")
        readout = int(mask.sum()) - 1
        stated = (record.get("readouts") or {}).get("clean")
        twin_stated = (twin.get("readouts") or {}).get("clean")
        if stated is not None and int(stated) != readout or twin_stated is not None and int(twin_stated) != readout:
            raise ValueError(f"instance {one}: the Readout is {readout} by the attention mask but the pools say "
                             f"{stated} (I) and {twin_stated} (N)")
        span = tuple(int(v) for v in (record.get("request_spans") or {}).get("clean") or ())
        twin_span = tuple(int(v) for v in (twin.get("request_spans") or {}).get("clean") or ())
        if len(span) != 2:
            raise ValueError(f"instance {one}: no request_spans['clean'] on the inversion row")
        differing = torch.nonzero(ids != twin_ids).flatten().tolist()
        outside = [p for p in differing if not span[0] <= p < span[1]]
        if outside:
            raise ValueError(f"instance {one}: I and N differ outside the request span {span}: positions "
                             f"{outside[:8]}")
        use_span: Optional[Tuple[int, int]] = (span[0], span[1])
        if len(twin_span) != 2 or twin_span[1] - twin_span[0] != span[1] - span[0]:
            use_span = None
            report.clause_fallback.append(one)
        entry = scores.get(one) or {}
        ref_clean = ((entry.get("inversion") or {}).get("clean") or {}).get("opposite_minus_honest")
        ref_twin = ((entry.get("baseline") or {}).get("clean") or {}).get("opposite_minus_honest")
        rows.append(PairedRow(id=one, split=split, input_ids=ids, twin_input_ids=twin_ids, attention_mask=mask,
                              readout=readout, span=use_span, target=target[0], distractor=distractor[0],
                              ref_m_clean=None if ref_clean is None else float(ref_clean),
                              ref_m_twin=None if ref_twin is None else float(ref_twin)))
    report.n_rows = len(rows)
    return rows, report


@dataclass
class PairBatch:
    input_ids: torch.Tensor          # [B, T], trimmed to the longest unpadded row
    twin_input_ids: torch.Tensor
    attention_mask: torch.Tensor
    readout: torch.Tensor            # [B]
    clause_mask: torch.Tensor        # [B, T] float32, ones on the clause of rows that have one
    has_clause: torch.Tensor         # [B] bool
    target: torch.Tensor
    distractor: torch.Tensor


def collate(rows: Sequence[PairedRow]) -> PairBatch:
    """Stack rows and trim the right padding every row shares (the prompts are right-padded, so the positions past
    the longest row are padding in every row and cannot change any earlier position under a causal mask)."""
    length = max(int(r.attention_mask.sum()) for r in rows)
    clause = torch.zeros(len(rows), length, dtype=torch.float32)
    has = torch.zeros(len(rows), dtype=torch.bool)
    for i, r in enumerate(rows):
        if r.span is not None:
            clause[i, r.span[0]:r.span[1]] = 1.0
            has[i] = True
    return PairBatch(
        input_ids=torch.stack([r.input_ids[:length] for r in rows]),
        twin_input_ids=torch.stack([r.twin_input_ids[:length] for r in rows]),
        attention_mask=torch.stack([r.attention_mask[:length] for r in rows]),
        readout=torch.tensor([r.readout for r in rows], dtype=torch.long),
        clause_mask=clause, has_clause=has,
        target=torch.tensor([r.target for r in rows], dtype=torch.long),
        distractor=torch.tensor([r.distractor for r in rows], dtype=torch.long))


# ==============================================================================
# HOOKS AND THE METRIC
# ==============================================================================

def decoder_layers(model):
    return model.model.layers


def geometry(model) -> Tuple[int, int]:
    layers = decoder_layers(model)
    return len(layers), int(layers[0].mlp.down_proj.in_features)


class NeuronCapture:
    """Capture every layer's `down_proj` input (the post-SwiGLU hidden neurons) and the final norm's input.

    `grad=True` makes the embedding output require grad, so the captures are in one autograd graph rooted there and
    `torch.autograd.grad(m, capture.acts)` gives each layer's total derivative. The captured tensors are the ones
    `down_proj` consumes, not copies.
    """

    def __init__(self, model, *, grad: bool):
        self.model = model
        self.grad = grad
        self.acts: List[Optional[torch.Tensor]] = []
        self.final: Optional[torch.Tensor] = None
        self.handles = []

    def _embed(self, module, inputs, output):
        if not output.requires_grad:
            return output.requires_grad_(True)
        return output

    def _layer(self, index):
        def pre(module, args):
            self.acts[index] = args[0]
        return pre

    def _norm(self, module, args):
        self.final = args[0]

    def __enter__(self):
        layers = decoder_layers(self.model)
        self.acts = [None] * len(layers)
        if self.grad:
            self.handles.append(self.model.model.embed_tokens.register_forward_hook(self._embed))
        for index, layer in enumerate(layers):
            self.handles.append(layer.mlp.down_proj.register_forward_pre_hook(self._layer(index)))
        self.handles.append(self.model.model.norm.register_forward_pre_hook(self._norm))
        return self

    def __exit__(self, *exc):
        for handle in self.handles:
            handle.remove()
        self.handles = []
        return False


@contextlib.contextmanager
def shift_neuron(model, *, layer: int, index: int, position, delta):
    """Add `delta[b]` to neuron `index` of `layer` at `position[b]` in every row b of the next forwards.

    The finite-difference reference for the AtP test (and a one-neuron activation patch when `delta` is the twin
    value minus the clean value).
    """
    def pre(module, args):
        x = args[0].clone()
        rows = torch.arange(x.shape[0], device=x.device)
        pos = torch.as_tensor(position, device=x.device).long()
        x[rows, pos, index] = x[rows, pos, index] + torch.as_tensor(delta, device=x.device, dtype=x.dtype)
        return (x,) + tuple(args[1:])

    handle = decoder_layers(model)[layer].mlp.down_proj.register_forward_pre_hook(pre)
    try:
        yield
    finally:
        handle.remove()


def _work_dtype(tensor):
    """float32 for the bf16/fp16/fp32 model; float64 only when the model itself runs in float64 (the tests)."""
    return torch.float64 if tensor.dtype == torch.float64 else torch.float32


def readout_metric(model, final_residual, readout, target, distractor):
    """m = logit(Target) - logit(Distractor) per row, fp32, through the real final RMSNorm, differentiable.

    `final_residual` is the final norm's input [B, T, hidden]. Only the two unembedding rows are used, so the full
    vocabulary is never materialized.
    """
    norm = model.model.norm
    eps = getattr(norm, "variance_epsilon", None)
    if eps is None:
        eps = getattr(norm, "eps", 1e-5)
    work = _work_dtype(final_residual)
    rows = torch.arange(final_residual.shape[0], device=final_residual.device)
    hidden = final_residual[rows, readout.to(final_residual.device)].to(work)
    scaled = hidden * torch.rsqrt(hidden.pow(2).mean(-1, keepdim=True) + eps) * norm.weight.to(work)
    unembed = model.lm_head.weight
    direction = (unembed[target.to(unembed.device)].to(work) - unembed[distractor.to(unembed.device)].to(work))
    return (scaled * direction.to(scaled.device)).sum(-1)


def _forward(model, input_ids, attention_mask):
    model.model(input_ids=input_ids, attention_mask=attention_mask, use_cache=False)


def run_metric(model, input_ids, attention_mask, readout, target, distractor):
    """m per row on the plain model (no grad), for checks and tests."""
    with torch.no_grad(), NeuronCapture(model, grad=False) as cap:
        _forward(model, input_ids, attention_mask)
        return readout_metric(model, cap.final, readout, target, distractor)


# ==============================================================================
# ACCUMULATION
# ==============================================================================

class Accumulator:
    """Running float64 sums per neuron over rows, on the model's device."""

    def __init__(self, n_layers: int, width: int, device, *, reverse: bool = False):
        self.reverse = reverse
        keys = READOUT_SUMS + CLAUSE_SUMS + (REVERSE_SUMS if reverse else ())
        self.sums = {k: torch.zeros(n_layers, width, dtype=torch.float64, device=device) for k in keys}
        self.n_readout = 0
        self.n_clause = 0

    def add(self, layer: int, key: str, values: torch.Tensor):
        """`values` is [rows, width]; summed over rows into `key`'s layer slice."""
        if values.shape[0]:
            self.sums[key][layer] += values.double().sum(0)

    def finalize(self) -> Dict[str, torch.Tensor]:
        out = {}
        s = self.sums
        if self.n_readout:
            n = float(self.n_readout)
            out["atp_readout_mean"] = s["atp_ro_sum"] / n
            out["atp_readout_absmean"] = s["atp_ro_abs"] / n
            out["contrast_readout_mean"] = s["diff_ro_sum"] / n
            out["contrast_readout_std"] = out["contrast_readout_mean"] / (_std(s["twin_ro_sum"], s["twin_ro_sq"], n)
                                                                          + STD_EPS)
            if self.reverse:
                out["rev_atp_readout_mean"] = s["rev_atp_ro_sum"] / n
                out["rev_atp_readout_absmean"] = s["rev_atp_ro_abs"] / n
        if self.n_clause:
            n = float(self.n_clause)
            out["atp_clause_mean"] = s["atp_cl_sum"] / n
            out["atp_clause_absmean"] = s["atp_cl_abs"] / n
            out["contrast_clause_mean"] = s["diff_cl_sum"] / n
            out["contrast_clause_std"] = out["contrast_clause_mean"] / (_std(s["twin_cl_sum"], s["twin_cl_sq"], n)
                                                                        + STD_EPS)
            if self.reverse:
                out["rev_atp_clause_mean"] = s["rev_atp_cl_sum"] / n
                out["rev_atp_clause_absmean"] = s["rev_atp_cl_abs"] / n
        return {k: v.float().cpu() for k, v in out.items()}


def _std(total, squares, n):
    """Population standard deviation (ddof 0, numpy's default) from running sums."""
    mean = total / n
    return (squares / n - mean * mean).clamp_min(0.0).sqrt()


def score_batch(model, batch: PairBatch, acc: Accumulator) -> Tuple[torch.Tensor, torch.Tensor]:
    """Run the clean forward with grad and the twin forward, add this batch to `acc`; -> (m_clean, m_twin) on CPU."""
    device = next(model.parameters()).device
    ids = batch.input_ids.to(device)
    twin_ids = batch.twin_input_ids.to(device)
    mask = batch.attention_mask.to(device)
    readout = batch.readout.to(device)
    target, distractor = batch.target.to(device), batch.distractor.to(device)

    with torch.enable_grad(), NeuronCapture(model, grad=True) as clean:
        _forward(model, ids, mask)
        m_clean = readout_metric(model, clean.final, readout, target, distractor)
        grads = torch.autograd.grad(m_clean.sum(), clean.acts)
    clean_acts = [a.detach() for a in clean.acts]
    clean.acts, clean.final = [], None

    if acc.reverse:
        with torch.enable_grad(), NeuronCapture(model, grad=True) as twin:
            _forward(model, twin_ids, mask)
            m_twin = readout_metric(model, twin.final, readout, target, distractor)
            twin_grads = torch.autograd.grad(m_twin.sum(), twin.acts)
        twin_acts = [a.detach() for a in twin.acts]
    else:
        with torch.no_grad(), NeuronCapture(model, grad=False) as twin:
            _forward(model, twin_ids, mask)
            m_twin = readout_metric(model, twin.final, readout, target, distractor)
        twin_acts, twin_grads = twin.acts, None
    twin.acts, twin.final = [], None

    rows = torch.arange(ids.shape[0], device=device)
    clause = batch.clause_mask.to(device)
    has = batch.has_clause.to(device)
    work = _work_dtype(clean_acts[0])
    for layer in range(len(clean_acts)):
        a_c = clean_acts[layer].to(work)
        a_t = twin_acts[layer].to(work)
        g = grads[layer].to(work)
        diff = a_c - a_t
        diff_ro = diff[rows, readout]
        twin_ro = a_t[rows, readout]
        atp_ro = diff_ro * g[rows, readout]
        acc.add(layer, "atp_ro_sum", atp_ro)
        acc.add(layer, "atp_ro_abs", atp_ro.abs())
        acc.add(layer, "diff_ro_sum", diff_ro)
        acc.add(layer, "twin_ro_sum", twin_ro)
        acc.add(layer, "twin_ro_sq", twin_ro * twin_ro)
        if bool(has.any()):
            weight = clause.unsqueeze(-1)
            atp_cl = (diff * g * weight).sum(1)[has]
            twin_cl = (a_t * weight).sum(1)[has]
            acc.add(layer, "atp_cl_sum", atp_cl)
            acc.add(layer, "atp_cl_abs", atp_cl.abs())
            acc.add(layer, "diff_cl_sum", (diff * weight).sum(1)[has])
            acc.add(layer, "twin_cl_sum", twin_cl)
            acc.add(layer, "twin_cl_sq", twin_cl * twin_cl)
        if twin_grads is not None:
            g_t = twin_grads[layer].to(work)
            rev_ro = -diff_ro * g_t[rows, readout]
            acc.add(layer, "rev_atp_ro_sum", rev_ro)
            acc.add(layer, "rev_atp_ro_abs", rev_ro.abs())
            if bool(has.any()):
                rev_cl = (-diff * g_t * clause.unsqueeze(-1)).sum(1)[has]
                acc.add(layer, "rev_atp_cl_sum", rev_cl)
                acc.add(layer, "rev_atp_cl_abs", rev_cl.abs())
        del a_c, a_t, g, diff
    acc.n_readout += int(ids.shape[0])
    acc.n_clause += int(has.sum())
    return m_clean.detach().double().cpu(), m_twin.detach().double().cpu()


def score_rows(model, rows: Sequence[PairedRow], *, batch_size: int, reverse: bool = False,
               progress=None) -> Tuple[Dict[str, torch.Tensor], dict]:
    """Score every row; -> (scores {name: float32 [layers, width]}, per-row record with timing)."""
    import time

    n_layers, width = geometry(model)
    device = next(model.parameters()).device
    acc = Accumulator(n_layers, width, device, reverse=reverse)
    m_clean: List[float] = []
    m_twin: List[float] = []
    sync = torch.cuda.synchronize if device.type == "cuda" else (lambda: None)
    sync()
    started = time.perf_counter()
    n_batches = int(math.ceil(len(rows) / batch_size)) if rows else 0
    for b, start in enumerate(range(0, len(rows), batch_size)):
        mc, mt = score_batch(model, collate(rows[start:start + batch_size]), acc)
        m_clean.extend(mc.tolist())
        m_twin.extend(mt.tolist())
        if progress is not None:
            progress(b + 1, n_batches)
    sync()
    seconds = time.perf_counter() - started
    record = {
        "n_rows": len(rows), "n_readout_rows": acc.n_readout, "n_clause_rows": acc.n_clause,
        "ids": [f"{r.split}/{r.id}" for r in rows],
        "m_clean": m_clean, "m_twin": m_twin,
        "ref_m_clean": [r.ref_m_clean for r in rows], "ref_m_twin": [r.ref_m_twin for r in rows],
        "clause_fallback_ids": [f"{r.split}/{r.id}" for r in rows if r.span is None],
        "scoring_seconds": seconds,
        "seconds_per_row": seconds / len(rows) if rows else None,
        "batch_size": batch_size, "reverse": reverse,
    }
    return acc.finalize(), record


# ==============================================================================
# THE BASELINE CHECK
# ==============================================================================

def baseline_summary(record: dict, margin: float = 0.7) -> dict:
    """The one-line checks the orchestrator reads: m's sign and margin rates, and agreement with the stored margins."""
    out = {}
    for stream in ("m_clean", "m_twin"):
        values = record[stream]
        if not values:
            continue
        n = len(values)
        out[stream] = {"mean": sum(values) / n,
                       "frac_gt_0": sum(v > 0 for v in values) / n,
                       f"frac_gt_{margin}": sum(v > margin for v in values) / n,
                       f"frac_lt_-{margin}": sum(v < -margin for v in values) / n}
        refs = [(v, r) for v, r in zip(values, record["ref_" + stream]) if r is not None]
        if refs:
            diffs = [abs(v - r) for v, r in refs]
            out[stream]["vs_stored_margin"] = {
                "n": len(refs), "mean_abs_diff": sum(diffs) / len(diffs), "max_abs_diff": max(diffs),
                "pearson": _pearson([v for v, _ in refs], [r for _, r in refs]),
                "sign_agreement": sum((v > 0) == (r > 0) for v, r in refs) / len(refs)}
    return out


def _pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


# ==============================================================================
# OUTPUT
# ==============================================================================

def write_outputs(output_dir: str, scores: Dict[str, torch.Tensor], record: dict, *, reports: Sequence[dict],
                  pools: dict, extra: Optional[dict] = None) -> Dict[str, str]:
    """`scores.pt` (float32 tensors by name) and `rows.json` (ids, m_clean, m_twin, counts, baseline, pools)."""
    os.makedirs(output_dir, exist_ok=True)
    scores_path = os.path.join(output_dir, "scores.pt")
    torch.save({k: v.float().contiguous() for k, v in scores.items()}, scores_path)
    rows = dict(record)
    rows["baseline"] = baseline_summary(record)
    rows["loader_reports"] = list(reports)
    rows["pools"] = pools
    rows.update(extra or {})
    rows_path = os.path.join(output_dir, "rows.json")
    with open(rows_path, "w") as handle:
        json.dump(rows, handle, indent=1)
    return {"scores": scores_path, "rows": rows_path}


def write_manifest(output_dir: str, *, notes: Sequence[str], **kwargs) -> str:
    """`run_manifest.py`'s record plus a `notes` list, hashed with the notes in, written without overwriting."""
    import run_manifest as rm

    manifest = rm.build_run_manifest(**kwargs)
    manifest.pop("manifest_hash", None)
    manifest["notes"] = list(notes)
    manifest = json.loads(json.dumps(manifest, default=str))
    manifest["manifest_hash"] = rm.manifest_hash(manifest)
    text = rm.render(manifest)
    os.makedirs(output_dir, exist_ok=True)
    n = 0
    while True:
        path = os.path.join(output_dir, rm.FILENAME if n == 0 else "run_manifest.%d.json" % n)
        try:
            with open(path, "x") as handle:
                handle.write(text)
            return path
        except FileExistsError:
            n += 1
