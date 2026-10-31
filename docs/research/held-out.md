# Held-out instance policy

This page states how held-out instances are protected in this repository. The registry that goes with it is
`held_out.json` in this directory. The policy follows spec section 6.4 of the autoresearch-workflow feature, and ruling
R19 of that spec says it is a policy and a registry only: no code refuses to score a held-out instance yet.

## Terms

- A **held-out set** is a fixed list of instance ids, frozen in a file whose sha256 is recorded in the registry.
- A **research session** is any agent or human session that explores, tunes, debugs or chooses between designs.
- A **paper-gating run** is a run whose numbers decide a claim that a paper or a FINDINGS row will state.
- A **provenance path** is the path of the `run_manifest.json` file that the run wrote (spec section 4.6).

## The rule

1. Research sessions never score held-out instance ids. This covers training, evaluation, screening, judge calls,
   debugging prints and any other use that shows a model output or a metric for those ids.
2. A held-out set is scored only by a paper-gating run. That run's provenance path is added to the set's
   `scored_runs` list in the registry, in the same change that reports the result.
3. Once a set is scored for a claim, it is spent for that claim. A second attempt at the same claim needs a new,
   unspent set; re-scoring the spent set after a design change does not count as held-out evidence.
4. A held-out set is created before any session sees results on it. Its file is frozen when it is registered, and
   any change to the file is a new set with a new id.

## The registry

`held_out.json` has this shape. Every entry describes one frozen set.

```json
{"schema": 1, "sets": [{"id": "sdr-v2-heldout-a", "task": "sdr_v2", "path": "data/heldout/sdr_v2_a.json",
  "sha256": "<sha256 of the file>", "n": 200, "created": "2026-11-02", "created_by": "claude-b2cb53cd",
  "purpose": "The claim this set is reserved for.", "scored_runs": []}]}
```

- `id` is a short unique name, and `task` is the task name used by the training and evaluation code.
- `path` is relative to the repository root, and `sha256` is the hash of that file when it was frozen.
- `n` is the number of instance ids in the set.
- `created` is the date of freezing, and `created_by` is the session tag or the person who froze it.
- `purpose` names the claim the set is reserved for.
- `scored_runs` lists the provenance paths of the paper-gating runs that scored the set, oldest first.

## How it is checked

The session audit compares the `dataset_files` of each run's provenance file against the registry. A run that hashed
a registered held-out file and is not listed in that set's `scored_runs` breaks rule 1.

A code guard that refuses to score registered ids is a proposed direction, not part of this policy (ruling R19).

## Current state

The registry has no sets yet. The first direction that needs held-out evidence registers its set here before its
first paper-gating run.
