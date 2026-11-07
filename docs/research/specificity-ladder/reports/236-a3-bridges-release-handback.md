# A3 Bridges test deployment release audit

Status: handed-back

## What changed

Do not release currently bound held job 50316662. Source/config transfer and actual virtual-container checks are coherent, but the held command supplies the frozen launcher’s arguments incorrectly. No transport source revision is needed to correct that root invocation.

**R236-A: actual held command passes named flags to a positional launcher.** Frozen `launch.sh` consumes three positional values and adds `--config`, `--config-sha256`, `--manifest-sha256` itself. The scheduler dry-run and held submission instead pass those flags after the shell path. The resulting host invocation is malformed: `--config --config --config-sha256 CONFIG_PATH --manifest-sha256 --config-sha256`; argparse fails before any binding checks. The container dry-run invokes host-built container commands directly and therefore does not exercise this launcher mismatch.

Smallest correction: retain frozen launcher/source/config and supply exactly `launch.sh CONFIG_PATH CONFIG_SHA TRANSPORT_MANIFEST_SHA`, without the extra named flags, through a correctly rebound held command/job. Preserve the unstarted old job and its receipts. Recheck exact command/spool/parent/output and ordinary root live usage/held/readback gates before release. Root owns that scheduler action.

The earlier effective-mount evidence gate also remains unobserved in the supplied dry-run receipt: `:ro` bind arguments and successful imports do not report actual mount options. Before release, capture effective source/HF/cgroup parent+child read-only and output-parent writable mappings, or identify an existing exact-binding receipt proving them. This is a pending deployment check, not a new source redesign.

## How verified

Independently checked all 1112 current local file hashes/lengths, total 24,256,092 bytes, complete config/inventory equality and all eight literal aliases. The six stage readback file lists concatenate exactly to config.files. Every candidate/oracle/baseline/packet source-pin member is covered with its pinned hash. Observer source-pins remain `e525683d15bae1106c0d8fb4ad8723ffa31f2591e662ee541aa05b98c9cad0cc`; config SHA is `2fd8748eec825bcc379cb54f40be89c9dac2dceb00fff3433994e900d8e42895`; transport manifest is `bd3533cc18025d7d2bf97515060a46f793abd4f4a43609e8dc6c9626d8a6e6e2`. Both reviewed source/transport identities are unchanged.

Read actual host/container/scheduler/held receipts. Same unchanged inventory case passes in the correct virtual namespace, closing review 231-r4’s conditional namespace attribution alongside the nine actual-host passes. Observer dry-run exits 0, expects 223 cases and creates no execution output. Packed Python 3.12.13 runs at the original `/u/swong2/.conda/envs/mgnp/bin/python`; recorded package versions are pytest 9.1.1, numpy 2.5.1, torch 2.11.0+cu128, transformers 5.13.0. Successful imports are dependency availability, not full-suite acceptance.

Scheduler test-only accepts the stated 18 CPU / 32 GiB / 59 minute CPU request. The actual submitted job is held, PENDING/JobHeldUser, runtime zero, no GPU/requeue, correct account/partition/QoS, and spooled launcher SHA `e015a251ff55de96fc495628b3095dbbbd09481f3b90b2474f4727bbc8ec711d` matches frozen source. Those checks cannot repair its incorrect argument list. A harmless local interpreter interceptor using the exact held arguments reproduces the malformed expansion in 0.106 seconds. Evidence: `.superpowers/sdd/plan/a3-green-bridges-binding-review236/{binding-audit.json,launch-argument-probe.json}`.

## Execution evidence

No full/native test or model work has started in the reviewed held-job receipt. Root’s actual dry-run wrapper reports exit 0, virtual inventory unittest exit 0, observer dry-run exit 0; the earlier host wrapper exit 1 with one namespace-dependent assertion remains preserved. This reviewer performed only local file/hash/JSON checks and a harmless shell argument interception, with no remote or scheduler actions. The actual 223 GREEN and five attributable r3 RED cases are still future execution gates.

## What is NOT done

No release approval for the malformed current binding, actual mount-option acceptance, runtime resource feasibility, test GREEN acceptance, A3 source/runtime publication or numerical/GPU admission. BASE stays on Delta. No source edits, git, RS, SSH, jobs or extra agents.

## Open questions

Root can close R236-A through a corrected positional invocation and exact new held binding, without changing reviewed source/config. Capture the effective mount evidence and fresh final live checks before releasing one corrected CPU job. Do not rerun A3 source review or alter virtual aliases for this invocation issue. Root owns report lint and scheduler changes.
