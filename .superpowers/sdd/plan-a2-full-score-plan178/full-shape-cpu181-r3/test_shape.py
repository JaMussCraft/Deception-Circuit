import unittest
from shape import distribution, add_exposure
class Tests(unittest.TestCase):
 def test_distribution_parent_padding(self):
  d=distribution([(3,5),(5,5),(2,8)])
  self.assertEqual((d['n'],d['unpadded_tokens'],d['padded_tokens'],d['padded_squared_tokens']),(3,10,18,114))
  self.assertEqual(d['parent_widths'],{'5':2,'8':1})
 def test_work_exposure_weighted(self):
  d={};add_exposure(d,'x',5,3);add_exposure(d,'x',8,1)
  self.assertEqual(d['x'],{'forwards':4,'padded_tokens':23,'padded_squared_tokens':139})
if __name__=='__main__':unittest.main()
