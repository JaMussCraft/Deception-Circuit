# Operator preflight

Observed 2026-10-20 23:42 UTC. No GPU allocation/reservation/submission made.

- Existing user jobs: none (`squeue -u swong2`).
- Both gpuH200x8 and gpuH200x8-interactive UP; latter hard max01:00:00, one-node allocation, GPU type h200.
- Fresh user fairshare: bgrb-delta-gpu0.084770; beto-delta-gpu0.067494; bimc-delta-gpu0.059101. Recheck immediately before submission; projected-start test waits for final wrapper.
- Python `/u/swong2/.conda/envs/mgnp/bin/python`:3.12.13, torch2.11.0+cu128, transformers5.13.0.
- HF cache `/work/nvme/beto/swong2/hub`; local model snapshot `/work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659`. Config, tokenizer files, index and all4 safetensors shards exist. Offline AutoTokenizer validation succeeded (TokenizersBackend,128256 vocab,eos128009). No model loaded.
- Worktree `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot`; output only within `outputs/_analyses/sdr-routing-pilot/<run-id>/`; create worktree logs directory before submission.
- No repository-local CLAUDE.md or .claude/CLAUDE.md found in Deception-Circuit main or pilot worktree; shared Alignment/.claude/CLAUDE.md read.

Pending launch template (not run; placeholder must be replaced after review):

```bash
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot
sbatch --parsable --account=bgrb-delta-gpu --partition=gpuH200x8-interactive --nodes=1 --gpus-per-node=1 --cpus-per-task=1 --mem=64G --time=00:XX:00 --output=logs/sdr_routing_pilot_%j.out scripts/sdr_routing_pilot.sbatch <reviewed CLI>
```

Lead requests20–30min first reservation where bounded grid estimate supports it, stage1 cumulative reservations<=3600GPU-sec including failures. Need actual-wrapper CPU dry-run, frozen CPU manifest, planned-forward/time count, independent graph/numeric/test review, and explicit lead submission instruction. Before sbatch write exact phase/time/GPU reservation to ledger atomically. Pending jobs count as reserved, failed allocations count, actual runtime never replenishes budget. Stage2 requires written viability gate and separate lead instruction. No automatic retries, account moves or expansion.

## Wrapper preflight,2026-10-20

Actual wrapper now inspected. Uses direct mgnp interpreter, offline HF flags,4CPUs,`--gres=gpu:h200:1`; validates Slurm allocation remaining120..3600s, lead `SDR_ALLOCATED_SECONDS`, prior stage1 reservations, and internal deadline remaining−90 capped3300s. Wrapper executes no GPU operation for `--dry-run`. Lead/worker report actual wrapper CPU dry-run passed; independent review/final manifest pending.

Scheduler dry-run only (no submission): actual wrapper accepted on all three accounts with30min,1H200,4CPU,64G. Predicted starts (cluster local time, estimates only): bgrb20:00:47, beto20:08:47, bimc20:14:47 on2026-10-20. Pseudo job IDs returned by `--test-only` are not real allocations/reservations.

Current nonfinal CPU manifest: primary-repo `outputs/_analyses/sdr-routing-pilot/cpu-task1-wrapper/manifest.json`, hash d7d33b96f38dc14097e20bc2774c8c7dd0e99e500d6b31165832eedbf1cb21ef.48groups24/24;480variants; semantic pass;120 baseline/self calls plus empty control. Unselected-pair theoretical bound115800row patches. Worker gives selected matching bound57600rows≈7204batch8calls (family-boundary overhead included), plus121baseline/self/empty calls. No reliable current batch8 GPU throughput before calibration. A30min allocation with<=1710s internal deadline needs<=0.233s/batch even ignoring load/writes to finish that upperbound;20min needs<=0.150s/batch. Recommend30min first reservation for bounded calibration/support checkpoint if partial-grid result is explicitly accepted; cannot promise complete grid from CPU evidence.

Corrected proposed submission template (not executed):

```bash
sbatch --parsable --account=bgrb-delta-gpu --partition=gpuH200x8-interactive --nodes=1 --gres=gpu:h200:1 --cpus-per-task=4 --mem=64G --time=00:30:00 --export=ALL,SDR_ALLOCATED_SECONDS=1800,SDR_PRIOR_RESERVED_GPU_SECONDS=0 --output=<worktree>/logs/sdr_routing_pilot_%j.out <worktree>/scripts/sdr_routing_pilot.sbatch --output <worktree>/outputs/_analyses/sdr-routing-pilot/<run-id> --manifest <final-reviewed-CPU-manifest>
```

No reservation made. Waiting for final CPU manifest/source fingerprints, independent graph/numeric review, and lead launch instruction.

Lead grid ruling supersedes preceding selected bound: <=12 fixed pairs/story×6families×2 primary scopes(readout,common)<=6912patch rows (<=864batch8calls plus~121baseline/self/control calls, with possible family-boundary overhead). Full480baselines/support remain. Extra pressureclauses baseline-only; fixed reciprocalP/H/N+truthcounterbalance/nonselfcontrols. Exact subset must be frozen before inference and independently reviewed.30min internal<=1710s permits~1.73s/call ignoring load/writes at this bound. No measured-throughput promise; incomplete cells explicitly counted. No reservation until final grid+review+lead instruction.
