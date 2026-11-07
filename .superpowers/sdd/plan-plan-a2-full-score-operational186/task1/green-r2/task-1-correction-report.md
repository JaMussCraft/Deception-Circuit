# Task 1 — corrected GREEN-r2 ready

The authorized R198-A/B corrections and declared G3 digest-key correction are complete for review. Root has not run the full 97-case suite or accepted this revision. No further A2 task was started.

Only `candidate/gpu/common.py` and `controller.py` changed relative to root's `source-before-review198` snapshot. A separate `candidate/tests/test_full_score_entry198.py` adds 15 cases; the original 82 assertions remain byte-for-byte unchanged at SHA256 `c5789c8fdc3a6a7aeb0f45a9f08b9f406b9641719659173276658076ffdcae8c`.

## Corrections

R198-A: retain cheap rejection of already-invalid identity, then repeat the immutable release/config/WAITING/catalogue barrier after bank and allocation I/O. Reobserve allocation and repeat the barrier after consume evidence I/O. No current release bytes are adopted. Mutation during the costly bank/allocation boundaries rejects before consume and with zero CLI calls.

R198-B: a slow consume write is followed by fresh actual allocation/deadline/lease eligibility. Keep the minimum deadline observed before and after consume; a subsequent extension cannot recover time. Immediately before the original Popen, the runner samples a fresh clock and enforces the reviewed minimum on the minimum of context, entry/current allocation and child-cap deadlines. A consumed-but-rejected permission remains spent; no retry or lease renewal occurs. Exact-floor equality remains permitted.

The real-bank regression separately exposed the earlier `groups_sha256` lookup error. The one-line correction reads the existing declared `groups_file_sha256` field; it neither changes the closed config nor signs current G3 bytes. Its minimal patch is saved separately.

## Actual focused evidence

All runs here used only tiny local fixture/mocked-I/O tests authorized by root, with the real entry guard unchanged by the tests. Actual interpreters were Python 3.9.18 and Python 3.12.13; no version was spoofed.

1. `local-red`: preserved first attempt, 14 failures in each environment due to the earlier real-bank key error. This is explicitly **not** attributable R198 ordering evidence.
2. `local-red-r2`: after isolating bank I/O, each environment ran 14 cases: 12 intended assertion failures, two positive passes, zero errors. Release/config/WAITING/catalogue mutation during bank or allocation work reached one fake CLI/consume; slow consume and final-allocation shortening also exposed the reviewed gaps. Production still matched the root-frozen eight-file snapshot.
3. `real-bank-red`: the separate real-bank case failed in each environment with the production `groups_sha256` KeyError before correction.
4. `local-green`: 15 corrected cases passed in each environment. Its exact intermediate common/controller source is preserved.
5. `local-green-r2`: the final 15 new cases plus two original tiny once-only/early-mutation cases passed in each environment: 17 tests, zero failures/errors, exit zero. Input pins bind the final source bytes. The full suite remains for root.

Raw stdout/stderr, JUnit, per-case observations and RESULT files are preserved. Archived RED test-source versions exactly match their recorded hashes. `evidence-index.json` distinguishes the non-attributable attempt from accepted narrow RED evidence.

## Frozen review packet

- `pins.json`: `bd43177acf745f48ed133a8419b26477eb6c40d0ddc533d170db7a0a8e556c57` (197 pinned files).
- `correction-diff.patch`: `b53154af1735121bad583e5445ea48dd7314b092b10b8d0400d7d350c50ec2a8`.
- `groups-digest-key-fix.patch`: `4080aef3daf5b776133a11656d0f444db601814649de8d663333c6f7f0295405`.
- New regression file: `748d759b1ca17f9b6efcb4c057edc617b916ebeb99901ae7acecdc591b57d74d`; its complete addition is saved in `regression-test-addition.patch`.

All original RED/source pins still match. Six host/observer Python files passed Python 3.6 grammar/API review, three shell syntax checks exited zero, and frozen direct plus relocated wrapper dry-runs exited zero. Actual Python 3.6 execution is not claimed. The production config template remains unbound, with admission/review false and all resource fields null.

## Root CPU commands

Root holds future A2 work pending its A3 assessment and chooses when to run this already-prepared correction suite and scoped review. Root supplies its actual CPU partition and fresh usage/session checks. The request remains two CPUs, 4 GiB, eight minutes, no GPU; each interpreter has a 120-second suite cap.

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2/launch_cpu_green.sh --dry-run --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2/executions/delta-green-r2-01
sbatch --test-only --account=beto-delta-cpu --partition="${A2_T1_CPU_PARTITION:?root chooses actual CPU partition}" --nodes=1 --ntasks=1 --cpus-per-task=2 --mem=4G --time=00:08:00 --job-name=a2-fullscore-t1-r2 --export=ALL --chdir=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2 --output=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2/cpu-green-%j.out /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2/launch_cpu_green.sh --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2/executions/delta-green-r2-01
sbatch --account=beto-delta-cpu --partition="${A2_T1_CPU_PARTITION:?root chooses actual CPU partition}" --nodes=1 --ntasks=1 --cpus-per-task=2 --mem=4G --time=00:08:00 --job-name=a2-fullscore-t1-r2 --export=ALL --chdir=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2 --output=/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2/cpu-green-%j.out /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2/launch_cpu_green.sh --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task1/green-r2/executions/delta-green-r2-01
```

The observer requires all 97 names (original 82 plus new 15) to pass in both actual environments, with unchanged pins and no errors/skips. Old GREEN job `23613976` was root-confirmed unstarted and cancelled at zero seconds; it supplied no test evidence. Old packets and results were preserved. No worker scheduler/RS/git/remote/model/native/heavy-suite action occurred, and no source publication, resource binding or GPU authority follows.
