import { useState, useEffect } from 'react';
import { Building2, Plus, X } from 'lucide-react';
import { apiFetch, getAuthHeaders } from '../api/client';
import { canAdmin, isAnalyst } from '../lib/rbac';
import './Lists.css';

const CURRENCY_OPTIONS = ['USD', 'EUR', 'JPY', 'INR', 'AUD'];

const INITIAL_FORM = {
  id: '',
  name: '',
  currency: 'USD',
  tax_rate: 0.08,
};

export default function Tenants() {
  const allowCreate = canAdmin();
  const analystMode = isAnalyst();
  const [tenants, setTenants] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(INITIAL_FORM);
  const [isSaving, setIsSaving] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [modalError, setModalError] = useState(null);

  const fetchTenants = () => {
    setIsLoading(true);
    apiFetch('/api/v1/tenants')
      .then(res => res.json())
      .then(data => { setTenants(data.tenants || []); setApiError(null); })
      .catch(err => { console.error('Failed to load tenants:', err); setApiError(err.message); })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => { fetchTenants(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!allowCreate) {
      setModalError('Only admin role can create tenants.');
      return;
    }
    setIsSaving(true);
    setModalError(null);
    try {
      const res = await apiFetch('/api/v1/tenants', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          id: form.id,
          name: form.name,
          currency: form.currency,
          tax_rate: parseFloat(form.tax_rate),
          promo_rules: {},
          features: {},
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        setModalError(err.error || 'Failed to create tenant');
        return;
      }
      setShowModal(false);
      setForm(INITIAL_FORM);
      fetchTenants();
    } catch (err) {
      console.error(err);
      setModalError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const featureList = (features) => {
    if (!features || typeof features !== 'object') return '—';
    const enabled = Object.entries(features)
      .filter(([, v]) => v === true)
      .map(([k]) => k);
    return enabled.length ? enabled.join(', ') : 'none';
  };

  return (
    <div className="page-container list-view">
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: 520 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2>Create Tenant</h2>
                <p className="muted">Register a new store locale in the platform.</p>
              </div>
              <button
                type="button"
                onClick={() => { setShowModal(false); setModalError(null); }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--md-on-surface-variant, #888)', padding: 4 }}
                aria-label="Close"
              >
                <X size={18} />
              </button>
            </div>
            {modalError && (
              <p style={{ color: 'var(--md-sys-color-error, #b00020)', marginTop: 8, marginBottom: 0 }}>{modalError}</p>
            )}
            <form onSubmit={handleCreate} className="modal-form">
              <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <label>
                  Tenant ID
                  <input
                    required
                    value={form.id}
                    onChange={e => setForm({ ...form, id: e.target.value })}
                    placeholder="e.g. au-store"
                    pattern="^[a-zA-Z0-9_\-]+$"
                  />
                </label>
                <label>
                  Display Name
                  <input
                    required
                    value={form.name}
                    onChange={e => setForm({ ...form, name: e.target.value })}
                    placeholder="e.g. Australia Store"
                  />
                </label>
                <label>
                  Currency
                  <select value={form.currency} onChange={e => setForm({ ...form, currency: e.target.value })}>
                    {CURRENCY_OPTIONS.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </label>
                <label>
                  Tax Rate
                  <input
                    type="number"
                    required
                    min="0"
                    max="1"
                    step="0.01"
                    value={form.tax_rate}
                    onChange={e => setForm({ ...form, tax_rate: e.target.value })}
                    placeholder="e.g. 0.10"
                  />
                </label>
              </div>
              <div className="modal-actions" style={{ marginTop: 32 }}>
                <button type="button" className="secondary-button" onClick={() => { setShowModal(false); setModalError(null); }}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={isSaving}>
                  {isSaving ? 'Creating…' : 'Create Tenant'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <header className="page-header sticky-header">
        <div>
          <div className="eyebrow">ACOS Platform</div>
          <h1>Tenants</h1>
          {analystMode && (
            <p className="muted" style={{ marginTop: 8 }}>
              Analyst role: tenant management is view-only.
            </p>
          )}
          <p className="muted">Manage store locales — currency, tax, and feature flags.</p>
        </div>
        <div className="header-actions">
          <button
            className="primary-button"
            onClick={() => setShowModal(true)}
            disabled={!allowCreate}
            title={!allowCreate ? 'Admin role required' : ''}
          >
            <Plus size={16} style={{ marginRight: 6 }} />
            Create Tenant
          </button>
        </div>
      </header>

      <div className="content-split">
        <div className="left-panel" style={{ maxWidth: '100%' }}>
          <section className="transparent-panel">
            <div className="table-wrap glass-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Currency</th>
                    <th>Tax Rate</th>
                    <th>Features</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    Array.from({ length: 4 }).map((_, i) => (
                      <tr key={`skel-${i}`}>
                        <td colSpan="5"><div className="skeleton-row" style={{ width: '100%', height: 40 }} /></td>
                      </tr>
                    ))
                  ) : tenants.length === 0 ? (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center', padding: 32 }} className="muted">
                        {apiError
                          ? <span className="text-on-error-container">API unavailable — check that the Ops API is running on port 8081</span>
                          : 'No tenants found.'}
                      </td>
                    </tr>
                  ) : (
                    tenants.map(t => (
                      <tr key={t.id}>
                        <td>
                          <code style={{ fontSize: '0.82rem', background: 'rgba(255,255,255,0.06)', padding: '2px 8px', borderRadius: 6 }}>
                            {t.id}
                          </code>
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <Building2 size={14} style={{ opacity: 0.5, flexShrink: 0 }} />
                            {t.name}
                          </div>
                        </td>
                        <td>{t.currency}</td>
                        <td>{t.tax_rate != null ? `${(t.tax_rate * 100).toFixed(0)}%` : '—'}</td>
                        <td className="muted" style={{ fontSize: '0.8rem' }}>{featureList(t.features)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
