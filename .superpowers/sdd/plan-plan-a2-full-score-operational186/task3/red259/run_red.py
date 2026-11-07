#!/usr/bin/env python3
"""Root-run bounded CPU fixture packet; never calls scheduler, RS or transport."""
import argparse, datetime, hashlib, json, os
from pathlib import Path
import subprocess, sys, time
import xml.etree.ElementTree as ET
P=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify():
    for filename in ['packet-pins.json','original-source-pins.json']:
        for name,digest in json.loads((P/filename).read_text()).items():
            path=Path(name) if filename=='original-source-pins.json' else P/name
            if sha(path)!=digest:raise RuntimeError('source pin changed: '+str(path))
    if any((P/'absent-root').iterdir()):raise RuntimeError('RED absent baseline unexpectedly implemented')

def write(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')

def main():
    a=argparse.ArgumentParser();a.add_argument('--output',required=True);a.add_argument('--dry-run',action='store_true');args=a.parse_args()
    verify();resources=json.loads((P/'resources.json').read_text())
    tests=[str(P/'tests'/name) for name in ['test_full_score_release.py','test_full_score_cache.py','test_full_score_usage.py']]
    if args.dry_run:
        print(json.dumps(dict(packet=str(P),pins_sha256=sha(P/'packet-pins.json'),tests=tests,resources=resources,
            execution=False,wrapper_uses_absolute_packet=True)));return 0
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=False)
    write(output/'run_manifest.json',dict(kind='TASK3_RED_FIXTURE_ONLY',commit='538109e809285b6ddc45d42df8786270a65f7b12',
        source_commit='50e947bb852613e3a270082651f2bd1b7bb0c525',commit_basis='root supplied frozen worktree identity; worker did not run git',
        packet=str(P),packet_pins_sha256=sha(P/'packet-pins.json'),original_source_pins_sha256=sha(P/'original-source-pins.json'),
        Slurm_job_id=os.environ.get('SLURM_JOB_ID'),cluster='root Slurm CPU allocation',
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),resources=resources))
    rows=[]
    for interpreter in resources['interpreters']:
        label='mgnp' if '/mgnp/' in interpreter else 'base39'
        for mode in ['historical-root','absent-root']:
            verify();name=label+'-'+mode;xml=output/(name+'.xml')
            env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                A2_ROOT_UNDER_TEST=str(P/mode),A2_TASK3_ACCEPTED=str(P/'accepted'),A2_TASK3_FIXTURES=str(P/'task1'),
                A2_CPU_UNDER_TEST=str(P/'accepted/cpu'))
            # Do not inherit any actual execution config/provider paths.
            for key in list(env):
                if key.startswith('A2_FULL_SCORE_'):env.pop(key)
            argv=[interpreter,'-B','-I','-m','pytest','-c','/dev/null','--confcutdir='+str(P/'tests'),
                '-p','no:cacheprovider','--basetemp='+str(output/(name+'-tmp')),
                '--junitxml='+str(xml),'-q','--tb=short']+tests
            started=time.monotonic()
            try:
                with (output/(name+'.log')).open('x') as log:
                    done=subprocess.run(argv,cwd=str(output),env=env,stdout=log,stderr=subprocess.STDOUT,
                        timeout=resources['per_invocation_timeout_seconds'],check=False)
                root=ET.parse(str(xml)).getroot()
                suites=[root] if root.tag=='testsuite' else list(root.iter('testsuite'))
                counts={key:sum(int(s.get(key,'0')) for s in suites) for key in ['tests','failures','errors','skipped']}
                counts['passed']=counts['tests']-counts['failures']-counts['errors']-counts['skipped']
                ok=(done.returncode==1 and counts['tests']==resources['expected_cases_each'] and counts['failures']>0
                    and counts['passed']>0 and counts['errors']==counts['skipped']==0)
                rows.append(dict(name=name,argv=argv,returncode=done.returncode,counts=counts,
                    expected_RED=ok,elapsed_seconds=time.monotonic()-started,junit_sha256=sha(xml)))
            except BaseException as exc:
                rows.append(dict(name=name,expected_RED=False,error=repr(exc),elapsed_seconds=time.monotonic()-started))
            verify()
    result=dict(status='PASS' if all(r['expected_RED'] for r in rows) else 'FAIL',
                operational_admission=False,model_loaded=False,results=rows)
    write(output/'RESULT.json',result);print(json.dumps(result));return 0 if result['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
