# Phase 15 - UX Polish & Lifecycle Operations

## Goal Description
Directly address the 4 critical observations from the Day 1 Demo feedback. This phase transforms the read-only dashboard into a fully intractable lifecycle manager with enhanced visual accessibility.

## User Review Required
Please review the proposed approach for adding "Deploy Agent" and "Author Skill" functionalities. We plan to use simple modal dialogs over the current view to keep the user in context.

## Proposed Changes

### 1. Typography & Readability Refinement
- **CSS Overhaul:** Update `index.css` and `Lists.css` to increase text contrast ratios.
- **Adjustments:** Darken primary text colors on light themes, increase font weights for data cells, and reduce excessive glassmorphic blur where it obscures text.

### 2. Graceful Loading States (Skeleton UI)
- **Delay Mitigation:** Introduce a `isLoading` state in React hooks.
- **UI Feedback:** While `fetch()` is resolving, render a beautiful pulsing skeleton table instead of a jarring empty screen that suddenly "pops" into existence.

### 3. Entity Write Operations (CRUD)
- **Backend POST Routes:** Add `@app.post("/agents")` and `@app.post("/skills")` into `ops_api/main.py`.
- **Frontend Modals:** Wire up the currently dead "Deploy Agent" and "Author Skill" buttons. Clicking them will launch a modal dialog allowing the user to input a name/category and execute a POST request to immediately deploy the entity.
- **Enable/Disable:** Add a toggle switch in the Agent/Skill Editor widget to dynamically patch their `status`.

### 4. Workflows Auth Removal & Build-out
- **Backend:** Strip the `_token: dict = Depends(require_ops_token)` out of the `/workflows` route in `main.py` so the dev frontend can fetch it.
- **Frontend View:** Build `Workflows.jsx` (currently missing) to render the fetched workflows, explaining visually what a Workflow Family is and what capabilities it exposes to the Orchestrator.

## Verification Plan
- Launch the UI natively and verify text contrast passes WCAG AA standards visually.
- Throttled the browser network to "Slow 3G" to observe the Skeleton Loaders.
- Deploy a brand new Agent via the UI and verify it immediately renders in the Postgres-backed list.
- Navigate to Workflows and ensure 403 Forbidden is permanently resolved.
