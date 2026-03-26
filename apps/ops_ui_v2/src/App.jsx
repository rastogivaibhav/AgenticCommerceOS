import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Agents from './pages/Agents';
import Skills from './pages/Skills';
import WorkflowRegistry from './pages/WorkflowRegistry';
import WorkflowEditor from './pages/WorkflowEditor';
import Simulation from './pages/Simulation';
import Experiments from './pages/Experiments';
import './App.css';



function App() {
  return (
    <BrowserRouter basename="/ui/">
      <Routes>
        <Route path="/" element={<Navigate to="/agents" replace />} />
        {/* Full-screen editor — outside Layout (no sidebar) */}
        <Route path="/workflows/:id/editor" element={<WorkflowEditor />} />
        <Route element={<Layout />}>
          <Route path="/agents" element={<Agents />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/workflows" element={<WorkflowRegistry />} />
          <Route path="/simulation" element={<Simulation />} />
          <Route path="/experiments" element={<Experiments />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
