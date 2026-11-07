"""Review272 contracts only; pure mount-plan and clock models, no native admission."""
import importlib.util
import json
from pathlib import Path
import sys
import types
from unittest import mock
import pytest

HERE = Path(__file__).resolve().parent
CORRECT_FAMILIES = ['test_prepared_receiver_resource_identity_and_capacity',
                    'test_prepared_final_barrier_after_all_costly_work']

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def host():
    sys.path.insert(0, str(HERE/'bridges'))
    sys.path.insert(0, str(HERE))
    return load('host_review272', HERE/'bridges/host.py')


def configuration(h, good=True):
    root = h.old.VIRT/h.PACKET_REL/'jobs/job-1'
    return dict(environment='mgnp', output=str(root/('child/execution' if good else 'execution')),
                shard=0, job_id='1')


def test_legacy_output_layout_cannot_expose_host_root():
    h = host()
    with pytest.raises((AssertionError, ValueError)):
        h.command(configuration(h, good=False), 'suite', 'v1', 4000)


def test_child_bind_allows_payload_but_excludes_host_and_prior_receipts():
    h = host(); c = configuration(h)
    root, child, output = h.job_layout(c['output'], c['job_id'])
    assert output == root/'child/execution' and child == root/'child'
    argv, _ = h.command(c, 'suite', 'v1', 4000)
    binds = [argv[i+1] for i, x in enumerate(argv) if x == '--bind']
    rw = [x for x in binds if x.endswith(':rw')]
    assert len(rw) == 1 and rw[0].split(':')[1] == str(child)
    # Evaluate the actual explicit mount plan by longest containing bind target.
    # This is a pure command contract; actual container permissions remain a gate.
    def writable(path):
        candidates = [(len(Path(x.split(':')[1]).parts), x.split(':')[-1])
            for x in binds if path.is_relative_to(Path(x.split(':')[1]))]
        assert candidates
        return max(candidates)[1] == 'rw'
    assert writable(output/'payload.json')
    assert writable(child/'inner-mounts-suite.json')
    for name in ('host-before.json', 'baseline-command.json', 'baseline-terminal.json', 'host-after.json'):
        assert not writable(root/name), name


def timer(wall=0., mono=0.):
    state = types.SimpleNamespace(wall=wall, mono=mono)
    return state, types.SimpleNamespace(time=lambda: state.wall, monotonic=lambda: state.mono, sleep=lambda _: None)


def patches(s, clock, child):
    stack = __import__('contextlib').ExitStack()
    stack.enter_context(mock.patch.object(s, 'time', clock))
    spawn = stack.enter_context(mock.patch.object(s.subprocess, 'Popen', return_value=child))
    stack.enter_context(mock.patch.object(s, 'group_signal', return_value=False))
    cleanup = stack.enter_context(mock.patch.object(s, 'cleanup_group'))
    stack.enter_context(mock.patch.object(s.signal, 'signal'))
    return stack, spawn, cleanup


@pytest.mark.parametrize('wall,mono', [(100., 100.), (100., 0.), (0., 100.)])
def test_expired_original_clocks_never_spawn_or_renew(wall, mono):
    h = host(); s = h.supervisor; state, clock = timer(wall, mono)
    child = mock.Mock(pid=123, returncode=0); child.poll.return_value = 0
    stack, spawn, cleanup = patches(s, clock, child)
    with stack:
        row = s.execute(['never-real'], None, None, 90, 10000,
            lambda timeout=15: ({}, 10000), wall_deadline=90, monotonic_deadline=90)
    assert not row['normal_completion'] and row['deadline'] <= 90
    spawn.assert_not_called(); cleanup.assert_not_called()


@pytest.mark.parametrize('expired_clock', ['wall', 'mono'])
def test_final_allocation_query_cannot_spawn_after_either_bound(expired_clock):
    h = host(); s = h.supervisor; state, clock = timer()
    def allocation(timeout=15):
        setattr(state, expired_clock, 100.)
        return {}, 10000
    child = mock.Mock(pid=123, returncode=0); child.poll.return_value = 0
    stack, spawn, cleanup = patches(s, clock, child)
    with stack:
        row = s.execute(['never-real'], None, None, 90, 10000, allocation,
            wall_deadline=90, monotonic_deadline=90)
    assert not row['normal_completion'] and row['deadline'] <= 90
    spawn.assert_not_called(); cleanup.assert_not_called()


def test_original_remaining_budget_is_usable_without_renewal():
    h = host(); s = h.supervisor; state, clock = timer(10., 10.)
    child = mock.Mock(pid=123, returncode=0); child.poll.return_value = 0
    stack, spawn, cleanup = patches(s, clock, child)
    with stack:
        row = s.execute(['never-real'], None, None, 90, 10000,
            lambda timeout=15: ({}, 10000), wall_deadline=90, monotonic_deadline=90)
    assert row['normal_completion'] and row['deadline'] == 90
    spawn.assert_called_once(); cleanup.assert_not_called()


def test_late_zero_after_final_query_fails_with_one_cleanup():
    h = host(); s = h.supervisor; state, clock = timer(); calls = []
    def allocation(timeout=15):
        calls.append(timeout)
        if len(calls) > 1:
            state.wall = state.mono = 90.
        return {}, 10000
    child = mock.Mock(pid=123, returncode=0); child.poll.return_value = 0
    stack, spawn, cleanup = patches(s, clock, child)
    with stack:
        row = s.execute(['never-real'], None, None, 90, 10000, allocation,
            wall_deadline=90, monotonic_deadline=90)
    assert not row['normal_completion'] and row['exit_code'] == 0
    spawn.assert_called_once(); cleanup.assert_called_once_with(child)


def test_host_command_io_consumes_original_stage_budget(tmp_path):
    h = host(); s = h.supervisor; state, clock = timer()
    c = dict(environment='base', output=str(tmp_path/'job-1/child/execution'), shard=0, job_id='1')
    root = tmp_path/'job-1'; root.mkdir()
    original_command = h.command
    def slow_command(*args):
        result = original_command(*args)
        state.wall = state.mono = 100.
        return result
    child = mock.Mock(pid=123, returncode=0); child.poll.return_value = 0
    stack, spawn, cleanup = patches(s, clock, child)
    with stack, mock.patch.object(h, 'time', clock), mock.patch.object(h, 'check_source'), \
            mock.patch.object(h, 'allocation', return_value=({}, 10000)), mock.patch.object(h, 'command', side_effect=slow_command):
        row, end, ref = h.execute_stage(c, 'oracle', 'v1', root, 10000, 10000)
    assert not row['normal_completion'] and row['deadline'] == 90
    command = json.loads((root/'oracle-command.json').read_text())
    assert command['deadline'] == command['monotonic_deadline'] == 90
    assert ref['path'] == str(root/'oracle-terminal.json')
    spawn.assert_not_called(); cleanup.assert_not_called()


def test_repaired_families_are_independent_exact_correction265_literals():
    p = json.loads((HERE/'partition.json').read_text())
    assert p['repaired_families'] == CORRECT_FAMILIES
    for i in ('0', '1'):
        expected = sorted(p['shards'][i]['members'],
            key=lambda n: n.split('::')[1].split('[')[0] not in CORRECT_FAMILIES)
        assert p['shards'][i]['execution_order'] == expected


def test_self_consistent_but_wrong_repaired_family_is_rejected():
    a = load('aggregate_review272', HERE/'aggregate.py')
    p = json.loads((HERE/'partition.json').read_text())
    p['repaired_families'] = ['test_prepared_correct_identity_understated_observed_resources_rejects',
                              'test_prepared_final_barrier_after_all_costly_work']
    for row in p['shards'].values():
        row['execution_order'] = sorted(row['members'],
            key=lambda n: n.split('::')[1].split('[')[0] not in p['repaired_families'])
    with pytest.raises((AssertionError, ValueError)):
        a.validate_partition(p)
