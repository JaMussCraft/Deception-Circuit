# Diagnostic transport 254 r2: unbound candidate

This package runs only the two revision-2 diagnostic selections and never produces GREEN or admission. It is not reviewed or authorized for execution. The earlier recipe revision 1 is historical and must not be executed. The existing deployment245 inventory is extended by six frozen diagnostic files; the complete 1,126-file and eight-alias inventory is pinned in `host.py` and `source-inventory.unbound.json`.

The host requires a real Bridges-2 `cis260361p` / `RM-shared` / `rm` 18-CPU, 32-GiB, 25-minute, one-task, no-GPU, no-requeue allocation. Before the first child it requires strictly more than 1,360 seconds: two times 600 seconds, one absolute 15 seconds TERM and five seconds KILL/reap, plus 120 seconds final reserve. Before the second it requires strictly more than 740 seconds. Source checking, image hashing and command setup precede allocation/deadline checks; a fresh check after opening logs clamps the original deadline immediately before spawn. Deadlines can shrink with actual scheduler end, never extend. A diagnostic failure or timeout is data; the second distinct selection is attempted only when its complete remaining budget fits.

The inner process checks effective cgroup mount flags using statvfs for each visible target, retaining raw cgroup mountinfo. Hidden stacked mounts are not rejected. The inner process checks effective cgroup mount flags before `exec` of the original pytest command. Each phase has a separate mode-0700 writable directory; host receipts and the other phase remain outside that bind. The supervisor uses Linux child subreaper semantics to reap its own process group after leader exit and TERM/KILL on timeout. It records raw return codes and diagnostic-only receipts; original plugin phase reports fsync their tracebacks. There is no periodic traceback thread.

Independent source review is required before any binding, staging, or scheduler action. The coordinator must check the source inventory and remote physical files and aliases, the actual host Python 3.6 compatibility and `prctl` behavior, apptainer bind and effective mount behavior, actual scheduler fields, and the private output parent and job ownership. The pure mock tests do not establish those conditions. The coordinator alone stages files and performs SSH, scheduling, and publication. No native tests ran locally.

After review and staging, create a new absolute immutable-path config from `config.template.json` by changing only `status` from `UNBOUND_NOT_RUNNABLE` to `ROOT_BOUND_A3_DIAGNOSTIC_PARTIAL`. Seal its exact bytes with SHA-256; also seal `manifest.json`. The launcher takes exactly `CONFIG CONFIG_SHA256 MANIFEST_SHA256`. The fixed launcher host path and `jobs/job-$SLURM_JOB_ID` must exist on Bridges; the latter must be an empty, ordinary, user-owned directory with no symlink parents. The root should use a held job when needed to create it before release, and should confirm scheduler and binding records first. The private output is never to be reused.

For local focused checks, from this directory:

```bash
/u/swong2/.conda/envs/mgnp/bin/python -B test_transport.py
/sw/external/python/anaconda3/bin/python3.9 -B test_transport.py
```

Both raw results are included as `test-mgnp.log` and `test-base.log`; these cover argument forwarding through relocated launch, config hash swap rejection, remaining-time boundaries and no-Popen on exhausted setup, cgroup mount selection, command environment, and mocked process-group cleanup. They are not an end-to-end Slurm or container run.
