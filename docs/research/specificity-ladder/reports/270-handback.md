# BASE selector collection diagnosis

Status: handed-back

## What changed

Diagnosed an old pytest selector-cache collision, not missing functions or wrong imported test paths. BASE `-I` disables user-site and selects global pytest 7.4.0; normal BASE uses the supported pytest 8.3.3. With `-c /dev/null`, rootdir is outside these files, so each explicit file gets an empty module node ID. The old selector cache keys by collector type plus node ID and reuses the first release module's report for later usage/cache selectors.

## How verified

Inspected actual installed collector/node source and reproduced collection only. Both requested functions import from the correct frozen files and exist. Same isolated BASE resolves the twelve selected cases when only explicit `--rootdir` is added. Normal BASE also resolves them. The whole-file runner bypasses that selector-cache branch and collects all 98 unique cases under isolated BASE, normal BASE and isolated mgnp. Evidence: `plan-a2-task3-collection-diagnosis270/collect-results.json`, `plan-a2-task3-collection-diagnosis270/selector-results.json`, `plan-a2-task3-collection-diagnosis270/import-origins.json`, `plan-a2-task3-collection-diagnosis270/verdict.json`.

## Execution evidence

Only tiny pure import and collect-only subprocesses ran, each under a bounded timeout. No test body, native/scientific code or full suite executed. Actual Python/pytest paths and versions are in `plan-a2-task3-collection-diagnosis270/interpreter-identities.json`; exact argv/logs and installed-source hashes are preserved beside it. Scientific rows, adapter commit and a full RED result do not apply.

Root separately reports normal-startup brief outcomes matching between supported pytest 8.3.3 and 9.1.1: twelve named cases, seven intended failures and five passes each, with no errors/skips. That truthful limited receipt supports only the recorded covered-interface implementation start; remaining features still need focused RED and full baseline/GREEN/native-chain validation remains mandatory. The queued full job stays unchanged.

## What is NOT done

No source/test/packet edits, scheduler, remote, git, RS or additional agent action occurred. Frozen pins remain unchanged. This diagnosis does not call the queued whole-file job broken and supplies no cancellation reason from the selector symptom. The isolated BASE run must be labeled as pytest 7.4.0, not as the supported normal BASE pytest 8.3.3.

## Open questions

For future standard-environment checks, drop `-I` while retaining bytecode-write prevention, explicit plugin-autoload disabling and conftest/cache isolation, then record actual interpreter/package identity. No package install, fallback Python or path injection is needed. Explicit rootdir is the smallest independent fix for a legacy isolated selector probe. Preserve the current queued packet and its original-source-pin targets. Root's normal-startup tiny orchestration check may establish only its truthful limited RED scope; complete Slurm RED/GREEN validation remains required.
