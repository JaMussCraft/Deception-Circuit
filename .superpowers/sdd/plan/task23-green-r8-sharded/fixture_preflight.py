"""Staged original-validator fixture preflight; diagnostics, never admission."""
import contextlib
import functools
import hashlib
import platform
import json
import os
from pathlib import Path
import time


class StageRecorder:
    """Persist only scalar observations; never retain input arguments/graphs."""
    def __init__(self, output, observe):
        self.output = Path(output); self.output.mkdir()
        self.observe = observe; self.stack = []; self.depth = {}; self.sequence = 0
        self.start = time.perf_counter()
        self.manifest = dict(kind='a3_injected_integration_fixture_preflight_v2', injected=True,
            model_loaded=False, execution_authorized=False, operational_admission=False,
            normal_completion=False, status='STARTED', results={}, active_case=None,
            active_stage=None, event_log=str(self.output / 'stages.jsonl'),
            observation_scope='actual current/lifetime process values and whole cgroup values; no subtraction or upper-bound claim')
        self.save()

    def save(self):
        temporary = self.output / '.run_manifest.json.tmp'
        with temporary.open('w') as stream:
            json.dump(self.manifest, stream, indent=2, sort_keys=True); stream.write('\n')
            stream.flush(); os.fsync(stream.fileno())
        temporary.replace(self.output / 'run_manifest.json')

    def mark(self, stage, event, error_type=None):
        self.sequence += 1
        row = dict(sequence=self.sequence, active_case=self.manifest['active_case'], stage=stage,
            event=event, active_stack=list(self.stack), wall_seconds=time.perf_counter()-self.start,
            unix_seconds=time.time(), observations=self.observe())
        if error_type is not None: row['error_type'] = error_type
        with (self.output / 'stages.jsonl').open('a') as stream:
            stream.write(json.dumps(row, sort_keys=True) + '\n'); stream.flush(); os.fsync(stream.fileno())
        self.manifest.update(active_stage=' > '.join(self.stack) if self.stack else None,
            last_event=row, event_count=self.sequence)
        self.save()

    @contextlib.contextmanager
    def phase(self, name):
        self.stack.append(name); self.mark(name, 'enter')
        try:
            yield
        except BaseException as error:
            self.stack.pop(); self.mark(name, 'error', type(error).__name__); raise
        else:
            self.stack.pop(); self.mark(name, 'exit')

    def watch(self, original, label, detail=None, predicate=None):
        @functools.wraps(original)
        def wrapped(*args, **kwargs):
            if self.depth.get(label, 0) or (predicate is not None and not predicate(*args, **kwargs)):
                return original(*args, **kwargs)
            self.depth[label] = self.depth.get(label, 0) + 1
            name = label if detail is None else label + ':' + detail(*args, **kwargs)
            try:
                with self.phase(name): return original(*args, **kwargs)
            finally: self.depth[label] -= 1
        return wrapped


def _large_read(path):
    try: return (Path(path) / 'payload.json').stat().st_size >= 1024*1024
    except (OSError, TypeError): return False


def run(output):
    import pytest
    import sys
    from tests.a3_prepared_integration_cases import PreparedCase, runtime
    from component_analysis import a3_pipeline
    candidate = Path(__file__).resolve().parents[2] / 'plan-a3/direction-preallocation-candidate287'
    assert Path(sys.modules[PreparedCase.__module__].__file__).resolve() == (candidate / 'tests/a3_prepared_integration_cases.py').resolve()
    r = runtime(); recorder = StageRecorder(output, r._prepared_process_observation)
    manifest = recorder.manifest
    pins_path = Path(__file__).resolve().parent / 'source-pins.json'
    pins_hash = hashlib.sha256(pins_path.read_bytes()).hexdigest()
    source_before = r.artifacts.code_hashes()
    manifest.update(commit='538109e809285b6ddc45d42df8786270a65f7b12',
        source_commit_role='accepted baseline; exact test/instrumentation revision identified by source pins',
        source_pins_reference=dict(path=str(pins_path), sha256=pins_hash), source_before=source_before,
        environment=dict(python=platform.python_version(), torch=str(r.torch.__version__), numpy=r.np.__version__),
        process=dict(pid=os.getpid(), job_id=os.environ.get('SLURM_JOB_ID'),
            cluster=os.environ.get('SLURM_CLUSTER_NAME'), requested_cpus=os.environ.get('SLURM_CPUS_PER_TASK'),
            requested_memory_MB=os.environ.get('SLURM_MEM_PER_NODE')),
        resource_role='diagnostic planning headroom, never receiver bounds or execution admission')
    recorder.save()
    try:
        for part in ('prefit', 'selected'):
            manifest['active_case'] = part; recorder.save(); started = time.perf_counter()
            symbols = [
                (PreparedCase, '_complete_selected_backing'), (PreparedCase, '_bind_original_authority'),
                (r.workload, '_validate_inventory'), (r.workload, 'build_inventory'), (r, 'read_object'),
                (r, 'live_guard'), (r, 'make_authority_context'), (r, 'validate_reservation'),
                (r._AuthorityContext, '__init__'), (r, '_retained_json_bytes'), (r, '_freeze_json'),
                (r, '_make_file_witness'), (r, '_check_file_witness'), (r.ladder, 'load_model'),
                (a3_pipeline, 'load_a1_parents'), (a3_pipeline, '_validate_parent_files'),
                (a3_pipeline, 'validate_assessment_membership')]
            originals = [(obj, name, getattr(obj, name)) for obj, name in symbols]
            with pytest.MonkeyPatch.context() as patch:
                # Original call arguments/results are forwarded without modification.
                for obj, name, label in [
                    (PreparedCase, '_complete_selected_backing', 'selected_backing'),
                    (PreparedCase, '_bind_original_authority', 'bind_original_authority'),
                    (r.workload, '_validate_inventory', 'validate_inventory'),
                    (r, 'live_guard', 'live_guard'), (r, 'make_authority_context', 'make_authority_context'),
                    (r, 'validate_reservation', 'validate_reservation'),
                    (r._AuthorityContext, '__init__', 'authority_context_init'),
                    (r, '_retained_json_bytes', 'retained_graph_walk'),
                    (r, '_freeze_json', 'freeze_graph'),
                    (r, '_make_file_witness', 'make_file_witness'),
                    (r, '_check_file_witness', 'check_file_witness')]:
                    patch.setattr(obj, name, recorder.watch(getattr(obj, name), label))
                patch.setattr(r.workload, 'build_inventory', recorder.watch(r.workload.build_inventory,
                    'build_inventory', detail=lambda *args, **kwargs: str(kwargs.get('stage', 'unknown'))))
                patch.setattr(r, 'read_object', recorder.watch(r.read_object, 'read_large_object',
                    detail=lambda path: Path(path).name, predicate=_large_read))
                with recorder.phase('construct_fixture'):
                    c = PreparedCase(recorder.output / part, patch, part=part, selected=(part == 'selected'))
                with recorder.phase('independent_inventory_validation'):
                    r.workload._validate_inventory(c.pilot_inventory)
                with recorder.phase('live_and_authority_guard'):
                    guard = c.guard()
                reservation = guard['reservation']
                assert reservation['allocation_verified'] is True and c.loader_calls == []
                selected_records = 0
                invocations = len(c.pilot_inventory['packing_invocations'])
                if part == 'selected':
                    with recorder.phase('selected_backing_read'):
                        selected, arrays = r.read_bundle(c.args.selected)
                    assert selected == c.selected and len(selected['selected_records']) == 9
                    assert {(row['task'], row['seed']) for row in selected['selected_records']} == {
                        (task, seed) for task in c.design['tasks'] for seed in (42, 1, 123)}
                    assert all(len(row['assessment_axes']) == 199 and len(row['calibration_axes']) == 32
                        for row in selected['selected_records'])
                    assert not selected['blocked_task_seeds'] and arrays and invocations == 63
                    assert len(c.design['mmlu_validation']) == 32
                    assert c.protocol['workload']['microbatch_size'] == 2
                    assert c.protocol['workload']['pad_tail_batches'] is True
                    selected_records = 9
                manifest['results'][part] = dict(status='FIXTURE_ORIGINAL_VALIDATORS_PASS',
                    pilot_stage=c.pilot_inventory['stage'], expected_pilot_stage='prefit' if part == 'prefit' else 'selected-pilot',
                    selected_records=selected_records, packing_invocations=invocations,
                    expected_key_count=len(c.pilot_inventory['expected_keys']),
                    published_inventory_bytes=(c.pilot_path / 'payload.json').stat().st_size,
                    conservative_host_tier_bytes=c.pilot_inventory['storage_requirements']['tiers']['host_ram'],
                    model_loader_calls=len(c.loader_calls), wall_seconds=time.perf_counter()-started,
                    observations=r._prepared_process_observation(), injected_allocation_only=True,
                    source_protection_and_root_validators_active=True)
                recorder.save()
            # Every instrumentation and ancestry-fixture patch is undone here.
            assert all(getattr(obj, name) is original for obj, name, original in originals)
            manifest['results'][part]['original_symbols_restored'] = True
            recorder.save()
            recorder.mark('part_complete', 'exit')
        source_after = r.artifacts.code_hashes()
        assert source_after == source_before and hashlib.sha256(pins_path.read_bytes()).hexdigest() == pins_hash
        manifest.update(status='FIXTURE_PREFLIGHT_COMPLETE', normal_completion=True, exit_code=0,
            source_after=source_after, source_pins_before_after_equal=True)
    except BaseException as error:
        manifest.update(status='FAILED', normal_completion=False, exit_code=1, error=repr(error)); raise
    finally: recorder.save()
