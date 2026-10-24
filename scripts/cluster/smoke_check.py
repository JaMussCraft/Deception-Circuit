"""Smoke check for a new cluster (ticket 07): GPU visible, model and wikitext load offline, evaluate_circuit parses.

Run by scripts/cluster/bridges2_smoke.sbatch from the repo root. It never evaluates a circuit: the
evaluate_circuit.py check builds the real argparse parser and resolve_cli() on the v2 run dirs and stops there.

    python scripts/cluster/smoke_check.py            # on a GPU node
    python scripts/cluster/smoke_check.py --no-model # CPU path for a login-node dry run: skips CUDA, model, wikitext
"""

import argparse
import os
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)

MODEL = "llama-8b-instruct"
V2_RUN_DIRS = [
    "outputs/llama-8b-instruct_far_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140717",
    "outputs/llama-8b-instruct_far_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323",
    "outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-140323",
    "outputs/llama-8b-instruct_sdr_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323",
    "outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_261021-173101",
    "outputs/llama-8b-instruct_ser_v2_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_261021-140323",
]


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{': ' + detail if detail else ''}", flush=True)
    return bool(ok)


def check_env():
    keys = ("HF_HOME", "HF_HUB_OFFLINE", "HF_DATASETS_OFFLINE", "TRANSFORMERS_OFFLINE", "CONDA_PREFIX",
            "VIRTUAL_ENV", "SLURM_JOB_ID", "SLURM_JOB_PARTITION")
    for k in keys:
        print(f"  {k}={os.environ.get(k, '<unset>')}")
    import torch
    import transformers
    import datasets
    import accelerate
    print(f"  python {sys.version.split()[0]}  torch {torch.__version__}  transformers {transformers.__version__}  "
          f"datasets {datasets.__version__}  accelerate {accelerate.__version__}")
    return True


def check_cuda():
    import torch
    avail = torch.cuda.is_available()
    print(f"torch.cuda.is_available() = {avail}", flush=True)
    if not avail:
        return check("cuda", False, "no CUDA device (driver too old for cu128, or no GPU allocated)")
    cap = torch.cuda.get_device_capability(0)
    return check("cuda", True, f"{torch.cuda.get_device_name(0)} sm_{cap[0]}{cap[1]}, "
                               f"arch list {torch.cuda.get_arch_list()}")


def check_model():
    import torch
    from models import ModelAdapter
    ok = check("hub offline", os.environ.get("HF_HUB_OFFLINE") == "1")
    t0 = time.time()
    adapter = ModelAdapter(MODEL)
    tok = adapter.load_tokenizer()
    model = adapter.load_full_model("cuda")
    load_s = time.time() - t0
    msgs = [{"role": "user", "content": "What is the capital of France? Answer in one word."}]
    ids = tok.apply_chat_template(msgs, add_generation_prompt=True, return_tensors="pt")
    if not torch.is_tensor(ids):  # transformers 5 returns a BatchEncoding
        ids = ids["input_ids"]
    with torch.no_grad():
        logits = model(ids.to("cuda")).logits[0, -1].float()
    top = tok.decode(int(logits.argmax()))
    ok &= check("model offline load", True, f"{adapter.hf_id} bf16 in {load_s:.0f}s, "
                                             f"dtype {next(model.parameters()).dtype}, next token {top!r}")
    # An observation, not a pass condition: the smoke job tests infrastructure, not the model's wording.
    print(f"  observation: next token {top!r} ({'contains' if 'Paris' in top else 'does not contain'} 'Paris')")
    return ok


def check_wikitext():
    from datasets import load_dataset
    ds = load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split="test")
    return check("wikitext offline load", len(ds) > 0, f"{len(ds)} rows")


def check_parser():
    """Parser-level check only: argparse + resolve_cli on the v2 run dirs, no session, no evaluation."""
    import evaluate_circuit
    ok = True
    for rd in V2_RUN_DIRS:
        full = os.path.join(REPO, rd)
        present = all(os.path.isfile(os.path.join(full, f)) for f in ("config.json", "active_nodes.json"))
        ok &= check("run dir", present, rd)
    argv = [V2_RUN_DIRS[2], "--evals", "sanity", "knockout", "--device", "cpu"]
    cli = evaluate_circuit.resolve_cli(evaluate_circuit.build_parser().parse_args(argv))
    ok &= check("evaluate_circuit parser", cli.run_dir == V2_RUN_DIRS[2] and cli.evals == ["sanity", "knockout"],
                f"legacy={cli.legacy} output_dir={cli.output_dir}")
    return ok


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--no-model", action="store_true", help="skip CUDA, model and wikitext (login-node dry path)")
    a = p.parse_args()
    ok = check_env()
    if not a.no_model:
        ok &= check_cuda()
        ok &= check_wikitext()
        ok &= check_model()
    ok &= check_parser()
    print("SMOKE " + ("PASS" if ok else "FAIL"), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
