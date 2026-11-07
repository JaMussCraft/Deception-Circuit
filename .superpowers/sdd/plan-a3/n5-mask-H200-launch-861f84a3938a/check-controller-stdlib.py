import ast,json,hashlib,types,re,tempfile,copy
from pathlib import Path
G=Path(__file__).resolve().parent;cfg=json.loads((G/'launch-config.json').read_text());B=Path(cfg['runtime'])
ns=dict(Path=Path,json=json,hashlib=hashlib,cfg=cfg,G=G,B=B);ns['sha']=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
node=next(n for n in ast.parse((B/'component_analysis/a3_direction_runtime.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='_slurm_memory_bytes')
def require(value,message):
 if not value:raise ValueError(message)
memns=dict(re=re,require=require);exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual_memory_parser>','exec'),memns);ns['authority']=types.SimpleNamespace(_slurm_memory_bytes=memns['_slurm_memory_bytes'])
for file,names in [('render-root-binding.py',['check_held_request']),('run-bounded-pilot.py',['deadlines','completed_receipt'])]:
 nodes=[n for n in ast.parse((G/file).read_text()).body if isinstance(n,ast.FunctionDef) and n.name in names];exec(compile(ast.Module(body=nodes,type_ignores=[]),'<exact_controller_functions>','exec'),ns)
assert ns['deadlines'](1000,2000)==(640,700) and ns['deadlines'](1000,900)==(540,600)
facts=dict(JobId='999',JobState='PENDING',Reason='JobHeldUser',Account=cfg['account'],Partition='gpuH200x8',WorkDir=str(B),RunTime='00:00:00',NumCPUs='4',TimeLimit='00:45:00',Requeue='0',Restarts='0',ReqTRES='cpu=4,mem=64G,gres/gpu=1',Command=str(G/'jobscript.sh'))
for part in cfg['allowed_partitions']+[cfg['partition']]:
 facts['Partition']=part;assert ns['check_held_request'](facts,'999',cfg['account'])
negatives=[]
for key,value in [('Partition','gpuA100x4'),('TimeLimit','01:00:00'),('Requeue','1'),('Restarts','1'),('ReqTRES','cpu=4,mem=32G,gres/gpu=1'),('ReqTRES','cpu=4,mem=64G,gres/gpu=10'),('Account','other'),('Command','/tmp/other.sh')]:
 d=dict(facts);d[key]=value
 try:ns['check_held_request'](d,'999',cfg['account'])
 except (AssertionError,ValueError):negatives.append(key+'='+value)
 else:raise AssertionError('held negative accepted '+key)
release=dict(job_id='999',reservation_id='r-new',pilot_inventory_sha256='a'*64,full_target_inventory_sha256='b'*64)
receipt=dict(kind='a3_mask_pilot_v2',complete=True,exit_code=0,injected=False,identity=dict(commit=cfg['commit']),reservation_id='r-new',allocation_job_id='999',pilot_inventory_sha256='a'*64,target_inventory_sha256='b'*64,purpose='validation_timing',timing_only=True,final=False,may_select_checkpoint=False,arms=['constrained','unconstrained'],hardware='NVIDIA H200',arm_measurements=[dict(arm=a,source_split='validation',purpose='validation_timing') for a in ['constrained','unconstrained']],measurements={k:[{}] for k in ['base_proof','targets','update','validation','binary_parity','checkpoint','selection','guard_initial','guard']+[k+':'+task for task in ['far_v2','sdr_v2','ser_v2'] for k in ['H_bank','assessment']]});receipt['measurements']['guard']=[dict(scope=dict(refreshes=1185))]
with tempfile.TemporaryDirectory(prefix='n5-launch-stdlib-') as td:
 root=Path(td)
 def publish(r):
  (root/'payload.json').write_text(json.dumps(r));raw=(root/'payload.json').read_bytes();(root/'COMPLETE.json').write_text(json.dumps(dict(kind='a3_complete',files={'payload.json':dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())})))
 publish(receipt);assert ns['completed_receipt'](root,release)['complete']
 for key,value in [('complete',False),('injected',True),('reservation_id','other'),('target_inventory_sha256','c'*64),('purpose','scientific_training'),('arms',['constrained'])]:
  r=copy.deepcopy(receipt);r[key]=value;publish(r)
  try:ns['completed_receipt'](root,release)
  except AssertionError:negatives.append('receipt.'+key)
  else:raise AssertionError('bad receipt accepted '+key)
 r=copy.deepcopy(receipt);del r['measurements']['H_bank:ser_v2'];publish(r)
 try:ns['completed_receipt'](root,release)
 except AssertionError:negatives.append('receipt.missing_required_bank')
 else:raise AssertionError('reduced control accepted')
(G/'stdlib-controller-checks.json').write_text(json.dumps(dict(method='Exact current controller AST; tiny stdlib-only transport/clock/receipt fixtures, no application/model/job execution',normal_interactive_declared_list_pass=True,deadline_extension_refused=True,earlier_end_shrinks_deadline=True,complete_exact_nonfinal_receipt_pass=True,negative_count=len(negatives),negatives=negatives,first_attempt_note='The initial AST harness omitted globalB; corrected harness namespace only, no controller change.'),indent=2)+'\n')
print('STDLIB_CONTROLLER_CHECKS_PASS',len(negatives))
