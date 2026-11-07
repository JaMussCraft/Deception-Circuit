#!/usr/bin/env python3
"""A2 fixture-only compatibility gate; never an allocation/admission receipt.

Root supplies a hash-bound closure after staging. No discovery result is silently
promoted to an approved binding. Run once per interpreter inside the pinned SIF,
with all inputs mounted read-only and a fresh writable output parent. The outer
caller must also bound container startup to the accepted 30-second gate.
"""
import argparse
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import signal
import site
import subprocess
import sys
import sysconfig
import time

W = '/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder'
S = W + '/.superpowers/sdd'
PACKET = S + '/plan-plan-a2-full-score-operational186/task2/green-r4'
BASELINE = S + '/plan-plan-a2-full-score-operational186/task2/green/root-dispatch/candidate-before-interface-review'
CANDIDATE = S + '/plan-a2-full-score-operational186/candidate'
PINS = 'ddee7e6df8220e06212c56b4bf79e6e5fa659fb2cfd9e4ead1131c164d5456b4'
IMAGE_SHA = 'f50c8e39dd5e2ac1c1a4bdfd443351cb970513fdb10a572725eb53d7396f8697'
INVENTORY = S + '/plan-a2-exact-base-inventory251/manifest.json'
INVENTORY_SHA = 'd15679ce4f535fac8f8ec737cd9c52980ff05ce87d4cc0bd93f285d01f9ecbb1'
CONTRACT_SHA = '3ac16a5b9bc943099ad1c87b7902725971c15a6ac06e84ca7a1c1e27e1d43549'
FORBIDDEN = {'torch','numpy','scipy','pandas','transformers','datasets','nnsight','mxeval','cupy','jax','tensorflow'}
BASE = dict(executable='/sw/external/python/anaconda3/bin/python3.9',
    executable_sha256='17738a15aa1bdf58022a869a8d23ef2dc6d8097a3a7f34f31fd814109ce2ad42',
    executable_bytes=16269152,version=[3,9,18],prefix='/sw/external/python/anaconda3',
    source_build_string='3.9.18 (main, Sep 11 2023, 13:41:44) \n[GCC 11.2.0]',SOABI='cpython-39-x86_64-linux-gnu',
    distributions={'pytest':'8.3.3','exceptiongroup':'1.3.1','iniconfig':'2.1.0','packaging':'25.0',
                   'pluggy':'1.6.0','tomli':'2.3.0','typing_extensions':'4.14.0'},
    origins={n:'/u/swong2/.local/lib/python3.9/site-packages/'+p for n,p in
        [('pytest','pytest/__init__.py'),('_pytest','_pytest/__init__.py'),
         ('exceptiongroup','exceptiongroup/__init__.py'),('iniconfig','iniconfig/__init__.py'),
         ('packaging','packaging/__init__.py'),('pluggy','pluggy/__init__.py'),
         ('tomli','tomli/__init__.py'),('typing_extensions','typing_extensions.py')]})

class Rejected(RuntimeError):
    pass

def require(condition, message):
    if not condition:
        raise Rejected(message)

def sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()

def load_bound(path, digest):
    raw=Path(path).read_bytes()
    require(sha_bytes(raw)==digest, 'hash mismatch: '+str(path))
    return json.loads(raw)

def file_digest(path):
    digest=hashlib.sha256();length=0
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):
            length+=len(chunk);digest.update(chunk)
    return length,digest.hexdigest()

def check_metadata(environment, seen, entries):
    if environment=='base':
        wanted={name:'/u/swong2/.local/lib/python3.9/site-packages/'+name+'-'+version+'.dist-info'
                for name,version in BASE['distributions'].items()}
        require(seen==wanted,'distribution metadata origin mismatch')
    for path in seen.values():
        require(path+'/METADATA' in entries,'unclosed distribution METADATA')
        require(path+'/RECORD' in entries,'unclosed distribution RECORD')

def write_fresh(path, value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write('\n')

def check_identity(environment, seen, expected):
    require(isinstance(expected,dict) and bool(expected), 'unbound identity')
    if environment=='base':
        require(expected==BASE, 'base binding differs from accepted exact contract')
    else:
        require(expected.get('executable')=='/u/swong2/.conda/envs/mgnp/bin/python', 'mgnp executable')
        require(expected.get('prefix')=='/u/swong2/.conda/envs/mgnp', 'mgnp prefix')
        require(expected.get('version')==[3,12,13], 'mgnp version')
        require(expected.get('distributions',{}).get('pytest')=='9.1.1', 'mgnp pytest')
        for key in ('executable_sha256','executable_bytes','source_build_string','SOABI','origins'):
            require(bool(expected.get(key)), 'unbound mgnp '+key)
    require(seen==expected, 'runtime identity/origin/build mismatch')

def check_inventory(proposed, entries):
    for original in proposed:
        name=original['path']
        require(name in entries,'proposed source bytes/alias omitted: '+name)
        entry=entries[name]
        require(entry['kind']==original['type'],'proposed entry kind changed: '+name)
        if entry['kind']=='symlink':
            require(entry['target']==original['target'],'proposed literal alias changed: '+name)
        else:
            require(entry['bytes']==original['bytes'] and entry['sha256']==original['sha256'],'proposed source bytes changed: '+name)

def check_entries(entries, readonly=True):
    require(isinstance(entries,dict) and bool(entries),'empty entries')
    for name,entry in entries.items():
        path=Path(name)
        require(path.is_absolute() and os.path.normpath(name)==name,'nonliteral closure path')
        require(entry.get('physical_path','').startswith('/') and bool(entry.get('role')), 'unbound path/role')
        # Parent aliases also matter, even when the leaf is a regular file.
        for parent in path.parents:
            if parent.is_symlink():
                require(str(parent) in entries, 'unlisted ancestor symlink: '+str(parent))
        require(os.path.lexists(name),'missing entry: '+name)
        if entry['kind']=='symlink':
            require(path.is_symlink() and os.readlink(name)==entry['target'], 'literal link changed: '+name)
            target=os.path.normpath(os.path.join(str(path.parent),entry['target']))
            require(target in entries, 'unclosed recursive symlink: '+target)
            require(path.exists(), 'dangling or cyclic symlink: '+name)
        else:
            require(entry['kind']=='file' and path.is_file() and not path.is_symlink(), 'not regular file: '+name)
            length,digest=file_digest(path)
            require(length==entry['bytes'] and digest==entry['sha256'], 'entry bytes changed: '+name)
        if readonly:
            require(bool(os.statvfs(name).f_flag & os.ST_RDONLY), 'input not mounted read-only: '+name)

def check_observed(entries, reads, modules):
    for name in reads:
        require(name in entries,'unlisted read/provider: '+name)
    for module in modules:
        require(module['name'].split('.')[0] not in FORBIDDEN, 'scientific import: '+module['name'])
        origin=module['origin']
        if origin not in (None,'built-in','frozen'):
            require(origin in entries,'unlisted imported origin: '+str(origin))

def check_startup(environment, seen, expected):
    require(isinstance(expected,dict) and bool(expected),'unbound startup')
    require(expected.get('user_site') is True, 'user site disabled')
    require(expected.get('sitecustomize') is None and expected.get('usercustomize') is None,'unexpected customization')
    if environment=='base':
        require('_distutils_hack.DistutilsMetaFinder' in expected.get('meta_path',[]), 'distutils finder omitted')
        require('_distutils_hack' in expected.get('preloaded',[]),'distutils preload omitted')
        require('/sw/external/python/anaconda3/lib/python3.9/site-packages/distutils-precedence.pth'
                in expected.get('pth',[]),'required pth omitted')
    require(seen==expected,'startup sys.path/meta_path/pth/preload mismatch')

def check_collection(phase, names, expected):
    count=22 if phase=='red' else 226
    require(len(names)==count and len(set(names))==count,'wrong collection count or duplicates')
    require(names==expected,'collection names/order differ')

def parse_readelf(raw):
    def brackets(tag):
        return re.findall(r'\('+tag+r'\)[^\n]*\[([^\]]*)\]',raw)
    interp=re.findall(r'Requesting program interpreter: ([^\]]+)\]',raw)
    undefined=[];exports=[]
    for line in raw.splitlines():
        fields=line.split()
        if len(fields)<8 or not re.match(r'^\d+:$',fields[0]):
            continue
        if fields[4] not in ('GLOBAL','WEAK','GNU_UNIQUE'):
            continue
        name=fields[7].replace('@@','@')
        if fields[6]=='UND':
            if fields[4]!='WEAK':undefined.append(name)
        else:exports.append(name)
    return dict(needed=sorted(set(brackets('NEEDED'))),interpreter=interp[0] if interp else None,
                rpath=brackets('RPATH'),runpath=brackets('RUNPATH'),
                undefined=sorted(set(undefined)),exports=sorted(set(exports)))

def parse_ldd(raw):
    result={}
    for line in raw.splitlines():
        match=re.match(r'\s*(\S+) => (.+?)(?: \(0x[0-9a-fA-F]+\))?\s*$',line)
        if match:
            result[match[1]]=None if match[2]=='not found' else match[2]
    return result

def check_resolution(expected, seen):
    require(all(path is not None for path in seen.values()),'loader has missing provider')
    for soname,path in expected.items():
        require(soname in seen and os.path.realpath(path)==os.path.realpath(seen[soname]),
                'actual loader provider differs: '+soname)

def check_startup_entries(startup, entries):
    for path in startup['pth']:
        require(path in entries,'required startup bytes unclosed: '+path)
    if '_distutils_hack' in startup['preloaded']:
        require(any(path.endswith('/_distutils_hack/__init__.py') for path in entries),'distutils transitive origin omitted')

def check_elf_graph(objects, providers, global_roots=()):
    require(bool(objects) and set(objects)==set(providers),'unbound ELF/provider graph')
    for name,obj in objects.items():
        mapping=providers[name]
        require(set(mapping)==set(obj['needed']),'unresolved DT_NEEDED: '+name)
        scope=set();todo=list(mapping.values())+list(global_roots)
        if obj['interpreter']:todo.append(obj['interpreter'])
        while todo:
            path=todo.pop()
            require(path in objects,'missing recursive ELF provider: '+path)
            if path in scope:continue
            scope.add(path)
            todo.extend(providers[path].values())
            if objects[path]['interpreter']:todo.append(objects[path]['interpreter'])
        exports=set(obj['exports'])
        for path in scope:exports.update(objects[path]['exports'])
        # Unversioned references can bind a provider's default symbol version.
        exports.update(symbol.split('@')[0] for symbol in list(exports))
        require(set(obj['undefined'])<=exports,'unsatisfied actual undefined symbols: '+name+' '+str(sorted(set(obj['undefined'])-exports)))

def check_bindings(closure, environment, pins):
    require(closure.get('schema')=='A2_FIXTURE_RUNTIME_CLOSURE_V1','closure schema')
    require(closure.get('contracts_sha256')==CONTRACT_SHA,'accepted contract binding')
    require(pins==PINS and closure.get('payload_pins_sha256')==PINS,'payload binding')
    require(closure.get('image_sha256')==IMAGE_SHA,'pinned SIF binding')
    require(closure.get('status')=='ROOT_BOUND_FOR_ACTUAL_SIF_PROBE','unbound closure')
    require(closure.get('scientific_environment_equivalent') is False,'scientific equivalence forbidden')
    require(isinstance(closure.get('entries'),dict) and bool(closure['entries']),'unbound entries')
    env=closure.get('environments',{}).get(environment)
    require(isinstance(env,dict),'unbound environment')
    for key in ('identity','startup','elf','providers','platform','helpers','stdlib_imports','collection_names','exclusions','readelf','ldd','distribution_metadata'):
        require(bool(env.get(key)), 'unbound '+environment+' '+key)
    for key in ('red','green'):
        require(len(env['collection_names'].get(key,[]))==(22 if key=='red' else 226),'unbound collection names')
    require(set(env['elf'])<=set(closure['entries']),'ELF outside closure')
    require(env['readelf'] in closure['entries'] and env['ldd'] in closure['entries'],'unclosed readelf/ldd executable')
    require(all(isinstance(e,dict) and e.get('reason') and e.get('evidence_path') in closure['entries']
                and e.get('absent_paths') is not None for e in env['exclusions']),'unreviewed exclusions')
    check_identity(environment,env['identity'],env['identity'])
    check_startup(environment,env['startup'],env['startup'])
    check_elf_graph(env['elf'],env['providers'],[env['identity']['executable']])
    check_startup_entries(env['startup'],closure['entries'])
    check_metadata(environment,env['distribution_metadata'],closure['entries'])
    require(closure.get('green_observer') in closure['entries'],'unbound GREEN observer')
    wanted={BASELINE+'/cpu/supervisor.py',BASELINE+'/cpu/validate-phase.py',
        CANDIDATE+'/cpu/supervisor.py',CANDIDATE+'/cpu/validate-phase.py',
        CANDIDATE+'/gpu/common.py',CANDIDATE+'/gpu/host-launch.py',CANDIDATE+'/gpu/controller.py',
        S+'/plan-plan-a2-full-score-operational186/task2/green/run_cpu_green.py',closure['green_observer']}
    require({h['path'] for h in env['helpers']}==wanted,'incomplete or excessive fixture helper set')
    require(all(not h['path'].endswith(('/gpu-probe.py','/module-probe.py')) for h in env['helpers']),'native probe must remain hash-only')
    require(any(h['name']=='common' and h.get('environment',{}).get('A2_FULL_SCORE_BOUND_CONFIG') in closure['entries']
                and h.get('environment',{}).get('A2_FULL_SCORE_BOUND_CONFIG_SHA256')==closure['entries'][h['environment']['A2_FULL_SCORE_BOUND_CONFIG']].get('sha256')
                for h in env['helpers']),'unbound tiny helper configuration')
    return env

def startup_snapshot():
    dirs=site.getsitepackages()+[site.getusersitepackages()]
    preloaded=sorted(n for n in sys.modules if n in {'_distutils_hack','mpl_toolkits','google','ruamel','sphinxcontrib','zope'})
    return dict(user_site=site.ENABLE_USER_SITE,
        sitecustomize=getattr(sys.modules.get('sitecustomize'),'__file__',None),
        usercustomize=getattr(sys.modules.get('usercustomize'),'__file__',None),
        sys_path=list(sys.path),meta_path=[type(x).__module__+'.'+type(x).__name__ for x in sys.meta_path],
        preloaded=preloaded,pth=sorted(str(p) for d in dirs for p in Path(d).glob('*.pth')))

def module_snapshot():
    return sorted([dict(name=name,origin=getattr(module,'__file__',None)) for name,module in list(sys.modules.items())],key=lambda x:x['name'])

def identity_snapshot(binding):
    from importlib import metadata
    origins={name:importlib.import_module(name).__file__ for name in binding['origins']}
    versions={name:metadata.version(name.replace('_','-')) for name in binding['distributions']}
    executable=Path(sys.executable)
    return dict(executable=sys.executable,executable_sha256=sha_bytes(executable.read_bytes()),
        executable_bytes=executable.stat().st_size,version=list(sys.version_info[:3]),
        source_build_string=sys.version,SOABI=sysconfig.get_config_var('SOABI'),prefix=sys.prefix,
        distributions=versions,origins=origins)

def maps_snapshot():
    names=set()
    for line in Path('/proc/self/maps').read_text().splitlines():
        fields=line.split(None,5)
        if len(fields)==6 and fields[5].startswith('/'):
            require(not fields[5].endswith(' (deleted)'),'deleted mapped file')
            names.add(fields[5])
    return sorted(names)

def make_auditor(entries, output, reads):
    output=str(Path(output).resolve())
    def hook(event,args):
        if event=='open':
            name,mode,flags=args
            if isinstance(name,int):return
            name=os.path.abspath(os.fsdecode(name))
            writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
            if writing:
                require(os.path.commonpath([name,output])==output,'write outside fresh output: '+name)
            elif name not in ('/proc/self/maps',):
                require(name in entries,'unlisted read: '+name)
                reads.add(name)
        elif event=='import':
            require(args[0].split('.')[0] not in FORBIDDEN,'scientific import: '+args[0])
        elif event in ('subprocess.Popen','os.system','os.fork','os.forkpty','os.posix_spawn','os.exec','os.spawn','ctypes.dlopen','socket.connect','socket.bind'):
            raise Rejected('fixture import/collection attempted forbidden operation: '+event)
    return hook

def helper_imports(helpers, entries):
    before=dict(os.environ);before_path=list(sys.path)
    allowed_helpers={h['path'] for h in helpers}
    stdlib=sysconfig.get_path('stdlib')
    try:
        for helper in helpers:
            require(helper['path'] in entries,'unclosed helper')
            require(helper['name']!='__main__','helper main prohibited')
            require(all(k.startswith('A2_') for k in helper.get('environment',{})),'helper cannot forge host fields')
            os.environ.update(helper.get('environment',{}))
            sys.path[:0]=helper.get('sys_path',[])
            spec=importlib.util.spec_from_file_location(helper['name'],helper['path'])
            module=importlib.util.module_from_spec(spec)
            sys.modules[helper['name']]=module
            previous=set(sys.modules)
            spec.loader.exec_module(module)
            for name in set(sys.modules)-previous:
                origin=getattr(sys.modules[name],'__file__',None)
                if origin:
                    pure_stdlib=origin.startswith(stdlib+'/') and '/site-packages/' not in origin and '/dist-packages/' not in origin
                    require(pure_stdlib or origin in allowed_helpers,'non-stdlib helper transitive import: '+name+' '+origin)
            check_observed(entries,[],module_snapshot())
            os.environ.clear();os.environ.update(before);sys.path[:]=before_path
    finally:
        os.environ.clear();os.environ.update(before);sys.path[:]=before_path

def worker(args, closure, env):
    phase=args.worker
    startup=startup_snapshot()
    check_startup(args.environment,startup,env['startup'])
    reads=set()
    sys.addaudithook(make_auditor(closure['entries'],args.output,reads))
    from importlib import metadata
    actual_metadata={name:str(metadata.distribution(name.replace('_','-'))._path) for name in env['identity']['distributions']}
    require(actual_metadata==env['distribution_metadata'],'actual distribution metadata origin mismatch')
    check_metadata(args.environment,actual_metadata,closure['entries'])
    identity=identity_snapshot(env['identity'])
    check_identity(args.environment,identity,env['identity'])
    for name in env['stdlib_imports']:
        require(name.split('.')[0] not in FORBIDDEN,'forbidden stdlib probe')
        importlib.import_module(name)
    helper_imports(env['helpers'],closure['entries'])
    spec=importlib.util.spec_from_file_location('fixture_original_observer',PACKET+'/run_cpu_green.py')
    observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)
    command=observer.command(sys.executable,Path(args.output),1,phase)
    command.append('--collect-only')
    os.environ['A2_CPU_UNDER_TEST']=(BASELINE if phase=='red' else CANDIDATE)+'/cpu'
    os.environ['A2_GREEN_OBSERVER']=S+'/plan-plan-a2-full-score-operational186/task2/green/run_cpu_green.py' if phase=='red' else closure['green_observer']
    import pytest
    class Collector:
        names=[]
        def pytest_collection_finish(self, session):self.names=[item.nodeid for item in session.items]
    collector=Collector()
    code=pytest.main(command[3:],plugins=[collector])
    require(code==0,'collection returned '+str(code))
    check_collection(phase,collector.names,env['collection_names'][phase])
    modules=module_snapshot();maps=maps_snapshot()
    check_observed(closure['entries'],sorted(reads)+maps,modules)
    require(set(maps)<=set(env['elf']),'unapproved mapped ELF provider')
    write_fresh(Path(args.output)/(phase+'-observation.json'),dict(startup=startup,identity=identity,
        modules=modules,reads=sorted(reads),maps=maps,collection_names=collector.names,command=command,
        distribution_metadata=actual_metadata,collection_exit_code=int(code),fixture_only=True))

def bounded(command, deadline, stdout, stderr, cwd=None):
    remaining=deadline-time.monotonic()
    require(remaining>0,'compatibility deadline exhausted')
    child=subprocess.Popen(command,stdout=stdout,stderr=stderr,cwd=cwd,start_new_session=True)
    try:
        code=child.wait(timeout=remaining)
        require(time.monotonic()<deadline,'post-reap deadline exhausted')
        return code
    finally:
        # Clean the owned group even if its leader exited before a descendant.
        try:os.killpg(child.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        child.wait()

def deadline_expired(signum, frame):
    raise Rejected('30-second compatibility gate deadline exhausted')

def main():
    started=time.monotonic();deadline=started+30
    signal.signal(signal.SIGALRM,deadline_expired)
    signal.setitimer(signal.ITIMER_REAL,30)
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--closure',required=True);ap.add_argument('--closure-sha256',required=True)
    ap.add_argument('--payload-pins',required=True);ap.add_argument('--environment',choices=['base','mgnp'],required=True)
    ap.add_argument('--output',required=True)
    ap.add_argument('--worker',choices=['red','green'],help=argparse.SUPPRESS)
    args=ap.parse_args()
    out=Path(args.output)
    if not args.worker:
        require(out.is_absolute() and not out.is_symlink(),'output must be fresh absolute directory')
        require(out.parent.is_dir() and not any(p.is_symlink() for p in [out.parent]+list(out.parent.parents)), 'symlinked output parent')
        out.mkdir(mode=0o700,exist_ok=False)
    try:
        closure=load_bound(args.closure,args.closure_sha256)
        env=check_bindings(closure,args.environment,args.payload_pins)
        if args.worker:
            worker(args,closure,env);return
        require(sys.flags.no_site==0 and sys.flags.no_user_site==0,'-S/-s forbidden')
        require(os.environ.get('PYTHONDONTWRITEBYTECODE')=='1','bytecode writes must be disabled')
        require(os.environ.get('PYTEST_DISABLE_PLUGIN_AUTOLOAD')=='1','plugin autoload must be disabled')
        require(all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')),'threads must be one')
        require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','GPU must be hidden')
        require(not any(os.environ.get(k) for k in ('LD_PRELOAD','LD_LIBRARY_PATH','PYTHONPATH','PYTHONHOME')),'unreviewed loader/python path override')
        require(sys.executable==env['identity']['executable'],'wrong probe interpreter')
        check_entries(closure['entries'])
        require(INVENTORY in closure['entries'] and closure['entries'][INVENTORY].get('sha256')==INVENTORY_SHA,'inventory source binding')
        inventory=load_bound(INVENTORY,INVENTORY_SHA)
        # Inventory is a retained-byte minimum, never an ABI acceptance receipt.
        check_inventory(inventory['entries'],closure['entries'])
        require(args.closure in closure['control_read_paths'],'closure not declared for worker reads')
        # Control manifest cannot contain its own digest: audit reads it before the
        # hook, then rely on the caller's same-buffer SHA binding above.
        require(closure['image_path'] in closure['entries'],'unclosed actual image')
        require(closure['entries'][closure['image_path']]['sha256']==IMAGE_SHA,'actual image digest')
        require(env['platform']==dict(machine=platform.machine(),system=platform.system(),release=platform.release()),'CPU/kernel platform mismatch')
        pins=load_bound(PACKET+'/pins.json',PINS)
        for name,digest in pins['files'].items():
            require(name in closure['entries'] and closure['entries'][name].get('sha256')==digest,'payload member not closed: '+name)
        baseline=json.loads(Path(BASELINE+'/manifest.json').read_text())
        require(sha_bytes(Path(BASELINE+'/manifest.json').read_bytes())=='bb3e57abfb3f5ae88f33eb843a08fa51c5991da4f713f775e8006cf62b78f37b','baseline manifest')
        for name,digest in baseline.items():
            require(closure['entries'].get(BASELINE+'/'+name,{}).get('sha256')==digest,'baseline member')
        for exclusion in env['exclusions']:
            for name in exclusion['absent_paths']:
                require(not os.path.lexists(name),'excluded path remains present: '+name)
        actual={}
        for i,name in enumerate(env['elf']):
            raw_path=out/('readelf-%03d.stdout'%i)
            with raw_path.open('xb') as stdout,(out/('readelf-%03d.stderr'%i)).open('xb') as stderr:
                code=bounded([env['readelf'],'-W','-l','-d','--dyn-syms',name],deadline,stdout,stderr)
            require(code==0,'readelf rejected '+name)
            actual[name]=parse_readelf(raw_path.read_text())
            with (out/('ldd-%03d.stdout'%i)).open('xb') as stdout,(out/('ldd-%03d.stderr'%i)).open('xb') as stderr:
                code=bounded([env['ldd'],name],deadline,stdout,stderr)
            ldd_raw=(out/('ldd-%03d.stdout'%i)).read_text()
            require(code==0 or (not actual[name]['needed'] and ('statically linked' in ldd_raw or 'statically linked' in (out/('ldd-%03d.stderr'%i)).read_text())), 'actual loader resolution failed: '+name)
            check_resolution(env['providers'][name],parse_ldd(ldd_raw))
        require(actual==env['elf'],'actual ELF interp/needed/rpath/runpath/symbol declarations differ')
        check_elf_graph(actual,env['providers'],[env['identity']['executable']])
        for phase in ('red','green'):
            argv=[sys.executable,str(Path(__file__).absolute()),'--closure',args.closure,'--closure-sha256',args.closure_sha256,
                  '--payload-pins',args.payload_pins,'--environment',args.environment,'--output',args.output,'--worker',phase]
            with (out/(phase+'.stdout')).open('xb') as stdout,(out/(phase+'.stderr')).open('xb') as stderr:
                code=bounded(argv,deadline,stdout,stderr,cwd=CANDIDATE+'/tests')
            require(code==0,'actual '+phase+' import/collection gate failed: '+str(code))
        require(time.monotonic()<deadline,'compatibility deadline exhausted')
        write_fresh(out/'RESULT.json',dict(status='FIXTURE_RUNTIME_COMPATIBILITY_ONLY',environment=args.environment,
            closure_sha256=args.closure_sha256,payload_pins_sha256=PINS,elapsed_seconds=time.monotonic()-started,
            image_sha256=IMAGE_SHA,scientific_environment_equivalent=False,allocation_or_admission=False,
            scientific_execution_authorized=False))
    except BaseException as exc:
        if not args.worker:
            write_fresh(out/'REJECTED.json',dict(status='REJECTED',reason=str(exc),exception=type(exc).__name__,
                environment=args.environment,closure_sha256=args.closure_sha256,elapsed_seconds=time.monotonic()-started,
                allocation_or_admission=False))
        raise

if __name__=='__main__':main()
