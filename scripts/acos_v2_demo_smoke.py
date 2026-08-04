#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.ops_api.main import app
from fastapi.testclient import TestClient
client=TestClient(app)
message="I’m buying a cot mattress for a newborn under £250, and I need to know if my previous nursery order can be returned."
res=client.post('/api/v2/a2a/invoke', json={'message':message,'channel':'store_partner','actor_type':'partner','channel_mode':'store_partner_assist'})
res.raise_for_status()
trace=res.json()['trace']
print('ACOS v2 demo status:', trace['status'])
print('Trace:', trace['trace_id'])
print('Agents:', ', '.join(a['agent_id'] for a in trace['agents']))
print('Capabilities:', ', '.join(trace['required_capabilities']))
print('Tools:', len(trace['tool_trace']))
print('Cost estimate:', trace['cost_estimate'])
assert trace['status']=='success'
assert {'nursery_advisor','mattress_recommender','returns_agent'} <= {a['agent_id'] for a in trace['agents']}
assert len(trace['tool_trace']) >= 3
