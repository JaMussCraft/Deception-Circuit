import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).parent/'source-snapshot';spec=importlib.util.spec_from_file_location('r2_tests',HERE/'test_runner.py');t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
class FinalCheck(unittest.TestCase):
 def test_missing_final_read_fails_with_partial_evidence(self):
  runtime=t.Correction279Tests().runtime();runtime._check_file_witness=lambda witness:None
  with tempfile.TemporaryDirectory() as td:
   (Path(td)/'payload.json').write_text('{"x":1}');rows=[]
   with self.assertRaisesRegex(ValueError,'final.*operation'):t.r.receiver(runtime,{'path':td},{},{},rows.append)
   self.assertEqual(len(rows),1);row=rows[0]
   self.assertEqual(row['entry']['status'],'completed');self.assertEqual(row['entry']['actual_operations']['full_payload_reads'],2)
   self.assertEqual(row['final_check']['status'],'failed');self.assertEqual(row['final_check']['actual_operations']['full_payload_reads'],0)
   self.assertEqual(row['actual_operations']['full_payload_reads'],2);self.assertEqual(row['native_observed']['full_payload_reads'],2)
   self.assertTrue(row['observer_provenance']['runtime_reader_sha256']);self.assertIn('process_after_release',row)
suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(t.Correction279Tests),unittest.defaultTestLoader.loadTestsFromTestCase(FinalCheck)])
result=unittest.TextTestRunner(verbosity=2).run(suite);assert result.testsRun==4 and result.wasSuccessful()
