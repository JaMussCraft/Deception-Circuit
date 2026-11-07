# Hand-back 35: Formal grader freeze command reconnaissance

Agent: infrastructure reader. Status: resolved.

## What changed

Only this report was written, in both the requested worktree and the hook-required primary directory:

- `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research/specificity-ladder/reports/35-grader-registry-recon-handback.md`
- `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/35-grader-registry-recon-handback.md`

No source, registry, session, configuration, usage counter, cadence, or gate was changed.

### Authoritative source and installation

The live package is `/projects/beto/swong2/Alignment/.agents/research_session/` and its tests are `/projects/beto/swong2/Alignment/.agents/tests/`. This is original Python source, not a generated Codex skill adapter. `readlink -f` resolves registry.py to itself. The shared bridge generator has no research_session references. `/u/swong2/.local/bin/research-session` directly executes base Python with `-B` against the live cli.py; no package installation or wrapper change is needed for a new registry parser.

Authority is explicit in `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/spec.md`, R1: RS lives in the Alignment package, staged by agents and applied by the orchestrator. The durable historical staging tree is documented in that feature's README, not an alternate automatically regenerated source. I did not inspect private staging contents. The original apply tool is `/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/autoresearch-workflow/tools/apply_staged.py`; its module documentation says agents stage full files and operation lists, and the orchestrator applies them. Wave A covers RS code/tests after review.

Live registry.py and cli.py are owned by swong2, mode 0600 with ACLs, and the agent runs as swong2. The containing .agents directories have group and ACL permissions. OS ownership is not the main constraint: the managed sandbox marks .agents as protected, and the project requires staging/orchestrator application. A direct edit of the live source should not be assumed authorized by filesystem ownership. No chmod, settings, hook or permission changes are needed or proposed. An installed command will use the existing private lock directory through records.state_lock; this is the same established RS write mechanism as claim, not a new session-state setter.

### Smallest formal implementation

Add a function and parser solely in `/projects/beto/swong2/Alignment/.agents/research_session/registry.py`:

```text
research-session freeze-grader SLUG SHA256 --session ID [--root RESEARCH_ROOT]
```

The parser should require `--session`, accept no `--as` override, and resolve the explicit selector using state.find_session. Reject an empty selector as well, so an empty shell argument cannot fall through to cwd selection. The existing resolver accepts full ID, exact tag, or unique prefix; ambiguous and missing selectors raise StateError. Explicit full session ID or established tag is preferred operationally. Do not copy claim's optional selector behavior: without a selector it chooses the most recently updated session with the same cwd.

Before entering the edit helper, require a string matching exactly lowercase hexadecimal of length sixty-four. Use re.fullmatch or an equivalent strict end check: the existing validator uses dollar anchoring, which can accept a final newline. Reject whitespace, uppercase, short, long and nonhex values. Preserve the existing registry convention rather than silently normalizing input.

Inside the callback passed to the existing `_edit_directions(root, slug, callback)`:

- Require status claimed or active and claimed_by exactly equal to the resolved session tag. A row with no claimant, another claimant, or a paused/done/abandoned status must refuse.
- Accept only a null/missing existing frozen_grader_sha256 or the identical hash. Refuse a different existing value; there is no replacement or force option.
- Set only frozen_grader_sha256. Let the helper perform its existing row/global updated date stamps, lock, load validation, final full-registry validation, and atomic write.

Use the module's existing stderr and return conventions: malformed input/session selector is a usage error; unknown direction, ownership, status, conflicting hash or invalid registry is a refusal. Same-hash acceptance is semantically idempotent; the current helper still rewrites and stamps the dates. Do not refactor it merely to avoid that harmless existing behavior.

No change to cli.py routing is required: registry is already in RECORD_MODULES and registers commands through add_parsers. Add a short command description to `/projects/beto/swong2/Alignment/docs/agents/research-session.md` and, if maintained as the binding command surface, the autoresearch-workflow spec section on commands. This does not require changing protocol cadence, acknowledgement, usage thresholds, ledger caps or gate allowlists.

After review/application, the orchestrator can target primary explicitly:

```text
research-session freeze-grader specificity-ladder HASH --session codex-01a1987e --root /projects/beto/swong2/Alignment/Deception-Circuit/docs/research
```

HASH is a placeholder to recompute from the actual reviewed worktree using its evaluation/grader_hash.py before invocation, then record consistently in its spec. The existing spec lists a fingerprint but says it is not installed and omits external rubric files; that remains a scientific provenance limitation. This setter does not make EVAL 5 authorized, choose MMLU sample size, or close the other preflight conditions.

### Exact test plan

Extend the registry CLI test class in `/projects/beto/swong2/Alignment/.agents/tests/test_research_session_registry.py`. Reuse its helpers for rows, claims, directions, sessions and CLI calls; the shared fixtures put all writes in temporary roots. These existing tests show the nearest patterns:

```text
RegistryCliTest.test_claim_and_release
RegistryCliTest.test_claim_uses_the_session_tag
RegistryCliTest.test_validate_dispatch
ValidatorTest.test_directions_bad_cases
```

Add cases for initial null freeze on owned claimed and active rows; matching hash retry; malformed hashes including final newline; missing/empty/unknown/ambiguous selector; absent direction; unclaimed/foreign/paused/completed rows; different existing hash; invalid input registry; explicit selection overriding a newer same-cwd foreign session; unrelated rows/fields preserved; and private session/direction state, worklog, ledger and usage fixtures remaining byte-identical. For refusals compare registry bytes before/after. Mock or wrap `_edit_directions` to show the successful command uses that helper, and test ownership/conflict checks through the callback while locked. Existing tests use temporary directories, mock credential/HTTP readers and never need live usage or credentials.

Run against staged package/tests first, preserving their shared helper layout, then installed paths after orchestrator application. Run both supported interpreters, with bytecode disabled, cache provider disabled and BLAS threads pinned:

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /sw/external/python/anaconda3/bin/python3.9 -B -m pytest -q -p no:cacheprovider /projects/beto/swong2/Alignment/.agents/tests/test_research_session_registry.py
```

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /u/swong2/.conda/envs/mgnp/bin/python -B -m pytest -q -p no:cacheprovider /projects/beto/swong2/Alignment/.agents/tests/test_research_session_registry.py
```

Then run the same interpreters/options on the complete `.agents/tests/test_research_session_*.py` suite. These are proposed validation commands, not checks run during this read-only task.

### Authorization assessment

The approved START explicitly requires recording the hash in spec.md and directions.json before any benchmark. The session protocol Start step on the frozen grader and the autoresearch-workflow grader-freeze rule repeat this. I found no explicit human-only requirement for initially recording that hash. Human-only checkpoint/cadence rules and explicit permission for EVAL 5 remain separate. The protocol's always-ask list covers merging, EVAL 5, dropping a direction, and raising caps, not initial grader metadata.

Accordingly, the existing START authorization reasonably covers an initial metadata freeze through a formal owned-direction RS command, provided the orchestrator reviews/applies the small infrastructure addition under the existing source process. This is an interpretation of the written rules, not a new user authorization. Replacing a nonnull differing hash requires a new spec ruling before any benchmark; this proposed command deliberately refuses that operation.

## How verified

Read-only file inspections included these exact narrow commands:

```text
sed -n '710,850p' .agents/research_session/registry.py
```

Observed: _caller_tag delegates optional selection to state.find_session; _edit_directions locks, loads/validates, updates timestamps, validates and writes; only claim/release parsers exist for direction mutations.

```text
sed -n '175,215p' .agents/research_session/state.py
```

Observed: explicit selectors match exact ID/tag or unique prefix; absent selector chooses latest cwd match.

```text
cat /u/swong2/.local/bin/research-session
```

Observed: wrapper directly invokes the Alignment package cli.py with base Python and -B.

```text
/u/swong2/.local/bin/codex-usage --pause-at 80
```

Observed: status ok, weekly used eleven percent, remaining eighty-nine percent, should_pause false; reset November sixth at 11:07 am EST. No tests, science scripts, jobs or paid APIs were run.

## Execution evidence

Not applicable: no runs.

## What is NOT done

Implementation, staging, application, test execution, hash recomputation and actual registry freeze remain for the orchestrator. No private writer was invoked. No git, GPU, API, notebook or subagent activity occurred. The startup synchronizer was not run because this task explicitly required read-only work; that is the parent session's responsibility.

Two broad read-only shell commands were denied by the project PreToolUse hook because their search terms or paths contained protected human-command/session strings. Neither command executed. I continued with unaffected repository-file reads; no guard was changed and no protected private staging path was inspected. This is a hook refusal, not an automatic sandbox approval-review rejection.

## Open questions

No human answer is required by the grader-field rules found. The orchestrator must decide whether to carry this small formal setter through staging/review/application now. Default: do so before scoring, without editing directions.json by hand. If installation is denied by the existing hook or sandbox, keep scoring blocked, report the concrete denial and seek only the needed source application approval. Do not reinterpret that as authorization to alter cadence or session controls.
