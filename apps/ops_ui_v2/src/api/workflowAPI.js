import { apiJson } from './client';

function pickEditorGraph(detail) {
  const versions = detail?.versions || [];
  const activeVersion = versions.find((version) => version.version === detail?.workflow?.active_version);
  const fallbackVersion = versions[versions.length - 1];
  const stepDefinitions = (activeVersion || fallbackVersion)?.step_definitions;

  if (Array.isArray(stepDefinitions)) {
    return stepDefinitions.find((entry) => entry && typeof entry === 'object' && ('nodes' in entry || 'edges' in entry)) || null;
  }

  if (stepDefinitions && typeof stepDefinitions === 'object') {
    return stepDefinitions;
  }

  return null;
}

export async function createWorkflow(workflow) {
  return apiJson('/workflows', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflow),
  });
}

export async function getWorkflow(id) {
  const detail = await apiJson(`/workflows/${id}`);
  if (!detail?.workflow) {
    return detail;
  }

  return {
    ...detail.workflow,
    step_definitions: pickEditorGraph(detail),
    versions: detail.versions || [],
    promotions: detail.promotions || [],
    audits: detail.audits || [],
    runs: detail.runs || [],
  };
}

export async function listWorkflows() {
  return apiJson('/workflows');
}

export async function updateWorkflow(id, updates) {
  return apiJson(`/workflows/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
}

export async function saveWorkflowDraft(workflowId, steps, edges) {
  return updateWorkflow(workflowId, {
    status: 'draft',
    step_definitions: steps,
    edges: edges,
  });
}
