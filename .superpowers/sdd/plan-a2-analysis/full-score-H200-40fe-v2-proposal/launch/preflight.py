"""Real CPU allocation; fresh source/access/grader and owning bank validation."""
import os,pathlib,json,time,traceback
from common import C,L,MAIN,sha,write,utc,packet,source,imports,budget,allocation
OUT=pathlib.Path(os.environ['A2_SCORE_PREFLIGHT_OUTPUT']);OUT.mkdir(parents=True,exist_ok=False);started=time.time()
try:
    alloc=allocation(gpu=False);packet();before=source()
    assert not ((MAIN/'score').exists() or (MAIN/'score').is_symlink()) and (MAIN/'bank').is_dir() and not (MAIN/'bank').is_symlink()
    assert sha(MAIN/'bank/banks.json')==C['bank_file_sha256'] and sha(MAIN/'bank/run_manifest.json')==C['bank_manifest_sha256']
    p,ar=imports();args=p.parser().parse_args(C['score_command'][2:]);assert args.stage=='score' and args.limit==0 and args.batch_size==8 and not args.injected
    prepared,selected,sidecar=p._load_context(args);receipt=p.a1.read_artifact(C['groups']);p._validate_live(args,receipt,prepared)
    banks=p.read_stage(MAIN/'bank','banks.json','bank',args,receipt);p.validate_banks(receipt,prepared,banks)
    assert len(receipt['groups'])==9 and receipt['receipt_sha256']==C['groups_receipt_sha256'] and not receipt['injected'] and not banks['injected']
    assert receipt['operations']==list(p.PRIMARY_OPERATIONS) and receipt['independent_donor_seeds']==[]
    assert len(p.expected_keys(receipt,0))==59652
    b=budget(prospective=True);after=source();assert before==dict(after,checked_utc=before['checked_utc'])
    write(OUT/'COMPLETE.json',dict(complete=True,launch_manifest_sha256=sha(L/'manifest.json'),source=after,allocation=alloc,budget=b,bank_file_sha256=C['bank_file_sha256'],bank_manifest_sha256=C['bank_manifest_sha256'],bank_numeric_environment={t:v['contract']['numeric_environment'] for t,v in banks['banks'].items()},bank_execution=banks['execution_provenance'],expected_rows=59652,limit=0,grader_registry=receipt['grader_registry'],elapsed_seconds=time.time()-started,pretrained_weights_loaded=False,tokenizer_loaded=False,GPU_admission=False))
except BaseException as error:
    write(OUT/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),partial_preserved=True,automatic_retry=False));raise
