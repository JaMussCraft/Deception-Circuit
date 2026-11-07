# Remaining native CPU continuation proposal

Status: handed-back

## What changed

Propose original cases 32–48 in one unchanged `pilot_cases` call on an actual Slurm CPU node, preserving all 32 completed cases. The full remaining scope is 31 cases; the later 14 cases 49–62 require a new decision after observing this chunk. No native fixture, job or aggregate has been executed by this proposal. [Exact cases and source identities](proposal.json).

## How verified

The external driver changes only reviewed scope/cap/output parameters from the completed job137 driver. Allocation validation, original numerical execution, controls, per-case full authentication, immutable Slurm sidecars, source checks and no-overwrite behavior remain. Syntax compilation and `bash -n` passed; the allocation helper is byte-identical. Frozen source hashes match. [Exact diff](accepted-driver.diff), [static checks](protocol-checks.json), [source and measurement closure](proposal.json).

Every future case has an exact operation/shape-class match among actual compute-node cases. This comparison retains model/profile/sites/cell families/group sizes and separates the MMLU path; it excludes source-name/hash identity only for planning the generic paired-source cost. Actual SER runtime has not been observed. Full identity and inventory checks still run before execution. [Case comparability and matching indices](proposal.json).

## Execution evidence

The derived next-chunk envelope uses maximum observed CPU setup (359.24 seconds), first authentication (159.51), later authentication (66.09 per case), and type-matched original case-work maxima. Original case work already contains native forwards. It adds 2 seconds per case for sidecar work and 30 seconds for final exit, then 20 percent buffer. The derived subtotal is 2320.51 seconds and buffered value 2784.62 seconds. These are planning inputs with uncontrolled filesystem caches, not guaranteed timing. [Exact formula and observed references](proposal.json).

Request a 2,820-second child cap plus 15-second kill grace within a 49-minute CPU interactive allocation, with 4 CPUs, 32 GiB and zero GPUs. The outer margin is 105 seconds. Require 16 GiB finite ancestor headroom before launch. All Slurm environment provenance remains genuine. [Bound and resource checks](protocol-checks.json), [launcher](launch.sbatch).

The derived buffered envelope for all 31 remaining cases is 4641.76 seconds, exceeding the interactive hour. Cases 49–62 currently have a derived 2436.33-second buffered envelope, but their final cap must be reconsidered after this chunk. [Full and later cost envelopes](proposal.json).

## What is NOT done

No new case, source/harness change, model forward, submission, retry, aggregate or production admission occurred. The proposed files are external operational drivers only. Case results remain scientifically injected and nonauthorizing. Root must review the exact manifest and authorize any execution.

## Open questions

Root chooses placement and submits only after acceptance/test-only. On failure preserve every artifact and stop. If successful, report actual case/auth/publication/resource timings before sizing the final scope. Full pilot aggregation remains a separate bounded operational problem.
