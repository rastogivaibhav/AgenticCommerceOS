import { apiJson } from './client';

export async function createWorkflow(workflow) {
  return apiJson('/workflows', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflow),
  });
}

export async function getWorkflow(id) {
  return apiJson(`/workflows/${id}`);
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
