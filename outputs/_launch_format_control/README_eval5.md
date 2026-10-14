# Format-control EVAL 5 (ticket 06): D, H and F on one screen

**Nothing here has been submitted.** EVAL 5 is launched only on the researcher's
explicit go-ahead (`FORMAT_CONTROL_EVAL5_GO=1` in the session that submits), and
only for a family whose Format Circuit knockout passes the eval 2 gate.

One suite per task family and benchmark group. The deceptive circuit **D**, its
Honest Twin **H** and the Format Circuit **F** are bound in ONE
`evaluate_circuit.py` invocation, so their knockouts run on the identical
screened items, against one judge cache, under identical settings. The random
rows stay size-matched per circuit.

| family | circuits | output (sm / lb) |
| --- | --- | --- |
| `far` | `D`, `H`, `F` (fine nls0.3) | `outputs/eval5_format_far`, `outputs/eval5_format_far_lb` |
| `sdr` | `D`, `H`, `F` (fine nls0.3) | `outputs/eval5_format_sdr`, `outputs/eval5_format_sdr_lb` |
| `sdr_coarse` | `D_hko`, `H_hko`, `F_hko` = `X - m` (heads only, MLPs intact) | `outputs/eval5_format_sdr_coarse`, `outputs/eval5_format_sdr_coarse_lb` |

Groups: `sm` = `sandbagging mask` (7 datasets), `lb` =
`lb:instructed-deception lb:harm-pressure-knowledge-report lb:convincing-game`.

## Files

| file | what |
| --- | --- |
| `eval5_cmd.py` | the pure command generator, the gate, the refusals, the dry-run parser and cost estimate; CLI `args`, `check`, `gate`, `sbatch`, `cost` |
| `submit_eval5.sh` | `<family> <sm\|lb> [--dry] [--standin]`: the only thing that can submit |
| `write_eval5_format_summary.py` | CLI over `evaluation/eval5_format_summary.py`: `result_summary.md` + `eval5_format.json` |
| `dryrun_eval5/<family>_<group>.log` | login-node `--dry-run` logs of the real suites |
| `dryrun_eval5_standin/<family>_<group>.log` | plumbing-only dry-runs with F := H (build phase) |
| `eval5_jobs.txt` | one line per submitted job (none yet) |

Run D, H and F come from ticket 04's `suites.json` (the one configuration
point); the coarse all-MLP operand `m` too. The gate reads ticket 04's
`suite_manifest.json` and its suites under `outputs/_suites/`.

## Settings

Exactly `outputs/_eval5_launch/eval5_args.sh` (main checkout): `--evals benchmarks
--ablation interchange --benchmark-n-per-dataset 50 --benchmark-n-random 6
--benchmark-screen-budget 600`. Added, neither changing a number:

- `--task-from <D run>`. Mandatory: with no task flag the evaluator defaults to
  every bound circuit's own test set, and D, H, F have three conditions, so it
  would run a 3 x 3 grid of benchmark cells. The task does not enter EVAL 5 (the
  corrupt stream comes from the benchmark), it only names the cell directory.
- `--benchmark-screen-cache /projects/beto/swong2/Alignment/Deception-Circuit/outputs/_screens`.
  The existing `eval5_*` suites read their screens from there; the worktree has
  none. Reading them puts D, H and F on the same items as `eval5_far`,
  `eval5_sdr`, `eval5_sdr_h03`, `eval5_sdr_coarse_nls0.3_*`. The screens were
  made on **NVIDIA A40** and the GPU is part of the cache key, hence the
  default `--partition gpuA40x4`. On another GPU every screen is repaid (and
  written into that cache directory) and the items are no longer comparable
  with the existing suites. The dry-run's runtime lines say `[cached]` for all
  7 + 3 datasets; its "Screen cache:" listing says "nothing cached" only because
  it builds the key without the model name (pre-existing evaluator quirk).
- `--benchmark-repo-root /projects/beto/swong2/Alignment`. MASK and Liars' Bench
  are checked out beside the main checkout; the default resolves them relative
  to the code, i.e. inside `.claude/worktrees/`. Not part of the screen-cache key.

## The gate and the refusals

`submit_eval5.sh` without `--dry` refuses, exit 3, naming the reason, unless all hold:

1. F is configured in `suites.json` (not null).
2. The pre-flight gate: the wikitext KL of F's knockout is `<= 0.66` in BOTH
   ticket 04 cells, F on the D test set and F on its own (`nopressure`) test
   set, found through `suite_manifest.json`'s `cells` index (`roles` contains
   `knockout`, circuit `F` or `F_hko__leaf`). The KL is `knockout.json`
   `headline.wikitext_kl` (else `wikitext.discovered.kl_per_token`). A missing
   cell, a missing KL, or a KL above the bar is a refusal that names the cell
   and the number. The spec's alternative, "or fluent generations", is the
   researcher's call: the refusal points at `generation.examples` in that
   `knockout.json`. This launcher has no override switch: a fluency ruling is
   the researcher's, recorded in the ticket, and acted on by them.
3. `FORMAT_CONTROL_EVAL5_GO=1` is set.
4. A `--dry-run` of these exact arguments passes (run by the script itself).

`--dry` needs no go-ahead: it prints the command, runs the dry-run, prints the
cost, and prints the sbatch line only when 1 and 2 hold ("no submit line" and
the reasons otherwise). `--standin` (F := H, ticket 04's `standin_config`
default) never gets a submit line.

```
# build phase (done): plumbing with F := H
bash outputs/_launch_format_control/submit_eval5.sh far sm --dry --standin
# once ticket 03's F runs are in suites.json and ticket 04's knockout cells exist
python outputs/_launch_format_control/eval5_cmd.py gate far
bash outputs/_launch_format_control/submit_eval5.sh far sm --dry
# only on the researcher's go-ahead
FORMAT_CONTROL_EVAL5_GO=1 bash outputs/_launch_format_control/submit_eval5.sh far sm --account bgrb-delta-gpu
```

`--time` defaults to the dry-run ceiling x 1.5 in quarter hours (ticket 04's rule):
`44:30:00` for `sm`, `19:00:00` for `lb`. The dry-run's estimate is pessimistic:
the one-cell coarse suite it rates at ~10 h ran in 3 h 51 min.

## Cost (stand-in dry-runs, 2026-10-13; F := H)

Per suite, 3 cells. Judge calls are an upper bound on the ablated configurations
(knockout, circuit_only, empty, 6 randoms per cell; `full` reuses the screen),
using the item counts of the existing suite on the same screens; the judge cache
dedups repeats. Screens cached: 0 screen judge calls.

| suite | judge calls | GPU hours (dry-run floor - ceiling, 1 GPU) |
| --- | ---: | --- |
| any family, `sm` | 4,671 | 24.3 - 29.6 |
| any family, `lb` | 4,050 | 9.2 - 12.5 |
| all six | 26,163 | 100.5 - 126.3 |

Anchored on wall time: the one-cell `eval5_sdr_coarse_nls0.3_nomb` (sm) ran
3 h 51 min with cached screens, so a three-cell `sm` suite is plausibly about
10 to 12 h on an A40. Its one-cell judge count (1,376 writes + 181 hits = 1,557)
is exactly a third of the 4,671 above.

## The summary and the interface for ticket 05

After a suite finishes:

```
python outputs/_launch_format_control/write_eval5_format_summary.py outputs/eval5_format_far outputs/eval5_format_far_lb
```

writes into each suite `result_summary.md` (per dataset: deception / honest /
unparsed rate under interchange for full, D / H / F knockout and D / H / F random
mean, dec/parsed, `ref_nll`, `distinct_n`; Δ and null percentile per circuit;
screen notes; the three grader caveats verbatim with the knockout rows matching
each trigger; the note that random rows are size-matched per circuit while the
screened items are shared; missing cells and failed datasets reported, not
raised) and `eval5_format.json`.

**Ticket 05 needs no new code.** Its `load_eval5` already reads
`<dir>/cells/<label>/<task>/<ablation>/benchmarks.json` and maps `<label>` to a
role by stripping `__leaf|__head` then `_hko`, which gives D, H, F for both
`D`/`H`/`F` (fine) and `D_hko__leaf`/... (coarse). Pass both groups:

```
--eval5-dir outputs/eval5_format_<family> --eval5-dir outputs/eval5_format_<family>_lb
```

(checked on a symlinked stand-in suite of real cells: D, H, F all found, 7
datasets each). For a reader that prefers one file, `eval5_format.json` is:

```
{"schema": "eval5_format/1", "suite_dir": ..., "datasets": [names],
 "missing": [roles without a cell],
 "roles": {"D"|"H"|"F": {"label": cell label or null, "missing": bool, "source": path,
            "failed_datasets": {name: error}, "judge": {...}, "resolved": {...},
            "datasets": {name: {"n": int, "screen": {...},
                                "full" | "knockout" | "random_mean":
                                   {"deceptive", "honest", "unparsed", "dec_parsed",
                                    "ref_nll", "distinct_n", ...},
                                "null_percentile", "null_p_value",
                                "caveat_hits": {"empty_generation", "mask_verdict_d",
                                                "lb_correct_guard"}}
                         | {"error": str}}}},
 "grader_caveats": [{"key", "title", "text", "source"}], "random_rows_note": str}
```

`evaluation.eval5_format_summary.tabulate(load_suite(dir))` returns the same
dict without writing.
