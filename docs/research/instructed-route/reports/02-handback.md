# Hand-back 02: B2 plan for the falsity probe, the SDR wish test and the SER MLP replication

Agent: planner-B2, Opus (claude-opus-5-5). Ticket: the team lead's B2 planning brief, which has no ticket file. Status:
resolved.

## What changed

- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/plans/B2-plan.md`,
  new, 250 lines. It holds the costed B2 plan: the designs of P1, P2 and P3, the code inventory, the cost table,
  tickets T1 to T8 with their test files and assertions, and the risks.
- Committed by the orchestrator from the worktree:
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/instructed-route/docs/research/instructed-route/reports/02-handback.md`,
  this file.
- Staged for the apply tool: nothing.
- No code, data, ledger or state file was touched. No git command was run.

## How verified

Every fact the plan relies on was read on the login node. The key commands and their observed output follow.

```
/u/swong2/.conda/envs/mgnp/bin/python -c "from datasets import load_from_disk; ..."
```

Observed:

| dataset or check | value |
| --- | --- |
| far_v2, ser_v2, sdr_v2 | train 200, validation 200, test 1,000 each |
| twins | every id shared, in every split |
| sdr_v2_inversion_reported | 618 test rows, 618 unique ids, 41 I clauses, 20 D clauses |
| 618 ids in SDR's held-out sample | 57 |
| FAR train and validation ids in SER test | 0 |
| test clauses shared with train | FAR 11 of 12, SER 16, SDR 19 |
| ser_v2 against ser_v2_nopressure test ids | equal |

```
python3 -c "... mechanism-analysis-p1/timings/ser.json and 1c-b.json ..."
```

Observed: the SER S1 to S6 sweeps took 497 to 1,131 s each, the S1 line including a 563 s model load. heldout_d ran
494 groups x 100 instances in 242 to 931 s, the 931 s including a 619 s load. heldout_h and heldout_f ran 21 groups in
13 to 14 s.

```
/u/swong2/.conda/envs/mgnp/bin/python -c "import sklearn"; /u/swong2/.conda/envs/mgnp/bin/python -c "import scipy"; /sw/external/python/anaconda3/bin/python3.9 -c "import sklearn; print(sklearn.__version__)"
```

Observed: mgnp raises ModuleNotFoundError for both sklearn and scipy. The base environment prints 1.3.0.

```
grep -rn "run_manifest" --include=*.py . | grep -v "^./tests"
```

Observed: only `run_io.py`, `run_manifest.py`, `evaluation/suite.py` and `evaluation/grader_hash.py` reference
it, so `analyze_components.py` writes no manifest.

```
cat docs/research/held_out.json
```

Observed: `"sets": []`.

```
wc -l docs/research/instructed-route/plans/B2-plan.md; research-session lint docs/research/instructed-route/plans/B2-plan.md
```

Observed: 250 lines, and lint exits 0.

## Execution evidence

Not applicable: no runs.

## What is NOT done

- No ticket is implemented. T1 to T8 are specified only.
- No dry run was made, so the seed-1 and seed-2 samples, the 618-row twin pairing and the per-cell counts are not yet
  verified.
- No GPU time was reserved or used, and no ledger row was written.
- The P1 control table's predictions are reasoned from the design and are not yet verified.
- The P2 and P3 costs are extrapolated from Bridges-2 H100 timings. They have not been measured on Delta.
- That `knockout/groups.json` gives the clean margin R-cls needs in its `clean_run` block comes from the code. It was
  not exercised end to end, so T4's golden test and the seed-0 baseline must confirm it.
- An advisor review led to four revisions, which are in the plan:
  - P2's primary positions are `all`, because the clause span differs between the wish prompt and its twin;
  - every `--include-ids` line sets `--n-causal 1000`;
  - the seed-2 ids are drawn on CPU in T3;
  - HI rows are kept only at `h_honest_instruction_clean` >= 0.3.
- I did not read B1's plan, so collisions are flagged only generically (risk 6).

## Open questions

1. **Instruction-confound label for P1.** Should a ruling in `spec.md` say, before P1 runs, that a misleadingness
   verdict is "clean" only when FAR I and both HI controls are under 0.6, and "instruction-confounded" when the
   controls match the detector pattern? The AUROC bands stay unchanged. Default: record it as a ruling that only
   labels the verdict.
2. **P2 null qualifier.** If a random or KV-group quartet also reaches f 0.5, does the verdict read "not
   quartet-specific"? Default: record it as a ruling that qualifies the verdict and leaves the 50% rule unchanged.
3. **P3 FAR and SDR cells.** They test the "SER alone" half of F-mech-009 and cost seconds. Default: include them as
   descriptive rows. The B2 verdict stays SER only.
4. **Layer selection.** It scores D against the pooled H and HI rows on FAR validation while the probe trains on D
   against H only. Is that within "train on FAR D versus H"? Default: yes.
5. **P3 run A reuses the mechanism-analysis held-out sample (seed 1)**, which B1 also tests on. Default: allowed,
   because neither test selects anything on it.
6. **T1 ordering against B1.** B1 may edit `analyze_components.py` or `knockout.py`. Default: land T1 first, then
   rebase B1's work.
