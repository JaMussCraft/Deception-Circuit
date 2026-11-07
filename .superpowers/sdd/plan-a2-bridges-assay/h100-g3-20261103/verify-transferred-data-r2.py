#!/usr/bin/env python3
"""Source-independent CPU-only transfer proof; no application imports or model load."""
import hashlib, json, os, re, socket, stat, sys, time
from pathlib import Path
MANIFEST_SHA="29960294fbda481dcd7807445b5db8be1157f9c49a1b030a7521287708cf5b7c"
IMAGE_SHA="f50c8e39dd5e2ac1c1a4bdfd443351cb970513fdb10a572725eb53d7396f8697"
ROOT=Path("/projects/beto/swong2/Alignment")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(8*1024*1024),b""): h.update(block)
    return h.hexdigest()
def require(ok,msg):
    if not ok: raise RuntimeError(msg)
def main():
    start=time.monotonic(); manifest,metadata=map(Path,sys.argv[1:3])
    raw=manifest.read_bytes(); require(hashlib.sha256(raw).hexdigest()==MANIFEST_SHA,"manifest digest")
    m=json.loads(raw); meta=json.loads(metadata.read_text())
    require(m["ordinary_count"]==389 and m["ordinary_bytes"]==436913681 and m["alias_count"]==5,"inventory counts")
    require(len(m["ordinary_files"])==389 and len(m["namespace_aliases"])==5,"entry counts")
    require(os.environ.get("SLURM_JOB_ID")==meta["job_id"],"job id")
    fields=dict(x.split("=",1) for x in meta["scontrol_job"].split() if "=" in x)
    require(fields["JobId"]==meta["job_id"] and fields["JobState"]=="RUNNING","live allocation")
    require(fields["Partition"]=="RM-shared" and fields["Account"]=="cis260361p","CPU partition/account")
    host=meta["host"].split(".")[0]
    require(fields["BatchHost"].split(".")[0]==host and socket.gethostname().split(".")[0]==host,"compute host")
    require(int(fields["NumNodes"])==1 and int(fields["NumCPUs"])>=4,"CPU allocation size")
    tres=fields.get("AllocTRES",fields.get("TRES",""))
    require(tres and not re.search(r"(?:^|,)gres/gpu(?:[:=])",tres),"CPU-only allocation")
    require(meta["image_sha256"]==IMAGE_SHA,"image digest")
    require(os.environ.get("CUDA_VISIBLE_DEVICES")=="","CPU visibility")
    require(bool(os.environ.get("APPTAINER_CONTAINER")),"real container required")
    results=[]
    for name,record in sorted(m["ordinary_files"].items()):
        p=Path(name); require(p.is_relative_to(ROOT) and record["path"]==name,"original namespace")
        require(not p.is_symlink() and stat.S_ISREG(p.stat().st_mode),"ordinary file: "+name)
        require(str(p.resolve())==name,"unexpected parent alias: "+name)
        require(p.stat().st_size==record["bytes"],"size: "+name)
        digest=sha(p); require(digest==record["sha256"],"hash: "+name)
        results.append({"path":name,"bytes":record["bytes"],"sha256":digest})
    aliases=[]
    for name,target in sorted(m["namespace_aliases"].items()):
        p=Path(name); require(p.is_symlink() and os.readlink(p)==target,"literal alias: "+name)
        require(p.exists() and str(p.resolve())==str(Path(target).resolve()),"alias resolution: "+name)
        children=[r for r in results if r["path"]==target or r["path"].startswith(target+"/")]
        require(children,"alias target absent from verified closure: "+name)
        for r in children:
            via=p if r["path"]==target else p/Path(r["path"]).relative_to(target)
            require(str(via.resolve())==r["path"],"alias child resolution")
            require(sha(via)==r["sha256"],"alias child hash")
        aliases.append({"path":name,"target":target,"verified_closure_files":len(children),"resolved":str(p.resolve())})
    return {"kind":"Bridges_CPU_transferred_data_proof","status":"PASS","manifest_sha256":MANIFEST_SHA,"ordinary_count":len(results),"ordinary_bytes":sum(r["bytes"] for r in results),"alias_count":len(aliases),"ordinary_files":results,"aliases":aliases,"allocation":meta,"elapsed_seconds":time.monotonic()-start,"python":sys.executable,"model_loaded":False,"source_admitted":False,"production_readiness":False,"final_source_choice_pending":True}
if __name__=="__main__":
    try: print(json.dumps(main(),indent=2))
    except Exception as exc:
        print(json.dumps({"status":"FAIL","error":str(exc),"model_loaded":False,"source_admitted":False},indent=2)); sys.exit(1)
