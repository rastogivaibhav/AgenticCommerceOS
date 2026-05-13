import React, { useCallback, useEffect, useRef, useState } from 'react';
import ReactFlow, {
  Background,
  BaseEdge,
  Controls,
  EdgeLabelRenderer,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlowProvider,
  addEdge,
  getBezierPath,
  useEdgesState,
  useNodesState,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import {
  Bot,
  CheckCircle2,
  GitBranch,
  MessageSquare,
  PhoneCall,
  ShoppingBag,
  UserRound,
} from 'lucide-react';
import EdgeConditionPanel from './EdgeConditionPanel';
import NodeConfigPanel from './NodeConfigPanel';
import NodeSidebar from './NodeSidebar';

function paletteForNode(type, data = {}) {
  if (type === 'triggerNode') return { color: '#7c3aed', icon: <MessageSquare size={13} color="#fff" /> };
  if (type === 'agentNode') return { color: '#175cd3', icon: <Bot size={13} color="#fff" /> };
  if (type === 'decisionNode') return { color: '#d97706', icon: <GitBranch size={13} color="#fff" /> };
  if (type === 'humanNode') return { color: '#c2410c', icon: <UserRound size={13} color="#fff" /> };
  if (type === 'endNode') return { color: '#15803d', icon: <CheckCircle2 size={13} color="#fff" /> };
  if (data.connectorType === 'salesforce') return { color: '#0284c7', icon: <PhoneCall size={13} color="#fff" /> };
  if (data.connectorType === 'whatsapp') return { color: '#15803d', icon: <MessageSquare size={13} color="#fff" /> };
  return { color: '#0f766e', icon: <ShoppingBag size={13} color="#fff" /> };
}

function NodeWrap({ type, data }) {
  const { color, icon } = paletteForNode(type, data);
  const sublabelMap = {
    triggerNode: data.channel || data.triggerType,
    connectorNode: data.action || data.bindingId,
    agentNode: data.agentId ? `-> ${data.agentId}` : 'Unbound agent',
    decisionNode: data.routingRule || 'No rule',
    humanNode: data.queue || data.action,
    endNode: data.outcomeType || 'success',
  };

  return (
    <div
      style={{
        background: 'rgba(255,255,255,0.96)',
        border: `1.5px solid ${color}`,
        borderRadius: 14,
        padding: '12px 16px',
        minWidth: 190,
        boxShadow: '0 12px 24px rgba(15, 23, 42, 0.12)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div
          style={{
            background: color,
            padding: 6,
            borderRadius: 8,
            display: 'flex',
            flexShrink: 0,
          }}
        >
          {icon}
        </div>
        <div>
          <strong style={{ color: '#0f172a', fontSize: 13, display: 'block', lineHeight: 1.3 }}>
            {data.label || 'Untitled Step'}
          </strong>
          <span style={{ color: '#64748b', fontSize: 11 }}>{sublabelMap[type] || 'Unconfigured'}</span>
        </div>
      </div>
    </div>
  );
}

const TriggerNode = ({ data }) => (
  <>
    <NodeWrap type="triggerNode" data={data} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#7c3aed' }} />
  </>
);

const ConnectorNode = ({ data }) => {
  const color = paletteForNode('connectorNode', data).color;
  return (
    <>
      <Handle type="target" position={Position.Top} style={{ background: color }} />
      <NodeWrap type="connectorNode" data={data} />
      <Handle type="source" position={Position.Bottom} style={{ background: color }} />
    </>
  );
};

const AgentNode = ({ data }) => (
  <>
    <Handle type="target" position={Position.Top} style={{ background: '#175cd3' }} />
    <NodeWrap type="agentNode" data={data} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#175cd3' }} />
  </>
);

const DecisionNode = ({ data }) => (
  <>
    <Handle type="target" position={Position.Top} style={{ background: '#d97706' }} />
    <NodeWrap type="decisionNode" data={data} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#d97706' }} />
  </>
);

const HumanNode = ({ data }) => (
  <>
    <Handle type="target" position={Position.Top} style={{ background: '#c2410c' }} />
    <NodeWrap type="humanNode" data={data} />
    <Handle type="source" position={Position.Bottom} style={{ background: '#c2410c' }} />
  </>
);

const EndNode = ({ data }) => (
  <>
    <Handle type="target" position={Position.Top} style={{ background: '#15803d' }} />
    <NodeWrap type="endNode" data={data} />
  </>
);

const nodeTypes = {
  triggerNode: TriggerNode,
  connectorNode: ConnectorNode,
  agentNode: AgentNode,
  decisionNode: DecisionNode,
  humanNode: HumanNode,
  endNode: EndNode,
};

const ConditionEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
  style,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge id={id} path={edgePath} markerEnd={markerEnd} style={{ ...style, stroke: '#64748b', strokeWidth: 1.6 }} />
      {data?.label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
              background: 'rgba(255,255,255,0.96)',
              border: '1px solid #cbd5e1',
              borderRadius: 999,
              padding: '3px 9px',
              fontSize: 11,
              color: '#334155',
              fontFamily: 'IBM Plex Mono, monospace',
              whiteSpace: 'nowrap',
              zIndex: 5,
              boxShadow: '0 8px 18px rgba(15, 23, 42, 0.08)',
            }}
            className="nodrag nopan"
          >
            {data.label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
};

const edgeTypes = { conditionEdge: ConditionEdge };

const STARTER_GRAPH = {
  nodes: [
    {
      id: 'trigger-1',
      type: 'triggerNode',
      position: { x: 280, y: 80 },
      data: {
        label: 'WhatsApp Inbound',
        channel: 'whatsapp',
        triggerType: 'inbound_message',
        bindingId: 'whatsapp-support',
      },
    },
    {
      id: 'agent-1',
      type: 'agentNode',
      position: { x: 280, y: 240 },
      data: {
        label: 'Support Agent',
        agentId: 'ag_support_l1',
      },
    },
    {
      id: 'end-1',
      type: 'endNode',
      position: { x: 280, y: 400 },
      data: {
        label: 'Resolved',
        outcomeType: 'success',
      },
    },
  ],
  edges: [
    {
      id: 'edge-trigger-agent',
      source: 'trigger-1',
      target: 'agent-1',
      type: 'conditionEdge',
      markerEnd: { type: MarkerType.ArrowClosed },
      data: {},
    },
    {
      id: 'edge-agent-end',
      source: 'agent-1',
      target: 'end-1',
      type: 'conditionEdge',
      markerEnd: { type: MarkerType.ArrowClosed },
      data: {},
    },
  ],
};

function normalizeLegacyNode(node) {
  const typeMap = {
    startNode: 'triggerNode',
    triggerNode: 'triggerNode',
    orchestratorNode: 'agentNode',
    agentNode: 'agentNode',
    subAgentNode: 'agentNode',
    integrationNode: 'connectorNode',
    logicNode: 'decisionNode',
    decisionNode: 'decisionNode',
    humanNode: 'humanNode',
    connectorNode: 'connectorNode',
    endNode: 'endNode',
  };
  const nextType = typeMap[node.type] || 'agentNode';
  const data = { ...(node.data || {}) };

  if (nextType === 'triggerNode') {
    data.channel = data.channel || (data.type === 'webhook' ? 'webhook' : 'api');
    data.triggerType = data.triggerType || data.type || 'manual';
  }
  if (nextType === 'connectorNode') {
    data.connectorType = data.connectorType || 'commerce';
    data.bindingId = data.bindingId || data.skillId || '';
    data.action = data.action || (data.skillId ? 'manual_review' : 'lookup_policy');
  }
  if (nextType === 'decisionNode') {
    data.routingRule = data.routingRule || data.logicType || 'true';
  }
  if (nextType === 'agentNode') {
    data.agentId = data.agentId || '';
  }

  return {
    ...node,
    type: nextType,
    data,
  };
}

function resolveGraph(initialGraph) {
  if (initialGraph?.nodes?.length) {
    return {
      nodes: initialGraph.nodes.map(normalizeLegacyNode),
      edges: initialGraph.edges ?? [],
    };
  }
  return STARTER_GRAPH;
}

function FlowEngine({ initialGraph, onGraphChange }) {
  const { nodes: seedNodes, edges: seedEdges } = resolveGraph(initialGraph);
  const [nodes, setNodes, onNodesChange] = useNodesState(seedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(seedEdges);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [edgePanelPos, setEdgePanelPos] = useState({ x: 0, y: 0 });
  const reactFlowWrapper = useRef(null);
  const { screenToFlowPosition, toObject } = useReactFlow();

  const onConnect = useCallback(
    (params) => {
      setEdges((existing) =>
        addEdge(
          {
            ...params,
            type: 'conditionEdge',
            animated: false,
            markerEnd: { type: MarkerType.ArrowClosed },
            data: {},
          },
          existing,
        ),
      );
    },
    [setEdges],
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow');
      const dataString = event.dataTransfer.getData('application/json');
      if (!type) return;

      let payload = {};
      try {
        payload = JSON.parse(dataString);
      } catch (error) {
        console.error('Failed to parse dropped node payload:', error);
      }

      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
      setNodes((existing) =>
        existing.concat({ id: `node-${Date.now()}`, type, position, data: payload }),
      );
    },
    [screenToFlowPosition, setNodes],
  );

  const handleNodeSave = (nodeId, newData) => {
    setNodes((existing) => existing.map((node) => (node.id === nodeId ? { ...node, data: newData } : node)));
    setSelectedNode((current) => (current?.id === nodeId ? { ...current, data: newData } : current));
  };

  const handleEdgeSave = (edgeId, newData) => {
    setEdges((existing) => existing.map((edge) => (edge.id === edgeId ? { ...edge, data: newData } : edge)));
    setSelectedEdge(null);
  };

  useEffect(() => {
    if (!onGraphChange) return;
    onGraphChange(toObject());
  }, [nodes, edges, onGraphChange, toObject]);

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', overflow: 'hidden' }}>
      <NodeSidebar />

      <div style={{ flexGrow: 1, position: 'relative', background: 'linear-gradient(180deg, #f8fbff, #f2f6fb)' }} ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={(_, node) => {
            setSelectedNode(node);
            setSelectedEdge(null);
          }}
          onEdgeClick={(event, edge) => {
            setSelectedEdge(edge);
            setSelectedNode(null);
            const rect = reactFlowWrapper.current?.getBoundingClientRect() || { left: 0, top: 0 };
            setEdgePanelPos({ x: event.clientX - rect.left, y: event.clientY - rect.top });
          }}
          onPaneClick={() => {
            setSelectedNode(null);
            setSelectedEdge(null);
          }}
          onDrop={onDrop}
          onDragOver={onDragOver}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          deleteKeyCode={['Delete', 'Backspace']}
          fitView
          attributionPosition="bottom-right"
        >
          <Background color="#d7e0ea" gap={18} />
          <Controls />
          <MiniMap
            nodeColor={(node) => paletteForNode(node.type, node.data).color}
            style={{ background: 'rgba(255,255,255,0.94)', border: '1px solid #d7e0ea' }}
          />
        </ReactFlow>

        <NodeConfigPanel
          key={selectedNode?.id || 'node-config'}
          node={selectedNode}
          onClose={() => setSelectedNode(null)}
          onSave={handleNodeSave}
        />

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
}

export default function WorkflowCanvas({ initialGraph, onGraphChange }) {
  return (
    <ReactFlowProvider>
      <FlowEngine initialGraph={initialGraph} onGraphChange={onGraphChange} />
    </ReactFlowProvider>
  );
}
