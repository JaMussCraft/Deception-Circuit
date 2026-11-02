import copy, runpy, torch
from component_analysis import a3_mask as m
h=runpy.run_path('tests/test_a3_mask.py'); tiny=h['tiny']
def chunks(kind):
 result=h['chunks'](kind,(2,1) if kind=='D' else (1,2))
 seq=98 if kind=='D' else 118
 for c in result:
  for key in ['input_ids','neutral_input_ids']:
   c.payload[key]=c.payload[key].repeat(1,1,(seq+3)//4)[...,:seq]
  counts=torch.tensor([[seq-(int(id_)+stream)%3 for stream in range(2)] for id_ in c.ids])
  mask=torch.arange(seq).view(1,1,-1)<counts[...,None]
  c.payload['attention_mask']=mask.long(); c.token_counts=counts
 return result

for constrained in (False, True):
 for regime,offset in [('active',2.),('inactive',6.),('kink',3.)]:
  model,s=tiny()
  with torch.no_grad():
   for g in s.gates.values(): g.log_alpha.zero_()
  ref=copy.deepcopy(model); rs=m.support_for(ref)
  opt=torch.optim.Adam(s.parameters(),lr=.01); ropt=torch.optim.Adam(rs.parameters(),lr=.01)
  ds,ins=chunks('D'),chunks('I'); rng=torch.get_rng_state()
  with torch.no_grad(): initial=[m.native_chunk_forward(model,c)['margin'].double() for c in ds]
  for c,margin,o in zip(ds,initial,[0.,offset]): c.baseline_margin=margin+o
  torch.set_rng_state(rng)
  do=[m.native_chunk_forward(ref,c)['margin'] for c in ds]; io=[m.native_chunk_forward(ref,c) for c in ins]
  d=torch.cat(do); db=torch.cat([c.baseline_margin for c in ds]).detach(); i=torch.cat([x['margin'] for x in io]); ib=torch.cat([c.baseline_margin for c in ins]).detach(); l=torch.cat([x['logits'] for x in io]); b=torch.cat([c.baseline_logits for c in ins]).detach()
  # Independent mathematical oracle: KL is sum p*(log p-log q), no production objective.
  arg=(d.double()-db.double()).mean()+1.
  q=torch.log_softmax(l,-1); logp=torch.log_softmax(b,-1); p=logp.exp()
  loss=arg.clamp_min(0) if arg.item()!=0 else arg*0
  if constrained: loss=loss+4*(ib-i).clamp_min(0).mean()+(p*(logp-q)).sum(-1).mean()
  penalties=[]
  for g in rs.gates.values(): penalties.extend((1-torch.sigmoid(g.log_alpha[g.eligibility]-g.beta*torch.log(-g.gamma/g.zeta))).unbind())
  loss=loss+.01*torch.stack(penalties).mean(); loss.backward(); grads=[p.grad.clone() for p in rs.parameters()]; ropt.step(); end=torch.get_rng_state()
  torch.set_rng_state(rng); actual=m.streamed_update(model,s,opt,ds,ins,m.native_chunk_forward,g_d_fit=torch.tensor(2.),identity={},constrained=constrained)
  maxerr=0.
  for (name,g),r,grad in zip(s.gates.items(),rs.parameters(),grads):
   maxerr=max(maxerr,(actual['gradients'][name]-grad).abs().max().item()); torch.testing.assert_close(actual['gradients'][name],grad,atol=2e-7,rtol=3e-5); torch.testing.assert_close(g.log_alpha,r,atol=2e-7,rtol=3e-5)
   for k in ['step','exp_avg','exp_avg_sq']: torch.testing.assert_close(opt.state[g.log_alpha][k],ropt.state[r][k],atol=2e-8,rtol=3e-5)
  assert torch.equal(end,torch.get_rng_state()); print('oracle',constrained,regime,'arg',arg.item(),'max_gradient_error',maxerr)

# Own-condition malformed evidence must reject before model forward / Adam.
mutations={
 'zero_count':lambda c:c.token_counts.__setitem__((0,0),0),
 'negative_count':lambda c:c.token_counts.__setitem__((0,0),-1),
 'infinite_count':lambda c:c.token_counts.__setitem__((0,0),float('inf')),
 'nan_count':lambda c:c.token_counts.__setitem__((0,0),float('nan')),
 'fractional_count':lambda c:c.token_counts.__setitem__((0,0),1.5),
 'mask_fractional_same_sum':lambda c:c.payload['attention_mask'].__setitem__((0,0,slice(0,2)),torch.tensor([.5,1.5])),
 'mask_negative_same_sum':lambda c:c.payload['attention_mask'].__setitem__((0,0,slice(0,2)),torch.tensor([-1.,3.])),
 'mask_nan':lambda c:c.payload['attention_mask'].__setitem__((0,0,-1),float('nan')),
 'mask_count_mismatch':lambda c:c.payload['attention_mask'].__setitem__((0,0,-1),0.),
 'donor_shape_mismatch':lambda c:c.payload.__setitem__('neutral_input_ids',c.payload['neutral_input_ids'][...,:-1]),
}
for label,mutate in mutations.items():
 model,s=tiny(); ds,ins=chunks('D'),chunks('I'); opt=torch.optim.Adam(s.parameters(),lr=.01)
 ins[0].token_counts=ins[0].token_counts.float(); ins[0].payload['attention_mask']=ins[0].payload['attention_mask'].float(); mutate(ins[0]); calls=[0]
 def unexpected(model,c):
  calls[0]+=1
  raise AssertionError('malformed data reached model')
 try:m.streamed_update(model,s,opt,ds,ins,unexpected,g_d_fit=2.,identity={})
 except ValueError as e:print('MALFORMED_REJECTED',label,str(e))
 else:raise AssertionError(label+' accepted')
 assert calls[0]==0 and not opt.state
# An altered but internally valid I layout must reject by checkpoint identity,
# not merely by invalid counts. Exact same layout must resume normally.
model,s=tiny(); ds,ins=chunks('D'),chunks('I'); opt=torch.optim.Adam(s.parameters(),lr=.01); kw=dict(g_d_fit=2.,identity={'layout':'independent'})
m.streamed_update(model,s,opt,ds,ins,m.native_chunk_forward,**kw)
saved=m.make_checkpoint(model,s,opt,ds,ins,identity=kw['identity'],update=1)
changed=copy.deepcopy(ins)
for c in changed:
 for key in ['input_ids','neutral_input_ids','attention_mask']:
  c.payload[key]=torch.cat([c.payload[key],torch.ones_like(c.payload[key][...,-1:])],-1)
 c.token_counts+=1
assert m._validate_chunks(ds,changed)==3
other,os=tiny(); oo=torch.optim.Adam(os.parameters(),lr=.01)
try:m.restore_checkpoint(saved,other,os,oo,ds,changed,identity=kw['identity'])
except ValueError as e:print('VALID_CHANGED_LAYOUT_REJECTED',str(e))
else:raise AssertionError('changed layout accepted')
assert not oo.state
m.restore_checkpoint(saved,other,os,oo,ds,ins,identity=kw['identity'])
m.streamed_update(model,s,opt,ds,ins,m.native_chunk_forward,**kw); expected=[p.detach().clone() for p in s.parameters()]; end=m.rng_state()
m.restore_rng(saved['rng']); m.streamed_update(other,os,oo,ds,ins,m.native_chunk_forward,**kw)
for a,b in zip(expected,os.parameters()):torch.testing.assert_close(a,b,atol=0,rtol=0)
assert torch.equal(end['cpu'],m.rng_state()['cpu'])
print('UNEQUAL_LAYOUT_EXACT_RESUME')
