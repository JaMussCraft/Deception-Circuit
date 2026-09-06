"""Joint multitask pruning over the deception-mechanism family (FAR/SDR/SER).

Concatenates the full train/val splits from each subtask so every mechanism
contributes equally (same per-task sample count). Test evaluation is reported
per subtask via `evaluate_subtasks`.
"""

from __future__ import annotations

import random
from typing import Dict, List, Tuple

from torch.utils.data import DataLoader

from tasks import Task, get_task, DECEPTION_TASKS
from tasks.deception import DeceptionTask


def _normalize_joint_tasks(names: List[str]) -> List[str]:
    if not names:
        raise ValueError("--joint-tasks must name at least one subtask")
    seen = set()
    ordered = []
    for name in names:
        if name not in DECEPTION_TASKS:
            raise ValueError(
                f"Unknown joint subtask {name!r}. Choose from {DECEPTION_TASKS}.")
        if name not in seen:
            seen.add(name)
            ordered.append(name)
    if len(ordered) < 2:
        raise ValueError(
            f"Joint pruning requires at least two subtasks; got {ordered!r}.")
    return ordered


class JointDeceptionTask(DeceptionTask):
    """Prune one circuit against multiple deception-mechanism tasks at once."""

    name = "joint"
    mechanism = "joint"

    @property
    def display_name(self) -> str:
        tasks = getattr(self, "_joint_tasks", DECEPTION_TASKS)
        return "Joint (" + "+".join(t.upper() for t in tasks) + ")"

    def supports_family(self, family: str) -> bool:
        return family == "llama"

    def prepare(self, tokenizer, device) -> dict:
        return {"joint_test_loaders": {}}

    def build_dataloaders(self, tokenizer, family, full_model, device, args, state):
        from dataset.deception_common import (
            DeceptionDatasetLlama, filter_by_model_behavior, load_dataset_config,
            load_or_generate_deception_data, resolve_margin, run_evaluation)

        joint_tasks = _normalize_joint_tasks(getattr(args, "joint_tasks", None)
                                             or list(DECEPTION_TASKS))
        self._joint_tasks = joint_tasks
        args.joint_tasks = joint_tasks

        bs = args.batch_size
        margins = []
        train_records, val_records = [], []
        test_loaders: Dict[str, DataLoader] = {}

        make_ds = lambda records: DeceptionDatasetLlama(
            records, tokenizer, max_length=args.max_seq_length)

        for sub_name in joint_tasks:
            sub = get_task(sub_name)
            path = sub.dataset_dir(args)
            config = load_dataset_config(path)
            margins.append(resolve_margin(args, config))

            train = load_or_generate_deception_data(path, "train", args.train_samples)
            val = load_or_generate_deception_data(path, "validation", args.val_samples)
            test = load_or_generate_deception_data(path, "test", args.test_samples)

            if getattr(args, "deception_runtime_filter", False):
                val, _, _ = filter_by_model_behavior(
                    val, full_model, tokenizer, device, margin_thresh=margins[-1],
                    max_length=args.max_seq_length, batch_size=bs)
                test, _, _ = filter_by_model_behavior(
                    test, full_model, tokenizer, device, margin_thresh=margins[-1],
                    max_length=args.max_seq_length, batch_size=bs)

            for rec in train:
                rec["_joint_task"] = sub_name
            for rec in val:
                rec["_joint_task"] = sub_name
            train_records.extend(train)
            val_records.extend(val)
            test_loaders[sub_name] = DataLoader(
                make_ds(test), batch_size=bs, shuffle=False)

        if len(set(margins)) > 1:
            print(f"Warning: subtask margin thresholds differ {dict(zip(joint_tasks, margins))}; "
                  f"using {margins[0]} for the joint objective.")
        state["margin"] = margins[0]
        state["joint_tasks"] = joint_tasks
        state["joint_test_loaders"] = test_loaders
        self._run_evaluation = run_evaluation

        rng = random.Random(args.seed)
        rng.shuffle(train_records)

        print(f"Joint dataset: {len(joint_tasks)} subtasks "
              f"({', '.join(joint_tasks)})")
        print(f"  train: {len(train_records)} "
              f"({len(train_records) // len(joint_tasks)} per subtask)")
        print(f"  val:   {len(val_records)} "
              f"({len(val_records) // len(joint_tasks)} per subtask)")

        train_dl = DataLoader(make_ds(train_records), batch_size=bs,
                              shuffle=getattr(args, "shuffle_train", True))
        val_dl = DataLoader(make_ds(val_records), batch_size=bs, shuffle=False)
        # Combined test loader kept for callers that expect a single test_dl.
        combined_test = []
        for sub_name in joint_tasks:
            combined_test.extend(test_loaders[sub_name].dataset.processed_data)
        test_dl = DataLoader(make_ds(combined_test), batch_size=bs, shuffle=False)
        return train_dl, val_dl, test_dl

    def build_variant_dataloader(self, variant, tokenizer, args, state):
        """The subtasks' variant test sets concatenated, in --joint-tasks order.

        DeceptionTask's implementation would look for a `<data-dir>/joint`
        directory, which does not exist: joint has no dataset of its own.
        """
        from dataset.deception_common import (DeceptionDatasetLlama,
                                              load_or_generate_deception_data)
        from evaluation import variants

        if variant not in variants.PROMPT_VARIANTS:
            return None
        joint_tasks = (state.get("joint_tasks")
                       or getattr(self, "_joint_tasks", None)
                       or list(DECEPTION_TASKS))
        records = []
        for sub_name in joint_tasks:
            sub = get_task(sub_name)
            sub_records = load_or_generate_deception_data(
                sub.dataset_dir(args), "test", args.test_samples)
            records.extend(variants.deception_records(
                sub_name, sub_records, variant, tokenizer, args.max_seq_length))
        return variants.loader(
            DeceptionDatasetLlama(records, tokenizer,
                                  max_length=args.max_seq_length),
            args.batch_size)

    def evaluate_subtasks(self, model, label_prefix, full_model, device,
                          tokenizer, state) -> Dict[str, dict]:
        """Run evaluation on each subtask's test split separately."""
        loaders = state.get("joint_test_loaders") or {}
        results = {}
        for sub_name, loader in loaders.items():
            name = f"{label_prefix} ({sub_name.upper()})"
            results[sub_name] = self._run_evaluation(
                model, name, full_model, loader, device, tokenizer=tokenizer)
        return results

    @staticmethod
    def fidelity_rows(per_task: Dict[str, dict], stage_label: str
                      ) -> List[Tuple[str, dict]]:
        rows = []
        for sub_name in sorted(per_task):
            rows.append((f"{stage_label} ({sub_name.upper()})", per_task[sub_name]))
        return rows
