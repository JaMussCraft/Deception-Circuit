"""NON-SCIENTIFIC schema envelopes. No model/forward/outcome interfaces."""
import ast,copy,hashlib,json,sys
FLOAT_SLOT='UNKNOWN_FINITE_FLOAT_SLOT'
INT_SLOT='UNKNOWN_INTEGER_SLOT_UPPER'
BOOL_SLOT='UNKNOWN_BOOLEAN_SLOT'
BASE=set('task instance_id condition stream group group_members operation expected_token opposite_token honest_token pressure_id source_provenance donor_provenance donor_seed self_replay_margin_error assay_valid supported degenerate gate_valid'.split())
ALIAS=set('group_source a2_group_sha256 a2_receipt_sha256 training_seed compute_alias'.split())
CONTROL=set('task instance_id stream max_abs_logit_error valid donor_choice_differs donor_provenance sender_keys mechanism_task condition'.split())
def need(ok,message):
 if not ok:raise ValueError(message)
def metric_types(choice=False):
 d={k:'float' for k in ('margin','raw_margin','native_margin','native_raw_margin')};d.update(argmax='int',native_argmax='int',correct='bool',binary_win='bool')
 if choice:d.update(choice_margin='float',choice_correct='bool')
 return d
def function(text,name):return next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
def verify_runner_schema(text):
 node=function(text,'score_cell');assign=next(n for n in ast.walk(node) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='record' for t in n.targets))
 need(isinstance(assign.value,ast.Call) and {k.arg for k in assign.value.keywords}==BASE,'unmodelled native record fields')
 stats=function(text,'_stats');a=next(n for n in ast.walk(stats) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='result' for t in n.targets))
 need({k.arg for k in a.value.keywords}==set(metric_types()),'native _stats base fields drift')
 extra={n.targets[0].slice.value for n in ast.walk(stats) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Subscript) and isinstance(n.targets[0].slice,ast.Constant) and isinstance(n.targets[0].slice.value,str)}
 need(extra=={'choice_margin','choice_correct'},'native choice branch drift')
 return {'record_fields':sorted(BASE),'metric_types':metric_types(True)}
def verify_append_schema(text):
 node=function(text,'score');append=next(n for n in ast.walk(node) if isinstance(n,ast.FunctionDef) and n.name=='append')
 calls=[n for n in ast.walk(append) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='deepcopy']
 need(any(ast.dump(c.args[0])==ast.dump(ast.parse('group["members"]',mode='eval').body) for c in calls),'alias members no longer deep-copied')
 need(any(ast.dump(c.args[0])==ast.dump(ast.parse('references[group["task"]]',mode='eval').body) for c in calls),'compact bank reference conversion drift')
 return {'alias_fields':sorted(ALIAS),'member_semantics':'deepcopy','source_provenance_semantics':'shallow reference'}
def verify_function_pins(texts,contract):
 for file,functions in contract.items():
  for name,pin in functions.items():
   actual=hashlib.sha256(ast.dump(function(texts[file],name),include_attributes=False).encode()).hexdigest()
   need(actual==pin,'native emitted branch/function drift: '+file+':'+name)
def bound_row(row,source,mapping,operation,name,group,compute,receipt_sha,bank_reference,choice):
 members=group['members'];supported=mapping is None or mapping['supported']
 r=dict(task=row['task'],instance_id=row['instance_id'],condition=row['condition'],stream=row['stream'],group=name,group_members=copy.deepcopy(members),operation=operation,expected_token=row['expected_token'],opposite_token=row['opposite_token'],honest_token=row['honest_token'],pressure_id=str(source.get('pressure_id',row['instance_id'])),source_provenance=source,donor_provenance=mapping,donor_seed=mapping.get('seed') if mapping else None,self_replay_margin_error=FLOAT_SLOT,assay_valid=BOOL_SLOT,supported=bool(supported),degenerate=operation in ('self_replay','empty') or not members,gate_valid=operation not in ('self_replay','empty') and bool(members),group_source='matched_pressure_twin',a2_group_sha256=group['membership_sha256'],a2_receipt_sha256=receipt_sha,training_seed=group['training_seed'],compute_alias=compute)
 if mapping is not None:r.update(degenerate=mapping.get('degenerate',False) or not members,gate_valid=mapping.get('gate_valid',False) and bool(members))
 if not supported:r['unsupported_reason']=mapping.get('unsupported_reason')
 else:
  for prefix in ('intact','patched'):
   for k,t in metric_types(choice).items():r[prefix+'_'+k]={'float':FLOAT_SLOT,'int':INT_SLOT,'bool':BOOL_SLOT}[t]
  if operation=='h_mean':r['mean_bank_provenance']=copy.deepcopy(bank_reference)
 validate_row_fields(r,choice);return r
def validate_row_fields(row,choice):
 expected=BASE|ALIAS
 if not row['supported']:expected=expected|{'unsupported_reason'}
 else:
  expected=expected|{p+'_'+k for p in ('intact','patched') for k in metric_types(choice)}
  if row['operation']=='h_mean':expected=expected|{'mean_bank_provenance'}
 need(set(row)==expected,'missing/unmodelled metadata/metric fields')
def bound_control(row,mapping,keys,task):
 c=dict(task=row['task'],instance_id=row['instance_id'],stream=row['stream'],max_abs_logit_error=FLOAT_SLOT,valid=BOOL_SLOT,donor_choice_differs=BOOL_SLOT,donor_provenance=mapping,sender_keys=[list(k) for k in keys],mechanism_task=task,condition=row['condition']);validate_control(c,keys);return c
def validate_control(control,keys):
 need(set(control)==CONTROL and control['sender_keys']==[list(k) for k in keys],'control field/sender coverage drift')
def json_size(value,*,ensure_ascii=True,compact=False):
 enc=json.JSONEncoder(sort_keys=True,allow_nan=False,ensure_ascii=ensure_ascii,**({'separators':(',',':')} if compact else {}));return sum(len(c.encode()) for c in enc.iterencode(value))
def encoder_accounting(value,*,compact=False):
 enc=json.JSONEncoder(sort_keys=True,allow_nan=False,**({'separators':(',',':')} if compact else {}));n=0;volume=0;chunks=0
 for c in enc.iterencode(value):n+=1;volume+=len(c.encode());chunks+=sys.getsizeof(c)
 # All output ASCII under actual default ensure_ascii; retain every pure-python
 # scalar chunk as a conservative C-encoder chunk/list envelope, plus full str,
 # UTF8 bytes and list over-allocation. No streaming-hash substitution.
 return dict(bytes=volume,chunks=n,chunk_object_bytes=chunks,full_encoding_overlap_bound=chunks+16*n+3*volume+4096)
def graph_sizes(value):
 seen=set();active=set();memo={};unique=[0]
 def walk(v):
  ident=id(v)
  need(ident not in active,'cyclic graph forbidden')
  if ident in memo:return memo[ident]
  active.add(ident)
  own=sys.getsizeof(v)
  if ident not in seen:seen.add(ident);unique[0]+=own
  if isinstance(v,dict):total=own+sum(walk(k)+walk(x) for k,x in v.items())
  elif isinstance(v,(list,tuple,set,frozenset)):total=own+sum(walk(x) for x in v)
  else:need(v is None or isinstance(v,(str,int,float,bool)),'non-JSON graph class');total=own
  active.remove(ident);memo[ident]=total;return total
 no_share=walk(value);return unique[0],no_share
