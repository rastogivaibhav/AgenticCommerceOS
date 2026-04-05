import React from 'react';
import { PlayCircle, StopCircle, Cpu, Settings, Users, Link2, Zap, Clock, GitBranch, Terminal } from 'lucide-react';

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
        borderRadius: '7px',
        cursor: 'grab',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        transition: 'border-color 0.15s',
      }}
      onMouseOver={e => e.currentTarget.style.borderColor = color}
      onMouseOut={e => e.currentTarget.style.borderColor = '#374151'}
    >
      <div style={{ background: color, padding: '5px', borderRadius: '5px', display: 'flex', flexShrink: 0 }}>
        {icon}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <span style={{ color: '#e5e7eb', fontSize: '13px' }}>{label}</span>
        {sublabel && <span style={{ color: '#6b7280', fontSize: '11px' }}>{sublabel}</span>}
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section>
      <h3 style={{ color: '#9ca3af', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '10px', marginTop: 0 }}>
        {title}
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '7px' }}>
        {children}
      </div>
    </section>
  );
}

export default function NodeSidebar() {
  return (
    <div style={{
      width: '230px',
      background: 'rgba(13, 15, 20, 0.97)',
      borderRight: '1px solid rgba(255,255,255,0.06)',
      padding: '16px 14px',
      display: 'flex',
      flexDirection: 'column',
      gap: '22px',
      overflowY: 'auto',
      flexShrink: 0,
    }}>
      <div style={{ fontSize: '11px', color: '#4b5563', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
        Drag nodes onto canvas
      </div>

      <Section title="Flow Control">
        <DragItem nodeType="startNode" data={{ label: 'Start', triggerType: 'manual' }} color="#22c55e" icon={<PlayCircle size={13} color="#fff" />} label="Start" sublabel="Entry point" />
        <DragItem nodeType="endNode" data={{ label: 'End', outcomeType: 'success' }} color="#ef4444" icon={<StopCircle size={13} color="#fff" />} label="End" sublabel="Terminal node" />
      </Section>

      <Section title="Triggers">
        <DragItem nodeType="triggerNode" data={{ label: 'Webhook Trigger', triggerType: 'webhook' }} color="#8b5cf6" icon={<Zap size={13} color="#fff" />} label="Webhook" sublabel="HTTP event" />
        <DragItem nodeType="triggerNode" data={{ label: 'CRON Schedule', type: 'cron' }} color="#8b5cf6" icon={<Clock size={13} color="#fff" />} label="CRON Schedule" sublabel="Time-based" />
      </Section>

      <Section title="Agents">
        <DragItem nodeType="orchestratorNode" data={{ label: 'Orchestrator', agentId: '' }} color="#a855f7" icon={<Cpu size={13} color="#fff" />} label="Orchestrator" sublabel="Routes sub-agents" />
        <DragItem nodeType="agentNode" data={{ label: 'Agent', agentId: '' }} color="#3b82f6" icon={<Settings size={13} color="#fff" />} label="Agent" sublabel="Task executor" />
        <DragItem nodeType="subAgentNode" data={{ label: 'Sub-Agent', agentId: '' }} color="#06b6d4" icon={<Users size={13} color="#fff" />} label="Sub-Agent" sublabel="Delegated task" />
      </Section>

      <Section title="Skills & APIs">
        <DragItem nodeType="integrationNode" data={{ label: 'API Integration', skillId: '' }} color="#10b981" icon={<Link2 size={13} color="#fff" />} label="Skill Integration" sublabel="Deterministic call" />
      </Section>

      <Section title="Logic">
        <DragItem nodeType="logicNode" data={{ label: 'Switch / Condition', logicType: 'switch' }} color="#f59e0b" icon={<GitBranch size={13} color="#fff" />} label="Switch / Condition" sublabel="Branch on value" />
        <DragItem nodeType="logicNode" data={{ label: 'Code Snippet', logicType: 'code' }} color="#f59e0b" icon={<Terminal size={13} color="#fff" />} label="Code Snippet" sublabel="Custom logic" />
      </Section>
    </div>
  );
}
