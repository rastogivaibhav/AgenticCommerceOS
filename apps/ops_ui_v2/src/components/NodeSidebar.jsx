import React from 'react';
import { Settings, Link2, Zap, Clock, Code, GitMerge, GitBranch, Terminal } from 'lucide-react';

export default function NodeSidebar() {
  const onDragStart = (event, nodeType, dataPayload) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.setData('application/json', JSON.stringify(dataPayload));
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div style={{ 
      width: '260px', 
      background: 'rgba(15, 17, 21, 0.95)', 
      borderRight: '1px solid rgba(255,255,255,0.05)', 
      padding: '16px', 
      display: 'flex', 
      flexDirection: 'column', 
      gap: '24px',
      overflowY: 'auto'
    }}>
      
      {/* TRIGGERS SECTION */}
      <section>
        <h3 style={{ color: '#fff', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px', opacity: 0.6 }}>Triggers</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          
          <div 
            onDragStart={(event) => onDragStart(event, 'triggerNode', { label: 'Webhook Trigger', type: 'webhook' })} 
            draggable 
            style={{ background: '#1e1e24', border: '1px solid #374151', padding: '10px 12px', borderRadius: '6px', cursor: 'grab', display: 'flex', alignItems: 'center', gap: '10px', transition: 'border 0.2s' }}
            onMouseOver={e => e.currentTarget.style.borderColor = '#8b5cf6'}
            onMouseOut={e => e.currentTarget.style.borderColor = '#374151'}
          >
            <Zap size={16} color="#8b5cf6"/>
            <span style={{ color: '#e5e7eb', fontSize: '13px' }}>Webhook Trigger</span>
          </div>

          <div 
            onDragStart={(event) => onDragStart(event, 'triggerNode', { label: 'CRON Schedule', type: 'cron' })} 
            draggable 
            style={{ background: '#1e1e24', border: '1px solid #374151', padding: '10px 12px', borderRadius: '6px', cursor: 'grab', display: 'flex', alignItems: 'center', gap: '10px', transition: 'border 0.2s' }}
            onMouseOver={e => e.currentTarget.style.borderColor = '#8b5cf6'}
            onMouseOut={e => e.currentTarget.style.borderColor = '#374151'}
          >
            <Clock size={16} color="#8b5cf6"/>
            <span style={{ color: '#e5e7eb', fontSize: '13px' }}>CRON Schedule</span>
          </div>

        </div>
      </section>

      {/* AUTONOMOUS AGENTS SECTION */}
      <section>
        <h3 style={{ color: '#fff', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px', opacity: 0.6 }}>Agents</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div 
            onDragStart={(event) => onDragStart(event, 'agentNode', { label: 'Agent Executor', agentId: '' })} 
            draggable 
            style={{ background: '#1e1e24', border: '1px solid #374151', padding: '10px 12px', borderRadius: '6px', cursor: 'grab', display: 'flex', alignItems: 'center', gap: '10px', transition: 'border 0.2s' }}
            onMouseOver={e => e.currentTarget.style.borderColor = '#3b82f6'}
            onMouseOut={e => e.currentTarget.style.borderColor = '#374151'}
          >
            <Settings size={16} color="#3b82f6"/>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ color: '#e5e7eb', fontSize: '13px' }}>Autonomous Agent</span>
              <span style={{ color: '#6b7280', fontSize: '11px' }}>Bind to systemic AI</span>
            </div>
          </div>
        </div>
      </section>

      {/* INTEGRATIONS SECTION */}
      <section>
        <h3 style={{ color: '#fff', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px', opacity: 0.6 }}>Skills & APIs</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div 
            onDragStart={(event) => onDragStart(event, 'integrationNode', { label: 'API Integration', skillId: '' })} 
            draggable 
            style={{ background: '#1e1e24', border: '1px solid #374151', padding: '10px 12px', borderRadius: '6px', cursor: 'grab', display: 'flex', alignItems: 'center', gap: '10px', transition: 'border 0.2s' }}
            onMouseOver={e => e.currentTarget.style.borderColor = '#10b981'}
            onMouseOut={e => e.currentTarget.style.borderColor = '#374151'}
          >
            <Link2 size={16} color="#10b981"/>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ color: '#e5e7eb', fontSize: '13px' }}>Skill Integration</span>
              <span style={{ color: '#6b7280', fontSize: '11px' }}>Execute deterministic task</span>
            </div>
          </div>
        </div>
      </section>

      {/* LOGIC & FORKS SECTION */}
      <section>
        <h3 style={{ color: '#fff', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '12px', opacity: 0.6 }}>Logic</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div 
            onDragStart={(event) => onDragStart(event, 'logicNode', { logicType: 'switch' })} 
            draggable 
            style={{ background: '#1e1e24', border: '1px solid #374151', padding: '10px 12px', borderRadius: '6px', cursor: 'grab', display: 'flex', alignItems: 'center', gap: '10px', transition: 'border 0.2s' }}
            onMouseOver={e => e.currentTarget.style.borderColor = '#f59e0b'}
            onMouseOut={e => e.currentTarget.style.borderColor = '#374151'}
          >
            <GitBranch size={16} color="#f59e0b"/>
            <span style={{ color: '#e5e7eb', fontSize: '13px' }}>Switch / Conditional</span>
          </div>
          <div 
            onDragStart={(event) => onDragStart(event, 'logicNode', { logicType: 'code' })} 
            draggable 
            style={{ background: '#1e1e24', border: '1px solid #374151', padding: '10px 12px', borderRadius: '6px', cursor: 'grab', display: 'flex', alignItems: 'center', gap: '10px', transition: 'border 0.2s' }}
            onMouseOver={e => e.currentTarget.style.borderColor = '#f59e0b'}
            onMouseOut={e => e.currentTarget.style.borderColor = '#374151'}
          >
            <Terminal size={16} color="#f59e0b"/>
            <span style={{ color: '#e5e7eb', fontSize: '13px' }}>Custom Snippet</span>
          </div>
        </div>
      </section>

    </div>
  );
}
