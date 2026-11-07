# Task 4 startup identity correction 287

Status: isolated test-only draft, awaiting root review and native validation.

The actual native RED is preserved in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/validation-failure281/observed-terminal-50319108.json`: startup record validation fails because the test expects the no-Slurm injected fallback while runtime records the ambient Slurm job. Report 287 documents the source-derived cause; production semantics remain unchanged.

The new complete test-file copy is `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/startup-identity-correction287/tests/test_a3_direction_runtime.py`. Input exercised-suite SHA-256 is `8a314262a2c4fb09c9f6ca883264e072d475affde7a4b927a4379b9c276ec112`; output SHA-256 is `760cfe9c9aef14b0ab3a0b41eaba526b2aa64376334be1bea5a710978f9c6f23`.

Only `test_completed_index_startup_is_measured_conditionally_and_charged_per_job` changes:

- Import `os` locally, then capture `expected_job_id=os.environ.get('SLURM_JOB_ID','injected-cpu')` and `expected_pid=os.getpid()` before fixture/index construction.
- Assert the record's job/PID against these independent values and pass both to the original positive validator call.
- Use the independently captured job and `expected_pid+1` for the existing wrong-PID rejection, and add a separate wrong-job rejection with the correct PID.
- Replace all four original hardcoded job arguments in that test, including missing-marker and changed-payload validation paths. All existing damage operations, expected exception types and cost/resource/linkage assertions remain.

No record-derived expected identity, environment mutation, runtime change or additional test identity/parametrization is introduced. The original function has seventeen assertion statements; the draft retains them with only the authorized validator-argument changes and adds one independent identity assertion. The wrong-job rejection is an added `pytest.raises` check within the same existing case.

Bounded checks are in the same new directory: `check_draft.py`, `pure-results.json`, `scope-pins.json`, `test_a3_direction_runtime.diff`. Both `/sw/external/python/anaconda3/bin/python3.9` and `/u/swong2/.conda/envs/mgnp/bin/python` ran `check_draft.py`, exit zero, no stderr, with twenty-second subprocess limits. The script AST-compares all other top-level nodes exactly, preserves the target's function arguments/decorators and every original statement in order after only the authorized call-argument normalization, and compiles the full old/draft source in memory. This statically preserves existing test identities and parametrizations; no native collection or claim of 223 passing cases occurs.

The same script extracts only the draft's two expected-identity assignments and the native validator's two job/PID guards. Controlled environment specimens cover absent Slurm job, the actual observed job string, and a present empty string; actual environment is never changed. Each specimen's five call argument sets produce the expected sequence: positive pass, wrong PID reject, wrong job reject, then two identity-only passes for the marker/payload paths. These last passes establish only that the expected identity does not introduce an unrelated mismatch; the real marker/payload authentication is outside this extracted probe and remains required natively. The independent expected PID is a literal process stand-in. No native record/source authentication or target construction runs.

Active candidate183, correction282, the exercised suite and frozen unsubmitted r7 remain unchanged. Root owns independent review, lint/number checks and assembly of any distinct r8. Combining this test file with correction282 is a later root action; no source publication, native import/test, scheduler/SSH/Git/RS operation, agent or new job occurred. All original full-case, both-environment and source/resource/numerical/GPU gates remain.
