#!/usr/bin/env python3
"""One discarded mgnp process. A diagnostic observation is never CPU COMPLETE."""
import argparse
import os
from pathlib import Path
import resource
import sys
import time

import runner
import data_path


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--config-sha256',required=True)
    ap.add_argument('--diagnostic-stage',choices=('prime','fresh'),required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--deadline',type=float,required=True);a=ap.parse_args()
    start=time.monotonic();started=time.time();usage=resource.getrusage(resource.RUSAGE_SELF)
    c=runner.read_ref(dict(path=a.config,sha256=a.config_sha256));runner.validate_config(c)
    runner.require(sys.executable==c['python'],'actual bank matching mgnp executable')
    runner.require(a.deadline>time.time() and a.deadline<=started+c['policy'][a.diagnostic_stage+'_cap_seconds'],'fixed child bound')
    v,s=runner.helpers(c);allocation=s.allocation(runner.allocation_config(c))
    runner.require(time.time()<min(a.deadline,allocation['end_epoch']-60),'actual CPU end/finish deadline')
    output=Path(a.output);runner.require(output.parent==Path(c['evidence_output']) and output.name==a.diagnostic_stage and output.is_dir(),'supervisor-created diagnostic output')
    params_ref=dict(path=str(output/'data-parameters.json'),sha256=runner.sha(output/'data-parameters.json'))
    params=runner.read_ref(params_ref);runner.require(params==runner.parameters(c,output,a.deadline),'exact data-only child parameters')
    process_before=runner.metrics()
    result=data_path.execute(v,params)
    runner.ensure_nonoperational(result)
    finished_usage=resource.getrusage(resource.RUSAGE_SELF)
    result.update(pid=os.getpid(),parent_pid=os.getppid(),diagnostic_stage=a.diagnostic_stage,
        started_unix=started,finished_unix=time.time(),wall_seconds=time.monotonic()-start,
        user_seconds=finished_usage.ru_utime-usage.ru_utime,system_seconds=finished_usage.ru_stime-usage.ru_stime,
        peak_RSS_bytes=finished_usage.ru_maxrss*1024,process_before=process_before,process_after=runner.metrics(),
        data_parameters_sha256=params_ref['sha256'],numeric_interpreter=sys.executable,deadline_unix=a.deadline)
    runner.require(time.time()<min(a.deadline,s.allocation(runner.allocation_config(c))['end_epoch']-60),'child guard deadline missed')
    runner.ensure_nonoperational(result);runner.write(output/'child-observation.json',result)
    runner.require(time.time()<a.deadline,'child serialized too late')


if __name__=='__main__':main()
