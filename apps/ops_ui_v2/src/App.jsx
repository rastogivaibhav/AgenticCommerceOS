import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Agents from './pages/Agents';
import Skills from './pages/Skills';
import WorkflowRegistry from './pages/WorkflowRegistry';
import WorkflowEditor from './pages/WorkflowEditor';
import Simulation from './pages/Simulation';
import Experiments from './pages/Experiments';
import Analytics from './pages/Analytics';
import Tenants from './pages/Tenants';
import ApiToastHost from './components/ApiToastHost';
import './App.css';



function App() {
  return (
    <BrowserRouter basename="/ui/">
      <ApiToastHost />
      <Routes>
        <Route path="/" element={<Navigate to="/agents" replace />} />
        {/* Full-screen editor — no sidebar layout */}
        <Route path="/workflows/:id/editor" element={<WorkflowEditor />} />
        <Route element={<Layout />}>
          <Route path="/agents" element={<Agents />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/workflows" element={<WorkflowRegistry />} />
          <Route path="/simulation" element={<Simulation />} />
          <Route path="/experiments" element={<Experiments />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/tenants" element={<Tenants />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
