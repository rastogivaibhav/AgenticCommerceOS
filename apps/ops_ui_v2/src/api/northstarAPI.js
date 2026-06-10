import { apiJson } from './client';

export async function getStudioProof() {
  return apiJson('/api/northstar/studio-proof');
}

export async function getNorthstarTools() {
  return apiJson('/api/northstar/tools');
}

export async function runNorthstarMessage(payload) {
  return apiJson('/api/northstar/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function getNorthstarReadiness() {
  return apiJson('/api/northstar/readiness');
}


export async function getNorthstarReplays() {
  return apiJson('/api/northstar/replays');
}

export async function rerunNorthstarReplay(replayId) {
  return apiJson(`/api/northstar/replays/${replayId}/rerun`, { method: 'POST' });
}


export async function getNorthstarDemoScript() {
  return apiJson('/api/northstar/demo-script');
}

export async function getNorthstarTestPlan() {
  return apiJson('/api/northstar/test-plan');
}

export async function getNorthstarRuns() {
  return apiJson('/api/northstar/runs');
}

export async function getNorthstarRun(runId) {
  return apiJson(`/api/northstar/runs/${runId}`);
}


export async function getNorthstarApiPlane() {
  return apiJson('/api/northstar/api-plane');
}

export async function runGraphQLProbe(query = '{ tools { name protocol } }') {
  return apiJson('/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
}

// ACOS v2 estate APIs
export async function getV2EstateSummary() { return apiJson('/api/v2/estate-summary'); }
export async function getV2Agents() { return apiJson('/api/v2/agents'); }
export async function getV2Agent(agentId) { return apiJson(`/api/v2/agents/${agentId}`); }
export async function getV2Capabilities() { return apiJson('/api/v2/capabilities'); }
export async function invokeV2A2A(payload) {
  return apiJson('/api/v2/a2a/invoke', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
}
export async function getV2A2ATraces() { return apiJson('/api/v2/a2a/traces'); }
export async function getV2ChannelModes() { return apiJson('/api/v2/channel-modes'); }
export async function getV2ToneProfiles() { return apiJson('/api/v2/tone-profiles'); }
export async function getV2Evaluations() { return apiJson('/api/v2/evaluations'); }
export async function getV2Guardrails() { return apiJson('/api/v2/guardrails'); }
export async function getV2Finops() { return apiJson('/api/v2/finops'); }
export async function getV2RouteToProduction() { return apiJson('/api/v2/route-to-production'); }
export async function getV2MemoryEvents() { return apiJson('/api/v2/memory/access-events'); }
export async function getV2Tools() { return apiJson('/api/v2/tools'); }
export async function getV2McpServers() { return apiJson('/api/v2/mcp/servers'); }
export async function getV2SessionMemory(sessionId = 'demo-session') { return apiJson(`/api/v2/memory/session/${sessionId}`); }
export async function getV2JourneyMemory(journeyId = 'demo-journey') { return apiJson(`/api/v2/memory/journey/${journeyId}`); }
export async function runV2Evaluation(agentId = 'mattress_recommender') {
  return apiJson('/api/v2/evaluations/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ agent_id: agentId }) });
}
export async function getV2VendorAgents() { return apiJson('/api/v2/vendor-agents'); }
