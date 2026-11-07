# A3 transport process-group cleanup successor

Status: handed-back

## What changed

Created distinct `plan/a3-green-bridges-transport229-r2` under the specificity-ladder worktree's `.superpowers/sdd/`, preserving the predecessor. Failed and interrupted runs send TERM to the owned child process group even when its leader has exited, wait a bounded grace period, send KILL if the group remains, and reap the leader. Missing groups are handled safely. Normal completion rejects a remaining process group and follows failure cleanup. The successor's launch and per-job namespace use its new path; the config template, observer authority and resource, source and deadline guards are unchanged. The final manifest SHA-256 is `c8b9f2a43027134d1ae7b2c7e17c7f588c5524ff00c3e3aa70f2185d0c88d4e5`.

## How verified

Two small real-process regressions reproduced surviving grandchildren under the predecessor cleanup in both Python environments: a reaped leader with a live child, and a leader exiting on TERM while its child ignores TERM. Both cases then passed with the successor. Nine focused tests passed in each of Python 3.9.18 and 3.12.13 in under one second per suite. Raw red and green logs are included and hashed in the successor manifest. Bash syntax and Python 3.6 grammar checks passed; actual Python 3.6 was not available. The predecessor manifest remains `14adee247cdf1138eeeb0a19ce2536cacc35fc3fd09df8febf578a68d0266a7c`.

## Execution evidence

No scheduler job, remote action, container, native test suite, production model or GPU ran. Local process fixtures created and terminated only their own new process groups. The results do not establish actual Bridges execution.

## What is NOT done

Independent review of this exact successor, final source configuration and any deployment remain outstanding. No observer, scientific source, authority or earlier packet was changed.

## Open questions

The reviewer should inspect cleanup across failure, signal and normal completion paths, and the coordinator must validate actual host and container behavior before any separately authorized run.
