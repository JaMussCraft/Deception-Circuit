#!/usr/bin/env python3
"""Bridges host Python3.6-compatible finite CPU phase-entry supervisor.
No job creation, catalogue transfer, release creation, model load or source edit.
"""
import argparse,datetime,hashlib,json,os,re,signal,socket,subprocess,sys,time
from pathlib import Path
PHASE="existing_G3_validation"
SOURCE="50e947bb852613e3a270082651f2bd1b7bb0c525"
V=Path("/projects/beto/swong2/Alignment")
def need(ok,msg):
    if not ok: raise RuntimeError(msg)
def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(8388608),b""):h.update(b)
    return h.hexdigest()
def dump(path,obj):
    with Path(path).open("x") as f:json.dump(obj,f,indent=2,allow_nan=False);f.write("\n")
def duration(s):
    days=0
    if "-" in s:d,s=s.split("-",1);days=int(d)
    p=[int(v) for v in s.split(":")]
    if len(p)==2:p.insert(0,0)
    need(len(p)==3,"Slurm duration");return days*86400+p[0]*3600+p[1]*60+p[2]
def end_epoch(s):return datetime.datetime.strptime(s,"%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp()
def allocation(job):
    r=subprocess.run(["scontrol","show","job",job,"-o"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,env=dict(os.environ,TZ="UTC"),timeout=15);need(r.returncode==0,"actual scontrol failed")
    f=dict(x.split("=",1) for x in r.stdout.split() if "=" in x)
    need(f.get("JobId")==job and f.get("JobState")=="RUNNING","actual running job")
    need(f.get("Account")=="cis260361p" and f.get("QOS")=="rm" and f.get("Partition")=="RM-shared","actual CPU placement")
    need(f.get("NumNodes")=="1" and f.get("NumCPUs")=="5" and f.get("CPUs/Task")=="5","actual CPU size")
    need(f.get("Requeue")=="0" and f.get("Restarts")=="0","no requeue/restart")
    need(duration(f["TimeLimit"])==900,"exact fifteen-minute allocation")
    need(f["BatchHost"].split(".")[0]==socket.gethostname().split(".")[0],"actual compute host")
    need(re.search(r"\("+str(os.getuid())+r"\)",f.get("UserId","")),"actual allocation user")
    tres=dict(x.split("=",1) for x in f.get("AllocTRES",f.get("TRES","")).split(",") if "=" in x)
    need(tres.get("cpu")=="5" and tres.get("mem") in ("8G","8192M"),"actual CPU/memory TRES")
    need(not any(k.startswith("gres/gpu") for k in tres),"GPU allocation forbidden")
    for k in ("SLURM_JOB_GPUS","SLURM_STEP_GPUS"):need(not os.environ.get(k),"GPU IDs forbidden")
    for k in ("SLURM_GPUS","SLURM_GPUS_ON_NODE","SLURM_GPUS_PER_NODE","SLURM_GPUS_PER_TASK"):need(os.environ.get(k,"") in ("","0"),"GPU count forbidden")
    need(os.environ.get("CUDA_VISIBLE_DEVICES","")=="","CPU visibility")
    return {"job_id":job,"host":socket.gethostname(),"captured_unix":time.time(),"scontrol_job":r.stdout,"fields":f,"tres":tres,"end_epoch":end_epoch(f["EndTime"]),"slurm_environment":{k:v for k,v in os.environ.items() if k.startswith("SLURM_")}}
def physical(c,virtual):
    p=Path(virtual);rel=p.relative_to(V);need(".." not in rel.parts,"namespace traversal");return Path(c["physical_Alignment"])/rel
def catalogues(c):
    rows=c["catalogues"]
    expected={str(V/"Deception-Circuit/docs/research"/name) for name in ("held_out.json","directions.json")}|{str(V/"Deception-Circuit/.claude/worktrees/specificity-ladder/docs/research"/name) for name in ("held_out.json","directions.json")}
    need(len(rows)==4 and {r["virtual_path"] for r in rows}==expected,"exact four current catalogue routes")
    for row in rows:need(digest(physical(c,row["virtual_path"]))==row["sha256"],"refreshed catalogue digest")
    for route,target in c["namespace_aliases"].items():
        p=physical(c,route);need(p.is_symlink() and os.readlink(str(p))==target,"literal namespace alias")
        need(physical(c,target).exists(),"namespace alias target absent")
    return rows
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--config",required=True);ap.add_argument("--config-sha256",required=True);a=ap.parse_args()
    need(digest(a.config)==a.config_sha256,"root-bound config digest");c=json.loads(Path(a.config).read_text());packet=Path(__file__).resolve().parent
    need(c["phase"]==PHASE and c["source_commit"]==SOURCE,"phase/source")
    need(c["ready_wait_seconds"]==300 and c["finish_reserve_seconds"]==45 and c["kill_grace_seconds"]==15,"fixed finite limits")
    need(digest(packet/"packet-manifest.json")==c["packet_manifest_sha256"],"packet manifest pin")
    need(digest(packet/"proposal.json")==c["proposal_sha256"],"actual proposal pin")
    files=json.loads((packet/"packet-manifest.json").read_text())["files_sha256"]
    for name,h in files.items():need(digest(packet/name)==h,"packet byte drift: "+name)
    need(digest(packet/"cpu-validate-existing-G3-r2.py")=="1c72b4ed5505810c5d78f1885c0c74d6c7fb5f9897b19c964375fa4d679f466e","reviewed validator bytes")
    job=os.environ.get("SLURM_JOB_ID","");need(re.fullmatch(r"[0-9]+",job),"actual job required")
    e=Path(c["physical_evidence_parent"])/job;e.mkdir(parents=True,exist_ok=False)
    first=allocation(job);initial_end=first["end_epoch"];need(initial_end-time.time()>345,"insufficient initial finish margin")
    first["image_sha256"]=digest(c["image"]);need(first["image_sha256"]==c["image_sha256"],"actual SIF digest");dump(e/"allocation-before.json",first)
    need(digest(c["validator_parameters"]["path"])==c["validator_parameters"]["sha256"],"root validator parameters digest")
    params=json.loads(Path(c["validator_parameters"]["path"]).read_text())
    need(params["accepted_source_commit"]==SOURCE and params["frozen_G3"]==c["frozen_G3"],"G3/source root parameters")
    need(digest(physical(c,c["frozen_G3"]["path"]))==c["frozen_G3"]["sha256"],"exact Delta G3 bytes")
    need(digest(c["Delta_G3_proof"]["path"])==c["Delta_G3_proof"]["sha256"],"exact Delta CPU G3 proof")
    proof=json.loads(Path(c["Delta_G3_proof"]["path"]).read_text());need(proof["status"]=="PASS" and proof["source_commit"]==SOURCE and proof["groups_sha256"]==c["frozen_G3"]["sha256"],"Delta owning freeze proof")
    v_e=Path(c["virtual_evidence_parent"])/job
    params["current_cpu_allocation"]={"path":str(e/"allocation-before.json"),"sha256":digest(e/"allocation-before.json")};params["validation_output"]=str(v_e/"validation");params["expected_cpu_account"]="cis260361p"
    dump(e/"actual-parameters.json",params);parameters_sha=digest(e/"actual-parameters.json")
    rows=catalogues(c)
    ready={"state":"READY","phase":PHASE,"job_id":job,"source_commit":SOURCE,"config_sha256":a.config_sha256,"packet_manifest_sha256":c["packet_manifest_sha256"],"proposal_sha256":c["proposal_sha256"],"groups_sha256":c["frozen_G3"]["sha256"],"Delta_G3_proof_sha256":c["Delta_G3_proof"]["sha256"],"catalogues":rows,"allocation_sha256":digest(e/"allocation-before.json"),"parameters_sha256":parameters_sha,"namespace_aliases_sha256":hashlib.sha256(json.dumps(c["namespace_aliases"],sort_keys=True,separators=(",",":")).encode()).hexdigest(),"ready_unix":time.time(),"initial_end_epoch":initial_end,"continuous_live_Delta":False,"model_admitted":False}
    dump(e/"READY.json",ready);release=e/"root-release.json";wait_end=time.monotonic()+300
    while not release.exists():
        current=allocation(job);deadline=min(initial_end,current["end_epoch"])
        need(time.monotonic()<wait_end and time.time()<deadline-45,"finite root release wait expired")
        time.sleep(2)
    body=json.loads(release.read_text());now=time.time()
    for key in ("phase","job_id","source_commit","config_sha256","packet_manifest_sha256","proposal_sha256","groups_sha256","Delta_G3_proof_sha256","catalogues","allocation_sha256","parameters_sha256","namespace_aliases_sha256"):need(body.get(key)==ready[key],"root release identity: "+key)
    need(body.get("Delta_current_catalogues_rechecked") is True,"actual Delta recheck required")
    current_proof=body["Delta_current_catalogue_proof"]
    need(re.fullmatch(r"[0-9a-f]{64}",current_proof["sha256"]) is not None,"current Delta catalogue proof digest")
    need(digest(current_proof["path"])==current_proof["sha256"],"actual root-copied current Delta catalogue proof")
    issued=body["issued_at"];expires=body["expires_at"]
    need(0<=now-issued<=300 and issued<=expires<=issued+300 and now<=expires,"root release age/expiry")
    release_sha=digest(release);catalogues(c)
    current=allocation(job);deadline=min(initial_end,current["end_epoch"]);need(time.time()<deadline-45,"no finish margin")
    dump(e/"allocation-entry.json",current)
    for name,h in files.items():need(digest(packet/name)==h,"packet drift at entry")
    need(digest(physical(c,c["frozen_G3"]["path"]))==c["frozen_G3"]["sha256"],"G3 drift at entry")
    env={"DC_CLUSTER":"bridges2","DC_B2_ALLOC":"cis260361p","CUDA_VISIBLE_DEVICES":"","PYTHONDONTWRITEBYTECODE":"1","G3_RUNTIME":params["accepted_runtime"],"G3_VALIDATOR":str(packet/"cpu-validate-existing-G3-r2.py"),"G3_PARAMETERS":str(e/"actual-parameters.json"),"G3_PARAMETERS_SHA":parameters_sha}
    env.update({k:v for k,v in os.environ.items() if k.startswith("SLURM_")})
    cmd=["apptainer","exec","--cleanenv","--contain","--no-home","--writable-tmpfs","--pwd",params["accepted_runtime"],"--bind",c["physical_Alignment"]+":"+str(V)+":ro","--bind","/ocean:/ocean:ro","--bind",c["physical_HF_hub"]+":/work/nvme/beto/swong2:ro","--bind",str(e)+":"+str(v_e)+":rw"]
    for key,value in sorted(env.items()):cmd.extend(["--env",key+"="+value])
    cmd.extend([c["image"],"bash",str(packet/"run-in-container.sh")]);dump(e/"command.json",{"argv":cmd})
    child=None;term=None;started=time.time();code=1
    with (e/"validation.log").open("x") as log:
        child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            next_check=0
            while child.poll() is None:
                now=time.time()
                if now>=next_check:
                    state=allocation(job);deadline=min(initial_end,state["end_epoch"]);next_check=now+5
                if now>=deadline-45 and term is None:os.killpg(child.pid,signal.SIGTERM);term=now
                if term is not None and now>=term+15:os.killpg(child.pid,signal.SIGKILL)
                time.sleep(.5)
            code=child.returncode
        finally:
            if child.poll() is None:os.killpg(child.pid,signal.SIGKILL);child.wait()
    result={"status":"PASS" if code==0 and term is None else "FAIL","exit_code":code,"phase":PHASE,"job_id":job,"source_commit":SOURCE,"elapsed_seconds":time.time()-started,"release_sha256":release_sha,"Delta_current_catalogue_proof":current_proof,"groups_sha256":c["frozen_G3"]["sha256"],"term_sent_unix":term,"continuous_live_Delta":False,"model_loaded":False,"GPU_admitted":False}
    dump(e/"allocation-after.json",allocation(job));need(digest(release)==release_sha,"release changed after entry");catalogues(c);need(digest(physical(c,c["frozen_G3"]["path"]))==c["frozen_G3"]["sha256"],"G3 modified")
    if code==0:
        actual=json.loads((e/"validation/cpu-readiness.json").read_text());need(actual["status"]=="PASS" and actual["groups_sha256"]==c["frozen_G3"]["sha256"] and actual["freeze_executed"] is False,"owning validation result")
    dump(e/"result.json",result);need(result["status"]=="PASS","CPU validation failed")
if __name__=="__main__":main()
