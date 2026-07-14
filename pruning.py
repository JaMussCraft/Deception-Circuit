"""
pruning.py — the two training phases, shared across all models and tasks.

Both phases optimise only the L0 gates of a frozen base model and share one
inner loop (`_optimize_gates`); they differ only in which model is built and
how the result is analysed:

  * Phase 1 (node pruning) trains node gates, then enforces hierarchical gate
    consistency and reports per-granularity compression.
  * Phase 2 (edge pruning) trains edge gates between the surviving nodes.

The objective each step is
    loss = (1 - lambda_sp) * (kl + task) + lambda_sp * sparsity
where (kl, task) come from the Task and `sparsity` from the model's gates.
The Task and ModelAdapter abstract away every task/model-specific detail.
"""

import time

import torch
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from tqdm import tqdm

from analysis import analyze_and_finalize_circuit


# ==============================================================================
# GPU memory tracker
# ==============================================================================

class GPUMemoryTracker:
    """Records labelled GPU-memory snapshots and prints a comparison table."""

    def __init__(self):
        self.snapshots = []  # [(tag, alloc, reserved, peak)]
        self._enabled = torch.cuda.is_available()
        if self._enabled:
            torch.cuda.reset_peak_memory_stats()

    @staticmethod
    def _gb(nbytes):
        return nbytes / 1024 ** 3

    def snap(self, tag: str):
        if not self._enabled:
            return
        a = torch.cuda.memory_allocated()
        r = torch.cuda.memory_reserved()
        p = torch.cuda.max_memory_allocated()
        self.snapshots.append((tag, a, r, p))
        print(f"  [GPU] {tag}: alloc {self._gb(a):.2f} GB | "
              f"reserved {self._gb(r):.2f} GB | peak {self._gb(p):.2f} GB")

    def reset_peak(self):
        if self._enabled:
            torch.cuda.reset_peak_memory_stats()

    def print_report(self):
        if not self._enabled or not self.snapshots:
            return
        print("\n" + "=" * 90)
        print("  GPU MEMORY MAP")
        print("=" * 90)
        print(f"{'Step':<40} {'Alloc (GB)':>10} {'Delta':>10} "
              f"{'Reserved':>10} {'Peak':>10}")
        print("-" * 90)
        prev = 0
        for tag, a, r, p in self.snapshots:
            d = a - prev
            sign = "+" if d >= 0 else ""
            print(f"{tag:<40} {self._gb(a):>10.3f} {sign + f'{self._gb(d):.3f}':>10} "
                  f"{self._gb(r):>10.3f} {self._gb(p):>10.3f}")
            prev = a
        node_peaks = [p for t, a, r, p in self.snapshots if "node" in t.lower()]
        edge_peaks = [p for t, a, r, p in self.snapshots if "edge" in t.lower()]
        overall = max(p for _, _, _, p in self.snapshots)
        total_gpu = torch.cuda.get_device_properties(0).total_memory
        print("-" * 90)
        if node_peaks:
            print(f"  Node pruning peak: {self._gb(max(node_peaks)):.3f} GB")
        if edge_peaks:
            print(f"  Edge pruning peak: {self._gb(max(edge_peaks)):.3f} GB")
        print(f"  Overall peak:      {self._gb(overall):.3f} GB "
              f"/ {self._gb(total_gpu):.1f} GB ({overall / total_gpu * 100:.1f}%)")
        print("=" * 90)


# ==============================================================================
# Shared inner loop
# ==============================================================================

def _maybe_cache_logits(adapter, task, full_model, train_dl, device):
    """Pre-compute reference logits once (Llama) to avoid a second big forward
    per step. Requires a non-shuffled train loader (see args.shuffle_train)."""
    if not adapter.cache_target_logits:
        return None
    print("Pre-caching reference-model logits for the training set...")
    cache = {}
    with torch.no_grad():
        for bi, batch in enumerate(tqdm(train_dl, desc="Caching")):
            batch = _to_device(batch, device)
            out = full_model(**task.target_inputs(batch), use_cache=False)
            cache[bi] = out.logits.detach()
    return cache


def _to_device(batch, device):
    for k, v in batch.items():
        if isinstance(v, torch.Tensor):
            batch[k] = v.to(device)
    return batch


def _optimize_gates(model, task, full_model, train_dl, val_dl, device, tokenizer,
                    *, num_epochs, lr, lambda_sparsity, state, adapter, tracker,
                    phase_label, clip_grad, eval_every=10):
    gate_params = [p for p in model.parameters() if p.requires_grad]
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Trainable gate parameters: {sum(p.numel() for p in gate_params):,} / "
          f"{total_params:,} "
          f"({sum(p.numel() for p in gate_params) / total_params * 100:.4f}%)")

    optimizer = AdamW(gate_params, lr=lr)
    scheduler = CosineAnnealingLR(optimizer, T_max=num_epochs, eta_min=1e-4)

    tracker.reset_peak()
    tracker.snap(f"{phase_label} model loaded")

    cached = _maybe_cache_logits(adapter, task, full_model, train_dl, device)

    model.train()
    step = 0
    start = time.time()
    pbar = tqdm(range(num_epochs), desc=f"{phase_label} pruning")
    for epoch in pbar:
        ep_loss = ep_kl = ep_task = ep_sp = 0.0
        for bi, batch in enumerate(train_dl):
            batch = _to_device(batch, device)
            optimizer.zero_grad()

            circuit_out = model(**task.model_inputs(batch))
            if cached is not None:
                target_logits = cached[bi]
            else:
                with torch.no_grad():
                    target_logits = full_model(**task.target_inputs(batch)).logits

            kl_loss, task_loss = task.compute_objective(
                circuit_out.logits, target_logits, batch, state, device)
            sp_loss = model.get_sparsity_loss(step=step)["total_sparsity"]

            loss = (1 - lambda_sparsity) * (kl_loss + task_loss) + lambda_sparsity * sp_loss
            loss.backward()
            if clip_grad:
                torch.nn.utils.clip_grad_norm_(gate_params, max_norm=1.0)
            optimizer.step()

            ep_loss += float(loss)
            ep_kl += float(kl_loss)
            ep_task += float(task_loss)
            ep_sp += float(sp_loss)
            step += 1

        scheduler.step()
        n = len(train_dl)
        pbar.set_postfix(L=f"{ep_loss / n:.3f}", KL=f"{ep_kl / n:.3f}",
                         T=f"{ep_task / n:.3f}",
                         Sp=f"{ep_sp / n:.3f}",
                         LR=f"{scheduler.get_last_lr()[0]:.2e}")

        if epoch == 0:
            tracker.snap(f"{phase_label} epoch 1 (fwd+bwd+optim)")
        if eval_every and (epoch + 1) % eval_every == 0:
            model.eval()
            task.evaluate(model, f"{phase_label} Ep {epoch + 1}", full_model,
                          val_dl, device, tokenizer, state)
            model.train()

    print(f"{phase_label} pruning time: {time.time() - start:.1f}s")
    tracker.snap(f"{phase_label} pruning done")

    if cached is not None:
        del cached
        torch.cuda.empty_cache()


# ==============================================================================
# Phase 1: node pruning
# ==============================================================================

def run_node_pruning(adapter, task, full_model, train_dl, val_dl, device, tokenizer,
                     node_cfg, args, state, tracker):
    print("\n" + "=" * 70)
    print(f"  PHASE 1: NODE PRUNING ({task.display_name})")
    print("=" * 70)

    model = adapter.build_node_model(node_cfg, device)
    _optimize_gates(
        model, task, full_model, train_dl, val_dl, device, tokenizer,
        num_epochs=args.node_epochs, lr=args.lr,
        lambda_sparsity=args.node_lambda_sparsity,
        state=state, adapter=adapter, tracker=tracker,
        phase_label="Node", clip_grad=True,
    )

    adapter.finalize_node_model(model, node_cfg)
    node_stats = analyze_and_finalize_circuit(model)
    return model, node_stats


# ==============================================================================
# Phase 2: edge pruning
# ==============================================================================

def run_edge_pruning(adapter, task, full_model, active_heads, active_mlps,
                     train_dl, val_dl, device, tokenizer, edge_cfg, args, state, tracker):
    print("\n" + "=" * 70)
    print(f"  PHASE 2: EDGE PRUNING ({task.display_name})")
    print("=" * 70)

    model = adapter.build_edge_model(active_heads, active_mlps, edge_cfg, device)
    _optimize_gates(
        model, task, full_model, train_dl, val_dl, device, tokenizer,
        num_epochs=args.edge_epochs, lr=args.lr,
        lambda_sparsity=args.edge_lambda_sparsity,
        state=state, adapter=adapter, tracker=tracker,
        phase_label="Edge", clip_grad=False,
    )
    return model
