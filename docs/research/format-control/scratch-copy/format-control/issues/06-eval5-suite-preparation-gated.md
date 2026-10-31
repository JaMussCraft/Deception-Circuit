# 06 — EVAL 5 benchmark suite with D, H and F in one run (gated)

**What to build:** A dry-run-validated launch script that puts the deceptive circuit, the honest twin and the Format Circuit of each task family into one EVAL 5 suite per benchmark group, with the exact settings of the exploratory wave, and the summary hook that feeds ticket 05. Nothing is submitted until the researcher says so.

**Status:** resolved
**Type:** task
**Blocked by:** 04 (the wikitext KL gate for each F comes from its knockout cell), 05 (summary columns)

**Gate:** submit only for suites whose F knockout has wikitext KL <= 0.66 or fluent generations, and only after the researcher's explicit go-ahead in the session that runs it. The three grader caveats in `Alignment/.scratch/eval5-grader-fixes/` stay as recorded caveats and are printed in every `result_summary.md`.

**Facts to build on**
- `outputs/_eval5_launch/eval5_args.sh` prints the arguments: `--evals benchmarks --ablation interchange --benchmarks <group> --benchmark-n-per-dataset 50 --benchmark-n-random 6 --benchmark-screen-budget 600 --output-dir outputs/eval5_<name>`; groups `sm` = `sandbagging mask`, `lb` = `lb:instructed-deception lb:harm-pressure-knowledge-report lb:convincing-game`. Coarse circuits go through `_launch/submit_eval5.sh` with the `c - m` heads-only expression.
- `evaluation/benchmark_eval.py`: screen with the full model, judged-deceptive items form the eval set, configs `full`, `knockout`, `circuit_only`, `empty`, `random-i`; coherence in `evaluation/coherence.py` (`ref_nll`, `ref_ppl`, `distinct_n`); `judge_cache.jsonl` per suite. Multiple `--circuit` bindings in one invocation share the screen and the cache; the random rows are size-matched per circuit.
- Existing suites to compare against: `outputs/eval5_{far,sdr}{,_lb}`, `eval5_far_h{,_lb}` (nls0.7 honest), `eval5_sdr_h03{,_lb}`, `eval5_sdr_coarse_nls0.3_nomb{,_lb}` and `_honest_nomb{,_lb}`; each has `result_summary.md`. Framing in memory `deception-eval-framing`: interchange primary, raw deception rate the headline, unparsed counts as not lying.

- [x] `outputs/_launch_format_control/submit_eval5.sh <family> <sm|lb> [--dry]`: binds `D`, `H`, `F` in one `evaluate_circuit.py` invocation (coarse: three `c - m` expressions against `_allmlp_nomb`), same settings as `eval5_args.sh`, output `outputs/eval5_format_<family>{,_lb}`; `--dry` prints the command and runs `--dry-run`, which must pass on the login node for all six (family × group) combinations.
- [x] A pre-flight check reads each F knockout's wikitext KL from the ticket 04 suite and refuses to print a submit line for a suite that fails the gate, naming the number.
- [x] `result_summary.md` writer for the new layout (three circuits in one suite): per dataset, deception rate under interchange for full / D-knockout / H-knockout / F-knockout / random rows, `ref_nll` and `distinct_n`, the three grader caveats, and the note that random rows are size-matched per circuit while the screened items are shared.
- [ ] Ticket 05's writer consumes the directory (`--eval5-dir`) and fills the benchmark columns of the decision block.
- [x] Tests: the submit script's command generator as a pure function (bindings, groups, coarse rewriting); the gate refusal; the summary writer on a fixture suite with three circuits.
- [x] Cost estimate per suite (judge calls, GPU hours) from `--dry-run` quoted in Comments for the researcher's decision; no submission by this ticket.
- [x] Both suites in both envs; failure names vs baseline.
- [x] Independent review (orchestrator-dispatched: build phase approved, fix round 1 re-review passed; gate rounds covered by the whole-branch review); report in `reports/06-eval5-suite-preparation-gated-review.md`.

## Comments

### 2026-10-13, build phase (implementer; nothing submitted to Slurm)

**Built** (worktree `Deception-Circuit/.claude/worktrees/format-control`): `outputs/_launch_format_control/{eval5_cmd.py, submit_eval5.sh, write_eval5_format_summary.py, README_eval5.md}`, `evaluation/eval5_format_summary.py`, `tests/test_format_control_eval5.py` (47 tests), stand-in dry-run logs under `outputs/_launch_format_control/dryrun_eval5_standin/`. No file of another ticket was changed. Commits are made by the orchestrator on the implementer's instruction: db72d03.

**Command.** One invocation binds `D`, `H`, `F` with `--task-from <D run>` (mandatory: without a task flag the evaluator defaults to each circuit's own test set and would run 9 benchmark cells instead of 3). Coarse adds `--circuit m=<_allmlp_nomb>`, `--expr D_hko=D - m`, `H_hko`, `F_hko`, `--compose-granularity leaf` (cells `X_hko__leaf`; ticket 04's ruling on leaf for heads-only). Settings are `eval5_args.sh` verbatim, plus two flags that change no number: `--benchmark-screen-cache <main checkout>/outputs/_screens` (the existing suites' A40 screens; the worktree has none) and `--benchmark-repo-root /projects/beto/swong2/Alignment` (MASK/LB checkouts; the default resolves inside `.claude/worktrees` and the first probe failed on it).

**Dry-runs (stand-in, F := H, ticket 04's `standin_config` default): all six pass on the login node** (mgnp). Grid "3 circuits x 1 tasks" in every log; coarse cells `D_hko__leaf`, `H_hko__leaf`, `F_hko__leaf` with D at 8,832 fine units, matching `eval5_sdr_coarse_nls0.3_nomb`. Runtime lines show `[cached]` for all 7 sm and 3 lb datasets. The real-F dry-runs are NOT done (F is null in `suites.json`): box 1 stays open.

**Gate.** `eval5_cmd.py gate <family>` reads `knockout.json` `headline.wikitext_kl` (else `wikitext.discovered.kl_per_token`) of F's knockout cell on the D and the F test set (manifest `cells` index, circuit `F` or `F_hko__leaf`); refuses on a missing cell, a missing KL, or KL > 0.66, naming cell and number. Tested pass / fail / missing / no-KL / coarse. Not yet run on real cells (ticket 04's cells do not exist): box 2 stays open. The "or fluent generations" route is left to the researcher; the refusal points at `generation.examples`.

**Refusals** (`submit_eval5.sh` without `--dry`, exit 3, in order): F null; gate; `FORMAT_CONTROL_EVAL5_GO=1` absent; then a passing `--dry-run` of the same arguments. `--dry` needs no go-ahead and prints the sbatch line only if F is set and the gate passes. `--standin` never gets a submit line. Script tests use a stub `sbatch` first on PATH.

**Cost estimate for the researcher (STAND-IN, F := H; F's size changes the random draws, not the counts).** Judge calls: upper bound over knockout, circuit_only, empty and 6 randoms per cell, with the existing suites' post-screen n; `full` reuses the screen; cached screens add 0.

| suite | judge calls | GPU h (dry-run floor - ceiling) | --time (ceiling x 1.5) |
| --- | ---: | --- | --- |
| `eval5_format_{far,sdr,sdr_coarse}` (sm), each | 4,671 | 24.3 - 29.6 | 44:30:00 |
| `eval5_format_{far,sdr,sdr_coarse}_lb`, each | 4,050 | 9.2 - 12.5 | 19:00:00 |
| all six | 26,163 | 100.5 - 126.3 | |

The dry-run estimate is pessimistic: the one-cell coarse sm suite it rates near 10 h ran in 3 h 51 min, so a three-cell sm suite is plausibly 10 to 12 h on an A40. The one-cell judge count of that suite (1,376 writes + 181 hits = 1,557) is exactly a third of 4,671.

**Researcher decision: partition.** The cached screens were made on NVIDIA A40 and the GPU is in the cache key, so the launcher defaults to `gpuA40x4`. Any other partition re-screens (and writes into the main checkout's `_screens`), and the items stop matching `eval5_far`, `eval5_sdr`, `eval5_sdr_h03`, `eval5_sdr_coarse_*`. This narrows the brief's "any partition".

**Summary writer.** `write_eval5_format_summary.py <suite>` writes `result_summary.md` and `eval5_format.json` (numbers by role). Checked on symlinked real cells: the coarse cell's numbers match the hand-written `eval5_sdr_coarse_nls0.3_nomb` summary (mean Δ +0.100; fine D +0.320, H +0.296), the full row is identical across three real suites, and the caveat counters reproduce the recorded rows (2 empty generations on `eval5_sdr_lb` D, 1 guard row on the coarse LB knockout).

**Ticket 05.** Its existing `load_eval5` already reads this layout (fine and coarse labels; checked on the smoke suite: D, H, F, 7 datasets each). Pass `--eval5-dir outputs/eval5_format_<family> --eval5-dir outputs/eval5_format_<family>_lb`. Box 4 stays open until it runs on real suites.

**Tests.** `tests/test_format_control_eval5.py` 47 passed in both envs. Full suite: base 8 failed, 786 passed, 20 skipped; mgnp 8 failed, 787 passed, 19 skipped. The 8 names are exactly the baseline's, in both envs; no new failure.

**Independent review:** not run in this dispatch (orchestrator instruction); box 8 open.

**Pre-existing quirk, not fixed (evaluate_circuit.py, not this ticket's file):** the dry-run's "Screen cache:" listing builds the key without the model and prints "nothing cached", while the runtime lines, which include the model, say `[cached]`.

### 2026-10-13, fix round 1 (review I1-I3 plus the orchestrator's rulings; nothing submitted)

- **I1:** the grader caveats are now exact quotes with source paths. Caveats 1 and 2 quote tickets 01 and 02. Caveat 3 is labelled "NO TICKET" and quotes the project memory note `eval5-grader-fixes-pending.md` (item 3) and `eval5_sdr_coarse_nls0.3_nomb_lb/result_summary.md`. A test compares every quote with its source file.
- **I2:** the gate refuses unless the manifest's planned F and each F knockout cell's `summary.json` operand equal the F that `suites.json` names now. A stale cell from another F run is refused, naming both paths.
- **I3 and the no-writes ruling:** the evaluator reads a worktree-local copy of the main checkout's A40 screens, at `outputs/_eval5_format_cache/screens` (copied, never linked; git-ignored). After the dry-run the launcher refuses on any uncached dataset, a non-A40 screen in the copy, or a non-A40 partition, unless `--allow-rescreen "<reason>"` is given; the reason is recorded. A test asserts that no path in the command lies under the main checkout's `outputs/` except the read-only run directories. The six stand-in dry-runs were re-run and all pass with every screen an A40 cache hit. The main checkout's `_screens` listing is unchanged.
- **A40 default:** kept and documented as keeping the screened items comparable with the existing suites; other partitions re-screen.
- **Gate override:** `--gate-override "<reason>"` clears only the KL bar, and is recorded in `eval5_record.json` with the numbers it overrode. Missing cells, missing KLs and stale F cells are never overridable.
- **Minor findings:** M1, M2, M3, M4, M6, M8, M10 and M12 are fixed. M7, M9 and M11 are documented in the README. M5 is ticket 05's file.
- **Tests:** 75 in the ticket file pass in both envs. Full suite: base 8 failed, 817 passed, 20 skipped; mgnp 8 failed, 818 passed, 19 skipped. Both sets of failures are exactly the 8 baseline names.
- **Details:** the fix-round section of `reports/06-implementer-report.md`.


- 2026-10-13 orchestrator: session stopped at its usage limit with this ticket in progress; see reports/00-orchestration-ledger.md for the exact remaining steps.

### 2026-10-15, SDR resume: real gate and real dry-runs (nothing submitted; FORMAT_CONTROL_EVAL5_GO unset)

**Gate, on ticket 04's merged suites** (`eval5_cmd.py gate`). Both cells of each family were produced by the F that `suites.json` names; the F-identity check passed.

| family | F knockout cell | wikitext KL | verdict |
| --- | --- | ---: | --- |
| sdr | `cells/F/sdr`, `cells/F/sdr_nopressure` | 1.342 | **REFUSED**: "F knockout wikitext KL 1.342 > 0.66 ... fails the eval 2 gate" (exit 3) |
| sdr_coarse | `cells/F_hko__leaf/sdr`, `cells/F_hko__leaf/sdr_nopressure` | 0.279 | passed |

**SDR fine F knockout, for the researcher's fluency ruling.** The perplexity ratio is 3.80, against a null median KL of 0.55. Two of the three wikitext knockout generations degenerate into runs of quotes and ellipses. Example: ` in 1967 in the film "  The Man Who ...  " , a " ...  " ...  " ...`. By my reading they are not fluent. The spec reads an incoherent Format Circuit knockout as outcome (c): retrain at lower NLS. The ruling is the researcher's, and `--gate-override` is the only route past it.

**Real `--dry` runs** (login node, mgnp, the worktree-local A40 screen copy, every screen `[cached]` and A40-cleared):

| suite | dry-run | judge calls (upper bound) | GPU h (floor - ceiling) | --time | submit line |
| --- | --- | ---: | --- | --- | --- |
| sdr_coarse sm | pass | 4,671 | 24.3 - 29.6 | 44:30:00 | printed, not run |
| sdr_coarse lb | pass | 4,050 | 9.2 - 12.5 | 19:00:00 | printed, not run |
| sdr sm | pass | 4,671 | 24.3 - 29.6 | | **refused** (gate, KL 1.342) |
| sdr lb | pass | 4,050 | 9.2 - 12.5 | | **refused** (gate, KL 1.342) |

Cells: coarse D_hko 8,832 units, H_hko 7,168 and F_hko 8,704, with `m` the worktree operand. Fine D 11,251, H 8,732 and F 11,882. Every grid is "3 circuits x 1 tasks". The main checkout's `outputs/_screens` listing is identical before and after. Logs are under `outputs/_launch_format_control/dryrun_eval5/`, and every run is in `eval5_record.json`. FAR's two real dry-runs await its cells, so box 1 stays open at 4 of 6.

**Two launcher fixes found by the real runs (test-first; 76 tests pass in both envs):**
- **Operand name.** Ticket 04 now builds the coarse all-MLP operand as `outputs/_launch_format_control/allmlp_nomb`, without a leading underscore. My signature check parsed the name and refused it. It now reads the operand's own masks. Those masks are identical to the main checkout's `_allmlp_nomb`, which the existing coarse suites used: all five arrays are equal, plus a `built_from` field. The first coarse dry runs (sm, lb) were refused for this reason before the fix.
- **Record race.** The SDR and coarse dry runs wrote `eval5_record.json` at the same time, and one event was lost: the first coarse sm run, which was refused for the operand-name reason. `record_event` now holds an flock (the Lustre mount has `flock`); a four-process test checks that no event is lost. The lost event is not reconstructed.

**Process slip.** I ran one read-only `git log` on `suites.json` despite the no-git rule. Nothing was changed.

**Full suite after these fixes:** base 8 failed, 844 passed, 20 skipped; mgnp 8 failed, 845 passed, 19 skipped. Both sets of failures are exactly the 8 baseline names. A first mgnp run also failed 47 tests in ticket 05's `tests/test_format_control_summary.py`. Ticket 05's `evaluation/format_control_summary.py` was rewritten at 07:17:32, during that run, which ended at 07:17:43. Re-run alone, that file passes 52 of 52, and the clean full mgnp run above followed.


### 2026-10-15, FAR resume and closing (nothing submitted; FORMAT_CONTROL_EVAL5_GO unset)

**FAR gate** (`eval5_cmd.py gate far`, exit 3): REFUSED, "F knockout wikitext KL 4.265 > 0.66" on `cells/F/far` and `cells/F/far_nopressure`. Both cells are the configured F's (`nls0.3_nopressure_noedge_261013-203424`). The NLS 0.4 side job under `_side_F04/` (KL 2.317) is outside the manifest's cells index and was not read. **FAR real dry-runs:** sm and lb both pass on the evaluator side, with every screen an A40 cache hit on the local copy, and neither prints a submit line. Fine units: D 5,436, H 10,935, F 12,986; grid 3 x 1. The main checkout's `_screens` listing is unchanged.

**Box 1 ticked:** all six real `--dry-run`s pass on the login node: far, sdr and sdr_coarse, each sm and lb.

#### Per-family gate (eval 2 wikitext KL of each knockout; the gate reads F)

| family | D KO KL | H KO KL | **F KO KL** | F ppl ratio | gate | eval 2 verdict (ticket 05) | EVAL 5 submit line |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| FAR fine | 0.327 | 2.784 | **4.265** | x69.7 | **refused** | (c) | none |
| SDR fine | 1.383 | 0.694 | **1.342** | x3.80 | **refused** | (c) | none |
| SDR coarse (heads-only `X - m`) | 0.364 | 0.275 | **0.279** | x1.31 | **passes** | (a) | printed for sm and lb, not run |

The F knockout generations differ sharply. FAR's are token salad (`riverHeaderCodeHeaderCode_Tis ... _marshall_marshall`). SDR fine's degenerate in 2 of 3 cases (`" ...  " ...`). Neither reads as fluent.

#### Cost of the one family that passed (sdr_coarse; real dry-runs; upper bounds)

| suite | judge calls | GPU h (dry-run floor - ceiling) | default --time | anchored wall time |
| --- | ---: | --- | --- | --- |
| `eval5_format_sdr_coarse` (sm) | 4,671 | 24.3 - 29.6 | 44:30:00 | about 10-12 h on an A40 (the one-cell coarse suite ran 3 h 51 min) |
| `eval5_format_sdr_coarse_lb` | 4,050 | 9.2 - 12.5 | 19:00:00 | a few hours |
| both | 8,721 | 33.5 - 42.1 | | |

All screens are cached, so no screen judge calls. The judge-call counts are upper bounds; the cache dedups repeats.

#### Recommended next decision for the researcher

1. **SDR coarse: launch, if you want the benchmark test of verdict (a).** It is the only family whose Format Circuit knockout is coherent (KL 0.279, below D's 0.364). Eval 2 already reads it as (a), "format explains it". EVAL 5 would check whether F's knockout also matches D's deception drop on sandbagging, MASK and Liars' Bench at equal or lower NLL cost, on the same screened items as `eval5_sdr_coarse_nls0.3_{nomb,honest_nomb}`. To launch, give the go-ahead in the session, record it here, and run `FORMAT_CONTROL_EVAL5_GO=1 bash outputs/_launch_format_control/submit_eval5.sh sdr_coarse sm` (and `lb`) on gpuA40x4.
2. **FAR and SDR fine: no EVAL 5; follow outcome (c).** The pre-registered response is to retrain the Format Circuit at a lower NLS, never to reinterpret. Two facts bear on that:
   - **Direction of the retrain.** On FAR, the NLS 0.4 retune side job gave KL 2.317, lower than 4.265 at 0.3 but still failing. Check which NLS direction shrinks the knockout's collateral before retraining.
   - **SDR fine's own D is above the bar.** D's knockout is 1.383, so the bar refuses D as well as F, and F is no less coherent than D. The spec gates F only. Whether "matched incoherence" justifies `--gate-override` is a judgement this ticket does not make; the generations argue against "fluent".
3. **No override is recommended.** Neither failing family's generations read as fluent, and the override exists only for that case.

Open: box 4 (ticket 05 consuming real EVAL 5 suites) needs a launched suite. Box 8 is the orchestrator's (build-phase review plus scoped re-review). Status stays `claimed`, since EVAL 5 itself waits on the researcher.

### 2026-10-15, whole-branch review I2 (worktree paths)

**Keep the format-control worktree until EVAL 5 has run.** Its F runs, the coarse `allmlp_nomb` operand and ticket 04's cells all record worktree paths. Alternatively, repoint `suites.json` (F and `allmlp`) to the merged location while the worktree still exists. The gate now treats a run at another path as the same F when its masks and `deception_condition` are identical, but it has to read the recorded run directory to compare them. Once the worktree is removed, the gate refuses with "cannot compare masks ... keep the format-control worktree". `suites.json` paths are unchanged.

#### Researcher go-ahead (recorded 2026-10-16, orchestrator job f037b43a)

The researcher (James Wong), in the session that submits, wrote: "I would like to do eval5 on D, H, F, and D-F." Family: `sdr_coarse` (the only family passing the gate; F knockout wikitext KL 0.279). Groups: `sm` and `lb`. The fourth circuit D−F (coarse: `(D - F) - m`, 33 heads; eval 2 knockout 0.119 vs null p5 0.517) is bound in the same invocation as D, H, F so all four share one screen and one judge cache. Partition gpuA40x4 (screen comparability). The researcher asked not to monitor the jobs; they will check tomorrow. `FORMAT_CONTROL_EVAL5_GO=1` is set by the orchestrator only for the two submit commands, after this entry.

#### Outcome (2026-10-18)

Both suites ran (lb 22947270 sound; sm 22947260 generated but 6,032 scoring judge calls failed with OpenRouter HTTP 402 after the key's credits ran out). Recovery is the judge-only `rejudge_benchmarks.py` (commit f4e50f7; README_eval5.md "PENDING" section), pending a credit top-up by the researcher's advisor. Box 4 (ticket 05 consuming real EVAL 5 suites) stays open until the re-score; the lb suite alone already shows F's knockout matching D's deception drop and D−F inert on Liars' Bench.
