# A3 edge driver hand-back

Status: handed-back

## What changed

Owned additions:

- `component_analysis/a3_edge_pipeline.py`
- `component_analysis/a3_edge_workload.py`
- `tests/test_a3_edge_pipeline.py`
- `tests/test_a3_edge_bank_contract.py`
- `scripts/jobs/specificity_a3_edges.sh`
- This report, mirrored to the primary checkout.

The standalone driver implements CPU preparation, static dry-run, bounded native
pilot, streamed attribution caches, validation selection, frozen null transfer,
and summary stages. Production preparation replays the existing authenticated
A1/A3 CPU producer and checks all original stream fields. Original file-byte
references stay distinct from derived padded-input digests. Implicit A1 masks
come from unpadded length, preserve interior token zero, reject conflicting
explicit masks, and never mutate parent rows.

All semantic bins remain in the frozen graph. Unsupported cells retain explicit
coverage failures. Attribution uses each condition's authenticated neutral twin,
sums token contractions, and fits the three canonical-pressure bootstrap
rankings. Exact interventions use same-condition designation donors. Both ranked
families use the frozen D-specific budget rule. All matched null memberships
freeze before assessment; duplicate draws remain logical slots while identical
source/profile/membership panels may reuse physical computation.

The native pilot produces ordinary-HF/native and gradient-enabled readout
comparisons, local receiver VJPs, midpoint agreement, serial geometry, and the
source-hashed complete analytic toy control. Pilot cells and scientific shards
have immutable restart coverage. Constructed receiver values are compared with
actual effective native tensors. H-mean floors recollect the complete required
sender union on ancestral original-H train-plus-validation rows, both streams,
with unpadded token-weighted pooling in the native additive representation.

Measured profiles cover gradient nodes, actual validation prefixes and selected
null sets, transfer, utility floors, banks, source refresh, serialization, CPU
uncertainty work and capacities. Actual completed calibration jobs, source/output
binding, original root admission references, current allocation leases and
reserved-hour ceilings remain separate requirements. The shared validator owns
financial authentication; the edge driver supplies its inventory validator and
edge phase limits. A separately authorized measured continuation may use the
larger registered integration count while retaining the failed comparison and
blocking the full edge-specificity claim.

Results retain the simultaneous intact-delta clamp estimand and its downstream
masking consequence. They do not claim a recursively pruned circuit, unique
intent, independent datasets from bootstrap fits, or inclusion of exploratory
edge ranks in direction Holm inference. Original utility source splits remain
separate from their validation/assessment roles.

Review round one, B1: one strict bank contract now spans native production,
cache decoding, utility intervention and completed-panel/summary intake. The
expected full sender union and typed key bounds come from actual model/frozen
preparation metadata; serialized records are checked before dict construction.
Every value must be an exact residual-width vector and remain finite after
float32 decoding and native-dtype conversion, including BF16. Task, base/source,
original ID order, both streams, unpadded token weights, additive representation
and numeric profile must match the independently derived contract. Linked bank
objects and byte references are mandatory on cached-panel reuse and summary
resume/final intake. Timing-only validation banks retain explicit separate
source contracts. The existing scalar pooling oracle changed only its explicit
independent fixture geometry; its unequal-length weighting assertions remain.
Workload, wrapper and shared authority source were not changed for this fix.

## How verified

Pre-review implementation acceptance below is retained for its exact earlier
package; it is not a broad post-B1 rerun.

Initial owning acceptance, with BLAS/OMP/MKL threads fixed to one,
`PYTHONDONTWRITEBYTECODE=1`, and pytest cache disabled:

- mgnp: **38 passed**, exit zero, elapsed 106.71 seconds.
  `/tmp/report106-a3-edges-mgnp-final.log`
- Base Python 3.9: **38 passed**, exit zero, elapsed 161.34 seconds; three
  environment deprecation/version warnings.
  `/tmp/report106-a3-edges-base-final.log`
- After the shared runtime's narrow direction-only receipt fix, the targeted
  source-fingerprint end-to-end case passed on mgnp: **1 passed** in **64.79**
  seconds (`/tmp/report106-a3-edges-mgnp-691-e2e.log`), and base: **1 passed**
  in **129.03** seconds (`/tmp/report106-a3-edges-base-691-e2e.log`).
- Actual wrapper syntax check passed. Direct and Slurm-spooled wrapper dry-runs
  run in the owning tests, without weights, CUDA queries or output writes.

Logs:

- `/tmp/report106-a3-edges-mgnp-final.log`
- `/tmp/report106-a3-edges-base-final.log`

Both commands used `tests/test_a3_edge_pipeline.py -p no:cacheprovider -q` and
separate final basetemp directories under `/tmp/report106-a3-edges-*`.

Coverage includes real tiny native attribution and joint interventions, the
complete source-to-pilot-to-measured-fit/selection/null-transfer/report path,
blocked and complete scientific-failure paths, source/label/mask/split changes,
signed ties, matched-null RNG and support, utility inapplicability, native
receiver equality, raw control tampering, shape/capacity failures, unequal-length
H-bank pooling, immutable restart, midpoint resume and injected finalization
rejection. Critical source, numerical, selection and restart seams were added
through observed failing tests before their implementations.

B1 focused red/green commands use the same one-thread environment above,
`tests/test_a3_edge_bank_contract.py -p no:cacheprovider -q`, dedicated basetemps,
and the corresponding pinned interpreter. The final commands also name
`tests/test_a3_edge_pipeline.py::test_H_bank_is_ancestral_both_stream_unpadded_token_pool`.

- Red mgnp: **17 failed, 4 passed**, exit one;
  `/tmp/report106-B1-red-mgnp.log`.
- Red base: **17 failed, 4 passed**, exit one;
  `/tmp/report106-B1-red-base.log`.
- Final focused mgnp: **24 passed**, exit zero, **75.39** seconds;
  `/tmp/report106-B1-final-mgnp.log`.
- Final focused base: **24 passed**, exit zero, **113.62** seconds with the same
  environment warnings; `/tmp/report106-B1-final-base.log`.

The retained final basetemps are `/tmp/report106-B1-final-mgnp` and
`/tmp/report106-B1-final-base`. These include the genuine complete native path,
then missing-bank rejection on panel reuse and summary resume, restoration of
the valid bank and a complete result, changed/missing/foreign link rejection,
independent residual-width head/MLP checks and native BF16 overflow rejection
before any forward. Original reviewer probes and logs were not edited.

## Execution evidence

These are CPU software controls, not a new research run.

- Scientific job and cluster: none; no Slurm submission, GPU scoring, external
  scoring API, notebook execution, git command or RS mutation by this worker.
- Process exits: zero for both final pytest commands.
- The complete injected fixture observed **120 of 120** logical learned/null
  slots and reused **two** identical exact panels. Each panel retained **10**
  mechanism rows, **100** IOI rows, and **32** rows for each MMLU floor. The toy
  mechanism assessment has one ID; it is not the production assessment sample.
  `/tmp/report106-source-and-acceptance.json`
- The independent ordinary/native baseline in both final artifacts is
  **20735.4765625 versus 20735.4765625**, with full-vocabulary argmax **9 versus
  9**. Midpoint diagnostics use the eight fixed validation identities. The
  separate complete analytic toy records actual endpoint and IG comparisons.
  `/tmp/report106-source-and-acceptance.json`
- Both fixture summaries are complete software flows with `injected=true` and
  `finalized=false`; the scientific point gate fails. Production finalization
  is rejected.

Completed fixture artifact roots:

- `/tmp/report106-a3-edges-mgnp-final/test_complete_tiny_native_stag0/run`
- `/tmp/report106-a3-edges-base-final/test_complete_tiny_native_stag0/run`

Their manifests are byte-complete `payload.json`/`COMPLETE.json` objects. They
name an explicitly injected dummy source identity, not a production commit.
No production `run_manifest.json` or scientific baseline reproduction is claimed.

Current post-B1 source SHA256 values (earlier broad-suite package is preserved
in `.superpowers/sdd/plan-a3/edge-review109-source`):

```text
acc0b7953af131bc65e328a38e8464f900775470ec00acf413984a4f2778f020  component_analysis/a3_edge_pipeline.py
400c98aea4881a3cac0c5fbbc6498824be938b48a5d1f3ff30745691e87b53aa  component_analysis/a3_edge_workload.py
2963d1e1745b51bbd4a46d462ade2cc6f1d0571abf3c55c0e64c7b949ced413e  tests/test_a3_edge_pipeline.py
33e6652e3114ca6e8ee1857cdbd37aa16895d19c49dae9710eafec76aa4b9a25  tests/test_a3_edge_bank_contract.py
41e3856a903e2e235f33ca229ecea2022915b4d6fa683239c7d88a989df20be1  scripts/jobs/specificity_a3_edges.sh
```

The full owning suites used shared runtime
`16f069ca5d314ab1f9ceccaad57baf64b1ef811c932bb0e7c7851c61e4d976c8`.
The focused end-to-end rechecks used the subsequent freeze
`691c258d8a46140eef0c4407cf8f06a8f36890d475fe3320fdb19fe2326d9871`;
its current dependency list is `/tmp/report97-source-frozen.json`. Those pre-review source hashes are retained in the original acceptance JSON;
the current table includes the B1 fix. The focused B1 suite uses the latter
shared freeze, with exact current evidence in
`/tmp/report106-B1-source-and-acceptance.json`.

## What is NOT done

No production A3 source preparation or Llama/H200 scientific execution occurred.
Real hardware timings, memory, original-H recollection and phase feasibility
remain unmeasured. CPU fixture timing cannot authorize production work.

Root must commit the reviewed files, produce the canonical new A3 design and
edge M0 proof under the actual source identity, and run the bounded pilot with
actual source/profile and allocation evidence. Later stages need the completed
root-anchored control, pilot and measurement references, fresh capacity and
ledger mappings, and a complete workload within the unchanged ceilings. The
historical A3 design is not a substitute. Production assessment remains the
unchanged A1 cohort and utility samples.

The shared runtime owner completed a narrow direction packing-receipt fix after
the full owning suites. Only the source-fingerprint end-to-end case was repeated
on both interpreters against its new freeze, as root requested. Shared full
direction acceptance remains separate.

Independent `109-a3-edge-driver-review.md` requested B1 changes. The focused author closure above
is ready for its scoped independent recheck; it is not self-acceptance of that
review. Orchestrator integration remains pending. No other
worker's source, frozen A1 artifacts, native adapter or reviewed edge core was
edited.

The shared authority owner has reopened its separate reviewer round after this
B1 acceptance. The exact B1 dependency above is preserved; source-bound rechecks
after that owner's next freeze belong to root integration.

## Open questions

No scientific ruling is left for this worker to choose. Actual production
feasibility and any hardware-specific numerical failure are operational gates
for root after review; unavailable or over-budget cells must remain explicit
rather than reducing the registered science or inventing a timing estimate.
