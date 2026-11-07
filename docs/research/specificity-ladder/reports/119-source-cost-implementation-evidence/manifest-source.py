"""Read-only candidate inventory for root freeze; never invokes git/chmod/preparation."""
import pathlib,json,hashlib,os,difflib,shutil,datetime
w=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');c=w/'.superpowers/sdd/plan-a3/source-guard-cost-fix-source';e=w/'docs/research/specificity-ladder/reports/119-source-cost-implementation-evidence';snapshot_path=w/'outputs/_analyses/specificity-ladder/a3-edge-runtime-87fceb28b3b4/snapshot.json';baseline=json.loads(snapshot_path.read_text());new=['component_analysis/a3_source_validation.py','tests/test_a3_source_validation.py'];names=sorted(set(baseline['source_sha256'])|set(new));sha={};blobs={};sizes={}
for name in names:
 p=c/name;assert p.is_file() and not p.is_symlink(),name;data=p.read_bytes();sha[name]=hashlib.sha256(data).hexdigest();blobs[name]=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();sizes[name]=len(data)
changed=[name for name in names if sha[name]!=baseline['source_sha256'].get(name)];expected=sorted(new+['component_analysis/a3_mask_pipeline.py','component_analysis/a3_edge_pipeline.py','tests/test_a3_mask_pipeline.py','tests/test_a3_edge_pipeline.py']);assert changed==expected,changed
links={}
for name,target in baseline['input_links'].items():
 p=c/name;assert p.is_symlink() and p.resolve()==pathlib.Path(target).resolve(),name;links[name]=dict(literal_target=os.readlink(p),resolved_target=str(p.resolve()))
ordinary=set();observed_links=set()
for folder,dirs,files in os.walk(c,followlinks=False):
 for name in dirs+files:
  p=pathlib.Path(folder)/name
  if p.is_symlink():observed_links.add(str(p.relative_to(c)))
  elif p.is_file():ordinary.add(str(p.relative_to(c)))
assert ordinary==set(names),(ordinary-set(names),set(names)-ordinary)
assert observed_links==set(links),observed_links
plan=w/'.superpowers/sdd/plan-a3/source-guard-cost-fix-plan';plan_sha=hashlib.sha256((plan/'repair-plan.md').read_bytes()).hexdigest();scope_sha=hashlib.sha256((plan/'scope.md').read_bytes()).hexdigest()
assert plan_sha=='6504f7ec2d8f25114dff3de7bd86074fc762171f88b7a3ba227a798fc689712f'
assert scope_sha=='1adc3191450dbf4314ce6f8f204cf42591931a54b072fc25fd09692106ce03a0'
manifest=dict(kind='source_guard_cost_candidate_freeze_input_v1',candidate_only=True,root_freeze_pending=True,baseline_commit=baseline['source_commit'],baseline_snapshot=str(snapshot_path),baseline_snapshot_sha256=hashlib.sha256(snapshot_path.read_bytes()).hexdigest(),candidate_root=str(c),source_file_count=len(names),source_files_sha256=sha,computed_git_blob_sha1=blobs,file_bytes=sizes,changed_files=changed,input_links=links,source_code_symlinks=False,accepted_plan_sha256=plan_sha,accepted_scope_sha256=scope_sha,plan_review_sha256=hashlib.sha256((plan/'plan-review.md').read_bytes()).hexdigest(),new_preparation_performed=False,real_input_fast_path_benchmark_performed=False,source_reservation_exception=False,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(e/'source-freeze-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(e/'source-post.json').write_text(json.dumps({name:sha[name] for name in changed},indent=2)+'\n')
diff=''
for name in changed:
 before='' if name in new else (e/('pre-'+pathlib.Path(name).name)).read_text()
 diff+=''.join(difflib.unified_diff(before.splitlines(True),(c/name).read_text().splitlines(True),fromfile='baseline/'+name,tofile='candidate/'+name))
(e/'candidate-diff.txt').write_text(diff);shutil.copy2('/tmp/source-cost-test-run.py',e/'test-runner.py')
print(json.dumps(dict(files=len(names),changed=changed,diff_bytes=len(diff.encode()),manifest_sha256=hashlib.sha256((e/'source-freeze-manifest.json').read_bytes()).hexdigest()),indent=2))
