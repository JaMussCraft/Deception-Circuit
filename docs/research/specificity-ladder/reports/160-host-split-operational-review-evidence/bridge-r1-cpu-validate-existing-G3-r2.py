#!/usr/bin/env python3
"""Existing-G3 Bridges CPU validation; no freeze, publication or re-signing; root binds reviewed parameters before execution.
This file is preparation only and is not source acceptance or GPU authority.
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
    need(os.environ.get("CUDA_VISIBLE_DEVICES")=="" and os.environ.get("APPTAINER_CONTAINER"),"CPU real container required")
    need(os.environ.get("SLURM_JOB_ID"),"CPU allocation required")
    allocation=json.loads(Path(c["current_cpu_allocation"]["path"]).read_text())
    need(sha(c["current_cpu_allocation"]["path"])==c["current_cpu_allocation"]["sha256"],"CPU allocation digest")
    fields=dict(x.split("=",1) for x in allocation["scontrol_job"].split() if "=" in x)
    need(fields["JobId"]==os.environ["SLURM_JOB_ID"] and fields["JobState"]=="RUNNING","actual running CPU job")
    need(fields["Partition"]=="RM-shared" and fields["Account"]==c["expected_cpu_account"],"CPU account/partition")
    need(fields["BatchHost"].split(".")[0]==socket.gethostname().split(".")[0],"actual compute host")
    need(int(fields["NumNodes"])==1 and int(fields["NumCPUs"])>=4,"CPU resources")
    tres=fields.get("AllocTRES",fields.get("TRES",""))
    need(tres and not re.search(r"(?:^|,)gres/gpu(?:[:=])",tres),"no GPU allocation")
    need(allocation["image_sha256"]=="f50c8e39dd5e2ac1c1a4bdfd443351cb970513fdb10a572725eb53d7396f8697","actual SIF digest")
    need(os.environ.get("HF_HUB_CACHE")=="/work/nvme/beto/swong2" and os.environ.get("TRANSFORMERS_CACHE")=="/work/nvme/beto/swong2","cache bind environment")
    need((out/"groups.json").is_file(),"exact existing Delta-frozen G3 required")
    need(c["frozen_G3"]["path"]==str(out/"groups.json") and sha(out/"groups.json")==c["frozen_G3"]["sha256"],"Delta G3 file digest")
    evidence=Path(c["validation_output"]);need(not evidence.exists() or (evidence.is_dir() and not any(evidence.iterdir())),"validation evidence must be fresh")
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
    env=dict(os.environ,PYTHONPATH=str(runtime))
    os.environ["PYTHONPATH"]=str(runtime)
    started=time.time()
    args=p.parser().parse_args(["--stage","freeze",*base,"--comparison",c["comparison"],"--source-records",c["source_records"]])
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
    need(sha(out/"groups.json")==c["frozen_G3"]["sha256"],"G3 changed during Bridges CPU validation")
    result={"kind":"existing_Delta_G3_Bridges_CPU_validation","status":"PASS","source_commit":c["accepted_source_commit"],"runtime":str(runtime),"parameters_sha256":a.parameters_sha256,"groups_sha256":sha(out/"groups.json"),"science_fields_equal_to_historical_G2":list(SCIENCE_FIELDS),"group_count":len(receipt["groups"]),"prefix_keys":len(p.expected_keys(receipt,4)),"model_geometry":receipt["model_geometry"],"module_origins":origins(),"source_before":source_before,"source_after":source_after,"child_PYTHONPATH":env["PYTHONPATH"],"allocation":allocation,"job_id":os.environ["SLURM_JOB_ID"],"host":socket.gethostname(),"started_unix":started,"finished_unix":time.time(),"model_loaded":False,"GPU_admitted":False,"root_source_acceptance_asserted":True}
    need(result["prefix_keys"]==2484,"prefix domain")
    result["numeric_environment"]=p.numeric_environment()
    result["freeze_executed"]=False
    result["read_stage_scope"]="No bank or score exists: G3 uses owning a1.read_artifact and _validate_live; read_stage remains required for future completed bank/score."
    evidence.mkdir(parents=True,exist_ok=True)
    (evidence/"cpu-readiness.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result,indent=2))
if __name__=="__main__":main()
