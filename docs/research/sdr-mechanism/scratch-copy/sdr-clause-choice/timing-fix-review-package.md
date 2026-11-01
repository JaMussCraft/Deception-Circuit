# Scoped fix review

Base package predates six already-reviewed unused-import removals; remaining diff is terminal/timing recovery and covering tests. No original model sources changed.

## scripts/sdr_clause_choice.py currentSHA 24d02bf06d4ef6fd164f1a34fd5c4414ed98b118d673892bca28ee33cc5bade1
--- package/scripts/sdr_clause_choice.py
+++ current/scripts/sdr_clause_choice.py
@@ -3,14 +3,11 @@
 from __future__ import annotations
 import argparse
 from collections import Counter, defaultdict
-from datetime import datetime, timezone
 import itertools
-import json
 import math
 import os
 from pathlib import Path
 import re
-import signal
 import sys
 import time
 
@@ -319,7 +316,12 @@
     timing = dict(accepted_sha256=file_hash(path), manifest_hash=manifest_id(protocol), publication_seconds=publication,
                   decode_seconds=result.get('elapsed_seconds', 0.)+result.get('external_forward_seconds', 0.),
                   max_forward_seconds=result.get('max_forward_seconds', 0.))
-    write_fresh(Path(directory)/(batch['id']+'.timing.json'), dict(body=timing, sha256=digest(timing)))
+    # Scientific acceptance is already durable. Optional publication timing must
+    # never invalidate it or make its outcomes eligible for re-execution.
+    try:
+        write_fresh(Path(directory)/(batch['id']+'.timing.json'), dict(body=timing, sha256=digest(timing)))
+    except OSError:
+        pass
 
 
 def accepted_batches(directory, protocol):
@@ -547,8 +549,25 @@
 
 
 def batch_timing(directory, protocol, batch_id):
-    path = Path(directory)/(batch_id+'.timing.json'); record = n.read_json(path); body = record['body']
-    if digest(body) != record['sha256'] or body['manifest_hash'] != manifest_id(protocol) or body['accepted_sha256'] != file_hash(Path(directory)/(batch_id+'.accepted.json')):
+    path = Path(directory)/(batch_id+'.timing.json')
+    terminal_path = Path(directory)/(batch_id+'.accepted.json')
+    if not path.exists():
+        terminal = n.read_json(terminal_path); accepted = terminal['body']
+        binding = n.read_json(Path(directory)/('run-'+accepted['run_hash']+'.json'))
+        if digest(accepted) != terminal['sha256'] or accepted['manifest_hash'] != manifest_id(protocol) or accepted['batch']['id'] != batch_id or digest(binding) != accepted['run_hash'] or binding['manifest_hash'] != manifest_id(protocol):
+            raise ValueError('accepted terminal/run timing recovery binding mismatch')
+        result = accepted['result']
+        # Decoder timings were atomic with acceptance. Only publication latency
+        # is unknown: use at least the invocation's declared initial IO budget.
+        body = dict(accepted_sha256=file_hash(terminal_path), manifest_hash=manifest_id(protocol),
+                    publication_seconds=max(1.,binding.get('initial_io_seconds',1.)), publication_measured=False,
+                    decode_seconds=result['elapsed_seconds']+result['external_forward_seconds'],
+                    max_forward_seconds=result['max_forward_seconds'])
+    else:
+        record = n.read_json(path); body = record['body']
+        if digest(body) != record['sha256']:
+            raise ValueError('accepted batch timing binding mismatch')
+    if body['manifest_hash'] != manifest_id(protocol) or body['accepted_sha256'] != file_hash(terminal_path):
         raise ValueError('accepted batch timing binding mismatch')
     if any(not math.isfinite(body[k]) or body[k] <= 0 for k in ('publication_seconds','decode_seconds','max_forward_seconds')):
         raise ValueError('positive measured batch timings required')

## scripts/jobs/run_sdr_clause_choice.sh currentSHA 2c3a771d9edd869042efcc81e117aa664961f655930adb123a44dbc1cc827fe3

## tests/test_sdr_clause_choice.py currentSHA 583a5052c1e206b791827b418e2504115c5005e86367d0a1001c7a6081be2855
--- package/tests/test_sdr_clause_choice.py
+++ current/tests/test_sdr_clause_choice.py
@@ -2,7 +2,6 @@
 from copy import deepcopy
 from collections import Counter
 import json
-from pathlib import Path
 import pytest
 from scripts import sdr_clause_choice as c
 
@@ -208,7 +207,6 @@
 
 @pytest.mark.parametrize('problem',['dtype','shape','nan'])
 def test_external_vector_fails_closed_before_decoding(fake_model,monkeypatch,problem):
-    import torch
     from scripts import sdr_routing_pilot
     model,p,rows,calls=fake_model
     def bad(model,captured):
@@ -323,3 +321,36 @@
     def forbidden(protocol):raise AssertionError('must reject resume before loading')
     monkeypatch.setattr(c,'load_runtime_model',forbidden)
     with pytest.raises(ValueError,match='resume prohibited'):c.run_baseline(p,output,resume=True)
+
+
+def test_crash_between_accepted_terminal_and_optional_timing_recovers_without_rerun(tmp_path,monkeypatch):
+    p,b=protocol_and_batch();result=valid_result();result.update(elapsed_seconds=2.,external_forward_seconds=.2,max_forward_seconds=.1)
+    binding=dict(manifest_hash=c.manifest_id(p),hardware={'name':'cpu'},initial_io_seconds=3.)
+    run_hash=c.digest(binding);c.write_fresh(tmp_path/f'run-{run_hash}.json',binding)
+    original=c.write_fresh
+    class AbruptCrash(BaseException):pass
+    def crash(path,value):
+        if str(path).endswith('.timing.json'):raise AbruptCrash()
+        return original(path,value)
+    monkeypatch.setattr(c,'write_fresh',crash)
+    with pytest.raises(AbruptCrash):c.accept_batch(tmp_path,p,b,result,run_hash)
+    accepted_path=tmp_path/(b['id']+'.accepted.json');before=accepted_path.read_bytes()
+    assert c.accepted_batches(tmp_path,p)=={b['id']:result}
+    timing=c.batch_timing(tmp_path,p,b['id'])
+    assert timing['publication_seconds']>=3. and timing['decode_seconds']==pytest.approx(2.2)
+    assert timing['publication_measured'] is False and accepted_path.read_bytes()==before
+
+
+def test_postaccept_optional_timing_oserror_does_not_poison_run(tmp_path,monkeypatch,fake_runtime):
+    p,calls,decode=fake_runtime;original=c.n.atomic_json
+    def failed_timing(path,value):
+        if str(path).endswith('.timing.json'):raise OSError('injected optional timing publication failure')
+        return original(path,value)
+    monkeypatch.setattr(c.n,'atomic_json',failed_timing)
+    output=tmp_path/'run';result=c.run_baseline(p,output)
+    assert result['coverage']['main_completed']==640 and len(calls)==84
+    assert not list(output.glob('*.failure.json'))
+    assert len(c.accepted_batches(output,p))==84
+    before={path.name:path.read_bytes() for path in output.glob('*.accepted.json')}
+    c.run_baseline(p,output,resume=True)
+    assert len(calls)==84 and all((output/name).read_bytes()==value for name,value in before.items())
