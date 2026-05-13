import os
import threading
import time
from contextlib import contextmanager

try:
    import psycopg2
    import psycopg2.extras
    import psycopg2.pool
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

import logging

logger = logging.getLogger(__name__)

_pool = None
_pool_lock = threading.Lock()
_pool_failed_at: float = 0.0
_POOL_RETRY_COOLDOWN = 30.0  # seconds before retrying a failed DB connection


def _get_database_url():
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://acos:acos@localhost:5432/acos"
    )


def _get_pool():
    global _pool, _pool_failed_at
    if _pool is not None:
        return _pool
    if not HAS_PSYCOPG2:
        return None
    # Don't hammer the DB — back off for _POOL_RETRY_COOLDOWN after a failure
    if _pool_failed_at and (time.monotonic() - _pool_failed_at) < _POOL_RETRY_COOLDOWN:
        return None
    with _pool_lock:
        if _pool is not None:
            return _pool
        try:
            maxconn = int(os.environ.get("DB_POOL_MAX", "10"))
            _pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=2,
                maxconn=maxconn,
                dsn=_get_database_url(),
                connect_timeout=5,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
            _pool_failed_at = 0.0
            logger.info(f"DB connection pool initialized (max={maxconn})")
        except Exception as e:
            logger.warning(f"Could not initialize DB connection pool: {e}")
            _pool = None
            _pool_failed_at = time.monotonic()
    return _pool


def is_pool_available():
    """Return True if the connection pool is initialized and ready."""
    return _get_pool() is not None


def get_connection():
    """Borrow a connection from the pool; caller must call close_connection() to return it.
    Returns None if pool is unavailable."""
    pool = _get_pool()
    if pool is None:
        return None
    try:
        return pool.getconn()
    except Exception as e:
        logger.warning(f"Could not get connection from pool: {e}")
        return None


def close_connection(conn=None):
    """Return a borrowed connection back to the pool."""
    if conn is None:
        return
    pool = _get_pool()
    if pool is not None:
        try:
            pool.putconn(conn)
        except Exception:
            pass


def check_connection() -> bool:
    """Probe DB connectivity without leaking a pooled connection."""
    conn = get_connection()
    if conn is None:
        return False
    close_connection(conn)
    return True


def ensure_schema():
    pool = _get_pool()
    if pool is None:
        logger.warning("Skipping schema init – no DB connection")
        return False
    try:
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "db", "schema.sql"
        )
        with open(schema_path) as f:
            sql = f.read()
        with transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        logger.info("Database schema ensured")
        return True
    except Exception as e:
        logger.warning(f"Schema init failed: {e}")
        return False


@contextmanager
def transaction():
    """Context manager for DB transactions using the connection pool."""
    pool = _get_pool()
    if pool is None:
        yield None
        return
    conn = None
    try:
        conn = pool.getconn()
        yield conn
        conn.commit()
    except Exception:
        if conn is not None:
            try:
                conn.rollback()
            except Exception:
                pass
        raise
    finally:
        if conn is not None:
            try:
                pool.putconn(conn)
            except Exception:
                pass


def apply_tenant_context(conn, tenant_id: str | None):
    """Attach tenant context for RLS-aware queries in pooled mode."""
    if conn is None or not tenant_id:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT set_config('app.tenant_id', %s, true)", (tenant_id,))
    except Exception as e:
        logger.warning(f"Could not apply tenant context for RLS: {e}")


@contextmanager
def tenant_transaction(tenant_id: str | None):
    """Transaction helper that applies `app.tenant_id` session context for RLS."""
    with transaction() as conn:
        apply_tenant_context(conn, tenant_id)
        yield conn
