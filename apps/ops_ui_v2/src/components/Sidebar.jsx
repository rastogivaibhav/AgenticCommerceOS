import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Users, Wrench, GitMerge, BarChart2, Building2, MessageSquareText, Route, X, MonitorCheck, BookOpenCheck, FlaskConical, Activity, Cable, Beaker, Workflow, Network, LibraryBig, Shield, ListChecks, Database, Palette, Coins, Rocket } from 'lucide-react';

const navSections = [
  {
    title: 'Ops',
    items: [
      { path: '/workflows', label: 'Flows', icon: GitMerge },
      { path: '/runs', label: 'Runs', icon: Activity },
      { path: '/channels', label: 'Channels', icon: MessageSquareText },
      { path: '/analytics', label: 'Metrics', icon: BarChart2 },
      { path: '/tenants', label: 'Tenants', icon: Building2 },
    ],
  },
  {
    title: 'Sandbox',
    items: [
      { path: '/demo-routes', label: 'Routes', icon: Route },
      { path: '/simulation', label: 'Map', icon: Workflow },
      { path: '/studio-proof', label: 'Proof', icon: MonitorCheck },
      { path: '/test-center', label: 'Tests', icon: FlaskConical },
      { path: '/demo-guide', label: 'Guide', icon: BookOpenCheck },
      { path: '/api-plane', label: 'APIs', icon: Cable },
      { path: '/experiments', label: 'Labs', icon: Beaker },
    ],
  },
  {
    title: 'Platform',
    items: [
      { path: '/estate', label: 'Estate', icon: Network },
      { path: '/agent-registry', label: 'Registry', icon: LibraryBig },
      { path: '/capabilities', label: 'Caps', icon: ListChecks },
      { path: '/a2a-trace', label: 'A2A', icon: GitMerge },
      { path: '/channel-modes', label: 'Modes', icon: MessageSquareText },
      { path: '/evaluations', label: 'Eval', icon: Beaker },
      { path: '/governance', label: 'Policy', icon: Shield },
      { path: '/tool-registry', label: 'Tools', icon: Wrench },
      { path: '/memory', label: 'Memory', icon: Database },
      { path: '/tone', label: 'Tone', icon: Palette },
      { path: '/finops', label: 'FinOps', icon: Coins },
      { path: '/route-to-production', label: 'Launch', icon: Rocket },
      { path: '/agents', label: 'Agents', icon: Users },
      { path: '/skills', label: 'Skills', icon: Wrench },
    ],
  },
];

function RailLinks({ onClose }) {
  return (
    <nav aria-label="Main navigation" className="flex flex-col items-center gap-3 py-2 w-full">
      {navSections.map((section) => (
        <div key={section.title} className="flex w-full flex-col items-center gap-1">
          <span className="text-[10px] uppercase tracking-[0.18em] text-on-surface-variant/70">
            {section.title}
          </span>
          {section.items.map((item) => {
            const IconComponent = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                title={`${section.title}: ${item.label}`}
                className={({ isActive }) =>
                  `flex flex-col items-center gap-1 w-16 py-2 rounded-2xl transition-colors ${
                    isActive
                      ? 'bg-secondary-container text-primary'
                      : 'text-on-surface-variant hover:bg-surface-variant'
                  }`
                }
              >
                <div className="w-10 h-7 flex items-center justify-center rounded-2xl">
                  <IconComponent size={20} />
                </div>
                <span className="text-[11px] font-medium leading-none">{item.label}</span>
              </NavLink>
            );
          })}
        </div>
      ))}
    </nav>
  );
}

export default function Sidebar({ isOpen, onClose }) {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <>
      {/* Desktop Navigation Rail */}
      <aside className="sidebar-desktop bg-surface-container-high border-r border-outline-variant">
        <RailLinks onClose={onClose} />
      </aside>

      {/* Mobile overlay drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={onClose} />
          <aside className="absolute inset-y-0 left-0 w-64 bg-surface-container flex flex-col border-r border-outline-variant">
            <div className="p-4 flex items-center justify-between border-b border-outline-variant">
              <h2 className="font-medium text-on-surface">Menu</h2>
              <button
                onClick={onClose}
                aria-label="Close menu"
                className="p-2 hover:bg-surface-variant rounded-full transition-colors text-on-surface"
              >
                <X size={20} />
              </button>
            </div>
            <nav aria-label="Main navigation" className="p-2 flex flex-col gap-1">
              {navSections.map((section) => (
                <div key={section.title} className="flex flex-col gap-1">
                  <div className="px-4 pt-3 text-[11px] uppercase tracking-[0.18em] text-on-surface-variant/70">
                    {section.title}
                  </div>
                  {section.items.map((item) => {
                    const IconComponent = item.icon;
                    return (
                      <NavLink
                        key={item.path}
                        to={item.path}
                        onClick={onClose}
                        className={({ isActive }) =>
                          `flex items-center gap-3 px-4 py-3 rounded-full transition-colors ${
                            isActive
                              ? 'bg-secondary-container text-primary font-medium'
                              : 'text-on-surface-variant hover:bg-surface-variant'
                          }`
                        }
                      >
                        <IconComponent size={20} />
                        <span className="text-sm">{item.label}</span>
                      </NavLink>
                    );
                  })}
                </div>
              ))}
            </nav>
          </aside>
        </div>
      )}
    </>
  );
}
