"""
tasks package — uniform Task interface + registry.

A `Task` bundles everything that differs between IOI / GP / GT:
  * which dataset to build (and its GPT-2 vs Llama variant),
  * how to read the clean / corrupted / mask tensors out of a batch,
  * the training objective (KL term + optional task-margin term),
  * task-specific evaluation and which fidelity metrics to report.

The training loops in pruning.py and the CLI in train.py consume only this
interface, so adding a task means adding one module here.
"""


class Task:
    """Base class. Subclasses set the class attributes and implement the hooks."""

    name = ""
    display_name = ""

    # Batch keys for the model inputs (GT uses the `clean_*` variants).
    clean_key = "input_ids"
    mask_key = "attention_mask"
    corrupt_key = "corrupted_input_ids"

    # Fidelity columns reported in the summary table: list of (result_key, label).
    metric_columns = [
        ("accuracy", "Accuracy"),
        ("logit_diff", "Logit Diff"),
        ("kl_div", "KL Div"),
        ("exact_match", "Exact Match"),
    ]

    # ---- capability ----------------------------------------------------
    def supports_family(self, family: str) -> bool:
        return True

    # ---- per-run state (e.g. GT digit-token map) -----------------------
    def prepare(self, tokenizer, device) -> dict:
        return {}

    # ---- data ----------------------------------------------------------
    def build_dataloaders(self, tokenizer, family, full_model, device, args, state):
        """Return (train_dl, val_dl, test_dl). Also caches the module's
        run_evaluation for use in `evaluate`. `state` comes from `prepare`."""
        raise NotImplementedError

    # ---- input plumbing ------------------------------------------------
    def model_inputs(self, batch) -> dict:
        return dict(
            input_ids=batch[self.clean_key],
            corrupted_input_ids=batch[self.corrupt_key],
            attention_mask=batch[self.mask_key],
        )

    def target_inputs(self, batch) -> dict:
        return dict(input_ids=batch[self.clean_key],
                    attention_mask=batch[self.mask_key])

    # ---- objective -----------------------------------------------------
    def compute_objective(self, circuit_logits, target_logits, batch, state, device):
        """Return (kl_loss, task_loss). The loop forms
        loss = (1 - lambda_sp) * (kl_loss + task_loss) + lambda_sp * sparsity."""
        raise NotImplementedError

    # ---- evaluation ----------------------------------------------------
    def evaluate(self, model, name, full_model, loader, device, tokenizer, state) -> dict:
        raise NotImplementedError


_TASKS = {}


def get_task(name: str) -> Task:
    if name not in _TASKS:
        # Lazy import so only the requested task's dataset module is loaded.
        if name == "ioi":
            from tasks.ioi import IOITask
            _TASKS[name] = IOITask
        elif name == "gp":
            from tasks.gp import GPTask
            _TASKS[name] = GPTask
        elif name == "gt":
            from tasks.gt import GTTask
            _TASKS[name] = GTTask
        elif name == "std":
            from tasks.std import STDTask
            _TASKS[name] = STDTask
        else:
            raise ValueError(f"Unknown task {name!r}. Choose from {list_tasks()}.")
    return _TASKS[name]()


def list_tasks():
    return ["ioi", "gp", "gt", "std"]
