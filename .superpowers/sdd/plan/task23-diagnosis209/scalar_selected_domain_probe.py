"""Tiny scalar execution of original grouping code; never build an inventory."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
W = HERE.parents[3]
CANDIDATE = HERE.parent.parent / 'plan-a3/direction-preallocation-candidate183'
FAILED = HERE.parent / 'task23-red-r1/red-run-01/base/fixture-preflight/selected'
source_path = CANDIDATE / 'component_analysis/a3_direction_workload.py'
source = source_path.read_text(); tree = ast.parse(source)
selected = json.loads((FAILED / 'selected/manifest.json').read_text())
design = json.loads((FAILED / 'design.json').read_text())['payload']
protocol = json.loads((FAILED / 'direction_protocol.json').read_text())['payload']
functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
build = functions['build_inventory']
needed = ['_require', '_integer', '_freeze', '_chunks', '_source_rows', '_length', '_timing_ids']
namespace = {'CONDITIONS': ('D', 'H', 'F', 'I', 'user_neutral')}
exec(compile(ast.Module(body=[functions[n] for n in needed], type_ignores=[]), str(source_path), 'exec'), namespace)
for n in build.body:
    if isinstance(n, ast.FunctionDef) and n.name in ('groups', 'streams'):
        exec(compile(ast.Module(body=[n], type_ignores=[]), str(source_path), 'exec'), namespace)


def count(d, cfg):
    namespace.update(design=d, cfg=cfg, batch=cfg['microbatch_size'])
    namespace['source_rows'] = lambda task, split: namespace['_source_rows'](d, task, split)
    namespace['timing'] = {task: namespace['_timing_ids'](namespace['_source_rows'](d, task, 'validation'))
        for task in list(d['tasks']) + ['ioi', 'mmlu']}
    keys = 0; invocations = 0; groups_by_source = {}
    for rec in selected['metadata']['selected_records']:
        assert rec['nuisance']['status'] == 'fitted'
        main = 1 + len(rec['assessment_axes']) + 1 + 4 + 6
        calibration = 1 + len(rec['calibration_axes'])
        for stage, cells in [('main', main), ('calibration', calibration)]:
            for src in (rec['task'], 'ioi', 'mmlu'):
                groups = namespace['groups'](src, 'validation', pilot=True,
                    target_split='assessment' if stage == 'main' else 'validation')
                expanded = cells
                if src == 'mmlu': expanded = (main - 4 - 6) * 2 + 6 if stage == 'main' else calibration * 2
                keys += sum(len(ids) for condition, stream, ids in groups) * expanded
                invocations += len({len(ids) for condition, stream, ids in groups})
                groups_by_source[stage + ':' + src] = sorted({len(ids) for condition, stream, ids in groups})
    return dict(raw_expected_keys=keys, packing_invocations=invocations, cohort_sizes=groups_by_source)


started = time.perf_counter(); old = count(design, protocol['workload'])
assert old['raw_expected_keys'] == (86456320 - 65536) // 1024 == 84366
assert old['packing_invocations'] == 63
small = copy.deepcopy(design)
for task, spec in small['tasks'].items():
    spec['selection_ids'] = spec['selection_ids'][:1]
    small['access_rows'][task] = [row for row in small['access_rows'][task]
        if row['split'] != 'validation' or row['instance_id'] in spec['selection_ids']]
small['ioi_validation'] = small['ioi_validation'][:1]
small['utility']['ioi'] = small['utility']['ioi'][:1]
small['utility']['mmlu'] = small['utility']['mmlu'][:2]
# Actual fixture correction must regenerate original IOI/MMLU maps and protocol
# identity, then call original validators. This scalar probe makes no such claim.
new = count(small, dict(protocol['workload'], pad_tail_batches=False))
keep63 = count(small, dict(protocol['workload'], microbatch_size=4, pad_tail_batches=False))
assert keep63['packing_invocations'] == 63
domain_only = copy.deepcopy(small)
domain_only['ioi_validation'] = copy.deepcopy(design['ioi_validation'])
domain63 = count(domain_only, protocol['workload'])
assert domain63['packing_invocations'] == 63 and domain63['raw_expected_keys'] == 45315
# Execute ORIGINAL small source validators/maps, not a hand-written substitute.
import types
pipeline_tree = ast.parse((CANDIDATE / 'component_analysis/a3_direction_pipeline.py').read_text())
design_tree = ast.parse((CANDIDATE / 'component_analysis/a3_design.py').read_text())
map_tree = ast.parse((CANDIDATE / 'component_analysis/ladder_tasks.py').read_text())
ns = dict(copy=copy, require=namespace['_require'], STREAMS=tuple(protocol['stream_order']))
identity_fn = next(n for n in design_tree.body if isinstance(n, ast.FunctionDef) and n.name == '_utility_identity')
exec(compile(ast.Module(body=[identity_fn], type_ignores=[]), '<original utility identity>', 'exec'), ns)
ns['a3_design'] = types.SimpleNamespace(_utility_identity=ns['_utility_identity'])
selection_fn = next(n for n in pipeline_tree.body if isinstance(n, ast.FunctionDef) and n.name == '_selection_sources')
exec(compile(ast.Module(body=[selection_fn], type_ignores=[]), '<original selection sources>', 'exec'), ns)
source_counts = {task: len(ns['_selection_sources'](domain_only, task))
    for task in list(domain_only['tasks']) + ['ioi', 'mmlu']}
map_fns = [n for n in map_tree.body if isinstance(n, ast.FunctionDef)
    and n.name in ('_map', 'ioi_item_swap_maps', 'mmlu_calibration_maps')]
exec(compile(ast.Module(body=map_fns, type_ignores=[]), '<original maps>', 'exec'), ns)
ioi_maps = ns['ioi_item_swap_maps'](domain_only['utility']['ioi'])
mmlu_maps = ns['mmlu_calibration_maps'](domain_only['utility']['mmlu'])
assert len(ioi_maps) == 1 and len(mmlu_maps) == 2
assert all(row['recipient_id'] != row['donor_id'] for row in mmlu_maps)

assert len(small['mmlu_validation']) == 32
assert len(selected['metadata']['selected_records']) == 9
assert all(len(rec['assessment_axes']) == 199 and len(rec['calibration_axes']) == 32
    for rec in selected['metadata']['selected_records'])
result = dict(status='SCALAR_GROUPING_PROBE_COMPLETE_NOT_FULL_VALIDATION',
    old=old, proposed_small=new, proposed_small_preserving_63=keep63, recommended_domain_only_preserving_policy_and_63=domain63, source_sha256=hashlib.sha256(source.encode()).hexdigest(),
    original_source_validator_counts=source_counts, original_map_counts=dict(ioi=len(ioi_maps), mmlu=len(mmlu_maps)),
    original_selected_records=9, assessment_axes_per_record=199, calibration_axes_per_record=32,
    mandatory_mmlu_validation=32, selected_manifest_bytes=(FAILED/'selected/manifest.json').stat().st_size,
    numeric_array_bytes=sum(v['bytes'] for v in selected['arrays'].values()),
    recommended_fraction_raw_keys=domain63['raw_expected_keys']/old['raw_expected_keys'],
    full_validator_run=False, actual_RAM_bound_established=False, candidate_changed=False,
    wall_seconds=time.perf_counter()-started)
(HERE / 'scalar-selected-domain-result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps(result, sort_keys=True))
