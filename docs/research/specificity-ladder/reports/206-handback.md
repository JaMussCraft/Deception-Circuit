# BASE on Bridges-2 feasibility estimate hand-back

## What changed

Added this record of a bounded read-only estimate. The detailed measurements and unknowns are in the [JSON evidence hand-back](../../../../.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/base-bridges-port-estimate206/base-bridges-port-estimate-handback.json). No port, copy, tests, model imports, job, scheduler action, or active-candidate change was made.

The local BASE Python 3.9 executable is 16,269,152 bytes. Bridges-2 does not have the executable path or either relevant Python 3.9 site-packages path. The named package trees differ materially: local BASE has torch 2.2.0.dev20231003+cu121 (3.9G), while user site has torch 2.8.0 (1.6G); Transformers, NumPy, pandas, and datasets versions also differ. Nnsight is present only in user site (506K). The six named user-site package directories total about 1.7G before transitive dependencies, interpreter/stdlib, metadata, and native libraries.

Recommendation: do not stage the environment yet. Keep the already-queued Delta BASE comparison intact. A further bounded path and dependency-closure estimate is justified only if multiple future BASE checks can amortize the transfer and verification effort.

## How verified

Checked the local executable size and dynamic links with `ls`, `readlink`, and `ldd`; read package versions from `.dist-info` directory names; and measured named package directories individually with bounded `du` calls. A read-only SSH check confirmed that the exact Python 3.9 and user-site paths are absent on Bridges-2, while the authorized allocation root exists. Whole-tree size probes did not finish within their individual time bounds. No numerical packages were imported.

The pre-work `codex-usage --pause-at 17` check returned `status: ok`, 16% used, and `should_pause: false`; reset was reported at 2026-11-13 16:18:29 UTC.

## Execution evidence

No experiment or job was run. All evidence is filesystem metadata, package-directory sizes, `ldd` output, and the read-only remote path check. The probe values and paths are recorded in the linked JSON evidence hand-back.

## What is NOT done

No complete environment size, dependency closure, native-extension dependency closure, disk/inode requirement, Python 3.9 ABI compatibility, archive feasibility, transfer throughput, or runtime import-path equivalence was established. No environment was exported, copied, or staged. This estimate does not alter or replace the pending BASE comparison.

## Open questions

- Which Python startup, user-site, and `PYTHONPATH` rules select the current BASE packages? The system and user-site trees contain conflicting versions, so copying one without establishing exact path precedence could change behavior.
- What is the full minimal dependency and native-library closure needed for repeated unit and native CPU checks on Bridges-2, and what is its archive size?
- Would that measured one-time transfer and verification cost beat using the existing Delta environment across the planned multiple checks?
