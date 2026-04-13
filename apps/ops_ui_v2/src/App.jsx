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
import ApiToastHost from './components/ApiToastHost';
import './App.css';

function App() {
  return (
    <BrowserRouter basename="/ui/">
      <ApiToastHost />
      <Routes>
        <Route path="/" element={<Navigate to="/workflows" replace />} />
        <Route path="/workflows/:id/editor" element={<WorkflowEditor />} />
        <Route element={<Layout />}>
          <Route path="/workflows" element={<WorkflowRegistry />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/channels" element={<Channels />} />
          <Route path="/demo-routes" element={<DemoRoutes />} />
          <Route path="/tenants" element={<Tenants />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
