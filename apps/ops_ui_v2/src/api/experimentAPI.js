import { apiJson } from './client';

export async function createExperiment(experiment) {
  return apiJson('/experiments', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(experiment),
  });
}

export async function runExperiment(experimentId, variant) {
  return apiJson(`/experiments/${experimentId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ variant }),
  });
}

export async function getExperimentResults(experimentId) {
  return apiJson(`/experiments/${experimentId}/results`);
}
