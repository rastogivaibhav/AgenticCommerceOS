import React, { useState, useEffect } from 'react';
import { X, Save, GitMerge } from 'lucide-react';

const OPERATORS = ['==', '!=', '>', '>=', '<', '<=', 'contains', 'not_contains'];

export default function EdgeConditionPanel({ edge, position, onClose, onSave }) {
  const [label, setLabel] = useState('');
  const [field, setField] = useState('');
  const [operator, setOperator] = useState('==');
  const [value, setValue] = useState('');

  useEffect(() => {
    if (edge) {
      setLabel(edge.data?.label || '');
      setField(edge.data?.condition?.field || '');
      setOperator(edge.data?.condition?.operator || '==');
      setValue(edge.data?.condition?.value || '');
    }
  }, [edge]);

  if (!edge) return null;

  const handleSave = () => {
    const newData = {
      label: label || (field ? `${field} ${operator} ${value}` : ''),
      condition: field ? { field, operator, value } : null,
    };
    onSave(edge.id, newData);
  };

  const panelStyle = {
    position: 'absolute',
    left: Math.min(position.x, window.innerWidth - 340),
    top: Math.max(position.y - 20, 8),
    width: '300px',
    background: '#111318',
    border: '1px solid #1f2937',
    borderRadius: '10px',
    boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
    zIndex: 20,
    display: 'flex',
    flexDirection: 'column',
    animation: 'slideInRight 0.15s ease-out',
  };

  const inputStyle = {
    width: '100%',
    padding: '8px 10px',
    background: '#1f2937',
    border: '1px solid #374151',
    borderRadius: '6px',
    color: '#fff',
    fontSize: '12px',
    boxSizing: 'border-box',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '11px',
    color: '#9ca3af',
    marginBottom: '5px',
    textTransform: 'uppercase',
    letterSpacing: '0.4px',
  };

  return (
    <div style={panelStyle}>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #1f2937', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: '#fff', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '7px' }}>
          <GitMerge size={14} color="#6b7280" /> Edge Condition
        </h3>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#6b7280', cursor: 'pointer', padding: '2px' }}>
          <X size={16} />
        </button>
      </div>

      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div>
          <label style={labelStyle}>Connector Label</label>
          <input
            type="text"
            value={label}
            onChange={e => setLabel(e.target.value)}
            placeholder="e.g. on_success, if_score_high"
            style={inputStyle}
          />
        </div>

        <div style={{ borderTop: '1px solid #1f2937', paddingTop: '12px' }}>
          <div style={{ fontSize: '11px', color: '#6b7280', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
            Condition Builder (optional)
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div>
              <label style={labelStyle}>Field</label>
              <input
                type="text"
                value={field}
                onChange={e => setField(e.target.value)}
                placeholder="e.g. score, status, output.type"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle}>Operator</label>
              <select value={operator} onChange={e => setOperator(e.target.value)} style={inputStyle}>
                {OPERATORS.map(op => <option key={op} value={op}>{op}</option>)}
              </select>
            </div>

            <div>
              <label style={labelStyle}>Value</label>
              <input
                type="text"
                value={value}
                onChange={e => setValue(e.target.value)}
                placeholder="e.g. 0.8, placed, error"
                style={inputStyle}
              />
            </div>
          </div>
        </div>
      </div>

      <div style={{ padding: '12px 16px', borderTop: '1px solid #1f2937' }}>
        <button
          onClick={handleSave}
          style={{
            width: '100%', padding: '9px', background: '#3b82f6', color: '#fff',
            border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '7px',
            fontSize: '12px',
          }}
        >
          <Save size={13} /> Apply Condition
        </button>
      </div>
    </div>
  );
}
