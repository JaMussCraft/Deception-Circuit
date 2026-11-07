#!/usr/bin/env python3
"""Fresh native owning CPU guard; never loads weights, scores or rewrites G3."""
import argparse
import hashlib
import importlib
import json
import os
import re
from pathlib import Path
import sys
import time

SOURCE = '50e947bb852613e3a270082651f2bd1b7bb0c525'
ALIGNMENT = '/projects/beto/swong2/Alignment'
W = ALIGNMENT + '/Deception-Circuit/.claude/worktrees/specificity-ladder'
CATALOGUES = tuple(root + '/docs/research/' + name for root in (
    ALIGNMENT + '/Deception-Circuit', W) for name in ('held_out.json', 'directions.json'))
REMOTE = '/ocean/projects/cis260361p/swong2/specificity-ladder-a2-assay-20261103/Alignment'
SCIENCE_FIELDS = ('schema','group_source','source_kind','groups','compute_groups','bank_keys','tasks',
    'comparison','comparison_sha256','a1_design_sha256','a1_selected_sha256','selection_receipt',
    'selection_sidecar_sha256','assessment','model_geometry','model_identity','a1_ancestor_commit',
    'a2_training_execution_commit','operations','independent_donor_seeds','injected','limitations')


def require(ok, message):
    if not ok: raise ValueError(message)


def digest(raw): return hashlib.sha256(raw).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): h.update(block)
    return h.hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key: ' + key)
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique_pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def bound(ref):
    path = Path(ref['path'])
    require(path.is_absolute() and not path.is_symlink(), 'ordinary absolute bound reference')
    raw = path.read_bytes()
    require(digest(raw) == ref['sha256'], 'bound reference changed: ' + str(path))
    return decode(raw)


def score_arguments(parameters):
    require(parameters['phase'] == 'full_score' and parameters['accepted_source_commit'] == SOURCE,
            'original full_score source only')
    return ['--stage', 'score', '--design', parameters['design'], '--selected', parameters['selected'],
            '--commit', SOURCE, '--batch-size', '8', '--registry', parameters['registry'],
            '--work-dir', parameters['new_g3_output']]


def validate_native_context(parameters, p):
    args = p.parser().parse_args(score_arguments(parameters))
    prepared, selected, sidecar = p._load_context(args)
    args.tasks = list(p.TASKS)
    args.injected = bool(prepared.get('injected'))
    for field in ('model', 'model_revision', 'tokenizer_revision'): setattr(args, field, prepared[field])
    receipt = p.a1.read_artifact(Path(parameters['new_g3_output']) / 'groups.json')
    p._validate_live(args, receipt, prepared)
    require(receipt['model_geometry'] == p.model_geometry_receipt(prepared), 'fresh geometry drift')
    require(not receipt['injected'] and not prepared['injected'] and len(receipt['groups']) == 9,
            'genuine nine-group freeze required')
    banks = p.read_stage(Path(parameters['new_g3_output']) / 'bank', 'banks.json', 'bank', args, receipt)
    p.validate_banks(receipt, prepared, banks)
    require(banks['kind'] == 'a2_h_banks' and banks['injected'] is False, 'genuine native bank')
    execution = banks['execution_provenance']
    require(execution['gpu_name'] == 'NVIDIA H100 80GB HBM3' and execution['dtype'] == 'torch.bfloat16'
            and execution['device'].split(':')[0] == 'cuda', 'authentic H100 BF16 bank provenance')
    numeric = p.numeric_environment()
    require(set(banks['banks']) == set(p.TASKS), 'complete bank tasks')
    for task in p.TASKS:
        require(banks['banks'][task]['contract']['numeric_environment'] == numeric,
                'actual numeric environment differs from bank: ' + task)
    for field in ('model', 'model_revision', 'tokenizer_revision'): setattr(args, field, prepared[field])
    tokenizer = p.a1.common.load_tokenizer(args)
    p.a1.validate_tokenization(prepared, tokenizer)
    p._validate_live(args, receipt, prepared)
    return dict(numeric_environment=numeric, bank_execution_provenance=execution,
                model_loaded=False, freeze_executed=False, GPU_admitted=False,
                _args=args, _prepared=prepared, _receipt=receipt, _banks=banks)


def verify_source_export(runtime, snapshot):
    runtime = Path(runtime)
    require(runtime.is_absolute() and not runtime.is_symlink() and str(runtime) == snapshot['runtime_root'],
            'exact ordinary runtime root')
    source, links = snapshot['source_sha256'], snapshot['input_links']
    require(snapshot['source_commit'] == SOURCE and len(source) == 511 and len(links) == 4
            and snapshot['source_code_symlinks'] is False, 'exact accepted 511+4 export')
    require(not set(source) & set(links), 'source/link overlap')
    for name in list(source) + list(links):
        rel = Path(name)
        require(not rel.is_absolute() and '..' not in rel.parts and str(rel) == name, 'unsafe relative source key')
    files, actual_links = set(), set()
    for path in runtime.rglob('*'):
        rel = str(path.relative_to(runtime))
        if path.is_symlink(): actual_links.add(rel)
        elif path.is_file(): files.add(rel)
    require(files == set(source) and actual_links == set(links), 'source inventory changed')
    for name, expected in source.items():
        item = runtime / name
        require(not item.is_symlink() and runtime.resolve() in item.resolve().parents
                and sha(item) == expected, 'ordinary source changed: ' + name)
    for name, target in links.items():
        item = runtime / name
        require(item.is_symlink() and os.readlink(item) == target and item.exists()
                and item.resolve() == Path(target).resolve(), 'literal input link changed: ' + name)
    return dict(source_count=511, input_link_count=4, source_commit=SOURCE, input_links=dict(links))


def validate_catalogues(current):
    require(set(current) == set(CATALOGUES), 'exact four current catalogue routes required')
    for virtual, row in current.items():
        require(type(row) is dict and set(row) == {'virtual','physical','bytes','sha256','delta_capture','remote','delta_reread'},
                'closed catalogue row')
        require(isinstance(row['sha256'],str) and re.fullmatch('[0-9a-f]{64}',row['sha256']), 'catalogue SHA256')
        physical = REMOTE + virtual[len(ALIGNMENT):]
        require(row['virtual'] == virtual and row['physical'] == physical, 'catalogue physical route')
        require(type(row['bytes']) is int and row['bytes'] >= 0, 'catalogue byte count')
        stamps = []
        for label, cluster, path in (('delta_capture', 'delta', virtual),
                                      ('remote', 'bridges2', physical), ('delta_reread', 'delta', virtual)):
            obs = row[label]
            require(type(obs) is dict and set(obs) == {'cluster','path','bytes','sha256','observed_unix'}, 'closed catalogue observation')
            require(obs['cluster'] == cluster and obs['path'] == path
                    and obs['sha256'] == row['sha256'] and obs['bytes'] == row['bytes'],
                    'catalogue same-buffer witness: ' + label)
            stamp = obs['observed_unix']
            require(type(stamp) in (int, float) and 0 < stamp < float('inf'), 'catalogue timestamp')
            stamps.append(stamp)
        require(stamps == sorted(stamps), 'catalogue capture/transfer/reread order')
    return current


def catalogue_expectations(ref, packet_sha256, job_id):
    witness = bound(ref)
    require(witness['complete'] is True and witness['adapter_manifest_sha256'] == packet_sha256
            and witness['actual_job_id'] == job_id, 'fresh Task2 job/packet witness required')
    for key, value in dict(source_files=511, ordinary_inputs=422, immutable_original_inputs=418,
                           current_catalogue_inputs=4, literal_source_links=4).items():
        require(type(witness[key]) is int and witness[key] == value, 'witness role count: ' + key)
    require(witness['catalogues_are_snapshots_not_continuous_Delta'] is True, 'catalogue snapshot scope')
    current = validate_catalogues(witness['current_catalogues'])
    require(sha(ref['path']) == ref['sha256'], 'catalogue witness changed while parsing')
    return current


def verify_input_closure(manifest, current, read_bytes=None):
    validate_catalogues(current)
    read_bytes = read_bytes or (lambda path: Path(path).read_bytes())
    rows, aliases = manifest['ordinary_files'], manifest['namespace_aliases']
    require(len(rows) == 422 and set(CATALOGUES) <= set(rows) and len(aliases) == 5,
            'exact corrected422 plus five aliases')
    require(not set(rows) & set(aliases), 'ordinary/alias overlap')
    for path, old in rows.items():
        require(Path(path).is_absolute() and old['path'] == path, 'exact lexical ordinary path')
        expected = current[path] if path in current else old
        raw = read_bytes(path)
        require(len(raw) == expected['bytes'] and digest(raw) == expected['sha256'],
                'ordinary input changed: ' + path)
    for path, target in aliases.items():
        item = Path(path)
        require(item.is_symlink() and os.readlink(item) == target and item.exists()
                and item.resolve() == Path(target).resolve(), 'literal namespace alias changed: ' + path)
    return dict(ordinary_count=422, immutable_original_count=418, current_catalogue_count=4, alias_count=5)


def validate_domain_identity(rows, controls, mask, reconstructed_controls, reference):
    require(len(rows) == len(set(rows)) == reference['rows'] == reference['reconstructed_rows'] == 59652,
            'complete unique native row domain')
    require(set(rows) == set(mask), 'native reconstructed row identities differ')
    require(len(controls) == len(set(controls)) == reference['positive_controls'] == 3396
            and len(reconstructed_controls) == len(set(reconstructed_controls))
            == reference['reconstructed_controls'] == 3396 and set(controls) == set(reconstructed_controls),
            'complete unique native control identities')
    for supported, reason in mask.values():
        require(type(supported) is bool and (reason is None if supported else isinstance(reason, str) and bool(reason)),
                'explicit support/reason semantics')
    raw = json.dumps([[list(k), list(mask[k])] for k in sorted(mask)],
                     separators=(',', ':'), ensure_ascii=True).encode()
    require(digest(raw) == reference['support_reason_mask_sha256'], 'complete support/reason mask drift')
    return dict(rows=59652, positive_controls=3396, support_reason_mask_sha256=digest(raw),
                reconstructed_rows=len(mask), reconstructed_controls=len(reconstructed_controls))


def reconstruct_domain(p, prepared, receipt):
    # Mirrors native caller filtering, singleton views and operation-specific map lookup.
    from component_analysis.ladder_tasks import task_batches
    from component_analysis.specificity_ladder import _rows
    require(not receipt['independent_donor_seeds'], 'new optional independent seeds require review')
    mask, controls = {}, set()
    def views(batches):
        found = {}
        for batch in batches:
            for row in _rows(batch):
                key = (row.condition, row.ids[0], row.stream)
                require(key not in found, 'duplicate native singleton identity')
                found[key] = row
        return found
    def mapping(maps, operation, key):
        found = [m for m in maps if m['operation'] == operation and
                 (m['recipient_condition'], m['recipient_id'], m['recipient_stream']) == key]
        require(len(found) <= 1, 'duplicate operation-filtered donor map')
        return found[0] if found else None
    def collect(task, kind, recipients, donors, groups, aliases, operations, maps):
        recipients, donors = views(recipients), views(donors)
        for operation in operations:
            for key in recipients:
                m = mapping(maps, operation, key)
                require(operation in ('zero','h_mean','self_replay','empty') or m is not None,
                        'required donor map absent')
                supported = True if m is None else m['supported']
                require(type(supported) is bool, 'native support boolean')
                if supported and operation not in ('zero','h_mean','self_replay','empty'):
                    require((m['donor_condition'],m['donor_id'],m['donor_stream']) in donors, 'missing native donor')
                for group, _ in groups:
                    for alias in aliases[group]:
                        rowkey = (task if kind == 'assessment' else kind, key[1], key[0], key[2], alias, operation, None)
                        require(rowkey not in mask, 'duplicate reconstructed row')
                        mask[rowkey] = (supported, None if supported else m.get('unsupported_reason'))
        for key, row in recipients.items():
            if kind == 'assessment': m = mapping(maps, 'item_swap', key)
            else:
                found = [m for m in maps if (m['recipient_condition'],m['recipient_id'],m['recipient_stream']) == key]
                require(len(found) == 1, 'native calibration map identity')
                m = found[0]
            require(m is not None, 'calibration donor missing')
            dk = (m['donor_condition'],m['donor_id'],m['donor_stream'])
            require(dk in donors, 'calibration donor unavailable')
            if kind in ('assessment','ioi'):
                require(m['donor_id'] == key[1], 'native same-row calibration')
            else:
                require(m['supported'] is True and m['recipient_positions'] == [int(row.readout[0])]
                        and m['donor_positions'] == [int(donors[dk].readout[0])], 'MMLU calibration readout')
            control = (task, task if kind == 'assessment' else kind, key[1], key[0], key[2])
            require(control not in controls, 'duplicate reconstructed control')
            controls.add(control)
    for task in p.TASKS:
        frozen = prepared['designs'][task]; ids = set(frozen['assessment_ids']); rows = prepared['rows'][task]
        groups, aliases = p._groups_for_compute(receipt, task)
        rs = [b for c in p.a1.design.CONDITIONS for s in p.a1.design.STREAMS
              for b in p.a1.batches([r for r in rows[c] if r['instance_id'] in ids], s, batch_size=8)]
        ds = [b for c in p.a1.design.CONDITIONS for s in p.a1.design.STREAMS
              for b in p.a1.batches(rows[c], s, batch_size=8)]
        maps = [m for m in frozen['donors'] if m['recipient_id'] in ids]
        collect(task,'assessment',rs,ds,groups,aliases,receipt['operations'],maps)
        for utility in ('ioi','mmlu'):
            rs = task_batches(prepared['utility'][utility], batch_size=8)
            ds = task_batches(prepared['utility'][utility], stream='corrupt' if utility == 'ioi' else 'clean')
            ops = ('item_swap','zero','h_mean','self_replay','empty') if utility == 'ioi' else ('zero','h_mean','self_replay','empty')
            collect(task,utility,rs,ds,groups,aliases,ops,prepared['utility'][utility+'_maps'])
    return mask, controls


def origins(runtime):
    result = {}
    for name, module in list(sys.modules.items()):
        if name.split('.')[0] in ('component_analysis','models','dataset','evaluation','scripts','config'):
            path = getattr(module, '__file__', None)
            if path:
                path = Path(path).resolve()
                require(runtime in path.parents, 'project import escaped frozen runtime: ' + name)
                result[name] = str(path)
    return result


def capture_identities(c):
    runtime = Path(c['accepted_runtime'])
    snapshot = bound(c['accepted_source_snapshot']); manifest = bound(c['input_manifest'])
    current = catalogue_expectations(c['current_catalogue_witness'], c['packet_manifest_sha256'], c['actual_CPU_job_id'])
    require(time.time() < c['phase_deadline_unix'], 'owning proof window expired')
    verify_source_export(runtime, snapshot); verify_input_closure(manifest, current)
    for name in ('independent_source_acceptance','accepted_export_receipt','historical_G2','full_domain_proof'):
        bound(c[name])
    main = Path(c['new_g3_output'])
    require(main == Path(W + '/outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1'), 'original main G3 only')
    hashes = {}
    for key, path, wanted in (('groups',main/'groups.json',c['frozen_G3_sha256']),
        ('bank',main/'bank/banks.json',c['bank_file_sha256']),
        ('bank_manifest',main/'bank/run_manifest.json',c['bank_manifest_sha256'])):
        require(not path.is_symlink() and sha(path) == wanted, 'immutable G3/bank binding: ' + key)
        hashes[key] = wanted
    require(not (main/'score').exists() and not (main/'score').is_symlink(), 'main score output already present')
    return dict(hashes, source=digest(json.dumps(snapshot,sort_keys=True).encode()),
                input_manifest=c['input_manifest']['sha256'], aliases=dict(manifest['namespace_aliases']),
                catalogues={path:sha(path) for path in CATALOGUES})


def validate_full_score(parameters):
    c = parameters; score_arguments(c)
    base_fields = set(decode((Path(__file__).parent/'parameters.template.json').read_bytes()))
    require(set(c) == base_fields | {'actual_CPU_job_id','actual_future_GPU_job_id','packet_manifest_sha256',
        'phase_request_sha256','phase_deadline_unix','evidence_output'}, 'closed owning parameters')
    require(all(value is not None for value in c.values()), 'unbound owning parameters')
    require(c['root_source_review_accepted'] is True, 'accepted independent source review required')
    require(os.environ.get('CUDA_VISIBLE_DEVICES','') == '' and os.environ.get('SLURM_CLUSTER_NAME') == 'delta'
            and os.environ.get('SLURM_JOB_ID') == c['actual_CPU_job_id'], 'actual Delta CPU context')
    runtime = Path(c['accepted_runtime'])
    require(str(runtime) == W + '/outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime',
            'exact source50e runtime')
    current = catalogue_expectations(c['current_catalogue_witness'], c['packet_manifest_sha256'], c['actual_CPU_job_id'])
    snapshot = bound(c['accepted_source_snapshot']); manifest = bound(c['input_manifest'])
    before = capture_identities(c)
    os.chdir(str(runtime)); sys.path.insert(0,str(runtime))
    p = importlib.import_module('component_analysis.a2_pipeline'); origins(runtime)
    native = validate_native_context(c,p)
    prepared, receipt, banks = (native.pop('_prepared'),native.pop('_receipt'),native.pop('_banks'))
    args = native.pop('_args')
    require(p.hash_content(banks) == c['bank_internal_payload_sha256'], 'native bank payload identity')
    old = p.a1.read_artifact(c['historical_G2']['path'])
    provenance = {'execution_commit','file_references','grader_registry','receipt_sha256','registry_hashes','runtime_code_hashes','utility_registry_hashes'}
    require(set(old) == set(SCIENCE_FIELDS)|provenance and set(receipt) == set(old)|{'grader_binding'}, 'exact G2/G3 schema')
    for field in SCIENCE_FIELDS: require(old[field] == receipt[field], 'immutable G2/G3 science: ' + field)
    proof = bound(c['full_domain_proof'])
    require(proof['source_commit'] == SOURCE and proof['model_loaded'] is False
            and proof['bank_sha256'] == c['bank_file_sha256'], 'accepted genuine domain proof identity')
    mask, reconstructed_controls = reconstruct_domain(p,prepared,receipt)
    domain = validate_domain_identity(p.expected_keys(receipt,0), p.a1.positive_keys(p._prepared_domain(receipt),0),
                                      mask, reconstructed_controls, proof['full'])
    p._validate_live(args,receipt,prepared)
    after = capture_identities(c); require(before == after, 'source/input/G3/bank/catalogues changed during proof')
    captures = []
    for index, path in enumerate(CATALOGUES):
        raw = Path(path).read_bytes()
        require(digest(raw) == before['catalogues'][path], 'catalogue changed before immutable capture')
        target = Path(c['evidence_output'])/('catalogue-%d.json' % index)
        with target.open('xb') as stream: stream.write(raw)
        captures.append(dict(virtual_path=path,sha256=digest(raw),bytes=len(raw),captured_bytes_path=str(target)))
    require(capture_identities(c) == before, 'final source/catalogue capture drift')
    return dict(native, **domain, phase='full_score', complete=False, status='GUARDS_PASSED_AWAIT_SUPERVISOR',
        source_commit=SOURCE, actual_CPU_job_id=c['actual_CPU_job_id'],
        actual_future_GPU_job_id=c['actual_future_GPU_job_id'], request_sha256=c['phase_request_sha256'],
        source_before=before, source_after=after, module_origins=origins(runtime),
        groups_file_sha256=c['frozen_G3_sha256'], packet_manifest_sha256=c['packet_manifest_sha256'],
        current_catalogue_witness_sha256=c['current_catalogue_witness']['sha256'],
        catalogue_capture_files=captures, catalogues=[dict(virtual_path=r['virtual_path'],sha256=r['sha256']) for r in captures],
        stable_Delta_catalogues_before_after=True,actual_Delta_owning_guards_passed=True,
        assessment_effects_inspected=False)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--parameters',required=True); ap.add_argument('--parameters-sha256',required=True)
    a = ap.parse_args(); c = bound(dict(path=a.parameters,sha256=a.parameters_sha256))
    result = validate_full_score(c)
    require(time.time() < c['phase_deadline_unix'], 'late native proof cannot publish')
    with (Path(c['evidence_output'])/'guard-result.json').open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False); stream.write('\n')


if __name__ == '__main__': main()
