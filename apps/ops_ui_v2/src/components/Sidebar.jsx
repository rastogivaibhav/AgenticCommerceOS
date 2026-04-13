import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Users, Wrench, GitMerge, BarChart2, Building2, MessageSquareText, Route, X } from 'lucide-react';

const navItems = [
  { path: '/workflows', label: 'Workflows', icon: GitMerge },
  { path: '/channels', label: 'Channels', icon: MessageSquareText },
  { path: '/demo-routes', label: 'Routes', icon: Route },
  { path: '/agents', label: 'Agents', icon: Users },
  { path: '/skills', label: 'Skills', icon: Wrench },
  { path: '/analytics', label: 'Analytics', icon: BarChart2 },
  { path: '/tenants', label: 'Tenants', icon: Building2 },
];

function RailLinks({ onClose }) {
  return (
    <nav aria-label="Main navigation" className="flex flex-col items-center gap-1 py-2 w-full">
      {navItems.map((item) => {
        const IconComponent = item.icon;
        return (
        <NavLink
          key={item.path}
          to={item.path}
          onClick={onClose}
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
              {navItems.map((item) => {
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
            </nav>
          </aside>
        </div>
      )}
    </>
  );
}
