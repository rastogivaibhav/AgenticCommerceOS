import React from 'react';
import {
  PlayCircle, StopCircle, Zap, Clock, Cpu, Settings, Users,
  Link2, GitBranch, Terminal,
} from 'lucide-react';

function DragItem({ nodeType, dataPayload, color, icon, label, sublabel }) {
  const onDragStart = (event) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.setData('application/json', JSON.stringify({ label, ...dataPayload }));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      draggable
      onDragStart={onDragStart}
      style={{
        display: 'flex', alignItems: 'center', gap: '9px',
        padding: '8px 10px', borderRadius: '7px', cursor: 'grab',
        background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
        marginBottom: '5px', userSelect: 'none',
      }}
      onMouseOver={e => e.currentTarget.style.background = 'rgba(255,255,255,0.07)'}
      onMouseOut={e => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
    >
      <div style={{ background: color, padding: '5px', borderRadius: '5px', display: 'flex', flexShrink: 0 }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '12px', color: '#f9fafb', fontWeight: 500 }}>{label}</div>
        {sublabel && <div style={{ fontSize: '10px', color: '#6b7280' }}>{sublabel}</div>}
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ fontSize: '10px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: '7px', paddingLeft: '2px' }}>
        {title}
      </div>
      {children}
    </div>
  );
}

export default function NodeSidebar() {
  return (
    <div style={{
      width: '180px', flexShrink: 0, background: '#111318',
      borderRight: '1px solid #1f2937', overflowY: 'auto',
      padding: '14px 10px',
    }}>
      <div style={{ fontSize: '11px', fontWeight: 600, color: '#9ca3af', marginBottom: '14px', letterSpacing: '0.3px' }}>
        Node Palette
      </div>

      <Section title="Flow Control">
        <DragItem nodeType="startNode" color="#22c55e" icon={<PlayCircle size={12} color="#fff" />} label="Start" sublabel="Entry point" dataPayload={{ triggerType: 'manual' }} />
        <DragItem nodeType="endNode" color="#ef4444" icon={<StopCircle size={12} color="#fff" />} label="End" sublabel="Terminal node" dataPayload={{ outcomeType: 'success' }} />
      </Section>

      <Section title="Triggers">
        <DragItem nodeType="triggerNode" color="#8b5cf6" icon={<Zap size={12} color="#fff" />} label="Webhook" sublabel="HTTP trigger" dataPayload={{ type: 'webhook' }} />
        <DragItem nodeType="triggerNode" color="#8b5cf6" icon={<Clock size={12} color="#fff" />} label="CRON" sublabel="Schedule trigger" dataPayload={{ type: 'cron' }} />
      </Section>

      <Section title="Agents">
        <DragItem nodeType="orchestratorNode" color="#a855f7" icon={<Cpu size={12} color="#fff" />} label="Orchestrator" sublabel="Fan-out router" dataPayload={{}} />
        <DragItem nodeType="agentNode" color="#3b82f6" icon={<Settings size={12} color="#fff" />} label="Agent" sublabel="Run an agent" dataPayload={{}} />
        <DragItem nodeType="subAgentNode" color="#06b6d4" icon={<Users size={12} color="#fff" />} label="Sub-Agent" sublabel="Delegated agent" dataPayload={{}} />
      </Section>

      <Section title="Skills & APIs">
        <DragItem nodeType="integrationNode" color="#10b981" icon={<Link2 size={12} color="#fff" />} label="Integration" sublabel="Skill / API call" dataPayload={{}} />
      </Section>

      <Section title="Logic">
        <DragItem nodeType="logicNode" color="#f59e0b" icon={<GitBranch size={12} color="#fff" />} label="Condition" sublabel="Switch / branch" dataPayload={{ logicType: 'switch' }} />
        <DragItem nodeType="logicNode" color="#f59e0b" icon={<Terminal size={12} color="#fff" />} label="Code" sublabel="Custom snippet" dataPayload={{ logicType: 'code' }} />
      </Section>
    </div>
  );
}
