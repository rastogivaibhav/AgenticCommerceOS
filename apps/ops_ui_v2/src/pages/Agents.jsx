import { useEffect, useMemo, useState } from 'react';
import { ChevronRight, Clock, Hash, Wrench } from 'lucide-react';
import { apiFetch } from '../api/client';
import { canOperate, isAnalyst } from '../lib/rbac';
import './Lists.css';

const STATUS_CLASSES = {
  healthy: 'bg-success-container text-on-success-container',
  degraded: 'bg-warning-container text-on-warning-container',
  disabled: 'bg-warning-container text-on-warning-container',
  error: 'bg-error-container text-on-error-container',
};

const DEMO_AGENTS = [
  {
    id: 'ag_marketing',
    name: 'Campaign Manager',
    subsystem: 'Marketing',
    status: 'healthy',
    calls: '12.4k',
    uptime: '99.9%',
    skills: ['sk_email_gen'],
    bound_skills: ['sk_email_gen'],
    grade: 'A+',
    latency: '110ms',
    runtime_provider: 'google_genai',
    model_name: 'gemini-2.0-flash',
    agent_version: 'v1',
    history: [],
  },
  {
    id: 'ag_returns',
    name: 'Returns Processor',
    subsystem: 'Reverse Logistics',
    status: 'healthy',
    calls: '1.2k',
    uptime: '99.8%',
    skills: ['sk_process_refund'],
    bound_skills: ['sk_process_refund'],
    grade: 'A',
    latency: '310ms',
    runtime_provider: 'local_fallback',
    model_name: 'gemini-2.0-flash',
    agent_version: 'v1',
    history: [],
  },
];

const DEFAULT_RUNTIME_CAPABILITIES = {
  supported_providers: ['google_genai', 'local_fallback'],
  roadmap_providers: ['crewai', 'salesforce_agentforce', 'servicenow_agent', 'openai_agent'],
  active_provider: 'local_fallback',
  default_model: 'gemini-2.0-flash',
};

const PROVIDER_LABELS = {
  google_genai: 'Google GenAI',
  local_fallback: 'Local Fallback',
  crewai: 'CrewAI',
  salesforce_agentforce: 'Salesforce Agentforce',
  servicenow_agent: 'ServiceNow Agent',
  openai_agent: 'OpenAI Agent',
};

export default function Agents() {
  const allowMutations = canOperate();
  const analystMode = isAnalyst();
  const [agents, setAgents] = useState(DEMO_AGENTS);
  const [runtimeCapabilities, setRuntimeCapabilities] = useState(DEFAULT_RUNTIME_CAPABILITIES);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAgentId, setSelectedAgentId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [skillToBind, setSkillToBind] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testMessage, setTestMessage] = useState('Check order status for ORD-1001');
  const [form, setForm] = useState({
    name: '',
    subsystem: 'Marketing',
    type: 'Task',
    runtimeProvider: DEFAULT_RUNTIME_CAPABILITIES.active_provider,
    modelName: DEFAULT_RUNTIME_CAPABILITIES.default_model,
    agentVersion: 'v1',
    deploymentCycle: 'Immediate',
  });
  const [isDeploying, setIsDeploying] = useState(false);
  const [isBindingSkill, setIsBindingSkill] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [apiError, setApiError] = useState(null);

  const supportedProviderOptions = useMemo(() => runtimeCapabilities.supported_providers || [], [runtimeCapabilities]);
  const roadmapProviderOptions = useMemo(() => runtimeCapabilities.roadmap_providers || [], [runtimeCapabilities]);

  const fetchAgents = () => {
    setIsLoading(true);
    apiFetch('/api/v1/agents')
      .then((res) => res.json())
      .then((data) => {
        setAgents(data.agents || []);
        if (data.runtime_capabilities) {
          setRuntimeCapabilities(data.runtime_capabilities);
        }
        setApiError(null);
      })
      .catch((err) => {
        console.error('Failed to load agents:', err);
        setApiError(err.message);
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleDeploy = async (e) => {
    e.preventDefault();
    if (!allowMutations) return;
    setIsDeploying(true);
    const newId = `ag_${form.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
    const newAgent = {
      id: newId,
      name: form.name,
      subsystem: form.subsystem,
      status: form.deploymentCycle === 'Immediate' ? 'healthy' : 'staged',
      calls: '0',
      uptime: '100%',
      skills: [],
      bound_skills: [],
      grade: '-',
      latency: '0ms',
      history: [],
      runtime_provider: form.runtimeProvider,
      model_name: form.modelName || runtimeCapabilities.default_model || 'gemini-2.0-flash',
      agent_version: form.agentVersion || 'v1',
      type: form.type,
    };
    try {
      await apiFetch('/api/v1/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newAgent),
      });
      setShowDeployModal(false);
      setForm({
        name: '',
        subsystem: 'Marketing',
        type: 'Task',
        runtimeProvider: runtimeCapabilities.active_provider || supportedProviderOptions[0] || 'local_fallback',
        modelName: runtimeCapabilities.default_model || 'gemini-2.0-flash',
        agentVersion: 'v1',
        deploymentCycle: 'Immediate',
      });
      fetchAgents();
      setSelectedAgentId(newId);
    } catch (err) {
      console.error(err);
    } finally {
      setIsDeploying(false);
    }
  };

  const handleBindSkill = async () => {
    if (!allowMutations || !selectedAgent || !skillToBind.trim()) return;
    setIsBindingSkill(true);
    try {
      await apiFetch(`/api/v1/agents/${selectedAgent.id}/bind-skill`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ skill_id: skillToBind.trim() }),
      });
      setSkillToBind('');
      fetchAgents();
    } catch (err) {
      console.error(err);
    } finally {
      setIsBindingSkill(false);
    }
  };

  const handleTestRun = async () => {
    if (!selectedAgent || !allowMutations) return;
    setIsTesting(true);
    setTestResult(null);
    try {
      const response = await apiFetch(`/api/v1/agents/${selectedAgent.id}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: testMessage,
          journey_type: 'post_purchase',
          tenant_id: 'default',
          customer_id: 'ops-test-customer',
        }),
      });
      const data = await response.json();
      setTestResult(data);
      fetchAgents();
    } catch (err) {
      console.error(err);
      setTestResult({ status: 'fail', error: err.message });
    } finally {
      setIsTesting(false);
    }
  };

  const toggleStatus = async () => {
    if (!selectedAgent || !allowMutations) return;
    const newStatus = selectedAgent.status === 'degraded' ? 'healthy' : 'degraded';
    try {
      await apiFetch(`/api/v1/agents/${selectedAgent.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      fetchAgents();
    } catch (err) {
      console.error(err);
    }
  };

  const filtered = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      a.subsystem.toLowerCase().includes(searchTerm.toLowerCase()),
  );
  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  return (
    <div className="page-container list-view">
      {showDeployModal && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: 680 }}>
            <h2>Create New Agent</h2>
            <p className="muted">Configure and provision an execution-ready commerce agent.</p>
            <form onSubmit={handleDeploy} className="modal-form">
              <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <label>
                  Agent Name
                  <input
                    required
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="e.g. VIP Concierge"
                  />
                </label>
                <label>
                  Subsystem Wrapper
                  <select value={form.subsystem} onChange={(e) => setForm({ ...form, subsystem: e.target.value })}>
                    <option value="Marketing">Marketing</option>
                    <option value="Customer Service">Customer Service</option>
                    <option value="Fulfillment">Fulfillment</option>
                    <option value="Reverse Logistics">Reverse Logistics</option>
                  </select>
                </label>

                <label>
                  Execution Mode
                  <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                    <option value="Task">Task Execution</option>
                    <option value="Conversational">Conversational</option>
                    <option value="Orchestrator">Orchestrator</option>
                  </select>
                </label>

                <label>
                  Runtime Provider
                  <select
                    value={form.runtimeProvider}
                    onChange={(e) => setForm({ ...form, runtimeProvider: e.target.value })}
                  >
                    <optgroup label="Supported Now">
                      {supportedProviderOptions.map((provider) => (
                        <option key={provider} value={provider}>
                          {PROVIDER_LABELS[provider] || provider}
                        </option>
                      ))}
                    </optgroup>
                    <optgroup label="Roadmap (Not Yet Supported)">
                      {roadmapProviderOptions.map((provider) => (
                        <option key={provider} value={provider} disabled>
                          {PROVIDER_LABELS[provider] || provider}
                        </option>
                      ))}
                    </optgroup>
                  </select>
                </label>

                <label>
                  Model Name
                  <input
                    value={form.modelName}
                    onChange={(e) => setForm({ ...form, modelName: e.target.value })}
                    placeholder="gemini-2.0-flash"
                  />
                </label>
                <label>
                  Agent Version
                  <input
                    value={form.agentVersion}
                    onChange={(e) => setForm({ ...form, agentVersion: e.target.value })}
                    placeholder="v1"
                  />
                </label>
              </div>

              <div className="lifecycle-options" style={{ marginTop: 24 }}>
                <h4 style={{ margin: '0 0 12px 0' }} className="text-on-surface">
                  Deployment Lifecycle Timing
                </h4>
                <div style={{ display: 'flex', gap: 24 }}>
                  <label className="radio-label" style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                    <input
                      type="radio"
                      value="Immediate"
                      checked={form.deploymentCycle === 'Immediate'}
                      onChange={(e) => setForm({ ...form, deploymentCycle: e.target.value })}
                    />
                    Deploy Immediately (Active)
                  </label>
                  <label className="radio-label" style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                    <input
                      type="radio"
                      value="Next Cycle"
                      checked={form.deploymentCycle === 'Next Cycle'}
                      onChange={(e) => setForm({ ...form, deploymentCycle: e.target.value })}
                    />
                    Stage for Next Release Cycle
                  </label>
                </div>
              </div>

              <div className="modal-actions" style={{ marginTop: 32 }}>
                <button type="button" className="secondary-button" onClick={() => setShowDeployModal(false)}>
                  Cancel Drop
                </button>
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
          {analystMode && (
            <p className="muted" style={{ marginTop: 8 }}>
              Analyst role: read-only mode is active on this screen.
            </p>
          )}
        </div>
        <div className="header-actions">
          <input
            className="search-input"
            placeholder="Search agents..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button
            className="primary-button"
            onClick={() => setShowDeployModal(true)}
            disabled={!allowMutations}
            title={!allowMutations ? 'Read-only for analyst role' : ''}
          >
            Create Agent
          </button>
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
                    Array.from({ length: 4 }).map((_, i) => (
                      <tr key={`skel-${i}`}>
                        <td colSpan="5">
                          <div className="skeleton-row" style={{ width: '100%', height: '40px' }}></div>
                        </td>
                      </tr>
                    ))
                  ) : filtered.length === 0 ? (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center', padding: '32px' }} className="muted">
                        {apiError ? (
                          <span className="text-on-error-container">
                            API unavailable - check that the Ops API is running on port 8081
                          </span>
                        ) : (
                          'No agents found.'
                        )}
                      </td>
                    </tr>
                  ) : (
                    filtered.map((agent) => (
                      <tr
                        key={agent.id}
                        className={`interactive-row ${selectedAgentId === agent.id ? 'selected-row' : ''}`}
                        onClick={() => setSelectedAgentId(agent.id)}
                      >
                        <td>
                          <div className="primary-cell">{agent.name}</div>
                          <div className="secondary-cell mono">{agent.id}</div>
                        </td>
                        <td>
                          <span className="tag-subsystem">{agent.subsystem}</span>
                        </td>
                        <td>
                          <span
                            className={`${
                              STATUS_CLASSES[agent.status?.toLowerCase()] ?? 'bg-surface-variant text-on-surface-variant'
                            } text-xs px-3 py-1 rounded-full font-medium`}
                          >
                            {agent.status}
                          </span>
                        </td>
                        <td className="metric-cell">{agent.calls}</td>
                        <td>
                          <ChevronRight size={16} className="text-muted" />
                        </td>
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
                <button className="close-btn" onClick={() => setSelectedAgentId(null)}>
                  x
                </button>
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
                  <h3 className="text-on-surface">
                    <Wrench size={16} /> Runtime
                  </h3>
                  <div className="tag-cloud">
                    <span className="skill-tag">{selectedAgent.runtime_provider || 'local_fallback'}</span>
                    <span className="skill-tag">{selectedAgent.model_name || 'gemini-2.0-flash'}</span>
                    <span className="skill-tag">{selectedAgent.agent_version || 'v1'}</span>
                  </div>
                </div>

                <div className="widget-section">
                  <h3 className="text-on-surface">
                    <Wrench size={16} /> Associated Skills
                  </h3>
                  <div className="tag-cloud">
                    {(selectedAgent.bound_skills || selectedAgent.skills || []).length > 0 ? (
                      (selectedAgent.bound_skills || selectedAgent.skills || []).map((skill) => (
                        <span key={skill} className="skill-tag">
                          {skill}
                        </span>
                      ))
                    ) : (
                      <span className="text-muted text-sm">No skills associated</span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                    <input
                      className="search-input"
                      style={{ width: '100%' }}
                      placeholder="skill id (e.g. sk_catalog_search)"
                      value={skillToBind}
                      onChange={(e) => setSkillToBind(e.target.value)}
                    />
                    <button
                      className="secondary-button compact"
                      disabled={!allowMutations || isBindingSkill || !skillToBind.trim()}
                      onClick={handleBindSkill}
                    >
                      {isBindingSkill ? 'Binding...' : 'Bind Skill'}
                    </button>
                  </div>
                </div>

                <div className="widget-section">
                  <h3 className="text-on-surface">Test Run</h3>
                  <input
                    className="search-input"
                    style={{ width: '100%' }}
                    value={testMessage}
                    onChange={(e) => setTestMessage(e.target.value)}
                    placeholder="Test prompt"
                  />
                  <button
                    className="secondary-button compact mt-3"
                    disabled={!allowMutations || isTesting}
                    onClick={handleTestRun}
                  >
                    {isTesting ? 'Running...' : 'Run Agent Test'}
                  </button>
                  {testResult && (
                    <div className="lint-panel" style={{ marginTop: 12 }}>
                      <div className="lint-header">Status: {testResult.status || 'unknown'}</div>
                      <div className="lint-success">
                        Provider: {testResult.runtime_provider || '-'} | Model: {testResult.model_name || '-'} | Duration:{' '}
                        {testResult.duration_ms ?? '-'} ms
                      </div>
                      {testResult.error && (
                        <div className="text-on-error-container text-sm" style={{ marginTop: 8 }}>
                          {testResult.error}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="widget-section" style={{ flexGrow: 1 }}>
                  <h3 className="text-on-surface">
                    <Clock size={16} /> Recent History
                  </h3>
                  <div className="history-list">
                    {selectedAgent.history?.length > 0 ? (
                      selectedAgent.history.map((run) => (
                        <div key={run.id} className="history-item">
                          <div className="h-left">
                            <Hash size={14} />
                            <span className="h-id mono">{run.id}</span>
                          </div>
                          <div className="h-right">
                            <span className={`h-outcome ${(run.outcome || '').toLowerCase()}`}>{run.outcome}</span>
                            <span className="h-time">{run.time}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-muted text-sm">No recent runs</div>
                    )}
                  </div>
                </div>
              </div>

              <div className="widget-footer">
                <button className="primary-button" disabled={!allowMutations}>
                  Save Configuration
                </button>
                <button
                  className={`danger-button outline ${selectedAgent.status === 'degraded' ? 'enable-btn' : ''}`}
                  onClick={toggleStatus}
                  disabled={!allowMutations}
                >
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
