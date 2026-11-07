#!/usr/bin/env python3
"""Existing frozen G3 actual Delta model-phase CPU preflight; no weights or GPU admission; root binds reviewed parameters before execution.
Root-triggered metadata validation only; never freezes or rewrites G3.
"""
import argparse, hashlib, importlib, json, os, re, socket, subprocess, sys, time
from pathlib import Path
SCIENCE_FIELDS=("schema","group_source","source_kind","groups","compute_groups","bank_keys","tasks","comparison","comparison_sha256","a1_design_sha256","a1_selected_sha256","selection_receipt","selection_sidecar_sha256","assessment","model_geometry","model_identity","a1_ancestor_commit","a2_training_execution_commit","operations","independent_donor_seeds","injected","limitations")
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
    return h.hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--parameters",required=True);ap.add_argument("--parameters-sha256",required=True);a=ap.parse_args()
    need(sha(a.parameters)==a.parameters_sha256,"root parameter digest")
    c=json.loads(Path(a.parameters).read_text());runtime=Path(c["accepted_runtime"]).resolve();out=Path(c["new_g3_output"])
    need(re.fullmatch("[0-9a-f]{40}",c["accepted_source_commit"]),"accepted full source SHA required")
    need(c["root_source_review_accepted"] is True,"root must first accept independent source review")
    need(os.environ.get("CUDA_VISIBLE_DEVICES","")=="","CPU visibility required")
    need(os.environ.get("SLURM_CLUSTER_NAME")=="delta","actual Delta CPU job required")
    need(os.environ.get("SLURM_JOB_ID"),"CPU allocation required")
    allocation=json.loads(Path(c["current_cpu_allocation"]["path"]).read_text())
    need(sha(c["current_cpu_allocation"]["path"])==c["current_cpu_allocation"]["sha256"],"CPU allocation digest")
    fields=dict(x.split("=",1) for x in allocation["scontrol_job"].split() if "=" in x)
    need(fields["JobId"]==os.environ["SLURM_JOB_ID"] and fields["JobState"]=="RUNNING","actual running CPU job")
    need(fields["Partition"].startswith("cpu") and fields["Account"].endswith("-cpu"),"actual Delta CPU account/partition")
    need(fields["BatchHost"].split(".")[0]==socket.gethostname().split(".")[0],"actual compute host")
    need(int(fields["NumNodes"])==1 and int(fields["NumCPUs"])>=4,"CPU resources")
    tres=fields.get("AllocTRES",fields.get("TRES",""))
    need(tres and not re.search(r"(?:^|,)gres/gpu(?:[:=])",tres),"no GPU allocation")
    need(os.environ.get("HF_HUB_CACHE")=="/work/nvme/beto/swong2" and os.environ.get("TRANSFORMERS_CACHE")=="/work/nvme/beto/swong2","cache bind environment")
    need((out/"groups.json").is_file() and sha(out/"groups.json")==c["frozen_G3_sha256"],"exact existing frozen G3 required")
    evidence=Path(c["evidence_output"]);need(evidence.is_dir(),"supervisor-owned fresh evidence directory")
    need(c["phase"] in ("bank","prefix4"),"model preflight phase")
    need(time.time()<c["phase_deadline_unix"],"phase window already expired")
    catalogue_paths=[Path("/projects/beto/swong2/Alignment/Deception-Circuit/docs/research")/name for name in ("held_out.json","directions.json")]+[Path("/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research")/name for name in ("held_out.json","directions.json")]
    catalogue_before={str(path):path.read_bytes() for path in catalogue_paths}
    need(runtime.is_relative_to(Path("/projects/beto/swong2/Alignment")),"original runtime namespace")
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
    for name in ("independent_source_acceptance","accepted_export_receipt","cpu_data_proof","historical_G2"):
        need(sha(c[name]["path"])==c[name]["sha256"],"root-bound receipt digest: "+name)
    proof=json.loads(Path(c["cpu_data_proof"]["path"]).read_text())
    need(proof["status"]=="PASS" and proof["ordinary_count"]==389 and proof["ordinary_bytes"]==436913681 and proof["alias_count"]==5,"transfer proof")
    need(proof["manifest_sha256"]=="29960294fbda481dcd7807445b5db8be1157f9c49a1b030a7521287708cf5b7c","transfer manifest")
    os.chdir(runtime);sys.path.insert(0,str(runtime))
    p=importlib.import_module("component_analysis.a2_pipeline")
    def origins():
        found={}
        for name,module in list(sys.modules.items()):
            if name.split(".")[0] in ("component_analysis","models","dataset","evaluation","scripts","config"):
                f=getattr(module,"__file__",None)
                if f:need(Path(f).resolve().is_relative_to(runtime),"import escaped exact source: "+name);found[name]=str(Path(f).resolve())
        return found
    origins()
    base=["--design",c["design"],"--selected",c["selected"],"--commit",c["accepted_source_commit"],"--batch-size","8","--registry",c["registry"],"--work-dir",str(out)]
    stage_args=["--stage","bank" if c["phase"]=="bank" else "score",*base]
    if c["phase"]=="prefix4":stage_args += ["--limit","4"]
    args=p.parser().parse_args(stage_args)
    started=time.time()
    prepared,selected,sidecar=p._load_context(args);receipt=p.a1.read_artifact(out/"groups.json")
    p._validate_live(args,receipt,prepared)
    need(receipt["model_geometry"]==p.model_geometry_receipt(prepared),"fresh geometry")
    need(not receipt["injected"] and len(receipt["groups"])==9,"genuine nine-group freeze")
    old=p.a1.read_artifact(c["historical_G2"]["path"])
    provenance_fields={"execution_commit","file_references","grader_registry","receipt_sha256","registry_hashes","runtime_code_hashes","utility_registry_hashes"}
    old_keys=set(SCIENCE_FIELDS)|provenance_fields
    need(len(SCIENCE_FIELDS)==22 and len(old_keys)==29,"expected exact historical G2 schema definition")
    need(set(old)==old_keys,"historical G2 exact top-level key set drift")
    need(set(receipt)==old_keys|{"grader_binding"},"fresh G3 exact top-level key set drift")
    for field in SCIENCE_FIELDS:need(receipt[field]==old[field],"scientific G2/G3 drift: "+field)
    for field in ("model","model_revision","tokenizer_revision"):setattr(args,field,prepared[field])
    tokenizer=p.a1.common.load_tokenizer(args);p.a1.validate_tokenization(prepared,tokenizer)
    p._validate_live(args,receipt,prepared)
    source_after=source_export()
    need(source_before==source_after,"accepted export metadata changed during CPU validation")
    need(sha(out/"groups.json")==c["frozen_G3_sha256"],"frozen G3 bytes changed")
    catalogue_after={str(path):path.read_bytes() for path in catalogue_paths}
    need(catalogue_before==catalogue_after,"actual Delta catalogue bytes changed during owning checks")
    rows=[]
    for index,(path,body) in enumerate(catalogue_before.items()):
        target=evidence/("catalogue-"+str(index)+".json")
        with target.open("xb") as stream:stream.write(body)
        rows.append(dict(virtual_path=path,sha256=hashlib.sha256(body).hexdigest(),captured_bytes_path=str(target)))
    need(time.time()<c["phase_deadline_unix"],"phase window missed after owning checks")
    result=dict(kind="Delta_actual_model_phase_guard_child",complete=False,status="GUARDS_PASSED_AWAIT_SUPERVISOR",phase=c["phase"],source_commit=c["accepted_source_commit"],groups_file_sha256=c["frozen_G3_sha256"],actual_future_GPU_job_id=c["actual_future_GPU_job_id"],request_sha256=c["phase_request_sha256"],actual_Delta_owning_guards_passed=True,stable_Delta_catalogues_before_after=True,catalogues=[dict(virtual_path=r["virtual_path"],sha256=r["sha256"]) for r in rows],catalogue_capture_files=rows,source_before=source_before,source_after=source_after,model_geometry=receipt["model_geometry"],numeric_environment=p.numeric_environment(),module_origins=origins(),prefix_keys=len(p.expected_keys(receipt,4)),group_count=len(receipt["groups"]),actual_CPU_allocation=allocation,actual_CPU_job_id=os.environ["SLURM_JOB_ID"],host=socket.gethostname(),started_unix=started,finished_unix=time.time(),parameters_sha256=a.parameters_sha256,model_loaded=False,GPU_admitted=False,freeze_executed=False,ledger_cap_checks="Root performs actual ledger/mapping/caps separately at release publication")
    need(result["prefix_keys"]==2484,"prefix domain")
    with (evidence/"guard-result.json").open("x") as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write("\n")
    print("ACTUAL_DELTA_OWNING_GUARDS_PASSED_AWAIT_SUPERVISOR",flush=True)
if __name__=="__main__":main()
