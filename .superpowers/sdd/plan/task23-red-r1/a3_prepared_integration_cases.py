"""CPU test fixtures only; none is a production provider or admission artifact.

External A1 ancestry uses the SAME injected seams as artifacts.live_fixture;
original validate_live source/protection checks and root reservation validation
remain active. All files below are fresh test files, never operational evidence.
"""
import copy
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
from types import SimpleNamespace


def runtime():
    from component_analysis import a3_direction_runtime
    return a3_direction_runtime


def rewrite_object(path, value):
    """Test attack/fixture publication at a new version; ordinary publisher stays real."""
    import shutil
    path = Path(path)
    if path.exists(): shutil.rmtree(path)
    runtime().publish_object(path, value)


def environment_identity():
    r = runtime()
    return dict(python_implementation=platform.python_implementation(),
        python_version=platform.python_version(), numpy_version=r.np.__version__,
        torch_version=r.torch.__version__, platform=platform.system(),
        deployment_family='injected-cpu-unit-fixture', storage_family='ordinary-test-directory')


class PreparedCase:
    """Own actual immutable artifacts and original validator inputs for one test."""
    def __init__(self, root, monkeypatch, *, part='prefit', selected=False):
        from tests.test_a3_direction_runtime import _real_injected_design
        from component_analysis import a3_pipeline
        r = runtime(); self.r = r; self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.monkeypatch = monkeypatch; self.part = part; self.trace = []; self.loader_calls = []
        def forbidden_loader(*args, **kwargs):
            self.loader_calls.append((args, kwargs)); raise AssertionError('unexpected model loader entry')
        self.monkeypatch.setattr(r.ladder, 'load_model', forbidden_loader)
        self.design, self.protocol = _real_injected_design()
        d = self.design; p = self.protocol
        # Four actual synthetic training IDs permit the original fit/selection
        # pipeline to emit complete selected backing, rather than inline axes.
        for task, spec in d['tasks'].items():
            original = list(d['access_rows'][task]); ids = [task + ':train:' + str(j) for j in range(4)]
            train = []
            for condition in ('D', 'H', 'F', 'I', 'user_neutral'):
                source = next(row for row in original if row['split'] == 'train' and row['condition'] == condition)
                for j, rid in enumerate(ids):
                    row = copy.deepcopy(source); row.update(instance_id=rid, source_id=rid, pressure_text='wording' + str(j // 2))
                    for stream, saved in row['streams'].items():
                        saved.update(prompt=rid + condition + stream, tokens=[1, 2, 3+j], readout=2)
                    train.append(row)
            spec['fit_ids'] = ids
            d['access_rows'][task] = train + [row for row in original if row['split'] != 'train']
        d['a1_identity']['grader_sha256'] = r.ladder.GRADER
        parent = copy.deepcopy(d['a1_identity']); parent_selected = {}
        d['a1_repo_root'] = str(self.root)
        d['parent_digests'] = dict(prepared=r.ladder.design._hash(parent), selected=r.ladder.design._hash(parent_selected))
        source = self.root / 'source.txt'; source.write_text('actual immutable injected source\n')
        d['historical_source_hashes'] = {str(source): r.common.file_hash(source)}
        d['matched_build_path'] = str(source); d['matched_build_file_sha256'] = r.common.file_hash(source)
        self.source_path = source
        self.registry = self.root / 'registry.json'; self.registry.write_text(json.dumps(dict(schema=1, sets=[])))
        # These ancestry-only seams already exist in live_fixture. No source,
        # protected-set, inventory, root mapping or reservation validator is mocked.
        self.monkeypatch.setattr(a3_pipeline, 'load_a1_parents', lambda *args: (
            copy.deepcopy(parent), copy.deepcopy(parent_selected), copy.deepcopy(d['parent_evidence'])))
        self.monkeypatch.setattr(a3_pipeline, '_validate_parent_files', lambda *args, **kwargs: None)
        self.monkeypatch.setattr(a3_pipeline, 'validate_assessment_membership', lambda *args: None)
        closure = r.artifacts.code_hashes()
        p.update(code_hashes=closure, injected_source_closure=copy.deepcopy(closure))
        cfg = p['workload']
        required = ('microbatch_size', 'axis_tile_size', 'num_layers', 'vocabulary_size', 'dtype_bytes',
            'hardware', 'warmup_batches', 'serialization_batches', 'finish_reserve_seconds', 'jobs')
        settings = {key: copy.deepcopy(cfg[key]) for key in required}
        settings.update(head_width=2, hidden_size=4, dtype='torch.float32', backend='fake',
            probe_max_bytes=1048576, axis_tile_sizes=dict(prefit=2, **{'fit-select': 2, 'selected-pilot': 32, 'remaining': 32}))
        r.freeze_operational_contract(d, p, settings)
        core = {key: value for key, value in d.items() if key not in ('direction_protocol', 'direction_protocol_sha256')}
        p['design_sha256'] = r.ladder.design._hash(core)
        d['direction_protocol'] = p; d['direction_protocol_sha256'] = r.ladder.design._hash(p)
        r.ladder.write_artifact(self.root / 'design.json', d)
        r.ladder.write_artifact(self.root / 'direction_protocol.json', p)
        self.selected = None
        if selected: self._complete_selected_backing()
        self.pilot_inventory = r.workload.build_inventory(d, p,
            stage='prefit' if part == 'prefit' else 'selected-pilot', selected=self.selected)
        self.pilot_path = self.root / 'inventory' / ('prefit' if part == 'prefit' else 'selected-pilot')
        r.publish_object(self.pilot_path, self.pilot_inventory)
        self.target_path = self.root / 'pilot-target-inventory' / part
        self.preparation_path = self.root / 'pilot-target-preparation' / part
        argv = ['--experiment', 'directions', '--stage', 'pilot', '--pilot-part', part,
            '--work-dir', str(self.root), '--design', str(self.root / 'design.json'), '--commit', p['commit'],
            '--inventory', str(self.pilot_path), '--registry', str(self.registry)]
        if selected: argv.extend(['--selected', str(self.root / 'selected')])
        self.args = r.parser().parse_args(argv)
        self._bind_original_authority()

    def _complete_selected_backing(self):
        """Use original fit/freezer and complete numeric files, never an inline fake selection."""
        r = self.r; p = r.pipeline; d = self.design; protocol = self.protocol
        metadata, layout = p._fit_contract(d, protocol)
        rng = r.np.random.default_rng(21); arrays = {}
        for item in layout:
            arrays[item['projection']] = r.np.eye(4, 2, dtype='float32')
            h = rng.normal(size=(len(item['instance_ids']), 2, 2)).astype('float32')
            for condition, name in item['activations'].items():
                arrays[name] = h.copy()
                if condition == 'D': arrays[name] += r.np.array([2., -1.], dtype='float32')
                if condition == 'user_neutral': arrays[name] -= r.np.array([.2, 1.], dtype='float32')
        cache = self.root / 'cache' / 'fit-selection'
        r.artifacts.write_bundle(cache, metadata, arrays)
        fits = p.fit_from_cache(d, cache, protocol=protocol, output=self.root / 'fits')
        _, fitted_arrays = r.artifacts.read_bundle(self.root / 'fits', expected=fits)
        fit_ref = p._bundle_byte_reference(self.root / 'fits')
        validation = self.root / 'validation'
        for group in p._selection_layout(d, protocol, fits):
            path = validation / group['group_id']
            r.artifacts.write_bundle(path / 'capture', group['capture_metadata'], {})
            identity = copy.deepcopy(group['capture_metadata']['identity'])
            identity['capture_lineage'] = [r.artifacts.capture_reference(path / 'capture', expected=group['capture_metadata'])]
            for shard in group['shards']:
                rows = []
                for key in shard['expected_keys']:
                    row = dict(zip(r.artifacts.KEY_FIELDS, key)); row['site'] = list(row['site'])
                    source = group['sources'][(row['condition'], row['instance_id'])]
                    fit = next(record for record in fits['fit_records'] if record['task'] == row['analysis_task']
                        and record['seed'] == row['seed'] and record['site'] == row['site'])
                    axis = p._loaded_fit_axis(fits, fitted_arrays, fit, 'dom'); condition = row['condition']
                    row.update(intact_margin=2. if condition in ('D', 'I') else 0.,
                        patched_margin=.6 if condition == 'D' else (1.8 if condition == 'I' else 0.),
                        intact_correct=True, patched_correct=True, epsilon=1e-6,
                        source_provenance=p._selection_source_record(source, row['stream'], row['source_task']),
                        numeric_profile=group['numeric_profile'], axis_hash=r.runner.axis_identity(axis),
                        replay_valid=True, supported=True, positive_control={'valid': True}, gate_valid=True)
                    rows.append(row)
                r.artifacts.publish_shard(path / 'shards' / shard['shard_id'], identity=identity,
                    expected_keys=shard['expected_keys'], rows=rows, execution={'fit_reference': fit_ref})
        self.selected = p.freeze_selection(d, self.root / 'fits', validation, protocol=protocol,
            output=self.root / 'selected', protocol_path=self.root / 'direction_protocol.json')
        assert len(self.selected['selected_records']) == 9 and not self.selected['blocked_task_seeds']

    def _bind_original_authority(self, preparation=None):
        from tests.test_a3_direction_runtime import _authority_case
        r = self.r
        if not hasattr(self, 'live_path'):
            _, _, _, _, self.live_path, self.live = _authority_case(self.root / 'authority',
                inventory=self.pilot_inventory, work_dir=str(self.root))
        actual = self.live['reservations'][0]
        actual.update(status='running', output_dir=str(self.root), source_commit=self.pilot_inventory['identity']['commit'])
        self.live_path.write_text(json.dumps(self.live))
        version = getattr(self, '_version', 0) + 1; self._version = version
        snapshot = self.root / ('ledger-snapshot-' + str(version) + '.json'); snapshot.write_bytes(self.live_path.read_bytes())
        original = r.read_object(self.root / 'authority' / 'admission'); original.pop('admission_sha256')
        original['kind'] = 'a3_root_pilot_admission_v1'
        if preparation is not None: original['pilot_target_preparation'] = preparation
        original['admission_sha256'] = r.workload.digest(original)
        self.admission_path = self.root / ('admission-' + str(version)); r.publish_object(self.admission_path, original)
        mapping = r.read_object(self.root / 'authority' / 'current-map')
        mapping.update(ledger_snapshot_path=str(snapshot), ledger_sha256=r.common.file_hash(snapshot),
            original_admission_paths=[str(self.admission_path)],
            storage_capacities={'host_ram': {'pool': 'ram', 'available_bytes': 2**44}})
        entry = mapping['entries'][0]; entry.update(phase=self.pilot_inventory['phase'], actual_entry=copy.deepcopy(actual))
        entry['reservation_lineage']['admission_sha256'] = original['admission_sha256']
        self.mapping_path = self.root / ('mapping-' + str(version)); r.publish_object(self.mapping_path, mapping)
        reservation = r.read_object(self.root / 'authority' / 'reservation')
        reservation.update(actual_entry={key: actual.get(key) for key in r.RESERVATION_FIELDS},
            admission_path=str(self.admission_path), admission_reference=r.object_reference(self.admission_path),
            admission_sha256=original['admission_sha256'], end_time_unix=time.time() + 600)
        self.reservation_path = self.root / ('reservation-' + str(version)); r.publish_object(self.reservation_path, reservation)
        self.args.ledger_snapshot = str(self.mapping_path); self.args.reservation = str(self.reservation_path)
        self.args.admission = str(self.admission_path)
        for name in ('_authority_context', '_authority_ledger_reference'):
            if hasattr(self.args, name): delattr(self.args, name)

    def prepare(self):
        args = copy.copy(self.args); args.stage = 'prepare'; args.action = 'pilot-target'
        return self.r.prepare_pilot_target(args, self.design, self.protocol, selected=self.selected)

    def anchor(self, *, retained_margin=1048576, transient_margin=1048576):
        r = self.r; self.prepare()
        target_ref = r.object_reference(self.target_path); preparation_ref = r.object_reference(self.preparation_path)
        self.namespace_policy = dict(work_dir=str(self.root), target_root=str(self.target_path),
            preparation_root=str(self.preparation_path), allowed_aliases=(), expected_resolved=dict(
                work_dir=str(self.root.resolve()), target_root=str(self.target_path.resolve()),
                preparation_root=str(self.preparation_path.resolve())))
        value, refs, namespace, witness, io_counts, observations = r._read_prepared_target_object(
            target_ref, preparation_ref, self.namespace_policy)
        self.observed = observations; self.target_inventory = value
        self.resource_record = dict(kind='a3_prepared_target_receiver_resources_v1', references=refs,
            source_identity=dict(commit=self.protocol['commit'], code_hashes=self.protocol['code_hashes'],
                design_sha256=self.protocol['design_sha256'], protocol_sha256=r.ladder.design._hash(self.protocol)),
            reader_sha256=r.common.file_hash(Path(r.__file__)), freeze_sha256=r.common.file_hash(Path(r.workload.__file__)),
            environment=environment_identity(), recipe=observations['recipe'], scope=observations['scope'],
            observed_io=io_counts, retained_metadata_bytes_bound=observations['retained_metadata_bytes'] + retained_margin,
            extra_transient_bytes_bound=observations['extra_transient_bytes'] + transient_margin,
            process_peak_rss_bytes_bound=2**44, cgroup_peak_bytes_bound=2**44,
            provenance=dict(pid=__import__('os').getpid(), normal_completion=True, exit_code=0,
                injected=True, source_before=self.protocol['code_hashes'], source_after=r.artifacts.code_hashes()),
            model_loaded=False, execution_authorized=False)
        self.resource_path = self.root / 'receiver-resources'; r.publish_object(self.resource_path, self.resource_record)
        preparation = dict(part=self.part, pilot_inventory_sha256=self.pilot_inventory['inventory_sha256'],
            target_reference=target_ref, preparation_reference=preparation_ref,
            receiver_resources_reference=r.object_reference(self.resource_path), namespace_policy=self.namespace_policy)
        self._bind_original_authority(preparation)
        self.preparation_binding = preparation
        return self

    def load(self):
        return self.r.load_prepared_pilot_target(self.args, self.design, self.protocol,
            self.pilot_inventory, selected=self.selected)

    def guard(self):
        return self.r.live_guard(self.design, self.protocol, self.args, self.pilot_inventory)
