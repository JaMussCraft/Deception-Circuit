#!/usr/bin/env python3
"""Postactivation once-only phase-entry checks, then exec unchanged owning validator."""
import hashlib,json,os,socket,sys,time
from pathlib import Path
import supervisor as host
ctx=json.loads(Path(sys.argv[1]).read_text());host.need(host.digest(ctx["config_path"])==ctx["config_sha256"],"bound config at entry")
c=json.loads(Path(ctx["config_path"]).read_text());e=Path(ctx["virtual_evidence"]);physical=Path(ctx["physical_evidence"])
ready=json.loads((e/"READY.json").read_text());release=e/"root-release.json"
host.need(Path(sys.executable).resolve()==Path("/ocean/projects/cis260361p/swong2/envs/mgnp/bin/python").resolve(),"actual activated packed interpreter")
host.need(os.environ.get("HF_HUB_CACHE")=="/work/nvme/beto/swong2" and os.environ.get("TRANSFORMERS_CACHE")=="/work/nvme/beto/swong2","postactivation cache environment")
host.need(os.environ.get("PYTHONPATH")==json.loads((e/"actual-parameters.json").read_text())["accepted_runtime"],"postactivation source PYTHONPATH")
host.dump(e/"ENTRY_READY.json",{"phase":host.PHASE,"job_id":os.environ["SLURM_JOB_ID"],"release_sha256":ctx["release_sha256"],"pid":os.getpid(),"host":socket.gethostname(),"postactivation_unix":time.time()})
wait_end=time.monotonic()+300
while not (e/"entry-facts.json").exists():
    host.need(time.monotonic()<wait_end and time.time()<ctx["initial_end_epoch"]-45,"postactivation entry wait expired")
    time.sleep(.2)
facts=json.loads((e/"entry-facts.json").read_text());allocation=facts["allocation"];fields=allocation["fields"]
host.need(facts["activation_ready_sha256"]==host.digest(e/"ENTRY_READY.json") and facts["release_sha256"]==ctx["release_sha256"],"actual postactivation allocation linkage")
host.need(fields["JobId"]==os.environ["SLURM_JOB_ID"]==ready["job_id"] and fields["JobState"]=="RUNNING","actual entry job")
host.need(fields["Account"]=="cis260361p" and fields["QOS"]=="rm" and fields["Partition"]=="RM-shared" and fields["NumCPUs"]=="5","actual entry CPU placement")
host.need(fields["BatchHost"].split(".")[0]==socket.gethostname().split(".")[0],"actual entry host")
host.need(facts["image_sha256"]==c["image_sha256"],"postactivation actual image")
body=json.loads(release.read_text())
for key in ("phase","job_id","source_commit","config_sha256","packet_manifest_sha256","proposal_sha256","groups_sha256","Delta_G3_proof_sha256","catalogues","allocation_sha256","parameters_sha256","namespace_aliases_sha256"):
    host.need(body.get(key)==ready[key],"postactivation root release identity: "+key)
host.need(body.get("Delta_current_catalogues_rechecked") is True,"root current Delta attestation")
proof=body["Delta_current_catalogue_proof"];host.need(host.digest(proof["path"])==proof["sha256"],"current Delta proof after activation")
host.catalogues(c)
packet=Path(__file__).resolve().parent
manifest=json.loads((packet/"packet-manifest.json").read_text())
host.need(host.digest(packet/"packet-manifest.json")==c["packet_manifest_sha256"],"packet pin after activation")
for name,digest in manifest["files_sha256"].items():host.need(host.digest(packet/name)==digest,"packet byte drift after activation")
host.need(host.digest(e/"actual-parameters.json")==ctx["parameters_sha256"]==ready["parameters_sha256"],"actual parameters unchanged at entry")
host.need(host.digest(host.physical(c,c["frozen_G3"]["path"]))==c["frozen_G3"]["sha256"],"G3 unchanged at entry")
validator=packet/"cpu-validate-existing-G3-r2.py"
host.need(host.digest(validator)=="1c72b4ed5505810c5d78f1885c0c74d6c7fb5f9897b19c964375fa4d679f466e","original reviewed validator bytes")
command=[sys.executable,str(validator),"--parameters",str(physical/"actual-parameters.json"),"--parameters-sha256",ctx["parameters_sha256"]]
host.dump(e/"owning-entry.json",{"phase":host.PHASE,"job_id":ready["job_id"],"release_sha256":ctx["release_sha256"],"actual_postactivation_allocation_sha256":host.digest(e/"entry-facts.json"),"owning_argv":command,"checked_unix":time.time(),"permission":"one bounded owning validator entry; no retry or freshness-through-internal-calls claim"})
# Final checks deliberately follow all hashing/metadata writes and immediately precede exec.
issued=body["issued_at"];expires=body["expires_at"]
host.need(host.digest(release)==ctx["release_sha256"],"unchanged root release immediately before owning entry")
now=time.time()
host.need(0<=now-issued<=300 and issued<=expires<=issued+300 and now<=expires,"root release expired before owning entry")
host.need(0<=now-allocation["captured_unix"]<=15,"actual allocation not freshly captured after activation")
host.need(now<min(ctx["initial_end_epoch"],allocation["end_epoch"])-45,"actual final finish margin")
os.execv(sys.executable,command)
