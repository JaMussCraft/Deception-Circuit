# CPU proof AST compatibility successor

Status: handed-back

## What changed

Created separate `proof-adapter-r4` and `root-proof-dispatch227` packets under the specificity-ladder worktree's `.superpowers/sdd/plan-a2-full-score-bridges-cpu-proposal199/`. The successor removes only empty `type_params` fields on expected function or class AST nodes before the unchanged pin comparison, and rejects nonempty, malformed or unexpected-owner fields. The reviewed source contract, 20 pins, worker, request, input pins, host and proof guards remain byte-identical. No native guard was reordered. The adapter manifest SHA-256 is `94a104fa5db26251b1f565baea61cf59b6e632ea453a0232ace01903ef8fecc0`; the dispatcher SHA-256 is `da3fd6aac9356a685410afd3800c824988ac90c4e0a60dfcbe63707382f9cddb`.

Compared with r3, the changed packet members are `proof_schema.py`, `launch.sh`, `inner.sh`, `test_host.py`, `test_catalogues.py`, `packet-files-from.txt`, and `manifest.json`; `test_ast_compat.py` is new. The wrapper and test path changes name r4. The 32-member manifest and 33-path transfer inventory, including the manifest, were checked. Dispatcher changes from the reviewed predecessor are only the packet path and fixed manifest pin, with corresponding fixture changes.

## How verified

Before the fix, the Python 3.12 actual frozen-source test reproduced the original first-function ValueError. The bounded packet suite then ran 34 tests under each supported interpreter: Python 3.9 passed with one 3.12-only generic syntax test skipped; Python 3.12 passed all 34. This includes all 20 actual source pins and source snapshot hashes, body and branch mutation rejection, malformed and nonempty type parameters, unknown field owners, preserved other AST fields, and a real 3.12 generic function. Nine dispatcher fixtures passed in each environment. Manifest content, inventory, unchanged files and shell syntax were checked. No full native or model tests ran.

## Execution evidence

No successor job, remote action, graph or model ran. The earlier job 50313499 failed at the original AST check with model loading false; see report 226 and its preserved evidence. The successor's local test runs are not resource or scientific proof.

## What is NOT done

Independent source review, transfer closure, fresh job-bound bindings and any separately authorized CPU diagnostic remain outstanding. Neither the predecessor packet nor failed job was altered.

## Open questions

The independent reviewer should examine every changed member, cross-version normalization and mutation coverage before the coordinator decides whether to run a successor. Actual Bridges host compatibility and end-to-end execution remain untested.
