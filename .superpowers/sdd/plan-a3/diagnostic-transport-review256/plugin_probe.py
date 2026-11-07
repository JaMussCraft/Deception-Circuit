"""Tiny isolated pytest protocol/durability probe; never imports project/native code."""
import hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parent
SOURCE=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a3/green-timeout-diagnosis253/diagnostic253.py')
def main():
 label,python=sys.argv[1:];root=R/('plugin-probe-'+label);root.mkdir();suite=root/'suite';suite.mkdir();plugin=root/'plugin';plugin.mkdir();assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='63568713bd1c40f143c43932a909f6faf7e831d3f217b6f311256b419c1f4bac';(plugin/'diagnostic253.py').write_bytes(SOURCE.read_bytes())
 expected=['test_mini.py::test_unselected_before','test_mini.py::test_selected_fail','test_mini.py::test_unselected_after'];(root/'collected.json').write_text(json.dumps(expected));(root/'selection.json').write_text(json.dumps([expected[1]]))
 (suite/'conftest.py').write_text('import json,os\nfrom pathlib import Path\ndef pytest_sessionstart(session):\n Path(os.environ["PROBE_ROOT"],"preflight").write_text("done")\ndef pytest_collection_finish(session):\n assert len(session.items)==3\ndef pytest_sessionfinish(session,exitstatus):\n Path(os.environ["PROBE_ROOT"],"session-final.json").write_text(json.dumps([item.nodeid for item in session.items]))\n')
 (suite/'test_mini.py').write_text('import os,time,pytest\nfrom pathlib import Path\nROOT=Path(os.environ["PROBE_ROOT"])\ndef test_unselected_before():\n raise AssertionError("unselected before executed")\n@pytest.fixture\ndef lifecycle():\n (ROOT/"setup").write_text("done")\n yield\n (ROOT/"teardown-started").write_text("done")\n deadline=time.monotonic()+5\n while not(ROOT/"parent-ack").exists() and time.monotonic()<deadline:time.sleep(.01)\n assert (ROOT/"parent-ack").exists()\n (ROOT/"teardown-done").write_text("done")\ndef test_selected_fail(lifecycle):\n assert False,"selected_failure"\ndef test_unselected_after():\n raise AssertionError("unselected after executed")\n')
 env=dict(os.environ,PYTHONPATH=str(plugin),PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PROBE_ROOT=str(root),DIAG253_COLLECTED=str(root/'collected.json'),DIAG253_SELECTION=str(root/'selection.json'),DIAG253_OUTPUT=str(root/'events'));env.pop('PYTEST_ADDOPTS',None)
 command=[python,'-B','-m','pytest','-vv','-p','no:cacheprovider','-p','diagnostic253','-o','faulthandler_timeout=0','--rootdir='+str(suite),'--confcutdir='+str(suite),'--basetemp='+str(root/'tmp'),str(suite/'test_mini.py')]
 process=subprocess.Popen(command,cwd=str(suite),env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);immediate=False
 try:
  deadline=time.monotonic()+8;events=root/'events/events.jsonl'
  while time.monotonic()<deadline and process.poll() is None:
   if events.exists():
    rows=[json.loads(v) for v in events.read_text().splitlines()]
    if any(v.get('event')=='phase-report' and v.get('when')=='call' and v.get('outcome')=='failed' for v in rows):
     immediate=True;(root/'parent-ack').write_text('observed durable failed call before process exit');break
   time.sleep(.01)
  stdout,stderr=process.communicate(timeout=10)
 finally:
  if process.poll() is None:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
 (root/'pytest.stdout').write_bytes(stdout);(root/'pytest.stderr').write_bytes(stderr);rows=[json.loads(v) for v in (root/'events/events.jsonl').read_text().splitlines()];reports=[v for v in rows if v.get('event')=='phase-report'];assert process.returncode==1 and immediate and (root/'preflight').exists() and (root/'setup').exists() and (root/'teardown-done').exists();assert [v['when'] for v in reports]==['setup','call','teardown'] and [v['outcome'] for v in reports]==['passed','failed','passed'] and 'selected_failure' in reports[1]['longrepr'];assert json.loads((root/'session-final.json').read_text())==expected and rows[0]['collected']==3 and rows[0]['acceptance'] is False and rows[-1]['acceptance'] is False
 result=dict(probe_only=True,production_suite_executed=False,collected=3,executed_selected=1,expected_pytest_exit=1,observed_pytest_exit=process.returncode,all_original_session_items_preserved=True,preflight_and_setup_call_teardown_protocol_preserved=True,failed_call_JSONL_visible_before_teardown_process_exit=immediate,periodic_traceback_disabled=True,command=command);(root/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
