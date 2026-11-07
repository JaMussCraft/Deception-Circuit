"""Two tiny parser probes only; no runtime staging, tracing, suite or process."""
import hashlib,importlib.util,json,pathlib
from unittest import mock
P=pathlib.Path('/projects/beto/swong2/Alignment/Deception-Circuit/.claude/worktrees/specificity-ladder/.superpowers/sdd/plan-a2-exact-fixture-bridges250/candidate-r2/runtime-probe.py')
sp=importlib.util.spec_from_file_location('review257r2_probe',str(P));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
exe='/virtual/python';control='/control/closure.json';marker='/output/STARTUP-BARRIER';argv=[exe,'/virtual/runtime-probe.py','--closure',control];digest=hashlib.sha256(b'x').hexdigest();entry=dict(kind='file',bytes=1,sha256=digest)
head='execve('+json.dumps(exe)+', '+json.dumps(argv)+', 0x1 /* 1 vars */) = 0\n';tail='openat(AT_FDCWD, '+json.dumps(marker)+', O_RDONLY|O_CLOEXEC) = -1 ENOENT (No such file or directory)\n'
manifest_raw=head+'openat(AT_FDCWD, '+json.dumps(control)+', O_RDONLY|O_CLOEXEC) = 3<'+control+'>\n'+tail
with mock.patch.object(m,'file_digest',lambda path:(1,digest)):
 try:m.check_startup_trace(manifest_raw,argv,marker,{exe:entry},'/cwd')
 except m.Rejected as error:control_rejection=str(error)
 assert control_rejection=='unlisted startup read: '+control
 # The directory open is metadata; readlinkat must nevertheless resolve its
 # actual directory FD, not substitute the process cwd for the consumed link.
 trace=head+'openat(AT_FDCWD, "/actual/dir", O_RDONLY|O_DIRECTORY|O_CLOEXEC) = 3</actual/dir>\n'+'readlinkat(3</actual/dir>, "alias", "target", 4096) = 6\n'+tail
 reads=m.check_startup_trace(trace,argv,marker,{exe:entry,'/cwd/alias':entry},'/cwd')
 assert '/actual/dir/alias' not in reads and '/cwd/alias' in reads
print(json.dumps(dict(control_manifest_rejection=control_rejection,control_manifest_bound_separately_by_existing_load_bound=True,relative_readlinkat_accepted_reads=reads,actual_consumed_link='/actual/dir/alias',actual_consumed_link_undeclared=True,scope='Pure check_startup_trace with file-digest I/O seam; no complete runtime receipt claimed'),indent=2))
