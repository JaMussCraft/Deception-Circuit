# Actual r5 cgroup diagnostic independent audit

Status: handed-back. Actual r5 visibility and top readonly mount accepted for this diagnostic only.

## What changed

Created only reviewer-owned review218 audit evidence and this handback. No actual job, source, adapter, authority or remote changes. [Scoped verdict](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-cgroup-r5-actual-review218/verdict.json) binds job `50311864` to diagnostic manifest `889ee0c986fd392ba1cf00300d93ae46f6714cae10a58175862a3a9ba7a88db7`.

## How verified

Independently rehashed all eight fetched files and all eight exact packet members. Submission, allocation, command, job identity and terminal accounting agree: Bridges account `cis260361p`, RM-shared/rm, 26 CPUs, 48 GiB, zero GPU and five-minute limit. Actual container command contains the reviewed ordered parent-plus-memory-child bind. Both host/container show the same exact own-job membership, unchanged native memory path, required readable counters and their individual native-path samefile checks. Cross-context directory inode values were not recorded by this tiny diagnostic; the genuine entry guard retains that separate check.

The container has two mounts stacked at `/sys/fs/cgroup/memory`: upper mount `1682`, whose parent is lower mount `1676`, has per-mount `ro`; hidden lower mount `1676` has per-mount `rw`. The topmost same-location mount is the one not parenting another at that location. The `rw,memory` superblock field is distinct from per-mount options. This interpretation follows the [Linux mountinfo specification](https://man7.org/linux/man-pages/man5/proc_pid_mountinfo.5.html); it does not reject the hidden lower line.

## Execution evidence

Actual job `50311864` completed with exit `0:0` after five seconds. Host/container exits are both zero, stderr empty, required counters visible, allocation failure/OOM counters zero, and no graph/model/proof admission is claimed. The exact local audit completed in both supported interpreters, two against two expected, both exit zero. [Audit result and exact evidence pins](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-cgroup-r5-actual-review218/audit-result.json), [commands](/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-cgroup-r5-actual-review218/run_manifest.json). No new job or remote action occurred. Last live usage was twenty percent, below checkpoint thirty-three and ordinary cap eighty.

## What is NOT done

No genuine graph/resource bound, model/scoring/effects, transfer acceptance, source publication or GPU admission. No combined adapter213 source has been reviewed. This historical probe did not call the proposed live entry `statvfs` assertion and cannot replace a fresh entry observation in a future job.

## Open questions

The proposed container-only assertion `os.statvfs(inner['frozen_worker_path']).f_flag & os.ST_RDONLY` matches the existing effective-readonly contract. `statvfs` observes mount flags for the selected path; `ST_RDONLY` denotes a readonly mount. [Linux statvfs specification](https://man7.org/linux/man-pages/man3/statvfs.3.html). Place it after unique actual native-path identity/membership checks and before entry permission/worker exec; preserve flags/path in entry evidence and fail closed on error or absent readonly bit. Host readonly must not be required. This adds a fresh check of an existing requirement, with no counter writes or new authority framework.

Root may now authorize distinct combined adapter integration. Its exact frozen source, tests and binding closure still require independent review, along with original transfer, fresh catalogue, actual job/output and resource-proof prerequisites. This acceptance grants no genuine execution or full-score admission.
