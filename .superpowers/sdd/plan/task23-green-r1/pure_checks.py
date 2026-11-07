import ast,copy,json,hashlib
from pathlib import Path
from types import SimpleNamespace
b=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd')
p=b/'plan-a3/direction-preallocation-candidate183/component_analysis/a3_direction_runtime.py'
t=ast.parse(p.read_text());wanted={'_validate_prepared_receiver_resources','_PreparedPilotTarget'}
nodes=[n for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in wanted]
def require(ok,msg):
 if not ok:raise ValueError(msg)
env=dict(require=require,Path=Path,common=SimpleNamespace(file_hash=lambda _: 'hash'),__file__=str(p),
 workload=SimpleNamespace(__file__='workload.py'),_PREPARED_RECIPE='recipe',_PREPARED_RESOURCE_SCOPE='scope',_PREPARED_TARGET_SEAL=object())
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(p),'exec'),env)
validate=env['_validate_prepared_receiver_resources'];source={'code_hashes':{'s':'h'}}
record=dict(kind='a3_prepared_target_receiver_resources_v1',references={},source_identity=source,reader_sha256='hash',freeze_sha256='hash',environment={},recipe='recipe',scope='scope',observed_io=dict(full_payload_reads=2,SHA_passes=2,parse_passes=1,freeze_passes=1,target_writes=0),provenance=dict(normal_completion=True,exit_code=0,source_before=source['code_hashes'],source_after=source['code_hashes']),model_loaded=False,execution_authorized=False,retained_metadata_bytes_bound=20,extra_transient_bytes_bound=30,process_peak_rss_bytes_bound=999,cgroup_peak_bytes_bound=999)
kwargs=dict(references={},source_identity=source,environment={},actual_host_capacity=100,existing_host_obligations=50)
assert validate(record,**kwargs)==dict(retained_metadata_bytes=20,extra_transient_bytes=30)
try:validate(record,**dict(kwargs,actual_host_capacity=99))
except ValueError:pass
else:raise AssertionError('99 should reject')
for field in ('recipe','scope','reader_sha256','freeze_sha256','references','source_identity','environment'):
 bad=copy.deepcopy(record);bad[field]='wrong'
 try:validate(bad,**kwargs)
 except ValueError:pass
 else:raise AssertionError(field+' should reject')
handle=object.__new__(env['_PreparedPilotTarget'])
try:handle.final_publication_barrier(None,{})
except ValueError:pass
else:raise AssertionError('forged handle should reject')
# Unmodified generic algorithms and accepted T1 helpers retain exact ASTs.
old=ast.parse((b/'plan/task23-red-r2/red-run-01').joinpath('run_manifest.json').read_text()) if False else None
original=(b/'plan-a3/direction-metadata-optionA-candidate/component_analysis/a3_direction_runtime.py')
old=ast.parse(original.read_text());olddefs={n.name:ast.dump(n,include_attributes=False) for n in old.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
newdefs={n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
for name in ('publish_object','read_object','object_reference','_FileWitness','_DependencyForest','_AuthorityContext','validate_reservation'):
 assert olddefs[name]==newdefs[name],name
print(json.dumps(dict(status='PASS',checks=12,scope='stdlib-only extracted resource arithmetic/identity, forged-handle rejection, static original-algorithm preservation',model_loaded=False)))
