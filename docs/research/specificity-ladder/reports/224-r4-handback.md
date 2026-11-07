# RED observer oracle correction

Status: handed-back

## What changed

Accepted the narrow observer/ruling correction only. The third legitimate baseline pass is the negative `timely_window=False` consumer case: accepted GPU validation raises its intended ValueError before reaching the other absent CPU fields. The positive `None` case still fails. This changes no production behavior, test body or source acceptance requirement.

## How verified

Independently rehashed all 266 pinned members and checked every prior 252 member remains identical. Both actual baseline XML files match exactly nineteen failure names and three pass names, with twenty-two unique cases and no errors/skips. The pinned oracle preserves that complete set. Observer checks now enforce exact failure/pass sets and unique full case coverage; all other observer functions remain AST-identical. Evidence: `plan-a2-task2-review224/r4/checks.json`.

## Execution evidence

Actual Delta job `23620810` produced RED_REJECTED because the old observer expected the wrong failure/pass split. Its two interpreter receipts contain only baseline RED; GREEN never ran. This review parsed those real XML/result files and performed brief metadata/hash checks only. No tests, native/scientific execution, model, scheduler or remote work occurred. Scientific rows, adapter commit and scientific run_manifest do not apply. Exact receipt paths/hashes remain in the new packet's bound oracle and the scoped review checks.

## What is NOT done

This is not Task two source acceptance or a passing GREEN claim. No production/test edits, git, RS, jobs, remote actions or agents were used. Resource/GPU/full-score admission remains absent. Prior failed attempts remain intact.

## Open questions

Root may use this accepted observer-only packet for the authorized bounded CPU run. Exact pins are `ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4`. Actual corrected GREEN must still contain 226 cases in each supported interpreter, with normal exits and no failures/errors/skips, before Task two acceptance. Evidence: `plan-plan-a2-full-score-operational186/task2/green-r4/pins.json`.
