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
    background: 'rgba(255,255,255,0.98)',
    border: '1px solid #d7e0ea',
    borderRadius: '14px',
    boxShadow: '0 16px 32px rgba(15,23,42,0.16)',
    zIndex: 20,
    display: 'flex',
    flexDirection: 'column',
    animation: 'slideInRight 0.15s ease-out',
  };

  const inputStyle = {
    width: '100%',
    padding: '9px 10px',
    background: 'rgba(255,255,255,0.96)',
    border: '1px solid #cbd5e1',
    borderRadius: '8px',
    color: '#0f172a',
    fontSize: '12px',
    boxSizing: 'border-box',
  };

  const labelStyle = {
    display: 'block',
    fontSize: '11px',
    color: '#64748b',
    marginBottom: '5px',
    textTransform: 'uppercase',
    letterSpacing: '0.4px',
  };

  return (
    <div style={panelStyle}>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #d7e0ea', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: '#0f172a', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '7px' }}>
          <GitMerge size={14} color="#64748b" /> Edge Condition
        </h3>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer', padding: '2px' }}>
          <X size={16} />
        </button>
      </div>

      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div>
          <label style={labelStyle}>Connector Label</label>
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="e.g. on_success, if_score_high"
            style={inputStyle}
          />
        </div>

        <div style={{ borderTop: '1px solid #e2e8f0', paddingTop: '12px' }}>
          <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '10px', textTransform: 'uppercase', letterSpacing: '0.4px' }}>
            Condition Builder (optional)
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div>
              <label style={labelStyle}>Field</label>
              <input
                type="text"
                value={field}
                onChange={(e) => setField(e.target.value)}
                placeholder="e.g. score, status, output.type"
                style={inputStyle}
              />
            </div>

            <div>
              <label style={labelStyle}>Operator</label>
              <select value={operator} onChange={(e) => setOperator(e.target.value)} style={inputStyle}>
                {OPERATORS.map((op) => <option key={op} value={op}>{op}</option>)}
              </select>
            </div>

            <div>
              <label style={labelStyle}>Value</label>
              <input
                type="text"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="e.g. 0.8, placed, error"
                style={inputStyle}
              />
            </div>
          </div>
        </div>
      </div>

      <div style={{ padding: '12px 16px', borderTop: '1px solid #d7e0ea' }}>
        <button
          onClick={handleSave}
          style={{
            width: '100%',
            padding: '9px',
            background: 'linear-gradient(180deg, #2e6bde, #175cd3)',
            color: '#fff',
            border: 'none',
            borderRadius: '999px',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '7px',
            fontSize: '12px',
          }}
        >
          <Save size={13} /> Apply Condition
        </button>
      </div>
    </div>
  );
}
