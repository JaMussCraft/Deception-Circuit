"""Suite-wide settings for tests/. The repo-root conftest.py is above pytest's rootdir
when the suite is run as `pytest tests` (no ini file), so it is not loaded then."""

import os

os.environ["DC_RUN_MANIFEST_GIT"] = "0"  # run_manifest.py: never shell out to git in tests
