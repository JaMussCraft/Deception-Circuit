# A3 GREEN Bridges test transport

Status: handed-back

## What changed

Prepared the unbound `plan/a3-green-bridges-transport229` packet in the specificity-ladder worktree's `.superpowers/sdd/`. It validates a coordinator-sealed configuration and source inventory, actual Bridges CPU allocation and job, and a fresh user-owned output namespace; it invokes the unchanged observer in mgnp-only GREEN mode inside the specified container and packed environment. It uses the parent and v1 memory child read-only bind arguments, watches the actual end time and child process group, and records normal transport completion only after the observer's normal mgnp result and source recheck. The final transport manifest SHA-256 is `14adee247cdf1138eeeb0a19ce2536cacc35fc3fd09df8febf578a68d0266a7c`. Earlier communicated hashes are superseded; only this final hash is reviewable.

## How verified

Seven pure fixture tests passed under both local Python 3.9.18 and 3.12.13. They exercise command and path mapping, source hashes and aliases, missing or changed bindings, sealed source inventory, deadline and late reaping checks, observer manifest rejection, and relocated wrapper arguments. Python 3.6 grammar parsing and Bash syntax passed; actual Python 3.6 execution was unavailable. The observer uses a 610-second outer baseline timeout, 90-second oracle and 2,700-second GREEN timeout; the supervisor requires 3,400 seconds plus 30 seconds reserve at launch and caps the child at 3,450 seconds. Packet manifest hashes were regenerated after the last change.

## Execution evidence

No remote action, scheduler job, container, native test suite, production model or GPU ran for this packet. The tests use only local fixtures; they do not establish real allocation, container or observer success.

## What is NOT done

The template is intentionally unbound. The coordinator must supply and seal the final GREEN observer, its complete source and literal-alias inventory, and expected case count, then arrange independent review and site-specific host validation. The earlier r3 inventory is not authority for final r4. Effective cgroup mount flags remain empirical; bind arguments alone do not establish them.

## Open questions

Actual Python 3.6, site container behavior and startup duration need review and, if authorized separately, real host evidence. The 59-minute allocation permits limited startup margin, so an insufficient-time check may fail before child launch. The observer's own outputs remain the test evidence; this transport receipt is not scientific proof or an admission decision.
