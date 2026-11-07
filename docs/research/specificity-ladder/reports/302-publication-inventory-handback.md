# Hand-back 302: Prepublication source mapping

Agent: Terra inventory worker. Status: handed-back.

## What changed

Created `/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/publication-inventory302/inventory.json`. It maps the frozen candidate to current worktree paths, with source pins and both byte hashes. The earlier inventory 280 is preserved. This is prepublication only, pending complete 223-case acceptance in both environments and subsequent root review; it is not publication or commit authority.

## How verified

All 362 ordinary candidate files in the 364-entry source-pin map match their candidate pins. Of those, 348 match current worktree bytes, 10 differ and four have no ordinary worktree file; the 14 differing or absent paths are precisely the prior inventory 280 paths. The remaining two pinned entries are registry symlinks to current worktree files, and both target hashes match their pins. No other missing candidate paths or candidate pin mismatches were found.

The three named candidate hashes match the supplied values: runtime `1d6c3886a7634641a8a4ad64135adeef34dcdac7ce6b388e8441df1bf2cea116`, prepared test `2f89de3edb0ac5d513b98c018c6ab1393179b73d9ee67c64d725a064eaa09fb3`, and runtime test `760cfe9c9aef14b0ab3a0b41eaba526b2aa64376334be1bea5a710978f9c6f23`. The inventory records exact prior inventory and source-pin file hashes and paths.

## Execution evidence

Not applicable: no runs.

## What is NOT done

No source copying, edits, tests, native imports, Git, jobs or publication. This is a point-in-time comparison, not an approval to overwrite worktree changes or an assertion of complete native execution.

## Open questions

- Root must assess worktree ownership and recheck all bytes after the remaining acceptance gates, before any eventual publication. Default: preserve current source and keep publication closed.
