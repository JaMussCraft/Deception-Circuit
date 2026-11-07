"""Pure CPU A3 direction math; no model, split selection, or inferential claims.

Callers supply eligible train captures in the SAME id/stream order for D/I/H.
Matrices are [id, stream, head_dim], or [id, head_dim] for one stream. IDs
are unique, clusters are canonical wording strings. Selection accepts already
computed A1 point gates from validation summaries only. Replay remains owned by
existing hooks: this module returns a single head's [batch, seq, head_dim].
"""
from __future__ import annotations

from collections import Counter
import math
import numpy as np
import torch

RANK_RTOL = 1e-6


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _tensor(value, name, *, ndim=None):
    _require(isinstance(value, torch.Tensor) and value.is_floating_point(), name+' must be a floating tensor')
    _require(value.device.type == 'cpu', name+' must be CPU')
    _require(value.numel() > 0 and bool(torch.isfinite(value).all()), name+' must be nonempty and finite')
    _require(ndim is None or value.ndim == ndim, name+' has invalid shape')
    out = value.detach().float()
    _require(bool(torch.isfinite(out).all()), name+' overflows fp32')
    return out


def _seed(seed):
    _require(type(seed) is int and seed >= 0, 'seed must be a nonnegative integer')
    return seed


def image_geometry(projection):
    """fp32 SVD and Moore-Penrose inverse with strict relative cutoff 1e-6."""
    w = _tensor(projection, 'projection', ndim=2)
    u, spectrum, vh = torch.linalg.svd(w, full_matrices=False)
    keep = spectrum > RANK_RTOL * spectrum[0]
    rank = int(keep.sum())
    _require(rank > 0, 'projection has zero attainable rank')
    u, vh, s = u[:, keep], vh[keep], spectrum[keep]
    pinv = (vh.T / s) @ u.T
    _require(bool(torch.isfinite(pinv).all()), 'unstable projection pseudoinverse')
    return dict(projection=w.clone(), U=u, rank=rank, spectrum=spectrum,
                pinv=pinv, rank_rtol=RANK_RTOL)


def _cohort(d, i, h, width):
    values = [_tensor(x, name) for x, name in [(d,'D'), (i,'I'), (h,'H')]]
    _require(values[0].ndim in (2,3) and all(x.shape == values[0].shape for x in values),
             'D/I/H require equal paired id and stream shapes')
    _require(values[0].shape[-1] == width, 'head width differs from projection')
    return [x[:, None, :] if x.ndim == 2 else x for x in values]


def _cluster_weights(cluster_ids, instance_ids, n, seed):
    _require(len(cluster_ids) == len(instance_ids) == n, 'id/cluster lengths differ')
    _require(all(isinstance(x,str) and x for x in list(cluster_ids)+list(instance_ids)), 'empty or invalid id/cluster')
    _require(len(set(instance_ids)) == n, 'instance ids must be unique paired rows')
    clusters = sorted(set(cluster_ids))
    draws = np.random.default_rng(_seed(seed)).choice(clusters, size=len(clusters), replace=True).tolist()
    multiplicity = Counter(draws)
    counts = torch.tensor([multiplicity[x] for x in cluster_ids], dtype=torch.float32)
    weights = counts / counts.sum()
    return weights, dict(cluster_draws=draws, cluster_multiplicities=dict(multiplicity),
        expanded_n=int(counts.sum()), unique_n=int((counts>0).sum()),
        effective_n=float(1 / weights.square().sum()), id_weights=weights,
        instance_ids=list(instance_ids), cluster_ids=list(cluster_ids))


def _axis(geometry, v, h, weights):
    v = _tensor(v, 'axis', ndim=1)
    _require(v.shape == (geometry['projection'].shape[0],), 'axis residual width differs')
    norm = torch.linalg.vector_norm(v)
    _require(math.isfinite(float(norm)) and float(norm) > torch.finfo(torch.float32).eps, 'zero/unstable direction norm')
    v = v / norm
    _require(torch.allclose(geometry['U'] @ (geometry['U'].T @ v), v, atol=2e-6, rtol=2e-6), 'axis outside attainable image')
    mu_h = (h.mean(1) * weights[:,None]).sum(0)
    coordinates = (h @ geometry['projection'].T) @ v
    center = (coordinates.mean(1)*weights).sum()
    variance = ((coordinates-center).square().mean(1)*weights).sum()
    _require(bool(torch.isfinite(mu_h).all()) and math.isfinite(float(variance)), 'nonfinite H fit statistics')
    return dict(v=v, pullback=geometry['pinv']@v, h_center=mu_h,
                projected_variance=float(variance), sigma_fit=float(variance.sqrt()))


def fit_direction(d, i, h, projection, *, seed, cluster_ids, instance_ids):
    """One paired train-cluster bootstrap fit, equal streams then weighted IDs.

    Sample C clusters with replacement, carry all members; a cluster drawn m
    times gives each of its ids weight m/sum_id(m). Never trim expanded rows.
    H center and population variance use the identical bootstrap weights.
    """
    geometry = image_geometry(projection)
    d,i,h = _cohort(d,i,h,geometry['projection'].shape[1])
    weights, receipt = _cluster_weights(cluster_ids,instance_ids,len(d),seed)
    delta = ((d-i).mean(1)*weights[:,None]).sum(0)
    # Retained SVD image also removes numerical components below the cutoff.
    raw = geometry['U'] @ (geometry['U'].T @ (geometry['projection'] @ delta))
    result = _axis(geometry,raw,h,weights)
    return dict(geometry, **receipt, **result, raw_norm=float(raw.norm()), seed=seed, kind='D_minus_I')


def prepare_image_direction(projection, v, h, *, id_weights):
    """Attach H center/variance and pullback to a frozen learned or null axis.

    Reuse the learned fit's id_weights for each null; orientation does not imply
    equal projected variance or perturbation energy.
    """
    geometry = image_geometry(projection)
    h = _tensor(h, 'H')
    _require(h.ndim in (2,3) and h.shape[-1]==geometry['projection'].shape[1], 'invalid H shape')
    if h.ndim==2:
        h = h[:,None,:]
    weights = _tensor(id_weights, 'id weights', ndim=1)
    _require(weights.shape==(len(h),) and bool((weights>=0).all())
             and abs(float(weights.sum())-1)<1e-6, 'id weights must be nonnegative and sum to one')
    return dict(geometry, **_axis(geometry,v,h,weights), id_weights=weights.clone(), kind='image_axis')


def fit_nuisance_direction(pressure_neutral, user_neutral, h, projection, *, seed, cluster_ids, instance_ids):
    """Fit pressure-neutral minus user-neutral framing; cannot select a site."""
    result = fit_direction(pressure_neutral,user_neutral,h,projection,seed=seed,
                           cluster_ids=cluster_ids,instance_ids=instance_ids)
    result['kind'] = 'neutral_frame'
    return result


def direction_cosine(a, b):
    x,y = _tensor(a['v'],'first axis',ndim=1),_tensor(b['v'],'second axis',ndim=1)
    _require(x.shape==y.shape and min(float(x.norm()),float(y.norm())) > torch.finfo(torch.float32).eps,
             'invalid cosine axes')
    return float(torch.clamp(torch.dot(x/x.norm(),y/y.norm()),-1,1))


def random_image_directions(projection, *, n, seed):
    """n isotropic unit residual axes, drawn in rank-r coordinates, RNG 10000+seed."""
    _require(type(n) is int and n>0, 'n must be positive integer')
    geometry = image_geometry(projection)
    generator = torch.Generator(device='cpu').manual_seed(10000+_seed(seed))
    coordinates = torch.randn(n,geometry['rank'],generator=generator)
    coordinates /= coordinates.norm(dim=-1,keepdim=True)
    return coordinates @ geometry['U'].T


def _positions(positions, shape):
    _require(isinstance(positions,torch.Tensor) and positions.device.type=='cpu', 'positions must be CPU tensor')
    batch, seq = shape[:2]
    if positions.dtype == torch.bool:
        _require(positions.shape in ((seq,),(batch,seq)), 'invalid position mask shape')
        return positions.expand(batch,seq)
    _require(positions.dtype in (torch.int32,torch.int64) and positions.shape == (batch,), 'positions require bool mask or integer index per row')
    _require(bool(((positions>=0)&(positions<seq)).all()), 'position out of bounds')
    return torch.arange(seq)[None,:] == positions[:,None]


def _validated_axis(direction, width):
    w = _tensor(direction['projection'],'projection',ndim=2)
    v = _tensor(direction['v'],'v',ndim=1)
    pullback = _tensor(direction['pullback'],'pullback',ndim=1)
    _require(w.shape[1]==width and v.shape==(w.shape[0],) and pullback.shape==(width,), 'invalid direction geometry')
    _require(abs(float(v.norm())-1)<2e-5 and torch.allclose(w@pullback,v,atol=2e-5,rtol=2e-5), 'invalid direction axis/pullback')
    return w,v,pullback


def direction_replacement(z, donor, direction, *, mode, positions):
    """Compute one head replacement from intact captures, never a recursive patch.

    interchange: z + W+v vT W(donor-z); remove: subtract centered H
    projection; steer_positive/steer_negative: +/- train sigma W+v.
    Positions identify unpadded readouts; attention-mask validation is caller-owned.
    """
    original = z
    z,donor = _tensor(z,'z',ndim=3),_tensor(donor,'donor',ndim=3)
    _require(z.shape==donor.shape, 'donor shape differs')
    mask = _positions(positions,z.shape)
    w,v,pullback = _validated_axis(direction,z.shape[-1])
    if mode == 'interchange':
        coefficient = ((donor-z)@w.T)@v
    elif mode == 'remove':
        center = _tensor(direction['h_center'],'H center',ndim=1)
        _require(center.shape==(z.shape[-1],), 'invalid H center shape')
        coefficient = -((z-center)@w.T)@v
    elif mode in ('steer_positive','steer_negative'):
        sigma = direction['sigma_fit']
        _require(math.isfinite(sigma) and sigma>=0, 'invalid fit sigma')
        coefficient = torch.full(z.shape[:2],sigma*(1 if mode=='steer_positive' else -1))
    else:
        raise ValueError('unknown direction mode')
    replacement = (z+coefficient[...,None]*pullback).to(original.dtype)
    _require(bool(torch.isfinite(replacement).all()), 'nonfinite replacement')
    return torch.where(mask[...,None],replacement,original)


def perturbation_diagnostics(z, replacement, direction, *, positions):
    z,replacement = _tensor(z,'z',ndim=3),_tensor(replacement,'replacement',ndim=3)
    _require(z.shape==replacement.shape, 'replacement shape differs')
    w,_,_ = _validated_axis(direction,z.shape[-1])
    mask = _positions(positions,z.shape)
    delta = (replacement-z)[mask]
    return dict(head_norm=delta.norm(dim=-1),residual_norm=(delta@w.T).norm(dim=-1),
                fit_projected_variance=direction['projected_variance'])


def select_direction(validation_rows, *, sites, seed):
    """Gate-first selection of exactly one site; no outcome-based sign choice.

    Every row: split='validation', site, seed, finite D_fraction/I_fraction,
    point_pass=bool from ALL A1 gates. All supplied rows must be validation.
    Candidate site coverage must be exact for this seed. Ties are lexical.
    """
    _seed(seed)
    _require(validation_rows and all(r.get('split')=='validation' for r in validation_rows), 'selection requires validation only')
    key = lambda site: (site,) if isinstance(site,str) else tuple(site)
    keys = [key(s) for s in sites]
    _require(keys and len(set(keys))==len(keys), 'duplicate/empty candidate sites')
    rows = [dict(r) for r in validation_rows if r.get('seed')==seed]
    _require(len(rows)==len(keys) and {key(r['site']) for r in rows}==set(keys), 'missing/duplicate validation candidates')
    for row in rows:
        _require(type(row.get('point_pass')) is bool and all(isinstance(row.get(k),(int,float)) and math.isfinite(row[k]) for k in ('D_fraction','I_fraction')), 'invalid validation summary')
    passing = [r for r in rows if r['point_pass']]
    selected = min(passing or rows,key=lambda r:(-r['D_fraction'] if passing else -(r['D_fraction']-r['I_fraction']), key(r['site'])))
    return dict(selected,validation_failure=not bool(passing))


def _labels(labels, n):
    labels = _tensor(labels,'labels',ndim=1)
    _require(labels.shape==(n,) and set(labels.tolist())=={-1.,1.}, 'labels require both D=+1/I=-1')
    return labels


def fit_ridge_probe(train_coordinates, labels):
    """Train-only standardization; lambda=1, unpenalized intercept. No filtering."""
    x = _tensor(train_coordinates,'train coordinates',ndim=2)
    y = _labels(labels,len(x))
    center = _tensor(x.mean(0), 'probe train center', ndim=1)
    scale = _tensor(x.std(0,unbiased=False), 'probe train scale', ndim=1)
    scale = torch.where(scale>0,scale,torch.ones_like(scale))
    standardized = _tensor((x-center)/scale, 'probe train standardized design', ndim=2)
    # Centered X makes the unpenalized intercept exactly mean(y).
    gram = _tensor(standardized.T@standardized+torch.eye(x.shape[1]), 'probe ridge system', ndim=2)
    target = _tensor(standardized.T@(y-y.mean()), 'probe ridge target', ndim=1)
    coef = _tensor(torch.linalg.solve(gram,target), 'probe coefficient', ndim=1)
    return dict(center=center,scale=scale,coefficient=coef,intercept=float(y.mean()),regularization=1.)


def probe_predictions(probe, coordinates):
    x = _tensor(coordinates,'probe coordinates',ndim=2)
    _require(isinstance(probe,dict) and {'center','scale','coefficient','intercept','regularization'} <= set(probe), 'incomplete probe fields')
    center = _tensor(probe['center'], 'probe center', ndim=1)
    scale = _tensor(probe['scale'], 'probe scale', ndim=1)
    coefficient = _tensor(probe['coefficient'], 'probe coefficient', ndim=1)
    _require(center.shape == scale.shape == coefficient.shape == (x.shape[1],), 'probe field shape differs from coordinates')
    _require(bool((scale>0).all()), 'probe scale must be positive')
    intercept = probe['intercept']
    _require(isinstance(intercept,(int,float)) and math.isfinite(intercept), 'probe intercept must be finite')
    _require(probe['regularization'] == 1., 'invalid probe regularization')
    standardized = _tensor((x-center)/scale, 'probe evaluation standardized design', ndim=2)
    scores = _tensor(standardized@coefficient+intercept, 'probe evaluation scores', ndim=1)
    predicted = torch.where(scores>=0,1.,-1.)
    return predicted


def probe_balanced_accuracy(probe, coordinates, labels):
    x = _tensor(coordinates,'probe coordinates',ndim=2)
    y = _labels(labels,len(x))
    predicted = probe_predictions(probe,x)
    return float(torch.stack([(predicted[y==c]==c).float().mean() for c in (-1.,1.)]).mean())
