import hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
HERE=Path(__file__).parent/'source-snapshot';spec=importlib.util.spec_from_file_location('review_runner',HERE/'runner.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class Recording(unittest.TestCase):
 def runtime(self,fail=False):
  def parse(raw,temporaries):return json.loads(raw)
  def freeze(value,memo=None):return value
  def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
  def reader(target,prep,policy):
   root=Path(target['path']);name='payload.json';index=0
   raw=(root/name).read_bytes();digest=hashlib.sha256(raw).hexdigest()
   if fail:raise ValueError('synthetic failure after observed read/hash')
   value=parse(raw,[]);frozen=freeze(value)
   file_hash(root/name);file_hash(root/name)
   return frozen,{},(),root/name,{'full_payload_reads':2,'SHA_passes':2,'parse_passes':1,'freeze_passes':1,'target_writes':0},{}
  def final(witness):pass
  return types.SimpleNamespace(_prepared_json_buffer=parse,_freeze_json=freeze,common=types.SimpleNamespace(file_hash=file_hash),_read_prepared_target_object=reader,_check_file_witness=final)
 def test_trial_totals_do_not_check_entry_final_split(self):
  # Deliberate synthetic 3-entry/0-final arrangement, not a native measurement.
  with tempfile.TemporaryDirectory() as td:
   (Path(td)/'payload.json').write_text('{"x":1}');records=[]
   r.receiver(self.runtime(),{'path':td},{},{},records.append)
   self.assertEqual(len(records),2)
   for row in records:
    self.assertEqual(row['status'],'completed');self.assertEqual(row['actual_operations']['full_payload_reads'],3);self.assertEqual(row['actual_operations']['SHA_passes'],3)
    self.assertEqual(row['native_observed']['full_payload_reads'],2)
    self.assertNotIn('actual_operations',row['entry']);self.assertNotIn('actual_operations',row['final_check'])
 def test_observed_failure_counters_are_omitted(self):
  with tempfile.TemporaryDirectory() as td:
   (Path(td)/'payload.json').write_text('{"x":1}');records=[]
   with self.assertRaisesRegex(ValueError,'synthetic failure'):r.receiver(self.runtime(True),{'path':td},{},{},records.append)
   self.assertEqual(records[0]['status'],'failed');self.assertNotIn('actual_operations',records[0]);self.assertNotIn('genuine_observation',records[0])
 def test_text_write_characters_are_labeled_bytes(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'unicode.txt'
   def publication():path.write_text('λ雪',encoding='utf-8')
   with r.PhaseObserver({'publication':publication}) as phases:publication()
   row=phases.rows[0]
   self.assertEqual(row['file_write_completions'],1)
   self.assertEqual(row['file_write_bytes'],2)
   self.assertEqual(path.stat().st_size,5)
if __name__=='__main__':unittest.main(verbosity=2)
