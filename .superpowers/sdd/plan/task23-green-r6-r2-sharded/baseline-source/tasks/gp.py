"""GP task — Gendered Pronoun prediction (GPT-2 and Llama)."""

import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from tasks import Task


class GPTask(Task):
    name = "gp"
    display_name = "GP (Gendered Pronoun)"

    def build_dataloaders(self, tokenizer, family, full_model, device, args, state):
        bs = args.batch_size
        path = os.path.join(args.data_dir, "gp")
        if family == "llama":
            from dataset.gp_llama import (
                load_or_generate_gp_data, GPDatasetLlama,
                run_evaluation, filter_dataset_by_model_correctness)
            Dataset = GPDatasetLlama
        else:
            from dataset.gp_gpt2 import (
                load_or_generate_gp_data, GPDataset,
                run_evaluation, filter_dataset_by_model_correctness)
            Dataset = GPDataset

        train = load_or_generate_gp_data(path, "train", args.train_samples)
        val = load_or_generate_gp_data(path, "validation", args.val_samples)
        test = load_or_generate_gp_data(path, "test", args.test_samples)

        val = filter_dataset_by_model_correctness(
            val, full_model, tokenizer, device,
            max_length=args.max_seq_length, batch_size=bs)
        test = filter_dataset_by_model_correctness(
            test, full_model, tokenizer, device,
            max_length=args.max_seq_length, batch_size=bs)
        self._run_evaluation = run_evaluation

        make = lambda d: Dataset(d, tokenizer, max_length=args.max_seq_length)
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
        task_loss = F.relu(0.1 - (lg - lb)).mean()
        return kl_loss, task_loss

    def evaluate(self, model, name, full_model, loader, device, tokenizer, state):
        return self._run_evaluation(model, name, full_model, loader, device,
                                    tokenizer=tokenizer)
