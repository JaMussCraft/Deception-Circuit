import os,time,pytest
from pathlib import Path
ROOT=Path(os.environ["PROBE_ROOT"])
def test_unselected_before():
 raise AssertionError("unselected before executed")
@pytest.fixture
def lifecycle():
 (ROOT/"setup").write_text("done")
 yield
 (ROOT/"teardown-started").write_text("done")
 deadline=time.monotonic()+5
 while not(ROOT/"parent-ack").exists() and time.monotonic()<deadline:time.sleep(.01)
 assert (ROOT/"parent-ack").exists()
 (ROOT/"teardown-done").write_text("done")
def test_selected_fail(lifecycle):
 assert False,"selected_failure"
def test_unselected_after():
 raise AssertionError("unselected after executed")
