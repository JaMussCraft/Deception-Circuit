from pathlib import Path
import ast,json,hashlib,tempfile,types,os
E=Path(__file__).parent;source=E/'final-a2-b2-scientific-launch.py';tree=ast.parse(source.read_text());functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('sha','key','validate_full_receipt','main')]
V=Path('/projects/beto/swong2/Alignment');W=V/'Deception-Circuit/.claude/worktrees/specificity-ladder';R=W/'outputs/_analyses/specificity-ladder/a2-runtime-6bd8bf5/runtime';C='6bd8bf5334f2e83613a129d2fcfeacf83e762191';plan=json.loads((E/'final-scientific-replacement-proposal.json').read_text());cell=plan['cells'][0];cellkey='sdr_v2-D-seed42';freeze=json.loads((E/'final-scientific-script-freeze.json').read_text())
results={}
for damage in ('none','receipt','output','dangling_receipt','dangling_output','output_after_auth','cache_after_auth','cancel_flag','wrong_cell','wrong_launcher'):
 with tempfile.TemporaryDirectory(prefix='review125-outer-') as temp:
  P=Path(temp);A=P/'Alignment';(P/'deployment').mkdir();(P/'logs').mkdir();proposal=P/'deployment/scientific-replacement-proposal.json';proposal.write_text(json.dumps(plan));fleet=A/(W/'outputs/_analyses/specificity-ladder/a2-fleet-6bd8bf5-h200/fleet-plan.json').relative_to(V);fleet.parent.mkdir(parents=True);fleet.write_bytes((W/'outputs/_analyses/specificity-ladder/a2-fleet-6bd8bf5-h200/fleet-plan.json').read_bytes());jobscript=P/'deployment/a2-b2-scientific-job.sh';jobscript.write_bytes((E/'final-a2-b2-scientific-job.sh').read_bytes());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();receipt=A/Path(cell['original_fleet_cell']['receipt']).relative_to(V);output=A/Path(cell['virtual_output_dir']).relative_to(V);receipt.parent.mkdir(parents=True,exist_ok=True);output.parent.mkdir(parents=True,exist_ok=True)
  placement={'jobs':{'777':{'cell_key':cellkey,'requested_minutes':cell['requested_minutes'],'source_commit':C,'virtual_output_dir':cell['virtual_output_dir']}},'proposal_sha256':sha(proposal),'launcher_sha256':sha(source),'job_script_sha256':sha(jobscript),'all_original_delta_jobs_cancelled_before_release':True}
  if damage=='cancel_flag':placement['all_original_delta_jobs_cancelled_before_release']=False
  if damage=='wrong_cell':placement['jobs']['777']['cell_key']='other'
  if damage=='wrong_launcher':placement['launcher_sha256']='0'*64
  (P/'deployment/scientific-placement.json').write_text(json.dumps(placement));events=[]
  if damage in ('receipt','output'):(receipt if damage=='receipt' else output).mkdir()
  if damage.startswith('dangling_'):(receipt if damage=='dangling_receipt' else output).symlink_to(P/'missing')
  def cache_check():
   events.append('cache')
   if damage=='cache_after_auth' and 'authorize' in events:raise AssertionError('changed current cache')
   return {'synthetic_fixture':True}
  def authorize(*args):
   events.append('authorize')
   if damage=='output_after_auth':output.mkdir()
   return 'fixture-auth'
  def child(*args,**kwargs):
   events.append('child')
   body={'status':'success','exit_code':0,'errors':[],'test_runner_injected':False,'test_clock_injected':False,'purpose':'scientific-seed','actual_epochs':500,'planned_epochs':500,'execution_commit':C,'source_commit':'77b6487b08b4410a4e5a9995c6ff5e46834a5ce3','task':'sdr_v2','condition':'D','seed':42,'gpu_count':1,'gpu_devices':['H100 fixture'],'environment':{'SLURM_JOB_ID':'777','SLURM_CLUSTER_NAME':'bridges2'}};receipt.write_text(json.dumps(body));return types.SimpleNamespace(returncode=0)
  ns={'Path':Path,'os':types.SimpleNamespace(environ={'SLURM_JOB_ID':'777','CUDA_VISIBLE_DEVICES':'0'}),'sys':types.SimpleNamespace(argv=['fixture','run',cellkey]),'json':json,'time':__import__('time'),'subprocess':types.SimpleNamespace(run=child),'hashlib':hashlib,'P':P,'A':A,'V':V,'W':W,'R':R,'C':C,'IMAGE':P/'image','__file__':str(source),'cache_check':cache_check,'authorize':authorize,'phase':lambda *a,**k:None,'dump':lambda *a,**k:None}
  exec(compile(ast.Module(body=functions,type_ignores=[]),'<exact-frozen-main>','exec'),ns)
  try:ns['main']();rejected=False
  except AssertionError:rejected=True
  if damage=='none':assert not rejected and events==['cache','authorize','cache','child'],events
  else:assert rejected and 'child' not in events,(damage,events)
  results[damage]={'rejected':rejected,'events':events}
(E/'final-outer-boundary-check.json').write_text(json.dumps({'launcher_sha256':sha(source),'cases':results,'no_actual_child_or_remote_or_model':True,'synthetic_schema_positive_only':True},indent=2))
print('final exact-main10fixture cases pass')
