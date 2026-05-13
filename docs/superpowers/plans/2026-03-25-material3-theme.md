# Material 3 Theme Migration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `apps/ops_ui_v2` from the existing indigo/glass-morphism design to Google Material Design 3 with a purple light/dark scheme, 80px Navigation Rail, and Roboto typography.

**Architecture:** All M3 color tokens are defined as CSS custom properties on `:root` / `:root.dark` in `index.css`, then mapped into `tailwind.config.js` as utility class names so component JSX uses semantic classes (`bg-surface-container`, `text-on-surface`) instead of raw values. The existing `ThemeProvider` already toggles a `dark` class on `<html>`, which matches the `:root.dark` selector — no ThemeProvider changes needed.

**Tech Stack:** React 18, Tailwind CSS (`darkMode: 'class'`), CSS custom properties, Roboto + Roboto Mono (Google Fonts), lucide-react icons, class-variance-authority (CVA) for Button.

---

## File Map

| File | Action |
|---|---|
| `apps/ops_ui_v2/tailwind.config.js` | Replace `colors` block with M3 token mappings; add success tokens |
| `apps/ops_ui_v2/src/index.css` | Replace CSS vars with M3 tokens (light + dark); add Roboto font import |
| `apps/ops_ui_v2/src/App.css` | Replace legacy `var(--*)` refs with M3 vars; update `.hero-panel`, `.error-banner`, form inputs |
| `apps/ops_ui_v2/src/components/Layout.css` | Narrow `.sidebar-desktop` from 256px → 80px |
| `apps/ops_ui_v2/src/components/Sidebar.jsx` | Rebuild as M3 Navigation Rail (icon pill + label) |
| `apps/ops_ui_v2/src/components/Header.jsx` | Rebuild as M3 Top App Bar (logo + title + search + avatar) |
| `apps/ops_ui_v2/src/components/Layout.jsx` | Update wrapper classes to M3 surface tokens |
| `apps/ops_ui_v2/src/components/Button.jsx` | Replace CVA variants with M3 filled/tonal/outlined/text |
| `apps/ops_ui_v2/src/components/MetricsCard.jsx` | Replace card bg with tonal container pattern (index-based cycle) |
| `apps/ops_ui_v2/src/pages/Lists.css` | Remove all glass/blur; replace rgba with M3 surface tokens |
| `apps/ops_ui_v2/src/pages/Agents.jsx` | Replace gray Tailwind classes; update status badge tokens |
| `apps/ops_ui_v2/src/pages/Skills.jsx` | Same as Agents; update type badge tokens |
| `apps/ops_ui_v2/src/pages/WorkflowRegistry.jsx` | Table, modal, template card M3 tokens |
| `apps/ops_ui_v2/src/pages/Analytics.jsx` | Metric card `index` props; chart/table containers |
| `apps/ops_ui_v2/src/pages/Simulation.css` | Mode toggle + live banner only (canvas nodes out of scope) |
| `apps/ops_ui_v2/src/pages/Simulation.jsx` | Gray class replacements on UI chrome only |
| `apps/ops_ui_v2/src/pages/Experiments.jsx` | Gray class replacements |
| `apps/ops_ui_v2/src/components/ExperimentForm.jsx` | M3 filled text-field inputs; tonal button |
| `apps/ops_ui_v2/src/components/ExperimentResults.jsx` | Variant cards tonal; table surface tokens |

**Not changed:** `ThemeProvider.jsx`, `lib/theme.jsx`, `WorkflowCanvas.jsx`, all backend files.

---

## Task 1: CSS Token Foundation

**Files:**
- Modify: `apps/ops_ui_v2/tailwind.config.js`
- Modify: `apps/ops_ui_v2/src/index.css`

- [ ] **Step 1: Replace tailwind.config.js**

Write the complete new file:

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary:                  'var(--md-primary)',
        'on-primary':             'var(--md-on-primary)',
        'primary-container':      'var(--md-primary-container)',
        'on-primary-container':   'var(--md-on-primary-container)',
        secondary:                'var(--md-secondary)',
        'secondary-container':    'var(--md-secondary-container)',
        'on-secondary-container': 'var(--md-on-secondary-container)',
        surface:                  'var(--md-surface)',
        'surface-variant':        'var(--md-surface-variant)',
        'surface-container':      'var(--md-surface-container)',
        'surface-container-high': 'var(--md-surface-container-high)',
        'on-surface':             'var(--md-on-surface)',
        'on-surface-variant':     'var(--md-on-surface-variant)',
        outline:                  'var(--md-outline)',
        'outline-variant':        'var(--md-outline-variant)',
        error:                    'var(--md-error)',
        'error-container':        'var(--md-error-container)',
        'on-error-container':     'var(--md-on-error-container)',
        'on-error':               'var(--md-on-error)',
        'warning-container':      'var(--md-warning-container)',
        'on-warning-container':   'var(--md-on-warning-container)',
        'success-container':      'var(--md-success-container)',
        'on-success-container':   'var(--md-on-success-container)',
      },
      spacing: {
        xs:   '0.25rem',
        sm:   '0.5rem',
        md:   '1rem',
        lg:   '1.5rem',
        xl:   '2rem',
        '2xl':'3rem',
      },
      borderRadius: {
        sm: '0.375rem',
        md: '0.5rem',
        lg: '0.75rem',
      },
      animation: {
        fadeIn:   'fadeIn 0.2s ease-in-out',
        slideUp:  'slideUp 0.3s ease-out',
        fadeInUp: 'fadeInUp 0.3s ease-out',
        slideIn:  'slideIn 0.3s ease-out',
      },
      keyframes: {
        fadeIn:   { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp:  { '0%': { transform: 'translateY(4px)', opacity: '0' }, '100%': { transform: 'translateY(0)', opacity: '1' } },
        fadeInUp: { '0%': { opacity: '0', transform: 'translateY(8px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
        slideIn:  { '0%': { opacity: '0', transform: 'translateX(-16px)' }, '100%': { opacity: '1', transform: 'translateX(0)' } },
      },
    },
  },
  darkMode: 'class',
  plugins: [],
}
```

- [ ] **Step 2: Replace index.css**

Write the complete new file:

```css
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;500&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;

/* ── M3 Purple Light ── */
:root {
  --md-primary:                #6750A4;
  --md-on-primary:             #FFFFFF;
  --md-primary-container:      #EADDFF;
  --md-on-primary-container:   #21005D;
  --md-secondary:              #625B71;
  --md-secondary-container:    #E8DEF8;
  --md-on-secondary-container: #1D192B;
  --md-tertiary:               #7E5260;
  --md-tertiary-container:     #FFD8E4;
  --md-on-tertiary-container:  #31111D;
  --md-surface:                #FFFBFE;
  --md-surface-variant:        #E7E0EC;
  --md-surface-container:      #F3EDF7;
  --md-surface-container-high: #ECE6F0;
  --md-on-surface:             #1C1B1F;
  --md-on-surface-variant:     #49454F;
  --md-outline:                #79747E;
  --md-outline-variant:        #CAC4D0;
  --md-error:                  #B3261E;
  --md-on-error:               #FFFFFF;
  --md-error-container:        #F9DEDC;
  --md-on-error-container:     #410E0B;
  --md-warning-container:      #FDE8C9;
  --md-on-warning-container:   #B45309;
  --md-success-container:      #C8F0DA;
  --md-on-success-container:   #198A56;
}

/* ── M3 Purple Dark ── */
:root.dark {
  --md-primary:                #D0BCFF;
  --md-on-primary:             #381E72;
  --md-primary-container:      #4F378B;
  --md-on-primary-container:   #EADDFF;
  --md-secondary:              #CCC2DC;
  --md-secondary-container:    #4A4458;
  --md-on-secondary-container: #E8DEF8;
  --md-tertiary:               #EFB8C8;
  --md-tertiary-container:     #633B48;
  --md-on-tertiary-container:  #FFD8E4;
  --md-surface:                #1C1B1F;
  --md-surface-variant:        #49454F;
  --md-surface-container:      #211F26;
  --md-surface-container-high: #2B2930;
  --md-on-surface:             #E6E1E5;
  --md-on-surface-variant:     #CAC4D0;
  --md-outline:                #938F99;
  --md-outline-variant:        #49454F;
  --md-error:                  #F2B8B5;
  --md-on-error:               #601410;
  --md-error-container:        #8C1D18;
  --md-on-error-container:     #F9DEDC;
  --md-warning-container:      #4A2F0A;
  --md-on-warning-container:   #FCD4A0;
  --md-success-container:      #0A2E1C;
  --md-on-success-container:   #9EEFC0;
}

body {
  background-color: var(--md-surface);
  color: var(--md-on-surface);
  font-family: 'Roboto', sans-serif;
  transition: background-color 0.3s ease;
}

* {
  @apply transition-colors duration-200;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-16px); }
  to   { opacity: 1; transform: translateX(0); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.5; }
}

.animate-fadeInUp { animation: fadeInUp 0.3s ease-out forwards; }
.animate-slideIn  { animation: slideIn 0.3s ease-out forwards; }
.animate-pulse    { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }

.transition-theme {
  transition: background-color 0.2s, color 0.2s, border-color 0.2s;
}

html {
  transition: background-color 0.3s ease, color 0.3s ease;
}

@media (max-width: 640px) {
  body { font-size: 14px; }
}
```

- [ ] **Step 3: Verify tokens load**

Open `http://localhost:5173`. Page background should shift to light purple-tinted white (`#FFFBFE`) and font should switch to Roboto.

Use `preview_snapshot` to confirm no JS console errors.

- [ ] **Step 4: Commit**

```bash
git add apps/ops_ui_v2/tailwind.config.js apps/ops_ui_v2/src/index.css
git commit -m "feat: add M3 purple token system and Roboto font"
```

---

## Task 2: Layout.css + App.css

**Files:**
- Modify: `apps/ops_ui_v2/src/components/Layout.css`
- Modify: `apps/ops_ui_v2/src/App.css`

- [ ] **Step 1: Narrow sidebar in Layout.css**

In `Layout.css` line 7, change `width: 256px` → `width: 80px`.

Final file:

```css
/* Layout styles are now handled by Tailwind CSS in the components */

/* Desktop sidebar — always a flex column on screens >= 768px */
.sidebar-desktop {
  display: flex;
  flex-direction: column;
  width: 80px;
  flex-shrink: 0;
}

@media (max-width: 767px) {
  .sidebar-desktop {
    display: none;
  }
}
```

- [ ] **Step 2: Update App.css — replace legacy CSS vars**

In `App.css`, perform these find-and-replace operations (all occurrences):

| Find | Replace |
|---|---|
| `font-family: 'Outfit', sans-serif;` | `font-family: 'Roboto', sans-serif;` |
| `color: var(--text-strong)` | `color: var(--md-on-surface)` |
| `color: var(--text-muted)` | `color: var(--md-on-surface-variant)` |
| `color: var(--accent-strong)` | `color: var(--md-primary)` |
| `background: var(--surface)` | `background: var(--md-surface-container)` |
| `background: var(--surface-subtle)` | `background: var(--md-surface-variant)` |
| `background: var(--surface-accent)` | `background: var(--md-primary-container)` |
| `border: 1px solid var(--border-subtle)` | `border: 1px solid var(--md-outline-variant)` |
| `border-color: var(--border-subtle)` | `border-color: var(--md-outline-variant)` |
| `border: 1px solid var(--border-strong)` | `border: 1px solid var(--md-outline)` |
| `box-shadow: var(--shadow-soft)` | `box-shadow: 0 1px 3px rgba(0,0,0,0.08)` |
| `background: var(--accent)` | `background: var(--md-primary)` |
| `background: var(--danger)` | `background: var(--md-error)` |

- [ ] **Step 3: Update App.css — block replacements**

Replace the `.hero-panel` rule:
```css
/* BEFORE */
.hero-panel {
  background:
    radial-gradient(circle at top right, rgba(99, 102, 241, 0.12), transparent 45%),
    linear-gradient(180deg, rgba(22, 24, 29, 0.8) 0%, rgba(15, 17, 21, 0.9) 100%);
}
/* AFTER */
.hero-panel {
  background: var(--md-surface-container);
}
```

Replace the `.error-banner` rule:
```css
/* BEFORE */
.error-banner {
  border-radius: 12px;
  padding: 12px 14px;
  background: #fee4e2;
  color: #b42318;
  border: 1px solid #fecdca;
}
/* AFTER */
.error-banner {
  border-radius: 12px;
  padding: 12px 14px;
  background: var(--md-error-container);
  color: var(--md-on-error-container);
  border: 1px solid var(--md-error-container);
}
```

Replace the form input block (`input, select, textarea { ... }`):
```css
/* BEFORE */
input,
select,
textarea {
  width: 100%;
  border: 1px solid var(--border-strong);
  background: var(--surface-subtle);
  color: var(--text-strong);
  border-radius: 12px;
  padding: 12px 14px;
  box-sizing: border-box;
}
/* AFTER */
input,
select,
textarea {
  width: 100%;
  border: none;
  border-bottom: 1px solid var(--md-outline);
  background: var(--md-surface-variant);
  color: var(--md-on-surface);
  border-radius: 4px 4px 0 0;
  padding: 12px 14px;
  box-sizing: border-box;
}
input:focus,
select:focus,
textarea:focus {
  outline: none;
  border-bottom: 2px solid var(--md-primary);
}
```

Replace the `.secondary-button:hover` rule:
```css
/* BEFORE */
.secondary-button:hover {
  background: rgba(255, 255, 255, 0.08);
}
/* AFTER */
.secondary-button:hover {
  background: var(--md-surface-variant);
}
```

- [ ] **Step 4: Verify sidebar narrowed**

Take `preview_screenshot`. Sidebar should now be ~80px wide with icon-only items (before new Sidebar.jsx is applied, it will show truncated labels — that's fine at this stage).

- [ ] **Step 5: Commit**

```bash
git add apps/ops_ui_v2/src/components/Layout.css apps/ops_ui_v2/src/App.css
git commit -m "feat: narrow sidebar to 80px and update App.css to M3 tokens"
```

---

## Task 3: Navigation Components

**Files:**
- Modify: `apps/ops_ui_v2/src/components/Sidebar.jsx`
- Modify: `apps/ops_ui_v2/src/components/Header.jsx`
- Modify: `apps/ops_ui_v2/src/components/Layout.jsx`

- [ ] **Step 1: Replace Sidebar.jsx with M3 Navigation Rail**

Write the complete new file:

```jsx
import { NavLink } from 'react-router-dom';
import { Activity, Users, Wrench, GitMerge, Zap, BarChart2, X } from 'lucide-react';

const navItems = [
  { path: '/agents',      label: 'Agents',      icon: Users },
  { path: '/skills',      label: 'Skills',      icon: Wrench },
  { path: '/workflows',   label: 'Workflows',   icon: GitMerge },
  { path: '/simulation',  label: 'Simulation',  icon: Activity },
  { path: '/experiments', label: 'Experiments', icon: Zap },
  { path: '/analytics',   label: 'Analytics',   icon: BarChart2 },
];

function RailLinks({ onClose }) {
  return (
    <nav className="flex flex-col items-center gap-1 py-2 w-full">
      {navItems.map(({ path, label, icon: Icon }) => (
        <NavLink
          key={path}
          to={path}
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
            <Icon size={20} />
          </div>
          <span className="text-[11px] font-medium leading-none">{label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export default function Sidebar({ isOpen, onClose }) {
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
                className="p-2 hover:bg-surface-variant rounded-full transition-colors text-on-surface"
              >
                <X size={20} />
              </button>
            </div>
            <nav className="p-2 flex flex-col gap-1">
              {navItems.map(({ path, label, icon: Icon }) => (
                <NavLink
                  key={path}
                  to={path}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-full transition-colors ${
                      isActive
                        ? 'bg-secondary-container text-primary font-medium'
                        : 'text-on-surface-variant hover:bg-surface-variant'
                    }`
                  }
                >
                  <Icon size={20} />
                  <span className="text-sm">{label}</span>
                </NavLink>
              ))}
            </nav>
          </aside>
        </div>
      )}
    </>
  );
}
```

- [ ] **Step 2: Replace Header.jsx with M3 Top App Bar**

Write the complete new file:

```jsx
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
```

- [ ] **Step 3: Update Layout.jsx wrapper classes**

In `Layout.jsx`, make two changes:

Change the outer `div` className:
```jsx
// BEFORE
<div className="flex h-screen bg-white dark:bg-gray-950">
// AFTER
<div className="flex h-screen bg-surface">
```

Change the `<main>` tag:
```jsx
// BEFORE
<main className="flex-1 overflow-auto">
// AFTER
<main className="flex-1 overflow-auto bg-surface">
```

- [ ] **Step 4: Verify navigation**

Take a `preview_screenshot`. The sidebar should be 80px with icons + short labels (stacked), with a purple active indicator. The header should show the ACOS purple logo block on the left, page title in center, search pill, and avatar.

- [ ] **Step 5: Commit**

```bash
git add apps/ops_ui_v2/src/components/Sidebar.jsx apps/ops_ui_v2/src/components/Header.jsx apps/ops_ui_v2/src/components/Layout.jsx
git commit -m "feat: M3 Navigation Rail and Top App Bar"
```

---

## Task 4: Button.jsx + MetricsCard.jsx

**Files:**
- Modify: `apps/ops_ui_v2/src/components/Button.jsx`
- Modify: `apps/ops_ui_v2/src/components/MetricsCard.jsx`

- [ ] **Step 1: Replace Button.jsx with M3 variants**

Write the complete new file:

```jsx
import { forwardRef } from 'react';
import { cva } from 'class-variance-authority';
import { cn } from '../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 font-medium transition-colors focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        filled:      'bg-primary text-on-primary hover:opacity-90 rounded-[20px]',
        tonal:       'bg-secondary-container text-on-secondary-container hover:opacity-90 rounded-[20px]',
        outlined:    'border border-outline text-primary hover:bg-surface-variant rounded-[20px]',
        text:        'text-primary hover:bg-surface-variant rounded-[20px]',
        // Legacy aliases so existing code using variant="default"/"ghost"/"outline" doesn't break
        default:     'bg-primary text-on-primary hover:opacity-90 rounded-[20px]',
        ghost:       'text-on-surface hover:bg-surface-variant rounded-[20px]',
        outline:     'border border-outline text-primary hover:bg-surface-variant rounded-[20px]',
        destructive: 'bg-error text-on-error hover:opacity-90 rounded-[20px]',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-5 text-sm',
        lg: 'h-12 px-6 text-base',
      },
    },
    defaultVariants: {
      variant: 'filled',
      size: 'md',
    },
  }
);

const Button = forwardRef(({ className, variant, size, ...props }, ref) => (
  <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
));

Button.displayName = 'Button';
export default Button;
```

- [ ] **Step 2: Replace MetricsCard.jsx with tonal pattern**

Write the complete new file. Cards cycle through 4 M3 tonal backgrounds based on their `index` prop:

```jsx
const CARD_TOKENS = [
  { bg: 'bg-primary-container',      text: 'text-on-primary-container' },
  { bg: 'bg-secondary-container',    text: 'text-on-secondary-container' },
  { bg: 'bg-warning-container',      text: 'text-on-warning-container' },
  { bg: 'bg-surface-container-high', text: 'text-on-surface' },
];

export default function MetricsCard({ title, value, unit = '', trend = null, delay = 0, index = 0 }) {
  const { bg, text } = CARD_TOKENS[index % 4];
  return (
    <div
      className={`${bg} ${text} rounded-2xl p-5 animate-fadeInUp`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <p className="text-sm font-medium uppercase tracking-wide opacity-80">{title}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <p className="text-3xl font-bold">
          {typeof value === 'number' ? value.toFixed(1) : value}
        </p>
        {unit && <p className="text-sm opacity-70">{unit}</p>}
      </div>
      {trend && (
        <p className="text-xs mt-2 opacity-80">
          {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from last period
        </p>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Audit all MetricsCard callers and add `index` props**

Search for every usage of `MetricsCard` across the codebase:
```bash
grep -rn "<MetricsCard" apps/ops_ui_v2/src --include="*.jsx"
```

For each usage found, add an appropriate `index` prop (`index={0}` through `index={3}`) to trigger the tonal color cycle. If only one card appears in a component, `index={0}` is fine (defaults to primary-container).

In `apps/ops_ui_v2/src/pages/Analytics.jsx`, the four cards should get `index={0}` through `index={3}` respectively.

- [ ] **Step 4: Verify**

Navigate to `/analytics`. Take a `preview_screenshot`. The four metric cards should show four different tonal backgrounds (purple, soft purple, warm amber, surface-high).

- [ ] **Step 5: Commit**

```bash
git add apps/ops_ui_v2/src/components/Button.jsx apps/ops_ui_v2/src/components/MetricsCard.jsx apps/ops_ui_v2/src/pages/Analytics.jsx
git commit -m "feat: M3 button variants and tonal MetricsCard with index cycle"
```

---

## Task 5: Lists.css

**Files:**
- Modify: `apps/ops_ui_v2/src/pages/Lists.css`

This is the most glass-heavy file. Read it in full before editing.

- [ ] **Step 1: Read Lists.css**

Read `apps/ops_ui_v2/src/pages/Lists.css` completely.

- [ ] **Step 2: Remove all backdrop-filter lines**

Delete every line containing `backdrop-filter` or `-webkit-backdrop-filter` (these are the blur/glass effects).

- [ ] **Step 3: Replace rgba backgrounds with M3 surface tokens**

Make these targeted replacements:

**`.sticky-header` background:**
```css
/* BEFORE */ background: rgba(18, 18, 20, 0.85);
/* AFTER  */ background: var(--md-surface-container-high);
```

**`.search-input` background + border:**
```css
/* BEFORE */
background: rgba(255, 255, 255, 0.05);
border: 1px solid rgba(255, 255, 255, 0.1);
/* AFTER */
background: var(--md-surface-variant);
border: 1px solid var(--md-outline-variant);
color: var(--md-on-surface);
```

Search input focus border color (e.g. `#6366f1`):
```css
/* AFTER */ border-color: var(--md-primary);
```

**`.glass-card` background + border:**
```css
/* BEFORE */
background: rgba(255, 255, 255, 0.02);
border: 1px solid rgba(255, 255, 255, 0.05);
/* AFTER */
background: var(--md-surface-container);
border: 1px solid transparent;
border-radius: 16px;
```

`.glass-card:hover`:
```css
/* AFTER */
border-color: var(--md-outline-variant);
box-shadow: 0 2px 8px rgba(0,0,0,0.12);
```

**`.glass-table-wrap`** — remove any rgba background and border-image, replace with:
```css
background: var(--md-surface-container);
border-radius: 16px;
border: none;
```

**`.modal-card` background + border:**
```css
/* BEFORE */
background: rgba(20, 20, 25, 0.7);
border: 1px solid rgba(255, 255, 255, 0.06);
/* AFTER */
background: var(--md-surface-container);
border: 1px solid var(--md-outline-variant);
border-radius: 16px;
```

**`.status-dot.healthy`:**
```css
/* AFTER */
background: var(--md-on-success-container);
box-shadow: none;
```

**`.status-dot.degraded`:**
```css
/* AFTER */
background: var(--md-on-warning-container);
box-shadow: none;
```

**`.tag-subsystem`:**
```css
/* AFTER */
background: var(--md-surface-variant);
color: var(--md-on-surface-variant);
```

**`.skill-icon-wrap`:**
```css
/* BEFORE */
background: rgba(99, 102, 241, 0.1);
color: #818cf8;
/* AFTER */
background: var(--md-primary-container);
color: var(--md-on-primary-container);
```

**`.tag-type.read`:**
```css
/* AFTER */
background: var(--md-secondary-container);
color: var(--md-on-secondary-container);
border: none;
```

**`.tag-type.write`:**
```css
/* AFTER */
background: var(--md-error-container);
color: var(--md-on-error-container);
border: none;
```

Any filter chip active state (background `#6366f1` or similar):
```css
/* AFTER */
background: var(--md-secondary-container);
border-color: var(--md-primary);
color: var(--md-on-secondary-container);
```

**`.status-badge.healthy`** (full pill label — separate from `.status-dot`):
```css
/* AFTER */
background: var(--md-success-container);
color: var(--md-on-success-container);
border: 1px solid var(--md-on-success-container);
```

**`.status-badge.degraded`:**
```css
/* AFTER */
background: var(--md-warning-container);
color: var(--md-on-warning-container);
border: 1px solid var(--md-on-warning-container);
```

**`.card-title-group h3`** (hardcoded `color: #f4f4f5`):
```css
color: var(--md-on-surface);
```

**`.stat-label`** (hardcoded `color: #a1a1aa`):
```css
color: var(--md-on-surface-variant);
```

**`.stat-val`** (hardcoded `color: #e4e4e7`):
```css
color: var(--md-on-surface);
```

**`.stat-row`** bottom border:
```css
/* BEFORE */ border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
/* AFTER  */ border-bottom: 1px solid var(--md-outline-variant);
```

**`.tag-category`:**
```css
/* AFTER */
background: var(--md-surface-variant);
color: var(--md-on-surface-variant);
```

**`.interactive-row:hover`:**
```css
/* BEFORE */ background: rgba(255, 255, 255, 0.04);
/* AFTER  */ background: var(--md-surface);
```

**`.search-input:focus`** — update the full focus block (remove indigo box-shadow):
```css
/* AFTER */
border-color: var(--md-primary);
background: var(--md-surface-variant);
box-shadow: none;
```

- [ ] **Step 4: Verify list pages**

Navigate to `/agents` and `/skills`. Take a `preview_screenshot`. Cards should have M3 surface-container backgrounds with no blur/glass. Status dots should use M3 semantic colors.

- [ ] **Step 5: Commit**

```bash
git add apps/ops_ui_v2/src/pages/Lists.css
git commit -m "feat: replace glass morphism with M3 surface tokens in Lists.css"
```

---

## Task 6: Agents.jsx

**Files:**
- Modify: `apps/ops_ui_v2/src/pages/Agents.jsx`

- [ ] **Step 1: Read Agents.jsx**

Read the full file before editing.

- [ ] **Step 2: Replace gray Tailwind classes**

Apply these find-and-replace operations throughout the file. **Apply all combined-class pairs (rows containing both a light and dark class, e.g. `bg-white dark:bg-gray-900`) first, then apply any remaining standalone `dark:*` class rows — order matters to avoid double-replacement.**

| Find | Replace |
|---|---|
| `bg-white dark:bg-gray-900` | `bg-surface-container` |
| `bg-white dark:bg-gray-950` | `bg-surface` |
| `bg-gray-50 dark:bg-gray-800` | `bg-surface-container-high` |
| `bg-gray-100 dark:bg-gray-700` | `bg-surface-variant` |
| `dark:bg-gray-900` (standalone) | `bg-surface-container` |
| `dark:bg-gray-950` (standalone) | `bg-surface` |
| `text-gray-900 dark:text-white` | `text-on-surface` |
| `text-gray-700 dark:text-gray-300` | `text-on-surface-variant` |
| `text-gray-600 dark:text-gray-400` | `text-on-surface-variant` |
| `text-gray-500 dark:text-gray-400` | `text-on-surface-variant` |
| `border-gray-200 dark:border-gray-700` | `border-outline-variant` |
| `border-gray-200 dark:border-gray-800` | `border-outline-variant` |
| `hover:bg-gray-100 dark:hover:bg-gray-800` | `hover:bg-surface-container-high` |
| `dark:border-gray-800` (standalone) | `border-outline-variant` |

- [ ] **Step 3: Replace status badge colors**

Find any status badge rendering. Replace with token-based logic:

```jsx
// Status badge class map
const STATUS_CLASSES = {
  healthy:  'bg-success-container text-on-success-container',
  degraded: 'bg-warning-container text-on-warning-container',
  disabled: 'bg-warning-container text-on-warning-container',
  error:    'bg-error-container text-on-error-container',
};

// Usage
<span className={`${STATUS_CLASSES[agent.status?.toLowerCase()] ?? 'bg-surface-variant text-on-surface-variant'} text-xs px-3 py-1 rounded-full font-medium`}>
  {agent.status}
</span>
```

Remove any hardcoded hex colors like `#10b981`, `#f59e0b` from status rendering.

- [ ] **Step 4: Verify**

Navigate to `/agents`. Take a `preview_screenshot`.

- [ ] **Step 5: Commit**

```bash
git add apps/ops_ui_v2/src/pages/Agents.jsx
git commit -m "feat: Agents page M3 surface tokens and status chips"
```

---

## Task 7: Skills.jsx

**Files:**
- Modify: `apps/ops_ui_v2/src/pages/Skills.jsx`

- [ ] **Step 1: Read Skills.jsx**

- [ ] **Step 2: Apply gray → M3 token replacements**

Same replacement table as Task 6 Step 2.

- [ ] **Step 3: Update type badge colors**

Replace read/write type badge inline styles or class logic:

```jsx
const TYPE_CLASSES = {
  read:  'bg-secondary-container text-on-secondary-container',
  write: 'bg-error-container text-on-error-container',
};
```

- [ ] **Step 4: Verify**

Navigate to `/skills`. Take a `preview_screenshot`.

- [ ] **Step 5: Commit**

```bash
git add apps/ops_ui_v2/src/pages/Skills.jsx
git commit -m "feat: Skills page M3 tokens and type badges"
```

---

## Task 8: WorkflowRegistry.jsx

**Files:**
- Modify: `apps/ops_ui_v2/src/pages/WorkflowRegistry.jsx`

- [ ] **Step 1: Read WorkflowRegistry.jsx**

- [ ] **Step 2: Apply gray → M3 token replacements**

Same replacement table as Task 6 Step 2.

- [ ] **Step 3: Update table styles**

Table container:
```jsx
className="bg-surface-container rounded-2xl overflow-hidden"
```

Table header row cells:
```jsx
className="bg-surface-container-high text-on-surface-variant text-[11px] font-medium uppercase tracking-wide px-4 py-3"
```

Table data rows (hover):
```jsx
className="hover:bg-surface cursor-pointer transition-colors"
```

- [ ] **Step 4: Update modal background**

Modal card container:
```jsx
className="bg-surface-container border border-outline-variant rounded-2xl ..."
```

- [ ] **Step 5: Update template card selection style**

Default template card:
```jsx
className="bg-surface-container border border-transparent rounded-2xl p-4 cursor-pointer hover:border-outline-variant transition-colors"
```

Selected template card:
```jsx
className="bg-primary-container border border-primary rounded-2xl p-4 cursor-pointer"
```

- [ ] **Step 6: Verify**

Navigate to `/workflows`. Take a `preview_screenshot`.

- [ ] **Step 7: Commit**

```bash
git add apps/ops_ui_v2/src/pages/WorkflowRegistry.jsx
git commit -m "feat: WorkflowRegistry M3 table, modal, and template cards"
```

---

## Task 9: Analytics.jsx

**Files:**
- Modify: `apps/ops_ui_v2/src/pages/Analytics.jsx`

(MetricsCard `index` props were already added in Task 4 Step 3.)

- [ ] **Step 1: Read Analytics.jsx**

- [ ] **Step 2: Apply gray → M3 token replacements**

Same replacement table as Task 6 Step 2.

- [ ] **Step 3: Update chart container panels**

```jsx
className="bg-surface-container rounded-2xl p-5"
```

- [ ] **Step 4: Update workflow performance table container**

```jsx
className="bg-surface-container rounded-2xl overflow-hidden"
```

Table header: `bg-surface-container-high`
Row hover: `hover:bg-surface`

- [ ] **Step 5: Verify**

Navigate to `/analytics`. Take a `preview_screenshot`. Four metric cards should display tonal colors.

- [ ] **Step 6: Commit**

```bash
git add apps/ops_ui_v2/src/pages/Analytics.jsx
git commit -m "feat: Analytics page M3 chart containers and table"
```

---

## Task 10: Simulation.css + Simulation.jsx

**Files:**
- Modify: `apps/ops_ui_v2/src/pages/Simulation.css`
- Modify: `apps/ops_ui_v2/src/pages/Simulation.jsx`

**Important:** ReactFlow canvas node styles (`.react-flow__node`, `.node-marketing`, `.node-core`, etc.) are **out of scope** — do NOT modify those classes.

- [ ] **Step 1: Read both files**

- [ ] **Step 2: Update Simulation.css — UI chrome only**

Update `.mode-toggle`:
```css
/* AFTER */
background: var(--md-surface-container-high);
border: 1px solid var(--md-outline-variant);
color: var(--md-on-surface);
```

Update `.live-overlay-banner`:
```css
/* AFTER */
background: var(--md-success-container);
border: 1px solid var(--md-on-success-container);
color: var(--md-on-success-container);
```

Update `.live-dot`:
```css
/* AFTER */
background: var(--md-on-success-container);
```

Update `.draggable-agent` hover:
```css
/* AFTER */
background: var(--md-primary-container);
border-color: var(--md-primary);
```

Update `.toolbox` (the agent palette panel — UI chrome, not a canvas node):
```css
/* AFTER */
background: var(--md-surface-container-high);
border: 1px solid var(--md-outline-variant);
```

- [ ] **Step 3: Apply gray → M3 token replacements in Simulation.jsx**

Same table as Task 6 Step 2, applied to UI chrome elements only (buttons, toolbar, panel backgrounds).

- [ ] **Step 4: Verify**

Navigate to `/simulation`. Take a `preview_screenshot`. Mode toggle and live banner should use M3 colors. Canvas nodes should be unchanged.

- [ ] **Step 5: Commit**

```bash
git add apps/ops_ui_v2/src/pages/Simulation.css apps/ops_ui_v2/src/pages/Simulation.jsx
git commit -m "feat: Simulation UI chrome M3 tokens (canvas out of scope)"
```

---

## Task 11: Experiments

**Files:**
- Modify: `apps/ops_ui_v2/src/pages/Experiments.jsx`
- Modify: `apps/ops_ui_v2/src/components/ExperimentForm.jsx`
- Modify: `apps/ops_ui_v2/src/components/ExperimentResults.jsx`

- [ ] **Step 1: Read all three files**

- [ ] **Step 2: Update Experiments.jsx**

Apply gray → M3 token replacements (same table as Task 6 Step 2). Update any status banner to use `bg-surface-container border-outline-variant`.

- [ ] **Step 3: Update ExperimentForm.jsx**

Apply gray → M3 token replacements.

For text inputs inside the form, update to M3 filled text-field pattern:
```jsx
className="w-full bg-surface-variant text-on-surface border-b border-outline focus:border-b-2 focus:border-primary rounded-t px-4 py-3 outline-none transition-colors"
```

Update any submit/run `<Button>` to use `variant="filled"`.

- [ ] **Step 4: Update ExperimentResults.jsx**

Apply gray → M3 token replacements.

Update variant cards:
```jsx
// Variant A
className="bg-primary-container text-on-primary-container rounded-2xl p-5"
// Variant B
className="bg-secondary-container text-on-secondary-container rounded-2xl p-5"
// Winner
className="bg-success-container text-on-success-container rounded-2xl p-5"
```

Table container: `bg-surface-container rounded-2xl overflow-hidden`
Table header: `bg-surface-container-high`
Row hover: `hover:bg-surface`

- [ ] **Step 5: Verify**

Navigate to `/experiments`. Take a `preview_screenshot`.

- [ ] **Step 6: Commit**

```bash
git add apps/ops_ui_v2/src/pages/Experiments.jsx apps/ops_ui_v2/src/components/ExperimentForm.jsx apps/ops_ui_v2/src/components/ExperimentResults.jsx
git commit -m "feat: Experiments M3 form fields, variant cards, results table"
```

---

## Task 12: Final Review + Dark Mode Check

- [ ] **Step 1: Sweep for remaining gray classes**

Run a search for leftover raw gray Tailwind classes in all JSX/JS files:

```bash
grep -rn "bg-gray-\|text-gray-\|dark:bg-gray-\|dark:text-gray-\|border-gray-\|dark:border-gray-" \
  apps/ops_ui_v2/src --include="*.jsx" --include="*.js"
```

Fix any hits using the replacement table from Task 6 Step 2.

- [ ] **Step 2: Sweep for raw hex colors in JSX**

```bash
grep -rn "#[0-9a-fA-F]\{3,6\}" apps/ops_ui_v2/src --include="*.jsx" --include="*.js"
```

Replace any structural hex colors (grays, blues) with M3 tokens. Content-specific colors (e.g. chart data series, workflow category tags) may stay.

- [ ] **Step 3: Full light-mode visual sweep**

Visit each route and take screenshots:
- `/agents` — cards, status chips, filter chips
- `/skills` — type badges, cards
- `/workflows` — table, modal, template cards
- `/analytics` — tonal metric cards, chart containers
- `/experiments` — form fields, variant cards
- `/simulation` — mode toggle, live banner (canvas unchanged)

- [ ] **Step 4: Dark mode check**

Click the theme toggle. Revisit `/agents` and `/analytics`. Verify:
- Background is `#1C1B1F` (dark surface)
- Cards are `#211F26` (dark surface-container)
- Primary color is `#D0BCFF` (soft lavender) on interactive elements
- Navigation Rail indicator is dark `#4A4458` (dark secondary-container)

- [ ] **Step 5: Fix any issues found**

Address any visual regressions before the final commit.

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat: complete Material 3 Purple theme migration"
```
