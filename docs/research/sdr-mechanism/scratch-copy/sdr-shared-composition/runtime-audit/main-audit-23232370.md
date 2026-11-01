# Independent main raw/runtime audit

2026-10-27 UTC. **PASS — the complete frozen main acquisition is verified for export and blinded annotation.** All3,936planned outcomes are accepted with the required numerical/provenance evidence. No semantic labels or effect interpretation were inspected or produced in this audit. Root owns release of the annotation phase.

Raw directory: `.scratch/sdr-shared-composition/operator/main-695b126-20261026T234700Z`. Source `695b126a9d5fe3045c9b5872fac7441d8fcdeec2`; final protocol file SHA256 `0f49bbec41852f33bca8896b83ace6080a7ba1f96e910e91ab58db9cd08f731c`, manifest `959824dc8973cd91f8423c00b7cf34d888bb054770c4fc31711fa2b8731adc44`.

The independent CPU checker imports no producer module. It read actual accepted, setup, attempt, invocation, timing and protocol files and recomputed their contracts rather than accepting producer summaries. Separately reconciled raw archive/progress/summary contents and operator-captured raw scheduler stdout. This reviewer loaded only the cached tokenizer on CPU; no model, GPU/job, notebook, paid API, git or production-source operation occurred.

## Exact acquisition coverage

- **492accepted batches/3,936unique planned rows**, comprising96baseline rows and192directed pairs×20arms. Exact frozen batch/row order, IDs, full envelopes and protocol/run hashes pass. No foreign/missing/duplicate outcome or effect-conditioned omission.
- **3,936EOS**,0cap,0stress,0execution-error row. Every response contains3generated tokens, including EOS:11,808tokens total. EOS IDs, legal vocabulary IDs, actual first token and logical original/generated readouts pass. CPU cached-tokenizer decoding independently reproduced all continuations, supplied-stem-plus-continuation and raw full response strings.
- All seven clean-only arms exactly match the corresponding fresh recipient baseline full token IDs, EOS finish and firstscore record. No behavioral-correctness gate was applied.
- One invocation,492attempts and24setup groups. No failure file, unclosed attempt, interruption receipt, retry or resume. Every accepted arm links to its exact attempt/invocation and setup bank. The persisted archive matches the independently ordered accepted rows exactly; progress/summary accepted IDs and counts agree with those raw rows.

## Numerical controls, masks and bank origins

Independently counted **16,608full-vocabulary comparison receipts**. Every receipt is finite, identical argmax, bitwise true and maximum absolute error0, with matching expected/observed hashes and complete row/physical-slot/step coverage:

| Control | Receipts |
| --- | ---: |
| Patched repeat | 11,520 |
| Firststep link | 3,936 |
| Baseline repeat / empty | 96 / 96 |
| Donor setup / U5 setup readout | 192 / 192 |
| Recipient setup repeat / empty / self | 192 / 192 / 192 |

All actual decoder firststep checksum/argmax/generated-token links pass. The repaired donor and naturally induced U5 setup readout comparisons are present for every group. Actual forward counts are **3,432decoder/control +192setup =3,624physical forwards**; each group has exactly8setup calls, and per-signature count sums reconcile with recorded totals.

For every group and arm, rebuilt all8×224Boolean mask bytes from frozen saved common maps or recipient prefix lengths. Exact mask hashes/counts, site keys, B8×L224×128 geometry and BF16 receipt dtype pass, with generated, padded and dummy positions false. Source values link to donor setup bank hashes; clean/induced receiver values link to their declared recipient-coordinate banks. No receiver bank was remapped through donor coordinates. All1,344required receiver norm records have exact key/row/prefix coverage, prefix-length×128denominators and finite nonnegative values.

## Source, calibration and hardware preservation

After main completion, independently rehashed **96bound files**, including66source files,19historical input/mask files, original parent and10cache files including all four model weight shards. All match the final protocol. Independently reconstructed Python/package versions and RECORD/METADATA hashes in mgnp; all match the frozen software record. This closure took24.99seconds with no model load.

The main invocation binds the exact reviewed calibration directory and has the same hardware identity: NVIDIA A100-SXM4-40GB, capability8.0, CUDA12.8, Torch2.11.0+cu128. Literal raw protocol equality and committed/nonprovisional source binding pass.

Compared **every calibration raw file** against the earlier independent calibration snapshot:all77files are byte-identical, including23accepted files and the hidden `.lock`. The operator's76file preservation count refers to JSON files only; the extra independently checked file is the lock. Calibration's164natural and16stress rows remain separate from all main rows. No calibration evidence was rewritten or repurposed.

## Deadline and scheduler reconciliation

Independently checked all492guard formulas against the frozen policy:67baseline/129patched decode-call budgets, nine cold allowances when setup is needed and one otherwise,1.5safety factor,40second shutdown and10second nonforward floor. Exactly24attempts correctly charge setup; every remaining attempt reuses its existing group banks. Every admission fits actual remaining allocation time; minimum headroom after its recorded full guard is407.223seconds.

Main setup elapsed time sums to45.340432seconds and decoder elapsed to570.174757seconds. Maximum repeated decoder forward is0.236227seconds, captured by timing profiles. Largest directly observed per-batch nonforward total is0.837269seconds; maximum attempt-to-next-attempt nonforward wall residual is1.127146seconds; maximum setup nonforward cost is0.714128seconds. All492accepted publication/read-hash timing receipts are present and bind actual accepted bytes. Publication/read-hash maxima are0.342718/0.090701seconds. Observed overhead remains below the10second floor, including conservative addition of maximum setup overhead; no allowance violation.

Parsed raw `sacct` stdout:job23232370 is **COMPLETED, exit0:0, one A100,0restarts,795actual GPU-seconds**. Scheduler local StartTime maps to epoch1793058730, exactly the invocation allocation start. Recorded deadline1793060050 equals start+1,320seconds; actual end1793059525 is795seconds after start, safely before that deadline. Account/partition/QOS are beto-delta-gpu/gpuA100x4-interactive/beto-delta-gpu. Main used795actual/1,320reserved GPU-seconds. Including calibration157actual/600reserved gives **952actual/1,920reserved A100 GPU-seconds**. Operator ledger remains authoritative; no extra allocation was used.

## Evidence and limits

- `main-raw-23232370.json`:full independent raw checker output, exact accepted-file/raw-inventory hashes and CPU decode verification.
- `main-independent-arithmetic-23232370.json`:control/token/forward counts, archive/progress equality, exact guard arithmetic, scheduler epochs and phase accounting.
- `main-bound-files-software-23232370.json`:post-main full-source/input/cache/weight and software closure.
- `main-calibration-preservation-23232370.json`:all77calibration files unchanged against the prior independent snapshot.
- `main-evidence-hashes-23232370.json`:audit artifact hashes.

The unchanged checker was validated with21hand-fixture tests passing in both base Python3.9 and mgnp Python3.12, plus ruff F. Those tests reject corrupted control/mask/bank-origin/token/hash/coverage/deadline/resume evidence; no already passed test suite was rerun for this raw audit.

Full raw logits and activation tensors are not archived. Numerical vector equality/errors, natural propagation, activation values/immutability and norm magnitudes are **receipt-verified**, supported by the reviewed runner and its tiny-model controls. File/protocol hashes, exact control/firststep links, masks, token trajectories/decoded text, source/cache/software identities and scheduler arithmetic were independently recomputed. An actual resume did not occur, so resume preservation remains tested by fixtures rather than observed here. This PASS establishes raw acquisition integrity and readiness for blinded annotation; it makes no claim about lexical commitments, mechanisms or strategic intent.
