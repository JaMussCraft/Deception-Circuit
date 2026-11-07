import unittest
from unittest.mock import patch
import helper as h
from test_usage_reset import fixture

class ResetTokenTests(unittest.TestCase):
 def test_malformed_captured_reset_fails_closed(self):
  for suffix in ('.5','e9','unknown'):
   with self.subTest(suffix=suffix):
    u,status,d=fixture({})
    status=status.replace('captured reset 1000','captured reset 1000'+suffix)
    with patch.object(h.time,'time',return_value=d['now']):
     with self.assertRaises(h.Rejected):h.validate_usage(u,status,'exact')
 def test_valid_line_with_following_status_and_newline(self):
  u,status,d=fixture({})
  with patch.object(h.time,'time',return_value=d['now']):
   self.assertEqual(h.validate_usage(u,status+'\nadditional status: present\n','exact')['route'],'expired_post_reset')

if __name__=='__main__':unittest.main()
