# Hand-back: Scored control admission repair

Agent: Codex Sol worker. Ticket: specificity-ladder A2 plan, offline materializer review fix. Status: resolved implementation; independent re-review remains outstanding.

## What changed

The orchestrator commits these worktree files by explicit file list:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_twin_training.py`: matched mode validates the frozen scored-control contract before returning a manifest or writing outputs.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_twin_training.py`: real Arrow inputs, actual producer score-record serialization, byte-hashed receipts and score files, negative admission cases and positive diagnostic-baseline cases.
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/14-materializer-fix-handback.md`: this report, also copied to `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/14-materializer-fix-handback.md`.

There are no staged apply operations. Other worker files were preserved. No A1 implementation was changed.

Matched inputs now require common D/H/I/neutral model identities, supported inversion and diagnostic neutral thresholds, identical receipt bytes across the two new source arms, required scoring provenance, safe dataset-relative evidence files and correct byte digests. Receipt commits and request-pool digests have their required full hexadecimal format; tokenizer name and available local revision agree. Every score id is unique and split-disjoint, including scored-but-rejected ids; a score cannot borrow a source id from a different split even when matching discarded that source row.

Every retained id has matching scores for both arms and both streams. Validation checks canonical prompt hashes, D-oriented honest/opposite words and their leading-space tokens, finite native logits and signed margins, and native argmax identity. Inversion must win the full-vocabulary opposite argmax and meet its recorded margin in both streams. Both new rows must carry canonical hashes of the actual original joined D/H rows. Baseline competence remains diagnostic: the positive fixture deliberately fails it. Native low-precision margins are preserved rather than recomputed from promoted logits. Extra scored-but-rejected rows remain allowed.

The frozen schema is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/a1-data-contract.md`; native score fields are from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_user_inversion_v2.py`. Threshold values are exactly those in that contract. Timing-only D mode keeps its provisional behavior.

Output manifests and both training configs record `a1_scoring` with receipt content and digest. Source provenance retains original root paths, configs and file hashes. I training configs do not inherit a broken root-relative `scoring_provenance` pointer: that original descriptor belongs to the source prompts, which remain in `source_recipient` and `source_reference`. Source score files are not recopied into training outputs. The producer worker reports the same receipt and score-file layout for its two assembled source arms; independent producer/materializer integration remains a lead check.

## How verified

Commands ran from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training.py -p no:cacheprovider -q -k actual_scored_contract
```

RED, before production edits: `34 failed, 33 deselected`; each malformed fixture was admitted instead of raising. Evidence: `/tmp/a2-fix-red.log`. The shell wrapper printed the log afterward and therefore returned success; the pytest output is the RED evidence.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training.py -p no:cacheprovider -q -k score_id_cannot_borrow
```

Additional RED before the source/score split guard: exit one, `1 failed, 68 deselected`, because an extra score could reuse a discarded source id from another split. Evidence: `/tmp/a2-fix-red-source-split.log`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_twin_training.py -p no:cacheprovider -q
```

Final GREEN after all changes: exit zero, `69 passed`. Evidence: `/tmp/a2-fix-final-mgnp.log`. This includes the locally cached real-tokenizer alignment test with no model load.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 HF_HUB_OFFLINE=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_twin_training.py -p no:cacheprovider -q
```

Final GREEN after all changes: exit zero, `68 passed, 1 skipped`. Evidence: `/tmp/a2-fix-final-base.log`. The optional local-tokenizer test skips because the base environment lacks its accessible cached tokenizer. Existing pandas bottleneck-version and deprecated Hugging Face cache warnings appear in this environment.

```bash
/u/swong2/.conda/envs/mgnp/bin/python -m py_compile dataset/build_twin_training.py tests/test_twin_training.py
```

Observed: exit zero. The same syntax check also ran successfully with `/sw/external/python/anaconda3/bin/python3.9`. Python Ruff is unavailable in mgnp, and no repository Ruff configuration was found. Markdown lint and the report-number audit accompany this hand-back.

## Execution evidence

- Job id and cluster: local CPU pytest and syntax commands only; no scheduler job.
- Exit code: both final focused suites and syntax checks exited zero. The additional RED exited one; the initial RED shell wrapper ended with its log-printing command as described above.
- Row counts: matched Arrow fixtures retain one id per train, validation and test split, against one expected per split. The optional mgnp real-tokenizer check asserts two original rows per split against two expected. These counts are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/tests/test_twin_training.py`.
- Baseline comparison: the initial admission regression accepted all 34 malformed cases against zero expected; the final focused suite rejects them. Evidence: `/tmp/a2-fix-red.log` and `/tmp/a2-fix-final-mgnp.log`. The positive baseline-incompetent fixture retains one row per split against one expected, proving baseline competence does not become a membership filter.
- Provenance file: no scientific `run_manifest.json` was created. Tests use explicitly synthetic full-length commit values in serialized receipts. The lead supplied checkpoint `0bbc035` as the starting code reference; the worker ran no git. Scientific readiness is not yet verified and no inference or scientific result is claimed.
- Budget: `/u/swong2/.local/bin/codex-usage --pause-at 80` reported six percent weekly used, with reset `2026-11-06T16:07:41+00:00`, at the final work checkpoint.

## What is NOT done

Independent re-review and acceptance of matched readiness belong to the lead and remain outstanding. There was no full real matched build, benchmark/protected-data scoring, GPU job, paid API use, model load, notebook execution, git operation or subagent. No broad suite was rerun, following the delegated instruction; the pre-existing sequence-length failure in `tests/test_deception_tasks.py::test_hyperparameters_are_identical_across_the_three_mechanisms` remains outside this repair. All previously completed materializer behavior was preserved.

## Open questions

The old review requested agreement on the producer schema; the frozen contract and direct producer-worker exchange resolve that ambiguity. The neutral threshold is diagnostic metadata, not a filter. Recorded request-pool and model/tokenizer revision fields are compared with matching config fields when supplied; the materializer cannot independently reconstruct the original request pool or prove inference occurred. Default: retain this explicit provenance boundary and have the lead independently review code plus an assembled-producer/materializer roundtrip before accepting matched readiness. No user decision blocks this repair.
