import React from 'react';
import {
  Bot,
  CheckCircle2,
  GitBranch,
  MessageSquare,
  PhoneCall,
  ShoppingBag,
  UserRound,
} from 'lucide-react';

function DragItem({ nodeType, data, color, icon, label, sublabel }) {
  const onDragStart = (event) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.setData('application/json', JSON.stringify(data));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      draggable
      onDragStart={onDragStart}
      style={{
        background: '#1a1d23',
        border: '1px solid #374151',
        padding: '10px 12px',
        borderRadius: 7,
        cursor: 'grab',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
      }}
    >
      <div style={{ background: color, padding: 5, borderRadius: 5, display: 'flex', flexShrink: 0 }}>
        {icon}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ color: '#e5e7eb', fontSize: 13 }}>{label}</span>
        {sublabel && <span style={{ color: '#6b7280', fontSize: 11 }}>{sublabel}</span>}
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section>
      <h3
        style={{
          color: '#9ca3af',
          fontSize: 11,
          textTransform: 'uppercase',
          letterSpacing: 0.8,
          marginBottom: 10,
          marginTop: 0,
        }}
      >
        {title}
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>{children}</div>
    </section>
  );
}

export default function NodeSidebar() {
  return (
    <div
      style={{
        width: 250,
        background: 'rgba(13, 15, 20, 0.97)',
        borderRight: '1px solid rgba(255,255,255,0.06)',
        padding: '16px 14px',
        display: 'flex',
        flexDirection: 'column',
        gap: 22,
        overflowY: 'auto',
        flexShrink: 0,
      }}
    >
      <div style={{ fontSize: 11, color: '#4b5563', textTransform: 'uppercase', letterSpacing: 0.8 }}>
        Drag typed steps onto the flow
      </div>

      <Section title="Triggers">
        <DragItem
          nodeType="triggerNode"
          data={{
            label: 'WhatsApp Inbound',
            channel: 'whatsapp',
            triggerType: 'inbound_message',
            bindingId: 'whatsapp-support',
          }}
          color="#8b5cf6"
          icon={<MessageSquare size={13} color="#fff" />}
          label="WhatsApp Trigger"
          sublabel="Customer message entry"
        />
      </Section>

      <Section title="Connectors">
        <DragItem
          nodeType="connectorNode"
          data={{
            label: 'Shopify Order Lookup',
            connectorType: 'shopify',
            bindingId: 'shopify-primary',
            action: 'get_order',
            config: { order_id: '{{trigger.order_id}}' },
          }}
          color="#10b981"
          icon={<ShoppingBag size={13} color="#fff" />}
          label="Shopify"
          sublabel="Order, customer, product"
        />
        <DragItem
          nodeType="connectorNode"
          data={{
            label: 'Salesforce Context',
            connectorType: 'salesforce',
            bindingId: 'salesforce-support',
            action: 'get_contact',
            config: { contact_key: '{{trigger.customer_phone}}' },
          }}
          color="#0ea5e9"
          icon={<PhoneCall size={13} color="#fff" />}
          label="Salesforce"
          sublabel="Contact and case context"
        />
        <DragItem
          nodeType="connectorNode"
          data={{
            label: 'WhatsApp Reply',
            connectorType: 'whatsapp',
            bindingId: 'whatsapp-support',
            action: 'send_message',
            config: { template: 'order_status_update' },
          }}
          color="#16a34a"
          icon={<MessageSquare size={13} color="#fff" />}
          label="WhatsApp Reply"
          sublabel="Customer response"
        />
      </Section>

      <Section title="Decisions">
        <DragItem
          nodeType="decisionNode"
          data={{
            label: 'Decision',
            logicType: 'decision',
            routingRule: 'confidence >= 0.7',
          }}
          color="#f59e0b"
          icon={<GitBranch size={13} color="#fff" />}
          label="Decision"
          sublabel="Branch by confidence or policy"
        />
      </Section>

      <Section title="Execution">
        <DragItem
          nodeType="agentNode"
          data={{ label: 'Agent', agentId: 'ag_support_l1' }}
          color="#3b82f6"
          icon={<Bot size={13} color="#fff" />}
          label="Agent"
          sublabel="Decision and drafting"
        />
        <DragItem
          nodeType="humanNode"
          data={{
            label: 'Human Escalation',
            queue: 'tier-2-order-support',
            bindingId: 'salesforce-support',
            action: 'create_case',
          }}
          color="#ef4444"
          icon={<UserRound size={13} color="#fff" />}
          label="Escalation"
          sublabel="Hand off to humans"
        />
        <DragItem
          nodeType="endNode"
          data={{ label: 'Completed', outcomeType: 'success' }}
          color="#22c55e"
          icon={<CheckCircle2 size={13} color="#fff" />}
          label="End"
          sublabel="Terminal state"
        />
      </Section>
    </div>
  );
}
