# Original-SDR shared-component composition implementation

2026-10-26. Task implementation is ready for independent review; no GPU inference, Slurm submission, notebook execution, paid API, git mutation or old-source/result edit was performed by this worker. Root alone owns exact-file git and release. This report describes the frozen initial review bytes, not a completed scientific acquisition.

## Exact files and provenance

Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot`; root verified base `4f0278487b0285dd27cbc34d20d88c911dc5562a`.

- `scripts/sdr_shared_composition.py`: SHA256 `e3265dc5800a1ecd7f68d97b32bbf3c183edce180c328385e757e950d3e4026f`.
- `scripts/jobs/run_sdr_shared_composition.sh`: SHA256 `8239a864a4725c3bd4ab15f0d38e50eed22cd9afd931ffc6b801b4d5cf527c8a`.
- `tests/test_sdr_shared_composition.py`: SHA256 `c4dd83aff5ee9a73b2503e12ca312170c253572eea4afa71602bc1afbf6122ac`.

Exact snapshots and checksums are under `implementation/review-source/`. Root is preparing the git diff package; the worker did not run git.

`implementation/protocol-provisional-v2.json` is the current provisional freeze. Its file SHA256 is `c320f8d3c7c6e1502cdb8109c5f2126f7581b81de983aa7ad3a8830abecb4c58`, scientific hash `1a29813fea112f713b66a673619afa25687a70527d832323159c92e9c4364412`, manifest hash `2278cf2c75fdbf99db387c56440f0495e83b8a9ee7d5660f078812924674b0a8`. It binds66 source files and10 model/tokenizer/config files, the original parent manifest and historical input/mask hashes, actual mgnp software metadata, exact20arms/maps and B8/L224/cap64. `UNCOMMITTED` freezes cannot execute inference. Root must rebind after the exact source commit and rerun the absolute wrapper dry-run.

Inputs are exactly96 original native P/N prompts from24 historical confirmation stories,192 directed pairs and3,936 scientific rows in492 immutable batches. Prefix lengths100–118 leave at least42tokens beyond the cap within L224. All192 maps equal the original saved common maps and the unchanged semantic-map recipe. Calibration selects the lexicographically first discovery story:4 inputs,8 pairs,21 natural batches/164rows plus forced64arms10/18 (2 batches/16rows),180 excluded calibration rows in23 batches. No behavioral selection/gate was added. The earlier `protocol-provisional.json` is superseded because the new test fixture was subsequently completed; retain it as preparation evidence.

The exact rubric SHA is `ba22cf760ada14625cb7d7219628f1725d314df7a12c13358c5d51777dbd9da3`; input-only semantic join SHA is `6976720316b3fa75059d1e723e4b368fc3802c0aae8cabb64787df83be3ebbee`. Both exact files and bytes are embedded/bound. The semantic join is secondary metadata and never selects rows.

## Implementation behavior

The runner reuses `hooks.capture_forward`, actual FP32 final norm/unembedding readout, fixed-slot batching, checksum/comparison/assignment primitives, flock ownership and inherited lexical annotation validation. No hook/framework or attention backend was added. Three setup captures per physical8-pair group produce natural recipient/source states, natural donor heads, then the freely evolving recipient under U5 alone. All MLPs/unselected heads remain natural. Subsequent pending arms share those compact banks. A resumed invocation recomputes setup only for groups with remaining arms; accepted arms are audited and skipped.

Source values use original saved common donor→recipient maps; clean/induced receiver values use full original recipient prefixes, with separate Boolean masks per key. Banks are cloned, version checked and audited against frozen geometry/mask hashes/counts. Q/K are pre-RoPE; outputs are pre-o_proj slices. K/Vgroup6 explicitly supplies H24–27. Generated, padded and dummy positions are excluded. Receiver summaries are FP32 last-prefix-token L2 and prefix RMS over exactly length×128coordinates for B_A−B_0 and B_0; no attention allocation/semantic readout claim is made.

Every EOS arm receives an independent same-shape full-vocabulary first score, checked against the actual decoder first-step checksum/argmax and actual first generated ID. Full FP32 finite/repeat controls run throughout patched decoding. Baselines have repeat/empty controls; setup has repeat/empty/selected self controls. Clean-only arms must exactly match fresh recipient baseline token IDs/finish through EOS/cap, plus the first-step record. The decoder preserves the literal supplied assistant stem and concatenates decoded continuation without stripping whitespace. Raw/full text and finish remain separate.

Per-arm acceptance is one immutable canonical JSON file published using fsync, hard-link atomic publication and directory fsync. Accepted envelopes bind protocol/run/batch/result hashes. Source/hardware/calibration identity is verified before resumption. Failed attempts and partial token/control/runtime state remain; unresolved operational attempts require an explicit interruption receipt binding attempt-file SHA and scheduler terminal state. Numerical/provenance failures prohibit operational resume. An accepted arm is never rerun because optional timing publication was absent. Current calibration `--resume` is deliberately rejected pending root review; main permits verified resume. Reviewer should assess whether that calibration restriction is unnecessarily narrow.

Per-signature cold and warm timings are retained. A prospective next-arm guard charges67 baseline or129 patched decode calls at the observed repeated-forward bound, plus a one-time cold allowance and needed setup/check calls,1.5buffer,10seconds packing/publication and an explicit shutdown reserve (CLI default40seconds). Main uses the completed calibration’s same-hardware cold/warm bounds; current invocation observations update bounds. No repeated whole-panel worst-case deadline stop exists. Calibration records actual setup/packing/norm wall time, startup from actual allocation start, decode/control timing, canonical publication, accepted-file read/hash timing and the natural per-arm forecast with1.4buffer. Operator adds startup/shutdown once when sizing the reservation.

## CLI and artifacts

Invoke the original absolute wrapper:

`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/scripts/jobs/run_sdr_shared_composition.sh`

It fixes the original worktree, executable interpreter (mgnp by default), offline cache use and BLAS threads; under Slurm it binds actual allocation StartTime/EndTime. No bashrc sourcing is needed.

Commands:

- `freeze --parent ORIGINAL_MANIFEST --spec SPEC --rubric RUBRIC --semantic-inputs INPUT_JOIN --cache CACHE --code-commit FULL40HEX_OR_UNCOMMITTED --output PROTOCOL`.
- `calibrate --protocol PROTOCOL --output FRESH_DIR [--dry-run] [--initial-forward-seconds .4] [--shutdown-seconds 40]`.
- `run --protocol PROTOCOL --calibration-dir COMPLETED_CAL_DIR --output FRESH_OR_RESUMED_DIR [--resume] [--interruption-receipt RECEIPT] [--dry-run]`.
- `assemble --protocol PROTOCOL --run-dir MAIN_DIR --output ARCHIVE`.
- `export --protocol PROTOCOL --run-dir MAIN_DIR --output VIEWS`.
- `analyze --protocol PROTOCOL --run-dir MAIN_DIR --annotations RATER1 RATER2 [--adjudication THIRD] --output JOINED_ANALYSIS`.

A run directory contains exact `protocol.json`; `run-HASH.json` hardware/allocation/invocation binding; immutable `attempt-ID.json` guard receipts; group setup receipts/norms/control/timings; `BATCH.accepted.json` envelopes; optional per-arm IO timing receipts; partial failure/interruption receipts; `progress.json`; summary/archive files. Completed calibration adds `calibration.json`. Main accepted rows include IDs, physical slots, actual generated IDs/readouts/finish, full/raw text, first-step checksum/argmax/raw damaging-minus-harmless margin and decoder checksum. Comparison receipts retain finite/argmax/bitwise/max-error and vector hashes. Archives require every planned accepted row; incomplete attempts remain in their separate failure files.

Public views contain only opaque `view_id`, exact question, lexical-sorted candidates, full response and finish; top level is `protocol_hash` (manifest hash), `views_hash`, `views`. Deduplication hashes the complete view. Two distinct independent complete-coverage annotations use inherited8kind tuples; cap primary labels are null/capped/false/uncertain. Raw text and termination remain available. All full-tuple disagreements require a fresh third adjudicator.

`analyze` outputs `normalized` (3,936rows) and `analysis`, plus annotation paths/hashes. Normalized row fields include id,recipient_id,donor_id,pair_id,story_id,axis (`clause`/`fact`),direction (`P0<-N0`,etc),arm(integer0–20),raw margin,literal committed candidate/null,kind,finish,generated_ids,text,view_id,full label,truth/other names,condition/truth,first_step and semantic metadata. Baselines use arm0/no pair. Analysis contains all160direction×arm category/literal counts,192pair contrast records, baseline/induced/rescue lexical triples, raw endpoint effects, per-story signs and all direction-specific summaries. There is no unaligned reciprocal pooled headline. All24sorted stories receive equal weight. Bootstrap uses shared `random.Random(20261026)` draws,2,000resamples of24indices, linear `(n−1)*p` percentiles; seed/draw hash are exported. No mediated fraction or effect-size gate exists.

## Verification evidence

Preparation baseline, before production edits:

- Base: `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python -m pytest -q tests/test_sdr_cue_positions.py tests/test_sdr_routing_pilot.py tests/test_sdr_clause_choice.py` →122passed,2skipped,185.67s. Existing pandas/bottleneck version warning.
- mgnp: same threads and `/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q tests/test_sdr_cue_positions.py tests/test_sdr_routing_pilot.py tests/test_sdr_clause_choice.py tests/test_nnsight_hooks.py tests/test_path_patching_passes.py` →161passed,196.56s.

Initial new tests failed at the explicit missing-runner assertion before the production file existed. Additional red tests established missing acceptance/export/attempt functions, partial-decoder support, cold/warm guard and incorrect accepted bank mask handling; these were implemented and rechecked. Two intermediate neighboring-suite runs began before a new toy runtime fixture included its seven-token vocabulary; each had exactly one failure in `test_cpu_runtime_pipeline_binds_receipts_and_calibration_costs` (mgnp112passed/1failed; base104passed/1skipped/1failed). The fixture was completed; final immutable additive tests below supersede that development failure. No inherited test failed.

Final exact new file:

- Base same thread pins and `/sw/external/python/anaconda3/bin/python -m pytest -q tests/test_sdr_shared_composition.py` →23passed,1skip,14.85s. Only skip is the actual pinned-NNsight tiny integration in the base environment.
- mgnp same pins and `/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q tests/test_sdr_shared_composition.py` →24passed,25.56s. One installed astor `ast.Num` deprecation warning.
- `/u/swong2/.local/bin/ruff check --select F scripts/sdr_shared_composition.py tests/test_sdr_shared_composition.py` →all checks passed.
- `bash -n scripts/jobs/run_sdr_shared_composition.sh` →exit0.

Coverage includes exact input/maps/arms, mixed source/receiver masks and generated/dummy exclusion, norm denominators, actual independent EOS/firststep identity, forced64 immutability, finite hard stops/cache restoration, atomic publication/crash, accepted hash/run provenance, wrong mask receipt rejection, unresolved operational attempts, partial interruption evidence, full3,936row hand-constructed directional analysis/bootstrap, and a CPU runtime journal/calibration integration. The mgnp actual tiny Llama/NNsight test proves U5-style source replacement changes a later natural Q receiver, equals a manual freely evolving source-only forward, and differs from an intermediate MLP-frozen path. No real model weights were loaded for tests.

The provisional freeze command used the above exact wrapper/spec/rubric/semantic paths and `--code-commit UNCOMMITTED`. The actual absolute wrapper CPU dry-run receipt will be appended below after completion.

## Known limits for independent review

The first failed numerical comparison raises immediately. Its local failing comparison receipt is not yet attached to the exception/failure artifact; successful receipts and partial tokens/runtime/error remain. This is a diagnostic completeness gap, not unsafe acceptance: no failed comparison reaches acceptance. Root requested retaining these review bytes and asked the task reviewer to assess whether attaching the first failing receipt is required.

CPU checks cannot establish real BF16/A100 numerical parity, actual model runtime/memory or completed3936scientific coverage. Those remain calibration/main acquisition obligations after independent code review, exact commit rebind and operator release. No inference is authorized by the provisional artifact or this report.

## Actual original wrapper CPU closure

Executed (exit0):

`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/scripts/jobs/run_sdr_shared_composition.sh calibrate --protocol /projects/beto/swong2/Alignment/.scratch/sdr-shared-composition/implementation/protocol-provisional-v2.json --output /projects/beto/swong2/Alignment/.scratch/sdr-shared-composition/implementation/cpu-dry-run-unused --dry-run`

Returned status`cpu_dry_run`, manifest`2278cf2c75fdbf99db387c56440f0495e83b8a9ee7d5660f078812924674b0a8`,3936rows/492batches and180calibrationrows/23batches, `model_loaded=false`, `output_mutated=false`. A fresh filesystem check confirms the dry-run destination does not exist. Source snapshot hashes were freshly rechecked and all three owned files remain identical to the immutable task-review package. Full actual cache/software/source/input verification succeeded through the production wrapper, with no model load.

## Scoped fix round1 — both P2 findings addressed

This section supersedes the numerical diagnostic limitation in the initial review above. Root released only the two required findings in `task-review.md`; no old helper, arm, scientific input, model setting or outcome selection was changed. Calibration-resume restriction remains unchanged.

The additive comparison now computes the full-vocabulary finite/geometry/bitwise/argmax/max-error diagnostic before raising, without calling the inherited raise-first helper. Each row’s receipt is appended directly to the current attempt before the next physical slot is checked. Thus a late failed slot and earlier successful slots from the same control survive the hard stop, with exact row/slot/control/step and both vector hashes. The bounded raw exception remains in the failure file. Forward finite/shape rejection records current row IDs/control/step, readouts, input/attention hashes, capture/replacement keys, observed/expected geometry, dtype, finite flag, offending nonfinite physical slots and observed vector hashes. Current attempt state is initialized before setup, so a new group’s setup failure has empty current decode rows rather than preceding accepted-arm tokens. Numerical failures still raise ValueError, cannot be accepted, and block operational resume.

Setup retains the natural donor capture readout and compares it with an independent donor readout on the exact same B8/L224 IDs/mask and FP32 path (`setup_donor_readout`). It also retains the natural U5 receiver-capture readout and compares it with an independent source-only readout using the identical mapped U5 bank (`setup_U5_readout`). This is the reviewed equivalent of comparing against arm01’s independent first score, without extending tensor lifetime across arm decoding. Both controls persist full-vocabulary receipts in setup artifacts/current failure state and stop immediately on drift. Neither transplants receiver coordinates or freezes intermediate components.

These controls add2forwards per setup group:5calls inside setup_banks (3natural captures+2independent readouts), plus the existing3recipient controls, total8setup calls/group. The next-group guard now charges8setup calls plus1decoder cold allowance, then the unchanged67/129warm decode-call budget. Calibration/main timing records include the added calls and comparison/hashing overhead. The calibration cold bound also includes the observed setup-capture maximum; the repeated decoder bound remains separate. There is no whole-panel worst-case stop or changed numerical tolerance.

Exact fixed bytes:

- Runner SHA256 `d18c0ae989e386a1c637a4d7234b4a557d5083cf09bcbc9c080785244bd027b6`.
- Tests SHA256 `0c0da3ef07fe29e0ee35820bffea28f192261ae77a93e77eef96138b63d3126c`.
- Wrapper remains SHA256 `8239a864a4725c3bd4ab15f0d38e50eed22cd9afd931ffc6b801b4d5cf527c8a`.
- Immutable scoped snapshots/checksums: `implementation/fix-round1/`.
- Exact unified diff against the initial reviewed snapshots: `implementation/fix-round1/scoped-fix.diff`, SHA256 `953c75dd039bc8c1fe34652853cea57dd834ee4515c9c11d03b3416211aaffdb`.

Seven end-to-end injected regressions were first observed failing against the initial reviewed implementation: late finite repeat mismatch after a token; parametrized NaN/shape forward rejection; a new group setup failure after a preceding arm was accepted; donor-capture-only drift; U5-receiver-capture-only drift; and matching setup controls. All7passed after the fix. An additional cold-bound regression was observed failing (`0.2`decoder bound ignored`5.0`setup bound), then passed after including setup maxima. The forward rejection assertions were further checked red for missing offending-slot diagnostics before adding those diagnostics.

Final exact-source commands, with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`:

- `/sw/external/python/anaconda3/bin/python -m pytest -q tests/test_sdr_shared_composition.py` →31passed,1pinned-NNsight skip,15.25s.
- `/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q tests/test_sdr_shared_composition.py` →32passed,28.63s; the same installed astor deprecation warning.
- `/u/swong2/.local/bin/ruff check --select F scripts/sdr_shared_composition.py tests/test_sdr_shared_composition.py` →all checks passed.
- `bash -n scripts/jobs/run_sdr_shared_composition.sh` →exit0.

The injected tests run the actual batch journal, setup, decoder and failure publisher with only the external model forward/load/allocation faked. They inspect published failure JSONs, prior tokens, successful late-control slots, failed receipts and offending row/step, prove no accepted terminal exists for a failed arm, and prove hard-failure resume verification rejects. A setup failure after an accepted first group explicitly names the second group and contains no preceding decode rows. Matching setup controls persist both new receipts and exactly8measured setup forwards. The original actual tiny-NNsight natural-propagation test remains in the full32test mgnp pass.

Scoped-fix rebind: `implementation/protocol-provisional-v3-fix1.json`, file SHA256 `2b2df762997d03b2c6421fedc3a72bc90f4f187dfe597b31a467bfeca8d84afa`, manifest hash `67689e8ad232734d531ef484a5ae1b288c20030a65705d5c0543595bb025df72`. Its entire scientific payload equals v2’s payload, with unchanged scientific hash `1a29813fea112f713b66a673619afa25687a70527d832323159c92e9c4364412`; still66source and10cache files. Freshly verified all current owned-file hashes against the scoped snapshot. `implementation/fix-round1/freeze-summary.json` records this equality.

Executed the original absolute wrapper again (exit0):

`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot/scripts/jobs/run_sdr_shared_composition.sh calibrate --protocol /projects/beto/swong2/Alignment/.scratch/sdr-shared-composition/implementation/protocol-provisional-v3-fix1.json --output /projects/beto/swong2/Alignment/.scratch/sdr-shared-composition/implementation/fix-round1/cpu-dry-run-unused --dry-run`

Returned `cpu_dry_run` with exact v3manifest hash,3936rows/492batches,180calibrationrows/23batches, `model_loaded=false`, `output_mutated=false`. Destination was freshly verified absent. Structured receipt: `implementation/fix-round1/wrapper-cpu-dry-run.json`. This remains a provisional UNCOMMITTED CPU closure; root must bind the final reviewed commit and rerun before any GPU release. No GPU/job/API/notebook/git action occurred in this fix round.

## Final-review analysis fix — tri-state emitted-item agreement

Read the complete final whole-feature review; this is its sole remaining P2 finding. `analyze_panel` now publishes `baseline_agreement=true/false` only when BOTH recipient and donor baselines are EOS commitments with literal candidates belonging to their original two-item sets. The field is `null` otherwise. Equal versus distinct committed names give true versus false; two noncommitments, a cap, or a one-sided commitment remain unavailable. All pair rows, candidate fields, categories and primary contrasts remain. Any future agreement-stratified consumer must select `is True` or `is False` explicitly; null is not disagreement.

Checked current consumers with `rg -n baseline_agreement scripts tests component_analysis` and the phase `scientific-audit/` and `postprocessing/` directories. The only production occurrence is the producer; no downstream truthiness-based consumer exists to change.

The existing actual full3,936row `analyze_panel` regression now includes five input-defined test cases: equal committed names, different committed names, refusal versus evasion (two null identities), a capped baseline, and one commitment versus a refusal. Against fix1 it failed with `[true,false,true,false,false]` rather than `[true,false,null,null,null]` (focused pytest exit1,7.28s). The two-line producer change then passed. The same test verifies all3,936normalized rows,96baselines,192pair records and160direction×arm tables remain; raw-margin directional means/intervals remain unchanged; and every pair’s damaging-item source effect and source interaction match explicit hand-constructed expected values despite the noncommitment fixtures. No acquisition/intervention/protocol construction or wrapper code changed.

Final exact-source verification (threads pinned as above):

- `/sw/external/python/anaconda3/bin/python -m pytest -q tests/test_sdr_shared_composition.py` →31passed,1pinned-NNsight skip,13.09s.
- `/u/swong2/.conda/envs/mgnp/bin/python -m pytest -q tests/test_sdr_shared_composition.py` →32passed,26.49s; same installed astor deprecation warning.
- `/u/swong2/.local/bin/ruff check --select F scripts/sdr_shared_composition.py tests/test_sdr_shared_composition.py` →all checks passed.

Source is frozen for scoped final review:

- Runner SHA256 `9045b94d4b14c8fd57969ced6617a5541dac09ffbfe4e8f7ceb3ce3fcd33346a`.
- Tests SHA256 `1d1b2f073d2cdf85222f0a65bab05c1627bb68502a278b10f66170cc41276495`.
- Wrapper remains SHA256 `8239a864a4725c3bd4ab15f0d38e50eed22cd9afd931ffc6b801b4d5cf527c8a`.
- Exact snapshots/checksums: `implementation/fix-round2/`.
- Scoped diff against fix1 snapshots: `implementation/fix-round2/scoped-fix.diff`, SHA256 `9d3c1aa8f606961e1094470fc08874b591263e4c3526da6c8973b2a9d5a19281`.

Root authorized omitting another provisional full-cache freeze/wrapper repeat for this analysis-only fix. Earlier provisional source hashes are now historical; root will perform the required final COMMITTED source rebind and actual wrapper CPU dry-run after scoped review/commit. No GPU, job, git operation, cache/model load, notebook, paid API, cleanup or extra feature was performed in this final fix wave.
