# A2 grader snapshot drift diagnosis

Agent: Codex Sol. Status: handed-back. Read-only diagnosis/remedy proposal.

## What changed

No source, catalogue, group receipt, failed preflight, ledger or plan changed. Diagnosed
failed preflight147 using compact selective receipt extraction and small registry/code
inspection only. The original G1 groups file remains hash-identical:
`8879dbaae5a5f69a801574eb67deab9c7fc5a037eb89963ed606a265580a74c8`. No validator/model/GPU/refreeze was run locally.
Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence/diagnosis.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence/run_manifest.json`.

## How verified

**The cause is unrelated catalogue metadata, not changed grader semantics/code.** The
frozen receipt records primary catalogue `5f3ef570...`; current primary is `5b92c9e5...`.
Runtime/worktree catalogue `f8c7dbb9...` is unchanged. Exact hashes/path aliases are in
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence/diagnosis.json`.

An ordinary historical catalogue copy in the deception-divergence worktree exactly
matches the receipt's recorded primary byte hash. Comparing that exact old catalogue
with current primary shows only:

- Top-level updated date advanced.
- The unrelated `deception-divergence` entry changed `status` from claimed to paused,
  cleared `claimed_by` and `claimed_at`, and advanced its updated date.
- No direction was added or removed; the entire `specificity-ladder` entry is identical.

This is not a specificity-ladder need/status change. Exact values and the byte diff:
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence/exact-catalogue-diff.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence/catalogue-byte-diff.patch`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence/recorded-primary-catalogue-exact.json`.

The frozen code constant, actual covered grader-file set/content digest under immutable
runtime, primary and worktree, and all specificity-ladder registered fingerprints equal
`866fd15dd30b695e46ffe955b09894fb831af92e2b9015eafbd7f0eee151d2f9`. Each covered file was independently hashed; no full model or
receipt parse was performed. `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence/diagnosis.json` retains every small file hash and entry.

The dependency is explicit in frozen source: `ladder_pipeline.grader_registry()` checks
actual grader code against its frozen constant and checks the specificity entry in both
catalogues, then returns **whole catalogue file hashes**. `a2_pipeline._validate_live`
compares those whole-file hashes to the frozen group receipt. The guard therefore
correctly rejects recorded byte drift under its existing contract, even when unrelated
ownership/status metadata alone changed. No guard was disabled or reinterpreted.

## Execution evidence

- Classification: compact static/source/JSON diagnosis; no scientific numerical verdict.
- Control: a byte-exact historical primary catalogue matches the frozen recorded digest;
  current file/code/fingerprint comparisons isolate the unrelated changed fields.
- Original G1 receipt was opened read-only via mmap; only the unique small
  `grader_registry` dictionary with exact expected path keys was decoded. The file hash
  still matches the frozen source binding. `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence/compact-diagnosis.py`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence/diagnosis.json`.
- Failed CPU preflight147 remains unchanged and unaccepted; there is no complete
  preflight or GPU admission. Existing raw failure/accounting remain in its evidence.
- Current catalogues are preserved as evidence copies only; live files were not edited.

## What is NOT done

No source/guard change, receipt rewrite/re-signing, new comparison/freeze, model, GPU,
submission/retry, heavy local validation, ledger/RS/Git/scheduler mutation, API, notebook,
subagent or assessment-effect inspection. No conclusion changes the original scientific
scope, controls, failed stability, old reservations or caps.

## Open questions

**Smallest immediate safe remedy:** root may authorize a fresh prospective G2 freeze in
a new namespace using the unchanged owning API, original A1 parents/mandatory sidecar
and original all-source comparison/records. The API re-audits every source and records
the current catalogue provenance. Verify all scientific fields, groups/memberships,
operations, IDs, bank keys and geometry agree with G1; bind the new receipt and fresh
launch/pilot namespace before another preflight. Preserve G1 and failed147, without
in-place metadata refresh or checksum re-signing. Exact prospective command and checks:
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence/remedy-proposal.json`. Nothing has been executed.

This does not cure the systematic whole-catalogue dependency: a later unrelated release
can stale G2 again, including while waiting for GPU. If root chooses a lasting correction,
review a narrow versioned semantic-grader binding separately: actual covered grader
files/code digest, registered specificity fingerprint, expected catalogue paths and
fresh validity checks remain mandatory; whole-catalogue hashes remain provenance rather
than scientific semantic equality. Test benign unrelated catalogue changes and failures
for grader code, specificity fingerprint, missing/duplicate entries and path provenance.
Such a source/schema change needs its own focused review/freeze and genuinely new
prospective receipt; it cannot retroactively upgrade G1 or bypass current guards.
