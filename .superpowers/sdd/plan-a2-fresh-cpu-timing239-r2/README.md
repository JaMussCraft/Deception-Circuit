# Diagnostic 239 r2: narrow review 244 correction

Status: handed-back for independent 244 r2 review; no native launch authority. Manifest SHA256 `c43d084973d38dbb2367b269879f23cc2d42383784f65d9abde937d4232573e6` binds 577 files. The original 239 manifest `63743b3e980ce194a5cbbc8fe0415aaf486c4f78967250751f025b1b5365180e` and all 546 members remain unchanged and included in provenance. Every Task2 helper/template remains byte-identical.

`original-to-r2.diff` is the raw non-git diff. Only the runner's `run_stage` function changes: each final/ongoing recheck retains the minimum of its original bound and current allocation end minus sixty seconds. Parameters and the child command are generated from that bound after the final metadata check. A fresh clock check immediately before the only Popen rejects equality or expiry. An increased later allocation end cannot renew the earlier shorter deadline. `child.py`, the data-only factor, all native guards, configuration/policy templates and measurement/admission semantics are unchanged. Launcher/request paths are rebased to this distinct immutable namespace.

Seven new tests exercise actual `run_stage` with only external metadata/process seams replaced. Before the correction, five cases fail as intended: expired fresh/prime bounds after costly authentication, equality at deadline, expired current CPU finish bound, and ignored shorter-current-end bound. The ordinary valid start and late-reaped-zero rejection already pass. After the correction, all seven pass; the valid normal case starts once and reaches saved-byte/supervisor checks, while late reaped zero remains rejected by the unchanged actual Task2 observation helper. No actual child process or native/scientific data is used in these fixtures.

Final pure suites pass 26 of 26 in both base Python 3.9 and mgnp Python 3.12, zero errors/failures. Exact XML/logs and `pure-results.json` are pinned. An initial full pure run passed 25 of 26 because the relocation test caught the copied old absolute launcher path; that namespace path was corrected and its failed logs/XML remain preserved. AST/shell and actual relocated dry-run pass. No native workload or scheduler action occurred.

The architecture, scope and proposal remain those independently reviewed for original 239: real Delta four CPUs, 32 GiB, 15 minutes, no GPU/requeue; prime 480 seconds then a different interpreter's full fresh pipeline 240 seconds, local publication allowance 45 seconds, CPU finish 60 seconds, proposed kill 15 seconds, bootstrap 75 seconds, total 900. Fixed hypothetical GPU WAITING remains 300 seconds with no extension or renewal. Actual request/transfer/remote publication remains unmeasured; `operational_feasible` stays null. No READY/WAITING/request/operational CPU_COMPLETE/release is emitted.

Original `data_path.execute` retains the unchanged native Task2 helper chain, all G2/G3/schema/bank/domain/support checks, three child source/catalogue captures and independent supervisor boundary. Counts remain 59,652 rows and 3,396 controls. Actual resource/witness/job/source-acceptance bindings remain NULL. Root must independently accept this correction, actual Task2 GREEN and source, then bind a fresh actual diagnostic CPU job/packet witness and separate bound config before dispatch. Another proof's witness cannot substitute. The actual Slurm WorkDir/chdir must be the original frozen runtime `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime`.

Safe relocated-compatible preview:

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/launch.sh --config UNBOUND --config-sha256 0000000000000000000000000000000000000000000000000000000000000000 --dry-run
```

Root-only prospective exact command after all acceptance/bindings:

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fresh-cpu-timing239-r2/launch.sh --config ROOT_BOUND_ABSOLUTE_CONFIG --config-sha256 ROOT_BOUND_SHA256
```

Use the frozen templates unchanged and write a separate bound config. Preserve any failed observation and stop, with no automatic retry or inferred resource/GPU admission. Root retains all git/RS/jobs/transfers/source publication and report lint.
