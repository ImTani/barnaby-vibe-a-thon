"""Keep tests away from the real demo state: Barnaby's state dir (events log, registry) goes to a temp folder."""
import os
import sys
import tempfile
from pathlib import Path

os.environ["BARNABY_STATE"] = tempfile.mkdtemp(prefix="barnaby-test-")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
