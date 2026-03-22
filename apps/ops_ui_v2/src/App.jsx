import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Agents from './pages/Agents';
import Skills from './pages/Skills';
import WorkflowRegistry from './pages/WorkflowRegistry';
import Simulation from './pages/Simulation';
import Experiments from './pages/Experiments';
import './App.css';



function App() {
  return (
    <BrowserRouter basename="/ui/">
      <Routes>
        <Route path="/" element={<Navigate to="/agents" replace />} />
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
