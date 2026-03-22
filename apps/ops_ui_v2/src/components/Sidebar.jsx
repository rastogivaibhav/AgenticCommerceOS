import { NavLink } from 'react-router-dom';
import { Activity, Users, Wrench, GitMerge, X } from 'lucide-react';

const navItems = [
  { path: '/agents', label: 'Agents', icon: Users },
  { path: '/skills', label: 'Skills', icon: Wrench },
  { path: '/workflows', label: 'Workflows', icon: GitMerge },
  { path: '/simulation', label: 'Simulation', icon: Activity },
];

export default function Sidebar({ isOpen, onClose }) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed md:static inset-y-0 left-0 z-40 w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transform transition-transform md:transform-none ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        <div className="p-4 flex items-center justify-between md:hidden border-b dark:border-gray-800">
          <h2 className="font-bold dark:text-white">Menu</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded transition-colors">
            <X size={20} className="dark:text-white" />
          </button>
        </div>

        <nav className="space-y-1 p-4">
          {navItems.map(({ path, label, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              onClick={onClose}
              className={({ isActive }) => `flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100 font-medium'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              <Icon size={20} />
              <span className="text-sm md:text-base">{label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
}
