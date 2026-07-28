"""
evaluation/metrics.py — the generic prediction-position evaluator.

`Task.pred_spec` says where a task's answer lives and what it competes against.
That one hook is enough to compute the four fidelity metrics, the argmax-token
distribution, and the reference-logit cache for *any* task, without this module
knowing anything about STD, IOI, or GP.

The metric definitions match `dataset/std_llama.run_evaluation` exactly, so the
generic path and the repo path can be cross-checked against each other (eval 1
does precisely that, which is what makes the other ~100 evaluations
trustworthy):

    accuracy     fraction with logit(target) > logit(distractor)
    logit_diff   mean logit(target) - logit(distractor)
    kl_div       mean KL(full ‖ circuit) at the prediction position, summed over
                 the vocabulary in fp32
    exact_match  fraction where the circuit's argmax equals the full model's

With no reference available the last two report self-faithfulness (0.0 and 1.0),
which is the convention `run_evaluation` already uses.
"""

from __future__ import annotations

from collections import Counter

import torch
import torch.nn.functional as F
from tqdm import tqdm

from evaluation.ablation import ablation_hook


def _to_device(mapping, device):
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in mapping.items()}


def _spec_positions(spec, key, device, fallback):
    value = spec.get(key)
    return fallback if value is None else value.to(device)


# ==============================================================================
# REFERENCE-LOGIT CACHE
# ==============================================================================

def build_ref_cache(ctx, loader) -> torch.Tensor:
    """Full-model logits at every sample's prediction position, [N, vocab].

    Worth 244 MB (bf16, 1000 x 128256) to skip one full-model forward per
    circuit — about 50 of them in the null evaluation. Indexed by position in
    the loader, so it is only valid for a shuffle=False loader over this dataset
    (both loaders the context builds satisfy that).
    """
    chunks = []
    for batch in tqdm(loader, desc="Caching reference logits", leave=False):
        spec = ctx.task.pred_spec(batch)
        inputs = _to_device(ctx.task.target_inputs(batch), ctx.device)
        logits = ctx.reference_logits(inputs["input_ids"], inputs["attention_mask"])
        n = logits.shape[0]
        idx = torch.arange(n, device=logits.device)
        pos = spec["pred_pos"].to(logits.device)
        chunks.append(logits[idx, pos].to(ctx.cli.ref_cache_device))
    cache = torch.cat(chunks)
    print(f"  Reference-logit cache: {tuple(cache.shape)} {cache.dtype} on "
          f"{cache.device} ({cache.numel() * cache.element_size() / 1024 ** 3:.2f} GB)")
    return cache


# ==============================================================================
# THE EVALUATOR
# ==============================================================================

def evaluate_pred_position(ctx, loader, *, model=None, hook=None,
                           ref_cache=None, use_reference=True,
                           collect_argmax=False, top_k=12,
                           desc="Evaluating") -> dict:
    """The four fidelity metrics (and optionally the argmax distribution).

    `hook` is the ablation hook to install for the circuit's forward passes;
    the reference model is never hooked (under `--reference shared` it takes the
    single-stream path, where no gate — and so no hook — is reached).
    """
    model = model if model is not None else ctx.node_model
    task, device = ctx.task, ctx.device
    if task.pred_spec(_probe(loader)) is None:
        raise ValueError(f"task {task.name} does not implement pred_spec")

    have_reference = use_reference and (
        ref_cache is not None or ctx.reference_model is not None
        or ctx.cli.reference == "shared")

    n = 0
    n_correct = 0
    n_exact = 0
    total_logit_diff = 0.0
    total_kl = 0.0
    counter = Counter()
    n_target = n_distractor = 0

    with torch.no_grad(), ablation_hook(model, hook):
        for batch in tqdm(loader, desc=desc, leave=False):
            spec = task.pred_spec(batch)
            inputs = _to_device(task.model_inputs(batch), device)
            logits = model(**inputs, use_cache=False).logits

            bsz = logits.shape[0]
            idx = torch.arange(bsz, device=device)
            pos = spec["pred_pos"].to(device)
            target = spec["target"].to(device)
            distractor = spec["distractor"].to(device)
            t_pos = _spec_positions(spec, "target_pos", device, pos)
            d_pos = _spec_positions(spec, "distractor_pos", device, pos)

            lt = logits[idx, t_pos, target].float()
            ld = logits[idx, d_pos, distractor].float()
            total_logit_diff += float((lt - ld).sum())
            n_correct += int((lt > ld).sum())

            pred = logits[idx, pos].float()
            argmax = pred.argmax(dim=-1)

            if have_reference:
                if ref_cache is not None:
                    ref = ref_cache[n:n + bsz].to(device).float()
                else:
                    ref_inputs = _to_device(task.target_inputs(batch), device)
                    ref_full = ctx.reference_logits(ref_inputs["input_ids"],
                                                    ref_inputs["attention_mask"])
                    ref = ref_full[idx, pos].float()
                total_kl += float(F.kl_div(
                    F.log_softmax(pred, dim=-1), F.log_softmax(ref, dim=-1),
                    reduction="sum", log_target=True))
                n_exact += int((argmax == ref.argmax(dim=-1)).sum())

            if collect_argmax:
                counter.update(argmax.tolist())
                n_target += int((argmax == target).sum())
                n_distractor += int((argmax == distractor).sum())

            n += bsz

    out = {
        "accuracy": n_correct / n,
        "logit_diff": total_logit_diff / n,
        "kl_div": (total_kl / n) if have_reference else 0.0,
        "exact_match": (n_exact / n) if have_reference else 1.0,
        "n": n,
    }
    if collect_argmax:
        out["argmax"] = argmax_summary(counter, ctx.tokenizer, n, top_k,
                                       n_target, n_distractor)
    return out


def _probe(loader):
    """One batch, for the pred_spec capability check."""
    for batch in loader:
        return batch
    raise ValueError("empty loader")


_FALLBACK_ANNOUNCED = set()


def evaluate_task_metrics(ctx, loader, *, hook=None, ref_cache=None,
                          collect_argmax=False, desc="Evaluating") -> dict:
    """The four metrics, however this task can produce them.

    Tasks that implement `pred_spec` go through the generic evaluator and get
    the reference cache and the argmax distribution for free. Tasks that do not
    (GT, today) fall back to `Task.evaluate` — correct, but a full-model forward
    per circuit and no argmax histogram.
    """
    if ctx.has_pred_spec:
        return evaluate_pred_position(ctx, loader, hook=hook, ref_cache=ref_cache,
                                      collect_argmax=collect_argmax, desc=desc)

    if collect_argmax and ctx.task.name not in _FALLBACK_ANNOUNCED:
        _FALLBACK_ANNOUNCED.add(ctx.task.name)
        print(f"  argmax distribution unavailable: {ctx.task.name} does not "
              f"implement pred_spec; falling back to task.evaluate (no "
              f"reference-logit cache).")

    with ablation_hook(ctx.node_model, hook):
        result = ctx.task.evaluate(ctx.node_model, desc, ctx.reference_model,
                                   loader, ctx.device, ctx.tokenizer, ctx.state)
    out = {k: v for k, v in result.items() if k != "outputs"}
    out.setdefault("n", len(loader.dataset))
    return out


def argmax_summary(counter, tokenizer, n, top_k, n_target, n_distractor) -> dict:
    """The incoherence detector: what is the model actually saying?"""
    top = []
    for token_id, count in counter.most_common(top_k):
        token = tokenizer.decode([token_id]) if tokenizer is not None else str(token_id)
        top.append({"id": int(token_id), "token": token, "count": int(count),
                    "frac": count / n})
    return {
        "top": top,
        "n_distinct": len(counter),
        "target_frac": n_target / n,
        "distractor_frac": n_distractor / n,
        "other_frac": (n - n_target - n_distractor) / n,
    }


# ==============================================================================
# NULL-DISTRIBUTION STATISTICS
# ==============================================================================

def _percentile(sorted_values, q):
    """Linear-interpolated percentile, without pulling in numpy at call sites."""
    if not sorted_values:
        return float("nan")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    pos = (len(sorted_values) - 1) * q / 100.0
    lo = int(pos)
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return float(sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac)


def summarize_null(values, discovered, better="higher") -> dict:
    """Where the discovered circuit sits in a null distribution.

    percentile  fraction of the null the discovered circuit beats (0-100)
    p_value     Monte-Carlo, (#random at least as good + 1) / (n + 1); the +1
                is what keeps it from ever claiming p = 0 off 50 samples
    z           (discovered - mean) / std, signed so positive always means
                better regardless of the metric's direction
    """
    values = [float(v) for v in values if v is not None]
    n = len(values)
    if not n:
        return {}
    ordered = sorted(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / max(n - 1, 1)
    std = var ** 0.5

    if better == "higher":
        n_beaten = sum(1 for v in values if v < discovered)
        n_at_least_as_good = sum(1 for v in values if v >= discovered)
        z = (discovered - mean) / std if std else float("inf") * (
            1 if discovered > mean else -1 if discovered < mean else 0)
    else:
        n_beaten = sum(1 for v in values if v > discovered)
        n_at_least_as_good = sum(1 for v in values if v <= discovered)
        z = (mean - discovered) / std if std else float("inf") * (
            1 if discovered < mean else -1 if discovered > mean else 0)

    return {
        "n": n,
        "better": better,
        "mean": mean,
        "std": std,
        "min": ordered[0],
        "max": ordered[-1],
        "p5": _percentile(ordered, 5),
        "p50": _percentile(ordered, 50),
        "p95": _percentile(ordered, 95),
        "best": ordered[-1] if better == "higher" else ordered[0],
        "discovered": float(discovered),
        "percentile": 100.0 * n_beaten / n,
        "p_value": (n_at_least_as_good + 1) / (n + 1),
        "z": z,
        "passes_95th": bool(n_beaten / n >= 0.95),
    }


def summarize_metrics(rows, discovered: dict, metric_columns, metric_better) -> dict:
    """summarize_null for every metric in `metric_columns`."""
    stats = {}
    for key, _ in metric_columns:
        if key not in discovered:
            continue
        values = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
        if not values:
            continue
        stats[key] = summarize_null(values, discovered[key],
                                    metric_better.get(key, "higher"))
    return stats
