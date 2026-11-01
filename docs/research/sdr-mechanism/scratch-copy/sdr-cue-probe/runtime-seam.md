# Cue probe: narrow additive runtime seam

2026-10-21. Read-only code exploration for the lead-selected **512 main / 64 calibration** behavioral cue probe. This note is the worker's only write for this assignment. No source edits, tests, models, GPU jobs, notebook execution, git changes or API calls. Other agents own scientific spec/plan/review. Lead compactions 4.

All source paths below are relative to `Deception-Circuit/.claude/worktrees/sdr-routing-pilot`, verified HEAD `1eb79892b0c4a428774cf340350d2297d9ec58f7`. Frozen native-controls science and failures remain immutable. New runs need their own source commit, payload/hash, output namespace and calibration; existing numerical receipts are provenance examples, not transferable calibration.

## Recommended boundary

**Import unchanged `scripts.sdr_native_controls.complete_batch(model, rows, protocol)` directly, and build a small cue-specific outer runner.** The generation primitive is genuinely shape/panel generic and does not call the old verifier, release registry or shard machinery. Do not invoke old `run_main`, `run_calibration`, `_run`, old CLI, old blind-export/join wrappers or old analysis on a forged 512-row protocol. Their old-panel contracts are intentional and must stay intact.

Minimal three additive files:

1. `scripts/sdr_cue_probe.py`: cue renderer/freeze/verifier; explicit calibration/main dispatch; small checkpointed outer runner around the imported primitive; strict new-calibration/main receipt checks and budget guard; cue-specific blind export/analysis as required by the science spec.
2. `scripts/jobs/run_sdr_cue_probe.sh`: short actual-allocation/environment wrapper following the old safe pattern, dispatching the **new** script.
3. `tests/test_sdr_cue_probe.py`: new scientific invariants, release boundaries, failure preservation and adapter tests. Do not copy old test suites merely to rename them.

No old file needs modification. No generic new registry, shard platform, old-cancellation receipt, dynamic claim engine or pipeline framework is needed for this small panel. If a one-job main allocation cannot satisfy the calibrated full-cap guard, stop and report that operational fact; do not silently subdivide/retry or relax the science.

## Exact callable seams

`n` below means `from scripts import sdr_native_controls as n`.

| Function and source | Use in new adapter | Important contract |
| --- | --- | --- |
| `n.canonical(value)` / `n.digest(value)`, `:42-46` | Canonical scientific/provenance hashes | UTF-8 sorted compact JSON, ensure_ascii=False |
| `n.file_hash(path)`, `:48-52`; `n.read_json(path)`, `:54-55` | Source/artifact hashing/loading | No model access |
| `n.atomic_json(path,value)`, `:57-61`; `n.fresh_output(path)`, `:63-67` | Fresh immutable run dirs and atomic checkpoints | Parent directory must already exist; existing output aborts |
| `n.load_tokenizer(cache)`, `:72-74` | CPU offline tokenization | `local_files_only=True`; encode prompts with add_special_tokens=False |
| `n.software()`, `:76-83`; `n.cache_hashes(cache)`, `:92-97` | Exact runtime/software/cache binding | Package RECORD/METADATA plus sys.version; cache includes model shards/config/tokenizer |
| `n.source_hashes()`, `:85-90` | Base imported-source hashes | Must **extend** with the new three files; does not discover them automatically |
| `n.make_batch(rows,*,batch_size,sequence_length,device)`, `:178-186` | Used internally by complete_batch | Fixed right padding, dummy first-mask token, no truncation |
| `n.compare_vectors(expected,observed)`, `:188-194` | Used internally for controls | Full FP32 shape, finite values, max error≤1e−5 AND identical greedy token; bitwise recorded |
| `n.complete_batch(model,rows:list[dict],protocol:dict)->list[dict]`, `:197-258` | **Primary reuse primitive** | See next section; no old-panel verifier called |
| `n.bind_allocation_operations(proposal,*,allocation_end,allocation_start)`, `:261-264` | Generic actual Slurm bounds | Binds timestamps and min(proposed reserved,actual allocation); metadata-only |
| `n.verify_operations(operations)`, `:267-272` | Operations schema/future deadline guard | Requires hardware/reserved/deadline and startup/IO/shutdown buffers |
| `n.check_deadline(protocol)`, `:274-276` | Primitive and outer loop | Honors `_stop.requested` and `_deadline` epoch |
| `n.forecast_main(protocol,calibration,operations,*,batch_count=None)`, `:278-292` | Reusable conservative full-cap forecast | Computes total batches from new main length; fixed IO growth48 is conservative for512; details below |
| `n.runtime_identity(operations)`, `:294-300` | Actual GPU identity | Requires SLURM_JOB_ID, CUDA, exactly one visible GPU, approved class in name; records class/name/capability/memory/count |
| `n.generation_map(protocol,generations)`, `:601-605` | Optional generic coverage check | Exact new main IDs/count and protocol hash; no old verifier |
| `n.view_for(row,generation)`, `:607-610` | Optional blind-view semantics | Full stem+continuation/options/finish; use new hash namespace if avoiding old view-ID prefix is desired |

Lower-level imports are already exercised by `complete_batch`:

- `component_analysis/hooks.py:53`: `load_analysis_model(model_name:str,*,device:str='cuda',hf_token:str=None,dtype=None)` loads SDPA nnsight model.
- `hooks._hf(model)`, `:199`; `device_and_dtype(model)->tuple`, `:211`; `attention_implementation(model)->str`, `:218`; `all_component_keys(model)->list`, `:253`.
- `hooks.capture_forward(model,input_ids,attention_mask,*,components,positions=None,replacements=None)->Capture`, `:490-507`.
- `scripts/sdr_routing_pilot.py:407-412`: `capture_logits(model,capture)` selects each row's logical readout residual and calls `hooks.readout_logits`.
- `hooks.readout_logits(model,residual,*,scale_from=None)`, `:583-622`, computes real RMSNorm and unembedding in FP32 over the **full vocabulary**. Do not replace this with captured BF16 logits, candidate-only argmax or `score_capture`'s two-candidate interpretation.

## Input and runtime flags for complete_batch

The imported primitive needs a protocol containing:

```text
payload.batch_size = 8
payload.sequence_length = 224
payload.max_new_tokens = 64
payload.eos = [128001,128008,128009]
scientific_hash = NEW cue science hash
provenance.cache = exact local cached model path
```

Each row needs `id`, `ids` (full prompt tokens) and `stem`; all scientific metadata stay in the new manifest. Preverify nonempty IDs, token validity and `length == len(ids)`; require `length + 64 <= 224` for **every** frozen main row and every calibration candidate considered by selection. Fixed224 is a contract, not a size to retune after outcomes.

For each actual run make a shallow runtime copy, adding only:

- `_calibration=True` **only when executing the 64 designated new calibration rows**; False for all512 main rows.
- `_stop={'requested':False}` with SIGTERM/SIGINT handlers.
- `_deadline=actual_allocation_end-shutdown_buffer_seconds`, subtracting the shutdown buffer exactly once.
- `_checkpoint_batch=callback(partial,stats)` to persist active batch IDs/statuses and runtime counters.

At first step, every row gets repeat and empty-hook controls. When `_calibration` is True it additionally gets full-component-baseline and self-replacement controls (`:225-239`), excluding READOUT_KEY from replacement and letting the actual final computation produce logits. Main must remain main mode with just repeat/empty. Do not abuse calibration mode to bypass main release, execute new main rows or relabel them calibration.

Greedy generation includes EOS and preserves logical readout positions; finished slots remain in physical B8L224. The full cap is64 generated tokens, with no extension or retry. The primitive returns each row's generated IDs, logical_readouts, finish, controls, continuation/raw continuation, full text/raw text, physical slot, status and runtime counters. It raises on failed numerics, nonfinite logits, overflow or deadline. Partial tokens remain available via callback; the outer runner must preserve them plus explicit attempted/error/unattempted states.

## Why the higher-level native pipeline cannot be reused

- `verify_protocol(protocol:dict)->None` at `:162-176` requires **3072 main /64cal/34fixtures**, fixed old source hashes and old overlap/pool contracts. `_run` invokes it at `:505` even if reached directly; `run_calibration` and `run_main` call `_run` at `:495-500`.
- `_release` at `:340` reads a root-native-controls release constant; `run_main` calls it. It is irrelevant to this new probe and must not be bypassed through monkeypatches or fake protocol labels.
- `build_shard_plan` at `:312-331` hardcodes384 physical batches, exact3600s buffers, old cancelled job23101635 and native registry. `merge_shards` at `:454-476` insists on3072 rows. None belongs in the cue probe.
- `runtime_binding` at `:302-303` and `_calibration_matches` at `:305-309` call old `source_hashes`; the latter compares old runtime bindings. A new small binding function is required to include new source files and new science. Do not override old functions.
- `export_blind_views`, `join_annotations`, `analyze_panel` transitively invoke old verifier or3072/gate contracts at `:612-655`. Reuse the view schema/coverage ideas, not the whole wrappers or old gate code. New analysis must answer cue sensitivity, never old behavior_go.

## Thin outer adapter and provenance

A small run function can adapt the non-sharding parts of `:502-599` without copying the entire native pipeline:

1. Verify the **new** manifest, all source/cache/software hashes, operations and root-supplied full40hex new source commit before model load. Identify actual GPU; construct new binding. For main require an independently persisted **new** calibration receipt with mode=calibration, status=completed,64 completed rows,64 controls_rows, complete expected controls for every ID, numerical_pass=True and exact binding equality (science, provenance, all sources, model/tokenizer, software, B/L and full hardware identity). Verify those claims against actual calibration row artifacts/hashes; a standalone permissive summary is insufficient.
2. Before asking for main allocation, emit the full-cap forecast from that calibration. At main startup recompute it and compare with `min(reserved_seconds,actual_end-now)` before loading the model. Keep main blocked without complete matching calibration. Do not transfer prior native-cal receipts or merely match GPU class.
3. Create a fresh output; write new protocol+operations; initialize all scheduled rows as unattempted/error_missing. Install handlers and atomic panel/active checkpoints.
4. Set offline flags; load once through hooks in BF16 CUDA SDPA; `hf.eval()`, temporarily set `use_cache=False`. Verify CUDA device, BF16 dtype, actual SDPA and eval mode (`native :556-559`). Record startup/premodel timings.
5. Iterate `range(0,len(rows),8)`, mark attempted, call unchanged complete_batch and update cumulative maximum-forward/control/startup/IO/runtime counts. Preserve fixed slots and IDs. On exceptions retain partial statuses/IDs, mark failed or partial_deadline, write receipt and re-raise. In finally restore use_cache and signal handlers. No denominator deletion or automatic retry.
6. Assert exact scheduled coverage and required control **names/counts**, finite/error/greedy checks before marking numerical completion. Receipt modes are distinct calibration/main; all new calibration IDs remain excluded from main and scientific labels.

New freeze schema can retain familiar `{payload,scientific_hash,provenance,provenance_hash,fixtures,main,calibration}` shape without claiming native-controls-v1 identity. Payload binds exact scientific spec/rubric, deterministic fixture ranks and selection rule, all new row IDs, factors, complete prompt bytes/token IDs/lengths/truth/favored names, B8L224/cap/EOS/numerical recipes and parent-protocol file SHA256/science hash. Parent is read-only evidence; new hash changes because new rows/renderer/endpoint differ. New rows should have a cue-specific namespace and never collide with old IDs.

Provenance binds new root commit, exact cached model/tokenizer/config hashes and software package identities; union `n.source_hashes()` with hashes of the three new files. The old helper already includes native source/wrapper/test, routing-pilot and transitive component_analysis/models/dataset modules; leaving that conservative base set is acceptable. It does **not** include new source automatically. Bind parent artifact's actual file hash as well as scientific hash, and keep a separate new payload hash; do not edit the old protocol provenance to make it appear current.

Freeze provisional CPU artifact first; root commits only the three additive files and supplies actual commit for a new committed freeze. Compare full payload equality provisional→final; only provenance commit should change. Freeze using the exact intended runtime environment via actual new wrapper CPU dry-run; base login and mgnp package identities differ. A valid-looking commit string alone is not source equality: verify listed file hashes, with root responsible for commit membership verification.

## Timing and actual wrapper guards

`n.forecast_main` has a **generic row-count component**: for512 rows, `total=ceil(512/8)=64`, generation64×64=4096 forwards and first-step controls64×2=128, totaling4224 full-cap main forwards before buffers. Calibration's eight physical batches may require up to8×(64+4)=544 forwards because its four first-step controls are additional to the natural forward. Both main and calibration still stop rows naturally at EOS; forecasting must assume the cap, not observed mean length.

The helper's fixed `io_scale=48` at `:284` is old3072/64 panel growth. It is a conservative overbound for new512/64 growth8 **if the new checkpoint schema/writes are no more expensive than the measured calibration scaling bound**. Simplest safe reuse is retain48 and label the forecast conservative; do not pretend it is an exact512 scaling estimate. If a cue-specific forecast replaces it, bind explicit serialization/checkpoint counts and document why growth8 or a byte-size ratio bounds the actual larger panel; do not simply drop the IO term. Include startup, premodel/source/cache verification, measured IO and operator startup/IO/shutdown buffers; record an explicit safety margin. Recheck available wall time after model startup before generation. If source/cache validation consumes unexpectedly long time, abort rather than letting forecast validity expire unnoticed.

Old wrapper `scripts/jobs/run_sdr_native_controls.sh:4-25` captures actual Slurm allocation start/end from `SLURM_JOB_START_TIME/END_TIME`, falling back to `scontrol show job`+date conversion. Preserve that behavior with a **cue-specific environment prefix** and feed epochs to generic bind_allocation_operations. `:27-38` guards correct worktree, initializes mgnp safely under nounset, exports offline and one-thread BLAS flags, then execs the script. The new wrapper must exec `scripts/sdr_cue_probe.py`, not the old native CLI. Allow explicit cue Python override for CPU dry-runs; actual GPU mode independently checks exact frozen software, SLURM_JOB_ID and one CUDA GPU. Commands require explicit approved worktree `--chdir` and `--time` at submission; no submission code is needed inside the science script. CPU dry-run must not import/load a real model, claim a GPU receipt or mark main released while calibration/hardware checks remain pending.

## Meaningful tests for the new seams

- All512 rows/64cal unique/disjoint; complete crossed-factor support; original-other and named-other mapping yields the same actual truth/favored identity. Explicit question order independent of record order, fixed lexical quoted answer-example order, `.THE`, exact old stems/N-A clause, and no unintended source-system differences.
- Tampered prompt/payload/source/parent/cache bindings fail; maximum length+64 exceeding224 fails without truncation. Freeze rebind changes provenance only.
- Main without64-row matching new calibration is blocked; wrong receipt mode, missing repeat/empty/full-baseline/self controls, incomplete rows, mismatched actual hardware/software/source/B/L or old native hash fails before model load. This tests scientific release boundaries, not dictionary mirroring.
- With fake hooks/model/clock and a stubbed imported complete_batch, demonstrate dispatch sends actual64cal rows with `_calibration=True`, then actual512 main rows with `_calibration=False`; main uses64 fixed batches, exact IDs and no cal IDs. No old verifier or registry is called.
- Full-cap forecast needs4224 main forwards even for calibration outputs that stopped immediately; insufficient allocation/deadline blocks before loading. Old helper IO48 remains counted if reused. Timing guard still rejects after elapsed verification/startup time.
- Inject mid-batch numerical exception and deadline/signal: partial tokens and attempted/unattempted IDs persist, no success receipt, no retry, final status coverage complete; restore model cache flag/handlers. Confirm fresh-output guard prevents overwriting evidence.
- One adapter integration test with fake logits/capture checks actual imported complete_batch path retains B8L224 and correct main/calibration control sets. Existing old tests already cover mixed EOS/fixed-slot generation (`tests/test_sdr_native_controls.py:118` onward); do not duplicate all their implementation-level cases.
- Actual new wrapper CPU dry-runs under intended environment for freeze/cal/main, with missing calibration explicitly blocked; shell syntax check. Existing scripts/tests remain untouched. Real numerical/calibration claims require later authorized GPU receipts, never mocked tests.
