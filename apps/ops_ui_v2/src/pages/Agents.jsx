import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ChevronRight,
  Clock3,
  FileCode2,
  Gauge,
  GitBranch,
  PlayCircle,
  Plus,
  ShieldCheck,
  Wrench,
} from 'lucide-react';
import { createAgent, getAgent, listAgents, testAgent } from '../api/agentsAPI';
import { getConnectorBindings } from '../api/opsAPI';
import { canOperate, isAnalyst } from '../lib/rbac';
import './Lists.css';

const STATUS_TONE = {
  healthy: 'healthy',
  degraded: 'degraded',
  disabled: 'degraded',
  sandbox: 'degraded',
};

const TABS = ['Overview', 'Code', 'Scorecard', 'Usage'];

function ModeBadge({ mode }) {
  const isLive = mode === 'live';
  return (
    <span
      className={`status-badge ${isLive ? 'healthy' : 'degraded'}`}
      style={{ textTransform: 'none' }}
    >
      {isLive ? 'Live data' : 'Demo data'}
    </span>
  );
}

function StatCard({ icon: Icon, label, value }) {
  const IconComponent = Icon;
  return (
    <div
      style={{
        border: '1px solid var(--md-outline-variant)',
        borderRadius: 16,
        padding: 16,
        background: 'var(--md-surface-variant)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          color: 'var(--md-on-surface-variant)',
          fontSize: 12,
          marginBottom: 8,
          textTransform: 'uppercase',
          letterSpacing: 0.4,
        }}
      >
        <IconComponent size={14} />
        {label}
      </div>
      <div style={{ color: 'var(--md-on-surface)', fontSize: 16, fontWeight: 600 }}>{value}</div>
    </div>
  );
}

export default function Agents() {
  const allowMutations = canOperate();
  const analystMode = isAnalyst();
  const [agents, setAgents] = useState([]);
  const [mode, setMode] = useState('demo');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAgentId, setSelectedAgentId] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [scorecard, setScorecard] = useState(null);
  const [activeTab, setActiveTab] = useState('Overview');
  const [testMessage, setTestMessage] = useState('Where is my order ORD-1001?');
  const [testResult, setTestResult] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState(null);
  const [connectorBindings, setConnectorBindings] = useState([]);
  const [createForm, setCreateForm] = useState({
    name: '',
    purpose: '',
    subsystem: 'Customer Service',
    runtime_provider: 'local_fallback',
    model_name: 'gemini-2.0-flash',
    agent_version: 'v1',
    system_prompt: '',
    connector_bindings: [],
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [apiError, setApiError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    setIsLoading(true);
    listAgents()
      .then((payload) => {
        if (!isMounted) return;
        setAgents(payload.agents || []);
        setMode(payload.mode || 'demo');
        setSelectedAgentId((current) => current || payload.agents?.[0]?.id || null);
        setApiError(null);
      })
      .catch((error) => {
        if (!isMounted) return;
        setApiError(error.message);
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    let isMounted = true;
    getConnectorBindings()
      .then((payload) => {
        if (!isMounted) return;
        setConnectorBindings(payload.bindings || []);
      })
      .catch(() => {
        if (!isMounted) return;
        setConnectorBindings([]);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedAgentId) return;
    let isMounted = true;
    setIsDetailLoading(true);
    getAgent(selectedAgentId)
      .then((payload) => {
        if (!isMounted) return;
        setSelectedAgent(payload.agent || null);
        setScorecard(payload.scorecard || null);
      })
      .catch((error) => {
        if (!isMounted) return;
        setApiError(error.message);
      })
      .finally(() => {
        if (isMounted) setIsDetailLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, [selectedAgentId]);

  const filteredAgents = useMemo(
    () =>
      agents.filter((agent) => {
        const haystack = [
          agent.name,
          agent.subsystem,
          agent.purpose,
          agent.runtime_provider,
          ...(agent.connector_bindings || []),
        ]
          .join(' ')
          .toLowerCase();
        return haystack.includes(searchTerm.toLowerCase());
      }),
    [agents, searchTerm],
  );

  const handleRunTest = async () => {
    if (!selectedAgent || !allowMutations) return;
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await testAgent(selectedAgent.id, {
        message: testMessage,
        tenant_id: 'default',
        customer_id: 'ops-test-customer',
        journey_type: 'service',
      });
      setTestResult(result);
      const payload = await getAgent(selectedAgent.id);
      setSelectedAgent(payload.agent || null);
      setScorecard(payload.scorecard || null);
    } catch (error) {
      setTestResult({ status: 'fail', error: error.message });
    } finally {
      setIsTesting(false);
    }
  };

  const handleCreateAgent = async (event) => {
    event.preventDefault();
    if (!allowMutations) return;
    const normalizedName = createForm.name.trim();
    if (!normalizedName) return;

    setIsCreating(true);
    setCreateError(null);
    const agentId = `ag_${normalizedName.toLowerCase().replace(/[^a-z0-9]+/g, '_')}`;

    try {
      await createAgent({
        id: agentId,
        name: normalizedName,
        purpose: createForm.purpose.trim(),
        subsystem: createForm.subsystem,
        runtime_provider: createForm.runtime_provider,
        model_name: createForm.model_name,
        agent_version: createForm.agent_version,
        status: 'healthy',
        calls: '0',
        uptime: '100%',
        grade: 'A+',
        latency: '0ms',
        bound_skills: [],
        skills: [],
        connector_bindings: createForm.connector_bindings,
        used_by_workflow_ids: [],
        code: {
          system_prompt: createForm.system_prompt.trim(),
          tool_bindings: [],
          runtime: {
            provider: createForm.runtime_provider,
            model: createForm.model_name,
          },
        },
        history: [],
      });
      const payload = await listAgents();
      setAgents(payload.agents || []);
      setMode(payload.mode || 'demo');
      setSelectedAgentId(agentId);
      setActiveTab('Overview');
      setShowCreateModal(false);
      setCreateForm({
        name: '',
        purpose: '',
        subsystem: 'Customer Service',
        runtime_provider: 'local_fallback',
        model_name: 'gemini-2.0-flash',
        agent_version: 'v1',
        system_prompt: '',
        connector_bindings: [],
      });
    } catch (error) {
      setCreateError(error.message);
    } finally {
      setIsCreating(false);
    }
  };

  const toggleConnectorBinding = (bindingId) => {
    setCreateForm((current) => {
      const next = new Set(current.connector_bindings || []);
      if (next.has(bindingId)) {
        next.delete(bindingId);
      } else {
        next.add(bindingId);
      }
      return { ...current, connector_bindings: Array.from(next) };
    });
  };

  return (
    <div className="page-container list-view">
      {showCreateModal && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: 620 }}>
            <h2>Create Agent</h2>
            <p className="muted">
              Register a runtime agent that can be bound into workflows and tested from the ops plane.
            </p>
            {createError && (
              <p className="text-on-error-container" style={{ marginTop: 12 }}>
                {createError}
              </p>
            )}
            <form onSubmit={handleCreateAgent} className="modal-form">
              <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <label>
                  Agent Name
                  <input
                    required
                    value={createForm.name}
                    onChange={(event) => setCreateForm((current) => ({ ...current, name: event.target.value }))}
                    placeholder="Order Exception Agent"
                  />
                </label>
                <label>
                  Purpose
                  <input
                    value={createForm.purpose}
                    onChange={(event) => setCreateForm((current) => ({ ...current, purpose: event.target.value }))}
                    placeholder="Resolve order exceptions and governed escalations."
                  />
                </label>
                <label>
                  Subsystem
                  <select
                    value={createForm.subsystem}
                    onChange={(event) =>
                      setCreateForm((current) => ({ ...current, subsystem: event.target.value }))
                    }
                  >
                    <option value="Customer Service">Customer Service</option>
                    <option value="Fulfillment">Fulfillment</option>
                    <option value="Marketing">Marketing</option>
                    <option value="Reverse Logistics">Reverse Logistics</option>
                  </select>
                </label>
                <label>
                  Runtime Provider
                  <select
                    value={createForm.runtime_provider}
                    onChange={(event) =>
                      setCreateForm((current) => ({ ...current, runtime_provider: event.target.value }))
                    }
                  >
                    <option value="local_fallback">local_fallback</option>
                    <option value="lmstudio_local">lmstudio_local</option>
                    <option value="google_genai">google_genai</option>
                  </select>
                </label>
                <label>
                  Model
                  <input
                    value={createForm.model_name}
                    onChange={(event) =>
                      setCreateForm((current) => ({ ...current, model_name: event.target.value }))
                    }
                    placeholder="gemini-2.0-flash"
                  />
                </label>
                <label>
                  Agent Version
                  <input
                    value={createForm.agent_version}
                    onChange={(event) =>
                      setCreateForm((current) => ({ ...current, agent_version: event.target.value }))
                    }
                    placeholder="v1"
                  />
                </label>
                <label style={{ gridColumn: '1 / -1' }}>
                  System Prompt
                  <textarea
                    rows="4"
                    value={createForm.system_prompt}
                    onChange={(event) =>
                      setCreateForm((current) => ({ ...current, system_prompt: event.target.value }))
                    }
                    placeholder="Use Shopify and Salesforce evidence before answering or escalating."
                  />
                </label>
                <div style={{ gridColumn: '1 / -1' }}>
                  <div style={{ marginBottom: 8, color: 'var(--md-on-surface)', fontSize: 14 }}>
                    Connector Bindings
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 10 }}>
                    {connectorBindings.map((binding) => (
                      <label
                        key={binding.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 8,
                          padding: 10,
                          border: '1px solid var(--md-outline-variant)',
                          borderRadius: 12,
                          background: 'var(--md-surface-variant)',
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={(createForm.connector_bindings || []).includes(binding.id)}
                          onChange={() => toggleConnectorBinding(binding.id)}
                        />
                        <span>
                          <strong>{binding.display_name}</strong>
                          <br />
                          <span className="secondary-cell">{binding.connector_type}</span>
                        </span>
                      </label>
                    ))}
                    {connectorBindings.length === 0 && (
                      <div className="secondary-cell">No connector bindings available.</div>
                    )}
                  </div>
                </div>
              </div>
              <div className="modal-actions" style={{ marginTop: 24 }}>
                <button type="button" className="secondary-button" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={isCreating || !createForm.name.trim()}>
                  {isCreating ? 'Creating...' : 'Create Agent'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <header className="page-header sticky-header">
        <div>
          <div className="eyebrow">Workflow Runtime Inventory</div>
          <h1>Agent Registry</h1>
          <p className="muted">
            Inspect the agents behind live workflows, review executable configuration, and verify
            scorecards before promotion.
          </p>
          <div style={{ display: 'flex', gap: 12, marginTop: 12, alignItems: 'center' }}>
            <ModeBadge mode={mode} />
            {analystMode && <span className="muted">Analyst role: verification is read-only.</span>}
          </div>
        </div>
        <div className="header-actions">
          <input
            className="search-input"
            placeholder="Search agents, runtimes, connectors..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
          />
          <button className="primary-button" disabled={!allowMutations} onClick={() => setShowCreateModal(true)}>
            <Plus size={16} style={{ marginRight: 6 }} />
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
                    <th>Runtime</th>
                    <th>Connectors</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    Array.from({ length: 4 }).map((_, index) => (
                      <tr key={`agent-skeleton-${index}`}>
                        <td colSpan="5">
                          <div className="skeleton-row" style={{ width: '100%', height: 40 }} />
                        </td>
                      </tr>
                    ))
                  ) : filteredAgents.length === 0 ? (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center', padding: 32 }} className="muted">
                        {apiError || 'No agents found.'}
                      </td>
                    </tr>
                  ) : (
                    filteredAgents.map((agent) => (
                      <tr
                        key={agent.id}
                        className={`interactive-row ${selectedAgentId === agent.id ? 'selected-row' : ''}`}
                        onClick={() => {
                          setSelectedAgentId(agent.id);
                          setActiveTab('Overview');
                        }}
                      >
                        <td>
                          <div className="primary-cell">{agent.name}</div>
                          <div className="secondary-cell">{agent.purpose}</div>
                          <div className="secondary-cell mono">{agent.id}</div>
                        </td>
                        <td>
                          <div className="primary-cell" style={{ fontSize: 14 }}>
                            {agent.runtime_provider}
                          </div>
                          <div className="secondary-cell">{agent.model_name}</div>
                        </td>
                        <td className="metric-cell">{(agent.connector_bindings || []).join(', ') || 'None'}</td>
                        <td>
                          <span className={`status-badge ${STATUS_TONE[agent.status] || 'degraded'}`}>
                            {agent.status}
                          </span>
                        </td>
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
                  <div className="eyebrow">Agent Detail</div>
                  <h2 className="text-on-surface">{selectedAgent.name}</h2>
                  <p className="muted" style={{ marginTop: 6 }}>{selectedAgent.purpose}</p>
                </div>
                <button className="close-btn" onClick={() => setSelectedAgentId(null)}>
                  x
                </button>
              </div>

              <div
                style={{
                  display: 'flex',
                  gap: 8,
                  borderBottom: '1px solid var(--md-outline-variant)',
                  paddingBottom: 12,
                  marginBottom: 16,
                  flexWrap: 'wrap',
                }}
              >
                {TABS.map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    className={activeTab === tab ? 'primary-button compact' : 'secondary-button compact'}
                    onClick={() => setActiveTab(tab)}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              <div className="widget-content" style={{ gap: 20 }}>
                {isDetailLoading ? (
                  <div className="muted">Loading agent detail...</div>
                ) : (
                  <>
                    {activeTab === 'Overview' && (
                      <>
                        <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
                          <StatCard icon={Wrench} label="Runtime" value={`${selectedAgent.runtime_provider} / ${selectedAgent.model_name}`} />
                          <StatCard icon={Clock3} label="Last Test" value={selectedAgent.last_test_at || 'No evidence'} />
                          <StatCard icon={GitBranch} label="Version" value={selectedAgent.agent_version || 'v1'} />
                          <StatCard icon={ShieldCheck} label="Provenance" value={selectedAgent.provenance_mode || mode} />
                        </div>

                        <div className="widget-section">
                          <h3 className="text-on-surface">Connector Bindings</h3>
                          <div className="tag-cloud">
                            {(selectedAgent.connector_bindings || []).map((binding) => (
                              <span key={binding} className="skill-tag">{binding}</span>
                            ))}
                          </div>
                        </div>

                        <div className="widget-section">
                          <h3 className="text-on-surface">Bound Tools</h3>
                          <div className="tag-cloud">
                            {(selectedAgent.bound_skills || []).map((skill) => (
                              <span key={skill} className="skill-tag">{skill}</span>
                            ))}
                          </div>
                        </div>
                      </>
                    )}

                    {activeTab === 'Code' && (
                      <div className="widget-section" style={{ marginTop: 0 }}>
                        <h3 className="text-on-surface">
                          <FileCode2 size={16} /> Executable Definition
                        </h3>
                        <pre
                          style={{
                            margin: 0,
                            padding: 16,
                            borderRadius: 12,
                            overflowX: 'auto',
                            background: '#111827',
                            color: '#d1d5db',
                            fontSize: 12,
                            lineHeight: 1.6,
                            border: '1px solid rgba(255,255,255,0.08)',
                          }}
                        >
                          {JSON.stringify(selectedAgent.code || {}, null, 2)}
                        </pre>
                      </div>
                    )}

                    {activeTab === 'Scorecard' && (
                      <>
                        <div style={{ display: 'grid', gap: 12, gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
                          <StatCard
                            icon={ShieldCheck}
                            label="Connector Health"
                            value={scorecard?.connector_health_status || 'unknown'}
                          />
                          <StatCard
                            icon={Activity}
                            label="Contract Validation"
                            value={scorecard?.contract_validation_status || 'unknown'}
                          />
                          <StatCard
                            icon={Gauge}
                            label="Failure Rate"
                            value={
                              scorecard?.recent_run_failure_rate === null || scorecard?.recent_run_failure_rate === undefined
                                ? 'No data'
                                : `${Math.round(scorecard.recent_run_failure_rate * 100)}%`
                            }
                          />
                          <StatCard
                            icon={Clock3}
                            label="Last Success"
                            value={scorecard?.last_successful_run_at || 'No data'}
                          />
                        </div>

                        <div className="widget-section">
                          <h3 className="text-on-surface">Verification</h3>
                          <input
                            className="search-input"
                            style={{ width: '100%' }}
                            value={testMessage}
                            onChange={(event) => setTestMessage(event.target.value)}
                          />
                          <button
                            className="secondary-button compact mt-3"
                            disabled={!allowMutations || isTesting}
                            onClick={handleRunTest}
                          >
                            <PlayCircle size={14} />
                            {isTesting ? 'Running test...' : 'Run agent verification'}
                          </button>
                          {testResult && (
                            <div className="lint-panel" style={{ marginTop: 12 }}>
                              <div className="lint-header">Status: {testResult.status}</div>
                              <div className="lint-success">
                                Provider: {testResult.runtime_provider || '-'} | Model:{' '}
                                {testResult.model_name || '-'} | Duration: {testResult.duration_ms ?? '-'} ms
                              </div>
                              {(testResult.system_tools_used || []).length > 0 && (
                                <div style={{ marginTop: 10, display: 'grid', gap: 8 }}>
                                  {(testResult.system_tools_used || []).map((step, index) => (
                                    <div key={`${step.system}-${step.tool}-${index}`} className="secondary-cell">
                                      {step.system} / {step.tool} | {step.mode} | {step.status}
                                      {step.note ? ` | ${step.note}` : ''}
                                    </div>
                                  ))}
                                </div>
                              )}
                              {testResult.error && (
                                <div className="text-on-error-container text-sm" style={{ marginTop: 8 }}>
                                  {testResult.error}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </>
                    )}

                    {activeTab === 'Usage' && (
                      <div className="widget-section">
                        <h3 className="text-on-surface">Used by Workflows</h3>
                        <div className="history-list">
                          {(selectedAgent.used_by_workflow_ids || []).map((workflowId) => (
                            <div key={workflowId} className="history-item">
                              <div className="h-left">
                                <GitBranch size={14} />
                                <span className="h-id mono">{workflowId}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
