import { useEffect, useMemo, useState } from 'react';
import { Menu, Moon, Settings2, Sun } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { useTheme } from '../lib/theme';

const PAGE_TITLES = {
  '/workflows': 'Workflow Operations',
  '/channels': 'Channel Onboarding',
  '/demo-routes': 'Workflow Validation',
  '/agents': 'Agent Registry',
  '/skills': 'Tooling Inventory',
  '/analytics': 'Operational Analytics',
  '/tenants': 'Tenant Administration',
};

const PLATFORM_MODE_LABELS = {
  normal: 'Normal',
  demo: 'Demo',
};

const RUNTIME_LABELS = {
  auto: 'Auto',
  google_genai: 'Google GenAI',
  local_openai_host: 'Local LLM (host)',
  local_openai_docker: 'Local LLM (docker)',
  local_fallback: 'Local fallback',
};

function ContextChip({ label, value, tone = 'default' }) {
  const tones = {
    default: {
      background: 'var(--md-surface-variant)',
      color: 'var(--md-on-surface-variant)',
      border: '1px solid var(--md-outline-variant)',
    },
    normal: {
      background: 'var(--md-secondary-container)',
      color: 'var(--md-on-secondary-container)',
      border: '1px solid var(--md-on-secondary-container)',
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

function PreferenceField({ label, value, onChange, disabled, options }) {
  return (
    <label style={{ display: 'grid', gap: 6, minWidth: 180 }}>
      <span style={{ fontSize: 12, color: 'var(--md-on-surface-variant)' }}>{label}</span>
      <select
        value={value}
        onChange={onChange}
        disabled={disabled}
        style={{
          minHeight: 38,
          borderRadius: 12,
          border: '1px solid var(--md-outline-variant)',
          background: 'var(--md-surface)',
          color: 'var(--md-on-surface)',
          padding: '0 12px',
        }}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function Header({
  context,
  contextError,
  canOperate,
  isUpdatingPreferences,
  onPreferencesUpdate,
  onMenuToggle,
}) {
  const { theme, toggleTheme } = useTheme();
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] ?? 'ACOS';
  const platformTone = context?.mode === 'demo' ? 'demo' : context?.mode ? 'normal' : 'default';
  const dataTone = context?.data_mode === 'live' ? 'live' : context?.data_mode ? 'demo' : 'default';
  const [platformMode, setPlatformMode] = useState('normal');
  const [runtimePreference, setRuntimePreference] = useState('auto');

  useEffect(() => {
    setPlatformMode(context?.mode || 'normal');
    setRuntimePreference(context?.runtime_preference || 'auto');
  }, [context?.mode, context?.runtime_preference]);

  const runtimeOptions = useMemo(
    () =>
      (context?.runtime_preference_options || Object.keys(RUNTIME_LABELS)).map((value) => ({
        value,
        label: RUNTIME_LABELS[value] || value,
      })),
    [context?.runtime_preference_options],
  );

  const modeOptions = useMemo(
    () =>
      (context?.mode_options || Object.keys(PLATFORM_MODE_LABELS)).map((value) => ({
        value,
        label: PLATFORM_MODE_LABELS[value] || value,
      })),
    [context?.mode_options],
  );

  const preferencesDirty = (
    platformMode !== (context?.mode || 'normal')
    || runtimePreference !== (context?.runtime_preference || 'auto')
  );

  const handleApplyPreferences = () => {
    if (!preferencesDirty || !onPreferencesUpdate) return;
    onPreferencesUpdate({
      platform_mode: platformMode,
      runtime_preference: runtimePreference,
    });
  };

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
            Governed retail and customer-service operations across workflows, channels, agents, and runtime controls.
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
          gap: 12,
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          padding: '0 16px 16px 16px',
        }}
      >
        {contextError ? (
          <ContextChip label="Context" value={contextError.message || 'Unavailable'} tone="error" />
        ) : (
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', overflowX: 'auto', flexWrap: 'wrap' }}>
            <ContextChip label="User" value={context?.display_name || 'Loading'} />
            <ContextChip label="Role" value={context?.primary_role || '...'} />
            <ContextChip label="Tenant" value={context?.tenant_id || 'default'} />
            <ContextChip label="Env" value={context?.environment || '...'} />
            <ContextChip
              label="Run Mode"
              value={PLATFORM_MODE_LABELS[context?.mode] || context?.mode || '...'}
              tone={platformTone}
            />
            <ContextChip
              label="Data"
              value={context?.data_mode === 'live' ? 'Live' : context?.data_mode === 'demo' ? 'Fallback' : '...'}
              tone={dataTone}
            />
            <ContextChip
              label="LLM"
              value={RUNTIME_LABELS[context?.runtime_provider] || context?.runtime_provider || '...'}
            />
          </div>
        )}

        {!contextError && context && canOperate && (
          <div
            style={{
              display: 'flex',
              gap: 12,
              alignItems: 'end',
              flexWrap: 'wrap',
              padding: 12,
              borderRadius: 16,
              border: '1px solid var(--md-outline-variant)',
              background: 'var(--md-surface)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--md-on-surface)' }}>
              <Settings2 size={16} />
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>Runtime Controls</div>
                <div style={{ fontSize: 12, color: 'var(--md-on-surface-variant)' }}>
                  Choose the operator posture and preferred LLM route for governed workflow execution.
                </div>
              </div>
            </div>
            <PreferenceField
              label="Platform Mode"
              value={platformMode}
              onChange={(event) => setPlatformMode(event.target.value)}
              disabled={isUpdatingPreferences}
              options={modeOptions}
            />
            <PreferenceField
              label="Preferred LLM"
              value={runtimePreference}
              onChange={(event) => setRuntimePreference(event.target.value)}
              disabled={isUpdatingPreferences}
              options={runtimeOptions}
            />
            <button
              type="button"
              className="primary-button"
              onClick={handleApplyPreferences}
              disabled={isUpdatingPreferences || !preferencesDirty}
              style={{ minHeight: 38 }}
            >
              {isUpdatingPreferences ? 'Applying...' : 'Apply'}
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
