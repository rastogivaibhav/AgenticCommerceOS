import React, { useState, useEffect } from 'react';
import { X, Save, Database, Key, Settings2 } from 'lucide-react';

export default function NodeConfigPanel({ node, onClose, onSave }) {
  const [formData, setFormData] = useState(node ? node.data : {});

  useEffect(() => {
    if (node) {
      setFormData(node.data);
    }
  }, [node]);

  if (!node) return null;

  const handleSave = () => {
    onSave(node.id, formData);
  };

  const handleChange = (key, value) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div style={{
      width: '320px',
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
      animation: 'slideInRight 0.2s ease-out'
    }}>
      <div style={{ padding: '16px 20px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: '#fff', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Settings2 size={16} /> Edit Node
        </h3>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#9ca3af', cursor: 'pointer' }}>
          <X size={18} />
        </button>
      </div>

      <div style={{ flexGrow: 1, overflowY: 'auto', padding: '20px' }}>
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#9ca3af', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Node ID</label>
          <div style={{ padding: '8px', background: 'rgba(255,255,255,0.03)', border: '1px dashed #374151', borderRadius: '4px', fontFamily: 'monospace', color: '#6b7280', fontSize: '12px' }}>
            {node.id}
          </div>
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#e5e7eb', marginBottom: '8px' }}>Label</label>
          <input 
            type="text" 
            value={formData.label || ''} 
            onChange={(e) => handleChange('label', e.target.value)}
            style={{ width: '100%', padding: '10px', background: '#1f2937', border: '1px solid #374151', borderRadius: '6px', color: '#fff' }}
          />
        </div>

        {/* Dynamic Fields based on Type */}
        {node.type === 'agentNode' && (
          <div style={{ background: 'rgba(59, 130, 246, 0.05)', border: '1px solid rgba(59, 130, 246, 0.2)', padding: '16px', borderRadius: '8px' }}>
            <h4 style={{ margin: '0 0 12px 0', color: '#3b82f6', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Database size={14}/> Runtime Parameters
            </h4>
            <label style={{ display: 'block', fontSize: '12px', color: '#e5e7eb', marginBottom: '8px' }}>Bind to Agent</label>
            <select 
              value={formData.agentId || ''} 
              onChange={(e) => handleChange('agentId', e.target.value)}
              style={{ width: '100%', padding: '10px', background: '#1f2937', border: '1px solid #374151', borderRadius: '6px', color: '#fff', marginBottom: '16px' }}
            >
              <option value="" disabled>Select System Agent</option>
              <option value="ag_order_triage">Order Triage</option>
              <option value="ag_support">L1 Support Bot</option>
              <option value="ag_refund">Refund Auto-Processor</option>
            </select>

            <label style={{ display: 'block', fontSize: '12px', color: '#e5e7eb', marginBottom: '8px' }}>Override System Prompt (Optional)</label>
            <textarea 
              rows={4}
              value={formData.systemPrompt || ''}
              onChange={(e) => handleChange('systemPrompt', e.target.value)}
              placeholder="Inject localized instructions..."
              style={{ width: '100%', padding: '10px', background: '#1f2937', border: '1px solid #374151', borderRadius: '6px', color: '#fff', resize: 'vertical' }}
            />
          </div>
        )}

        {node.type === 'integrationNode' && (
          <div style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '16px', borderRadius: '8px' }}>
            <h4 style={{ margin: '0 0 12px 0', color: '#10b981', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Key size={14}/> Resource Bindings
            </h4>
            <label style={{ display: 'block', fontSize: '12px', color: '#e5e7eb', marginBottom: '8px' }}>Bind Skill API</label>
            <select 
              value={formData.skillId || ''} 
              onChange={(e) => handleChange('skillId', e.target.value)}
              style={{ width: '100%', padding: '10px', background: '#1f2937', border: '1px solid #374151', borderRadius: '6px', color: '#fff', marginBottom: '16px' }}
            >
              <option value="" disabled>Select API Skill</option>
              <option value="sk_address">Validate Address (GET)</option>
              <option value="sk_refund">Process Stripe Refund (POST)</option>
            </select>
            
            <label style={{ display: 'block', fontSize: '12px', color: '#e5e7eb', marginBottom: '8px' }}>JSON Payload Template</label>
            <textarea 
              rows={4}
              value={formData.payloadTemplate || ''}
              onChange={(e) => handleChange('payloadTemplate', e.target.value)}
              placeholder="{'id': '{{input.id}}'}"
              style={{ width: '100%', padding: '10px', background: '#1f2937', border: '1px solid #374151', borderRadius: '6px', color: '#a78bfa', fontFamily: 'monospace', resize: 'vertical' }}
            />
          </div>
        )}
      </div>

      <div style={{ padding: '20px', borderTop: '1px solid #1f2937', background: 'rgba(0,0,0,0.2)' }}>
        <button 
          onClick={handleSave}
          style={{ width: '100%', padding: '12px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
        >
          <Save size={16} /> Save Node Configuration
        </button>
      </div>

    </div>
  );
}
