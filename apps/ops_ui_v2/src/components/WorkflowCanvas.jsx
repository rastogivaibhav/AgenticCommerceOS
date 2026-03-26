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
  Position,
  getBezierPath,
  EdgeLabelRenderer,
  BaseEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  PlayCircle, StopCircle, Cpu, Settings, Link2, Zap, Clock,
  GitBranch, Terminal, Users
} from 'lucide-react';
import NodeSidebar from './NodeSidebar';
import NodeConfigPanel from './NodeConfigPanel';
import EdgeConditionPanel from './EdgeConditionPanel';

// ─── SHARED NODE WRAPPER ──────────────────────────────────────────────────────
function NodeWrap({ color, icon, label, sublabel }) {
  return (
    <div style={{
      background: '#1a1d23', border: `1.5px solid ${color}`,
      borderRadius: '10px', padding: '12px 16px', minWidth: '170px',
      boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>
        <div style={{ background: color, padding: '5px', borderRadius: '6px', display: 'flex', flexShrink: 0 }}>
          {icon}
        </div>
        <div>
          <strong style={{ color: '#f9fafb', fontSize: '13px', display: 'block', lineHeight: '1.3' }}>{label}</strong>
          {sublabel && <span style={{ color: '#6b7280', fontSize: '11px' }}>{sublabel}</span>}
        </div>
      </div>
    </div>
  );
}

// ─── NODE TYPES ───────────────────────────────────────────────────────────────
const StartNode = ({ data }) => (
  <>
    <NodeWrap color="#22c55e" icon={<PlayCircle size={13} color="#fff" />} label={data.label || 'Start'} sublabel={data.triggerType || 'manual'} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#22c55e' }} />
  </>
);

const EndNode = ({ data }) => (
  <>
    <Handle type="target" position={Position.Top} style={{ background: '#ef4444' }} />
    <NodeWrap color="#ef4444" icon={<StopCircle size={13} color="#fff" />} label={data.label || 'End'} sublabel={data.outcomeType || 'success'} />
  </>
);

const OrchestratorNode = ({ data }) => (
  <>
    <Handle type="target" position={Position.Top} style={{ background: '#a855f7' }} />
    <NodeWrap color="#a855f7" icon={<Cpu size={13} color="#fff" />} label={data.label || 'Orchestrator'} sublabel={data.agentId ? `→ ${data.agentId}` : 'Unbound'} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#a855f7' }} />
  </>
);

const AgentNode = ({ data }) => (
  <>
    <Handle type="target" position={Position.Top} style={{ background: '#3b82f6' }} />
    <NodeWrap color="#3b82f6" icon={<Settings size={13} color="#fff" />} label={data.label || 'Agent'} sublabel={data.agentId ? `→ ${data.agentId}` : 'No agent bound'} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#3b82f6' }} />
  </>
);

const SubAgentNode = ({ data }) => (
  <>
    <Handle type="target" position={Position.Top} style={{ background: '#06b6d4' }} />
    <NodeWrap color="#06b6d4" icon={<Users size={13} color="#fff" />} label={data.label || 'Sub-Agent'} sublabel={data.agentId ? `→ ${data.agentId}` : 'Unbound'} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#06b6d4' }} />
  </>
);

const TriggerNode = ({ data }) => (
  <>
    <NodeWrap color="#8b5cf6" icon={data.type === 'cron' ? <Clock size={13} color="#fff" /> : <Zap size={13} color="#fff" />} label={data.label || 'Trigger'} sublabel={data.type} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#8b5cf6' }} />
  </>
);

const IntegrationNode = ({ data }) => (
  <>
    <Handle type="target" position={Position.Top} style={{ background: '#10b981' }} />
    <NodeWrap color="#10b981" icon={<Link2 size={13} color="#fff" />} label={data.label || 'Integration'} sublabel={data.skillId ? `API: ${data.skillId}` : 'No skill bound'} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#10b981' }} />
  </>
);

const LogicNode = ({ data }) => (
  <>
    <Handle type="target" position={Position.Top} style={{ background: '#f59e0b' }} />
    <NodeWrap color="#f59e0b" icon={data.logicType === 'code' ? <Terminal size={13} color="#fff" /> : <GitBranch size={13} color="#fff" />} label={data.label || 'Condition'} sublabel={data.logicType} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#f59e0b' }} />
  </>
);

const nodeTypes = {
  startNode: StartNode,
  endNode: EndNode,
  orchestratorNode: OrchestratorNode,
  agentNode: AgentNode,
  subAgentNode: SubAgentNode,
  triggerNode: TriggerNode,
  integrationNode: IntegrationNode,
  logicNode: LogicNode,
};

// ─── CONDITION EDGE ───────────────────────────────────────────────────────────
const ConditionEdge = ({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data, markerEnd, style }) => {
  const [edgePath, labelX, labelY] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
  const label = data?.label;
  return (
    <>
      <BaseEdge id={id} path={edgePath} markerEnd={markerEnd} style={style} />
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
              background: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '4px',
              padding: '2px 8px',
              fontSize: '11px',
              color: '#d1d5db',
              fontFamily: 'monospace',
              whiteSpace: 'nowrap',
              zIndex: 5,
            }}
            className="nodrag nopan"
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};

const edgeTypes = { conditionEdge: ConditionEdge };

// ─── STARTER GRAPH (new / blank workflows) ────────────────────────────────────
const STARTER_NODES = [
  { id: 'start-1', type: 'startNode', data: { label: 'Start', triggerType: 'manual' }, position: { x: 300, y: 80 } },
  { id: 'end-1',   type: 'endNode',   data: { label: 'End',   outcomeType: 'success' }, position: { x: 300, y: 240 } },
];
const STARTER_EDGES = [
  { id: 'e-s-e', source: 'start-1', target: 'end-1', type: 'conditionEdge', animated: true, markerEnd: { type: MarkerType.ArrowClosed }, data: {} },
];

function resolveGraph(initialGraph) {
  if (initialGraph?.nodes?.length) {
    return { nodes: initialGraph.nodes, edges: initialGraph.edges ?? [] };
  }
  return { nodes: STARTER_NODES, edges: STARTER_EDGES };
}

// ─── FLOW ENGINE ─────────────────────────────────────────────────────────────
const FlowEngine = ({ initialGraph }) => {
  const { nodes: seedNodes, edges: seedEdges } = resolveGraph(initialGraph);
  const [nodes, setNodes, onNodesChange] = useNodesState(seedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(seedEdges);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [edgePanelPos, setEdgePanelPos] = useState({ x: 0, y: 0 });
  const reactFlowWrapper = useRef(null);
  const { screenToFlowPosition, toObject } = useReactFlow();

  const onConnect = useCallback((params) => {
    setEdges((eds) => addEdge({
      ...params,
      type: 'conditionEdge',
      animated: false,
      markerEnd: { type: MarkerType.ArrowClosed },
      data: {},
    }, eds));
  }, [setEdges]);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback((event) => {
    event.preventDefault();
    const type = event.dataTransfer.getData('application/reactflow');
    const dataStr = event.dataTransfer.getData('application/json');
    if (!type) return;
    let payload = {};
    try { payload = JSON.parse(dataStr); } catch (_) {}
    const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
    setNodes((nds) => nds.concat({ id: `node-${Date.now()}`, type, position, data: payload }));
  }, [screenToFlowPosition, setNodes]);

  const onNodeClick = useCallback((_, node) => {
    setSelectedNode(node);
    setSelectedEdge(null);
  }, []);

  const onEdgeClick = useCallback((event, edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
    const rect = reactFlowWrapper.current?.getBoundingClientRect() || { left: 0, top: 0 };
    setEdgePanelPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setSelectedEdge(null);
  }, []);

  const handleNodeSave = (nodeId, newData) => {
    setNodes((nds) => nds.map((n) => (n.id === nodeId ? { ...n, data: newData } : n)));
    setSelectedNode((prev) => prev?.id === nodeId ? { ...prev, data: newData } : prev);
  };

  const handleEdgeSave = (edgeId, newData) => {
    setEdges((eds) => eds.map((e) => (e.id === edgeId ? { ...e, data: newData } : e)));
    setSelectedEdge(null);
  };

  useEffect(() => {
    window.serializeWorkflowGraph = () => toObject();
  }, [toObject]);

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', overflow: 'hidden' }}>
      <NodeSidebar />

      <div style={{ flexGrow: 1, position: 'relative' }} ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onEdgeClick={onEdgeClick}
          onPaneClick={onPaneClick}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          deleteKeyCode={['Delete', 'Backspace']}
          fitView
          attributionPosition="bottom-right"
        >
          <Background color="#222" gap={18} />
          <Controls />
          <MiniMap
            nodeColor={(n) => {
              const m = { startNode: '#22c55e', endNode: '#ef4444', orchestratorNode: '#a855f7', agentNode: '#3b82f6', subAgentNode: '#06b6d4', triggerNode: '#8b5cf6', integrationNode: '#10b981', logicNode: '#f59e0b' };
              return m[n.type] || '#374151';
            }}
            style={{ background: '#111318' }}
          />
        </ReactFlow>

        <NodeConfigPanel node={selectedNode} onClose={() => setSelectedNode(null)} onSave={handleNodeSave} />

        {selectedEdge && (
          <EdgeConditionPanel
            edge={selectedEdge}
            position={edgePanelPos}
            onClose={() => setSelectedEdge(null)}
            onSave={handleEdgeSave}
          />
        )}
      </div>
    </div>
  );
};

// ─── EXPORTED WRAPPER ─────────────────────────────────────────────────────────
export default function WorkflowCanvas({ initialGraph }) {
  return (
    <ReactFlowProvider>
      <FlowEngine initialGraph={initialGraph} />
    </ReactFlowProvider>
  );
}
