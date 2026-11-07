"""Unexecuted proposal: original full selected aggregate or first32 calibration."""
from pathlib import Path
import argparse,hashlib,json,os,resource,time

def main():
    parser=argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--root',required=True);parser.add_argument('--out',required=True)
    parser.add_argument('--phase',required=True,choices=('selected-pilot-aggregate','calibration'))
    args=parser.parse_args();root=Path(args.root).resolve();out=Path(args.out).resolve();w=Path.cwd();began=time.perf_counter()
    expectation=json.loads(Path(__file__).with_name('expectation.json').read_text())
    assert root==Path(expectation['scenario_root']) and out.is_dir()
    from allocation_facts import read_current
    allocation=read_current(w,minimum_remaining_seconds=(5475 if args.phase=='selected-pilot-aggregate' else 1875))
    def write(name,value):
        with (out/name).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    def mark(event,**extra):print(json.dumps(dict(event=event,elapsed_seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,**extra)),flush=True)
    def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    def sources():assert {name:sha(w/name) for name in expectation['source_hashes']}==expectation['source_hashes']
    def cases():
        directory=root/'pilot-verification-cases/selected'
        assert {p.name for p in directory.iterdir()}==set(expectation['case_ids'])
        assert {name:sha(directory/name/'COMPLETE.json') for name in expectation['case_ids']}==expectation['case_marker_sha256']
    write('allocation.json',allocation);sources();cases()
    for ref in expectation['pinned_files']:assert sha(ref['path'])==ref['sha256']
    import subprocess
    command=['sacct','-n','-P','-j','23470886','--format=JobIDRaw,State,ExitCode']
    proc=subprocess.run(command,capture_output=True,text=True,check=True,timeout=15)
    rows=[line.split('|') for line in proc.stdout.splitlines() if line.strip()]
    assert any(row[0]=='23470886' for row in rows)
    assert all(row[1:]==['COMPLETED','0:0'] for row in rows if row[0]=='23470886' or row[0].startswith('23470886.'))
    write('completed-parent.json',dict(command=command,stdout=proc.stdout,stderr=proc.stderr,new_model_forwards=0))
    mark('before_model_parent_source_case_markers_verified')
    from tests import a3_direction_native_scenario as s
    from component_analysis import hooks
    r=s.r;ids=expectation['case_ids'];reads=[];forwards=[0];auth=[False]
    original_capture=hooks.capture_forward;original_read=s._read_pilot_case;original_shard=r.score_runtime_shard;shard_observations=[]
    def counted(*a,**kw):
        if auth[0]:raise AssertionError('Unexpected model forward in original case authentication')
        forwards[0]+=1;return original_capture(*a,**kw)
    def timed_read(path,*a,**kw):
        name=Path(path).name;assert name==ids[len(reads)];start=time.perf_counter();auth[0]=True;mark('case_auth_start',case_id=name)
        try:value=original_read(path,*a,**kw)
        finally:auth[0]=False
        assert sha(Path(path)/'COMPLETE.json')==expectation['case_marker_sha256'][name]
        item=dict(case_id=name,authentication_seconds=time.perf_counter()-start,new_model_forwards=0);reads.append(item);mark('case_auth_end',**item);return value
    def timed_shard(model,design,protocol,shard,**kwargs):
        start=time.perf_counter();before=forwards[0];mark('scoring_shard_start',shard_id=shard['shard_id'])
        value=original_shard(model,design,protocol,shard,**kwargs)
        item=dict(shard_id=shard['shard_id'],actual_forward_calls=forwards[0]-before,score_call_seconds=time.perf_counter()-start)
        shard_observations.append(item);mark('scoring_shard_end',**item);return value
    if args.phase=='selected-pilot-aggregate':
        for name in ('pilot/selected','pilot-verification-aggregate/selected'):assert not (root/name).exists(),'Existing aggregate output refuses fresh attempt'
        s._read_pilot_case=timed_read
    else:
        aggregate=r.read_object(root/'pilot-verification-aggregate/selected')
        assert aggregate['case_order']==ids and aggregate['injected'] is True and aggregate['execution_authorized'] is False
        assert aggregate['case_forwards_reexecuted'] is False and aggregate['new_reconciliation_work_is_actual'] is True
        assert not s.complete_ids(root,'calibration'),'Fresh first32 calibration scope required'
        r.score_runtime_shard=timed_shard
    try:
        hooks.capture_forward=counted;mark('original_phase_start',phase=args.phase)
        result=s.run_phase(root,args.phase,start=0,count=32,resume=True)
        assert result['complete'] is True and result['injected'] is True and result['scientific_execution'] is False and result['execution_authorized'] is False
        assert result['native_forward_calls']==forwards[0]
        extra={}
        if args.phase=='selected-pilot-aggregate':
            assert len(reads)==result['completed_pilot_cases']==63
            aggregate=r.read_object(root/'pilot-verification-aggregate/selected')
            assert aggregate['case_order']==ids and aggregate['case_forwards_reexecuted'] is False
            assert result['original_case_forward_calls_replayed']==aggregate['original_case_forward_calls']
            extra=dict(case_authentication=reads,original_case_forward_calls_replayed=aggregate['original_case_forward_calls'],actual_new_reconciliation_forwards=forwards[0],original_case_forwards_reexecuted=False)
        else:
            assert len(result['shard_ids'])==32 and set(result['shard_ids'])==set(s.complete_ids(root,'calibration'))
            assert [row['shard_id'] for row in shard_observations]==result['shard_ids']
            assert sum(row['actual_forward_calls'] for row in shard_observations)==forwards[0]
            startup={};shards=[]
            for shard_id in result['shard_ids']:
                manifest=r.artifacts._strict_json(root/'runtime-shards'/shard_id/'run_manifest.json');execution=manifest['execution'];ref=execution['candidate_index_startup_reference']
                key=json.dumps(ref,sort_keys=True)
                if key not in startup:
                    assert r.object_reference(ref['path'])==ref
                    startup[key]=dict(reference=ref,record=r.read_object(ref['path']),actual_startup_seconds=execution['candidate_index_startup_seconds'])
                shards.append(dict(shard_id=shard_id,execution=execution))
            assert len(startup)==1
            extra=dict(shard_observations=shard_observations,shards=shards,complete_startup_records=list(startup.values()),actual_calibration_forwards=forwards[0],startup_record_validated_once_after_completion=True)
        sources();cases();mark('original_phase_complete',phase=args.phase,actual_forwards=forwards[0])
        write('coordinator-result.json',dict(phase=args.phase,result=result,extra=extra,case_markers_unchanged=True,source13_unchanged=True,actual_job_id=allocation['job_id'],actual_step_id=allocation['step_id'],actual_host=allocation['host'],injected=True,scientific_execution=False,production_admission=False,wall_seconds=time.perf_counter()-began))
    except BaseException as error:
        write('coordinator-failure.json',dict(phase=args.phase,error=repr(error),actual_observed_forwards=forwards[0],completed_case_authentication=reads,elapsed_seconds=time.perf_counter()-began));raise
    finally:hooks.capture_forward=original_capture;s._read_pilot_case=original_read;r.score_runtime_shard=original_shard

if __name__=='__main__':main()
