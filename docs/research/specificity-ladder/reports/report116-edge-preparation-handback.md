# Edge successor CPU preparation hand-back

Agent: Codex Sol. Status: handed-back. CPU preparation only; model admission remains pending.

## What changed

Actual canonical and repaired edge CPU preparation ran from the reviewed frozen source
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-runtime-87fceb28b3b4/runtime` at commit
`87fceb28b3b46f4a406c0280db785697a0bbd3fc` into the new output
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4`. The original ruling and execution settings were copied byte-for-byte;
original parents, mandatory selection completion sidecar, matched inputs, historical
CSV and protected registries were consumed through their original paths.

New complete artifacts are `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/canonical/design.json`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/canonical/direction_protocol.json`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/edge/prepared`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/edge/inventory-fit-target` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/edge/inventory-pilot`.
The owning workload API constructs both inventories; the pilot embeds the exact full
initial fit target. The edge CLI exposes prepare and execution stages, so inventory
publication uses the owning CPU producer and validator without crossing model admission.

`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run_manifest.json` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/publication-receipt.json` bind raw artifact file hashes and lineage.
All 509 frozen source files remain ordinary read-only files with unchanged hashes;
all 75 protected input files retain their pre-run hashes and sizes. See
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/source-binding-before.json`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/ancestry-before.json`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/ancestry-after.json` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run_manifest.json`.

## How verified

The exact executable argv, effective environment, working directory, start/end times,
exit code and raw log path are recorded in each command receipt below. The procedure
uses explicit mgnp Python, the original pinned offline cache, only the frozen runtime
in PYTHONPATH, single-thread numerics and disabled bytecode.

```bash
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run-step.py canonical
```

Observed: exit 0 in 315.89 seconds.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/canonical-command.json`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/canonical.log`.

```bash
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run-step.py edge
```

Observed: exit 0 in 350.63 seconds.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/edge-command.json`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/edge.log`.

```bash
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run-step.py inventories
```

Observed: exit 0 in 226.76 seconds.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/inventories-command.json`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/inventories.log`.

```bash
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run-step.py dry-run
```

Observed: exit 0 in 56.79 seconds.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/dry-run-command.json`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/dry-run.log`.

```bash
/sw/external/python/anaconda3/bin/python3.9 /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run-step.py validate
```

Observed: exit 0 in 83.53 seconds.
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/validate-command.json`;
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/validate.log`.

Canonical and edge preparation used the actual frozen job wrappers and authenticated
CPU producer replay. The wrapper dry-run reports source admission with model loading,
writes and execution authorization all false: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/dry-run.log`.
Final owner intake validates the prepared source, complete inventory coverage,
source-bound task membership, exact embedded target, all frozen source hashes and
original assessment/utility content: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/validate-preparation.py` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/validate.log`.

The first owner procedure reached and passed the actual prepared/inventory validators,
then its extra author comparison exited 1 because runtime registry dictionary keys
moved from the old runtime path to the successor path. Those keys resolve to identical
files with identical stored and actual hashes. Only the author comparison procedure was
corrected to verify those exact path aliases; every other MMLU metadata field and every
scientific row remained exact. The complete repeated procedure then exited 0.
Both attempts and the original procedure are retained in
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/first-validate-command.json`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/first-validate.log`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/validate-preparation-first.py`,
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/registry-alias-comparison.json` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/validate-command.json`.
No prepared artifact or source guard was edited.

The original and successor scientific payload digests match after resolving only those
named registry provenance path keys. Assessment rows, utility rows, source prompts,
tokens, order, maps and all other scientific content match exactly. Raw operational
changes are enumerated in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/scientific-comparison.json`.

## Execution evidence

- Job id and cluster: local CPU subprocesses only, with exact commands above; no scheduler job or GPU allocation used.
- Exit code: all final CPU stages exit 0; the preserved first author-comparison attempt exits 1 for the diagnosed registry aliases. See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run_manifest.json`.
- Complete output coverage: pilot observed 96 against expected 96 output keys, with 604 physical requirements and 9664 physical calls; full initial fit target observed 6384 against expected 6384 output keys, with 302 physical requirements and 106684 physical calls. Owning validators check exact complete coverage. See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run_manifest.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/inventories.log`.
- Original baseline reproduces: assessment membership is 100 against original 100 per task; IOI utility is 100 against original 100 and MMLU utility is 32 against original 32, with exact preserved row/token/source content. No numerical baseline or scientific scoring ran. See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/scientific-comparison.json`, `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run_manifest.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-independent-pilots-74efb4d04819/run_manifest.json`.
- Provenance file: `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run_manifest.json`, commit `87fceb28b3b46f4a406c0280db785697a0bbd3fc`; complete file bindings are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/publication-receipt.json`.

For independent M1 sizing, the first isolated actual `validate_prepared` call took
36.63 seconds wall time on the recorded CPU, excluding unrelated owner checks.
Its user/system CPU times and exact interpreter/package/thread profile are in
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/first-validate-prepared-timing.json`.
Actual receiver groups total 151, producing 9664 cached pilot stability keys;
per-task receiver and key counts, integration nodes, streams and IDs are in
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/evidence/receiver-groups.json` and `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run_manifest.json`.
The readiness reviewer was given the raw artifacts after all memory-heavy work ended.

## What is NOT done

CPU preparation does not authorize any model load or initial pilot. No active source,
frozen source, earlier artifact, research-session state, scheduler job, queued mask
mapping, GPU work, large weights, paid API or notebook was changed or used. No git
command or broader test suite ran.

The published target covers initial full fit profiling. Later exact selection and
assessment targets require their actual completed fit/selection ancestry and their
own source-bound measurements; they were not invented or claimed here. All edge M1
reservations share the existing 0.75 GPU-hour ceiling, including any later pilots.
See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run_manifest.json`.

The initial future command template is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/m1-command-template.sh`.
It remains unexecuted and requires root-provided successor ledger mapping and matching
reservation plus an actual H200 allocation. The existing queued mask job and its
original immutable mapping remain unchanged.

## Open questions

Root and the independent readiness reviewer must decide whether the repeated guard
cost and full used-path work fit the bounded initial pilot. Default: hold model work
until that review and fresh source/output/inventory-bound root authority succeed.

The exact next prerequisites are a new root successor mapping and matching reservation,
fresh allocation/lease and storage/capacity checks, and initial pilot controls and
fit-target measurements under the owning guards. Later-stage measurements remain
separate prerequisites. See `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/run_manifest.json` and
`/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4/m1-command-template.sh`.
