const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getMetrics(timeRange = '7d') {
  const response = await fetch(`${API_BASE}/analytics/metrics?range=${timeRange}`);
  if (!response.ok) throw new Error('Failed to fetch metrics');
  return response.json();
}

export async function getTimeSeries(timeRange = '7d') {
  const response = await fetch(`${API_BASE}/analytics/timeseries?range=${timeRange}`);
  if (!response.ok) throw new Error('Failed to fetch time series');
  return response.json();
}

export async function getWorkflowMetrics() {
  const response = await fetch(`${API_BASE}/analytics/workflows`);
  if (!response.ok) throw new Error('Failed to fetch workflow metrics');
  return response.json();
}

export async function exportAnalytics(format = 'csv') {
  const response = await fetch(`${API_BASE}/analytics/export?format=${format}`);
  if (!response.ok) throw new Error('Failed to export analytics');
  return response.blob();
}
