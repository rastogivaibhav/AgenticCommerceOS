import React, { useState, useEffect } from 'react';
import { X, Save, Database, Key, Settings2, PlayCircle, StopCircle, Cpu, Users } from 'lucide-react';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8081';

function useAgents() {
  const [agents, setAgents] = useState([]);
  useEffect(() => {
    fetch(`${API}/agents`, { headers: { Authorization: `Bearer ${localStorage.getItem('ops_token') || 'dev-ops-token'}` } })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.agents) setAgents(d.agents); })
      .catch(() => {});
  }, []);
  return agents;
}

function useSkills() {
  const [skills, setSkills] = useState([]);
  useEffect(() => {
    fetch(`${API}/skills`, { headers: { Authorization: `Bearer ${localStorage.getItem('ops_token') || 'dev-ops-token'}` } })
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.skills) setSkills(d.skills); })
      .catch(() => {});
  }, []);
  return skills;
}

// ─── SHARED FORM CONTROLS ─────────────────────────────────────────────────────
const inputStyle = { width: '100%', padding: '9px', background: '#1f2937', border: '1px solid #374151', borderRadius: '6px', color: '#fff', fontSize: '12px', boxSizing: 'border-box' };
const labelStyle = { display: 'block', fontSize: '11px', color: '#9ca3af', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.4px' };
const sectionStyle = { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', padding: '14px', borderRadius: '8px' };

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: '14px' }}>
      <label style={labelStyle}>{label}</label>
      {children}
    </div>
  );
}

// ─── NODE-TYPE PANELS ─────────────────────────────────────────────────────────
function StartPanel({ data, onChange }) {
  return (
    <div style={sectionStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '14px' }}>
        <PlayCircle size={14} color="#22c55e" />
        <span style={{ color: '#22c55e', fontSize: '12px', fontWeight: 600 }}>Start Configuration</span>
      </div>
      <Field label="Trigger Type">
        <select value={data.triggerType || 'manual'} onChange={e => onChange('triggerType', e.target.value)} style={inputStyle}>
          <option value="manual">Manual</option>
          <option value="webhook">Webhook (HTTP)</option>
          <option value="schedule">Schedule (CRON)</option>
          <option value="api">API Call</option>
        </select>
      </Field>
      {data.triggerType === 'schedule' && (
        <Field label="CRON Expression">
          <input type="text" value={data.cronExpr || ''} onChange={e => onChange('cronExpr', e.target.value)} placeholder="0 9 * * 1-5" style={inputStyle} />
        </Field>
      )}
    </div>
  );
}

function EndPanel({ data, onChange }) {
  return (
    <div style={sectionStyle}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '14px' }}>
        <StopCircle size={14} color="#ef4444" />
        <span style={{ color: '#ef4444', fontSize: '12px', fontWeight: 600 }}>End Configuration</span>
      </div>
      <Field label="Outcome Type">
        <select value={data.outcomeType || 'success'} onChange={e => onChange('outcomeType', e.target.value)} style={inputStyle}>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
          <option value="timeout">Timeout</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </Field>
    </div>
  );
}

function AgentPanel({ data, onChange, agents, color, title, icon }) {
  return (
    <div style={{ ...sectionStyle, borderColor: `${color}30` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '14px' }}>
        {icon}
        <span style={{ color, fontSize: '12px', fontWeight: 600 }}>{title}</span>
      </div>
      <Field label="Bind Agent">
        <select value={data.agentId || ''} onChange={e => onChange('agentId', e.target.value)} style={inputStyle}>
          <option value="">— Select Agent —</option>
          {agents.map(a => (
            <option key={a.id || a.agent_id} value={a.id || a.agent_id}>
              {a.name || a.id || a.agent_id}
            </option>
          ))}
        </select>
      </Field>
      <Field label="System Prompt Override">
        <textarea
          rows={3}
          value={data.systemPrompt || ''}
          onChange={e => onChange('systemPrompt', e.target.value)}
          placeholder="Inject localized instructions..."
          style={{ ...inputStyle, resize: 'vertical' }}
        />
      </Field>
    </div>
  );
}

function IntegrationPanel({ data, onChange, skills }) {
  return (
    <div style={{ ...sectionStyle, borderColor: '#10b98130' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '14px' }}>
        <Key size={14} color="#10b981" />
        <span style={{ color: '#10b981', fontSize: '12px', fontWeight: 600 }}>Skill Binding</span>
      </div>
      <Field label="Skill / API">
        <select value={data.skillId || ''} onChange={e => onChange('skillId', e.target.value)} style={inputStyle}>
          <option value="">— Select Skill —</option>
          {skills.map(s => (
            <option key={s.id || s.skill_id} value={s.id || s.skill_id}>
              {s.name || s.id || s.skill_id}
            </option>
          ))}
        </select>
      </Field>
      <Field label="JSON Payload Template">
        <textarea
          rows={4}
          value={data.payloadTemplate || ''}
          onChange={e => onChange('payloadTemplate', e.target.value)}
          placeholder={'{"id": "{{input.id}}"}'}
          style={{ ...inputStyle, fontFamily: 'monospace', color: '#a78bfa', resize: 'vertical' }}
        />
      </Field>
    </div>
  );
}

// ─── MAIN PANEL ───────────────────────────────────────────────────────────────
export default function NodeConfigPanel({ node, onClose, onSave }) {
  const [formData, setFormData] = useState({});
  const agents = useAgents();
  const skills = useSkills();

  useEffect(() => {
    if (node) setFormData(node.data);
  }, [node]);

  if (!node) return null;

  const handleChange = (key, value) => setFormData(prev => ({ ...prev, [key]: value }));

  const typeLabels = {
    startNode: 'Start Node', endNode: 'End Node',
    orchestratorNode: 'Orchestrator', agentNode: 'Agent',
    subAgentNode: 'Sub-Agent', triggerNode: 'Trigger',
    integrationNode: 'Integration', logicNode: 'Logic',
  };

  return (
    <div style={{
      width: '300px',
      background: '#111318',
      borderLeft: '1px solid #1f2937',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      boxShadow: '-4px 0 24px rgba(0,0,0,0.5)',
      position: 'absolute',
      right: 0, top: 0,
      zIndex: 10,
      animation: 'slideInRight 0.15s ease-out',
    }}>
      <div style={{ padding: '14px 18px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: '#fff', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '7px' }}>
          <Settings2 size={14} color="#6b7280" />
          {typeLabels[node.type] || 'Node Config'}
        </h3>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#6b7280', cursor: 'pointer' }}>
          <X size={17} />
        </button>
      </div>

      <div style={{ flexGrow: 1, overflowY: 'auto', padding: '16px' }}>
        <Field label="Node ID">
          <div style={{ padding: '7px 9px', background: 'rgba(255,255,255,0.03)', border: '1px dashed #374151', borderRadius: '4px', fontFamily: 'monospace', color: '#4b5563', fontSize: '11px' }}>
            {node.id}
          </div>
        </Field>

        <Field label="Label">
          <input type="text" value={formData.label || ''} onChange={e => handleChange('label', e.target.value)} style={inputStyle} />
        </Field>

        {node.type === 'startNode' && <StartPanel data={formData} onChange={handleChange} />}
        {node.type === 'endNode' && <EndPanel data={formData} onChange={handleChange} />}
        {node.type === 'orchestratorNode' && (
          <AgentPanel data={formData} onChange={handleChange} agents={agents} color="#a855f7" title="Orchestrator Binding" icon={<Cpu size={14} color="#a855f7" />} />
        )}
        {node.type === 'agentNode' && (
          <AgentPanel data={formData} onChange={handleChange} agents={agents} color="#3b82f6" title="Agent Binding" icon={<Database size={14} color="#3b82f6" />} />
        )}
        {node.type === 'subAgentNode' && (
          <AgentPanel data={formData} onChange={handleChange} agents={agents} color="#06b6d4" title="Sub-Agent Binding" icon={<Users size={14} color="#06b6d4" />} />
        )}
        {node.type === 'integrationNode' && <IntegrationPanel data={formData} onChange={handleChange} skills={skills} />}
        {node.type === 'triggerNode' && (
          <div style={sectionStyle}>
            <Field label="Trigger Type">
              <select value={formData.type || 'webhook'} onChange={e => handleChange('type', e.target.value)} style={inputStyle}>
                <option value="webhook">Webhook</option>
                <option value="cron">CRON Schedule</option>
                <option value="manual">Manual</option>
              </select>
            </Field>
          </div>
        )}
        {node.type === 'logicNode' && (
          <div style={sectionStyle}>
            <Field label="Logic Type">
              <select value={formData.logicType || 'switch'} onChange={e => handleChange('logicType', e.target.value)} style={inputStyle}>
                <option value="switch">Switch / Conditional</option>
                <option value="code">Custom Code Snippet</option>
              </select>
            </Field>
            {formData.logicType === 'code' && (
              <Field label="Code">
                <textarea rows={5} value={formData.code || ''} onChange={e => handleChange('code', e.target.value)} placeholder="return input.score > 0.8;" style={{ ...inputStyle, fontFamily: 'monospace', resize: 'vertical' }} />
              </Field>
            )}
          </div>
        )}
      </div>

      <div style={{ padding: '14px 18px', borderTop: '1px solid #1f2937', background: 'rgba(0,0,0,0.2)' }}>
        <button
          onClick={() => onSave(node.id, formData)}
          style={{ width: '100%', padding: '10px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '7px', fontSize: '12px' }}
        >
          <Save size={14} /> Save Node
        </button>
      </div>
    </div>
  );
}
