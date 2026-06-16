"""
GT task — Greater-Than (GPT-2 only).

The model sees e.g. "The war lasted from 1743 to 17" and must put probability
mass on year-completions greater than 43. The objective is a KL match on the
re-normalised two-digit-number logits at the final position; there is no
auxiliary margin term. Llama is not supported for this task.
"""

import os
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from tasks import Task


class GTTask(Task):
    name = "gt"
    display_name = "GT (Greater-Than)"

    # GT batches carry clean_* tensors.
    clean_key = "clean_input_ids"
    mask_key = "clean_attention_mask"
    corrupt_key = "corrupted_input_ids"

    metric_columns = [
        ("accuracy", "Accuracy"),
        ("prob_diff", "Prob Diff"),
        ("cutoff_sharpness", "Cutoff Sharp"),
        ("kl_div", "KL Div"),
    ]

    def supports_family(self, family: str) -> bool:
        return family != "llama"

    def prepare(self, tokenizer, device) -> dict:
        from dataset.gt_gpt2 import create_two_digit_token_mapping
        two = create_two_digit_token_mapping(tokenizer)
        digit_token_ids = torch.tensor(
            [tok for _, tok in sorted(two.items())], device=device)
        return {"two_digit_tokens": two, "digit_token_ids": digit_token_ids}

    def build_dataloaders(self, tokenizer, family, full_model, device, args, state):
        from dataset.gt_gpt2 import (
            load_or_generate_gt_data, GTDataset,
            run_evaluation, filter_dataset_by_model_correctness)
        bs = args.batch_size
        two = state["two_digit_tokens"]
        path = os.path.join(args.data_dir, "gt")

        train = load_or_generate_gt_data(path, "train", args.train_samples)
        val = load_or_generate_gt_data(path, "validation", args.val_samples)
        test = load_or_generate_gt_data(path, "test", args.test_samples)

        val = filter_dataset_by_model_correctness(
            val, full_model, tokenizer, device, two, batch_size=bs)
        test = filter_dataset_by_model_correctness(
            test, full_model, tokenizer, device, two, batch_size=bs)
        self._run_evaluation = run_evaluation

        make = lambda d: GTDataset(d, tokenizer, max_length=args.max_seq_length)
        train_dl = DataLoader(make(train), batch_size=bs, shuffle=getattr(args, "shuffle_train", True))
        val_dl = DataLoader(make(val), batch_size=bs, shuffle=False)
        test_dl = DataLoader(make(test), batch_size=bs, shuffle=False)
        return train_dl, val_dl, test_dl

    def compute_objective(self, circuit_logits, target_logits, batch, state, device):
        bs = circuit_logits.size(0)
        ar = torch.arange(bs, device=device)
        last = batch["last_token_idx"]
        last_circuit = circuit_logits[ar, last, :]
        last_target = target_logits[ar, last, :]

        digit_ids = state["digit_token_ids"]
        expand = digit_ids.unsqueeze(0).expand(bs, -1)
        dlc = torch.gather(last_circuit, 1, expand)
        dlt = torch.gather(last_target, 1, expand)

        kl_loss = F.kl_div(
            F.log_softmax(dlc.float(), dim=-1),
            F.log_softmax(dlt.float(), dim=-1),
            reduction="batchmean", log_target=True,
        )
        # No auxiliary task-margin term for GT.
        return kl_loss, torch.zeros((), device=device)

    def evaluate(self, model, name, full_model, loader, device, tokenizer, state):
        return self._run_evaluation(model, name, full_model, loader, device,
                                    state["two_digit_tokens"], tokenizer=tokenizer)
