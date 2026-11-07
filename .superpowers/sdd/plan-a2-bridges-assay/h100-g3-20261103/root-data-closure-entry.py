from pathlib import Path
import hashlib,json,subprocess
P=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/data-closure-supplement')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'packet-manifest.json')=='ed76c315390fd7bf55d166abe40f75325a2c7df3ca2a2c30fb374cbc9df91b77'
m=json.loads((P/'packet-manifest.json').read_text())
for name,digest in m['files_sha256'].items(): assert sha(P/name)==digest,name
raise SystemExit(subprocess.call(['bash',str(P/'launch.sh')]))
