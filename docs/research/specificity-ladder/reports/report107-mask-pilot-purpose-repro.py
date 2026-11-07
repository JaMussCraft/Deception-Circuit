import copy, runpy, torch
from component_analysis import a3_mask as m
h=runpy.run_path('tests/test_a3_mask.py'); tiny=h['tiny']; chunks=h['chunks']
def cohort(split):
 ds,ins=chunks('D'),chunks('I')
 for c in ins:
  for key in ['input_ids','neutral_input_ids','attention_mask']:
   c.payload[key]=torch.cat([c.payload[key],c.payload[key][...,:2]],-1)
  c.token_counts.fill_(6)
 for c in ds+ins:c.split=split
 return ds,ins
def reject(label,fn):
 try:fn()
 except (ValueError,RuntimeError) as e:print('REJECTED',label,str(e))
 else:raise AssertionError(label+' accepted')
for constrained in [False,True]:
 model,s=tiny()
 with torch.no_grad():
  for g in s.gates.values():g.log_alpha.zero_()
 ref=copy.deepcopy(model); rs=m.support_for(ref)
 opt=torch.optim.Adam(s.parameters(),lr=.01); ropt=torch.optim.Adam(rs.parameters(),lr=.01)
 ds,ins=cohort('validation'); rds,rins=cohort('train'); start=m.rng_state()
 kw=dict(g_d_fit=2.,identity={'source':'purpose-review'},constrained=constrained)
 expected=m.streamed_update(ref,rs,ropt,rds,rins,m.native_chunk_forward,**kw); end=m.rng_state()
 m.restore_rng(start)
 actual=m.streamed_update(model,s,opt,ds,ins,m.native_chunk_forward,purpose='validation_timing',**kw)
 for name,g in s.gates.items():
  torch.testing.assert_close(actual['gradients'][name],expected['gradients'][name],atol=0,rtol=0)
  torch.testing.assert_close(g.log_alpha,rs.gates[name].log_alpha,atol=0,rtol=0)
  for field in ['step','exp_avg','exp_avg_sq']:
   torch.testing.assert_close(opt.state[g.log_alpha][field],ropt.state[rs.gates[name].log_alpha][field],atol=0,rtol=0)
 assert torch.equal(end['cpu'],m.rng_state()['cpu'])
 assert all(c.split=='validation' for c in ds+ins)
 saved=m.make_checkpoint(model,s,opt,ds,ins,identity=kw['identity'],update=1,purpose='validation_timing')
 assert saved['purpose']==saved['update_spec']['purpose']=='validation_timing'
 m.streamed_update(model,s,opt,ds,ins,m.native_chunk_forward,purpose='validation_timing',**kw)
 expected_params=[p.detach().clone() for p in s.parameters()]; end=m.rng_state()
 other,os=tiny(); oo=torch.optim.Adam(os.parameters(),lr=.01)
 assert m.restore_checkpoint(saved,other,os,oo,ds,ins,identity=kw['identity'],purpose='validation_timing')==1
 m.streamed_update(other,os,oo,ds,ins,m.native_chunk_forward,purpose='validation_timing',**kw)
 for a,b in zip(expected_params,os.parameters()):torch.testing.assert_close(a,b,atol=0,rtol=0)
 assert torch.equal(end['cpu'],m.rng_state()['cpu'])
 print('PURPOSE_NATIVE_PARITY_AND_RESUME',constrained,'exact')
 # Split mismatch/default rejection must happen before model callbacks and Adam.
 fresh,fs=tiny(); fo=torch.optim.Adam(fs.parameters(),lr=.01); calls=[0]
 def unexpected(*a):calls[0]+=1;raise AssertionError('bad context reached model')
 for split,purpose in [('validation',None),('test',None),('train','validation_timing'),('test','validation_timing'),('validation','unknown')]:
  bad_d,bad_i=cohort(split); context={} if purpose is None else {'purpose':purpose}
  reject('update_'+split+'_'+str(purpose),lambda:m.streamed_update(fresh,fs,fo,bad_d,bad_i,unexpected,**context,**kw))
  reject('checkpoint_'+split+'_'+str(purpose),lambda:m.make_checkpoint(fresh,fs,fo,bad_d,bad_i,identity=kw['identity'],update=0,**context))
  reject('restore_'+split+'_'+str(purpose),lambda:m.restore_checkpoint(saved,fresh,fs,fo,bad_d,bad_i,identity=kw['identity'],**context))
 assert calls[0]==0 and not fo.state
 # Cross-context restore is rejected even if both datasets are well formed.
 train_d,train_i=cohort('train')
 reject('cross_context_restore',lambda:m.restore_checkpoint(saved,fresh,fs,fo,train_d,train_i,identity=kw['identity']))
 changed=copy.deepcopy(saved); changed['purpose']='scientific_training'
 reject('altered_checkpoint_purpose',lambda:m.restore_checkpoint(changed,fresh,fs,fo,ds,ins,identity=kw['identity'],purpose='validation_timing'))
 # Caller relabeling cannot let already-used timing state enter a fit.
 reject('reuse_timing_state_as_fit',lambda:m.streamed_update(model,s,opt,train_d,train_i,m.native_chunk_forward,**kw))
 reject('retag_timing_checkpoint_as_fit',lambda:m.make_checkpoint(model,s,opt,train_d,train_i,identity=kw['identity'],update=2))
 assert not fo.state
 # Existing source identity guard remains in the new timing context.
 fresh.model.norm.variance_epsilon=1.
 reject('changed_timing_base_source',lambda:m.restore_checkpoint(saved,fresh,fs,fo,ds,ins,identity=kw['identity'],purpose='validation_timing'))
 assert not fo.state
print('PURPOSE_REVIEW_COMPLETE')
