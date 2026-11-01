# Native SDR composition: implementation seams

Read-only source audit, 2026-10-26. Worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot`. `timeout 20s git rev-parse HEAD` returned `4f0278487b0285dd27cbc34d20d88c911dc5562a`; bounded `git status --short` returned no entries. Root AGENTS, shared `.claude/CLAUDE.md`, memory index and SDR mechanism/usage notes were read; no repository-local AGENTS/CLAUDE file existed at the checked repository/worktree root locations. Root reports startup synchronization already completed. No model, notebook, job, external API, git mutation or production-code edit was performed. This document is the only write by this worker.

## Smallest reliable route

Add one runner, its focused tests and one absolute-path shell wrapper. Import the existing hook/scoring/batching primitives; leave every old runner, hook file, frozen manifest and result unchanged. The new scientific operation is **natural propagation with a downstream clamp/rescue**, which the existing `hooks.capture_forward` already supports. No new hook implementation, training, prunable model or NNsight remote execution is needed.

For a fixed physical recipient/donor batch, take three setup captures:

1. Natural recipient: capture source keys, downstream keys and `READOUT_KEY`.
2. Natural donor: capture source keys and `READOUT_KEY`.
3. Recipient with the mapped source transplant only: capture all proposed downstream keys and `READOUT_KEY` together. This is the naturally induced downstream state; all intermediate heads and MLPs run freely.

From those captures construct independent immutable banks for source transplant, clean recipient receivers and induced recipient receivers. Reuse them across all arms of that same physical batch. Baseline, source-only, clean-receiver-only, source-plus-clean-receiver and induced-receiver-only define the core comparison. Joint Q/K and head-quartet output banks are dictionary unions over unique keys with the specified masks; no extra setup forward per receiver is necessary. Capture benchmark source families in setup 1/2 if U6/S32/outside controls are scheduled. Delete large capture objects after cloning compact selected tensors; do not retain all-component activation caches across the panel.

**Do not call `path_patching.receiver_inputs` for this natural-chain question.** At `component_analysis/path_patching.py:644` it freezes embedding/every other head/every MLP at recipient values. That measures a controlled direct edge. Its `readout_from_receivers` at line 665 is an ordinary receiver-replacement forward and is reusable in spirit, but calling `capture_forward` directly avoids constructing full `Streams` objects and accidentally inheriting full freezes. `sdr_routing_pilot.assemble_path_streams` at line 655 similarly captures every component and is unnecessary here.

## Exact source references

All source paths below are relative to the worktree above.

| Function/file | Reuse or constraint |
|---|---|
| `component_analysis/hooks.py:53 load_analysis_model` | Unmodified HF Llama model wrapped by pinned NNsight; local cache, BF16, SDPA. |
| `hooks.py:230 geometry` | Assert 32 attention heads, 8 KV groups, head width 128, hidden width 4096. |
| `hooks.py:321 _write`, `:374 _traced_forward`, `:490 capture_forward` | Boolean masked replacements and simultaneous source/receiver writes already exist. Captured values are effective values after writes. |
| `scripts/sdr_routing_pilot.py:174 semantic_map`, `:202 remap_capture` | Original named-span correspondence and recipient-coordinate donor remapping. |
| `sdr_routing_pilot.py:407 capture_logits`, `:415 score_capture` | Real final norm/unembedding recomputed in FP32; full-vocabulary argmax, truth margin, probabilities, checksum and top-k. |
| `sdr_routing_pilot.py:958 family_replacements` | Ordinary masked head transplant, unmapped current values remain free; dose 1 is an overwrite and dose .5 interpolates baseline/donor. This helper infers shape from captures and can work at L224; no need to use its old L128 caller. |
| `scripts/sdr_native_controls.py:178 make_batch` | Fixed physical B8/L224 right padding with harmless dummy rows. |
| `scripts/sdr_completion_diagnostic.py:315 assistant_stem` | Extract original forced assistant stem for full response reconstruction. |
| `scripts/sdr_cue_circuits.py:222 compare_full`, `:228 prefix_positions`, `:235 checked_assignment`, `:296 decode_batch` | Reuse numerical comparison, original-prefix masks and real assignment check. Decoder is the closest template for an additive mixed-bank decoder. |
| `scripts/sdr_cue_positions.py:162 pack_bank`, `:186 decode_batch` | Useful immutable-bank, capture receipts and per-step repeat patterns, but cannot be used unchanged for mixed masks or receiver kinds. |
| `sdr_cue_positions.py:331 run_lock`, `:370 begin_attempt`, `:389 make_terminal`, `:468 commit_terminal`, `:474 verify_completed_batches` | Useful sealed per-batch journal design. Existing validators are hard-bound to old protocol counts/schema; reuse generic sealing/publishing helpers or reproduce a much smaller new schema, not the old protocol validator. |

`capture_forward` still saves readout residuals across layers because it always requests `residual=True`; source/receiver outputs themselves are selective. NNsight captures full projection-site values internally before slicing selected heads, so compact clones plus early deletion matter. Do not call `all_component_keys` or retain `streams.clean_outputs` merely to clamp a few receivers. A B8/L224/head128 BF16 bank is 458,752 bytes per key; U5 plus a handful of Q/K/V/head keys is only a few MiB of compact bank storage. Underlying full-site captures can be larger, but remain batch-local.

## Hook semantics and GQA

The sole intervention surface is NNsight `model.trace`; it is not a separate set of Torch `register_forward_hook` callbacks. Execution order in `hooks.py:438` is Q projection, K projection, V projection, attention head outputs at **input to `o_proj`**, MLP input/output, then final norm input. Never slice the summed `o_proj` output as if it were a head. Q/K projection captures are before rotary-position application; under the unchanged recipient prompt the recipient's own rotary positions apply after replacement. Donor maps with shifted token locations are therefore meaningful interventions, not equality of final rotated Q/K states.

`('q',17,24)` affects Q head 24 only. `('k',17,6)` or `('v',17,6)` affects KV group 6 shared by query heads 24–27. Report that full footprint. These grouped interventions touch candidate L17H26 and outsider L17H25 as well as selector L17H24. `('head',17,24)` is the selector's output only; `head17:24–27` is a distinct whole-group output clamp. `('head',24,27)` is a later output receiver, downstream of both L17H24 and L17H26.

For a strict source→L17 receiver claim use U5 = candidate6 minus L17H26: `(12,6),(13,5),(13,20),(13,21),(14,24)`. The L17H26 output cannot be upstream of same-layer Q/K/V. U6 and H26-alone remain informative benchmark arms, with their different causal location explicit.

## Frozen families and controls

Original `FAMILIES` at `sdr_routing_pilot.py:27`:

- candidate6: L12H6, L13H5/H20/H21, L14H24, L17H26.
- selector2: L17H24, L24H27.
- outsider2: L15H8, L17H25; inside D but outside shared32.
- frozen outside_mask2: L17H18, L12H19; outside D∪H∪F.

Shared32 from the immutable Stage1 manifest is:

```
L8:  H0,H1,H8,H9,H11,H14
L9:  H20,H26,H28,H31
L10: H1,H2,H3,H28
L12: H4,H6,H7,H13,H28
L13: H5,H18,H20,H21
L14: H4,H5,H23,H24
L17: H24,H26
L24: H16,H26,H27
```

All candidate6 and both selector heads are in shared32. Ordinary family unions use set union to avoid duplicate overwrites. Frozen shared32 derives from D∩H∩F in `frozen_families` at line 248, with suite and mask hashes recorded. The later original-mask cue code `sdr_cue_circuits.select_families` at line 119 independently asserts original seed42/coarse-mask identity; it is deliberately hard-bound to its historical audit. For this additive runner, bind the already-frozen original manifest family values and original mask file hashes, instead of rebuilding masks through a validator tied to a different old study.

Deterministic geometry controls can be nominated by the lowest-index-outside-union rule, frozen before results: Q17H0, K17g0/V17g0 (H0–3 are all outside D∪H∪F); L24H0 is a matched-layer output control. Entire L17 KV groups outside the union are 0,2,3,4,5,7. If needed, an exact-layer five-head outside source is L12H0 + L13H0/H2/H3 + L14H0 under the same smallest-unused-index rule. These are prospective control nominations, not historical effect matches.

## Native data and pairing

Immutable original parent:

`outputs/_analyses/sdr-routing-pilot/stage1-retry-f7cb49f-20261021T002501Z/manifest.json`

Internal manifest hash: `36bff9ebb6e4d9d3954ba81ce0f281664d0f887041109c986c5a86fd9cdd3ff0`. It binds 48 historically selected stories and 480 saved prompt variants: 288 P, 96 H, 96 N. Native pressure plus two alternative P clauses × two factual polarities, with one H and one N per polarity. P is the original saved pressure; H replaces only that clause with matched honest instruction; N deletes it. P/N have shifted prefix lengths. Alternative P clauses were baseline-only in the old patch schedule. Do not call archived P↔P′ truth flips a clause-only manipulation.

`panel_for_record:231` and `fixed_patch_plan:295` are the original construction/recipe; `build_manifest:327` locks the primary original SDR test dataset and excludes v2. Old schedule had 192 same-truth pressure-presence directed pairs (PH and PN combined), 192 changed-truth pressure-presence pairs, 96 same-pressure factual flips and 96 cross-story N controls, of which 32 lacked partners. The full saved `maps` already covers more allowed within-story pairs than the scheduled patches.

For the proposed 24 original confirmation stories, four native prompts/story (P0,P1,N0,N1) give 96 unique baselines; P0↔N0, P1↔N1, P0↔P1 and N0↔N1 give eight directed pairs/story =192. The extra N0↔N1/factual-polarity balance uses already frozen original prompts/maps but is a new prospective intervention schedule; do not describe it as identical to the archived 12-pair schedule. The original confirmation label is retained for provenance; these stories have already been measured and are not new unexposed confirmation.

Reuse exact `prompt`, `ids`, `length`, truth/other token IDs, story/split and source IDs from the original manifest. Do not reconstruct token IDs from new formatting, add suffix spaces or remove the supplied stem. New row adapter needs `id=variant_id` and `stem=assistant_stem(v)` (without the two shell newlines). Example original assistant text is `The reading I will show you is`; audited stem segment includes initial newline token and has IDs `[271,791,5403,358,690,1501,499,374]`. One example P/H prefix has length114 and N has length100. Audit `stem` anchor includes `\n\n`, whereas the reconstruction helper intentionally strips the shell separator. Label full supplied-stem+generated continuation and retain raw continuation separately.

Original model snapshot: `/work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659`. Stage1 software: Python3.12.13, Torch2.11.0+cu128, Transformers5.13.0, NNsight0.7.0, datasets5.0.0. New provenance should bind cache config/tokenizer/generation config and weight shards, all source hashes and exact physical geometry. Old `original_component_overlap=[]` is known unreliable historical negative-exposure metadata; preserve without interpreting it as no overlap.

## Minimal new decoder and controls

`sdr_cue_circuits.decode_batch` accepts externally built replacement dictionaries, including receiver keys. However, at its frozen-bank validation it requires **every replacement mask equal the full original prefix**. The source map here is partial-common, so unchanged reuse fails. `sdr_cue_positions.decode_batch` requires one shared site mask and its packer allows head keys only. Neither can accept the proposed combination unchanged.

Copy the small no-cache fixed-slot decoding kernel into the additive runner, keeping imports for batching, FP32 scoring, generation record construction, assignment/compare helpers and tokenizer. Replace the one-global-mask invariant with a per-key frozen mask contract:

- Source bank: donor head outputs remapped to recipient coordinates only on saved common semantic map; unmapped positions remain natural.
- Receiver bank: clean or naturally induced recipient states at every **original recipient prefix** position; no donor coordinate mapping for receiver states captured on that recipient.
- Every head/Q/K/V value has shape B8×L224×128, BF16/finite; each Boolean positions mask has shape B8×L224 and is a subset of the original recipient prefix. Dummy rows and generated positions are always false. Values and masks are cloned and version-checked across decoding.
- `use_cache=False`; every step recomputes the full fixed L224 sequence. Source/receiver banks remain fixed on the original prefix for all steps; the growing generated suffix and generated-token receiver states remain free.
- Use all three cached EOS IDs `[128001,128008,128009]`, greedy FP32 argmax and cap64; retain EOS/cap/errors/all planned rows. Finish all arms already frozen, without favorable-row selection.

The first-token mechanistic readout must use the **same B8/L224 kernel, masks, dtype and FP32 final readout** as EOS. It is cheap to score every arm before continuation and save its full checksum plus emitted token; decoder step0 must exactly match that arm's stored checksum/argmax. Do not compare a new L224/A100 baseline to old L128/H200 and call cross-shape/hardware inequality a failed no-op: same-path new controls are mandatory; archived cross-hardware/shape replay can be reported separately.

Numerical/control minimum: recipient repeated/empty-hook and selected self-replacement (head plus Q/K/V), natural donor/source setup-capture agreement, each source/clamp/union arm repeated at full vocabulary, actual `_write` untouched-position checks, original/generated/padding/dummy mask checks and immutable-bank receipts. A clean receiver clamp alone is a scientific arm and a powerful baseline-prefix no-op at step0; after generated trajectories differ it must not be silently expected to preserve another arm's response. Fresh forced64 calibration stresses first/last step and masks; retain short natural calibration for per-arm runtime. Avoid tautological replacement of READOUT. Unit tests should use distinctive tensors and small fake/tiny models to prove natural intermediate propagation, source+receiver composition, wrong-site rejection, full GQA group footprints, and first-token/EOS identity; no notebook execution.

Existing useful tests: `test_sdr_routing_pilot.py:68,88,162,306,346,453`; `test_sdr_cue_circuits.py:49,105`; `test_sdr_cue_positions.py:149`; `test_path_patching_passes.py:160`; `test_nnsight_hooks.py:56`. Runtime integration of the same pinned model environment remains necessary after CPU tests.

Attention patterns are optional. `hooks.attention_weights:532` switches to eager and accepts no replacement dictionary. It cannot produce source-patched/clamped attention unchanged. Do not quietly compare baseline eager attention to patched SDPA logits as if both were one exact path. Getting patched attention needs a new supported trace entry point or an explicitly reviewed hook extension; omit that add-on from the minimal no-hook-change route. Q/K/head state changes and causal clamp/rescue effects can be measured with the current primitives.

## Cost grounded in actual receipts

The original Stage2 main `.../stage2-main-6a2ea52-20261021T005608Z/calibration.json` records 7,360 B8/L128 forwards, 23.850s model load, 18.887GB peak and no unmeasured outcomes. Its `cost.json` measures 513.264s inside Python; operator Slurm ledger records **531s allocation actual**. Net Python work after load is about0.0665s/forward, including serialization and heavy full-freeze traces. Do not conflate Python elapsed with Slurm actual.

The later same-model A100 B8/L224 position calibration at `.scratch/sdr-cue-followup/operator/calibration-2949214-20261025T163125Z/calibration.json` records ~0.160s measured forward time: natural patched batches were 11/31/35 forwards with1.75/4.96/5.60s forward time; natural max response lengths5/15/17. Full forced64 bound45.927s/batch; premodel81.378s and startup13.292s were observed separately. Its main completed4,224 rows/528 batches in **1,109 Slurm seconds**, versus3,300 reserved; calibration403s. Phase total1,512actual versus4,500reserved, zero API. These are receipts, not guarantees for new receiver clamps.

For the current **3,936-row design** (96 baseline +192pairs×20arms), B8 gives12 baseline batches and480 intervention batches. Natural per-batch max completion length3–17 with patched-repeat each step means roughly2,900–16,500 decoder forwards before setup/calibration; at observed A100~0.16s/forward, raw decoding is roughly8–44minutes. One setup triple per192-pair panel is72 forwards (~12s), plus extra setup source families and control work; setup reuse is therefore cheap relative to decoding. At cap64 the hard decoder budget alone is12×66 +480×128 =62,232forwards, roughly2.77A100hours at that rate. The large difference is why fresh natural calibration and durable remaining-batch resume matter. Actual cap64 forced calibration remains a safe-start check for an individual batch; do not multiply the worst isolated timing by all remaining work and compare it repeatedly with already-elapsed allocation time.

A smaller first-token-only phase across all3,936rows costs only492 scoring forwards plus setup/repeats (likely minutes including model/startup), and can provide the mechanistic matrix before bounded EOS validation. If all3,936EOS rows are retained, propose a resumable one-hour allocation only after exact source/arm calibration supports it; forecast natural per-arm measured work×reasonable uncertainty plus startup/publication/shutdown once, and calculate against remaining deadline. Do not present sub-hour completion as established by historical mean lengths. H200 should be faster but needs L224 receiver-specific calibration; no direct A100/H200 ratio is established by these different scripts.

The wrapper should follow `scripts/jobs/run_sdr_cue_positions.sh`'s verified absolute original path, approved cwd, real Slurm start/end binding and offline mgnp invocation. Old pilot sbatch has closed2-hour cap/H200-only logic and should not be reused as the new budget controller. Use a new output namespace, sealed calibration/source/protocol binding, per-accepted-batch journals and allocation-specific receipts, with no old-output mutation. Operator alone owns reservations/accounting. No job is released by this note.

## Interpretation boundary

Measured natural sender→receiver blocking/rescue would address how shared computations compose under the original native reporting task, including reuse for no-pressure/factual operations. It need not pass a new deception-specificity gate. Q/K rescue establishes conditional causal influence of those receiver states in this intervention design; it does not by itself establish unique natural information routing, complete mediation, strategic intent or an end-to-end deception mechanism. A clean-clamp interaction is contextual blocking, not a proof of exclusive transmission. The closed named-consequence3840 grid and failed gates remain closed. No v2/selective/Bridges-2 work belongs in this implementation.

The read Claude usage-limit note is explicitly about Claude-service counters. This code audit used Codex Sol; Claude usage.json is not a measure of this worker's Codex service budget.
