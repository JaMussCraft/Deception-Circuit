# Startup and executed-byte closure correction handback

Status: handed-back

Frozen for scoped re-review; stopped after the assigned correction. Actual SIF/runtime compatibility remains unobserved.

## What changed

Corrected review257 P1 only in the distinct `plan-a2-exact-fixture-bridges250/candidate-r2/` revision; the original candidate and evidence remain untouched. The original 43 tests are byte-for-byte unchanged. A separate test file adds 18 startup/read-witness cases. Exact source/evidence hashes and commands are in the [r2 manifest](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence-r2/run_manifest.json).

Each current master/worker invocation now requires root-sealed external startup evidence from its exact interpreter exec through a unique barrier attempted after the Python read/import hook is installed. The witness binds the current nonce, PID, kernel start token, role, argv, working directory and closure hash. Missing, incomplete, stale, writable or mismatched evidence rejects. Successful startup opens, descriptor reads, file-backed mappings and symlink reads reconcile with declared bytes, including actually consumed caches and resources that leave no module origin. Normal site/user-site and required distutils behavior remain enabled; bytecode-write prevention is not treated as cache-read prevention.

The r2 template adds an unbound external-startup field and still rejects. Actual runtime/provider/configuration/tool bindings remain null. The explicit root handshake and evidence-protection requirements are in [PROBE_SCHEMA.txt](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/candidate-r2/PROBE_SCHEMA.txt). The probe implements neither the external tracer wrapper nor deployment.

Frozen SHA256 values:

- `runtime-probe.py`: `2e52bde1c8a818ef9d68e53b4226b21d503ad356fe730649de4d4438fe2c87db`
- Original `test_runtime_probe.py`: `e3b0bf2f557bad38e1e520d11915e4a8b829233b918f6d4341aa6a6aae445633`
- `test_startup_closure.py`: `bc5001af9f87ef2d6e4bf6a994234a5804f6b9979d61b28f5fe47ffb8f5760bd`
- `closure.template.json`: `d8294c2786359443aa7f6199643d433512cdd44729737e38a543dda2589e97d4`
- `PROBE_SCHEMA.txt`: `86fc7525cfad3573f52af4f60ce6a7c3023f2bf7c3644d38a50921a542acfc4c`
- `task1-evidence-r2/run_manifest.json`: `20ff4ffb9b306404db7167b1c70b1a161de105ddf7f2abf55914944ff8f0c028`

## How verified

The new pure fixture actually executes cache value 2 while the authenticated source contains value 1, with bytecode writes disabled and a late hook missing the cache read. It also reads a tiny resource before the hook without retaining a module origin. Actual local strace output captures both paths. The corrected gate rejects either undeclared path and changed consumed-cache bytes; explicitly pinning the consumed bytes passes the pure reconciliation. These assertions run under both original interpreters; [r2 raw evidence and counts](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence-r2/run_manifest.json) record the distinction from actual runtime acceptance.

Attributable RED has 15 missing-feature failures on each interpreter before implementation. The preserved first BASE attempt has 7 failures and 8 fixture setup errors; a broad path-extraction fixture was corrected before the attributable RED runs. Final GREEN has 61 of 61 passing on each interpreter: original 43 plus 18 new cases, in 8.18 seconds on BASE and 7.64 seconds on mgnp. Every check was capped at 30 seconds. See [exact commands, exit codes and evidence hashes](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence-r2/run_manifest.json).

Final raw output is `task1-evidence-r2/final-base2.stdout` and `final-mgnp2.stdout`; both exit files contain zero. Dedicated `raw-base2/` and `raw-mgnp2/` directories retain each actual script, source/cache bytes, raw trace and `observed.json` mismatch, rather than relying on temporary fixtures surviving other sessions.

## Execution evidence

Local pure checks only; no Slurm job or actual SIF startup handshake ran. Job/cluster admission and Slurm state are not applicable. The [run manifest](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence-r2/run_manifest.json) records local host, exact argv/environment, expected and observed counts, exit codes and root-supplied source commit `538109e809285b6ddc45d42df8786270a65f7b12`; no git command ran.

Both interpreters reproduce the local baseline source value 1 / executed cache value 2 before the late hook. Corrected reconciliation rejects the undeclared consumed bytes, and the full pure suites pass 61 of 61 each. This is a probe regression baseline, not reproduction or acceptance of the actual fixture job/runtime. Sources: [local regression manifest](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/task1-evidence-r2/run_manifest.json).

## What is NOT done

No actual runtime or startup-witness acceptance, SIF staging, remote access, copies/installations, interpreter rebuild/substitution, scientific BASE port, Task Two host/observer work, native/full suite, job mutation, git, RS mutation, source publication or extra agents. The root has reprioritized genuine timing and operational work after the original Delta gate passed; this revision is preserved optional preparation, and the worker stops here.

Root's [read-only strace/private-library smoke](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/root-tool-discovery/read-only-strace-private-libs.json) establishes only inspection-tool executability in the unchanged SIF. It uses the SIF loader with a tracer-local private-library argument, without a global library-path or glibc/loader override. Actual tool/provider closure remains an explicit root binding prerequisite. The full required trace flags, protected live capture and same-process read-only seal handshake remain unmeasured. A child-writable live trace is insufficient even if the later copied seal is read-only.

## Open questions

Await scoped re-review of this frozen P1 correction. Root alone decides whether optional runtime-slice work resumes and owns protected external tracing, exact binding/staging, actual compatibility/collection gates and any later transport work. No automatic retry or substituted interpreter is authorized. The fixed compatibility deadline includes waiting for external evidence; root must preserve failed gates and stop if the bound cannot be met.
