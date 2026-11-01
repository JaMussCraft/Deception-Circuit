# V5 generation-only checkpoint implementation

2026-10-24. Authorized narrower implementation of report158 on reviewed base9eb2a6a, in `Deception-Circuit/.claude/worktrees/selective-transfer-v5`. No git, submissions, GPU/pretrained-model inference, API calls, budget operations, or model/l0/config/native-helper edits by this worker. Root alone commits and launches. Independent Astra review is in progress.

## Behavior

Explicit opt-in requires both `--benchmark-generation-checkpoint-dir PATH` and positive `--benchmark-stop-after-generation-batches N`, together with frozen masks, historical fixed cohort and interchange. Defaults preserve callers. One lifetime `flock` holds an inode that is never unlinked; process death releases it. Each original stable full-row bucket commits raw generated integer tokens, including EOS and post-EOS pads, by unique temporary JSON, flush/fsync, atomic replace and directory fsync. The NEW-batch count spans all phases. The Nth durable save raises `GenerationSegmentComplete`; public entry exits75 with a segment receipt explicitly marking evaluation incomplete/no headline. In-flight unsaved batches remain unrecoverable.

Recipient-intact, native donor, and each masked state have distinct namespaces. Full state reuses recipient tokens. Cold replay reconstructs the existing ordered missing-donor list, references, pairing and corrupt stream; pending rows are never filtered/rebucketed. No state/coherence result cache, KV persistence, pickle, lock recovery service, authorization framework, scientific protocol change or native token-limit change. Existing judge cache remains in use; coherence/judging may be revisited.

Identity binds source BYTES (generation/mask/donor/preprocessing/model/compatibility/l0/config/train/tasks), frozen cohort/mask bytes, immutable model revision/config, exact tokenizer backend/template/special-token bindings, H200 model/capability, dtype, torch/transformers/CUDA/cuDNN/attention and SDP/TF32/determinism settings, stable opt-in seed, datasets, actual effective masks, donor assignments/references, and exact clean/corrupt/attention tensor shape/dtype/bytes. The plan binds resolved cap, EOS/pad IDs, cache policy, greedy decoding, batch size, stable row order and trims. Source HEAD is external provenance, not cache identity. Per-segment PID/host/job/GPU UUID are provenance only. A root run manifest rejects changed source/runtime/artifacts even when all tokens are cached. Every committed batch is validated before any missing batch in that phase generates; corrupt/foreign/checksum-invalid/out-of-range records fail closed. Checkpoint errors and deliberate segment stop explicitly bypass stock dataset best-effort exception handling.

The live store resides on Session, preserving CLI JSON serialization. Opt-in main sets torch seed0 before session/model construction; otherwise a fresh Python process's random initial seed would reject every cold resume. Greedy evaluation and frozen masks have no stochastic sampling.

## Owned files / SHA256

Worktree paths relative to `Deception-Circuit/.claude/worktrees/selective-transfer-v5`:

| File | SHA256 |
|---|---|
| `evaluation/gen_engine.py` | `65f11469ae782dc1a11f08e7a67dd2d6186470f829826afd22e2b76083343ee3` |
| `evaluation/generation_checkpoint.py` (new) | `eb28dc47c4125afa3e067be50f3ab8f219865b89d5295e4df03a747625d4e2fb` |
| `evaluation/benchmark_eval.py` | `502630061bf3f480fe1a4b0d306c7c63fa6ab6f56ed02082dc2a14631925ad2b` |
| `evaluate_circuit.py` | `79eba2a2aa8e6b5745feb7b30e8d47c06845d686651332744326de9d6889e324` |
| `tests/test_generation_checkpoint.py` (new) | `53851eed7a97751a7f88b63987be080281899f15e66f2fb252dce643ecb361f7` |
| `tests/test_screen_cache.py` (flag classification only) | `ac2aaeea59066951cc021fc586e1af9938f04b78f14a1d217b63c8c94b561eae` |

External files relative to Alignment:

| File | SHA256 |
|---|---|
| `.scratch/selective-deception/analysis/transfer_v5_checkpoint_smoke.py` | `8eb9c848f4f2b0db17b7aa04b9c2af77d26c29296f65ebfecbf931155ea27497` |
| `.scratch/selective-deception/analysis/transfer_v5_checkpoint_smoke.sbatch` | `fa524bdfdeea24d8cbf1fdd0c7d2349086d7aefa5cd0fba0219503ee48ea87f3` |

## Verification

Test-first missing-module failures observed in both supported environments. Independent review found real dataset-loop exception swallowing; a regression test reproduced it before the explicit rethrow fix. Review also caught/stabilized Session serialization and fresh-process seed issues.

CPU-only suite: `tests/test_generation_checkpoint.py tests/test_gen_engine.py tests/test_screen_cache.py tests/test_fixed_benchmark_cohort.py tests/test_benchmark_eval.py`, with `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`, OPENAI/OPENROUTER/ANTHROPIC keys removed.

- mgnp `/u/swong2/.conda/envs/mgnp/bin/python`: **216 passed in54.03s**, final log `/tmp/v5-checkpoint-mgnp-final2.log`.
- Base `/sw/external/python/anaconda3/bin/python`: **216 passed in67.53s**, final log `/tmp/v5-checkpoint-base-final2.log` (3 existing environment warnings).
- Syntax compilation passed for owned production Python and smoke script. `bash -n` passed. Actual `.sbatch --dry-run` executed on CPU successfully, `/tmp/v5-checkpoint-smoke-wrapper-dry-final.json`; it performs no model load/inference.

New coverage: raw EOS/pad integer equality and original ordering across ragged prompts/tied lengths/short final batch; genuine separate-process synthetic resume; separate deterministic tiny actual-model replay (fresh model instance, same Python process); no generation on cache hits; actual execution-identity drift with mocked hardware (source/model/tokenizer/runtime/dtype/effective masks); exact donor/reference/corrupt reconstruction and full-token reuse; tensor/cap/cache/EOS/batch drift; committed JSON/checksum/token/shape/row/foreign-record corruption before any new batch; ignored partial temporary writes; cross-process flock conflict, inode retention and process-death release; failed batch commit abort; real BenchmarkEvaluation dataset-loop stop/error propagation; public CLI75 incomplete receipt and JSON-safe CLI/default behavior.

## Root gates and technical proof

Before production: complete independent Astra review, root commit/freeze exact sources, root receipt/reservation and bounded H200 proof. Root ran prior-source proof001 successfully (172s; exact whole/resumed evidence,8/2new batches). Root then required production opt-in deterministic=True and both TF32=False to match proof settings. Those three setters and opt-in-versus-stock tests are now added; new source freeze and bounded proof002 remain required. No efficacy result exists. The old stopped SB batch saved no raw tokens and cannot be recovered.

The prepared proof wrapper has a15-minute/one-H200 request and no submission logic. Root supplies a NEW directory as its sole positional argument after externally authorizing/reserving it. It executes three explicitly planned fresh Python processes: uninterrupted8 original batches, split6 batches (all3 recipient +all2 donor +first masked batch), and cold resume2 batches. Eight generated tokens on fixed synthetic ragged/tied inputs are for technical proof only. Total16 NEW batches/two passes/three model loads; the actual frozen new-allW23 mask is applied and round-trip checked. Final comparison requires exact raw recipient/donor/masked tokens, original row order, restored donor refs/assignments, and reconstructed corrupt tensor, plus expected new-batch counts8/2. Its outputs do not grade deception or change the scientific native1024 cap. Exit75 is expected exactly once; unexpected status aborts and no automatic retry occurs. Production segmentation still needs separate root receipts/reservations and a duration sufficient for one whole native1024 batch plus startup/save margin.


## Post-review runtime alignment

Root approved only three additional setters beside opt-in seed0 in `evaluate_circuit.py`: deterministic algorithms enabled and matmul/cuDNN TF32 disabled. Non-opt-in execution leaves existing settings untouched. A two-case public-main regression first observed one failing opt-in/one passing stock case, then passed after the change. mgnp expanded218-case suite passed44.10s (`/tmp/v5-runtime-aligned-mgnp.log`); base expanded218-case suite passed71.66s (`/tmp/v5-runtime-aligned-base.log`), with three existing environment warnings. The external actual segment shell and child environment both set `CUBLAS_WORKSPACE_CONFIG=:4096:8`. New provisional segment receipt gates immutable proof002; proof001 is preserved. Root alone commits, reproofs and finalizes execution receipts; see report163.
