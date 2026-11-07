# Task 1 — GREEN_READY-r3 (root rerun and acceptance remain)

## What changed

Only the native fixture expectation in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/tests/test_a3_prepared_pilot_target.py` changed in this revision, as authorized by root following independent review 193. The native builder retains Python tuples; the original JSON publisher serializes them as arrays. The old chained comparison incorrectly required Python-type equality across that serialization.

The corrected case compares the frozen result to both original published JSON representations, compares its canonical digest to the native builder value, and checks exact payload bytes against the native publisher. The original inventory digest, positive exact expected-key count, final witness and every other assertion remain. No tuple restoration or production change was introduced. The suite still has 55 cases per interpreter.

Runtime `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py` is byte-identical to the independently reviewed r2 source. Its 113 original functions/classes and all other original module statements remain unchanged from the accepted oracle. The generic publisher/reader/reference/witness/workload/native code remains unchanged.

## Frozen revision

- Packet: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3`.
- Unchanged runtime SHA256: `f39162481d54b9e86119cf4528ba0d9a9c90809e41daf101053891206ee2c6b9`.
- Corrected test SHA256: `4082bc6d81fc86479bf9cb0e44f3a49afc75533f7cd7c26c0f6d21c5fcba2097`.
- Source-pins SHA256: `6a7756fe46db30cea28b26b5926bd24d4de529c8e168357523019c39a7df2e29`.
- One-hunk correction: `task1-green-r3/test-correction.diff`, SHA256 `3328bd8fb57d3e99255c9ba306d48be920ed7adcdc69b6b23350f5cc0fddbbb3`.
- Rationale: `task1-green-r3/test-correction-rationale.json`.

Original test `9a9ae6e2eff235e4ddf95447681204e9a03eb74adc149a1dcc30788aa9e53790` remains in the immutable RED and failed GREEN-r2 packets. All prior packets, failed results and exact runtime snapshots are preserved. The prior complete implementation report is retained at `task1-green-r3/previous-task-report.md`; current runtime diff/source are in `task1-green-r3/runtime.diff` and `task1-green-r3/runtime-source.py`.

## How verified

Static AST comparison shows exactly one changed test function, `test_prepared_native_prefit_inventory_seam_without_model`. The runtime matches the r2 snapshot byte-for-byte. Static AST parsing, `bash -n`, source-pin checks and direct/relocated stdlib-only wrapper dry-runs returned zero, planning the same 55 cases per interpreter. A relocated Slurm-style wrapper from another working directory resolves the same absolute packet. Local packaging provenance is `task1-green-r3/run_manifest.json`, with `pytest_executed=false`. No heavy test or scheduler command ran in this worker.

## Execution evidence

The actual root GREEN-r2 job `23612764` on Delta failed, as retained. Base had 54 passes and one failure out of 55 cases, zero errors/skips; mgnp did not run because the packet stopped after the base failure. The failure is the corrected native Python-tuple versus published-JSON assertion. The base untouched oracle emitted 62 bytes against expected 62 bytes. Root's failed provenance is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r2/green-run-01/run_manifest.json`, accepted baseline commit `538109e809285b6ddc45d42df8786270a65f7b12`, manifest SHA256 `0d9d1ea125810251047e4cf748d49fadbf99b8993d2ab31394132598bd7ff98d`. Its status is FAILED, exit one, no normal-completion claim.

Earlier accepted RED job `23612303`, Delta, COMPLETED `0:0`, had 55 expected missing-helper failures on each interpreter with no errors/skips, and 62 actual versus 62 expected oracle bytes on each. Its preserved provenance is `task1/red-run-01/run_manifest.json`, same accepted baseline commit, manifest SHA256 `171b2411e513bb07b0f0360ce65f0b45b1af3083f0100b1bc565d2e1710700c7`.

## What is NOT done

GREEN-r3 has not run. No claim of Task 1 completion or mgnp GREEN is made. Root CPU rerun, independent corrected-packet review and Task 1 acceptance remain. Genuine producer/receiver resource bounds, production intake/handle/guard integration, full-suite/native numerical gates and later tasks remain separate. No worker git, RS, scheduler, remote, model construction, GPU action or source publication. Root owns research-report linting under the worker prohibition on RS.

## Open questions

Exact root commands, to execute only after packet review:

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3/cpu.sbatch --dry-run
```

Proposed bounded Delta request: one CPU, four GiB, five minutes, both environments sequentially. Root selects the permitted actual account and partition.

```bash
sbatch --account=beto --partition=cpu --cpus-per-task=1 --mem=4G --time=00:05:00 --output=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3/green-slurm-%j.log /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3/cpu.sbatch --mode GREEN --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan/task1-green-r3/green-run-01
```

The packet requires exactly 55 passes per interpreter, zero failures/errors/skips, pytest exit zero, before/after source pins and exact oracle baselines. Return terminal evidence and `green-run-01/run_manifest.json`. Default: keep all sources frozen through the job and do not advance Task 2 before root acceptance.
