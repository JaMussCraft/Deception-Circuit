# Initial edge M1 source/data and operational readiness

Status: handed-back

## What changed

**Source/data integration: PASS. Initial edge M1 execution admission: BLOCKED.** The completed successor artifacts are internally and ancestrally consistent, but current source-refresh cost and the staged timing-reservation plan do not justify spending an initial edge M1 reservation. These are operational integration blockers; they do not undo accepted component reviews109/110 or the narrow tokenizer repair115. No GPU execution is admitted here.

Exact frozen source: `87fceb28b3b46f4a406c0280db785697a0bbd3fc`, under `outputs/_analyses/specificity-ladder/a3-edge-runtime-87fceb28b3b4/runtime`. Completed preparation: `outputs/_analyses/specificity-ladder/a3-edge-pilots-87fceb28b3b4`. All ordinary source/archive identities match, with only the accepted pipeline/test tokenizer delta from the old mask source bundle. That old bundle and mask authority were untouched. Source and execution evidence: `117-edge-pilot-readiness-evidence/source.json` and `117-edge-pilot-readiness-evidence/run_manifest.json`.

**B1 — repeated full source validation has no feasible admitted cost bound.** `execution_guard` calls full `validate_prepared` on every refresh. That call rereads canonical/parent evidence, checks original streams and H-bank domains, copies protection inputs and rebuilds all graphs. `cached_pilot_stability` emits every condition/node/ID/stream/receiver key, and `execute` guards once before the index plus once per key, including resumed reads.

The exact source count is `64` keys per receiver: D/I, both `8` and `16` nodes, first `8` validation identities and both streams. The completed graphs have the following counts. Evidence: `117-edge-pilot-readiness-evidence/artifact-check.json` and `117-edge-pilot-readiness-evidence/receiver-groups.json`.

| Task | Graph edges | Receivers | Stability cache keys |
|---|---:|---:|---:|
| FAR | 2172 | 54 | 3456 |
| SDR | 1695 | 43 | 2752 |
| SER | 2044 | 54 | 3456 |

Stability alone therefore requires at least `9,667` full validations: `9,664` keys plus the task index checks. This excludes additional control, loading, native-check, measurement and authority work. The owner's single completed exact call measured `36.626855` seconds wall and `34.265033` seconds combined CPU on the recorded login EPYC host, with threads pinned. Its raw evidence is `117-edge-pilot-readiness-evidence/first-validate-prepared-timing.json`.

Derived repeated work at that observed rate is about `98.35` wall-hours / `92.01` CPU-hours, compared with the `2,700`-second edge M1 ceiling, before any model compute. This is a labeled linear CPU-source-work extrapolation, not a guaranteed per-call target-host lower bound or a GPU forecast. The observed rate, exact refresh count and absence of an established much lower target-host bound make current admission unjustified. See `117-edge-pilot-readiness-evidence/guard-sizing.json`. No guard was weakened or optimization implemented.

**B2 — the initial fit-target pilot cannot fund/price the complete staged path by itself.** The initial measurement target contains only `attribute_receiver` profiles at the chosen fit node count. Later selection and assessment need their own exact set/operation profiles, including H-bank and eligible utility profiles. The cost projector requires every exact profile ID and exact profile equality; initial fit/control elapsed times cannot substitute.

The ordinary current CLI path is `M1 fit-target pilot → M4 fit → M1 select-target pilot → M4 select → M1 assess-target pilot → M4 assess`. Every `--stage pilot` remains M1 and repeats the full stability/control workflow. Its later targets depend on completed fit/selection artifacts. Reserving the entire `0.75` edge M1 allowance for the first pilot leaves no legal later timing reservation, even if that first job finishes early: original reservations are not refunded by actual-time reconciliation. A `16`-node continuation also needs actual matching timing profiles; no automatic node-scaling or conversion of stability caches into admitted timing receipts is assumed. A concrete staged timing plan within the existing ceiling remains required. Evidence: `117-edge-pilot-readiness-evidence/source-path-analysis.json`.

The completed initial pilot inventory has `96` scientific keys, `604` attribution profiles and `9,664` declared receiver-level invocations; its nested fit target has `6,384` keys, `302` profiles and `106,684` invocations. These are inventory counts, not observed GPU forwards or measured durations. Independent loading/controls declare `2` model loads, `256` ordinary plus `256` native-value forwards, `14` local VJP backwards, `45` value/finite-difference forwards and `302` target-profile benchmarks. Exact declarations: `117-edge-pilot-readiness-evidence/artifact-check.json` and `117-edge-pilot-readiness-evidence/control-counts.json`.

## How verified

Waited for the owner's completed raw manifest and end of memory-heavy work; no partial artifacts were read or validated. Independently checked frozen source SHA256, manually computed declared Git blob identities, archive hash, read-only status and the exact declared input links. No git command was used. Reused accepted109/110/115 scopes and the actual dual-interpreter parent producer replays from115, avoiding another full replay or broad suite.

The independent pinned-interpreter process authenticates completed object bytes/references, current canonical source/parent/grader/protection evidence and all original assessment/utility membership. It recomputes prepared digests/rules/code closure, original streams, ancestral H-bank domains and extended protection checks, then rebuilds every graph and both inventories exactly. It checks the nested measurement target against the standalone fit target and against the actual profile list. All source/row content matches the prior independent115 producer-admission digest. All ancestry inputs remain byte-identical and imports resolve inside the frozen successor.

This constituent validation covers the prepared contract independently while reusing the owner's one isolated full `validate_prepared` call for CPU sizing, as coordinated with root. The initial owner procedure's later comparison failed on expected old-bundle/new-bundle provenance path keys; that failure is preserved. The owner corrected only that comparison to hash-checked resolved registry maps, with no source/artifact/guard changes; its final procedure exits successfully. Independent current byte/protection checks do not rely on its passed flags.

A separate model-free source-support check authenticates canonical/prepared files and tests the actual first fixed validation IDs for D/I and both streams. All `96` source pairs support the prospective graph edges; no extra static initial-source blocker was found. Declared unsupported metadata stays explicit. Source-support evidence is `117-edge-pilot-readiness-evidence/pilot-source-support.json`.

The actual wrapper command uses the frozen root, pinned mgnp interpreter and offline/thread environment. Its raw dry-run succeeds with `source_admitted=true`, `model_loaded=false`, `writes=false` and `execution_authorized=false`. Unlike the mask parser-only dry-run, it checks the real prepared edge source; it still supplies no live allocation authority. The initial model path reaches accepted edge controls and shared ledger/context/lease helpers, without direction-only execution/admission/numerical seams. No model or GPU was used for this review.

## Execution evidence

CPU review only; scheduler job and allocated cluster are not applicable. Independent completed-artifact validation and the fixed-source support check exit successfully. Original assessment baseline is `100` expected/observed per mechanism, original IOI `100` expected/observed and MMLU `32` expected/observed; disjoint validation utility counts are `100`/`32`. Independent exact inventory reconstruction matches both published digests. Evidence: `117-edge-pilot-readiness-evidence/run_manifest.json` and `117-edge-pilot-readiness-evidence/artifact-check.json`.

Pilot digest: `5901800f36a0af4534ebcdb60a2b0b140166e930f68ce196ab045239b758c373`. Fit-target digest: `7991be5ca8f1ca93badbed05ed306a8ef9f74b83f402f49f988250e2169c6b00`. Raw completed producer manifest SHA256: `3a580b14d222bf78e0f8fa3c187b40d2341406c92ae321c99336e62b8ace9e53`. Baseline assertion: the successor source-row digest equals the prior independent115 actual-producer digest, with identical scientific cohorts and original utility bytes. The receipt names the exact source commit; no scientific run manifest or effect estimate is fabricated.

Reviewer commands use `/u/swong2/.conda/envs/mgnp/bin/python -B`, frozen-only `PYTHONPATH`, offline caches and host threads pinned. Scripts/logs are `117-edge-pilot-readiness-evidence/check_completed_edge.py`, `117-edge-pilot-readiness-evidence/artifact-check.log`, `117-edge-pilot-readiness-evidence/check_pilot_support.py` and `117-edge-pilot-readiness-evidence/pilot-source-support.log`. The owner timing is explicitly attributed and reused; no duplicate timing call was made. Raw wrapper, initial/final owner procedure evidence and initial comparison failure are preserved alongside the reviewer outputs. Enclosing cgroup headroom was checked and inventory work remained serial after owner completion.

## What is NOT done

No source edits, git, RS writes, scheduler access/submission, GPU/large weights, APIs, notebooks or subagents. No published preparation was changed. No model timing, native BF16 numerical controls, GPU-memory bound or scientific result is established. The declared primitive/control counts remain planning expectations. The CPU source-check extrapolation is not native runtime evidence. No source-cache optimization, graph/cohort reduction, cap increase or new timing adapter is implemented or authorized by this review. Held mask job/source/authority remain outside this review and untouched.

## Open questions

Root must resolve B1 with an accepted, measured feasible source-proof cost strategy or a justified target-host bound while preserving all source/protection/ledger/cap/lease/completion guarantees. B2 requires a complete staged timing-reservation plan within the original shared edge M1 allowance before any initial spend. The following is the exact intended command shape after those blockers and genuine root prerequisites are resolved; it is not an instruction to launch now:

```bash
export SPECIFICITY_A3_EDGE_REPO_ROOT="$B2" PYTHONPATH="$B2"
export DC_PYTHON=/u/swong2/.conda/envs/mgnp/bin/python DC_CLUSTER=delta
export HF_HOME=/work/nvme/beto/swong2 HF_HUB_CACHE=/work/nvme/beto/swong2/hub
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
bash "$B2/scripts/jobs/specificity_a3_edges.sh"   --stage pilot --measure-stage fit --steps 8   --design "$O2/canonical/design.json"   --commit 87fceb28b3b46f4a406c0280db785697a0bbd3fc   --work-dir "$FRESH_EDGE_PILOT_OUTPUT" --prepared "$O2/edge/prepared"   --inventory "$O2/edge/inventory-pilot"   --ledger-snapshot "$ROOT_MAPPING" --reservation "$ROOT_RESERVATION"   --registry "$W/docs/research/held_out.json"
```

There is no edge `--admission` or `--target-inventory` flag. The original admission is linked through the reservation; the pilot embeds and independently rebuilds its exact fit target. `--measure-stage select` later requires genuine fit evidence, and `--measure-stage assess` genuine selection evidence. Both are separate timing work, not authorization inherited from the first pilot.

Root needs a real original pilot admission/reservation bound to this exact stage identity and pilot inventory as upper inventory; canonical RS original rounded charge/phase ownership and complete mapping/admission references; a separate scheduler checkout `B2` and matching reserved output root; actual H200 type/count, CPU/RAM contract and current live lease; and sufficient finish/shard reserve. The pinned runtime signature must match preparation. Keep the edge M1 allowance, total M1, M4 and A3/global original charges intact. If a prior mask mapping may resume, a newly added RS ID also needs its monotone successor without changing old anchors or forcing incompatible host-capacity declarations.

Minimum declared device is one H200 with serial physical batch one, BF16/SDPA and the frozen native geometry; numerical/VJP/independent-loading controls remain unmeasured until the actual admitted pilot. CPU contract must be a positive integer, with host threads pinned. Native resident/peak memory is still unknown. The following are source-derived storage floors in bytes, not measured total process peaks. Exact values: `117-edge-pilot-readiness-evidence/artifact-check.json`.

| Scope | Host floor | Each cache/output/scratch tier | Shared-disk sum |
|---|---:|---:|---:|
| Initial pilot | 7697697190 | 3848848595 | 11546545785 |
| Future fit target | 67606784294 | 33803392147 | 101410176441 |

Actual admitted host capacity must also cover resident/native peaks and retained/transient proof work; tiers sharing a physical disk pool add. The future fit floor already exceeds the old mask's declared host allowance and cannot inherit that job's capacity proof. Later M4 cost/admission also requires genuine completed same-H200 measurements and all original controls. No reservation size or GPU duration forecast is asserted here.
