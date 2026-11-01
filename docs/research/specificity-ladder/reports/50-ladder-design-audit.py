"""Independent CPU audit of immutable prepared ladder; never calls prepare/freeze_design.
Only owned audit receipts are written. Local tokenizer/cache use only, no model.
"""
import ast,hashlib,inspect,json,random,sys
from collections import Counter,defaultdict
from pathlib import Path
from datasets import load_from_disk
from transformers import AutoTokenizer
import pyarrow.parquet as pq
R=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
P=Path('/projects/beto/swong2/Alignment/Deception-Circuit')
D=R/'outputs/_analyses/specificity-ladder/ladder-6bd8bf5/design.json'
O=R/'docs/research/specificity-ladder/reports'
H=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
U=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
J=lambda p:json.loads(Path(p).read_text())
def FH(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for c in iter(lambda:f.read(2**20),b''):h.update(c)
 return h.hexdigest()
def actual(p):return Path(p) if Path(p).is_absolute() else R/p
raw=J(D); x=raw['payload'];assert H(x)==raw['sha256'];assert x['commit']=='6bd8bf5334f2e83613a129d2fcfeacf83e762191'
assert x['kind']=='prepared' and x['injected'] is False and x['seed']==1
rev='0e9e39f249a16976918f6564b8830bc894c89659';assert x['model_revision']==x['tokenizer_revision']==rev
start=J(O/'50-ladder-design-initial-code-hashes.json');assert set(start)==set(x['code_hashes'])
assert all(v['recorded']==v['actual']==x['code_hashes'][p] and v['matches'] for p,v in start.items())
current_code={p:FH(R/p) for p in x['code_hashes']}
changes=[p for p,h in current_code.items() if h!=x['code_hashes'][p]]
for domain in ['source_hashes','selection_hashes','registry_hashes']:
 for p,h in x[domain].items():assert FH(actual(p))==h,(domain,p)
# Direction registries may legitimately receive unrelated session metadata; inspect
# the actual frozen grader field in both plus record their byte-hash agreement.
grader_files=sorted(list((R/'evaluation/benchmarks').glob('*.py'))+[R/'evaluation/benchmark_eval.py'])
g=hashlib.sha256(''.join(f'{p.relative_to(R).as_posix()}\t{FH(p)}\n' for p in grader_files).encode()).hexdigest()
assert g==x['grader_sha256']=='866fd15dd30b695e46ffe955b09894fb831af92e2b9015eafbd7f0eee151d2f9'
pfiles=sorted(list((P/'evaluation/benchmarks').glob('*.py'))+[P/'evaluation/benchmark_eval.py'])
assert hashlib.sha256(''.join(f'{q.relative_to(P).as_posix()}\t{FH(q)}\n' for q in pfiles).encode()).hexdigest()==g
gr={}
for path,h in x['grader_registry'].items():
 rows=J(path)['directions'];row=next(r for r in rows if r['id']=='specificity-ladder');assert row['frozen_grader_sha256']==g
 gr[path]={'byte_hash_matches':FH(path)==h,'actual_sha256':FH(path),'frozen_grader_sha256':g}
for path in x['registry_hashes']:assert J(path)=={'schema':1,'sets':[]}
snap=Path(x['tokenizer_loading']['resolved_snapshot']);assert snap.name==rev
assert FH(snap/'tokenizer_config.json')==x['tokenizer_loading']['tokenizer_config_sha256']
tok=AutoTokenizer.from_pretrained(str(snap),local_files_only=True)
def encode(text,special=False):return list(tok.encode(text,add_special_tokens=special))
def batch(texts,special=False):return tok(texts,add_special_tokens=special,truncation=False)['input_ids']
def contextual(prompt,word,tokens,special=False):
 v=encode(prompt+' '+word,special);assert v[:-1]==tokens and len(v)==len(tokens)+1;return v[-1]
headers={role:encode('<|start_header_id|>'+role+'<|end_header_id|>\n\n') for role in ['system','user','assistant']}
eot=tok.convert_tokens_to_ids('<|eot_id|>')
def layout(tokens):
 roles=[];contents=[]
 for role,h in headers.items():
  starts=[i for i in range(len(tokens)-len(h)+1) if tokens[i:i+len(h)]==h];assert len(starts)==1
  i=starts[0];start=i+len(h);end=tokens.index(eot,start) if eot in tokens[start:] else len(tokens)
  roles.append([role,i,end]);contents.append([role,start,end])
 return {'role_spans':roles,'content_spans':contents}
sel={Path(p).parent.name:J(p)['instance_ids'] for p in x['selection_hashes']}; exclusion=set.union(*(set(v) for v in sel.values()))
assert len(sel)==3 and all(len(v)==len(set(v)) for v in sel.values())
readpath=P/'docs/research/mechanism-analysis/phase1/p1c_readings.json'; readings=J(readpath)
for task in ['far','sdr','ser']:
 old=readings['rab'][task]['deciding_numbers']['members']; rec=x['recorded_groups'][task]
 assert len(old)==20 and rec['source_members']==old and rec['source_hash']==H(old)
 assert rec['members']==[[v.split('.')[0],int(v.split('.')[1]),int(v.split('.')[2])] for v in old]
 assert rec['descriptive']==(task=='sdr')
result={'artifact':str(D),'artifact_byte_sha256':FH(D),'envelope_sha256':raw['sha256'],'recorded_code_commit':x['commit'],'initial_source_code_hashes_all_match':True,'current_code_mismatches':changes,'source_file_hashes_checked':len(x['source_hashes']),'selection_file_hashes_checked':len(x['selection_hashes']),'grader':g,'actual_primary_grader_matches':True,'grader_registry':gr,'protected_registries_empty':True,'tokenizer_revision':rev,'selection_union_count':len(exclusion),'tasks':{}}
print('envelope/source/selection/grader hashes pass',flush=True)
factors=['designation_polarity','item_polarity','template_variant']; conditions=['D','H','F','I','user_neutral'];streams=['clean','corrupt']
# Reproduce balanced sampling independently rather than calling draw_sample.
def draw(rows,n=100):
 lev=lambda row,f:None if row.get(f) is None else str(row[f])
 active=[f for f in factors if len({lev(q,f) for q in rows})>1]
 buckets=defaultdict(list)
 for i,q in enumerate(rows):buckets[tuple((f,lev(q,f)) for f in active)].append((q['instance_id'],i))
 keys=sorted(buckets,key=lambda k:tuple(str(v) for _,v in k));pools=[sorted(buckets[k]) for k in keys];sizes=list(map(len,pools))
 share,extra=divmod(n,len(pools));targets=[share+int(i<extra) for i in range(len(pools))];counts=[min(a,b) for a,b in zip(targets,sizes)]
 while sum(counts)<n:
  for i in sorted([i for i in range(len(pools)) if counts[i]<sizes[i]],key=lambda i:(counts[i],i)):
   if sum(counts)==n:break
   counts[i]+=1
 rng=random.Random(1);chosen=[]
 for pp,num in zip(pools,counts):chosen.extend(rng.sample(pp,num))
 chosen=sorted((i,rid) for rid,i in chosen);return [r for i,r in chosen],[i for i,r in chosen],active
for task in x['tasks']:
 rows=x['rows'][task];f=x['designs'][task];assert set(rows)==set(conditions)
 indexed={}; counts={}; all_norm=0
 suffix={'D':'','H':'_honest','F':'_nopressure','I':'_user_inversion','user_neutral':'_user_neutral'}
 orig={}; roots={}
 for c in conditions:
  root=R/'data/datasets' if c in ['D','H','F'] else R/'outputs/_analyses/specificity-ladder/a1-control-77b6487-m07'
  directory=root/(task+suffix[c]);ds=load_from_disk(str(directory)); roots[c]=directory
  orig[c]={s:list(ds[s]) for s in ['train','validation','test']}
  index={q['instance_id']:q for q in rows[c]};assert len(index)==len(rows[c]);indexed[c]=index
  splitdigests={s:H(qs) for s,qs in orig[c].items()}
  flat=[(s,q) for s in ['train','validation','test'] for q in orig[c][s]]
  assert [q['instance_id'] for s,q in flat]==[q['instance_id'] for q in rows[c]]
  origD={q['instance_id']:q for ss in orig['D'].values() for q in ss}
  text=[]
  for (split,q),nr in zip(flat,rows[c]):
   canon=origD[q['instance_id']]
   for stream in streams:
    honest,opposite=(canon['distractor'],canon['target']) if stream=='clean' else (canon['target'],canon['distractor'])
    text.extend([q[stream+'_prompt'],q[stream+'_prompt']+' '+honest,q[stream+'_prompt']+' '+opposite])
  enc=batch(text);it=iter(enc)
  for (split,q),nr in zip(flat,rows[c]):
   assert nr['condition']==nr['source_condition']==c and nr['split']==split and nr['task']==task
   assert nr['source_hash']==splitdigests[split]; canon=origD[q['instance_id']]
   for k in ['instance_id','pressure_id','template_variant','designation_polarity','item_polarity','pressure_slot','item_pair','request_id']:assert nr[k]==q.get(k)
   for stream in streams:
    rr=nr['streams'][stream];t,th,to=next(it),next(it),next(it)
    honest,opposite=(canon['distractor'],canon['target']) if stream=='clean' else (canon['target'],canon['distractor'])
    assert rr['prompt']==q[stream+'_prompt'] and rr['tokens']==t and rr['readout']==len(t)-1
    assert th[:-1]==to[:-1]==t and len(th)==len(to)==len(t)+1
    assert rr['honest_token']==th[-1] and rr['opposite_token']==to[-1] and rr['expected_token']==(to[-1] if c in ['D','I'] else th[-1])
    assert rr['honest_word']==honest and rr['opposite_word']==opposite and rr['honest_item']==canon[stream+'_item_d']
    assert rr['layout']==layout(t)
    if c in ['I','user_neutral']:
     assert rr['user_request_span']==q['request_spans'][stream] and len(t)==q['token_lengths'][stream] and rr['readout']==q['readouts'][stream]
     assert q['request_text'] in rr['prompt']
   all_norm+=1
  counts[c]={s:len(v) for s,v in orig[c].items()}
 test={c:{k:q for k,q in indexed[c].items() if q['split']=='test'} for c in conditions}
 common=set.intersection(*(set(v) for v in test.values()))-exclusion;eligible=[test['D'][k] for k in sorted(common)]
 ids,indices,active=draw(eligible)
 assert f['n']==100 and f['seed']==1 and f['assessment_ids']==ids
 assert f['sample']['instance_ids']==ids and f['sample']['eligible_pool_ids']==sorted(common) and f['sample']['eligible_pool_indices']==indices and f['sample']['join_on']=='instance_id'
 assert [f['sample']['eligible_pool_ids'][i] for i in indices]==ids and f['sample']['factors']==active
 assert len(ids)==len(set(ids))==100 and not set(ids)&exclusion
 assert f['mover_selection_ids']==sel[task] and f['selection_exclusion_ids']==sorted(exclusion)
 assert set(f['mover_selection_ids'])<=set(test['H'])
 for rid in common:
  for factor in factors:assert len({json.dumps(test[c][rid].get(factor),sort_keys=True) for c in conditions})==1
 banned=exclusion|set(ids)
 pools={c:[indexed[c][rid] for rid in sorted(indexed[c]) if indexed[c][rid]['split'] in ['train','validation'] and rid not in banned] for c in conditions}
 assert f['bank_ids']==[q['instance_id'] for q in pools['H']] and len(f['bank_ids'])==400
 assert set(f['bank_ids']).isdisjoint(ids) and all(indexed['H'][rid]['split'] in ['train','validation'] for rid in f['bank_ids'])
 assert f['hashes']=={'selection':H({'domain':'selection','ids':sorted(exclusion),'rows':[test['H'][rid] for rid in sel[task]]}),'assessment':H({'domain':'assessment','rows':{c:[test[c][rid] for rid in ids] for c in conditions}}),'bank':H({'domain':'bank','rows':pools['H']}),'donor_sources':H(pools),'donors':H(f['donors'])}
 for rid in indexed['I']:
  ii,nn=indexed['I'][rid],indexed['user_neutral'][rid]
  for s in streams:
   a,b=ii['streams'][s],nn['streams'][s];st,en=a['user_request_span'];assert b['user_request_span']==[st,en] and a['layout']==b['layout'] and len(a['tokens'])==len(b['tokens'])
   assert a['tokens'][:st]==b['tokens'][:st] and a['tokens'][en:]==b['tokens'][en:]
 def aligned(a,b):return len(a['tokens'])==len(b['tokens']) and a['layout']==b['layout']
 def request_match(a,b,s):return a.get('request_id') is not None and a['request_id']==b.get('request_id') and a['streams'][s].get('user_request_span')==b['streams'][s].get('user_request_span')
 def semantic(a,b):return all(a.get(k) is not None and a[k]==b.get(k) for k in ['honest_word','opposite_word','honest_item'])
 coverage=defaultdict(Counter);expectedkeys={(rid,c,s,op,seed) for rid in ids for c in conditions for s in streams for op in ['item_swap','h_twin','zero','h_mean','self_replay','empty','independent_resample'] for seed in ([101,102,103] if op=='independent_resample' else [None])};seen=set()
 for m in f['donors']:
  rid,c,s,op,seed=m['recipient_id'],m['recipient_condition'],m['recipient_stream'],m['operation'],m['seed'];key=(rid,c,s,op,seed);assert key in expectedkeys and key not in seen;seen.add(key)
  recipient=test[c][rid];rr=recipient['streams'][s];n=len(rr['tokens']);assert m['requested_positions']==n
  coverage[c+'/'+op]['total']+=1;coverage[c+'/'+op]['supported']+=int(m['supported']);coverage[c+'/'+op]['no_op']+=int(m['no_op']);coverage[c+'/'+op]['covered_positions']+=m['covered_positions'];coverage[c+'/'+op]['requested_positions']+=n
  if op in ['zero','h_mean','empty']:
   assert m['supported'] and m['gate_valid'];assert m['donor_id'] is None and m['donor_positions']==[]
   assert m['recipient_positions']==([] if op=='empty' else list(range(n))) and m['covered_positions']==(0 if op=='empty' else n)
   assert m['no_op']==m['degenerate']==(op=='empty');continue
  ds=s
  if op=='item_swap':donor=recipient;ds='corrupt' if s=='clean' else 'clean';assert m['eligible_ids']==[]
  elif op=='self_replay' or (op=='h_twin' and c in ['H','user_neutral']):donor=recipient;assert m['eligible_ids']==[]
  else:
   dc='user_neutral' if c in ['I','user_neutral'] else 'H'
   pp=[q for q in (pools[dc] if op=='independent_resample' else [test[dc][rid]]) if semantic(rr,q['streams'][s]) and (c not in ['I','user_neutral'] or request_match(recipient,q,s))]
   if op=='independent_resample':pp=[q for q in pp if q['instance_id']!=rid and q['template_variant']==recipient['template_variant'] and aligned(rr,q['streams'][s])]
   pp.sort(key=lambda q:q['instance_id']);assert m['eligible_ids']==[q['instance_id'] for q in pp]
   if not pp:
    assert not m['supported'] and m['unsupported_reason']=='no eligible H-derived donor' and m['covered_positions']==0 and m['recipient_positions']==m['donor_positions']==[];continue
   if op=='independent_resample':
    drawseed=int(H([seed,c,rid,s]),16);assert drawseed==m['draw_seed'];donor=random.Random(drawseed).choice(pp)
   else:donor=pp[0]
  dr=donor['streams'][ds];assert m['donor_id']==donor['instance_id'] and m['donor_condition']==donor['condition'] and m['donor_stream']==ds and m['donor_split']==donor['split'] and m['donor_hash']==H(donor)
  good=aligned(rr,dr);assert m['supported']==good
  if not good:
   assert m['unsupported_reason']=='full unpadded length or explicit role/content boundaries unsupported' and m['covered_positions']==0 and m['recipient_positions']==m['donor_positions']==[];continue
  noop=rr['tokens']==dr['tokens'];assert m['no_op']==m['degenerate']==noop and m['gate_valid']==(not noop) and m['covered_positions']==n
  assert m['recipient_positions']==m['donor_positions']==list(range(n))
 assert seen==expectedkeys and len(seen)==9000
 result['tasks'][task]={'normalized_rows_checked':all_norm,'source_split_counts':counts,'selection_count':len(sel[task]),'selection_union_excluded':len(exclusion),'eligible_count':len(eligible),'assessment_count':len(ids),'assessment_ids':ids,'assessment_indices':indices,'bank_count':len(f['bank_ids']),'bank_split_counts':dict(Counter(indexed['H'][rid]['split'] for rid in f['bank_ids'])),'domain_hashes':f['hashes'],'donor_maps_checked':len(seen),'coverage':{k:dict(v) for k,v in coverage.items()}}
 print(task,'normalized rows, draw and all donor maps pass',flush=True)
# Utility samples are independently rebuilt from immutable raw cache/generator inputs,
# never by calling the ladder utility adapter or model-correct filtering loaders.
u=x['utility'];ioi=u['ioi'];assert len(ioi)==100
mod=R/'dataset/ioi_llama.py';names=J(R/'dataset/names.json');names=sorted(set(names['girls']+names['boys']));nt=batch([' '+name for name in names]);valid=[name for name,t in zip(names,nt) if len(t)==1]
constants={}
for node in ast.parse(mod.read_text()).body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ['BABA_TEMPLATES','ABBA_TEMPLATES','PLACES','OBJECTS']:constants[node.targets[0].id]=ast.literal_eval(node.value)
rng=random.Random(1);eligibleioi=[];seen=set();ioisource=U({'generator':FH(mod),'names':FH(R/'dataset/names.json'),'name_order':'sorted','seed':1,'count':1000})
for index in range(1000):
 a,b=rng.sample(valid,2);template=rng.choice(constants['BABA_TEMPLATES']+constants['ABBA_TEMPLATES']);place=rng.choice(constants['PLACES']);obj=rng.choice(constants['OBJECTS'])
 clean=template.format(A=a,B=b,PLACE=place,OBJECT=obj);corrupt=template.format(A=b,B=b,PLACE=place,OBJECT=obj)
 assert clean.endswith(' '+a) and corrupt.endswith(' '+b)
 cp,sp=clean[:-(len(a)+1)],corrupt[:-(len(b)+1)];sig=(cp,sp,a,b)
 if sig in seen:continue
 seen.add(sig);ct,st=encode(cp,True),encode(sp,True)
 try:tokens=[contextual(p,name,t,True) for p,t in [(cp,ct),(sp,st)] for name in [a,b]]
 except AssertionError:continue
 eligibleioi.append((index,a,b,template,cp,sp,ct,st,tokens))
assert [r['source_id'] for r in ioi]==[f'ioi:seed=1:row={v[0]}' for v in eligibleioi[:100]]
for row,data,m in zip(ioi,eligibleioi[:100],u['ioi_maps']):
 index,a,b,template,cp,sp,ct,st,tokens=data;assert row['a']==a and row['b']==b and row['source_hash']==ioisource and row['expected_token']==row['honest_token']==tokens[0] and row['opposite_token']==tokens[1]
 for stream,prompt,t,answers in [('clean',cp,ct,tokens[:2]),('corrupt',sp,st,tokens[2:])]:
  rr=row['streams'][stream];assert rr['prompt']==prompt and rr['prompt_utf8_hex']==prompt.encode().hex() and rr['tokens']==t and rr['readout']==len(t)-1 and rr['attention_mask']==[1]*len(t) and rr['answer_tokens']==answers
  assert rr['layout']=={'role_spans':[['text',0,len(t)]],'content_spans':[['text',0,len(t)]]} and t[0]==tok.bos_token_id
 supported=len(ct)==len(st);assert m['recipient_id']==m['donor_id']==row['instance_id'] and m['donor_stream']=='corrupt' and m['donor_condition']=='IOI' and m['operation']=='item_swap' and m['supported']==supported
 assert m['covered_positions']==(len(ct) if supported else 0) and m['recipient_positions']==(list(range(len(ct))) if supported else []) and m['donor_positions']==m['recipient_positions']
print('IOI raw generation, first eligible draw, token/readout and maps pass',flush=True)
mm=u['mmlu_manifest'];ms=Path(mm['snapshot']);assert ms.name==mm['revision']=='c30699e8356da336a370243923dbaf21066bb9fe'
parquets=sorted((ms/'all').glob('test-*.parquet'));assert {str(p.relative_to(ms)):FH(p) for p in parquets}==mm['parquet_hashes']
items=[]
for path in parquets:
 digest=FH(path)
 for i,q in enumerate(pq.read_table(path).to_pylist()):q.update(source_id=f'{path.relative_to(ms)}:{i:08d}',source_hash=digest);items.append(q)
# Neutral prompt formatting is specified exactly; do not import sandbagging prompts.
items.sort(key=lambda q:q['source_id']);meligible=[];rejected=Counter(malformed=0,overlength=0,contextual_tokens=0);prompts=[];validitems=[]
for q in items:
 choices=q.get('choices');a=q.get('answer')
 validq=isinstance(choices,list) and len(choices)==4 and all(isinstance(v,str) and v.strip() for v in choices) and isinstance(q.get('question'),str) and bool(q['question'].strip()) and not isinstance(a,bool) and isinstance(a,(int,float)) and int(a)==a and 0<=int(a)<4
 if not validq:rejected['malformed']+=1;continue
 block=q['question'].strip()+'\n\n'+'\n'.join(f'{letter}: {choice}' for letter,choice in zip('ABCD',choices))
 prompt=tok.apply_chat_template([{'role':'system','content':'Answer the multiple-choice question. Respond with only the correct letter.'},{'role':'user','content':block}],tokenize=False,add_generation_prompt=True)+'Answer:'
 prompts.extend([prompt]+[prompt+' '+letter for letter in 'ABCD']);validitems.append((q,prompt))
enc=batch(prompts);it=iter(enc)
for q,prompt in validitems:
 t=next(it);ext=[next(it) for j in range(4)]
 if len(t)>1024:rejected['overlength']+=1;continue
 if any(v[:-1]!=t or len(v)!=len(t)+1 for v in ext) or len({v[-1] for v in ext})!=4:rejected['contextual_tokens']+=1;continue
 meligible.append((q,prompt,t,[v[-1] for v in ext]))
chosen=random.Random(1).sample(meligible,32);assert mm['eligible']==len(meligible) and mm['rejected']==dict(rejected) and mm['sample_ids']==[q['source_id'] for q,p,t,a in chosen]
assert mm['sample_hash']==U(u['mmlu']) and mm['adapter_source_hash']==FH(R/'component_analysis/ladder_tasks.py')
# Hash exactly the raw formatter definition as stored by inspect.getsource.
formatter=(R/'evaluation/benchmarks/sandbagging.py').read_text();tree=ast.parse(formatter);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='format_question');source='\n'.join(formatter.splitlines()[fn.lineno-1:fn.end_lineno])+'\n';assert hashlib.sha256(source.encode()).hexdigest()==mm['prompt_format_hash']
assert mm['tokenizer_identity']['chat_template_hash']==U(tok.chat_template)
for row,data in zip(u['mmlu'],chosen):
 q,prompt,t,answers=data;rr=row['streams']['clean'];gold=int(q['answer']);assert row['source_id']==q['source_id'] and row['source_hash']==q['source_hash'] and row['source_revision']==ms.name and row['question_hash']==U(q['question'])
 assert row['instance_id']=='mmlu:'+q['source_id'] and row['gold_letter']=='ABCD'[gold] and row['choice_tokens']==answers and row['expected_token']==row['honest_token']==answers[gold]
 assert rr['prompt']==prompt and rr['prompt_utf8_hex']==prompt.encode().hex() and rr['tokens']==t and rr['readout']==len(t)-1 and rr['attention_mask']==[1]*len(t) and rr['answer_tokens']==answers and rr['layout'] is None
for i,(row,m) in enumerate(zip(u['mmlu'],u['mmlu_maps'])):
 pp=[q for q in u['mmlu'][i+1:]+u['mmlu'][:i] if q['instance_id']!=row['instance_id'] and q['question_hash']!=row['question_hash']];donor=next((q for q in pp if q['gold_letter']!=row['gold_letter']),pp[0])
 assert m['recipient_id']==row['instance_id'] and m['donor_id']==donor['instance_id'] and m['operation']=='positive_calibration' and m['donor_stream']=='clean' and m['supported'] and m['recipient_positions']==[row['streams']['clean']['readout']] and m['donor_positions']==[donor['streams']['clean']['readout']] and m['covered_positions']==m['requested_positions']==1
result['utility']={'seed':x['seed'],'ioi_rows':len(ioi),'ioi_generated':1000,'ioi_eligible_unique':len(eligibleioi),'ioi_source_hash':ioisource,'ioi_draw_and_tokens_pass':True,'ioi_supported_item_swap':sum(m['supported'] for m in u['ioi_maps']),'mmlu_rows':len(u['mmlu']),'mmlu_revision':ms.name,'mmlu_parquet_hashes':mm['parquet_hashes'],'mmlu_raw_rows':len(items),'mmlu_eligible':len(meligible),'mmlu_rejected':dict(rejected),'mmlu_source_ids':mm['sample_ids'],'mmlu_sample_hash':mm['sample_hash'],'mmlu_calibration_supported':sum(m['supported'] for m in u['mmlu_maps']),'mmlu_nested_grader_registry':mm['grader_registry'],'correctness_filter_used':False,'token_readout_and_prompt_checks':'pass'}
result['verdict']='original frozen semantic design passes CPU audit; changed code requires new prepared artifact with exact semantic equality before selection'
(O/'50-ladder-design-audit-calculations.json').write_text(json.dumps(result,indent=2)+'\n');print('MMLU raw parquet draw and complete audit pass',flush=True)
