# A2 original-H bank and prefix scoring launch readiness

Status: handed-back operational proposal only. No submission or model/GPU execution.

## What changed

New external `launch/` packet only. The original timing plan, frozen groups, source, data, A1 ancestry and ledgers remain unchanged. Root selected H200 prospectively: no frozen contract requires A100. `hardware-risk.json` identifies exact original source checks. Bank contracts bind model/config/source/numerical runtime; scoring requires the bank's actual GPU name/dtype/device family. The external controller additionally binds the same single visible physical GPU UUID, actual Slurm allocation and unchanged CUDA-visible environment across both original CLI children.

The target is immutable source `40fe57289405fd53a3fce02e5d4e47a0ebf78b64`, A1 ancestor `5f450dc93dac707af649dee8c8ca60888b2831db`, and the byte-identical all-nine-groups receipt. Preserve all original H train/validation IDs, both streams and all typed bank keys. The fixed pilot produces 2484 logical rows and 144 controls with `--limit 4`; the full 59652-row assay remains unadmitted. No unstable group is filtered.

## How verified

Static source/interface/metadata inspection only. No local source re-audit, tokenizer/model load, GPU probe, test or timing. Existing source proves the original CLI calls full A1 validation, original source/sidecar/code checks, then after tokenizer identity/layout validation calls current source/registry/grader `_validate_live` immediately before the original model loader. The controller supplies no `model_loader` callback, because that would set injected lineage.

Hardware preference is H200 with ample prospective memory headroom; total/free capacity is checked in the admitted allocation, not inferred from sinfo labels. Broader union capture, whole MLPs and input shapes remain unmeasured. H200 is not declared to fit by an A100 speed ratio. Preserve original BF16 model, FP32 analysis/accumulation, SDPA backend, batch eight, library/runtime/environment and all controls. Two separate original children load their own models; both startups and all CPU/protection/publication overhead count against the same one-GPU, 25-minute attempt.

## Execution evidence

No execution result is claimed. `config.json`, `commands.json`, `source-inspection.json`, `queue-observation.txt`, `static-checks.json` and final `manifest.json` contain exact prospective bindings and checks.

Root sequence:

1. Submit `cpu-preflight.sh` in a real CPU allocation, four CPUs/32 GiB/five minutes proposed. Supply fresh `A2_TIMING_PREFLIGHT_OUTPUT`. It uses actual frozen `_load_context`, `_validate_live`, receipt/bank-contract/source/geometry and canonical budget checks, without tokenizer/weights/GPU. It writes one complete CPU record or preserves failure; no retry.
2. Before GPU submission, run short `pre-submit.py` with `A2_TIMING_PREFLIGHT_COMPLETE`. Require completed CPU source/protection checks within fifteen minutes, unchanged launch hash/groups and unchanged PRIMARY live ledger since its prospective budget check. Root separately refreshes live usage, H200 account/partition/availability and budget. The worktree ledger is empty/stale and must never authorize spend.
3. Root submits one held H200 job, registers a new RS reservation for 25 minutes/one GPU, publishes the required append-only successor phase mapping, and writes external `root-release.template.json` fields bound to that actual job/reservation/account/partition/preflight and exact launch manifest. Old failures/cancellations and the held A3 reservation remain charged and unchanged. Root unholds only when ready. This agent neither submits nor writes authority.
4. The GPU controller checks actual RUNNING allocation/node/H200 GPU TRES, one visible H200, actual resource/lease, primary live ledger plus fully normalized immutable mapping, all old charges and A2/global caps. Root admission is for this exact bank/prefix attempt only, never full scoring. It records a tiny allocation-only CUDA probe UUID/name/total/free memory before the bank and again before scoring. The one-byte probe loads no model.
5. Execute the exact original bank CLI in the canonical main namespace. Preserve complete original H unions and newly measured bank/peak/provenance. Preserve any partial failure. No copied/re-signed A1 bank and no automatic retry.
6. Start the complete fixed score pilot only if the remaining actual lease exceeds the prospectively fixed 1116-second eligibility floor, which includes original A100 orientation, load/source allowance, buffer and finish reserve. This is NOT an H200 cost forecast or completion guarantee. Recheck after staging. If insufficient, retain the complete bank and stop without scoring; never reduce controls/rows or extend the attempt.
7. Exclusively create the distinct pilot namespace, copy only unchanged groups bytes, and link `pilot/bank` to the completed canonical bank. Its actual owner resolves to the main bank. Run the original `score --limit 4` on the same GPU/runtime. Read only completion execution/count metadata; do not inspect/select assessment effects. Require exact pilot counts and preserve the canonical full-score path absent. A successful prefix does not admit full scoring.

Proposed root commands, not executed:

```bash
A2_TIMING_PREFLIGHT_OUTPUT=/ROOT/FRESH/CPU/RECEIPTS sbatch --parsable --export=ALL --account=ROOT_CPU_ACCOUNT --partition=cpu --constraint=projects --ntasks=1 --cpus-per-task=4 --mem=32G --time=00:05:00 --output=/ROOT/LOGS/preflight-%j.out /ABSOLUTE/launch/cpu-preflight.sh
A2_TIMING_PREFLIGHT_COMPLETE=/ROOT/FRESH/CPU/RECEIPTS/COMPLETE.json /u/swong2/.conda/envs/mgnp/bin/python /ABSOLUTE/launch/pre-submit.py
A2_TIMING_ROOT_RELEASE=/ROOT/EXTERNAL/RELEASE.json A2_TIMING_EXECUTION_OUTPUT=/ROOT/FRESH/GPU/RECEIPTS sbatch --hold --parsable --export=ALL --account=ROOT_H200_ACCOUNT --partition=ROOT_H200_PARTITION --gres=gpu:h200:1 --constraint=projects --ntasks=1 --cpus-per-task=4 --mem=64G --time=00:25:00 --chdir=/IMMUTABLE/40fe/runtime --output=/ROOT/LOGS/timing-%j.out /ABSOLUTE/launch/gpu-timing.sh
```

Original bank/score argv are exact in `commands.json`. Shell environment fixes only original execution/cache/thread/offline settings; GPU launch never overwrites Slurm's GPU visibility or fabricates job variables. Real UUID/name is checked again before the second child, and original bank/scoring numerical-path gates remain. The 120-second finish reserve and hard Slurm lease bound both children; interrupted stages remain partial and do not resume automatically.

## What is NOT done

No model/GPU run, cache-weight read, GPU/CPU submission, RS/ledger/scheduler mutation, source/data/plan edit, efficacy inspection, Git, API/notebook/subagent or full-assay admission. No A100 contract is relabelled as H200: a new actual H200 bank must be collected and its real H200 provenance retained.

## Open questions

Root must approve exact resource commands and current budget. Live primary ledger at inspection retained all prior charges; it is not a spending authorization or future snapshot. The new reservation and successor mapping do not yet exist. H200 timing/peak/input-shape qualification remains the purpose of the bounded attempt. Unknown duration or OOM may yield only a bank or partial artifacts; that is retained evidence, not permission to retry, shrink coverage or promote the prefix.
