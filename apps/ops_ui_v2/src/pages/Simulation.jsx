import { useState, useCallback, useEffect } from 'react';
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Activity, PlayCircle } from 'lucide-react';
import Button from '../components/Button';
import { getNorthstarRuns, runNorthstarMessage } from '../api/northstarAPI';
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
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [runs, setRuns] = useState([]);
  const [status, setStatus] = useState('Loading captured run data...');

  const onConnect = useCallback((params) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  const loadRuns = useCallback(async () => {
    try {
      const payload = await getNorthstarRuns();
      setRuns(payload.runs || []);
      setStatus(`${payload.runs?.length || 0} captured north-star runs loaded`);
    } catch (error) {
      setStatus(error.message || 'Unable to load north-star runs');
    }
  }, []);

  const runGoldenJourney = useCallback(async () => {
    setStatus('Creating sample run...');
    try {
      await runNorthstarMessage({
        tenant_id: 'default',
        channel: 'web',
        channel_user_id: 'simulation-user',
        customer_id: 'simulation-customer',
        text: 'I need an outfit for a winter wedding under GBP200, available for pickup near Reading',
      });
      await loadRuns();
    } catch (error) {
      setStatus(error.message || 'Sample run failed');
    }
  }, [loadRuns]);

  // Animate the journey map to show active paths while recent runs are being observed.
  useEffect(() => {
    setEdges((eds) => eds.map((edge) => ({ ...edge, animated: true, style: { stroke: '#10b981', strokeWidth: 2 } })));
    loadRuns();
  }, [setEdges, loadRuns]);

  return (
    <div className="page-container simulation-view">
      <header className="page-header" style={{ paddingBottom: '16px', marginBottom: 0 }}>
        <div>
          <div className="eyebrow">Sandbox Mapping</div>
          <h1>Journey Planner & Run Monitor</h1>
          <p className="muted">Map orchestration paths and overlay recently captured run activity without implying live traffic.</p>
        </div>
        <div className="header-actions">
          <div className="mode-toggle">
            <button className="toggle-btn active live-active" type="button">
              <Activity size={16} /> Captured Runs
            </button>
          </div>
          <Button variant="outline" onClick={runGoldenJourney}>
            <PlayCircle size={16} /> Create sample run
          </Button>
        </div>
      </header>

      <div className="flow-container">
        <div className="live-overlay-banner">
          <span className="live-dot"></span> {status} | latest runs: {runs.length}
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
            nodeColor={(node) => {
              if (node.className === 'node-marketing') return '#ec4899';
              if (node.className === 'node-payment') return '#f59e0b';
              if (node.className === 'node-support') return '#6366f1';
              return '#10b981';
            }}
            maskColor="rgba(0,0,0,0.6)"
            position="top-right"
          />
        </ReactFlow>
      </div>
    </div>
  );
}
