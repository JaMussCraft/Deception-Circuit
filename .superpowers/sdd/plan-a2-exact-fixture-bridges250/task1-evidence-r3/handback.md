# Hand-back 255: Startup trace reconciliation corrections

Agent: scoped implementation worker. Ticket: review 257, round 2. Status: handed-back. Actual startup remains unaccepted.

## What changed

The candidate at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/candidate-r3/` carries the exact invocation-bound closure path and digest separately from entries. The trace must include that path, its current digest must match, and other reads still require closure entries. Relative `readlinkat` uses the annotated directory descriptor or fails closed. Existing witness checks are unchanged. The post-hook auditor permits the exact closure path for reauthentication. The source diff is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence-r3/runtime-probe.diff`.

Frozen SHA-256: r2 probe `2e52bde1c8a818ef9d68e53b4226b21d503ad356fe730649de4d4438fe2c87db`; r3 probe `b96eb624085f70b01c11263f5a084aa862cac089f30df4b431d4fff89ed66dcc`; new tests `b38462c54ca7fc984fa15a5f721d120720bbb67b5dbe40e5f50c0f1242709148`; diff `a826db80d00f54e774f715aac9f939793c98c1c2984899c2fb2790077263ce4f`. Copied original test hashes match r2, as listed in the evidence manifest.

## How verified

The bounded pytest command used each supported interpreter with plugin autoload disabled, `--noconftest`, `-p no:cacheprovider`, and `-k 'not actual and not incomplete_or_other_invocation and not changed_consumed_cache and not probe_cli and not deadline_kills'` on candidate-r3. Base and mgnp each reported 53 passed and 10 deselected, including both new tests. The deselected cases launch local trace or child processes. After clarification that these fixtures were allowed, the complete bounded suite reported 63 passed on each interpreter, including all 61 original cases. Raw output and exact hashes are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence-r3/`.

Both interpreters ran the new tests against a temporary copy of r2 before the correction: two failed each. The control test failed because the separate binding interface was absent; the descriptor test accepted the wrong cwd path. On r3 the tests exercise changed bytes, wrong control digest and identity, extra undeclared reads, correct symlink, wrong target and unresolved descriptor. The r2 evidence previously recorded 61 passing tests per interpreter; those tests remain byte for byte unchanged and passed again in r3.

## Execution evidence

- Job id and cluster: local bounded pytest checks, no scheduler job.
- Exit code: r3 checks 0 on both interpreters; r2 negative checks 1 on both.
- Counts: 63 of 63 full-suite checks passed per interpreter; the earlier 53-case selection is also preserved; 2 of 2 targeted r2 tests failed per interpreter.
- Baseline reproduces: r2 descriptor counterexample accepts cwd attribution where actual descriptor path is undeclared; the test expects rejection and fails on both interpreters.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence-r3/run_manifest.json`, source commit `538109e809285b6ddc45d42df8786270a65f7b12` inherited from r2 evidence, not independently checked with git.

## What is NOT done

No actual external startup handshake, provider or container compatibility acceptance, native scientific import, full suite, runtime staging, scheduler work or GPU execution. This candidate is not an authorization for Task 250 host or a repeat accepted Task 2.

## Open questions

Independent review should examine the exact control binding, audit-hook allowance and descriptor parsing before any use. Default: retain the existing runtime acceptance gate and do not launch the fixture.
