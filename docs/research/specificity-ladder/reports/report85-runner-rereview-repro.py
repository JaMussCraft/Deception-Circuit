"""Independent CPU re-attacks for report85; synthetic model fixtures only."""
import copy
import torch
from pytest import MonkeyPatch
from tests import test_a3_direction_runner as t
from component_analysis import a3_direction_runner as r, hooks

mp = MonkeyPatch()
calls = t.fake.__wrapped__(mp)
original = hooks.capture_forward

def rejected(label, action):
    before = len(calls)
    try:
        action()
    except ValueError as exc:
        print(label + ': blocked: ' + str(exc) + '; extra forwards=' + str(len(calls)-before))
    else:
        raise AssertionError(label + ' unexpectedly accepted')

# Original nonzero-patch fault, now passed through the new measurement producer.
def packing_fault(model, ids, mask, **kw):
    cap = original(model, ids, mask, **kw)
    baseline = torch.stack((ids.float(), ids.float()*2), -1)
    changed = any(not torch.equal(rep.value, baseline) for rep in (kw.get('replacements') or {}).values())
    if len(ids)>2 and changed:
        cap.logits = cap.logits*1.5
        cap.residual = cap.residual*1.5
    return cap
mp.setattr(hooks, 'capture_forward', packing_fault)
rejected('packing-sensitive patch measurement', lambda: t.measured_setup(calls))
mp.setattr(hooks, 'capture_forward', original)
ident, index, axes, cells = t.measured_setup(calls)
print('baseline measured packing valid=' + str(ident['packed_equivalence']['valid']))
for field in ('source', 'axis', 'input', 'receipt'):
    changed = copy.deepcopy(ident)
    ax = copy.deepcopy(axes)
    b = t.batch()
    if field == 'source': changed['numeric_profile']['source_sha256'] = '9'*64
    elif field == 'axis': ax['x']['sigma_fit'] += .1
    elif field == 'input': b.input_ids[0,0] += 1
    else: changed['packed_equivalence']['comparisons'].pop()
    rejected('stale packing '+field, lambda: r.score_direction_cells(object(), [b], cells=cells, capture_index=index, axes=ax, sink=lambda x:None, identity=changed))

b=t.batch(); d=t.batch('corrupt'); ident=t.identity()
ident.pop('injected'); ident.pop('diagnostic_only')
pid=r.profile_identity(ident)
fabricated=[dict(task=b.task, condition=b.condition, instance_id=rid, stream=b.stream, valid=True, profile_id=pid, recipient_sha256=r._recipient_digest(b,i), control_id='f'*64) for i,rid in enumerate(b.ids)]
rejected('fabricated positive controls', lambda: r.score_direction_cells(object(),[b],cells=[dict(t.cell('zero'),positive_controls=fabricated)],capture_index={},axes={'x':t.axis()},sink=lambda x:None,identity=ident))
before=len(calls)
controls=r.run_positive_controls(object(),[b],donor_batches=[d],donor_maps=t.donor_maps(b,d),identity=ident)['rows']
print('positive helper forwards=' + str(len(calls)-before) + '; expected=' + str(3*len(b.ids)))
idx,_=t.cache(calls,ident)
for field in ('error','valid','sender','donor','geometry','tolerance'):
    stale=copy.deepcopy(controls)
    row=stale[0]
    if field=='error': row['reviewed']['max_abs_logit_error']=999.
    elif field=='valid': row['valid']=False
    elif field=='sender': row['sender_keys']=[]
    elif field=='donor': row['donor']['tokens'][0]+=1
    elif field=='geometry': row['measurement']['padded_width']+=1
    else: row['measurement']['rtol']=1.
    rejected('stale positive '+field, lambda: r.score_direction_cells(object(),[b],cells=[dict(t.cell('zero'),positive_controls=stale)],capture_index=idx,axes={'x':t.axis()},sink=lambda x:None,identity=ident))
mp.setattr(hooks,'attention_implementation',lambda m:'wrong')
rejected('positive wrong runtime',lambda:r.run_positive_controls(object(),[b],donor_batches=[d],donor_maps=t.donor_maps(b,d),identity=ident))
mp.undo()
print('all independent re-attacks blocked')
