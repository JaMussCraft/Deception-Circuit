import copy
import importlib.util
import json
from pathlib import Path
import py_compile
import sys
import tempfile

P = Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/candidate/runtime-probe.py')
spec = importlib.util.spec_from_file_location('review_probe', str(P))
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

def tool_graph():
    startup = dict(user_site=True, sitecustomize=None, usercustomize=None, sys_path=['/fixture'],
        meta_path=['_distutils_hack.DistutilsMetaFinder'], preloaded=['_distutils_hack'],
        pth=['/sw/external/python/anaconda3/lib/python3.9/site-packages/distutils-precedence.pth'])
    helpers = [dict(path=x,name='helper%d'%i) for i,x in enumerate([
        p.BASELINE+'/cpu/supervisor.py',p.BASELINE+'/cpu/validate-phase.py',
        p.CANDIDATE+'/cpu/supervisor.py',p.CANDIDATE+'/cpu/validate-phase.py',
        p.CANDIDATE+'/gpu/common.py',p.CANDIDATE+'/gpu/host-launch.py',p.CANDIDATE+'/gpu/controller.py',
        p.S+'/plan-plan-a2-full-score-operational186/task2/green/run_cpu_green.py','/fixture/new-observer.py'])]
    helpers[4].update(name='common',environment={'A2_FULL_SCORE_BOUND_CONFIG':'/fixture/config.json','A2_FULL_SCORE_BOUND_CONFIG_SHA256':'a'*64})
    metadata={n:'/u/swong2/.local/lib/python3.9/site-packages/'+n+'-'+v+'.dist-info' for n,v in p.BASE['distributions'].items()}
    entries={x:{} for x in ['/fixture/readelf','/fixture/ldd','/fixture/new-observer.py','/fixture/evidence',p.BASE['executable'],*startup['pth'],'/fixture/_distutils_hack/__init__.py']}
    entries['/fixture/config.json']={'sha256':'a'*64}
    for d in metadata.values():
        entries[d+'/METADATA']={};entries[d+'/RECORD']={}
    elf={p.BASE['executable']:dict(needed=[],interpreter=None,rpath=[],runpath=[],undefined=[],exports=[])}
    env=dict(identity=copy.deepcopy(p.BASE),startup=startup,elf=elf,providers={p.BASE['executable']:{}},platform={'fixture':True},helpers=helpers,
        stdlib_imports=['json'],collection_names={'red':[str(i) for i in range(22)],'green':[str(i) for i in range(226)]},
        exclusions=[dict(reason='fixture',evidence_path='/fixture/evidence',absent_paths=[])],readelf='/fixture/readelf',ldd='/fixture/ldd',distribution_metadata=metadata)
    closure=dict(schema='A2_FIXTURE_RUNTIME_CLOSURE_V1',contracts_sha256=p.CONTRACT_SHA,payload_pins_sha256=p.PINS,
        image_sha256=p.IMAGE_SHA,status='ROOT_BOUND_FOR_ACTUAL_SIF_PROBE',scientific_environment_equivalent=False,entries=entries,environments={'base':env},green_observer='/fixture/new-observer.py')
    p.check_bindings(closure,'base',p.PINS)
    print(json.dumps({'check':'tool_graph','accepted':True,'tools_in_elf':set([env['readelf'],env['ldd']])<=set(env['elf'])}))

def startup_bytecode():
    # Tiny pure pre-hook import models site startup / top-level probe imports.
    with tempfile.TemporaryDirectory() as d:
        root=Path(d); source=root/'preloaded.py'; output=root/'out';output.mkdir()
        source.write_text('value = 2\n')
        original_stat=source.stat()
        pyc=py_compile.compile(str(source),doraise=True)
        source.write_text('value = 1\n')
        import os
        os.utime(str(source),ns=(original_stat.st_atime_ns,original_stat.st_mtime_ns))
        length,digest=p.file_digest(source)
        entries={str(source):dict(kind='file',physical_path=str(source),bytes=length,sha256=digest,role='pure fixture source')}
        p.check_entries(entries,readonly=False)
        spec=importlib.util.spec_from_file_location('preloaded_fixture',str(source))
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        reads=set();sys.addaudithook(p.make_auditor(entries,str(output),reads))
        p.check_observed(entries,reads,[{'name':'preloaded_fixture','origin':mod.__file__}])
        print(json.dumps({'check':'startup_bytecode','accepted':True,'source_value':1,'module_value':mod.value,'cached_path':mod.__cached__,'cached_path_declared':False,'observed_reads':sorted(reads)}))
        # Do not let TemporaryDirectory cleanup enter the permanent audit hook.
        import os
        sys.stdout.flush();os._exit(0)

if sys.argv[1]=='tools':tool_graph()
elif sys.argv[1]=='startup':startup_bytecode()
