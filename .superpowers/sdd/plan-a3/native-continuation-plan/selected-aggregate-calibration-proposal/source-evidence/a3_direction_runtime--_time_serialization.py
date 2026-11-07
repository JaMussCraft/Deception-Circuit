def _time_serialization(shapes,design,protocol,root,guard):
    """Measure real immutable publication, hash reread and numeric serialization.

    Bytes are explicitly inert envelopes derived from frozen source metadata;
    these benchmarks contain no fabricated target outcome observations.
    """
    import tempfile
    raw_sources=[r for rows in design['access_rows'].values() for r in rows]
    raw_sources.extend(r for t in ('ioi','mmlu') for r in design[t+'_validation']+design['utility'][t])
    largest=max((pipeline._selection_source_record(r,s,r.get('task','mechanism')) for r in raw_sources for s in r['streams']),key=lambda r:len(json.dumps(r)))
    times=[];observed=[];total_bytes=0
    parent=Path(root)/'pilot-scratch';parent.mkdir(parents=True,exist_ok=True)
    guard()
    for index,shape in enumerate(shapes):
        if index%32==0:guard()
        with tempfile.TemporaryDirectory(prefix='serialization-',dir=parent) as tmp:
            target=Path(tmp)/'artifact';start=time.perf_counter()
            def writer(directory):
                n=shape['rows'];row=dict(benchmark_no_outcomes=True,source_metadata=largest,
                    numeric_profile=shape.get('profile'),scalar_envelope={f'scalar{k}':-1.7976931348623157e308 for k in range(40)})
                common.write_jsonl(directory/'rows.jsonl',[row for _ in range(n)])
                common.write_json(directory/'run_manifest.json',dict(kind='a3_serialization_benchmark_v1',shape=shape,
                    key_byte_envelope='k'*shape.get('key_bytes',0),startup_reference_byte_envelope='r'*workload.STARTUP_REFERENCE_BYTES,
                    not_scientific_evidence=True))
                if 'numeric_bytes' in shape:
                    count=(shape['numeric_bytes']+3)//4;np.save(directory/'readouts.npy',np.zeros(count,dtype=np.float32),allow_pickle=False)
                    require(np.load(directory/'readouts.npy',allow_pickle=False,mmap_mode='r').nbytes>=shape['numeric_bytes'],'short serialization array')
                artifacts._finish(directory)
            common.publish(target,writer);artifacts._complete(target)
            elapsed=time.perf_counter()-start
            total_bytes+=sum(p.stat().st_size for p in target.iterdir() if p.is_file())
            times.append(elapsed);observed.append(workload.digest(shape))
    return times,observed,total_bytes
