## Research-session hooks in Codex

Codex runs the research-session hooks from `~/.codex/hooks.json` in every session, and they act only when the working
directory is inside this project. A fresh Codex session must trust them once with `/hooks`; until then Codex skips
them. They count compactions, gate spawns and `sbatch` on the Codex weekly reading, and save each subagent's last
message. A Codex freeze refuses only spawns and `sbatch`, because Codex documents no message tool. Edits made with
`apply_patch` are linted before they land, but shell commands that write files are not. So run
`research-session lint <file>` after every write to a Markdown file under `docs/research/` or `.agents/memory/`.
Codex gets no compaction-summary file and no turn-end reminder, because its hook events do not support them. Only the
user creates the kill switch `/u/swong2/.claude/research-session/DISABLED`, which turns every hook off.
