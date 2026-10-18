# Format-control EVAL 5 (ticket 06): D, H and F on one screen

**Nothing here has been submitted.** EVAL 5 is launched only on the researcher's
explicit go-ahead, and only for a family whose Format Circuit knockout passes
the eval 2 gate. `FORMAT_CONTROL_EVAL5_GO=1` is a speed bump, not proof of
consent: any agent can export it. The go-ahead itself is obtained from the
researcher in the session that submits and recorded in ticket 06 before anyone
sets it.

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

## Extra composed circuits (`eval5_extra_circuits`)

A family's `suites.json` entry may list extra composed circuits of D, H and F,
`"eval5_extra_circuits": [[label, expr], ...]`. Each is one more cell in the
**same** invocation as D, H and F (same screen, same judge cache, own
size-matched random rows), bound after their exprs:

- coarse: `--expr <label>_hko=(<expr>) - m` at leaf, filed as
  `cells/<label>_hko__leaf/`;
- fine (none configured, not launched): `--expr D=D --expr H=H --expr F=F
  --expr <label>=<expr> --compose-granularity head`, filed as
  `cells/<label>__head/`. The explicit D/H/F exprs are needed because any
  `--expr` replaces the evaluator's default of every bound circuit on its own;
  one granularity (head, the primary fine reading) keeps one cell per extra.

A label is an identifier other than D, H, F and `m`, without the `_hko`,
`__leaf` or `__head` endings; an expression names only D, H and F. The gate and
every refusal are unchanged: they concern F. The record (`eval5_record.json`)
carries `extra_circuits` and `cell_labels` in each event, and the cost block
compares the dry-run's cell count with the configured one (a WARNING line if
they differ). The summary gives each extra its own role after D, H, F (key =
label without `__leaf|__head` and `_hko`, e.g. `D_minus_F`, shown as
"D−F (deceptive minus format)"); ticket 05's `load_eval5` and its decision rule
read D, H and F only and ignore it.

**2026-10-16 request.** The researcher asked for EVAL 5 on D, H, F **and
D−F** for `sdr_coarse`, so the coarse entry carries
`"eval5_extra_circuits": [["D_minus_F", "D - F"]]`: four cells (`D_hko`,
`H_hko`, `F_hko`, `D_minus_F_hko`) per group. FAR and SDR-fine keep three.
D−F is 33 heads (4,224 fine units; D has 69, F 68, they share 36). The real
dry-runs of 2026-10-16 (`dryrun_eval5/sdr_coarse_{sm,lb}.log`) passed with all
screens `[cached]`, the gate passed, and both printed a submit line (not run):

| group | cells | dry-run TOTAL (min) | judge calls | GPU hours | default `--time` |
| --- | ---: | --- | ---: | --- | --- |
| `sm` (3 cells, 2026-10-15) | 3 | 1460.5 - 1774.3 | 4,671 | 24.3 - 29.6 | 44:30:00 |
| `sm` | 4 | 1946.3 - 2260.1 | 6,228 | 32.4 - 37.7 | **56:45:00** |
| `lb` (3 cells, 2026-10-15) | 3 | 549.8 - 752.0 | 4,050 | 9.2 - 12.5 | 19:00:00 |
| `lb` | 4 | 731.9 - 934.2 | 5,400 | 12.2 - 15.6 | 23:30:00 |

**The 4-cell `sm` default `--time` (56:45:00) exceeds the gpuA40x4 MaxTime
(2-00:00:00, `sinfo -p gpuA40x4 -o "%l"`).** The time rule is unchanged; pass
an explicit `--time` of at most `48:00:00` for `sm`. The anchor (the one-cell
coarse `sm` suite ran 3 h 51 min) puts four cells near 15 to 16 h, well
inside that.

## Files

| file | what |
| --- | --- |
| `eval5_cmd.py` | the pure command generator, the local screen cache (`seed-cache`, `cache-check`), the gate, the refusals, the dry-run parser and cost, the record; CLI `args`, `check`, `gate`, `seed-cache`, `cache-check`, `sbatch`, `cost`, `record` |
| `submit_eval5.sh` | `<family> <sm\|lb> [--dry] [--standin] [--gate-override R] [--allow-rescreen R]`: the only thing that can submit |
| `write_eval5_format_summary.py` | CLI over `evaluation/eval5_format_summary.py`: `result_summary.md` + `eval5_format.json` |
| `eval5_record.json` | every dry run and submission: arguments, cost, gate KLs, overrides with their reasons, job id |
| `dryrun_eval5/<family>_<group>.log` | login-node `--dry-run` logs of the real suites, with the cost appended |
| `dryrun_eval5_standin/<family>_<group>.log` | plumbing-only dry-runs with F := H (build phase) |
| `outputs/_eval5_format_cache/screens/` | the worktree-local copy of the A40 screens (git-ignored by its own `.gitignore`) |

Runs D, H and F come from ticket 04's `suites.json` (the one configuration
point); the coarse all-MLP operand `m` too. The gate reads ticket 04's
`suite_manifest.json` and its suites under `outputs/_suites/`.

## Settings

Exactly `outputs/_eval5_launch/eval5_args.sh` (main checkout): `--evals benchmarks
--ablation interchange --benchmark-n-per-dataset 50 --benchmark-n-random 6
--benchmark-screen-budget 600`. Added, none changing a number:

- `--task-from <D run>`. Mandatory: with no task flag the evaluator defaults to
  every bound circuit's own test set, and D, H, F have three conditions, so it
  would run a 3 x 3 grid of benchmark cells. The task does not enter EVAL 5 (the
  corrupt stream comes from the benchmark), it only names the cell directory.
- `--benchmark-screen-cache <worktree>/outputs/_eval5_format_cache/screens`.
  **The launcher never writes into the main checkout.** Before every dry run
  `seed-cache` copies (files, never links; a symlinked source is followed) the
  group's screens from the main checkout's `outputs/_screens` into this
  worktree-local copy. Only screens whose key says NVIDIA A40 are copied, and an
  entry already in the copy is never overwritten. The evaluator reads the copy,
  and on a miss writes there. The judge cache already lives in the suite's own
  output directory under the worktree. The only main-checkout paths a command
  names are the read-only circuit run directories and, read-only, the benchmark
  repos (a test asserts this for all six suites).
- `--benchmark-repo-root /projects/beto/swong2/Alignment`. MASK and Liars' Bench
  are checked out beside the main checkout (read-only); the default resolves
  them inside `.claude/worktrees/`. Not part of the screen-cache key.

**Partition.** `--partition` defaults to `gpuA40x4` to keep the screened items
item-for-item comparable with the existing eval5_* suites (`eval5_far`,
`eval5_sdr`, `eval5_sdr_h03`, `eval5_sdr_coarse_nls0.3_*`), whose screens were
made on NVIDIA A40; the GPU is part of the cache key, so other partitions
re-screen. The brief's "any partition" is for speed and does not override
comparability (orchestrator ruling, 2026-10-13).

## The refusals

`submit_eval5.sh` without `--dry` submits only when every refusal clears, in
this order, each naming its reason (exit 3; a failing dry-run exits 5):

1. F is configured in `suites.json` (not null). `--standin` never submits.
2. The pre-flight gate, on ticket 04's suite:
   - the manifest's planned F (`suite_manifest.json` `runs.F`) equals the F
     `suites.json` names now;
   - F's knockout cell exists on the D test set and on F's own (`nopressure`)
     test set (`cells` index, `roles` contains `knockout`, circuit `F` or
     `F_hko__leaf`);
   - each cell was produced by that F (its `summary.json`
     `circuit_spec.operands.F`): a stale cell from another F run is refused,
     naming both paths;
   - each cell's wikitext KL (`knockout.json` `headline.wikitext_kl`, else
     `wikitext.discovered.kl_per_token`) is `<= 0.66`; the refusal names the
     cell and the number. Wikitext KL depends only on the circuit, so the two
     cells should agree; both are required anyway.
   - coarse only: D, H and F have the same mask signature as the all-MLP
     operand (`nomb` = no `mlp_blocks` gate), each read from its own
     `active_nodes.json`, as the old coarse launcher derived it. The operand is
     ticket 04's `outputs/_launch_format_control/allmlp_nomb` (built by
     `build_allmlp.py`); its masks are identical to the main checkout's
     `_allmlp_nomb`, which the existing coarse suites used (checked 2026-10-15:
     all five mask arrays equal, plus a `built_from` provenance field).
3. `FORMAT_CONTROL_EVAL5_GO=1` is set (see the top of this file).
4. A `--dry-run` of these exact arguments passes (run by the script itself).
5. Every screen of the group is an A40 cache hit: each dataset is `[cached]` in
   that dry-run log, the local copy holds no non-A40 screen for the group, and
   the partition is an A40 one.

`--config`, `--manifest`, `--suite-root`, `--record`, `--cache-src` and
`--cache-dir` decide the gate and the cache, so outside `--dry` they are refused
(exit 2) unless `EVAL5_ALLOW_PATH_OVERRIDES=1` (the tests set it).

`--dry` needs no go-ahead: it prints the command, runs the dry-run, appends the
cost to the log, and prints the sbatch line only when refusals 1, 2 and 5
clear ("no submit line" and the reasons otherwise). It records the dry run.

## Keep this worktree until EVAL 5 has run

The Format Circuit runs, the coarse operand `allmlp_nomb` and ticket 04's cells
all name paths inside `.claude/worktrees/format-control/`: in `suites.json`, in
`suite_manifest.json`, and in each cell's `summary.json` operands. The gate
matches the configured F against the F that produced the cells. A run at
another path counts as the same F when its `active_nodes.json` masks and
`config.json` `deception_condition` are identical (`same_run` in
`eval5_cmd.py`). That comparison has to read the recorded run directory.

- **Keep the format-control worktree** until EVAL 5 has run and its summaries
  are written. This is the supported path.
- **After a merge**, `suites.json` may be repointed (F and `allmlp`) to the
  merged copies in the main checkout. The gate then matches by mask content,
  but only while the worktree's run directories still exist. Once they are
  gone it refuses with "cannot compare masks ... keep the format-control
  worktree". Do not change the paths before that; the cells were produced from
  them.

## The two explicit overrides (researcher decisions, recorded)

Neither weakens the default: without the flag the refusal stands, and each flag
needs a non-empty reason, which is printed and written to `eval5_record.json`
with the gate numbers or cache reasons it overrode.

- `--gate-override "<who, why>"`: the spec's "or fluent generations" exception.
  It clears **only** the KL bar. A missing cell, a missing KL, a stale F or a
  manifest planned with another F are never overridable. Read
  `generation.examples` in the F knockout's `knockout.json` before deciding.
- `--allow-rescreen "<who, why>"`: lets a suite run when a screen is not an A40
  cache hit or the partition is not A40. The job then re-screens into the
  worktree-local copy, and its items no longer match the existing suites; say
  so wherever the results are read.

```
# build phase (done): plumbing with F := H
bash outputs/_launch_format_control/submit_eval5.sh far sm --dry --standin
# once ticket 03's F runs are in suites.json and ticket 04's knockout cells exist
python outputs/_launch_format_control/eval5_cmd.py gate far
bash outputs/_launch_format_control/submit_eval5.sh far sm --dry
# only on the researcher's go-ahead, recorded in ticket 06
FORMAT_CONTROL_EVAL5_GO=1 bash outputs/_launch_format_control/submit_eval5.sh far sm --account bgrb-delta-gpu
# a researcher-ruled override, e.g. fluent generations above the KL bar
FORMAT_CONTROL_EVAL5_GO=1 bash outputs/_launch_format_control/submit_eval5.sh far sm \
    --gate-override "JW 2026-10-20: F knockout generations read fluent" --account bgrb-delta-gpu
```

`--time` defaults to the dry-run ceiling x 1.5 in quarter hours (ticket 04's
rule): `44:30:00` for `sm`, `19:00:00` for `lb` with three cells (`56:45:00`
and `23:30:00` for the four-cell coarse suite, see "Extra composed circuits":
the `sm` one is above the partition's 48 h MaxTime). That is far above the anchored
runtime (the one-cell coarse suite the dry-run rates near 10 h ran in 3 h 51
min), so a shorter `--time` (for example 18:00:00 for `sm`) backfills better;
the default stays the safe one.

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

The real-F dry-runs of 2026-10-15 (`dryrun_eval5/sdr*_{sm,lb}.log`) give the
same numbers: F's size changes the random draws, not the counts. Gate status
(2026-10-15, all six real dry-runs passed on the evaluator side):

| family | F knockout wikitext KL | gate | submit line |
| --- | ---: | --- | --- |
| `sdr_coarse` | 0.279 | passes | printed for sm and lb, not run |
| `sdr` | 1.342 | refused | none |
| `far` | 4.265 | refused | none |

Anchored on wall time: the one-cell `eval5_sdr_coarse_nls0.3_nomb` (sm) ran
3 h 51 min with cached screens, so a three-cell `sm` suite is plausibly about
10 to 12 h on an A40. Its one-cell judge count (1,376 writes + 181 hits = 1,557)
is exactly a third of the 4,671 above.

## The summary and the interface for ticket 05

After a suite finishes:

```
python outputs/_launch_format_control/write_eval5_format_summary.py outputs/eval5_format_far outputs/eval5_format_far_lb
```

writes into each suite `result_summary.md` and `eval5_format.json`. The summary
has, per dataset, the deception / honest / unparsed rate under interchange for
full, the D / H / F knockouts and the D / H / F random means, with dec/parsed,
`ref_nll` and `distinct_n`; Δ and the null percentile per circuit; means over
the datasets every circuit has; screen notes; the note that random rows are
size-matched per circuit while the screened items are shared; missing,
unreadable and duplicate cells and failed datasets, reported, not raised; and
the three grader caveats.

**The grader caveats are quoted word for word** (line breaks re-flowed) from
their sources, each quote followed by its source path, and a test compares
every quote with its source file:

| caveat | source |
| --- | --- |
| Empty generation scored honest | ticket `.scratch/eval5-grader-fixes/issues/01-empty-generation-scored-honest.md` |
| MASK verdict D coded deceptive | ticket `.scratch/eval5-grader-fixes/issues/02-mask-refusal-coded-deceptive.md` |
| Liars' Bench "not correct" verdict guard | **no ticket**: item 3 of the project memory note `eval5-grader-fixes-pending.md` and `outputs/eval5_sdr_coarse_nls0.3_nomb_lb/result_summary.md`, where it was found; labelled so in every summary |

Under each, the table counts the knockout rows matching that caveat's trigger.

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
 "missing": [roles without a readable cell], "unreadable": {role: path},
 "duplicates": {role: [ignored paths]},
 "extra_roles": [extra roles, e.g. "D_minus_F"], "extra_exprs": {role: expr},
 "role_names": {role: display name},
 "roles": {"D"|"H"|"F"|<extra role>: {"label": cell label or null, "missing": bool, "source": path,
            "failed_datasets": {name: error}, "judge": {...}, "resolved": {...},
            "datasets": {name: {"n": int, "screen": {...},
                                "full" | "knockout" | "random_mean":
                                   {"deceptive", "honest", "unparsed", "dec_parsed",
                                    "ref_nll", "distinct_n", ...},
                                "null_percentile", "null_p_value",
                                "caveat_hits": {"empty_generation", "mask_verdict_d",
                                                "lb_correct_guard"}}
                         | {"error": str}}}},
 "grader_caveats": [{"key", "title", "ticket", "label", "quotes": [{"source", "text"}]}],
 "random_rows_note": str}
```

`evaluation.eval5_format_summary.tabulate(load_suite(dir))` returns the same
dict without writing.

## PENDING: re-score the sm suite's judge calls (as of 2026-10-18)

Both `sdr_coarse` suites ran on 2026-10-17 (lb 22947270, sm 22947260; D, H,
F and D−F in one invocation each). The OpenRouter key ran out of credits
between the two jobs, so in `outputs/eval5_format_sdr_coarse` (sandbagging +
MASK) 6,032 of ~6,228 scoring judge calls returned HTTP 402 and every
knockout / random row reads 0.0 deception with the rows marked
`raw: "judge-failed"`. `outputs/eval5_format_sdr_coarse_lb` is sound (8 empty
judge completions on one word-salad generation; they will stay unparsed).
The generations and judge prompts are stored per config, so the fix is a
judge-only re-score on the login node, no GPU:

```
cd /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/format-control   # or wherever the suite dirs live
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python rejudge_benchmarks.py outputs/eval5_format_sdr_coarse --dry           # 4,661 calls (gpt-4o 4,162; o3-mini 499), ~$20-40
nohup python rejudge_benchmarks.py outputs/eval5_format_sdr_coarse --max-calls 5000 > outputs/eval5_format_sdr_coarse/rejudge.log 2>&1
python rejudge_benchmarks.py outputs/eval5_format_sdr_coarse_lb              # 1 call; exit 1 or 3 on the hopeless row is expected
python outputs/_launch_format_control/write_eval5_format_summary.py outputs/eval5_format_sdr_coarse outputs/eval5_format_sdr_coarse_lb
python write_format_control_summary.py outputs/_suites/format-control-sdr-coarse-nls0.3 --data-dir data/datasets \
    --eval5-dir outputs/eval5_format_sdr_coarse --eval5-dir outputs/eval5_format_sdr_coarse_lb
```

Needs `OPENROUTER_API_KEY` with credit (check
`curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $OPENROUTER_API_KEY"`).
Restart-safe: verdicts land in the suite's `judge_cache.jsonl` as they arrive,
and a second run only sends what is still missing. The tool refuses a dataset
whose rebuilt prompt differs from the stored one and a cell whose stored
numbers do not reproduce from its labels; a one-time
`benchmarks.json.pre_rejudge` backup is kept. One known stale field after the
re-score: each cell's top-level `judge` block (cache hits / writes) and the
"judge cache (X cell's view)" line in `result_summary.md`; the fresh stats are
in the `rejudge` block. The EVAL 5 output directories, `_shards/`, Slurm logs
and the screen cache are untracked: move them with the worktree if it is
removed.
