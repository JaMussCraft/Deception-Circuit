"""Unbound root-submit measurement adapter. No project import at module import."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time


def describe():
    return dict(status='UNBOUND_PREPARATION_ONLY', source_commit=None, resources=None,
                actual_job=None, source_publication=None, native_imports=False,
                execution_authorized=False, model_loaded=False)


def producer(runtime, args, design, protocol):
    """Exact-object primitive; authentic operational startup uses native main."""
    return runtime.prepare_pilot_target(args, design, protocol, selected=None)


def process_snapshot():
    result = dict(pid=os.getpid(), process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
        process_peak_scope='process lifetime high-water RSS on Linux', process_rss_bytes=None,
        observations_are_upper_bounds=False, cgroup_membership=None, cgroup_rows=[],
        cgroup_scope='entire memory-controller cgroup ancestry including other processes; lifetime peaks')
    try:
        fields=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
        result['process_rss_bytes']=int(fields['VmRSS'].split()[0])*1024
        membership=Path('/proc/self/cgroup').read_text(); result['cgroup_membership']=membership
        rows=[line.split(':',2) for line in membership.splitlines()]
        legacy=next((p for h,c,p in rows if 'memory' in c.split(',')),None)
        relative=legacy or next(p for h,c,p in rows if h=='0' and c=='')
        controller='v1' if legacy else 'v2'
        for line in Path('/proc/self/mountinfo').read_text().splitlines():
            left,right=line.split(' - ',1); left=left.split(); right=right.split()
            if (controller=='v2' and right[0]=='cgroup2') or (controller=='v1' and right[0]=='cgroup' and 'memory' in right[2].split(',')):
                mount=Path(left[4]); root=Path(left[3]); break
        else: raise ValueError('memory-controller mount unavailable')
        rel=Path(relative)
        try: suffix=rel.relative_to(root)
        except ValueError: suffix=Path(relative.lstrip('/'))
        node=mount/suffix
        if not node.is_dir(): raise ValueError('memory-controller path unavailable')
        while True:
            row=dict(path=str(node),controller=controller)
            names=('memory.current','memory.peak','memory.events','memory.max') if controller=='v2' else ('memory.usage_in_bytes','memory.max_usage_in_bytes','memory.failcnt','memory.oom_control','memory.limit_in_bytes')
            for name in names:
                try: row[name]=(node/name).read_text().strip()
                except OSError: row[name]=None
            result['cgroup_rows'].append(row)
            if node==mount: break
            if mount not in node.parents: raise ValueError('cgroup escaped mount')
            node=node.parent
        result['cgroup_applicability']=controller+' actual ancestry; missing values remain unavailable'
    except (OSError, KeyError, ValueError, StopIteration) as error:
        result['cgroup_applicability']='unavailable: '+str(error)
    return result


def stamp():
    usage=resource.getrusage(resource.RUSAGE_SELF)
    return (time.monotonic(),usage.ru_utime,usage.ru_stime)


def elapsed(before):
    return dict(zip(('wall_seconds','user_seconds','system_seconds'),
                    (b-a for a,b in zip(before,stamp()))))


class NullSyntheticObserver:
    """Injection for protocol tests only; cannot assert authentic I/O or coldness."""
    genuine_observation=False
    def __init__(self): self.counts={}
    def __enter__(self): return self
    def __exit__(self,*args): return False


class Observer:
    """Observe pinned Python operations, preserving all native functions/objects.

    Profiling is synchronous and incurs overhead included in measured timings.
    No raw bytes/decoded graph are retained by the observer. This recipe covers
    the pinned Path.read_bytes/common.file_hash/native reader implementation;
    changed implementations require separate review, not assumed equivalence.
    """
    genuine_observation=True
    def __init__(self,runtime,target_path):
        self.runtime=runtime; self.path=os.path.abspath(os.fspath(target_path))
        self.reader_code=runtime._read_prepared_target_object.__code__
        self.parse_code=runtime._prepared_json_buffer.__code__
        self.freeze_code=runtime._freeze_json.__code__
        self.hash_code=runtime.common.file_hash.__code__
        self.counts=dict(full_payload_reads=0,SHA_passes=0,parse_passes=0,
                         freeze_passes=0,target_writes=0,read_bytes=0)
        self.read_code=Path.read_bytes.__code__
        self.write_codes={Path.write_bytes.__code__,Path.write_text.__code__}
    def target(self,value):
        try: return os.path.abspath(os.fspath(value))==self.path
        except TypeError: return False
    def initial_target(self,frame):
        loc=frame.f_locals
        return (frame.f_code is self.reader_code and loc.get('index')==0
                and loc.get('name')=='payload.json' and self.target(Path(loc['root'])/loc['name']))
    def profile(self,frame,event,arg):
        code=frame.f_code; parent=frame.f_back
        if event=='return' and code is self.read_code and self.target(frame.f_locals.get('self')):
            if isinstance(arg,bytes):
                self.counts['full_payload_reads']+=1; self.counts['read_bytes']+=len(arg)
        elif event=='return' and code is self.hash_code and self.target(frame.f_locals.get('path')):
            if isinstance(arg,str): self.counts['SHA_passes']+=1
        elif event=='c_return' and getattr(arg,'__name__','') in ('openssl_sha256','sha256') and self.initial_target(frame):
            self.counts['SHA_passes']+=1
        elif event=='call' and code is self.parse_code and parent and self.initial_target(parent):
            self.counts['parse_passes']+=1
        elif event=='call' and code is self.freeze_code and parent and parent.f_code is self.reader_code:
            self.counts['freeze_passes']+=1
        elif event=='call' and code in self.write_codes and self.target(frame.f_locals.get('self')):
            self.counts['target_writes']+=1
    def __enter__(self):
        if sys.getprofile() is not None: raise ValueError('existing profiler would make observations incomparable')
        sys.setprofile(self.profile); return self
    def __exit__(self,*args):
        sys.setprofile(None); return False


def check_counts(counts):
    expected=dict(full_payload_reads=3,SHA_passes=3,parse_passes=1,freeze_passes=1,target_writes=0)
    if any(counts.get(key)!=value for key,value in expected.items()):
        raise ValueError('actual target operation counts differ: '+repr(counts))


def receiver(runtime,target_reference,preparation_reference,namespace_policy,emit,*,observer_factory=None):
    """One fresh-launch entry trial then same-process repeat; no authority minting.

    Caller must launch this once in a genuinely new process. Synthetic injection
    preserves trial sequencing but its records explicitly disclaim genuine cold
    or native observations. Graphs remain alive through the one final witness.
    """
    if observer_factory is None:
        observer_factory=lambda:Observer(runtime,Path(target_reference['path'])/'payload.json')
    for trial in ('fresh-process','same-process-repeat'):
        record=dict(trial=trial,pid=os.getpid(),status='started',observations_are_upper_bounds=False,
                    filesystem_cache_claim=None,release_policy='drop exact result after final check; gc.collect before repeat')
        result=None; start=stamp(); record['process_before']=process_snapshot()
        try:
            with observer_factory() as observed:
                step=stamp()
                result=runtime._read_prepared_target_object(target_reference,preparation_reference,namespace_policy)
                record['entry']=elapsed(step)
                record['process_retained']=process_snapshot()
                step=stamp(); runtime._check_file_witness(result[3])
                record['final_check']=elapsed(step)
                # Preserve actual small native observations, without copying or changing graph/witness.
                record['native_observed']=result[4]; record['native_resources']=result[5]
            record['actual_operations']=dict(observed.counts)
            record['genuine_observation']=observed.genuine_observation
            if observed.genuine_observation: check_counts(observed.counts)
            record['status']='completed'
        except BaseException as error:
            record.update(status='failed',error_type=type(error).__name__,error=str(error))
            raise
        finally:
            record['timing']=elapsed(start);record['process_after_final']=process_snapshot()
            result=None;gc.collect()
            record['process_after_release']=process_snapshot()
            emit(record)


def require_fresh_process(parent_pid):
    if type(parent_pid) is not int or parent_pid==os.getpid() or parent_pid!=os.getppid():
        raise ValueError('fresh receiver requires actual distinct immediate launcher PID')
    return dict(receiver_pid=os.getpid(),launcher_pid=parent_pid,
                evidence='distinct PID and actual parent match; root supervisor must start new executable once')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--phase',choices=('producer','receiver'))
    args=parser.parse_args(argv)
    if args.dry_run:
        print(json.dumps(describe(),sort_keys=True));return 0
    parser.error('unbound packet: root must authenticate inputs and invoke adapter under existing supervisor')

if __name__=='__main__': raise SystemExit(main())


class PhaseObserver:
    """Inclusive observed native call intervals; nested durations do not sum.

    File-read/hash/write completions cover all paths in each interval, including
    source and guards. They are measured calls, not target-only declarations.
    Peak snapshots retain lifetime/whole-cgroup scope. Instrumentation overhead
    remains charged. No return values or native frames survive callback return.
    """
    def __init__(self,functions):
        self.codes={fn.__code__:name for name,fn in functions.items() if hasattr(fn,'__code__')}
        self.active={};self.rows=[]
    def profile(self,frame,event,arg):
        if event=='call' and frame.f_code in self.codes:
            self.active[id(frame)]=(stamp(),dict(phase=self.codes[frame.f_code],
                process_before=process_snapshot(),file_read_completions=0,file_read_bytes=0,
                SHA_constructor_completions=0,file_write_completions=0,file_write_bytes=0,
                io_scope='all paths in this inclusive call; nested rows overlap'))
        if event=='return' and frame.f_code is Path.read_bytes.__code__ and isinstance(arg,bytes):
            for start,row in self.active.values():
                row['file_read_completions']+=1;row['file_read_bytes']+=len(arg)
        if event=='return' and frame.f_code in (Path.write_bytes.__code__,Path.write_text.__code__) and isinstance(arg,int):
            for start,row in self.active.values():
                row['file_write_completions']+=1;row['file_write_bytes']+=arg
        if event=='c_return' and getattr(arg,'__name__','') in ('openssl_sha256','sha256'):
            for start,row in self.active.values(): row['SHA_constructor_completions']+=1
        if event=='return' and id(frame) in self.active:
            start,row=self.active.pop(id(frame));row.update(elapsed(start))
            row.update(status='returned',process_after=process_snapshot())
            self.rows.append(row)
    def __enter__(self):
        if sys.getprofile() is not None:raise ValueError('existing profiler prevents comparable phase observations')
        sys.setprofile(self.profile);return self
    def __exit__(self,*args):
        sys.setprofile(None)
        for start,row in self.active.values():
            row.update(elapsed(start));row['status']='unfinished';self.rows.append(row)
        self.active.clear();return False


def produce_native(runtime,native_argv,emit):
    """Root supplies authentic native argv; native parser/dispatch/guards run intact.

    Full source/import/allocation/storage authentication belongs to root's
    existing supervisor/driver. This adapter accepts no authority configuration.
    Normal completion is not resource acceptance or scientific authorization.
    """
    functions={}
    for name in ('main','dispatch','live_guard','prepare_pilot_target',
                 '_publish_prepared_target_object','publish_object'):
        fn=getattr(runtime,name,None)
        if fn is not None:functions[name]=fn
    for module_name,symbol in (('workload','build_inventory'),('artifacts','code_hashes')):
        module=getattr(runtime,module_name,None);fn=getattr(module,symbol,None)
        if fn is not None:functions[module_name+'.'+symbol]=fn
    start=stamp();record=dict(phase='producer',pid=os.getpid(),status='started',
        process_before=process_snapshot(),execution_authorized=False,model_loaded=False,
        observations_are_upper_bounds=False,observer_overhead_included=True)
    phases=PhaseObserver(functions)
    try:
        with phases: result=runtime.main(native_argv)
        if result!=0: raise ValueError('native producer returned nonzero: '+repr(result))
        record['status']='completed';return result
    except BaseException as error:
        record.update(status='failed',error_type=type(error).__name__,error=str(error));raise
    finally:
        record.update(timing=elapsed(start),native_phases=phases.rows,process_after=process_snapshot())
        emit(record)


def receive_native(runtime,target_reference,preparation_reference,namespace_policy,emit,*,launcher_pid):
    """Actual new-process gate before untouched lower DATA reader, once per PID."""
    launch=require_fresh_process(launcher_pid)
    global _receiver_launched
    if globals().get('_receiver_launched',False):raise ValueError('receiver entry already used in this process')
    _receiver_launched=True
    def stamped(record):
        record['launch_provenance']=launch;emit(record)
    return receiver(runtime,target_reference,preparation_reference,namespace_policy,stamped)
