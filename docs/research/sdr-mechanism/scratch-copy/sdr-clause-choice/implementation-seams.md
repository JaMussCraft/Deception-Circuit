# Minimal native clause-choice generation implementation

2026-10-26. Read-only code exploration for root/designer. Scope now640 **unprefilled** main responses, baseline first; S32/candidate6 intervention follow-up is separate. No model loading/inference, jobs, notebook execution, APIs, git operations, or original source edits performed. Only this note written. Old worktree `W=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/sdr-routing-pilot`, root-supplied base `29492146127f56c05a4087b1bfdeea0e63a4d24a`.

## Recommended three-file implementation

1. `scripts/sdr_clause_choice.py`: frozen input manifest, baseline run/calibrate/assemble/export CLI, small analysis join; import existing numerical/generation utilities.
2. `scripts/jobs/run_sdr_clause_choice.sh`: offline environment + exact cwd/interpreter + actual Slurm deadline wrapper.
3. `tests/test_sdr_clause_choice.py`: CPU contract and mocked-generation tests for only the new seams.

Prefer root-created isolated sibling `Deception-Circuit/.claude/worktrees/sdr-clause-choice` based on2949214, so the original evidence worktree/source/HEAD stay untouched. If root instead explicitly authorizes additive files on the existing original research branch, imports also work there; no old file needs editing. All git/worktree actions remain root-owned. The generation kernel imports are relative to the chosen checkout; old static protocol builders must never run.

Estimated new production Python: ~180–280lines when existing kernel naturally fits; ~270–380lines if configurable-L baseline loop is needed. Wrapper ~35–60lines, CPU tests ~100–160lines. These are planning estimates, not promises. A new source/manifest/run hashing framework, sharding registry, or fork of the old1000line journal runner is unnecessary for80main batches.

## Exact intact reuse seam (preferred when naturally fitting)

`W/scripts/sdr_cue_positions.py:184 decode_batch(model, rows, protocol, *, donor_rows=None, family_keys=(), site=None, stress=False, state=None)` can run an intact baseline directly:

```python
from scripts import sdr_cue_positions as pos
state = {}
result = pos.decode_batch(model, rows, runtime_protocol, state=state)
```

Leave donor_rows/family_keys/site unset and stress=False. **This function does not call its outer frozen-protocol builder/verifier**, so no384row/640pair/parent-spec protocol needs to be cloned. No position metadata is needed without head keys.

Inputs:

- each row: `{id, ids, stem}` is sufficient for decode; retain prompt, length, fixture/story IDs, factor labels and candidate mapping in the frozen manifest. For this **unprefilled** study, `stem=''`; the prompt ends immediately after the assistant header/newlines, and emitted text is the continuation itself.
- protocol: `scientific_hash` + `payload.eos` (the real EOS list) and optional `payload.vocab_size`(128256); `provenance.cache` tokenizer directory. Optional `_tokenizer` avoids repeated local tokenizer loads, `_deadline` is epoch seconds, `_stop={'requested':False}` supports termination. Do not serialize these runtime additions into the frozen scientific payload.
- exact kernel geometry **B8,L224,max64** is hardcoded. All rows must satisfy `len(ids)+64<=224`; no truncation. This is an implementation eligibility condition after CPU tokenization, **not a scientific wording restriction**. Designer must not simplify prompts merely to fit160tokens.

Outputs: `{rows, controls, captures, timings, forward_seconds, packing_seconds, elapsed_seconds, error}`. Each generation row contains id/protocol_hash, generated_ids, logical_readouts, finish(eos/capped), status, physical_slot, continuation/raw_continuation/text/raw_text. Controls are per-row full-vocabulary comparisons with step/control, finite/bitwise/max_abs_error/identical_greedy/tolerance and expected_sha256/observed_sha256. Intact uses no banks/captures. Step0 has repeat and empty controls; every decoding step checks finite full FP32 vocabulary. Greedy is argmax over **all128256tokens**, not a two-candidate decision. Mixed EOS stops only the completed slot; dummy slots never become real rows. `use_cache=False` is set/restored within this function.

## First-step identity/readout evidence without modifying the kernel

The position decoder's **actual step0 full vector checksum is already in each repeat/empty control** (`cc.compare_full`, circuits.py:222). Add one independent preflight forward per physical batch, through the identical path and geometry:

```python
ids, mask, _ = n.make_batch(rows, batch_size=8, sequence_length=224, device=device)
with torch.inference_mode():
    capture = hooks.capture_forward(model, ids, mask, components=[hooks.READOUT_KEY])
    logits = pilot.capture_logits(model, capture)
assert logits.dtype == torch.float32 and logits.shape == (8, 128256)
assert bool(torch.isfinite(logits).all())
# For each REAL slot: save row ID, prompt/token hash, physical slot,
# capture.readout[slot], cc.tensor_sha(logits[slot]), argmax and top-two gap.
# Assert capture.readout[slot] == len(row['ids'])-1.
# After decode: assert first generated ID == saved argmax, and
# logical_readouts[0] == saved readout. Require the actual repeat/empty
# expected_sha256 == saved preflight SHA, both comparisons pass.
```

Set model.eval()/use_cache=False **before preflight** as well. Record the kernel's actual full-vector comparison receipt, not a fabricated checksum. Existing same-path runs were bitwise; exact preflight/kernel checksum equality is a stronger fail-closed identity check. If it fails, stop and diagnose rather than relaxing it post hoc. The normal within-kernel numerical acceptance is max_abs_error<=1e-5 **and** identicalgreedy, with finite FP32 tensors. `cc.compare_full` raises on failure and records both hashes.

This retains first-token argmax as a numerical identity receipt, separately from semantic EOS behavior. On an unprefilled prompt the first token can be a quotation, lead-in, refusal, or non-item: it is not a behavioral candidate label.

`capture_logits` is `W/scripts/sdr_routing_pilot.py:407`; it indexes the final-norm INPUT at `capture.readout` and calls `hooks.readout_logits` (`component_analysis/hooks.py:583`) to recompute actual final RMSNorm and unembedding in FP32. Do not replace this with `.logits.float()` on an already BF16 unembedding, two-candidate softmax, or a different explicit-mask path. HF's own BF16 logits are not the reference vector for FP32 ranking identity.

## Configurable alternative if new prefixes exceed160tokens

`W/scripts/sdr_native_controls.py:197 complete_batch(model, rows, protocol)` is the short general-length ancestor. It accepts payload.batch_size/sequence_length/max_new_tokens/eos and uses `n.make_batch`(178), `n.compare_vectors`(188), `pilot.capture_logits`, and the same `hooks.capture_forward` path. Its own old outer `_run` is unnecessary.

However, unchanged complete_batch exposes no full first-step hash/readout metadata, its `.float()` does not assert originating FP32, and its `_checkpoint_batch` receives rows/stats **not logits**. Do not claim that callback supplies logits. If needed, add an ~85–110line baseline decode function **in the new file**, derived from this loop with:

- frozen B8, `L=32*ceil((max_prefix+64)/32)`, max64 and cached tokenizer supplied once;
- assert FP32/full-vocab shape/finite at every step;
- use `cc.compare_full` for step0 repeat/empty and record actual first-step vector hash/argmax/readout + preflight identity;
- keep exact right padding/logical append/mixedEOS/dummy/cap semantics;
- return per-batch state/timings; no per-token filesystem writes.

This is a small additive configurable kernel, not a modification to old source. Choose **one** kernel at CPU freeze and bind its name/B/L/source hash in the manifest. Do not switch after viewing outcomes. Prompts can be longer than224 total if this option is chosen and memory/timing calibration is renewed.

## Proportionate provenance, atomic batch outputs and resume

Frozen manifest: exact ordered640main rows and distinct calibration rows; per-row prompt/ids/length/empty stem/factors/semantic candidate mapping; fixed ordered batch memberships; source-file hashes+root-supplied committed source ID; cached checkpoint revision and model/tokenizer/config file hashes; software versions; B/L/EOS/max64; prespecified analysis/response rubric. A single canonical SHA binds scientific inputs. Keep run allocation/deadline/hardware outside that scientific hash.

Reuse `n.canonical/digest/file_hash/atomic_json/software/cache_hashes`; for source closure `pos.source_hashes()` plus the new Python/wrapper/test files is a simple existing closure (it hashes its imported old modules/packages). Hash model files once at freeze and once at execution preflight, **not per batch**. Root supplies full committed source; agent does not inspect/mutate git. Distinguish model **snapshot/revision identity** from atomic output **checkpointing**.

For each fixed batch, write an attempt marker before decode; keep `state={}` externally so exceptions preserve partial token state; after checks write **one immutable accepted terminal JSON** by atomic temp+fsync+rename, containing row IDs/order, manifest/run hashes, first-step receipts, decoder outputs/controls and timings. A small progress JSON can list accepted IDs/counts. No per-token writes; no full-panel rewrite after every token. `n.atomic_json` is enough under single-writer ownership; if overwrite rejection is required, check occupied path and fail before write. Do not make stronger power-loss durability claims than the helper provides.

Before starting a batch, check enough remaining time for a calibrated full64step batch plus IO/shutdown. Signals set `_stop.requested`; existing check_deadline runs before each forward. On failure/deadline, write a **distinct failure record** with partial state, leave batch unaccepted and all remaining IDs visible. On resume, enumerate/hash-check accepted terminal files against frozen membership and skip only valid complete batches; never silently replace an accepted terminal or count a failed partial row as honest. Final assembly requires640unique planned IDs and explicit finish/status for every row. An interruption can require a later root-released invocation; no automatic new job.

Avoid saving every vocabulary vector for every step. Actual full vectors are compared in memory; firststep full-vector hashes, argmax, gap, numerical receipts and optionally saved firststep FP32 tensors provide auditability without gigabytes of redundant logs.

## Cached model, environment and wrapper

Verified historical cached checkpoint:
`/work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659`.
Historical metadata:4safetensors shards + index, config/generation_config/tokenizer/special-token files; EOS `[128001,128008,128009]`. Reverify actual cached bytes at new freeze; snapshot path alone is insufficient.

`hooks.load_analysis_model(cache,device='cuda',dtype=torch.bfloat16)` creates unmodified HF LlamaForCausalLM wrapped by nnsight. Assert CUDA/BF16/SDPA/eval and `use_cache=False`; no prunable model or remote=True. Historical mgnp interpreter `/u/swong2/.conda/envs/mgnp/bin/python`:Python3.12.13,torch2.11.0+cu128,transformers5.13.0,nnsight0.7.0,tokenizers0.22.2,numpy2.5.1. These are verified **past receipt values**, not a claim of the current installed versions; new manifest records actual environment.

Wrapper examples `W/scripts/jobs/run_sdr_native_controls.sh` and `run_sdr_cue_positions.sh`: use `set -euo pipefail`, guarded bashrc+conda init or explicit Python override, offline flags HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE=1, BLAS/OMP threads1, actual Slurm StartTime/EndTime binding. New wrapper must use its own cwd/interpreter variable, not the old position wrapper's hardcoded old-worktree path. Root/operator dry-runs the **actual new absolute wrapper** with model loading disabled before any release. Slurm `--wrap 'exec bash ABS_WRAPPER ...'` avoids BASH_SOURCE pointing at Slurm's spool copy; explicit --chdir/--time and absolute log paths. Do not use shell tracing or print credential-bearing environment.

## Runtime evidence and complete640 operational budget

Authoritative existing A100 references:

- `.scratch/sdr-cue-followup/operator/main-final-slurm-receipt-2949214.json`:job23194944,4224EOS rows(384intact+3840patch),4999forwards, **1109actualA100seconds** vs3300reserved. Exact hardware NVIDIAA100-SXM4-40GB, peak17.05GiB in accompanying `main-operator-completion-summary-2949214.json`; forward_seconds794.536, total decoder848.466, mean output3.822tokens,max28. This implies ~0.159seconds/forward on that exact B8/L224 path; not a new hardware guarantee.
- `.scratch/sdr-cue-followup/operator/calibration-completion-summary-2949214.json`:403actualA100seconds, premodel81.378/model-load13.292seconds. Natural intact B8 took1.138decode seconds for7forwards (row lengths3/3/3/3/3/5/3/3), publication.145seconds. Forced suites tested patch kernels and are not a baseline-only calibration requirement.
- `W/outputs/_analyses/sdr-cue-probe/main-5f74d0c-20261021T204828Z/receipt.json`:512neutral responses,728forwards,204actualH200seconds; premodel61.614/model-load7.961/IO46.225seconds. Old per-token checkpointing increased IO and a full-cap forecast reserved8100seconds despite204actual. Do not repeat that reservation policy.

640main responses =**80B8batches**, distinct calibration extra. Baseline natural generation requires per-batch `(max emitted length)+2` forwards; independent firststep preflight adds1. At historical5–10max emitted tokens/batch, ~640–1040forwards (~100–170A100compute seconds), plus measured startup/hashing/load/80atomic writes/final assembly. A **rough4–8minute expected allocation** is a planning orientation only; unprefilled responses can be substantially longer, and largerL changes timing. Exact64cap ceiling is80×67=**5360forwards**, ~853A100compute seconds at the historical mean, plus fixedcost/IO; do not claim all640fit a10minute reservation under all outcomes.

Use one small fresh disjoint natural timing calibration (e.g.16–32rows, frozen coverage of design families), no scientific outcome selection, then **1.5×observed remaining batch work + measured fixedcost + explicit shutdown/final audit** to choose main walltime. Maintain a per-batch64step admission guard and planned durable resume rather than reserving an oversized worst-case horizon. Kernel/geometry/hardware changes invalidate direct calibration reuse. Root/operator reserve full walltime×GPUcount separately before actual submission; this note releases no resources. All640main prompts must eventually be retained/scored, including capped/unresolved/refusal outputs; calibration is excluded from the640denominator. Optional S32/candidate6 transplant rows are additional compute and remain unreleased.

## Minimal useful CPU tests and later patch risks

1. Frozen factor coverage/640unique IDs, literal prompts fact-preserving outside clause, candidate identity mapping, exact tokenization/no truncation, empty stem and geometry eligibility/configurable-L selection; no notebook execution.
2. Tiny mocked decoder: mixedEOS, firststepEOS,64cap, rightpad/dummy slots, logicalreadout=length-1, full-vocab noncandidate greedy; no duplicated/skipped tokens. Assert firststep receipt agrees with generated token and actual control hash.
3. Numerical failures: NaN/Inf, wrongdtype/vocabshape, maxerror>1e-5, or differentgreedy despite small absolute error all fail. Firststep slot/hash/readout mismatch fails.
4. Source/manifest/model-config tamper rejected; expireddeadline does not call model; atomic terminal failure does not count acceptance; occupiedacceptedbatch not overwritten; resume completes exact640coverage with no duplicate acceptance. Actual wrapper dryrun must not load model or touch real GPU outputdir.

Reuse existing `tests/test_sdr_native_controls.py` and `test_sdr_cue_positions.py` mocking patterns. Run focused new tests under base and mgnp (no model inference); no broad suites until changes justify them. No need new tests that merely assert constant line-for-line duplicates.

Later original-mask patches can reuse position decoder donor_rows/family_keys/site and frozen prefix masks after a **separate behavior/support gate and release**. S32 exact family is `families, bindings = sdr_cue_circuits.select_families(); families['S']` (outer function also expects old audited suite files); freeze the known exact list/hash, not a new trained mask. Candidate6 is `sdr_routing_pilot.FAMILIES['candidate6'] = [(12,6),(13,5),(13,20),(13,21),(14,24),(17,26)]`. Position kernel's pack_bank requires matched masks/B8/L224/head_dim128; unequal-length new clauses require verified token correspondence or explicitly defined mapped positions. Do not silently apply identity mapping across inserted/deleted clause tokens. Baseline need not implement any of this now. Full/self capture controls excluding READOUT and patched-repeat controls belong to the later patch validation; baseline-only numerical checks do not certify a transplant kernel.
