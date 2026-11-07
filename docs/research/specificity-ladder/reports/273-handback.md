# A3 deployment273 independent release review

Status: handed-back. ACCEPT four existing held CPU releases after the required final root live checks. No native/GREEN or GPU admission.

## What changed

Created only reviewer-owned [receipt checks](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-deployment273-review/receipt-checks.json), pins and [verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/sharded-deployment273-review/verdict.json). Review binds deployment manifest `0da6a11ee021622a4fc153db3dc2d702c663cf55230ee885f2ad45135031bcdc`, accepted source-pins `0028bac99907b0f44781d668d3cd97f58030ac51c493c857456a58b90b7b1833` and partition `73aa13bd780837687cc2953fe6f64cd1df60b92056d856b7aad74d0dfb8a5306`. No source, remote file, RS entry or scheduler state changed in this review.

## How verified

All manifest references, accepted review272-r2, current host members, four configs/pointers and dispatches rehash. Actual bound spooled bootstrap hashes equal the dispatch bytes; both local Delta spool files also rehash. Dispatches invoke the immutable absolute packet wrapper with actual config pointer and exact host-manifest digest. The actual held records match:

| Job | Environment/shard | Account / partition / QoS | CPU / RAM / wall |
|---|---|---|---|
| 23631878 | BASE / zero | beto-delta-cpu / cpu-preempt / beto-delta-cpu | two / 32GiB / eighty minutes |
| 23631880 | BASE / one | beto-delta-cpu / cpu-preempt / beto-delta-cpu | two / 32GiB / eighty minutes |
| 50319105 | mgnp / zero | cis260361p / RM-shared / rm | eighteen / 32GiB / eighty minutes |
| 50319108 | mgnp / one | cis260361p / RM-shared / rm | eighteen / 32GiB / eighty minutes |

Each has one node/task, zero runtime, no GPU TRES, no requeue/restart and exact command/workdir/output paths. Actual configs bind distinct job/child/execution namespaces and expected shards. All four binding readers run check_source successfully on the full 1,133-file/eight-alias closure. Metadata and physical routes match the frozen inventory. The separately authenticated transport-inventory control SHA `0d35b0ed94c5e5eb0759adee9add614bbe21842a9d66d34e121aaa87bf17dd9c` matches its actual stage receipt.

## Execution evidence

Actual Bridges Python3.6.8 imports/dry-run and subreaper setup succeed; the exact SIF hash is checked. Three real container invocations pass through the source-bound inner gate with distinct stage receipts. Each observes host-root readonly flags, writes only child output, preserves the host canary and records effective cgroup root15/memory4111 plus fourteen raw mountinfo rows. This is a separate smoke namespace with substituted pure probe argv, not native or actual held-job execution.

Remote audit matched 740 files and staged the missing 393, plus two dispatches; later actual binding checks cover all 1,133 files and eight aliases. Initial missing-job-id smoke and missing-control-manifest binding failures are preserved. Root corrected only smoke inputs and staged the authenticated control; the same held job 50319105 and frozen source then pass binding. All four registrations succeed. No job was released in this review. Final readbacks checked here: 4 of four, each exit zero with fresh source/control/config/pointer/spool equality, exact held resources and canonical owned empty roots with child absent; observed raw mode0o2700 means inherited setgid with permission bits0700. Root must inspect all four and its final live usage before release.

Each 4,800-second budget equals 610 baseline +90 oracle +3,600 suite +120 final reserve +20 single cleanup +360 nonstage overhead. This is a bounded proposal, not proof that native validation finishes. Initial local Delta checks confirm canonical, owned, empty roots with permission bits0700. Later final readbacks are checked below; raw mode0o2700 includes inherited setgid and retains no group/other access. Latest usage is forty-two percent, cap eighty and cadence forty.

## What is NOT done

No actual compute-node native/controller/resource outcomes, complete 223 coverage, final trusted aggregation, model/GPU/scientific admission or protected-heldout authorization. The four independent allocations are not interchangeable, and no retry, replacement or extension is accepted here. Initial failed checks remain historical evidence.

## Open questions

Before each release, root must freshly verify usage/no freeze; the same held/unstarted job and exact resource tuple; unchanged source/partition/host/control/config/pointer/spool bytes on actual routes; and the actual root's canonical no-symlink ancestry, owner, permission bits0700, emptiness and absent child/execution. Inherited setgid is allowed and recorded transparently. The pointer checks matter because the immutable bootstrap reads config.sha256 at launch. Then root may release each of these four existing jobs once and record each receipt. Preserve bounded monitoring and all partial outcomes. Both exact interpreters still require normal original controls and complete disjoint 223 coverage under the trusted aggregation map.
