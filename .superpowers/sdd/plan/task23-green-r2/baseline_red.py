"""Attributable five-case RED against saved r1 runtime; no scheduler calls."""
import argparse,json,os,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--python',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();packet=Path(__file__).resolve().parent;suite=packet/'baseline-suite';output=args.output
    output.mkdir();start=time.time()
    nodes=['test_prepared_producer_descriptor_binds_complete_inventory_summary','test_prepared_completed_intake_rejects_incomplete_originally_anchored_resources']
    argv=[args.python,'-m','pytest','-q','-p','no:cacheprovider','--import-mode=importlib','--confcutdir='+str(suite),
        '--rootdir='+str(suite),'--basetemp='+str(output/'tmp'),'--junitxml='+str(output/'junit.xml')]+[str(suite/'test_a3_prepared_pilot_target.py')+'::'+name for name in nodes]
    manifest=dict(status='STARTED',argv=argv,normal_completion=False,expected_cases=5,model_loaded=False,execution_authorized=False)
    def save():(output/'run_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    save()
    try:
        env=dict(os.environ,PYTHONPATH=str(packet/'baseline-source'))
        try:result=subprocess.run(argv,cwd=str(packet),env=env,capture_output=True,text=True,timeout=180)
        except subprocess.TimeoutExpired as error:
            def decoded(value):return value.decode(errors='replace') if isinstance(value,bytes) else value or ''
            (output/'pytest.stdout').write_text(decoded(error.stdout));(output/'pytest.stderr').write_text(decoded(error.stderr))
            manifest.update(status='TIMEOUT',timeout_seconds=180);save();raise
        (output/'pytest.stdout').write_text(result.stdout);(output/'pytest.stderr').write_text(result.stderr)
        manifest.update(status='EXITED',pytest_exit_code=result.returncode,termination_signal=-result.returncode if result.returncode<0 else None);save()
        assert (output/'junit.xml').is_file(),'baseline RED missing JUnit'
        cases=ET.parse(output/'junit.xml').getroot().findall('.//testcase')
        manifest.update(observed_cases=len(cases),failures=sum(c.find('failure') is not None for c in cases),
            errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases));save()
        assert result.returncode==1 and len(cases)==5 and manifest['failures']==5 and not manifest['errors'] and not manifest['skipped'],manifest
        counts={}
        for case in cases:
            name=case.attrib['name'].split('[',1)[0];counts[name]=counts.get(name,0)+1
            message=case.find('failure').get('message','')
            assert ('AssertionError' in message if name==nodes[0] else 'DID NOT RAISE' in message),message
        assert counts=={nodes[0]:1,nodes[1]:4},counts
        manifest.update(status='CORRECTION_RED_EXPECTED',normal_completion=True,exit_code=0,per_function_case_counts=counts)
    except BaseException as error:
        manifest.update(error=repr(error),exit_code=1);raise
    finally:manifest.update(wall_seconds=time.time()-start);save()

if __name__=='__main__':main()
