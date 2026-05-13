from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from acosplatform.v2_store import get_v2_repository
NOW=lambda: datetime.now(timezone.utc).isoformat()
repo=get_v2_repository()
def _record_access(tenant_id, actor, scope, subject_id, purpose, verdict='allow'):
    ev={'id':'ma_'+uuid4().hex[:10],'tenant_id':tenant_id,'actor_id':actor,'scope':scope,'subject_id':subject_id,'purpose':purpose,'verdict':verdict,'created_at':NOW()}
    with repo._conn() as conn:
        conn.execute("INSERT OR REPLACE INTO v2_memory_access_events(id,tenant_id,actor_id,scope,subject_id,purpose,verdict,created_at) VALUES(?,?,?,?,?,?,?,?)", (ev['id'],tenant_id,actor,scope,subject_id,purpose,verdict,ev['created_at']))
    return ev
def seed_memory(tenant_id='default'):
    if not repo.list_json('v2_memory_records', tenant_id):
        repo.upsert_json('v2_memory_records','session_demo',{'id':'session_demo','scope':'session_memory','subject_id':'demo-session','summary':'Customer is considering nursery mattress and previous order return.','data_classification':'customer'},tenant_id)
        repo.upsert_json('v2_memory_records','journey_demo',{'id':'journey_demo','scope':'journey_memory','subject_id':'demo-journey','stage':'research_and_returns','constraints':{'budget':250,'category':'nursery'}},tenant_id)
def get_session_memory(session_id, tenant_id='default', actor='orchestrator'):
    seed_memory(tenant_id); _record_access(tenant_id, actor, 'session_memory', session_id, 'read session context')
    return [m for m in repo.list_json('v2_memory_records', tenant_id) if m.get('scope')=='session_memory' and m.get('subject_id') in {session_id,'demo-session'}]
def get_journey_memory(journey_id, tenant_id='default', actor='orchestrator'):
    seed_memory(tenant_id); _record_access(tenant_id, actor, 'journey_memory', journey_id, 'read journey context')
    return [m for m in repo.list_json('v2_memory_records', tenant_id) if m.get('scope')=='journey_memory' and m.get('subject_id') in {journey_id,'demo-journey'}]
def list_access_events(tenant_id='default'):
    seed_memory(tenant_id)
    with repo._conn() as conn:
        rows=[dict(r) for r in conn.execute("SELECT * FROM v2_memory_access_events WHERE tenant_id in (?, 'default') ORDER BY created_at DESC", (tenant_id,)).fetchall()]
    return rows or [_record_access(tenant_id,'orchestrator','journey_memory','demo-journey','resolve nursery mattress journey')]
