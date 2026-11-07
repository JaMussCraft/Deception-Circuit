# Data-only timing diagnostic source review

Status: handed-back

## What changed

Requested one narrow correction, R244-A, in `runner.py:run_stage`. Its final `recheck()` returns a current deadline, but the caller discards it and does not check a fresh clock against that bound before Popen. Costly packet authentication can exhaust the fixed stage or actual CPU finish window, yet a new interpreter still starts and performs configuration/hash work before later guards reject. This is a process-entry bound gap; no successful late measurement or false operational admission was observed.

## How verified

Independently rehashed all 546 packet/source members and checked six reused Task two helpers against their pinned original bytes. The manifest matches `63743b3e980ce194a5cbbc8fe0415aaf486c4f78967250751f025b1b5365180e`. Evidence: `plan-a2-fresh-timing-review244/checks.json`.

The data factor retains source/export/input/alias closure, exact current catalogue witness binding, native context/live/geometry/bank-reader/bank-contract/numeric/tokenizer/layout checks, internal bank payload hash, exact G2/G3 science comparison, reconstructed full row/control/support-reason identity, final native live validation, child catalogue-byte captures and independent supervisor identity capture. It uses unchanged data helpers without inventing a future GPU job or calling the closed operational entry. Separate discarded prime/fresh interpreters, strict reap checks and failure preservation are present. Raw process/job memory scopes remain distinguished. No other scoped semantic-parity blocker was found.

## Execution evidence

A tiny source-bound `run_stage` probe replaces only external metadata/process I/O. Its fresh deadline is 1240, authentication advances the clock to 1250, and the mocked Popen boundary is still reached. Zero actual processes start. Evidence: `plan-a2-fresh-timing-review244/expired-preentry-result.json`.

Both immutable pure-fixture XML files contain nineteen cases without failures/errors/skips. This reviewer read those files and ran only the tiny expiry probe; no native or full suite ran. Source hashing completed in about eleven seconds. No scientific rows, actual diagnostic job, adapter commit or scientific run_manifest claim applies. Exact source checks and local probe provenance are in `plan-a2-fresh-timing-review244/run_manifest.json` and `plan-a2-fresh-timing-review244/checks.json`.

## What is NOT done

No candidate or Task two source was edited, and no jobs, SSH, git, RS, transfers or additional agents were used. No author handback was read. The existing genuine proof and queued Task two GREEN are separate and supply no acceptance here. `operational_feasible` remains null and remote request/transfer/publication costs remain unmeasured. No resource, GPU, full-score or scientific admission follows.

## Open questions

Reject an expired window immediately before Popen using a fresh clock and the minimum of the original fixed stage bound and returned current CPU bound. Keep the effective deadline nonincreasing and consistent, or abort a shortened/unfit packet; never renew it. Add tiny real-orchestration regressions for authentication exhausting the stage and current CPU end-minus-margin already expiring, both requiring zero Popen, plus a valid bounded start. Preserve all semantic data guards and the closed Task two source. Actual Task two GREEN/source acceptance and a new root-bound diagnostic request still precede launch.
