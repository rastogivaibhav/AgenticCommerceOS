export function exportToCSV(data, filename = 'data.csv') {
  const csv = convertToCSV(data);
  downloadFile(csv, filename, 'text/csv');
}

export function exportToJSON(data, filename = 'data.json') {
  const json = JSON.stringify(data, null, 2);
  downloadFile(json, filename, 'application/json');
}

function convertToCSV(data) {
  if (!Array.isArray(data) || data.length === 0) return '';

  const headers = Object.keys(data[0]);
  const rows = data.map((obj) =>
    headers.map((h) => {
      const val = obj[h];
      return typeof val === 'string' && val.includes(',')
        ? `"${val}"`
        : val;
    }).join(',')
  );

  return [headers.join(','), ...rows].join('\n');
}

function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}
