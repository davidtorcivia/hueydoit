const BASE = '';

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || JSON.stringify(err));
  }
  return res.json();
}

export const api = {
  getStatus: () => request('GET', '/api/status'),

  getLights: () => request('GET', '/api/lights'),
  addLight: (data) => request('POST', '/api/lights', data),
  removeLight: (name) => request('DELETE', `/api/lights/${encodeURIComponent(name)}`),
  testLight: (name) => request('POST', `/api/lights/${encodeURIComponent(name)}/test`),
  getBridgeLights: () => request('GET', '/api/lights/bridge'),

  getRules: () => request('GET', '/api/rules'),
  createRule: (data) => request('POST', '/api/rules', data),
  updateRule: (id, data) => request('PUT', `/api/rules/${id}`, data),
  deleteRule: (id) => request('DELETE', `/api/rules/${id}`),
  reorderRules: (rules) => request('PUT', '/api/rules/reorder', { rules }),
  testRule: (condition) => request('POST', '/api/rules/test', { condition }),

  getProviders: () => request('GET', '/api/providers'),
  updateProvider: (name, data) => request('PUT', `/api/providers/${encodeURIComponent(name)}`, data),
  refreshProvider: (name) => request('POST', `/api/providers/${encodeURIComponent(name)}/refresh`),

  sendWebhook: (name, data) => request('POST', `/api/webhooks/${encodeURIComponent(name)}`, data),

  setOverride: (target, data) => request('POST', `/api/override/${encodeURIComponent(target)}`, data),
  clearOverride: (target) => request('DELETE', `/api/override/${encodeURIComponent(target)}`),

  getHolidays: () => request('GET', '/api/holidays'),
  addHoliday: (data) => request('POST', '/api/holidays', data),
  removeHoliday: (id) => request('DELETE', `/api/holidays/${id}`),
  updateHolidayConfig: (slug, data) => request('PUT', `/api/holidays/${encodeURIComponent(slug)}/config`, data),

  pairBridge: () => request('POST', '/api/bridge/pair'),
  getBridgeStatus: () => request('GET', '/api/bridge/status'),

  getLogs: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request('GET', `/api/logs${qs ? '?' + qs : ''}`);
  },
};
