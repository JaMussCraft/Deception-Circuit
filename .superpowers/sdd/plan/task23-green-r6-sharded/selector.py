"""Diagnostic253 successor: full collection, frozen ordered execution, durable phases."""
import json
import os
from pathlib import Path
import sys
import time

_LOG = None

def _event(value):
    value['unix_seconds'] = time.time()
    _LOG.write(json.dumps(value, sort_keys=True) + '\n')
    _LOG.flush()
    os.fsync(_LOG.fileno())

def pytest_runtestloop(session):
    global _LOG
    if session.config.option.collectonly:
        return None
    partition = json.loads(Path(os.environ['A3_SHARD_PARTITION']).read_text())
    expected = partition['full_collection']
    selected = partition['shards'][os.environ['A3_SHARD']]['execution_order']
    assert not session.testsfailed and not session.shouldstop
    assert [item.nodeid for item in session.items] == expected
    assert selected and len(set(expected)) == len(expected) and len(set(selected)) == len(selected)
    lookup = {item.nodeid: item for item in session.items}
    items = [lookup[node] for node in selected]
    _LOG = Path(os.environ['A3_SHARD_EVENTS']).open('x')
    import pytest
    _event(dict(python_version=sys.version, pytest_version=pytest.__version__, pytest_origin=pytest.__file__, event='start', kind='SHARD_ONLY', collected=expected, requested=selected,
        python=sys.executable, executable=os.path.abspath(sys.executable), full_suite_accepted=False,
        execution_authorized=False))
    try:
        for index, item in enumerate(items):
            _event(dict(event='item-start', nodeid=item.nodeid))
            following = items[index + 1] if index + 1 < len(items) else None
            session.config.hook.pytest_runtest_protocol(item=item, nextitem=following)
            _event(dict(event='item-finish', nodeid=item.nodeid))
            if session.shouldstop or session.shouldfail:
                raise RuntimeError('pytest stop before normal shard completion')
        _event(dict(event='finished', requested_count=len(items), full_suite_accepted=False))
    finally:
        _LOG.close()
        _LOG = None
    return True

def pytest_runtest_logreport(report):
    if _LOG is not None:
        _event(dict(event='phase-report', nodeid=report.nodeid, when=report.when,
            outcome=report.outcome, duration_seconds=report.duration,
            longrepr=str(report.longrepr) if report.failed else None))
