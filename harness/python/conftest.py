import sys
import os

# Ensure both repo root and harness/python are importable
HARNESS_PYTHON = os.path.dirname(__file__)
REPO_ROOT = os.path.dirname(os.path.dirname(HARNESS_PYTHON))
sys.path.insert(0, REPO_ROOT)
sys.path.insert(0, HARNESS_PYTHON)

# Explicitly opt test runs into local dev auth bypass. Production remains fail-closed.
os.environ.setdefault("ALLOW_INSECURE_DEV_AUTH", "1")

import acosplatform.db.connection
acosplatform.db.connection.get_connection = lambda: None
