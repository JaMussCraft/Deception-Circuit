# Current artifact audit — 2026-10-18

Read-only artifact/Slurm audit; no APIs, model loading, notebooks, jobs, git mutation or tests executed. Only this /tmp report written. Paths below relative to `R=/projects/beto/swong2/Alignment/Deception-Circuit` unless absolute. Current parent main is specified as 9d9c2a9.
## Canonical masks

D/H/F all Llama-3.1-8B-Instruct SDR coarse heads-only NLS0.3 seed42. Expanded masks include all32 unpruned MLPs; always compose leaf and subtract all-MLP operand. Do not use raw masks for a whole-circuit knockout. Expanded config neuron flags were changed by expansion; `config.coarse.json` preserves original pruning geometry.
- D: `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/nls0.3_noedge_noan_nomh_nomo_nomb_260922-092742` — 69 heads. Main F active/config/coarse mask are byte-identical to WT source still named by suites.json.
  - `active_nodes.json` SHA256 `09f2f5f6f7add2917f3778a6d24293f7710ccc350b8773322dbe645bd4c89c41`
  - `active_nodes.coarse.json` SHA256 `110a7a87bd2bf5dc9abdffa6d0efed20549b0dd4b2319ebfb0f57cdc8126c536`
  - `config.json` SHA256 `388cb80d5132567881110cee0a9d7b87d8bbf5cff1ad00748fec082e40b830b9`
- H: `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/nls0.3_honest_noedge_noan_nomh_nomo_nomb_260922-092743` — 56 heads. Main F active/config/coarse mask are byte-identical to WT source still named by suites.json.
  - `active_nodes.json` SHA256 `87b14ba212a050c79940833f3558eb64ffa33550ee2288bc2592b32335eac992`
  - `active_nodes.coarse.json` SHA256 `98abc1f4c97a54b6f70aa53b62c999428c619bb2cfb851c008909c94f5413562`
  - `config.json` SHA256 `c9a9a4629cbcef2c5efba86af18c0147fc8a94d06932df01f1b5da32ea485911`
- F: `/projects/beto/swong2/Alignment/Deception-Circuit/outputs/llama-8b-instruct_sdr_coarse/nls0.3_nopressure_noedge_noan_nomh_nomo_nomb_261013-204850` — 68 heads. Main F active/config/coarse mask are byte-identical to WT source still named by suites.json.
  - `active_nodes.json` SHA256 `bcb045b9f7ec7faacec2787875f58076d056baeeb8530262021b9c48192366af`
  - `active_nodes.coarse.json` SHA256 `833aceb454d7bba6c1e049c9a0ce95d07369e948193fb64d765b02ac6cf3fa06`
  - `config.json` SHA256 `a50abfa15ebff64be4e7fb63f6d4b72c829a9e43e51da2241e1772f6afa6ca3c`
- m: `outputs/llama-8b-instruct_sdr_coarse/_allmlp_nomb` (used by D∩H component analysis); format-control equivalent `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control/outputs/_launch_format_control/allmlp_nomb`.
- D∩H: `(D & H) - m`, **leaf**; 43 heads; SHA256 of JSON sorted list with compact separators `ac748d9a356cb25340f959558020136d5b75cd7f2c6d89f42ee4de5c10273fa4`. Heads: L7H1, L7H2, L7H23, L7H29, L8H0, L8H1, L8H6, L8H8, L8H9, L8H11, L8H14, L9H20, L9H26, L9H28, L9H31, L10H1, L10H2, L10H3, L10H28, L11H8, L11H12, L11H13, L11H14, L12H4, L12H6, L12H7, L12H13, L12H28, L13H5, L13H18, L13H20, L13H21, L14H4, L14H5, L14H23, L14H24, L17H24, L17H26, L24H16, L24H17, L24H18, L24H26, L24H27.
- D∩H∩F: `(D & H & F) - m`, **leaf**; 32 heads; SHA256 of JSON sorted list with compact separators `7dd3a8b14885d00e26dc8fe6a5897feac8ff978d52e4b1a749170f105ffb74c9`. Heads: L8H0, L8H1, L8H8, L8H9, L8H11, L8H14, L9H20, L9H26, L9H28, L9H31, L10H1, L10H2, L10H3, L10H28, L12H4, L12H6, L12H7, L12H13, L12H28, L13H5, L13H18, L13H20, L13H21, L14H4, L14H5, L14H23, L14H24, L17H24, L17H26, L24H16, L24H26, L24H27.
- (D∩H)−F: `((D & H) - F) - m`, **leaf**; 11 heads; SHA256 of JSON sorted list with compact separators `d0e7e6a8d399009fc14716f4c3166619b7cd2044cd852c7f8d3c1004231c8a5a`. Heads: L7H1, L7H2, L7H23, L7H29, L8H6, L11H8, L11H12, L11H13, L11H14, L24H17, L24H18.

## Existing cells and usable data

D∩H canonical component cell: `outputs/_analyses/sdr-dh-core/dh_core__leaf/sdr/`; honest counterpart `outputs/_analyses/sdr-dh-core-honest/dh_core__leaf/sdr/`; all-model KO sweep `outputs/_analyses/sdr-dh-core-kosweep/dh_core__leaf/sdr/`. These are now under main, not the deleted component-analysis worktree. `head_table.json` meta confirms43 heads/0MLPs/10layers and operand provenance.

D∩H sample: `sample.json`, test, n100, seed0, balanced across8 designation×item×template strata (identity52/inversion48; item50/50; audit50/lab50). SHA256 `63ede26d657b6c1a9d3be4c4daa79df3d48619bc781d491695d283227e556a55`. Join by instance_id, not pre-tokenization split index. `knockout/knockout.json`: clean margin1.6131697845, accuracy1; `knockout/knockout_families.json`: joint43 KO margin−1.6051, accuracy.01. `dla/dla.json` sources say honest instruction comes from `data/datasets/sdr/matched_honest_survivors.json` and **clean** stream:71/100 paired,29 missing. Descriptive pressure1000 and honest twin1000 are different coverage from paired71/causal100. H sample is independently drawn and not paired with D.

Triple-core prior cell: `.claude/worktrees/format-control/outputs/_suites/format-control-sdr-coarse-nls0.3/cells/D_and_H_and_F_hko__leaf/sdr/interchange/`. Summary confirms32 heads/4096 neurons/0MLP fine units/8layers. KO headline accuracy.002, wikitext KL.1149290, runtime309.9s; null20 task accuracy p5.38365. Wikitext floor_ok false due bf16 floor. Source knockout SHA256 `01e70ac16eb7c1d3ff2b66e5f7e05d368685b4213200e1b898b25f7d085bb91e`. This is an evaluated expression, not a standalone trained run with its own active_nodes/config.

Actual Arrow files read without model:
- `data/datasets/sdr/train/data-00000-of-00001.arrow`: n200; SHA256 `75b433676df75b89c0a0df9e7f763fd7a10b77b7cd81591b29e9790ef3a6c44b`.
- `data/datasets/sdr/validation/data-00000-of-00001.arrow`: n200; SHA256 `1f4687f180c80c81d633008f87dba6d5ced4835975cb480268057fd2c7d4aab2`.
- `data/datasets/sdr/test/data-00000-of-00001.arrow`: n1000; SHA256 `86b232f0cc2d0bada1e9c61c4bbd4b036e07410f5a483e1dd5baa73f5e5ae7a7`.
- `data/datasets/sdr_honest/train/data-00000-of-00001.arrow`: n200; SHA256 `a90291d34f0d51c6b533d144f3dba6438bf7f921304988c2e9189dcef51ffd88`.
- `data/datasets/sdr_honest/validation/data-00000-of-00001.arrow`: n200; SHA256 `a39f54da106379f997a337f74b44d467f149ce278249db2b810a245967088e16`.
- `data/datasets/sdr_honest/test/data-00000-of-00001.arrow`: n1000; SHA256 `094e69115412c5ac94e1827c51e7b3a98fcb68bf917a15b963131d389b2b526a`.
- `data/datasets/sdr_nopressure/train/data-00000-of-00001.arrow`: n150; SHA256 `c8c74ec290759084963e3c0707bdf2aa8cc901076a14ca2aa331c66d3ba80c55`.
- `data/datasets/sdr_nopressure/validation/data-00000-of-00001.arrow`: n150; SHA256 `c66f405f13f6e3b5d62413f59ad3f55ab333f3e5469dc313d29f195234d806fe`.
- `data/datasets/sdr_nopressure/test/data-00000-of-00001.arrow`: n520; SHA256 `901a2756f68939aaeaefdae2db289d0d584fd4cc0ddf77b2140cd99ac396fe7d`.

Within each dataset train/val/test instance IDs are disjoint. D and H test IDs overlap0. F test520 consists of selected D-source rows, and is not all1000 D rows. F train/val150/150 (config requests200 each), with honest-source fallback44/54; source margin relaxed.7→.5→.3, final margin.3; met_minimums false recorded before fallback. F dataset is derived via stored pressure-clause deletion, swaps D-source labels to honest, retains pressure_id. Main and WT test Arrow copies byte-identical for all three conditions.

Recommendation for cheap Stage1: reuse43-head D∩H mask and existing sample IDs, evaluate paired pressure vs honest-instruction on the surviving71 clean-counterfactual pairs; record exclusions rather than compare independent H sample. Triple32 is a small optional comparator. Use held-out split and avoid rerunning EVAL1–5 or full path grids; known43 joint KO saturates so group/single or mechanism-directed diagnostic is more informative. Preserve labels/paired coverage and use new output directory.
## EVAL5 live state

Sources: `.claude/worktrees/format-control/outputs/eval5_format_sdr_coarse{,_lb}/cells/*/sdr/interchange/benchmarks.json`, suite.log, LB result_summary/eval5_format.json.

sm unscored verified now: D1480 + H1518 + F1519 + D−F1515 =6032 raw `judge-failed` entries; suite.log contains6032 explicit `judge call failed ... Error code:402` lines. No cell has a rejudge block. All4 generated benchmarks.json, no failed_datasets, so successful process completion is not scoring success. Do not quote sm depletion-contaminated deception rates. Recovery remains judge-only but is paid and outside this task.

LB scored on same50 screened items per each of3 datasets,6 random sets per circuit; mean raw-deception full1.000/D.193/H.180/F.107/D−F.753. Per dataset D/H/F/D−F KO: instructed .06/.12/.04/.72; harm-pressure .32/.32/.22/.68; convincing .20/.10/.06/.86. Eight raw judge-failed entries total across4 files, recorded as empty-completion issue, not402 (no explicit402 failure in log). Known correct-string guard clips honest counts, refusal/unparsed often drives raw-deception drop; convincing-game KO honest fractions0 for all roles.
## Verified Slurm anchors and smoke commands

`sacct -X` read today confirms all COMPLETED,1GPU,1CPU,64GB:

| job | purpose | partition | elapsed | requested limit |
|---|---|---|---|---|
|22899541|D∩H attention+DLA+43singleKO|A40interactive|15:08|45:00|
|22899542|honest task descriptive+KO|A100interactive|04:36|30:00|
|22899543|1056-component KO sweep|H200interactive|09:33|59:00|
|22899733|43-head familyKO+singles|A40interactive|03:16|20:00|
|22945674|H∩F,H−F,triple eval2|H200interactive|17:57|1:00:00|
|22947260|format sm|A40|14:26:51|22:00:00|
|22947270|format LB|A40|02:46:17|10:00:00|

Script `scripts/analyze_components.sbatch` defaults4h,1GPU64GB, mgnp, relative paths from SLURM_SUBMIT_DIR; override explicit time before script. Main logs `logs/analyze_components_2289954{1,2,3}.out` and22899733 show bf16/SDPA model. Budget on reserved GPU-hours, not observed elapsed; a4h default violates small Stage1. Parent later expanded total cap20h; keep initial diagnostic small and track retries.

CPU smoke (not run by this auditor):
```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_component_analysis.py tests/test_analyze_components_end_to_end.py tests/test_analyze_components_registry.py -q -p no:cacheprovider
```
These tests use tiny fixtures/stubs and test no-model boundaries; no model load needed. Repeat with `/sw/external/python/anaconda3/bin/python` for base env. For real-mask CPU intake, `analyze_components.py --circuit D=<canonicalD> --circuit H=<canonicalH> --circuit m=<canonicalm> --expr "dh=(D & H) - m" --compose-granularity leaf --task-from <D> --data-dir <absolute-main-data> --n-causal 100 --seed 0 --analyses knockout --dry-run --output-dir /tmp/<new-dir>`; dry-run loads no model **but writes head_table/segmentation/sample**, so never target old cell.

Baseline source `.scratch/format-control/reports/00-baseline-failures.md` under Alignment lists8 from old worktree; primary main now7 because MASK path passes there. New worktree may retain location MASK failure. Remaining7 names: `test_three_specs_registered`; `test_pressure_pools_are_well_formed[ser]`; `test_clauses_never_reuse_an_item_word_or_a_predicate_word[far|sdr|ser]` (3); `test_length_matching_narrows_the_cross_task_median_gap`; `test_hyperparameters_are_identical_across_the_three_mechanisms`. EVAL5 seven location assertions retired9d9c2a9. Auditor did not rerun full suite or assert a fresh test result.
