# Mask driver hand-back

Agent: mask pipeline implementer. Status: handed-back. The implementation is ready for independent review; production execution is not admitted by this report.

## What changed

Review108 fix round one closes the accepted typed-H-bank blocker. This fix changes only `component_analysis/a3_mask_pipeline.py`, `tests/test_a3_mask_pipeline.py` and this hand-back. Wrapper, workload, accepted numerical core and shared runtime remain unedited. Pre-fix bytes are preserved at `/tmp/a3-mask-round1-before-pipeline.py`, `/tmp/a3-mask-round1-before-tests.py` and `/tmp/a3-mask-round1-before-report102.md`; auditable source diffs are `/tmp/a3-mask-round1-pipeline.diff` and `/tmp/a3-mask-round1-tests.diff`.

A single full-bank validator now runs before publication, reuse and assessment intervention, with applicable checks repeated at CPU final intake. Expected geometry comes from the actual model and authenticated preparation; final production intake uses independent execution proof linked to the original measured model admission. It never infers widths from bank declarations. Explicitly injected fixtures capture their separate actual-model proof before bank construction. Required support is the complete typed candidate/reference union, including valid layer/head/block bounds and uniqueness. Exact flat lengths, finite numeric/profile-cast values, original source IDs/counts/domain, execution profile and numeric/base identities are mandatory. The low-level export path separately rejects scalar, singleton-broadcast, nested and wrong-length means before hooks or forwarding. Valid zero-removal groups retain the full valid bank and remain supported.

Exact new-driver review/commit list:

- `component_analysis/a3_mask_pipeline.py`
- `component_analysis/a3_mask_workload.py`
- `tests/test_a3_mask_pipeline.py`
- `scripts/jobs/specificity_a3_mask.sh`
- `docs/research/specificity-ladder/reports/report102-a3-mask-pipeline-handback.md`

The standalone CLI implements CPU preparation/inventory/cost proposal, disposable actual validation-only pilots, full scientific training and checkpoint selection, native assessment and canonical summaries. It leaves the direction pipeline untouched. The numerical core is the separately accepted unequal-layout and explicit-purpose source; this resumed integration made no further core changes.

Preparation authenticates the audited original A1 parents/completion marker, canonical A3 source, both root ruling files, complete matched source maps and actual protection registries. It binds the candidate/control/reference/timing protocol, physical widths, current interpreter/launcher and cluster profile files into execution identity. Masks derive from authenticated unpadded token lengths, including actual A1 records without serialized masks; conflicting explicit masks reject. No pad-token equality, truncation or invented D/I correspondence is used.

The two objective arms retain their own neutral donors and all eligible matched train IDs. Every run completes the fixed schedule, with detached intact targets, replay-derived fit gap/epsilon and the reviewed single-step streamed update. Primary opposite-designation validation and frozen IOI swaps select only after completion. An early chosen checkpoint links a separate completed-run history and immutable validation observations. Safe JSON snapshots contain gate/Adam/RNG/source/chunk state, never base weights or arbitrary pickle. Identical orphaned validation/boundary publications are reusable on exact resume; changed state rejects.

Actual native adapters implement the crossed operations, source-specific original-H-domain banks, positive/replay controls, both MMLU floors, fixed typed random memberships and unchanged FAR exports on descriptive transfers. New30 remains the read-only FAR-row node-list reference with its distinct SDR ancestry. Missing comparison data blocks full-phase cost admission. Summaries keep raw target choices, fractional margin removal, point/interval gates, readiness and joined utility floors separate; the mask family is exploratory.

The actual disposable pilot executes both objective arms and every bank/control/transfer/utility/validation/checkpoint/restore class on validation sources. Its model is permanently barred from scientific fitting and explicitly removed from the device. Timing-only control IDs follow the root-approved first-eligible prefix policy; update and checkpoint-validation timing retain the entire eligible matched validation cohort. Source-frozen extra masked padding keeps the measured numerical branch consistent without changing original tokens/readouts.

Shared root authority supplies immutable original admission/upper-inventory proof, process-local proof caching, current successor mappings and fresh canonical RS facts/protection/caps/live Slurm allocation. Submit-time deadlines do not authorize execution. All reservation states retain original reserved-hour charges. Cost proposals remain nonauthorizing, include full target capacity, actual hashing/parity caches, measured guard work and per-job rounded reservations, and follow the additive milestone table in `plan-a3.md`.

Final deployment correction: the wrapper sources the selected cluster profile and binds current and legacy HF readers to its existing flat cache. It selects an explicit pinned interpreter; it does not rely on bashrc or activation helpers. Explicit launcher/interpreter files and both repository cluster profiles are source-hashed. Offline flags and model revision remain fixed.

The subsequent narrow Slurm-spooling fix resolves the repository from `SPECIFICITY_A3_MASK_REPO_ROOT` or the actual Slurm working directory established by `--chdir=WORKTREE`. Repository markers and byte equality between the launched script and the selected worktree wrapper authenticate that resolution. Wrong directories, bad overrides and stale copied scripts fail before Python dispatch. Script-relative discovery is used only outside Slurm; `SLURM_SUBMIT_DIR` cannot silently override an incorrect execution directory.

Final source hashes:

```text
d082395ff1a97e9fa825a7dd1c4a36e9ebb6b2fa0738a726b7ebc6fffa97b246  component_analysis/a3_mask_pipeline.py
889f2359e024d6846dcad1623fd28583a3f87b27b1e5314f689fdc6df4d92828  component_analysis/a3_mask_workload.py
5f2bfd0b5dd0bbfba9e7add96073d9a75695ec8aa04eb4cd4dfa8e39f075aa87  tests/test_a3_mask_pipeline.py
cbdf6473ba56f16346c8e98e6cd422aded421f8b3ddeec537b4351fff1f06cce  scripts/jobs/specificity_a3_mask.sh
```

## How verified

Current fix-specific evidence: the pre-fix scoped counterexamples produced **34 failures**, documented in [/tmp/a3-mask-round1-red.log](/tmp/a3-mask-round1-red.log). After correction, **51 selected tests passed in 28.79 seconds** on mgnp and **51 passed in 36.77 seconds** on base, both exit zero; base retains three environment warnings. Logs: [/tmp/a3-mask-round1-mgnp.log](/tmp/a3-mask-round1-mgnp.log), [/tmp/a3-mask-round1-base.log](/tmp/a3-mask-round1-base.log). Both used the established thread limits and `-p no:cacheprovider`; the exact selector was:

```text
exported_h_mean_rejects or assessment_rejects_invalid_bank or final_intake_rejects_completed or valid_bank_preserves or bank_reuse_checks or cpu_bank_geometry or final_intake_revalidates or actual_native_assessment or actual_validation_only_pilot
```

The independent original `/tmp/a3_mask_review108_probe.py` and its pre-fix logs remain untouched. Separate adaptation `/tmp/a3-mask-round1-fullflow.py` changes only the obsolete source-pin assertion and the expected malformed-bank outcome; the small explicit diff is `/tmp/a3-mask-round1-fullflow.diff`. Both interpreters complete its actual native **200-update** fit, disk continuation from **100 to 200**, complete **73-row** assessment, **8** positives and **6** summary cells, while rejecting the former singleton-bank reproducer. Sources: [/tmp/a3-mask-round1-fullflow-mgnp.log](/tmp/a3-mask-round1-fullflow-mgnp.log), [/tmp/a3-mask-round1-fullflow-base.log](/tmp/a3-mask-round1-fullflow-base.log). These are injected software results; no scientific success is inferred. Unrelated numerical suites were not repeated.

The tested shared dependency is frozen `component_analysis/a3_direction_runtime.py` SHA256 `691c258d8a46140eef0c4407cf8f06a8f36890d475fe3320fdb19fe2326d9871`, printed in both full-flow logs. The accepted core remains SHA256 `93e1c70fb6073fc0c8e8eb5bf0ca1a37946ab2733cd8e09a5167ab2394e0a505`; its tests remain `6728ea080b91a64f727cc6791a11e1547aa505c592f6e5022bbbc5de6f25c480`.

Historical pre-review acceptance follows; it is not substituted for the scoped fix evidence above.

Completed coupled numerical/controller acceptance, before the final wrapper-only dependency correction:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_mask.py tests/test_a3_mask_pipeline.py -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_mask.py tests/test_a3_mask_pipeline.py -p no:cacheprovider -q
```

Observed: mgnp **82 passed in 50.36 seconds**, exit zero; base **82 passed in 59.76 seconds**, exit zero, with three known environment warnings. Exact logs: [/tmp/a3-mask-final-mgnp.log](/tmp/a3-mask-final-mgnp.log) and [/tmp/a3-mask-final-base.log](/tmp/a3-mask-final-base.log). Completed numerical checks were not restarted for the deployment-only correction.

Final changed-seam acceptance on both interpreters used the same thread limits and pytest options, with `-k 'wrapper or actual_module_dry'`. Observed: mgnp **8 passed in 31.47 seconds** and base **8 passed in 28.09 seconds**, both exit zero. Logs: [/tmp/a3-mask-spool-mgnp.log](/tmp/a3-mask-spool-mgnp.log), [/tmp/a3-mask-spool-base.log](/tmp/a3-mask-spool-base.log). The copied-wrapper regression reproduces sbatch spooling outside the repository with a simulated Slurm job ID; it checks valid chdir, explicit override, wrong cwd, wrong override and stale-copy refusal. Existing clean-HF-environment checks still resolve exact cached config/index and stat shard-file existence without reading weights. Shell syntax passes. No unchanged numerical suite was rerun for this narrow fix.

Coverage includes actual tiny-native full scheduled training with no mechanism test rows accessible; actual validation-only pilots; actual scientific-purpose crossed assessment and utility controls; exact next-update disk resume; changed model/chunk/RNG rejection; immutable completed-history selection; typed random degeneracy; strict collateral boundaries; real parent-schema masks; incomplete controls/reference/capacity rejection; and genuine completed-root authority fixtures with a fresh live-allocation lease and failed-job refusal.

## Execution evidence

Fix-round scope: both focused pytest processes exit zero, **51 observed against 51 selected** on each interpreter: [mgnp](/tmp/a3-mask-round1-mgnp.log), [base](/tmp/a3-mask-round1-base.log). Both adapted complete-flow processes exit zero, with **73 observed against 73 expected** assessment rows, **8 against 8** positive controls and **6 against 6** summary cells: [mgnp flow](/tmp/a3-mask-round1-fullflow-mgnp.log), [base flow](/tmp/a3-mask-round1-fullflow-base.log). The final gate/Adam/RNG checkpoint fingerprint matches uninterrupted execution exactly after disk continuation. These remain tiny injected CPU flows, not scientific baseline reproduction.

All execution was local CPU software testing, with tiny random native models. No Slurm job, GPU, API generation, pretrained weight load, notebook, protected scoring, canonical RS mutation or git command occurred.

- Both coupled test processes exited zero: **82 observed against 82 expected** per interpreter: [mgnp log](/tmp/a3-mask-final-mgnp.log), [base log](/tmp/a3-mask-final-base.log).
- Both final deployment-seam processes exited zero: **8 observed against 8 selected tests** per interpreter: [mgnp wrapper log](/tmp/a3-mask-spool-mgnp.log), [base wrapper log](/tmp/a3-mask-spool-base.log).
- Numerical baseline: the disk-resume test compares every next-update model-state tensor with uninterrupted execution at zero absolute and relative tolerance, and checks identical CPU RNG. Expected difference is zero; the passing exact assertions imply observed difference zero. This is a tiny-model software baseline, not reproduction of an A1 scientific baseline.
- Scientific `run_manifest.json` and full production execution commit are not applicable to this hand-back. Tests exercise explicitly injected run manifests; no scientific verification or replication is claimed.

## What is NOT done

Independent full-driver review, root commit, final canonical production preparation, actual H200 timing, full-phase measured admission and scientific fitting/assessment remain root-owned. No empirical GPU runtime, memory forecast, mask result or specificity finding is asserted here. Completed source protection and live reservation evidence must be refreshed for every real invocation.

A concrete performance concern remains for measurement, not an unfinished callback: the accepted core rehashes complete intact-target cohorts around every numerical chunk. The cost model includes its additional cohort-size factor and retained full-vocabulary parity caches. Actual measurements may block the phase ceiling. A changed chunk size requires a newly measured profile before scientific fitting; no sample, update, seed or control is silently dropped.

The original H banks, A1 artifacts and closed study remain unchanged. Earlier core hand-backs are separate from this new-driver file list.

## Open questions

Root should regenerate the fix-only package against the preserved review108 bytes and route the scoped B1 closure before production acceptance. The original review and its evidence remain intact. Root should dispatch the prepared independent review brief at `.superpowers/sdd/plan-a3/mask-driver-review-brief.md` against the exact files/hashes above. No new human scientific ruling is needed for that review.

Concrete root interface: publish a completed `a3_mask_root_execution_bundle_v1` binding commit/design-file digest, pinned native numeric profile and `padding_policy=max_profile_source_length_plus_one_masked`. CPU `prepare --action inventory` writes separate `inventory-full` and `inventory-pilot` objects. The M1 CLI requires both its original pilot reservation/inventory and the completed full target inventory. The resulting measured cost proposal provides `measured_base_identity` and rounded per-job proposals; the genuine original M5 root admission must bind that measured model hash. Actual root mappings must use the shared authority's immutable admission references, successor and live-allocation rules.

Slurm launches must supply `--chdir=WORKTREE` or an explicit `SPECIFICITY_A3_MASK_REPO_ROOT`; copied scripts are checked against the selected frozen worktree. Scientific fit jobs use explicit seed/arm and exact optional resume boundary. Assessment uses one task with `--group all`, retaining durable source-checked group completion. Summary is CPU-only and refuses missing required groups/evidence. Root alone reserves/submits and handles any measured over-cap scope decision.
