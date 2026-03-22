const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function createWorkflow(workflow) {
  const response = await fetch(`${API_BASE}/workflows`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflow),
  });
  if (!response.ok) throw new Error('Failed to create workflow');
  return response.json();
}

export async function getWorkflow(id) {
  const response = await fetch(`${API_BASE}/workflows/${id}`);
  if (!response.ok) throw new Error('Failed to fetch workflow');
  return response.json();
}

export async function listWorkflows() {
  const response = await fetch(`${API_BASE}/workflows`);
  if (!response.ok) throw new Error('Failed to fetch workflows');
  return response.json();
}

export async function updateWorkflow(id, updates) {
  const response = await fetch(`${API_BASE}/workflows/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!response.ok) throw new Error('Failed to update workflow');
  return response.json();
}

export async function saveWorkflowDraft(workflowId, steps, edges) {
  return updateWorkflow(workflowId, {
    status: 'draft',
    step_definitions: steps,
    edges: edges,
  });
}
