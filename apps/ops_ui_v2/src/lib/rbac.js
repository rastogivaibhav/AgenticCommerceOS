function decodeBase64Url(value) {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padding = normalized.length % 4;
  const padded = normalized + (padding ? '='.repeat(4 - padding) : '');
  return atob(padded);
}

function parseJwtPayload(token) {
  if (!token || typeof token !== 'string') return {};
  const parts = token.split('.');
  if (parts.length < 2) return {};
  try {
    const json = decodeBase64Url(parts[1]);
    return JSON.parse(json);
  } catch {
    return {};
  }
}

function toNormalizedRoleSet(payload) {
  const roles = new Set();

  const role = payload?.role;
  if (typeof role === 'string' && role.trim()) {
    roles.add(role.trim().toLowerCase());
  }

  const roleClaim = payload?.roles;
  if (typeof roleClaim === 'string') {
    roleClaim
      .split(',')
      .map((r) => r.trim().toLowerCase())
      .filter(Boolean)
      .forEach((r) => roles.add(r));
  } else if (Array.isArray(roleClaim)) {
    roleClaim
      .map((r) => String(r).trim().toLowerCase())
      .filter(Boolean)
      .forEach((r) => roles.add(r));
  }

  const realmRoles = payload?.realm_access?.roles;
  if (Array.isArray(realmRoles)) {
    realmRoles
      .map((r) => String(r).trim().toLowerCase())
      .filter(Boolean)
      .forEach((r) => roles.add(r));
  }

  return roles;
}

export function getCurrentRoles() {
  const token = localStorage.getItem('ops_token') || '';
  const payload = parseJwtPayload(token);
  const roles = toNormalizedRoleSet(payload);

  // Local dev fallback keeps current behavior unless an explicit JWT is present.
  if (roles.size === 0) {
    roles.add('admin');
  }
  return roles;
}

export function hasAnyRole(...allowedRoles) {
  const current = getCurrentRoles();
  return allowedRoles.some((role) => current.has(String(role).toLowerCase()));
}

export function canOperate() {
  return hasAnyRole('admin', 'ops');
}

export function canAdmin() {
  return hasAnyRole('admin');
}

export function isAnalyst() {
  const roles = getCurrentRoles();
  return roles.has('analyst') && !roles.has('admin') && !roles.has('ops');
}
