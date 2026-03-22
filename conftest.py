import sys
import os

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.dirname(__file__))

import acosplatform.db.connection
acosplatform.db.connection.get_connection = lambda: None
