# Task2 r4 baseline-oracle correction

Pins SHA256 `ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4` bind266 files. Production, all semantic test bodies and the original baseline snapshot are unchanged; every prior252 pin was checked. Failed r3 job23620810 and every raw output remain preserved and pinned. Root reported FAILED1:0/21 seconds. Neither environment reached GREEN.

Both actual XMLs contain exactly22 baseline cases,19 failures,3 passes, zero errors/skips and identical name sets. The additional passing case is `test_review224_actual_Task2_COMPLETE_satisfies_actual_Task1_consumer[timely_window]`. It explicitly inserts `timely_window=False` into the original CPU receipt; the actual Task1 consumer rejects that false value at its first CPU condition before later missing fields. The positive None producer-compatibility case still fails. `narrow-ruling.json` records this attribution. The other two passes are the unchanged negative alias cases.

Only the new observer's baseline oracle changes: it requires exact19 failed names and exact3 passed names from both authenticated XMLs, not just counts or a partial subset. Duplicate/substituted/missing cases reject. All22 baseline cases remain, followed by all226 corrected GREEN cases in both interpreters. No production guard or test body changes to force RED. Root accepted this narrow oracle correction; independent review precedes actual dispatch.

Same resource proposal: Delta CPU/cpu-interactive, one node/task, two CPUs, eight GiB, six minutes, no GPU/requeue. RED30 seconds/environment, GREEN90 seconds/environment. Require exact baseline sets and then226 passes, zero failures/errors/skips, matching names and before/after pins. Preserve and stop on any unexpected observation; no automatic retry.

Preview:

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r4/launch_cpu_green.sh --pins-sha256 ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4 --dry-run --output /tmp/a2-task2-r4-preview
```

Exact command within root's CPU allocation, fresh absent output:

```bash
bash /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r4/launch_cpu_green.sh --pins-sha256 ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4 --output /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-plan-a2-full-score-operational186/task2/green-r4/root-green-01
```

AST/shell and relocated preview pass; no additional pytest case or full suite was run locally in this correction. Prior r3 tiny-marker2/2-per-environment evidence remains preserved. No native proof/resource/witness/Task3/GPU admission is produced. Root retains all scheduler and review actions.
