# Hand-back: Direction prefit CPU timeout and remaining preparation

Agent: Sol. Status: handed-back. Actual failure diagnosed; remaining CPU proposal is ready for root review, unexecuted.

## What changed

Root review found that the first unexecuted continuation packet retained the old constructed shell target and omitted its local settings file. That packet remains preserved and must not run. The corrected separate packet is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163-r2`. Its shell target is absolute, the original settings bytes are present and hash-bound, and its dependency walk covers launch, supervisor, preparation, config, settings, validation and actual input paths. The prospective output is separate. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163-r2/dependency-walk.json`.

Preserved the failed run and completed artifacts in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-direction-prefit-preparation-861f84a3938a-r158`. Added an actual-run evidence bundle and a separate continuation proposal at `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163`. No original source, admission, canonical, completed inventory, ledger or failed evidence was edited.

The supervisor sent TERM at 1320.014 seconds and recorded child exit `-15` at 1320.515 seconds. The fixed child boundary explains termination; this was not the scheduler walltime boundary. Job-local memory controllers show no OOM event. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-direction-prefit-preparation-861f84a3938a-r158/evidence/result.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-direction-prefit-preparation-861f84a3938a-r158/evidence/memory-before.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-direction-prefit-preparation-861f84a3938a-r158/evidence/memory-after.json`.

Canonical creation completed in 246.543 seconds and prefit inventory creation completed in 244.549 seconds. The complete prefit payload has 1077037861 bytes, and its actual digest matches its original marker. Fit-select has no object or result; dry-run and validation never started. Sources: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-direction-prefit-preparation-861f84a3938a-r158/evidence/canonical-result.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-direction-prefit-preparation-861f84a3938a-r158/evidence/inventory-prefit-result.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/actual-job23475935/run_manifest.json`.

The continuation reuses both completed artifacts without rerunning their construction. It runs only the missing original fit-select command into a fresh output, the original prefit dry-run without authority, and the original metadata validation adapted for separate paths. It requests four CPUs, 32 GiB, zero GPUs and 45 minutes, with a 2520-second child boundary plus 15 seconds grace. This is a bounded request, not a completion forecast; fit-select already exceeded approximately 829 seconds without a receipt. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/proposal.json`.

## How verified

```text
python3 /tmp/create_report163.py
```

Observed: immutable export hashes, input links, frozen native files and completed-artifact fingerprints matched; proposal scripts parse. The actual source check covered 511 ordinary files, four input links and thirteen frozen native files. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/actual-job23475935/run_manifest.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/static-checks.json`.

```text
sacct -j 23475935 --noheader --parsable2 --format=JobID,State,ExitCode,ElapsedRaw,AllocCPUS,ReqMem,MaxRSS,NodeList
```

Observed: terminal scheduler evidence is preserved in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/actual-job23475935/sacct.txt`.

The continuation retains original live source, grader/protection and geometry checks; all original scientific-core comparisons, inventory checks, timing-membership checks, numerical-profile checks and module-origin checks remain. It checks completed artifact bytes before and after execution. Only fit-select output and evidence destinations change. Files: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/prepare.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/validate.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/commands.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/config.json`.

## Execution evidence

- Job id and cluster: `23475935`, Delta; actual host `cn137.delta.ncsa.illinois.edu`, CPU-only allocation. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-direction-prefit-preparation-861f84a3938a-r158/evidence/allocation-before.json`.
- Exit code or Slurm state: `FAILED`, `143:0`; elapsed 1330 seconds. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/actual-job23475935/run_manifest.json`.
- Row counts: two completed original preparation commands against four expected before validation; zero scientific rows observed against zero requested. Fit-select objects: zero against one expected. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/actual-job23475935/run_manifest.json`.
- Baseline reproduces: complete prefit payload actual byte count 1077037861 against marker byte count 1077037861; content digest also matches. This is artifact preservation, not a model baseline or a scientific result. Source: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/actual-job23475935/run_manifest.json`.
- Provenance file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/actual-job23475935/run_manifest.json`, source commit `861f84a3938a5e22fa329af0c469b2dd812fe68a`. This retrospective evidence manifest links the original commands/results and does not pretend to be a successful preparation receipt.

## What is NOT done

The proposed continuation has not run. No successful fit-select object, wrapper dry-run or final validation exists. The canonical science comparison and genuine inventory summaries remain for the CPU validation; a completed prefit marker alone does not establish readiness.

No model fit, selected direction timing, GPU reservation, admission or full native aggregation is claimed. No mask retry is authorized. Direction timing still has only 0.5 GPU-hours total across separate prefit and later selected timing. Structural serial-forward lower counts remain 16770 and 272610 respectively; they exclude other work and do not establish an affordable split. The original worksheet implementation retains these derived calculations in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/validate.py`; total allowance is recorded in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-prefit-remaining-cpu-r163/proposal.json`.

## Open questions

Root should use the corrected separate packet and review its immutable proposal manifest, dry-run the exact CPU wrapper and submit the single accepted continuation. Preserve its output on failure; do not automatically retry. After completion, independent review must inspect genuine inventories, source/protection checks and both timing parts before any model reservation. The next scientific decision remains whether the complete two-part timing allowance is feasible; CPU preparation does not answer it by itself.
