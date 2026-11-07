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

def execute(argv, stdout, stderr, cap, initial_end, allocation, env=None, cwd=None):
    _, current_end = allocation()
    bound = stage_bound(time.time(), initial_end, current_end, cap)
    mono = time.monotonic() + max(0, bound - time.time())
    child = None; cleaning = False; raw = dict(argv=argv, exit_code=None, normal_completion=False,
        started=time.time(), deadline=bound)
    def interrupt(signum, frame):
        raise RuntimeError('supervisor signal %d' % signum)
    handlers = {sig: signal.signal(sig, interrupt) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        # Expensive command construction and source checks happen at the caller.
        _, current_end = allocation()
        bound = min(bound, stage_bound(time.time(), initial_end, current_end, cap))
        raw['deadline'] = bound
        child = subprocess.Popen(argv, stdout=stdout, stderr=stderr, env=env, cwd=cwd, start_new_session=True)
        while child.poll() is None:
            left = min(bound - time.time(), mono - time.monotonic())
            if left <= 0:
                raise TimeoutError('stage deadline')
            _, current_end = allocation(timeout=min(15, left))
            bound = min(bound, current_end - FINAL_RESERVE - CLEANUP_RESERVE)
            if time.time() >= bound or time.monotonic() >= mono:
                raise TimeoutError('shortened allocation')
            time.sleep(min(.2, left))
        raw.update(exit_code=child.returncode, finished=time.time(), deadline=bound)
        # A leader that exits with live descendants is incomplete and fails.
        assert not group_signal(child.pid, 0), 'live child descendants'
        _, current_end = allocation()
        bound = min(bound, current_end - FINAL_RESERVE - CLEANUP_RESERVE)
        raw['deadline'] = bound
        assert timely(child.returncode, time.time(), bound) and time.monotonic() < mono, 'late/nonzero child'
        raw['normal_completion'] = True
    except BaseException as ex:
        raw.update(error=repr(ex), finished=time.time(), exit_code=None if child is None else child.poll())
        if child is not None and not cleaning:
            cleaning = True
            # A signal cannot interrupt and restart the shared cleanup budget.
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
