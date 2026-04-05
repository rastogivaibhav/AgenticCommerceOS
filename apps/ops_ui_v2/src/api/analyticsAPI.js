import { apiFetch, apiJson } from './client';

export async function getMetrics(timeRange = '7d') {
  return apiJson(`/analytics/metrics?range=${encodeURIComponent(timeRange)}`);
}

export async function getTimeSeries(timeRange = '7d') {
  return apiJson(`/analytics/timeseries?range=${encodeURIComponent(timeRange)}`);
}

export async function getWorkflowMetrics() {
  return apiJson('/analytics/workflows');
}

export async function exportAnalytics(format = 'csv') {
  const response = await apiFetch(`/analytics/export?format=${encodeURIComponent(format)}`);
  if (!response.ok) throw new Error('Failed to export analytics');
  return response.blob();
}
