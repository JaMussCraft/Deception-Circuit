"""Shared bounded supervisor; Python 3.6-compatible, no scheduler policy here."""
import ctypes
import errno
import os
import signal
import subprocess
import time

CAPS = {'baseline': 610, 'oracle': 90, 'suite': 3600}
FINAL_RESERVE = 120
CLEANUP_RESERVE = 20

def stage_bound(now, initial_end, current_end, cap):
    end = min(initial_end, current_end)
    assert now + cap + FINAL_RESERVE + CLEANUP_RESERVE < end, 'stage cap cannot fit with final and cleanup reserves'
    return min(now + cap, end - FINAL_RESERVE - CLEANUP_RESERVE)

def timely(code, finished, bound):
    return code == 0 and finished < bound

def group_signal(pgid, sig):
    try:
        os.killpg(pgid, sig)
        return True
    except OSError as ex:
        if ex.errno == errno.ESRCH:
            return False
        raise

def enable_subreaper():
    assert ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0) == 0

def cleanup_group(child):
    # One shared budget, never renewed after TERM, KILL, wait or interruption.
    started = time.monotonic(); term_end = started + 15; final_end = started + 20
    pgid = child.pid; group_signal(pgid, signal.SIGTERM); killed = False
    while True:
        child.poll()
        if child.returncode is not None:
            while True:
                try:
                    pid, _ = os.waitpid(-pgid, os.WNOHANG)
                except ChildProcessError:
                    break
                if not pid:
                    break
        if not group_signal(pgid, 0):
            child.wait(timeout=max(0, final_end - time.monotonic()))
            return
        now = time.monotonic()
        if now >= final_end:
            raise RuntimeError('process group not reaped within shared20s budget')
        if now >= term_end and not killed:
            group_signal(pgid, signal.SIGKILL); killed = True
        time.sleep(min(.05, max(0, final_end - time.monotonic())))

def execute(argv, stdout, stderr, cap, initial_end, allocation, env=None, cwd=None,
            wall_deadline=None, monotonic_deadline=None):
    # Production callers supply both bounds captured before source/command/log I/O.
    # The default starts a fresh stage here for direct pure callers with no prior
    # preparation. Neither path may renew a bound after any allocation query.
    started = time.time(); started_mono = time.monotonic()
    supplied = wall_deadline is not None or monotonic_deadline is not None
    bound = started + cap if wall_deadline is None else wall_deadline
    mono = started_mono + cap if monotonic_deadline is None else monotonic_deadline
    bound = min(bound, initial_end - FINAL_RESERVE - CLEANUP_RESERVE)
    child = None; cleaning = False
    raw = dict(argv=argv, exit_code=None, normal_completion=False, started=started,
        deadline=bound, monotonic_deadline=mono)
    def interrupt(signum, frame):
        raise RuntimeError('supervisor signal %d' % signum)
    def remaining():
        left = min(bound - time.time(), mono - time.monotonic())
        if left <= 0:
            raise TimeoutError('stage deadline expired')
        return left
    handlers = {sig: signal.signal(sig, interrupt) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        assert not supplied or (wall_deadline is not None and monotonic_deadline is not None), 'both original bounds required'
        left = remaining()
        _, current_end = allocation(timeout=min(15, left))
        if not supplied:
            # Budget feasibility is tested against the original start, not now.
            bound = min(bound, stage_bound(started, initial_end, current_end, cap))
        bound = min(bound, current_end - FINAL_RESERVE - CLEANUP_RESERVE)
        raw['deadline'] = bound
        # Final clock checks are after allocation I/O and immediately before Popen.
        remaining()
        child = subprocess.Popen(argv, stdout=stdout, stderr=stderr, env=env, cwd=cwd, start_new_session=True)
        while child.poll() is None:
            left = remaining()
            _, current_end = allocation(timeout=min(15, left))
            bound = min(bound, current_end - FINAL_RESERVE - CLEANUP_RESERVE)
            raw['deadline'] = bound
            left = remaining()
            time.sleep(min(.2, left))
        raw.update(exit_code=child.returncode, finished=time.time(), deadline=bound)
        assert not group_signal(child.pid, 0), 'live child descendants'
        left = remaining()
        _, current_end = allocation(timeout=min(15, left))
        bound = min(bound, current_end - FINAL_RESERVE - CLEANUP_RESERVE)
        raw.update(deadline=bound, finished=time.time())
        remaining()
        assert timely(child.returncode, raw['finished'], bound), 'late/nonzero child'
        raw['normal_completion'] = True
    except BaseException as ex:
        raw.update(error=repr(ex), finished=time.time(), deadline=bound,
            exit_code=None if child is None else child.poll())
        if child is not None and not cleaning:
            cleaning = True
            for sig in handlers:
                signal.signal(sig, signal.SIG_IGN)
            try:
                cleanup_group(child)
            except BaseException as cleanup_error:
                raw['cleanup_error'] = repr(cleanup_error)
    finally:
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
    return raw
