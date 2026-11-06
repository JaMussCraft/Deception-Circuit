# Independent corrected full-shape CPU packet review

Status: handed-back

## What changed

Accepted the distinct corrected packet for one genuine CPU metadata execution only. Appended a correction to the previous review: native `_map_index` filters by operation before identity lookup. My prior claim that utility all-map input bypassed this filter was wrong; Terra identified it and the source confirms it. The old packet and review remain preserved. [Correction](182-r2-full-shape-packet-review-evidence/correction-182-B2.json), [scoped verdict](182-r2-full-shape-packet-review-evidence/verdict.json).

## How verified

Read the exact native map filter, capture loops, alias expansion, donor defaults and positive calibration. The revised proof uses native donor padding and operation filtering, keeps matched support flags/reasons, and cross-checks reconstructed row/control keys against the original domains. Positive-pair work uses the maximum retained parent width. Verified new and preserved old packet member hashes, grammar and shell syntax; inspected raw semantic RED and GREEN logs and independently ran the focused fixtures. [Source comparison](182-r2-full-shape-packet-review-evidence/verdict.json), [raw proof](182-r2-full-shape-packet-review-evidence/shape.py).

## Execution evidence

No Slurm job or genuine geometry calculation was performed by this review. Base observed 6 passing tests against 6 expected; mgnp observed 6 against 6 expected, both exit 0. There are 4 native-seam methods and 2 arithmetic methods. Semantic RED records 1 expected donor-width failure against 1 observed: original width 2 differs from native expected width 9. These fixtures are not accepted scientific artifacts or baseline replication. [Counts](182-r2-full-shape-packet-review-evidence/verdict.json), [raw semantic RED](182-r2-full-shape-packet-review-evidence/red-semantic-native.log), [provenance](182-r2-full-shape-packet-review-evidence/run_manifest.json).

## What is NOT done

No genuine full-shape result, model execution, runtime bound, GPU-memory bound, rigorous output-size proof or full-score admission. Delta filesystem facts do not prove Bridges capacity. The unchanged trusted runtime was not repaired or modified.

## Open questions

Root must submit the exact reviewed packet under its required runtime working directory and CPU allocation, with a fresh output directory and no automatic retry. Review actual shape/support/work ratios before cost binding; obtain conservative GPU/host memory and serialized-output/atomic-copy support plus actual Bridges capacity. All new full-only controller, admission, current protection, quota, ledger and phase-entry guards remain required. [Resources and remaining gates](182-r2-full-shape-packet-review-evidence/verdict.json).
