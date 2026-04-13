import { Moon, Sun, Menu } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { useTheme } from '../lib/theme';

const PAGE_TITLES = {
  '/workflows': 'Workflow Operations',
  '/channels': 'Channel Onboarding',
  '/demo-routes': 'Demo Route Dispatch',
  '/agents': 'Agent Registry',
  '/skills': 'Tooling Inventory',
  '/analytics': 'Operational Analytics',
  '/tenants': 'Tenant Administration',
};

function ContextChip({ label, value, tone = 'default' }) {
  const tones = {
    default: {
      background: 'var(--md-surface-variant)',
      color: 'var(--md-on-surface-variant)',
      border: '1px solid var(--md-outline-variant)',
    },
    live: {
      background: 'var(--md-success-container)',
      color: 'var(--md-on-success-container)',
      border: '1px solid var(--md-on-success-container)',
    },
    demo: {
      background: 'var(--md-warning-container)',
      color: 'var(--md-on-warning-container)',
      border: '1px solid var(--md-on-warning-container)',
    },
    error: {
      background: 'var(--md-error-container)',
      color: 'var(--md-on-error-container)',
      border: '1px solid var(--md-on-error-container)',
    },
  };
  const style = tones[tone] || tones.default;

  return (
    <div
      style={{
        ...style,
        borderRadius: 999,
        display: 'flex',
        gap: 6,
        alignItems: 'center',
        padding: '6px 10px',
        fontSize: 12,
        whiteSpace: 'nowrap',
      }}
    >
      <span style={{ opacity: 0.75 }}>{label}</span>
      <strong style={{ fontWeight: 600 }}>{value}</strong>
    </div>
  );
}

export default function Header({ context, contextError, onMenuToggle }) {
  const { theme, toggleTheme } = useTheme();
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] ?? 'ACOS';
  const modeTone = context?.mode === 'live' ? 'live' : context?.mode ? 'demo' : 'default';

  return (
    <header className="sticky top-0 z-50 border-b border-outline-variant bg-surface-container">
      <div className="flex min-h-16 items-center gap-4 px-4">
        <button
          onClick={onMenuToggle}
          className="md:hidden p-2 rounded-full hover:bg-surface-variant text-on-surface transition-colors"
          aria-label="Open menu"
        >
          <Menu size={20} />
        </button>

        <div className="hidden md:flex h-10 min-w-10 rounded-xl items-center justify-center bg-primary flex-shrink-0">
          <span className="text-on-primary text-[10px] font-bold tracking-widest">ACOS</span>
        </div>

        <div className="flex-1 min-w-0">
          <h1 className="text-[22px] font-normal text-on-surface">{title}</h1>
          <p className="text-xs text-on-surface-variant">
            Governed commerce workflows with explicit tenant, environment, and runtime context.
          </p>
        </div>

        <button
          onClick={toggleTheme}
          title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
          className="p-2 rounded-full hover:bg-surface-variant text-on-surface-variant transition-colors"
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>
      </div>

      <div
        style={{
          display: 'flex',
          gap: 10,
          alignItems: 'center',
          overflowX: 'auto',
          padding: '0 16px 14px 16px',
        }}
      >
        {contextError ? (
          <ContextChip label="Context" value={contextError.message || 'Unavailable'} tone="error" />
        ) : (
          <>
            <ContextChip label="User" value={context?.display_name || 'Loading'} />
            <ContextChip label="Role" value={context?.primary_role || '...'} />
            <ContextChip label="Tenant" value={context?.tenant_id || 'default'} />
            <ContextChip label="Env" value={context?.environment || '...'} />
            <ContextChip label="Mode" value={context?.mode || '...'} tone={modeTone} />
          </>
        )}
      </div>
    </header>
  );
}
