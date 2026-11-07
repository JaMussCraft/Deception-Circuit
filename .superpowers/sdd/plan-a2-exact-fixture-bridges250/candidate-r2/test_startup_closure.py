"""Real local cache/resource reads; no staged-runtime compatibility claim."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import pytest

PROBE=Path(__file__).with_name('runtime-probe.py')

@pytest.fixture
def probe():
    spec=importlib.util.spec_from_file_location('r2_probe',str(PROBE))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

@pytest.fixture
def actual_startup(tmp_path):
    """Exercise valid cache mismatch and a resource read before a late hook."""
    import py_compile
    source=tmp_path/'preloaded.py';resource=tmp_path/'startup-secret.txt'
    source.write_text('value = 2\n');initial=source.stat()
    cache=Path(py_compile.compile(str(source),doraise=True))
    source.write_text('value = 1\n')
    os.utime(str(source),ns=(initial.st_atime_ns,initial.st_mtime_ns))
    resource.write_text('tiny startup resource\n')
    marker=tmp_path/'audit-installed.marker'
    script=tmp_path/'run-fixture.py'
    script.write_text('''import importlib.util,json,os,sys
from pathlib import Path
resource=Path(sys.argv[1]);source=Path(sys.argv[2]);marker=sys.argv[3]
value=resource.read_text()
spec=importlib.util.spec_from_file_location('preloaded_fixture',str(source))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
# The late audit hook cannot recover earlier cache/resource reads.
reads=[]
sys.addaudithook(lambda event,args: reads.append(str(args[0])) if event=='open' else None)
try:os.open(marker,os.O_RDONLY)
except FileNotFoundError:pass
print(json.dumps(dict(value=module.value,source_origin=module.__file__,cache=module.__cached__,late_reads=reads)))
''')
    argv=[sys.executable,str(script),str(resource),str(source),str(marker)]
    trace=tmp_path/'trace'
    command=['/usr/bin/strace','-qq','-yy','-s','4096','-e',
             'trace=%file,%process,read,pread64,readv,preadv,preadv2,mmap','-o',str(trace)]+argv
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=5)
    assert result.returncode==0,result.stderr
    seen=json.loads(result.stdout)
    (tmp_path/'observed.json').write_text(result.stdout)
    assert seen['value']==2 and seen['source_origin']==str(source)
    assert str(cache) not in seen['late_reads'] and str(resource) not in seen['late_reads']
    lines=trace.read_text().splitlines()
    stop=next(i for i,line in enumerate(lines) if str(marker) in line and 'openat(' in line)
    raw='\n'.join(lines[:stop+1])+'\n'
    assert str(cache) in raw and str(resource) in raw
    # Pin all real files mentioned by the actual trace; each regression removes
    # only its target. This includes the real interpreter's startup inputs.
    paths=set(re.findall(r'<(/[^>]+)>',raw))
    paths.update(re.findall(r'"(/[^"\\]+)"',raw))
    entries={}
    for name in paths:
        p=Path(name)
        try:is_file=p.is_file()
        except OSError:continue
        if is_file:
            payload=p.read_bytes()
            entries[name]=dict(kind='file',physical_path=name,bytes=len(payload),
                sha256=hashlib.sha256(payload).hexdigest(),role='pure trace fixture')
    return dict(raw=raw,argv=argv,marker=str(marker),entries=entries,cache=str(cache),
        resource=str(resource),source=str(source),observed=seen)

def test_actual_undeclared_cache_executed_before_hook_rejects(probe,actual_startup):
    f=actual_startup;entries=dict(f['entries']);entries.pop(f['cache'])
    # Feature assertion occurs only after the real mismatch has reproduced.
    assert hasattr(probe,'check_startup_trace'),'missing external executed-byte gate'
    with pytest.raises(probe.Rejected,match='unlisted startup read'):
        probe.check_startup_trace(f['raw'],f['argv'],f['marker'],entries)

def test_actual_resource_read_leaves_no_module_origin_rejects(probe,actual_startup):
    f=actual_startup;entries=dict(f['entries']);entries.pop(f['resource'])
    assert hasattr(probe,'check_startup_trace'),'missing external startup resource gate'
    with pytest.raises(probe.Rejected,match='unlisted startup read'):
        probe.check_startup_trace(f['raw'],f['argv'],f['marker'],entries)

def test_actual_explicitly_pinned_consumed_cache_is_reported(probe,actual_startup):
    f=actual_startup
    assert hasattr(probe,'check_startup_trace'),'missing external executed-byte gate'
    reads=probe.check_startup_trace(f['raw'],f['argv'],f['marker'],f['entries'])
    assert f['cache'] in reads and f['resource'] in reads

def test_changed_consumed_cache_bytes_rejects(probe,actual_startup):
    f=actual_startup
    Path(f['cache']).write_bytes(b'replaced after recorded closure')
    assert hasattr(probe,'check_startup_trace'),'missing external executed-byte gate'
    with pytest.raises(probe.Rejected,match='startup bytes changed'):
        probe.check_startup_trace(f['raw'],f['argv'],f['marker'],f['entries'])

@pytest.mark.parametrize('mutation',['missing_exec','missing_barrier','unfinished','wrong_argv'])
def test_incomplete_or_other_invocation_trace_rejects(probe,actual_startup,mutation):
    f=actual_startup;raw=f['raw'];argv=f['argv']
    if mutation=='missing_exec':raw='\n'.join(raw.splitlines()[1:])+'\n'
    if mutation=='missing_barrier':raw='\n'.join(raw.splitlines()[:-1])+'\n'
    if mutation=='unfinished':raw=raw.replace('openat(', 'openat(<unfinished ...> ',1)
    if mutation=='wrong_argv':argv=argv+['different']
    assert hasattr(probe,'check_startup_trace'),'missing complete same-invocation gate'
    with pytest.raises(probe.Rejected):probe.check_startup_trace(raw,argv,f['marker'],f['entries'])

def test_startup_binding_is_mandatory(probe):
    assert hasattr(probe,'check_external_startup_binding'),'missing external-startup binding gate'
    with pytest.raises(probe.Rejected):probe.check_external_startup_binding(None)

@pytest.mark.parametrize('field',['pid','proc_start_ticks','nonce','role','closure_sha256','argv'])
def test_witness_is_bound_to_current_process(probe,field):
    assert hasattr(probe,'check_startup_witness'),'missing same-process witness gate'
    context=dict(pid=12,proc_start_ticks=34,nonce='a'*32,role='master',closure_sha256='b'*64,
                 argv=['/exact/python','/exact/probe.py'],marker='/tmp/barrier')
    witness=dict(kind='A2_EXTERNAL_STARTUP_WITNESS_V1',context=copy.deepcopy(context),
        trace_sha256=hashlib.sha256(b'raw').hexdigest(),complete_from_exec_through_marker=True,
        tracer_path='/usr/bin/strace',tracer_sha256='c'*64,trace_options=probe.STARTUP_TRACE_OPTIONS)
    witness['context'][field]='other'
    with pytest.raises(probe.Rejected):
        probe.check_startup_witness(witness,b'raw',context,dict(path='/usr/bin/strace',sha256='c'*64))

def test_missing_external_witness_fields_reject(probe):
    context=dict(pid=12,proc_start_ticks=34,nonce='a'*32,role='master',closure_sha256='b'*64,
                 argv=['/exact/python','/exact/probe.py'],marker='/tmp/barrier')
    for witness in (None,{},dict(kind='A2_EXTERNAL_STARTUP_WITNESS_V1',context=context)):
        with pytest.raises(probe.Rejected):
            probe.check_startup_witness(witness,b'',context,dict(path='/usr/bin/strace',sha256='c'*64))

def test_mutable_external_witness_mount_rejects_before_hook(probe,tmp_path):
    import argparse
    binding=dict(kind='ROOT_STRACE_STARTUP_V1',nonce='a'*32,readonly_root=str(tmp_path),
        tracer=dict(path='/usr/bin/strace',sha256='c'*64),trace_options=probe.STARTUP_TRACE_OPTIONS)
    args=argparse.Namespace(worker=None,output=str(tmp_path/'out'),closure_sha256='b'*64)
    import time
    with pytest.raises(probe.Rejected,match='not mounted read-only'):
        probe.startup_handshake(args,dict(external_startup=binding),{},time.monotonic()+1)

def test_incomplete_trace_options_reject(probe,tmp_path):
    binding=dict(kind='ROOT_STRACE_STARTUP_V1',nonce='a'*32,readonly_root=str(tmp_path),
        tracer=dict(path='/usr/bin/strace',sha256='c'*64),trace_options=['-e','trace=%file'])
    with pytest.raises(probe.Rejected):probe.check_external_startup_binding(binding)
