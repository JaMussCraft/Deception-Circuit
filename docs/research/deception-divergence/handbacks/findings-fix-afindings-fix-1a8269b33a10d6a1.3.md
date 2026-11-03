# Last message of findings-fix afindings-fix-1a8269b33a10d6a1 (2026-11-02T11:32:12-05:00)

I applied both of your corrections. The findings check and the lint check now both exit 0, on FINDINGS.md and on the hand-back.

My earlier report that the findings check failed was wrong. When given no `--root`, the tool reads the main checkout's FINDINGS.md, even when run from the worktree. Until you commit, check the worktree file with this command:

```
/u/swong2/.local/bin/research-session findings-check --root /projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/docs/research
```

**The new row edits.** Nothing else in these rows changed.
- **F-rte-005** now says the senders sit in "layers 22 to 31".
- **F-rte-006** now gives the key-arm dispersion as 0.21 and 0.17 in raw logits, or 0.021 and 0.028 of the mean twin gap G. I left its "against 0.02" as written, as you asked. The checked control range is 0.019 to 0.030 logits.
- **F-mech-009** now ends with "(superseded by F-rte-001)", which the checker requires.

Compared with main, exactly four rows differ: F-mech-009, F-rte-005, F-rte-006 and F-rte-008. Each is still one table line.

The hand-back records each correction with the file that verifies it, and the corrected check results. I sent you the one-line message with the exit codes.

Files are in `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/deception-divergence/`:
- `docs/research/FINDINGS.md`
- `docs/research/deception-divergence/reports/03-handback.md`
- `docs/research/deception-divergence/reports/f-rte-008-interval-repro.py`
- `docs/research/deception-divergence/reports/f-rte-008-interval-repro.json`
