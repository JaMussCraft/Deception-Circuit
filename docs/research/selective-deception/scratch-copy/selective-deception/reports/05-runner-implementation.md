# Task2 bounded diagnostic runner — implementation handoff

Implemented in the selective-deception worktree, based on reviewed Task1 `a842b7a8a3fc10bbd13e25e2b7c35db8950d983e`. Root owns review, git writes, production freeze and all Slurm submissions. No notebooks,8B model loads, GPU execution, downloads, external API calls, jobs, or git mutations were performed. Default shell sandbox failed initialization (`bwrap` temporary-directory read-only error); narrowly scoped reviewed escalation was used for local reads/owned edits/CPU tests. No approval rejection occurred.

## Files and scope

- `evaluate_selective_deception.py`:263 lines, cache-only prepare/dry-run, run, summary/export CLI; creates the existing Session/EvalContext around one original node model and shared reference.
- `evaluation/selective_runner.py`:376 lines, frozen work selection, exact cost plan, donor-local intact diagnostics, canonical43/33/random43 mask resolution, existing evaluator/gen_engine integration, row persistence, summary and blinded export.
- `tests/test_selective_runner.py`:22 focused tests with actual random tiny CPU Llama forwards, cached decoding, Session/EvalContext integration and persistence/selection checks.
- `scripts/selective_deception.sbatch`:1GPU,64GB,1CPU,mgnp,15min default, no requeue/array/retry; offline flags and child-process API env unsets.
- **Explicitly root-approved surgical addition** `evaluation/metrics.py`:only `collect_per_example` adds target/distractor logits, full-vocabulary probabilities, summed mass and logit difference from already-computed logits. No extra forward, evaluator copy, default aggregate changes, or new hooks.

## CLI and APIs

```
--manifest PATH --output-dir PATH
[--prepare] [--dry-run] [--run] [--subset all|smoke]
[--summarize] [--export-blind DIRECTORY]
[--data-dir CANONICAL_SDR_DIR] [--model-path LOCAL_SNAPSHOT_OR_CANONICAL_CACHED_ID]
[--circuit D=PATH --circuit H=PATH --circuit F=PATH --circuit m=PATH]
[--reference shared] [--device cuda]
```

`--prepare` refuses overwrite; it freezes the full64-cluster manifest. `--subset smoke` selects the existing manifest's first2cluster IDs, all their original/reversed score and primary/alternative generation conditions plus exact donor-reference closure. It does not resample, modify manifest identity, change decoding, or alter a run fingerprint. Main can fill missing rows in that directory. Summary/export uses stored run provenance and requires the exact manifest, without loading tokenizer or model.

Public helpers: `select_work`, `donor_diagnostics`, `work_plan`, `ResultStore`, `safe_knockout`, `resolve_masks`, `aligned_inputs`, `FrozenTask`, `score_row`, `reference_stream`, `generate_row`, `execute`, `summarize`, `export_blind`. Full manifest validation happens through Task1 load/build once per CLI invocation; no per-row reconstruction/validation. No Task1 edits.

## Scientific behavior

Canonical absolute D/H/F/m bindings come from the artifact audit. Resolver composes `(D&H)-m` and `(D-F)-m` at leaf granularity. CPU preflight verified core43heads/5,504attention neurons/10attention blocks, comparator33heads/4,224neurons/11blocks, random43heads/5,504neurons/10blocks. Every intervention has zeroMLP membership; complements retain allMLPs. Existing seed0/index0 sampler preserves the core's per-layer counts and is independent of results.

Core/D−F/random selectivity rows retain Task1's identical fixed nonself derangedH donor assignments. Paired self-H remains `sanity_only`, never benign utility evidence. Summary explicitly labels selectivity conditional on nonself mismatched-content interchange. Donor-local intended answer and observed donor argmax relation to each recipient remain distinct. No outcome-driven filtering occurs.

Scores use `evaluate_pred_position`, exact frozen donor token IDs, shared-mask alignment checks and unpadded rows. Outputs include D/H logits/full-vocabulary probabilities, D−H margin, pairwise preference, argmax D/H/other plus actual token/text. A deduplicated intact donor-score table covers all four policy×designation states, reversed donors and generation-donor first-token diagnostics; labels are taken from each donor's own source cluster. Targets link to the exact donor diagnostic and store observed argmax agreement with recipient D/H/other labels. First-token diagnostics on free-response prompts are routing measurements, not semantic generation validity judgments.

Every declared donor reference is generated intact before target interventions, through existing `gen_engine.generate`. Existing `pack_reference` extends only continuation tokens (including first EOS) when short; no arbitrary continuation padding is invented. Saved flags disclose tiling/truncation, earlyEOS, empty continuation, prompt alignment/padding, terminationEOS/cap, visible-empty response, lengths and repetition fraction. Saved text/tokenIDs exclude EOS. Cap-hit has no inherent deception/failure label. Primary/alternative generation stay separate from original scores.

No-op score summaries use explicit absolute0.02 bf16 tolerance on D/H logits; tiny fp32 tests use1e-6. Generation identities require exact token-ID equality. Tiny actual self-donor score and generation match intact; nontrivial donor score changes actual logits. Summary exposes no-op failures for root's gate; it never replaces missing generations with score outcomes.

Blinded `responses.jsonl` contains shuffled anonymousID, recipient prompt, groundtruth scenario/answer words, response text and quality only. A separate `private_mapping.jsonl` retains row/condition/donor identity. Both files mode0600. No semantic judge is instantiated/called; annotation remains deferred. Summary always marks generated-deception endpoint pending blinded semantic annotation. Recipient prompt necessarily includes its factual/policy instructions; no extra condition/mask/donor identity is exported.

## Persistence and fingerprints

`run.json` stores the complete exact manifest, source revision + dirty diff SHA256 + code-file hashes, original local snapshot revision/config/tokenizer identities, package/Python versions, BF16/shared reference, exact masks+mask hashes+operand configurations, tokenizer padding/EOS settings and runtime GPU type/capability/CUDA. Full manifest hash covers exact recipient/donor tokenization, semantic label IDs, decoding and all reference assignments. Immutable HF cache revision/blob paths, file sizes and nanosecond mtimes identify weight shards; this avoids rereading16GB of weights just for a CPU dry-run. Small tokenizer/config files have SHA256 hashes. Different source, model, tokenizer, masks, hardware/runtime, donor, token cap or manifest cannot share a run directory.

Cache lookup uses pure `try_to_load_from_cache` rather than repository-wide snapshot completion: the installed new Hub version otherwise rejects an adequate model cache merely because README/license files are absent. All necessary configured weight shards must exist, and tokenizer loading explicitly sets local_files_only. Existing ModelAdapter receives the absolute cached snapshot directory; offline environment is set before transformer imports. Original shared weights are loaded once; no redundant8B reference model.

CLI locks each execution/summary/export directory with a nonblocking process lock. ResultStore rejects changed fingerprint/content and duplicate/conflicting complete rows. Complete JSONL records contain frozen input row, manifest-linked row hash, run fingerprint, payload and result checksum; each record is appended and fsynced before moving on. Interrupted unterminated tail is truncated; corrupt newline-terminated records fail. All completed rows survive interruption; `--summarize` reports exact missing IDs. Full completion requires every target row, unique reference and deduplicated donor diagnostic. Smoke cannot mark full completion. Summaries/exports do not truncate a live writer's partial line because they share its lock.

## Actual canonical CPU preflight

Executed only in mgnp with local cached original Llama tokenizer,1000canonical SDR test records,64frozen clusters, no weights/GPU. `verify_tokenization` checks all frozen prompts/label IDs, then constructs the existing `DeceptionDatasetLlama` for all64 original selected D records: **no dropped rows; exact unpadded input-prefix IDs; exact prefix_length−1 readout; exact leading-space target/distractor IDs**. The cached tokenizer boundary agrees with the existing scoring path. Generation transformations deliberately use a different free-response boundary.

Diagnostic-only temporary manifest:
`/tmp/selective-runner-final-manifest.json`
Hash `fef334ad0a8e1bd3df62ae800368965172512a93ce01632384089f3a316d1712`.
Cached snapshot `/work/nvme/beto/swong2/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659`.
This is CPU evidence, **not root's production freeze**: source revision/dirty hash changes after root commits, so root must prepare a fresh production manifest after final review/commit.

| selector | target score passes | intact donor passes | total score passes | target generations | unique donor refs | total completions | worst new tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| full |1088|356|1444|320|84|404|38,784|
| first2frozen clusters |40|24|64|40|12|52|4,992|

Full expected outputs =1444scores+404completions=**1848 records**. Smoke =64scores+52completions=116records. These totals include all donor validity forwards and references. Main after successful smoke fills the missing exact full-manifest records (no repeat of valid completed rows), so combined smoke+resume still has at most38,784 completion tokens, rather than two full runs.

## Exact commands

Run from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/selective-deception`.

Executed CPU proof:
```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /u/swong2/.conda/envs/mgnp/bin/python evaluate_selective_deception.py \
 --manifest /tmp/selective-runner-final-manifest.json \
 --output-dir /tmp/selective-runner-final-preflight --prepare --dry-run
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /u/swong2/.conda/envs/mgnp/bin/python evaluate_selective_deception.py \
 --manifest /tmp/selective-runner-final-manifest.json \
 --output-dir /tmp/selective-runner-final-preflight --subset smoke --dry-run
```

After review/commit, root prepares the real freeze with the same mgnp environment that jobs use:
```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /u/swong2/.conda/envs/mgnp/bin/python evaluate_selective_deception.py \
 --data-dir /projects/beto/swong2/Alignment/Deception-Circuit/data/datasets/sdr \
 --manifest outputs/selective-sdr-stage1/manifest.json \
 --output-dir outputs/selective-sdr-stage1/run --prepare --dry-run
mkdir -p logs
sbatch --test-only --time=00:15:00 scripts/selective_deception.sbatch \
 --manifest outputs/selective-sdr-stage1/manifest.json \
 --output-dir outputs/selective-sdr-stage1/run --subset smoke --run --reference shared
```
Root only, after reserving0.25GPUh in the ledger and checking scheduler/account/partition availability:
```bash
sbatch --time=00:15:00 scripts/selective_deception.sbatch \
 --manifest outputs/selective-sdr-stage1/manifest.json \
 --output-dir outputs/selective-sdr-stage1/run --subset smoke --run --reference shared
```
After inspecting elapsed/load/decode rate, no-op flags and missing rows, root may reserve a measured main runtime; illustrative1h reservation (not submitted or guaranteed sufficient):
```bash
sbatch --time=01:00:00 scripts/selective_deception.sbatch \
 --manifest outputs/selective-sdr-stage1/manifest.json \
 --output-dir outputs/selective-sdr-stage1/run --run --reference shared
/u/swong2/.conda/envs/mgnp/bin/python evaluate_selective_deception.py \
 --manifest outputs/selective-sdr-stage1/manifest.json \
 --output-dir outputs/selective-sdr-stage1/run --summarize \
 --export-blind outputs/selective-sdr-stage1/blind
```
No scheduler command above was executed by this worker. Default15min gives a hard0.25GPUh reservation; illustrative smoke15min+main60min+recovery45min=2GPUh, drawn from the shared20GPUh/max2jobs/$0API envelope. Wrapper encodes only the15min default. There is no new budget permission. Actual8B runtime and peak GPU memory remain unmeasured. OneBF16 original8B model is roughly16GB weight storage; dual-stream KV at~213tokens is on the order of55MB for one row, excluding activations/gate overhead.64GB Slurm host memory requested; root must inspect actual MaxRSS and GPU peak after smoke. Paired conditions use one model/hardware type, and resume refuses a different recorded GPU type/capability/runtime.

## Verification and TDD evidence

Initial RED: `/tmp/selective-runner-red.log` recorded14 unavailable-module errors before runner existed. CLI RED `/tmp/selective-runner-red2.log` included missing CLI plus donor-helper integration failures; those were corrected with no Task1 change. Concrete regression RED `/tmp/selective-runner-cache-red.log` reproduced unnecessary snapshot download attempt; corrected to pure cache discovery. `/tmp/selective-runner-empty-red.log` had1failed/1passed for visible-empty text versus token-only emptiness; corrected to decoded text.strip().

Final focused commands, no full-suite repetition:
```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /u/swong2/.conda/envs/mgnp/bin/python -m pytest \
 tests/test_selective_runner.py tests/test_selective_diagnostics.py -q -p no:cacheprovider
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /sw/external/python/anaconda3/bin/python -m pytest \
 tests/test_selective_runner.py tests/test_selective_diagnostics.py -q -p no:cacheprovider
bash -n scripts/selective_deception.sbatch
```

Final **mgnp77passed in18.01s; base77passed in23.06s**. Base has3existing dependency warnings: bottleneck/pandas requirement, deprecatedTRANSFORMERS_CACHE and tensorflow/ml_dtypes deprecation. Focused tests cover original55manifest contracts plus22runner cases: donor-local labels, shared-reference context, probability/argmax distinction, real tiny score and generation no-ops/nontrivial donor, EOS/tiling/visible empty/cap semantics, per-layer random/MLP retention, left padding/alignment, dry-run no weights, cache discovery, duplicate/conflicting/incomplete persistence, writer lock, immutable smoke→full exact-once execution and blinded leakage. Shell syntax check passed. Root owns full-suite integration and independent scientific/code review.

Logs and compact CPU plans are copied beside this report. No edits beyond this report/log handoff remain planned.
