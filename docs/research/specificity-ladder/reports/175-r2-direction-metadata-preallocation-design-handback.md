# Hand-back `175-r2`: prepared metadata design after independent review

Agent: Codex Sol. Status: handed-back. Revised design is complete; implementation/publication/admission remain unapproved.

## What changed

Created a distinct [revised packet](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-design175-r2/revision180-resolution.json); original design `359d9528…` and report remain unchanged. It resolves the four findings in [independent review](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-independent-review180/verdict.json).

The final order is now explicit:

```text
_measure_complete_guard_union(...)
reconciliation.before_publication()
prepared_target.final_publication_barrier(reconciliation, receipt)
_publish_measured_pilot_receipt(...)
```

The new barrier compares descriptor/target full-byte witnesses and namespace/root identities against the authenticated ENTRY state, never a newly adopted reference. After those costly scans it runs the original fresh live guard, refreshes the effective allocation deadline, checks the unchanged identity/alias seal and deadline, then invokes the existing bounded writer. Replacement during guard-union measurement, final hashes or fresh guard work cannot silently become the new expected backing. Original live/numeric/post-load checks stay. [Interfaces](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-design175-r2/interfaces.json).

[Path policy](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-design175-r2/namespace-policy.json) pins normalized lexical paths, exact approved resolution and literal ancestor aliases. Target/descriptor roots and leaves cannot be symlinks. A local phase-only witness over resolved roots and scoped namespace identities detects in-phase root/leaf/alias replacement, including identical-content replacement; `object_reference` alone does not. Pre-entry ordinary identical materialization at the exact approved namespace may be accepted; no cross-host inode history is claimed. Unrelated sibling creation is allowed.

## How verified

Read and pinned review180 plus the actual publisher, reader, witness, guard-union and publication order. No source, test, builder, oracle or job was run. [Resolution map](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-design175-r2/revision180-resolution.json).

[Read/hash accounting](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-design175-r2/receiver-and-pass-counts.json) now lists the actual existing helper compositions and a chosen receiver plan: small exact-format checks; same-buffer payload hash/parse; one entry phase-witness scan; one final phase-witness scan. This plans three full logical payload reads/hashes, one parse/freeze and no GPU-time target write; tests must prove the real implementation counts. Existing source/pilot/numeric reads remain separately charged. The original publisher’s repeated completion scans and reference hashes are explicitly included on the CPU producer side; the descriptor must match bytes emitted from the validated value, not merely a self-signed current file.

[RAM/graph accounting](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-design175-r2/receiver-graph-and-RAM.json) includes raw bytes, possible decoded text, expanded parsed graph, frozen graph/memo overlap, retained pilot authority, model staging and numerical proofs. No unmeasured alias sharing is subtracted. One sealed graph supplies the exact requirement identities to reconciliation; equal-value copies, mutation, reinitialization, fork/PID or pickle misuse reject.

## Execution evidence

Not applicable: no runs. Candidate workload `765b22a0…`, its tests and the queued base workflow remain untouched. The packet is a source design, not receiver-cost or paired-feasibility evidence.

## What is NOT done

No implementation, publication, measurement, new job or cap change. Direction M1 still has 0.5 GPU-hours TOTAL. Moving construction does not prove that all remaining reads, guards, geometry/model load, numerical controls, reconciliation, final barrier and receipt publication fit both timing parts. The selected target remains unavailable until its real dependency. [Measurement gates](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/direction-metadata-preallocation-design175-r2/measurement-and-budget.json).

Modified runtime and any new reader must enter the immutable source/hash closure. The final source still needs the original nine fresh prefit numerical cases and complete prefit aggregate/reconciliation using the prepared route; old selected-case admission is not inherited.

## Open questions

Independent180 found phase-scoped immutable transport compatible with the original in-memory target in principle; a new authority-policy exception or per-refresh giant-file witness is not inherently required. Root must now review/authorize the concrete implementation plan and require exact-format, rejection, namespace, graph and resource evidence before a source decision. No guard-result caching or feasibility claim follows from design acceptance.
