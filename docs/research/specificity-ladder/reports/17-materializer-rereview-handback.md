# Hand-back `17`: Materializer admission re-review

Agent: Codex Sol independent reviewer. Ticket: A2 plan `Task 1`. Status: resolved; prior P1 closed by scoped code review.

## What changed

Review only. No implementation, fixture, or producer edits were made. Commit the report from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/17-materializer-rereview-handback.md`. A matching copy is maintained at `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/17-materializer-rereview-handback.md`. No staged apply operation exists.

No remaining correctness blocker was found in the requested admission scope. The prior P1 in `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/11-a2-materializer-review-handback.md` is closed: raw or unscored controls, changed model identities, and unsupported inversion thresholds fail before a matched manifest is returned or output written.

The admission path in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/dataset/build_twin_training.py` checks the following:

- `_evidence_file` and `_scoring_receipt` require the named receipt, receipt and score byte digests, files resolving inside each source root, full source commit format, scorer identity, execution metadata, actual tokenizer identity and available tokenizer revision, and agreement with source model/config metadata. Both arms must carry identical receipt bytes and score-file bytes.
- `_index`, cross-source ownership, and score indexing reject duplicate or cross-split identities before cohort matching. Extra scored-but-rejected rows are permitted but receive native-score validation; an extra score cannot borrow an original source identity from another split even when that source row is later discarded.
- `_validate_scored_control` checks each retained arm against original joined D/H row hashes, exact original prompt hashes, and canonical honest/opposite words for each designation stream. Full-vocabulary argmax identity, decoded token, choice and finite native scores must agree. Both inversion streams meet the recorded permitted threshold. Baseline competence stays diagnostic.
- Native margins remain the scorer's values; the implementation checks signed aliases without subtracting promoted logits. Timing-only D still requires no A1 evidence and remains provisional.

Output `a1_scoring` is appropriately an embedded receipt plus receipt digest describing original source prompts. Removing root-relative `scoring_provenance` from transformed output avoids pointing at absent files or implying the new neutral corruption was scored. The assembled source I and neutral datasets remain self-contained as required by `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/a1-data-contract.md`.

## How verified

Read the current implementation and tests directly, alongside the prior review, A2 `Task 1`, the frozen scored-data contract, A1 `score_pairs`, and the native `score_prompts` implementation. Worker report14 was not read. No uncovered gap warranted another reproduction or a broad suite.

Direct evidence-reading command:

```bash
cat /tmp/a2-fix-final-mgnp.log
cat /tmp/a2-fix-final-base.log
```

Observed terminal summaries: 69 passed in `/tmp/a2-fix-final-mgnp.log`; 68 passed and 1 skipped in `/tmp/a2-fix-final-base.log`. The named skip is the locally unavailable real-tokenizer check; base also reports environment/deprecation warnings. These are direct log observations, not a rerun by this reviewer.

The tests directly cover absent or stale receipt/score evidence, wrong source/receipt model and tokenizer identity, unsupported thresholds, escaped/missing files, mismatched arms, malformed provenance, duplicate and leaked score identities, missing retained records, stale prompt hashes, wrong canonical words, nonfinite numbers, invalid argmax/choice, weak inversion margins in either stream, signed-margin inconsistency, and original D/H hash mismatch. Positive cases retain diagnostic baseline failure, allowed extra rejected records and native rounded margins. Existing D-only and loader checks remain present.

## Execution evidence

- Job id and cluster: no scheduler job, inference, or reproduction launched by this reviewer; local read-only inspection of supplied CPU pytest logs.
- Exit code or Slurm state: both supplied logs reached successful pytest terminal summaries; the owning worker retains command exit-status evidence.
- Row counts: no dataset built by this reviewer. Positive matched fixtures expect one retained row per split; timing-only fixtures remain separate.
- Baseline reproduces: no scientific baseline run or claim. The source tests distinguish accepted scored controls from rejected invalid evidence and retain baseline failure as diagnostic.
- Provenance file: no scientific `run_manifest.json` created. This is code-review evidence, not a scientific result.

## What is NOT done

No implementation changes, broad tests, GPU work, API calls, notebooks, git operations, subagents, or worker-narrative review. A1 producer execution and the A2 wrapper/projection gate are outside this review. Actual scored data and training remain later execution gates.

## Open questions

No additional admission change requested. Default: accept the scoped P1 closure; both required interpreter logs now contain successful terminal summaries. This does not authorize fleet reservation or claim that any assembled control was measured successfully.
