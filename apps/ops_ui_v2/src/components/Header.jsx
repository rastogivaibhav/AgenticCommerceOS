import { useTheme } from '../lib/theme';
import Button from './Button';
import { Moon, Sun, Menu } from 'lucide-react';

export default function Header({ onMenuToggle }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800">
      <div className="px-4 md:px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuToggle}
            className="md:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-900 rounded-md transition-colors"
          >
            <Menu size={20} className="dark:text-white" />
          </button>
          <h1 className="text-xl md:text-2xl font-bold dark:text-white">ACOS Control Plane</h1>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleTheme}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            className="rounded-full p-2"
          >
            {theme === 'light' ? (
              <Moon size={18} />
            ) : (
              <Sun size={18} className="text-yellow-400" />
            )}
          </Button>
        </div>
      </div>
    </header>
  );
}
