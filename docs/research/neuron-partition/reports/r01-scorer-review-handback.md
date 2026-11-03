# Hand-back R01: independent review of the W1 neuron attribution-patching scorer

Agent: independent reviewer (Claude Opus 5.5), read-only. Ticket: the team lead's review brief of Tue 3 Nov 2026 for
commit 1393444. Status: resolved. Verdict: PASS WITH FIXES, with no blockers, two major findings and seven minor
findings.

## What changed

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reviews/01-scorer-review.md`
  (new). This is the review: the verdict, nine findings with evidence and fixes, answers to the seven questions, and
  the commands run.
- This hand-back (new). No code, data or job file was changed.

## How verified

- The scorer tests ran on mgnp against the committed test file: 24 passed.
- Seven source mutations were run through the test suite. Six were caught. The absmean-as-absolute-mean mutation was
  not caught.
- An independent numeric check of the pilot cells and the full D/H reverse cell read `rows.json` and `scores.pt`
  directly.
- A CPU layout check on real FAR rows measured clause and readout positions and answer-position balance.

## Execution evidence

The commands and key output are in the review's last section. The helper scripts are in
`/u/swong2/.claude/jobs/5201d56c/tmp/rev1/`, a temporary directory.

## What is NOT done

- The one-neuron interchange validation proposed in finding 2 needs a GPU, so it was not run.
- The base Python 3.9 interpreter was not run. The brief asked for mgnp only.
- W1's uncommitted CLI and test edits made during the review, which add `--ids` and halves, were not reviewed.

## Open questions

- **Finding 1, for the lead.** Should R6 rank on an all-position AtP, to match the every-position interchange? The
  alternative is to record why readout-only is the intended target.
- **Finding 2, for the lead and W4.** s_D and s_H agree in sign on only 0.63 of the top 100 neurons. Should T_H wait
  for a direct-patch check of the top neurons?
