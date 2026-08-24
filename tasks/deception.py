"""Shared Task implementation for the deception-mechanism family (FAR/SDR/SER).

The objective is unchanged from STD — single-token binary forced choice read at
`prefix_length - 1`, KL to the full model at the prediction position plus a
margin hinge on logit(target) − logit(distractor) — because the three mechanisms
are only comparable if the readout is identical. Only the dataloader
construction differs, and even that differs only in which directory it loads.
"""

import os

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from tasks import Task


class DeceptionTask(Task):
    """Base for the three mechanism tasks; subclasses set `name`/`display_name`."""

    mechanism = ""

    def supports_family(self, family: str) -> bool:
        return family == "llama"

    def dataset_dir(self, args) -> str:
        """<data-dir>/<task>, or <data-dir>/<task>_honest for the honest twin."""
        condition = getattr(args, "deception_condition", "deceptive")
        suffix = "_honest" if condition == "honest" else ""
        return os.path.join(args.data_dir, f"{self.name}{suffix}")

    def build_dataloaders(self, tokenizer, family, full_model, device, args, state):
        bs = args.batch_size
        from dataset.deception_common import (
            DeceptionDatasetLlama, filter_by_model_behavior, load_dataset_config,
            load_or_generate_deception_data, resolve_margin, run_evaluation)

        path = self.dataset_dir(args)
        config = load_dataset_config(path)
        state["margin"] = resolve_margin(args, config)

        train = load_or_generate_deception_data(path, "train", args.train_samples)
        val = load_or_generate_deception_data(path, "validation", args.val_samples)
        test = load_or_generate_deception_data(path, "test", args.test_samples)

        # Splits are already behaviorally filtered by the build script (train
        # included). --deception-runtime-filter re-checks val/test against the
        # current full model, mirroring the other tasks' pattern.
        if getattr(args, "deception_runtime_filter", False):
            val, _, _ = filter_by_model_behavior(
                val, full_model, tokenizer, device, margin_thresh=state["margin"],
                max_length=args.max_seq_length, batch_size=bs)
            test, _, _ = filter_by_model_behavior(
                test, full_model, tokenizer, device, margin_thresh=state["margin"],
                max_length=args.max_seq_length, batch_size=bs)
        self._run_evaluation = run_evaluation

        make = lambda d: DeceptionDatasetLlama(d, tokenizer,
                                               max_length=args.max_seq_length)
        train_dl = DataLoader(make(train), batch_size=bs,
                              shuffle=getattr(args, "shuffle_train", True))
        val_dl = DataLoader(make(val), batch_size=bs, shuffle=False)
        test_dl = DataLoader(make(test), batch_size=bs, shuffle=False)
        return train_dl, val_dl, test_dl

    def build_variant_dataloader(self, variant, tokenizer, args, state):
        from dataset.deception_common import (DeceptionDatasetLlama,
                                              load_or_generate_deception_data)
        from evaluation import variants

        if variant not in variants.PROMPT_VARIANTS:
            return None
        records = load_or_generate_deception_data(
            self.dataset_dir(args), "test", args.test_samples)
        records = variants.deception_records(self.name, records, variant,
                                             tokenizer, args.max_seq_length)
        return variants.loader(
            DeceptionDatasetLlama(records, tokenizer,
                                  max_length=args.max_seq_length),
            args.batch_size)

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

    def pred_spec(self, batch):
        # The prompt ends with the assistant stem; the answer is the next token,
        # read at prefix_length - 1 (the real, unpadded length).
        return {"pred_pos": batch["prefix_length"] - 1,
                "target": batch["target_token"],
                "distractor": batch["distractor_token"]}

    def evaluate(self, model, name, full_model, loader, device, tokenizer, state):
        return self._run_evaluation(model, name, full_model, loader, device,
                                    tokenizer=tokenizer)
