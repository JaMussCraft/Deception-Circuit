# H100 marker monitor hand-back

## What changed

No job, watcher, source, or execution artifact was changed. Read-only observations:

- GPU job `50189932` was RUNNING on the first snapshot and later reached scheduler state `COMPLETED|0:0|00:37:40`.
- `CONSUMED-bank.json` and `WAITING-prefix4.json` were present. `bank-command.json` reported exit code 0, elapsed 970.7687 s, started 2026-11-06T17:41:28.000201Z and finished 17:57:38.768870Z.
- `CONSUMED-prefix4.json` appeared with release SHA `798e079abd230bd578ff33e62fce727021e5675fb6625e59cca1ad6ba2942263`.
- The permitted stderr tail showed weight loading completed 291/291 for bank and prefix4.
- `COMPLETE.json` reported `complete:true`, scope `one measured original-H bank + prefix4 scoring only`, `full_scoring_admitted:false`, source commit `50e947bb852613e3a270082651f2bd1b7bb0c525`, GPU H100 80GB. Prefix4 score command reported exit code 0, elapsed 638.8854 s, from 18:01:28.838330Z to 18:12:07.723699Z.

## How verified

Used the assigned fixed SSH route to read only job `50189932` sacct state and small markers under its execution directory. Read only the last 2 KiB of permitted stderr files and the assigned local watcher log for failure/finish indications.

## Execution evidence

Root was notified of bank completion, prefix4 consumption, weight completion, and terminal COMPLETE/scheduler state. Monitoring stopped on scheduler terminal.

## What is NOT done

No scientific acceptance or interpretation was performed. Full scoring was not admitted according to the marker. No scheduler or model commands were run by this monitor.

## Open questions

None for the assigned monitor; root owns subsequent review.
