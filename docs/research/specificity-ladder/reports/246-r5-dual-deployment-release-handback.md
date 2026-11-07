# A3 r5 dual CPU test deployment release audit

Status: handed-back

## What changed

Accepted both exact held CPU test bindings—Bridges mgnp 50316975 and Delta BASE 23622800—subject to root’s fresh usage, held-state, source/config and spool checks before release. No new source or binding finding in the scoped deployment audit. This authorizes neither scientific/model/GPU execution nor acceptance of unobserved test results.

The new Bridges config includes 1120 ordinary files plus eight unchanged literal aliases. It adds all four actual primary/worktree held_out.json and directions.json targets to the accepted 1116-file r5 proposal. Thus the registry alias contents and native primary/branch contexts are explicitly bound rather than assumed from an older transfer. Baseline’s two registry files remain ordinary copies; no test semantics changed.

## How verified

Independently checked all 1120 current local file hashes/lengths and all eight literal alias targets. Six successful stage receipts cover every config file exactly, plus the separately sealed config file itself: 1121 transferred/read-back rows. The transfer script refuses to overwrite different existing bytes, creates only missing files, then rehashes every row. Every observer source-pin member is covered by a regular row or its exact declared registry-alias target.

Config SHA is `6e1e7858314f7ee426a60dfd646cd1612e8648a9e652281550e61940b9666f62`; r5 source-pins remain `05b53e5f2b2c2d737782753cde63cb6c1b428038d71d7666c644777deb1184c9`. Ordinary bytes total 24,329,303. Actual after-stage container dry-run passes both baseline context checks and count 223, creates no test output, and the unchanged alias inventory test passes. The earlier premature before-stage check remains preserved and does not supply acceptance. Actual statvfs/mountinfo confirms reviewed source/cache/environment/cgroup-parent+memory read-only and fresh private output-parent writable mappings.

Bridges 50316975 actual held Command uses the correct three positional launcher arguments for deployment 245 config and reviewed transport manifest `bd3533cc18025d7d2bf97515060a46f793abd4f4a43609e8dc6c9626d8a6e6e2`. Frozen spool SHA is `e015a251ff55de96fc495628b3095dbbbd09481f3b90b2474f4727bbc8ec711d`. It requests 18 CPUs, 32 GiB, 59 minutes under cis260361p/RM-shared/rm, no GPU/requeue. Actual held readback is PENDING/JobHeldUser with zero runtime and absent execution output.

Delta BASE 23622800 binds the same r5 observer/pins through frozen cpu.sbatch. Actual spool SHA `0d2991714ed8518644aab2c92abad581db65436319452348d7ad6e81b9ff9c7e` matches local source and stored spool; wrapper dry-run passes closure/count 223. It requests 2 CPUs, 32 GiB, 59 minutes under bimc-delta-cpu on cpu,cpu-preempt with no requeue/GPU, passes --environment base and uses its distinct absent output root. Held readback likewise shows zero runtime and JobHeldUser.

Evidence: `.superpowers/sdd/plan-a3/r5-deployment-review246/binding-audit.json`. Accepted source 243 and unchanged transport reviews were not rerun.

## Execution evidence

Reviewer performed only local metadata/hash/receipt checks. Actual root receipts show successful staging, after-stage container dry-run and effective-mount check; BASE wrapper dry-run exits 0. Both jobs are recorded held and unstarted. No actual five-case baseline RED or 223-case GREEN results are claimed from these receipts. No native/full suite, model, scheduler or remote action was executed by this reviewer.

## What is NOT done

No job release, fresh live-state/usage query, test GREEN acceptance, source/runtime publication, genuine prepared resource feasibility or numerical/GPU admission. Failed r4 evidence and premature staging-check failure remain preserved. No code edits, git, RS, SSH, jobs or extra agents.

## Open questions

No further deployment correction is requested. Root may release these two exact bounded test jobs after its ordinary fresh final checks. Preserve actual per-environment manifests/JUnit and require all five intended r3 baseline failures plus all 223 GREEN cases before accepting execution. Actual allocation guards and supervisor deadlines remain active at job startup. Root owns release, result review and report lint.
