"""R198-A/B: genuine entry guard around costly I/O and consume evidence.

The owning native preflight/audit are isolated, not the entry guard. Production
accepts no callback parameter; tests replace external module-level I/O only.
"""
import datetime
from pathlib import Path

import pytest

from test_full_score_controller import c, require_module, release, save, sha, S


def at_epoch(value):
    return datetime.datetime.fromtimestamp(value, datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')


def runner(c, monkeypatch, context_end=2000, allocation_ends=(2000,), consumed_at=None):
    controller = require_module('controller', monkeypatch, c)
    guard = controller.common
    # Keep the production entry function unchanged and actually invoked.
    assert controller.entry_release is guard.entry_release
    clock = {'now': 1100.0}
    monkeypatch.setattr(guard.time, 'time', lambda: clock['now'])
    r = release(c)
    waiting = Path(c['evidence_root']) / 'WAITING-full_score.json'
    save(waiting, {'phase': 'full_score', 'bound_config_sha256': r['bound_config_sha256']})
    r['_waiting_path'], r['_waiting_sha256'] = str(waiting), sha(waiting)
    r['catalogues'] = []
    for number in range(4):
        path = Path(c['evidence_root']) / ('catalogue-%d.json' % number)
        save(path, {'fixture_catalogue': number})
        r['catalogues'].append({'virtual_path': str(path), 'sha256': sha(path)})
    observed = {'Popen': [], 'wait_timeouts': [], 'allocations': [], 'clock': clock}
    def allocation(**kwargs):
        index = min(len(observed['allocations']), len(allocation_ends) - 1)
        work_end = allocation_ends[index]
        observed['allocations'].append(work_end)
        return {'facts': {'EndTime': at_epoch(work_end + c['resources']['finish_margin_seconds'])}}
    monkeypatch.setattr(guard, 'allocation', allocation)
    monkeypatch.setattr(controller, 'preflight_full_score', lambda config, acquired:
                        {'environment': {'PYTHONPATH': S}, 'work_deadline': context_end})
    monkeypatch.setattr(controller, 'audit_score_result', lambda config:
                        {'complete': True, 'counts': {'rows': 59652, 'expected': 59652, 'positive_controls': 3396},
                         'domain_audit': {'complete': True}, 'support_mask_audit': {'complete': True}})
    def popen(command, **kwargs):
        observed['Popen'].append({'command': command, 'cwd': str(kwargs['cwd']), 'at': clock['now']})
        class Child:
            pid = 198
            returncode = None
            def wait(self, timeout=None):
                self.returncode = 0
                observed['wait_timeouts'].append(timeout)
                return 0
            def poll(self):
                return self.returncode
        return Child()
    monkeypatch.setattr(controller.subprocess, 'Popen', popen)
    if consumed_at is not None:
        real_write = guard.write
        def slow_consume(path, value):
            real_write(path, value)
            if Path(path).name == 'CONSUMED-full_score.json':
                clock['now'] = consumed_at
        monkeypatch.setattr(guard, 'write', slow_consume)
    return controller, guard, r, observed


def execute(c, controller, r, observed):
    error = None
    try:
        controller.run_full_score(c, r)
    except (ValueError, AssertionError, TimeoutError) as caught:
        error = caught
    save(Path(c['evidence_root']) / 'R198-observation.json',
         {'Popen_count': len(observed['Popen']), 'wait_timeouts': observed['wait_timeouts'],
          'allocation_work_ends': observed['allocations'], 'final_clock': observed['clock']['now'],
          'consumed': (Path(c['evidence_root']) / 'CONSUMED-full_score.json').exists(),
          'error': None if error is None else repr(error)})
    return error


@pytest.mark.parametrize('during', ['bank', 'allocation'])
@pytest.mark.parametrize('target', ['release', 'config', 'WAITING', 'catalogue'])
def test_real_entry_rechecks_immutable_files_after_costly_IO(c, monkeypatch, during, target):
    controller, guard, r, observed = runner(c, monkeypatch)
    paths = {'release': Path(r['_release_path']), 'config': guard.CONFIG,
             'WAITING': Path(r['_waiting_path']), 'catalogue': Path(r['catalogues'][0]['virtual_path'])}
    fired = []
    def mutate():
        if not fired:
            path = paths[target]
            path.write_bytes(path.read_bytes() + b'\n')
            fired.append(target)
    if during == 'bank':
        original = guard.verify_existing_bank
        def bank(config):
            result = original(config)
            mutate()
            return result
        monkeypatch.setattr(guard, 'verify_existing_bank', bank)
    else:
        original = guard.allocation
        def allocation(**kwargs):
            result = original(**kwargs)
            mutate()
            return result
        monkeypatch.setattr(guard, 'allocation', allocation)
    error = execute(c, controller, r, observed)
    assert fired == [target], 'the race must occur inside the costly boundary'
    assert observed['Popen'] == [], 'R198-A: immutable mutation during costly I/O reached original CLI'
    assert not (Path(c['evidence_root']) / 'CONSUMED-full_score.json').exists(), 'R198-A: race must reject before consume'
    assert error is not None


@pytest.mark.parametrize('bound', ['allocation', 'context'])
def test_real_entry_slow_consume_cannot_drop_below_reviewed_floor(c, monkeypatch, bound):
    controller, guard, r, observed = runner(c, monkeypatch,
        context_end=1800 if bound == 'context' else 2000,
        allocation_ends=(1800 if bound == 'allocation' else 2000,), consumed_at=1250)
    error = execute(c, controller, r, observed)
    assert observed['Popen'] == [], 'R198-B: positive remaining below minimum_entry reached original CLI'
    assert (Path(c['evidence_root']) / 'CONSUMED-full_score.json').exists(), 'failed consumed permission remains spent'
    assert observed['clock']['now'] < r['expires_at'], 'must fail the floor, not the finite lease'
    assert 0 < min(1800, r.get('_entry_work_deadline', 1800)) - observed['clock']['now'] < c['resources']['minimum_entry_seconds']
    assert error is not None


@pytest.mark.parametrize('end,want_timeout', [(2000, 750), (1850, 600)])
def test_real_entry_positive_and_exact_floor_survive_slow_consume(c, monkeypatch, end, want_timeout):
    controller, guard, r, observed = runner(c, monkeypatch, allocation_ends=(end,), consumed_at=1250)
    error = execute(c, controller, r, observed)
    assert error is None
    assert len(observed['Popen']) == 1
    assert observed['wait_timeouts'] == [want_timeout]
    assert (Path(c['evidence_root']) / 'CONSUMED-full_score.json').exists()


def test_real_entry_reobserves_shortened_allocation_after_consume(c, monkeypatch):
    controller, guard, r, observed = runner(c, monkeypatch, allocation_ends=(2000, 1800), consumed_at=1250)
    error = execute(c, controller, r, observed)
    assert observed['Popen'] == [], 'R198-B: final actual allocation shortening was ignored'
    assert len(observed['allocations']) >= 2
    assert (Path(c['evidence_root']) / 'CONSUMED-full_score.json').exists()
    assert error is not None


def test_real_entry_allowed_shortening_sets_exact_Popen_timeout(c, monkeypatch):
    controller, guard, r, observed = runner(c, monkeypatch, allocation_ends=(2000, 1900), consumed_at=1250)
    error = execute(c, controller, r, observed)
    assert error is None
    assert len(observed['Popen']) == 1
    assert observed['wait_timeouts'] == [650], 'R198-B: child timeout must use fresh post-consume allocation'
    assert len(observed['allocations']) >= 2
