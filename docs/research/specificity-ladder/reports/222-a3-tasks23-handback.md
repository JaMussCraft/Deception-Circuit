# A3 Tasks 2–3 handback

Status: handed-back

## What changed

The producer/runtime implementation and distinct frozen correction/GREEN-r2 packet are ready for root execution. Details, pins, resources and launch template are in [report 222](222-a3-tasks23-implementation.md). The original 137 test bodies and all old regression function bodies remain unchanged; five meaningful correction cases were appended.

## How verified

Bounded static/pure checks and direct/relocated wrapper dry-runs passed. Full runtime tests were not run locally. The complete original Task 1 transport/generic/authority/witness ASTs are unchanged. Each interpreter packet requires five actual r1 correction RED failures followed by all 201 r2 GREEN passes, with exact per-function counts and zero errors/skips.

## Execution evidence

Previously accepted Delta RED job `23618388` has a saved normal-completion manifest, supervisor exit zero and 137/137 observed cases in each interpreter: 55 passes plus the intended 52/30 missing-symbol failures, zero errors/skips. Its original publisher baseline reproduces 62/62 expected bytes on both interpreters. Provenance: `W/.superpowers/sdd/plan/task23-red-r2/red-run-01/run_manifest.json`, baseline commit `538109e809285b6ddc45d42df8786270a65f7b12` and exact isolated source pins. No r2 correction RED/GREEN result is claimed.

## What is NOT done

Compute-node correction RED/GREEN, independent review, task acceptance and all genuine source/resource/numerical/GPU gates remain. No worker scheduler action, source publication, git, RS or model execution occurred. Root owns the proposed jobs and Markdown linting.

## Open questions

Root launch target: `W/.superpowers/sdd/plan/task23-green-r2/cpu.sbatch --mode GREEN --environment base|mgnp --output ...`. Each independent shard requests two CPUs, 32 GiB and forty minutes. Source-pins SHA256 is `3700539550ec8d15e39e50c74a46403c526ca2975bbbf804ef7bb7895fc51f10`. Report 222 states the full launch command, runtime uncertainty and deployment-binding review limitation.
