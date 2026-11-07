"""Execute only extracted pure orchestration predicates against CPU fixtures."""
import ast,json,pathlib,time,hashlib
W=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');P0=W/'outputs/_analyses/specificity-ladder/a2-bridges2-20261102/remote-deployment';E=W/'docs/research/specificity-ladder/reports/120-a2-bridges-pilot-readiness-evidence';source=(P0/'a2-b2-launch.py').read_text();tree=ast.parse(source)
receipt=json.loads((W/'outputs/_analyses/specificity-ladder/a2-timing-6bd8bf5-h200/sdr_v2-D-seed42.json').read_text())
status_assert=next(n for n in ast.walk(tree) if isinstance(n,ast.Assert) and "body['status']" in ast.unparse(n.test))
accepted=eval(compile(ast.Expression(status_assert.test),'<actual outer success predicate>','eval'),{'body':receipt})
assert accepted is False and receipt['status']=='success'
fixture=E/'outer-contract-fixture';(fixture/'deployment').mkdir(parents=True,exist_ok=True);job='fixture-only-not-slurm';C='6bd8bf5334f2e83613a129d2fcfeacf83e762191';body=dict(job_id=job,arm='D',source_commit=C,purpose='timing-only',issued_at=time.time(),expires_at=time.time()+600,registries=[],fixture_only=True,execution_authorized=False)
(fixture/'deployment'/('authorization-'+job+'-D.json')).write_text(json.dumps(body)+'\n')
authorize=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='authorize');events=[]
ns=dict(P=fixture,job=job,C=C,json=json,time=time,Path=pathlib.Path,A=fixture,V=pathlib.Path('/projects/beto/swong2/Alignment'),phase=lambda x:events.append(x),sha=lambda x:(_ for _ in ()).throw(AssertionError('empty registry list should never call sha')))
exec(compile(ast.Module(body=[authorize],type_ignores=[]),'<actual authorize function>','exec'),ns);out=ns['authorize']('D');assert out['registries']==[]
r=dict(kind='independent_outer_launch_contract_counterexamples',launcher_sha256=hashlib.sha256(source.encode()).hexdigest(),genuine_saved_status=receipt['status'],actual_outer_success_expression=ast.unparse(status_assert.test),genuine_success_receipt_rejected=True,empty_fresh_registry_list_accepted=True,executed_only_extracted_predicates=True,real_authority_or_remote_job=False)
(E/'outer-contract-probe.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
