import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, ExternalLink, GitBranch, MessageSquare, ShoppingBag } from 'lucide-react';
import { createWorkflow, listWorkflows } from '../api/workflowAPI';
import { canOperate, isAnalyst } from '../lib/rbac';
import '../App.css';
import './Lists.css';

const EMPTY_WORKFLOWS = [];

const FAMILY_OPTIONS = [
  { id: 'service', name: 'Service', desc: 'Support, returns, escalation, and customer recovery.' },
  { id: 'post_purchase', name: 'Post Purchase', desc: 'Shipment, delivery, and order visibility flows.' },
  { id: 'purchase', name: 'Purchase', desc: 'Cart, checkout, and commerce conversion orchestration.' },
  { id: 'discovery', name: 'Discovery', desc: 'Product discovery and recommendation assistance.' },
  { id: 'engagement', name: 'Engagement', desc: 'Retention, messaging, and loyalty workflows.' },
];

function ModeBadge({ mode }) {
  const live = mode === 'live';
  return (
    <span className={`status-badge ${live ? 'healthy' : 'degraded'}`} style={{ textTransform: 'none' }}>
      {live ? 'Live data' : 'Demo data'}
    </span>
  );
}

export default function WorkflowRegistry() {
  const allowMutations = canOperate();
  const analystMode = isAnalyst();
  const navigate = useNavigate();
  const [payload, setPayload] = useState({ workflows: [], mode: 'demo', environment: 'dev' });
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [form, setForm] = useState({ name: '', workflow_family: 'service', description: '' });
  const [apiError, setApiError] = useState(null);

  const fetchWorkflows = async () => {
    setIsLoading(true);
    try {
      const nextPayload = await listWorkflows();
      setPayload(nextPayload);
      setApiError(null);
    } catch (error) {
      setApiError(error.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const workflows = payload.workflows || EMPTY_WORKFLOWS;
  const recommendedDemo = workflows.find((workflow) => workflow.id === payload.recommended_demo_workflow_id)
    || workflows.find((workflow) => workflow.is_demo);

  const filtered = useMemo(
    () =>
      workflows.filter((workflow) => {
        const haystack = `${workflow.name} ${workflow.workflow_family} ${workflow.description || ''}`.toLowerCase();
        return haystack.includes(searchTerm.toLowerCase());
      }),
    [searchTerm, workflows],
  );

  const handleCreate = async (event) => {
    event.preventDefault();
    if (!allowMutations) return;
    setIsCreating(true);
    try {
      const result = await createWorkflow({
        tenant_id: 'default',
        name: form.name,
        workflow_family: form.workflow_family,
        description: form.description,
        business_owner: 'acos-team',
        change_summary: 'Initial draft',
      });
      setShowCreateModal(false);
      setForm({ name: '', workflow_family: 'service', description: '' });
      await fetchWorkflows();
      if (result?.workflow?.id) {
        navigate(`/workflows/${result.workflow.id}/editor`);
      }
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="page-container list-view">
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: 720 }}>
            <h2>Create Workflow Draft</h2>
            <p className="muted">Start from a single workflow family and open it directly in the designer.</p>
            <form onSubmit={handleCreate} className="modal-form">
              <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <label>
                  Workflow Name
                  <input
                    required
                    value={form.name}
                    onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                    placeholder="Order exception triage"
                  />
                </label>
                <label>
                  Workflow Family
                  <select
                    value={form.workflow_family}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, workflow_family: event.target.value }))
                    }
                  >
                    {FAMILY_OPTIONS.map((option) => (
                      <option key={option.id} value={option.id}>
                        {option.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <label>
                Description
                <textarea
                  rows={4}
                  value={form.description}
                  onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                  placeholder="Governed customer-support workflow using real connector steps."
                />
              </label>
              <div className="modal-actions">
                <button type="button" className="secondary-button" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={isCreating || !form.name.trim()}>
                  {isCreating ? 'Creating...' : 'Create & Open'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <header className="page-header sticky-header">
        <div>
          <div className="eyebrow">Governed Runtime Control</div>
          <h1>Workflow Operations</h1>
          <p className="muted">
            Start from one clear story: inspect the order-support demo flow, validate it, and then
            branch into the rest of the workflow inventory.
          </p>
          <div style={{ display: 'flex', gap: 12, marginTop: 12, alignItems: 'center' }}>
            <ModeBadge mode={payload.mode} />
            <span className="muted">Environment: {payload.environment}</span>
            {analystMode && <span className="muted">Analyst role: creation is disabled.</span>}
          </div>
        </div>
        <div className="header-actions">
          <input
            className="search-input"
            placeholder="Search workflows..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
          <button
            className="primary-button"
            onClick={() => setShowCreateModal(true)}
            disabled={!allowMutations}
          >
            Create Workflow
          </button>
        </div>
      </header>

      {recommendedDemo && (
        <section
          className="glass-card"
          style={{ marginBottom: 24, display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: 20 }}
        >
          <div>
            <div className="eyebrow">Recommended Demo Flow</div>
            <h2 style={{ marginTop: 6, marginBottom: 10 }}>{recommendedDemo.name}</h2>
            <p className="muted" style={{ marginBottom: 16 }}>
              WhatsApp inbound request, Shopify order lookup, Salesforce customer context, agent
              decision, and governed escalation in one path.
            </p>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
              <span className="skill-tag">
                <MessageSquare size={14} /> WhatsApp
              </span>
              <span className="skill-tag">
                <ShoppingBag size={14} /> Shopify
              </span>
              <span className="skill-tag">
                <GitBranch size={14} /> Salesforce
              </span>
            </div>
            <button
              className="primary-button"
              onClick={() => navigate(`/workflows/${recommendedDemo.id}/editor`)}
            >
              Open Demo Flow
            </button>
          </div>
          <div
            style={{
              borderRadius: 16,
              border: '1px solid var(--md-outline-variant)',
              padding: 18,
              background: 'var(--md-surface-variant)',
            }}
          >
            <div className="stat-row">
              <span className="stat-label">Family</span>
              <span className="stat-val">{recommendedDemo.workflow_family}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Active Version</span>
              <span className="stat-val">{recommendedDemo.active_version || 'Draft only'}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Last Promotion</span>
              <span className="stat-val">{recommendedDemo.last_promoted_at || 'Not promoted yet'}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Demo Status</span>
              <span className="stat-val">Guided entrypoint</span>
            </div>
          </div>
        </section>
      )}

      <div className="content-split">
        <div className="left-panel" style={{ maxWidth: '100%' }}>
          <section className="transparent-panel">
            <div className="bg-surface-container rounded-2xl overflow-hidden">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Workflow</th>
                    <th>Family</th>
                    <th>Status</th>
                    <th>Active Version</th>
                    <th>Last Promotion</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    Array.from({ length: 4 }).map((_, index) => (
                      <tr key={`workflow-skeleton-${index}`}>
                        <td colSpan="6">
                          <div className="skeleton-row" style={{ width: '100%', height: 40 }} />
                        </td>
                      </tr>
                    ))
                  ) : filtered.length === 0 ? (
                    <tr>
                      <td colSpan="6" style={{ textAlign: 'center', padding: 32 }} className="muted">
                        {apiError || 'No workflows available.'}
                      </td>
                    </tr>
                  ) : (
                    filtered.map((workflow) => (
                      <tr
                        key={workflow.id}
                        className="interactive-row"
                        onClick={() => navigate(`/workflows/${workflow.id}/editor`)}
                      >
                        <td>
                          <div className="primary-cell">{workflow.name}</div>
                          <div className="secondary-cell mono">{workflow.id}</div>
                          {workflow.is_demo && (
                            <div className="secondary-cell" style={{ color: 'var(--md-on-warning-container)' }}>
                              Recommended demo entrypoint
                            </div>
                          )}
                        </td>
                        <td>
                          <span className="tag-subsystem">{workflow.workflow_family}</span>
                        </td>
                        <td>
                          <span className={`status-badge ${workflow.status === 'active' ? 'healthy' : 'degraded'}`}>
                            {workflow.status}
                          </span>
                        </td>
                        <td className="metric-cell">{workflow.active_version || 'Draft only'}</td>
                        <td className="metric-cell">{workflow.last_promoted_at || 'Not promoted'}</td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#6b7280' }}>
                            <ExternalLink size={14} />
                            <ChevronRight size={14} />
                          </div>
                        </td>
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
