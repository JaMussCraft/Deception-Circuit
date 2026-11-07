# Task 1 — RED_READY (intermediate; implementation has not started)

## What changed

Only the new candidate test and Task 1 packet/report files were written. All 360 existing Python/shell source files match the accepted optionA oracle, including untouched runtime hash `ac56b1ce177a095115e4f9cca7b61519e6c3344acd50ec218832e2908aad1b07`. No generic publisher, reader, reference, witness, workload or native file changed.

- Candidate test: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/tests/test_a3_prepared_pilot_target.py`.
- Packet: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1`.
- Test SHA256: `9a9ae6e2eff235e4ddf95447681204e9a03eb74adc149a1dcc30788aa9e53790`.
- Source pins SHA256: `853cc03f5c1247c699496c0fc1baa6c93ab5c45318a4e3b2316e5332d52e9990`.

The packet freezes 361 candidate Python/shell sources, 360 oracle sources, and five packet source/interface files. It includes `interface-ruling.json`, independent exact emitted-byte literals, original publisher fixtures, corruption of either target or preparation, re-signed writer/reader races, frozen reference/value mutation, native prefit inventory seam without a model, and alias/replacement/sibling lifetime cases. The reader observation test intercepts actual target file reads and actual SHA/parse/freeze calls, including buffer identity; it separately checks two startup reads and the final witness's one additional read. These count logical bytes, not physical disk I/O. The private witness itself is untouched.

## How verified

Static Python AST parsing and `bash -n` returned zero. Running the wrapper with `--dry-run` returned zero and reported 55 parametrized cases without importing candidate/oracle modules or executing pytest. A copy of the wrapper relocated into a temporary Slurm-style spool directory, invoked from another working directory, resolved the exact same absolute packet and commands. See `task1/run_manifest.json` and `task1/dry-run.json` for the local dry-run provenance. The runtime diff is empty; `task1/test-red.diff` contains the new tests.

## Execution evidence

No pytest or scheduler submission has been performed by this worker. Expected root RED per interpreter: 55 test-body failures, zero errors or skips, pytest exit one, each failure naming missing `_publish_prepared_target_object`, `_read_prepared_target_object`, or `_prepared_namespace_identity`. The packet only reports `RED_EXPECTED` after checking every JUnit failure message, exact counts, oracle primitive publisher baseline, source pins before/after, and candidate/oracle import origins. Intentional RED exits are recorded as pytest exit one; packet normal completion exits zero. A killed/partial run cannot carry the normal-completion flag.

Local wrapper dry-run: exit zero, 55 planned cases against 55 expected cases; direct and relocated wrapper command descriptions equal. Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1/run_manifest.json`, accepted baseline commit `538109e809285b6ddc45d42df8786270a65f7b12`. This is packaging evidence only. The actual oracle byte baseline and attributable RED have not yet run.

## What is NOT done

No transport implementation, GREEN run, full-suite run, independent semantic review, source publication, RS change, git, remote action, model construction, GPU action, or execution admission. Task 1 remains incomplete. Root must run RED before authorizing implementation; the same frozen tests subsequently run GREEN with a separately pinned implementation revision. Root owns research-report linting because this worker is prohibited from invoking RS.

## Open questions

Root commands, from any working directory (no scheduler command has been executed here):

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1/cpu.sbatch --dry-run
```

Proposed bounded resource request: one CPU, four GiB, five minutes, dual environments sequentially. Select the actual permitted CPU account/partition at submission; the following is the concrete Delta proposal:

```bash
sbatch --account=beto --partition=cpu --cpus-per-task=1 --mem=4G --time=00:05:00 --output=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1/red-slurm-%j.log /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1/cpu.sbatch --mode RED --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1/red-run-01
```

Return the terminal job evidence and `red-run-01/run_manifest.json`; do not change source while this job is active. The implementation default is STOP until root accepts attributable RED. The native fixture first resolves the missing reader in its body, so it does not build any inventory in RED. Its subsequent GREEN use is fixture evidence only, not a genuine producer/receiver resource bound or native numerical gate.
