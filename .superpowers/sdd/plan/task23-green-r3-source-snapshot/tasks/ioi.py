"""IOI task — Indirect Object Identification (GPT-2 and Llama)."""

import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from tasks import Task


class IOITask(Task):
    name = "ioi"
    display_name = "IOI (Indirect Object Identification)"

    def build_dataloaders(self, tokenizer, family, full_model, device, args, state):
        bs = args.batch_size
        if family == "llama":
            from dataset.ioi_llama import (
                generate_ioi_data_llama, IOIDatasetLlama,
                run_evaluation, filter_dataset_by_model_correctness)
            train = generate_ioi_data_llama(args.train_samples, tokenizer, seed=args.seed)
            val = generate_ioi_data_llama(args.val_samples, tokenizer, seed=args.seed + 1)
            test = generate_ioi_data_llama(args.test_samples, tokenizer, seed=args.seed + 2)
            make = lambda d: IOIDatasetLlama(d, tokenizer, max_length=args.max_seq_length)
        else:
            from dataset.ioi_gpt2 import (
                load_or_generate_ioi_data, IOIDataset,
                run_evaluation, filter_dataset_by_model_correctness)
            path = os.path.join(args.data_dir, "ioi")
            train = load_or_generate_ioi_data(path, "train", args.train_samples)
            val = load_or_generate_ioi_data(path, "validation", args.val_samples)
            test = load_or_generate_ioi_data(path, "test", args.test_samples)
            make = lambda d: IOIDataset(d, tokenizer, max_length=args.max_seq_length)

        val = filter_dataset_by_model_correctness(val, full_model, tokenizer, device, batch_size=bs)
        test = filter_dataset_by_model_correctness(test, full_model, tokenizer, device, batch_size=bs)
        self._run_evaluation = run_evaluation

        train_dl = DataLoader(make(train), batch_size=bs, shuffle=getattr(args, "shuffle_train", True))
        val_dl = DataLoader(make(val), batch_size=bs, shuffle=False)
        test_dl = DataLoader(make(test), batch_size=bs, shuffle=False)
        return train_dl, val_dl, test_dl

    def compute_objective(self, circuit_logits, target_logits, batch, state, device):
        bs = circuit_logits.size(0)
        total_kl = 0.0
        for i in range(bs):
            t_s = batch["T_Start"][i].item() - 1
            t_e = batch["T_End"][i].item() - 1
            vl = batch["attention_mask"][i].sum().item()
            end = min(t_e, int(vl))
            if t_s < end:
                total_kl = total_kl + F.kl_div(
                    F.log_softmax(circuit_logits[i, t_s:end].float(), dim=-1),
                    F.log_softmax(target_logits[i, t_s:end].float(), dim=-1),
                    reduction="sum", log_target=True,
                )
        kl_loss = total_kl / bs

        idx = torch.arange(bs, device=device)
        pos_good = batch["T_Start"] - 1
        pos_bad = batch["D_Start"] - 1
        tok_good = batch["target_tokens"][:, 0]
        tok_bad = batch["distractor_tokens"][:, 0]
        lg = circuit_logits[idx, pos_good, tok_good].float()
        lb = circuit_logits[idx, pos_bad, tok_bad].float()
        task_loss = F.relu(4.0 - (lg - lb)).mean()
        return kl_loss, task_loss

    def evaluate(self, model, name, full_model, loader, device, tokenizer, state):
        return self._run_evaluation(model, name, full_model, loader, device,
                                    tokenizer=tokenizer)
