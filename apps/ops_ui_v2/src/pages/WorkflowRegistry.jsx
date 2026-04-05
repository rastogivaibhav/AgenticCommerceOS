import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { GitBranch, ChevronRight, Sparkles, MessageCircle, ShoppingBag, ShieldAlert, Cpu, ExternalLink } from 'lucide-react';
import { apiFetch } from '../api/client';
import { canOperate, isAnalyst } from '../lib/rbac';
import '../App.css';
import './Lists.css';

function request(path, options = {}) {
  return apiFetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  })
}

export default function WorkflowRegistry() {
  const allowMutations = canOperate();
  const analystMode = isAnalyst();
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [wizardStep, setWizardStep] = useState(1);
  const [isCreating, setIsCreating] = useState(false);
  const [form, setForm] = useState({ name: '', template: 'discovery', description: '' });
  const [apiError, setApiError] = useState(null);

  const fetchWorkflows = async () => {
    setIsLoading(true);
    try {
      const res = await request('/workflows');
      if (res.ok) {
        const data = await res.json();
        setWorkflows(data.workflows || []);
        setApiError(null);
      } else {
        setApiError('API returned ' + res.status);
      }
    } catch(e) {
      console.error(e);
      setApiError(e.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!allowMutations) {
      return;
    }
    setIsCreating(true);
    try {
      const res = await request('/workflows', {
        method: 'POST',
        body: JSON.stringify({
          tenant_id: 'default',
          name: form.name,
          workflow_family: form.template,
          description: form.description,
          business_owner: 'acos-team',
          change_summary: 'Initial template generation',
        })
      });
      const data = await res.json();
      setShowCreateModal(false);
      setWizardStep(1);
      setForm({ name: '', template: 'discovery', description: '' });
      await fetchWorkflows();

      // Open full-screen editor for the new workflow
      if (data?.workflow?.id) {
        navigate(`/workflows/${data.workflow.id}/editor`);
      }
    } catch(e) {
      console.error(e);
    } finally {
      setIsCreating(false);
    }
  };

  const getTemplateIcon = (id) => {
    switch(id) {
      case 'purchase': return <ShoppingBag size={24} className="text-accent" />;
      case 'post_purchase': return <Cpu size={24} className="text-accent" />;
      case 'service': return <ShieldAlert size={24} className="text-accent" />;
      case 'engagement': return <MessageCircle size={24} className="text-accent" />;
      default: return <Sparkles size={24} className="text-accent" />;
    }
  };

  const templates = [
    { id: 'discovery', name: 'AI Product Discovery', desc: 'Deploy an agentic pipeline to recommend products based on natural language chat.' },
    { id: 'purchase', name: 'E-Commerce Checkout', desc: 'Secure payment routing and cart abandonment recovery flows.' },
    { id: 'post_purchase', name: 'Fulfillment Tracker', desc: 'Logistics orchestration, shipping updates, and automatic delivery confirmations.' },
    { id: 'service', name: 'L1 Service Escalation', desc: 'Handle refunds, automated returns, and triage complaints to human agents.' },
    { id: 'engagement', name: 'Loyalty Loop', desc: 'Re-engagement campaigns, dynamic discounts, and personalized check-ins.' },
    { id: 'custom', name: 'Blank Canvas', desc: 'Start from an empty graph and orchestrate nodes from scratch.' }
  ];

  const filtered = workflows.filter(w => w.name.toLowerCase().includes(searchTerm.toLowerCase()) || w.workflow_family.toLowerCase().includes(searchTerm.toLowerCase()));

  return (
    <div className="page-container list-view">
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-card bg-surface-container border border-outline-variant rounded-2xl" style={{ maxWidth: 800 }}>
            {wizardStep === 1 ? (
              <>
                <h2 style={{ fontSize: '24px', marginBottom: '8px' }}>Provision New Graph</h2>
                <p className="muted" style={{ marginBottom: '32px' }}>Select an architecture template to bootstrap your orchestration flow.</p>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '32px' }}>
                  {templates.map(tpl => (
                    <div
                      key={tpl.id}
                      onClick={() => { setForm({...form, template: tpl.id}); setWizardStep(2); }}
                      className={form.template === tpl.id
                        ? 'bg-primary-container border border-primary rounded-2xl p-4 cursor-pointer'
                        : 'bg-surface-container border border-transparent rounded-2xl p-4 cursor-pointer hover:border-outline-variant transition-colors'
                      }
                    >
                      <div style={{ background: 'rgba(139, 92, 246, 0.1)', width: '48px', height: '48px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                        {getTemplateIcon(tpl.id)}
                      </div>
                      <h3 className="text-on-surface text-[15px] mb-2">{tpl.name}</h3>
                      <p className="text-on-surface-variant text-[13px] leading-relaxed">{tpl.desc}</p>
                    </div>
                  ))}
                </div>
                
                <div className="modal-actions" style={{ justifyContent: 'flex-start' }}>
                  <button type="button" className="secondary-button" onClick={() => setShowCreateModal(false)}>Cancel</button>
                </div>
              </>
            ) : (
              <form onSubmit={handleCreate} className="modal-form">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                  <div style={{ background: 'rgba(139, 92, 246, 0.1)', padding: '8px', borderRadius: '6px' }}>
                    {getTemplateIcon(form.template)}
                  </div>
                  <div>
                    <h2 style={{ fontSize: '20px', margin: 0 }}>Configure {templates.find(t => t.id === form.template)?.name}</h2>
                    <span className="muted text-sm">Step 2 of 2</span>
                  </div>
                </div>

                <label>
                  Workflow Identifier
                  <input required value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g. VIP Triage Processor" autoFocus style={{ padding: '12px', fontSize: '15px' }} />
                </label>

                <label style={{ marginTop: '16px' }}>
                  Description (Optional)
                  <textarea rows={4} value={form.description} onChange={e => setForm({...form, description: e.target.value})} placeholder="Describe the autonomous bounds of this flow..." style={{ padding: '12px', fontSize: '14px' }} />
                </label>

                <div className="modal-actions" style={{ marginTop: 32 }}>
                  <button type="button" className="secondary-button" onClick={() => setWizardStep(1)}>Back to Templates</button>
                  <button type="submit" className="primary-button" disabled={isCreating || !form.name.trim()}>
                    {isCreating ? 'Provisioning...' : 'Create & Open Editor'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      <header className="page-header sticky-header">
        <div>
          <div className="eyebrow">ACOS Control Plane</div>
          <h1>Orchestration Workflows</h1>
          <p className="muted">Govern active graphical pipelines, templates, and execution contexts.</p>
          {analystMode && (
            <p className="muted" style={{ marginTop: 8 }}>
              Analyst role: workflow creation is disabled (read-only).
            </p>
          )}
        </div>
        <div className="header-actions">
          <input 
            className="search-input" 
            placeholder="Search workflows..." 
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
          <button
            className="primary-button"
            onClick={() => setShowCreateModal(true)}
            disabled={!allowMutations}
            title={!allowMutations ? 'Read-only for analyst role' : ''}
          >
            Create Workflow
          </button>
        </div>
      </header>

      <div className="content-split">
        <div className="left-panel" style={{ maxWidth: '100%' }}>
          <section className="transparent-panel">
            <div className="bg-surface-container rounded-2xl overflow-hidden">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="bg-surface-container-high text-on-surface-variant text-[11px] font-medium uppercase tracking-wide px-4 py-3">Workflow</th>
                    <th className="bg-surface-container-high text-on-surface-variant text-[11px] font-medium uppercase tracking-wide px-4 py-3">Template Family</th>
                    <th className="bg-surface-container-high text-on-surface-variant text-[11px] font-medium uppercase tracking-wide px-4 py-3">Status</th>
                    <th className="bg-surface-container-high text-on-surface-variant text-[11px] font-medium uppercase tracking-wide px-4 py-3">Versions</th>
                    <th className="bg-surface-container-high text-on-surface-variant text-[11px] font-medium uppercase tracking-wide px-4 py-3"></th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    Array.from({length: 4}).map((_, i) => (
                      <tr key={`skel-${i}`}>
                        <td colSpan="5"><div className="skeleton-row" style={{width: '100%', height: '40px'}}></div></td>
                      </tr>
                    ))
                  ) : filtered.length === 0 ? (
                     <tr><td colSpan="5" style={{textAlign: 'center', padding: '32px'}} className="muted">{apiError ? <span className="text-on-error-container">API unavailable — check the Ops API</span> : 'No workflows deployed.'}</td></tr>
                  ) : (
                    filtered.map(workflow => (
                      <tr
                        key={workflow.id}
                        className="interactive-row hover:bg-surface cursor-pointer transition-colors"
                        onClick={() => navigate(`/workflows/${workflow.id}/editor`)}
                      >
                        <td>
                          <div className="primary-cell">{workflow.name}</div>
                          <div className="secondary-cell mono">{workflow.id}</div>
                        </td>
                        <td><span className="tag-subsystem">{workflow.workflow_family}</span></td>
                        <td>
                          <div className="status-cell">
                            <div className={`status-dot ${workflow.status === 'active' ? 'healthy' : 'degraded'}`}></div>
                            <span style={{textTransform: 'capitalize'}}>{workflow.status}</span>
                          </div>
                        </td>
                        <td className="metric-cell">{workflow.version_count || 1}</td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#6b7280' }}>
                            <ExternalLink size={14} />
                            <span style={{ fontSize: '12px' }}>Open Editor</span>
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
