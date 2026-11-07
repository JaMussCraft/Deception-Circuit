# Hand-back 265: isolated prepared-target attack fixture correction

Agent: Sol. Status: resolved scoped correction; root review and native acceptance remain open.

## What changed

Only the new candidate directory and this report were written. No existing suite, runtime, wrapper, packet or job
was changed. No staged apply operation was created.

- Candidate directory: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/fixture-correction265`.
- Candidate fixture: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/fixture-correction265/test_a3_prepared_pilot_target.py`.
- Scoped diff: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/fixture-correction265/fixture.patch`.
- Frozen file hashes and obligations: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/fixture-correction265/manifest.json`.

The receiver-resource test now constructs plain attack data through a strict JSON roundtrip. Production frozen
wrappers retain their identity-preserving deepcopy behavior. Existing positive controls, capacity boundary checks
and expected ValueError contexts remain intact.

The final-barrier test now patches the module's live_guard, the actual production call site, delegates to the
original guard, and mutates only while the final barrier is active. An added assertion requires exactly one final
module guard call. The existing mutation-fired and no-publication assertion remains. The passed runner guard is
c.guard, whose actual fixture implementation delegates to the module guard. No production guard was replaced in
source or weakened.

The test names, signatures, decorators and parameter values are unchanged. Other module AST is identical. The
historical collection contains 223 unique identities; a fresh native collection has not been performed.

Original fixture SHA256: `ccdecf2545b4bbc5ab9448f2c2114c72c3e2c6d4a0fbce8dcad7fdb76fdf8bf1`.
Candidate fixture SHA256: `e2a7c5622508974fafafe016e9c3d1d55903302f646f05c5f35630570a1f6e86`.

## How verified

```bash
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/fixture-correction265/pure_check.py
```

Observed exit 0. Four original constructions raise TypeError before validation; four corrected constructions permit
mutation without changing frozen originals, then the exact validator reference-check prefix raises ValueError.
This check exercises the reference rejection prefix only, not the complete native validator or resource controls.

```bash
/u/swong2/.conda/envs/mgnp/bin/python /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/fixture-correction265/pure_check.py
```

Observed exit 0 and identical JSON output. Both interpreter checks together completed within two seconds in the
final local command. The script uses only standard-library AST extraction; no native project import occurs.

The exact production final_publication_barrier AST and corrected nested mutate/barrier/live_guard functions were
executed for each of the three damage variants. Real temporary files were mutated. The original guard returned
before mutation, the final module guard count was one, and the subsequent identity call rejected. Scope, deadline
and identity dependencies in this tiny construction probe are instrumented stand-ins; native witness authentication
and full runner behavior are not established by it. The script also checks preserved original assertions and
rejection contexts, unchanged parameters and unchanged AST outside the two test functions. Candidate syntax compiled.

Pure output and interpreter stdout are under the candidate directory as pure-check.json, pure-check-base.stdout
and pure-check-mgnp.stdout. Actual prior failure excerpts are preserved separately as existing-red-evidence.json.

## Execution evidence

- Job id and cluster: no new job; local standard-library checks shown above. Prior RED comes from diagnostic job
  50318613 on Bridges-2, not an acceptance run.
- Exit code or Slurm state: both local checks exit 0. The cited scheduler snapshot reports the prior job RUNNING;
  root subsequently reported the diagnostic phase reached its 600-second bound and received TERM. This worker did
  not query scheduler state.
- Row counts: four of four pure resource construction probes and three of three pure final-barrier hook probes;
  223 historical node identities, with zero fresh native collection or acceptance results.
- Baseline reproduces: the local exact original construction reproduces TypeError in four of four combinations.
  Actual diagnostic call reports show four corresponding TypeErrors at original fixture line 523, plus one actual
  final-live-guard DID NOT RAISE ValueError at line 652 after 49.94829459208995 seconds. The descriptor-marker case
  has setup passed and no observed call report; it is not counted as a reproduced sixth failure.
- Provenance file: local construction provenance and source hashes are in
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/fixture-correction265/manifest.json`.
  These checks do not claim a scientific run_manifest or commit provenance. Prior actual events come from
  `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/diagnostic-deployment264/progress-1794034303.json`,
  whose exact file hash is retained in existing-red-evidence.json.

## What is NOT done

Native fixtures, complete validators, full suites, fresh collection, packet construction, submission and acceptance
were deliberately not run. No Git, remote command, scheduler mutation or research-session state change occurred.
The same hook correction covers the parameter family, but the descriptor-marker actual call outcome remains
unobserved. Production runtime/source candidate183 remains untouched. Existing failure evidence stays preserved.

## Open questions

Root should independently review the diff, then build a distinct complete validation packet using this candidate.
Default: retain all 223 node identities, run complete native validation on both supported interpreters, preserve
positive controls and original expected-rejection assertions, and require actual evidence before acceptance.
Do not retarget already frozen source or queued packets. No additional user decision is required by this hand-back.
