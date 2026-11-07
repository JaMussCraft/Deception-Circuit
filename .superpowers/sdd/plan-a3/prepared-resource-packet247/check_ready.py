"""Validate description bindings only; never run or authorize CPU/model work."""
import argparse
import json
from pathlib import Path
import re

REFERENCE_KEYS = ('actual_job', 'source_publication', 'admission', 'resources',
                  'design', 'protocol', 'pilot_inventory')


def validate(config):
    errors = []
    if config.get('execution_authorized') is not False:
        errors.append('execution_authorized must remain false: packet is descriptive only')
    if not isinstance(config.get('source_commit'), str) or not re.fullmatch('[0-9a-f]{40}', config['source_commit']):
        errors.append('source_commit is unpublished/unbound')
    for key in REFERENCE_KEYS:
        ref = config.get(key)
        if not (isinstance(ref, dict) and isinstance(ref.get('path'), str)
                and Path(ref['path']).is_absolute() and isinstance(ref.get('sha256'), str)
                and re.fullmatch('[0-9a-f]{64}', ref['sha256'])):
            errors.append(key + ' requires root-bound absolute path and exact content hash')
    if config.get('phase') == 'receiver':
        for key in ('target_reference', 'preparation_reference', 'namespace_policy'):
            if not isinstance(config.get(key), dict) or not config[key]:
                errors.append(key + ' is unbound')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    args = parser.parse_args()
    errors = validate(json.loads(args.config.read_text()))
    print(json.dumps(dict(status='UNBOUND' if errors else 'DESCRIPTION_BOUND_ONLY', errors=errors,
                         execution_authorized=False, native_imports=False), indent=2))
    return 2 if errors else 0

if __name__ == '__main__':
    raise SystemExit(main())
