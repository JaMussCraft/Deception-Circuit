import pathlib,json,mmap,re,hashlib,ast,datetime
W=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder');PRIMARY=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit');B=W/'outputs/_analyses/specificity-ladder/a3-source-cost-runtime-40fe57289405/runtime';G=W/'outputs/_analyses/specificity-ladder/a2-analysis/all18-40fe57289405-v1/groups.json';E=W/'docs/research/specificity-ladder/reports/148-a2-grader-snapshot-diagnosis-evidence'
def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open('rb') as f:
  for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
 return h.hexdigest()
keys={str(root/'docs/research/directions.json') for root in (PRIMARY,B)};matches=[]
with G.open('rb') as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as view:
 for match in re.finditer(rb'"grader_registry"\s*:\s*(\{[^{}]*\})',view):
  value=json.loads(match.group(1))
  if set(value)==keys:matches.append(dict(byte_offset=match.start(),value=value))
assert len(matches)==1,[(r['byte_offset'],r['value']) for r in matches]
frozen=matches[0]['value'];current={};catalogs={}
for root in (PRIMARY,W,B):
 path=root/'docs/research/directions.json';data=json.loads(path.read_text());entry=next(item for item in data['directions'] if item['id']=='specificity-ladder')
 key=str(path);current[key]=dict(sha256=sha(path),bytes=path.stat().st_size,resolved=str(path.resolve()),entry=entry)
 catalogs[str(root)]=data
 (E/('current-'+('primary' if root==PRIMARY else 'worktree' if root==W else 'runtime')+'-directions.json')).write_text(json.dumps(data,indent=2)+'\n')
# Reproduce only the documented small-file grader hash, no source/model imports.
all_files={}
for root in (B,PRIMARY,W):
 paths=sorted(list((root/'evaluation/benchmarks').glob('*.py'))+[root/'evaluation/benchmark_eval.py'])
 files={str(path.relative_to(root)):sha(path) for path in paths if path.is_file()}
 digest=hashlib.sha256(''.join(name+'\t'+value+'\n' for name,value in sorted(files.items())).encode()).hexdigest();all_files[str(root)]=dict(grader_sha256=digest,files=files)
ladder_source=(B/'component_analysis/ladder_pipeline.py').read_text();assignment=next(node for node in ast.parse(ladder_source).body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GRADER' for t in node.targets));grader=ast.literal_eval(assignment.value)
result=dict(kind='compact_read_only_A2_grader_snapshot_diagnosis',groups_path=str(G),groups_file_sha256=sha(G),extraction='read-only mmap; parse only unique small grader_registry dictionary with exact frozen primary/runtime path keys; no full receipt parse or source validation',extracted=matches[0],frozen_grader_registry=frozen,current_registry=current,changed_recorded_paths={path:dict(recorded=value,current=current[path]['sha256'],changed=value!=current[path]['sha256']) for path,value in frozen.items()},frozen_code_GRADER=grader,current_grader_code=all_files,specificity_registered_fingerprints={path:row['entry'].get('frozen_grader_sha256') for path,row in current.items()},no_source_or_receipt_or_ledger_modified=True,no_model_GPU_or_heavy_replay=True,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(E/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({key:result[key] for key in ('changed_recorded_paths','frozen_code_GRADER','specificity_registered_fingerprints')},indent=2));print('CODE_HASHES',{root:row['grader_sha256'] for root,row in all_files.items()});print('PRIMARY_SPECIFICITY_ENTRY',json.dumps(current[str(PRIMARY/'docs/research/directions.json')]['entry'],indent=2))
