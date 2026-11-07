import datetime
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import helper as h

MATRIX = json.loads((Path(__file__).parent / 'test-matrix.json').read_text())

def fixture(overrides):
 d=dict(MATRIX['new_branch_base']); d.update(overrides)
 def stamp(value):
  if value is None:return 'unknown'
  result=datetime.datetime.fromtimestamp(value, datetime.timezone.utc)
  if d.get('timestamp_timezone', 'aware') is None:result=result.replace(tzinfo=None)
  return result.isoformat()
 u={'status':d.get('meter_status','ok'),'should_pause':d.get('should_pause',False),'weekly':{'used_percent':d['live'],'resets_at':d['live_reset']},'checked_at':stamp(d['live_checked_at'])}
 status=('session '+('exact' if d.get('session_matches',True) else 'other')+'\n'
  f"last reading: seven-day {d['cached']}% at {stamp(d['cached_read_at'])} ({d.get('cache_label','fresh')})\n"
  f"session points {d['points']} ({d['since']} since register); cadence {d['cadence']}; next checkpoint {d['next_index']} at +{d['next_at_plus']}\n"
  f"freeze: {d['freeze']}; acked\nweekly cap exception: {d['exception']} (last observed); captured reset {d['old_reset']}")
 return u,status,d

class ResetTests(unittest.TestCase):
 def test_approved_matrix(self):
  for case in MATRIX['cases']:
   with self.subTest(case=case['name']):
    u,status,d=fixture(case['override'])
    with patch.object(h.time,'time',return_value=d['now']):
     if case['expected'].startswith('PASS'):
      result=h.validate_usage(u,status,'exact')
      self.assertEqual(result['route'],'matching_reset' if case['expected']=='PASS_EXISTING_ROUTE' else 'expired_post_reset')
     else:
      with self.assertRaises(h.Rejected):h.validate_usage(u,status,'exact')

class AdditionalTests(unittest.TestCase):
 def test_invalid_inputs_fail_closed(self):
  variants=[{'old_reset':0},{'old_reset':-1},{'live_reset':0},{'live_reset':2000.0},{'live':101},{'cached':101},{'live':float('nan')},{'live':float('inf')},{'live':-1},{'cached':-1}]
  for variant in variants:
   with self.subTest(variant=variant):
    u,status,d=fixture(variant)
    with patch.object(h.time,'time',return_value=d['now']):
     with self.assertRaises(h.Rejected):h.validate_usage(u,status,'exact')
 def test_matching_unknown_state_rejected(self):
  u,status,d=fixture({'old_reset':2000,'exception':'unknown'})
  with patch.object(h.time,'time',return_value=d['now']):
   with self.assertRaises(h.Rejected):h.validate_usage(u,status,'exact')
 def test_actual_usage_orders_read_only_calls_and_keeps_raw(self):
  u,status,d=fixture({})
  class Result:
   def __init__(self,stdout):self.stdout=stdout
  calls=[];writes=[]
  def call(argv):
   calls.append(argv)
   return Result(json.dumps(u) if len(calls)==1 else status)
  def exclusive(path,data):writes.append((path,json.loads(data)))
  with patch.object(h.time,'time',return_value=d['now']),patch.object(h,'call',side_effect=call),patch.object(h,'exclusive',side_effect=exclusive):
   h.usage({'usage_pause_percent':99,'session':'exact'},Path('/unused'),'fixture')
  self.assertEqual(calls,[['/u/swong2/.local/bin/codex-usage','--pause-at','99'],['/u/swong2/.local/bin/research-session','status','--session','exact']])
  self.assertEqual(writes[0][1]['live'],u);self.assertEqual(writes[0][1]['session_status'],status)
  self.assertTrue(writes[0][1]['projection']['below_cap_no_exception_authority'])

if __name__ == '__main__':unittest.main()
