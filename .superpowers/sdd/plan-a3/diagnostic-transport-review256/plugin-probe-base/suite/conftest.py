import json,os
from pathlib import Path
def pytest_sessionstart(session):
 Path(os.environ["PROBE_ROOT"],"preflight").write_text("done")
def pytest_collection_finish(session):
 assert len(session.items)==3
def pytest_sessionfinish(session,exitstatus):
 Path(os.environ["PROBE_ROOT"],"session-final.json").write_text(json.dumps([item.nodeid for item in session.items]))
