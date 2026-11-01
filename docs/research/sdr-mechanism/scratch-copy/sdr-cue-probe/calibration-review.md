# Independent cue calibration and main-resource review

**Calibration integrity PASS. Corrected timing/resource arithmetic PASS for one8100-second matched H200 allocation.** Main remains unreleased by this review; root owns launch authorization. Lead compactions5. No model execution, GPU, scheduler action, source/git change, semantic interpretation or inferential analysis was performed. Reviewer script/log: `code-review/audit_calibration.py`, `code-review/calibration-audit.{json,log}`.

Actual calibration: job23107161, source `5f74d0c3653a63c411997e0f666a79171076a8d8`, output `Deception-Circuit/.claude/worktrees/sdr-routing-pilot/outputs/_analyses/sdr-cue-probe/calibration-5f74d0c-20261021T201906Z`. Operator's terminal sacct evidence reports COMPLETED/0:0/Restarts0/91allocatedH200seconds. Script final checkpoint measures89.925081seconds; scheduler shutdown accounts for the difference, and operator ledger remains authoritative.

## Integrity and numerical coverage

The saved protocol exactly equals committed `freeze-final-5f74d0c/protocol.json`, scientific hash `9f13e56da0678f289616aba6eaf853d936c042b82a8b55d53db420279ddd95e8`, provenance `e3e041af1f6c5f0353ce4760676e44e47fbeaa16f372bd2d61b87f1b90d75fdb`, protocol-file SHA256 `a6f968660f2cd072dc1589591d532143440356f49c50fd17c8b9b5166c56e915`. Canonical payload/provenance digests, receipt operations digest and all three required artifact hashes independently match. Receipt source54hashes,software and cache10bindings exactly match final protocol; all54current source files independently match their hashes. This phase did not repeat the prior full model-weight audit.

Exactly64planned calibration IDs appear once in original order; all completed to EOS with valid1–64token continuations, correct logical readout ranges and no internal EOS. Main512 IDs and fixture identities are disjoint from calibration. All8attempt files match exact rows, operation digest and attempt1; no duplicate/retry/orphan attempt. Every row has repeat/empty_hook/full_component_baseline/self_replacement in order:256controls, all finite/bitwise/identical-greedy/pass, actual maximum error0 and tolerance1e-5. All8batch runtime copies agree across slots. Independently reconstructing batch forwards as maximum emitted-token length+4controls gives79physical,632real-row,0dummy; maximum forward and aggregate control times match receipt.126active/18panel checkpoints reconcile; all64statuses are completed, paidAPI0. No response text was interpreted or used for selection.

Hardware is exactly one NVIDIA H200, capability[9,0],150111977472bytes. Runtime shape/precision binding is B8/L224/cap64, frozen EOS[128001,128008,128009], BF16SDPA/fullFP32readout/no-cache/eval. Saved actual Slurm bounds span600seconds, deadline equals actual allocation end, premodel63.381384seconds fits120second headroom and final checkpoint precedes shutdown boundary. Main must match these exact scientific/source/software/hardware bindings; a different H200 memory/class/name/count requires review and new matched calibration.

## Corrected timing and resource check

**Finding resolved operationally by using a fresh forecast:** receipt.main_forecast is a pre-final-checkpoint snapshot. Its7533.969964seconds uses earlier panel-checkpoint/I/O timings. Final receipt updates max_panel_checkpoint_seconds and io_seconds after creating that snapshot. The main runner always recomputes forecast from the final receipt, so embedded snapshot is not the runtime release gate. Preserve the original receipt unchanged and supersede the embedded number in operator planning/reporting. No scientific source change is needed.

Independent full-cap arithmetic from final receipt and proposed120/120/90startup/I/O/shutdown,120premodelheadroom,60margin:

| Term | Seconds |
| --- | ---: |
|4224forwards=(4096generation+128controls)×1.0630303639918566|4490.240257501602|
|8320active checkpoints×0.16134634497575462|1342.4015901982784|
|132panel checkpoints×0.20200568111613393×48|1279.9079955518246|
|Measured controls+load+I/O=3.4460395912174135+8.767727588070557+6.722124725813046|18.935891905101016|
|Explicit startup/I/O/shutdown buffers|330|
|Measured premodel+headroom+margin=63.38138389587402+120+60|243.38138389587402|
|**Total required**|**7704.86711905268**|

Minimum integer allocation under this forecast is **7705seconds**; a practical allocation must also satisfy the runner's remaining-time checks after verification/model load. Proposed **8100seconds (02:15:00)** exceeds the total by **395.13288094732seconds**. At calibration's measured premodel+load duration, the deliberately conservative post-load recheck retains about322.983769seconds. This is one allocation, no sharding, cap reduction, mean-answer-length estimate, retries or calibration inclusion. If actual startup exhausts remaining fit/headroom, the existing hard stop governs.

Operator fresh CLI forecast and matched main CPU dry-run were still running at initial report publication. Root should require that fresh CLI output equal7704.86711905268seconds and archive its artifact before release; it must not publish7533.969964seconds as the final release forecast. Main proposal is otherwise fitting with the exact matched resource above. This review grants no scheduler permission and changes no operator accounting.

## Fresh forecast closure

Inspected operator/main-forecast-5f74d0c (a JSON file): exact required7704.86711905268seconds matches independent arithmetic. Actual matched-main wrapper CPU dry-run receipt has statuscpu_dry_run/numerical_pass=false. Operator records the embedded snapshot as superseded. Calibration/timing review fully PASS; immutable artifacts preserved.
