# Bounded native continuation on frozen source

Status: handed-back; accepted in principle by root, NOT RELEASED or executed. Real-input source benchmarks and the fetched Bridges comparison take priority.

## Clear next action

After root releases the step and contention clears, run the prepared external supervisor below. It performs exactly one NEW selected-pilot case at index 1, then authenticates that new case again in the same process with forwards/pilot/publication trapped. It stops there. No aggregate or later case is launched. The existing authenticated case at index 0 is preserved without re-execution or re-signing. [Exact case IDs and original scope](source-and-cases.json), [proposed scope/costs](observed-costs-and-proposal.json).

```bash
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder
/sw/external/python/anaconda3/bin/python3.9 \
  .superpowers/sdd/plan-a3/native-continuation-plan/supervisor.py
```

[supervisor.py](supervisor.py) creates the fresh scenario `diagnostics/next-case1-and-warm-01` directory, checks at least 16 GiB finite ancestor headroom, uses single BLAS/OMP/MKL threads and direct child `wait4`/RSS/process samples, and records leaf plus ancestor memory limits/events. Its cap is 1,200 seconds plus 15 seconds kill grace. It uses no recurring traceback thread. Existing output, source mismatch, unexpected case children or partial scratch cause refusal; no automatic overwrite/retry follows a failure. These are a proposed operational cap and procedure, not a guaranteed completion duration. [Controls and byte-valued headroom](observed-costs-and-proposal.json), [exact coordinator](coordinator.py).

## Existing APIs and unchanged guards

The coordinator calls original `verify_scenario`, `read_bundle`, `inventory`, `pilot_cases` and `_read_pilot_case`, then repeats the original source/model/backing checks. It preserves the full canonical case order, authenticates old case bytes before/after, and checks that genuine per-case forward counts match the independent passive counter. Extra warm-authentication time and its zero new forwards are separate evidence outside pilot/proof bundles.

Using `pilot_cases` directly omits only `run_phase`'s redundant outer `_case_invocations` call. `pilot_cases` still calls that same validator internally before any native execution; it independently rebuilds the frozen inventory. It still loads/validates its own selected metadata and axes, records original samples/controls, publishes a completed case and runs the full original case reader. This is external coordination using existing APIs, with no change to production/harness source or scientific counts. [Static evidence](evidence.json), [coordinator](coordinator.py).

Within one `pilot_cases` call, model/design/protocol/inventory and loaded axes already serve the entire requested case loop. The existing default `_NUMERIC_BACKING_CACHE` also reuses selected-axis validation across proof constructors in the same process. Every cache hit nevertheless verifies reference bytes, PID, injected/source signature and the full selected-file witness. Each case still authenticates its own observations, scope, controls, receipt and dependency witness. These costs cannot be skipped. Validator/cache objects from the earlier terminal process cannot cross a restart. [Runtime signatures and source hashes](evidence.json).

## Observed and estimated cost

The original CLI reached numerics after 583.17 seconds. Its redundant outer inventory validation cost 71.23 seconds; removing only that repeated call gives a derived setup point estimate of 511.94 seconds. Original case work was 102.63 seconds, including 59.28 seconds in the native invocation and 11,100 actual forwards. Isolated full case authentication took 186.89 seconds. [Observed logs and arithmetic](observed-costs-and-proposal.json).

The proposed cold-case process estimate is 822.47 seconds. Adding same-process authentication gives a derived estimate of 924.36 seconds, or 976.99 seconds after the observed slower-I/O sensitivity. The warm-authentication proxy is 101.89 seconds: cold full authentication minus the first backing-bundle read and axis load. It is NOT an observed cache-hit measurement or an upper bound. Publication includes an explicit planning allowance; process teardown uses its observed duration. The next case shares source/profile/cell-operation counts and batch-group count with the measured case but has different inputs. Actual timings must replace these estimates before choosing larger chunks. [Definitions, allowances and limitations](observed-costs-and-proposal.json), [case descriptors](source-and-cases.json).

## Dependencies and continuation limits

The step depends on the exact frozen source closure, scenario/design/protocol/tiny-model state, selected bundle and its fit/validation ancestry, existing selected inventory, and preserved original case. The coordinator checks the whole source closure and original case order; it independently rebuilds/compares the inventory. No admission/ledger authority is created. [Exact paths, hashes and IDs](source-and-cases.json), [input hashes](evidence.json).

The simpler unchanged CLI alternative is `python -m tests.a3_direction_native_scenario --root ROOT --phase selected-pilot --start 1 --count 1 --resume`, with a derived 893.70-second point estimate before slow-I/O sensitivity. It cannot expose a post-case warm-cache measurement once its process exits. The prepared lower-API step is preferred because it measures that missing cost without another native case. [Cost comparison](observed-costs-and-proposal.json).

Larger same-process chunks may amortize existing setup/cache construction, but cached byte-witness work remains per case and is currently unmeasured. Repeated `run_phase` calls reload model/context; repeated `pilot_cases` calls reload axes and revalidate inventory. Neither API accepts an already validated inventory/axes context. The harness directly reconstructs case proof objects rather than accepting a previously completed-case success flag. Swapping constructors or injecting cached success would change behavior and is outside this step.

Full aggregation remains atomic: it authenticates the complete exact case set/order and then executes original `run_pilot` reconciliation, fresh evidence publication and complete dependency checks. There is no measured short-process bound or resumable aggregate API. No calibration or full-pilot completion can be claimed before that succeeds. A reusable prepared-context or staged-aggregation interface would need a separately reviewed test-only change; editing the frozen harness also changes the scenario-pinned source identity, so preserved lineage cannot simply be re-signed. This plan implements neither change and releases no aggregate attempt. All original pilot/calibration/assessment/summary/finality coverage remains required.
