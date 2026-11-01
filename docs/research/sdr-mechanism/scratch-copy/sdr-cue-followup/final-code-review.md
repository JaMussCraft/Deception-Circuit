# Final whole-branch code review

2026-10-25. Reviewed `ca41bfdb2fd4e4c4c784eabd321ea75e41a45299..29492146127f56c05a4087b1bfdeea0e63a4d24a`, all three additive files, against spec SHA256 `b06fc61df13c9c64563d7043fd06502658fc32539cb659639038812b6c1a0cbe`, design review, plan, task report, initial review, fix re-review and progress rulings. Packaged diff SHA256: `e413624a745b003fc00cc1b109acddcc48baca71deceb5bd038af34c689438ea`.

## Strengths and integration findings

- `scripts/sdr_cue_positions.py:76,130,143`: input freezing derives the exact parent panel and literal S/C_S memberships, freezes structural token boundaries, and rebuilds source/software/cache provenance for verification. The 4,224-row/528-batch schedule preserves every pair and complementary arm. The final independent committed-input rebind remains a release gate.
- `scripts/sdr_cue_positions.py:162,186,276,411`: head banks remain natural and fixed; masks exclude generated, dummy and padding positions. Main controls, forced64 controls, fresh current-history self captures and E/system causal-null checks are audited by their actual schedules, masks, head membership and physical forward counts. The unchanged hooks replace head slices at o_proj input and use the actual FP32 final norm/unembedding readout.
- `scripts/sdr_cue_positions.py:311,331,474,557,681,693`: exclusive durable terminal publication, process-held locking, immutable attempt/invocation provenance, hard-stop distinctions and completed-terminal reconciliation support the intended bounded resume workflow. The actual-allocation buffer check and shared finalization fix resolve both earlier findings. Finalization validates existing assembly canonically and does not rerun accepted outcomes.
- `scripts/sdr_cue_positions.py:531,598,648`: natural timing covers all six arms plus intact; forced64 timing independently guards batch admission. Calibration is structurally audited before main and binds the exact hardware class/name/capability/memory while allowing a new per-attempt UUID. H200 parent timing is not reused as A100 qualification.
- `scripts/sdr_cue_positions.py:750,754,769`: inherited blind export/join helpers retain exact coverage and multiplicities. Analysis uses pair-fixed anchors, all five factorial components, fixture-equal means, matched S-minus-C_S differences, complete nine-category transitions/triples and descriptive-only parent replay. Empty strata remain explicit. No scientific effect or outcome controls scheduling.
- `scripts/jobs/run_sdr_cue_positions.sh:4,8,32`: wrapper binds the approved checkout and actual Slurm allocation, guards environment startup, and dispatches the additive runner with offline/thread settings.

## Important or critical issues

**None identified.** No additional experiment, infrastructure change, broad test rerun or implementation fix is required by this review.

## Declined to judge

- Actual A100 memory capacity, numerical behavior, nnsight execution and timing: CPU source review cannot establish these; the separately released fresh calibration must do so without changing B8/L224, cap64, masks or tolerances to force a pass.
- Final committed freeze, independent exact source/input rebind and selected operator actual-wrapper CPU qualification: explicitly pending under the accepted one-final-freeze ruling. Earlier provisional checks do not qualify the final source, and this review does not waive those gates.
- Live scheduler availability, allocation ownership, job release and measured cost accounting: operator/root responsibilities requiring fresh external evidence; this review submits no job or reservation.
- Authenticity of an external PREEMPTED/TIMEOUT receipt after a hard kill: code checks its bound job, eligible state and past end time; root/operator must independently verify it against the scheduler before recording an interruption. An unheld lock is not acceptance evidence.
- Scientific effect sizes, labels, factual/deception interpretation and final narrative: no new GPU outcomes exist for this review; independent all-row integrity, blinded labeling and arithmetic/narrative review remain mandatory.
- Unrelated v2 studies, stopped prior grids, unused H100 portability work and merge/push decisions: outside this additive study and unchanged by the reviewed range.

## Verdict and evidence limits

**PASS — spec compliant and code approved to proceed to the remaining qualification gates.** This is not GPU release, a claim of scientific completion, or permission to merge/push.

Read the complete packaged diff in nonoverlapping segments, including all tests. Focused unchanged-helper checks addressed three concrete integration risks: hook/readout and physical-mask semantics; actual deadline/hardware identity; inherited panel/label/summary assumptions. Those contracts are compatible. Source and git remained read-only; no helper agents were launched. No concrete unresolved doubt warranted a reproduction or test rerun.

Read the existing clean dual-environment logs: 44 new tests passed in base82.80s and mgnp56.51s; after the allocation/finalization fixes, all11 affected tests passed in base23.98s and mgnp18.23s. Prior parent-suite/oracle/source-closure evidence is controller-provided and was not regenerated. The mock-based tests establish CPU contracts, not real GPU execution. No model, GPU, API, notebook, remote-write or expensive cache preflight was run.
