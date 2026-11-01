# Independent review181 — fixed remaining paid blocks

**PASS for root finalization and activation, 2026-10-25.** Reviewed controller179, its final33 mocked tests, inactive manifest template, and all eight prepared receipt/argv/CPU-preflight records from preparation180. No jobs, reservations, controller activation, model calls, API calls, cache changes or budget-ledger changes were made by this reviewer. Root must still finalize receipts/reservations and the source-bound manifest, then run the concrete manifest dry run before activation.

The controller enforces exactly the remaining frozen order: LB harm-pressure → convincing-game → MASK continuations → disinformation → doubling_down_known_facts → known_facts → provided_facts → statistics. Each submission is exactly one H200 for one hour, with no requeue. The manifest requires eight unique root reservation IDs and receipts and the declared8h/36.6h cumulative reservation snapshot; the controller does not allocate/recycle master GPU budget. All receipt source bindings are included in the manifest's union; manifest and source bytes are rechecked between jobs. Root's GPU ledger remains authoritative for the reservation claim.

The global single-use guard and exclusive receipt guards prevent replay after interruption; state is append-only with flush/fsync. One job is submitted and awaited before the next. The corrected queue gate refuses any extant GPU job, including pending or suspended jobs, and never cancels it. A failed/unrecognized submission, missing accounting, requeue observation, non-COMPLETED state or nonzero exit stops without retry/reorder. The controller cannot coordinate submissions made independently after its queue check; root should not launch competing GPU jobs during this batch.

A successful scheduler result alone cannot release the next block. The receipt-content guard must identify the exact submitted job, and the result must be freshly changed and no older than that guard. The unchanged v2 runner applies strict original completion to all remaining datasets; the instructed INVALID exception is not extended. A new narrow content gate independently compares complete item/prompt order/content, selection provenance, native token cap, partner IDs, donor pool/pairing, fresh H200 intact/donor/no-screen provenance, and every state's generation and label coverage. Missing/error/unscored rows stop. This addresses the shallow legacy flags-only completion concern found in review.

Before every dispatch and after every result, immutable source bindings and cache prefix/appends must pass; the shared authoritative $20/5000 budget guard is checked, and any pending or unknown-cost attempt stops for root reconciliation. No key values or generated content enter controller state, no shell interpolation is used for Slurm commands, and the login process performs only CPU/read-only checks and scheduling. The pinned pricing/guard code remains bound; the controller does not independently fetch changed provider prices. Root's existing price review remains the basis for those prospective prices.

Independent validation:

- Final controller suite: **33 passed in mgnp; 33 passed in base Python3.9**. Coverage includes ordered progression, failure stops, source/cache/budget rejection, unknown/pending billing, replay protection, stale/wrong-job output, changed manifest, live/pending GPU conflicts, and fixed content/donor/per-state completeness.
- Independently passed v2/legacy receipt validation for all8 unreviewed templates; verified exact frozen recipient IDs, native donor counts, native512, one H200/3600seconds, reviewed=false and absent reservations/decisions.
- Verified all8 saved actual shell→v2 runner→public CLI CPU dry-run records, associated log hashes and receipt hashes: **exit0**, no credentials passed, no model/API. This is distinct from the controller's own dry run, which validates receipts/commands/guards but does not run the public CLI.

| Split | Recipients | Used native donors | Generation batches | Stop-after limit |
|---|---:|---:|---:|---:|
| harm-pressure | 50 | 50 | 42 | 43 |
| convincing-game | 50 | 50 | 42 | 43 |
| continuations | 28 | 28 | 24 | 25 |
| disinformation | 11 | 9 | 12 | 13 |
| doubling_down_known_facts | 29 | 14 | 22 | 23 |
| known_facts | 37 | 34 | 30 | 31 |
| provided_facts | 50 | 50 | 42 | 43 |
| statistics | 16 | 16 | 12 | 13 |

The extra batch allowance permits scoring after the final planned batch; it does not change the frozen inputs or create another mask state. No acceptance rule depends on whether deception improves. Automatic operational continuation does not establish efficacy: root still reviews raw responses, coherence/refusal, full checkpoint provenance, and scientific limits after acquisition. This lean controller does not independently decode every checkpoint into result text or link every label to its cache entry; no such claim is made. Unexpected failures stop rather than silently reduce denominators or amend another dataset's semantics.

Reviewed artifact SHA256:

- run-fixed-paid-batch.py: `44b6f92ffed8a4e740d926556729cb0d58a667ecfe2e2ef1882dab88ee0aa4fc`
- test_fixed_paid_batch.py: `a7ef37fa55125741da50f57006701db3e48297a577394ed458e1285ab2e995a3`
- fixed-paid-batch.manifest.template.json: `b1e18550f3baacdbf656787887ab5e921dc02dda12eb3e3504bff5ee09f3fe1f`
- fixed-paid-batch/preparation-index.json: `6343e3e22d4793edbad9dad1f8a2a90145cfbb7778c2b9a67208ff3cd553f22a`
