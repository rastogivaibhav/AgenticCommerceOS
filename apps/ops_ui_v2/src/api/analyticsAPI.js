import { apiFetch } from './client';

async function getAnalyticsJson(path) {
  const response = await apiFetch(path);
  if (!response.ok) {
    throw new Error(`Failed analytics request (${response.status})`);
  }

  const data = await response.json();
  return {
    data,
    provenance: response.headers.get('X-ACOS-Analytics-Provenance') || 'live',
    detail: response.headers.get('X-ACOS-Analytics-Detail') || '',
  };
}

export async function getMetrics(timeRange = '7d') {
  return getAnalyticsJson(`/analytics/metrics?range=${encodeURIComponent(timeRange)}`);
}

export async function getTimeSeries(timeRange = '7d') {
  return getAnalyticsJson(`/analytics/timeseries?range=${encodeURIComponent(timeRange)}`);
}

export async function getWorkflowMetrics() {
  return getAnalyticsJson('/analytics/workflows');
}

export async function exportAnalytics(format = 'csv') {
  const response = await apiFetch(`/analytics/export?format=${encodeURIComponent(format)}`);
  if (!response.ok) throw new Error('Failed to export analytics');
  return response.blob();
}
