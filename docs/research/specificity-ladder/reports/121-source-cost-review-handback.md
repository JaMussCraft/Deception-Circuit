# Independent source-cost repair safety review

Status: handed-back

## What changed

**Source/spec verdict: BLOCKED. Code-quality verdict: BLOCKED. Practical timing/budget readiness: UNRESOLVED.** Reviewed exact frozen candidate `caae47195503460c1df63670d23448c49b316a67` against the accepted source-cost repair plan and baseline `87fceb28b3b46f4a406c0280db785697a0bbd3fc`. These verdicts concern the proposed source-proof reuse boundary; they do not withdraw accepted unrelated authority or tokenizer scopes. [Manifest](121-source-cost-review-evidence/run_manifest.json).

**B1 — prepared envelope changes can enter the initialization gap.** In `build_state`, artifact contents are compared with the owned immutable view before dependency discovery and before the initial file witness. A valid prepared envelope replaced during dependency discovery is therefore witnessed as the new static input while the semantic callback validates the old owned payload. The independent fixture rewrites only its temporary prepared payload and valid completion marker in that interval. The minted view differs from a genuine `read_object` of the artifact, yet minting and subsequent refresh succeed. [Exact rejection probe](121-source-cost-review-evidence/test_independent_source_boundaries.py), [owning helper](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-source-cost-runtime-caae47195503/runtime/component_analysis/a3_source_validation.py).

The minimal repair must bind the artifact envelope before the artifact-to-owned comparison, then prove that same envelope remains current through dependency discovery and full semantic validation. A separate early envelope witness is sufficient in principle; discovery need not be redesigned. Add an expected-rejection regression at this exact interval, including prepared payload/completion changes and canonical envelope identity. Merely rechecking a witness first captured after the replacement does not close the gap.

**B2 — full grader lexical provenance is outside the static dependency closure.** The actual current grader validator hashes `evaluation/benchmark_eval.py` and the benchmark source glob, but both owner source closures omit the former and do not bind the complete grader glob's lexical ancestry. After minting, replacing the temporary grader file with a same-byte external symlink leaves the actual grader hash unchanged, and source refresh accepts it. Current content validation is functioning; the promised path/ancestor authentication is missing. [Actual closure cross-check](121-source-cost-review-evidence/closure-crosscheck.json), [exact probe](121-source-cost-review-evidence/test_independent_source_boundaries.py).

The bounded repair must include every file actually discovered by the genuine grader-file enumerator, its lexical and target ancestors, and source-glob membership in the static witness/provenance boundary. Continue calling the real current grader validator on every refresh. Preserve legitimate protected/direction catalog content and atomic-file updates; fixing grader source provenance does not justify freezing mutable registry contents.

## How verified

Independently matched every ordinary frozen source file against the root snapshot and confirmed the delta is confined to the owned pipelines, helper and their tests. Source hashes remained unchanged after probes. The snapshot contains the correct source map but retains an inherited stale code-file-count field; root should reconcile that metadata when freezing the successor. [Exact hashes and count distinction](121-source-cost-review-evidence/source-verification.json).

Inspected the accepted plan and review clarifications, raw candidate diff, helper, both owner factories/guards, unchanged full validators, actual protected-set/grader discovery, and consumed startup/host-memory fields. The helper is included in both owning source closures. The code retains the existing authority calls and guard call sites; cold initialization is added to consumed startup and peak host accounting. These positive design properties do not cure the initialization/provenance gaps.

Ran independent temporary CPU fixtures in both project interpreters. Positive controls cover sealed empty/nested containers, initializer and normal seal mutation rejection, JSON serialization, independent mutable deep copies, valid unrelated atomic registry updates, independently returned evidence and changed same-size static bytes with restored timestamps. The negative probes use real artifact publication/completion checking and real current registry/grader validation, without a model or injected execution authority. [Probe source](121-source-cost-review-evidence/test_independent_source_boundaries.py).

## Execution evidence

Both interpreters produced the same result: the expected rejection cases fail because the unsafe paths are accepted; the positive controls pass. Exact counts, wall times and tested source hashes are recorded in the [manifest](121-source-cost-review-evidence/run_manifest.json), with [mgnp output](121-source-cost-review-evidence/independent-mgnp.log) and [base output](121-source-cost-review-evidence/independent-base.log). These are fixture-boundary counterexamples, not timing benchmarks.

Initial reviewer harness failures are preserved separately: pytest first inherited the active worktree's conftest import route; isolated configuration/import mode corrected it. Base Python's fixture `copy2` failed while copying filesystem ACL metadata; only reviewer fixture transport changed to byte-only copying. Neither is counted as an application defect. No candidate code was edited.

The tested helper SHA is `264f02fd842290fe48f943fb2cde5a0c86f1ecbfe081c1fae2175f415c172fc8`; exact pipeline/test hashes are in [source verification](121-source-cost-review-evidence/source-verification.json). Original failure logs and reviewer probe versions remain available for successor closure.

## What is NOT done

No source, original input, existing artifact, reservation, research-session state or scheduler mutation; no git, remote access, subagents, notebooks, model weights, GPU work or paid API. No broad owning suite or numerical direction execution was repeated. Author implementation handback prose was excluded.

No practical model-admission claim is possible here. Root instructed the genuine new-input owner to finish its current atomic CPU step and stop further preparation/benchmarking after these blockers were reported. This review does not extrapolate earlier CPU costs into a GPU forecast, assume mandatory byte IO will fit the phase cap, or change science, authority cadence, phase charges or the held original mask reservation.

## Open questions

Root should freeze a bounded successor closing both rejection probes, then obtain independent exact-source closure and genuine fresh matched preparation/measurement. The initialization artifact boundary and full grader ancestry must reject before model work; current catalogs, live authority and immutable in-memory consumed source must remain independently enforced.

Practical readiness still requires actual initialization, fresh-byte refresh, retained/transient host-memory and full used-path measurements on new genuine inputs, followed by the existing staged pilot/cap decision. Source-safety closure alone will not establish that the pilot can finish within its original ceiling.
