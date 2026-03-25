import { useTheme } from '../lib/theme';
import { Moon, Sun, Menu, Search } from 'lucide-react';
import { useLocation } from 'react-router-dom';

const PAGE_TITLES = {
  '/agents':      'Agents',
  '/skills':      'Skills',
  '/workflows':   'Workflows',
  '/simulation':  'Simulation',
  '/experiments': 'Experiments',
  '/analytics':   'Analytics',
};

export default function Header({ onMenuToggle }) {
  const { theme, toggleTheme } = useTheme();
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] ?? 'ACOS';

  return (
    <header className="sticky top-0 z-50 h-16 flex items-center px-4 gap-4 bg-surface-container border-b border-outline-variant">
      {/* Mobile menu toggle */}
      <button
        onClick={onMenuToggle}
        className="md:hidden p-2 rounded-full hover:bg-surface-variant text-on-surface transition-colors"
        aria-label="Open menu"
      >
        <Menu size={20} />
      </button>

      {/* Logo block */}
      <div className="hidden md:flex w-10 h-10 rounded-xl items-center justify-center bg-primary flex-shrink-0">
        <span className="text-on-primary text-[10px] font-bold tracking-widest">ACOS</span>
      </div>

      {/* Page title */}
      <h1 className="flex-1 text-[22px] font-normal text-on-surface">{title}</h1>

      {/* Search bar */}
      <div className="hidden md:flex items-center gap-2 bg-surface-variant rounded-[28px] h-10 px-4 text-on-surface-variant">
        <Search size={16} />
        <span className="text-sm">Search</span>
      </div>

      {/* Theme toggle */}
      <button
        onClick={toggleTheme}
        title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        className="p-2 rounded-full hover:bg-surface-variant text-on-surface-variant transition-colors"
        aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
      >
        {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
      </button>

      {/* User avatar */}
      <div className="w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container text-xs font-medium flex-shrink-0">
        OP
      </div>
    </header>
  );
}
