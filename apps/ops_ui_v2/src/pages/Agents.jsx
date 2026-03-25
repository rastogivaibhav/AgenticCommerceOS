import { useState, useEffect } from 'react';
import { Activity, ShieldCheck, AlertTriangle, ChevronRight, Hash, Clock, Wrench } from 'lucide-react';
import './Lists.css';

const STATUS_CLASSES = {
  healthy:  'bg-success-container text-on-success-container',
  degraded: 'bg-warning-container text-on-warning-container',
  disabled: 'bg-warning-container text-on-warning-container',
  error:    'bg-error-container text-on-error-container',
};

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAgentId, setSelectedAgentId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [form, setForm] = useState({ 
    name: '', 
    subsystem: 'Marketing',
    type: 'Task',
    techStack: 'Google ADK',
    modelName: 'gemini-2.5-pro',
    apiKey: '',
    deploymentCycle: 'Immediate'
  });
  const [isDeploying, setIsDeploying] = useState(false);
  const [apiError, setApiError] = useState(null);

  const fetchAgents = () => {
    setIsLoading(true);
    fetch('http://localhost:8081/api/v1/agents')
      .then(res => res.json())
      .then(data => { setAgents(data.agents || []); setApiError(null); })
      .catch(err => { console.error('Failed to load agents:', err); setApiError(err.message); })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleDeploy = async (e) => {
    e.preventDefault();
    setIsDeploying(true);
    const newId = 'ag_' + form.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const newAgent = {
      id: newId,
      name: form.name,
      subsystem: form.subsystem,
      status: form.deploymentCycle === 'Immediate' ? 'healthy' : 'staged',
      tech_stack: form.techStack,
      type: form.type,
      calls: '0',
      uptime: '100%',
      skills: [],
      grade: '-',
      latency: '0ms',
      history: []
    };
    try {
      await fetch('http://localhost:8081/api/v1/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newAgent)
      });
      setShowDeployModal(false);
      setForm({ name: '', subsystem: 'Marketing', type: 'Task', techStack: 'Google ADK', modelName: 'gemini-2.5-pro', apiKey: '', deploymentCycle: 'Immediate' });
      fetchAgents();
      setSelectedAgentId(newId);
    } catch (err) {
      console.error(err);
    } finally {
      setIsDeploying(false);
    }
  };

  const toggleStatus = async () => {
    if (!selectedAgent) return;
    const newStatus = selectedAgent.status === 'degraded' ? 'healthy' : 'degraded';
    try {
      await fetch(`http://localhost:8081/api/v1/agents/${selectedAgent.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      fetchAgents();
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = agents.filter(a => a.name.toLowerCase().includes(searchTerm.toLowerCase()) || a.subsystem.toLowerCase().includes(searchTerm.toLowerCase()));
  const selectedAgent = agents.find(a => a.id === selectedAgentId);

  return (
    <div className="page-container list-view">
      {showDeployModal && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: 640 }}>
            <h2>Create New Agent</h2>
            <p className="muted">Configure and provision a new autonomous component into the ecosystem.</p>
            <form onSubmit={handleDeploy} className="modal-form">
              <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <label>
                  Agent Name
                  <input required value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g. VIP Concierge" />
                </label>
                <label>
                  Subsystem Wrapper
                  <select value={form.subsystem} onChange={e => setForm({...form, subsystem: e.target.value})}>
                    <option value="Marketing">Marketing</option>
                    <option value="Customer Service">Customer Service</option>
                    <option value="Fulfillment">Fulfillment</option>
                    <option value="Reverse Logistics">Reverse Logistics</option>
                  </select>
                </label>
                
                <label>
                  Execution Mode
                  <select value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
                    <option value="Task">Task Execution</option>
                    <option value="Conversational">Conversational</option>
                    <option value="Orchestrator">Orchestrator</option>
                  </select>
                </label>

                <label>
                  Tech Stack Integration
                  <select value={form.techStack} onChange={e => setForm({...form, techStack: e.target.value})}>
                    <option value="Google ADK">Google ADK</option>
                    <option value="Crew AI">Crew AI</option>
                    <option value="Salesforce Agentforce">Salesforce Agentforce</option>
                    <option value="ServiceNow Agent">ServiceNow Agent</option>
                    <option value="OpenAI Agent">OpenAI Agent</option>
                  </select>
                </label>
              </div>

              {form.techStack === 'Google ADK' && (
                <div className="dynamic-fields" style={{ marginTop: 16, padding: 16, background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
                  <h4 style={{ margin: '0 0 12px 0', color: 'var(--accent)' }}>Google ADK Configuration</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                    <label>
                      Target Foundational Model
                      <select value={form.modelName} onChange={e => setForm({...form, modelName: e.target.value})}>
                        <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                        <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                      </select>
                    </label>
                    <label>
                      Service Account Binding
                      <input type="password" value={form.apiKey} onChange={e => setForm({...form, apiKey: e.target.value})} placeholder="gcp_iam_binding" />
                    </label>
                  </div>
                </div>
              )}

              {['Salesforce Agentforce', 'ServiceNow Agent'].includes(form.techStack) && (
                <div className="dynamic-fields" style={{ marginTop: 16, padding: 16, background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
                  <h4 style={{ margin: '0 0 12px 0', color: 'var(--accent)' }}>Enterprise Integration Configuration</h4>
                  <label>
                    OAuth Tenant URL Origin
                    <input type="text" placeholder="https://mytenant.instance.com" />
                  </label>
                </div>
              )}

              <div className="lifecycle-options" style={{ marginTop: 24 }}>
                <h4 style={{ margin: '0 0 12px 0' }} className="text-on-surface">Deployment Lifecycle Timing</h4>
                <div style={{ display: 'flex', gap: 24 }}>
                  <label className="radio-label" style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                    <input type="radio" value="Immediate" checked={form.deploymentCycle === 'Immediate'} onChange={e => setForm({...form, deploymentCycle: e.target.value})} />
                    Deploy Immediately (Active)
                  </label>
                  <label className="radio-label" style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                    <input type="radio" value="Next Cycle" checked={form.deploymentCycle === 'Next Cycle'} onChange={e => setForm({...form, deploymentCycle: e.target.value})} />
                    Stage for Next Release Cycle
                  </label>
                </div>
              </div>

              <div className="modal-actions" style={{ marginTop: 32 }}>
                <button type="button" className="secondary-button" onClick={() => setShowDeployModal(false)}>Cancel Drop</button>
                <button type="submit" className="primary-button" disabled={isDeploying || !form.name.trim()}>
                  {isDeploying ? 'Deploying...' : form.deploymentCycle === 'Immediate' ? 'Deploy Now' : 'Stage Agent'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <header className="page-header sticky-header">
        <div>
          <div className="eyebrow">ACOS Ecosystem</div>
          <h1>System Agents</h1>
          <p className="muted">Monitor and manage the autonomous agents across diverse operational domains.</p>
        </div>
        <div className="header-actions">
          <input 
            className="search-input" 
            placeholder="Search agents..." 
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
          <button className="primary-button" onClick={() => setShowDeployModal(true)}>Create Agent</button>
        </div>
      </header>

      <div className={`content-split ${selectedAgent ? 'panel-open' : ''}`}>
        <div className="left-panel">
          <section className="transparent-panel">
            <div className="table-wrap glass-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th>Subsystem</th>
                    <th>Status</th>
                    <th>Vol.</th>
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
                     <tr><td colSpan="5" style={{textAlign: 'center', padding: '32px'}} className="muted">{apiError ? <span className="text-on-error-container">API unavailable — check that the Ops API is running on port 8081</span> : 'No agents found.'}</td></tr>
                  ) : (
                    filtered.map(agent => (
                      <tr 
                        key={agent.id} 
                        className={`interactive-row ${selectedAgentId === agent.id ? 'selected-row' : ''}`}
                        onClick={() => setSelectedAgentId(agent.id)}
                      >
                        <td>
                          <div className="primary-cell">{agent.name}</div>
                          <div className="secondary-cell mono">{agent.id}</div>
                        </td>
                        <td><span className="tag-subsystem">{agent.subsystem}</span></td>
                        <td>
                          <span className={`${STATUS_CLASSES[agent.status?.toLowerCase()] ?? 'bg-surface-variant text-on-surface-variant'} text-xs px-3 py-1 rounded-full font-medium`}>
                            {agent.status}
                          </span>
                        </td>
                        <td className="metric-cell">{agent.calls}</td>
                        <td><ChevronRight size={16} className="text-muted" /></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {selectedAgent && (
          <div className="right-panel">
            <div className="editor-widget glass-card">
              <div className="widget-header">
                <div>
                  <div className="eyebrow">Agent Editor</div>
                  <h2 className="text-on-surface">{selectedAgent.name}</h2>
                </div>
                <button className="close-btn" onClick={() => setSelectedAgentId(null)}>×</button>
              </div>
              
              <div className="widget-content">
                <div className="report-card">
                  <div className="rc-metric">
                    <span className="rc-label">Grade</span>
                    <span className={`rc-value grade-${selectedAgent.grade?.[0] || 'pending'}`}>{selectedAgent.grade}</span>
                  </div>
                  <div className="rc-metric">
                    <span className="rc-label">Avg Latency</span>
                    <span className="rc-value">{selectedAgent.latency}</span>
                  </div>
                  <div className="rc-metric">
                    <span className="rc-label">Uptime</span>
                    <span className="rc-value">{selectedAgent.uptime}</span>
                  </div>
                </div>

                <div className="widget-section">
                  <h3 className="text-on-surface"><Wrench size={16}/> Associated Skills</h3>
                  <div className="tag-cloud">
                    {selectedAgent.skills?.length > 0 ? selectedAgent.skills.map(skill => (
                      <span key={skill} className="skill-tag">{skill}</span>
                    )) : <span className="text-muted text-sm">No skills associated</span>}
                  </div>
                  <button className="secondary-button compact mt-3">+ Bind Skill</button>
                </div>

                <div className="widget-section" style={{ flexGrow: 1 }}>
                  <h3 className="text-on-surface"><Clock size={16}/> Recent History</h3>
                  <div className="history-list">
                    {selectedAgent.history?.length > 0 ? selectedAgent.history.map(run => (
                      <div key={run.id} className="history-item">
                        <div className="h-left">
                          <Hash size={14} />
                          <span className="h-id mono">{run.id}</span>
                        </div>
                        <div className="h-right">
                          <span className={`h-outcome ${run.outcome.toLowerCase()}`}>{run.outcome}</span>
                          <span className="h-time">{run.time}</span>
                        </div>
                      </div>
                    )) : <div className="text-muted text-sm">No recent runs</div>}
                  </div>
                </div>
              </div>
              
              <div className="widget-footer">
                <button className="primary-button">Save Configuration</button>
                <button className={`danger-button outline ${selectedAgent.status === 'degraded' ? 'enable-btn' : ''}`} onClick={toggleStatus}>
                  {selectedAgent.status === 'degraded' ? 'Enable Agent' : 'Disable Agent'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
