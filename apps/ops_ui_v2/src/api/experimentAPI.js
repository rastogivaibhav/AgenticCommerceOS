const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function createExperiment(experiment) {
  const response = await fetch(`${API_BASE}/experiments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(experiment),
  });
  if (!response.ok) throw new Error('Failed to create experiment');
  return response.json();
}

export async function runExperiment(experimentId, variant) {
  const response = await fetch(`${API_BASE}/experiments/${experimentId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ variant }),
  });
  if (!response.ok) throw new Error('Failed to run experiment');
  return response.json();
}

export async function getExperimentResults(experimentId) {
  const response = await fetch(`${API_BASE}/experiments/${experimentId}/results`);
  if (!response.ok) throw new Error('Failed to fetch results');
  return response.json();
}
