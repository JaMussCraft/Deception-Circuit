# CPU proof AST diagnosis

Status: handed-back

## What changed

Added the standard-library-only diagnostic and its exact per-function dumps and comparison under the worktree packet `proof-ast-diagnosis226/`. No frozen packet, source or contract changed. The detailed diagnosis is `diagnosis.md`; `comparison.json` SHA-256 is `1ba31a6144ce0106b5a194a7a27bd5bec397f4e312dd1c466ee81d61869369dd`.

## How verified

The five raw source file hashes match the snapshot. Python 3.9.18 reproduces all 20 contract pins; Python 3.12.13 reproduces none. Every full dump differs only by a total of 22 added empty `type_params` fields; omitting only these yields identical dumps and all 20 pins. The generation command and original interpreter of the earliest located contract were not found. Historical schema fixture tests do not invoke the function pin verifier.

## Execution evidence

The preserved Bridges job 50313499 failed at the first function pin with `MODEL_LOADED: false`; its source-before-activation receipt names commit `50e947bb852613e3a270082651f2bd1b7bb0c525` and 511 files plus four literal links. This diagnostic ran only local AST parsing and hashing under the two interpreters; no model, graph, job or remote action ran.

## What is NOT done

No proof, scientific result, runtime fix or rerun is claimed in this diagnosis. Frozen pins and failed evidence are preserved.

## Open questions

A separately reviewed successor can omit only empty type parameter fields, reject nonempty fields, and test all frozen pins and meaningful mutations across both runtimes. Actual execution remains a separate coordinator decision.
