"""Login-node check of outputs/_launch_mechanism_v2/submit_train.sh (ticket 05). Re-run before any fine-run go.
usage: /u/swong2/.conda/envs/mgnp/bin/python -I outputs/_launch_mechanism_v2/check_launcher.py   (CPU only; calls sbatch --test-only only in refusal checks, which exit before sbatch)

Runs the launcher's --dry and --plan modes, then for every printed sbatch line:
  * required flags present, coarse/fine flag sets correct, slug correct
  * train.build_parser().parse_args(...) accepts it, resolve_args succeeds
  * get_task(task).dataset_dir(args) resolves to data/datasets/<task>[_honest] and exists
  * resolved_run_config matches the reference config except task, deception_condition,
    deception_margin_loss (0.7 vs null) and output_dir
  * resolve_margin prefers --deception-margin-loss over the dataset's margin_thresh
Also checks that test-only/submit default to the 6 coarse runs and that a fine run is refused
without --include-fine.  Exit 0 = all checks pass.
"""
import json
import os
import re
import shlex
import subprocess
import sys

WT = "/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/mechanism-datasets"
MAIN = "/projects/beto/swong2/Alignment/Deception-Circuit"
LAUNCHER = os.path.join(WT, "outputs/_launch_mechanism_v2/submit_train.sh")
REF_COARSE = os.path.join(MAIN, "outputs/llama-8b-instruct_sdr_coarse/"
                          "nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742/config.coarse.json")
REF_FINE = os.path.join(MAIN, "outputs/llama-8b-instruct_sdr/nls0.3_noedge_260819-083414/config.json")
sys.path.insert(0, WT)
os.chdir(WT)

import train  # noqa: E402
from run_io import resolved_run_config, build_run_slug  # noqa: E402
from tasks import get_task  # noqa: E402
from dataset.deception_common import load_dataset_config, resolve_margin  # noqa: E402

COMMON = ("--node-lambda-sparsity 0.3 --no-edge-pruning --seed 42 --node-epochs 500 --lr 0.03 "
          "--batch-size 7 --max-seq-length 120 --train-samples 200 --val-samples 200 "
          "--test-samples 1000 --deception-margin-loss 0.7").split()
COARSE = "--no-prune-attention-neurons --no-prune-mlp-hidden --no-prune-mlp-output --no-prune-mlp-blocks".split()
EXPECTED_DIFF = {"task", "deception_condition", "deception_margin_loss", "output_dir"}
TASKS = ["far_v2", "sdr_v2", "ser_v2"]
fails = []
notes = set()


def check(cond, msg):
    if not cond:
        fails.append(msg)
    return cond


def run(*args):
    return subprocess.run(["bash", LAUNCHER, *args], capture_output=True, text=True, timeout=120)


def has_seq(tokens, seq):
    return any(tokens[i:i + len(seq)] == seq for i in range(len(tokens) - len(seq) + 1))


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flatten(v, prefix + k + "."))
        else:
            out[prefix + k] = v
    return out


if not os.path.exists(LAUNCHER):
    print("FAIL: launcher missing:", LAUNCHER)
    sys.exit(1)

dry = run("--dry")
check(dry.returncode == 0, f"--dry exit {dry.returncode}: {dry.stderr}")
lines = [l for l in dry.stdout.splitlines() if l.startswith("sbatch ")]
check(len(lines) == 12, f"--dry printed {len(lines)} sbatch lines, expected 12")

ref = {"coarse": flatten(json.load(open(REF_COARSE))), "fine": flatten(json.load(open(REF_FINE)))}
seen = set()
for line in lines:
    toks = shlex.split(line)
    i = toks.index("scripts/train_deception.sbatch")
    sb, task, rest = toks[1:i], toks[i + 1], toks[i + 2:]
    opts = dict(t.split("=", 1) for t in sb if t.startswith("--") and "=" in t)
    check(opts.get("--partition") == "gpuH200x8", f"default partition {opts.get('--partition')}")
    check(opts.get("--time") == "01:30:00", f"default time {opts.get('--time')}")
    check("PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True" in opts.get("--export", ""), "export")
    cond = rest[rest.index("--deception-condition") + 1]
    kind = "coarse" if "--no-prune-mlp-blocks" in rest else "fine"
    seen.add((task, cond, kind))
    tag = f"[{task} {cond} {kind}]"
    check(task in TASKS, f"{tag} task")
    check(has_seq(rest, COMMON), f"{tag} common settings not passed verbatim")
    if kind == "coarse":
        check(has_seq(rest, COARSE), f"{tag} coarse flags")
        out = rest[rest.index("--output-dir") + 1]
        hon = "_honest" if cond == "honest" else ""
        pat = rf"^outputs/llama-8b-instruct_{task}_coarse/nls0\.3{hon}_noedge_noan_nomh_nomo_nomb_\d{{6}}-\d{{6}}$"
        check(re.match(pat, out), f"{tag} output dir {out}")
    else:
        check(not any(f in rest for f in COARSE), f"{tag} fine line has coarse flags")
        check("--output-dir" not in rest, f"{tag} fine line passes --output-dir (default slug expected)")
    argv = ["--model", "llama-8b-instruct", "--task", task] + rest
    args = train.build_parser().parse_args(argv)
    node_cfg, edge_cfg = train.resolve_args(args)
    ddir = get_task(task).dataset_dir(args)
    want = f"./data/datasets/{task}" + ("_honest" if cond == "honest" else "")
    check(os.path.normpath(ddir) == os.path.normpath(want), f"{tag} dataset_dir {ddir} != {want}")
    check(os.path.isdir(ddir), f"{tag} dataset dir missing {ddir}")
    check(resolve_margin(args, load_dataset_config(ddir)) == 0.7, f"{tag} margin override not 0.7")
    if kind == "fine":
        slug = build_run_slug(args, node_cfg)
        want_slug = "nls0.3" + ("_honest" if cond == "honest" else "") + "_noedge"
        check(re.match(rf"^{want_slug}_\d{{6}}-\d{{6}}$", slug), f"{tag} default slug {slug}")
        args.output_dir = f"outputs/llama-8b-instruct_{task}/{slug}"
    cfg = flatten(resolved_run_config(args, node_cfg, edge_cfg))
    r = ref[kind]
    diff = {k for k in set(cfg) | set(r) if cfg.get(k, "<absent>") != r.get(k, "<absent>")}
    # keys the 2026-08-19 fine reference predates; inert for a non-joint task
    schema_new = {k for k in diff if k not in r and (k, cfg[k]) in {("joint_tasks", None), ("joint_scale_epochs", True)}}
    if schema_new:
        notes.add(f"{kind} reference lacks {sorted(schema_new)} (added to config.json later; inert defaults)")
    diff -= schema_new
    check(diff <= EXPECTED_DIFF, f"{tag} unexpected config diffs vs reference: "
          + ", ".join(f"{k}: {cfg.get(k, '<absent>')!r} vs ref {r.get(k, '<absent>')!r}" for k in sorted(diff - EXPECTED_DIFF)))
    check(cfg["deception_margin_loss"] == 0.7 and r["deception_margin_loss"] is None, f"{tag} margin 0.7 vs ref null")
    check(cfg["deception_condition"] == cond, f"{tag} condition")

check(seen == {(t, c, k) for t in TASKS for c in ("deceptive", "honest") for k in ("coarse", "fine")},
      f"run set {sorted(seen)}")

plan = run("--plan")
check(plan.returncode == 0, f"--plan exit {plan.returncode}: {plan.stderr}")
sel = plan.stdout.split()
check(sorted(sel) == sorted(f"{t}_{c}_coarse" for t in TASKS for c in ("D", "H")), f"--plan default selection {sel}")
plan_f = run("--plan", "--include-fine")
check(len(plan_f.stdout.split()) == 12, f"--plan --include-fine selection {plan_f.stdout.split()}")
refuse = run("--test-only", "--only", "far_v2_D_fine")
check(refuse.returncode == 2 and "--include-fine" in refuse.stderr, f"fine refusal: rc {refuse.returncode} {refuse.stderr!r}")
bad_p = run("--test-only", "--partition", "gpuA100x4")
check(bad_p.returncode == 2, f"A100 partition not refused: rc {bad_p.returncode}")
mixed = run("--dry", "--partition", "gpuH200x8,gpuA40x4")
check(mixed.returncode == 0 and "--time=03:00:00" in mixed.stdout, f"widened pair dry: rc {mixed.returncode} {mixed.stderr!r}")
short = run("--test-only", "--partition", "gpuH200x8,gpuA40x4", "--time", "01:30:00")
check(short.returncode == 2, f"A40 pair with 01:30:00 not refused: rc {short.returncode}")
other = run("--test-only", "--partition", "gpuH200x8,gpuA100x4")
check(other.returncode == 2, f"pair with A100 not refused: rc {other.returncode}")
a40 = run("--dry", "--partition", "gpuA40x4")
check("--time=03:00:00" in a40.stdout, "A40 fallback default time not 03:00:00")
ia = run("--dry", "--partition", "gpuH200x8-interactive", "--only", "far_v2_D_coarse")
check(ia.returncode == 0 and sum(l.startswith("sbatch ") for l in ia.stdout.splitlines()) == 1 and "--time=01:00:00" in ia.stdout
      and "--partition=gpuH200x8-interactive" in ia.stdout, f"interactive dry: {ia.stdout!r} {ia.stderr!r}")
ia2 = run("--test-only", "--partition", "gpuH200x8-interactive")
check(ia2.returncode == 2, f"interactive without --only not refused: rc {ia2.returncode}")
ia3 = run("--test-only", "--partition", "gpuH200x8-interactive", "--only", "far_v2_D_coarse far_v2_H_coarse")
check(ia3.returncode == 2, f"interactive with two runs not refused: rc {ia3.returncode}")
ia4 = run("--test-only", "--partition", "gpuH200x8-interactive", "--time", "01:30:00", "--only", "far_v2_D_coarse")
check(ia4.returncode == 2, f"interactive over cap not refused: rc {ia4.returncode}")

if fails:
    print(f"FAIL ({len(fails)}):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
for n in sorted(notes):
    print("NOTE:", n)
print(f"PASS: {len(lines)} dry lines; coarse/fine flags, slugs, parser, resolve_args, dataset dirs, "
      "margin override, config-vs-reference, selection and refusals all OK")
