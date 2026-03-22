import { useState, useCallback, useEffect } from 'react';
import ReactFlow, { 
  MiniMap, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState, 
  addEdge,
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Activity, GitCommit } from 'lucide-react';
import './Simulation.css';

const initialNodes = [
  { id: '1', type: 'input', data: { label: 'Marketing (Acquisition)' }, position: { x: 50, y: 150 }, className: 'node-marketing' },
  { id: '2', data: { label: 'Discovery (Search/Browse)' }, position: { x: 300, y: 150 }, className: 'node-core' },
  { id: '3', data: { label: 'Purchase (Checkout)' }, position: { x: 550, y: 150 }, className: 'node-payment' },
  { id: '4', data: { label: 'Fulfillment' }, position: { x: 800, y: 50 }, className: 'node-core' },
  { id: '5', data: { label: 'Customer Service' }, position: { x: 800, y: 250 }, className: 'node-support' },
];

const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: false, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e2-3', source: '2', target: '3', animated: false, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e3-4', source: '3', target: '4', animated: false, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e3-5', source: '3', target: '5', animated: false, markerEnd: { type: MarkerType.ArrowClosed } },
];

export default function Simulation() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  // Handle live traffic mode animation constantly
  useEffect(() => {
    setEdges((eds) => eds.map(e => ({ ...e, animated: true, style: { stroke: '#10b981', strokeWidth: 2 } })));
  }, [setEdges]);

  return (
    <div className="page-container simulation-view">
      <header className="page-header" style={{ paddingBottom: '16px', marginBottom: 0 }}>
        <div>
          <div className="eyebrow">ACOS Runtime</div>
          <h1>Journey Planner & Simulation</h1>
          <p className="muted">Map out agent orchestration paths and observe live system traffic.</p>
        </div>
        <div className="header-actions">
          <div className="mode-toggle">
            <button className="toggle-btn active live-active">
              <Activity size={16}/> Live Traffic
            </button>
          </div>
        </div>
      </header>

      <div className="flow-container">
        <div className="live-overlay-banner">
          <span className="live-dot"></span> Live execution traffic flowing...
        </div>
        
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          attributionPosition="bottom-right"
        >
          <Background color="#555" gap={16} />
          <Controls />
          <MiniMap 
            nodeColor={(n) => {
              if (n.className === 'node-marketing') return '#ec4899';
              if (n.className === 'node-payment') return '#f59e0b';
              if (n.className === 'node-support') return '#6366f1';
              return '#10b981';
            }} 
            maskColor="rgba(0,0,0,0.6)" 
          />
        </ReactFlow>
      </div>
    </div>
  );
}
