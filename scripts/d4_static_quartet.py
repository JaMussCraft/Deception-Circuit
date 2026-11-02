#!/usr/bin/env python
"""D4(d): a static QK/OV read of the layer-17 quartet L17H24 to L17H27 (direction deception-divergence, U2 as
approved; the rule is `docs/research/deception-divergence/spec.md`, D4 rules, P1 and P2). CPU only.

Only the weight matrices the scores need are read, lazily, from the model's safetensors shards (resolved from the
local Hugging Face cache by the id `models/__init__.py` gives `llama-8b-instruct`), so the run fits on a login node.

Conventions (row vectors, x a residual-stream vector; TransformerLens's "fold LN" convention):

- Grouped-query attention: 32 query heads, 8 key/value groups of 128 dims, head h reads KV group g = h // 4. The
  quartet heads 24 to 27 all read group 6; W_Q is per head.
- A head's OV circuit, written in the residual stream: W_OV^h = diag(gamma_in^L) W_V^{g(h)T} W_O^{hT}, where
  gamma_in^L is the sending layer's `input_layernorm.weight` (folded) and W_O^h is the 128 columns of `o_proj` that
  head h writes. The per-token RMS divisor is a positive scalar and is not folded (the known limitation of any static
  read).
- A head's query map: W_Q^h folded = diag(gamma_in^17) W_Q^{hT} (d_model x 128). "The quartet's W_Q" is the four
  heads stacked, d_model x 512.

**P1 (query side).** The Q-composition score of sender head A (layers 7 to 16, 320 heads) into the quartet, in the
Elhage et al. (2021) normalised Frobenius form with the quartet's W_Q as the reading matrix:

    s(A) = || W_OV^A W_Q^quartet ||_F / ( || W_OV^A ||_F || W_Q^quartet ||_F ).

This is the rule score of record: the spec names "the quartet's W_Q", and the form is exactly invariant to RoPE, which
right-multiplies the query by an orthogonal matrix. Reported beside it and deciding nothing: the per-head score into
each quartet head's own W_Q, and the literal Elhage Q-composition into each head's W_QK = W_Q^h W_K^{g T} (both sides
folded), which RoPE does not leave invariant. The rule: head.15.8 and head.14.4 each rank within the top 5 percent of
the 320 scores (rank <= ceil(0.05 x 320) = 16), and the layer-14 and layer-15 sums of s each exceed the sum of every
other layer from 7 to 16. The random baseline is 20 seeded draws of four heads from the 28 non-quartet layer-17
heads (layer-matched, the B2 convention), each read with the same rule.

**P2 (copy).** The OV copy score of Wang et al. (2022) against the item unembeddings. Item tokens are the first answer
token (`dataset.deception_common.encode_answer_token`, leading space, as the loaders use it) of every `target` and
`distractor` of the far_v2, sdr_v2 and ser_v2 test splits, multi-token items dropped as the loaders drop them,
deduplicated. For head h and item token t: logits = W_U diag(gamma_final) W_OV^{hT} e_t (the final RMSNorm scale
folded into W_U, the RMS divisor rank-neutral), and the own-logit rank is 1 + the number of vocabulary logits strictly
above logit_t. The copy score is the fraction of item tokens with rank <= 5; the mean own-logit rank is reported
beside. The rule: at least 2 of the 4 quartet heads reach a copy score of 0.5. Baseline: 20 seeded non-quartet
layer-17 heads. Beside, deciding nothing: the same score with the item embedding first passed through mlp.0 (e +
MLP0(RMSNorm(e))), the variant Wang et al. used on GPT-2; and the ceiling of the read, the identity map (embedding
straight to the unembedding) and the copy score of every one of the 1,024 heads, so that a fail can be told apart
from a read no head of this model passes.

Writes `<out>/static_quartet.json`, `<out>/static_quartet.md` and `<out>/run_manifest.json`.

    OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 python scripts/d4_static_quartet.py \\
        --out outputs/_analyses/deception-divergence/d4d
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCHEMA = "d4_static_quartet/1"
MODEL_KEY = "llama-8b-instruct"

N_HEADS = 32
N_KV = 8
D_HEAD = 128
GROUP_SIZE = N_HEADS // N_KV

QUARTET_LAYER = 17
QUARTET_HEADS = (24, 25, 26, 27)
QUARTET_KV_GROUP = 6
SENDER_LAYERS = tuple(range(7, 17))
NAMED_SENDERS = ((15, 8), (14, 4))
NAMED_LAYERS = (14, 15)
TOP_FRACTION = 0.05

COPY_TOP_K = 5
COPY_BAR = 0.5
COPY_HEADS_NEEDED = 2

N_RANDOM = 20
RANDOM_SEED = 20261102

TASKS = ("far_v2", "sdr_v2", "ser_v2")
ITEM_SPLIT = "test"
LOGIT_CHUNK = 256


def head_name(layer: int, head: int) -> str:
    return f"head.{layer}.{head}"


def kv_group(head: int) -> int:
    return head // GROUP_SIZE


# ==============================================================================
# Lazy weights
# ==============================================================================

def resolve_snapshot(model_id: str) -> str:
    """The local snapshot directory of `model_id`, from the Hugging Face cache only (no download).

    Resolved through the cached weight index rather than `snapshot_download`, which on huggingface_hub 1.x refuses
    a snapshot that lacks the repository's non-weight files (README, LICENSE)."""
    from huggingface_hub import try_to_load_from_cache

    index = try_to_load_from_cache(model_id, "model.safetensors.index.json")
    if not isinstance(index, str) or not os.path.isfile(index):
        raise FileNotFoundError(f"{model_id}: model.safetensors.index.json is not in the local Hugging Face cache")
    return os.path.dirname(index)


class LazyWeights:
    """Reads single tensors (or row ranges) from a sharded safetensors checkpoint on demand."""

    def __init__(self, snapshot: str):
        self.snapshot = snapshot
        with open(os.path.join(snapshot, "model.safetensors.index.json")) as handle:
            self.weight_map: Dict[str, str] = json.load(handle)["weight_map"]
        self._open: Dict[str, object] = {}
        self.read: Dict[str, List[int]] = {}

    def _handle(self, shard: str):
        from safetensors import safe_open

        if shard not in self._open:
            self._open[shard] = safe_open(os.path.join(self.snapshot, shard), framework="pt")
        return self._open[shard]

    def shard_of(self, name: str) -> str:
        if name not in self.weight_map:
            raise KeyError(f"{name} is not in the checkpoint index")
        return self.weight_map[name]

    def get(self, name: str, rows: Optional[Sequence[int]] = None, dtype=torch.float64) -> torch.Tensor:
        shard = self.shard_of(name)
        handle = self._handle(shard)
        if rows is None:
            tensor = handle.get_tensor(name)
        else:
            part = handle.get_slice(name)
            tensor = torch.stack([part[int(r):int(r) + 1][0] for r in rows])
        self.read[name] = list(tensor.shape)
        return tensor.to(dtype)

    def shards_used(self) -> List[str]:
        return sorted({self.weight_map[name] for name in self.read})


def shard_lfs_sha256(snapshot: str, shard: str) -> Optional[str]:
    """The sha256 the Hugging Face cache names the shard's blob by (LFS files are stored under their sha256)."""
    path = os.path.realpath(os.path.join(snapshot, shard))
    name = os.path.basename(path)
    return name if len(name) == 64 and all(c in "0123456789abcdef" for c in name) else None


def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 24), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ==============================================================================
# Factors (pure)
# ==============================================================================

def ov_factors(w_v: torch.Tensor, w_o: torch.Tensor, gamma: torch.Tensor, head: int,
               d_head: int = D_HEAD, group_size: int = GROUP_SIZE) -> Tuple[torch.Tensor, torch.Tensor]:
    """(A, B) with W_OV = A @ B in the row convention (x W_OV): A = diag(gamma) W_V^{gT} (d x r), B = W_O^{hT} (r x d).

    `w_v` is `v_proj.weight` [n_kv * d_head, d], `w_o` is `o_proj.weight` [d, n_heads * d_head]."""
    g = head // group_size
    v = w_v[g * d_head:(g + 1) * d_head]                      # [r, d]
    a = gamma[:, None] * v.T                                   # [d, r]
    b = w_o[:, head * d_head:(head + 1) * d_head].T            # [r, d]
    return a, b


def q_factor(w_q: torch.Tensor, gamma: torch.Tensor, heads: Iterable[int], d_head: int = D_HEAD) -> torch.Tensor:
    """diag(gamma) W_Q^T for the given heads, stacked along the output: [d, r * len(heads)]."""
    rows = torch.cat([w_q[h * d_head:(h + 1) * d_head] for h in heads])
    return gamma[:, None] * rows.T


def k_factor(w_k: torch.Tensor, gamma: torch.Tensor, head: int, d_head: int = D_HEAD,
             group_size: int = GROUP_SIZE) -> torch.Tensor:
    """W_K^{g} diag(gamma): [r, d], so that W_QK^h = q_factor(h) @ k_factor(h) (x_q W_QK x_k^T)."""
    g = head // group_size
    return w_k[g * d_head:(g + 1) * d_head] * gamma[None, :]


def _fro2_lowrank(left: torch.Tensor, middle: torch.Tensor, right: torch.Tensor) -> float:
    """||left @ middle @ right||_F^2 through r x r Gram matrices: tr((L^T L) M (R R^T) M^T)."""
    gl = left.T @ left
    gr = right @ right.T
    return float(torch.trace(gl @ middle @ gr @ middle.T))


def ov_norm(a: torch.Tensor, b: torch.Tensor) -> float:
    return math.sqrt(float(torch.trace((a.T @ a) @ (b @ b.T))))


def q_composition(a: torch.Tensor, b: torch.Tensor, qf: torch.Tensor) -> float:
    """||W_OV W_Q|| / (||W_OV|| ||W_Q||), W_OV = a @ b, W_Q = qf (d x m)."""
    bq = b @ qf                                                # [r, m]
    num = math.sqrt(float(torch.trace((a.T @ a) @ (bq @ bq.T))))
    return num / (ov_norm(a, b) * float(torch.linalg.norm(qf)))


def qk_composition(a: torch.Tensor, b: torch.Tensor, qf: torch.Tensor, kf: torch.Tensor) -> float:
    """Elhage Q-composition ||W_OV W_QK|| / (||W_OV|| ||W_QK||), W_QK = qf @ kf."""
    num = math.sqrt(_fro2_lowrank(a, b @ qf, kf))
    qk = math.sqrt(float(torch.trace((qf.T @ qf) @ (kf @ kf.T))))
    return num / (ov_norm(a, b) * qk)


def dense_q_composition(w_ov: torch.Tensor, w_q: torch.Tensor) -> float:
    """The same score from full matrices; tests and the run's spot check."""
    return float(torch.linalg.norm(w_ov @ w_q) / (torch.linalg.norm(w_ov) * torch.linalg.norm(w_q)))


def own_logit_ranks(resid: torch.Tensor, token_ids: Sequence[int], gamma_final: torch.Tensor,
                    w_u: torch.Tensor, chunk: int = LOGIT_CHUNK) -> List[int]:
    """Rank of each row's own token among all vocabulary logits of (resid * gamma_final) @ W_U^T (1 = top).

    `resid` is [n, d] (already through the head's OV); the RMS divisor of the final norm is a positive per-row scalar
    and does not change a rank, so it is left out."""
    ranks: List[int] = []
    ids = torch.as_tensor(list(token_ids), dtype=torch.long)
    w_u = w_u.to(torch.float32)
    for start in range(0, resid.shape[0], chunk):
        x = (resid[start:start + chunk] * gamma_final[None, :]).to(torch.float32)
        logits = x @ w_u.T                                     # [c, vocab]
        own = logits.gather(1, ids[start:start + chunk, None])
        ranks.extend((1 + (logits > own).sum(1)).tolist())
    return [int(r) for r in ranks]


def copy_summary(ranks: Sequence[int], k: int = COPY_TOP_K) -> dict:
    arr = np.asarray(ranks, dtype=float)
    return {"n_items": int(arr.size), "copy_score": float((arr <= k).mean()) if arr.size else None,
            "mean_own_rank": float(arr.mean()) if arr.size else None,
            "median_own_rank": float(np.median(arr)) if arr.size else None}


def rms_norm(x: torch.Tensor, gamma: torch.Tensor, eps: float) -> torch.Tensor:
    return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + eps) * gamma[None, :]


# ==============================================================================
# Readings (pure)
# ==============================================================================

def top_rank_cutoff(n: int, fraction: float = TOP_FRACTION) -> int:
    return int(math.ceil(fraction * n))


def ranking(scores: Dict[str, float]) -> List[Tuple[str, float]]:
    """Descending by score, ties broken by name so the order is reproducible."""
    return sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))


def p1_reading(scores: Dict[str, float], *, named: Sequence[str], named_layers: Sequence[int],
               layers: Sequence[int], fraction: float = TOP_FRACTION) -> dict:
    """The P1 rule on one set of sender scores {head.L.H: s}."""
    order = ranking(scores)
    rank_of = {name: i + 1 for i, (name, _s) in enumerate(order)}
    cutoff = top_rank_cutoff(len(scores), fraction)
    sums = {int(L): float(sum(s for name, s in scores.items() if int(name.split(".")[1]) == L)) for L in layers}
    others = {L: v for L, v in sums.items() if L not in named_layers}
    layer_pass = {int(L): bool(all(sums[L] > v for v in others.values())) for L in named_layers}
    named_pass = {name: bool(rank_of[name] <= cutoff) for name in named}
    return {"n_senders": len(scores), "top_rank_cutoff": cutoff, "top_fraction": fraction,
            "named_ranks": {name: rank_of[name] for name in named},
            "named_scores": {name: scores[name] for name in named},
            "named_in_top": named_pass, "layer_sums": {str(L): v for L, v in sums.items()},
            "layer_sum_order": [int(L) for L, _v in sorted(sums.items(), key=lambda kv: -kv[1])],
            "named_layers_exceed_every_other": {str(L): v for L, v in layer_pass.items()},
            "pass": bool(all(named_pass.values()) and all(layer_pass.values()))}


def p2_reading(copy_scores: Dict[str, float], bar: float = COPY_BAR, needed: int = COPY_HEADS_NEEDED) -> dict:
    reaching = sorted(name for name, s in copy_scores.items() if s is not None and s >= bar)
    return {"bar": bar, "heads_needed": needed, "heads_reaching": reaching, "n_reaching": len(reaching),
            "pass": len(reaching) >= needed}


def random_heads(layer: int, exclude: Sequence[int], n: int, size: int, seed: int) -> List[List[int]]:
    """n seeded draws of `size` distinct heads of `layer`, none in `exclude`."""
    pool = [h for h in range(N_HEADS) if h not in set(exclude)]
    rng = np.random.default_rng(seed)
    return [sorted(int(h) for h in rng.choice(pool, size=size, replace=False)) for _ in range(n)]


# ==============================================================================
# Items
# ==============================================================================

def item_tokens(tokenizer, tasks: Sequence[str] = TASKS, split: str = ITEM_SPLIT) -> dict:
    """{per_task: {task: {n_records, n_strings, n_single_token, n_dropped_multi, token_ids}}, token_ids: pooled}."""
    from dataset import deception_common as dc

    per_task, pooled = {}, []
    for task in tasks:
        records = dc.load_or_generate_deception_data(str(ROOT / "data" / "datasets" / task), split=split)
        strings = sorted({str(r[field]) for r in records for field in ("target", "distractor")})
        ids, dropped = [], []
        for s in strings:
            enc = dc.encode_answer_token(tokenizer, s)
            if len(enc) == 1:
                ids.append(int(enc[0]))
            else:
                dropped.append(s)
        ids = sorted(set(ids))
        per_task[task] = {"n_records": len(records), "n_strings": len(strings), "n_single_token": len(ids),
                          "n_dropped_multi_token": len(dropped), "dropped_examples": dropped[:5], "token_ids": ids}
        pooled.extend(ids)
    return {"split": split, "per_task": per_task, "token_ids": sorted(set(pooled))}


# ==============================================================================
# Run
# ==============================================================================

def layer_name(layer: int, part: str) -> str:
    return f"model.layers.{layer}.{part}"


def run(out_dir: str, *, verify_hashes: bool = False, n_random: int = N_RANDOM, seed: int = RANDOM_SEED) -> dict:
    from models import MODEL_REGISTRY

    started = time.time()
    model_id = MODEL_REGISTRY[MODEL_KEY][0]
    snapshot = resolve_snapshot(model_id)
    with open(os.path.join(snapshot, "config.json")) as handle:
        config = json.load(handle)
    assert config["num_attention_heads"] == N_HEADS and config["num_key_value_heads"] == N_KV
    assert config["hidden_size"] // N_HEADS == D_HEAD
    assert all(kv_group(h) == QUARTET_KV_GROUP for h in QUARTET_HEADS)
    eps = float(config["rms_norm_eps"])
    w = LazyWeights(snapshot)
    checks: Dict[str, object] = {}

    # ---------------- receivers: the quartet and the random layer-17 draws
    w_q17 = w.get(layer_name(QUARTET_LAYER, "self_attn.q_proj.weight"))
    w_k17 = w.get(layer_name(QUARTET_LAYER, "self_attn.k_proj.weight"))
    w_v17 = w.get(layer_name(QUARTET_LAYER, "self_attn.v_proj.weight"))
    w_o17 = w.get(layer_name(QUARTET_LAYER, "self_attn.o_proj.weight"))
    g17 = w.get(layer_name(QUARTET_LAYER, "input_layernorm.weight"))
    d = config["hidden_size"]
    checks["shapes"] = {"q_proj": list(w_q17.shape), "k_proj": list(w_k17.shape), "v_proj": list(w_v17.shape),
                        "o_proj": list(w_o17.shape)}
    assert list(w_q17.shape) == [N_HEADS * D_HEAD, d] and list(w_o17.shape) == [d, N_HEADS * D_HEAD]
    assert list(w_k17.shape) == [N_KV * D_HEAD, d] and list(w_v17.shape) == [N_KV * D_HEAD, d]
    checks["quartet_kv_group"] = {h: kv_group(h) for h in QUARTET_HEADS}

    p1_random_draws = random_heads(QUARTET_LAYER, QUARTET_HEADS, n_random, len(QUARTET_HEADS), seed)
    p2_random_heads = random_heads(QUARTET_LAYER, QUARTET_HEADS, 1, n_random, seed + 1)[0]

    quartet_q = q_factor(w_q17, g17, QUARTET_HEADS)
    head_q = {h: q_factor(w_q17, g17, [h]) for h in QUARTET_HEADS}
    head_k = {h: k_factor(w_k17, g17, h) for h in QUARTET_HEADS}
    random_q = [q_factor(w_q17, g17, draw) for draw in p1_random_draws]

    # ---------------- senders: every head of layers 7 to 16
    stacked: Dict[str, float] = {}
    per_head: Dict[int, Dict[str, float]] = {h: {} for h in QUARTET_HEADS}
    qk: Dict[int, Dict[str, float]] = {h: {} for h in QUARTET_HEADS}
    rand_scores: List[Dict[str, float]] = [dict() for _ in p1_random_draws]
    spot = None
    for L in SENDER_LAYERS:
        w_v = w.get(layer_name(L, "self_attn.v_proj.weight"))
        w_o = w.get(layer_name(L, "self_attn.o_proj.weight"))
        g = w.get(layer_name(L, "input_layernorm.weight"))
        for h in range(N_HEADS):
            name = head_name(L, h)
            a, b = ov_factors(w_v, w_o, g, h)
            stacked[name] = q_composition(a, b, quartet_q)
            for qh in QUARTET_HEADS:
                per_head[qh][name] = q_composition(a, b, head_q[qh])
                qk[qh][name] = qk_composition(a, b, head_q[qh], head_k[qh])
            for i, rq in enumerate(random_q):
                rand_scores[i][name] = q_composition(a, b, rq)
            if (L, h) == NAMED_SENDERS[0]:
                dense = dense_q_composition(a @ b, quartet_q)
                spot = {"sender": name, "low_rank": stacked[name], "dense": dense,
                        "abs_diff": abs(dense - stacked[name])}
        del w_v, w_o
    checks["dense_spot_check"] = spot
    assert spot is not None and spot["abs_diff"] < 1e-9, spot

    named = [head_name(L, h) for L, h in NAMED_SENDERS]
    p1 = {"score_of_record": "stacked quartet W_Q (d x 512), RMSNorm gammas folded",
          "rule": p1_reading(stacked, named=named, named_layers=NAMED_LAYERS, layers=SENDER_LAYERS),
          "ranking": [{"sender": n, "score": s} for n, s in ranking(stacked)],
          "beside": {"per_head_W_Q": {head_name(QUARTET_LAYER, h): p1_reading(
                         per_head[h], named=named, named_layers=NAMED_LAYERS, layers=SENDER_LAYERS)
                         for h in QUARTET_HEADS},
                     "per_head_W_QK_elhage": {head_name(QUARTET_LAYER, h): p1_reading(
                         qk[h], named=named, named_layers=NAMED_LAYERS, layers=SENDER_LAYERS)
                         for h in QUARTET_HEADS}}}
    baseline = []
    for draw, scores in zip(p1_random_draws, rand_scores):
        reading = p1_reading(scores, named=named, named_layers=NAMED_LAYERS, layers=SENDER_LAYERS)
        baseline.append({"heads": [head_name(QUARTET_LAYER, h) for h in draw], "pass": reading["pass"],
                         "named_ranks": reading["named_ranks"], "named_scores": reading["named_scores"],
                         "layer_sum_order": reading["layer_sum_order"]})
    p1["random_baseline"] = {
        "kind": f"{n_random} seeded draws of 4 non-quartet layer-{QUARTET_LAYER} heads (seed {seed})",
        "n_pass": sum(1 for b in baseline if b["pass"]), "draws": baseline,
        "named_score_vs_draws": {n: {"quartet": stacked[n],
                                     "draw_max": max(b["named_scores"][n] for b in baseline),
                                     "draw_mean": float(np.mean([b["named_scores"][n] for b in baseline])),
                                     "n_draws_at_or_above": sum(1 for b in baseline
                                                                if b["named_scores"][n] >= stacked[n])}
                                 for n in named}}

    # ---------------- P2: copy scores
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(snapshot)
    items = item_tokens(tokenizer)
    ids = items["token_ids"]
    emb = w.get("model.embed_tokens.weight", rows=ids)                 # [n, d]
    w_u = w.get("lm_head.weight", dtype=torch.float32)                 # [vocab, d]
    g_final = w.get("model.norm.weight")
    checks["lm_head_shape"] = list(w_u.shape)
    checks["lm_head_fro_norm"] = float(torch.linalg.norm(w_u))
    # mlp.0 for the beside variant (Wang et al.'s residual after the first MLP)
    g_post0 = w.get(layer_name(0, "post_attention_layernorm.weight"))
    gate0 = w.get(layer_name(0, "mlp.gate_proj.weight"), dtype=torch.float32)
    up0 = w.get(layer_name(0, "mlp.up_proj.weight"), dtype=torch.float32)
    down0 = w.get(layer_name(0, "mlp.down_proj.weight"), dtype=torch.float32)
    x0 = rms_norm(emb, g_post0, eps).to(torch.float32)
    hidden0 = torch.nn.functional.silu(x0 @ gate0.T) * (x0 @ up0.T)    # [n, d_mlp]
    emb_mlp0 = emb + (hidden0 @ down0.T).to(torch.float64)
    del gate0, up0, down0

    def head_copy(h: int, base: torch.Tensor) -> List[int]:
        a, b = ov_factors(w_v17, w_o17, g17, h)
        resid = rms_norm(base, torch.ones_like(g17), eps) @ a @ b      # the sending norm's divisor, then OV
        return own_logit_ranks(resid, ids, g_final, w_u)

    per_task_ids = {t: set(v["token_ids"]) for t, v in items["per_task"].items()}
    position = {tid: i for i, tid in enumerate(ids)}

    def summarize(ranks: List[int]) -> dict:
        out = copy_summary(ranks)
        out["per_task"] = {t: copy_summary([ranks[position[tid]] for tid in sorted(s)])
                           for t, s in per_task_ids.items()}
        return out

    quartet_copy, quartet_copy_mlp0 = {}, {}
    for h in QUARTET_HEADS:
        quartet_copy[head_name(QUARTET_LAYER, h)] = summarize(head_copy(h, emb))
        quartet_copy_mlp0[head_name(QUARTET_LAYER, h)] = summarize(head_copy(h, emb_mlp0))
    rand_copy = {head_name(QUARTET_LAYER, h): summarize(head_copy(h, emb)) for h in p2_random_heads}
    rand_values = [v["copy_score"] for v in rand_copy.values()]

    # The ceiling of this read on this model (beside, deciding nothing): the identity map (embedding straight to the
    # unembedding) and every head of every layer, so a fail can be told apart from a read no head can pass.
    identity = copy_summary(own_logit_ranks(emb, ids, g_final, w_u))
    scan: Dict[str, dict] = {}
    for L in range(int(config["num_hidden_layers"])):
        if L == QUARTET_LAYER:
            w_v, w_o, g = w_v17, w_o17, g17
        else:
            w_v = w.get(layer_name(L, "self_attn.v_proj.weight"))
            w_o = w.get(layer_name(L, "self_attn.o_proj.weight"))
            g = w.get(layer_name(L, "input_layernorm.weight"))
        for h in range(N_HEADS):
            a, b = ov_factors(w_v, w_o, g, h)
            resid = rms_norm(emb, torch.ones_like(g), eps) @ a @ b
            scan[head_name(L, h)] = copy_summary(own_logit_ranks(resid, ids, g_final, w_u))
    scan_order = sorted(scan.items(), key=lambda kv: (-kv[1]["copy_score"], kv[0]))
    quartet_scan_ranks = {head_name(QUARTET_LAYER, h): 1 + [n for n, _v in scan_order].index(head_name(QUARTET_LAYER, h))
                          for h in QUARTET_HEADS}
    ceiling = {"identity_map": identity, "n_heads": len(scan),
               "n_heads_reaching_bar": sum(1 for v in scan.values() if v["copy_score"] >= COPY_BAR),
               "max_copy_score": scan_order[0][1]["copy_score"],
               "top10": [{"head": n, **v} for n, v in scan_order[:10]],
               "quartet_rank_among_all_heads": quartet_scan_ranks,
               "copy_score_by_head": {n: v["copy_score"] for n, v in scan.items()}}
    p2 = {"score_of_record": "embedding -> head OV (input gamma folded) -> final-norm gamma -> W_U; rank <= 5",
          "rule": p2_reading({n: v["copy_score"] for n, v in quartet_copy.items()}),
          "heads": quartet_copy,
          "random_baseline": {"kind": f"{n_random} seeded non-quartet layer-{QUARTET_LAYER} heads (seed {seed + 1})",
                              "heads": rand_copy, "copy_score_max": max(rand_values),
                              "copy_score_mean": float(np.mean(rand_values)),
                              "n_reaching_bar": sum(1 for v in rand_values if v >= COPY_BAR)},
          "beside_mlp0": {"note": "item embedding plus mlp.0 of it (Wang et al.'s variant); deciding nothing",
                          "heads": quartet_copy_mlp0,
                          "reading": p2_reading({n: v["copy_score"] for n, v in quartet_copy_mlp0.items()})},
          "ceiling": ceiling}

    # ---------------- weights provenance
    shards = w.shards_used()
    weights = {"model": model_id, "snapshot": snapshot, "revision": os.path.basename(snapshot.rstrip("/")),
               "tensors_read": w.read, "shards": {}}
    for shard in shards:
        entry = {"lfs_sha256_from_blob_name": shard_lfs_sha256(snapshot, shard)}
        if verify_hashes:
            entry["sha256"] = file_sha256(os.path.join(snapshot, shard))
            entry["matches_blob_name"] = entry["sha256"] == entry["lfs_sha256_from_blob_name"]
        weights["shards"][shard] = entry
    weights["index_sha256"] = file_sha256(os.path.join(snapshot, "model.safetensors.index.json"))
    weights["config_sha256"] = file_sha256(os.path.join(snapshot, "config.json"))

    result = {"schema": SCHEMA, "direction": "deception-divergence", "rider": "D4(d)",
              "rule_source": "docs/research/deception-divergence/spec.md, D4 rules, P1 and P2",
              "quartet": {"layer": QUARTET_LAYER, "heads": list(QUARTET_HEADS), "kv_group": QUARTET_KV_GROUP},
              "senders": {"layers": list(SENDER_LAYERS), "n": len(stacked)},
              "conventions": {"rmsnorm": "input_layernorm gammas folded into W_V (sender) and W_Q/W_K (receiver); "
                                         "final norm gamma folded into W_U; per-token RMS divisors not folded",
                              "rope": "the stacked and per-head W_Q scores are exactly RoPE-invariant; the W_QK "
                                      "(Elhage literal) scores ignore RoPE",
                              "gqa": f"head h reads KV group h // {GROUP_SIZE}"},
              "items": {"split": items["split"], "n_pooled": len(ids),
                        "per_task": {t: {k: v for k, v in e.items() if k != "token_ids"}
                                     for t, e in items["per_task"].items()}},
              "P1": p1, "P2": p2,
              "verdicts": {"P1": "pass" if p1["rule"]["pass"] else "fail",
                           "P2": "pass" if p2["rule"]["pass"] else "fail"},
              "checks": checks, "weights": weights, "seed": seed, "n_random": n_random,
              "seconds": round(time.time() - started, 1)}
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "static_quartet.json"), "w") as handle:
        json.dump(result, handle, indent=2)
    with open(os.path.join(out_dir, "static_quartet.md"), "w") as handle:
        handle.write(markdown(result))
    from run_manifest import write_run_manifest
    manifest = write_run_manifest(out_dir, script=str(Path(__file__).resolve()), model=model_id,
                                  model_revision_value=weights["revision"], seed=seed, grader=None,
                                  dataset_files=[str(ROOT / "data" / "datasets" / t / "dataset_dict.json")
                                                 for t in TASKS],
                                  code_files=[str(ROOT / "dataset" / "deception_common.py")])
    result["manifest"] = manifest
    return result


def _fmt(x, nd=4):
    return "n/a" if x is None else f"{x:.{nd}f}"


def markdown(r: dict) -> str:
    p1, p2 = r["P1"], r["P2"]
    rule = p1["rule"]
    lines = [
        "# D4(d): static QK/OV read of the layer-17 quartet", "",
        f"Rule: `{r['rule_source']}`. Weights: {r['weights']['model']} at revision {r['weights']['revision']}.", "",
        "## P1, query side", "",
        f"Score of record: {p1['score_of_record']}. {rule['n_senders']} senders (layers 7 to 16); top 5 percent "
        f"means rank at most {rule['top_rank_cutoff']}.", "",
        "| sender | score | rank | in top 5% |", "|---|---|---|---|"]
    for n in rule["named_ranks"]:
        lines.append(f"| {n} | {_fmt(rule['named_scores'][n])} | {rule['named_ranks'][n]} | "
                     f"{rule['named_in_top'][n]} |")
    lines += ["", "| layer | sum of scores |", "|---|---|"]
    for L, v in rule["layer_sums"].items():
        lines.append(f"| {L} | {_fmt(v)} |")
    lines += ["", f"Layer order by sum: {', '.join(str(x) for x in rule['layer_sum_order'])}. Layers 14 and 15 "
              f"exceed every other: {rule['named_layers_exceed_every_other']}.", "",
              f"**P1 verdict: {r['verdicts']['P1']}.**", "",
              "Top 16 senders:", "", "| rank | sender | score |", "|---|---|---|"]
    for i, e in enumerate(p1["ranking"][:16]):
        lines.append(f"| {i + 1} | {e['sender']} | {_fmt(e['score'])} |")
    rb = p1["random_baseline"]
    lines += ["", f"Random baseline ({rb['kind']}): {rb['n_pass']} of {len(rb['draws'])} draws pass the same rule.",
              "", "| named sender | score into quartet | draw mean | draw max | draws at or above |",
              "|---|---|---|---|---|"]
    for n, v in rb["named_score_vs_draws"].items():
        lines.append(f"| {n} | {_fmt(v['quartet'])} | {_fmt(v['draw_mean'])} | {_fmt(v['draw_max'])} | "
                     f"{v['n_draws_at_or_above']} |")
    lines += ["", "Beside (deciding nothing): per quartet head, the ranks of the two named senders.", "",
              "| quartet head | W_Q: rank 15.8, 14.4, pass | W_QK (Elhage): rank 15.8, 14.4, pass |",
              "|---|---|---|"]
    for qh, rd in p1["beside"]["per_head_W_Q"].items():
        rk = p1["beside"]["per_head_W_QK_elhage"][qh]
        a = ", ".join(str(v) for v in rd["named_ranks"].values())
        b = ", ".join(str(v) for v in rk["named_ranks"].values())
        lines.append(f"| {qh} | {a}, {rd['pass']} | {b}, {rk['pass']} |")
    rule2 = p2["rule"]
    counts = ", ".join("%s %d" % (t, v["n_single_token"]) for t, v in r["items"]["per_task"].items())
    lines += ["", "## P2, copy", "",
              f"Item tokens: {r['items']['n_pooled']} unique single-token items from the {r['items']['split']} "
              f"splits ({counts}).", "",
              "| head | copy score | mean own rank | median own rank | copy score after mlp.0 (beside) |",
              "|---|---|---|---|---|"]
    for n, v in p2["heads"].items():
        m = p2["beside_mlp0"]["heads"][n]
        lines.append(f"| {n} | {_fmt(v['copy_score'], 3)} | {_fmt(v['mean_own_rank'], 1)} | "
                     f"{_fmt(v['median_own_rank'], 1)} | {_fmt(m['copy_score'], 3)} |")
    rb2 = p2["random_baseline"]
    lines += ["", f"Heads reaching {rule2['bar']}: {rule2['n_reaching']} of 4 (needed {rule2['heads_needed']}).",
              f"Random baseline ({rb2['kind']}): mean {_fmt(rb2['copy_score_mean'], 3)}, max "
              f"{_fmt(rb2['copy_score_max'], 3)}, {rb2['n_reaching_bar']} reach the bar.", "",
              f"**P2 verdict: {r['verdicts']['P2']}.**", ""]
    ce = p2["ceiling"]
    lines += [f"Ceiling of this read (beside, deciding nothing): the identity map (embedding straight to W_U) scores "
              f"{_fmt(ce['identity_map']['copy_score'], 3)}; {ce['n_heads_reaching_bar']} of {ce['n_heads']} heads "
              f"reach {rule2['bar']}, the best {_fmt(ce['max_copy_score'], 3)}. Quartet ranks among all heads: "
              f"{ce['quartet_rank_among_all_heads']}.", "",
              "| head | copy score | mean own rank | median own rank |", "|---|---|---|---|"]
    for e in ce["top10"]:
        lines.append(f"| {e['head']} | {_fmt(e['copy_score'], 3)} | {_fmt(e['mean_own_rank'], 1)} | "
                     f"{_fmt(e['median_own_rank'], 1)} |")
    lines += ["",
              "## Checks", "",
              f"- Dense spot check on {r['checks']['dense_spot_check']['sender']}: low-rank "
              f"{r['checks']['dense_spot_check']['low_rank']:.12f}, dense {r['checks']['dense_spot_check']['dense']:.12f}.",
              f"- Shapes: {r['checks']['shapes']}; lm_head {r['checks']['lm_head_shape']}, Frobenius norm "
              f"{r['checks']['lm_head_fro_norm']:.4f}.",
              f"- Quartet KV groups: {r['checks']['quartet_kv_group']}.",
              f"- Conventions: {r['conventions']['rmsnorm']}; {r['conventions']['rope']}.", ""]
    return "\n".join(lines)


def main(argv=None) -> dict:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", default="outputs/_analyses/deception-divergence/d4d")
    parser.add_argument("--verify-hashes", action="store_true",
                        help="sha256 every shard read (slow on Lustre); default records the LFS blob name")
    parser.add_argument("--n-random", type=int, default=N_RANDOM)
    parser.add_argument("--seed", type=int, default=RANDOM_SEED)
    cli = parser.parse_args(argv)
    result = run(cli.out, verify_hashes=cli.verify_hashes, n_random=cli.n_random, seed=cli.seed)
    print(f"P1 {result['verdicts']['P1']}: ranks {result['P1']['rule']['named_ranks']} (cutoff "
          f"{result['P1']['rule']['top_rank_cutoff']}), layer order {result['P1']['rule']['layer_sum_order']}")
    print(f"P2 {result['verdicts']['P2']}: copy scores "
          f"{ {n: round(v['copy_score'], 3) for n, v in result['P2']['heads'].items()} }")
    print(f"wrote {cli.out}/static_quartet.json, .md and {result['manifest']} in {result['seconds']} s")
    return result


if __name__ == "__main__":
    main()
