import pathlib,json,hashlib,os,difflib,datetime,shutil
w=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');c=w/'.superpowers/sdd/plan-a3/source-guard-cost-fix-source-r2';e=w/'docs/research/specificity-ladder/reports/123-source-cost-round2-evidence';pointer=json.loads(pathlib.Path('/tmp/a3-source-cost-successor.json').read_text());s=json.loads(pathlib.Path(pointer['snapshot']).read_text());sha={};blobs={};size={}
for name in s['source_sha256']:
 p=c/name;assert p.is_file() and not p.is_symlink(),name;data=p.read_bytes();sha[name]=hashlib.sha256(data).hexdigest();blobs[name]=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();size[name]=len(data)
changed=sorted(name for name in sha if sha[name]!=s['source_sha256'][name]);assert changed==['component_analysis/a3_source_validation.py','tests/test_a3_source_validation.py'],changed
links={}
for name,target in s['input_links'].items():
 p=c/name;assert p.is_symlink() and p.resolve()==pathlib.Path(target).resolve();links[name]=dict(literal_target=os.readlink(p),resolved_target=str(p.resolve()))
ordinary=set();actual_links=set()
for folder,dirs,files in os.walk(c,followlinks=False):
 for name in dirs+files:
  p=pathlib.Path(folder)/name
  if p.is_symlink():actual_links.add(str(p.relative_to(c)))
  elif p.is_file():ordinary.add(str(p.relative_to(c)))
assert ordinary==set(sha) and actual_links==set(links)
m=dict(kind='source_guard_cost_round2_freeze_input_v1',candidate_root=str(c),candidate_only=True,root_freeze_pending=True,baseline_commit=pointer['source_commit'],baseline_snapshot=pointer['snapshot'],source_file_count=len(sha),source_files_sha256=sha,computed_git_blob_sha1=blobs,file_bytes=size,changed_files=changed,input_links=links,source_code_symlinks=False,root_correction_scope=['B1 early artifact envelope witness continuity','B2 actual grader lexical and glob closure'],new_source_preparation=False,real_input_benchmark=False,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(e/'source-freeze-manifest.json').write_text(json.dumps(m,indent=2)+'\n');(e/'source-post.json').write_text(json.dumps({n:sha[n] for n in changed},indent=2)+'\n')
diff=''
for name in changed:diff+=''.join(difflib.unified_diff((e/('pre-'+pathlib.Path(name).name)).read_text().splitlines(True),(c/name).read_text().splitlines(True),fromfile='caae/'+name,tofile='round2/'+name))
(e/'candidate-diff.txt').write_text(diff);shutil.copyfile('/tmp/source-cost-r2-test-run.py',e/'test-runner.py')
probe=w/'docs/research/specificity-ladder/reports/121-source-cost-review-evidence/test_independent_source_boundaries.py';(e/'independent-probe-binding.json').write_text(json.dumps(dict(path=str(probe),sha256=hashlib.sha256(probe.read_bytes()).hexdigest(),modified=False),indent=2)+'\n')
print(json.dumps(dict(source_file_count=len(sha),changed=changed,helper_sha256=sha['component_analysis/a3_source_validation.py'],manifest_sha256=hashlib.sha256((e/'source-freeze-manifest.json').read_bytes()).hexdigest()),indent=2))
