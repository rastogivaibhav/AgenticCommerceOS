function resolveShopperBase() {
  const configured = (import.meta.env.VITE_SHOPPER_API_URL || '').trim();
  if (configured) return configured.replace(/\/+$/, '');
  if (typeof window !== 'undefined' && window.location?.hostname) {
    return `${window.location.protocol}//${window.location.hostname}:8080`;
  }
  return 'http://localhost:8080';
}

const SHOPPER_API_BASE = resolveShopperBase();

export async function runShopperJourney(payload, apiKey = 'test-key-1') {
  const response = await fetch(`${SHOPPER_API_BASE}/v1/journey`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey,
    },
    body: JSON.stringify(payload),
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.error || data?.detail || `Shopper request failed (${response.status})`);
  }

  return data;
}
