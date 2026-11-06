"""CPU-only native A2 structural shape proof; no model and no effect reads."""
import argparse,collections,hashlib,json,os,resource,subprocess,sys,time
from pathlib import Path

def distribution(pairs):
 lengths=sorted(x for x,_ in pairs); widths=collections.Counter(str(w) for _,w in pairs)
 def quantile(q):return lengths[int((len(lengths)-1)*q)] if lengths else None
 return dict(n=len(pairs),min=min(lengths) if lengths else None,max=max(lengths) if lengths else None,p50=quantile(.5),p90=quantile(.9),p99=quantile(.99),unpadded_tokens=sum(x for x,_ in pairs),padded_tokens=sum(w for _,w in pairs),padded_squared_tokens=sum(w*w for _,w in pairs),lengths=dict(collections.Counter(map(str,lengths))),parent_widths=dict(widths))
def add_exposure(d,key,width,count):
 item=d.setdefault(key,dict(forwards=0,padded_tokens=0,padded_squared_tokens=0));item['forwards']+=count;item['padded_tokens']+=width*count;item['padded_squared_tokens']+=width*width*count

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--manifest-sha256',required=True);a=ap.parse_args();P=Path(__file__).resolve().parent
 def packet():
  assert sha(P/'manifest.json')==a.manifest_sha256
  for n,h in read(P/'manifest.json').items():assert sha(P/n)==h,n
 packet();out=Path(a.output);out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
 W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');R=W/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime';G=W/'outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1';D=W/'.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103/root-H100-R5/job-50189932';F=D/'actual-completed-20261106';V=Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research/specificity-ladder/reports/177-h100-timing-evidence/verdict.json')
 job=os.environ['SLURM_JOB_ID'];facts=subprocess.check_output(['scontrol','show','job',job,'-o'],text=True,timeout=15,env=dict(os.environ,TZ='UTC'));fields=dict(x.split('=',1) for x in facts.split() if '=' in x);assert fields['JobState']=='RUNNING' and fields['NumCPUs']=='4' and fields['Partition'].startswith('cpu') and fields['Account'].endswith('-cpu') and 'gres/gpu' not in fields.get('AllocTRES','')
 assert sha(V)=='79bacf2ae71cfaa68424aa71d378618737fda05b852724164adbe87fdb31a707';verdict=read(V);assert verdict['verdict']=='ACCEPT_GENUINE_H100_BANK_AND_PREFIX4_TIMING_CONTROLS_ONLY' and verdict['full_domain_expected_rows']==59652 and verdict['full_domain_expected_controls']==3396
 assert sha(G/'groups.json')=='c3095b10aac09a23ee35e4620402581b0407623d1e111a2407a691f60f599de4';assert sha(F/'bank/banks.json')=='a8afbd51a994a6346d1bb8c832b68cab0ea42c83a195c22a29aae4016723e00b'
 assert sha(R.parent/'snapshot.json')=='68cc15073e383d0943620cab4271a9ee859ae51203e69704b83cca8ac7770f77';snapshot=read(R.parent/'snapshot.json');assert snapshot['source_commit']=='50e947bb852613e3a270082651f2bd1b7bb0c525' and len(snapshot['source_sha256'])==511 and len(snapshot['input_links'])==4
 def source():
  for n,h in snapshot['source_sha256'].items():assert sha(R/n)==h,n
  for n,t in snapshot['input_links'].items():assert (R/n).is_symlink() and os.readlink(R/n)==t,n
 source();os.chdir(R);sys.path.insert(0,str(R));from component_analysis import a2_pipeline as p
 from component_analysis.ladder_tasks import task_batches
 from component_analysis.specificity_ladder import _rows
 assert Path(p.__file__).resolve()==R/'component_analysis/a2_pipeline.py'
 cfg=read(D/'config.json');cmd=read(F/'execution/bank-command.json')['command'];args=p.parser().parse_args(cmd[2:]);prepared,selected,sidecar=p._load_context(args);args.tasks=list(p.TASKS)
 for k in ('model','model_revision','tokenizer_revision'):setattr(args,k,prepared[k])
 args.injected=False;receipt=p.a1.read_artifact(G/'groups.json');p._validate_live(args,receipt,prepared)
 assert sha(G/'bank/banks.json')==sha(F/'bank/banks.json');bank=p.read_stage(G/'bank','banks.json','bank',args,receipt);p.validate_banks(receipt,prepared,bank);assert p.hash_content(bank)=='17045db1a43c7a4e53f31edb2e2719367b2efc1665dc6081880dc45f122ec1a1';assert not bank['injected'] and not receipt['injected'] and not prepared['injected']
 tokenizer=p.a1.common.load_tokenizer(args);p.a1.validate_tokenization(prepared,tokenizer);p._validate_live(args,receipt,prepared)
 def unpack(batches):
  data={};shapes=collections.Counter()
  for b in batches:
   shapes[str(tuple(b.input_ids.shape))]+=1
   for one in _rows(b):
    key=(one.condition,one.ids[0],one.stream);assert key not in data
    data[key]=(int(one.attention_mask.sum()),int(one.input_ids.shape[1]))
  return data,dict(shapes)
 def summarize(label,rs,ds,groups,ops,maps,exposure,domains,shapes,support):
  r,rb=unpack(rs);d,db=unpack(ds)
  def by_domain(items):
   values=collections.defaultdict(list)
   for (condition,rid,stream),pair in items.items():values[condition+'|'+stream].append(pair)
   return {key:distribution(value) for key,value in values.items()}
  domains[label]={'recipients':by_domain(r),'donors':by_domain(d)};shapes[label]={'recipient_batch_shapes':rb,'donor_batch_shapes':db}
  byop={}
  for m in maps:
   key=(m['recipient_condition'],m['recipient_id'],m['recipient_stream']);index=byop.setdefault(m['operation'],{});assert key not in index,'duplicate frozen donor map';index[key]=m
  for op in ops:
   for key,(_,rw) in r.items():
    m=byop.get(op,{}).get(key); donor_required=op not in ('zero','h_mean','self_replay','empty');assert not donor_required or m is not None
    supported=not donor_required or m['supported'];support[label+'|'+op+'|'+('supported' if supported else 'unsupported')]+=1;add_exposure(exposure,label+'|'+op+'|recipient',rw,1+2*groups+(groups if supported else 0))
    if donor_required and supported:
     dk=(m['donor_condition'],m['donor_id'],m['donor_stream']);add_exposure(exposure,label+'|'+op+'|donor',d[dk][1],1)
  # Positive control uses 3 captures at common max padded width; mapped recipient/donor parent widths retained.
  for key,(_,rw) in r.items():
   m=byop['item_swap'][key] if label.endswith('|assessment') else next(m for m in maps if (m['recipient_condition'],m['recipient_id'],m['recipient_stream'])==key)
   assert label.endswith('|assessment') or label.endswith('|ioi') or m['supported'];dk=(m['donor_condition'],m['donor_id'],m['donor_stream']);width=max(rw,d[dk][1]);add_exposure(exposure,label+'|positive',width,3)
 def collect(limit):
  expected=p.expected_keys(receipt,limit);positive=p.a1.positive_keys(p._prepared_domain(receipt),limit);assert len(expected)==len(set(expected))==(2484 if limit else 59652);assert len(positive)==len(set(positive))==(144 if limit else 3396)
  coverage=collections.Counter('|'.join(map(str,(x[0],x[2],x[3],x[4],x[5]))) for x in expected);exp={};domains={};shapes={};groups_meta={};support=collections.Counter()
  for task in p.TASKS:
   frozen=prepared['designs'][task];ids=frozen['assessment_ids'][:limit or None];source_rows=prepared['rows'][task];groups,aliases=p._groups_for_compute(receipt,task);groups_meta[task]={'compute_groups':len(groups),'aliases':sum(map(len,aliases.values())),'union_keys':len(receipt['bank_keys'][task])}
   rs=[b for c in p.a1.design.CONDITIONS for s in p.a1.design.STREAMS for b in p.a1.batches([r for r in source_rows[c] if r['instance_id'] in ids],s,batch_size=8)];ds=[b for c in p.a1.design.CONDITIONS for s in p.a1.design.STREAMS for b in p.a1.batches(source_rows[c],s,batch_size=8)];maps=[m for m in frozen['donors'] if m['recipient_id'] in ids]
   assert not receipt['independent_donor_seeds'],'unsupported optional donor seeds; stop for review'
   summarize(task+'|assessment',rs,ds,len(groups),receipt['operations'],maps,exp,domains,shapes,support)
   for utility in ('ioi','mmlu'):
    rows=prepared['utility'][utility][:limit or None];rs=task_batches(rows,batch_size=8);ds=task_batches(prepared['utility'][utility],stream='corrupt' if utility=='ioi' else 'clean',batch_size=8);ids2={r['instance_id'] for r in rows};maps=[m for m in prepared['utility'][utility+'_maps'] if m['recipient_id'] in ids2];ops=('item_swap','zero','h_mean','self_replay','empty') if utility=='ioi' else ('zero','h_mean','self_replay','empty');summarize(task+'|'+utility,rs,ds,len(groups),ops,maps,exp,domains,shapes,support)
  totals={k:sum(v[k] for v in exp.values()) for k in ('forwards','padded_tokens','padded_squared_tokens')};return dict(rows=len(expected),positive_controls=len(positive),coverage=dict(coverage),groups=groups_meta,domains=domains,batch_shapes=shapes,support_coverage=dict(support),exposure=exp,totals=totals)
 prefix=collect(4);full=collect(0);source();p._validate_live(args,receipt,prepared);packet();ratios={k:full['totals'][k]/prefix['totals'][k] for k in full['totals']};ratios['rows']=full['rows']/prefix['rows'];usage=resource.getrusage(resource.RUSAGE_SELF);fs=os.statvfs(out);prefix_bytes=(F/'pilot/score/score.json').stat().st_size
 result=dict(kind='a2_full_shape_cpu_only',source_commit=cfg['commit'],source_files=511,source_links=4,bank_sha256=sha(F/'bank/banks.json'),verdict_sha256=sha(V),allocation=fields,full=full,prefix=prefix,ratios=ratios,peak_rss_bytes=usage.ru_maxrss*1024,elapsed_seconds=time.monotonic()-start,bank_bytes=(F/'bank/banks.json').stat().st_size,prefix_score_file_bytes=prefix_bytes,full_row_linear_storage_orientation_bytes=prefix_bytes*full['rows']/prefix['rows'],output_filesystem_available_bytes=fs.f_bavail*fs.f_frsize,output_filesystem_available_inodes=fs.f_favail,limitations=['Shape exposure is not a runtime upper bound; kernels, overhead, memory and I/O are not measured.','Exposure reconstructs score_cell and positive_control capture counts from native singleton views and frozen maps; independent review required.','No rigorous full GPU memory or serialized output upper bound; prefix payload and row-linear scaling are orientation only.','No model, score(), forward, effect file contents, or outcome aggregation used.'],model_loaded=False,effects_read=False,full_score_admitted=False)
 with (out/'RESULT.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
if __name__=='__main__':main()
