"""Distinct retry-invariant fixture correction; stdlib only, no production edits."""
import ast,collections,difflib,hashlib,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;S=P.parent
OLD=S/'plan-a2-whole-packet-correction321/packet-r4';NEW=P/'packet-r5'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
write=lambda p,v:Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
oldpins=read(OLD/'packet-pins.json')
assert sha(OLD/'packet-pins.json')=='88407b1745c6169afbf75de0d3789e5d10cb55cda88c4134580af58f6d1e679c'
assert all(sha(OLD/n)==h for n,h in oldpins.items())
assert not NEW.exists();NEW.mkdir()
for n in oldpins:
 dest=NEW/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(str(OLD/n),str(dest))
(NEW/'evidence').mkdir()
f=NEW/'candidate/tests/test_full_score_integration.py';before=f.read_text()
old="""    with pytest.raises((ValueError,FileExistsError)):controller.run_full_score(j.producer.g,r)
    with pytest.raises(FileExistsError):j.producer.publish()
    assert len(calls)==1 and j.events.count('publish')==1
"""
new="""    # A completed score must reject before any retry can rewrite evidence.
    # Real bank/input guards precede the duplicate-publication claim guard.
    retained_roots=(j.producer.work,j.cpu,Path(j.producer.g['main_root']),Path(j.producer.g['evidence_root']))
    def retry_state():
        paths={path for root in retained_roots for path in root.rglob('*') if path.is_file()}
        paths.add(Path(r['_release_path']))
        return {str(path):(path.stat().st_size,j.m.sha(path)) for path in paths}
    retained=retry_state();pending=Path(r['_release_path']+'.pending')
    assert not pending.exists() and not pending.is_symlink()
    with pytest.raises(ValueError,match='^score already exists or is symlink$'):
        controller.run_full_score(j.producer.g,r)
    with pytest.raises(ValueError,match='^score already exists or is symlink$'):
        j.producer.publish()
    assert retry_state()==retained
    assert not pending.exists() and not pending.is_symlink()
    assert (j.cpu/'COMPLETE.json').read_bytes()==before
    assert j.events.count('stage')==1 and not j.p._TASK4_MODEL_CALLS
    assert len(calls)==1 and j.events.count('publish')==1
"""
assert before.count(old)==1;after=before.replace(old,new)
old="""    assert not calls and not j.p._TASK4_MODEL_CALLS and 'publish' not in j.events
    with pytest.raises(FileExistsError):j.producer.publish()
"""
new="""    assert not calls and not j.p._TASK4_MODEL_CALLS and 'publish' not in j.events
    claim=j.producer.work/'publish-once.claim';assert claim.is_file()
    record=j.m.read(j.producer.work/'trigger-record.json')
    retained_roots=(j.producer.work,j.cpu,Path(j.producer.g['main_root']),Path(j.producer.g['evidence_root']))
    def retry_state():
        paths={path for root in retained_roots for path in root.rglob('*') if path.is_file()}
        paths.update((Path(record['request']),Path(record['marker'])))
        return {str(path):(path.stat().st_size,j.m.sha(path)) for path in paths}
    retained=retry_state();remote_before={path:j.m.sha_bytes(raw) for path,raw in j.remote.items()}
    final=Path(j.producer.waiting_paths()[1])
    absent=(final,Path(str(final)+'.pending'),Path(j.producer.g['main_root'])/'score')
    assert all(not path.exists() and not path.is_symlink() for path in absent)
    if fault=='catalogue':
        # The retained damaged input is re-authenticated before claim creation.
        with pytest.raises(ValueError) as rejected:j.producer.publish()
        assert str(rejected.value)=='ordinary input changed: '+j.producer.g['minimum_registry_paths'][0]
    else:
        with pytest.raises(FileExistsError) as rejected:j.producer.publish()
        assert rejected.value.filename==str(claim)
    assert retry_state()==retained
    assert {path:j.m.sha_bytes(raw) for path,raw in j.remote.items()}==remote_before
    assert all(not path.exists() and not path.is_symlink() for path in absent)
    assert j.events.count('stage')==1 and not calls and not j.p._TASK4_MODEL_CALLS and 'publish' not in j.events
"""
assert after.count(old)==1;after=after.replace(old,new);f.write_text(after)
(NEW/'run_cpu.sh').write_text((OLD/'run_cpu.sh').read_text().replace(str(OLD),str(NEW)))
meta=read(NEW/'dependencies.json');meta['predecessor_packet']=str(OLD);write(NEW/'dependencies.json',meta)
proposal=read(NEW/'candidate/proposal.json');proposal['predecessor_packet']=str(OLD)
q=proposal['CPU_test_proposal'];q['actual_failed_run_context']=dict(job='23638286',environment='base39',tests=33,passed=31,failed=2,errors=0,skips=0,pytest_seconds=750.79,mgnp_status='root-owned, unfinished when this correction began',successful_full_path_measured=False,note='Native normal success/audit passed before wrong retry-exception assertion; three serial mutation audits were not reached. Remaining31cases passed BASE. No final dual-environment acceptance inferred.')
q['rationale']='Retain separately reviewed2CPU/16GiB/3600s request and1650s per environment. BASE actually took750.79s for33cases with31passes; positive failed only after normal native score/audit and before three serial mutation audits. Corrected retry assertions add retained-file streaming hashes and expose those three audits. 1650s leaves899.21s above that observed BASE duration as planning allowance; MGNP completion/runtime remains root-owned. This is not a measured successful-path time/RAM upper bound or automatic retry. Two environment bounds total3300s, leaving300s observer headroom; timeout preserves failure.'
proposal['correction327']=['Assert guard-ordered exact rejection, not a fixed duplicate-publication exception.','Retain successful artifacts/failed partial evidence and assert no extra CLI/stage/publication or repair.'];write(NEW/'candidate/proposal.json',proposal)
manifest=read(NEW/'candidate/manifest.json');manifest['kind']='UNBOUND_TASK4_R5_RETRY_INVARIANT_FIXTURE_SOURCE_INVENTORY';manifest['correction327_fixture_only']=True;manifest['predecessor_packet_pins_sha256']=sha(OLD/'packet-pins.json');manifest['integration_test_sha256']=sha(f);manifest['dependencies_sha256']=sha(NEW/'dependencies.json');write(NEW/'candidate/manifest.json',manifest)
with (NEW/'candidate/README.md').open('a') as stream:stream.write('\nCorrection327 changes only retry assertions. Original root authentication runs before the exclusive publication claim. A completed score rejects with the precise original existing-score cause; a retained catalogue mutation rejects with its exact ordinary-input path; other transfer variants reject at the existing claim filename. Retained local/remote artifacts and absent outputs are checked across rejection. All33cases and original native semantics remain. BASE750.79s measured only the partially reached path; MGNP/final outcomes remain root-owned. Retained3600s/1650s limits are a bounded diagnostic proposal, not a runtime/RAM guarantee or automatic retry.\n')
write(NEW/'packet-pins.json',{n:sha(NEW/n) for n in oldpins})
(P/'fixture.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='frozen321/test_full_score_integration.py',tofile='correction327/test_full_score_integration.py')))
# Every original assertion/decorator remains; only two existing test functions differ.
aa,bb=ast.parse(before),ast.parse(after);dump=lambda n:ast.dump(n,include_attributes=False);fa={n.name:n for n in aa.body if isinstance(n,ast.FunctionDef)};fb={n.name:n for n in bb.body if isinstance(n,ast.FunctionDef)}
changed=[name for name in fa if dump(fa[name])!=dump(fb[name])]
assert changed==['test_whole_chain_normal_native_full_publication','test_transfer_failure_cannot_cross_score_boundary']
for name,n in fa.items():
 assert [dump(x) for x in n.decorator_list]==[dump(x) for x in fb[name].decorator_list]
 a=collections.Counter(dump(x) for x in ast.walk(n) if isinstance(x,ast.Assert));b=collections.Counter(dump(x) for x in ast.walk(fb[name]) if isinstance(x,ast.Assert));assert not a-b,name
assert all(sha(OLD/n)==h for n,h in oldpins.items())
production=manifest['unchanged_component_files'];assert len(production)==17 and all(sha(n)==h for n,h in production.items())
red=Path(str(S/'plan-a2-task4-deployment324/run-01'))
write(P/'diagnosis.json',dict(kind='ACTUAL_BASE_RED_TEST_EXPECTATION_ORDERING_ONLY',hypothesis='Original authentication precedes exclusive claim; retry remains forbidden but may reject earlier on existing score or retained input mutation.',failed_BASE_log=dict(path=str(red/'base39.log'),sha256=sha(red/'base39.log')),failed_BASE_xml=dict(path=str(red/'base39.xml'),sha256=sha(red/'base39.xml')),ROOT_guard_order=['verify_runtime_pins','exclusive publish-once.claim'],expected_original_causes=dict(completed_score='score already exists or is symlink',catalogue='ordinary input changed: <exact attacked catalogue path>',other_transfer='FileExistsError at original publish-once.claim'),corrected_native_tests_run=False))
write(P/'correction-manifest.json',dict(kind='FIXTURE_ONLY_RETRY_INVARIANT_CORRECTION327',packet=str(NEW),packet_pins_sha256=sha(NEW/'packet-pins.json'),integration_test_sha256=sha(f),predecessor_packet=str(OLD),predecessor_packet_pins_sha256=sha(OLD/'packet-pins.json'),changed_test_functions=changed,all_original33_case_assertions_and_parameters_preserved=True,production17_unchanged=production,production_changes=[],native_imports=False,pytest_runs=0,actual_bindings_unchanged_null=True,resource_proposal=dict(CPUs=2,RAM_bytes=17179869184,walltime_seconds=3600,per_environment_timeout_seconds=1650,BASE_pytest_seconds=750.79,MGNP_result='root-owned pending at diagnosis',successful_runtime_bound=False)))
print(json.dumps(read(P/'correction-manifest.json')))
