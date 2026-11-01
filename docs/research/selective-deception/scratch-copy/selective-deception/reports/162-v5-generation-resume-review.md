# V5 generation-only resume independent review

2026-10-24. **PASS for root's bounded H200 technical calibration; no outstanding implementation blocker.** Actual cold-process H200 equivalence remains a required gate before long production segments. No GPU proof or scientific efficacy result is claimed here.

Reviewed the implementation against base `9eb2a6a5c8481d99053b78ec2cdc43a3c606cd3c`, report158 with the accepted narrowing, and final report159. Scope is raw generation-batch persistence only: no state/coherence cache, KV serialization, pickle, stale-lock framework, or changed scientific cohort/state/token policy. Review performed no git operation, job, model inference, API call, or budget operation; only this report is authored by the reviewer.

## Findings resolved before this verdict

1. The original broad dataset exception handler swallowed `GenerationSegmentComplete`, preventing public exit75 and potentially continuing another dataset beyond the global new-batch limit. The final code explicitly rethrows both segment completion and checkpoint errors before stock best-effort handling. Regression coverage invokes the actual `BenchmarkEvaluation.run` loop and asserts the second dataset is never visited.
2. An unseeded `torch.initial_seed()` made cold CLI identity unstable. Opt-in entry now fixes torch seed0 before session/model construction; ordinary execution is unchanged.
3. The worker found the live store on CLI would break suite JSON serialization. It now lives on Session; serializable public CLI fields remain intact.
4. Checkpoint commit/identity/phase-creation errors now fail through the dedicated checkpoint exception. Stock dataset error policy remains unchanged. Lock conflicts arise outside that loop and abort directly.

## Correctness reviewed

Opt-in requires both public flags, a positive global NEW-batch limit, fixed cohort, frozen masks and interchange; public flag classification is updated. Benchmark-native token priority remains intact, including sandbagging1024. The engine retains its original stable descending sort, equal-length order, original bucket composition, trim widths, padding and inverse permutation. It persists raw generated integer IDs including first EOS and post-EOS pads; it never re-buckets remaining rows or reconstructs through text.

Run/phase/plan bindings cover source bytes, immutable model revision/config, exact tokenizer serialization/template, H200/software/dtype/backend/seed identity, artifact bytes, effective masks, ordered donor dependencies, exact clean/corrupt/attention tensors and resolved decoding policy. Bindings and committed records are validated even when every batch is cached. Missing batches generate; corrupt/foreign/checksum-invalid/shape-invalid/token-invalid records reject before new generation in that phase. Atomic save uses unique temporary JSON, file fsync, replace and directory fsync. The lifetime exclusive flock retains its inode and releases on process death. The counter spans phases and raises only after the Nth durable saved batch.

Recipient and donor restoration uses the existing missing-donor and reference construction, preserves assignments and actual corrupt streams, and enables future masked conditioning from restored tokens. Full state reuses recipient-intact tokens. Config judging and coherence remain subject to the existing judge cache and budget guard; persistence creates no payment/rejudge bypass. Incomplete segments carry false evaluation-complete/headline flags and do not produce a completed block headline. Repeated coherence/judge work and loss of an in-flight unsaved batch are accepted limitations of this narrowed implementation.

## Evidence inspected

Read final test logs directly: `/tmp/v5-checkpoint-mgnp-final2.log` reports216 passed in54.03s; `/tmp/v5-checkpoint-base-final2.log` reports216 passed in67.53s. This is the focused five-file suite listed in report159, not a claim about the full repository suite. Coverage includes separate-process synthetic resume, deterministic real tiny-model replay in fresh model instances, full/donor/corrupt restoration, no-generation cache hits, actual identity drift with mocked hardware, failed commits, process-death lock release, and real dataset-loop propagation. Read the actual wrapper CPU dry-run output `/tmp/v5-checkpoint-smoke-wrapper-dry-final.json`; its split boundary is6. Worker reports shell syntax check passed.

Read root's `transfer-v5/resume-source-preservation.json`: all10 baseline model/l0/config/train/context files equal9eb2a6a, and all16 frozen V2 bindings (including native helper) match. Independently recomputed all8 final report159 file hashes below; every hash matched.

## Prepared H200 proof and remaining gate

Reviewed both smoke source and actual sbatch wrapper. Three fresh Python processes run uninterrupted8 batches, split6 batches (all3 intact +all2 donors +first masked batch), then cold resume2 batches. Synthetic ragged/tied prompts use8 generated tokens solely for technical equivalence. The actual frozen23-head removal is applied and round-trip checked; native interchange is the model's hook-free dual-stream path. Exact final comparison covers raw intact/donor/masked IDs, row order, references/partner assignments, corrupt tensor, effective mask and new-batch counts. The cold resume therefore restores donors and one masked batch before generating subsequent masked batches. No API or automatic retry is present; the wrapper checks the first segment's exit75.

Root must freeze/commit sources and bind a new receipt/reservation, run this bounded proof, inspect its result, then prepare production segments with enough time for a complete native1024 batch plus startup/save margin. The proof is not yet executed. Historical stopped SB RAM tokens remain unrecoverable. This verdict permits the technical proof stage, not an unsupported claim that H200 resume already passed.

## Reviewed hashes

| File | SHA256 |
|---|---|
| `evaluation/gen_engine.py` | `65f11469ae782dc1a11f08e7a67dd2d6186470f829826afd22e2b76083343ee3` |
| `evaluation/generation_checkpoint.py` | `eb28dc47c4125afa3e067be50f3ab8f219865b89d5295e4df03a747625d4e2fb` |
| `evaluation/benchmark_eval.py` | `502630061bf3f480fe1a4b0d306c7c63fa6ab6f56ed02082dc2a14631925ad2b` |
| `evaluate_circuit.py` | `3c5c8fbadc4b9db17deadc5cd0016585689ef74cd36bbb89b2234b50aa7a84f1` |
| `tests/test_generation_checkpoint.py` | `4da4471523fbd38f78697da0bead5bff60a58a06b452596a004e3db6f8d91090` |
| `tests/test_screen_cache.py` | `ac2aaeea59066951cc021fc586e1af9938f04b78f14a1d217b63c8c94b561eae` |
| `.scratch/selective-deception/analysis/transfer_v5_checkpoint_smoke.py` | `8eb9c848f4f2b0db17b7aa04b9c2af77d26c29296f65ebfecbf931155ea27497` |
| `.scratch/selective-deception/analysis/transfer_v5_checkpoint_smoke.sbatch` | `fa524bdfdeea24d8cbf1fdd0c7d2349086d7aefa5cd0fba0219503ee48ea87f3` |

## Follow-up review: runtime alignment and thin production launcher

2026-10-24. **PASS for the narrow runtime correction and report163 launcher; proof002 remains the production gate.** Prior proof001/job23160883 passed172s: root audit reports exact whole/resumed raw evidence,8/2new batches and52unchanged source bindings. That proof used deterministic algorithms and disabled TF32, while the previous public opt-in CLI did not explicitly select those settings. Identity binding prevents incompatible cache mixing but cannot substitute for evidence under the intended production runtime. Aligning the public runtime and repeating the bounded proof is the appropriate narrow correction.

Reviewed the three added public opt-in setters: deterministic algorithms=True, matmul TF32=False, cuDNN TF32=False, next to existing seed0. The ordinary CLI path remains untouched. The segment shell and child environment set CUBLAS_WORKSPACE_CONFIG=:4096:8 before execution. Read final logs directly:218 focused tests pass in mgnp44.10s and base71.66s; six segment wrapper tests pass in both environments. The new parameterized public-main regression checks opt-in settings and unchanged stock behavior. Read actual shell-to-wrapper-to-public-CLI CPU dry-run output; native1024 and the fixed50recipient/50donor/200intervention scope remain intact.

Reviewed the thin launcher and unchanged inherited helper. It binds source/artifact/argv bytes, requires root-reviewed receipt and passing proof002 SHA, preserves exact frozen argv except common output/checkpoint and explicit batch limit, cleans credentials, and consumes a content-SHA-keyed one-use receipt guard (renaming a receipt cannot bypass it). It passes75 through as incomplete, requires a freshly written complete50-row/five-state/native1024 block on0, kills the child process group on timeout and has no retry/submission loop. Mutable judge cache/ledger retain existing prefix/budget validation. No new blocker found. Source commit is root-recorded provenance; exact bytes are enforced.

The inspected template remains reviewed=false with null proof002 hash and old commit provenance explicitly pending root finalization. It is not execution authorization. Root must record the new commit, bind the completed proof002, finalize the new receipt/reservation, and repeat the actual-shell dry-run against that final receipt. The historical hash table above remains the prior reviewed version; the following verified current hashes supersede the two changed core entries and identify this launcher review.

| File | SHA256 |
|---|---|
| `run-sandbagging-segment.py` | `4f9d8cd2dbf7b0f9418772a28d2cab595bc05245177e07e31826e061c339fd1a` |
| `launch-sandbagging-segment.sbatch` | `3af6ce2aebb33777b5e2015e700192a37c09b72b7b002259599d67748c69e92a` |
| `sandbagging-segment-001.argv.json` | `cdff1e8ddc3c801c6b7655fef1a9c9920b2e8ab180ff30de7d739fedd3b93999` |
| `sandbagging-segment-001.receipt.template.json` | `dddd02b631e16a9f83d101448ef4c76f2505fcbb71181435ecfad381651b66cb` |
| `test_sandbagging_segment.py` | `e43b698e49dc19abf48fd38ec250b8913b739a2faf830115040372585f228a1c` |
| `core evaluate_circuit.py` | `79eba2a2aa8e6b5745feb7b30e8d47c06845d686651332744326de9d6889e324` |
| `core tests/test_generation_checkpoint.py` | `53851eed7a97751a7f88b63987be080281899f15e66f2fb252dce643ecb361f7` |
