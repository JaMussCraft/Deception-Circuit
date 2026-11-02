# A3 edge review handback

Status: handed-back

## What changed

Completed independent review109. Spec compliance: request changes. Code quality: request changes. Sole consolidated high-severity blocker B1: native H-bank width, unique support and source/profile provenance are insufficiently checked; scalar values broadcast through utility clamps, and report intake ignores linked bank existence/bytes. Full report: [109-a3-edge-driver-review.md](109-a3-edge-driver-review.md). No implementation edits.

## How verified

Exact four-file package hashes matched before and after testing. Read accepted plan/rulings, authenticated actual original A1 design/selection/completion, and inspected matched D/I Arrow data. Independent scalar/duplicate/provenance and absent-bank counterexamples reproduce on both interpreters; signed-ranking, budget and exact nineteen-draw null oracles pass. Targeted deployment, guard-consumer, source, variable-length bank, resume and measured-capacity checks pass. Report109 contains precise lines, reproductions, closure requirements and limits.

## Execution evidence

CPU-only, no Slurm job. Both interpreters: four targeted independent/complete-path tests pass, plus eight targeted seams. mgnp durations 85.64 and 27.67 seconds; base 111.77 and 26.92 seconds, with three known environment warnings per pytest invocation. Both intake probes exit 0 and demonstrate acceptance while referenced banks are absent; directories were restored. Logs `/tmp/report109-{mgnp,base}.log`, `/tmp/report109-{mgnp,base}-seams.log`, `/tmp/report109-{mgnp,base}-intake.log`; scripts `/tmp/report109_oracles.py` and `/tmp/report109_intake.py`. Evidence: [mgnp](/tmp/report109-mgnp.log), [base](/tmp/report109-base.log), [mgnp seams](/tmp/report109-mgnp-seams.log), [base seams](/tmp/report109-base-seams.log), [observed exits](109-original-evidence.json).

Each complete path retains 120/120 logical slots, two physical panels, ten mechanism rows, IOI 100 and two MMLU 32 floors per panel. Ordinary/native fp32 baseline margin reproduces exactly: 20735.4765625 versus 20735.4765625, argmax 9 versus 9, identical full-readout digest. Retained tiny operational provenance uses explicit synthetic commit aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa and complete=true/finalized=false. Original A1 run_manifest.json names 5f450dc93dac707af649dee8c8ca60888b2831db. No new scientific result is claimed. Evidence: [mgnp intake](/tmp/report109-mgnp-intake.log), [base intake](/tmp/report109-base-intake.log).

## What is NOT done

No source edits, git, RS mutations, GPU, submission, API or notebook work. No broad author-suite rerun. Real numerical producer and measured cost paths run with explicit injected execution authority; live Slurm/shared Unit F authority remains separately reviewed. Tiny mechanism coverage is not production coverage.

## Open questions

Root should dispatch one bounded B1 fix, then independent focused closure on the new exact package. Production remains blocked pending B1 and shared-runtime acceptance. Live weekly usage 39 percent; reset 2026-11-06 16:07:41 UTC. Historical tool-reading transcription: [evidence index](109-original-evidence.json).
