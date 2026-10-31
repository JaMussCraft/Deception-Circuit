# 06 recon: evaluation suites for the v2 coarse circuits, and portability to Bridges-2

Read-only recon, 2026-10-24. No code edited, no git beyond `remote -v` / `branch -vv`, no jobs, no evaluations.
Worktree: `Deception-Circuit/.claude/worktrees/mechanism-datasets` (HEAD bd67758). Main checkout read for the
coarse SDR wave (`outputs/llama-8b-instruct_sdr_coarse/_launch/`, `wave_status.md`) and the format-control suites.

## Part A. Evaluation suites

### A1. What exists for coarse heads-only circuits

All evaluations go through `evaluate_circuit.py` (one model load per process; any number of `--circuit NAME=RUN`,
`--expr`, `--task-from RUN` gives an expr x task grid). Default `--evals` = `sanity knockout null pressure`
(evals 1-4); `benchmarks` (EVAL 5) is opt-in and out of scope. Standard flags everywhere: `--ablation interchange
--n-random 20 [--knockout-null-count 20]`, eval batch 32, 1,000 test items.

Coarse caveat that shapes every design: a heads-only run is saved coarse (`active_nodes.coarse.json`) and expanded by
`expand_coarse_masks.py`; the expanded mask contains every MLP unit (no `mlp_blocks` gate). So the atomic run's own
eval 2 knocks out all 32 MLPs ("full KO", useless). The informative knockout is the algebra cell
`X - m` at `--compose-granularity leaf`, with `m` = all MLPs, no heads. Sufficiency of a composed head set is
`(EXPR) | m`. Head-granularity composition is wrong here (it ORs all 589,824 MLP units back in).

GPU times are sacct elapsed for real past jobs (1 GPU, includes the ~3-4 min model load). A40 unless stated.

| # | evaluation | measures | how it is run (launcher) | inputs | A40 min/cell | A100 / H200 min/cell |
|---|---|---|---|---|---|---|
| 1 | sanity | saved mask reproduces in-run `node_eval` (acc/EM/LD/KL, tolerance 0.002); mask round-trip; generic-vs-task cross-check | `--evals sanity` (in every atomic job) | run dir: `active_nodes.json` (expanded), `config.json`, `results.json` | part of the suff cell | |
| 2a | knockout, full (expanded mask) | necessity + wikitext collateral + variant rows + 3 generations; for coarse removes all MLPs | default evals via SDR-wave `postprocess.sh` | run dir | evals 1-4 job: 59-60 (22308104/105) | A100x4 30 (22881282) |
| 2b | heads-only knockout (`headsko`) | necessity of the heads only, task-side KO null (20 random head sets, pct<=5 & z<=-2 on acc/LD/KL/EM), wikitext KL/token + ppl ratio vs random, flips to honest | `submit_headsko.sh` (`c - m`, `--evals knockout --n-random 20`); fc suite `X_hko` | run dir + `m` operand | 29-30 (22316469/474; fc 22895982/985) | A100 15 (22879998, 22881288) |
| 3 | random-circuit null (sufficiency) | circuit-alone vs 20 size-matched random circuits | `--evals null` | run dir | in suff cell | |
| 4 | pressure variants | circuit under `no_pressure` / `honest_instruction` prompts, labels unchanged (acc should FALL, LD go negative) | `--evals pressure` | run dir; v2 records carry `pressure`, `honest_instruction_*_prompt` | in suff cell | |
| - | sufficiency cell (1+3+4) | the fc-suite atomic cell | fc `X__<dataset>`: `--evals sanity null pressure` | run dir | 28.6-33.4 (fc 22895970-80); 10.5-12.9 on a `_nopressure` test set (variants skipped) | |
| - | size check | heads, attn blocks, fine units | `evaluation/masks.count_masks`; fc `size_check.py` | `active_nodes.coarse.json` | CPU | |
| - | pair compositions D&H, D-H, H-D | sufficiency `(E) \| m` (`--evals null pressure`) and heads-KO `(E) - m` (`--evals knockout`) on D's test set | `submit_composed.sh <slug> '<expr>'` | D, H, m | suff 28.7, KO 29.8-30.1 (22876800-27) | A100 14-15 (22876827, 22881284-88) |
| - | seed compositions (union, intersection) | same two-cell design over D, D1, D123 | `submit_composed.sh` with `EXTRA_BIND` | seed runs | as above | |
| - | seed stability / Jaccard | pairwise head Jaccard, chance-corrected, all-way core | `_launch/seed_stability.py`, fc `overlap.py` | coarse masks | CPU | |
| - | delta / XOR family | KO of `D-F`, `D&F`, `F-D`, `D-H-F`, `H-D-F`, `F-D-H` (+6 extra) on D's test set | fc `fc_launch.py` (coarse: `<label>_hko=(<expr>) - m` at leaf); `--xor A,B,C` expands the exclusives | D, H, F, m | 29.4-30.7 (fc 22895991-96) | H200-int: 3 exprs in one job 18.0 (22945674); A100-int 15.4 |
| - | honest-twin / nopressure test-set cells | every circuit on `<task>`, `<task>_honest`, `<task>_nopressure` (suff + heads-KO) | fc coarse suite (9 suff + 9 KO jobs), `--task-from` the run whose config names that condition | D, H, F (or a stand-in run dir with `deception_condition: nopressure`) | as suff/KO above; nopressure KO 15.0-15.6 | |
| - | cross-task transfer | each circuit on each other task (faithfulness 3x3; delta-leaf matrix) | `_suites/_launch_260922/` (one job per circuit x task) | the three task runs | fine circuits: ~61 per cell | |
| - | flip audit, merge, summaries | positional-default check, shard merge, verdict tables | `merge_shards.py`, `flip_audit_analysis.py`, `write_*summary.py`, fc `postprocess.sh` | suite outputs + `data/datasets` | CPU | |

GPU memory: never logged for evaluation (the only `max_memory_allocated` is in training). Evidence: every coarse
cell fit on 40 GB A100s (gpuA100x4, e.g. 22881282, 22881288, 22946214) with the default `--reference separate`
(two bf16 8B copies, ~32 GB weights, plus a 0.24 GB `[1000,128256]` bf16 reference-logit cache and batch-32
activations). So the peak is somewhere between ~33 and 40 GB. `--reference shared` drops one copy (~15 GB less, documented
as exact). Host RAM peak (sacct MaxRSS) is 14.4 GB; the sbatch's `--mem=64G` is generous.

### A2. The coarse SDR heads-only "pass" set

- **Evals 1-4** = `sanity`, `knockout`, `null`, `pressure`, run by `_launch/postprocess.sh` as
  `evaluate_circuit.py <run> --n-random 20` (interchange) after the in-run gate (acc>=0.90, EM>=0.90, KL<=0.20).
  For heads-only coarse runs eval 2 in that job is the full-expanded KO, so the wave added the **heads-only KO cell**
  (`submit_headsko.sh`, `c - m`, leaf, `--evals knockout --n-random 20`, output `<run>/evaluations_headsko/`).
  Pass reading for the pair: eval 1 `verification.ok` (max delta 3e-5), heads-KO acc 0.002 / 0.000 vs random
  0.390 / 0.585, wikitext KL/token 0.36 / 0.28. The EVAL-5 gate later adopted (KL/token < 0.28 OR 4/4 KO-null
  separation, with KL <= 0.66 and on-task necessity) is the only written numeric gate beyond the training gate.
- **D&H and XOR compositions.** Seed-42 pair at leaf: `D & H` (43 heads), `D - H` (26), `H - D` (13), each with a
  suff cell `(E) | m` (`--evals null pressure`) and a KO cell `(E) - m` (`--evals knockout`) on D's test set
  (`_composed/{dh_inter,d_only,h_only}`). Seeds: `D | D1 | D123` (77) and `D & D1 & D123` (53). The XOR family
  (`D-H-F`, `H-D-F`, `F-D-H`) and six extra deltas ran only in the format-control coarse suite, KO cells only.
  Eval 5 then ran on D, H, D&H and the seed core.

### A3. Recommended minimal set for the six v2 circuits

Head sets from `active_nodes.coarse.json` (computed now, heads in live attention blocks):

| | far | sdr | ser |
|---|---|---|---|
| D / H heads | 58 / 60 | 60 / 58 | 55 / 69 |
| D&H / D-H / H-D | 32 / 26 / 28 (J 0.37) | 39 / 21 / 19 (J 0.49) | 36 / 19 / 33 (J 0.41) |
| D exclusive (X - Y - Z over D's) | 8 | 14 | 10 |

D pairwise: far&sdr 41, far&ser 40, sdr&ser 36 heads. D shared core far&sdr&ser = 31 (union 87). H core = 28.
All six D and H circuits share 18 heads. The v1 SDR pair's D&H was 43 of 69/56, so v2 overlaps are lower.

| block | cells | count | A40 h | H200/H100 h (est.) |
|---|---|---|---|---|
| A. per-task pairs: atomic suff (sanity+null+pressure) on own test set, and heads-KO `X - m`, for 6 circuits | 6 suff + 6 KO | 12 | 6.0 | ~1.2 |
| A'. pair compositions per task: `D&H` suff + KO, `D-H` KO, `H-D` KO (the v1 exclusive-alone suff cells sat at the empty-circuit floor, so they are dropped) | 4 x 3 | 12 | 6.0 | ~1.2 |
| B. cross-task: each D on the other two D test sets (suff + KO); shared core `far&sdr&ser` suff + KO on all 3 tasks; XOR exclusives `(X-Y-Z) - m` KO on own test set | 6+6, 3+3, 3 | 21 | 10.5 | ~2.1 |
| C. controls: H on D's test set (suff + KO, the same-test-set comparison) and D on `<task>_nopressure` (suff + KO, ~13-15 min each) | 6 + 6 | 12 | 4.4 | ~0.9 |
| total minimal | | 57 | ~27 | ~5.5 (+ load overhead) |

Optional extensions: D on `<task>_honest` (6 cells, +3 h A40), H on nopressure (6, +1.4 h), H cross-task and H core
(12+, +6 h), pairwise D intersections (3 x 3 KO). The full format-control-style grid for the six circuits
(2 circuits x 3 test sets x {suff, KO} x 3 tasks = 36 cells) is ~15 A40 h on its own.

Speed ratios used: A100 = 2x A40 (15 vs 30 min per KO cell); H200 = ~5x (18 min for 3 KO exprs in one process).
H100 is assumed close to H200 (unmeasured). Packing several `--expr`/`--task-from` into one process saves the ~3-4 min
load per cell; walltime rule in `fc_cells.walltime` (estimate x 1.5, quarter hours, floor 60 min).

Prerequisites and code notes:
- `evaluate_circuit.py` already accepts v2 ids (`evaluation/context.py:161`, `evaluation/circuits.py:317` include
  `DECEPTION_TASKS_V2`). No change is needed for evals 1-4. All six v2 run dirs are already expanded, with
  `*.coarse.json` backups.
- `component_analysis/dataloaders.py:72` `MECHANISM_TASKS = ("far", "sdr", "ser")` is v1-only. Its guard at line
  149 rejects `*_v2`, so any component analysis on v2 needs it extended to `DECEPTION_TASKS_V2`. That also means
  checking the item-swap pairing against v2 records, which have new fields (`clean_item_d`, `pressure_slot`,
  `honest_twin_kind`, ...). Not needed for these evals.
- The `m` operand: `outputs/_launch_format_control/allmlp_nomb` has exactly the v2 mask keys and shapes
  (attention_blocks 32, heads 32x32, neurons 32x4096, mlp_hidden 32x14336, mlp_output 32x4096). Its `config.json` says
  `task sdr, nopressure`, so plans would print a misleading condition. Rebuild it from a v2 run with the
  `submit_headsko.sh` recipe (`_allmlp_nomb` under each v2 output dir) and confirm "complement verified" in the
  dry-run.
- No F (nopressure-trained) v2 circuits exist. To evaluate on `<task>_v2_nopressure`, `--task-from` needs a run dir
  whose `config.json` names `deception_condition: nopressure`. Make a config-only stand-in, as fc `standin-dryrun
  --f-run` does. `--task NAME` binds only the default (deceptive) condition.
- v2 `_honest` is the neutral-clause twin (`honest_twin_kind`), not the honest-instruction prompt. Eval 4's
  `honest_instruction` variant is a different counterfactual, built from `dc.HONEST_INSTRUCTION`.
- `wave_status.md`'s seed-123 note is that the reload sanity can fail the 0.002 tolerance across GPU types (A40-trained,
  A100-evaluated). The v2 D runs trained on H200 (far D, ser D) and A40 (the rest), so eval 1 may flag drift on any
  other GPU type.

## Part B. Portability to Bridges-2

### B1. Python environment

| item | value |
|---|---|
| env | conda `mgnp` at `/u/swong2/.conda/envs/mgnp`, 9.2 GB, Python 3.12.13 |
| pins | torch 2.11.0+cu128 (CUDA 12.8), transformers 5.13.0, datasets 5.0.0, accelerate 1.15.0, huggingface_hub 1.23.0, tokenizers 0.22.2, safetensors 0.8.0, numpy 2.5.1, pandas 3.0.3, nnsight 0.7.0, openai 3.8.0, tqdm 4.68.4 |
| compiled CUDA archs (mgnp torch) | sm_75 sm_80 sm_86 sm_90 sm_100 sm_120 (**no sm_70**) |
| repo env files | `requirements.txt` only, with ranges (torch>=2.7, transformers>=4.52, datasets>=2.14, openai>=1.40, ...). No environment.yml, pyproject or setup.py. |
| second supported env | login base py3.9 / torch 2.8.0 / transformers 4.57.3 (per requirements.txt and memory; `models/_compat.py` dispatches). Results differ by ~1 ulp between the two. |
| activation in sbatch | `source ~/.bashrc && conda activate mgnp` under `set +u` |

Recommendation: `conda pack` mgnp (or `pip freeze` into a pinned list) and unpack under `$PROJECT` on Bridges-2
(`module load anaconda3`; PSC advises envs in $PROJECT because $HOME is 25 GB). Rebuilding from `requirements.txt`
would pick different versions and lose comparability.

### B2. Model weights and caches

| item | value |
|---|---|
| model | `meta-llama/Llama-3.1-8B-Instruct` (`models/__init__.py` MODEL_REGISTRY), gated on HF |
| dtype | `torch_dtype=torch.bfloat16` for the reference and prunable models; gates are cast to fp32 (`models/__init__.py:66`, gate params `.float()`) |
| cache | `HF_HOME=/work/nvme/beto/swong2` and `TRANSFORMERS_CACHE=/work/nvme/beto/swong2/` exported in `~/.bashrc` |
| on disk | `hub/models--meta-llama--Llama-3.1-8B-Instruct` 15 GB |
| also needed | wikitext-2 for eval 2 collateral: `load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1")` (`evaluation/wikitext.py:55`); cached at `hub/datasets--Salesforce--wikitext` (7.5 MB) and `datasets/Salesforce___wikitext` |
| token | `$HF_HOME/token` (37 B). `--hf-token` is optional. The weights are cached, so rsyncing the snapshot and running with `HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1` avoids moving the token. The logs show "Fetching 4 files" on load, so the hub is contacted unless offline mode is set. |
| secrets | `~/.bashrc` also exports API keys (NNSIGHT_API_KEY, OPENROUTER_API_KEY). Evals 1-4 do not need them; do not copy `.bashrc` wholesale. |

### B3. Hard-coded paths and Slurm settings to change

| where | what |
|---|---|
| `scripts/evaluate_circuit.sbatch` | `--account=beto-delta-gpu`, `--partition=gpuA40x4`, `--gpus-per-node=1`, `--mem=64G`, `--time=12:00:00`, `--output=logs/...`, `source ~/.bashrc && conda activate mgnp`. Bridges-2: `-A <alloc>`, `-p GPU-shared --gpus=l40s-48:1` (or `h100-80:1`), `module load anaconda3`, the env under $PROJECT, export HF_HOME and offline flags. |
| SDR-wave launchers (`postprocess.sh`, `submit_headsko.sh`, `submit_composed.sh`) | hard-code `--account=bimc/beto/bgrb-delta-gpu` and partitions `gpuA40x4,gpuA100x4,gpuA100x8`; paths are repo-relative (they `cd` to the repo root). |
| `outputs/_launch_format_control/suites.json`, `suite_manifest.json` | absolute `/projects/beto/swong2/Alignment/Deception-Circuit/...` run dirs (main checkout); `submit.sh` passes `--accounts *-delta-gpu` |
| `outputs/_launch_format_control/eval5_cmd.py:49,95,97`, `evaluation/eval5_format_summary.py:53-56`, `dataset/check_v2_scaffold.py:49` | absolute `/projects/beto/...` and `/u/swong2/...`. Only needed for EVAL 5 and the v2 builder, not evals 1-4. |
| run `config.json` | `data_dir: "./data/datasets"` (relative), so jobs must start from the repo root |
| `evaluation/circuits.py:147` `norm_run_dir` | makes every run dir absolute, and `suite.json`/`summary.json` record it. Outputs written on Bridges-2 will carry `/ocean/projects/...` paths. Delta-side merge/summary scripts that compare run-dir strings with a Delta-path manifest (`merge_shards.py --manifest`) may then mismatch. Plan the manifest with relative paths, or post-process on one side only. |
| threading | launchers export `OMP/MKL/OPENBLAS_NUM_THREADS=1` (memory: pin BLAS threads) |

### B4. What must be present remotely

1. Code at the commit used (branch `mechanism-datasets`, HEAD bd67758; see B7).
2. `data/datasets/{far,sdr,ser}_v2{,_honest,_nopressure}` (9 dirs, 4.3-4.9 MB each) and `comparison_set_v2.json`.
3. The six v2 run dirs under `outputs/llama-8b-instruct_{far,sdr,ser}_v2_coarse/`, with `active_nodes.json` (expanded,
   7.9 MB), `config.json`, `results.json` (sanity reference) and the `*.coarse.json` backups. That is ~31 MB per task dir,
   mostly `history.json`/`train.log`, which can be skipped. Do not copy the failed ser D dir `..._261021-140323`.
4. An `m` operand dir (`active_nodes.json` + `config.json`, 2.1 MB) and a nopressure task-source stand-in (B4/A3).
5. The HF snapshot (15 GB) and wikitext caches; the conda env (9.2 GB packed).
Total transfer is about 25 GB, dominated by weights and env.

### B5. What evaluations write (to rsync back)

- Single atomic circuit on its own task: `<run>/evaluations/interchange/` with `sanity.json`, `knockout.json`
  (~1.4 MB), `null.json`, `pressure.json`, `random_circuits.json`, `summary.json`, `evaluation.log`, `plots/`.
- Any expression or multi-task run is a suite at `--output-dir` or `outputs/_suites/<name>/`, with `suite.json`,
  `suite.log`, `matrix.json`/`.csv` (written only at the end of the job), and
  `cells/<label>__leaf/<task>/interchange/{summary,knockout,null,pressure}.json` + `plots/`. Under fc the shards go to
  `_shards/<job>/`, merged into `cells/`.
- Slurm stdout goes to `logs/evaluate_circuit_<jobid>.out` (the launchers' own `logs/<suite>/`). `logs/` is git-ignored.
- Sizes are ~1.6-1.8 MB per cell. 57 cells come to ~100 MB.

### B6. Bridges-2 hardware (PSC user guide, fetched 2026-10-24)

| type (`--gpus=`) | nodes | GPUs/node | GPU mem | node RAM | SU |
|---|---|---|---|---|---|
| `h100-80` | 10 | 8 H100 | 80 GB | 2 TB | 2 per GPU-h |
| `l40s-48` | 3 | 8 L40S | 48 GB | 1 TB | 1 per GPU-h |
| `v100-32` | 24 (+1 DGX-2 with 16) | 8 | 32 GB | 512 GB (DGX-2 1.5 TB) | 1 per GPU-h |
| `v100-16` | 9 | 8 | 16 GB | 192 GB | 1 per GPU-h |

Partitions: `GPU` takes whole nodes (8 GPUs, max 64 per job, 48 h). `GPU-shared` takes 1-4 GPUs of one node, 48 h max,
1 h default. Batch syntax is `sbatch -p GPU-shared --gpus=l40s-48:1 -t HH:MM:SS`; interactive is
`interact -p GPU-shared --gres=gpu:h100-80:1`. $HOME is `/jet/home/<user>` (25 GB). $PROJECT is
`/ocean/projects/<grp>/<user>`, not backed up. $LOCAL is node scratch.

V100 and this pipeline:
- **V100 (sm_70) cannot run the mgnp env at all.** The torch 2.11+cu128 wheel has no sm_70 kernels (arch list above).
  The anaconda base torch 2.2.0.dev+cu121 still carries sm_70, but it is not a supported project env. I did not
  check the py3.9/torch 2.8 login env's arch list.
- Even with a sm_70 build, V100 has no native bf16. PyTorch emulates it or falls back (no bf16 tensor-core GEMM,
  no flash SDPA), so it would be several times slower than an A40 and numerically off Delta.
- On 32 GB, the default `--reference separate` cannot fit (weights alone ~32 GB). `--reference shared` (~17 GB
  weights) would fit; 16 GB V100s cannot hold the model.
- **Use `l40s-48` or `h100-80` instead.** L40S (Ada, sm_89, runs the sm_86 cubin) has native bf16 and 48 GB, the
  same memory class as the A40 every coarse eval ran on. H100 (sm_90, native) is likely ~H200 speed at 2 SU/GPU-h.

Bit-exactness: results will not be bit-exact with Delta on any Bridges-2 GPU. bf16 kernels differ by architecture,
and the seed-123 sanity (A40 to A100) already sat at the 0.002 tolerance. Keep each suite on one GPU type. Read the
eval-1 verdict with that caveat. Re-run one Delta reference cell on Bridges-2 as a same-path control, for example
v1 coarse SDR D's sanity, or one fc headsko cell whose numbers are on disk.

Not verified: the user says Bridges-2 goes offline Nov 9, 2026. The PSC guide mentions a planned relocation to a
CMU datacenter but gives no dates, and a web search found nothing. The guide names the data-transfer host
`data.bridges2.psc.edu` (not "b2dtn") and says transfers are initiated from the remote side, which matches
"rsync from Delta". Compute-node internet access was not checked, so plan for offline mode.

### B7. Git

- Remote: `origin https://github.com/JaMussCraft/Deception-Circuit.git`.
- `main` is aef064a and tracks `origin/main`. **`mechanism-datasets` (bd67758) has no upstream, so it is not pushed.** A `git clone` on
  Bridges-2 will not have the v2 code, datasets or run dirs until the branch is pushed. Otherwise, rsync the worktree.
- `.gitignore` excludes only `logs/`, `outputs/_analyses/`, `data/datasets/ioi`, `__pycache__`, `wandb/`. So `outputs/`
  run dirs and `data/datasets/*_v2` are tracked in the commits, untracked worktree items aside (`outputs/_build_v2/`
  and the failed ser D dir, per the session git status).
