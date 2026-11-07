import copy,unittest
import helper as h
class Contracts(unittest.TestCase):
 def setUp(self):
  self.now=1000.;self.gpu={'actual_job_id':'22','commit':h.SOURCE,'groups_file_sha256':'a'*64,'launch_packet_manifest_sha256':h.R5,'reservation_id':'r2','expected_account':'cis260382p','allowed_partitions':['GPU-shared'],'main_root':'/projects/main','canonical_ledger':'/projects/ledger','maximum_reserved_gpu_hours':1.0,'exact_requested_GPU_seconds':3600,'experiment_limits':{'A1':25,'A2':60,'A3':40},'global_limit':125}
  self.cpu={'standing_CPU_job_id':'11','packet_manifest_sha256':h.CPU3,'frozen_G3_sha256':'a'*64,'H100_packet_manifest_sha256':h.R5,'source_commit':h.SOURCE}
  self.wait={'phase':'bank','job_id':'22','source_commit':h.SOURCE,'bound_config_sha256':'b'*64,'requested_at':990.}
 def request(self,now=None):return h.construct_request(self.wait,self.cpu,self.gpu,'b'*64,'/tmp/marker','c'*64,self.now if now is None else now)
 def test_request_exact_schema(self):
  r=self.request();self.assertEqual(r['actual_future_GPU_job_id'],'22');self.assertEqual(r['root_trigger_issued_at'],1000.);self.assertEqual(r['GPU_WAITING_requested_at'],990.)
 def test_wrong_waiting_job(self):
  self.wait['job_id']='23'
  with self.assertRaises(h.Rejected):self.request()
 def test_expired_waiting(self):
  with self.assertRaises(h.Rejected):self.request(1260.)
 def test_future_waiting(self):
  with self.assertRaises(h.Rejected):self.request(989.)
 def test_request_freshness(self):
  r=self.request()
  with self.assertRaises(h.Rejected):h.check_request_fresh(r,1016.)
 def complete(self):
  return dict(status='PASS',complete=True,timely_window=True,actual_Delta_owning_guards_passed=True,stable_Delta_catalogues_before_after=True,source_commit=h.SOURCE,groups_file_sha256='a'*64,actual_future_GPU_job_id='22',actual_CPU_job_id='11',phase='bank',standing_packet_manifest_sha256=h.CPU3,H100_packet_manifest_sha256=h.R5,final_GPU_bound_config_sha256='b'*64,request_sha256='d'*64,deadline_unix=1200.,supervisor_finished_unix=1100.,model_loaded=False,GPU_admitted=False,freeze_executed=False)
 def test_complete_valid(self):
  q=self.complete();old=copy.deepcopy(q);h.validate_complete(q,self.request(),'d'*64,self.gpu,'b'*64,1120.);self.assertEqual(q,old)
 def test_complete_late(self):
  q=self.complete();q['supervisor_finished_unix']=1201.
  with self.assertRaises(h.Rejected):h.validate_complete(q,self.request(),'d'*64,self.gpu,'b'*64,1210.)
 def test_complete_wrong_identity(self):
  q=self.complete();q['actual_CPU_job_id']='12'
  with self.assertRaises(h.Rejected):h.validate_complete(q,self.request(),'d'*64,self.gpu,'b'*64,1120.)
 def test_complete_not_actual_guards(self):
  q=self.complete();q['actual_Delta_owning_guards_passed']=False
  with self.assertRaises(h.Rejected):h.validate_complete(q,self.request(),'d'*64,self.gpu,'b'*64,1120.)
 def ledgers(self):
  rows=[dict(id='r1',job_id='1',cluster='delta',account='old',partition='gpu',gpus=1,requested_minutes=60,reserved_gpu_hours=1.0,source_commit='old',output_dir='/old',manifest_hash=None,status='FAILED'),dict(id='r2',job_id='22',cluster='bridges2',account='cis260382p',partition='GPU-shared',gpus=1,requested_minutes=60,reserved_gpu_hours=1.0,source_commit=h.SOURCE,output_dir='/projects/main',manifest_hash=None,status='PENDING')]
  mapping={'ledger_path':'/projects/ledger','entries':[dict(reservation_id=r['id'],experiment='A1' if r['id']=='r1' else 'A2',original_reserved_gpu_hours=r['reserved_gpu_hours'],actual_entry=copy.deepcopy(r)) for r in rows]};return {'reservations':rows,'totals':{'reserved_gpu_hours':2.0}},mapping
 def test_all_original_charges_include_failed(self):
  ledger,mapping=self.ledgers();r=h.validate_budget(ledger,mapping,self.gpu);self.assertEqual(r['exact_requested_GPU_seconds_total'],'7200')
 def test_rounded_cap_cannot_hide_exact_excess(self):
  ledger,mapping=self.ledgers();ledger['reservations'][0].update(requested_minutes=1500.002,reserved_gpu_hours=25.0);mapping['entries'][0].update(original_reserved_gpu_hours=25.0,actual_entry=copy.deepcopy(ledger['reservations'][0]));ledger['totals']['reserved_gpu_hours']=26.0
  with self.assertRaises(h.Rejected):h.validate_budget(ledger,mapping,self.gpu)
 def test_reservation_wrong_actual_job(self):
  ledger,mapping=self.ledgers();ledger['reservations'][1]['job_id']='23'
  with self.assertRaises(h.Rejected):h.validate_budget(ledger,mapping,self.gpu)
 def test_usage_active_reset_match(self):
  u={'status':'ok','should_pause':False,'weekly':{'used_percent':93,'resets_at':123}};s='session exact\nseven-day 93% (fresh)\nsession points 9 (8 since register); cadence 16; next checkpoint 1 at +16\nfreeze: none; acked\nweekly cap exception: active (last observed); captured reset 123'
  h.validate_usage(u,s,'exact')
  with self.assertRaises(h.Rejected):h.validate_usage(u,s.replace('reset 123','reset 124'),'exact')
 def test_usage_freeze_rejects(self):
  u={'status':'ok','should_pause':False,'weekly':{'used_percent':20,'resets_at':123}}
  with self.assertRaises(h.Rejected):h.validate_usage(u,'session exact\nseven-day 20% (fresh)\nfreeze: checkpoint 1','exact')
 def test_nonempty_protected_set(self):
  with self.assertRaises(h.Rejected):h.validate_heldout({'sets':[{'id':'new'}]})
 def test_duplicate_JSON_rejects(self):
  with self.assertRaises(h.Rejected):h.decode('{"complete":true,"complete":false}')
 def test_remote_namespace_escape_rejects(self):
  with self.assertRaises(h.Rejected):h.physical({'physical_Alignment_root':'/ocean/mirror'},'/projects/beto/swong2/Alignment/../outside')
 def test_once_only_request_never_replaces(self):
  import tempfile
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'request.json';h.atomic_new(path,b'first')
   with self.assertRaises(FileExistsError):h.atomic_new(path,b'second')
   self.assertEqual(path.read_bytes(),b'first')
 def test_generated_remote_inspection_Python36(self):
  import ast
  class Capture(h.Transport):
   def remote(self,script):self.script=script;return {}
  b={'ssh_argv':['ssh','bridges2'],'rsync_ssh_argv':['ssh'],'dtn_host':'b2dtn'}
  t=Capture(b,self.gpu);t.inspect([],"/ocean/marker","/ocean/release")
  ast.parse(t.script,feature_version=(3,6))
 def test_generated_remote_atomic_Python36(self):
  import ast,tempfile
  from pathlib import Path
  class Capture(h.Transport):
   def remote(self,script):self.script=script;return {}
   def fetch_upload(self,local,remote):self.upload=(str(local),remote)
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'fake.json';path.write_text('{}')
   t=Capture({},self.gpu);t.publish(path,'/ocean/release','/ocean/marker','a'*64,2000.)
   ast.parse(t.script,feature_version=(3,6));self.assertEqual(t.upload[1],'/ocean/release.pending')
 def test_packet_member_mutation_rejected_after_first_check(self):
  import tempfile
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);member=root/'driver.py';member.write_bytes(b'accepted')
   manifest=root/'manifest.json';manifest.write_bytes(h.encoded({'driver.py':h.sha(member)}));pin=h.sha(manifest)
   h.check_manifest(manifest,pin);member.write_bytes(b'changed')
   with self.assertRaises(h.Rejected):h.check_manifest(manifest,pin)
 def usage_fixture(self,live=95,cached=94,points=10,since=9):
  u={'status':'ok','should_pause':False,'weekly':{'used_percent':live,'resets_at':123}}
  status=f'session exact\nseven-day {cached}% (fresh)\nsession points {points} ({since} since register); cadence 16; next checkpoint 1 at +16\nfreeze: none; acked\nweekly cap exception: active (last observed); captured reset 123'
  return u,status
 def test_cached_meter_lag_below_checkpoint_passes(self):
  u,s=self.usage_fixture();r=h.validate_usage(u,s,'exact');self.assertEqual(r['projected_points'],'11');self.assertEqual(r['next_checkpoint_points'],'17')
 def test_cached_lag_crosses_projected_checkpoint_rejects(self):
  u,s=self.usage_fixture(points=16,since=15)
  with self.assertRaises(h.Rejected):h.validate_usage(u,s,'exact')
 def test_live99_rejects(self):
  u,s=self.usage_fixture(live=99)
  with self.assertRaises(h.Rejected):h.validate_usage(u,s,'exact')
 def test_live_meter_rollback_rejects(self):
  u,s=self.usage_fixture(live=93)
  with self.assertRaises(h.Rejected):h.validate_usage(u,s,'exact')
 def test_lag_reset_mismatch_rejects(self):
  u,s=self.usage_fixture();u['weekly']['resets_at']=124
  with self.assertRaises(h.Rejected):h.validate_usage(u,s,'exact')
 def test_lag_exception_inactive_rejects(self):
  u,s=self.usage_fixture()
  with self.assertRaises(h.Rejected):h.validate_usage(u,s.replace('exception: active','exception: expired'),'exact')
 def test_lag_unknown_percentage_rejects(self):
  u,s=self.usage_fixture()
  with self.assertRaises(h.Rejected):h.validate_usage(u,s.replace('seven-day 94%','seven-day unknown%'),'exact')
 def test_lag_missing_checkpoint_counters_rejects(self):
  u,s=self.usage_fixture()
  with self.assertRaises(h.Rejected):h.validate_usage(u,s.replace('session points 10','unknown points 10'),'exact')
 def test_stored_cache_label_is_not_live_authority(self):
  u,s=self.usage_fixture();s=s.replace('seven-day 94% (fresh)','last reading: five-hour not applicable, seven-day 94%, Fable unknown% at 2026-11-03T17:30:49-05:00 (unknown or stale)')
  r=h.validate_usage(u,s,'exact');self.assertEqual(r['stored_freshness_label'],'unknown or stale');self.assertFalse(r['cache_label_authority']);self.assertEqual(r['cache_read_at'],'2026-11-03T17:30:49-05:00')
 def remote_fixture(self,d):
  import os,time,datetime
  from pathlib import Path
  root=Path(d);pending=root/'lease.pending';marker=root/'WAITING.json';pending.write_text('{"phase":"bank"}');marker.write_text('{}');end=time.time()+3600
  fields=dict(JobId='22',JobState='RUNNING',Account='cis260382p',QOS='gpu',Partition='GPU-shared',UserId='test('+str(os.getuid())+')',NumNodes='1',NumCPUs='4',Requeue='0',Restarts='0',TimeLimit='01:00:00',EndTime=datetime.datetime.fromtimestamp(end,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'),TRES='cpu=4,mem=64G,node=1,gres/gpu=1,gres/gpu:h100-80=1',TresPerNode='gres:gpu:h100-80:1')
  payload=dict(pending=str(pending),final=str(root/'lease.final'),sha=h.sha(pending),waiting=str(marker),waiting_sha=h.sha(marker),expiry=time.time()+100,job='22',account='cis260382p',phase='bank',initial_end_epoch=end,finish_reserve_seconds=300,score_floor_seconds=1950)
  return payload,fields
 def test_actual_remote_running_recheck_precedes_atomic_link(self):
  import tempfile
  from unittest.mock import patch
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   p,fields=self.remote_fixture(d);raw=' '.join(k+'='+v for k,v in fields.items())
   with patch('subprocess.check_output',return_value=raw) as probe:
    import contextlib,io
    with contextlib.redirect_stdout(io.StringIO()):exec(compile(h.remote_publish_program(p),'fake-remote','exec'),{})
   self.assertEqual(probe.call_args.args[0],['scontrol','show','job','22','-o']);self.assertTrue(Path(p['final']).exists());self.assertFalse(Path(p['pending']).exists())
 def test_remote_nonrunning_never_publishes(self):
  import tempfile
  from unittest.mock import patch
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   p,f=self.remote_fixture(d);f['JobState']='CANCELLED'
   with patch('subprocess.check_output',return_value=' '.join(k+'='+v for k,v in f.items())):
    with self.assertRaises(AssertionError):exec(compile(h.remote_publish_program(p),'fake-remote','exec'),{})
   self.assertFalse(Path(p['final']).exists());self.assertTrue(Path(p['pending']).exists())
 def test_remote_changed_resources_never_publishes(self):
  import tempfile
  from unittest.mock import patch
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   p,f=self.remote_fixture(d);f['NumCPUs']='8'
   with patch('subprocess.check_output',return_value=' '.join(k+'='+v for k,v in f.items())):
    with self.assertRaises(AssertionError):exec(compile(h.remote_publish_program(p),'fake-remote','exec'),{})
   self.assertFalse(Path(p['final']).exists())
 def test_remote_expired_work_deadline_never_publishes(self):
  import tempfile,time
  from unittest.mock import patch
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   p,f=self.remote_fixture(d);p['initial_end_epoch']=time.time()+299
   with patch('subprocess.check_output',return_value=' '.join(k+'='+v for k,v in f.items())):
    with self.assertRaises(AssertionError):exec(compile(h.remote_publish_program(p),'fake-remote','exec'),{})
   self.assertFalse(Path(p['final']).exists())
 def test_transport_publish_really_queries_before_fake_publication(self):
  import tempfile,contextlib,io
  from unittest.mock import patch
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   p,f=self.remote_fixture(d);source=Path(d)/'source.json';source.write_text('{"phase":"bank"}')
   class Fake(h.Transport):
    def fetch_upload(self,local,remote):
     self.upload_called=True;target=Path(remote);assert target.is_relative_to(Path(d));target.write_bytes(Path(local).read_bytes())
    def remote(self,program):
     output=io.StringIO()
     with contextlib.redirect_stdout(output):exec(compile(program,'fake-remote','exec'),{})
     return h.decode(output.getvalue())
   t=Fake({},self.gpu)
   with patch('subprocess.check_output',return_value=' '.join(k+'='+v for k,v in f.items())) as probe:
    result=t.publish(source,p['final'],p['waiting'],p['waiting_sha'],p['expiry'],p['initial_end_epoch'])
   self.assertTrue(result['published']);self.assertTrue(t.upload_called);self.assertEqual(probe.call_count,1);self.assertTrue(Path(p['final']).exists())
if __name__=='__main__':unittest.main()





