import ast,json,tempfile,pathlib,types,hashlib,copy
D=pathlib.Path(__file__).resolve().parent;L=D/'launch';source=(L/'controller.py').read_text()
pre=source[:source.index('ACTIVE=subprocess.Popen')]
assert pre.rfind('allocation(gpu=True,release=release)')>pre.rfind('budget(prospective=False,release=release)')
post=source[source.index("assert ACTIVE.returncode==0"):]
assert post.index('allocation(gpu=True,release=release)')<post.index('p,ar=imports()')
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='bounded_work_end');ns={'C':{'finish_reserve_seconds':300}};exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual_deadline>','exec'),ns)
assert ns['bounded_work_end'](10000,11000,8000)==(10000,9700)
assert ns['bounded_work_end'](10000,9000,8000)==(9000,8700)
negative=[]
for observed,now in [(9000,8700),(9000,9001)]:
 try:ns['bounded_work_end'](10000,observed,now)
 except TimeoutError:negative.append('expired_lease_'+str(now))
 else:raise AssertionError('expired lease accepted')
node=next(n for n in ast.parse((L/'common.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='no_retry');ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual_noretry>','exec'),ns);ns['no_retry']({'Requeue':'0','Restarts':'0'})
for d in [{'Requeue':'1','Restarts':'0'},{'Requeue':'0','Restarts':'1'},{}]:
 try:ns['no_retry'](d)
 except AssertionError:negative.append('requeue_restart_or_missing')
 else:raise AssertionError('retry accepted')
with tempfile.TemporaryDirectory(prefix='a2-score-release-') as td:
 T=pathlib.Path(td);C=dict(commit='a'*40,groups_file_sha256='b'*64,main_root='/main',bank_file_sha256='c'*64,bank_manifest_sha256='d'*64);(T/'manifest.json').write_text('{}')
 def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
 preflight=dict(complete=True,launch_manifest_sha256=sha(T/'manifest.json'),bank_file_sha256='c'*64,bank_manifest_sha256='d'*64,source=dict(source_commit='a'*40,groups_file_sha256='b'*64));(T/'complete.json').write_text(json.dumps(preflight))
 good=dict(launch_manifest_sha256=sha(T/'manifest.json'),allowed_partitions=['gpuH200x8'],source_commit='a'*40,groups_file_sha256='b'*64,main_root='/main',full_scoring_admitted=True,score_only=True,bank_rebuild_authorized=False,current_usage_pass=True,bank_file_sha256='c'*64,bank_manifest_sha256='d'*64,job_id='unit-fixture',preflight_complete_path=str(T/'complete.json'),preflight_complete_sha256=sha(T/'complete.json'))
 env={'A2_SCORE_ROOT_RELEASE':str(T/'release.json'),'SLURM_JOB_ID':'unit-fixture'};ns=dict(os=types.SimpleNamespace(environ=env),pathlib=pathlib,json=json,C=C,L=T,sha=sha)
 node=next(n for n in ast.parse((L/'common.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='gpu_release');exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual_release_gate>','exec'),ns)
 (T/'release.json').write_text(json.dumps(good));assert ns['gpu_release']()==good
 for k,value in [('full_scoring_admitted',False),('score_only',False),('bank_rebuild_authorized',True),('current_usage_pass',False),('allowed_partitions',['gpuA100x4']),('source_commit','e'*40),('groups_file_sha256','e'*64),('bank_file_sha256','e'*64),('job_id','wrong'),('preflight_complete_sha256','e'*64)]:
  r=copy.deepcopy(good);r[k]=value;(T/'release.json').write_text(json.dumps(r))
  try:ns['gpu_release']()
  except AssertionError:negative.append('release_'+k)
  else:raise AssertionError('bad release accepted '+k)
 preflight['complete']=False;(T/'complete.json').write_text(json.dumps(preflight));r=copy.deepcopy(good);r['preflight_complete_sha256']=sha(T/'complete.json');(T/'release.json').write_text(json.dumps(r))
 try:ns['gpu_release']()
 except AssertionError:negative.append('false_preflight')
 else:raise AssertionError('false preflight accepted')
(D/'operational-stdlib-checks.json').write_text(json.dumps(dict(method='Exact current controller/common AST, tiny stdlib-only clock/release transport fixtures; no application/model/allocation execution',fresh_actual_lease_check_before_Popen=True,post_success_boundary_before_output_parsing=True,earlier_deadline_shrinks=True,extension_not_used=True,no_requeue_single_attempt=True,positive_release_pass=True,negative_count=len(negative),negatives=negative),indent=2)+'\n')
print('OPERATIONAL_STDLIB_PASS',len(negative))
