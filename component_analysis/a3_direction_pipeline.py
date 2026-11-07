"""CPU-only direction fits and validation selection; no model dispatch.

Fit schema v1 (immutable scientific ``a3_direction_fit`` bundle): ``identity``
retains the capture's full ancestry/profile and adds its exact capture_reference.
``fit_records`` contains every frozen task/site/seed, including failed DOM,
nuisance, image_probe and metadata_probe receipts. ``valid`` means DOM fitted;
``blocked_task_seeds`` forbids downstream inference when a seed has no candidate.
``geometries`` maps stable content digests to one shared set of array references
(projection/U/pinv/spectrum). Per-fit ``arrays`` references hold v, pullback,
H center and weights; probe arrays hold train-only center/scale/coefficient.
No activation cache is copied into the fit bundle. Nulls and evaluation are later
stages and must use these frozen transforms, never refit or choose sites here.

Capture schema v1: protocol['fit_cache']['capture_identity'] freezes ancestry,
source closure and numeric profile before capture; membership and design/protocol
hashes are independently computed by _fit_contract. Capture arrays are
``geometry{site_union_index}_projection`` and
``t{task_index}_s{task_site_index}_{D,I,H,user_neutral}`` [id,stream,head].
The full expected capture metadata includes the derived ``cache_layout``.
Protocol ``fit_cache.probe_max_bytes`` bounds conservative peak probe storage.
The future stage adapter must publish this complete train capture via the strict
artifact writer; runner's transient sink payloads are not complete cache bundles.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import numpy as np
import torch

from component_analysis import a3_direction_artifacts as artifacts
from component_analysis import a3_directions as directions
from component_analysis import a3_design

require = artifacts.require
CONDITIONS = ('D', 'I', 'H', 'user_neutral')
STREAMS = ('clean', 'corrupt')
IDENTITY_SOURCE_FIELDS = ('commit', 'code_hashes', 'a1_identity', 'parent_evidence',
    'matched_source_hashes', 'grader_sha256', 'model', 'model_revision',
    'tokenizer_revision', 'tokenizer_identity', 'numeric_profile')


def _fit_contract(design, protocol):
    """Build expectations solely from trusted frozen inputs, never loaded cache."""
    require(design.get('seeds') == [42, 1, 123], 'fit requires all frozen seeds')
    contract = protocol.get('fit_cache', {})
    source = contract.get('capture_identity', {})
    require(set(source) == set(IDENTITY_SOURCE_FIELDS), 'incomplete frozen capture source identity')
    require(type(contract.get('probe_max_bytes')) is int and contract['probe_max_bytes'] > 0,
            'positive frozen probe byte limit required')
    require(source['commit'] == protocol.get('commit') and source['code_hashes'] == protocol.get('code_hashes'),
            'changed frozen capture source closure')
    for field in ('a1_identity', 'parent_evidence'):
        require(source[field] == design.get(field), 'changed frozen capture ' + field)
    injected = design.get('injected')
    require(type(injected) is bool and protocol.get('injected') is injected, 'changed injected provenance')
    rows, layout, ids, site_union = [], [], [], []
    require(isinstance(design.get('tasks'), dict) and design['tasks'], 'missing fit tasks')
    require(design.get('injected') is True or 'task_order' in protocol,'production requires frozen task_order')
    task_order=protocol.get('task_order',sorted(design['tasks']))
    require(len(task_order)==len(set(task_order)) and set(task_order)==set(design['tasks']),'changed frozen operational task_order')
    for ti, task in enumerate(task_order):
        spec=design['tasks'][task]
        task_ids = spec['fit_ids']; sites = spec['direction_sites']
        require(task_ids and len(set(task_ids)) == len(task_ids), 'duplicate/empty fit IDs')
        require(not set(task_ids) & (set(spec['selection_ids']) | set(spec['assessment_ids']) |
                                   set(design.get('selection_exclusion_ids', []))), 'fit ID split/exclusion collision')
        require(sites and len({tuple(s) for s in sites}) == len(sites), 'duplicate/empty fit sites')
        indexed = {}
        for row in design['access_rows'][task]:
            if row.get('instance_id') in task_ids and row.get('condition') in CONDITIONS:
                key = (row['condition'], row['instance_id'])
                require(key not in indexed and row.get('split') == 'train', 'duplicate/nontrain fit source')
                require(set(row['streams']) == set(STREAMS), 'fit source requires both exact streams')
                indexed[key] = row
        require(len(indexed) == len(task_ids)*len(CONDITIONS), 'incomplete fit source rows')
        task_rows = [copy.deepcopy(indexed[(c, rid)]) for c in CONDITIONS for rid in task_ids]
        clusters = [a3_design._pressure(indexed[('D', rid)]) for rid in task_ids]
        rows.append(dict(task=task, rows=task_rows))
        ids.extend(task_ids)
        for si, site in enumerate(sites):
            if site not in site_union:
                site_union.append(copy.deepcopy(site))
            layout.append(dict(task=task, site=copy.deepcopy(site), instance_ids=list(task_ids),
                cluster_ids=clusters, streams=list(STREAMS),
                activations={c:f't{ti}_s{si}_{c}' for c in CONDITIONS},
                projection=f'geometry{site_union.index(site)}_projection'))
    require(len(ids) == len(set(ids)), 'cross-task duplicate fit ID')
    core = {k:v for k,v in design.items() if k not in ('direction_protocol', 'direction_protocol_sha256')}
    expected_operational = dict(task_order=list(task_order), stream_order=list(STREAMS),
        seeds=list(design['seeds']), candidate_sites={t:v['direction_sites'] for t,v in design['tasks'].items()},
        design_sha256=artifacts.ladder.design._hash(core))
    for field, value in expected_operational.items():
        require(field not in protocol or protocol[field] == value, 'changed frozen operational ' + field)
    require('direction_protocol' not in design or design['direction_protocol'] == protocol,
            'changed frozen attached direction protocol')
    require('direction_protocol_sha256' not in design or
            design['direction_protocol_sha256'] == artifacts.ladder.design._hash(protocol),
            'changed frozen direction protocol digest')
    identity = dict(copy.deepcopy(source), analysis_split='train', injected=injected,
        design_sha256=artifacts.ladder.design._hash(core), protocol_sha256=artifacts.ladder.design._hash(protocol),
        ordered_ids=ids, streams=list(STREAMS), conditions=list(CONDITIONS), sites=site_union,
        row_identity_sha256=artifacts.ladder.design._hash(rows), capture_lineage=[])
    metadata = dict(schema_version=1, kind='a3_readout_chunk', split='train', injected=injected,
                    identity=identity, cache_schema_version=1, cache_layout=layout)
    artifacts.validate_scientific_metadata(metadata)
    return metadata, layout


def _tensor(array):
    # Portable cache is read-only mmap; own CPU storage before using torch.
    require(array.dtype.kind == 'f', 'floating fit array required')
    return torch.from_numpy(np.array(array, dtype=np.float32, copy=True))


def _put(arrays, prefix, values, names):
    refs = {}
    for name in names:
        value = values[name]
        if isinstance(value, torch.Tensor):
            value = value.detach().cpu().numpy()
        array = np.array(value, copy=True)
        require(np.isfinite(array).all(), 'nonfinite fitted array')
        key = prefix + '_' + name
        arrays[key] = array
        refs[name] = key
    return refs


def _bootstrap(cluster_ids, ids, seed):
    weights, receipt = directions._cluster_weights(cluster_ids, ids, len(ids), seed)
    return weights, {k:v for k,v in receipt.items() if k != 'id_weights'}


def _axis_fit(fn, d, i, h, projection, *, seed, layout, bootstrap, arrays, prefix):
    try:
        fitted = fn(d, i, h, projection, seed=seed,
                    cluster_ids=layout['cluster_ids'], instance_ids=layout['instance_ids'])
        receipt = dict(status='fitted', bootstrap=bootstrap,
            arrays=_put(arrays, prefix, fitted, ('v', 'pullback', 'h_center', 'id_weights')),
            raw_norm=fitted['raw_norm'], projected_variance=fitted['projected_variance'],
            sigma_fit=fitted['sigma_fit'], rank=fitted['rank'])
        return receipt, fitted
    except (ValueError, RuntimeError, FloatingPointError) as error:
        return dict(status='unfitted', reason=str(error), bootstrap=bootstrap), None


def _metadata_features(design, task, ids, *, split="train"):
    require(split in ("train","validation","assessment"),"unknown probe source split")
    source_split="test" if split=="assessment" else split
    indexed = {(r['condition'],r['instance_id']):r for r in design['access_rows'][task]
               if r.get('split') == source_split and r['instance_id'] in ids and r['condition'] in ('D','I')}
    values = []
    for condition in ('D','I'):
        cohort = []
        for rid in ids:
            stream_values = []
            for stream in STREAMS:
                record = indexed[(condition,rid)]['streams'][stream]
                n = len(record['tokens']); request = record.get('user_request_span', [])
                roles = (record.get('layout') or {}).get('content_spans', [])
                stream_values.append([n, request[1]-request[0] if request else 0,
                    request[0] if request else 0,
                    sum(b-a for name,a,b in roles if name == 'user'),
                    sum(b-a for name,a,b in roles if name == 'system'), record.get('readout',n-1)])
            cohort.append(stream_values)
        values.append(torch.tensor(cohort, dtype=torch.float32))
    return values


def _probe_preflight(n_ids, n_streams, features, expanded_n, *, head_width=0):
    n = expanded_n*n_streams*2
    # Conservative live fp32 copies, standardization, solve/Gram workspace and
    # labels/indices; includes original image coordinates and paired expansion.
    return dict(expanded_examples=n, features=features,
        estimated_peak_bytes=4*(8*n*features + 8*features*features + 8*n + 4*n_ids*n_streams*features + 4*head_width*features),
        dtype='float32', one_fit_at_a_time=True)


def _probe_fit(coordinates, *, geometry, projection, features, layout, bootstrap,
               max_bytes, arrays, prefix):
    width = geometry['rank'] if geometry is not None else 6
    preflight = _probe_preflight(len(layout['instance_ids']), len(STREAMS), width, bootstrap['expanded_n'],
        head_width=projection.shape[1] if projection is not None else 0)
    receipt = dict(bootstrap=bootstrap, **preflight)
    try:
        require(preflight['estimated_peak_bytes'] <= max_bytes, 'probe byte preflight exceeds frozen limit')
        if coordinates is not None:
            require(geometry is not None, 'unfitted image geometry')
            # Associate the small head-to-image map first; never materialize
            # an [id,stream,residual_width] probe intermediate.
            transform = projection.T @ geometry['U']
            d, i = [x @ transform for x in coordinates]
        else:
            d, i = features
        counts = bootstrap['cluster_multiplicities']
        multiplicities = torch.tensor([counts.get(c,0) for c in layout['cluster_ids']], dtype=torch.int64)
        indices = torch.repeat_interleave(torch.arange(len(multiplicities)), multiplicities)
        expanded = torch.cat((d[indices].reshape(-1,width), i[indices].reshape(-1,width)))
        labels = torch.cat((torch.ones(len(expanded)//2), -torch.ones(len(expanded)//2)))
        probe = directions.fit_ridge_probe(expanded, labels)
        receipt.update(status='fitted', arrays=_put(arrays,prefix,probe,('center','scale','coefficient')),
                       intercept=probe['intercept'], regularization=probe['regularization'])
    except (ValueError, RuntimeError, FloatingPointError) as error:
        receipt.update(status='failed', reason=str(error))
    return receipt


def fit_from_cache(design: dict, cache_path, *, protocol: dict, output) -> dict:
    """Fit every frozen train candidate; publish even blocked/failed receipts.

    Return the complete output metadata, usable as strict read_bundle expected.
    Does not read validation/assessment caches, score probes or select sites.
    Noninjected captures still require the complete current runtime source closure.
    """
    expected, layout = _fit_contract(design, protocol)
    metadata, cached = artifacts.read_bundle(cache_path, expected=expected)
    reference = artifacts.capture_reference(cache_path, expected=expected)
    names = {item['projection'] for item in layout}
    names.update(name for item in layout for name in item['activations'].values())
    require(set(cached) == names, 'incomplete/unexpected train cache array coverage')
    # All structural cache errors reject before any fit or publication.
    for item in layout:
        projection = cached[item['projection']]
        require(projection.ndim == 2 and projection.dtype.kind == 'f', 'invalid projection shape/dtype')
        shape = (len(item['instance_ids']), len(STREAMS), projection.shape[1])
        require(all(cached[name].shape == shape and cached[name].dtype.kind == 'f'
                    for name in item['activations'].values()), 'invalid paired train activation shapes')
    arrays, geometries, records = {}, {}, []
    site_geometries = {}
    for li, item in enumerate(layout):
        projection = _tensor(cached[item['projection']])
        site_key = tuple(item['site'])
        if site_key not in site_geometries:
            digest = hashlib.sha256(np.asarray(cached[item['projection']]).tobytes() +
                                    repr(projection.shape).encode()).hexdigest()
            gid = 'geometry_' + digest
            if gid not in geometries:
                try:
                    geometry = directions.image_geometry(projection)
                    refs = _put(arrays, gid, geometry, ('projection','U','pinv','spectrum'))
                    geometries[gid] = dict(status='fitted', arrays=refs, rank=geometry['rank'], rank_rtol=geometry['rank_rtol'])
                except (ValueError, RuntimeError) as error:
                    geometry = None
                    # Finite failed projections remain in the source cache; no fabricated SVD.
                    geometries[gid] = dict(status='unfitted', reason=str(error), source_array=item['projection'])
            else:
                g = geometries[gid]
                geometry = None if g['status'] != 'fitted' else dict(
                    rank=g['rank'], **{name:torch.from_numpy(arrays[ref]) for name,ref in g['arrays'].items()})
            site_geometries[site_key] = (gid, geometry)
        gid, geometry = site_geometries[site_key]
        d, i, h, neutral = [_tensor(cached[item['activations'][c]]) for c in CONDITIONS]
        features = _metadata_features(design, item['task'], item['instance_ids'])
        for seed in design['seeds']:
            _, bootstrap = _bootstrap(item['cluster_ids'], item['instance_ids'], seed)
            prefix = f'fit{li}_seed{seed}'
            dom, fitted = _axis_fit(directions.fit_direction,d,i,h,projection,seed=seed,layout=item,
                                   bootstrap=bootstrap,arrays=arrays,prefix=prefix+'_dom')
            nuisance, nf = _axis_fit(directions.fit_nuisance_direction,h,neutral,h,projection,seed=seed,layout=item,
                                    bootstrap=bootstrap,arrays=arrays,prefix=prefix+'_nuisance')
            cosine = directions.direction_cosine(fitted,nf) if fitted is not None and nf is not None else None
            image_probe = _probe_fit((d,i),geometry=geometry,projection=projection,features=None,
                layout=item,bootstrap=bootstrap,max_bytes=protocol['fit_cache']['probe_max_bytes'],arrays=arrays,prefix=prefix+'_image_probe')
            metadata_probe = _probe_fit(None,geometry=None,projection=None,features=features,
                layout=item,bootstrap=bootstrap,max_bytes=protocol['fit_cache']['probe_max_bytes'],arrays=arrays,prefix=prefix+'_metadata_probe')
            records.append(dict(task=item['task'],site=item['site'],seed=seed,geometry=gid,
                valid=fitted is not None,status='fitted' if fitted is not None else 'unfitted',
                dom=dom,nuisance=nuisance,nuisance_cosine=cosine,image_probe=image_probe,metadata_probe=metadata_probe))
            del fitted, nf
        del d, i, h, neutral, features
    blocked = [dict(task=task,seed=seed,reason='no finite valid DOM candidate')
        for task in design['tasks'] for seed in design['seeds']
        if not any(r['task']==task and r['seed']==seed and r['valid'] for r in records)]
    identity = copy.deepcopy(metadata['identity'])
    identity['capture_lineage'] = [reference]
    result = dict(schema_version=1, kind='a3_direction_fit', split='train', injected=metadata['injected'],
        identity=identity, fit_schema_version=1, fit_records=records, geometries=geometries,
        blocked_task_seeds=blocked, status='blocked' if blocked else 'fitted',
        train_cache=dict(path=str(Path(cache_path).resolve()),reference=reference),
        probe_feature_names=list(design.get('confounds',{}).get('feature_names',
            ['prompt_length','request_length','request_position','user_content_length','system_content_length','readout_position'])),
        probe_policy=dict(labels={'D':1,'I':-1},regularization=1,train_standardization=True,
                          diagnostic_only=True,site_selection=False,probe_max_bytes=protocol['fit_cache']['probe_max_bytes']))
    artifacts.write_bundle(output,result,arrays)
    return result


def _select_candidates(records, summaries, *, task, seed):
    """Retain every failed candidate; pass only finite summaries to reviewed core."""
    import math
    relevant = [r for r in records if r['task'] == task and r['seed'] == seed]
    indexed = {tuple(r['site']): r for r in summaries}
    require(len(indexed) == len(summaries), 'duplicate validation summary')
    usable, failures = [], []
    for record in relevant:
        site = record['site']
        if not record['valid']:
            failures.append(dict(task=task, seed=seed, site=site, reason='unfitted DOM', fit_receipt=record))
            continue
        require(tuple(site) in indexed, 'missing fitted validation candidate')
        row = indexed.pop(tuple(site))
        require(row.get('seed') == seed and row.get('split') == 'validation', 'selection requires validation only')
        if not all(type(row.get(k)) in (int, float) and math.isfinite(row[k]) for k in ('D_fraction', 'I_fraction')):
            failures.append(dict(task=task, seed=seed, site=site, reason='nonfinite validation fraction'))
        else:
            usable.append(row)
    require(not indexed, 'unexpected validation candidate')
    if not usable:
        return None, failures
    return directions.select_direction(usable, sites=[r['site'] for r in usable], seed=seed), failures


def _store_selection_axis(axis, *, reference, arrays, **extra):
    from component_analysis.a3_direction_runner import axis_identity
    receipt = dict(arrays=_put(arrays, reference, axis, ('v', 'pullback', 'h_center', 'id_weights')),
        sigma_fit=axis['sigma_fit'], projected_variance=axis['projected_variance'],
        geometry_rank=axis['rank'], sha256=axis_identity(axis), **extra)
    return dict(reference=reference, sha256=receipt['sha256']), receipt


def _freeze_null_axes(projection, h, weights, *, seed, prefix, arrays):
    panels, axes = [], {}
    for family, n, seed_argument in (('assessment', 199, seed), ('calibration', 32, 21000 + seed)):
        descriptors = []
        values = directions.random_image_directions(projection, n=n, seed=seed_argument)
        for index, value in enumerate(values):
            axis = directions.prepare_image_direction(projection, value, h, id_weights=weights)
            descriptor, receipt = _store_selection_axis(axis, reference=f'{prefix}_{family}{index}',
                arrays=arrays, rng_seed=10000 + seed_argument, rng_argument=seed_argument)
            descriptor['axis_index'] = index
            axes[descriptor['reference']] = receipt
            descriptors.append(descriptor)
        panels.append(descriptors)
    return panels[0], panels[1], axes


def _bundle_byte_reference(path):
    """Link a complete immutable directory's marker and every child byte."""
    root = Path(path)
    marker = artifacts._complete(root)
    return dict(path=str(root.resolve()), completion_sha256=artifacts.common.file_hash(root/'COMPLETE.json'),
        completion_bytes=(root/'COMPLETE.json').stat().st_size, files=marker['files'])


def _read_selection_fits(design, protocol, fits_path):
    expected, layout = _fit_contract(design, protocol)
    # Outcomes are not expected source identity. Check that identity independently
    # before giving the full manifest to the exact structural/byte reader.
    artifacts._complete(Path(fits_path))
    manifest = artifacts._strict_json(Path(fits_path)/'manifest.json')
    meta = manifest.get('metadata', {})
    require(meta.get('kind') == 'a3_direction_fit' and meta.get('fit_schema_version') == 1,
            'complete direction fit bundle required')
    cache = meta.get('train_cache', {})
    require(isinstance(cache.get('path'), str), 'missing fit train capture')
    reference = artifacts.capture_reference(cache['path'], expected=expected)
    identity = copy.deepcopy(expected['identity']); identity['capture_lineage'] = [reference]
    require(meta.get('identity') == identity and cache.get('reference') == reference,
            'changed fit/capture ancestry')
    meta, arrays = artifacts.read_bundle(fits_path, expected=meta)
    records = meta.get('fit_records', [])
    wanted = {(r['task'], tuple(r['site']), seed) for r in layout for seed in design['seeds']}
    actual = [(r['task'], tuple(r['site']), r['seed']) for r in records]
    require(len(actual) == len(set(actual)) and set(actual) == wanted, 'incomplete fit candidate coverage')
    for row in records:
        require(type(row.get('valid')) is bool and row['valid'] == (row.get('dom', {}).get('status') == 'fitted'),
                'inconsistent DOM fit status')
    blocked = [dict(task=t, seed=s, reason='no finite valid DOM candidate')
        for t in design['tasks'] for s in design['seeds']
        if not any(r['task'] == t and r['seed'] == s and r['valid'] for r in records)]
    require(meta.get('blocked_task_seeds') == blocked, 'changed fit blockers')
    _, captures = artifacts.read_bundle(cache['path'], expected=expected)
    by_site = {(r['task'], tuple(r['site'])):r for r in layout}
    validated_geometry = {}
    for row in records:
        source_layout = by_site[(row['task'], tuple(row['site']))]
        key = (row['geometry'], source_layout['projection'])
        if key not in validated_geometry:
            validated_geometry[key] = _validate_shared_geometry(meta['geometries'][row['geometry']], arrays,
                _tensor(captures[source_layout['projection']]))
        _validate_fit_bootstrap_h(meta, arrays, row, source_layout,
            _tensor(captures[source_layout['activations']['H']]), validated_geometry[key])
    return meta, arrays, captures, layout


def _validate_shared_geometry(receipt, arrays, source_projection):
    """Check the complete image/inverse, including unlearned directions.

    Compare the full source-derived inverse/spectrum and image subspace, while
    allowing orthonormal basis rotations/signs inside that same retained image.
    """
    try:
        expected = directions.image_geometry(source_projection)
    except (ValueError, RuntimeError, FloatingPointError):
        require(receipt.get('status') == 'unfitted', 'invalid shared geometry fit status')
        return None
    require(receipt.get('status') == 'fitted' and type(receipt.get('rank')) is int
            and receipt['rank'] == expected['rank'] and receipt.get('rank_rtol') == expected['rank_rtol'],
            'changed shared geometry rank/cutoff')
    refs = receipt.get('arrays', {})
    require(set(refs) == {'projection','U','pinv','spectrum'}, 'incomplete shared geometry arrays')
    actual = {name:_tensor(arrays[ref]) for name,ref in refs.items()}
    require(actual['projection'].shape == source_projection.shape
            and torch.equal(actual['projection'], source_projection),
            'changed fit geometry versus source site projection')
    require(all(actual[name].shape == expected[name].shape for name in ('U','pinv','spectrum')),
            'changed shared geometry shapes')
    require(all(bool(torch.isfinite(value).all()) for value in actual.values()),
            'nonfinite shared geometry')
    u = actual['U']; canonical_u = expected['U']
    require(torch.allclose(u.T @ u, torch.eye(expected['rank'], dtype=u.dtype), atol=2e-6, rtol=2e-6)
            and torch.allclose(canonical_u @ (canonical_u.T @ u), u, atol=2e-6, rtol=2e-6),
            'changed shared geometry orthonormal image')
    require(torch.allclose(actual['spectrum'], expected['spectrum'], atol=2e-6, rtol=2e-6)
            and torch.allclose(actual['pinv'], expected['pinv'], atol=2e-6, rtol=2e-6),
            'changed shared geometry spectrum/pseudoinverse')
    return expected


def _validate_fit_bootstrap_h(fits, arrays, record, layout, h, geometry):
    """Seed/cluster-derived bootstrap and H checks; never refit a learned axis."""
    import math
    weights, bootstrap = _bootstrap(layout['cluster_ids'], layout['instance_ids'], record['seed'])
    for family in ('dom','nuisance','image_probe','metadata_probe'):
        require(record.get(family, {}).get('bootstrap') == bootstrap,
                'changed fit bootstrap receipt '+family)
    for family in ('dom','nuisance'):
        if record[family]['status'] != 'fitted':
            continue
        require(geometry is not None, 'fitted axis requires valid shared geometry')
        axis = _loaded_fit_axis(fits, arrays, record, family)
        require(axis['id_weights'].shape == weights.shape and torch.equal(axis['id_weights'], weights),
                'changed fit bootstrap weights '+family)
        require(h.shape == (len(layout['instance_ids']), len(STREAMS), geometry['projection'].shape[1]),
                'changed train H statistics source shape')
        center_h = (h.mean(1) * weights[:,None]).sum(0)
        coordinates = (h @ geometry['projection'].T) @ axis['v']
        center = (coordinates.mean(1) * weights).sum()
        variance = float(((coordinates-center).square().mean(1) * weights).sum())
        sigma = math.sqrt(variance)
        require(torch.allclose(axis['h_center'], center_h, atol=2e-6, rtol=2e-6)
                and math.isclose(axis['projected_variance'], variance, abs_tol=2e-6, rel_tol=2e-6)
                and math.isclose(axis['sigma_fit'], sigma, abs_tol=2e-6, rel_tol=2e-6),
                'changed train H statistics '+family)


def _loaded_fit_axis(fits, arrays, record, family):
    import math
    receipt = record[family]
    require(receipt.get('status') == 'fitted', 'unfitted axis')
    names = ('v', 'pullback', 'h_center', 'id_weights')
    refs = receipt.get('arrays')
    require(isinstance(refs, dict) and set(refs) == set(names), 'invalid fit-axis arrays schema')
    geometry = fits['geometries'][record['geometry']]
    require(geometry.get('status') == 'fitted', 'unfitted selected geometry')
    axis = {name: _tensor(arrays[ref]) for name, ref in geometry['arrays'].items()}
    axis.update({name: _tensor(arrays[refs[name]]) for name in names})
    axis.update(rank=geometry['rank'], sigma_fit=receipt['sigma_fit'], projected_variance=receipt['projected_variance'])
    require(all(math.isfinite(float(axis[k])) and axis[k] >= 0 for k in ('sigma_fit', 'projected_variance')),
            'invalid fit H variance')
    require(abs(axis['sigma_fit']**2-axis['projected_variance']) <= 1e-5*max(1, axis['projected_variance']),
            'inconsistent fit H sigma')
    v = axis['v']; projection = axis['projection']
    require(v.shape == (projection.shape[0],) and axis['pullback'].shape == (projection.shape[1],)
            and axis['h_center'].shape == (projection.shape[1],), 'invalid selected axis geometry')
    require(torch.allclose(v.norm(), torch.tensor(1.), atol=2e-6, rtol=2e-6)
            and torch.allclose(axis['U'] @ (axis['U'].T @ v), v, atol=2e-6, rtol=2e-6)
            and torch.allclose(axis['pinv'] @ v, axis['pullback'], atol=2e-6, rtol=2e-6),
            'changed selected axis/image geometry')
    return axis


def _selection_source_record(source, stream, source_task):
    """Exact provenance built by ladder batches, independently of scored rows."""
    record = copy.deepcopy(source)
    saved = record['streams'][stream]
    if source_task not in ('ioi', 'mmlu'):
        for key in ('expected_token', 'honest_token', 'opposite_token'):
            if key in saved:
                record[key] = saved[key]
    record.update(tokens=copy.deepcopy(saved['tokens']), layout=copy.deepcopy(saved.get('layout')),
                  utility_assessment=stream == 'clean')
    return record


def _selection_sources(design, task):
    if task in ('ioi', 'mmlu'):
        rows = copy.deepcopy(design[task+'_validation'])
        require(rows and (task != 'mmlu' or len(rows) == 32), 'missing full validation utility')
        if not design['injected'] and task == 'ioi':
            require(len(rows) == 100, 'validation IOI requires full frozen membership')
        ids = [r['instance_id'] for r in rows]
        require(len(ids) == len(set(ids)), 'duplicate validation utility ID')
        for row in rows:
            require(row.get('analysis_split', row.get('split')) == 'validation', 'validation utility split required')
            require(row.get('condition') == task.upper() and 'clean' in row.get('streams', {}),
                    'invalid validation utility condition/stream')
        fixed = design.get('utility', {}).get(task, [])
        fixed_ids, fixed_prompts = set(), set()
        for row in fixed:
            source_ids, prompts = a3_design._utility_identity(row)
            fixed_ids.update(source_ids); fixed_prompts.update(prompts)
        for row in rows:
            source_ids, prompts = a3_design._utility_identity(row)
            require(not source_ids & fixed_ids and not prompts & fixed_prompts,
                    'validation/assessment utility collision')
        return rows
    spec = design['tasks'][task]; ids = spec['selection_ids']
    require(ids and len(ids) == len(set(ids)), 'empty/duplicate selection IDs')
    require(not set(ids) & (set(spec['fit_ids']) | set(spec['assessment_ids']) |
                            set(design.get('selection_exclusion_ids', []))), 'selection ID exclusion collision')
    rows = [copy.deepcopy(r) for r in design['access_rows'][task] if r.get('instance_id') in ids]
    index = {(r['condition'], r['instance_id']): r for r in rows}
    conditions = ('D', 'H', 'F', 'I', 'user_neutral')
    require(len(index) == len(rows) == len(ids)*5 and set(index) == {(c,i) for c in conditions for i in ids},
            'incomplete validation source membership')
    for row in rows:
        require(row.get('split') == 'validation' and set(row.get('streams', {})) == set(STREAMS),
                'invalid validation source split/streams')
    return [index[(c, i)] for c in conditions for i in ids]


def _selection_layout(design, protocol, fits):
    """Operational per-profile shard layout; F must freeze it before execution.

    selection_cache.groups freezes group_id, analysis_task, source_task, site,
    numeric_profile and rows_per_shard. No expected row keys come from caches.
    Group capture is <root>/<group>/capture; shards live under <group>/shards.
    This is an explicit fixture adapter until the canonical F producer exists.
    """
    import re
    for field, count in (('assessment_orientations', 199), ('calibration_orientations', 32)):
        require(field not in protocol or protocol[field] == count, 'changed frozen null count '+field)
    groups = protocol.get('selection_cache', {}).get('groups')
    require(isinstance(groups, list), 'frozen per-profile selection_cache groups required')
    expected_scopes = {(t, source, tuple(site)) for t,spec in design['tasks'].items()
        for site in spec['direction_sites'] for source in (t, 'ioi', 'mmlu')}
    seen, names, layout = set(), set(), []
    for raw in groups:
        require(set(raw) == {'group_id','analysis_task','source_task','site','numeric_profile','rows_per_shard'},
                'invalid validation-only selection group')
        group = copy.deepcopy(raw)
        name = group['group_id']; task = group['analysis_task']; source = group['source_task']; site = group['site']
        require(isinstance(name, str) and re.fullmatch('[A-Za-z][A-Za-z0-9_-]*', name) and name not in names,
                'invalid/duplicate validation group')
        names.add(name); scope = (task, source, tuple(site))
        require(scope in expected_scopes and scope not in seen, 'changed/duplicate validation scope')
        seen.add(scope)
        profile = group['numeric_profile']; artifacts.validate_numeric_profile(profile)
        capture_source = protocol['fit_cache']['capture_identity']
        require(profile['model'] == capture_source['model'] and profile['model_revision'] == capture_source['model_revision']
                and profile['source_sha256'] == artifacts.ladder.design._hash(protocol['code_hashes']),
                'changed validation profile source/model')
        require(type(group['rows_per_shard']) is int and group['rows_per_shard'] > 0,
                'positive frozen shard size required')
        records = [r for r in fits['fit_records'] if r['task'] == task and r['site'] == site and r['valid']]
        sources = _selection_sources(design, source)
        group['sources'] = {(r['condition'], r['instance_id']): r for r in sources}
        streams = list(STREAMS) if source not in ('ioi', 'mmlu') else ['clean']
        conditions = list(dict.fromkeys(r['condition'] for r in sources))
        ids = list(dict.fromkeys(r['instance_id'] for r in sources))
        identity = copy.deepcopy(capture_source)
        identity.update(analysis_split='validation', injected=design['injected'],
            design_sha256=fits['identity']['design_sha256'], protocol_sha256=artifacts.ladder.design._hash(protocol),
            ordered_ids=ids, streams=streams, conditions=conditions, sites=[site],
            row_identity_sha256=artifacts.ladder.design._hash(sources), capture_lineage=[], numeric_profile=profile)
        group['capture_metadata'] = dict(schema_version=1, kind='a3_readout_chunk', split='validation',
            injected=design['injected'], identity=identity, cache_schema_version=1,
            selection_capture_scope=dict(analysis_task=task, source_task=source, site=site))
        artifacts.validate_scientific_metadata(group['capture_metadata'])
        keys = []
        operations = ['zero', 'h_mean'] if source == 'mmlu' else ['interchange']
        for record in records:
            for operation in operations:
                for row in sources:
                    for stream in streams:
                        keys.append(('validation',task,source,'validation',record['seed'],tuple(site),'learned',0,
                                     operation,row['instance_id'],row['condition'],stream))
        size = group['rows_per_shard']
        group['shards'] = [dict(shard_id=f'shard{j//size:06d}', expected_keys=keys[j:j+size])
                           for j in range(0, len(keys), size)]
        group['expected_keys'] = keys
        if keys:
            layout.append(group)
    require(seen == expected_scopes, 'incomplete validation profile scope coverage')
    return layout


def _read_selection_validation(design, protocol, fits, fit_arrays, validation_root, fit_reference):
    from component_analysis.a3_direction_runner import axis_identity
    all_rows, references = [], []
    axis_hashes = {(r['task'], tuple(r['site']), r['seed']):
        axis_identity(_loaded_fit_axis(fits, fit_arrays, r, 'dom'))
        for r in fits['fit_records'] if r['valid']}
    for group in _selection_layout(design, protocol, fits):
        root = Path(validation_root)/group['group_id']
        capture = artifacts.capture_reference(root/'capture', expected=group['capture_metadata'])
        identity = copy.deepcopy(group['capture_metadata']['identity']); identity['capture_lineage'] = [capture]
        inventory = dict(identity=identity, shards=group['shards'])
        rows = artifacts.read_completed_shards(inventory, root/'shards', identity=identity)
        artifacts._coverage(rows, group['expected_keys'])
        for shard in group['shards']:
            path = root/'shards'/shard['shard_id']
            manifest = artifacts._strict_json(path/'run_manifest.json')
            require(manifest.get('execution', {}).get('fit_reference') == fit_reference,
                    'changed validation fit byte linkage')
            references.append(dict(group_id=group['group_id'], capture=capture,
                capture_bundle=_bundle_byte_reference(root/'capture'), shard=_bundle_byte_reference(path)))
        for row in rows:
            source = group['sources'][(row['condition'], row['instance_id'])]
            require(row.get('source_provenance') == _selection_source_record(source, row['stream'], row['source_task']),
                    'changed validation source bytes/tokens/readouts/labels')
            require(row.get('numeric_profile') == group['numeric_profile'], 'changed validation scoring profile')
            expected_axis = axis_hashes[(row['analysis_task'], tuple(row['site']), row['seed'])]
            require(row.get('axis_hash') == expected_axis, 'changed validation axis/site')
            require(all(type(row.get(k)) is bool for k in ('supported','replay_valid','gate_valid'))
                    and type(row.get('positive_control', {}).get('valid')) is bool,
                    'missing validation support/replay evidence')
            require(row['gate_valid'] == (row['supported'] and row['replay_valid'] and row['positive_control']['valid']),
                    'inconsistent validation gate evidence')
        all_rows.extend(rows)
    return all_rows, references


def _portable_validation(value):
    """JSON cannot encode NaN; failed fractions stay explicit unavailable values."""
    import math
    if isinstance(value, dict):
        return {k:_portable_validation(v) for k,v in value.items()}
    if isinstance(value, list):
        return [_portable_validation(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _selection_protocol_reference(protocol, protocol_path, *, injected, expected=None):
    """Canonical envelope plus exact file bytes; reference sits outside payload."""
    if protocol_path is None:
        require(injected is True and expected is None, 'production selection requires protocol_path')
        return None
    path = Path(protocol_path)
    require(path.is_file() and not path.is_symlink(), 'canonical protocol file required')
    envelope = artifacts._strict_json(path)
    digest = artifacts.ladder.design._hash(protocol)
    require(set(envelope) == {'payload', 'sha256'} and envelope['payload'] == protocol
            and envelope['sha256'] == digest, 'changed canonical protocol envelope/payload')
    reference = dict(path=str(path.resolve()), file_sha256=artifacts.common.file_hash(path),
                     bytes=path.stat().st_size, payload_sha256=digest)
    require(expected is None or reference == expected, 'changed canonical protocol file bytes')
    return reference


def freeze_selection(design: dict, fits_path, validation_root, *, protocol: dict, output,
                     protocol_path=None) -> dict:
    """Freeze validation choice and all axes before any assessment outcomes.

    Scientific identity's train split describes FIT/CAPTURE ANCESTRY only.
    selection_split='validation' and byte-linked validation evidence are mandatory;
    this artifact must never be described as train-only site selection. Unit F's
    canonical protocol/capture producer is required before production execution.
    """
    from component_analysis.a3_direction_runner import direction_point_metrics
    from component_analysis.a3_direction_workload import inventory_identity
    protocol_reference = _selection_protocol_reference(protocol, protocol_path, injected=design.get('injected'))
    fits, fit_arrays, captures, fit_layout = _read_selection_fits(design, protocol, fits_path)
    fit_reference = _bundle_byte_reference(fits_path)
    rows, references = _read_selection_validation(design, protocol, fits, fit_arrays, validation_root, fit_reference)
    summaries = []
    for record in fits['fit_records']:
        if not record['valid']:
            continue
        subset = [r for r in rows if r['analysis_task'] == record['task'] and r['seed'] == record['seed']
                  and r['site'] == record['site']]
        metrics = direction_point_metrics(subset, seed=record['seed'], require_mmlu=True)
        summaries.append(dict(metrics, site=record['site'], split='validation', task=record['task']))
    arrays, axes, selected, blocked, failures = {}, {}, [], [], []
    for geometry in fits['geometries'].values():
        for ref in geometry.get('arrays', {}).values():
            arrays[ref] = np.array(fit_arrays[ref], copy=True)
    layout_index = {(r['task'], tuple(r['site'])): r for r in fit_layout}
    for task in design['tasks']:
        for seed in design['seeds']:
            candidates = [r for r in summaries if r['task'] == task and r['seed'] == seed]
            choice, failed = _select_candidates(fits['fit_records'], candidates, task=task, seed=seed)
            failures.extend(failed)
            if choice is None:
                blocked.append(dict(task=task, seed=seed, reason='no usable finite validation DOM candidate'))
                continue
            record = next(r for r in fits['fit_records'] if r['task'] == task and r['seed'] == seed and r['site'] == choice['site'])
            prefix = f'selected{len(selected)}'
            dom = _loaded_fit_axis(fits, fit_arrays, record, 'dom')
            descriptor, receipt = _store_selection_axis(dom, reference=prefix+'_learned', arrays=arrays)
            axes[descriptor['reference']] = dict(receipt, geometry=record['geometry'], fit_receipt=record['dom'])
            layout = layout_index[(task, tuple(record['site']))]
            h = _tensor(captures[layout['activations']['H']])
            assessment, calibration, null_axes = _freeze_null_axes(dom['projection'], h, dom['id_weights'],
                seed=seed, prefix=prefix, arrays=arrays)
            for value in null_axes.values(): value['geometry'] = record['geometry']
            axes.update(null_axes)
            nuisance = record['nuisance']
            if nuisance['status'] == 'fitted':
                nf = _loaded_fit_axis(fits, fit_arrays, record, 'nuisance')
                nd, nr = _store_selection_axis(nf, reference=prefix+'_nuisance', arrays=arrays)
                axes[nd['reference']] = dict(nr, geometry=record['geometry'], fit_receipt=nuisance)
                nuisance = dict(status='fitted', axis=nd)
            else:
                nuisance = dict(status='unfitted', reason=nuisance['reason'], fit_receipt=nuisance)
            selected.append(dict(task=task, seed=seed, site=record['site'], geometry=record['geometry'],
                learned_axis=descriptor, assessment_axes=assessment, calibration_axes=calibration,
                nuisance=nuisance, nuisance_cosine=record['nuisance_cosine'], selection=choice,
                image_probe=record['image_probe'], metadata_probe=record['metadata_probe'],
                steering=dict(signs=[-1,1], learned=descriptor, nuisance=nuisance.get('axis'), random=assessment[0]),
                inference='descriptive' if task == 'sdr_v2' else 'confirmatory'))
    result = dict(schema_version=1, kind='a3_direction_selection', split='train', selection_split='validation',
        identity=copy.deepcopy(fits['identity']), inventory_identity=inventory_identity(design, protocol),
        injected=design['injected'], selection_schema_version=1,
        status='blocked' if blocked else ('validation-failed' if any(r['selection']['validation_failure'] for r in selected) else 'selected'),
        selected_records=selected, axes=axes, geometries=copy.deepcopy(fits['geometries']),
        fit_reference=fit_reference, train_cache=copy.deepcopy(fits['train_cache']), protocol=copy.deepcopy(protocol),
        protocol_sha256=artifacts.ladder.design._hash(protocol), protocol_file_reference=protocol_reference,
        validation_references=references,
        validation_table=_portable_validation(summaries), candidate_failures=failures, blocked_task_seeds=blocked,
        analysis_split_scope='train fit/capture ancestry; selection used validation only',
        confirmatory_tasks=['far_v2','ser_v2'], descriptive_tasks=['sdr_v2'])
    _selection_protocol_reference(protocol, protocol_path, injected=design.get('injected'), expected=protocol_reference)
    artifacts.write_bundle(output, result, arrays)
    return result


def main(argv=None, *, tokenizer=None, model_loader=None):
    """Lazy dispatch; pure CPU fit/selection imports remain model-free."""
    from component_analysis.a3_direction_runtime import main as runtime_main
    return runtime_main(argv,tokenizer=tokenizer,model_loader=model_loader)


if __name__=='__main__':
    main()
