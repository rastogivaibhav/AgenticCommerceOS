import { apiJson } from './client';

export async function listDemoRoutes() {
  return apiJson('/api/v1/demo/routes');
}

export async function simulateDemoRoute(routeId, payload) {
  return apiJson(`/api/v1/demo/routes/${routeId}/simulate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
