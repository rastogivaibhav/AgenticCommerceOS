function resolveApiBase() {
  const configured = (import.meta.env.VITE_API_URL || '').trim();
  if (configured) return configured.replace(/\/+$/, '');
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin;
  }
  return '';
}

const API_BASE = resolveApiBase();
const TOAST_EVENT = 'ops-api-toast';

export function getOpsToken() {
  return localStorage.getItem('ops_token') || '';
}

export function getNorthstarApiKey() {
  return localStorage.getItem('northstar_api_key') || '';
}

export function getAuthHeaders() {
  const token = getOpsToken();
  const northstarKey = getNorthstarApiKey();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(northstarKey ? { 'X-API-Key': northstarKey } : {}),
  };
}

export function buildApiUrl(path) {
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE}${normalized}`;
}

function emitApiToast(message, tone = 'error') {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(
    new CustomEvent(TOAST_EVENT, {
      detail: { message, tone },
    }),
  );
}

function toastMessageForStatus(status) {
  if (status === 401) {
    return 'Authentication failed (401). Switch/mint a role token and retry.';
  }
  if (status === 403) {
    return 'Permission denied (403). Your current role is read-only for this action.';
  }
  if (status >= 500) {
    return `Server error (${status}). Please retry in a moment.`;
  }
  return '';
}

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

export async function apiFetch(path, options = {}) {
  const {
    auth = true,
    headers = {},
    body,
    method = 'GET',
    notifyErrorToast = true,
    maxRetries = 2,
    retryDelay = 1000,
  } = options;

  let lastError;

  // DEF-027: Retry logic with exponential backoff
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      const requestHeaders = {
        ...(auth ? getAuthHeaders() : {}),
        ...headers,
      };

      const init = {
        method,
        headers: requestHeaders,
      };

      if (body !== undefined) {
        init.body = body;
      }

      const response = await fetch(buildApiUrl(path), init);

      // Only retry on network-related errors, not on 4xx/5xx responses
      if (response.ok) {
        return response;
      }

      // Don't retry on client errors (4xx)
      if (response.status >= 400 && response.status < 500) {
        if (notifyErrorToast) {
          const toastMsg = toastMessageForStatus(response.status);
          if (toastMsg) emitApiToast(toastMsg, 'error');
        }
        return response;
      }

      // Retry on server errors (5xx)
      if (response.status >= 500 && attempt < maxRetries) {
        lastError = response;
        const delay = retryDelay * Math.pow(2, attempt); // Exponential backoff
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }

      if (notifyErrorToast) {
        const toastMsg = toastMessageForStatus(response.status);
        if (toastMsg) emitApiToast(toastMsg, response.status >= 500 ? 'warning' : 'error');
      }

      return response;
    } catch (error) {
      lastError = error;

      // Retry on network errors
      if (attempt < maxRetries) {
        const delay = retryDelay * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }

      if (notifyErrorToast) {
        emitApiToast('Network error. Check API connectivity and try again.', 'warning');
      }

      throw error;
    }
  }

  // All retries exhausted
  if (lastError instanceof Response) {
    return lastError;
  }
  throw lastError;
}

export async function apiJson(path, options = {}) {
  const response = await apiFetch(path, options);
  if (!response.ok) {
    const fallback = `Request failed (${response.status})`;
    let detail = '';
    let payload = null;
    try {
      payload = await response.json();
      detail = payload?.error || payload?.detail || payload?.message || '';
    } catch {
      payload = null;
      detail = '';
    }
    throw new ApiError(detail || fallback, response.status, payload);
  }
  return response.json();
}
