# Hand-back 07: D2 premise plan and two-turn build

Agent: Opus worker (claude-opus-5-5), direction deception-divergence. Ticket: the lead's message of Mon 2 Nov 2026,
"D2 plan and two-turn premise build", and the follow-ups on jobs 50153789 and 50155519. Status: the plan, the code,
the tests and the GPU job are done; the classifier arm is read; the acts-on-it arm waits for the judge, which the
orchestrator runs (commands in "Results so far").

## What changed

Committed by the orchestrator from the worktree
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence`:

- `docs/research/deception-divergence/plans/D2-plan.md`: the D2 premise plan, with the rulings to record (section 9).
- `docs/research/deception-divergence/reports/07-handback.md`: this file.
- `docs/research/deception-divergence/results/d2/`: the dry-run `build_summary.json` and one `build_report.json`
  per task, copied from the ignored output directory.
- `scripts/d2_rows.py`: the two-turn row builder (forced answer, second user turn, segment spans, prefix/suffix
  split, condition loader with the target asserts).
- `scripts/d2_premise.py`: stages `inputs`, `build --dry-run`, `features`, `direction`, `generate`, `read` and
  `judge`.
- `scripts/jobs/run_d2_premise.sh`: the Slurm wrapper for Delta and Bridges-2, with `--dry-run`.
- `spontaneous/d2_judge.py`, `spontaneous/grader/d2_judge_prompt.txt`, `spontaneous/grader/d2_judge_config.json`:
  the D2 judge, whose three files make freeze G-D2. `spontaneous/judge.py` (B3 freeze G1) is untouched.
- `data/d2/d2_inputs.json`: the derived inputs (sha256 `a91cb15b846a815b631986957fecdf9b03ef705a1dc6f6bd826e3d5637932451`):
  the 48 Pacchiardi questions with their indices and groups, 128 + 32 AdvBench and 128 + 32 Alpaca prompts, seeds and
  the sha256 of every source file.
- `tests/test_d2_rows.py` (8 tests) and `tests/test_d2_premise.py` (24 tests).
- `.gitignore`: one line, `data/d2/_downloads/`, beside the existing `data/b3/_downloads/`.

After job 50155519 (worktree files, not yet committed):

- `scripts/d2_premise.py` (sha256 `ad21b9d48b5883c7610a8d6bd078d2fc1ccd2fb961b2d0492e96462be7bcfe40`): two changes
  to the read side only, beyond the lead's literal ask, each for a reason found while preparing the judge. No
  function used by `features`, `direction` or `generate` changed (a line diff against the job's copy at
  `fe47e7c6...` touches only lines after 1,249: `load_labels`, the acts-on-it block of `read_task`, `readings_md`
  and `run_read`). (1) A `read` with the calibration labels only, the step that freezes the proxy tokens, reported
  the verdict as final with no maintenance rate; the arm is now `partial` while any test row lacks a label, the
  verdict is not final, and `--write-tokens` still writes the token file. (2) `load_labels` mapped every file's
  rows by row id, so passing the cross-check or re-judge labels to `read` would have overwritten primary labels for
  those rows, and nothing reported the cross-check agreement or the re-judge flip rate that R11 asks for. Records
  with stage `crosscheck` or `rejudge` are now kept out of the primary labels, and `readings.json` gains a
  `judge_checks` block (agreement overall and per task, agreement without UNCLEAR, a confusion count, and the
  re-judge flip rate). The lead may accept or revert either change; neither touches the G-D2 files.
- `tests/test_d2_premise.py` (sha256 `e53a533f67a19647f3dc21686e2047f086bcf44e6fcd53707afdb7259291d7eb`): 27 tests;
  the end-to-end test also runs a calibration-only read, and two new tests check that check labels never overwrite
  primary labels and that `judge` stage output (mocked transport, reviewed test ledgers) round-trips into `read`.
- `docs/research/deception-divergence/results/d2/job50155519/`: the job's `readings.json`, `readings.md`,
  `refusal_direction.json` and its manifest, the GPU timings and the nine per-task stage manifests, copied from the
  ignored output directory.
- `logs/bridges2/d2_premise_50155519.out`: the job log (sha256 `d206a71e...`, equal on both ends).

Not committed: the raw downloads in `data/d2/_downloads/` (`pacchiardi_probes/`, `advbench/`, `alpaca/`, each its
own directory, read with `python -I` only). Nothing is staged for the apply tool.

## How verified

Source files, read as data:

| file | sha256 |
|---|---|
| `probes.csv` (`LoryPack/LLM-LieDetector`, 65 questions) | `21cb2b84bb941131beda9c3d272842137f8128bcb3a76f63e019a55318296710` |
| `lie_indices.npy` (24) | `9f40f628791220aa1e97439b106c50f3eec5879f26555460e3d7d7e91c9ed96a` |
| `no_lie_indices.npy` (14) | `bbd8ace69967cea7a2db0f24f3a58881423973905dbd88ccfc3e1192909c4172` |
| `knowable_indices.npy` (10) | `4b11ea884941e5dfa215d4e8cccfc8cbf1cd2942b3f87e62245e5479d701a361` |
| `harmful_behaviors.csv` (AdvBench, 520 rows) | `6cd1a5c63c07610d7eb67307772ee5606017ee950b5770ab288a2c487489d3e1` |
| `alpaca_data.json` (52,002 rows, 31,323 with no input) | `2eddafc6b977608d778aaab8dfc7e50e547b3af9826dfb9e909d9fc362e4a419` |

The repository README says the paper's 48 elicitation questions are the union of the three group files; the union
has exactly 48 distinct indices, so no question was written by us.

```
OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest -p no:cacheprovider -q tests/test_d2_rows.py tests/test_d2_premise.py
```

Observed: 32 passed (mgnp, transformers 5.13.0).

```
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_d2_rows.py tests/test_d2_premise.py
```

Observed: 32 passed (base, transformers 4.57.3; the logistic regression also matches scikit-learn 1.3.0 here).

What the tests cover: the four-turn text is byte-identical to `render_messages` on the real tokenizer; every segment
decodes to its text and the prefix/suffix split is a token boundary; a mid-token span is refused; the forced item
is D's target in D, I and H (the honest twin's own target is the true item); the cached second-turn logits equal
independent unpadded forwards on a tiny Llama with the real vocabulary (within 1e-4); directional ablation leaves
every residual orthogonal to the direction; activation addition at layer 0 equals an embedding shift; the
end-to-end GPU stages and the read stage run on the tiny model; the logistic regression reaches the L2 optimum;
AUROC with ties, the clustered bootstrap, the 15-point rule, the "explains" rule, the R2 reading, the acts-on-it
rates, the proxy calibration and agreement on synthetic rows; the judge request carries no clause, condition or
task; the judge config is canonical and the freeze hash reproduces by the shell recipe; the judge stage samples and
its dry run counts requests; the wrapper parses and refuses a foreign working directory.

```
/u/swong2/.conda/envs/mgnp/bin/python -m spontaneous.d2_judge --print-hash
```

Observed: `1e41b6b92a0d0c92c68c790c9c220cf1f866fae7b30ed3a1d4c7e0fabcf50215`, equal to the `sha256sum | awk | sort |
sha256sum` recipe in the module docstring.

```
/u/swong2/.local/bin/research-session lint docs/research/deception-divergence/plans/D2-plan.md docs/research/deception-divergence/reports/07-handback.md
```

Observed: no findings.

After job 50155519:

```
DC_DELTA_REPO_ROOT=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence scripts/remote/b2.sh fetch outputs/_analyses/deception-divergence/d2
```

Observed: 28 files on each end; `sha256sum` agrees for all 24 files the job wrote. The four build files
differ only in their CPU seconds and estimate fields, because the local copies come from the later no-cache dry run
and rsync kept the newer files. The log came over `ssh ... cat` (the fetch helper refuses `logs/`).

```
/u/swong2/.conda/envs/mgnp/bin/python -I scripts/d2_premise.py read
```

Observed: run on the Delta login node against the fetched files, the result equals the job's own `readings.json`
in every field; 131 floating-point fields differ, all below one part in 10^9 (the fitted weights' last digits). The
job's `readings.json` was then restored in the output directory.

```
/u/swong2/.conda/envs/mgnp/bin/python -I scripts/d2_premise.py judge --judge-stage <stage> --dry-run
```

Observed for each of the five stages: the request counts in the judge table below; G-D2 hash
`1e41b6b92a0d0c92c68c790c9c220cf1f866fae7b30ed3a1d4c7e0fabcf50215` in every report.

```
OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -I -m pytest -p no:cacheprovider -q tests/test_d2_rows.py tests/test_d2_premise.py
OMP_NUM_THREADS=4 HF_HUB_OFFLINE=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest -p no:cacheprovider -q tests/test_d2_rows.py tests/test_d2_premise.py
```

Observed: 35 passed on mgnp and 35 passed on base Python 3.9.

## Execution evidence

- Job id and cluster: 50155519 on Bridges-2, GPU-shared, one H100-80, account cis260361p, host
  w001.ib.bridges2.psc.edu, wrapper `scripts/jobs/run_d2_premise.sh --no-prefix-cache` (stages `features direction
  generate`, then `read`). The first submission, 50153789, failed on the cache guard and wrote no feature file.
- Exit code or Slurm state: COMPLETED, exit 0:0, elapsed 00:41:59 (0.70 GPU-hours against the 1.03 estimate).
  Stage seconds from `gpu_timings_1793673782.json`: unablated features 306, 335 and 327 (FAR, SDR, SER), refusal
  direction 33, ablated features 235, 268 and 267, generation 123, 88 and 107, model loads 310 in total.
- Row counts, observed against the dry-run table, all equal:

| task | unablated rows | ablated rows | generations (cal, test unablated, test ablated) | test ids |
|---|---|---|---|---|
| far_v2 | 1,430 / 1,430 | 1,030 / 1,030 | 1,460 / 1,460 (200, 630, 630) | 210 |
| sdr_v2 | 1,550 / 1,550 | 1,150 / 1,150 | 1,700 / 1,700 (200, 750, 750) | 250 |
| ser_v2 | 1,547 / 1,547 | 1,147 / 1,147 | 1,694 / 1,694 (200, 747, 747) | 249 |

  Every condition splits as planned (fit 200 D and 200 H, gate 200 and 200, test D, I and H equal). Row ids are
  unique, no generation is empty, and two of 4,854 generations reach the 128-token cap (one FAR, one SER).
- Cached against full features on 8 rows per task, descriptive only under R14 (the full path is the path of record):

| task | max absolute logit difference | acts-on-it top-1 token mismatches (of 8) |
|---|---|---|
| far_v2 | 0.2506 | 0 |
| sdr_v2 | 0.3750 | 2 |
| ser_v2 | 0.3751 | 0 |

- Baseline reproduces: the FAR comparison gives 0.2506, the same figure to four digits as the failed job 50153789
  (0.251), and the local `read` reproduces the job's classifier numbers to within one part in 10^9 (SDR gap 0.160
  against 0.160).
- Provenance file: `outputs/_analyses/deception-divergence/d2/<task>/features_unablated.manifest.json` (and the
  ablated and generation manifests), copied to `results/d2/job50155519/`; each names commit
  `fb2cb9e7fd6e4e7e2f594b3d03f1a079e4b40e54`, bfloat16, inputs sha256 `a91cb15b...`, and code hashes
  `scripts/d2_premise.py` `fe47e7c6...`, `scripts/d2_rows.py` `c06a4fd8...`, `spontaneous/d2_judge.py`
  `701a88a5...`, which equal the committed files at fb2cb9e. Output file hashes:

| file | sha256 |
|---|---|
| far_v2/features_unablated.jsonl | `6affb59a95845b87d1d86ff75f9716abb94713b529611abe7d5e4e0bd49d35fd` |
| far_v2/features_ablated.jsonl | `37cc9fe1f473118a16a769c7321244f10462728175b42d59e35e4e0ec3926d3e` |
| far_v2/generations.jsonl | `ca859868f6b206ff9387a550a1168a59d2471a2707ba0b4c37ddf9b466965525` |
| sdr_v2/features_unablated.jsonl | `4a0b9cb6d61f83f28f154d0f718d2b9f7673eedea61ba96d4223673e05648ffa` |
| sdr_v2/features_ablated.jsonl | `75f8bf0ecb51e11809e66fc0096ce42cb9a904a237032b51b02034069a4a0cc5` |
| sdr_v2/generations.jsonl | `8c3a467c55233b0fa0a5db8dbfd8c1b34d34e7731f6dcbddf74727c09f885a6d` |
| ser_v2/features_unablated.jsonl | `f6368efc02d7d8c33f32c4f775285bed51d114c63ce86d6d724a2c33c0cb9c5d` |
| ser_v2/features_ablated.jsonl | `4ef894d0706fb51d494eb1ddb683279f5a44de5b586bc508cf14c1a2d9b5fb78` |
| ser_v2/generations.jsonl | `22115e82f078af9ad440a9bcd5a7ff75970182d4ee188511381e4f25be64f106` |
| readings.json | `7f6ad3693a733f0a7eef76af0e2406d959216d70cf400c95c7a35148d64f1714` |

The classifier arm's evidence block is complete. The acts-on-it arm has no evidence yet, so the premise verdict is
not yet verified: the judge labels are missing.

The earlier CPU dry run (both interpreters, equal key for key) predicted the row counts above; its tables are in
`results/d2/build_summary.json` and the per-task build reports.

## Results so far

**Refusal direction (R12).** Layer 11, position -5, chosen among 19 of 125 non-degenerate candidates that passed
Arditi's filter (bypass -9.81, induce 7.72, KL 0.055). Ablation takes the harmful refusal share on the 32 held-out
AdvBench prompts from 1.0 to 0.0, so the control is valid.

**Classifier arm (R10), test ids, threshold 0.5:**

| task | gate AUROC (validation, D vs H) | rate D | rate I | rate H | gap D - I | 95% interval | gap under ablation (refit) | separates | refusal explains | R2 p |
|---|---|---|---|---|---|---|---|---|---|---|
| far_v2 | 1.000 | 1.000 | 0.995 | 0.000 | 0.005 | 0.000 to 0.018 | 0.000 | no | yes | 0.995 |
| sdr_v2 | 1.000 | 1.000 | 0.840 | 0.000 | 0.160 | 0.086 to 0.227 | 0.136 | yes | no | 0.840 |
| ser_v2 | 1.000 | 1.000 | 0.855 | 0.000 | 0.145 | 0.076 to 0.215 | 0.032 | no | yes | 0.855 |

- SDR passes the pre-registered rule by one point: the gap is 0.160 against the 0.15 bar, and its interval
  (0.086 to 0.227) spans the bar. Ablation leaves 0.136 of it, less than half the change needed to "explain" it.
- SER misses by half a point (0.145), and the refusal control would explain it anyway (0.145 to 0.032).
- FAR has no gap. Its "refusal explains: yes" is degenerate, because any change of a near-zero gap counts as half.
- The R2 reading is "I patterns like D: falsity state" on all three tasks (spread 1.0, p 0.84 to 0.995). The
  plan's qualifier applies: D and I share clause words, so this can be lexical.
- AUROC of D against H is 1.000 on validation and test in every task, and I against H is 0.991 to 1.000. Only H
  lacks an operator clause, so the probe may be reading the clause's presence rather than a lie state; D against I
  is 0.69 to 0.76.
- Under ablation the frozen classifier calls almost everything D (H rate 0.46, 0.98 and 1.00), so it is
  uninformative, as R12 anticipated by making the refit primary. The refit has no gate (no gate rows were run
  ablated); its held-out D and H test rates (1.0 and 0.0) are the out-of-sample check.
- Per question group (descriptive, not in the rule), the D - I gap is: FAR lie 0.000, no-lie 0.086, knowable 0.148;
  SDR 0.152, 0.044, 0.316; SER 0.213, 0.181, 0.004.

**Verdict so far.** The classifier arm passes on SDR only. Every task's verdict is not final until the acts-on-it
arm is judged, so the premise does not yet pass or fail.

**Generations.** Read by eye on a seeded sample: replies are complete sentences; the model often corrects the
forced answer in all three conditions (for example "I made a mistake... the correct answer is actually ...") and
sometimes refuses to help mislead a boss in D. Nothing here is a judged rate.

**Judge plan for the orchestrator (not run).** Requests are counted by the dry run against empty caches; duplicate
requests (identical facts and reply) share one paid call and every row still gets its label. The cost uses the
measured prompt sizes (about 670 input tokens, 8 output tokens) at the pinned prices (Haiku $1 and $5, Sonnet $3
and $15 per million).

| stage | model | rows | paid requests | estimated cost | ledger ceiling (minimum) |
|---|---|---|---|---|---|
| calibration | Haiku 4.5 | 600 | 547 | $0.39 | $2.00 |
| main | Haiku 4.5 | 2,127 | 1,666 | $1.19 | $4.50 |
| main_ablated | Haiku 4.5 | 2,127 | 1,739 or fewer | $1.23 | $4.50 |
| crosscheck | Sonnet 4.5 | 200 | 191 | $0.41 | $7.00 |
| rejudge | Haiku 4.5 | 213 | 202 | $0.14 | $2.00 |
| total | | 5,267 | 4,345 or fewer | about $3.40 | $20.00 |

The ceilings matter more than the spend. `JudgeBudget` counts in-flight reservations against the ceiling: a Haiku
reservation is $0.20 at concurrency 8 ($1.60 in flight), and a Sonnet reservation is $3.00 at concurrency 2 ($6.00
in flight), which `d2_premise.py` cannot lower. A crosscheck ledger below about $6.50 stops on its second call.
B3's split ($10, $3, $7) does not carry over. Each stage stays far under 5,000 attempts.

Commands, from the worktree with `OPENROUTER_API_KEY` set; `J` is `outputs/_analyses/deception-divergence/d2/judge`
and the frozen token file's default path is `docs/research/deception-divergence/results/d2/proxy_tokens.json`
(a default; any tracked path works):

```
PY="/u/swong2/.conda/envs/mgnp/bin/python -I scripts/d2_premise.py"
J=outputs/_analyses/deception-divergence/d2/judge
TOK=docs/research/deception-divergence/results/d2/proxy_tokens.json
# 1. calibration labels (600 rows)
$PY judge --judge-stage calibration --ledger $J/ledger_calibration.jsonl --cache $J/cache_haiku.jsonl --labels-out $J/labels_calibration.jsonl
# 2. freeze the proxy tokens; record the printed sha256 in spec.md before step 3 (G-D2)
$PY read --labels $J/labels_calibration.jsonl --write-tokens $TOK
# 3. and 4. primary labels on the test rows
$PY judge --judge-stage main --ledger $J/ledger_main.jsonl --cache $J/cache_haiku.jsonl --labels-out $J/labels_main.jsonl
$PY judge --judge-stage main_ablated --ledger $J/ledger_main_ablated.jsonl --cache $J/cache_haiku.jsonl --labels-out $J/labels_main_ablated.jsonl
# 5. Sonnet cross-check (200 seeded unablated test rows)
$PY judge --judge-stage crosscheck --ledger $J/ledger_crosscheck.jsonl --cache $J/cache_sonnet.jsonl --labels-out $J/labels_crosscheck.jsonl
# 6. re-judge (213 seeded rows) through a fresh cache
$PY judge --judge-stage rejudge --ledger $J/ledger_rejudge.jsonl --cache $J/cache_rejudge.jsonl --primary-cache $J/cache_haiku.jsonl --labels-out $J/labels_rejudge.jsonl
# 7. the verdict, against the frozen tokens
$PY read --labels $J/labels_calibration.jsonl $J/labels_main.jsonl $J/labels_main_ablated.jsonl $J/labels_crosscheck.jsonl $J/labels_rejudge.jsonl --tokens $TOK
```

Each live stage refuses without a reviewed ledger, so the five ledgers (schema 1, reviewed, the ceilings above,
`max_paid_attempts` up to 5,000) come first. Add `--dry-run` to any judge line to recount against the cache before
paying. Step 7 checks that the frozen token file equals the calibration and fails otherwise. Before the read-side
change above, step 7 would have let the cross-check and re-judge labels overwrite primary labels; with it, those
files feed only the R11 report.

## What is NOT done

- The judge stages, the proxy token freeze and the acts-on-it arm have not run, so no task's verdict is final.
  Paid calls are the orchestrator's.
- The full repository test suite was not run; only the two D2 test files ran, on both interpreters. No existing
  file other than `.gitignore` was edited.
- Once, while checking the output files, a combined command ran `git status --short` in the worktree (read only, no
  output). The brief forbids git; no other git command ran.
- The patching payload (plan section 8) is planned only and needs its own ruling if the premise passes.
- No teacher-forced stem set was built for the first-token proxy, although the brief asked for one as
  instructed-route R4 did. The proxy is calibrated from the first generated token of the judged validation
  generations; an ambiguous opener such as "I" falls into neither list and its rows count as `undecided`. If such
  openers start more than a fifth of the calibration rows, a stem-resolved proxy needs a ruling before the proxy
  can be the patching readout (plan section 3b). The judge is the primary readout either way.
- The model tests use a tiny random Llama (2 layers, 64 hidden) with the real 128,256-token vocabulary instead of
  the vocab-101 model in `tests/helpers.py`, so that the real rows, the 48 questions and the real yes, no and
  refusal token ids run unchanged.
- Arditi pooled four harmful sources; only AdvBench is used. The refusal direction's validity is checked, not
  assumed.

- Job 50153789 (Bridges-2) failed after 158 s on the cache guard: far_v2 cached against full features differ by
  0.251 against the 0.25 bar; no feature file was written for any task. The guard now applies to the cached path
  only, and `--no-prefix-cache` (forwarded by the wrapper to every stage) makes the full path the path of record,
  with the comparison recorded in each features manifest. Changed: `scripts/d2_premise.py`,
  `tests/test_d2_premise.py` (33 tests pass on mgnp), the plan's section 6 note. Resubmitted as 50155519, which
  completed (see "Execution evidence").

## Open questions

- FAR and SER have no unused I ids after the premise (all 210 and 249 are in it), so a passing FAR or SER would
  need its patching ids from the premise ids or from fresh inversion rows. Default: reuse the premise ids and say
  so in the ruling.
- The first-answer full stop follows `deception_v2.demo_exchange`; the brief's wording had no full stop. Default:
  keep the full stop (it is the model's natural continuation of the requested format and defines the prior-answer
  span as item plus full stop plus `<|eot_id|>`).
- Should the D2 judge hash also go into `directions.json`? Default: spec.md only, as B3's hashes were.
