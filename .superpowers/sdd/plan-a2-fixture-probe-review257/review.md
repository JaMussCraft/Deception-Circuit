# Independent fixture probe review

Verdict: **REQUEST CHANGES** for one material executed-byte/startup-closure gap. The existing pure suite passes in both interpreters; actual SIF/runtime compatibility remains unobserved.

## Finding

**P1 — Start tracing before required startup reads, and authenticate the bytecode actually executed.**

Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/candidate/runtime-probe.py`, lines `9–23`, `259–260`, `326–331`, `401` and `443–446`.

Each fresh process runs normal `site` startup and all top-level probe imports before installing `make_auditor`. The later module snapshot records `module.__file__`, which normally names the source even when CPython executed its bytecode cache. `PYTHONDONTWRITEBYTECODE=1` prevents cache writes but permits cache reads. Neither startup snapshots nor `check_observed` inspect existing `__cached__` bytes or recover earlier opens. A closure can therefore authenticate the source and still omit bytes actually executed. The same missing observation window covers pure startup resource/helper reads that leave no module origin behind. This contradicts the required bytecode policy and rejection of undeclared startup/helper reads.

The owned pure fixture authenticates a source file containing `value = 1`, then imports it through a valid undeclared timestamp cache containing `value = 2` before installing the auditor. `check_observed` accepts its declared source origin, while the executed value is 2 and the observed-read set is empty. This occurs under both supplied interpreters with bytecode writes disabled. Evidence: `run_manifest.json`. The fixture tests the relevant gate functions and process order; it does not claim to manufacture a successful full compatibility receipt.

Required correction: close and authenticate the bytes consumed before the current hook, including existing bytecode, through a bounded startup/read witness or an explicitly enforced cache-absence policy plus evidence for startup/resource reads. Keep normal user-site startup and the original interpreter; do not use `-S`/`-s` or broaden into a scientific environment port. Add a regression covering an actual pre-hook import/cache read, rather than calling only the audit hook with a fabricated event. The accepted closure must reject this fixture or declare/authenticate the consumed cache before execution is accepted.

## Inspection-tool prerequisite

`check_bindings` at lines `229–230` requires inspection tools only in `entries`, without requiring their ELF loader/provider graph. A pure structural fixture passes binding validation while both tools are absent from `env.elf`. The parent explicitly retains real tool/provider binding as a root prerequisite, so this is not a separate blocker in this implementation review. Root must actually bind and close the read-only tool, its interpreter if applicable, and its providers before running the gate. Tool execution alone does not establish that closure. The root tooling receipt showing successful bound readelf execution does not replace the per-object runtime gate.

## Coverage and scope

- Exact supplied probe, tests, template and author-manifest hashes match. All thirty files in the author evidence manifest match their recorded lengths/hashes.
- Existing pure tests pass 43 against expected 43 under each exact interpreter (`run_manifest.json`). They exercise wrong BASE executable bytes/version/build/SOABI/pytest origin, recursive aliases/providers, required startup declarations, metadata, observed reads, known scientific imports, collection names/counts, deadline cleanup and null-template rejection.
- BASE identity pins the original executable and seven package distributions/origins; there is no Bridges Python substitution. Actual observed identity is compared with the bound identity. Read-only file checks, recursive provider checks and post-reap deadlines are present.
- The worker retains original observer command flags and distinct RED/GREEN target selection, adds collection only, and compares exact ordered names. Actual collection was not run by this review.
- The template is unusable until bound. Result status and schema disclaim scientific environment equivalence, allocation and admission. The recorded pure checks are honestly scoped to probe tests, not the actual fixture gates or a scientific BASE baseline.
- Required original source inventory is retained rather than indiscriminately copying Delta system providers. Exclusion evidence is required by bindings, but actual staged exclusion/startup behavior remains root work.

## Evidence

Owned artifacts: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-fixture-probe-review257/`.

`run_manifest.json` records exact argv, local exit codes, source provenance, author evidence hashes and raw outputs. `reproduce.py` is pure fixture code. `bytecode-base.stdout` and `bytecode-mgnp.stdout` contain the source/cache mismatch and empty read log. `base.stdout` and `mgnp.stdout` contain the repeated 43-case passes. `tools-base.stdout` records the structural tool prerequisite check.

No author handback, scientific native/model code, actual runtime staging, SSH, jobs, git, full tests, RS mutations, or additional agents were used. Every execution check was bounded to at most thirty seconds.
