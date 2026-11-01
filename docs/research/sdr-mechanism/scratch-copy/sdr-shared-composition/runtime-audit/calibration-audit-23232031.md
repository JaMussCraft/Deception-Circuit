# Independent calibration raw/runtime audit

2026-10-26. **PASS — calibration numerical, provenance, coverage and observed runtime requirements are satisfied.** The proposed1A100×1,320second main allocation is supported as an operational forecast with the unchanged full panel and verified interruption/resume policy. Root remains release authority; this audit submits no job and makes no behavioral/scientific-effect claim.

Raw directory: `.scratch/sdr-shared-composition/operator/calibration-695b126-20261026T233500Z`. Source `695b126a9d5fe3045c9b5872fac7441d8fcdeec2`; final manifest `959824dc8973cd91f8423c00b7cf34d888bb054770c4fc31711fa2b8731adc44`. Independent checker and hand fixtures are in this directory and import no producer code. All reads/outputs were CPU-only; no model, notebook, job, API or git operation was performed by this reviewer. No lexical outcomes were inspected for mechanism selection.

## Raw numerical and coverage findings

Read every actual run, attempt, setup, accepted, timing and protocol file rather than accepting producer summary claims. Recomputed canonical envelope/run/protocol hashes and raw accepted-file SHA256s, exact expected IDs/order and invocation bindings. Coverage is exactly **23accepted batches/180rows**:164natural rows in21batches and16forced64 rows in2batches. All164natural rows reached EOS; forced arms10/18 each have8stress rows of64tokens. No cap, missing row/batch, foreign row, failure file or unclosed attempt was found. One invocation, one setup group and23attempts; no resume/retry was needed.

The selected calibration story is disjoint from the96main inputs/192main pairs; no calibration output enters main. All20natural operators were represented. Firstscore/full-vocabulary checksum and actual decoder first token agree for every natural row; forced rows preserve the independent firstscore/checksum while injecting the prospectively fixed stress token. Saved logical readouts, EOS/cap/stress contracts and legal token IDs were independently checked. CPU cached-tokenizer decoding reproduced every saved continuation, supplied-stem-plus-continuation and raw full response. All seven clean-only arms exactly reproduce their fresh recipient baseline full token sequence, EOS finish and firstscore record.

There are **1,732full-vocabulary comparison receipts**, all finite, identical argmax, bitwise true and maximum absolute error0:

| Control | Receipts |
| --- | ---: |
| Patched repeat | 1,504 |
| Firststep link | 180 |
| Baseline repeat / empty | 4 / 4 |
| Donor setup / U5 setup readout | 8 / 8 |
| Recipient setup repeat / empty / self | 8 / 8 / 8 |

Counts were recomputed per row, physical slot and step. The two repaired setup readout controls are present with their expected/observed vector hashes. The three natural setup captures plus donor/U5 readout controls and recipient repeat/empty/self total exactly8setup forwards. Together with404decoder/control forwards this is **412physical forwards**.

For every setup and science/stress arm bank, independently rebuilt all8×224mask bytes from the frozen prefix lengths/common maps and verified key coverage, hashes/counts, B8×L224×128 geometry and BF16 receipt dtype. Generated, padding and dummy slots are false. Each arm's actual value hash links to the declared donor-source, recipient-clean or U5-induced setup bank; receiver banks are never remapped through donor coordinates. All56required receiver norm records have the correct key/row/prefix-length×128denominator and finite nonnegative values.

## Provenance and accounting

Independently rehashed **96bound files**:66source files,19historical input/mask files, original parent and10model/tokenizer/config files, including all four weight shards. All match the final protocol. Independently reconstructed mgnp Python/package versions and RECORD/METADATA hashes; all match the frozen software record. This CPU closure took21.36seconds and loaded no model. Raw hardware is NVIDIA A100-SXM4-40GB, capability8.0, CUDA12.8 and Torch2.11.0+cu128, consistent with the frozen runtime requirements.

Parsed the operator-captured **raw sacct stdout** separately from its derived accounting fields. Job23232031 is COMPLETED, exit0:0, one GPU,0restarts, **157actual GPU-seconds**;600GPU-seconds were reserved under the prospective10minute allocation. America/Chicago scheduler StartTime maps to epoch1793058127, exactly the run's allocation start. Recorded allocation deadline1793058727 equals start+600; actual scheduler end1793058284 is157seconds after start. The early successful end is distinct from the requested deadline. Account/partition/QOS are beto-delta-gpu/gpuA100x4-interactive/beto-delta-gpu. Numeric reservation/accounting ownership remains with the operator.

## Independent timing arithmetic and main sizing

Actual setup is1.930678seconds, including1.274728seconds of forward time and0.655950seconds of packing/norm/control/hash overhead. Maximum cold forward is1.269098seconds; maximum repeated decoder forward is0.162562seconds. The two forced64batches take21.429145/21.414772seconds and129forwards each. Natural calibration completions are3tokens here; this single input-defined story does not establish a whole-panel response-length bound.

The direct largest observed per-batch nonforward total, including applicable setup overhead and accepted publication/read-hash, is0.968180seconds. Maximum attempt-to-next-attempt wall time after subtracting all forward work is1.138882seconds. Adding the maximum observed setup overhead conservatively to the direct nonforward maximum gives **1.624130seconds**, below the fixed10second guard allowance. Publication/read-hash maxima are0.228090/0.045948seconds; all23timing receipts are present and link to the actual accepted-file bytes. The last forced batch's next-attempt wall interval is unavailable because it is terminal; its direct costs and scheduler completion remain accounted separately.

Independently reproduced the main forecast from natural per-arm raw elapsed times, one setup/group and actual accepted-file I/O maxima:

`12×baseline + 24×sum(20natural arms) + 24×setup + 492×(maxpublication+maxreadhash) = 771.821569seconds`.

With1.4variable-work factor, first actual attempt minus scheduler start as independent startup proxy76.330185seconds, and40seconds shutdown once, the total is **1,196.880382seconds**. This agrees with the operator's1,196.880203seconds using its model-loaded startup timestamp, differing by0.000179seconds. Proposed **1,320seconds/22minutes** leaves123.12seconds rounding headroom over that buffered orientation. The forecast remains advisory after start; immutable complete coverage/cap64 and next-batch full-cap admission remain mandatory. If the main panel runs longer, retain all accepted bytes/failed attempts and use only explicitly reviewed exact resume. No outcome-conditioned arm/prompt changes are authorized.

## Evidence files and limits

- `calibration-raw-23232031.json`:initial raw audit, CPU decode and independently hashed source/input/config/tokenizer closure.
- `calibration-raw-timing-23232031.json`:timing-aware full audit with previous-snapshot preservation, exact accepted-byte/inventory hashes and independent decoding.
- `calibration-bound-files-software-23232031.json`:all-source/input/cache/weight rehash and independent software closure.
- `calibration-independent-arithmetic-23232031.json`:raw control counts, scheduler epoch/accounting reconciliation and timing/forecast arithmetic.

The checker hand fixtures pass21tests in both base Python3.9 and mgnp Python3.12; ruff F passes. Tests specifically reject corrupt receipt hashes/control coverage/masks/bank origins/firsttokens, missing norms, altered accepted bytes or deleted prior failure evidence, and independently recompute timing costs. They do not execute the producer or a model.

Raw logits/activation tensors are not archived, so vector equality/error, natural propagation, tensor values/immutability and norm magnitudes remain **receipt-verified** through the reviewed runner; they are not independently recomputed model results. Mask bytes, digests, control/firststep links, token trajectories/decoded text, file/software identities and accounting arithmetic were independently recomputed. No failure or resume occurred here, so preservation during an actual main resume still requires a pre-resume audit snapshot and post-resume comparison. No semantic annotation or scientific-effect inference is included in this PASS.
