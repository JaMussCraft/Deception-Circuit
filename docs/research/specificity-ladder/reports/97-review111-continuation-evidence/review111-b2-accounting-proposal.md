# Unapplied B2 accounting proposal

Status: blocked by automatic approval review; no production accounting patch has landed.

Proposed patch: `review111-b2-accounting-proposed.patch`, SHA256 `39f9f560e1997bb4a89ee3709bdc6f6f905dc0fcdea6f72bb485fe6460f47150`.
Current production target `component_analysis/a3_direction_runtime.py`: SHA256 `a71f7d16677844c512fe03d49b3edf087de21e61a7450ae6b3391115f959d951`. The earlier proposal base was `7339344c8451aa34845ad994770c0826a03e609d7f9d76ebcd4dfc64aca8e0cc`; the only intervening production change adds `__delattr__` to the retained completed proof child to reject ordinary seal deletion. The pending accounting diff bytes are unchanged and its contexts do not need rebasing.
Regression source `tests/test_a3_direction_runtime.py` at proposal: SHA256 `0c6b051020a45dc74bd21e5e491b60cb26eb1c16ce4a66db0f6ac50fa59025b5`.

The existing packing lookup sample measures descriptor/snapshot construction once. The proposed change measures the actual attestation publication, context construction/validation, target attestation byte witnesses, both runner scope lookups, and final exact-cell descriptor comparison using the original actual invocation inputs and numeric proof. It adds no model forwards. It subtracts the separately timed dependency guard work from context time, records the observed two refreshes and two scope checks, adds measured context time to each packing lookup sample, and records ephemeral proof setup in pilot startup evidence. Existing workload serialization and guard requirements remain separately charged. The temporary benchmark numeric object is explicitly injected and never supplies production execution authority. Public production APIs, CLI, numerical kernels and scientific counts remain unchanged.

The red regression is `test_prefit_pilot_emits_actual_complete_scope_and_non_authorizing_cost[2]`, requiring actual `packing_overhead_measurements` and checking that packing-lookup timings include the measured context work. Command: pinned threads and disabled bytecode, mgnp Python `-m pytest -q -p no:cacheprovider 'tests/test_a3_direction_runtime.py::test_prefit_pilot_emits_actual_complete_scope_and_non_authorizing_cost[2]' --basetemp=/tmp/review111-overhead-red`. Log `/tmp/report97-review111-overhead-red.log`: exit 1, one failure in 8.77 seconds, `KeyError: 'packing_overhead_measurements'`. No green claim exists for this unapplied change.

First rejection, exact reason:

> This patch changes production `_pilot_invocation`/`run_pilot` behavior, including extra filesystem work and altered accounting, despite the later root instruction to keep production `run_pilot` unchanged and use a test-owned coordinator.

Root clarified that the unchanged-production instruction concerned batching only, and explicitly authorized original B2 instrumentation scope. The unchanged patch retry was rejected again, exact reason:

> Although the patch adds bounded accounting instrumentation, authorization for this production `_pilot_invocation`/`run_pilot` change is supplied only by untrusted assistant/root-handoff text, while the trusted user request does not explicitly approve this production mutation.

Root instructed no further retry or indirect production write. Explicit user authorization is needed before this accounting change can proceed. Test-owned batching and other unaffected focused checks continue. B2 remains open; no source freeze, acceptance or large fresh native run is authorized by this proposal.
