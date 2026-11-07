class _CompletedPackingProof:
    """Completed-file-bound numerical proof with bounded immutable metadata."""
    def __init__(self,path,*,numeric_cache=None):
        start=time.perf_counter();self.pid=os.getpid();self.path=str(Path(path).absolute())
        self.reference=_freeze_json(object_reference(path));payload=read_object(path)
        require(type(payload.get('injected')) is bool,'explicit measured proof execution class required')
        if not payload['injected']:require(type(payload.get('timing_only')) is bool,'explicit production measured timing stage required')
        self.proof=workload._validate_packing_proof(payload['evidence'],payload['measurement'])
        raw=payload['evidence']['runner_receipt']
        snapshots={bid:[self.proof._rows[(r['task'],r['condition'],r['stream'],r['instance_id'])] for r in rows]
            for bid,rows in payload['evidence']['snapshots'].items()}
        self.metadata=_freeze_json(dict({k:v for k,v in payload.items() if k in ('runtime_profile','injected','source_commit','timing_only','not_target_observations')},
            measurement=dict(profile=self.proof._profile),evidence=dict(snapshots=snapshots,
                runner_receipt=dict(receipt_sha256=raw['receipt_sha256'],scope=dict(profile=self.proof._profile,batches=self.proof._batches)))))
        references=payload.get('numeric_backing_references',{})
        require(isinstance(references,dict),'numeric backing references must be immutable completed bindings')
        if payload.get('injected') is not True and payload.get('timing_only') is False:
            require(references,'selected measurements require actual numeric backing references')
        summaries=tuple(_numeric_backing_proof(backing,reference,self.proof._profile,injected=payload.get('injected') is True,cache=numeric_cache)
            for backing,reference in references.items())
        hashes=frozenset(h for summary in summaries for h in summary['axis_hashes'])
        if hashes:require(all(spec['axis_sha256'] in hashes for spec in self.proof._specs.values()),'measured axis differs from actual numeric backing')
        self.numeric_backing_summaries=tuple((x['axis_hashes'],x['reference']) for x in summaries)
        self.witness=_make_file_witness([path,*references])
        require(object_reference(path)==self.reference,'measured packing bytes changed during validation')
        self.retained_bytes,_=_retained_json_bytes([self.metadata,self.proof._rows,self.proof._specs,self.proof._observed,self.witness.identities,self.numeric_backing_summaries])
        self.validation_seconds=time.perf_counter()-start;self._sealed=True
    def __setattr__(self,name,value):
        if getattr(self,'_sealed',False):raise TypeError('completed packing proofs are immutable')
        object.__setattr__(self,name,value)
    def __delattr__(self,name):raise TypeError('completed packing proofs are immutable')
    def refresh(self):
        require(self.pid==os.getpid(),'packing proofs cannot cross process/restart');_check_file_witness(self.witness)
    def check(self,measurement):self.refresh();return self.proof.check(measurement)
    def __reduce__(self):raise TypeError('completed packing proofs are process-local')
