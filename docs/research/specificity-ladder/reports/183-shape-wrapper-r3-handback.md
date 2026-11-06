# Hand-back 183: A2 shape wrapper relocation

Agent: worker. Status: handed-back. Independent review and root dry-run precede any submission.

## What changed

New packet `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-full-score-plan178/full-shape-cpu181-r3`; manifest SHA-256 `bd12ebd27853dd63156dc2d1b2662688d4e8c2513269e4ef872db557538a821b`, wrapper `run.sh` SHA-256 `e8ea857d88e49841d393fcb5d32ef3902ef8d31d43de315b2b43e24496ba56c8`. The wrapper now invokes the exact absolute r3 `shape.py` path, so Slurm's spooled wrapper location cannot redirect it. Its pinned shape, native tests, original regression fixture and request are byte-identical to r2; shape SHA-256 `b30a79cbaac9d62b7d825dc810e3b57cb1f82591bb4a7b0b736aa7e3b9385fd9`. The new relocation test is included in the r3 manifest. All r2 manifest members and manifest `71af5046b4701991fd3d444f1fb70c9e03304a5b2d723363757579877be8fa97` remain intact. Resources and child limits are unchanged.

For root review, using W as `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`, P as `$W/.superpowers/sdd/plan-a2-full-score-plan178/full-shape-cpu181-r3`, S as `$W/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime`, and E as a new root-selected execution parent, the dry-run shape is:

```bash
sbatch --test-only --parsable --account=beto-delta-cpu --partition=cpu-interactive --nodes=1 --ntasks=1 --cpus-per-task=4 --mem=16G --time=00:15:00 --no-requeue --export=ALL --chdir="$S" --job-name=a2-shape181-r3 --output="$E/job-%j.log" "$P/run.sh" "$E/execution" bd12ebd27853dd63156dc2d1b2662688d4e8c2513269e4ef872db557538a821b
```

Root creates a fresh E with absent `execution`, reviews actual placement and all gates, then a single deliberate submission uses the same arguments with `--test-only` removed. No retry is implied. Wrapper closure: Slurm may copy `run.sh`; it invokes the exact r3 path above, and `shape.py` rehashes its manifest and members before use.

## How verified

The captured original r2 failure for Delta job 23612166 is `root-shape181-r2-01/job-23612166.log`: Python attempted to open `shape.py` under `/var/spool/slurmd/job23612166`. It is preserved; no model or proof result was produced.

Before the r3 fix, `red-wrapper.log` from `/sw/external/python/anaconda3/bin/python3.9 -m unittest -v test_wrapper_relocation` exited 1: the intercepted copied wrapper pointed to the arbitrary temporary spool directory instead of r3. After the fix, the same test exited 0 on base and mgnp, one test per interpreter; `bash -n run.sh` passed. The fake `timeout` only records arguments and does not execute Python or produce scientific artifacts. A byte comparison checked copied scientific files and all r2 manifest pins.

## Execution evidence

Local wrapper tests only: semantic RED exit 1, GREEN exit 0 on both interpreters. Scientific rows and baseline reproduction do not apply. Delta job 23612166 failed exit `2:0` after 5 seconds, per root-reported scheduler state and preserved log; it produced no proof result. Scientific source remains commit `50e947bb852613e3a270082651f2bd1b7bb0c525`; new packet provenance is its manifest above.

## What is NOT done

No new submission, scheduler call, real-data run, model, effects, git, RS or remote access. The earlier failed attempt is preserved; r3 requires independent review and fresh operational gates. This correction does not establish full-shape, GPU runtime, memory or storage conclusions.

## Open questions

Root should obtain independent exact-manifest review and perform the new dry-run, including actual immutable path and fresh output checks. Default: do not submit until those gates pass.
