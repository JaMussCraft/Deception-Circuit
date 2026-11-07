"""Run in a real Slurm CPU allocation before root submits the GPU attempt."""
import os,pathlib,json,time,traceback
from common import C,L,MAIN,PILOT,sha,write,utc,packet,source,imports,budget,allocation
OUT=pathlib.Path(os.environ['A2_TIMING_PREFLIGHT_OUTPUT']);assert not OUT.exists();OUT.mkdir(parents=True)
started=time.time()
try:
    alloc=allocation(gpu=False);packet();before=source()
    assert not ((MAIN/'bank').exists() or (MAIN/'bank').is_symlink()) and not ((MAIN/'score').exists() or (MAIN/'score').is_symlink()) and not (PILOT.exists() or PILOT.is_symlink())
    p,ar=imports();args=p.parser().parse_args(C['bank_command'][2:]);prepared,selected,sidecar=p._load_context(args);receipt=p.a1.read_artifact(C['groups']);p._validate_live(args,receipt,prepared)
    assert len(receipt['groups'])==9 and receipt['receipt_sha256']==C['groups_receipt_sha256'] and not receipt['injected']
    contracts={task:p.bank_contract(receipt,prepared,task) for task in p.TASKS}
    assert all(len(contract['source_ids'])==400 for contract in contracts.values())
    assert receipt['operations']==list(p.PRIMARY_OPERATIONS) and receipt['independent_donor_seeds']==[]
    b=budget(prospective=True);after=source();assert before==dict(after,checked_utc=before['checked_utc'])
    write(OUT/'COMPLETE.json',dict(complete=True,launch_manifest_sha256=sha(L/'manifest.json'),source=after,allocation=alloc,budget=b,registry_hashes=receipt['registry_hashes'],utility_registry_hashes=receipt['utility_registry_hashes'],grader_registry=receipt['grader_registry'],bank_contracts=contracts,elapsed_seconds=time.time()-started,completed_epoch=time.time(),pretrained_weights_loaded=False,tokenizer_loaded=False,GPU_admission=False))
except BaseException as error:
    write(OUT/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),partial_preserved=True,automatic_retry=False));raise
