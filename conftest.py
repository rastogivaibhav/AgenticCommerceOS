import sys
import os

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Explicitly opt test runs into local dev auth bypass. Production remains fail-closed.
os.environ.setdefault("ALLOW_INSECURE_DEV_AUTH", "1")

import acosplatform.db.connection
acosplatform.db.connection.get_connection = lambda: None
