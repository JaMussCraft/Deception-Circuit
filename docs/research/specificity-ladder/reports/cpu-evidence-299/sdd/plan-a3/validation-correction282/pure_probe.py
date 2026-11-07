"""Tiny extracted checks only: no application imports or native acceptance."""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def boundary(path, origin):
    tree = ast.parse(path.read_text())
    outer = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_completed_pilot_source')
    nested = next(n for n in outer.body if isinstance(n, ast.FunctionDef) and n.name == 'resolved_object')
    calls = []
    def reference(value):
        calls.append(('reference', value))
        return {'path': value, 'files': {'payload.json': {'sha256': 'fixture-only', 'nbytes': 2}}}
    def read(value):
        calls.append(('read', value))
        return {'fixture': 'payload'}
    ns = dict(origin=origin, require=require, object_reference=reference, read_object=read, os=os)
    exec(compile(ast.Module(body=[nested], type_ignores=[]), str(path), 'exec'), ns)
    return ns['resolved_object'], calls


def run(path):
    failures = []
    specimens = [({}, 'absent'), ({'ref': None}, 'null'), ({'ref': 'bad'}, 'scalar'),
                 ({'ref': []}, 'list'), ({'ref': {}}, 'no-path'),
                 ({'ref': {'path': None}}, 'null-path'), ({'ref': {'path': 7}}, 'integer-path'),
                 ({'ref': {'path': []}}, 'list-path'), ({'ref': {'path': ''}}, 'empty-path')]
    for origin, label in specimens:
        fn, calls = boundary(path, origin)
        try:
            fn('ref')
        except ValueError:
            if calls:
                failures.append(label + ': reached reference I/O')
        except Exception as error:
            failures.append(label + ': leaked ' + type(error).__name__)
        else:
            failures.append(label + ': accepted')
    for valid_path in ('/fixture/object', Path('/fixture/object')):
        ref = {'path': valid_path, 'files': {'payload.json': {'sha256': 'fixture-only', 'nbytes': 2}}}
        fn, calls = boundary(path, {'ref': ref})
        assert fn('ref') == (valid_path, {'fixture': 'payload'})
        assert calls == [('reference', valid_path), ('read', valid_path)]
        damaged = copy.deepcopy(ref)
        damaged['files']['payload.json']['sha256'] = 'tampered'
        fn, calls = boundary(path, {'ref': damaged})
        try:
            fn('ref')
        except ValueError:
            assert calls == [('reference', valid_path)]
        else:
            raise AssertionError('byte-reference equality bypassed')
    return dict(scope='NON_NATIVE_EXTRACTED_REFERENCE_BOUNDARY_ONLY', failures=failures,
                malformed_cases=len(specimens), valid_path_cases=2, unequal_reference_cases=2)


if __name__ == '__main__':
    target = OLD if sys.argv[1] == 'red' else HERE / 'component_analysis/a3_direction_runtime.py'
    result = run(target)
    print(json.dumps(result, indent=2))
    sys.exit(bool(result['failures']))
