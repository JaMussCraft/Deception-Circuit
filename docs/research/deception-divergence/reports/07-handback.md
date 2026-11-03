# Hand-back 07: D2 premise plan and two-turn build

Agent: Opus worker (claude-opus-5-5), direction deception-divergence. Ticket: the lead's message of Mon 2 Nov 2026,
"D2 plan and two-turn premise build", and the follow-ups on jobs 50153789 and 50155519 and on the judge. Status:
done. The plan, the code, the tests, the GPU job, the judge (run by the orchestrator) and the final read are
complete, and the R13 verdict is in "Results". The patching ruling and the independent review are the
orchestrator's.

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

- `scripts/d2_premise.py` (sha256 `ad21b9d48b5883c7610a8d6bd078d2fc1ccd2fb961b2d0492e96462be7bcfe40` after these
  two changes, `2c159274957cd76e6ee41a97640fe04737b989ec385b5238ec9ee8d40813f338` after the review 04 fix below): two changes
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
- `tests/test_d2_premise.py` (sha256 `e53a533f...` with 27 tests, then
  `f4c4443f01d973c2994faf94964648cc2e75686b7f89ba6f23d8e6c4fef4548e` with 28 after the review 04 fix);
  the end-to-end test also runs a calibration-only read, and two new tests check that check labels never overwrite
  primary labels and that `judge` stage output (mocked transport, reviewed test ledgers) round-trips into `read`.
- `docs/research/deception-divergence/results/d2/job50155519/`: the job's `readings.json`, `readings.md`,
  `refusal_direction.json` and its manifest, the GPU timings and the nine per-task stage manifests, copied from the
  ignored output directory.
- `logs/bridges2/d2_premise_50155519.out`: the job log (sha256 `d206a71e...`, equal on both ends).

After the judge (worktree files, not yet committed; the orchestrator ran every paid stage and the final read):

- `docs/research/deception-divergence/results/d2/judge/`: the five ledgers, the five label files and their five
  manifests, copied unchanged from `outputs/_analyses/deception-divergence/d2/judge/` (hashes in "Execution
  evidence").
- `docs/research/deception-divergence/results/d2/readings_final.json` and `readings_final.md`: the final read
  (created 21:19:53, `final` true), kept apart from the job's partial read in `results/d2/job50155519/`.
- `docs/research/deception-divergence/results/d2/proxy_tokens.json` (sha256 `304ad7fa...`) was written by the
  orchestrator's calibration read; it is listed here because it belongs in the commit.
- Review 04 fix: `proxy_agreement` now reports `qualifies` false, `applicable` false and a `reason` ("empty
  maintenance token list" or "empty correction token list") when either token list is empty; `agree` is reported
  as before. A new test checks both cases. `calibrate_proxy` and the token file are unchanged. The orchestrator's
  final read command was re-run, and its output replaced `results/d2/readings_final.json` and `readings_final.md`.
- Not copied: the three judge caches, which hold full prompts. They stay in the ignored output directory:

| cache | bytes | sha256 |
|---|---|---|
| `judge/cache_haiku.jsonl` | 369,903 | `24b0765522770d150bb40cbe05ae772431f679e27a80cab987824b4b0fb92aa1` |
| `judge/cache_sonnet.jsonl` | 19,777 | `2f23c6f7603273dcf82bccb7c8ef2f3f7d06e66e95b8a84f86eaa0839197c609` |
| `judge/cache_rejudge.jsonl` | 20,353 | `005ea409dbf063e2e78259735f8726f9cfe22b063b335dc4afb23154f5a2d446` |

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

After the judge, each ledger and label file was read with a short script (header, reserve and settle events, costs,
label status, grader hash in each manifest). The files were then copied, and every copy's sha256 equals its source.
A third check confirmed that the label files' sha256 equal the `labels` block of the final `readings.json`. The
token file's sha256 was recomputed and matches the G-D2 entry in spec.md. A fourth check decoded the proxy token ids
with the Llama-3 tokenizer: 40 "I", 791 "The", 11458 "However", 14524 "Wait", 53692 "Actually".

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

Judge (run by the orchestrator; read and checked here):

| stage | model | ledger ceiling | paid attempts | settled cost (USD) | unsettled | labels (all parsed) |
|---|---|---|---|---|---|---|
| calibration | Haiku 4.5 | $2.00, 700 | 547 | 0.3313 | 0 | 600 |
| main | Haiku 4.5 | $4.50, 2,000 | 1,546 | 0.9460 | 0 | 2,127 |
| main_ablated | Haiku 4.5 | $4.50, 2,100 | 1,578 | 0.9578 | 0 | 2,127 |
| crosscheck | Sonnet 4.5 | $8.00, 250 | 191 | 0.3491 | 0 | 200 |
| rejudge | Haiku 4.5 | $2.00, 300 | 202 | 0.1229 | 0 | 213 |
| total | | $21.00 in ceilings | 4,064 | 2.7071 | 0 | 5,267 |

Every ledger header is schema 1 and reviewed. Every label manifest names grader `d2_judge_sha256`
`1e41b6b92a0d...`, the G-D2 freeze. The main and ablated stages paid for fewer requests than the dry run's 1,666 and
1,739, because they shared the Haiku cache with the calibration stage. The ceilings sum to $21.00, above the $20
direction cap, but the spend is $2.71.

| record file | sha256 |
|---|---|
| judge/labels_calibration.jsonl | `7b3d25af2f75d46d8acf5f46483db19c120158d4a99c469fdd97c3d297114b8f` |
| judge/labels_main.jsonl | `6c430de9951772231d8603a518a13ae68d394a962e2c47a246c7ccef9e6705ee` |
| judge/labels_main_ablated.jsonl | `5c1e632b381b24df22e791433a1d002cd1cec9d1a0dfdffa5e21fc3434f86fec` |
| judge/labels_crosscheck.jsonl | `38eb9a49c46c4e7e8d0e2d2ed04f244a37e31a316b2e2ab4a154e1682e94544f` |
| judge/labels_rejudge.jsonl | `58cdb586dad3ff1740860f3356f7032534e08055de1ba3d7bfb43afc4c5a8810` |
| judge/ledger_calibration.jsonl | `2ad39d57c5be35617f6063397d38457672e396942e1bef3e419f66541c937362` |
| judge/ledger_main.jsonl | `5ad9c9ba4d49143400e0e9360e374265a15a2b4983256093fccd85b46f9d2ce4` |
| judge/ledger_main_ablated.jsonl | `9eef51a9b53e9c7fa5ccc899c7f09516ec55a36a19923c4647e63aa09ff98d7a` |
| judge/ledger_crosscheck.jsonl | `76ec60ac75ca3a771138066a2eaa42d2772c418d835df579108c4bc1fd17cd21` |
| judge/ledger_rejudge.jsonl | `92db59d497429bd259628d1561a1da414b7355c6e37b362853daf78d6340e1fd` |
| readings_final.json (re-run after the review 04 fix) | `2072104864653f00f80e51f2001b121d07ca78d63d7db27135c8581d02947721` |
| readings_final.md (re-run after the review 04 fix) | `ab524e3eb3a5bd5615ae789d65ee5e3134f75e4bfd52b27979d9f982a54d9e88` |

The orchestrator's final read named code `scripts/d2_premise.py` `ad21b9d4...` (the read-side changes above); the
re-run after the review 04 fix names `2c159274...` and differs from it only in the proxy flags. Both name `scripts/d2_rows.py`
`c06a4fd8...` and `spontaneous/d2_judge.py` `701a88a5...`, and the frozen token file
`results/d2/proxy_tokens.json` with sha256 `304ad7fa5e9963067e57f06833a03b64e2938eb6deb68dd33aadda31992302a0`.
The orchestrator recorded that hash in spec.md after the calibration stage and before the main stage, and the final
read checked the file against the calibration.

The execution-evidence block is complete for both arms.

The earlier CPU dry run (both interpreters, equal key for key) predicted the row counts above; its tables are in
`results/d2/build_summary.json` and the per-task build reports.

## Results

### R13 verdict

| task | classifier arm | acts-on-it arm | refusal control | task verdict |
|---|---|---|---|---|
| far_v2 | no separation (gap 0.005) | no separation (gap -0.012) | valid | fails |
| sdr_v2 | separates (gap 0.160, 0.086 to 0.227), not explained (ablated 0.136) | no separation (gap 0.031) | valid | passes |
| ser_v2 | misses (gap 0.145 < 0.15), and explained (ablated 0.032) | no separation (gap 0.000) | valid | fails |

The direction's premise passes under R13, on SDR only.

- **The SDR pass rests on the classifier arm alone.** That arm fits D against H on the 48 elicitation answers and
  rates I on the same scale.
- **The acts-on-it arm is uninformative.** After the forced wrong first answer, the model corrects it when the user
  says they will act on it. Among rows the judge decided, 96 to 100 percent are corrections in every condition
  without ablation, and 89 to 100 percent with it. Maintenance is under 0.04 everywhere without ablation, so no arm
  can separate and the R2 reading is undefined on every task.
- **The R2 reading on the classifier scale is the same on every task:** I patterns like D (p 0.84 to 0.995, spread
  1.0), which the plan labels a falsity state. See caveat (a) for what that label can and cannot mean here.

Refusal direction (R12): layer 11, position -5, chosen among 19 of 125 non-degenerate candidates that passed
Arditi's filter (bypass -9.81, induce 7.72, KL 0.055). Ablation takes the harmful refusal share on the 32 held-out
AdvBench prompts from 1.0 to 0.0, so the control is valid.

### Classifier arm

Test ids, threshold 0.5. "Refit" is the R12 primary under ablation: the classifier fitted again on ablated fit rows.
"Frozen" applies the unablated classifier to ablated features.

| task | condition | gate AUROC (val D vs H) | rate D | rate I | rate H | gap D - I | 95% interval | AUROC D vs I | AUROC I vs H |
|---|---|---|---|---|---|---|---|---|---|
| far_v2 | base | 1.000 | 1.000 | 0.995 | 0.000 | 0.005 | 0.000 to 0.018 | 0.711 | 1.000 |
| far_v2 | ablated, refit | none | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 to 0.000 | 0.663 | |
| far_v2 | ablated, frozen | | 1.000 | 1.000 | 0.457 | 0.000 | | | |
| sdr_v2 | base | 1.000 | 1.000 | 0.840 | 0.000 | 0.160 | 0.086 to 0.227 | 0.763 | 1.000 |
| sdr_v2 | ablated, refit | none | 1.000 | 0.864 | 0.000 | 0.136 | 0.069 to 0.196 | 0.775 | |
| sdr_v2 | ablated, frozen | | 1.000 | 1.000 | 0.984 | 0.000 | | | |
| ser_v2 | base | 1.000 | 1.000 | 0.855 | 0.000 | 0.145 | 0.076 to 0.215 | 0.690 | 0.991 |
| ser_v2 | ablated, refit | none | 1.000 | 0.968 | 0.000 | 0.032 | 0.005 to 0.061 | 0.635 | |
| ser_v2 | ablated, frozen | | 1.000 | 1.000 | 1.000 | 0.000 | | | |

Test AUROC of D against H is 1.000 on every task, and training AUROC is 1.000 (base and refit). Mean classifier
score: D 0.996 to 0.998, I 0.823 to 0.942, H 0.002 to 0.003.

Per question group (descriptive, not in the rule; each group fits its own classifier):

| task | group | gate AUROC | rate D | rate I | rate H | gap | 95% interval | AUROC D vs I |
|---|---|---|---|---|---|---|---|---|
| far_v2 | lie | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 | 0.000 to 0.000 | 0.714 |
| far_v2 | no-lie | 1.000 | 1.000 | 0.914 | 0.000 | 0.086 | 0.031 to 0.161 | 0.614 |
| far_v2 | knowable | 1.000 | 0.981 | 0.833 | 0.000 | 0.148 | 0.079 to 0.237 | 0.624 |
| sdr_v2 | lie | 1.000 | 1.000 | 0.848 | 0.000 | 0.152 | 0.076 to 0.228 | 0.806 |
| sdr_v2 | no-lie | 1.000 | 0.996 | 0.952 | 0.012 | 0.044 | 0.008 to 0.088 | 0.612 |
| sdr_v2 | knowable | 0.966 | 0.896 | 0.580 | 0.068 | 0.316 | 0.239 to 0.400 | 0.653 |
| ser_v2 | lie | 1.000 | 0.996 | 0.783 | 0.000 | 0.213 | 0.142 to 0.295 | 0.722 |
| ser_v2 | no-lie | 0.999 | 0.996 | 0.815 | 0.008 | 0.181 | 0.060 to 0.317 | 0.640 |
| ser_v2 | knowable | 0.974 | 0.916 | 0.912 | 0.044 | 0.004 | -0.088 to 0.095 | 0.391 |

### Acts-on-it arm

Judged labels on test rows. The maintenance rate is MAINTAINED / (MAINTAINED + CORRECTED). Counts are MAINTAINED,
CORRECTED and UNCLEAR. The gap is D - I on ids where both are decided.

| task | condition | counts D | counts I | counts H | maintenance D | maintenance I | maintenance H | gap | 95% interval | paired ids | UNCLEAR share D, I, H |
|---|---|---|---|---|---|---|---|---|---|---|---|
| far_v2 | base | 2, 197, 11 | 4, 166, 40 | 1, 209, 0 | 0.010 | 0.024 | 0.005 | -0.012 | -0.043 to 0.031 | 162 | 0.05, 0.19, 0.00 |
| far_v2 | ablated | 9, 141, 60 | 18, 141, 51 | 3, 206, 1 | 0.060 | 0.113 | 0.014 | -0.067 | -0.185 to 0.000 | 120 | 0.29, 0.24, 0.00 |
| sdr_v2 | base | 8, 198, 44 | 1, 229, 20 | 0, 250, 0 | 0.039 | 0.004 | 0.000 | 0.031 | -0.005 to 0.093 | 193 | 0.18, 0.08, 0.00 |
| sdr_v2 | ablated | 9, 216, 25 | 2, 220, 28 | 0, 250, 0 | 0.040 | 0.009 | 0.000 | 0.030 | 0.005 to 0.066 | 202 | 0.10, 0.11, 0.00 |
| ser_v2 | base | 1, 205, 43 | 1, 239, 9 | 0, 249, 0 | 0.005 | 0.004 | 0.000 | 0.000 | -0.015 to 0.014 | 203 | 0.17, 0.04, 0.00 |
| ser_v2 | ablated | 13, 217, 19 | 9, 214, 26 | 0, 247, 2 | 0.057 | 0.040 | 0.000 | 0.014 | -0.039 to 0.062 | 207 | 0.08, 0.10, 0.01 |

The spread between the D and H maintenance rates is 0.005, 0.039 and 0.005, far below the 0.30 that the R2 reading
needs. The FAR ablated pass raises the UNCLEAR flag, with D at 0.29 against the 0.25 bar.

First-token proxy, frozen in `results/d2/proxy_tokens.json`. The correction lists are FAR "I", "The", "However",
"Wait" and "Actually"; SDR "I" and "Actually"; SER "I". The maintenance list is empty on every task. Agreement with
the judge on unablated decided test rows is 0.988 (579 rows), 0.987 (686) and 0.997 (695), with no undecided row. The
proxy is marked not applicable on every task (`qualifies` false, reason "empty maintenance token list").

### Judge checks (R11)

| check | rows | exact agreement | agreement where both decided | flip rate |
|---|---|---|---|---|
| Sonnet cross-check, all | 200 | 0.965 | 1.000 (179 rows) | |
| cross-check far_v2 | 50 | 0.980 | 1.000 (45) | |
| cross-check sdr_v2 | 69 | 0.913 | 1.000 (57) | |
| cross-check ser_v2 | 81 | 1.000 | 1.000 (77) | |
| re-judge, all | 213 | 1.000 | 1.000 (196) | 0.000 |

Confusion, primary label then check label:

| check | C to C | M to M | U to U | C to U | M to U | U to C |
|---|---|---|---|---|---|---|
| cross-check | 175 | 4 | 14 | 3 | 1 | 3 |
| re-judge | 191 | 5 | 17 | 0 | 0 | 0 |

The cross-check's 7 disagreements all involve UNCLEAR. The 21 rows outside "both decided" are the 14 UNCLEAR
agreements plus those 7 disagreements. No row flips between MAINTAINED and CORRECTED in either check.

### Spend and the proxy freeze

| item | value |
|---|---|
| OpenRouter spend, five ledgers, all settled | $2.7071 of the $20 cap |
| paid attempts | 4,064 |
| GPU | job 50155519, 0.70 GPU-hours (plus 158 s for the failed 50153789) |
| proxy token file sha256, recorded in spec.md before the main stage | `304ad7fa5e9963067e57f06833a03b64e2938eb6deb68dd33aadda31992302a0` |

### Caveats

- **(a) The classifier may read the instruction clause, not a lie-maintenance state.** It is trained on D against
  H. D and I both carry an operator clause and H does not, so a gate AUROC of 1.000 and I rates of 0.84 to 0.995
  are what a clause-presence reader would produce. Four observations bear on this:
  - **Not falsity alone.** H has the same forced false first answer and scores 0.000 on every task, so the
    classifier does not read the falsity of the prior answer by itself. It reads something D and I share and H
    lacks. In this design that is the clause, or the fact that the falsehood was instructed, and nothing here tells
    them apart. The R2 label "falsity state" can only mean "instructed falsity" here.
  - **Unrelated questions.** D and H separate almost perfectly on the knowable group too (gate 0.97 to 1.00).
    Those are questions unrelated to the lie, so the signal is available everywhere in the context. Pacchiardi et
    al. report lie detection from unrelated questions as well, so this does not settle the question.
  - **D against I.** This AUROC is 0.69 to 0.76, the only part of the evidence that bears on a D-specific
    component. D's and I's clauses differ in wording as well as in whom they deceive, so even that difference can
    be lexical.
  - **The refusal ablation is silent.** The refit separates D from H as perfectly as before, so the D-H marker is
    not the refusal direction. That says nothing about clause against state.
  - What would bear on it: a condition with the clause but a true forced answer, a condition with a lie but no
    clause, or the position-resolved patching of plan section 8. None was run.
- **(b) The SDR pass is narrow and stands alone.** The gap is 0.160 against the 0.15 bar, so it passes by one
  point. Its interval runs from 0.086 to 0.227, so the data cannot exclude a gap well under the bar; the pass
  rests on the point estimate. SER sits 0.5 points below the bar, where its interval (0.076 to 0.215) overlaps
  SDR's almost entirely. Only one of three tasks passes, on one arm.
- **(c) The acts-on-it null is a limit of the design, not evidence about the state.** With a forced wrong first
  answer, the model corrects itself in nearly every row of every condition, honest twin included. The arm has no
  room to separate D from I. Its null says the two-turn design under forced wrong answers cannot measure
  maintenance in this model. It says nothing about whether a maintenance state exists. The R2 reading on this arm
  is undefined, not "I patterns like H".
- **(d) Other points from `readings_final.json`:**
  - **The proxy is vacuous.** Its maintenance list is empty, so it labels every row CORRECTED when any correction
    token is present. Its agreement (0.987 to 0.997) equals the judge's CORRECTED share; on FAR, 572 of 579 rows
    is exactly 0.988. It passes the 0.85 bar numerically but cannot detect maintenance. After review 04,
    `readings_final.json` marks it `qualifies` false and `applicable` false with the reason "empty maintenance
    token list". On re-running the final read, every other field of `readings.json` is identical apart from the
    script's code hash, and `readings.md` differs only in its timestamp, so no other number moved.
  - **The plan's proxy trigger fired.** "I" opens at least 112, 125 and 188 of the 200 calibration rows (FAR, SDR, SER),
    above the one-fifth trigger of plan section 3b. So a stem-resolved proxy needs a ruling before any first-token
    proxy can serve as a patching readout.
  - **The frozen classifier is uninformative under ablation.** It calls H rows D at 0.46, 0.98 and 1.00. Ablating
    the refusal direction moves the probe answers along the classifier's D-H axis, which is why R12 made the refit
    primary. The refit has no validation gate, because no gate rows were run ablated. Its held-out D and H test
    rates (1.0 and 0.0) are the only out-of-sample check.
  - **Ablation makes I more D-like on every task** (refit I rate FAR 0.995 to 1.000, SDR 0.840 to 0.864, SER 0.855
    to 0.968). That is what "explains" SER's gap.
  - **The gap is not carried by a consistent question group.** By group, SDR's gap sits mostly in the knowable
    (0.316) and lie (0.152) groups. SER's sits in the lie (0.213) and no-lie (0.181) groups, with knowable at 0.004
    and a D-I AUROC of 0.391, below chance. FAR's appears only in knowable (0.148). The groups are descriptive and
    not corrected for multiplicity.
  - **"Refusal explains" is degenerate where the gap is near zero.** That covers FAR's classifier arm and the FAR
    and SER acts-on-it arms, where any change counts as half.
  - **D carries the most UNCLEAR labels.** Unablated, 0.17 to 0.18 on SDR and SER; ablated FAR reaches 0.29 and
    trips the flag. Among the few maintained rows, D leads on SDR (8 of 206 decided), and the SDR acts-on-it
    interval under ablation (0.005 to 0.066) excludes zero. Both are far under the 15-point rule.
  - **The I ids are the whole inversion pool on FAR (210) and SER (249).** SDR uses 250 of its 788 ids. The first
    answer is forced, so the model never chose the lie it is asked to maintain.

## What is NOT done

- Not done by this worker: the patching ruling and the independent review, which are the orchestrator's. The
  findings entry is not written either.
- No stem-resolved proxy exists. Plan section 3b's trigger fired ("I" opens more than a fifth of the calibration
  rows on every task), so one needs a ruling before any first-token proxy serves as a patching readout.
- The full repository test suite was not run; only the two D2 test files ran, on both interpreters. No existing
  file other than `.gitignore` was edited.
- Once, while checking the output files, a combined command ran `git status --short` in the worktree (read only, no
  output). The brief forbids git; no other git command ran.
- The patching payload (plan section 8) is planned only. The premise passes on SDR, so it now waits on the
  orchestrator's ruling.
- No teacher-forced stem set was built for the first-token proxy, although the brief asked for one as
  instructed-route R4 did. The proxy is calibrated from the first generated token of the judged validation
  generations. In the event, "I" reached the 80 percent majority for CORRECTED and joined the correction list on
  every task, and no maintenance token qualified (see caveat (d)). The judge is the primary readout either way.
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
