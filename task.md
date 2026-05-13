# ACOS — Task Checklist

## Phases 1–12: Core Build, V2 Dashboard, & Comprehensive Coverage ✅ Complete

## Phase 13: Live API Integration

### Sprint 10 — Database Seeding & Models
- [x] INT-01: Verify Postgres models for Agents and Skills exist in `acosplatform/db/repository.py`.
- [x] INT-02: Create `seed_data.py` to orchestrate default ecosystem entity insertion.

### Sprint 11 — Backend APIs (FastAPI)
- [x] INT-03: Create FastAPI routes for `GET /api/v1/agents` wrapping DB queries.
- [x] INT-04: Create FastAPI routes for `GET /api/v1/skills` wrapping DB queries.
- [x] INT-05: Integrate routers into `ops_api/main.py` securely with CORS.

### Sprint 12 — Frontend Integration (React)
- [x] INT-06: Formulate data fetching hooks integrating `ops_ui_v2` with `localhost:8000`.
- [x] INT-07: Extract `MOCK_AGENTS` and `MOCK_SKILLS` from the UI files and bind dynamic API fetches.
- [x] INT-08: Run full stack `ops_ui_v2` + `ops_api` integration testing to formally verify.

## Phase 15: UX Polish & Lifecycle Operations
### Sprint 13 — Resolving Day 1 Feedback
- [x] FIX-01: Remove Ops token requirement for Workflows in `main.py` and implement `POST` and `PATCH` endpoints for Agents and Skills.
- [x] FIX-02: Implement `Workflows.jsx` frontend view to render the list of workflows securely.
- [x] FIX-03: Add creating/deploying functionality (Modals + fetch POST) and enable/disable toggles to `Agents.jsx` and `Skills.jsx`.
- [x] FIX-04: Enhance UI readability (contrast, font sizing) and introduce Skeleton Loaders for all async `fetch` delays.

## Phase 16: UX Masterclass
### Sprint 14 — Premium Design System Refactor
- [x] UX-01: Inject `Inter` and `Outfit` fonts into `index.html` and rewrite global root CSS variables for a modern HSL dark mode.
- [x] UX-02: Upgrade the Sidebar navigation with active glow states and glassmorphism.
- [x] UX-03: Implement fluid `translateY` micro-animations and glowing status dots in `Agents.jsx` & `Skills.jsx`.
- [x] UX-04: Refactor `Widget.css` and `Lists.css` to remove harsh borders in favor of deep drop shadows and transluscent paneling.

## Phase 17: Interactive Workflow Configurator
### Sprint 15 — Backend & UI Editor
- [x] WF-01: Update `WorkflowVersionCreateRequest` and `create_workflow_version()` backend schema.
- [x] WF-02: Inject `loadAgents` and `loadSkills` into `WorkflowRegistry.jsx` to fetch data.
- [x] WF-03: Create the `WorkflowEditor` React component with Agent Binding dropdowns.
- [x] WF-04: Implement Monaco/JSON editor for Step Definitions schema editing.
- [x] WF-05: Update payload submissions to accurately send bindings and JSON schemas to the database.

## Phase 18: Enhanced Entity Factory
### Sprint 16 — Dynamic Create Forms
- [x] EF-01: Build `CreateAgentForm` in `Agents.jsx` with dynamic Tech Stack fields (Google ADK default).
- [x] EF-02: Build `CreateSkillForm` in `Skills.jsx` with dynamic integration options.
- [x] EF-03: Implement "Immediate" vs "Next Cycle" deployment lifecycle radio toggles.
- [x] EF-04: Update `POST` payloads to transmit new metadata (`tech_stack`, modified `status`).

## Phase 19: Visual Orchestrator & Jira Workflows
### Sprint 17 — Interactive Nodes & Registry
- [x] VO-01: Seed PostgreSQL with default Jira-style Workflows (E-Commerce, IT Support, Auto-Triage).
- [x] VO-02: Refactor `WorkflowRegistry.jsx` to mirror `Agents.jsx`'s glassmorphic list layout.
- [x] VO-03: Implement "Create from Template" Jira-style modal for Workflow creation.
- [x] VO-04: Rip `ReactFlow` from Simulation and create `WorkflowCanvas.jsx` node builder.

## Phase 20: Robust Workflow Editor GUI
### Sprint 18 — Enterprise Graphical Orchestration
- [x] WE-01: Wrap `WorkflowCanvas` with `<ReactFlowProvider>` to implement flawless `screenToFlowPosition` geometry calculation.
- [x] WE-02: Extract left toolbox into `NodeSidebar.jsx` featuring dynamic, categorized Draggables (Triggers, Agents, Integrations).
- [x] WE-03: Create `NodeConfigPanel.jsx`, an interactive right-drawer to deeply edit JSON payload configurations of a selected Node.
- [x] WE-04: Wire keyboard/graph lifecycle actions (`onNodesDelete`) and Backend Patch saving.

## Phase 21: Rich Workflow Creator Wizard
### Sprint 19 — Premium Orchestration Onboarding
- [x] WZ-01: Implement multi-step wizard state (`wizardStep 1` and `wizardStep 2`) inside `WorkflowRegistry.jsx`.
- [x] WZ-02: Build the massive, visual Template Card grid (e.g., E-Commerce Checkout, Blank Flow) with Lucide icons and hover effects.
- [x] WZ-03: Redesign the Step 2 "Name Your Workflow" configuration screen.
- [x] WZ-04: Wire `handleCreate` to accurately extract the generated workflow ID and trigger `setSelectedWorkflowId` for auto-canvas transition.
