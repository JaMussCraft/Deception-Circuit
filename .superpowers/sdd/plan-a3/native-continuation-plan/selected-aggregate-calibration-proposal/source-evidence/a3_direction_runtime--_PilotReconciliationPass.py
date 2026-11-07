class _PilotReconciliationPass:
    """Atomic model-free scope reconciliation over private immutable inputs."""
    def __init__(self,proofs,inventory,*,guard,injected,extra_witnesses=()):
        require(all(type(p) is _CompletedPackingProof and p.pid==os.getpid() for p in proofs),'validated completed pilot proofs required')
        self.proofs=tuple(proofs);self.inventory=_freeze_json(inventory);self.guard=guard;self.injected=injected
        self._requirement_ids=frozenset(id(r) for r in self.inventory['requirements'])
        expected={}
        for witness in [p.witness for p in proofs]+list(extra_witnesses):
            require(type(witness) is _FileWitness and witness.pid==os.getpid(),'current immutable file witnesses required')
            for path,identity in zip(witness.paths,witness.identities):
                require(path not in expected or expected[path]==identity,'conflicting pilot backing fingerprints')
                expected[path]=identity
        self._paths=tuple(sorted(expected));self._expected=tuple(expected[p] for p in self._paths)
        self._active=False;self._finished=False;self._deadline=None;self._witness=None
        self.verified_bytes=0;self.verification_seconds=0.;self._sealed=True
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):raise TypeError('pilot reconciliation inputs are immutable')
        object.__setattr__(self,name,value)
    def _refresh(self):
        start=time.perf_counter();witness=_make_file_witness(self._paths)
        require(witness.identities==self._expected,'pilot receipt/numeric backing changed across reconciliation')
        volume=sum(row[2][3] for tree in witness.identities for row in tree if row[0]=='file')
        object.__setattr__(self,'verified_bytes',self.verified_bytes+volume)
        object.__setattr__(self,'verification_seconds',self.verification_seconds+time.perf_counter()-start)
        object.__setattr__(self,'_witness',witness)
    def _live_guard(self):
        evidence=self.guard()
        if evidence is None and self.injected:return
        result=evidence.get('reservation',{}) if isinstance(evidence,dict) else {}
        require(result.get('allocation_verified') is True and result.get('execution_authorized') is True,'reconciliation requires current live allocation authority')
        allocation=result.get('allocation',{});end=allocation.get('end_time_unix')
        require(type(end) in (int,float) and math.isfinite(end),'reconciliation needs effective lease deadline')
        deadline=end-self.inventory['finish_reserve_seconds']-result['reservation']['minimum_shard_seconds']
        object.__setattr__(self,'_deadline',deadline);self.check_deadline()
    def check_deadline(self):
        require(self._deadline is None or time.time()<self._deadline,'reconciliation has insufficient live finish time')
    def __enter__(self):
        self._refresh();self._live_guard();object.__setattr__(self,'_active',True);return self
    def model_guard(self):
        self._refresh();self._live_guard();self.check_deadline()
    def check(self,proof,requirement,measurement=None):
        require(self._active and proof in self.proofs and id(requirement) in self._requirement_ids,'unbound reconciliation target/proof')
        self.check_deadline();measurement=requirement if measurement is None else measurement
        require(all(measurement.get(k)==requirement.get(k) for k in ('profile','timing_inputs','axis_scope','donor_convention')),'reconciliation target scope differs from immutable inventory')
        return proof.proof.check(measurement)
    def __exit__(self,kind,value,traceback):
        object.__setattr__(self,'_active',False)
        if kind is None:
            self._refresh();self._live_guard();object.__setattr__(self,'_finished',True)
        return False
    def before_publication(self):
        require(self._finished,'incomplete reconciliation cannot publish')
        self._refresh();self._live_guard()
    def __reduce__(self):raise TypeError('pilot reconciliation passes are process-local')
