import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  FlaskConical,
  GitBranch,
  Loader2,
  PlayCircle,
  Save,
  ShieldCheck,
} from 'lucide-react';
import WorkflowCanvas from '../components/WorkflowCanvas';
import { executeWorkflow, getWorkflow, testWorkflowRun, updateWorkflow } from '../api/workflowAPI';
import { canOperate, isAnalyst } from '../lib/rbac';

function StatusPill({ label, tone = 'default' }) {
  const tones = {
    default: {
      background: 'var(--md-surface-variant)',
      color: 'var(--md-on-surface-variant)',
      border: '1px solid var(--md-outline-variant)',
    },
    success: {
      background: '#dcfce7',
      color: '#166534',
      border: '1px solid #bbf7d0',
    },
    warning: {
      background: 'var(--md-warning-container)',
      color: 'var(--md-on-warning-container)',
      border: '1px solid rgba(188, 110, 0, 0.18)',
    },
  };

  return (
    <span
      style={{
        ...tones[tone],
        fontSize: 11,
        padding: '3px 8px',
        borderRadius: 999,
      }}
    >
      {label}
    </span>
  );
}

export default function WorkflowEditor() {
  const allowSave = canOperate();
  const analystMode = isAnalyst();
  const { id } = useParams();
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState(null);
  const [draftGraph, setDraftGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [executionForm, setExecutionForm] = useState({
    message: 'Where is my order ORD-1001?',
    customer_id: 'cust_1001',
    tenant_id: 'default',
    order_id: 'ORD-1001',
    environment: 'dev',
  });

  useEffect(() => {
    setLoading(true);
    getWorkflow(id)
      .then((payload) => {
        setWorkflow(payload);
        setDraftGraph(payload?.step_definitions ?? null);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const activeVersion = useMemo(() => {
    const versions = workflow?.versions || [];
    return workflow?.active_version || versions[versions.length - 1]?.version || 'draft';
  }, [workflow]);

  const handleSave = useCallback(async () => {
    if (!allowSave || !draftGraph) return;
    setSaving(true);
    setSaveMsg(null);
    try {
      await updateWorkflow(id, { step_definitions: draftGraph });
      setSaveMsg('Saved');
      setTimeout(() => setSaveMsg(null), 2500);
    } catch (error) {
      console.error(error);
      setSaveMsg('Save failed');
    } finally {
      setSaving(false);
    }
  }, [allowSave, draftGraph, id]);

  const handleTestRun = useCallback(async () => {
    if (!allowSave) return;
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testWorkflowRun(id, {
        tenant_id: 'default',
        environment: 'dev',
        message: 'Where is my order ORD-1001?',
      });
      setTestResult(result);
    } catch (error) {
      console.error(error);
      setTestResult({ status: 'fail', error: error.message });
    } finally {
      setTesting(false);
    }
  }, [allowSave, id]);

  const handleExecuteJourney = useCallback(async () => {
    setExecuting(true);
    setExecutionResult(null);
    try {
      const result = await executeWorkflow(id, {
        message: executionForm.message,
        customer_id: executionForm.customer_id,
        tenant_id: executionForm.tenant_id,
        order_id: executionForm.order_id || undefined,
        environment: executionForm.environment || workflow?.environment || 'dev',
      });
      setExecutionResult(result);
    } catch (error) {
      setExecutionResult({ error: error.message });
    } finally {
      setExecuting(false);
    }
  }, [executionForm, id, workflow?.environment]);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        background: 'linear-gradient(180deg, rgba(250, 252, 255, 0.95), rgba(244, 247, 251, 0.98))',
        color: 'var(--md-on-surface)',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          padding: '12px 20px',
          borderBottom: '1px solid var(--md-outline-variant)',
          background: 'rgba(255,255,255,0.86)',
          backdropFilter: 'blur(16px)',
          flexShrink: 0,
        }}
      >
        <button
          onClick={() => navigate('/workflows')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'var(--md-surface-container)',
            border: '1px solid var(--md-outline-variant)',
            color: 'var(--md-on-surface-variant)',
            cursor: 'pointer',
            fontSize: 13,
            padding: '8px 12px',
            borderRadius: 999,
          }}
        >
          <ArrowLeft size={15} /> Back
        </button>

        <div style={{ width: 1, height: 24, background: 'var(--md-outline-variant)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1 }}>
          <div style={{ background: 'var(--md-primary-container)', padding: 8, borderRadius: 10 }}>
            <GitBranch size={16} color="var(--md-on-primary-container)" />
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--md-on-surface)' }}>
              {workflow?.name || 'Workflow Designer'}
            </div>
            <div
              style={{
                fontSize: 11,
                color: 'var(--md-on-surface-variant)',
                fontFamily: 'IBM Plex Mono, monospace',
              }}
            >
              {id}
            </div>
          </div>
          <div style={{ marginLeft: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <StatusPill label={workflow?.status || 'draft'} tone={workflow?.status === 'active' ? 'success' : 'warning'} />
            <StatusPill label={`Version ${activeVersion}`} />
            <StatusPill
              label={workflow?.provenance_mode || workflow?.mode || 'demo'}
              tone={(workflow?.mode || workflow?.provenance_mode) === 'live' ? 'success' : 'warning'}
            />
            {analystMode && <StatusPill label="Read-only" tone="warning" />}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {saveMsg && (
            <span
              style={{
                fontSize: 12,
                color: saveMsg === 'Saved' ? '#166534' : 'var(--md-on-error-container)',
                padding: '4px 10px',
                borderRadius: 999,
                background: saveMsg === 'Saved' ? '#dcfce7' : 'var(--md-error-container)',
              }}
            >
              {saveMsg}
            </span>
          )}
          <button
            onClick={handleTestRun}
            disabled={testing || !allowSave}
            className="secondary-button"
            style={{ cursor: testing || !allowSave ? 'not-allowed' : 'pointer' }}
          >
            {testing ? <Loader2 size={14} className="animate-spin" /> : <FlaskConical size={14} />}
            Test Flow
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !allowSave || !draftGraph}
            className="primary-button"
            style={{ cursor: saving || !allowSave ? 'not-allowed' : 'pointer' }}
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            Save Workflow
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', minHeight: 0, flex: 1 }}>
        <div style={{ minWidth: 0, overflow: 'hidden', position: 'relative' }}>
          {loading ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                color: 'var(--md-on-surface-variant)',
                gap: 10,
              }}
            >
              <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
              <span style={{ fontSize: 13 }}>Loading workflow...</span>
            </div>
          ) : (
            <WorkflowCanvas
              key={id}
              initialGraph={workflow?.step_definitions ?? null}
              onGraphChange={setDraftGraph}
            />
          )}
        </div>

        <aside
          style={{
            borderLeft: '1px solid var(--md-outline-variant)',
            background: 'rgba(255,255,255,0.78)',
            padding: 20,
            overflowY: 'auto',
          }}
        >
          <div className="eyebrow">Release Context</div>
          <h2 style={{ marginTop: 6, marginBottom: 12, fontSize: 18 }}>Current Evidence</h2>

          <div
            style={{
              border: '1px solid var(--md-outline-variant)',
              borderRadius: 18,
              padding: 16,
              background: 'color-mix(in srgb, var(--md-surface-container) 90%, white)',
              marginBottom: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <ShieldCheck size={16} color="#166534" />
              <strong style={{ fontSize: 13 }}>Workflow Summary</strong>
            </div>
            <div style={{ color: 'var(--md-on-surface-variant)', fontSize: 13, lineHeight: 1.6 }}>
              <div>Family: {workflow?.workflow_family || 'Unknown'}</div>
              <div>Active version: {activeVersion}</div>
              <div>Runs loaded: {workflow?.runs?.length || 0}</div>
              <div>Promotions logged: {workflow?.promotions?.length || 0}</div>
            </div>
          </div>

          <div
            style={{
              border: '1px solid var(--md-outline-variant)',
              borderRadius: 18,
              padding: 16,
              background: 'color-mix(in srgb, var(--md-surface-container) 90%, white)',
              marginBottom: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <PlayCircle size={16} color="var(--md-primary)" />
              <strong style={{ fontSize: 13 }}>Core Data Plane Run</strong>
            </div>
            <div style={{ display: 'grid', gap: 10 }}>
              <input
                className="search-input"
                style={{ width: '100%' }}
                value={executionForm.message}
                onChange={(event) =>
                  setExecutionForm((current) => ({ ...current, message: event.target.value }))
                }
                placeholder="Customer message"
              />
              <input
                className="search-input"
                style={{ width: '100%' }}
                value={executionForm.order_id}
                onChange={(event) =>
                  setExecutionForm((current) => ({ ...current, order_id: event.target.value }))
                }
                placeholder="Order ID"
              />
              <input
                className="search-input"
                style={{ width: '100%' }}
                value={executionForm.customer_id}
                onChange={(event) =>
                  setExecutionForm((current) => ({ ...current, customer_id: event.target.value }))
                }
                placeholder="Customer ID"
              />
              <input
                className="search-input"
                style={{ width: '100%' }}
                value={executionForm.environment}
                onChange={(event) =>
                  setExecutionForm((current) => ({ ...current, environment: event.target.value }))
                }
                placeholder="Environment"
              />
              <button
                className="primary-button"
                style={{ justifyContent: 'center' }}
                disabled={executing || !allowSave}
                onClick={handleExecuteJourney}
              >
                {executing ? 'Executing...' : 'Run Core Data Plane'}
              </button>
            </div>
            {executionResult && (
              <div style={{ marginTop: 14, color: 'var(--md-on-surface)', fontSize: 13, lineHeight: 1.6 }}>
                {executionResult.error ? (
                  <div style={{ color: 'var(--md-on-error-container)' }}>{executionResult.error}</div>
                ) : (
                  <>
                    <div>Run ID: {executionResult.run_id}</div>
                    <div>Journey: {executionResult.journey}</div>
                    <div>Execution mode: {executionResult.execution_mode || 'demo'}</div>
                    <div>Requested workflow: {executionResult.requested_workflow_id}</div>
                    <div>
                      Resolved workflow: {executionResult.workflow?.workflow_id || 'n/a'} /{' '}
                      {executionResult.workflow?.workflow_version || 'n/a'}
                    </div>
                    <div>Resolution path: {executionResult.workflow?.resolution || 'n/a'}</div>
                    <div>Graph nodes executed: {executionResult.node_trace?.length || 0}</div>
                    {executionResult.response_text && <div>Customer response: {executionResult.response_text}</div>}
                    <div>Trace: {executionResult.trace?.trace_id || 'n/a'}</div>
                    {executionResult.node_trace?.length > 0 && (
                      <div style={{ marginTop: 12, display: 'grid', gap: 8 }}>
                        {executionResult.node_trace.map((item) => (
                          <div
                            key={item.node_id}
                            style={{
                              padding: 10,
                              borderRadius: 12,
                              background: 'var(--md-surface-variant)',
                              border: '1px solid var(--md-outline-variant)',
                            }}
                          >
                            <div style={{ fontWeight: 600 }}>
                              {item.label}{' '}
                              <span style={{ color: 'var(--md-on-surface-variant)' }}>({item.node_type})</span>
                            </div>
                            <div style={{ color: 'var(--md-on-surface-variant)' }}>Status: {item.status}</div>
                            {item.mode && <div style={{ color: 'var(--md-on-surface-variant)' }}>Mode: {item.mode}</div>}
                            {item.note && <div style={{ color: 'var(--md-on-warning-container)' }}>Note: {item.note}</div>}
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>

          <div
            style={{
              border: '1px solid var(--md-outline-variant)',
              borderRadius: 18,
              padding: 16,
              background: 'color-mix(in srgb, var(--md-surface-container) 90%, white)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <FlaskConical size={16} color="var(--md-primary)" />
              <strong style={{ fontSize: 13 }}>Latest Test Run</strong>
            </div>
            {testResult ? (
              <div style={{ color: 'var(--md-on-surface)', fontSize: 13, lineHeight: 1.6 }}>
                <div>Status: {testResult.status}</div>
                <div>Mode: {testResult.mode || 'sandbox'}</div>
                <div>Run ID: {testResult.run_id || 'n/a'}</div>
                <div>Connectors exercised: {testResult.connector_results?.length || 0}</div>
                <div>Graph nodes executed: {testResult.node_trace?.length || 0}</div>
                {testResult.response_text && <div>Customer response: {testResult.response_text}</div>}
                {testResult.connector_results?.length > 0 && (
                  <div style={{ marginTop: 12, display: 'grid', gap: 8 }}>
                    {testResult.connector_results.map((item) => (
                      <div
                        key={`${item.node_id}-${item.connector_type}`}
                        style={{
                          padding: 10,
                          borderRadius: 12,
                          background: 'var(--md-surface-variant)',
                          border: '1px solid var(--md-outline-variant)',
                        }}
                      >
                        <div style={{ fontWeight: 600 }}>
                          {item.connector_type} / {item.action}
                        </div>
                        <div style={{ color: 'var(--md-on-surface-variant)' }}>Mode: {item.mode}</div>
                        <div style={{ color: 'var(--md-on-surface-variant)' }}>Status: {item.status}</div>
                        {item.note && <div style={{ color: 'var(--md-on-warning-container)' }}>Note: {item.note}</div>}
                      </div>
                    ))}
                  </div>
                )}
                {testResult.error && (
                  <div style={{ color: 'var(--md-on-error-container)', marginTop: 12 }}>{testResult.error}</div>
                )}
              </div>
            ) : (
              <div style={{ color: 'var(--md-on-surface-variant)', fontSize: 13 }}>
                Run a test flow to verify Shopify lookup, Salesforce context, and WhatsApp response.
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
