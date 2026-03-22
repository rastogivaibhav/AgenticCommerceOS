import { Outlet, NavLink } from 'react-router-dom';
import { Activity, Users, Wrench, GitMerge } from 'lucide-react';
import './Layout.css';

export default function Layout() {
  return (
    <div className="layout-container">
      <nav className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-logo">Δ</div>
          <span className="brand-text">ACOS</span>
        </div>
        
        <div className="sidebar-links">
          <NavLink to="/agents" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Users className="nav-icon" size={20} />
            Agents
          </NavLink>
          <NavLink to="/skills" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Wrench className="nav-icon" size={20} />
            Skills
          </NavLink>
          <NavLink to="/workflows" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <GitMerge className="nav-icon" size={20} />
            Workflows
          </NavLink>
          <NavLink to="/simulation" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <Activity className="nav-icon" size={20} />
            Simulation
          </NavLink>
        </div>
        
        <div className="sidebar-footer">
          <div className="ops-user">JLP Superadmin</div>
        </div>
      </nav>
      
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
