"""Small synthetic protocol checks; never imports project/native modules."""
import gc
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
import weakref

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('measurement278', P/'runner.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class PacketTests(unittest.TestCase):
    def test_unbound_dryrun_has_no_native_import(self):
        value = r.describe()
        self.assertFalse(value['native_imports'])
        self.assertIsNone(value['source_commit'])
        self.assertIsNone(value['resources'])
        self.assertEqual(value['status'], 'UNBOUND_PREPARATION_ONLY')

    def test_producer_calls_native_with_exact_objects_and_selected_none(self):
        args, design, protocol, returned = object(), {}, {}, object()
        calls = []
        def prepare(a, d, p, *, selected):
            calls.append((a, d, p, selected))
            return returned
        runtime = types.SimpleNamespace(prepare_pilot_target=prepare)
        self.assertIs(r.producer(runtime, args, design, protocol), returned)
        self.assertEqual(calls, [(args, design, protocol, None)])

    def test_receiver_retains_exact_result_through_check_and_releases_between_trials(self):
        class Graph: pass
        references = []
        witnesses = []
        events = []
        def reader(t, p, n):
            if references:
                self.assertIsNone(references[-1]())
            graph, witness = Graph(), object()
            references.append(weakref.ref(graph)); witnesses.append(witness)
            events.append(('read', t, p, n))
            return (graph, {}, (), witness, {}, {})
        def check(witness):
            self.assertIs(witness, witnesses[-1])
            self.assertIsNotNone(references[-1]())
            events.append(('final', witness))
        runtime = types.SimpleNamespace(_read_prepared_target_object=reader, _check_file_witness=check)
        records = []
        target, preparation, namespace = {}, {}, {}
        r.receiver(runtime, target, preparation, namespace, records.append,
                   observer_factory=lambda: r.NullSyntheticObserver())
        self.assertEqual([x['trial'] for x in records], ['fresh-process', 'same-process-repeat'])
        self.assertEqual(len(events), 4)
        self.assertTrue(all(ref() is None for ref in references))
        self.assertEqual(records[0]['pid'], records[1]['pid'])
        self.assertFalse(records[0]['observations_are_upper_bounds'])

    def test_actual_profile_detects_reads_hash_parse_freeze_and_extra_read(self):
        import hashlib
        def parse(raw, temporaries):
            return json.loads(raw)
        def freeze(value, memo=None): return value
        def file_hash(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        def reader(target, prep, policy):
            root=Path(target); name='payload.json'; index=0
            raw=(root/name).read_bytes()
            digest=hashlib.sha256(raw).hexdigest()
            value=parse(raw, [])
            frozen=freeze(value)
            file_hash(root/name)
            return (frozen, {}, (), root/name, {}, {})
        def final(witness): file_hash(witness)
        runtime=types.SimpleNamespace(_read_prepared_target_object=reader,
            _check_file_witness=final,_prepared_json_buffer=parse,_freeze_json=freeze,
            common=types.SimpleNamespace(file_hash=file_hash))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'payload.json'; path.write_text('{"x":1}')
            with r.Observer(runtime, path) as observation:
                result=reader(td, None, None); final(result[3])
            self.assertEqual(observation.counts, dict(full_payload_reads=3, SHA_passes=3,
                parse_passes=1, freeze_passes=1, target_writes=0, read_bytes=21))
            with r.Observer(runtime, path) as extra:
                result=reader(td, None, None); final(result[3]); path.read_bytes()
            self.assertEqual(extra.counts['full_payload_reads'],4)
            with self.assertRaises(ValueError): r.check_counts(extra.counts)

    def test_failure_is_emitted_and_reraised(self):
        records=[]
        def fail(*args): raise ValueError('synthetic failure')
        runtime=types.SimpleNamespace(_read_prepared_target_object=fail)
        with self.assertRaisesRegex(ValueError, 'synthetic failure'):
            r.receiver(runtime, {}, {}, {}, records.append,
                       observer_factory=lambda: r.NullSyntheticObserver())
        self.assertEqual(records[0]['status'],'failed')
        self.assertEqual(records[0]['trial'],'fresh-process')

if __name__ == '__main__': unittest.main()

# Added before implementation after root clarified process and import boundaries.
class LaunchBoundaryTests(unittest.TestCase):
    def test_dryrun_and_unbound_execution_cannot_import_native(self):
        import subprocess
        import sys
        probe = '''import importlib.abc, runpy, sys
class Deny(importlib.abc.MetaPathFinder):
 def find_spec(self, name, path=None, target=None):
  if name.split('.')[0] in {'component_analysis','dataset','torch','numpy'}:
   raise AssertionError('native import attempted: '+name)
sys.meta_path.insert(0,Deny())
sys.argv=[sys.argv[1]]+sys.argv[2:]
runpy.run_path(sys.argv[0],run_name='__main__')
'''
        dry=subprocess.run([sys.executable,'-B','-c',probe,str(P/'runner.py'),'--dry-run'],capture_output=True,text=True)
        self.assertEqual(dry.returncode,0,dry.stderr)
        self.assertEqual(json.loads(dry.stdout)['status'],'UNBOUND_PREPARATION_ONLY')
        unbound=subprocess.run([sys.executable,'-B','-c',probe,str(P/'runner.py'),'--phase','receiver'],capture_output=True,text=True)
        self.assertEqual(unbound.returncode,2,unbound.stderr)
        self.assertIn('unbound',unbound.stderr.lower())

    def test_fresh_process_requires_launch_marker_and_synthetic_cannot_claim_it(self):
        with self.assertRaises(ValueError): r.require_fresh_process(None)
        with self.assertRaises(ValueError): r.require_fresh_process(__import__('os').getpid())
        self.assertFalse(r.NullSyntheticObserver().genuine_observation)

class OperationalAdapterTests(unittest.TestCase):
    def test_operational_producer_enters_unchanged_native_main_and_records_failure(self):
        records=[];argv=['actual-root-native-arguments'];seen=[]
        def main(args): seen.append(args);return 0
        runtime=types.SimpleNamespace(main=main)
        self.assertEqual(r.produce_native(runtime,argv,records.append),0)
        self.assertIs(seen[0],argv)
        self.assertEqual(records[0]['status'],'completed')
        self.assertFalse(records[0]['execution_authorized'])
        def failed(args): raise ValueError('native guard rejection')
        runtime.main=failed
        with self.assertRaisesRegex(ValueError,'native guard rejection'):
            r.produce_native(runtime,argv,records.append)
        self.assertEqual(records[-1]['status'],'failed')

    def test_native_receiver_requires_launch_before_reader_and_preserves_inputs(self):
        def forbidden(*args): raise AssertionError('reader called before launch check')
        runtime=types.SimpleNamespace(_read_prepared_target_object=forbidden)
        with self.assertRaises(ValueError):
            r.receive_native(runtime,{}, {}, {},lambda row:None,launcher_pid=None)

    def test_phase_observer_records_actual_nested_calls_without_retaining_return(self):
        def build(): return object()
        def publish(): return build()
        with r.PhaseObserver({'build':build,'publish':publish}) as phases:
            publish()
        self.assertEqual([row['phase'] for row in phases.rows],['build','publish'])
        self.assertTrue(all(row['wall_seconds']>=0 and row['status']=='returned' for row in phases.rows))


class Correction279Tests(unittest.TestCase):
    def runtime(self, *, extra_entry=False, failure=None):
        import hashlib
        def parse(raw, temporaries): return json.loads(raw)
        def freeze(value, memo=None): return value
        def file_hash(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
        def reader(target, preparation, namespace):
            root=Path(target['path']); name='payload.json'; index=0
            raw=(root/name).read_bytes(); digest=hashlib.sha256(raw).hexdigest()
            if failure=='entry': raise ValueError('synthetic entry rejection after real read/hash')
            value=parse(raw,[]); frozen=freeze(value)
            file_hash(root/name)
            if extra_entry: file_hash(root/name)
            return frozen,{},(),root/name,dict(full_payload_reads=2,SHA_passes=2,parse_passes=1,freeze_passes=1,target_writes=0),{}
        def final(witness):
            if not extra_entry: file_hash(witness)
            if failure=='final': raise ValueError('synthetic final rejection after real read/hash')
        return types.SimpleNamespace(_prepared_json_buffer=parse,_freeze_json=freeze,
            common=types.SimpleNamespace(file_hash=file_hash),
            _read_prepared_target_object=reader,_check_file_witness=final)

    def test_entry_final_split_rejects_three_zero_and_preserves_two_one(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'payload.json').write_text('{"x":1}')
            records=[]
            with self.assertRaisesRegex(ValueError,'entry.*operation'):
                r.receiver(self.runtime(extra_entry=True),{'path':td},{},{},records.append)
            self.assertEqual(records[0]['entry']['actual_operations']['full_payload_reads'],3)
            self.assertEqual(records[0]['final_check']['status'],'not_started')
            self.assertEqual(records[0]['native_observed']['full_payload_reads'],2)
            records=[]
            r.receiver(self.runtime(),{'path':td},{},{},records.append)
            self.assertEqual(len(records),2)
            for row in records:
                self.assertEqual(row['entry']['status'],'completed')
                self.assertEqual(row['final_check']['status'],'completed')
                self.assertEqual(row['entry']['actual_operations'],dict(full_payload_reads=2,SHA_passes=2,parse_passes=1,freeze_passes=1,target_writes=0,read_bytes=14))
                self.assertEqual(row['final_check']['actual_operations'],dict(full_payload_reads=1,SHA_passes=1,parse_passes=0,freeze_passes=0,target_writes=0,read_bytes=7))
                self.assertEqual(row['entry']['cumulative_after'],row['final_check']['cumulative_before'])
                self.assertEqual(row['final_check']['cumulative_after'],row['actual_operations'])
                self.assertEqual(row['entry']['cumulative_before']['full_payload_reads'],0)
                self.assertTrue(row['observer_provenance']['genuine_observation'])

    def test_partial_counts_and_provenance_survive_entry_and_final_failures(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/'payload.json').write_text('{"x":1}')
            for phase,reads in [('entry',1),('final',3)]:
                with self.subTest(phase=phase):
                    records=[]
                    with self.assertRaisesRegex(ValueError,'synthetic '+phase+' rejection'):
                        r.receiver(self.runtime(failure=phase),{'path':td},{},{},records.append)
                    row=records[0]
                    self.assertIn('actual_operations',row)
                    self.assertEqual(row['actual_operations']['full_payload_reads'],reads)
                    self.assertEqual(row['actual_operations']['SHA_passes'],reads)
                    self.assertTrue(row['observer_provenance']['genuine_observation'])
                    self.assertEqual(row['observer_provenance']['observer_class'],'Observer')
                    self.assertTrue(row['observer_provenance']['runtime_reader_sha256'])
                    self.assertEqual(row['status'],'failed')
                    step=row['entry' if phase=='entry' else 'final_check']
                    self.assertEqual(step['status'],'failed')
                    self.assertEqual(step['actual_operations']['full_payload_reads'],1)
                    self.assertEqual(step['cumulative_after'],row['actual_operations'])
                    self.assertIn('wall_seconds',step)
                    if phase=='entry':
                        self.assertEqual(row['final_check']['status'],'not_started')
                        self.assertNotIn('native_observed',row)
                    else:
                        self.assertEqual(row['entry']['status'],'completed')
                        self.assertEqual(row['native_observed']['full_payload_reads'],2)

    def test_phase_writer_separates_unicode_characters_from_raw_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            text=Path(td)/'unicode.txt';binary=Path(td)/'binary.dat'
            def publication():
                text.write_text('λ雪',encoding='utf-8')
                binary.write_bytes(b'\xff\x00\x01')
            with r.PhaseObserver({'publication':publication}) as observed: publication()
            row=observed.rows[0]
            self.assertEqual(text.stat().st_size,5)
            self.assertEqual(binary.stat().st_size,3)
            self.assertEqual(row['file_write_completions'],2)
            self.assertEqual(row['file_write_bytes'],3)
            self.assertEqual(row['file_write_text_characters'],2)
            self.assertEqual(row['file_write_bytes_completions'],1)
            self.assertEqual(row['file_write_text_completions'],1)
