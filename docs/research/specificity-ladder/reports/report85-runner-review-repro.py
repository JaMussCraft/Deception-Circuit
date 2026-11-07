import torch
from pytest import MonkeyPatch
from tests import test_a3_direction_runner as t
from component_analysis import a3_direction_runner as r, hooks
mp=MonkeyPatch()
calls=t.fake.__wrapped__(mp)
original=hooks.capture_forward

def bad_packing(model, ids, mask, **kw):
    cap=original(model,ids,mask,**kw)
    replacements=kw.get('replacements') or {}
    z=torch.stack((ids.float(), ids.float()*2),-1)
    changed=any(not torch.equal(rep.value, z) for rep in replacements.values())
    if len(ids)>2 and changed:
        cap.logits=cap.logits*1.5
        cap.residual=cap.residual*1.5
    return cap
mp.setattr(hooks,'capture_forward',bad_packing)
results=[]
for tile in (1,3):
    ident=t.identity(tile)
    idx,_=t.cache(calls,ident)
    out=[]
    ret=r.score_direction_cells(object(),[t.batch()],cells=[dict(t.cell('zero'),axis_index=i) for i in range(4)],capture_index=idx,axes={'x':t.axis()},sink=out.append,identity=ident)
    results.append([row['patched_margin'] for chunk in out for row in chunk['rows']])
    print('tile',tile,'accepted rows',ret['rows'],'max replay error',ret['max_replay_margin_error'])
print('serial==packed',results[0]==results[1],results)
# A positive-control row can be reduced to invented assertions and is accepted in production mode.
ident=t.identity(); ident.pop('injected');ident.pop('diagnostic_only')
b=t.batch();pid=r.profile_identity(ident)
c=dict(t.cell('zero'),positive_controls=[dict(task=b.task,condition=b.condition,instance_id=rid,stream=b.stream,valid=True,profile_id=pid,recipient_sha256=r._recipient_digest(b,i),control_id='f'*64) for i,rid in enumerate(b.ids)])
idx,_=t.cache(calls,ident);out=[]
r.score_direction_cells(object(),[b],cells=[c],capture_index=idx,axes={'x':t.axis()},sink=out.append,identity=ident)
print('fabricated production positive controls gate_valid', [row['gate_valid'] for row in out[0]['rows']])
mp.undo()
