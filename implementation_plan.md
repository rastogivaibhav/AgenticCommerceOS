# ACOS Ops Dashboard V2 - Implementation Plan

## Goal Description
The current Ops Dashboard is a static, single-file HTML script that provides high-level metrics. The goal of V2 is to transform this into a fully-fledged "Agentic Control Plane" that gives JLP complete visibility and control over the ACOS system.

We will build a modular, beautiful, and dynamic interface for managing Agents, Skills, Workflows, and Live Simulations.

## User Review Required
> [!IMPORTANT]
> **Architecture Shift:** Because of the complexity of the requested features (visual graph editors, code editors with linting, etc.), maintaining a single HTML file is no longer viable. 
> 
> **Proposed Solution:** I propose spinning up a modern Vite + React application in `apps/ops_ui_v2`. This will allow us to use industry-standard libraries like `reactflow` (for the journey planner) and `@monaco-editor/react` (for the skill code editor/linter). Is this architecture approach acceptable?

## Proposed Changes

### 1. Frontend Foundation (Vite + React)
Create a new frontend architecture optimized for complex state management.
- Scaffold a new project using `npx -y create-vite@latest apps/ops_ui_v2 --template react`
- Setup routing (`react-router-dom`) for `/agents`, `/skills`, `/workflow`, and `/simulation`.
- Implement a premium, rich aesthetic with dark mode, glassmorphism, and micro-animations to match the "Superpowers" vibe.

### 2. Agents & Skills Views
Modern, tabular, and card-based views for the system's core entities.
- **List of Agents**: Dashboard showing all active agents, their assigned subsystem (e.g., Returns, Catalog), and health status.
- **List of Skills**: View showing available tools and integrations.

### 3. Deep Editors
- **Agent Editor**: A detail screen to rename agents, assign/remove skills (multi-select), view historical performance ("Report Card"), and monitor recent invocations.
- **Skill Editor**: Implement Monaco Editor (VS Code's editor) in the browser. Allow users to edit skill prompt/code, see real-time linting issues, and a kill-switch for "in-flight" runaway skills.

### 4. Journey Planner & Live Simulation
This is the "crown jewel" of the V2 dashboard.
- **User Journey Planner**: Implement `reactflow` to create a drag-and-drop canvas. Admins can draw logic nodes (Discovery ➔ Purchase ➔ Fulfillment) and drag Agents onto the nodes to handle the tasks.
- **Live Simulation (Train Track)**: A dynamic visualization showing "live traffic" moving through the graph. As an order comes in, the admin watches it move from the "Marketing" node to the "CRM" node, highlighting exactly which Agent is processing it in real-time.

## Verification Plan
### Automated Tests
- Run `npm run build` to ensure the Vite app compiles correctly without errors.
- Add frontend unit tests for complex state logic (like graph node serialization).

### Manual Verification
- Spin up the Vite dev server (`npm run dev`) and test the drag-and-drop workflow planner.
- Test the Skill Editor linting features to ensure bad code throws visible UI warnings.
- Run the [demo_traffic.py](file:///c:/Users/vrast/OneDrive/Apps/Documents/acos/demo_traffic.py) server to simulate data and verify the "Train Track" simulation correctly animates the live traffic across the visual nodes.
