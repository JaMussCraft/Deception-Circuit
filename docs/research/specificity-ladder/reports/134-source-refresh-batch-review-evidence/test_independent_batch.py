from pathlib import Path
import importlib.util,os,json,copy,hashlib
import pytest
R=Path(os.environ['REVIEW134_RUNTIME']);spec=importlib.util.spec_from_file_location('review134_fixture',R/'tests/test_a3_source_validation.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
@pytest.fixture(autouse=True)
def fixture_bytes_only(monkeypatch):monkeypatch.setattr(f.shutil,'copy2',f.shutil.copyfile)

@pytest.mark.parametrize('slot',['_seal','_pid','_owner','_owner_seal','_witness','_dictionary','_binding','_paths_ref','_rows_ref','_roots','_rows','_routes','_record'])
def test_each_registered_raw_slot_change_rejects(tmp_path,monkeypatch,slot):
 c=f.setup_case(tmp_path,monkeypatch);s=c.build(owner_seal=object());plan=s._scan_plan;old=getattr(plan,slot);new=() if isinstance(old,tuple) else ({} if isinstance(old,dict) else object());object.__setattr__(plan,slot,new)
 with pytest.raises((ValueError,TypeError)):f.refresh(c,s)

@pytest.mark.parametrize('damage',['dictionary','empty_reinit','same_reinit','equal_rows_new_tuple'])
def test_original_witness_binding_is_not_rebaselineable(tmp_path,monkeypatch,damage):
 c=f.setup_case(tmp_path,monkeypatch);s=c.build();w=s._witness
 if damage=='dictionary':object.__setattr__(w,'__dict__',dict(vars(w)))
 elif damage=='equal_rows_new_tuple':object.__setattr__(w,'identities',tuple(x for x in w.identities))
 else:
  roots=w.paths;del w._sealed;w.__init__([] if damage=='empty_reinit' else roots)
 with pytest.raises((ValueError,TypeError)):f.refresh(c,s)

def test_copied_raw_plan_cannot_inherit_registration(tmp_path,monkeypatch):
 c=f.setup_case(tmp_path,monkeypatch);s=c.build();raw=object.__new__(type(s._scan_plan))
 for slot in type(raw).__slots__:
  if slot!='__weakref__':object.__setattr__(raw,slot,getattr(s._scan_plan,slot))
 with pytest.raises((ValueError,TypeError)):c.s._check_source_file_witness(s._witness,raw)

@pytest.mark.parametrize('damage',['bytes_same_size_mtime','same_bytes_replace','missing','same_bytes_link','extra_artifact_child'])
def test_change_after_every_file_read_is_caught_only_at_closing(tmp_path,monkeypatch,damage):
 c=f.setup_case(tmp_path,monkeypatch);s=c.build();expected=[r for t in s._witness.identities for r in t if r[0]=='file'];real=c.s._read_source_file;calls=[]
 def reading(path,identity):
  result=real(path,identity);calls.append(str(path))
  if len(calls)==len(expected):
   if damage=='bytes_same_size_mtime':
    stamp=c.static.stat().st_mtime_ns;c.static.write_bytes(b'changed!');os.utime(c.static,ns=(stamp,stamp))
   elif damage=='same_bytes_replace':
    p=tmp_path/'new';p.write_bytes(c.static.read_bytes());p.replace(c.static)
   elif damage=='missing':c.static.unlink()
   elif damage=='same_bytes_link':
    p=tmp_path/'same';p.write_bytes(c.static.read_bytes());c.static.unlink();c.static.symlink_to(p)
   else:(c.prepared_path/'unexpected').write_text('extra')
  return result
 monkeypatch.setattr(c.s,'_read_source_file',reading)
 with pytest.raises(ValueError):f.refresh(c,s)
 assert len(calls)==len(expected)

def test_same_inode_file_through_new_parent_alias_cannot_hide_at_closing(tmp_path,monkeypatch):
 c=f.setup_case(tmp_path,monkeypatch);folder=tmp_path/'route';folder.mkdir();file=folder/'file';file.write_text('same')
 s=c.s.build_state(owner='fixture',originals={'design':c.design,'prepared':c.prepared},artifacts={'design':('artifact',c.design_path),'prepared':('object',c.prepared_path)},dependencies=lambda owned:([file,c.static],[],[]),semantic=lambda owned:({},{}),registry_paths=[],scope={'commit':'a'*40})
 expected=sum(r[0]=='file' for t in s._witness.identities for r in t);real=c.s._read_source_file;calls=[]
 def reading(path,identity):
  value=real(path,identity);calls.append(path)
  if len(calls)==expected:
   target=tmp_path/'moved';folder.rename(target);folder.symlink_to(target)
  return value
 monkeypatch.setattr(c.s,'_read_source_file',reading)
 with pytest.raises(ValueError):f.refresh(c,s)
 assert len(calls)==expected

@pytest.mark.parametrize('overlap',[False,True])
def test_current_atomic_registry_after_hash_is_fresh_not_frozen(tmp_path,monkeypatch,overlap):
 c=f.setup_case(tmp_path,monkeypatch);s=c.build();count=sum(r[0]=='file' for t in s._witness.identities for r in t);real=c.s._read_source_file;seen=[];registry=c.primary/'docs/research/held_out.json'
 def reading(path,identity):
  value=real(path,identity);seen.append(path)
  if len(seen)==count:
   p=registry.with_suffix('.next');p.write_text(json.dumps({'schema':1,'sets':[{'ids':['recipient' if overlap else 'unrelated-review134']}]}));p.replace(registry)
  return value
 monkeypatch.setattr(c.s,'_read_source_file',reading)
 if overlap:
  with pytest.raises(ValueError,match='overlap'):f.refresh(c,s)
 else:assert f.refresh(c,s)['registry_hashes'][str(registry)]==hashlib.sha256(registry.read_bytes()).hexdigest()
 assert len(seen)==count

def test_all_duplicate_bytes_and_descriptor_checks_repeat_per_refresh(tmp_path,monkeypatch):
 c,s,tree,target,middle=f.batch_tree_case(tmp_path,monkeypatch);from component_analysis import a3_direction_runtime as a
 assert s._scan_plan._rows_now(hash_files=True)==tuple(a._file_tree_identity(p) for p in s._witness.paths)
 expected=[(r[1],r[2][3]) for t in s._witness.identities for r in t if r[0]=='file'];real=c.s._read_source_file;fstat=c.s.os.fstat;reads=[];stats=[]
 def reading(path,identity):reads.append((str(path),identity[3]));return real(path,identity)
 def observing(fd):stats.append(fd);return fstat(fd)
 monkeypatch.setattr(c.s,'_read_source_file',reading);monkeypatch.setattr(c.s.os,'fstat',observing)
 f.refresh(c,s);f.refresh(c,s)
 assert reads==expected+expected and len(stats)==4*len(expected)
 assert len([p for p,size in expected if p==str(tree/'a')])>=2

def test_mutation_after_descriptor_read_rejects_and_closes_handle(tmp_path,monkeypatch):
 c=f.setup_case(tmp_path,monkeypatch);s=c.build();opening=Path.open;handles=[]
 class Reader:
  def __init__(self,h):self.h=h;self.changed=False;handles.append(h)
  def __enter__(self):return self
  def __exit__(self,*args):self.h.close()
  def fileno(self):return self.h.fileno()
  def read(self,*args):
   value=self.h.read(*args)
   if value and not self.changed:
    self.changed=True
    with opening(c.static,'r+b') as out:out.write(b'changed!')
   return value
 def patched(path,*args,**kwargs):
  h=opening(path,*args,**kwargs)
  return Reader(h) if path==c.static and args and args[0]=='rb' else h
 monkeypatch.setattr(Path,'open',patched)
 with pytest.raises(ValueError):f.refresh(c,s)
 assert handles and all(h.closed for h in handles)
