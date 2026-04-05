import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, GitBranch, Loader2 } from 'lucide-react';
import WorkflowCanvas from '../components/WorkflowCanvas';
import { getWorkflow, updateWorkflow } from '../api/workflowAPI';
import { canOperate, isAnalyst } from '../lib/rbac';

export default function WorkflowEditor() {
  const allowSave = canOperate();
  const analystMode = isAnalyst();
  const { id } = useParams();
  const navigate = useNavigate();
  const [workflow, setWorkflow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);

  useEffect(() => {
    setLoading(true);
    getWorkflow(id)
      .then(setWorkflow)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const handleSave = useCallback(async () => {
    if (!allowSave) return;
    if (!window.serializeWorkflowGraph) return;
    setSaving(true);
    setSaveMsg(null);
    try {
      const graphData = window.serializeWorkflowGraph();
      await updateWorkflow(id, { step_definitions: graphData });
      setSaveMsg('Saved');
      setTimeout(() => setSaveMsg(null), 2500);
    } catch (e) {
      console.error(e);
      setSaveMsg('Save failed');
    } finally {
      setSaving(false);
    }
  }, [allowSave, id]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#0d0f14', color: '#fff' }}>
      {/* Editor header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '16px',
        padding: '12px 20px', borderBottom: '1px solid rgba(255,255,255,0.07)',
        background: 'rgba(15,17,21,0.95)', flexShrink: 0
      }}>
        <button
          onClick={() => navigate('/workflows')}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: '13px', padding: '6px 10px', borderRadius: '6px' }}
          onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.06)'}
          onMouseOut={e => e.currentTarget.style.background = 'transparent'}
        >
          <ArrowLeft size={15} /> Back
        </button>

        <div style={{ width: '1px', height: '24px', background: 'rgba(255,255,255,0.1)' }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1 }}>
          <div style={{ background: 'rgba(139,92,246,0.15)', padding: '6px', borderRadius: '6px' }}>
            <GitBranch size={16} color="#8b5cf6" />
          </div>
          <div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: '#f9fafb' }}>
              {workflow?.name || 'Workflow Editor'}
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280', fontFamily: 'monospace' }}>
              {id}
            </div>
          </div>
          <div style={{ marginLeft: '12px' }}>
            <span style={{
              fontSize: '11px', padding: '3px 8px', borderRadius: '999px',
              background: 'rgba(34,197,94,0.12)', color: '#4ade80',
              border: '1px solid rgba(34,197,94,0.2)'
            }}>
              {workflow?.status || 'draft'}
            </span>
            {analystMode && (
              <span style={{
                marginLeft: '8px',
                fontSize: '11px',
                padding: '3px 8px',
                borderRadius: '999px',
                background: 'rgba(245,158,11,0.12)',
                color: '#fbbf24',
                border: '1px solid rgba(245,158,11,0.2)',
              }}>
                Read-only
              </span>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {saveMsg && (
            <span style={{
              fontSize: '12px', color: saveMsg === 'Saved' ? '#4ade80' : '#f87171',
              padding: '4px 10px', borderRadius: '4px',
              background: saveMsg === 'Saved' ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)'
            }}>
              {saveMsg}
            </span>
          )}
          <button
            onClick={handleSave}
            disabled={saving || !allowSave}
            style={{
              display: 'flex', alignItems: 'center', gap: '7px',
              background: (saving || !allowSave) ? '#374151' : '#3b82f6',
              border: 'none', color: '#fff', padding: '8px 18px',
              borderRadius: '8px', fontWeight: 600, cursor: (saving || !allowSave) ? 'not-allowed' : 'pointer',
              fontSize: '13px', transition: 'background 0.2s'
            }}
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            Save Workflow
          </button>
        </div>
      </div>

      {/* Full-screen canvas */}
      <div style={{ flexGrow: 1, overflow: 'hidden', position: 'relative' }}>
        {loading ? (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b7280', gap: '10px' }}>
            <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} />
            <span style={{ fontSize: '13px' }}>Loading workflow…</span>
          </div>
        ) : (
          /* key forces a full remount once workflow data arrives so
             useNodesState initialises with the saved graph, not the default */
          <WorkflowCanvas
            key={id}
            initialGraph={workflow?.step_definitions ?? null}
          />
        )}
      </div>
    </div>
  );
}
