"""Private source-only proof reuse; fresh bytes/protection never confer execution authority.

The owners still validate their full semantic contracts before minting. Immutable
source views thaw on explicit copies, unlike the separate inventory proof views.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import sys
import time
import stat
import weakref

_JSON_SEAL=object()
_STATE_SEAL=object()
_SCAN_SEAL=object()
_SCAN_PLANS=weakref.WeakKeyDictionary()
_SCAN_MINTS=weakref.WeakKeyDictionary()
_clock=time.perf_counter


def require(value,message):
    if not value:raise ValueError(message)


class _SourceDict(dict):
    __slots__=('_seal',)
    def __init__(self,values=(),*,_token=None):
        if _token is not _JSON_SEAL or hasattr(self,'_seal'):raise TypeError('source view construction is private')
        dict.__init__(self,values);object.__setattr__(self,'_seal',_JSON_SEAL)
    def _immutable(self,*a,**k):raise TypeError('authenticated source is immutable')
    __setitem__=__delitem__=clear=pop=popitem=setdefault=update=__ior__=__setattr__=__delattr__=_immutable
    def __copy__(self):return dict(self)
    def __deepcopy__(self,memo):
        out={};memo[id(self)]=out
        out.update((copy.deepcopy(k,memo),copy.deepcopy(v,memo)) for k,v in self.items());return out


class _SourceList(list):
    __slots__=('_seal',)
    def __init__(self,values=(),*,_token=None):
        if _token is not _JSON_SEAL or hasattr(self,'_seal'):raise TypeError('source view construction is private')
        list.__init__(self,values);object.__setattr__(self,'_seal',_JSON_SEAL)
    def _immutable(self,*a,**k):raise TypeError('authenticated source is immutable')
    __setitem__=__delitem__=append=clear=extend=insert=pop=remove=reverse=sort=__iadd__=__imul__=__setattr__=__delattr__=_immutable
    def __copy__(self):return list(self)
    def __deepcopy__(self,memo):
        out=[];memo[id(self)]=out;out.extend(copy.deepcopy(v,memo) for v in self);return out


def freeze(value,_memo=None,_active=None):
    """Copy JSON into sealed views; never trust raw or subclass instances."""
    if type(value) in (_SourceDict,_SourceList):
        require(getattr(value,'_seal',None) is _JSON_SEAL,'unsealed source view');return value
    if type(value) in (str,int,bool,type(None)):return value
    if type(value) is float:
        require(math.isfinite(value),'nonfinite source JSON');return value
    require(type(value) in (dict,list,tuple),'non-JSON or subclass source value')
    memo={} if _memo is None else _memo;active=set() if _active is None else _active
    require(id(value) not in active,'cyclic source JSON')
    if id(value) in memo:return memo[id(value)]
    active.add(id(value))
    if type(value) is dict:
        require(all(type(k) is str for k in value),'non-string source key')
        out=_SourceDict(((k,freeze(v,memo,active)) for k,v in value.items()),_token=_JSON_SEAL)
    else:out=_SourceList((freeze(v,memo,active) for v in value),_token=_JSON_SEAL)
    active.remove(id(value));memo[id(value)]=out;return out


def is_view(value):
    return type(value) in (_SourceDict,_SourceList) and getattr(value,'_seal',None) is _JSON_SEAL


def _links_many(paths):
    """Full lexical/target ancestry; deduplicate shared parent RPCs."""
    rows=[];seen=set()
    def visit(node):
        for candidate in [node]+list(node.parents):
            if candidate in seen:continue
            seen.add(candidate)
            if candidate.is_symlink():
                try:target=candidate.resolve(strict=True)
                except (OSError,RuntimeError) as error:raise ValueError('source path provenance dangling/cycle') from error
                st=candidate.lstat()
                rows.append((str(candidate),st.st_dev,st.st_ino,st.st_mode,st.st_mtime_ns,st.st_ctime_ns,os.readlink(candidate),str(target)))
                literal=Path(os.readlink(candidate))
                visit(literal if literal.is_absolute() else candidate.parent/literal)
    for path in paths:visit(Path(path).absolute())
    return tuple(sorted(rows))


def _links(path):
    return _links_many((path,))


def access_contexts(design,extra_rows):
    """Exactly validate_access's recognized IDs, without copying rich rows."""
    from component_analysis.a3_design import _utility_identity
    from dataset import user_inversion_pipeline as common
    candidates={task:set(design.get('donor_ids',{}).get(task,[])) for task in design.get('access_rows',{})}
    for task,rows in design.get('access_rows',{}).items():
        for row in rows:candidates[task].update(_utility_identity(row)[0])
    for task in ('ioi','mmlu'):
        candidates[task]=set(design.get('donor_ids',{}).get(task,[]))
        for name,rows in design.get('utility',{}).items():
            if (name==task or name.startswith(task+'_')) and isinstance(rows,list):
                for row in rows:
                    if isinstance(row,dict):candidates[task].update(_utility_identity(row)[0])
        for row in design.get(task+'_validation',[]):candidates[task].update(_utility_identity(row)[0])
    for task,rows in extra_rows.items():
        for row in rows:candidates.setdefault(task,set()).update(_utility_identity(row)[0])
    return freeze({task:{'rows':{'D':{split:([{'instance_id':rid} for rid in sorted(ids)] if split=='test' else []) for split in common.SPLITS}}} for task,ids in candidates.items()})


class _Protection:
    __slots__=('_seal','_defaults','contexts','explicit','registry_links','reference_links','grader_links')
    def __init__(self,contexts,registry_paths):
        from dataset import user_inversion_pipeline as common
        from component_analysis import ladder_pipeline as ladder
        if hasattr(self,'_seal'):raise TypeError('protection context cannot be reinitialized')
        object.__setattr__(self,'contexts',contexts)
        object.__setattr__(self,'explicit',tuple(str(Path(p).absolute()) for p in registry_paths))
        paths=[Path(common.PRIMARY_REGISTRY),common.REPO/'docs/research/held_out.json']+[Path(p) for p in self.explicit]
        object.__setattr__(self,'registry_links',{str(p.absolute()):_links(p) for p in paths})
        object.__setattr__(self,'reference_links',{})
        object.__setattr__(self,'grader_links',{str(root/'docs/research/directions.json'):_links(root/'docs/research/directions.json') for root in (ladder.PRIMARY,ladder.REPO)})
        object.__setattr__(self,'_defaults',(str(Path(common.PRIMARY_REGISTRY).absolute()),str(common.REPO.absolute()),str(ladder.PRIMARY.absolute()),str(ladder.REPO.absolute())))
        object.__setattr__(self,'_seal',_STATE_SEAL)
    def __setattr__(self,*args):raise TypeError('protection metadata is immutable')
    def __delattr__(self,*args):raise TypeError('protection metadata is immutable')
    def refresh(self,registry_paths):
        from types import SimpleNamespace
        from dataset import user_inversion_pipeline as common
        from component_analysis import ladder_pipeline as ladder
        require(tuple(str(Path(p).absolute()) for p in registry_paths)==self.explicit,'source registry scope changed')
        require((str(Path(common.PRIMARY_REGISTRY).absolute()),str(common.REPO.absolute()),str(ladder.PRIMARY.absolute()),str(ladder.REPO.absolute()))==self._defaults,'source default registry routing changed')
        for path,expected in self.registry_links.items():require(_links(path)==expected,'registry path provenance changed')
        paths=list(dict.fromkeys([Path(common.PRIMARY_REGISTRY),common.REPO/'docs/research/held_out.json']+[Path(p).resolve() for p in self.explicit]))
        # Read only small CURRENT registries to discover new file-backed sets.
        current={};references={}
        for path in paths:
            require(path.is_file(),'missing required protected registry')
            content=path.read_bytes();raw=json.loads(content);current[str(path)]=hashlib.sha256(content).hexdigest()
            entries=raw.get('sets') if isinstance(raw,dict) else None
            for entry in entries if isinstance(entries,list) else ():
                if isinstance(entry,dict) and 'path' in entry:
                    require(isinstance(entry['path'],str),'invalid protected set reference')
                    lexical=path.parent.parent.parent/entry['path'];key=str(lexical.absolute());shape=_links(lexical)
                    if key in self.reference_links:require(shape==self.reference_links[key],'protected set provenance changed')
                    references[key]=shape
        registries=common.check_registry(SimpleNamespace(splits=list(common.SPLITS),registry=list(self.explicit)),self.contexts)
        require(registries==current,'protected registry changed during refresh')
        for path,expected in references.items():require(_links(path)==expected,'protected set provenance changed during refresh')
        for path,expected in self.registry_links.items():require(_links(path)==expected,'registry path provenance changed during refresh')
        self.reference_links.update(references)
        for path,expected in self.grader_links.items():require(_links(path)==expected,'grader registry provenance changed')
        graders=ladder.grader_registry()
        for path,expected in self.grader_links.items():require(_links(path)==expected,'grader registry provenance changed during refresh')
        return registries,graders


def _peak_bytes():return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024


def _rss_bytes():
    try:return int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
    except (OSError,ValueError,IndexError):return _peak_bytes()


def _outer(value):return tuple((k,id(v)) for k,v in value.items())


def _scan_identity(st):
    return (st.st_dev,st.st_ino,st.st_mode,st.st_size,st.st_mtime_ns,st.st_ctime_ns)


def _scan_lstat(path):
    try:return _scan_identity(Path(path).lstat())
    except (OSError,RuntimeError) as error:raise ValueError('immutable referenced source path missing/invalid') from error


def _copy_scan_tuple(value):
    if type(value) in (str,int):return value
    require(type(value) is tuple,'invalid source scan identity shape')
    return tuple(_copy_scan_tuple(item) for item in value)


def _compile_scan_routes(paths):
    """Mint-only graph discovery, retaining lexical literals and all target routes."""
    nodes={}
    def visit(node):
        node=Path(node).absolute()
        for candidate in [node]+list(node.parents):
            key=str(candidate)
            if key in nodes:continue
            identity=_scan_lstat(candidate);mode=identity[2]
            if stat.S_ISLNK(mode):
                literal=os.readlink(candidate)
                nodes[key]=(key,'symlink',identity,literal)
                try:target=candidate.resolve(strict=True)
                except (OSError,RuntimeError) as error:raise ValueError('immutable referenced source route dangling/cycle') from error
                spelling=Path(literal)
                visit(spelling if spelling.is_absolute() else candidate.parent/spelling)
                visit(target)
            else:
                require(stat.S_ISDIR(mode) or stat.S_ISREG(mode),'unsupported source route kind')
                nodes[key]=(key,'directory' if stat.S_ISDIR(mode) else 'file')
    for path in paths:visit(path)
    return tuple(nodes[key] for key in sorted(nodes,key=lambda key:(len(Path(key).parts),key)))


def _read_source_file(path,expected):
    """One complete occurrence, bound to its opened regular-file descriptor."""
    try:
        with Path(path).open('rb') as handle:
            before=_scan_identity(os.fstat(handle.fileno()))
            require(stat.S_ISREG(before[2]) and before==expected,'immutable referenced source descriptor changed')
            content=handle.read()
            require(len(content)==expected[3] and handle.read(1)==b'','immutable referenced source incomplete read')
            digest=hashlib.sha256(content).hexdigest()
            require(_scan_identity(os.fstat(handle.fileno()))==expected,'immutable referenced source changed during read')
        require(_scan_lstat(path)==expected,'immutable referenced source path replaced after read')
        return digest
    except (OSError,RuntimeError) as error:raise ValueError('immutable referenced source file unreadable') from error


class _SourceScanPlan:
    """Private mint-registered plan; the legacy witness itself is not a mint token."""
    __slots__=('_seal','_pid','_owner','_owner_seal','_witness','_dictionary','_binding','_paths_ref','_rows_ref','_roots','_rows','_routes','_record','__weakref__')
    def __init__(self,witness,*,_token=None,owner=None,owner_seal=None):
        from component_analysis.a3_direction_runtime import _FileWitness
        if _token is None or _token is not _SCAN_MINTS.get(witness) or hasattr(self,'_seal') or self in _SCAN_PLANS:raise TypeError('source scan plan construction is private')
        require(type(witness) is _FileWitness and witness.pid==os.getpid() and witness._sealed is True,'invalid owner source witness')
        roots=_copy_scan_tuple(witness.paths);rows=_copy_scan_tuple(witness.identities)
        require(bool(roots) and len(roots)==len(rows) and all(rows),'empty/incomplete owner source witness')
        paths=list(roots)
        for tree in rows:
            for row in tree:
                paths.append(row[1])
                if row[0]=='symlink':
                    literal=Path(row[3]);paths.extend((str(literal if literal.is_absolute() else Path(row[1]).parent/literal),row[4]))
        values=dict(_pid=os.getpid(),_owner=owner,_owner_seal=owner_seal,_witness=witness,_dictionary=vars(witness),
            _binding=tuple((key,id(value)) for key,value in vars(witness).items()),_paths_ref=witness.paths,_rows_ref=witness.identities,
            _roots=roots,_rows=rows,_routes=_compile_scan_routes(paths))
        for key,value in values.items():object.__setattr__(self,key,value)
        object.__setattr__(self,'_seal',_SCAN_SEAL)
        record=tuple((key,getattr(self,key)) for key in self.__slots__ if key not in ('_record','__weakref__'))
        object.__setattr__(self,'_record',record)
        _SCAN_PLANS[self]=record
        self._authenticate(witness)
    def __setattr__(self,*args):raise TypeError('source scan plan is immutable')
    def __delattr__(self,*args):raise TypeError('source scan plan is immutable')
    def __reduce__(self):raise TypeError('source scan plans are process-local')
    def _authenticate(self,witness):
        from component_analysis.a3_direction_runtime import _FileWitness
        require(type(self) is _SourceScanPlan and self in _SCAN_PLANS,'unminted source scan plan')
        record=_SCAN_PLANS[self]
        require(record is self._record and all(getattr(self,key,None) is value for key,value in record),'source scan plan fields changed')
        require(self._seal is _SCAN_SEAL and self._pid==os.getpid(),'source scan plan process changed')
        require(type(witness) is _FileWitness and witness is self._witness,'source witness replaced')
        require(vars(witness) is self._dictionary and tuple((key,id(value)) for key,value in vars(witness).items())==self._binding,'source witness reinitialized/altered')
        require(witness.pid==self._pid and witness._sealed is True and witness.paths is self._paths_ref and witness.identities is self._rows_ref,'source witness binding changed')
        require(witness.paths==self._roots and witness.identities==self._rows and bool(self._roots) and all(self._rows),'source witness rows changed')
    def _routes_now(self):
        observed=[]
        for row in self._routes:
            identity=_scan_lstat(row[0]);mode=identity[2]
            if row[1]=='symlink':
                require(stat.S_ISLNK(mode) and identity==row[2] and os.readlink(row[0])==row[3],'immutable referenced source route provenance changed')
                observed.append((row[0],identity,row[3]))
            else:
                require((stat.S_ISDIR(mode) if row[1]=='directory' else stat.S_ISREG(mode)),'immutable referenced source route kind changed')
                # Ordinary parent content times/membership are not frozen source.
                # Their routing identities must remain coherent within THIS scan.
                observed.append((row[0],identity[:3]))
        return tuple(observed)
    def _rows_now(self,*,hash_files):
        self._authenticate(self._witness)
        result=[]
        for tree in self._rows:
            observed=[]
            for row in tree:
                identity=_scan_lstat(row[1])
                require(identity==row[2],'immutable referenced source file/tree fingerprint changed')
                if row[0]=='file':
                    require(stat.S_ISREG(identity[2]),'immutable referenced source file kind changed')
                    digest=_read_source_file(row[1],row[2]) if hash_files else row[3]
                    observed.append(('file',row[1],identity,digest))
                elif row[0]=='directory':
                    require(stat.S_ISDIR(identity[2]),'immutable referenced source directory kind changed')
                    children=tuple(sorted(p.name for p in Path(row[1]).iterdir()))
                    observed.append(('directory',row[1],identity,children))
                else:
                    require(row[0]=='symlink' and stat.S_ISLNK(identity[2]),'immutable referenced source link kind changed')
                    observed.append(('symlink',row[1],identity,os.readlink(row[1]),row[4],_scan_lstat(row[4])))
            result.append(tuple(observed))
        actual=tuple(result)
        require(actual==self._rows,'immutable referenced source file/tree fingerprint changed')
        return actual


def _check_source_file_witness(witness,plan):
    require(type(plan) is _SourceScanPlan,'invalid source scan plan')
    plan._authenticate(witness)
    before=plan._routes_now()
    plan._rows_now(hash_files=True)
    return before


def _close_source_file_witness(witness,plan,before):
    plan._authenticate(witness)
    # Independent closing PATH/membership checks cover replacement of an earlier
    # file, not merely the last opened descriptor. All route metadata is fresh.
    plan._rows_now(hash_files=False)
    require(plan._routes_now()==before,'immutable referenced source routing changed during scan')


class _SourceState:
    __slots__=('_seal','_pid','_owner','_owner_seal','_scope','_originals','_bindings','_views','_witness','_scan_plan','_static_paths','_static_links','_missing','_glob','_protection','_base','_initialization','_stats')
    def __init__(self,*,_token=None,**values):
        if _token is not _STATE_SEAL or hasattr(self,'_seal'):raise TypeError('source state construction is private')
        for key,value in values.items():object.__setattr__(self,key,value)
        object.__setattr__(self,'_seal',_STATE_SEAL)
    def __setattr__(self,*args):raise TypeError('source proof is immutable')
    def __delattr__(self,*args):raise TypeError('source proof is immutable')
    def __reduce__(self):raise TypeError('source states are process-local')
    def _check(self):
        require(getattr(self,'_seal',None) is _STATE_SEAL,'unsealed source state')
        require(self._pid==os.getpid(),'source state cannot cross process/restart')
        require(type(self._scan_plan) is _SourceScanPlan,'invalid source scan plan')
        self._scan_plan._authenticate(self._witness)
        require(self._scan_plan._owner==self._owner and self._scan_plan._owner_seal is self._owner_seal,'source scan owner changed')
    def view(self,name):self._check();return self._views[name]
    def stats(self):
        self._check()
        # Walk the actual retained object graph, including witness dictionaries and
        # private slots; class/module/function globals are never proof components.
        from component_analysis.a3_direction_runtime import _FileWitness
        seen=set()
        def size(value):
            if id(value) in seen:return 0
            seen.add(id(value));total=sys.getsizeof(value)
            if isinstance(value,dict):total+=sum(size(k)+size(v) for k,v in value.items())
            elif isinstance(value,(list,tuple,set,frozenset)):total+=sum(size(v) for v in value)
            if type(value) in (_SourceState,_SourceScanPlan,_Protection,_SourceDict,_SourceList):
                for name in value.__slots__:
                    if hasattr(value,name):total+=size(getattr(value,name))
            elif type(value) is _FileWitness:total+=size(vars(value))
            return total
        plan_bytes=size(self._scan_plan);seen.clear();retained=size(self)
        # Charge the actual shared weak mint table conservatively; never follow
        # its weak references into other owners' retained source graphs.
        registration=sum(sys.getsizeof(table)+sys.getsizeof(table.data)+sum(size(ref) for ref in table.data) for table in (_SCAN_PLANS,_SCAN_MINTS))
        result={**self._stats,**self._initialization,'retained_bytes':retained+registration,
            'scan_plan_bytes':plan_bytes,'scan_registration_bytes':registration}
        return copy.deepcopy(result)
    def refresh(self,*,owner,bound_inputs,registry_paths,scope):
        self._check();require(owner==self._owner and scope==self._scope,'source owner/scope changed')
        for name,value in bound_inputs.items():
            require(name in self._views and (value is self._views[name] or value is self._originals[name]),'source object replaced')
        for name,value in self._originals.items():require(_outer(value)==self._bindings[name],'source outer binding changed')
        from component_analysis import a3_direction_runtime as authority
        started=_clock()
        scan_before=_check_source_file_witness(self._witness,self._scan_plan)
        for path,links in self._missing:
            require(not Path(path).exists() and not Path(path).is_symlink() and _links(path)==links,'missing source dependency appeared/redirected')
        for folder,pattern,expected in self._glob:
            require(tuple(str(p) for p in sorted(Path(folder).glob(pattern)))==expected,'source closure membership changed')
        registries,graders=self._protection.refresh(registry_paths)
        _close_source_file_witness(self._witness,self._scan_plan,scan_before)
        self._stats['refreshes']+=1;self._stats['refresh_seconds']+=_clock()-started
        evidence=copy.deepcopy(self._base)
        evidence.update(registry_hashes=registries,grader_registry=graders)
        if self._owner=='mask':evidence['H_bank_protection']=dict(registries)
        return evidence


def build_state(*,owner,originals,artifacts,dependencies,semantic,registry_paths,scope,started=None,precheck=None,owner_seal=None):
    """Owners supply their FULL validator; callbacks are discarded before return."""
    from component_analysis import a3_direction_runtime as authority,ladder_pipeline as ladder
    started=_clock() if started is None else started;rss_before=_rss_bytes();peak_before=_peak_bytes()
    require(set(originals)==set(artifacts),'source artifact bindings incomplete')
    require(all(type(v) is dict for v in originals.values()),'original source objects must be ordinary dictionaries')
    before={name:_outer(v) for name,v in originals.items()}
    owned={name:freeze(v) for name,v in originals.items()}
    roots=[]
    for kind,path in artifacts.values():
        require(kind in ('artifact','object'),'unknown source envelope')
        roots.append(Path(path).absolute())
    # Bind the ACTUAL envelopes before comparing their payloads to the owned
    # views. Dependency discovery must not be able to replace and rebaseline them.
    artifact_witness=authority._make_file_witness(sorted(set(map(str,roots))))
    artifact_paths=tuple(sorted(set(artifact_witness.paths)|{row[1] for tree in artifact_witness.identities for row in tree}))
    artifact_links=_links_many(artifact_paths)
    for name,(kind,path) in artifacts.items():
        actual=ladder.read_artifact(path) if kind=='artifact' else authority.read_object(path)
        require(actual==owned[name],'source object differs from actual artifact')
    if precheck is not None:precheck(owned)
    paths,missing,glob=dependencies(owned);roots.extend(Path(p).absolute() for p in paths)
    authority._check_file_witness(artifact_witness)
    require(_links_many(artifact_paths)==artifact_links,'source envelope provenance changed during discovery')
    # grader_registry hashes every actual grader file. Bind the same complete
    # lexical/glob closure as static source, not only its content-hash decision.
    from evaluation.grader_hash import grader_files,GRADER_GLOBS
    grader_root=Path(ladder.REPO).absolute()
    roots.extend(grader_root/name for name in grader_files(root=str(grader_root)))
    glob=list(glob)+[(grader_root,pattern) for pattern in GRADER_GLOBS]
    witness=authority._make_file_witness(sorted(set(map(str,roots))))
    # Only this owner factory creates a one-shot receipt for its exact witness.
    # A caller-made exact-type/PID/sealed witness is not mint provenance.
    scan_mint=object();_SCAN_MINTS[witness]=scan_mint
    try:scan_plan=_SourceScanPlan(witness,_token=scan_mint,owner=owner,owner_seal=owner_seal)
    finally:_SCAN_MINTS.pop(witness,None)
    del scan_mint
    static_paths=tuple(sorted(set(witness.paths)|{row[1] for tree in witness.identities for row in tree}))
    static_links=_links_many(static_paths)
    absent=[]
    for p in missing:
        require(not Path(p).exists() and not Path(p).is_symlink(),'expected missing source exists')
        absent.append((str(Path(p).absolute()),_links(p)))
    watched=[(str(Path(folder).absolute()),pattern,tuple(str(p) for p in sorted(Path(folder).absolute().glob(pattern)))) for folder,pattern in glob]
    base,extra=semantic(owned)
    protection=_Protection(access_contexts(owned['design'],extra),registry_paths)
    registries,graders=protection.refresh(registry_paths)
    authority._check_file_witness(artifact_witness)
    require(_links_many(artifact_paths)==artifact_links,'source envelope provenance changed during initialization')
    authority._check_file_witness(witness)
    scan_plan._authenticate(witness)
    scan_plan._routes_now()
    require(_links_many(static_paths)==static_links,'immutable source path provenance changed during initialization')
    for path,links in absent:
        require(not Path(path).exists() and not Path(path).is_symlink() and _links(path)==links,'missing source changed during initialization')
    for folder,pattern,expected in watched:
        require(tuple(str(p) for p in sorted(Path(folder).glob(pattern)))==expected,'source closure changed during initialization')
    for name,value in originals.items():
        require(_outer(value)==before[name] and value==owned[name],'source input changed during initialization')
    for name,value in originals.items():
        for key,item in owned[name].items():value[key]=item
    static_base={k:v for k,v in base.items() if k not in ('registry_hashes','grader_registry','H_bank_protection')}
    state=_SourceState(_token=_STATE_SEAL,_pid=os.getpid(),_owner=owner,_owner_seal=owner_seal,_scope=freeze(scope),_originals=dict(originals),
        _bindings={name:_outer(value) for name,value in originals.items()},_views=freeze(owned),_witness=witness,_scan_plan=scan_plan,_static_paths=static_paths,_static_links=static_links,
        _missing=tuple(absent),_glob=tuple(watched),_protection=protection,_base=freeze(static_base),
        _initialization=None,_stats=dict(refreshes=0,refresh_seconds=0.))
    # Discard parse/validation-only payloads and callbacks before sampling the
    # returned-state RSS; the retained context owns only its sealed source graph.
    del actual,base,extra,static_base,owned,semantic,dependencies,precheck,artifact_witness,artifact_paths,artifact_links
    # Finalize measured facts after construction and transient payload release.
    peak=_peak_bytes();rss_after=_rss_bytes()
    facts=dict(roots=len(scan_plan._roots),verified_bytes=sum(row[2][3] for tree in scan_plan._rows for row in tree if row[0]=='file'),
        host_peak_bytes=peak,host_peak_before_bytes=peak_before,rss_before_bytes=rss_before,rss_after_bytes=rss_after,
        initialization_transient_upper_bytes=max(0,peak-rss_after))
    facts['initialization_seconds']=_clock()-started
    object.__setattr__(state,'_initialization',freeze(facts))
    return state


def checked_state(value,owner,owner_seal):
    require(type(value) is _SourceState,'caller metadata is not a source state');value._check()
    require(value._owner==owner and value._owner_seal is owner_seal,'source owner validator seal differs');return value


def startup_seconds(seconds,state):
    if state is None:return seconds
    require(type(state) is _SourceState,'invalid source startup proof');state._check()
    return seconds+state._initialization['initialization_seconds']


def host_peak_bytes(guard=None):
    state=getattr(guard,'_source_state',None)
    if state is None:return _peak_bytes()
    require(type(state) is _SourceState,'invalid source memory proof');state._check()
    return max(_peak_bytes(),state._initialization['host_peak_bytes'])


def source_dependencies(design,*,root,owner_paths=()):
    """All immutable files read by the existing full live source validators."""
    from component_analysis import a3_pipeline,a3_direction_artifacts as artifacts,ladder_pipeline as ladder
    evidence=design['parent_evidence'];parent,_,current=a3_pipeline.load_a1_parents(evidence['prepared_path'],evidence['selected_path'])
    require(current==evidence,'changed source ancestry while discovering dependencies')
    paths=[evidence[k] for k in ('prepared_path','selected_path','completion_path')]
    paths.extend(owner_paths)
    for field in ('source_hashes','selection_hashes'):
        for name in parent[field]:paths.append(Path(name) if Path(name).is_absolute() else Path(design['a1_repo_root'])/name)
    paths.extend(Path(root)/name for name in parent['code_hashes'])
    paths.extend(Path(root)/name for name in design['direction_protocol']['code_hashes'])
    paths.extend(design['historical_source_hashes']);paths.append(design['matched_build_path'])
    for manifest in (design.get('mmlu_validation_candidates_manifest',{}),design.get('utility',{}).get('mmlu_manifest',{})):
        for name,sha in manifest.get('parquet_hashes',{}).items():
            artifacts.validate_cached_utility_source(manifest['snapshot'],name,sha)
            paths.append(Path(manifest['snapshot'])/name)
    return paths,[],[(Path(root)/'component_analysis','a3_direction_*.py')]


def new30_dependencies():
    """Lexical JSON-only archived paths, including the first absent link."""
    study=Path('/projects/beto/swong2/Alignment/Deception-Circuit/outputs/_studies/selective-deception/study')
    receipt=study/'sparse-optimization-v4/comparison/selection-receipt.json';paths=[];missing=[]
    if not receipt.is_file():return paths,[receipt]
    import json
    data=json.loads(receipt.read_text());paths.append(receipt)
    matches=[m for m in data['masks'] if m['label']=='new-allW30'];require(len(matches)==1,'ambiguous New30 dependency')
    selected=matches[0];proposal=selected['source_proposal'];links=[selected['head_list']['path']]+[proposal[k+'_path'] for k in ('export','manifest','run_identity')]
    for link in links:
        require('selective-deception/' in link,'invalid New30 dependency path')
        path=study/link.split('selective-deception/',1)[1]
        require(path.resolve().is_relative_to(study.resolve()),'escaped New30 dependency')
        if not path.is_file():missing.append(path);break
        paths.append(path)
    return paths,missing
