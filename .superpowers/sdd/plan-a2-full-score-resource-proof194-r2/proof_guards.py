"""Read-only owning checks. This module has no model/scoring entry interface."""
import hashlib,json,os,sys
from pathlib import Path
P=Path(__file__).resolve().parent
W=Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder')
R=W/'outputs/_analyses/specificity-ladder/a2-grader-runtime-50e947bb8526/runtime'
G=W/'outputs/_analyses/specificity-ladder/a2-analysis/bridges-h100-G3-v1'
D=W/'.superpowers/sdd/plan-a2-bridges-assay/h100-g3-20261103'
H=D/'root-H100-R5/job-50189932'
REG=[Path('/projects/beto/swong2/Alignment/Deception-Circuit/docs/research')/n for n in ('held_out.json','directions.json')]+[W/'docs/research'/n for n in ('held_out.json','directions.json')]
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def packet(digest):
 assert sha(P/'manifest.json')==digest
 for n,h in read(P/'manifest.json').items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and sha(P/n)==h,n
 for n,h in read(P/'input-pins.json').items():assert sha(n)==h,n
 return digest
def capture():
 snap=read(R.parent/'snapshot.json');assert snap['source_commit']=='50e947bb852613e3a270082651f2bd1b7bb0c525'
 files={str(x.relative_to(R)) for x in R.rglob('*') if x.is_file() and not x.is_symlink()};links={str(x.relative_to(R)) for x in R.rglob('*') if x.is_symlink()}
 assert len(files)==511 and len(links)==4 and files==set(snap['source_sha256']) and links==set(snap['input_links'])
 for n,h in snap['source_sha256'].items():
  item=R/n;assert not Path(n).is_absolute() and '..' not in Path(n).parts and not item.is_symlink() and item.resolve().is_relative_to(R.resolve()) and sha(item)==h
 for n,t in snap['input_links'].items():assert os.readlink(R/n)==t and (R/n).exists() and (R/n).resolve()==Path(t).resolve()
 config=read(H/'config.json');manifest=Path(config['input_manifest']);assert sha(manifest)==config['input_manifest_sha256'];inputs=read(manifest);assert len(inputs['ordinary_files'])==422
 for n,row in inputs['ordinary_files'].items():assert row['path']==n and Path(n).stat().st_size==row['bytes'] and sha(n)==row['sha256'],n
 aliases={}
 for n,t in inputs['namespace_aliases'].items():
  item=Path(n);assert item.is_symlink() and os.readlink(item)==t and item.exists() and item.resolve()==Path(t).resolve(),n
  aliases[n]={'literal':t,'resolved':str(item.resolve())}
 origins={n:str(Path(m.__file__).resolve()) for n,m in list(sys.modules.items()) if n.split('.')[0] in ('component_analysis','models','dataset','evaluation','scripts','config') and getattr(m,'__file__',None)}
 assert all(Path(p).is_relative_to(R.resolve()) for p in origins.values()),origins
 return dict(source_snapshot=sha(R.parent/'snapshot.json'),source_count=len(files),links=snap['input_links'],inputs=sha(manifest),input_count=422,aliases=aliases,groups=sha(G/'groups.json'),bank=sha(G/'bank/banks.json'),bank_manifest=sha(G/'bank/run_manifest.json'),catalogues={str(p):sha(p) for p in REG},module_origins=origins)
def owning():
 os.chdir(R);sys.path.insert(0,str(R));from component_analysis import a2_pipeline as p
 args=p.parser().parse_args(read(H/'actual-completed-20261106/execution/bank-command.json')['command'][2:]);args.stage='score';args.work_dir=str(G);args.limit=0;args.tasks=list(p.TASKS);args.injected=False
 prepared,selected,sidecar=p._load_context(args)
 for k in ('model','model_revision','tokenizer_revision'):setattr(args,k,prepared[k])
 receipt=p.a1.read_artifact(G/'groups.json');p._validate_live(args,receipt,prepared);assert receipt['model_geometry']==p.model_geometry_receipt(prepared)
 banks=p.read_stage(G/'bank','banks.json','bank',args,receipt);p.validate_banks(receipt,prepared,banks)
 assert not any(x['injected'] for x in (receipt,prepared,banks)) and not receipt['independent_donor_seeds']
 tokenizer=p.a1.common.load_tokenizer(args);p.a1.validate_tokenization(prepared,tokenizer);p._validate_live(args,receipt,prepared)
 assert all(p.numeric_environment()==banks['banks'][task]['contract']['numeric_environment'] for task in p.TASKS)
 return p,args,prepared,selected,sidecar,receipt,banks,tokenizer
