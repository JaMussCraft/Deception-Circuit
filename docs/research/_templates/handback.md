# Hand-back <NN>: <plain title of the ticket or task>

<!--
Template for <dir>/reports/<NN>-handback.md (spec section 4.7). Every agent writes one, with these five headings in
this order. Start it early and fill it in as you go, so a HOLD or an interruption leaves a usable record.
-->

Agent: <agent type and model>. Ticket: `<path to the ticket file>`. Status: <resolved / claimed, blocked on ...>.

## What changed

<Absolute paths only. Split them into the files the orchestrator commits from the worktree and the files staged
for the apply tool, with the op file name.>

- Committed by the orchestrator from the worktree: `<absolute path>`, <one line on what changed>.
- Staged, op file `<S/ops/NN-slug.json>`, wave <A>: `<absolute destination>`.

## How verified

<Each command in its own code block, followed by the observed output or its key lines. Do not describe a check you
did not run.>

```
<the exact command>
```

Observed: <output or key lines>.

## Execution evidence

<Required for any claim about a run. If no job or script run is claimed, write exactly: "Not applicable: no runs.">

- Job id and cluster: <job id on Delta / Bridges-2, or the local command>.
- Exit code or Slurm state: <0 / COMPLETED>.
- Row counts: <observed N against expected M, for each output file that matters>.
- Baseline reproduces: <one assertion with both numbers, for example "unablated accuracy 0.912 against 0.912 in the
  reference run">.
- Provenance file: `<path to run_manifest.json>`, commit `<40-hex commit it names>`.

The words confirmed, refuted, verified and replicated may only describe a result whose execution-evidence block above
is complete. Otherwise write "not yet verified" and say which item is missing.

## What is NOT done

<Every checkbox or step not finished, every step skipped, and why. Failures are reported as failures.>

## Open questions

<Questions for the orchestrator or the user, each with the default you would take if no answer comes.>
