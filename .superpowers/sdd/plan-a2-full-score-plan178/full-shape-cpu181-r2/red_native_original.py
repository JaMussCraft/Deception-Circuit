import unittest
from test_native_seams import rows,task_batches,_rows
class RedOriginal(unittest.TestCase):
 def test_original_proof_utility_donor_width(self):
  # Original 181 shape.py passed batch_size=8 to task_batches for utility donors.
  donor=task_batches(rows(),stream='corrupt',batch_size=8)
  self.assertEqual(int(next(_rows(donor[0])).input_ids.shape[1]),9)
if __name__=='__main__':unittest.main()
