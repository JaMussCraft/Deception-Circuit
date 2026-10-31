# Ticket 04 review: purity judge, full builder, reproducibility test (self-review, 2026-10-20)

The brief asks for `mattpocock-skills:code-review` against the branch base. That skill diffs with git, and
git is forbidden to implementers, so I did both axes myself by reading every new file. An independent review
by the orchestrator is still advised before the builder is used.

Files reviewed: `dataset/mechanism_purity_v2.py`, `dataset/build_deception_v2.py`, `scripts/build_v2.sbatch`,
`tests/test_purity_v2.py`, `tests/test_build_v2.py`, `tests/test_v2_reproducibility.py`. No existing file
was edited.

## Spec axis

| requirement (spec §8, ticket 04) | status |
|---|---|
| Judge = v1 `judge` + `readable_transcript`, `anthropic/claude-sonnet-4.5`, clean pressure prompt + deceptive answer | met (imported, not copied) |
| ~100 survivors per task, seeded, 100 per passing SER wording, partial JSONL per call, `--dry-run` prints one prompt | met |
| Top-up rerun of a short cell at a new seed offset, ledger entry, <= 2 h | met (job 23060023, 0.25 h) |
| Thresholds of §8.1, inclusive, SER fabrication per wording, `none` <= 0.20 per task | met, boundary-tested |
| §14.G4 wording selection; hard stop on FAR/SDR/selected wording; A failure with B selected recorded only | met, tested |
| Builder: one seeded list shared by the three tasks, v1 `seen` discipline, 1.3 x pilot `n_generate` | met; the train list's prefix equals the pilot's list (tested) |
| Gated filters prior -> pressure -> nopressure -> neutral at 0.7 / 0.3 / 0.5, max 120 tokens | met; gating tested by forward counts |
| 25% per (designation x item polarity), variants balanced, variant >= 25%, clause/pair cap from the selection, instance_id order | met with a caveat (S2) |
| D/H/F on identical ids and order, labels flipped, `slot_kind`, `pressure`/`pressure_id`/`neutral_id`, per-condition margins | met, tested |
| Refuse to overwrite; re-check every row of every condition; SER literal truth | met, tested |
| `dataset_config.json` keys; `filter_report.json` with the Required reports; `provenance.json`; comparison set | met (finalize stage) |
| Reproducibility test: byte equality from provenance + row fields, sha256 of pools and sources, skips when absent | met; exercised on CPU-built data, including a drift case |
| Length band <= 12 by clause selection (§14.G6) | met by a pre-registered instance-level window (S3) |
| Full build run, datasets listed, built numbers quoted | **not done: purity hard stop** |

## Standards axis and findings

S1. **Private helpers.** The builder calls `contingency._deceptive` and `_honest` for the per-gate flags, so
the gates are bit-identical to the pilot's rule, and it re-checks every survivor with the public
`contingency.classify`. A public alias in `contingency.py` would be cleaner but would change a file whose
sha256 the pilot jobs recorded. Left as is.

S2. **Greedy selection.** `select_split` is greedy (round-robin over the 8 cells, instance_id order, then a
least-used-first retry ranked by shortfall, variant floor and quota deviation). On a pool whose caps leave
almost no slack it can fall a few rows short of a feasible fill (a 10-clause, 10-pair pool at cap 20 for 200
rows filled 198). A shortfall is handed back or topped up, never met by relaxing a cap. Documented in the
docstring and in the test.

S3. **Length window instead of whole-clause exclusion.** G6 says the band is met by "length-matched clause
selection: shared or flavor clauses may be excluded". The builder drops out-of-window rows before scoring
and reports excluded rows per clause and the clauses with no in-window row. The pre-registered window is
94-106, the pooled range of the three selected pilot cells; the CPU dry path found no out-of-window row in any
of the three cells, so no clause is excluded at present.

S4. **F rows carry `honest_twin_kind: "nopressure"`.** The ticket names the field only for H. D rows carry
null.

S5. **Provenance records the base plan.** A top-up's scale is recorded in the work dir's `plan_<tag>.json` and
the tags in `provenance.topups`, but `provenance.plan` is the base plan. Worth adding if a top-up is ever used.

S6. **Coverage.** The builder is tested end to end on fakes (real `deception_v2`, whitespace tokenizer, rule
model) and on the real tokenizer through the `--no-model` path for all three selected cells. It has not scored
with the real model, because the purity gate stopped the ticket first.

S7. **Small things.** `gate_chunk`'s inner `run` has an unused `cond` argument. `build_filter_report` is long
but linear. `mechanism_purity_v2.main` reloads the survivor files once more for the pooled counts.

## Outcome

No blocking finding in the new code. The ticket stopped at the purity gate (`reports/purity-hard-stop.md`).

## Addendum 2026-10-21 (spec §14.G11 build)

- **New code reviewed the same way.**
  - `dataset/purity_judge_v2.py` and its tests.
  - The builder's construction checks: `construction_check`, asserted per row in `recheck` and reported in
    `filter_report.json`.
  - The purity limitation: `purity_limitation`, recorded in `filter_report.json` and `provenance.json`.
- **S6 is resolved.** The builder now ran with the real model on all three tasks. Its train lists reproduce the
  pilot's contingent survivors exactly (FAR 71/71, SDR 133/133, SER 70/70), which also confirms that lazy
  realization and gating match the pilot harness.
- **S2 did not bite.** `instance_id_order` filled every split, so the fallback was never needed.
- **S3.** The window excluded nothing; the band is 12 and the gap 5.
- **New finding S8.** The builder's sha256 is frozen into each `provenance.json` and checked by the
  reproducibility test. Any later edit to `dataset/build_deception_v2.py`, `dataset/deception_v2.py`,
  `dataset/clause_surgery.py` or `dataset/contingency.py` will fail that test until the datasets are rebuilt or the
  provenance is deliberately re-pinned. This is intended (ticket 04), but whoever edits those files next should
  know.
