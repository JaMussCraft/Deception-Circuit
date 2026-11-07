# A3 transport alias inventory successor

Status: handed-back

## What changed

Created distinct `plan/a3-green-bridges-transport229-r3` under the specificity-ladder worktree's `.superpowers/sdd/`. Its configuration guard requires the exact eight virtual alias paths: four in the preallocation candidate and four in the oracle candidate. Existing literal-target, physical mapping, source hash, deadline and process-group cleanup checks remain. The template and wrapper path name the successor. Its manifest SHA-256 is `bd3533cc18025d7d2bf97515060a46f793abd4f4a43609e8dc6c9626d8a6e6e2`; the r2 predecessor remains unchanged.

## How verified

The old four-alias guard rejected the complete eight-alias fixture in both Python environments. The successor accepts that fixture and rejects omission of the four oracle aliases. Direct local source inspection found the expected four literal aliases and targets in each candidate tree and none in the baseline source. Ten focused tests passed under each of Python 3.9.18 and 3.12.13, including the retained real-process cleanup cases. Raw red and green logs are in the successor manifest. Bash syntax and Python 3.6 grammar checks passed; actual Python 3.6 was unavailable.

## Execution evidence

No remote action, scheduler job, container, native suite, production model or GPU ran. These checks do not establish actual Bridges transfer or observer success.

## What is NOT done

The actual final configuration and source inventory remain coordinator-owned and unbound; the older copied inventory was excluded from the new packet. Independent review and deployment remain outstanding. No scientific source or observer changed.

## Open questions

The coordinator must seal and independently review the final source mapping and literal targets, and validate actual host and container behavior before any separately authorized execution.
