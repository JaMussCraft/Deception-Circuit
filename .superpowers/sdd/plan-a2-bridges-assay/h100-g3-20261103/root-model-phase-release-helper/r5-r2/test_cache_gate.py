import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import cache_gate as c
class CacheGate(unittest.TestCase):
 def fixture(self,folder):
  root=Path(folder);hub=root/'hub';cache=hub/c.MODEL_REPO;snapshot=cache/'snapshots'/c.REVISION;(cache/'refs').mkdir(parents=True);snapshot.mkdir(parents=True);(cache/'refs/main').write_text(c.REVISION+'\n')
  metadata=[]
  for name in ['config.json','generation_config.json','model.safetensors.index.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json']:
   p=snapshot/name;p.write_text('{}');metadata.append(dict(name=name,nbytes=p.stat().st_size,sha256=c.file_sha(p)))
  blob=cache/'blobs'/('f'*64);blob.parent.mkdir();blob.write_bytes(b'small fake weights, deliberately not hashed by per-start gate')
  weight=snapshot/'model-00001-of-00001.safetensors';weight.symlink_to(blob);weights=[dict(name=weight.name,nbytes=blob.stat().st_size,expected_sha256=blob.name)]
  ref=root/'reference.json';ref.write_text(json.dumps(dict(remote_cache=str(cache),revision=c.REVISION,metadata=metadata,weights=weights)))
  proof=root/'full-proof.json';proof.write_text(json.dumps(dict(reference_sha256=c.file_sha(ref))))
  return ref,proof,hub,snapshot,weight,dict(reference_sha256=c.file_sha(ref),full_proof_sha256=c.file_sha(proof))
 def test_valid_metadata_and_weight_identity_no_weight_hash(self):
  with tempfile.TemporaryDirectory() as d:
   ref,proof,hub,snapshot,weight,pins=self.fixture(d);real=c.file_sha;seen=[]
   def observed(path):seen.append(Path(path));return real(path)
   with patch.object(c,'file_sha',side_effect=observed):r=c.check_cache(ref,proof,hub,**pins)
   self.assertEqual(len(r['metadata']),6);self.assertEqual(len(r['weights']),1);self.assertFalse(r['full_weights_rehashed']);self.assertNotIn(weight,seen);self.assertNotIn(weight.resolve(),seen)
 def test_wrong_refs_main(self):
  with tempfile.TemporaryDirectory() as d:
   ref,proof,hub,snapshot,weight,pins=self.fixture(d);(snapshot.parent.parent/'refs/main').write_text('wrong')
   with self.assertRaises(AssertionError):c.check_cache(ref,proof,hub,**pins)
 def test_metadata_same_size_different_hash(self):
  with tempfile.TemporaryDirectory() as d:
   ref,proof,hub,snapshot,weight,pins=self.fixture(d);(snapshot/'tokenizer.json').write_text('[]')
   with self.assertRaises(AssertionError):c.check_cache(ref,proof,hub,**pins)
 def test_weight_size_drift(self):
  with tempfile.TemporaryDirectory() as d:
   ref,proof,hub,snapshot,weight,pins=self.fixture(d);weight.resolve().write_bytes(b'wrong size')
   with self.assertRaises(AssertionError):c.check_cache(ref,proof,hub,**pins)
 def test_weight_blob_name_drift(self):
  with tempfile.TemporaryDirectory() as d:
   ref,proof,hub,snapshot,weight,pins=self.fixture(d);old=weight.resolve();new=old.with_name('e'*64);new.write_bytes(old.read_bytes());weight.unlink();weight.symlink_to(new)
   with self.assertRaises(AssertionError):c.check_cache(ref,proof,hub,**pins)
 def test_physical_hub_mismatch(self):
  with tempfile.TemporaryDirectory() as d:
   ref,proof,hub,snapshot,weight,pins=self.fixture(d)
   with self.assertRaises(AssertionError):c.check_cache(ref,proof,hub/'other',**pins)
 def test_original_full_proof_unchanged(self):
  with tempfile.TemporaryDirectory() as d:
   ref,proof,hub,snapshot,weight,pins=self.fixture(d);before=proof.read_bytes();c.check_cache(ref,proof,hub,**pins);self.assertEqual(proof.read_bytes(),before)
if __name__=='__main__':unittest.main()
