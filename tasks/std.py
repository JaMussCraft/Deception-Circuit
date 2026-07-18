"""STD task — Stipulated-Truth Deception (Llama chat models only)."""

import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from tasks import Task


class STDTask(Task):
    name = "std"
    display_name = "STD (Stipulated-Truth Deception)"

    def supports_family(self, family: str) -> bool:
        return family == "llama"

    def build_dataloaders(self, tokenizer, family, full_model, device, args, state):
        bs = args.batch_size
        from dataset.std_llama import (
            load_or_generate_std_data, load_std_dataset_config,
            resolve_std_margin, STDDatasetLlama,
            run_evaluation, filter_std_by_model_behavior)

        path = os.path.join(args.data_dir, f"std_{args.std_variant}")
        config = load_std_dataset_config(path)
        state["margin"] = resolve_std_margin(args, config)

        train = load_or_generate_std_data(path, "train", args.train_samples)
        val = load_or_generate_std_data(path, "validation", args.val_samples)
        test = load_or_generate_std_data(path, "test", args.test_samples)

        # Splits are already behaviorally filtered by build_std_dataset.py
        # (train included). --std-runtime-filter re-checks val/test against the
        # current full model, mirroring the other tasks' pattern.
        if getattr(args, "std_runtime_filter", False):
            val, _, _ = filter_std_by_model_behavior(
                val, full_model, tokenizer, device,
                margin_thresh=state["margin"],
                max_length=args.max_seq_length, batch_size=bs)
            test, _, _ = filter_std_by_model_behavior(
                test, full_model, tokenizer, device,
                margin_thresh=state["margin"],
                max_length=args.max_seq_length, batch_size=bs)
        self._run_evaluation = run_evaluation

        make = lambda d: STDDatasetLlama(d, tokenizer, max_length=args.max_seq_length)
        train_dl = DataLoader(make(train), batch_size=bs, shuffle=getattr(args, "shuffle_train", True))
        val_dl = DataLoader(make(val), batch_size=bs, shuffle=False)
        test_dl = DataLoader(make(test), batch_size=bs, shuffle=False)
        return train_dl, val_dl, test_dl

    def compute_objective(self, circuit_logits, target_logits, batch, state, device):
        bs = circuit_logits.size(0)
        total_kl = 0.0
        for i in range(bs):
            pred_pos = batch["prefix_length"][i].item() - 1
            total_kl = total_kl + F.kl_div(
                F.log_softmax(circuit_logits[i, pred_pos].float(), dim=-1),
                F.log_softmax(target_logits[i, pred_pos].float(), dim=-1),
                reduction="sum", log_target=True,
            )
        kl_loss = total_kl / bs

        idx = torch.arange(bs, device=device)
        pos = batch["prefix_length"] - 1
        lg = circuit_logits[idx, pos, batch["target_token"]].float()
        lb = circuit_logits[idx, pos, batch["distractor_token"]].float()
        task_loss = F.relu(state["margin"] - (lg - lb)).mean()
        return kl_loss, task_loss

    def evaluate(self, model, name, full_model, loader, device, tokenizer, state):
        return self._run_evaluation(model, name, full_model, loader, device,
                                    tokenizer=tokenizer)
