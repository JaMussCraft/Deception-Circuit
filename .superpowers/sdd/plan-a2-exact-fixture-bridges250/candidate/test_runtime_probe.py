"""Tiny pure closure tests. These do not claim staged runtime compatibility."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

PROBE = Path(__file__).with_name('runtime-probe.py')

@pytest.fixture
def probe():
    if not PROBE.exists():
        class Missing:
            def __getattr__(self, name):
                raise AssertionError('Task 1 runtime probe has not been implemented: '+name)
        return Missing()
    spec = importlib.util.spec_from_file_location('fixture_runtime_probe', str(PROBE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def tree(tmp_path):
    leaf = tmp_path / 'lib.so'
    leaf.write_bytes(b'tiny provider bytes')
    alias = tmp_path / 'libalias.so'
    alias.symlink_to('lib.so')
    entries = {
        str(leaf): dict(kind='file', physical_path=str(leaf), bytes=leaf.stat().st_size,
                        sha256=hashlib.sha256(leaf.read_bytes()).hexdigest(), role='fixture'),
        str(alias): dict(kind='symlink', physical_path=str(alias), target='lib.so', role='fixture')}
    return entries, leaf, alias

def identity():
    return dict(executable='/sw/external/python/anaconda3/bin/python3.9',
                executable_sha256='17738a15aa1bdf58022a869a8d23ef2dc6d8097a3a7f34f31fd814109ce2ad42',
                executable_bytes=16269152, version=[3,9,18],
                source_build_string='3.9.18 (main, Sep 11 2023, 13:41:44) \n[GCC 11.2.0]',
                SOABI='cpython-39-x86_64-linux-gnu', prefix='/sw/external/python/anaconda3',
                distributions={'pytest': '8.3.3', 'exceptiongroup':'1.3.1','iniconfig':'2.1.0',
                               'packaging':'25.0','pluggy':'1.6.0','tomli':'2.3.0','typing_extensions':'4.14.0'},
                origins={name: '/u/swong2/.local/lib/python3.9/site-packages/'+tail for name,tail in
                    [('pytest','pytest/__init__.py'),('_pytest','_pytest/__init__.py'),
                     ('exceptiongroup','exceptiongroup/__init__.py'),('iniconfig','iniconfig/__init__.py'),
                     ('packaging','packaging/__init__.py'),('pluggy','pluggy/__init__.py'),
                     ('tomli','tomli/__init__.py'),('typing_extensions','typing_extensions.py')]})

def test_exact_base_identity(probe):
    probe.check_identity('base', identity(), identity())

@pytest.mark.parametrize('field,value', [('executable_sha256','0'*64),('version',[3,9,13]),
    ('source_build_string','3.9.18 different build'),('SOABI','other'),('executable_bytes',1)])
def test_identity_rejects_equal_version_wrong_bytes_or_build(probe, field, value):
    seen=identity();seen[field]=value
    with pytest.raises(probe.Rejected): probe.check_identity('base',seen,identity())

def test_closure_cannot_weaken_base_pin(probe):
    seen=identity();seen['version']=[3,9,13]
    with pytest.raises(probe.Rejected): probe.check_identity('base',seen,seen)

def test_pytest_origin_rejects(probe):
    seen=identity();seen['origins']['pytest']='/tmp/pytest/__init__.py'
    with pytest.raises(probe.Rejected): probe.check_identity('base',seen,identity())

def test_file_and_literal_recursive_symlink(probe, tree):
    entries,leaf,alias=tree
    probe.check_entries(entries, readonly=False)
    leaf.unlink()
    with pytest.raises(probe.Rejected): probe.check_entries(entries, readonly=False)

def test_missing_recursive_elf_target_rejects(probe, tree):
    entries,leaf,alias=tree
    del entries[str(leaf)]
    with pytest.raises(probe.Rejected): probe.check_entries(entries, readonly=False)

def test_changed_literal_symlink_rejects(probe, tree):
    entries,leaf,alias=tree
    alias.unlink();alias.symlink_to(str(leaf))
    with pytest.raises(probe.Rejected): probe.check_entries(entries, readonly=False)

def test_changed_file_rejects(probe, tree):
    entries,leaf,alias=tree; leaf.write_bytes(b'changed')
    with pytest.raises(probe.Rejected): probe.check_entries(entries, readonly=False)

@pytest.mark.parametrize('seen', ['/tmp/unlisted-helper.py','/tmp/unlisted.so'])
def test_unlisted_helper_read_or_provider_rejects(probe, tree, seen):
    entries,leaf,alias=tree
    with pytest.raises(probe.Rejected): probe.check_observed(entries, [seen], [])

def test_observed_closed_imports(probe, tree):
    entries,leaf,alias=tree
    probe.check_observed(entries,[str(leaf)], [dict(name='helper',origin=str(leaf))])

@pytest.mark.parametrize('name',['torch','numpy','transformers','pandas','scipy'])
def test_scientific_import_always_rejects(probe, tree, name):
    entries,leaf,alias=tree
    with pytest.raises(probe.Rejected): probe.check_observed(entries,[],[dict(name=name,origin=str(leaf))])

def test_startup_preserves_distutils_behavior(probe):
    expected=dict(user_site=True,sitecustomize=None,usercustomize=None,sys_path=['/literal'],
        meta_path=['_distutils_hack.DistutilsMetaFinder'],preloaded=['_distutils_hack'],
        pth=['/sw/external/python/anaconda3/lib/python3.9/site-packages/distutils-precedence.pth'])
    probe.check_startup('base', expected, expected)
    seen=copy.deepcopy(expected);seen['meta_path']=[]
    with pytest.raises(probe.Rejected): probe.check_startup('base',seen,expected)

def test_startup_omission_cannot_be_approved_by_closure(probe):
    empty=dict(user_site=True,sitecustomize=None,usercustomize=None,sys_path=[],meta_path=[],preloaded=[],pth=[])
    with pytest.raises(probe.Rejected): probe.check_startup('base',empty,empty)

def test_no_site_shortcut_rejects(probe):
    expected=dict(user_site=False,sitecustomize=None,usercustomize=None,sys_path=[],meta_path=[],preloaded=[],pth=[])
    with pytest.raises(probe.Rejected): probe.check_startup('mgnp',expected,expected)

@pytest.mark.parametrize('count',[0,21,23])
def test_wrong_collection_rejects(probe,count):
    with pytest.raises(probe.Rejected): probe.check_collection('red',[str(n) for n in range(count)],['x']*22)

def test_collection_names_not_just_count(probe):
    names=['test_file.py::test_case[%d]'%n for n in range(22)]
    probe.check_collection('red',names,names)
    wrong=list(names);wrong[1]='other'
    with pytest.raises(probe.Rejected):probe.check_collection('red',wrong,names)

def test_unbound_template_rejects(probe):
    closure=json.loads(PROBE.with_name('closure.template.json').read_text())
    with pytest.raises(probe.Rejected):probe.check_bindings(closure,'base','ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4')

def test_elf_missing_needed_provider_rejects(probe):
    objects={'/x':dict(needed=['libc.so.6'],interpreter=None,rpath=[],runpath=[],undefined=[],exports=[])}
    with pytest.raises(probe.Rejected):probe.check_elf_graph(objects, {'/x':{}})

def test_elf_missing_versioned_symbol_rejects(probe):
    objects={'/x':dict(needed=['libc.so.6'],interpreter='/ld',rpath=[],runpath=[],undefined=['missing@GLIBC_2.99'],exports=[]),
             '/libc':dict(needed=[],interpreter=None,rpath=[],runpath=[],undefined=[],exports=['present@GLIBC_2.2.5']),
             '/ld':dict(needed=[],interpreter=None,rpath=[],runpath=[],undefined=[],exports=[])}
    with pytest.raises(probe.Rejected):probe.check_elf_graph(objects,{'/x':{'libc.so.6':'/libc'},'/libc':{},'/ld':{}})
    objects['/libc']['exports'].append('missing@GLIBC_2.99')
    probe.check_elf_graph(objects,{'/x':{'libc.so.6':'/libc'},'/libc':{},'/ld':{}})

def test_readelf_parser_uses_undefined_symbol_needs(probe):
    raw='''  INTERP 0x0 0x0\n      [Requesting program interpreter: /lib64/ld.so]\n 0x1 (NEEDED) Shared library: [libc.so.6]\n 0x1 (RUNPATH) Library runpath: [$ORIGIN/../lib]\n  1: 000 0 FUNC GLOBAL DEFAULT UND memcpy@GLIBC_2.14 (2)\n  2: 000 0 FUNC WEAK DEFAULT UND optional\n  3: 000 0 FUNC GLOBAL DEFAULT 10 provided@@V1\n'''
    parsed=probe.parse_readelf(raw)
    assert parsed['undefined']==['memcpy@GLIBC_2.14']
    assert parsed['exports']==['provided@V1']
    assert parsed['needed']==['libc.so.6']
    assert parsed['interpreter']=='/lib64/ld.so'
    assert parsed['runpath']==['$ORIGIN/../lib']

def test_loader_resolution_not_just_approved_set(probe):
    raw='''libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x0000)\nlibm.so.6 => not found\n/lib64/ld-linux-x86-64.so.2 (0x000)'''
    assert probe.parse_ldd(raw)=={'libc.so.6':'/lib/x86_64-linux-gnu/libc.so.6','libm.so.6':None}
    with pytest.raises(probe.Rejected):probe.check_resolution({'libc.so.6':'/approved/libc.so'},probe.parse_ldd(raw))

def test_open_audit_rejects_unlisted_read_and_outside_write(probe, tree, tmp_path):
    entries,leaf,alias=tree
    reads=set();hook=probe.make_auditor(entries,str(tmp_path/'out'),reads)
    hook('open',(str(leaf),'r',0));assert str(leaf) in reads
    with pytest.raises(probe.Rejected):hook('open',(str(tmp_path/'hidden-helper.py'),'r',0))
    with pytest.raises(probe.Rejected):hook('open',(str(leaf),'w',1))
    hook('open',(str(tmp_path/'out'/'trace'),'w',1))
    with pytest.raises(probe.Rejected):hook('subprocess.Popen',('scontrol',[],None,None))

def test_required_startup_files_must_be_entries(probe,tree):
    entries,leaf,alias=tree
    with pytest.raises(probe.Rejected):probe.check_startup_entries(dict(pth=['/missing.pth'],preloaded=['_distutils_hack']),entries)

def test_helper_cannot_forge_slurm_even_for_import(probe, tree):
    entries,leaf,alias=tree
    with pytest.raises(probe.Rejected):probe.helper_imports([dict(path=str(leaf),name='helper',environment={'SLURM_JOB_ID':'123'})],entries)

def test_dynamic_native_loader_is_hash_only(probe, tree, tmp_path):
    entries,leaf,alias=tree
    hook=probe.make_auditor(entries,str(tmp_path/'out'),set())
    with pytest.raises(probe.Rejected):hook('ctypes.dlopen',(str(leaf),))

def test_audit_blocks_exec_and_fork(probe, tree, tmp_path):
    entries,leaf,alias=tree
    hook=probe.make_auditor(entries,str(tmp_path/'out'),set())
    for event in ('os.exec','os.spawn','os.fork'):
        with pytest.raises(probe.Rejected):hook(event,())

def test_helper_import_requires_stdlib_transitive_origins(probe, tmp_path):
    helper=tmp_path/'helper.py';other=tmp_path/'thirdparty.py'
    helper.write_text('import thirdparty\n');other.write_text('value=1\n')
    entries={str(p):dict(kind='file',physical_path=str(p),bytes=p.stat().st_size,
        sha256=hashlib.sha256(p.read_bytes()).hexdigest(),role='helper') for p in (helper,other)}
    import sys
    entries.update({m.__file__: {} for m in list(sys.modules.values()) if getattr(m,'__file__',None)})
    try:
        with pytest.raises(probe.Rejected):
            probe.helper_imports([dict(path=str(helper),name='helper_pure',sys_path=[str(tmp_path)])],entries)
    finally:
        sys.modules.pop('helper_pure',None);sys.modules.pop('thirdparty',None)

def test_required_distribution_metadata_cannot_be_unlisted(probe):
    with pytest.raises(probe.Rejected):probe.check_metadata('base',{'pytest':'/tmp/shadow.dist-info'}, {})

def test_probe_cli_rejects_unbound_template_and_preserves_output(probe,tmp_path):
    import subprocess
    import sys
    closure=PROBE.with_name('closure.template.json')
    out=tmp_path/'fresh-output'
    cmd=[sys.executable,str(PROBE),'--closure',str(closure),'--closure-sha256',hashlib.sha256(closure.read_bytes()).hexdigest(),
        '--payload-pins','ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4',
        '--environment','base','--output',str(out)]
    result=subprocess.run(cmd,capture_output=True,timeout=5)
    assert result.returncode!=0
    raw=(out/'REJECTED.json').read_bytes()
    assert json.loads(raw)['reason']=='unbound closure'
    assert not (out/'RESULT.json').exists()
    result=subprocess.run(cmd,capture_output=True,timeout=5)
    assert result.returncode!=0 and (out/'REJECTED.json').read_bytes()==raw

def test_deadline_kills_owned_group(probe,tmp_path):
    import sys
    import time
    with (tmp_path/'stdout').open('wb') as stdout,(tmp_path/'stderr').open('wb') as stderr:
        with pytest.raises(Exception):
            probe.bounded([sys.executable,'-c','import time;time.sleep(10)'],time.monotonic()+0.05,stdout,stderr)

def test_inventory_bytes_and_aliases_cannot_be_trimmed(probe, tree):
    entries,leaf,alias=tree
    proposed=[dict(path=str(leaf),type='file',bytes=entries[str(leaf)]['bytes'],sha256=entries[str(leaf)]['sha256']),
              dict(path=str(alias),type='symlink',target='lib.so')]
    probe.check_inventory(proposed,entries)
    del entries[str(alias)]
    with pytest.raises(probe.Rejected):probe.check_inventory(proposed,entries)

def test_hard_gate_deadline_rejects(probe):
    with pytest.raises(probe.Rejected):probe.deadline_expired(None,None)
