"""Stdlib baseline export closure check; native validators remain authoritative."""
import hashlib
import json
from pathlib import Path

GRADER = '866fd15dd30b695e46ffe955b09894fb831af92e2b9015eafbd7f0eee151d2f9'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_context(root, pins):
    root = Path(root).resolve()
    files = {}

    def read(relative):
        path = root / relative
        require(path.resolve().is_relative_to(root), 'escaped context: ' + relative)
        require(not any(part.is_symlink() for part in [path, *path.parents] if part != root and root in part.parents),
                'context alias: ' + relative)
        require(path.is_file(), 'missing context: ' + relative)
        require(relative in pins, 'unpinned context: ' + relative)
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        require(digest == pins[relative], 'context hash mismatch: ' + relative)
        files[relative] = dict(sha256=digest, bytes=len(data))
        return json.loads(data)

    protected = read('docs/research/held_out.json')
    directions = read('docs/research/directions.json')
    require(isinstance(protected, dict) and protected.get('schema') == 1 and
            isinstance(protected.get('sets'), list), 'invalid protected registry')
    require(isinstance(directions, dict) and isinstance(directions.get('directions'), list),
            'invalid directions registry')
    entry = next((row for row in directions['directions'] if row.get('id') == 'specificity-ladder'), {})
    require(entry.get('frozen_grader_sha256') == GRADER, 'missing/stale frozen grader registry')
    for entry in protected['sets']:
        require(isinstance(entry, dict), 'invalid protected entry')
        if 'path' not in entry:
            continue
        relative = entry['path']
        require(isinstance(relative, str) and not Path(relative).is_absolute(), 'invalid context path')
        raw = read(relative)
        require(files[relative]['sha256'] == entry.get('sha256'), 'protected dependency hash mismatch')
        if isinstance(raw, dict):
            raw = raw.get('instance_ids', raw.get('ids', raw.get('rows')))
        require(isinstance(raw, list) and len(raw) == entry.get('n'), 'protected dependency count mismatch')
    return dict(files=files, protected_sets=len(protected['sets']), native_imports=False)
