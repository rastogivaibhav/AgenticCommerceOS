import React, { useState, useCallback, useRef, useEffect } from 'react';
import ReactFlow, { 
  MiniMap, 
  Controls, 
  Background, 
  useNodesState, 
  useEdgesState, 
  addEdge,
  useReactFlow,
  ReactFlowProvider,
  MarkerType,
  Handle,
  Position
} from 'reactflow';
import 'reactflow/dist/style.css';
import { GitCommit, Settings, Link2, Wifi, Zap, Clock, GitBranch, Terminal } from 'lucide-react';
import NodeSidebar from './NodeSidebar';
import NodeConfigPanel from './NodeConfigPanel';

// --- CUSTOM NODE COMPONENTS ---
const TriggerNode = ({ data }) => (
  <div style={{ background: '#1e1e24', border: '1px solid #8b5cf6', borderRadius: '8px', padding: '12px', minWidth: '160px', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', transition: 'all 0.2s ease' }} className="hover:shadow-lg">
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ background: '#8b5cf6', padding: '4px', borderRadius: '4px', transition: 'all 0.2s ease' }}>
        {data.type === 'cron' ? <Clock size={14} color="#fff" /> : <Zap size={14} color="#fff" />}
      </div>
      <strong style={{ color: '#fff', fontSize: '13px' }}>{data.label || 'Trigger'}</strong>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const AgentNode = ({ data }) => (
  <div style={{ background: '#1e1e24', border: '1px solid #3b82f6', borderRadius: '8px', padding: '12px', minWidth: '180px', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', transition: 'all 0.2s ease' }} className="hover:shadow-lg">
    <Handle type="target" position={Position.Top} />
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ background: '#3b82f6', padding: '4px', borderRadius: '4px', transition: 'all 0.2s ease' }}>
        <Settings size={14} color="#fff" />
      </div>
      <div>
        <strong style={{ color: '#fff', fontSize: '13px', display: 'block' }}>{data.label || 'Agent'}</strong>
        <span style={{ color: '#9ca3af', fontSize: '11px' }}>{data.agentId ? `Bound: ${data.agentId}` : 'No agent bound'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const IntegrationNode = ({ data }) => (
  <div style={{ background: '#1e1e24', border: '1px solid #10b981', borderRadius: '8px', padding: '12px', minWidth: '180px', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', transition: 'all 0.2s ease' }} className="hover:shadow-lg">
    <Handle type="target" position={Position.Top} />
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ background: '#10b981', padding: '4px', borderRadius: '4px', transition: 'all 0.2s ease' }}>
        <Link2 size={14} color="#fff" />
      </div>
      <div>
        <strong style={{ color: '#fff', fontSize: '13px', display: 'block' }}>{data.label || 'Integration'}</strong>
        <span style={{ color: '#9ca3af', fontSize: '11px' }}>{data.skillId ? `API: ${data.skillId}` : 'No skill bound'}</span>
      </div>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const LogicNode = ({ data }) => (
  <div style={{ background: '#1e1e24', border: '1px solid #f59e0b', borderRadius: '8px', padding: '12px', minWidth: '160px', boxShadow: '0 4px 12px rgba(0,0,0,0.3)', transition: 'all 0.2s ease' }} className="hover:shadow-lg">
    <Handle type="target" position={Position.Top} />
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <div style={{ background: '#f59e0b', padding: '4px', borderRadius: '4px', transition: 'all 0.2s ease' }}>
        {data.logicType === 'code' ? <Terminal size={14} color="#fff" /> : <GitBranch size={14} color="#fff" />}
      </div>
      <strong style={{ color: '#fff', fontSize: '13px' }}>{data.label || 'Condition'}</strong>
    </div>
    <Handle type="source" position={Position.Bottom} />
  </div>
);

const nodeTypes = {
  triggerNode: TriggerNode,
  agentNode: AgentNode,
  integrationNode: IntegrationNode,
  logicNode: LogicNode
};

const initialNodes = [
  { id: 'start', type: 'triggerNode', data: { label: 'Webhook Trigger', type: 'webhook' }, position: { x: 250, y: 50 } },
  { id: 'agent-1', type: 'agentNode', data: { label: 'Order Triage', agentId: 'ag_order_triage' }, position: { x: 250, y: 150 } },
  { id: 'integ-1', type: 'integrationNode', data: { label: 'Validate Address', skillId: 'sk_address' }, position: { x: 250, y: 250 } },
];
const initialEdges = [
  { id: 'e1', source: 'start', target: 'agent-1', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
  { id: 'e2', source: 'agent-1', target: 'integ-1', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
];

// --- CORE ENGINE USING REACT FLOW HOOKS ---
const FlowEngine = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState(null);
  const reactFlowWrapper = useRef(null);
  
  const { screenToFlowPosition, toObject } = useReactFlow();

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow');
      const dataStr = event.dataTransfer.getData('application/json');
      
      if (!type) return;
      
      let payload = {};
      try { payload = JSON.parse(dataStr); } catch (e) {}

      // Flawless Geometry Mapping directly relative to reactflow canvas bound
      const position = screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });

      const newNode = {
        id: `node-${Date.now()}`,
        type,
        position,
        data: payload,
      };
      setNodes((nds) => nds.concat(newNode));
    },
    [screenToFlowPosition, setNodes]
  );

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  const handleNodeSave = (nodeId, newData) => {
    setNodes((nds) => nds.map((n) => (n.id === nodeId ? { ...n, data: newData } : n)));
    setSelectedNode((prev) => prev && prev.id === nodeId ? { ...prev, data: newData } : prev);
  };

  // Provide a global save handler for the parent WorkflowRegistry
  // This satisfies WE-04 for Serialization
  useEffect(() => {
    window.serializeWorkflowGraph = () => {
      return toObject();
    };
  }, [toObject]);

  return (
    <div className="animate-fadeInUp" style={{ width: '100%', height: '100%', display: 'flex', overflow: 'hidden' }}>
      <div className="hidden lg:block">
        <NodeSidebar />
      </div>

      <div style={{ flexGrow: 1, position: 'relative' }} ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-right"
        >
          <Background color="#333" gap={16} />
          <Controls />
        </ReactFlow>

        <NodeConfigPanel node={selectedNode} onClose={() => setSelectedNode(null)} onSave={handleNodeSave} />
      </div>
    </div>
  );
};

// --- EXPORTED WRAPPER ---
export default function WorkflowCanvas() {
  return (
    <ReactFlowProvider>
      <FlowEngine />
    </ReactFlowProvider>
  );
}
