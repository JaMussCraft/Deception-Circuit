# 07 — Set up Bridges-2 (PSC) as a second GPU cluster dispatched from Delta

**What to do:** make the evaluation pipeline runnable on Bridges-2 via SSH multiplexing from Delta, with Delta as
the canonical copy of code and results.

**Status:** resolved
**Type:** task
**Blocked by:** SSH masters opened by the user (orchestrator confirms); branch pushed (done by the orchestrator).
**GPU allocation:** 1 H100 GPU-h for smoke tests (ledger section `bridges2`).

## Facts to build on

- Recon: `reports/06-recon-evals-and-bridges2.md` Part B (env pins, model cache, hard-coded paths, Bridges-2
  partitions; V100 unusable; use GPU-shared with `--gpus=h100-80:1`).
- Hosts: `bridges2.psc.edu` (login, Slurm) and `data.bridges2.psc.edu` (transfers). SSH config aliases `bridges2`
  and `b2dtn` with ControlMaster sockets in `~/.ssh/cm/` (written by the orchestrator). Every rsync runs FROM
  Delta. Username swong2. Allocation id: read with `projects` on Bridges-2 and record it.
- Never copy `~/.bashrc` or any API key to Bridges-2. Use `HF_HUB_OFFLINE=1` with the copied snapshot.
- Code lives at `https://github.com/JaMussCraft/Deception-Circuit.git`, branch `mechanism-datasets`.

## Acceptance criteria

- [x] `scripts/cluster/delta.env` (reproduces today's Delta behaviour exactly) and `scripts/cluster/bridges2.env`
      exporting `DC_ACCOUNT, DC_PARTITION, DC_GPU_SPEC, DC_ACTIVATE, DC_HF_HOME, DC_HF_OFFLINE, DC_REPO_ROOT,
      DC_TIME_DEFAULT`; `scripts/evaluate_circuit.sbatch` sources `scripts/cluster/${DC_CLUSTER:-delta}.env` and
      behaves identically to before when `DC_CLUSTER` is unset (diff of a `--dry` Delta line before/after).
- [x] `scripts/remote/b2.sh {sync-code|sync-data|submit|status|fetch}` on Delta: code via `git pull` on Bridges-2
      (branch mechanism-datasets), data via rsync to b2dtn (datasets are in git; run dirs, operand, model
      snapshot, wikitext cache go by rsync), `fetch` rsyncs `evaluations*/` and suite output dirs back into the
      worktree without overwriting newer Delta files (`--update`, `--ignore-existing` where appropriate).
- [x] Environment on Bridges-2: conda-pack of mgnp (preferred) or a pinned rebuild (torch 2.11.0+cu128,
      transformers 5.13.0, datasets 5.0.0, accelerate 1.15.0; record which); `python -c "import torch; print(torch.cuda.is_available())"`
      on an h100-80 GPU-shared smoke job prints True; one `evaluate_circuit.py --dry-run`-style parser check passes.
- [x] Model snapshot + wikitext cache present under the Bridges-2 `$DC_HF_HOME`; offline load verified in the smoke job.
- [x] A short `docs/bridges2.md` (or section in CONTEXT.md): layout on Bridges-2 (/ocean path), how to open the
      SSH masters, how to dispatch and fetch, the one-GPU-type rule, the "Delta is canonical" rule, the relocation note.
- [x] Ledger `bridges2` section created (SU rate 2 per H100 GPU-h) and the smoke job reconciled.
- [x] Review in `reports/07-bridges2-second-cluster-review.md`; progress in `reports/07-handback.md`.

## Comments

**Phase A done on 2026-10-24. Blocked on the SSH masters.**

The details are in `reports/07-handback.md` and `reports/07-bridges2-second-cluster-review.md`.

- **Criterion 1 is ticked.** The wrapper has no `--dry`, and the hard stop forbids evaluate_circuit.py.
  The proof is a stub run of the original and the new wrapper, and the `#SBATCH`, stdout and stderr diffs
  are all empty. A pytest also pins the old trace.
- **Criterion 2 is implemented but unticked.** The `--dry` output is tested, and the fetch semantics were
  checked with a local rsync. The first live transfer happens in Phase B. Code sync uses `fetch` plus
  `merge --ff-only` rather than a literal `git pull`.
- **Criterion 3 is partial.** It uses conda-pack, not a rebuild. Job 23156522 produced
  `/work/nvme/beto/swong2/envs/mgnp-conda-pack.tar.gz` (5.56 GB), which unpacks and imports the pinned
  versions on Delta. The h100 smoke job is Phase B. The parser check calls build_parser and resolve_cli
  only, and its CPU path passed on the login node.
- **Criterion 4 is partial.** Offline load from a manifest-only HF_HOME was verified on Delta.
  Bridges-2 is Phase B.
- **Criterion 6 is partial.** The ledger section exists. The smoke reconciliation is Phase B.
- **Tests.** Both envs fail only the 8 baseline names.
- **Commit and push.** The orchestrator must commit and push the files listed in the handback before
  Phase B sync-code.

**Phase B done on 2026-10-24. Resolved.**

- **Smoke job.** Bridges-2 job 49773269 printed SMOKE PASS on an H100 80GB, sm_90. CUDA was True, the
  model and wikitext loaded offline, and the parser check passed. The model load took 458 s from /ocean.
- **Failed first attempt.** Job 49772768 failed after 3 s because Bridges-2 sets `SBATCH_EXPORT=NONE`.
  b2.sh now passes `--export=ALL,...`.
- **Settings.** The allocation is cis260361p, and the root is `/ocean/projects/cis260361p/swong2/`. The GPU
  spec is `--gpus-per-node=h100-80:1 --cpus-per-task=1 --mem=64G`, settled with `--test-only`. BLAS threads
  are pinned to 1 in both profiles, as the orchestrator asked.
- **Environment.** The conda-pack env is unpacked and was checked by checksum.
- **Model and wikitext.** The model snapshot and wikitext are on Bridges-2, checked by sha256 and totals.
- **Ledger.** The `bridges2` section shows 0.5 GPU-h, or 1.0 SU, committed against ticket 07's 1.0 GPU-h.
- **Fixed during Phase B.** The transfer host needed directories created through the login host. Fetch had
  been rewriting Delta file metadata; that is now prevented, and the 989 affected files have their
  permissions restored.
- **Commit list.** The Phase B commit list is in `reports/07-handback.md`.
