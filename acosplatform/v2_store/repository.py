from __future__ import annotations
import json, os, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NOW=lambda: datetime.now(timezone.utc).isoformat()
def _json(v): return json.dumps(v if v is not None else [], separators=(",",":"))
def _loads(v, default=None):
    if v in (None, ""): return default
    if isinstance(v, (list,dict)): return v
    try: return json.loads(v)
    except Exception: return default

class V2Repository:
    def __init__(self, database_url: str | None = None, store: str | None = None):
        self.store=(store or os.getenv('ACOS_V2_STORE') or 'sqlite').lower()
        self.database_url=database_url or os.getenv('ACOS_V2_SQLITE_PATH') or 'var/acos_v2.db'
        self.ensure_schema()
    @contextmanager
    def _conn(self):
        db_path=Path(self.database_url.replace('sqlite:///', ''))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn=sqlite3.connect(db_path)
        conn.row_factory=sqlite3.Row
        try:
            yield conn; conn.commit()
        finally:
            conn.close()
    def ensure_schema(self):
        with self._conn() as conn:
            conn.executescript('''
            CREATE TABLE IF NOT EXISTS v2_agents(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', payload_json TEXT NOT NULL, status TEXT DEFAULT 'draft', created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_agent_versions(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', agent_id TEXT NOT NULL, version TEXT NOT NULL, status TEXT DEFAULT 'draft', payload_json TEXT NOT NULL, created_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_agent_cards(agent_id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', card_json TEXT NOT NULL, created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_capabilities(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', payload_json TEXT NOT NULL, created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_agent_capability_mappings(tenant_id TEXT DEFAULT 'default', agent_id TEXT NOT NULL, capability_id TEXT NOT NULL, status TEXT DEFAULT 'active', PRIMARY KEY(tenant_id,agent_id,capability_id));
            CREATE TABLE IF NOT EXISTS v2_a2a_tasks(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', trace_id TEXT, agent_id TEXT, capability_id TEXT, status TEXT, request_json TEXT, response_json TEXT, error TEXT, created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_a2a_traces(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', payload_json TEXT NOT NULL, status TEXT DEFAULT 'success', created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_tools(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', payload_json TEXT NOT NULL, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_mcp_servers(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', payload_json TEXT NOT NULL, status TEXT DEFAULT 'active', created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_memory_records(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', scope TEXT, subject_id TEXT, payload_json TEXT NOT NULL, data_classification TEXT DEFAULT 'internal', created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_memory_access_events(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', actor_id TEXT, scope TEXT, subject_id TEXT, purpose TEXT, verdict TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_evaluation_sets(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', payload_json TEXT NOT NULL, created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_evaluation_runs(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', agent_id TEXT, status TEXT, score REAL, result_json TEXT NOT NULL, created_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_approval_requests(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', agent_id TEXT, version_id TEXT, status TEXT, evidence_json TEXT NOT NULL, created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_route_to_production(tenant_id TEXT DEFAULT 'default', agent_id TEXT NOT NULL, stage TEXT NOT NULL, evidence_json TEXT NOT NULL, updated_at TEXT, PRIMARY KEY(tenant_id,agent_id));
            CREATE TABLE IF NOT EXISTS v2_policy_decisions(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', actor_id TEXT, agent_id TEXT, policy_id TEXT, verdict TEXT, evidence_json TEXT NOT NULL, created_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_cost_records(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', agent_id TEXT, run_id TEXT, cost_amount REAL, currency TEXT DEFAULT 'GBP', created_at TEXT);
            CREATE TABLE IF NOT EXISTS v2_vendor_agents(id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'default', payload_json TEXT NOT NULL, enabled INTEGER DEFAULT 1, kill_switch INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT);
            ''')
    def upsert_json(self, table: str, id_value: str, payload: dict[str, Any], tenant_id: str='default', status: str | None=None):
        now=NOW(); payload=dict(payload); payload.setdefault('tenant_id', tenant_id)
        with self._conn() as conn:
            if table in {'v2_agents','v2_tools','v2_mcp_servers','v2_a2a_traces'}:
                conn.execute(f"INSERT OR REPLACE INTO {table}(id,tenant_id,payload_json,status,created_at,updated_at) VALUES(?,?,?,?,COALESCE((SELECT created_at FROM {table} WHERE id=?),?),?)", (id_value, tenant_id, _json(payload), status or payload.get('status','active'), id_value, now, now))
            elif table in {'v2_capabilities','v2_evaluation_sets'}:
                conn.execute(f"INSERT OR REPLACE INTO {table}(id,tenant_id,payload_json,created_at,updated_at) VALUES(?,?,?,COALESCE((SELECT created_at FROM {table} WHERE id=?),?),?)", (id_value, tenant_id, _json(payload), id_value, now, now))
            elif table == 'v2_memory_records':
                conn.execute("INSERT OR REPLACE INTO v2_memory_records(id,tenant_id,scope,subject_id,payload_json,data_classification,created_at,updated_at) VALUES(?,?,?,?,?,?,COALESCE((SELECT created_at FROM v2_memory_records WHERE id=?),?),?)", (id_value, tenant_id, payload.get('scope'), payload.get('subject_id'), _json(payload), payload.get('data_classification','internal'), id_value, now, now))
            elif table == 'v2_vendor_agents':
                conn.execute("INSERT OR REPLACE INTO v2_vendor_agents(id,tenant_id,payload_json,enabled,kill_switch,created_at,updated_at) VALUES(?,?,?,?,?,COALESCE((SELECT created_at FROM v2_vendor_agents WHERE id=?),?),?)", (id_value, tenant_id, _json(payload), int(payload.get('enabled', True)), int(payload.get('kill_switch', False)), id_value, now, now))
        return payload
    def list_json(self, table: str, tenant_id: str='default') -> list[dict[str,Any]]:
        with self._conn() as conn:
            return [_loads(r[0], {}) for r in conn.execute(f"SELECT payload_json FROM {table} WHERE tenant_id in (?, 'default')", (tenant_id,)).fetchall()]
    def get_json(self, table: str, id_value: str, tenant_id: str='default') -> dict[str,Any] | None:
        with self._conn() as conn:
            row=conn.execute(f"SELECT payload_json FROM {table} WHERE id=? AND tenant_id in (?, 'default')", (id_value, tenant_id)).fetchone()
            return _loads(row[0], {}) if row else None
    def map_capability(self, agent_id: str, capability_id: str, tenant_id: str='default'):
        with self._conn() as conn:
            conn.execute("INSERT OR REPLACE INTO v2_agent_capability_mappings(tenant_id,agent_id,capability_id,status) VALUES(?,?,?,'active')", (tenant_id, agent_id, capability_id))
    def mappings(self, tenant_id: str='default'):
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM v2_agent_capability_mappings WHERE tenant_id in (?, 'default')", (tenant_id,)).fetchall()]
    def insert_task(self, task: dict[str,Any]):
        now=NOW(); task=dict(task); task.setdefault('updated_at', now)
        with self._conn() as conn:
            conn.execute("INSERT OR REPLACE INTO v2_a2a_tasks(id,tenant_id,trace_id,agent_id,capability_id,status,request_json,response_json,error,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,COALESCE((SELECT created_at FROM v2_a2a_tasks WHERE id=?),?),?)", (task['task_id'], task.get('tenant_id','default'), task.get('trace_id'), task.get('agent_id'), task.get('capability_id'), task.get('status'), _json(task.get('request',{})), _json(task.get('response',{})), task.get('error'), task['task_id'], now, task['updated_at']))
        return task
    def list_tasks(self, tenant_id='default'):
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT id as task_id, tenant_id, trace_id, agent_id, capability_id, status, request_json, response_json, error, created_at, updated_at FROM v2_a2a_tasks WHERE tenant_id in (?, 'default') ORDER BY created_at DESC", (tenant_id,)).fetchall()]
    def get_task(self, task_id, tenant_id='default'):
        with self._conn() as conn:
            r=conn.execute("SELECT id as task_id, tenant_id, trace_id, agent_id, capability_id, status, request_json, response_json, error, created_at, updated_at FROM v2_a2a_tasks WHERE id=? AND tenant_id in (?, 'default')", (task_id, tenant_id)).fetchone()
            return dict(r) if r else None
    def insert_trace(self, trace): return self.upsert_json('v2_a2a_traces', trace['trace_id'], trace, trace.get('tenant_id','default'), trace.get('status','success'))
    def list_traces(self, tenant_id='default', limit=50): return sorted(self.list_json('v2_a2a_traces', tenant_id), key=lambda x: x.get('created_at',''), reverse=True)[:limit]
    def get_trace(self, trace_id, tenant_id='default'): return self.get_json('v2_a2a_traces', trace_id, tenant_id)
    def insert_eval_run(self, run):
        run=dict(run); run.setdefault('created_at', NOW())
        with self._conn() as conn:
            conn.execute("INSERT OR REPLACE INTO v2_evaluation_runs(id,tenant_id,agent_id,status,score,result_json,created_at) VALUES(?,?,?,?,?,?,?)", (run['run_id'], run.get('tenant_id','default'), run.get('agent_id'), run.get('status'), run.get('score'), _json(run), run.get('created_at')))
        return run
    def list_eval_runs(self, tenant_id='default'):
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT id as run_id, tenant_id, agent_id, status, score, result_json, created_at FROM v2_evaluation_runs WHERE tenant_id in (?, 'default') ORDER BY created_at DESC", (tenant_id,)).fetchall()]
    def get_eval_run(self, run_id, tenant_id='default'):
        with self._conn() as conn:
            r=conn.execute("SELECT id as run_id, tenant_id, agent_id, status, score, result_json, created_at FROM v2_evaluation_runs WHERE id=? AND tenant_id in (?, 'default')", (run_id, tenant_id)).fetchone()
            return dict(r) if r else None
    def set_route_stage(self, agent_id, stage, evidence=None, tenant_id='default'):
        with self._conn() as conn:
            conn.execute("INSERT OR REPLACE INTO v2_route_to_production(tenant_id,agent_id,stage,evidence_json,updated_at) VALUES(?,?,?,?,?)", (tenant_id, agent_id, stage, _json(evidence or {}), NOW()))
    def route_rows(self, tenant_id='default'):
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("SELECT * FROM v2_route_to_production WHERE tenant_id in (?, 'default')", (tenant_id,)).fetchall()]

_REPO=None
def get_v2_repository() -> V2Repository:
    global _REPO
    if _REPO is None: _REPO=V2Repository()
    return _REPO
