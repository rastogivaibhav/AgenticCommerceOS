import React, { useEffect, useMemo, useState } from 'react';
import {
  Bot,
  GitBranch,
  MessageSquare,
  Save,
  Settings2,
  ShoppingBag,
  UserRound,
  X,
} from 'lucide-react';
import { listAgents } from '../api/agentsAPI';
import { getConnectorBindings } from '../api/opsAPI';

const inputStyle = {
  width: '100%',
  padding: 9,
  background: '#1f2937',
  border: '1px solid #374151',
  borderRadius: 6,
  color: '#fff',
  fontSize: 12,
  boxSizing: 'border-box',
};

const labelStyle = {
  display: 'block',
  fontSize: 11,
  color: '#9ca3af',
  marginBottom: 5,
  textTransform: 'uppercase',
  letterSpacing: 0.4,
};

const sectionStyle = {
  background: 'rgba(255,255,255,0.03)',
  border: '1px solid rgba(255,255,255,0.07)',
  padding: 14,
  borderRadius: 8,
};

const CONNECTOR_ACTIONS = {
  shopify: ['get_order', 'get_customer', 'get_product', 'create_return_intent'],
  salesforce: ['get_contact', 'get_case', 'create_case', 'update_case'],
  whatsapp: ['inbound_message_trigger', 'send_message', 'send_template_message', 'handoff_tag'],
  commerce: ['lookup_policy', 'manual_review', 'create_note'],
};

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 14 }}>
      <label style={labelStyle}>{label}</label>
      {children}
    </div>
  );
}

function PanelHeader({ icon, title, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 14 }}>
      {icon}
      <span style={{ color, fontSize: 12, fontWeight: 600 }}>{title}</span>
    </div>
  );
}

function TriggerPanel({ data, onChange, bindings }) {
  const whatsappBindings = bindings.filter((binding) => binding.connector_type === 'whatsapp');
  return (
    <div style={sectionStyle}>
      <PanelHeader icon={<MessageSquare size={14} color="#8b5cf6" />} title="Trigger Settings" color="#8b5cf6" />
      <Field label="Channel">
        <select
          value={data.channel || 'whatsapp'}
          onChange={(event) => onChange('channel', event.target.value)}
          style={inputStyle}
        >
          <option value="whatsapp">WhatsApp</option>
          <option value="api">API</option>
          <option value="webhook">Webhook</option>
        </select>
      </Field>
      <Field label="Trigger Type">
        <select
          value={data.triggerType || 'inbound_message'}
          onChange={(event) => onChange('triggerType', event.target.value)}
          style={inputStyle}
        >
          <option value="inbound_message">Inbound message</option>
          <option value="manual">Manual test</option>
          <option value="webhook">Webhook event</option>
        </select>
      </Field>
      <Field label="Binding">
        <select
          value={data.bindingId || ''}
          onChange={(event) => onChange('bindingId', event.target.value)}
          style={inputStyle}
        >
          <option value="">Select binding</option>
          {whatsappBindings.map((binding) => (
            <option key={binding.id} value={binding.id}>
              {binding.display_name} ({binding.mode})
            </option>
          ))}
        </select>
      </Field>
      <Field label="Sample Message">
        <textarea
          rows={3}
          value={data.sampleMessage || ''}
          onChange={(event) => onChange('sampleMessage', event.target.value)}
          style={{ ...inputStyle, resize: 'vertical' }}
        />
      </Field>
    </div>
  );
}

function AgentPanel({ data, onChange, agents }) {
  return (
    <div style={sectionStyle}>
      <PanelHeader icon={<Bot size={14} color="#3b82f6" />} title="Agent Binding" color="#3b82f6" />
      <Field label="Agent">
        <select
          value={data.agentId || ''}
          onChange={(event) => onChange('agentId', event.target.value)}
          style={inputStyle}
        >
          <option value="">Select agent</option>
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id}>
              {agent.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Role">
        <input
          type="text"
          value={data.role || 'primary_executor'}
          onChange={(event) => onChange('role', event.target.value)}
          style={inputStyle}
        />
      </Field>
    </div>
  );
}

function ConnectorPanel({ data, onChange, bindings }) {
  const connectorType = data.connectorType || 'shopify';
  const filteredBindings = bindings.filter((binding) => binding.connector_type === connectorType);
  const actions = CONNECTOR_ACTIONS[connectorType] || [];

  return (
    <div style={sectionStyle}>
      <PanelHeader icon={<ShoppingBag size={14} color="#10b981" />} title="Connector Step" color="#10b981" />
      <Field label="Connector">
        <select
          value={connectorType}
          onChange={(event) => onChange('connectorType', event.target.value)}
          style={inputStyle}
        >
          <option value="shopify">Shopify</option>
          <option value="salesforce">Salesforce</option>
          <option value="whatsapp">WhatsApp</option>
          <option value="commerce">Commerce Ops</option>
        </select>
      </Field>
      <Field label="Binding">
        <select
          value={data.bindingId || ''}
          onChange={(event) => onChange('bindingId', event.target.value)}
          style={inputStyle}
        >
          <option value="">Select binding</option>
          {filteredBindings.map((binding) => (
            <option key={binding.id} value={binding.id}>
              {binding.display_name} ({binding.mode})
            </option>
          ))}
        </select>
      </Field>
      <Field label="Action">
        <select
          value={data.action || actions[0] || ''}
          onChange={(event) => onChange('action', event.target.value)}
          style={inputStyle}
        >
          {actions.map((action) => (
            <option key={action} value={action}>
              {action}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Config JSON">
        <textarea
          rows={5}
          value={JSON.stringify(data.config || {}, null, 2)}
          onChange={(event) => {
            try {
              onChange('config', JSON.parse(event.target.value || '{}'));
            } catch {
              onChange('config_raw', event.target.value);
            }
          }}
          style={{ ...inputStyle, fontFamily: 'monospace', resize: 'vertical' }}
        />
      </Field>
    </div>
  );
}

function DecisionPanel({ data, onChange }) {
  return (
    <div style={sectionStyle}>
      <PanelHeader icon={<GitBranch size={14} color="#f59e0b" />} title="Decision Routing" color="#f59e0b" />
      <Field label="Routing Rule">
        <textarea
          rows={4}
          value={data.routingRule || ''}
          onChange={(event) => onChange('routingRule', event.target.value)}
          style={{ ...inputStyle, fontFamily: 'monospace', resize: 'vertical' }}
        />
      </Field>
    </div>
  );
}

function HumanPanel({ data, onChange, bindings }) {
  const salesforceBindings = bindings.filter((binding) => binding.connector_type === 'salesforce');
  return (
    <div style={sectionStyle}>
      <PanelHeader icon={<UserRound size={14} color="#ef4444" />} title="Human Escalation" color="#ef4444" />
      <Field label="Queue">
        <input
          type="text"
          value={data.queue || ''}
          onChange={(event) => onChange('queue', event.target.value)}
          style={inputStyle}
        />
      </Field>
      <Field label="Case Binding">
        <select
          value={data.bindingId || ''}
          onChange={(event) => onChange('bindingId', event.target.value)}
          style={inputStyle}
        >
          <option value="">Select binding</option>
          {salesforceBindings.map((binding) => (
            <option key={binding.id} value={binding.id}>
              {binding.display_name} ({binding.mode})
            </option>
          ))}
        </select>
      </Field>
      <Field label="Escalation Action">
        <select
          value={data.action || 'create_case'}
          onChange={(event) => onChange('action', event.target.value)}
          style={inputStyle}
        >
          <option value="create_case">create_case</option>
          <option value="update_case">update_case</option>
        </select>
      </Field>
    </div>
  );
}

function EndPanel({ data, onChange }) {
  return (
    <div style={sectionStyle}>
      <PanelHeader icon={<Settings2 size={14} color="#22c55e" />} title="Terminal State" color="#22c55e" />
      <Field label="Outcome">
        <select
          value={data.outcomeType || 'success'}
          onChange={(event) => onChange('outcomeType', event.target.value)}
          style={inputStyle}
        >
          <option value="success">success</option>
          <option value="escalated">escalated</option>
          <option value="failure">failure</option>
        </select>
      </Field>
    </div>
  );
}

export default function NodeConfigPanel({ node, onClose, onSave }) {
  const [formData, setFormData] = useState(() => node?.data || {});
  const [agents, setAgents] = useState([]);
  const [bindings, setBindings] = useState([]);

  useEffect(() => {
    let isMounted = true;
    Promise.all([listAgents(), getConnectorBindings()])
      .then(([agentPayload, bindingPayload]) => {
        if (!isMounted) return;
        setAgents(agentPayload.agents || []);
        setBindings(bindingPayload.bindings || []);
      })
      .catch((error) => {
        console.error('Failed to load node config dependencies:', error);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const nodeLabel = useMemo(() => {
    const labelMap = {
      triggerNode: 'Trigger',
      connectorNode: 'Connector',
      agentNode: 'Agent',
      decisionNode: 'Decision',
      humanNode: 'Escalation',
      endNode: 'End',
    };
    return labelMap[node?.type] || 'Node';
  }, [node]);

  if (!node) return null;

  const handleChange = (key, value) => {
    setFormData((current) => ({ ...current, [key]: value }));
  };

  return (
    <div
      style={{
        width: 320,
        background: '#111318',
        borderLeft: '1px solid #1f2937',
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        boxShadow: '-4px 0 24px rgba(0,0,0,0.5)',
        position: 'absolute',
        right: 0,
        top: 0,
        zIndex: 10,
      }}
    >
      <div
        style={{
          padding: '14px 18px',
          borderBottom: '1px solid #1f2937',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h3
          style={{
            margin: 0,
            color: '#fff',
            fontSize: 13,
            display: 'flex',
            alignItems: 'center',
            gap: 7,
          }}
        >
          <Settings2 size={14} color="#6b7280" />
          {nodeLabel} Settings
        </h3>
        <button
          onClick={onClose}
          style={{ background: 'transparent', border: 'none', color: '#6b7280', cursor: 'pointer' }}
        >
          <X size={17} />
        </button>
      </div>

      <div style={{ flexGrow: 1, overflowY: 'auto', padding: 16 }}>
        <Field label="Node ID">
          <div
            style={{
              padding: '7px 9px',
              background: 'rgba(255,255,255,0.03)',
              border: '1px dashed #374151',
              borderRadius: 4,
              fontFamily: 'monospace',
              color: '#4b5563',
              fontSize: 11,
            }}
          >
            {node.id}
          </div>
        </Field>

        <Field label="Label">
          <input
            type="text"
            value={formData.label || ''}
            onChange={(event) => handleChange('label', event.target.value)}
            style={inputStyle}
          />
        </Field>

        {node.type === 'triggerNode' && (
          <TriggerPanel data={formData} onChange={handleChange} bindings={bindings} />
        )}
        {node.type === 'agentNode' && (
          <AgentPanel data={formData} onChange={handleChange} agents={agents} />
        )}
        {node.type === 'connectorNode' && (
          <ConnectorPanel data={formData} onChange={handleChange} bindings={bindings} />
        )}
        {node.type === 'decisionNode' && (
          <DecisionPanel data={formData} onChange={handleChange} />
        )}
        {node.type === 'humanNode' && (
          <HumanPanel data={formData} onChange={handleChange} bindings={bindings} />
        )}
        {node.type === 'endNode' && <EndPanel data={formData} onChange={handleChange} />}
      </div>

      <div style={{ padding: '14px 18px', borderTop: '1px solid #1f2937', background: 'rgba(0,0,0,0.2)' }}>
        <button
          onClick={() => onSave(node.id, formData)}
          style={{
            width: '100%',
            padding: 10,
            background: '#3b82f6',
            color: '#fff',
            border: 'none',
            borderRadius: 6,
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 7,
            fontSize: 12,
          }}
        >
          <Save size={14} /> Save Node
        </button>
      </div>
    </div>
  );
}
