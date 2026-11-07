"""Create a distinct fixture-only correction from immutable GREEN270-r3.
No production imports, pytest/native runs, git, Slurm, RS or remote actions.
"""
import ast,collections,hashlib,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parent;S=P.parent
OLD=S/'plan-plan-a2-full-score-operational186/task3/green270-r3'
NEW=S/'plan-plan-a2-full-score-operational186/task3/green270-r4'
REL='closure/sdd/plan-a2-full-score-operational186/candidate'
C=OLD/REL;R=P/'candidate-r4'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
old_pins=json.loads((OLD/'packet-pins.json').read_text())
assert all(sha(OLD/name)==wanted for name,wanted in old_pins.items())
assert not R.exists() and not NEW.exists()
for name in old_pins:
    if name.startswith(REL+'/'):
        source=OLD/name;dest=R/source.relative_to(C);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(str(source),str(dest))
file=R/'tests/test_full_score_root_integration.py';before=file.read_text()
anchor="    m=module();ledger,mapping,g=budget_fixture(m,7200)\n    canonical=tmp_path/'ledger.json';frozen_old=tmp_path/'old-ledger.json';frozen_new=tmp_path/'new-ledger.json'"
assert before.count(anchor)==1
replacement="""    m=module();ledger,mapping,g=budget_fixture(m,7200)
    # budget_fixture supplies arithmetic/charge fields only. Native scoring
    # identity comes from the accepted real GPU template, with a raw G3 file
    # hash check; no model, actual ledger or MAIN output is written here.
    owning=json.loads((t1.GPU/'config.template.json').read_text())
    assert owning['commit']==m.SOURCE
    assert m.sha(owning['groups'])==owning['groups_file_sha256']
    g.update(groups_file_sha256=owning['groups_file_sha256'],main_root=owning['main_root'])
    ledger['reservations'][1]['output_dir']=g['main_root']
    mapping['entries'][1]['actual_entry']['output_dir']=g['main_root']
    expected_identity=dict(purpose='A2 original source50e full scoring',source_commit=owning['commit'],
        groups_sha256=owning['groups_file_sha256'],main_root=owning['main_root'])
    canonical=tmp_path/'ledger.json';frozen_old=tmp_path/'old-ledger.json';frozen_new=tmp_path/'new-ledger.json'"""
after=before.replace(anchor,replacement)
anchor2="    captured,normalized,budget=m.collect_native_closure(g)\n    assert normalized['original_mapping_reference']==ar.object_reference(origin)"
assert after.count(anchor2)==1
after=after.replace(anchor2,"    captured,normalized,budget=m.collect_native_closure(g)\n    assert normalized['expected_identity']==expected_identity\n    assert normalized['original_mapping_reference']==ar.object_reference(origin)")
file.write_text(after)
# Preserve every prior test assertion and parameter route, without executing any
# test module or importing the native normalizer.
before_ast=ast.parse(before);after_ast=ast.parse(after)
def nodes(tree):
    return {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
a,b=nodes(before_ast),nodes(after_ast)
name='test_original_native_normalizer_preserves_full_mapping_chain'
assert set(a)==set(b)
assert all(ast.dump(a[n])==ast.dump(b[n]) for n in a if n!=name)
assert [ast.dump(x) for x in a[name].decorator_list]==[ast.dump(x) for x in b[name].decorator_list]
old_asserts=collections.Counter(ast.dump(n) for n in ast.walk(a[name]) if isinstance(n,ast.Assert))
new_asserts=collections.Counter(ast.dump(n) for n in ast.walk(b[name]) if isinstance(n,ast.Assert))
assert not (old_asserts-new_asserts) and sum(new_asserts.values())==sum(old_asserts.values())+3
changed=[str(f.relative_to(R)) for f in R.rglob('*') if f.is_file() and sha(f)!=sha(C/f.relative_to(R))]
assert changed==['tests/test_full_score_root_integration.py']
# Reproduce the complete sealed packet layout; keep the actual observer and
# complete source/native closure unchanged. Only its location wrapper changes.
for name in old_pins:
    dest=NEW/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(str(OLD/name),str(dest))
snapshot=json.loads((OLD/'native-snapshot.json').read_text())
for name,target in snapshot['input_links'].items():
    dest=NEW/'native-source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.symlink_to(target)
shutil.copyfile(str(file),str(NEW/REL/'tests/test_full_score_root_integration.py'))
(NEW/'run_cpu.sh').write_text((OLD/'run_cpu.sh').read_text().replace('/task3/green270-r3','/task3/green270-r4'))
(NEW/'build_packet.py').write_text('"""Frozen fixture-only successor. Constructed by '+str(P/'prepare_r4.py')+'. Do not regenerate in place."""\n')
originals=json.loads((OLD/'original-source-pins.json').read_text())
for f in R.rglob('*'):
    if f.is_file():originals[str(f)]=sha(f)
originals[str(P/'prepare_r4.py')]=sha(P/'prepare_r4.py')
originals[str(P/'diagnosis.json')]=sha(P/'diagnosis.json')
config=json.loads((C/'gpu/config.template.json').read_text())
originals[config['groups']]=config['groups_file_sha256']
write(NEW/'original-source-pins.json',originals)
production={str(f.relative_to(C)):sha(f) for folder in ('root','gpu','cpu') for f in (C/folder).rglob('*') if f.is_file()}
assert all(sha(NEW/REL/name)==wanted and sha(R/name)==wanted for name,wanted in production.items())
correction=dict(kind='FIXTURE_ONLY_IDENTITY_CONTRACT_CORRECTION',root_cause='budget-only config omitted mandatory groups_file_sha256 at native scoring identity seam',
    previous_packet=str(OLD),candidate=str(R),changed_candidate_files=changed,
    previous_fixture_sha256=sha(C/'tests/test_full_score_root_integration.py'),corrected_fixture_sha256=sha(file),
    production_unchanged_sha256=production,old_native_assertions=sum(old_asserts.values()),new_native_assertions=sum(new_asserts.values()),
    preserved_parameter_routes=5,preserved_full_RED_cases=98,preserved_full_GREEN_cases=379,
    source_commit=config['commit'],groups_file_sha256=config['groups_file_sha256'],main_root=config['main_root'],
    actual_canonical_ledger_or_MAIN_written=False,native_or_full_tests_run=False)
write(P/'correction-manifest.json',correction);write(NEW/'correction-manifest.json',correction)
# All old files and raw actual deployment evidence remain outside this edit.
assert all(sha(OLD/name)==wanted for name,wanted in old_pins.items())
pins={}
for f in NEW.rglob('*'):
    if not f.is_symlink() and f.is_file() and f.name!='packet-pins.json':
        if f.suffix=='.py':ast.parse(f.read_text(),filename=str(f))
        pins[str(f.relative_to(NEW))]=sha(f)
write(NEW/'packet-pins.json',pins)
print(json.dumps(dict(packet=str(NEW),packet_pins_sha256=sha(NEW/'packet-pins.json'),original_source_pins_sha256=sha(NEW/'original-source-pins.json'),correction=correction),indent=2))
