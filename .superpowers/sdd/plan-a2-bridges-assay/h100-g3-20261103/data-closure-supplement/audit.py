#!/usr/bin/env python3
"""CPU-only actual owning-read trace; no freeze, source edit, model, submission or release."""
import argparse,ast,hashlib,importlib,json,os,re,socket,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parent;C=json.loads((P/"config.json").read_text());ROOT=Path("/projects/beto/swong2/Alignment");R=Path(C["runtime"])
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(8388608),b""):h.update(b)
 return h.hexdigest()
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def write(p,x):
 with Path(p).open("x") as f:json.dump(x,f,indent=2,allow_nan=False);f.write("\n")
def safe(p):
 return not any(x in p.parts for x in (".ssh",".aws",".git")) and p.name.lower() not in ("token","stored_tokens","credentials",".netrc","id_rsa","id_ed25519")
def run(out):
 job=os.environ.get("SLURM_JOB_ID","");need(job.isdigit() and os.environ.get("SLURM_CLUSTER_NAME")=="delta","actual Delta CPU required")
 raw=subprocess.check_output(["scontrol","show","job",job,"-o"],universal_newlines=True);f=dict(x.split("=",1) for x in raw.split() if "=" in x);tres=dict(x.split("=",1) for x in f.get("AllocTRES",f.get("TRES","")).split(",") if "=" in x)
 need(f["JobId"]==job and f["JobState"]=="RUNNING" and f["Partition"].startswith("cpu") and f["Account"].endswith("-cpu"),"actual CPU allocation")
 need(not any(k.startswith("gres/gpu") for k in tres) and os.environ.get("CUDA_VISIBLE_DEVICES","")=="","no GPU allocation")
 need(f["BatchHost"].split(".")[0]==socket.gethostname().split(".")[0],"actual compute host")
 write(out/"allocation.json",{"job_id":job,"scontrol_job":raw,"host":socket.gethostname(),"all_SLURM":{k:v for k,v in os.environ.items() if k.startswith("SLURM_")}})
 catalogues=[ROOT/"Deception-Circuit/docs/research"/n for n in ("held_out.json","directions.json")]+[ROOT/"Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research"/n for n in ("held_out.json","directions.json")]
 before={str(p):sha(p) for p in catalogues};need(sha(C["G3"])==C["G3_sha256"],"exact G3")
 reads={};enabled=True
 def audit(event,args):
  if not enabled or event!="open" or not args or not isinstance(args[0],(str,bytes)):return
  mode=args[1] if len(args)>1 else None;flags=args[2] if len(args)>2 else 0
  if isinstance(mode,str) and any(ch in mode for ch in ("w","a","x","+")):return
  if isinstance(flags,int) and flags & (os.O_WRONLY|os.O_CREAT|os.O_TRUNC):return
  rawpath=os.fsdecode(args[0]);p=Path(rawpath);cwd=os.getcwd();absolute=Path(os.path.abspath(str(p)))
  if absolute.is_relative_to(ROOT) and safe(absolute):reads[(rawpath,cwd,str(absolute))]=1
 os.chdir(R);sys.path.insert(0,str(R));sys.addaudithook(audit);start=time.time()
 runtime=R
 c={"accepted_source_snapshot":{"path":str(R.parent/"snapshot.json"),"sha256":C["snapshot_sha256"]},"accepted_source_commit":C["source_commit"],"source_files":C["source_files"]}
 def source_export():
         ref=c["accepted_source_snapshot"]
         need(sha(ref["path"])==ref["sha256"],"accepted source snapshot digest")
         snapshot=json.loads(Path(ref["path"]).read_text())
         need(snapshot["source_commit"]==c["accepted_source_commit"],"accepted export commit")
         need(Path(snapshot["runtime_root"])==runtime,"accepted export runtime identity")
         source=snapshot["source_sha256"];links=snapshot["input_links"]
         need(type(source) is dict and len(source)==511,"accepted export exact 511 ordinary source entries")
         need(type(links) is dict and len(links)==4,"accepted export exact four literal input links")
         need(source==c["source_files"],"root source closure differs from accepted export")
         need(not snapshot.get("source_code_symlinks",False),"source code symlinks forbidden")
         for name in list(source)+list(links):
             rel=Path(name)
             need(not rel.is_absolute() and ".." not in rel.parts and str(rel)==name,"invalid export relative path")
         need(not(set(source)&set(links)),"source/link inventory overlap")
         actual_files=set();actual_links=set()
         for item in runtime.rglob("*"):
             name=str(item.relative_to(runtime))
             if item.is_symlink():actual_links.add(name)
             elif item.is_file():actual_files.add(name)
         need(actual_files==set(source),"ordinary source inventory has missing or extra files")
         need(actual_links==set(links),"literal input link inventory has missing or extra aliases")
         for rel,digest in source.items():
             item=runtime/rel
             need(not item.is_symlink() and item.resolve().is_relative_to(runtime),"source escaped accepted export: "+rel)
             need(sha(item)==digest,"accepted source digest: "+rel)
         for rel,target in links.items():
             item=runtime/rel
             need(item.is_symlink() and os.readlink(item)==target,"literal accepted input link: "+rel)
             need(item.exists() and item.resolve()==Path(target).resolve(),"accepted input target resolution: "+rel)
         return {"source_count":len(source),"input_link_count":len(links),"snapshot_sha256":ref["sha256"],"input_links":links}
 source_before=source_export()
 p=importlib.import_module("component_analysis.a2_pipeline")
 args=p.parser().parse_args(["--stage","freeze","--design",C["design"],"--selected",C["selected"],"--commit",C["source_commit"],"--registry",C["registry"],"--batch-size","8","--work-dir",str(Path(C["G3"]).parent),"--comparison",C["comparison"],"--source-records",C["source_records"]])
 prepared,selected,sidecar=p._load_context(args);receipt=p.a1.read_artifact(C["G3"]);p._validate_live(args,receipt,prepared);need(receipt["model_geometry"]==p.model_geometry_receipt(prepared),"owning geometry")
 for name in ("model","model_revision","tokenizer_revision"):setattr(args,name,prepared[name])
 tokenizer=p.a1.common.load_tokenizer(args);p.a1.validate_tokenization(prepared,tokenizer);p._validate_live(args,receipt,prepared)
 keys=[]
 for field in ("source_hashes","selection_hashes"):
  for name,h in prepared[field].items():
   absolute=Path(os.path.abspath(name));need(sha(absolute)==h,"owning hash-key reference")
   keys.append({"field":field,"key":name,"actual_read_cwd":str(R),"absolute":str(absolute),"resolved":str(absolute.resolve()),"sha256":h})
 for name,h in prepared["code_hashes"].items():
  absolute=Path(p.a1.REPO)/name;need(sha(absolute)==h,"owning prepared code-hash closure")
  keys.append({"field":"code_hashes","key":name,"actual_read_cwd":str(p.a1.REPO),"absolute":str(absolute),"resolved":str(absolute.resolve()),"sha256":h})
 need(sha(C["Delta_G3_proof"])==C["Delta_G3_proof_sha256"],"exact accepted Delta CPU proof")
 proof=json.loads(Path(C["Delta_G3_proof"]).read_text());need(proof["status"]=="PASS" and proof["source_commit"]==C["source_commit"] and proof["groups_sha256"]==C["G3_sha256"],"accepted Delta G3 proof binding")
 need(len(p.expected_keys(receipt,4))==proof["prefix_keys"],"owning G3 prefix domain equals Delta proof");need(proof["model_geometry"]==receipt["model_geometry"],"Delta G3 geometry proof equality");need(sha(C["G3"])==C["G3_sha256"],"G3 not rewritten")
 need(sha(C["historical_G2"]["path"])==C["historical_G2"]["sha256"],"exact root-bound historical G2")
 old=p.a1.read_artifact(C["historical_G2"]["path"])
 science_fields=('schema', 'group_source', 'source_kind', 'groups', 'compute_groups', 'bank_keys', 'tasks', 'comparison', 'comparison_sha256', 'a1_design_sha256', 'a1_selected_sha256', 'selection_receipt', 'selection_sidecar_sha256', 'assessment', 'model_geometry', 'model_identity', 'a1_ancestor_commit', 'a2_training_execution_commit', 'operations', 'independent_donor_seeds', 'injected', 'limitations')
 provenance={"execution_commit","file_references","grader_registry","receipt_sha256","registry_hashes","runtime_code_hashes","utility_registry_hashes"}
 oldkeys=set(science_fields)|provenance
 need(len(science_fields)==22 and len(oldkeys)==29 and set(old)==oldkeys and set(receipt)==oldkeys|{"grader_binding"},"exact historical29/fresh30 receipt schemas")
 for field in science_fields:need(old[field]==receipt[field],"owning existing-G3 scientific field comparison")
 source_after=source_export();need(source_before==source_after,"accepted export changed during audit")
 after={str(q):sha(q) for q in catalogues};need(before==after,"current Delta catalogue changed during audit")
 origins={name:str(Path(m.__file__).resolve()) for name,m in sys.modules.items() if getattr(m,"__file__",None) and name.split(".")[0] in ("component_analysis","dataset","evaluation","models","scripts","config")};need(all(Path(v).is_relative_to(R) for v in origins.values()),"source origin fallback")
 enabled=False
 write(out/"python-read-events.json",[{"path":a,"cwd":b,"absolute":c} for a,b,c in sorted(reads)])
 write(out/"hash-key-references.json",keys)
 write(out/"owning-proof.json",{"status":"PASS","job_id":job,"source_commit":C["source_commit"],"groups_sha256":C["G3_sha256"],"elapsed_seconds":time.time()-start,"source_before":source_before,"source_after":source_after,"science_fields_equal_to_historical_G2":list(science_fields),"historical_G2_sha256":C["historical_G2"]["sha256"],"model_geometry":receipt["model_geometry"],"prefix_keys":len(p.expected_keys(receipt,4)),"module_origins":origins,"catalogues_before":before,"catalogues_after":after,"model_loaded":False,"groups_frozen":False})
def collect(out):
 proof=json.loads((out/"owning-proof.json").read_text());need(proof["status"]=="PASS","completed owning read path required")
 events=json.loads((out/"python-read-events.json").read_text());observed={x["absolute"] for x in events};os_events=[]
 for line in (out/"filesystem.strace").read_text().splitlines():
  if not re.search(r"\b(?:open|openat)(?:\(| resumed>)",line) or not re.search(r"= [0-9]+<",line):continue
  if "O_WRONLY" in line or "O_CREAT" in line or "O_TRUNC" in line:continue
  m=re.search(r"= [0-9]+<([^>]+)>",line)
  if m and m.group(1).startswith("/"):
   resolved=m.group(1);observed.add(resolved)
   # -yy annotates actual cwd/dirfd, preserving relative OS reads as well as return-fd identity.
   q=re.search(r'(?:openat\([^,]*, |open\()(?P<q>"(?:[^"\\]|\\.)*")',line)
   if q:
    try:
     original=ast.literal_eval(q.group("q"));base=re.search(r'openat\([^<]*<([^>]+)>',line)
     lexical=original if original.startswith("/") else str(Path(base.group(1) if base else str(R))/original)
     observed.add(lexical)
     if safe(Path(resolved)) and (Path(resolved).is_relative_to(ROOT) or resolved.startswith("/work/nvme/beto/swong2/")):
      os_events.append({"path":original,"anchor":base.group(1) if base else str(R),"absolute":lexical,"resolved_fd":resolved})
    except (ValueError,SyntaxError):pass
 need(sha(C["original_manifest"])==C["original_manifest_sha256"],"original manifest bytes")
 old=json.loads(Path(C["original_manifest"]).read_text());oldfiles=old["ordinary_files"];files={};aliases={};excluded={};outside={}
 def classify(p):
  s=str(p)
  if not safe(p):return "credentials/control excluded"
  if p.is_relative_to(out) or ".superpowers" in p.parts:return "audit/operational control excluded"
  if p.suffix in (".py",".pyc",".sh",".so"):return "source/code excluded"
  if p.name in ("held_out.json","directions.json","ledger.json","state.json","worklog.json","root-release.json"):return "root-current control/catalogue excluded"
  if p in (Path(C["G3"]),Path(C["historical_G2"]["path"]),Path(C["Delta_G3_proof"])):return "existing root-bound G3/historical G2/CPU proof excluded from supplemental transfer"
  if p.is_relative_to(R):return "accepted immutable source export excluded"
  if "/runtime/" in s and "/outputs/_analyses/specificity-ladder/" in s:return "original immutable source export excluded"
  if p.name in ("snapshot.json","source.tar","application.tar") and "/outputs/_analyses/specificity-ladder/" in s:return "immutable source export receipt/archive excluded"
  return None
 for name in sorted(observed):
  p=Path(name)
  if not p.is_absolute() or not p.exists() or not p.is_file():continue
  resolved=p.resolve()
  if not (resolved.is_relative_to(ROOT) or str(resolved).startswith("/work/nvme/beto/swong2/")):continue
  reason=classify(resolved)
  if reason:excluded[str(resolved)]=reason;continue
  need(resolved.suffix not in (".safetensors",".bin",".pt",".pth",".pkl",".pickle"),"unexpected model/binary read requires separate review")
  # Record every literal alias on the lexical route before deduplicating resolved ordinary targets.
  for ancestor in [p]+list(p.parents):
   if ancestor.is_symlink():aliases[str(ancestor)]=os.readlink(ancestor)
  item={"path":str(resolved),"bytes":resolved.stat().st_size,"sha256":sha(resolved)}
  if resolved.is_relative_to(ROOT):files[str(resolved)]=item
  else:outside[str(resolved)]=item
 missing={n:r for n,r in files.items() if n not in oldfiles};changed={n:{"old":oldfiles[n],"current":r} for n,r in files.items() if n in oldfiles and (oldfiles[n]["sha256"]!=r["sha256"] or oldfiles[n]["bytes"]!=r["bytes"])}
 keys=json.loads((out/"hash-key-references.json").read_text());need(all(Path(k["resolved"]).exists() for k in keys),"every relative/absolute hash key exists")
 # Each hash key must have an actual traced read, not merely a guessed JSON reference.
 need(all(k["absolute"] in observed or k["resolved"] in observed for k in keys),"hash-key reference missing from real read trace")
 result={"kind":"actual_owning_read_input_closure_supplement","status":"PASS" if not changed else "BLOCKED_EXISTING_INPUT_DRIFT","source_commit":C["source_commit"],"groups_sha256":C["G3_sha256"],"ordinary_files":files,"supplement_files":missing,"supplement_count":len(missing),"supplement_bytes":sum(v["bytes"] for v in missing.values()),"changed_existing_inputs":changed,"namespace_aliases":aliases,"external_metadata":outside,"excluded":excluded,"actual_OS_read_events":os_events,"hash_key_reference_count":len(keys),"coverage":"OS strace -f -yy successful read-opens plus Python audit at actual read-time cwd, executing full unchanged owning existing-G3 context/live/geometry/tokenizer path; source/credentials/control excluded; no speculative JSON-only completeness claim","model_loaded":False,"groups_frozen":False}
 write(out/"supplement-manifest.json",result);(out/"supplement-resolved-project-files.txt").write_text("".join(str(Path(n).relative_to(ROOT))+"\n" for n in sorted(missing)))
 need(not changed,"existing transferred input digest drift requires root review; do not restage silently")
 write(out/"COMPLETE.json",{"status":"PASS","supplement_count":len(missing),"supplement_bytes":result["supplement_bytes"],"source_commit":C["source_commit"],"groups_sha256":C["G3_sha256"],"model_loaded":False,"freeze_executed":False})
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("phase",choices=("run","collect"));ap.add_argument("output");a=ap.parse_args();o=Path(a.output).resolve();(run if a.phase=="run" else collect)(o)
