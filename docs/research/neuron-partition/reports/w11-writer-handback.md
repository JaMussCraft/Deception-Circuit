# Hand-back 13: Results report of the four follow-ups of Wed 4 Nov 2026

Agent: report writer W11, Claude Sonnet 5.5. Ticket: the message from the team lead of session claude-5201d56c. Status: resolved, with F9 and F10 marked pending independent recomputation.

## What changed

- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/13-followups-4nov.md`, the results report of follow-ups A to D.
- Committed by the orchestrator from the worktree: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/w11-writer-handback.md`, this file.
- Staged: nothing.

## How verified

```
/u/swong2/.local/bin/research-session lint /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/neuron-partition/docs/research/neuron-partition/reports/13-followups-4nov.md
```

Observed: no output and exit code 0. A grep for parentheses, semicolons, em-dashes and arrows found none after the final edit. Every number was copied from the verdict files, the one-neuron report, the ledger, rulings R15 to R21 and the WORKLOG findings F7 to F10. Totals were checked by sum: this phase's reservations add to 5.75 and its actual seconds add to 10,900, and with the earlier 15.8334 and 27,732 they give the ledger's 21.5834 and 38,632.

## Execution evidence

Not applicable: no runs. The report quotes runs by other agents and I did not run or recompute them.

## What is NOT done

- Reviews 07 and 08 did not exist at 12:47 PM EST, so the SER and one-neuron results are marked pending independent recomputation.
- I did not verify that code is identical between commit 800c903, named by the one-neuron manifest, and the commit in its job name. The report says so.
- The rows of the N2 cell and the one-neuron cell for intact IOI accuracy are not in the hand-backs I read, so the report states them as not stated or not applicable.
- The costs in the options section are estimates from this phase's reservations, not ledger rows.

## Open questions

- Whether to update the report when reviews 07 and 08 land. Default: the orchestrator tells me the verdicts and I amend the two sections.
- Whether option 4, the clause-reading test, belongs among the options, since the lead listed three examples and wrap-up. Default: keep it, because report 05 raised it.
