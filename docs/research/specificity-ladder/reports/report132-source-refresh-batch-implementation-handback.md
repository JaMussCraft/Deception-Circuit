# Source-only fresh witness batching implementation hand-back

Agent: Codex Sol. Status: handed-back. Software candidate only.

## What changed

Only `component_analysis/a3_source_validation.py` and `tests/test_a3_source_validation.py`
changed in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/source-refresh-batch-source`, against frozen `f5a5687ec12091f0d148b38b301598e9c7cb98cd`. Exact two-file diff, pre/post
hashes, complete freeze-input manifest and tested source copies are under `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence`.

The helper compiles a private immutable source scan plan within the existing stable mint
envelope. A one-shot receipt binds the exact witness produced by the owner factory;
process-local weak mint registration binds every original plan field, nonempty copied
roots/rows/order and exact witness dictionary/field identities. Raw/cloned/reinitialized
or changed proof objects cannot supply replacement expectations.

Every original file occurrence is still completely read and hashed on every refresh.
Opened regular-file descriptors must match all expected identity fields before and after
reading through EOF; paths, file identities and actual directory memberships receive
fresh closing checks. Complete lexical, relative-literal, intermediate and target routes
are observed independently before and at closing. Ordinary route-only parents retain
routing/coherence checks without freezing their catalog content timestamps.

Current registries, protected sets, actual graders, missing paths, New30, grader glob
membership and authority sites retain their original semantics/cadence. No pipeline,
shared runtime, workload or original A1 file changed. New plan/registry allocations enter
the actual retained graph walk and existing consumed initialization/host fields; weak
identity bookkeeping is charged conservatively without retaining dead source graphs.

## How verified

Baseline red tests failed in both interpreters; the new proof regressions include genuine
legacy-witness empty/reinitialization and replacement acceptance counterexamples. Two
additional red regressions caught a changed registered route graph and a caller-built
nonempty exact-type witness during development; their raw failed runs and subsequent
green checks are retained. See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/red-mgnp.log`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/red-base.log`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/red-plan-binding-mgnp.log` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/red-owner-mint-mgnp.log`.

Final focused group: 221 passed under explicit mgnp Python and
221 passed under base Python. Exact argv, source hashes, environment,
exit/timing and logs: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/handoff-mgnp.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/handoff-mgnp.log`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/handoff-base.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/handoff-base.log`. Threads were limited, bytecode and
pytest cache disabled, and dedicated temporary directories used.

The checks cover exact oracle row/order equivalence, every repeated hash occurrence on
successive refreshes, overlapping trees/completions/aliases, raw/empty/copied/reinitialized
proofs, descriptor substitution, incomplete reads and closing-on-error, post-read content/
rename/disappearance/membership attacks, a same-inode alias added after prefix observation,
relative/intermediate aliases/cycles, valid atomic catalog/current registry updates, stale
grader/protected overlap, source/data/in-memory boundaries and initialization accounting.
Original independent B1/B2 probes remain byte-identical and passed in both final groups.

The initial complete groups each had a missing-path smoke-test failure because my runner
omitted the existing `A3_A1_SCHEMA_TEST_DESIGN` override. The final runs supply its original
absolute parent path and offline settings; neither candidate source nor tests changed for
that correction. Both original failed logs/receipts remain in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/affected-mgnp.log` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/affected-base.log`.

## Execution evidence

- Classification: local CPU software checks, including real small filesystem/registry validators and the existing original-parent schema smoke test. No numerical scientific verdict.
- Controls: original witness oracle, complete byte occurrence/order comparison, explicit mutation/race negatives and untouched independent B1/B2 probes. See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/run_manifest.json`.
- Source binding: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/source-pre.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/source-post.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/source-freeze-manifest.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/candidate-diff.txt`. All 511 ordinary source files checked; only the named two differ and original input links are preserved.
- Exact tested source identities: helper `eaabf9ef8247159686ec6ee00b6dbcb876495a0dac62281bb26077a9eb65fcee`; test `f3164a051cf18c5f44e7da13b364e02057426e02b7daccd557947afd54c66241`. The final command receipts bind these hashes.
- Raw command/timing/log runner: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/run-focused-tests.py`; implementation decisions/results: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/132-source-refresh-batch-evidence/execution-ledger.md`.

## What is NOT done

No actual new-source preparation, real-input performance claim, source freeze, model,
GPU, scheduler/job, RS/reservation/ledger/cap mutation, Git, paid API, notebook or subagent.
No TTL/stat-only cache, cross-refresh digest reuse, skipped original byte occurrence or
guard-cadence reduction. Old prepared hashes and held-job mappings were not rewritten.
Original authority/workload APIs remain unchanged. Software checks grant no admission.

## Open questions

Root owns independent review and exact immutable successor freeze. Only then can genuine
new-source preparation and real-input oracle/byte-count, initialization/RAM and refresh
measurements proceed, including separate-copy mutation negatives. This candidate removes
per-root reconstruction in the hot source check, but mandatory IO and added closing checks
remain; performance/cap feasibility is unmeasured and unresolved. Stop here with exact
candidate hashes; no mutable-candidate preparation is authorized.
