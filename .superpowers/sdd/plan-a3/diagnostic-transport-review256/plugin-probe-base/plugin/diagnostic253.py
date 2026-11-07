"""Root CPU DIAGNOSTIC_PARTIAL only; never acceptance, no test/assertion edits."""
import json
import os
from pathlib import Path
import time

_LOG = None

def _event(value):
    value['unix_seconds'] = time.time()
    with _LOG.open('a') as stream:
        stream.write(json.dumps(value, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())

def pytest_runtestloop(session):
    global _LOG
    # The original collection hook has already authenticated all223 nodes.
    expected = json.loads(Path(os.environ['DIAG253_COLLECTED']).read_text())
    selected = json.loads(Path(os.environ['DIAG253_SELECTION']).read_text())
    assert [item.nodeid for item in session.items] == expected
    assert selected and len(selected) == len(set(selected))
    wanted = set(selected)
    items = [item for item in session.items if item.nodeid in wanted]
    assert [item.nodeid for item in items] == selected
    output = Path(os.environ['DIAG253_OUTPUT'])
    output.mkdir(parents=True, exist_ok=False)
    _LOG = output / 'events.jsonl'
    _event(dict(kind='DIAGNOSTIC_PARTIAL', event='start', collected=len(expected),
                requested=selected, acceptance=False, execution_authorized=False))
    for index, item in enumerate(items):
        _event(dict(event='item-start', nodeid=item.nodeid))
        following = items[index + 1] if index + 1 < len(items) else None
        session.config.hook.pytest_runtest_protocol(item=item, nextitem=following)
        _event(dict(event='item-finish', nodeid=item.nodeid))
    _event(dict(event='finished', requested_count=len(items), acceptance=False))
    return True

def pytest_runtest_logreport(report):
    if _LOG is None:
        return
    _event(dict(event='phase-report', nodeid=report.nodeid, when=report.when,
                outcome=report.outcome, duration_seconds=report.duration,
                longrepr=str(report.longrepr) if report.failed else None))
