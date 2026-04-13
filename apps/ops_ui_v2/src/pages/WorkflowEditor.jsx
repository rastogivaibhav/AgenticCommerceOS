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
    default: { background: 'rgba(255,255,255,0.06)', color: '#d1d5db', border: '1px solid rgba(255,255,255,0.08)' },
    success: { background: 'rgba(34,197,94,0.12)', color: '#4ade80', border: '1px solid rgba(34,197,94,0.2)' },
    warning: { background: 'rgba(245,158,11,0.12)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.2)' },
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

  const activeVersion = useMemo(
    () => {
      const versions = workflow?.versions || [];
      return workflow?.active_version || versions[versions.length - 1]?.version || 'draft';
    },
    [workflow],
  );

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
  }, [executionForm]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#0d0f14', color: '#fff' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          padding: '12px 20px',
          borderBottom: '1px solid rgba(255,255,255,0.07)',
          background: 'rgba(15,17,21,0.95)',
          flexShrink: 0,
        }}
      >
        <button
          onClick={() => navigate('/workflows')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'transparent',
            border: 'none',
            color: '#9ca3af',
            cursor: 'pointer',
            fontSize: 13,
            padding: '6px 10px',
            borderRadius: 6,
          }}
        >
          <ArrowLeft size={15} /> Back
        </button>

        <div style={{ width: 1, height: 24, background: 'rgba(255,255,255,0.1)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1 }}>
          <div style={{ background: 'rgba(139,92,246,0.15)', padding: 6, borderRadius: 6 }}>
            <GitBranch size={16} color="#8b5cf6" />
          </div>
          <div>
            <div style={{ fontSize: 15, fontWeight: 600, color: '#f9fafb' }}>
              {workflow?.name || 'Workflow Designer'}
            </div>
            <div style={{ fontSize: 11, color: '#6b7280', fontFamily: 'monospace' }}>{id}</div>
          </div>
          <div style={{ marginLeft: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <StatusPill label={workflow?.status || 'draft'} tone={workflow?.status === 'active' ? 'success' : 'warning'} />
            <StatusPill label={`Version ${activeVersion}`} />
            <StatusPill label={workflow?.provenance_mode || workflow?.mode || 'demo'} tone={(workflow?.mode || workflow?.provenance_mode) === 'live' ? 'success' : 'warning'} />
            {analystMode && <StatusPill label="Read-only" tone="warning" />}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {saveMsg && (
            <span
              style={{
                fontSize: 12,
                color: saveMsg === 'Saved' ? '#4ade80' : '#f87171',
                padding: '4px 10px',
                borderRadius: 4,
                background: saveMsg === 'Saved' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)',
              }}
            >
              {saveMsg}
            </span>
          )}
          <button
            onClick={handleTestRun}
            disabled={testing || !allowSave}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 7,
              background: testing || !allowSave ? '#374151' : '#111827',
              border: '1px solid rgba(255,255,255,0.08)',
              color: '#fff',
              padding: '8px 16px',
              borderRadius: 8,
              fontWeight: 600,
              cursor: testing || !allowSave ? 'not-allowed' : 'pointer',
              fontSize: 13,
            }}
          >
            {testing ? <Loader2 size={14} className="animate-spin" /> : <FlaskConical size={14} />}
            Test Flow
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !allowSave || !draftGraph}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 7,
              background: saving || !allowSave ? '#374151' : '#3b82f6',
              border: 'none',
              color: '#fff',
              padding: '8px 18px',
              borderRadius: 8,
              fontWeight: 600,
              cursor: saving || !allowSave ? 'not-allowed' : 'pointer',
              fontSize: 13,
            }}
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
                color: '#6b7280',
                gap: 10,
              }}
            >
              <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
              <span style={{ fontSize: 13 }}>Loading workflow…</span>
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
            borderLeft: '1px solid rgba(255,255,255,0.06)',
            background: '#0f1115',
            padding: 20,
            overflowY: 'auto',
          }}
        >
          <div className="eyebrow">Release Context</div>
          <h2 style={{ marginTop: 6, marginBottom: 12, fontSize: 18 }}>Current Evidence</h2>

          <div
            style={{
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 16,
              padding: 16,
              background: 'rgba(255,255,255,0.03)',
              marginBottom: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <ShieldCheck size={16} color="#4ade80" />
              <strong style={{ fontSize: 13 }}>Workflow Summary</strong>
            </div>
            <div style={{ color: '#9ca3af', fontSize: 13, lineHeight: 1.6 }}>
              <div>Family: {workflow?.workflow_family || 'Unknown'}</div>
              <div>Active version: {activeVersion}</div>
              <div>Runs loaded: {workflow?.runs?.length || 0}</div>
              <div>Promotions logged: {workflow?.promotions?.length || 0}</div>
            </div>
          </div>

          <div
            style={{
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 16,
              padding: 16,
              background: 'rgba(255,255,255,0.03)',
              marginBottom: 16,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <PlayCircle size={16} color="#34d399" />
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
              <div style={{ marginTop: 14, color: '#d1d5db', fontSize: 13, lineHeight: 1.6 }}>
                {executionResult.error ? (
                  <div style={{ color: '#f87171' }}>{executionResult.error}</div>
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
                              background: '#111827',
                              border: '1px solid rgba(255,255,255,0.06)',
                            }}
                          >
                            <div style={{ fontWeight: 600 }}>
                              {item.label} <span style={{ color: '#6b7280' }}>({item.node_type})</span>
                            </div>
                            <div style={{ color: '#9ca3af' }}>Status: {item.status}</div>
                            {item.mode && <div style={{ color: '#9ca3af' }}>Mode: {item.mode}</div>}
                            {item.note && <div style={{ color: '#fbbf24' }}>Note: {item.note}</div>}
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
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 16,
              padding: 16,
              background: 'rgba(255,255,255,0.03)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
              <FlaskConical size={16} color="#60a5fa" />
              <strong style={{ fontSize: 13 }}>Latest Test Run</strong>
            </div>
            {testResult ? (
              <div style={{ color: '#d1d5db', fontSize: 13, lineHeight: 1.6 }}>
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
                          background: '#111827',
                          border: '1px solid rgba(255,255,255,0.06)',
                        }}
                      >
                        <div style={{ fontWeight: 600 }}>
                          {item.connector_type} / {item.action}
                        </div>
                        <div style={{ color: '#9ca3af' }}>Mode: {item.mode}</div>
                        <div style={{ color: '#9ca3af' }}>Status: {item.status}</div>
                        {item.note && <div style={{ color: '#fbbf24' }}>Note: {item.note}</div>}
                      </div>
                    ))}
                  </div>
                )}
                {testResult.error && (
                  <div style={{ color: '#f87171', marginTop: 12 }}>{testResult.error}</div>
                )}
              </div>
            ) : (
              <div style={{ color: '#9ca3af', fontSize: 13 }}>
                Run a test flow to verify Shopify lookup, Salesforce context, and WhatsApp response.
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
