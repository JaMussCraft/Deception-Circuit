# Task One fixture runtime probe handback

Status: handed-back for root source review; actual runtime compatibility remains unobserved.

## What changed

Implemented only the new fixture probe, pure tests, rejecting closure template and explicit probe schema under `.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/candidate/`. Raw test evidence and its `run_manifest.json` are under the sibling `task1-evidence/` directory. Every original packet and candidate remains untouched.

The probe requires exact BASE bytes/build/SOABI, seven package versions and literal module/metadata origins; measured mgnp bindings; retained inventory source bytes and recursive aliases; actual read-only closure inputs; required distutils startup behavior and evidence-bound exclusions; actual ELF declarations, symbol needs and loader providers; explicit stdlib-only helper imports; closed file/module/mapping traces; and exact ordered RED/GREEN collection names. Separate fresh collection workers retain distinct original RED and new GREEN observer hooks. Native/GPU probes remain hash-only. No fake Slurm field is introduced.

The template leaves actual SIF/runtime/provider/startup/helper/collection bindings null and rejects. Schema details, staging responsibilities and the exact invocation are in `candidate/PROBE_SCHEMA.txt`.

Source SHA256 values:

- `runtime-probe.py`: `d8e7cd94c385c49f321f97e9fcde4e07ce298e35ef2dee045fc012d6fb0e7f5a`
- `test_runtime_probe.py`: `e3b0bf2f557bad38e1e520d11915e4a8b829233b918f6d4341aa6a6aae445633`
- `closure.template.json`: `368695a42ae5af639485f136f395d5710fb3032305def83a24c27257dff8e89f`
- `PROBE_SCHEMA.txt`: `1a964cd30cc828e563f995fd0caa3abb6e4f68d7bd01ea5ec50f2d8d5da9da84`
- `task1-evidence/run_manifest.json`: `4f36b2dc51405b5475b25c70e6b833df9767a9b405129b75cdf5125842401b4d`

## How verified

Both supported interpreters passed all 43 tiny probe tests: BASE in 0.69 seconds and mgnp in 0.88 seconds. Each command was capped at 30 seconds. Tests cover wrong executable SHA/version/build/SOABI, pytest origin, changed files/aliases, missing recursive targets/providers/versioned symbols, unlisted reads, scientific imports, startup omissions, exact collection names, metadata roots, pure helper transitive imports, forbidden execution, CLI refusal of an unbound template, preservation of existing output and real child timeout cleanup. See the [test evidence manifest](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence/run_manifest.json).

Exact commands and environment are recorded in `task1-evidence/run_manifest.json`. Each uses the corresponding absolute interpreter with `-m pytest -q -p no:cacheprovider --noconftest --confcutdir=<candidate> <candidate>/test_runtime_probe.py`, under `timeout 30`, with plugin autoload and bytecode writes disabled and BLAS/OpenMP threads pinned to one. Final raw outputs are `final-base.stdout` and `final-mgnp.stdout`; both exit files contain zero.

Test-first evidence is preserved. The corrected initial RED runs show 31 missing-implementation assertion failures on each interpreter. The first RED attempt instead produced 31 setup errors and remains preserved. Intermediate GREEN retained one synthetic startup fixture using the wrong literal pth path; that test fixture was corrected. Subsequent added gates have their own failing RED logs. The [evidence manifest](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence/run_manifest.json) describes every retained attempt.

## Execution evidence

No Slurm job, remote runtime, native/scientific run, allocation or admission occurred. Job ID and Slurm state are not applicable. Local host and full commands are in `task1-evidence/run_manifest.json`, which names root-supplied frozen source commit `538109e809285b6ddc45d42df8786270a65f7b12`; the worker ran no git.

Observed pure-test counts are 43 of 43 passing on each interpreter. The local missing-feature baseline has 31 failures on each interpreter before implementation, followed by 43 passes on each after the added gates. This does not reproduce the actual fixture or scientific baseline. Actual required collection counts remain 22 RED-selected and 226 GREEN cases per staged runtime, with exact names and cross-environment agreement still unobserved. The live weekly usage check returned 33 percent spent, 67 percent remaining and `should_pause: false`; reset is recorded by the live account tool as 2026-11-13T16:18:29Z. Sources: [local test and usage manifest](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence/run_manifest.json) and [accepted contracts](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/contracts.json).

## What is NOT done

No Task Two host, observer or launch implementation; runtime build/copy/install; remote access; actual SIF probe; fixture collection; full suite; native/scientific workload; job submission/cancellation/retarget; git; research-session state mutation; source publication; or extra agents. No scientific BASE equivalence or actual CPU/kernel/provider compatibility claim is made.

Inventory251 remains proposed source retention, and its missing startup/assets/bytecode/provider decisions still require root's measured closure completion. The current source insists on its retained entries and additional observed inputs rather than silently trimming them. The probe's readelf/ldd subprocess count and full input hashing have not been timed in the SIF; exceeding the fixed gate fails closed. The caller must bound container startup itself, authenticate the actual image invocation and physical staging translation, and protect private output parents. Audit hooks begin after ordinary interpreter startup; startup bytes, pth listings, preload/finder behavior and imported-origin reconciliation are explicit complementary checks.

## Open questions

Root tool discovery reports `/usr/bin/readelf` absent in the pinned SIF; `/usr/bin/ldd` is present. The explicit tool-path interface supports a root-reviewed pinned read-only inspection-tool bind, including its loader/provider closure, as a deployment prerequisite. Actual tool bindings remain null. This is a tool-presence result, not runtime compatibility; see [root discovery receipt](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/root-tool-discovery/sif-tool-presence.json).

No new design decision is requested. Remaining root gates: source acceptance; Task Two implementation; exact slice staging and completed hash-bound manifests; actual SIF read-only startup/ELF/provider/helper/import/collection probes under each interpreter within the accepted bound; source/name agreement across both observations; actual host bindings and placement; and only then the separately authorized bounded fixture CPU job. Preserve a failed gate and stop for narrow review; do not substitute Bridges Python, retry automatically or infer compatibility from these pure tests.
