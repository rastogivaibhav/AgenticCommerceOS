import { useEffect, useState } from 'react';
import { AlertOctagon, ChevronRight, Database, Globe, Lock, Play, Zap } from 'lucide-react';
import Editor from '@monaco-editor/react';
import { apiFetch } from '../api/client';
import { canOperate, isAnalyst } from '../lib/rbac';
import './Lists.css';

const TYPE_CLASSES = {
  read: 'bg-secondary-container text-on-secondary-container',
  write: 'bg-error-container text-on-error-container',
};

const DEMO_SKILLS = [
  {
    id: 'sk_catalog_search',
    name: 'Catalog Search',
    category: 'Integration',
    type: 'read',
    calls: '105k',
    code: 'def search_catalog(query: str):\n    return []\n',
    linterWarnings: [],
    input_schema: { type: 'object', properties: { query: { type: 'string' } }, required: ['query'] },
    output_schema: { type: 'object', properties: { status: { type: 'string' } }, required: ['status'] },
    execution_mode: 'local',
    timeout_seconds: 15,
    retries: 0,
  },
  {
    id: 'sk_process_refund',
    name: 'Process Refund',
    category: 'Finance',
    type: 'write',
    calls: '340',
    code: 'def process_refund(order_id: str, amount: float):\n    return {"status": "queued"}\n',
    linterWarnings: ['Line 7: Unhandled exception edge-case for large refunds'],
    input_schema: {
      type: 'object',
      properties: { order_id: { type: 'string' }, amount: { type: 'number' } },
      required: ['order_id', 'amount'],
    },
    output_schema: { type: 'object', properties: { status: { type: 'string' } }, required: ['status'] },
    execution_mode: 'local',
    timeout_seconds: 15,
    retries: 1,
  },
];

const DEFAULT_INPUT_SCHEMA = {
  type: 'object',
  properties: {},
  required: [],
};

const DEFAULT_OUTPUT_SCHEMA = {
  type: 'object',
  properties: { status: { type: 'string' } },
  required: ['status'],
};

export default function Skills() {
  const allowMutations = canOperate();
  const analystMode = isAnalyst();
  const [skills, setSkills] = useState(DEMO_SKILLS);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSkillId, setSelectedSkillId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAuthorModal, setShowAuthorModal] = useState(false);
  const [form, setForm] = useState({
    name: '',
    category: 'Integration',
    type: 'read',
    executionMode: 'local',
    timeoutSeconds: 15,
    retries: 0,
    inputSchema: JSON.stringify(DEFAULT_INPUT_SCHEMA, null, 2),
    outputSchema: JSON.stringify(DEFAULT_OUTPUT_SCHEMA, null, 2),
    deploymentCycle: 'Immediate',
  });
  const [testPayload, setTestPayload] = useState('{\n  "query": "wireless earbuds"\n}');
  const [testResult, setTestResult] = useState(null);
  const [isDeploying, setIsDeploying] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [apiError, setApiError] = useState(null);

  const fetchSkills = () => {
    setIsLoading(true);
    apiFetch('/api/v1/skills')
      .then((res) => res.json())
      .then((data) => {
        setSkills(data.skills || []);
        setApiError(null);
      })
      .catch((err) => {
        console.error('Failed to load skills:', err);
        setApiError(err.message);
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchSkills();
  }, []);

  const handleAuthor = async (e) => {
    e.preventDefault();
    if (!allowMutations) return;

    let parsedInputSchema = DEFAULT_INPUT_SCHEMA;
    let parsedOutputSchema = DEFAULT_OUTPUT_SCHEMA;
    try {
      parsedInputSchema = JSON.parse(form.inputSchema || '{}');
      parsedOutputSchema = JSON.parse(form.outputSchema || '{}');
    } catch (err) {
      setApiError('Input/output schema must be valid JSON.');
      return;
    }

    setIsDeploying(true);
    const newId = `sk_${form.name.toLowerCase().replace(/[^a-z0-9]/g, '_')}`;
    const newSkill = {
      id: newId,
      name: form.name,
      category: form.category,
      type: form.type,
      status: form.deploymentCycle === 'Immediate' ? 'active' : 'staged',
      calls: '0',
      code: 'def evaluate(payload: dict):\n    return {"status": "ok"}\n',
      linterWarnings: [],
      execution_mode: form.executionMode,
      timeout_seconds: Number(form.timeoutSeconds),
      retries: Number(form.retries),
      input_schema: parsedInputSchema,
      output_schema: parsedOutputSchema,
    };
    try {
      await apiFetch('/api/v1/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSkill),
      });
      setShowAuthorModal(false);
      setForm({
        name: '',
        category: 'Integration',
        type: 'read',
        executionMode: 'local',
        timeoutSeconds: 15,
        retries: 0,
        inputSchema: JSON.stringify(DEFAULT_INPUT_SCHEMA, null, 2),
        outputSchema: JSON.stringify(DEFAULT_OUTPUT_SCHEMA, null, 2),
        deploymentCycle: 'Immediate',
      });
      fetchSkills();
      setSelectedSkillId(newId);
    } catch (err) {
      console.error(err);
    } finally {
      setIsDeploying(false);
    }
  };

  const runSkillTest = async () => {
    if (!selectedSkill || !allowMutations) return;
    setIsTesting(true);
    setTestResult(null);
    try {
      const parsedPayload = JSON.parse(testPayload || '{}');
      const response = await apiFetch(`/api/v1/skills/${selectedSkill.id}/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input_payload: parsedPayload,
          tenant_id: 'default',
        }),
      });
      const data = await response.json();
      setTestResult(data);
    } catch (err) {
      setTestResult({ status: 'fail', error: err.message || 'Invalid test payload JSON.' });
    } finally {
      setIsTesting(false);
    }
  };

  const filtered = skills.filter(
    (s) =>
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.category.toLowerCase().includes(searchTerm.toLowerCase()),
  );
  const selectedSkill = skills.find((s) => s.id === selectedSkillId);

  const getTypeIcon = (category) => {
    switch (category) {
      case 'Integration':
        return <Database size={16} />;
      case 'Core':
        return <Zap size={16} />;
      case 'External':
        return <Globe size={16} />;
      default:
        return <Lock size={16} />;
    }
  };

  return (
    <div className="page-container list-view">
      {showAuthorModal && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: 720 }}>
            <h2>Create New Skill</h2>
            <p className="muted">Add an executable skill with explicit input/output contracts.</p>
            <form onSubmit={handleAuthor} className="modal-form">
              <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <label>
                  Skill Name
                  <input
                    required
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    placeholder="e.g. Check Warranty"
                  />
                </label>
                <label>
                  Category
                  <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
                    <option value="Integration">Integration</option>
                    <option value="Finance">Finance</option>
                    <option value="CRM">CRM</option>
                    <option value="Logistics">Logistics</option>
                  </select>
                </label>
                <label>
                  I/O Type
                  <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                    <option value="read">Read Only</option>
                    <option value="write">Write/Mutate</option>
                  </select>
                </label>
                <label>
                  Execution Mode
                  <select value={form.executionMode} onChange={(e) => setForm({ ...form, executionMode: e.target.value })}>
                    <option value="local">Local</option>
                    <option value="http_connector">HTTP Connector</option>
                  </select>
                </label>
                <label>
                  Timeout (seconds)
                  <input
                    type="number"
                    min="1"
                    value={form.timeoutSeconds}
                    onChange={(e) => setForm({ ...form, timeoutSeconds: e.target.value })}
                  />
                </label>
                <label>
                  Retries
                  <input
                    type="number"
                    min="0"
                    value={form.retries}
                    onChange={(e) => setForm({ ...form, retries: e.target.value })}
                  />
                </label>
              </div>

              <label>
                Input Schema (JSON)
                <textarea
                  rows={8}
                  value={form.inputSchema}
                  onChange={(e) => setForm({ ...form, inputSchema: e.target.value })}
                />
              </label>
              <label>
                Output Schema (JSON)
                <textarea
                  rows={8}
                  value={form.outputSchema}
                  onChange={(e) => setForm({ ...form, outputSchema: e.target.value })}
                />
              </label>

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
                <button type="button" className="secondary-button" onClick={() => setShowAuthorModal(false)}>
                  Cancel Drop
                </button>
                <button type="submit" className="primary-button" disabled={isDeploying || !form.name.trim()}>
                  {isDeploying ? 'Deploying...' : form.deploymentCycle === 'Immediate' ? 'Deploy Now' : 'Stage Skill'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <header className="page-header sticky-header">
        <div>
          <div className="eyebrow">ACOS Capabilities</div>
          <h1>Skill Library</h1>
          <p className="muted">Browse and manage pluggable skills, API integrations, and utilities used by agents.</p>
          {analystMode && (
            <p className="muted" style={{ marginTop: 8 }}>
              Analyst role: write actions are disabled on this screen.
            </p>
          )}
        </div>
        <div className="header-actions">
          <input
            className="search-input"
            placeholder="Search skills..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <button
            className="primary-button"
            onClick={() => setShowAuthorModal(true)}
            disabled={!allowMutations}
            title={!allowMutations ? 'Read-only for analyst role' : ''}
          >
            Create Skill
          </button>
        </div>
      </header>

      <div className={`content-split ${selectedSkill ? 'panel-open' : ''}`}>
        <div className="left-panel">
          <section className="transparent-panel">
            <div className="table-wrap glass-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Skill Name</th>
                    <th>Category</th>
                    <th>Type</th>
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
                          'No skills found.'
                        )}
                      </td>
                    </tr>
                  ) : (
                    filtered.map((skill) => (
                      <tr
                        key={skill.id}
                        className={`interactive-row ${selectedSkillId === skill.id ? 'selected-row' : ''}`}
                        onClick={() => setSelectedSkillId(skill.id)}
                      >
                        <td>
                          <div className="skill-name-cell">
                            <div className="skill-icon-wrap">{getTypeIcon(skill.category)}</div>
                            <div>
                              <div className="primary-cell">{skill.name}</div>
                              <div className="secondary-cell mono">{skill.id}</div>
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className="tag-category">{skill.category}</span>
                        </td>
                        <td>
                          <span
                            className={`${
                              TYPE_CLASSES[skill.type?.toLowerCase()] ?? 'bg-surface-variant text-on-surface-variant'
                            } text-xs px-2 py-0.5 rounded font-medium`}
                          >
                            {skill.type}
                          </span>
                        </td>
                        <td className="metric-cell">{skill.calls}</td>
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

        {selectedSkill && (
          <div className="right-panel">
            <div className="editor-widget glass-card code-widget">
              <div className="widget-header">
                <div>
                  <div className="eyebrow">Skill Editor</div>
                  <div className="skill-title-group">
                    <h2 style={{ margin: 0 }} className="text-on-surface">
                      {selectedSkill.name}
                    </h2>
                    <span
                      className={`${
                        TYPE_CLASSES[selectedSkill.type?.toLowerCase()] ?? 'bg-surface-variant text-on-surface-variant'
                      } text-xs px-2 py-0.5 rounded font-medium`}
                    >
                      {selectedSkill.type}
                    </span>
                  </div>
                </div>
                <button className="close-btn" onClick={() => setSelectedSkillId(null)}>
                  x
                </button>
              </div>

              <div className="monaco-container">
                <Editor
                  height="100%"
                  defaultLanguage="python"
                  theme="vs-dark"
                  value={selectedSkill.code}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 13,
                    fontFamily: 'Consolas, monospace',
                    scrollBeyondLastLine: false,
                    padding: { top: 16 },
                  }}
                />
              </div>

              <div className="lint-panel">
                <div className="lint-header">
                  <AlertOctagon size={14} className={selectedSkill.linterWarnings?.length ? 'text-warn' : 'text-success'} />{' '}
                  Static Analysis {selectedSkill.linterWarnings?.length ? `(${selectedSkill.linterWarnings.length} Issues)` : '(Clean)'}
                </div>
                {selectedSkill.linterWarnings?.length > 0 ? (
                  <ul className="lint-list">
                    {selectedSkill.linterWarnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="lint-success">All validations passed. Ready for deployment.</div>
                )}
              </div>

              <div className="lint-panel" style={{ marginTop: 8 }}>
                <div className="lint-header">Contract + Runtime</div>
                <div className="lint-success">
                  Mode: {selectedSkill.execution_mode || 'local'} | Timeout: {selectedSkill.timeout_seconds ?? 15}s | Retries:{' '}
                  {selectedSkill.retries ?? 0}
                </div>
              </div>

              <div className="widget-section">
                <label style={{ display: 'block', marginBottom: 8 }}>Test Input Payload (JSON)</label>
                <textarea rows={6} value={testPayload} onChange={(e) => setTestPayload(e.target.value)} />
              </div>

              {testResult && (
                <div className="lint-panel">
                  <div className="lint-header">Test Result: {testResult.status || 'unknown'}</div>
                  {testResult.error ? (
                    <div className="text-on-error-container">{testResult.error}</div>
                  ) : (
                    <div className="lint-success">
                      Connector: {testResult.connector_source || '-'} | Duration: {testResult.duration_ms ?? '-'} ms | Contract:{' '}
                      {testResult.contract_validation?.output_valid ? 'pass' : 'fail'}
                    </div>
                  )}
                </div>
              )}

              <div className="widget-footer">
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button className="primary-button compact" disabled={!allowMutations}>
                    Commit Code
                  </button>
                  <button className="secondary-button compact" disabled={!allowMutations || isTesting} onClick={runSkillTest}>
                    <Play size={14} style={{ marginRight: '6px' }} /> {isTesting ? 'Running...' : 'Test Skill'}
                  </button>
                </div>
                <button className="danger-button compact outline enable-btn" disabled={!allowMutations}>
                  Disable Skill
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
