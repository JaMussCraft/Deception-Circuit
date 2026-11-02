# Direction reporting hand-back

Status: handed-back

## What changed

Owned files are `component_analysis/a3_direction_reporting.py`,
`tests/test_a3_direction_reporting.py`, and this report. The report is mirrored
into the primary checkout. No other worker's implementation was edited.

`pack_statistics_panel(design, selected, rows, *, split)` derives primary row
keys from the canonical source membership and frozen selected axis descriptors.
It returns only the strict FAR/SER statistics schema. Complete paired streams,
all frozen seeds and null indices, both utility floors, binary full-vocabulary
correctness, source tokens/readouts/labels, axis hashes, replay evidence,
positive-control references, common intact baselines and validation exclusions
are checked before normalization. Original IOI assessment source split remains
`generated`; mechanism and MMLU source splits remain `test`. Invalid coverage
blocks normalization; invalid scientific denominators remain unavailable in the
reviewed estimator.

`summarize_descriptive_sdr` uses the reviewed gate, triplet/rank, wording-cluster,
paired utility draw and interval helpers with the standard defaults. It returns
`descriptive_only=True` and no Holm decision. FAR/SER alone enter the reviewed
confirmatory summary.

`summarize_direction_diagnostics` derives separate nuisance primary, learned and
nuisance secondary, and signed steering coverage from source membership and
selection. Nuisance and secondary estimates use the reviewed scalar point
estimator. Secondary mechanism operation names are adapted only at that
estimator's interface, retaining their actual operation in the report and using
the same axis's existing MMLU floors. Steering gets raw signed tables without
necessity or floor verdicts. MMLU operations remain separate tables. A nuisance
point pass carries an explicit role/framing ambiguity label. Missing applicable
groups are incomplete; an explicit failed nuisance fit with its reason and
receipt is unavailable.

Optional `probe_results` have a documented strict adapter in `_probe_summary`:
completed assessment results must retain the selected train fit reference and
exact probe fit receipt, paired original assessment membership and binary
correctness. Balanced accuracy is recomputed from that coverage. Missing probe
results keep diagnostic readiness false.

`assemble_direction_summary` links canonical JSON serialization hashes and byte
counts for every supplied input, including optional calibration/probe inputs.
These are canonical payload identities, **not original file-byte hashes**.
Optional `artifact_reference` entries retain the runtime reader's actual
completion-marker and child-file references separately. Assembly exposes
`diagnostic_readiness`, remains nonfinal, and cannot authorize continuation or
write research-session state.

Independent review99 corrections are included. Reporting consumes the reviewed
runner's `replay_valid` attestation of matched-batch `torch.allclose` at
`atol=1e-5, rtol=1e-5` plus exact full-vocabulary argmax agreement. It checks all
stored replay maxima are finite and nonnegative and retains the measured epsilon
lower bound. It imposes no new absolute ceiling and does not recompute relative
acceptance using an individual row's margin: the stored error may cover other
members of the same batch. The runtime's completed artifact and frozen source
lineage must attest the producing runner and actual comparator evidence.

Primary packing and diagnostic reporting now share `_validate_frozen_profile`.
Every noninjected diagnostic input, including primary baselines and reused
same-axis MMLU floors, must match the selected model, model revision and code
source digest. Rehashing a wrong profile and its own positive-control reference
does not satisfy this frozen identity check.

## How verified

Test-first collection initially failed because the reporting module did not
exist. Further targeted red runs exposed absent selected-design binding, absent
production donor maps, missing diagnostic APIs, incorrect original IOI split
assumptions and pooled MMLU diagnostic tables before their fixes. Review99's
relative-replay and self-consistent wrong-profile failures were also reproduced
in targeted regressions before correction. Those regressions cover a zero-margin
member sharing a valid relative-tolerance batch maximum, inadequate measured
epsilon, failed replay attestation, and independent model/revision/source changes
in steering observations and reused MMLU floors.

Both final scoped CPU suites passed: derived test count **39 passing** per
interpreter, with exit code **0**. Tests are in
`tests/test_a3_direction_reporting.py`.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -m pytest tests/test_a3_direction_reporting.py -p no:cacheprovider -q
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -m pytest tests/test_a3_direction_reporting.py -p no:cacheprovider -q
```

Tests exercise complete synthetic calibration and assessment normalization,
missing/duplicate axes/seeds/streams/utilities, source/prompt leakage, stale
canonical bytes, native labels and controls, common intact baselines, the scalar
runner oracle, undefined denominators, descriptive SDR, separate diagnostic
coverage, nuisance ambiguity and probe ancestry. Small explicitly injected
bootstrap counts are test fixtures; production defaults are unchanged.

## Execution evidence

CPU only. No model weights were loaded, no GPU/API execution or Slurm job was
started, no notebook ran, and no git or research-session mutation was performed.
There is no model-execution job id, cluster, scientific baseline result or
`run_manifest.json` from this task. Production row counts are unobserved because
the model workload remains unexecuted.

The synthetic scalar baseline reproduces the same learned D/I fractions in the
existing runner point estimator and normalized statistics evaluator; the test
checks their numeric equality and point-gate equality. This is a CPU software
oracle, not scientific evidence about the model.

## What is NOT done

There is no CLI, disk publication, completed-shard reader, protected-registry
revalidation or production finality gate in this module. The pure assembly
rejects `final=True`; the runtime owner must independently attest complete
artifacts, current sources/registries and the full frozen production inventory.
Injected fixtures can never finalize through this interface.

The existing canonical preparation seam needs an explicit IOI amendment:
`a3_pipeline.prepare` currently preserves generated validation IOI rows without
adding `analysis_split='validation'`, while selection already requires that
analysis split. The runtime owner must attach this field while preserving
`split='generated'`, and test canonical prepare through selection. This reporting
adapter accepts explicit validation analysis metadata and rejects missing
validation split evidence. Preparation was outside this worker's ownership.

Actual raw-file references and completion markers must be obtained and checked
by the runtime artifact readers. Canonical JSON hashes do not attest original
serialization bytes. The runtime must produce completed probe results matching
the documented adapter and require diagnostic readiness before finalizing.

## Open questions

Independent review remains with root. The runtime must confirm that its shared
intact cache supplies identical intact outcomes across axes, seeds and utility
sites; this module refuses mismatches instead of choosing a baseline silently.
If the existing producer cannot meet that invariant, it needs an explicit
reviewed canonical-baseline adapter rather than a reporting tolerance default.

No new scientific scope or compute admission is requested.
