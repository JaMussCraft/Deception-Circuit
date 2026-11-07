# A2 exact fixture transport to Bridges-2 implementation plan

> Root-assigned implementers use executing-plans after root accepts this plan; no extra agents. Root alone reviews/commits by explicit file list and owns copies, transfers, scheduler, RS and publication. This design authorizes no implementation or deployment.

**Goal:** run the unchanged Task2 fixture RED/GREEN packet on Bridges-2 with exact selected Delta interpreter/package bytes and literal origins, without porting the scientific BASE environment.

**Architecture:** adapt the accepted229-r3 host transport/process-group mechanics. One real Bridges host wrapper launches four isolated SIF invocations, one per environment/phase, with sealed actual host allocation receipts and only fresh private phase outputs writable. A new fixture observer variant consumes those receipts, preserving original commands/tests/oracle; it never invents Delta Slurm metadata or needs container scontrol.

**Tech stack:** host Python3.6 stdlib; pinned Ubuntu2204 SIF; exact BASE3.9.18/pytest8.3.3 slice; existing packed mgnp3.12.13/pytest9.1.1; original pytest fixtures. `contracts.json` supplies exact paths, hashes, names, resource/deadline fields and unset deployment bindings.

**Spec:** root's design-only250 brief, source r4 observer/pins/oracle, inventories248/251, accepted229-r3 transport and CPU-proof actual host receipt precedents. Proposed technical choices remain subject to independent review and root acceptance.

## Exact source and global constraints

`W=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder`, `S=W/.superpowers/sdd`.

- Packet: `S/plan-plan-a2-full-score-operational186/task2/green-r4`; pins SHA256 `ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4`, all266 members immutable.
- Candidate: `S/plan-a2-full-score-operational186/candidate` (single-plan namespace). `packet.parents[4] == W` is valid. No path correction is needed.
- Baseline: `S/plan-plan-a2-full-score-operational186/task2/green/root-dispatch/candidate-before-interface-review`, with unchanged seven-member manifest.
- Runtime inventory251: `S/plan-a2-exact-base-inventory251/manifest.json`, SHA256 `d15679ce4f535fac8f8ec737cd9c52980ff05ce87d4cc0bd93f285d01f9ecbb1`; proposed1103-entry/89-ELF inventory, eleven system dependencies. This is not remote compatibility evidence.
- Reuse host/cleanup/shell patterns from `S/plan/a3-green-bridges-transport229-r3`, not its A3 counts/resources or mgnp-only scope. Reuse actual host receipt ideas from `S/plan-a2-full-score-bridges-cpu-proposal199/proof-adapter-r4/host_supervisor.py`, not failed proof authority.
- Preserve valid Delta job23623058, both queued jobs and all running jobs/results. No cancellation, retarget or native scientific source/test/diagnostic239/A3 change. Existing Bridges authorization covers placement; technical plan/runtime acceptance remains required.
- No GPU, weights/model, native scientific pipeline, effects, cache downloads, operational CPU_COMPLETE, release, ledger transition or scientific cap change. Ordinary80-percent usage cap and forty-point native cadence remain root checks.
- This task writes only this plan, contracts and primary250 handback. No code, bundle copy/install, SSH, jobs, tests, git, RS, source publication or extra agents.

## Review focus

1. Byte-identical Python/packages can still fail SIF ABI/startup/import resolution: actual bounded compatibility gates are mandatory.
2. The observer-inspection hook must retain different original RED/new GREEN targets or the RED signature changes.
3. Missing container scontrol must not produce fake Delta facts: real immutable host receipts establish actual Bridges identity.
4. Missing .pth/helper/ELF/alias closure can change imports despite equal versions: close actual imports and declare unused exclusions.
5. Expiry and leader exit must not allow late success or live descendants: preserve fresh entry checks, nonincreasing deadlines, strict post-reap checks and owned-group cleanup.

## Proposed file layout after acceptance

Only new `S/plan-a2-exact-fixture-bridges250/candidate/{host.py,observer.py,launch.sh,runtime-probe.py,bindings.template.json,test_transport.py}`. Root generates separate immutable runtime/fixture closure manifests and actual bindings. Use controlled exact copies, not a generic environment/package manager. Do not modify original packet or production files.

### Task 1: close the fixture-only runtime and pass actual compatibility gates

**Interface:** `runtime-probe.py --closure PATH --closure-sha256 SHA --payload-pins SHA --environment base|mgnp --output FRESH` emits `FIXTURE_RUNTIME_COMPATIBILITY_ONLY`, with no allocation/admission claim. Closure records exact virtual/physical paths, lengths/hashes or literal symlink chains, roles, provider maps and exclusions.

- [ ] Test first: wrong executable SHA/3.9.13/pytest origin, missing recursive ELF target, required startup omission, unlisted helper read or unapproved provider rejects. A matched version or local ldd alone cannot pass.
- [ ] Complete proposed251 before bundle acceptance: source symlink/assets/bytecode policy, PT_INTERP/DT_NEEDED/RPATH/RUNPATH and actual undefined symbol needs. Conservative readelf label unions are not a minimum ABI. Preserve executable `/sw/external/python/anaconda3/bin/python3.9`, stdlib/extensions, fourteen Anaconda targets and selected seven pytest distribution roots/metadata at original prefixes. Exact versions/origins/build/SOABI are in contracts; no rebuild, pip install or binary patch.
- [ ] Preserve actual fixture-required `distutils-precedence.pth`/`_distutils_hack` bytes, behavior and pure transitive imports. User-site origins remain enabled; no `-S`/`-s` shortcut. Absent sitecustomize/usercustomize stay absent. Unused namespace .pth/preloads and easy-install's mxeval path may be excluded only after bounded startup/import evidence shows no required fixture/helper dependency. Disclose those sys.path/meta_path exclusions; do not copy full mxeval/data/native packages or claim scientific environment equivalence. Unexpected required imports stop for narrow closure review.
- [ ] System provider choice: the pinned Ubuntu SIF's loader/system libraries, explicitly hashed/resolved and ABI-tested. Source251's eleven system dependencies are references, not blindly copied libc/loader overrides. Exact Anaconda libraries remain at literal origins. Close all declared ELF providers and actual dynamic imports; missing symbols/assets/CPU-kernel compatibility fails the gate. Never fall back to Bridges3.9.13.
- [ ] Root stages the reviewed slice after implementation acceptance. Before a fixture CPU job, run actual SIF read-only input probes, bounded30 seconds per environment: exact versions/bytes/origins/startup, actual ELF resolution/maps, stdlib/pytest dependencies and dynamically loaded stdlib-only helpers. Configuration-bound helper imports use tiny fixture metadata without forging actual Slurm fields or executing main/native paths. Hash-only GPU/native probe artifacts are not executed. Reject unexpected scientific/model imports. Actual `pytest --collect-only` must resolve the original paths and collect22 RED-selected and226 GREEN cases under each runtime. No full suite/native workload on login.
- [ ] Reconcile required opens/imports with the staged closure and freeze accepted probe/manifests. Inventory251, source versions or collection alone is insufficient. Preserve failed gates and stop; no unreviewed trimming, compatibility substitution or environment-port expansion.

### Task 2: truthful Bridges host/observer transport

**Interfaces:** `host.py --config PATH --config-sha256 SHA --manifest-sha256 SHA`; `observer.py --environment base|mgnp --mode red|green --host-receipt PATH --host-receipt-sha256 SHA --output FRESH --payload-pins-sha256 SHA --deadline-unix EPOCH --deadline-monotonic T`. Keep the public `command(python,out,n,mode='green')` function body unchanged from r4; its source hash is in contracts. Importing it for the original source-inspection test must not run main.

- [ ] Test first: real Bridges accepted/Delta claim rejected; no scontrol needed inside; wrong job/UID/host/config/hash/phase or swapped receipt buffer rejected; omitted entry198/changed oracle/duplicate names rejected; expired/shortened deadline causes zero Popen; leader-exited grandchild cleaned; late zero rejected; swapped positional arguments and relocated spool wrapper rejected. Use bounded pure fixtures and retain source tests unchanged.
- [ ] Adapt229-r3's Python3.6 actual allocation/path/cleanup machinery. Validate real own numeric job/UID/host, `bridges2`, cis260361p/QoSrm/RM-shared, one node/task, five CPUs/8GiB/six minutes, no GPU/requeue/restart and correct physical WorkDir. Validate actual job cgroup scope using existing patterns. Do not invent Slurm vars/server responses.
- [ ] Host-before receipts bind raw actual allocation/cgroup, phase/environment/nonce, argv/config/transport/runtime/SIF/payload hashes, output and fixed deadlines. Keep receipts outside all child-writable binds, mount read-only and authenticate/parse the same bytes. Observer checks actual inherited Bridges identity without scontrol. Fresh host-after/final acquisition remains real; never overwrite before receipts. Existing internal unit-test Slurm mocks remain fixture-local, never actual host evidence.
- [ ] Stage all266 payload pins, baseline manifest and actual fixture-read closure read-only under the proven physical-to-original-virtual Alignment mapping. Assert W using the original payload, not the new directory. Preserve literal aliases/targets and exact helper origins. No scientific cache/weights bind or whole-project writable bind.
- [ ] RED: CPU-under-test is the original baseline; `A2_GREEN_OBSERVER` is original `task2/green/run_cpu_green.py`. GREEN: CPU-under-test is unchanged current candidate; inspection hook targets the new observer with unchanged all-three-file public command. Pin both observers. Pointing RED to the new observer would erase an intended failure and must reject.
- [ ] Order: RED/base, RED/mgnp, GREEN/base, GREEN/mgnp. Separate SIF invocation and fresh private phase output each time, so BASE bindings cannot contaminate mgnp. Preserve source command flags, plugin autoload/cacheprovider/conftest isolation, offline/thread1/bytecode settings and reviewed startup behavior. Match exact22 RED cases,19 failed names/3 passed names, zero errors/skips/duplicates and same names across environments; intended inner pytest exit1 yields observer exit0. Both GREENs require226 passes, zero failures/errors/skips, matching names and inner exit0:107 original CPU+22 review CPU+82 controller+15 entry198. No assertion/oracle weakening.
- [ ] Host enforces original30-second RED/90-second GREEN caps from container Popen through observed normal exit, including startup. Fixed360-second envelope: bootstrap validation60, phase caps240, final validation30, finish/cleanup30. Effective wall/monotonic bounds only decrease with initial/current allocation ends. Require remaining caps to fit, fresh clock before Popen after costly checks, strict post-reap checks and shortened-allocation monitoring; no renewal on extension.
- [ ] Reuse229-r3 owned process-group cleanup including descendants after leader exit, start_new_session, TERM/grace/KILL/reap and ESRCH handling. Success requires no live descendants. Preserve failed logs/XML/partials, no retry/requeue. Wrapper accepts exactly three quoted positional arguments `(config,configSHA,manifestSHA)` and an absolute physical packet path independent of spool dirname; direct/swap/relocated tests are required.
- [ ] Record before/after byte/origin/version/startup/ELF identities and aggregate actual Bridges receipts with all raw phase outputs. Use a transport-specific fixture-only terminal kind, not a Delta owning proof or operational CPU_COMPLETE. Later acceptance gates require separate root interpretation, never an implicit scientific admission.

### Task 3: root-only review and one bounded fixture deployment

- [ ] Independently review source diffs, closure/startup/provider choices, hook targets, oracle, real host receipts, deadline/cleanup behavior and attributable pure RED/GREEN. Host3.6 grammar checks do not masquerade as actual-host execution.
- [ ] Root alone builds controlled copies and stages them into a new namespace; seal hashes and successful actual SIF compatibility/collection probes before fixture scheduling. Actual job/config/outputs remain unset until root binds real facts. Use private0700 owned non-symlinked parents; only active-phase output writable, host/previous-phase receipts protected.
- [ ] Proposed job: cis260361p/QoSrm/RM-shared, five CPUs,8GiB,six minutes,no GPU/requeue. Five cores cover8GiB under the observed2000MB/core rule; verify actual placement. Prior RED XMLs took3.436/3.435s and job23620810 ended at21s; earlier107-case dual observer took22.069s. Full226 GREEN remains unobserved: retain30/90 caps and bounded extra bundle/SIF checks, not a claim of proven full runtime/memory.
- [ ] Preserve Delta23623058 and all running jobs. Root may decide whether additional Bridges dispatch remains useful as queues progress, without automatic cancellation/retarget or a new scientific scope/cap decision.
- [ ] After acceptance/binding, root runs one fixed packet, collects raw host/container origins/ELF maps, phase names/counts, hashes/logs/XML and normal exits. A source/provider/startup/cap failure stops with preserved evidence; any correction is separately frozen/reviewed, never an automatic fallback or changed assertion.

## Handoff limits

This is a design-only proposal. Root plan acceptance precedes implementation; staging/import/ABI acceptance precedes the CPU fixture job. Actual success proves only unchanged fixture behavior under the declared exact byte slice, not scientific BASE equivalence or operational CPU/GPU admission. `contracts.json` preserves exact machine-readable counts, paths, hook targets, full oracle, proposal and NULL deployment bindings. No code, bundle, install, collection/test run, remote/scheduler/state change or source publication was performed in this task.
