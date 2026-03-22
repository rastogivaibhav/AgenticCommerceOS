import React, { useState, useEffect } from 'react';
import { Activity, GitBranch, Play, Settings, ChevronRight, Copy, Search, Sparkles, MessageCircle, ShoppingBag, ShieldAlert, Cpu } from 'lucide-react';
import '../App.css';
import './Lists.css';

import WorkflowCanvas from '../components/WorkflowCanvas';

function request(path, options = {}) {
  const url = path.startsWith('http') ? path : `http://localhost:8000${path}`
  return fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer demo-ops-token',
      ...(options.headers || {}),
    },
  })
}

export default function WorkflowRegistry() {
  const [workflows, setWorkflows] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedWorkflowId, setSelectedWorkflowId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [wizardStep, setWizardStep] = useState(1);
  const [isCreating, setIsCreating] = useState(false);
  const [form, setForm] = useState({ name: '', template: 'discovery', description: '' });

  const fetchWorkflows = async () => {
    setIsLoading(true);
    try {
      const res = await request('/workflows');
      if (res.ok) {
        const data = await res.json();
        setWorkflows(data.workflows || []);
      }
    } catch(e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
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
      setShowCreateModal(false);
      setWizardStep(1);
      setForm({ name: '', template: 'discovery', description: '' });
      await fetchWorkflows();
      
      // Auto-Transition to visual canvas
      if (res && res.workflow && res.workflow.id) {
        setSelectedWorkflowId(res.workflow.id);
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
  const selectedWorkflow = workflows.find(w => w.id === selectedWorkflowId);

  const handleDeployArchitecture = async () => {
    if (!selectedWorkflowId || !window.serializeWorkflowGraph) return;
    try {
      const graphData = window.serializeWorkflowGraph();
      await request(`/workflows/${selectedWorkflowId}`, {
        method: 'PATCH',
        body: JSON.stringify({
          name: selectedWorkflow.name,
          step_definitions: graphData
        })
      });
      // In a real app we'd show a toast, simply re-fetching to implicitly verify
      fetchWorkflows();
    } catch(err) {
      console.error(err);
    }
  };

  return (
    <div className="page-container list-view">
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: 800 }}>
            {wizardStep === 1 ? (
              <>
                <h2 style={{ fontSize: '24px', marginBottom: '8px' }}>Provision New Graph</h2>
                <p className="muted" style={{ marginBottom: '32px' }}>Select an architecture template to bootstrap your orchestration flow.</p>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '32px' }}>
                  {templates.map(tpl => (
                    <div 
                      key={tpl.id}
                      onClick={() => { setForm({...form, template: tpl.id}); setWizardStep(2); }}
                      style={{ 
                        background: '#151821', 
                        border: '1px solid #374151', 
                        borderRadius: '12px', 
                        padding: '24px', 
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                      }}
                      onMouseOver={e => { e.currentTarget.style.borderColor = '#8b5cf6'; e.currentTarget.style.transform = 'translateY(-2px)' }}
                      onMouseOut={e => { e.currentTarget.style.borderColor = '#374151'; e.currentTarget.style.transform = 'translateY(0)' }}
                    >
                      <div style={{ background: 'rgba(139, 92, 246, 0.1)', width: '48px', height: '48px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                        {getTemplateIcon(tpl.id)}
                      </div>
                      <h3 style={{ fontSize: '15px', color: '#fff', marginBottom: '8px' }}>{tpl.name}</h3>
                      <p style={{ fontSize: '13px', color: '#9ca3af', lineHeight: 1.5 }}>{tpl.desc}</p>
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
                    {isCreating ? 'Provisioning Environment...' : 'Deploy to Canvas'}
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
        </div>
        <div className="header-actions">
          <input 
            className="search-input" 
            placeholder="Search workflows..." 
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
          <button className="primary-button" onClick={() => setShowCreateModal(true)}>Create Workflow</button>
        </div>
      </header>

      <div className={`content-split ${selectedWorkflow ? 'panel-open' : ''}`}>
        <div className="left-panel">
          <section className="transparent-panel">
            <div className="table-wrap glass-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Workflow</th>
                    <th>Template Family</th>
                    <th>Status</th>
                    <th>Versions</th>
                    <th></th>
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
                     <tr><td colSpan="5" style={{textAlign: 'center', padding: '32px'}} className="muted">No workflows deployed.</td></tr>
                  ) : (
                    filtered.map(workflow => (
                      <tr 
                        key={workflow.id} 
                        className={`interactive-row ${selectedWorkflowId === workflow.id ? 'selected-row' : ''}`}
                        onClick={() => setSelectedWorkflowId(workflow.id)}
                      >
                        <td>
                          <div className="primary-cell">{workflow.name}</div>
                          <div className="secondary-cell mono">{workflow.id}</div>
                        </td>
                        <td><span className={`tag-subsystem`}>{workflow.workflow_family}</span></td>
                        <td>
                          <div className="status-cell">
                            <div className={`status-dot ${workflow.status === 'active' ? 'healthy' : 'degraded'}`}></div>
                            <span style={{textTransform: 'capitalize'}}>
                              {workflow.status}
                            </span>
                          </div>
                        </td>
                        <td className="metric-cell">{workflow.version_count || 1}</td>
                        <td><ChevronRight size={16} className="text-muted" /></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {selectedWorkflow && (
          <div className="right-panel">
            <div className="editor-widget glass-card" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div className="widget-header" style={{ flexShrink: 0 }}>
                <div>
                  <div className="eyebrow">Visual Orchestrator</div>
                  <h2 style={{color: '#fff', display: 'flex', alignItems: 'center', gap: 8}}>
                    <GitBranch size={20} className="text-accent" />
                    {selectedWorkflow.name}
                  </h2>
                </div>
                <button className="close-btn" onClick={() => setSelectedWorkflowId(null)}>×</button>
              </div>
              
              <div className="widget-content" style={{ flexGrow: 1, padding: 0, position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <div style={{ padding: '16px 24px', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: 16, background: 'rgba(0,0,0,0.2)' }}>
                   <div style={{ flex: 1 }}>
                     <span className="text-muted text-sm" style={{ display: 'block' }}>Active Version</span>
                     <span className="mono" style={{ color: '#fff' }}>{selectedWorkflow.active_version || 'v1 (Draft)'}</span>
                   </div>
                   <div style={{ flex: 1 }}>
                     <span className="text-muted text-sm" style={{ display: 'block' }}>Environment</span>
                     <span style={{ color: '#10b981' }}>Production (Active)</span>
                   </div>
                   <div>
                     <button className="secondary-button compact"><Settings size={14} style={{ marginRight: 4 }} /> Settings</button>
                   </div>
                </div>

                <div className="canvas-container" style={{ flexGrow: 1, background: '#111318', position: 'relative' }}>
                  <WorkflowCanvas />
                </div>
              </div>
              
              <div className="widget-footer" style={{ flexShrink: 0 }}>
                <button className="primary-button" onClick={handleDeployArchitecture}><Play size={16} style={{ marginRight: 6 }}/> Deploy Architecture</button>
                <button className="secondary-button text-muted"><Copy size={16} style={{ marginRight: 6 }}/> Duplicate Pipeline</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
