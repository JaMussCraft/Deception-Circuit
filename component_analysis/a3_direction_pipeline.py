"""CPU-only direction fit stage; no model dispatch, selection, or evaluation.

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
    for ti, (task, spec) in enumerate(design['tasks'].items()):
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
    expected_operational = dict(task_order=list(design['tasks']), stream_order=list(STREAMS),
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


def _metadata_features(design, task, ids):
    indexed = {(r['condition'],r['instance_id']):r for r in design['access_rows'][task]
               if r.get('split') == 'train' and r['instance_id'] in ids and r['condition'] in ('D','I')}
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
