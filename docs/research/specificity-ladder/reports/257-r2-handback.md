# Startup closure correction scoped review

Status: handed-back

## What changed

Requested two narrow reconciliation corrections. The same-invocation external witness design addresses the original late-hook observation problem in principle, but current code does not yet close it.

- R257-r2-A: the complete startup prefix includes the required pre-hook `load_bound(args.closure, digest)` read. Reconciliation demands an `entries` record for that manifest, while its existing `control_read_paths` contract intentionally avoids self-hashing. Pass the exact already-authenticated control path/digest separately and check it without exempting arbitrary paths. Every legitimate master/worker would otherwise reject this required read.
- R257-r2-B: relative `readlinkat` resolves against cwd instead of its annotated directory FD. The pure parser accepts a trace consuming `/actual/dir/alias` with only `/cwd/alias` declared. Resolve the correct dirfd or reject the unsupported form; never substitute cwd.

## How verified

Read the original P1 finding, exact source diff, schema and new eighteen tests. Frozen manifest `20ff4ffb9b306404db7167b1c70b1a161de105ddf7f2abf55914944ff8f0c028` and probe `2e52bde1c8a818ef9d68e53b4226b21d503ad356fe730649de4d4438fe2c87db` match. All 285 recorded files match size/SHA; original forty-three test bytes are unchanged. Evidence: `plan-a2-fixture-probe-review257/r2/checks.json`.

Raw saved fixtures show actual source-value one/executed-cache-value two and pre-hook resource reads under both interpreters. The recorded final outputs contain sixty-one passes each. Two tiny source-bound parser checks reproduce the control-read rejection and wrong-dirfd acceptance, using a declared file-digest I/O seam. These checks do not construct a successful full runtime receipt. Evidence: `plan-a2-fixture-probe-review257/r2/reconcile-results.json`.

## Execution evidence

No full suite was rerun. This review performed source/raw-file hash checks and two tiny in-memory reconciliation cases only, with no runtime staging, native/scientific execution, external tracing, remote call or scheduler job. Exact scripts/results and scope are in `plan-a2-fixture-probe-review257/r2/run_manifest-r2.json`. Scientific rows, adapter commit and an actual SIF compatibility result do not apply.

## What is NOT done

No candidate/source edit, git, RS, job, deployment or additional agent occurred. Root's actual protected external handshake, tracer identity/PID namespace association, tool/provider closure and container compatibility remain separate gates. This authorizes neither the optional host work nor a repeat of accepted Task two fixtures. All predecessors remain preserved.

## Open questions

Add a positive reconciliation containing the separately authenticated closure read, plus changed-control and extra-unlisted-read rejections. Add correct/undeclared/unresolved relative-dirfd `readlinkat` cases. Keep normal startup, original interpreter, actual bytecode/resource authentication, complete sealed prefix, nonce/PID/start/role/argv/closure binding and existing deadlines. No broader redesign or scientific environment port is requested. Actual handshake/container evidence remains required after source correction.
