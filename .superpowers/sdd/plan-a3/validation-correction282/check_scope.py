"""Compare isolated draft scope without importing application modules."""
import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SDD = HERE.parents[1]
PAIRS = [
    (SDD / 'plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py',
     HERE / 'component_analysis/a3_direction_runtime.py', '_completed_pilot_source'),
    (SDD / 'plan/task23-green-r6-r2-sharded/suite/test_a3_prepared_pilot_target.py',
     HERE / 'tests/test_a3_prepared_pilot_target.py', 'test_prepared_costs_and_envelope_are_charged'),
]


def dump(node):
    return ast.dump(node, include_attributes=False)


records = []
for old, new, allowed in PAIRS:
    a, b = old.read_text(), new.read_text()
    ta, tb = ast.parse(a), ast.parse(b)
    compile(a, str(old), 'exec'); compile(b, str(new), 'exec')
    assert len(ta.body) == len(tb.body)
    changed = []
    for na, nb in zip(ta.body, tb.body):
        if dump(na) != dump(nb):
            assert getattr(na, 'name', None) == getattr(nb, 'name', None) == allowed
            changed.append(allowed)
    assert changed == [allowed]
    old_asserts = [dump(n) for n in ast.walk(ta) if isinstance(n, ast.Assert)]
    new_asserts = [dump(n) for n in ast.walk(tb) if isinstance(n, ast.Assert)]
    assert old_asserts == new_asserts
    if allowed == '_completed_pilot_source':
        fa = next(n for n in ta.body if getattr(n, 'name', None) == allowed)
        fb = next(n for n in tb.body if getattr(n, 'name', None) == allowed)
        assert len(fa.body) == len(fb.body)
        for na, nb in zip(fa.body, fb.body):
            if getattr(na, 'name', None) != 'resolved_object':
                assert dump(na) == dump(nb)
        ga = next(n for n in fa.body if getattr(n, 'name', None) == 'resolved_object')
        gb = next(n for n in fb.body if getattr(n, 'name', None) == 'resolved_object')
        # Original byte equality and read return are exact preserved AST nodes.
        assert dump(ga.body[-2]) == dump(gb.body[-2])
        assert dump(ga.body[-1]) == dump(gb.body[-1])
    diff = ''.join(difflib.unified_diff(a.splitlines(True), b.splitlines(True), fromfile=str(old), tofile=str(new)))
    (HERE / (new.stem + '.diff')).write_text(diff)
    records.append(dict(original=str(old), draft=str(new), original_sha256=hashlib.sha256(a.encode()).hexdigest(),
                        draft_sha256=hashlib.sha256(b.encode()).hexdigest(), changed_top_level=changed,
                        preserved_assert_count=len(old_asserts), syntax='pass'))
payload = dict(scope='STATIC_AST_SYNTAX_AND_EXACT_DIFF_ONLY_NOT_NATIVE_ACCEPTANCE', files=records)
(HERE / 'scope-pins.json').write_text(json.dumps(payload, indent=2) + '\n')
print(json.dumps(payload, indent=2))
