import os
from contextlib import contextmanager

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

import logging

logger = logging.getLogger(__name__)

_conn = None


def _get_database_url():
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://acos:acos@localhost:5432/acos"
    )


def get_connection():
    global _conn
    if not HAS_PSYCOPG2:
        return None
    if _conn is not None:
        try:
            _conn.cursor().execute("SELECT 1")
            return _conn
        except Exception:
            _conn = None

    try:
        _conn = psycopg2.connect(
            _get_database_url(),
            connect_timeout=5,
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
        _conn.autocommit = False   # FIX-11: use explicit transactions
        logger.info("Connected to PostgreSQL")
        return _conn
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL: {e}")
        return None


def ensure_schema():
    conn = get_connection()
    if conn is None:
        logger.warning("Skipping schema init – no DB connection")
        return False
    try:
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "db", "schema.sql"
        )
        with open(schema_path) as f:
            sql = f.read()
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        logger.info("Database schema ensured")
        return True
    except Exception as e:
        conn.rollback()
        logger.warning(f"Schema init failed: {e}")
        return False


@contextmanager
def transaction():
    """Context manager for explicit DB transactions with commit/rollback (FIX-11)."""
    conn = get_connection()
    if conn is None:
        yield None
        return
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def close_connection():
    global _conn
    if _conn is not None:
        try:
            _conn.close()
        except Exception:
            pass
        _conn = None
