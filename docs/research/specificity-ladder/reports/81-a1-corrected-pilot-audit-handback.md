# Hand-back: Corrected A1 pilot artifact and timing audit

Agent: Codex independent review worker. Status: handed-back.

## What changed

No production, test, frozen-input, or result files were changed. Review artifacts, to commit by explicit file list, are:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/tools/81-corrected-pilot-audit.py`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/81-corrected-pilot-audit.json`
- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/81-a1-corrected-pilot-audit-handback.md`

Each is mirrored at the same direction-relative path in `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/`.

Verdict: accept the corrected pilot as complete for its frozen pilot scope. No actionable artifact or provenance findings were found. A full run on the same A100 with the same batch geometry has adequate bounded timing evidence for a three-hour reservation. This recommendation admits execution, not a scientific verdict.

## How verified

The read-only audit uses actual artifact readers, prepared-design validation, selection-sidecar validation, expected row/control generators, protected-registry checks, grader checks, bank-reference resolution, batch constructors and donor-map validation. It constructs no model or tokenizer, touches no weights, and requests no GPU or API.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 /u/swong2/.conda/envs/mgnp/bin/python docs/research/specificity-ladder/tools/81-corrected-pilot-audit.py > docs/research/specificity-ladder/reports/81-corrected-pilot-audit.json
```

The working directory was `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`. Observed output: `artifact_audit_passed`. The script also compiles under base Python. No broad test suite was needed for this artifact-only review.

The audit rehashes the current production source and data through the actual helpers, checks model and tokenizer revision identity, validates the content-hashed score envelope, and compares the published run manifest with its copy inside the score. It checks design, selection, group, bank, domain, utility-sample and selection-file sidecar links. The derived audit counts are 16 code files, 208 source files, three selection-source files, two protected-registry files, and two grader-registry files. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/81-corrected-pilot-audit.json`.

Fresh design scientific fields equal the original design exactly. Its only differing top-level fields are `commit`, `code_hashes`, and `grader_registry`; the sole differing code hash is the reviewed calibration implementation. Groups, raw selection evidence and every mean-bank value/provenance field equal the old selected artifact exactly. Fresh selection differs only in design hash and execution provenance. Both semantic-equivalence receipts' file-byte hashes match independently. The differing registry row is only `instructed-route`, with status and claim bookkeeping changed; the specificity-ladder entry and frozen grader identity remain unchanged. These comparisons use raw old/new artifacts, not an author's report.

Every score row's recipient source record, canonical token labels and group membership matches reconstructed frozen batches. Every donor-operation row matches its frozen donor-map provenance and support flag; computed identity flags are allowed to reflect the runner's explicit token-identity check. Mean-bank references resolve to the exact selected artifact. Unsupported rows remain present rather than disappearing from the denominator.

The pilot finalization helper raises exactly `pilot cannot emit final verdict` when called with `final=True`. Pilot and non-injected flags are explicit. The older complete-pilot absence is not hidden by this check.

## Execution evidence

- Job and cluster: `23417413` on Delta; `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/pilot-4/accounting.txt` records main/batch/extern `COMPLETED`, exit `0:0`, 399 seconds. Its stdout says `score: complete`.
- Row counts: 1,188 observed against 1,188 unique frozen expected row keys, and 144 observed against 144 unique frozen positive-control keys. All 1,188 rows have valid assays and maximum logged empty/self-replay margin error zero. Of these rows, 924 are supported, 708 are gate-valid, and 336 are marked degenerate; these flags are not interchangeable. All 144 positive controls have donor full-vocabulary fp32 logit-recovery error exactly zero, using all sender keys including embeddings and excluding READOUT. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/81-corrected-pilot-audit.json` and its raw score source below.
- Baseline reproduces: intact-versus-empty/self replay has logged maximum margin error zero against expected zero, and production assay validity also enforces argmax agreement. The exact SER/I clean pair `00b809b51070` that previously failed with `0.041628360748291016` now has donor recovery error zero. There is no old complete scoring artifact to compare scientific effect values against: the original pilot stopped at calibration. Original failure evidence remains `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/logs/lad-a1-pilot-23415975.err`.
- Provenance: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/pilot-4/score/run_manifest.json`, commit `5f450dc93dac707af649dee8c8ca60888b2831db`; exact content-hashed results are `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/pilot-4/score/score.json`. The model is pinned Llama-3.1-8B-Instruct, BF16 on A100, with the recorded tokenizer and frozen grader identity.

Exact frozen inventory, derived using actual expected-key helpers and recorded collapsed duplicate groups, is in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/81-corrected-pilot-audit.json`:

| Scope | Pilot rows | Full rows |
| --- | ---: | ---: |
| FAR mechanism (derived) | 360 | 9,000 |
| SDR mechanism (derived) | 360 | 9,000 |
| SER mechanism (derived) | 360 | 9,000 |
| IOI, across the three mechanism groups (derived) | 60 | 1,500 |
| MMLU, across the three mechanism groups | 48 | 384 |
| Total | 1,188 | 28,884 |
| Positive controls | 144 | 3,396 |

Each mechanism's full scope contains one hundred assessment IDs, both designation streams, all five conditions, and nine operation/seed combinations. The independent-resample operation retains its three frozen donor seeds. Utility scope is one hundred IOI and thirty-two MMLU items for each mechanism group; inapplicable operations remain excluded as specified. No scientific efficacy interpretation is drawn from the pilot's four IDs per mechanism.

Timing and memory values come directly from `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/ladder-5f450dc/pilot-4/score/run_manifest.json`: model load 32.8757 seconds, scoring compute 335.8885 seconds, model-load-plus-compute stage 369.6934 seconds, peak allocated 19,575,337,984 bytes and peak reserved 20,759,707,648 bytes. The stage excludes artifact publication. Accounting therefore includes about 29.3 additional seconds outside that stage, derived from the accounting and stage values.

The shape census mirrors the scorer's actual singleton capture calls, not its outer batching count. It retains original parent padding; mechanism donor parents use the full source pool in batches of eight, and utility donor parents use the helper's default batch size of sixteen. Calibration uses the larger original parent width. Scientific scoring retains its own recipient geometry. Supported donor operations add a donor capture; unsupported operations still execute intact/empty/self controls but omit the patched capture. Utility calls repeat for each mechanism group.

Derived capture inventory and cost proxies are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/81-corrected-pilot-audit.json`:

| Workload | Pilot | Full |
| --- | ---: | ---: |
| Singleton forward captures | 5,268 | 129,480 |
| Sum of padded forward widths | 575,019 | 14,168,955 |
| Sum of squared padded widths | 73,001,245 | 1,824,059,195 |
| Largest padded width | 526 | 526 |
| Largest unmasked length encountered | 149 | 526 |

The largest shape is MMLU. The pilot already includes thirty-six all-sender calibration captures at that padded width; the full run includes 555 captures at it. Full scientific MMLU scoring also reaches it, whereas pilot scientific MMLU recipients have width 148. MMLU forward count grows by eight times, but its padded-token work grows by a derived 14.16 times and its squared-width work by 21.74 times. IOI's maximum width grows from eighteen to twenty-one. Mechanism maxima are already covered in pilot donor captures: FAR 121, SDR 139, SER 130. These are geometry facts, not new measured runtimes. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/81-corrected-pilot-audit.json`.

Using the measured compute time and loading the model only once yields derived stage projections of 8,288.5 seconds by capture count, 8,309.5 seconds by padded-token work, 8,309.9 seconds by a Llama linear-plus-attention FLOP proxy, and 8,425.6 seconds by squared-width work. The latter deliberately overweights long attention shapes as a sensitivity calculation, not a proven runtime bound. Aggregate work ratios are about 24.58 to 24.99; they were calculated from the actual full inventory rather than assuming a uniform expansion. The largest taskwise linear-work ratio is IOI's derived 27.26, which would project about 9,189 seconds if applied to all measured compute. That remains below the proposed reservation. Evidence and formulas: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/81-corrected-pilot-audit.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/tools/81-corrected-pilot-audit.py`.

The capture-kind strata provide a further derived overhead check: calibration padded-token work grows by about 19.67 times, ordinary intact/empty/replay work by 24.87 times, and donor-capture work by 27.39 times. The expensive all-sender calibration workload therefore does not expand faster than the aggregate estimate. Per-kind times remain unmeasured. Evidence: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/81-corrected-pilot-audit.json`.

Recommendation: reserve three hours on one A100 with the unchanged batch geometry. This provides a derived buffer of about forty minutes beyond the squared-width projection, including publication and scheduling-wrapper overhead. No additional timing run is required for this admission: the largest padded all-sender shape has already executed within memory. Longer unmasked MMLU content and a greater share of long scoring calls remain a runtime uncertainty, not an established resource failure. A different GPU, batch geometry, group set or tokenization would require a new assessment.

The primary ledger snapshot gives a derived A1 reservation total of 1.5 GPU-hours and 1,992 actual GPU-seconds across its completed A1 jobs, excluding A2 paths. Adding this reservation yields 4.5 reserved A1 GPU-hours against its phase cap of 25, leaving 20.5. The session-wide ledger total includes the separate A2 fleet and is not the A1 total. Sources: `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/ledger.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/START.md`, and the derived audit JSON above.

## What is NOT done

No full assessment run was submitted or executed by this reviewer. The runtime estimates are projections from one measured pilot and do not guarantee completion time. Per-task or per-hook timing was not recorded by the production pilot, so relative overhead cannot be fitted independently.

No model weights were reread and no tokenization was regenerated. Identity was audited through pinned runtime provenance, exact immutable tokenized data equivalence, current source/data hashes and sidecar validation. No native-logit or residual recovery claim beyond the production pilot's recorded full-vocabulary fp32 control is made. Noops here mean the production margin/argmax checks, not an unrecorded whole-logit equality test.

No scientific efficacy, final gate verdict, full-run pass, merge or findings-register update is claimed. The pilot remains unable to finalize, and original artifacts retain their original identities.

## Open questions

No blocking artifact or compute question remains for the proposed unchanged full run. Default: the orchestrator dry-runs the exact full wrapper, reserves the suggested duration through the primary ledger, and launches only under the existing session authorization. Audit the complete output and its noops/recovery controls before any scientific verdict.
