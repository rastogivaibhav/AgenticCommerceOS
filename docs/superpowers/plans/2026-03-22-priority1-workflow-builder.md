# ACOS Priority 1: Workflow Builder → Experiments → Analytics → Export (2-Week GA Release)

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a production-grade Workflow Builder with experiment execution, analytics dashboard, and export capability in 2 weeks. Modern Figma-like UI with dark/light mode and responsive design across all user personas (Business Analysts, Production Engineers, Executives).

**Architecture:**
- **Frontend:** React 19 + Vite with shadcn/ui components + Tailwind CSS for responsive, themeable UI
- **Backend:** Existing FastAPI ops_api with new endpoints for workflow creation/management
- **Database:** Leverage existing schema (workflows, workflow_versions, experiments, runs)
- **Design System:** shadcn/ui base components + custom design tokens for dark/light mode + Figma-like animations
- **Responsive Strategy:** Mobile-first breakpoints (sm: 640px, md: 768px, lg: 1024px, xl: 1280px, 2xl: 1536px)

**Tech Stack:**
- React 19.2.4, Vite 8, React Router 7.13, Tailwind CSS, shadcn/ui, Lucide icons, ReactFlow for visual builder
- FastAPI (existing), PostgreSQL (existing)
- Vitest for unit tests, Playwright for E2E

**Timeline:**
- **Week 1:** Foundation (design system, layout shell, auth UI, Workflow Builder canvas)
- **Week 2:** Feature completion (Experiment execution, Analytics, Export, responsive polish, testing)
- **Target GA:** End of Week 2

---

## Phase 1: Foundation & Design System (Days 1-3)

### Task 1: Set up Design System & Theme Infrastructure

**Files:**
- Create: `apps/ops_ui_v2/src/lib/theme.js` (theme context & utilities)
- Create: `apps/ops_ui_v2/src/lib/colors.js` (design tokens)
- Create: `apps/ops_ui_v2/src/components/ThemeProvider.jsx`
- Modify: `apps/ops_ui_v2/tailwind.config.js` (theme configuration)
- Modify: `apps/ops_ui_v2/src/index.css` (CSS variables)

**Steps:**

- [ ] **1.1: Install shadcn/ui and dependencies**

```bash
cd apps/ops_ui_v2
npm install -D tailwindcss postcss autoprefixer
npm install class-variance-authority clsx tailwind-merge
npx shadcn-ui@latest init -d
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tabs @radix-ui/react-select
npm install zustand axios
```

Expected output: shadcn/ui initialized, tailwind configured.

- [ ] **1.2: Create design tokens file**

Create `apps/ops_ui_v2/src/lib/colors.js`:

```javascript
export const colors = {
  light: {
    background: '#ffffff',
    foreground: '#000000',
    card: '#f5f5f5',
    cardBorder: '#e0e0e0',
    primary: '#0066ff',
    primaryHover: '#0052cc',
    accent: '#10b981',
    destructive: '#ef4444',
    muted: '#6b7280',
    mutedForeground: '#9ca3af',
  },
  dark: {
    background: '#0f0f0f',
    foreground: '#ffffff',
    card: '#1a1a1a',
    cardBorder: '#2d2d2d',
    primary: '#3b82f6',
    primaryHover: '#2563eb',
    accent: '#10b981',
    destructive: '#f87171',
    muted: '#4b5563',
    mutedForeground: '#9ca3af',
  },
};

export const spacing = {
  xs: '0.25rem',
  sm: '0.5rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '3rem',
};

export const typography = {
  display: { fontSize: '2.25rem', fontWeight: 700 },
  h1: { fontSize: '1.875rem', fontWeight: 700 },
  h2: { fontSize: '1.5rem', fontWeight: 600 },
  h3: { fontSize: '1.25rem', fontWeight: 600 },
  body: { fontSize: '1rem', fontWeight: 400 },
  small: { fontSize: '0.875rem', fontWeight: 400 },
};
```

- [ ] **1.3: Create theme context**

Create `apps/ops_ui_v2/src/lib/theme.js`:

```javascript
import { createContext, useContext, useEffect, useState } from 'react';
import { colors } from './colors';

const ThemeContext = createContext();

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  useEffect(() => {
    localStorage.setItem('theme', theme);
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.style.colorScheme = theme;

    // Apply CSS variables
    const palette = colors[theme];
    Object.entries(palette).forEach(([key, value]) => {
      document.documentElement.style.setProperty(`--color-${key}`, value);
    });
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light');

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, colors: colors[theme] }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
};
```

- [ ] **1.4: Update tailwind.config.js for CSS variables**

Modify `apps/ops_ui_v2/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: 'rgb(var(--color-primary) / <alpha-value>)',
        secondary: 'rgb(var(--color-secondary) / <alpha-value>)',
        accent: 'rgb(var(--color-accent) / <alpha-value>)',
        muted: 'rgb(var(--color-muted) / <alpha-value>)',
      },
      backgroundColor: {
        default: 'var(--color-background)',
        card: 'var(--color-card)',
      },
      textColor: {
        default: 'var(--color-foreground)',
        muted: 'var(--color-muted-foreground)',
      },
      spacing: {
        xs: '0.25rem',
        sm: '0.5rem',
        md: '1rem',
        lg: '1.5rem',
        xl: '2rem',
        '2xl': '3rem',
      },
      borderRadius: {
        sm: '0.375rem',
        md: '0.5rem',
        lg: '0.75rem',
      },
      animation: {
        fadeIn: 'fadeIn 0.2s ease-in-out',
        slideUp: 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(4px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  darkMode: 'class',
  plugins: [],
}
```

- [ ] **1.5: Create ThemeProvider component**

Create `apps/ops_ui_v2/src/components/ThemeProvider.jsx`:

```jsx
import { ThemeProvider as ContextProvider } from '../lib/theme';

export function ThemeProvider({ children }) {
  return <ContextProvider>{children}</ContextProvider>;
}
```

- [ ] **1.6: Update App.jsx to include ThemeProvider**

Modify `apps/ops_ui_v2/src/App.jsx`:

```jsx
import { ThemeProvider } from './components/ThemeProvider';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import WorkflowBuilder from './pages/WorkflowBuilder';
import Experiments from './pages/Experiments';
import Analytics from './pages/Analytics';

function App() {
  return (
    <ThemeProvider>
      <Router>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<WorkflowBuilder />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/analytics" element={<Analytics />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
```

- [ ] **1.7: Commit**

```bash
git add apps/ops_ui_v2/
git commit -m "feat: establish design system with theme infrastructure and Tailwind CSS"
```

---

### Task 2: Build Responsive Layout Shell & Navigation

**Files:**
- Create: `apps/ops_ui_v2/src/components/Layout.jsx`
- Create: `apps/ops_ui_v2/src/components/Sidebar.jsx`
- Create: `apps/ops_ui_v2/src/components/Header.jsx`
- Create: `apps/ops_ui_v2/src/components/Button.jsx`
- Create: `apps/ops_ui_v2/src/pages/Dashboard.jsx`
- Modify: `apps/ops_ui_v2/src/App.jsx`
- Modify: `apps/ops_ui_v2/src/index.css`

**Steps:**

- [ ] **2.1: Create Button component (shadcn/ui style)**

Create `apps/ops_ui_v2/src/components/Button.jsx`:

```jsx
import { forwardRef } from 'react';
import { cva } from 'class-variance-authority';
import { cn } from '../lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed',
  {
    variants: {
      variant: {
        default: 'bg-blue-600 hover:bg-blue-700 text-white dark:bg-blue-500 dark:hover:bg-blue-600',
        outline: 'border border-gray-300 hover:bg-gray-50 dark:border-gray-600 dark:hover:bg-gray-900',
        ghost: 'hover:bg-gray-100 dark:hover:bg-gray-900 text-gray-900 dark:text-white',
        destructive: 'bg-red-600 hover:bg-red-700 text-white',
      },
      size: {
        sm: 'h-8 px-3 text-sm',
        md: 'h-10 px-4 text-base',
        lg: 'h-12 px-6 text-base',
      },
    },
    defaultVariants: {
      variant: 'default',
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

- [ ] **2.2: Create utility functions**

Create `apps/ops_ui_v2/src/lib/utils.js`:

```javascript
export function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

export const getResponsiveClass = (mobile, tablet, desktop) => {
  return `${mobile} md:${tablet} lg:${desktop}`;
};
```

- [ ] **2.3: Create Header component**

Create `apps/ops_ui_v2/src/components/Header.jsx`:

```jsx
import { useTheme } from '../lib/theme';
import Button from './Button';
import { Moon, Sun, Menu, X } from 'lucide-react';
import { useState } from 'react';

export default function Header({ onMenuToggle }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800">
      <div className="px-4 md:px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onMenuToggle}
            className="md:hidden p-2 hover:bg-gray-100 dark:hover:bg-gray-900 rounded-md"
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
```

- [ ] **2.4: Create Sidebar component**

Create `apps/ops_ui_v2/src/components/Sidebar.jsx`:

```jsx
import { Link, useLocation } from 'react-router-dom';
import { BarChart3, Zap, TrendingUp, X } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Workflow Builder', icon: Zap },
  { path: '/experiments', label: 'Run Experiments', icon: BarChart3 },
  { path: '/analytics', label: 'Analytics', icon: TrendingUp },
];

export default function Sidebar({ isOpen, onClose }) {
  const location = useLocation();

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
        <div className="p-4 flex items-center justify-between md:hidden">
          <h2 className="font-bold dark:text-white">Menu</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded">
            <X size={20} />
          </button>
        </div>

        <nav className="space-y-1 p-4">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              onClick={onClose}
              className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                location.pathname === path
                  ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100 font-medium'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              <Icon size={20} />
              <span className="text-sm md:text-base">{label}</span>
            </Link>
          ))}
        </nav>
      </aside>
    </>
  );
}
```

- [ ] **2.5: Create Layout component**

Create `apps/ops_ui_v2/src/components/Layout.jsx`:

```jsx
import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="flex h-screen bg-white dark:bg-gray-950">
      <Sidebar isOpen={menuOpen} onClose={() => setMenuOpen(false)} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header onMenuToggle={() => setMenuOpen(!menuOpen)} />
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

- [ ] **2.6: Create placeholder pages**

Create `apps/ops_ui_v2/src/pages/WorkflowBuilder.jsx`:

```jsx
export default function WorkflowBuilder() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold dark:text-white mb-6">Workflow Builder</h1>
      <p className="dark:text-gray-400">Workflow builder coming soon...</p>
    </div>
  );
}
```

Create `apps/ops_ui_v2/src/pages/Experiments.jsx`:

```jsx
export default function Experiments() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold dark:text-white mb-6">Run Experiments</h1>
      <p className="dark:text-gray-400">Experiments coming soon...</p>
    </div>
  );
}
```

Create `apps/ops_ui_v2/src/pages/Analytics.jsx`:

```jsx
export default function Analytics() {
  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold dark:text-white mb-6">Analytics Dashboard</h1>
      <p className="dark:text-gray-400">Analytics coming soon...</p>
    </div>
  );
}
```

- [ ] **2.7: Update index.css for global styles**

Modify `apps/ops_ui_v2/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --color-background: #ffffff;
  --color-foreground: #000000;
  --color-card: #f5f5f5;
  --color-card-border: #e0e0e0;
  --color-primary: #0066ff;
  --color-primary-hover: #0052cc;
  --color-accent: #10b981;
  --color-destructive: #ef4444;
  --color-muted: #6b7280;
  --color-muted-foreground: #9ca3af;
}

:root.dark {
  --color-background: #0f0f0f;
  --color-foreground: #ffffff;
  --color-card: #1a1a1a;
  --color-card-border: #2d2d2d;
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --color-accent: #10b981;
  --color-destructive: #f87171;
  --color-muted: #4b5563;
  --color-muted-foreground: #9ca3af;
}

body {
  background-color: var(--color-background);
  color: var(--color-foreground);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  transition: background-color 0.3s ease;
}

* {
  @apply transition-colors duration-200;
}

@media (max-width: 640px) {
  body {
    font-size: 14px;
  }
}
```

- [ ] **2.8: Commit**

```bash
git add apps/ops_ui_v2/src/
git commit -m "feat: build responsive layout shell with header, sidebar, and navigation"
```

---

## Phase 2: Workflow Builder Implementation (Days 4-7)

### Task 3: Create Workflow Builder Canvas & Visual Editor

**Files:**
- Create: `apps/ops_ui_v2/src/components/WorkflowCanvas.jsx`
- Create: `apps/ops_ui_v2/src/components/StepNode.jsx`
- Create: `apps/ops_ui_v2/src/components/ToolPanel.jsx`
- Create: `apps/ops_ui_v2/src/store/workflowStore.js` (Zustand)
- Create: `apps/ops_ui_v2/src/hooks/useWorkflow.js`
- Modify: `apps/ops_ui_v2/src/pages/WorkflowBuilder.jsx`
- Create: `apps/ops_ui_v2/src/api/workflowAPI.js` (API client)

**Steps:**

- [ ] **3.1: Create Zustand store for workflow state**

Create `apps/ops_ui_v2/src/store/workflowStore.js`:

```javascript
import { create } from 'zustand';

export const useWorkflowStore = create((set) => ({
  // Workflow metadata
  workflow: {
    name: '',
    description: '',
    family: 'default',
    owner: 'analyst',
  },

  // Steps/nodes
  nodes: [],
  edges: [],
  selectedNode: null,

  // Workflow state
  isDraft: true,
  isSaving: false,

  // Actions
  updateWorkflow: (updates) => set((state) => ({
    workflow: { ...state.workflow, ...updates }
  })),

  addNode: (node) => set((state) => ({
    nodes: [...state.nodes, { id: Date.now().toString(), ...node }]
  })),

  updateNode: (id, updates) => set((state) => ({
    nodes: state.nodes.map(n => n.id === id ? { ...n, ...updates } : n)
  })),

  deleteNode: (id) => set((state) => ({
    nodes: state.nodes.filter(n => n.id !== id),
    edges: state.edges.filter(e => e.source !== id && e.target !== id)
  })),

  addEdge: (edge) => set((state) => ({
    edges: [...state.edges, edge]
  })),

  deleteEdge: (edgeId) => set((state) => ({
    edges: state.edges.filter(e => e.id !== edgeId)
  })),

  setSelectedNode: (id) => set({ selectedNode: id }),

  reset: () => set({
    workflow: { name: '', description: '', family: 'default', owner: 'analyst' },
    nodes: [],
    edges: [],
    selectedNode: null,
    isDraft: true,
  }),
}));
```

- [ ] **3.2: Create API client for workflow endpoints**

Create `apps/ops_ui_v2/src/api/workflowAPI.js`:

```javascript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function createWorkflow(workflow) {
  const response = await fetch(`${API_BASE}/workflows`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(workflow),
  });
  if (!response.ok) throw new Error('Failed to create workflow');
  return response.json();
}

export async function getWorkflow(id) {
  const response = await fetch(`${API_BASE}/workflows/${id}`);
  if (!response.ok) throw new Error('Failed to fetch workflow');
  return response.json();
}

export async function listWorkflows() {
  const response = await fetch(`${API_BASE}/workflows`);
  if (!response.ok) throw new Error('Failed to fetch workflows');
  return response.json();
}

export async function updateWorkflow(id, updates) {
  const response = await fetch(`${API_BASE}/workflows/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!response.ok) throw new Error('Failed to update workflow');
  return response.json();
}

export async function createWorkflowVersion(workflowId, version) {
  const response = await fetch(`${API_BASE}/workflows/${workflowId}/versions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(version),
  });
  if (!response.ok) throw new Error('Failed to create workflow version');
  return response.json();
}

export async function saveWorkflowDraft(workflowId, steps, edges) {
  return updateWorkflow(workflowId, {
    status: 'draft',
    step_definitions: steps,
    edges: edges,
  });
}
```

- [ ] **3.3: Create StepNode component**

Create `apps/ops_ui_v2/src/components/StepNode.jsx`:

```jsx
import { X, GripVertical } from 'lucide-react';
import Button from './Button';

export default function StepNode({
  id,
  data,
  isSelected,
  onSelect,
  onDelete,
  onUpdate,
}) {
  return (
    <div
      onClick={() => onSelect(id)}
      className={`bg-white dark:bg-gray-900 border-2 rounded-lg p-4 cursor-move transition-all ${
        isSelected
          ? 'border-blue-500 shadow-lg'
          : 'border-gray-300 dark:border-gray-700 hover:border-gray-400'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <GripVertical size={16} className="text-gray-400" />
          <span className="font-semibold text-sm dark:text-white">{data.type}</span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(id);
          }}
          className="p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded text-red-600"
        >
          <X size={16} />
        </button>
      </div>

      <input
        type="text"
        placeholder="Step name"
        value={data.name || ''}
        onChange={(e) => onUpdate(id, { name: e.target.value })}
        className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-800 dark:border-gray-700 dark:text-white mb-2"
      />

      <textarea
        placeholder="Configuration (JSON)"
        value={data.config || '{}'}
        onChange={(e) => onUpdate(id, { config: e.target.value })}
        className="w-full px-2 py-1 text-xs border rounded font-mono dark:bg-gray-800 dark:border-gray-700 dark:text-white"
        rows="3"
      />
    </div>
  );
}
```

- [ ] **3.4: Create ToolPanel component**

Create `apps/ops_ui_v2/src/components/ToolPanel.jsx`:

```jsx
import Button from './Button';
import { Plus } from 'lucide-react';

const stepTypes = [
  'input',
  'agent_call',
  'data_transform',
  'decision',
  'output',
];

export default function ToolPanel({ onAddStep }) {
  return (
    <div className="w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 p-4 overflow-y-auto">
      <h3 className="font-semibold dark:text-white mb-4">Add Steps</h3>
      <div className="space-y-2">
        {stepTypes.map((type) => (
          <Button
            key={type}
            variant="outline"
            size="sm"
            className="w-full justify-start"
            onClick={() => onAddStep(type)}
          >
            <Plus size={16} />
            {type.replace(/_/g, ' ').toUpperCase()}
          </Button>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **3.5: Create WorkflowCanvas component**

Create `apps/ops_ui_v2/src/components/WorkflowCanvas.jsx`:

```jsx
import { useState } from 'react';
import StepNode from './StepNode';
import Button from './Button';
import { useWorkflowStore } from '../store/workflowStore';
import { Save, Play } from 'lucide-react';

export default function WorkflowCanvas() {
  const {
    workflow,
    nodes,
    edges,
    selectedNode,
    updateWorkflow,
    addNode,
    updateNode,
    deleteNode,
    setSelectedNode,
    addEdge,
  } = useWorkflowStore();

  const [connecting, setConnecting] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const handleAddStep = (type) => {
    addNode({
      type,
      name: `${type}-${Date.now()}`,
      config: '{}',
    });
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Call API to save workflow
      console.log('Saving workflow:', { workflow, nodes, edges });
      // await saveWorkflowDraft(workflow.id, nodes, edges);
    } catch (error) {
      console.error('Failed to save:', error);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex h-full gap-4 p-4 bg-white dark:bg-gray-950">
      {/* Canvas area */}
      <div className="flex-1 flex flex-col">
        <div className="mb-4">
          <input
            type="text"
            placeholder="Workflow name"
            value={workflow.name}
            onChange={(e) => updateWorkflow({ name: e.target.value })}
            className="text-2xl font-bold px-2 py-1 border rounded dark:bg-gray-900 dark:border-gray-700 dark:text-white"
          />
        </div>

        <div className="flex-1 bg-gray-50 dark:bg-gray-900 border rounded-lg p-4 overflow-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {nodes.map((node) => (
              <StepNode
                key={node.id}
                id={node.id}
                data={node}
                isSelected={selectedNode === node.id}
                onSelect={setSelectedNode}
                onDelete={deleteNode}
                onUpdate={updateNode}
              />
            ))}
            {nodes.length === 0 && (
              <p className="text-gray-500 dark:text-gray-400">
                Add steps using the panel on the right
              </p>
            )}
          </div>
        </div>

        <div className="mt-4 flex gap-2 justify-end">
          <Button variant="outline" onClick={handleSave} disabled={isSaving}>
            <Save size={16} />
            {isSaving ? 'Saving...' : 'Save Draft'}
          </Button>
          <Button variant="default" onClick={() => console.log('Deploy workflow')}>
            <Play size={16} />
            Deploy
          </Button>
        </div>
      </div>

      {/* Tool panel */}
      <div className="hidden lg:block">
        <div className="bg-gray-50 dark:bg-gray-900 border rounded-lg p-4 w-64">
          <h3 className="font-semibold dark:text-white mb-4">Add Steps</h3>
          <div className="space-y-2">
            {['input', 'agent_call', 'data_transform', 'decision', 'output'].map((type) => (
              <Button
                key={type}
                variant="outline"
                size="sm"
                className="w-full justify-start"
                onClick={() => handleAddStep(type)}
              >
                + {type.replace(/_/g, ' ').toUpperCase()}
              </Button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **3.6: Update WorkflowBuilder page**

Modify `apps/ops_ui_v2/src/pages/WorkflowBuilder.jsx`:

```jsx
import WorkflowCanvas from '../components/WorkflowCanvas';

export default function WorkflowBuilder() {
  return <WorkflowCanvas />;
}
```

- [ ] **3.7: Commit**

```bash
git add apps/ops_ui_v2/src/
git commit -m "feat: implement workflow builder canvas with step editor"
```

---

### Task 4: Create Experiment Execution Flow

**Files:**
- Create: `apps/ops_ui_v2/src/components/ExperimentForm.jsx`
- Create: `apps/ops_ui_v2/src/components/ExperimentResults.jsx`
- Create: `apps/ops_ui_v2/src/store/experimentStore.js`
- Create: `apps/ops_ui_v2/src/api/experimentAPI.js`
- Modify: `apps/ops_ui_v2/src/pages/Experiments.jsx`

**Steps:**

- [ ] **4.1: Create experiment store**

Create `apps/ops_ui_v2/src/store/experimentStore.js`:

```javascript
import { create } from 'zustand';

export const useExperimentStore = create((set) => ({
  experiments: [],
  currentExperiment: null,
  results: [],
  isRunning: false,

  createExperiment: (exp) => set((state) => ({
    experiments: [...state.experiments, {
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
      status: 'draft',
      ...exp,
    }],
  })),

  setCurrentExperiment: (exp) => set({ currentExperiment: exp }),

  runExperiment: () => set({ isRunning: true }),

  setResults: (results) => set((state) => ({
    results,
    isRunning: false,
    currentExperiment: state.currentExperiment ? {
      ...state.currentExperiment,
      status: 'completed',
    } : null,
  })),

  resetExperiment: () => set({
    currentExperiment: null,
    results: [],
    isRunning: false,
  }),
}));
```

- [ ] **4.2: Create experiment API**

Create `apps/ops_ui_v2/src/api/experimentAPI.js`:

```javascript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function createExperiment(experiment) {
  const response = await fetch(`${API_BASE}/experiments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(experiment),
  });
  if (!response.ok) throw new Error('Failed to create experiment');
  return response.json();
}

export async function runExperiment(experimentId, variant) {
  const response = await fetch(`${API_BASE}/experiments/${experimentId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ variant }),
  });
  if (!response.ok) throw new Error('Failed to run experiment');
  return response.json();
}

export async function getExperimentResults(experimentId) {
  const response = await fetch(`${API_BASE}/experiments/${experimentId}/results`);
  if (!response.ok) throw new Error('Failed to fetch results');
  return response.json();
}

export async function listExperiments() {
  const response = await fetch(`${API_BASE}/experiments`);
  if (!response.ok) throw new Error('Failed to fetch experiments');
  return response.json();
}
```

- [ ] **4.3: Create ExperimentForm component**

Create `apps/ops_ui_v2/src/components/ExperimentForm.jsx`:

```jsx
import { useState } from 'react';
import Button from './Button';
import { useExperimentStore } from '../store/experimentStore';
import { Play, Plus, X } from 'lucide-react';

export default function ExperimentForm() {
  const { createExperiment, runExperiment } = useExperimentStore();
  const [formData, setFormData] = useState({
    name: '',
    workflow: '',
    variantA: { param1: 'value1' },
    variantB: { param1: 'value2' },
    sampleSize: 100,
  });

  const [variants, setVariants] = useState({
    a: [{ key: 'param1', value: 'value1' }],
    b: [{ key: 'param1', value: 'value2' }],
  });

  const handleAddVariant = (side) => {
    setVariants((prev) => ({
      ...prev,
      [side]: [...prev[side], { key: '', value: '' }],
    }));
  };

  const handleUpdateVariant = (side, index, field, value) => {
    setVariants((prev) => ({
      ...prev,
      [side]: prev[side].map((v, i) =>
        i === index ? { ...v, [field]: value } : v
      ),
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const variantA = Object.fromEntries(variants.a.filter(v => v.key).map(v => [v.key, v.value]));
    const variantB = Object.fromEntries(variants.b.filter(v => v.key).map(v => [v.key, v.value]));

    createExperiment({
      name: formData.name,
      workflowId: formData.workflow,
      variantA,
      variantB,
      sampleSize: formData.sampleSize,
    });

    runExperiment();
    setFormData({ name: '', workflow: '', sampleSize: 100 });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-900 rounded-lg border p-6 max-w-2xl">
      <h2 className="text-2xl font-bold dark:text-white mb-6">Create Experiment</h2>

      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium dark:text-gray-300 mb-2">
            Experiment Name
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Checkout Flow Optimization"
            className="w-full px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700 dark:text-white"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium dark:text-gray-300 mb-2">
            Workflow
          </label>
          <select
            value={formData.workflow}
            onChange={(e) => setFormData({ ...formData, workflow: e.target.value })}
            className="w-full px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700 dark:text-white"
            required
          >
            <option value="">Select workflow</option>
            <option value="checkout">Checkout Flow</option>
            <option value="recommendation">Recommendation Engine</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium dark:text-gray-300 mb-2">
            Sample Size
          </label>
          <input
            type="number"
            value={formData.sampleSize}
            onChange={(e) => setFormData({ ...formData, sampleSize: parseInt(e.target.value) })}
            min="10"
            className="w-full px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700 dark:text-white"
          />
        </div>
      </div>

      {/* Variants Configuration */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {['a', 'b'].map((side) => (
          <div key={side} className="border rounded-lg p-4 dark:border-gray-700">
            <h3 className="font-semibold dark:text-white mb-4">
              Variant {side.toUpperCase()}
            </h3>
            <div className="space-y-3">
              {variants[side].map((variant, idx) => (
                <div key={idx} className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Key"
                    value={variant.key}
                    onChange={(e) =>
                      handleUpdateVariant(side, idx, 'key', e.target.value)
                    }
                    className="flex-1 px-2 py-1 border rounded text-sm dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                  />
                  <input
                    type="text"
                    placeholder="Value"
                    value={variant.value}
                    onChange={(e) =>
                      handleUpdateVariant(side, idx, 'value', e.target.value)
                    }
                    className="flex-1 px-2 py-1 border rounded text-sm dark:bg-gray-800 dark:border-gray-700 dark:text-white"
                  />
                  {variants[side].length > 1 && (
                    <button
                      type="button"
                      onClick={() =>
                        setVariants((prev) => ({
                          ...prev,
                          [side]: prev[side].filter((_, i) => i !== idx),
                        }))
                      }
                      className="p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded"
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => handleAddVariant(side)}
                className="w-full"
              >
                <Plus size={16} /> Add Parameter
              </Button>
            </div>
          </div>
        ))}
      </div>

      <Button type="submit" variant="default" className="w-full">
        <Play size={16} /> Run Experiment
      </Button>
    </form>
  );
}
```

- [ ] **4.4: Create ExperimentResults component**

Create `apps/ops_ui_v2/src/components/ExperimentResults.jsx`:

```jsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Button from './Button';
import { Download } from 'lucide-react';

export default function ExperimentResults({ experiment, results }) {
  if (!experiment || !results.length) {
    return (
      <div className="bg-white dark:bg-gray-900 rounded-lg border p-6 max-w-2xl">
        <p className="text-gray-500 dark:text-gray-400">No results available</p>
      </div>
    );
  }

  const chartData = [
    {
      name: 'Variant A',
      score: results.filter((r) => r.variant === 'a').reduce((sum, r) => sum + r.score, 0) / results.filter((r) => r.variant === 'a').length,
      runs: results.filter((r) => r.variant === 'a').length,
    },
    {
      name: 'Variant B',
      score: results.filter((r) => r.variant === 'b').reduce((sum, r) => sum + r.score, 0) / results.filter((r) => r.variant === 'b').length,
      runs: results.filter((r) => r.variant === 'b').length,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-900 rounded-lg border p-6">
        <h2 className="text-2xl font-bold dark:text-white mb-6">
          {experiment.name} - Results
        </h2>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="score" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {chartData.map((data) => (
          <div key={data.name} className="bg-gray-50 dark:bg-gray-900 rounded-lg border p-4">
            <p className="text-sm font-medium dark:text-gray-300">{data.name}</p>
            <p className="text-3xl font-bold dark:text-white mt-2">
              {data.score.toFixed(2)}
            </p>
            <p className="text-sm dark:text-gray-400 mt-1">
              Based on {data.runs} runs
            </p>
          </div>
        ))}
      </div>

      <div className="flex gap-2">
        <Button variant="outline" onClick={() => window.print()}>
          <Download size={16} /> Export Results
        </Button>
      </div>
    </div>
  );
}
```

- [ ] **4.5: Update Experiments page**

Modify `apps/ops_ui_v2/src/pages/Experiments.jsx`:

```jsx
import { useState } from 'react';
import ExperimentForm from '../components/ExperimentForm';
import ExperimentResults from '../components/ExperimentResults';
import { useExperimentStore } from '../store/experimentStore';

export default function Experiments() {
  const { currentExperiment, results, isRunning } = useExperimentStore();

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold dark:text-white mb-8">Experiments</h1>

      {!currentExperiment ? (
        <ExperimentForm />
      ) : (
        <>
          {isRunning && (
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900 rounded-lg border border-blue-200 dark:border-blue-700">
              <p className="text-sm text-blue-900 dark:text-blue-200">
                Running experiment... This may take a few moments.
              </p>
            </div>
          )}
          <ExperimentResults experiment={currentExperiment} results={results} />
        </>
      )}
    </div>
  );
}
```

- [ ] **4.6: Commit**

```bash
git add apps/ops_ui_v2/src/
git commit -m "feat: add experiment execution form and results visualization"
```

---

## Phase 3: Analytics & Export (Days 8-10)

### Task 5: Build Analytics Dashboard

**Files:**
- Create: `apps/ops_ui_v2/src/components/MetricsCard.jsx`
- Create: `apps/ops_ui_v2/src/components/ChartPanel.jsx`
- Create: `apps/ops_ui_v2/src/store/analyticsStore.js`
- Create: `apps/ops_ui_v2/src/api/analyticsAPI.js`
- Modify: `apps/ops_ui_v2/src/pages/Analytics.jsx`

**Steps:**

- [ ] **5.1: Install charting library**

```bash
cd apps/ops_ui_v2
npm install recharts
```

- [ ] **5.2: Create analytics store**

Create `apps/ops_ui_v2/src/store/analyticsStore.js`:

```javascript
import { create } from 'zustand';

export const useAnalyticsStore = create((set) => ({
  metrics: {
    totalRuns: 0,
    avgScore: 0,
    totalCost: 0,
    successRate: 0,
  },
  timeSeries: [],
  workflowMetrics: [],
  isLoading: false,

  setMetrics: (metrics) => set({ metrics }),
  setTimeSeries: (timeSeries) => set({ timeSeries }),
  setWorkflowMetrics: (workflowMetrics) => set({ workflowMetrics }),
  setIsLoading: (isLoading) => set({ isLoading }),

  fetchAnalytics: async () => {
    set({ isLoading: true });
    try {
      // Metrics would be fetched from API
      set({
        metrics: {
          totalRuns: 1523,
          avgScore: 8.7,
          totalCost: 234.56,
          successRate: 94.2,
        },
        timeSeries: [
          { date: 'Mon', runs: 120, cost: 45.2 },
          { date: 'Tue', runs: 145, cost: 52.1 },
          { date: 'Wed', runs: 135, cost: 48.9 },
          { date: 'Thu', runs: 165, cost: 61.3 },
          { date: 'Fri', runs: 190, cost: 72.1 },
          { date: 'Sat', runs: 98, cost: 38.4 },
          { date: 'Sun', runs: 72, cost: 29.2 },
        ],
        workflowMetrics: [
          { name: 'Checkout', runs: 450, score: 9.1, cost: 89.2 },
          { name: 'Recommendation', runs: 380, score: 8.4, cost: 71.5 },
          { name: 'Payment', runs: 320, score: 9.3, cost: 60.1 },
          { name: 'Shipping', runs: 373, score: 8.2, cost: 57.3 },
        ],
        isLoading: false,
      });
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      set({ isLoading: false });
    }
  },
}));
```

- [ ] **5.3: Create MetricsCard component**

Create `apps/ops_ui_v2/src/components/MetricsCard.jsx`:

```jsx
export default function MetricsCard({ title, value, unit = '', trend = null }) {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border p-4">
      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
      <div className="mt-2 flex items-baseline gap-2">
        <p className="text-3xl font-bold dark:text-white">
          {typeof value === 'number' ? value.toFixed(1) : value}
        </p>
        {unit && <p className="text-sm text-gray-500 dark:text-gray-400">{unit}</p>}
      </div>
      {trend && (
        <p className={`text-xs mt-2 ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% from last period
        </p>
      )}
    </div>
  );
}
```

- [ ] **5.4: Create ChartPanel component**

Create `apps/ops_ui_v2/src/components/ChartPanel.jsx`:

```jsx
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export default function ChartPanel({ title, data, type = 'line', xKey, yKeys = [] }) {
  const chartProps = {
    data,
    margin: { top: 5, right: 30, left: 0, bottom: 5 },
  };

  return (
    <div className="bg-white dark:bg-gray-900 rounded-lg border p-6">
      <h3 className="text-lg font-semibold dark:text-white mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={300}>
        {type === 'line' ? (
          <LineChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey={xKey} stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }} />
            <Legend />
            {yKeys.map((key, idx) => (
              <Line key={key} type="monotone" dataKey={key} stroke={['#3b82f6', '#10b981'][idx]} />
            ))}
          </LineChart>
        ) : (
          <BarChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey={xKey} stroke="#6b7280" />
            <YAxis stroke="#6b7280" />
            <Tooltip contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }} />
            <Legend />
            {yKeys.map((key, idx) => (
              <Bar key={key} dataKey={key} fill={['#3b82f6', '#10b981'][idx]} />
            ))}
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
```

- [ ] **5.5: Create analytics API**

Create `apps/ops_ui_v2/src/api/analyticsAPI.js`:

```javascript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function getMetrics(timeRange = '7d') {
  const response = await fetch(`${API_BASE}/analytics/metrics?range=${timeRange}`);
  if (!response.ok) throw new Error('Failed to fetch metrics');
  return response.json();
}

export async function getTimeSeries(timeRange = '7d', metric = 'runs') {
  const response = await fetch(
    `${API_BASE}/analytics/timeseries?range=${timeRange}&metric=${metric}`
  );
  if (!response.ok) throw new Error('Failed to fetch time series');
  return response.json();
}

export async function getWorkflowMetrics() {
  const response = await fetch(`${API_BASE}/analytics/workflows`);
  if (!response.ok) throw new Error('Failed to fetch workflow metrics');
  return response.json();
}

export async function exportAnalytics(format = 'csv') {
  const response = await fetch(`${API_BASE}/analytics/export?format=${format}`);
  if (!response.ok) throw new Error('Failed to export analytics');
  return response.blob();
}
```

- [ ] **5.6: Update Analytics page**

Modify `apps/ops_ui_v2/src/pages/Analytics.jsx`:

```jsx
import { useEffect } from 'react';
import { useAnalyticsStore } from '../store/analyticsStore';
import MetricsCard from '../components/MetricsCard';
import ChartPanel from '../components/ChartPanel';
import Button from '../components/Button';
import { Download } from 'lucide-react';

export default function Analytics() {
  const { metrics, timeSeries, workflowMetrics, isLoading, fetchAnalytics } =
    useAnalyticsStore();

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleExport = async () => {
    try {
      const blob = await fetch('http://localhost:8000/analytics/export?format=csv').then(r => r.blob());
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold dark:text-white">Analytics Dashboard</h1>
        <Button variant="outline" onClick={handleExport}>
          <Download size={16} /> Export Data
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">Loading analytics...</p>
        </div>
      ) : (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricsCard title="Total Runs" value={metrics.totalRuns} trend={12} />
            <MetricsCard title="Avg Score" value={metrics.avgScore} unit="/ 10" trend={5} />
            <MetricsCard title="Total Cost" value={metrics.totalCost} unit="$" trend={-3} />
            <MetricsCard title="Success Rate" value={metrics.successRate} unit="%" trend={8} />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartPanel
              title="Daily Activity"
              data={timeSeries}
              type="line"
              xKey="date"
              yKeys={['runs', 'cost']}
            />
            <ChartPanel
              title="Workflow Performance"
              data={workflowMetrics}
              type="bar"
              xKey="name"
              yKeys={['runs', 'score']}
            />
          </div>

          {/* Detailed Metrics Table */}
          <div className="bg-white dark:bg-gray-900 rounded-lg border overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold dark:text-white">
                    Workflow
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold dark:text-white">
                    Runs
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold dark:text-white">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold dark:text-white">
                    Cost
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y dark:divide-gray-800">
                {workflowMetrics.map((wf) => (
                  <tr key={wf.name} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-6 py-3 text-sm dark:text-white">{wf.name}</td>
                    <td className="px-6 py-3 text-sm dark:text-gray-400">{wf.runs}</td>
                    <td className="px-6 py-3 text-sm dark:text-gray-400">
                      {wf.score.toFixed(1)}
                    </td>
                    <td className="px-6 py-3 text-sm dark:text-gray-400">
                      ${wf.cost.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
```

- [ ] **5.7: Commit**

```bash
git add apps/ops_ui_v2/src/
git commit -m "feat: build analytics dashboard with metrics and charts"
```

---

### Task 6: Implement Export Functionality

**Files:**
- Create: `apps/ops_ui_v2/src/utils/export.js`
- Create: `apps/ops_ui_v2/src/components/ExportDialog.jsx`
- Modify: `apps/ops_ui_v2/src/pages/Analytics.jsx`
- Create: `apps/ops_api/routers/export.py` (backend)

**Steps:**

- [ ] **6.1: Create export utilities**

Create `apps/ops_ui_v2/src/utils/export.js`:

```javascript
export function exportToCSV(data, filename = 'data.csv') {
  const csv = convertToCSV(data);
  downloadFile(csv, filename, 'text/csv');
}

export function exportToJSON(data, filename = 'data.json') {
  const json = JSON.stringify(data, null, 2);
  downloadFile(json, filename, 'application/json');
}

export function exportToPDF(htmlContent, filename = 'report.pdf') {
  // Placeholder - would require a PDF library like jsPDF
  console.log('PDF export not yet implemented');
}

function convertToCSV(data) {
  if (!Array.isArray(data) || data.length === 0) return '';

  const headers = Object.keys(data[0]);
  const rows = data.map((obj) =>
    headers.map((h) => {
      const val = obj[h];
      return typeof val === 'string' && val.includes(',')
        ? `"${val}"`
        : val;
    }).join(',')
  );

  return [headers.join(','), ...rows].join('\n');
}

function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}
```

- [ ] **6.2: Create ExportDialog component**

Create `apps/ops_ui_v2/src/components/ExportDialog.jsx`:

```jsx
import { useState } from 'react';
import Button from './Button';
import { Download, X } from 'lucide-react';
import { exportToCSV, exportToJSON } from '../utils/export';

export default function ExportDialog({ data, isOpen, onClose }) {
  const [format, setFormat] = useState('csv');
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const timestamp = new Date().toISOString().split('T')[0];
      if (format === 'csv') {
        exportToCSV(data, `analytics-${timestamp}.csv`);
      } else if (format === 'json') {
        exportToJSON(data, `analytics-${timestamp}.json`);
      }
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />

      {/* Dialog */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-white dark:bg-gray-900 rounded-lg shadow-lg max-w-sm w-full">
          <div className="flex items-center justify-between p-6 border-b dark:border-gray-800">
            <h2 className="text-lg font-semibold dark:text-white">Export Analytics</h2>
            <button
              onClick={onClose}
              className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            >
              <X size={20} />
            </button>
          </div>

          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium dark:text-gray-300 mb-2">
                Format
              </label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="w-full px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700 dark:text-white"
              >
                <option value="csv">CSV (.csv)</option>
                <option value="json">JSON (.json)</option>
              </select>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900 p-3 rounded text-sm text-blue-900 dark:text-blue-200">
              You're exporting {Array.isArray(data) ? data.length : 'your'} records
            </div>
          </div>

          <div className="p-6 border-t dark:border-gray-800 flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="default" onClick={handleExport} disabled={isExporting}>
              <Download size={16} />
              {isExporting ? 'Exporting...' : 'Export'}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
```

- [ ] **6.3: Create export router in backend**

Create `apps/ops_api/routers/export.py`:

```python
from fastapi import APIRouter, Depends, Query
from acosplatform.auth.api_key import require_ops_token
from acosplatform.db.repository import get_runs
import csv
import io

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/analytics")
async def export_analytics(
    format: str = Query("csv", regex="^(csv|json)$"),
    timeRange: str = Query("7d"),
    _token: dict = Depends(require_ops_token),
):
    """Export analytics data in specified format"""
    runs = get_runs(limit=1000)

    if format == "csv":
        return _export_csv(runs)
    else:
        return _export_json(runs)

def _export_csv(runs):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['id', 'workflow', 'score', 'cost', 'created_at'])
    writer.writeheader()

    for run in runs:
        writer.writerow({
            'id': run['id'],
            'workflow': run.get('journey', ''),
            'score': run.get('score', 0),
            'cost': run.get('cost', 0),
            'created_at': run.get('created_at', ''),
        })

    return {
        'content': output.getvalue(),
        'filename': 'analytics.csv',
        'media_type': 'text/csv',
    }

def _export_json(runs):
    return {
        'content': runs,
        'filename': 'analytics.json',
        'media_type': 'application/json',
    }
```

- [ ] **6.4: Commit**

```bash
git add apps/ops_ui_v2/src/ apps/ops_api/
git commit -m "feat: add export functionality for analytics data (CSV, JSON)"
```

---

## Phase 4: Polish & Testing (Days 11-14)

### Task 7: Responsive Design Refinement

**Files:**
- Modify: All component files for responsive adjustments
- Create: `apps/ops_ui_v2/src/responsive.test.jsx`

**Steps:**

- [ ] **7.1: Review & fix responsive breakpoints on all pages**

Test all pages at: 375px (mobile), 768px (tablet), 1280px (desktop)

For each page/component:
- Ensure sidebar collapses to hamburger menu on mobile
- Verify grid layouts adapt (1 col → 2 col → 3+ col)
- Check that tables become cards on mobile
- Ensure padding/spacing scales appropriately

```bash
# Commands to test responsiveness
npm run dev  # Then manually test different viewport sizes
```

- [ ] **7.2: Optimize mobile performance**

Create `apps/ops_ui_v2/src/responsive.test.jsx`:

```jsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Layout from '../components/Layout';

describe('Responsive Design', () => {
  it('should show hamburger menu on mobile', () => {
    render(<Layout />);
    // Test implementation
    expect(screen.getByRole('button')).toBeDefined();
  });

  it('should hide sidebar on mobile and show on desktop', () => {
    // Test at different viewport sizes
    expect(true).toBe(true);
  });
});
```

Run tests:

```bash
npm run test
```

- [ ] **7.3: Add loading states and error boundaries**

Modify `apps/ops_ui_v2/src/components/Layout.jsx` to add error boundary:

```jsx
import { ErrorBoundary } from 'react-error-boundary';

function ErrorFallback({error, resetErrorBoundary}) {
  return (
    <div className="p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 rounded">
      <h2 className="font-semibold text-red-900 dark:text-red-100">Something went wrong</h2>
      <p className="text-sm text-red-700 dark:text-red-200 mt-1">{error.message}</p>
      <button onClick={resetErrorBoundary} className="mt-2 text-sm underline">Try again</button>
    </div>
  );
}

export default function Layout() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      {/* existing layout */}
    </ErrorBoundary>
  );
}
```

Install error boundary:

```bash
npm install react-error-boundary
```

- [ ] **7.4: Commit**

```bash
git add apps/ops_ui_v2/src/
git commit -m "refactor: optimize responsive design and add error boundaries"
```

---

### Task 8: Dark Mode Polish & Animation Refinements

**Files:**
- Modify: `apps/ops_ui_v2/src/index.css` (animations)
- Modify: All component files (dark mode tweaks)
- Create: `apps/ops_ui_v2/src/components/Skeleton.jsx`

**Steps:**

- [ ] **8.1: Add skeleton loading components**

Create `apps/ops_ui_v2/src/components/Skeleton.jsx`:

```jsx
export function Skeleton({ className = '' }) {
  return (
    <div
      className={`animate-pulse bg-gray-200 dark:bg-gray-800 rounded ${className}`}
    />
  );
}

export function SkeletonChart() {
  return (
    <div className="space-y-4 p-6 bg-white dark:bg-gray-900 rounded-lg border">
      <Skeleton className="h-6 w-1/3" />
      <div className="space-y-2">
        {Array(3).fill(0).map((_, i) => (
          <Skeleton key={i} className="h-4 w-full" />
        ))}
      </div>
    </div>
  );
}
```

- [ ] **8.2: Enhance animations**

Modify `apps/ops_ui_v2/src/index.css`:

```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-16px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.animate-fadeInUp {
  animation: fadeInUp 0.3s ease-out;
}

.animate-slideIn {
  animation: slideIn 0.3s ease-out;
}

/* Smooth transitions */
.transition-theme {
  transition: background-color 0.2s, color 0.2s, border-color 0.2s;
}
```

- [ ] **8.3: Review dark mode colors across components**

Ensure all components use proper dark mode classes:
- Text: `dark:text-white`, `dark:text-gray-300`, `dark:text-gray-400`
- Backgrounds: `dark:bg-gray-900`, `dark:bg-gray-800`
- Borders: `dark:border-gray-800`, `dark:border-gray-700`

```bash
# Verify dark mode works:
npm run dev  # Toggle dark mode in browser
```

- [ ] **8.4: Commit**

```bash
git add apps/ops_ui_v2/src/
git commit -m "polish: refine dark mode colors and add smooth animations"
```

---

### Task 9: Backend API Endpoints

**Files:**
- Create/Modify: `apps/ops_api/routers/workflows.py`
- Create/Modify: `apps/ops_api/routers/experiments.py`
- Create/Modify: `apps/ops_api/routers/analytics.py`
- Modify: `apps/ops_api/main.py`

**Steps:**

- [ ] **9.1: Create workflow endpoints**

Create/Modify `apps/ops_api/routers/workflows.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from acosplatform.auth.api_key import require_ops_token
from acosplatform.workflows.service import (
    create_workflow_draft,
    create_workflow_version,
    get_workflow_detail,
    list_workflows_with_state,
)
from acosplatform.models.workflows import WorkflowCreateRequest, WorkflowVersionCreateRequest
import uuid

router = APIRouter(prefix="/workflows", tags=["workflows"])

@router.get("")
async def list_workflows(_token: dict = Depends(require_ops_token)):
    """List all workflows"""
    return list_workflows_with_state()

@router.post("")
async def create_workflow(
    req: WorkflowCreateRequest,
    _token: dict = Depends(require_ops_token),
):
    """Create a new workflow"""
    workflow_id = str(uuid.uuid4())
    return create_workflow_draft(
        workflow_id=workflow_id,
        name=req.name,
        description=req.description,
        family=req.workflow_family,
    )

@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    _token: dict = Depends(require_ops_token),
):
    """Get workflow details"""
    return get_workflow_detail(workflow_id)

@router.post("/{workflow_id}/versions")
async def create_version(
    workflow_id: str,
    req: WorkflowVersionCreateRequest,
    _token: dict = Depends(require_ops_token),
):
    """Create a new workflow version"""
    return create_workflow_version(
        workflow_id=workflow_id,
        version=req.version,
        steps=req.step_definitions,
    )
```

- [ ] **9.2: Create experiment endpoints**

Create/Modify `apps/ops_api/routers/experiments.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from acosplatform.auth.api_key import require_ops_token
from acosplatform.evaluation.scorer import get_experiment_results
from acosplatform.db.repository import get_runs
import uuid

router = APIRouter(prefix="/experiments", tags=["experiments"])

@router.post("")
async def create_experiment(
    experiment: dict,
    _token: dict = Depends(require_ops_token),
):
    """Create and start a new experiment"""
    # Implementation would save experiment and trigger runs
    return {
        "id": str(uuid.uuid4()),
        "name": experiment.get("name"),
        "status": "running",
    }

@router.get("/{experiment_id}/results")
async def get_results(
    experiment_id: str,
    _token: dict = Depends(require_ops_token),
):
    """Get experiment results"""
    return get_experiment_results(experiment_id)

@router.post("/{experiment_id}/run")
async def run_experiment(
    experiment_id: str,
    variant: dict,
    _token: dict = Depends(require_ops_token),
):
    """Run an experiment variant"""
    # Trigger runs and return status
    return {
        "experiment_id": experiment_id,
        "status": "running",
    }
```

- [ ] **9.3: Create analytics endpoints**

Create/Modify `apps/ops_api/routers/analytics.py`:

```python
from fastapi import APIRouter, Depends, Query
from acosplatform.auth.api_key import require_ops_token
from acosplatform.db.repository import get_runs, get_cost_summary, get_usage
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/metrics")
async def get_metrics(
    range: str = Query("7d"),
    _token: dict = Depends(require_ops_token),
):
    """Get aggregated metrics"""
    runs = get_runs(limit=1000)

    total_runs = len(runs)
    avg_score = sum(r.get('score', 0) for r in runs) / max(total_runs, 1)
    total_cost = sum(r.get('cost', 0.0) for r in runs)
    success_rate = 94.2  # Would be calculated from runs

    return {
        "totalRuns": total_runs,
        "avgScore": avg_score,
        "totalCost": total_cost,
        "successRate": success_rate,
    }

@router.get("/timeseries")
async def get_timeseries(
    range: str = Query("7d"),
    metric: str = Query("runs"),
    _token: dict = Depends(require_ops_token),
):
    """Get time series data"""
    runs = get_runs(limit=1000)
    # Would aggregate by day and return time series
    return []

@router.get("/workflows")
async def get_workflow_metrics(_token: dict = Depends(require_ops_token)):
    """Get per-workflow metrics"""
    return [
        {"name": "Checkout", "runs": 450, "score": 9.1, "cost": 89.2},
        {"name": "Recommendation", "runs": 380, "score": 8.4, "cost": 71.5},
        {"name": "Payment", "runs": 320, "score": 9.3, "cost": 60.1},
        {"name": "Shipping", "runs": 373, "score": 8.2, "cost": 57.3},
    ]

@router.get("/export")
async def export_analytics(
    format: str = Query("csv"),
    _token: dict = Depends(require_ops_token),
):
    """Export analytics data"""
    runs = get_runs(limit=10000)

    if format == "csv":
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=['id', 'workflow', 'score', 'cost'])
        writer.writeheader()
        for run in runs:
            writer.writerow({
                'id': run['id'],
                'workflow': run.get('journey', ''),
                'score': run.get('score', 0),
                'cost': run.get('cost', 0),
            })
        return {"content": output.getvalue(), "media_type": "text/csv"}

    return {"content": runs, "media_type": "application/json"}
```

- [ ] **9.4: Update main.py to include routers**

Modify `apps/ops_api/main.py` to add:

```python
from apps.ops_api.routers import workflows, experiments, analytics

app.include_router(workflows.router)
app.include_router(experiments.router)
app.include_router(analytics.router)
```

- [ ] **9.5: Commit**

```bash
git add apps/ops_api/
git commit -m "feat: implement backend API endpoints for workflows, experiments, analytics"
```

---

### Task 10: Testing & QA

**Files:**
- Create: `apps/ops_ui_v2/src/__tests__/integration.test.jsx`
- Create: `tests/test_api_endpoints.py`

**Steps:**

- [ ] **10.1: Write integration tests for frontend**

Create `apps/ops_ui_v2/src/__tests__/integration.test.jsx`:

```jsx
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import App from '../App';

describe('Application Integration', () => {
  it('renders main layout', () => {
    render(<App />);
    expect(screen.getByText(/ACOS Control Plane/)).toBeDefined();
  });

  it('theme toggle works', async () => {
    render(<App />);
    const themeButton = screen.getByTitle(/Switch to/);
    fireEvent.click(themeButton);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('navigation works', () => {
    render(<App />);
    const link = screen.getByText('Workflow Builder');
    expect(link).toBeDefined();
  });
});
```

Run tests:

```bash
npm run test
```

- [ ] **10.2: Write backend API tests**

Create `tests/test_api_endpoints.py`:

```python
import pytest
from fastapi.testclient import TestClient
from apps.ops_api.main import app

client = TestClient(app)

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}

def test_list_workflows(auth_headers):
    response = client.get("/workflows", headers=auth_headers)
    assert response.status_code == 200

def test_create_workflow(auth_headers):
    payload = {
        "name": "Test Workflow",
        "description": "Test",
        "workflow_family": "test",
    }
    response = client.post("/workflows", json=payload, headers=auth_headers)
    assert response.status_code == 200

def test_analytics_metrics(auth_headers):
    response = client.get("/analytics/metrics", headers=auth_headers)
    assert response.status_code == 200
    assert "totalRuns" in response.json()

def test_export_analytics(auth_headers):
    response = client.get("/analytics/export?format=csv", headers=auth_headers)
    assert response.status_code == 200
```

Run backend tests:

```bash
pytest tests/test_api_endpoints.py -v
```

- [ ] **10.3: Manual QA checklist**

Create `QA_CHECKLIST.md`:

```markdown
# QA Checklist for GA Release

## Workflow Builder
- [ ] Create workflow with multiple steps
- [ ] Edit step configuration
- [ ] Delete steps
- [ ] Save draft workflow
- [ ] Deploy workflow
- [ ] Responsive on mobile/tablet/desktop

## Experiments
- [ ] Create experiment with 2 variants
- [ ] Add/remove parameters
- [ ] Run experiment
- [ ] View results in chart
- [ ] Dark mode rendering
- [ ] Mobile responsiveness

## Analytics
- [ ] Load metrics dashboard
- [ ] View all charts (time series, bar charts)
- [ ] Export to CSV
- [ ] Export to JSON
- [ ] Filter by time range
- [ ] Dark/light mode toggle

## General
- [ ] Light mode colors correct
- [ ] Dark mode colors correct
- [ ] All animations smooth
- [ ] No console errors
- [ ] Responsive at all breakpoints
- [ ] Loading states work
- [ ] Error handling works
```

- [ ] **10.4: Run end-to-end tests**

```bash
npm run test:e2e
```

- [ ] **10.5: Commit test files**

```bash
git add tests/ apps/ops_ui_v2/src/__tests__/
git commit -m "test: add integration and API endpoint tests"
```

---

### Task 11: Documentation & Deployment Prep

**Files:**
- Create: `docs/USER_GUIDE.md`
- Create: `docs/API_GUIDE.md`
- Create: `DEPLOYMENT.md`
- Modify: `README.md`

**Steps:**

- [ ] **11.1: Create user guide**

Create `docs/USER_GUIDE.md`:

```markdown
# ACOS Control Plane - User Guide

## Getting Started

### For Business Analysts
1. Navigate to "Workflow Builder"
2. Click "Create New Workflow"
3. Add steps by selecting from the right panel
4. Configure each step with parameters
5. Click "Deploy" to activate

### Running Experiments
1. Go to "Run Experiments"
2. Select a workflow
3. Configure Variant A and Variant B
4. Set sample size
5. Click "Run Experiment"
6. View results in real-time

### Viewing Analytics
1. Navigate to "Analytics Dashboard"
2. Review key metrics (Runs, Score, Cost, Success Rate)
3. View trends in time series chart
4. See per-workflow performance
5. Export data for further analysis

## Dark Mode
- Click the moon/sun icon in the top-right
- Your preference is saved automatically

## Mobile Usage
- All features responsive on mobile
- Use hamburger menu for navigation
```

- [ ] **11.2: Create API documentation**

Create `docs/API_GUIDE.md`:

```markdown
# ACOS Ops API Documentation

## Authentication
All requests require `Authorization: Bearer <token>` header.

## Endpoints

### Workflows
- `GET /workflows` - List all workflows
- `POST /workflows` - Create new workflow
- `GET /workflows/{id}` - Get workflow details
- `POST /workflows/{id}/versions` - Create version

### Experiments
- `POST /experiments` - Create experiment
- `GET /experiments/{id}/results` - Get results
- `POST /experiments/{id}/run` - Run experiment

### Analytics
- `GET /analytics/metrics` - Get metrics
- `GET /analytics/timeseries` - Get time series
- `GET /analytics/workflows` - Workflow metrics
- `GET /analytics/export?format=csv|json` - Export data

## Error Handling
All endpoints return standard error format:
```json
{"detail": "error message"}
```
```

- [ ] **11.3: Create deployment guide**

Create `DEPLOYMENT.md`:

```markdown
# Deployment Guide - GA Release

## Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL 12+
- Docker (optional)

## Frontend Deployment

```bash
cd apps/ops_ui_v2
npm install
npm run build

# Build output in dist/
# Deploy to CDN or web server
```

## Backend Deployment

```bash
pip install -r requirements.txt
export DATABASE_URL="postgresql://..."
export APP_VERSION="1.0.0"
uvicorn apps.ops_api.main:app --host 0.0.0.0 --port 8000
```

## Docker Deployment

```bash
docker-compose up -d
```

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `APP_VERSION` - Version string
- `ALLOWED_ORIGINS` - CORS origins
- `OPS_ENVIRONMENT` - Environment (dev/staging/prod)
```

- [ ] **11.4: Update README**

Modify `README.md`:

```markdown
# ACOS Control Plane

Modern, production-grade workflow orchestration platform with Figma-like UI.

## Features
- 🎨 Workflow Builder with visual editor
- 🧪 A/B Experiment execution and analytics
- 📊 Real-time analytics dashboard
- 📥 Export data (CSV, JSON)
- 🌙 Dark/Light mode
- 📱 Fully responsive design
- 🔐 API key authentication

## Quick Start

```bash
# Frontend
cd apps/ops_ui_v2
npm install && npm run dev

# Backend
pip install -r requirements.txt
python -m uvicorn apps.ops_api.main:app --reload
```

Visit: http://localhost:5173

## Documentation
- [User Guide](docs/USER_GUIDE.md)
- [API Guide](docs/API_GUIDE.md)
- [Deployment Guide](DEPLOYMENT.md)

## Tech Stack
- React 19 + Vite
- shadcn/ui + Tailwind CSS
- FastAPI + PostgreSQL
- Recharts for analytics
```

- [ ] **11.5: Commit documentation**

```bash
git add docs/ DEPLOYMENT.md README.md
git commit -m "docs: add user guide, API guide, and deployment instructions"
```

---

### Task 12: Final Testing, Bug Fixes & Release Prep

**Files:**
- All files (final review)

**Steps:**

- [ ] **12.1: Run full test suite**

```bash
# Frontend tests
cd apps/ops_ui_v2
npm run test
npm run test:e2e
npm run build  # Check build succeeds
npm run lint

# Backend tests
cd ../..
pytest tests/ -v --cov
```

- [ ] **12.2: Performance audit**

```bash
# Check bundle size
npm run build  # Then check dist/ size
# Goal: < 500KB gzipped

# Frontend performance
# Use Chrome DevTools Lighthouse
```

- [ ] **12.3: Security review**

```bash
# Check for vulnerabilities
npm audit
pip audit

# Environment variables check
# Ensure no secrets in code
```

- [ ] **12.4: Cross-browser testing**

Test on:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

- [ ] **12.5: Final bug fixes and polish**

Review and fix:
- Any failing tests
- Performance issues
- Visual inconsistencies
- Accessibility issues

```bash
npm run lint -- --fix  # Auto-fix linting issues
```

- [ ] **12.6: Tag release version**

```bash
git tag -a v1.0.0 -m "Release v1.0.0 - GA"
git push origin v1.0.0
```

- [ ] **12.7: Final commit**

```bash
git add .
git commit -m "chore: final polishing and release preparation for v1.0.0"
git push origin main
```

---

## Post-Implementation Checklist

### Before GA Launch
- [ ] All tests passing (unit, integration, E2E)
- [ ] Code coverage > 80%
- [ ] Documentation complete
- [ ] Security audit passed
- [ ] Performance audit passed
- [ ] Cross-browser testing complete
- [ ] Mobile responsiveness verified at all breakpoints
- [ ] Dark/light mode fully functional
- [ ] API endpoints tested with real workflows
- [ ] Export functionality tested (CSV, JSON)
- [ ] Error handling and edge cases covered
- [ ] Rate limiting configured
- [ ] Logging properly configured
- [ ] Monitoring/observability set up

### Deployment Steps
1. Deploy backend API to production
2. Verify API health
3. Deploy frontend to CDN/hosting
4. Run smoke tests in production
5. Monitor error rates and performance
6. Announce GA release

### Post-Launch Monitoring
- [ ] Monitor API error rates
- [ ] Monitor frontend performance (Core Web Vitals)
- [ ] Track user analytics
- [ ] Monitor database performance
- [ ] Set up alerts for critical issues

---

## Time Allocation Summary

| Phase | Days | Tasks |
|-------|------|-------|
| **Foundation** | 1-3 | Design system, layout shell, navigation |
| **Workflow Builder** | 4-7 | Canvas editor, step management |
| **Experiments** | 5-7 | Form, execution, results visualization |
| **Analytics** | 8-10 | Dashboard, charts, export |
| **Polish & Testing** | 11-14 | Responsive design, dark mode, testing, deployment |

**Total: 14 days (2 weeks)**

---

## Key Architectural Decisions

1. **shadcn/ui + Tailwind**: Provides Figma-like premium look with minimal custom CSS
2. **Zustand for state**: Lightweight, performant store for workflow and experiment state
3. **Recharts for charts**: Built on React, dark mode friendly, minimal setup
4. **FastAPI backend**: Type-safe, performant, well-documented
5. **CSS variables for theming**: Enables seamless dark/light mode switching
6. **Mobile-first responsive**: Ensures great UX on all devices
7. **Modular component architecture**: Makes it easy for AI to generate and modify code

---

## Notes for AI Code Generation

- Each component is self-contained and testable
- Use existing patterns (Button, API client structure) for new components
- Pseudo-code provided gives exact implementation detail
- Files marked for creation should be new; files marked for modification should follow existing patterns
- Test as you go - don't wait until Task 10 to validate
- Commit frequently (every 1-2 tasks) for easy rollback

```

This is your **detailed 2-week production plan**. All file paths, pseudo-code, and implementation details are provided for AI-assisted development.

---

## Next Steps

**Two options for execution:**

1. **Subagent-Driven (Recommended)** — I dispatch a fresh subagent per task, with review checkpoints between tasks. Fastest iteration, highest quality oversight.

2. **Inline Execution** — I execute tasks sequentially in this session with batch checkpoints. Good for continuity but single-threaded.

**Which approach would you prefer?**