import copy, runpy, torch
from component_analysis import a3_mask as m
h=runpy.run_path('tests/test_a3_mask.py'); tiny=h['tiny']; chunks=h['chunks']
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
# Baseline bytes mutate after update admission, before I uses them.
model,s=tiny(); ds,ins=chunks('D'),chunks('I'); opt=torch.optim.Adam(s.parameters(),lr=.01); calls=[0]
def mutate(model,c):
 calls[0]+=1
 if calls[0]==3: ins[0].baseline_margin.add_(100.)
 return m.native_chunk_forward(model,c)
try:
 m.streamed_update(model,s,opt,ds,ins,mutate,g_d_fit=torch.tensor(2.),identity={})
 print('MUTATION_ACCEPTED',calls[0],ins[0].baseline_margin[0,0].item())
except Exception as e: print('mutation_rejected',type(e).__name__,str(e))
# Failed updates must not produce checkpoints.
model,s=tiny(); ds,ins=chunks('D'),chunks('I'); opt=torch.optim.Adam(s.parameters(),lr=.01)
def fail(model,c): raise RuntimeError('intentional review failure')
try: m.streamed_update(model,s,opt,ds,ins,fail,g_d_fit=torch.tensor(2.),identity={})
except RuntimeError: pass
try: m.make_checkpoint(model,s,opt,ds,ins,identity={},update=0)
except RuntimeError as e: print('FAILED_CHECKPOINT_REJECTED',str(e))
else: raise AssertionError('failed checkpoint accepted')
import runpy, torch
from component_analysis import a3_mask as m
h=runpy.run_path('tests/test_a3_mask.py'); model,s=h['tiny'](); ds,ins=h['chunks']('D'),h['chunks']('I'); opt=torch.optim.Adam(s.parameters(),lr=.01)
m.streamed_update(model,s,opt,ds,ins,m.native_chunk_forward,g_d_fit=2.,identity={'source':'same'})
saved=m.make_checkpoint(model,s,opt,ds,ins,identity={'source':'same'},update=1)
other,os=h['tiny'](); oo=torch.optim.Adam(os.parameters(),lr=.01)
print('norm_epsilon_before',other.model.norm.variance_epsilon)
other.model.norm.variance_epsilon=1.
print('restore_with_changed_base_norm_epsilon',m.restore_checkpoint(saved,other,os,oo,ds,ins,identity={'source':'same'}))
m.streamed_update(model,s,opt,ds,ins,m.native_chunk_forward,g_d_fit=2.,identity={'source':'same'})
m.restore_rng(saved["rng"])
m.streamed_update(other,os,oo,ds,ins,m.native_chunk_forward,g_d_fit=2.,identity={'source':'same'})
print('next_update_max_parameter_difference',max((a-b).abs().max().item() for a,b in zip(s.parameters(),os.parameters())))
