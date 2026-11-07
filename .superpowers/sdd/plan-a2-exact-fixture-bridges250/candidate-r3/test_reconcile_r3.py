import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('probe_r3', str(Path(__file__).with_name('runtime-probe.py')))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

def entry(path):
    raw = path.read_bytes()
    return {'kind': 'file', 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def prefix(exe, argv, marker, body):
    return ('execve(' + json.dumps(str(exe)) + ', ' + json.dumps(argv) + ', 0x1 /* 1 vars */) = 0\n'
            + body + 'openat(AT_FDCWD, ' + json.dumps(str(marker))
            + ', O_RDONLY) = -1 ENOENT (No such file or directory)\n')

def test_authenticated_control_read_and_wrong_control_reject(tmp_path):
    exe = tmp_path/'python'; exe.write_bytes(b'exe')
    control = tmp_path/'closure.json'; control.write_bytes(b'{"entries":{}}')
    other = tmp_path/'other'; other.write_bytes(b'other')
    marker = tmp_path/'barrier'; digest = hashlib.sha256(control.read_bytes()).hexdigest()
    argv = [str(exe), '--closure', str(control), '--closure-sha256', digest]
    body = 'openat(AT_FDCWD, '+json.dumps(str(control))+', O_RDONLY) = 3<'+str(control)+'>\n'
    raw = prefix(exe, argv, marker, body)
    digest = hashlib.sha256(control.read_bytes()).hexdigest()
    entries = {str(exe): entry(exe)}
    assert str(control) in probe.check_startup_trace(raw, argv, str(marker), entries, str(tmp_path), (str(control), digest))
    with pytest.raises(probe.Rejected):
        probe.check_startup_trace(raw, argv, str(marker), entries, str(tmp_path), (str(control), '0'*64))
    with pytest.raises(probe.Rejected):
        probe.check_startup_trace(raw, argv, str(marker), entries, str(tmp_path), (str(other), digest))
    extra = body + 'openat(AT_FDCWD, '+json.dumps(str(other))+', O_RDONLY) = 4<'+str(other)+'>\n'
    with pytest.raises(probe.Rejected):
        probe.check_startup_trace(prefix(exe, argv, marker, extra), argv, str(marker), entries, str(tmp_path), (str(control), digest))
    control.write_bytes(b'changed')
    with pytest.raises(probe.Rejected):
        probe.check_startup_trace(raw, argv, str(marker), entries, str(tmp_path), (str(control), digest))

def test_readlinkat_uses_annotated_dirfd_and_fails_closed(tmp_path):
    exe = tmp_path/'python'; exe.write_bytes(b'exe')
    cwd = tmp_path/'cwd'; cwd.mkdir()
    actual = tmp_path/'actual'; actual.mkdir()
    (cwd/'alias').symlink_to('target'); (actual/'alias').symlink_to('target')
    marker = tmp_path/'barrier'; argv = [str(exe)]
    body = 'readlinkat(3<'+str(actual)+'>, "alias", "target", 4096) = 6\n'
    raw = prefix(exe, argv, marker, body)
    entries = {str(exe):entry(exe), str(cwd/'alias'):{'kind':'symlink','target':'target'}}
    with pytest.raises(probe.Rejected, match='unlisted startup read'):
        probe.check_startup_trace(raw, argv, str(marker), entries, str(cwd))
    entries[str(actual/'alias')] = {'kind':'symlink','target':'target'}
    assert str(actual/'alias') in probe.check_startup_trace(raw, argv, str(marker), entries, str(cwd))
    entries[str(actual/'alias')]['target'] = 'wrong'
    with pytest.raises(probe.Rejected, match='symlink changed'):
        probe.check_startup_trace(raw, argv, str(marker), entries, str(cwd))
    with pytest.raises(probe.Rejected, match='unresolved startup dirfd'):
        probe.check_startup_trace(raw.replace('3<'+str(actual)+'>', '3'), argv, str(marker), entries, str(cwd))
