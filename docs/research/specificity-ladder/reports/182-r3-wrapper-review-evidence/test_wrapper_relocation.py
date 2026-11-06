import os,shutil,subprocess,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class WrapperRelocation(unittest.TestCase):
 def test_spooled_wrapper_uses_immutable_script(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);spool=root/'slurm-spool';spool.mkdir();wrapper=spool/'slurm-script';shutil.copyfile(P/'run.sh',wrapper)
   tools=root/'bin';tools.mkdir();capture=root/'args';interceptor=tools/'timeout'
   interceptor.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$CAPTURE"\n');interceptor.chmod(0o755)
   env=dict(os.environ,SLURM_JOB_ID='fixture',PATH=str(tools)+':'+os.environ['PATH'],CAPTURE=str(capture))
   result=subprocess.run(['bash',str(wrapper),'/tmp/proof-output','fixture-manifest'],env=env,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr)
   args=capture.read_text().splitlines()
   self.assertEqual(args,['--signal=TERM','--kill-after=15','840','/u/swong2/.conda/envs/mgnp/bin/python','-B',str(P/'shape.py'),'--output','/tmp/proof-output','--manifest-sha256','fixture-manifest'])
if __name__=='__main__':unittest.main()
