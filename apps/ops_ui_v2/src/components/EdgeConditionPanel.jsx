import React, { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';

const inputStyle = {
  width: '100%', padding: '8px', background: '#1f2937',
  border: '1px solid #374151', borderRadius: '6px',
  color: '#fff', fontSize: '12px', boxSizing: 'border-box',
};

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
      label: label || undefined,
      condition: field ? { field, operator, value } : undefined,
    };
    onSave(edge.id, newData);
  };

  return (
    <div style={{
      position: 'absolute',
      left: Math.min(position.x, window.innerWidth - 280),
      top: position.y,
      width: 260,
      background: '#111318',
      border: '1px solid #1f2937',
      borderRadius: '8px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      zIndex: 20,
      padding: '14px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={{ fontSize: '12px', fontWeight: 600, color: '#f9fafb' }}>Edge Condition</span>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#6b7280', cursor: 'pointer' }}>
          <X size={15} />
        </button>
      </div>

      <div style={{ marginBottom: '10px' }}>
        <label style={{ display: 'block', fontSize: '10px', color: '#9ca3af', marginBottom: '4px', textTransform: 'uppercase' }}>
          Connector Label
        </label>
        <input
          type="text"
          value={label}
          onChange={e => setLabel(e.target.value)}
          placeholder="e.g. high score"
          style={inputStyle}
        />
      </div>

      <div style={{ marginBottom: '8px' }}>
        <label style={{ display: 'block', fontSize: '10px', color: '#9ca3af', marginBottom: '4px', textTransform: 'uppercase' }}>
          Condition Field
        </label>
        <input
          type="text"
          value={field}
          onChange={e => setField(e.target.value)}
          placeholder="e.g. score"
          style={inputStyle}
        />
      </div>

      <div style={{ display: 'flex', gap: '6px', marginBottom: '8px' }}>
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', fontSize: '10px', color: '#9ca3af', marginBottom: '4px', textTransform: 'uppercase' }}>
            Operator
          </label>
          <select value={operator} onChange={e => setOperator(e.target.value)} style={inputStyle}>
            {OPERATORS.map(op => <option key={op} value={op}>{op}</option>)}
          </select>
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ display: 'block', fontSize: '10px', color: '#9ca3af', marginBottom: '4px', textTransform: 'uppercase' }}>
            Value
          </label>
          <input
            type="text"
            value={value}
            onChange={e => setValue(e.target.value)}
            placeholder="e.g. 0.8"
            style={inputStyle}
          />
        </div>
      </div>

      <button
        onClick={handleSave}
        style={{
          width: '100%', padding: '8px', background: '#3b82f6',
          color: '#fff', border: 'none', borderRadius: '6px',
          fontWeight: 600, cursor: 'pointer', display: 'flex',
          alignItems: 'center', justifyContent: 'center', gap: '6px', fontSize: '12px',
        }}
      >
        <Save size={13} /> Save Condition
      </button>
    </div>
  );
}
