import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import Agents from './pages/Agents';
import Skills from './pages/Skills';
import WorkflowRegistry from './pages/WorkflowRegistry';
import WorkflowEditor from './pages/WorkflowEditor';
import Analytics from './pages/Analytics';
import Tenants from './pages/Tenants';
import Channels from './pages/Channels';
import DemoRoutes from './pages/DemoRoutes';
import StudioProof from './pages/StudioProof';
import DemoGuide from './pages/DemoGuide';
import TestCenter from './pages/TestCenter';
import Runs from './pages/Runs';
import APIPlane from './pages/APIPlane';
import Experiments from './pages/Experiments';
import Simulation from './pages/Simulation';
import ApiToastHost from './components/ApiToastHost';
import V2EstateDashboard from './pages/V2EstateDashboard';
import V2AgentRegistry from './pages/V2AgentRegistry';
import V2AgentDetail from './pages/V2AgentDetail';
import V2Capabilities from './pages/V2Capabilities';
import V2A2ATrace from './pages/V2A2ATrace';
import V2ChannelModes from './pages/V2ChannelModes';
import V2Evaluation from './pages/V2Evaluation';
import V2Governance from './pages/V2Governance';
import V2RouteToProduction from './pages/V2RouteToProduction';
import V2FinOps from './pages/V2FinOps';
import V2Tone from './pages/V2Tone';
import V2Memory from './pages/V2Memory';
import V2ToolRegistry from './pages/V2ToolRegistry';
import './App.css';

function App() {
  return (
    <BrowserRouter basename="/ui/">
      <ApiToastHost />
      <Routes>
        <Route path="/" element={<Navigate to="/workflows" replace />} />
        <Route path="/workflows/:id/editor" element={<WorkflowEditor />} />
        <Route element={<Layout />}>
          <Route path="/estate" element={<V2EstateDashboard />} />
          <Route path="/agent-registry" element={<V2AgentRegistry />} />
          <Route path="/agent-detail/:id" element={<V2AgentDetail />} />
          <Route path="/capabilities" element={<V2Capabilities />} />
          <Route path="/a2a-trace" element={<V2A2ATrace />} />
          <Route path="/channel-modes" element={<V2ChannelModes />} />
          <Route path="/evaluations" element={<V2Evaluation />} />
          <Route path="/governance" element={<V2Governance />} />
          <Route path="/tool-registry" element={<V2ToolRegistry />} />
          <Route path="/memory" element={<V2Memory />} />
          <Route path="/tone" element={<V2Tone />} />
          <Route path="/finops" element={<V2FinOps />} />
          <Route path="/route-to-production" element={<V2RouteToProduction />} />
          <Route path="/workflows" element={<WorkflowRegistry />} />
          <Route path="/studio-proof" element={<StudioProof />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/demo-guide" element={<DemoGuide />} />
          <Route path="/test-center" element={<TestCenter />} />
          <Route path="/api-plane" element={<APIPlane />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/experiments" element={<Experiments />} />
          <Route path="/simulation" element={<Simulation />} />
          <Route path="/channels" element={<Channels />} />
          <Route path="/demo-routes" element={<DemoRoutes />} />
          <Route path="/tenants" element={<Tenants />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
