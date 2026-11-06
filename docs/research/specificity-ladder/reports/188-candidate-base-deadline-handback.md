# Hand-back 188: candidate base CPU deadline packet

Agent: worker. Status: handed-back. Proposal only; exact packet review and resource decision are required before use.

## What changed

New packet `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-optionA-plan/genuine-candidate-base-cpu-r4`. Manifest SHA-256 `a52c8696e83b525f64347ec8d714fb9bc450befa2e4638d6a46a6192eea8befe`; supervisor `08766a5132677faabfed1a78fe2ce7717b3d411f68859e81c5165fece4b412ad`; test `6e1bc97ed6094e1cced1cfe6957de94d6754c61b826b2f49fe3132f96c9b3080`.

The sole supervisor change from r2 adds `or elapsed>=c['CPU_child_seconds']` to the existing nonzero/TERM failure condition. A normal child reaped exactly at or after the bound cannot produce COMPLETE. `run.py`, `allocation_facts.py`, `oracle_cpu.sh`, and `config.template.json` are byte-identical to r2. The config remains SHA `77ec8f936b216bd5cd5a6e0e1945bf0b5e2be8903dc43b1b1cb6594387fc791e` with all four candidate/oracle path and hash fields null. `proposal.json` is updated and `test_deadline.py` added. All original r2 manifest members and manifest `21122c2077c367c7ccf9b08f8b865f263b7dcba66bf0480af25e14757973ed4d` remain intact.

The unmodified limits are 4 CPU, 192 GiB, one-hour Slurm, 3500 seconds initial remaining, 3300-second child limit and 15-second kill grace. These values are carried forward, not endorsed as sufficient for candidate base. Root must first consume the completed same-environment base oracle and measured timing, decide resources, and construct a distinct reviewed candidate config containing exact candidate workload and completed base receipt paths/hashes. The proposal has no fake binding.

For later root-reviewed use only, an absolute-safe shell shape is below. P is the new packet path, W the specificity worktree, C a new root-reviewed bound config, H its actual SHA, and O a fresh nonexistent output. The wrapper is invoked by an absolute path within `--wrap`, so Slurm does not substitute a spool location for `dirname "$0"`:

```bash
sbatch --account=bimc-delta-cpu --partition=cpu-interactive --constraint=projects --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=192G --time=01:00:00 --no-requeue --chdir="$W" --export=ALL,CUDA_VISIBLE_DEVICES= --output="ROOT_SELECTED_LOG-%j" --wrap="bash $P/oracle_cpu.sh --packet-sha256 a52c8696e83b525f64347ec8d714fb9bc450befa2e4638d6a46a6192eea8befe --config $C --config-sha256 $H --mode candidate --environment base --output $O"
```

This is not a submission or a resource decision. Root selects actual paths and checks current placement and approval; no automatic retry.

## How verified

Before the fix, both interpreters ran the copied supervisor with fake clock and child. In each, `test_reaped_normal_exit_at_or_after_limit_fails` exited 1 with two expected failures at 3300 and 3301 seconds. After the fix:

```bash
PYTHONDONTWRITEBYTECODE=1 /sw/external/python/anaconda3/bin/python3.9 -m unittest -v test_deadline
```

```bash
PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python -m unittest -v test_deadline
```

Both exited 0 with five tests, including before-bound normal exit, at/after-bound rejection, TERM then KILL and terminated zero exit, and simulated child failures. Logs are retained in the packet. Both interpreters parsed all Python files; `bash -n oracle_cpu.sh` passed. A byte comparison and manifest rehash established the preservation inventory above.

## Execution evidence

Local fake-supervisor tests only; RED and GREEN exits/counts are above. No Slurm job or scientific output, rows or baseline. The original frozen input source remains commit `861f84a3938a5e22fa329af0c469b2dd812fe68a`; packet provenance is the r4 manifest above. The simulated missing-stream/postguard cases represent nonzero child exit and do not independently execute `run.py`.

## What is NOT done

No candidate binding, actual oracle validation, genuine CPU work, model, scheduler, git, RS or remote operation. No speedup, equivalence, scientific acceptance, or future resource feasibility is claimed.

## Open questions

Root should assess actual base-reference timing and independent packet/source review before binding the candidate and selecting a reviewed resource envelope. Default: do not launch while those gates remain unresolved.
