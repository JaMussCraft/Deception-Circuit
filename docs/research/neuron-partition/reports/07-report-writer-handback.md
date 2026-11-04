# Hand-back 07: report writer, first report filled

Agent: report writer (Claude, Opus), session claude-5201d56c. Ticket: the lead's brief of Tue 3 Nov 2026 to fill the
placeholders of `05-first-report.md`. Status: resolved; review 03 confirmed the headline numbers. The
session hook asks for this file; the lead's brief named only the report.

## What changed

- **`05-first-report.md`.** Every placeholder is filled. The summary leads with the N1 decision and the near miss at
  size 500. Section (c) puts the all-position classes first, with the readout classes beside them as the comparison.
  Section (e) holds the twin and mean tables verbatim for all four classes and the zero table's D-only rows. It also
  has one comparison table of D-only rows and the deciding N2 rows under the mean reference.
- **Evidence.** The table adds the ablation pilot, the all-position ranking run, jobs A, B and C, and the queued IOI
  resolution job, which appeared in the ledger while the report was written.
- **Review 03 round.** The review line now states review 03's CONFIRMED WITH NOTES and ruling R13. A new
  paragraph gives the IOI resolution reading, and the zero table's caption notes zero's own IOI shift of -17.0 at
  size 500. "What is NOT done" lists the 1,000-row IOI measurement as pending under R13
  (`../reviews/03-verdict-review.md`).
- **IOI fold-in.** The 1,000-row result is in the report, labelled exploratory, not pre-registered (R13), in a
  paragraph after the IOI resolution reading, the evidence table, "What is NOT done" and open question 1. N1 stays
  failed. The numbers match the results table of hand-back 02 and finding F5 (`02-w2-ablation-handback.md`).
- **Length.** The report is under 300 lines. To fit, the conditions and baseline tables became prose, the test table
  became one paragraph, and the zero table keeps only its D-only rows.

## How verified

- **Lint.** `research-session lint` reports nothing on the report or on this file.
- **Numbers.** `scripts/check_report_numbers.py --root WT` resolves every number but the "05" of the report title. The
  remaining SER budget is marked derived from the ledger's 13.5 reserved GPU-hours.
- **Spot checks.** The N1 bar flags and the null IOI values were read from
  `outputs/_analyses/neuron-partition/verdict/far_atp_all_c3d7763/verdict.json`. At size 500 only the IOI bar fails,
  on every subset. The 20 null IOI shifts run from -3 to +6. The N2 "D rate change" is D's own deceptive rate, which
  falls from 0.985 to 0.933 at size 2,000.

- **Recheck after the lead's commit.** The lead reported a "Review pending" line at line 7. The file on disk had
  none: the review 03 edits were already in, so the commit had caught the earlier draft. The lint and the number check
  were rerun, both clean except the title's "05", and the lead was asked to recommit.

## Execution evidence

- **No jobs.** This worker ran no job and spent no GPU time. The only temp file is a copy of the earlier report,
  `outputs/_analyses/neuron-partition/writer_tmp/05-first-report.before.md`.

## What is NOT done

- **The IOI resolution job.** It shows as queued with no result, and its numbers are not in the report.

## Open questions

- **Zero table.** The brief asked for every reference's table with all four classes. The zero table keeps only its
  D-only rows so that the report fits under 300 lines. Default: leave it trimmed, since zero does not decide N1.
