# Session 5 — Real A/B Experiments Wired to DB: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace all stub/local-only A/B experiment code with end-to-end wiring: UI form → ops API → `run_ab_test()` → `run_journey()` × 2 → persist to `experiments` table → UI reads from live API.

**Architecture:** The FastAPI experiments router gains real endpoints that call `run_ab_test()` (synchronous, runs both variants in one request) and read from `get_experiments()`. The Zustand store becomes API-driven. The UI form is simplified to the fields the backend actually needs.

**Tech Stack:** FastAPI, psycopg2 (via existing pool), React 18, Zustand, Tailwind v4 (`@theme inline` M3 Purple tokens), Lucide React icons.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `apps/ops_api/routers/experiments.py` | **Rewrite** | GET list, POST (run experiment), GET by ID |
| `apps/ops_ui_v2/src/store/experimentStore.js` | **Rewrite** | API-driven state: fetch list, create+run, reset |
| `apps/ops_ui_v2/src/components/ExperimentForm.jsx` | **Rewrite** | Simplified form: name, workflow_family, message, customer_id, sampleSize (informational) |
| `apps/ops_ui_v2/src/pages/Experiments.jsx` | **Modify** | Add past-experiments table + `useEffect` mount fetch |
| `apps/ops_ui_v2/src/components/ExperimentResults.jsx` | **Modify** | Consume new API response shape (`variant_a.score`, `variant_b.score`, `winner`) |

**Do NOT touch:**
- `acosplatform/evaluation/scorer.py` — `run_ab_test()` and `score()`
- `acosplatform/journey/engine.py` — `run_journey()`
- `acosplatform/db/repository.py` — `save_experiment()` and `get_experiments()`
- `apps/ops_api/main.py` — dashboard endpoint and router include

---

## Task 1: Rewrite `experiments.py` router

**Files:**
- Rewrite: `apps/ops_api/routers/experiments.py`

Key facts:
- `run_ab_test(name, payload, run_func)` is synchronous — call directly (no `await`)
- `payload` must be `{"message": str, "customer_id": str, "tenant_id": str}`
- `run_ab_test` returns `{experiment, variant_a: {score, run_id}, variant_b: {score, run_id}, winner, experiment_id}`
- `get_experiments()` returns a list of dicts from DB (columns: id, name, variant_a, variant_b, winner, created_at)
- `experiment_id` in URL is a string; cast to `int` before filtering
- Auth: POST requires `require_ops_token`; GET endpoints are unauthenticated (matches `/agents` GET pattern)
- Remove `POST /experiments/{id}/run` — was a stub, replaced by synchronous execution in POST /experiments

- [ ] **Step 1: Rewrite the router file**

```python
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from acosplatform.auth.api_key import require_ops_token
from acosplatform.db.repository import get_experiments
from acosplatform.evaluation.scorer import run_ab_test
from acosplatform.journey.engine import run_journey

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("")
def list_experiments():
    return {"experiments": get_experiments()}


@router.post("")
def create_experiment(body: dict, _token: dict = Depends(require_ops_token)):
    name = body["name"]
    payload = {
        "message": body["message"],
        "customer_id": body["customer_id"],
        "tenant_id": body["tenant_id"],
    }
    result = run_ab_test(
        experiment_name=name,
        payload=payload,
        run_func=run_journey,
    )
    return result


@router.get("/{experiment_id}/results")
def get_experiment_results(experiment_id: str):
    try:
        eid = int(experiment_id)
    except ValueError:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    experiments = get_experiments()
    record = next((e for e in experiments if e.get("id") == eid), None)
    if not record:
        return JSONResponse(status_code=404, content={"error": "Not found"})
    return {"experiment": record}
```

- [ ] **Step 2: Verify the API server starts without errors**

```bash
cd /c/Users/vrast/OneDrive/Apps/Documents/acos
python -c "from apps.ops_api.routers.experiments import router; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Smoke-test POST /experiments manually**

```bash
curl -s -X POST http://localhost:8081/experiments \
  -H "Authorization: Bearer dev-ops-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"plan-test-1","workflow_family":"discovery","customer_id":"cust-1","tenant_id":"default","message":"show me headphones"}' \
  | python -m json.tool
```
Expected: JSON with `"winner"` field (`"A"` or `"B"`).

- [ ] **Step 4: Verify GET /experiments returns the experiment**

```bash
curl -s http://localhost:8081/experiments | python -m json.tool
```
Expected: `{"experiments": [...]}` with at least one record containing `name`, `winner`, `variant_a`, `variant_b`.

- [ ] **Step 5: Verify GET /experiments/1/results**

```bash
curl -s http://localhost:8081/experiments/1/results | python -m json.tool
```
Expected: `{"experiment": {...}}` with the first experiment's record.

- [ ] **Step 6: Verify DB row was inserted**

```bash
psql acos -c "SELECT id, name, winner FROM experiments ORDER BY id DESC LIMIT 5;"
```
Expected: at least one row.

- [ ] **Step 7: Commit**

```bash
git add apps/ops_api/routers/experiments.py
git commit -m "feat: wire experiments router to run_ab_test and DB"
```

---

## Task 2: Rewrite `experimentStore.js`

**Files:**
- Rewrite: `apps/ops_ui_v2/src/store/experimentStore.js`

Key facts:
- API base is `http://localhost:8081` (ops API port) — **not** `window.location.origin`
- Token: `localStorage.getItem('ops_token') || 'dev-ops-token'`
- `fetchExperiments` calls `GET /experiments` with `Authorization` header
- `createExperiment(formData)` POSTs to `/experiments`, sets `isRunning` true before, false after, then calls `fetchExperiments()` to refresh list and sets `currentExperiment` to the response
- Remove `setResults()` — results live in `currentExperiment` from API response
- Keep `resetExperiment()` and `setCurrentExperiment()`

- [ ] **Step 1: Rewrite the store**

```javascript
import { create } from 'zustand';

const API = 'http://localhost:8081';
const getToken = () => localStorage.getItem('ops_token') || 'dev-ops-token';

export const useExperimentStore = create((set, get) => ({
  experiments: [],
  currentExperiment: null,
  isRunning: false,

  fetchExperiments: async () => {
    try {
      const res = await fetch(`${API}/experiments`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      set({ experiments: data.experiments || [] });
    } catch (e) {
      console.error('fetchExperiments error', e);
    }
  },

  createExperiment: async (formData) => {
    set({ isRunning: true });
    try {
      const res = await fetch(`${API}/experiments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify(formData),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error('createExperiment API error', err);
        return;
      }
      const result = await res.json();
      set({ currentExperiment: result });
      await get().fetchExperiments();
    } catch (e) {
      console.error('createExperiment error', e);
    } finally {
      set({ isRunning: false });
    }
  },

  setCurrentExperiment: (exp) => set({ currentExperiment: exp }),

  resetExperiment: () => set({
    currentExperiment: null,
    isRunning: false,
  }),
}));
```

- [ ] **Step 2: Verify no import errors**

```bash
cd /c/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_ui_v2
node --input-type=module <<< "import('./src/store/experimentStore.js').then(() => console.log('OK'))"
```
Expected: `OK` (or silent success without syntax errors — Vite will catch them at build time).

- [ ] **Step 3: Commit**

```bash
git add apps/ops_ui_v2/src/store/experimentStore.js
git commit -m "feat: experimentStore rewritten to call live API"
```

---

## Task 3: Rewrite `ExperimentForm.jsx`

**Files:**
- Rewrite: `apps/ops_ui_v2/src/components/ExperimentForm.jsx`

Key facts:
- Old form: experiment name + workflow select (checkout/recommendation) + sampleSize + variant A/B key-value editor → all replaced
- New form fields:
  - **Experiment Name** (text, required)
  - **Workflow Family** (select: discovery, purchase, post_purchase, service, engagement)
  - **Test Message** (text/textarea, required) — the `message` field sent to `run_journey`
  - **Customer ID** (text, default `cust-1`)
  - **Sample Size** (number, informational only — not sent to API, backend always runs exactly 2 variants)
- On submit: call `createExperiment({ name, workflow_family, customer_id, tenant_id: 'default', message })` from store — this is now `async`
- Show loading state while `isRunning` (disable button, change label)
- All Tailwind classes use Tailwind v4 M3 tokens: `bg-surface-container`, `text-on-surface`, `border-outline`, `text-on-surface-variant`, `bg-primary-container`, `text-primary`, etc.
- `tenant_id` is hardcoded to `'default'` in the form (matches Session 4 default)

- [ ] **Step 1: Rewrite ExperimentForm.jsx**

```jsx
import { useState } from 'react';
import Button from './Button';
import { useExperimentStore } from '../store/experimentStore';
import { Play } from 'lucide-react';

const WORKFLOW_FAMILIES = [
  { value: 'discovery', label: 'Discovery' },
  { value: 'purchase', label: 'Purchase' },
  { value: 'post_purchase', label: 'Post Purchase' },
  { value: 'service', label: 'Service' },
  { value: 'engagement', label: 'Engagement' },
];

export default function ExperimentForm() {
  const { createExperiment, isRunning } = useExperimentStore();
  const [formData, setFormData] = useState({
    name: '',
    workflow_family: '',
    message: '',
    customer_id: 'cust-1',
    sampleSize: 2,
  });

  const set = (key, value) => setFormData((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    await createExperiment({
      name: formData.name,
      workflow_family: formData.workflow_family,
      message: formData.message,
      customer_id: formData.customer_id,
      tenant_id: 'default',
    });
  };

  const inputCls =
    'w-full bg-surface-variant text-on-surface border-b border-outline focus:border-b-2 focus:border-primary rounded-t px-4 py-3 outline-none transition-colors';

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-surface-container rounded-lg border border-outline-variant p-4 md:p-6 max-w-2xl animate-slideIn transition-theme"
    >
      <h2 className="text-xl md:text-2xl font-bold text-on-surface mb-6">Create Experiment</h2>

      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-on-surface-variant mb-2">
            Experiment Name
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => set('name', e.target.value)}
            placeholder="e.g., Headphones Discovery Test"
            className={inputCls}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-on-surface-variant mb-2">
            Workflow Family
          </label>
          <select
            value={formData.workflow_family}
            onChange={(e) => set('workflow_family', e.target.value)}
            className={inputCls}
            required
          >
            <option value="">Select workflow family</option>
            {WORKFLOW_FAMILIES.map((wf) => (
              <option key={wf.value} value={wf.value}>
                {wf.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-on-surface-variant mb-2">
            Test Message
          </label>
          <input
            type="text"
            value={formData.message}
            onChange={(e) => set('message', e.target.value)}
            placeholder="e.g., show me noise-cancelling headphones"
            className={inputCls}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-on-surface-variant mb-2">
            Customer ID
          </label>
          <input
            type="text"
            value={formData.customer_id}
            onChange={(e) => set('customer_id', e.target.value)}
            placeholder="cust-1"
            className={inputCls}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-on-surface-variant mb-2">
            Sample Size{' '}
            <span className="text-xs text-on-surface-variant">(informational — backend always runs 2 variants)</span>
          </label>
          <input
            type="number"
            value={formData.sampleSize}
            onChange={(e) => set('sampleSize', parseInt(e.target.value))}
            min="2"
            className={inputCls}
            disabled
          />
        </div>
      </div>

      <Button type="submit" variant="filled" className="w-full" disabled={isRunning}>
        <Play size={16} />
        {isRunning ? 'Running…' : 'Run Experiment'}
      </Button>
    </form>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/ops_ui_v2/src/components/ExperimentForm.jsx
git commit -m "feat: ExperimentForm rewritten with API fields, Tailwind v4 M3 tokens"
```

---

## Task 4: Update `ExperimentResults.jsx` for new API shape

**Files:**
- Modify: `apps/ops_ui_v2/src/components/ExperimentResults.jsx`

Key facts:
- Old: received `experiment` object + `results` array of `{variant: 'a'|'b', score}` (local state)
- New: `currentExperiment` is the API response: `{experiment: name, variant_a: {score, run_id}, variant_b: {score, run_id}, winner, experiment_id}`
- `Experiments.jsx` passes `experiment={currentExperiment}` — component receives the API result directly
- Remove dependency on `results` prop — all data comes from `experiment`
- Keep Tailwind v4 M3 token classes already in use

- [ ] **Step 1: Update ExperimentResults.jsx**

```jsx
import Button from './Button';
import { Download } from 'lucide-react';

export default function ExperimentResults({ experiment }) {
  if (!experiment) {
    return (
      <div className="bg-surface-container rounded-lg border border-outline-variant p-6 max-w-2xl">
        <p className="text-on-surface-variant">No results available</p>
      </div>
    );
  }

  const scoreA = experiment.variant_a?.score ?? 0;
  const scoreB = experiment.variant_b?.score ?? 0;
  const winner = experiment.winner || (scoreA >= scoreB ? 'A' : 'B');
  const name = experiment.experiment || experiment.name || 'Experiment';

  return (
    <div className="space-y-6">
      <div className="bg-surface-container rounded-2xl overflow-hidden border border-outline-variant p-6">
        <h2 className="text-2xl font-bold text-on-surface mb-6">{name} — Results</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-primary-container text-on-primary-container rounded-2xl p-5">
            <p className="text-sm font-medium">Variant A</p>
            <p className="text-3xl font-bold mt-2">{scoreA.toFixed ? scoreA.toFixed(1) : scoreA}</p>
            <p className="text-xs mt-1 opacity-70">score / 10</p>
          </div>

          <div className="bg-success-container text-on-success-container rounded-2xl p-5 flex items-center justify-center">
            <div className="text-center">
              <p className="text-sm font-medium">Winner</p>
              <p className="text-3xl font-bold mt-2">Variant {winner}</p>
            </div>
          </div>

          <div className="bg-secondary-container text-on-secondary-container rounded-2xl p-5">
            <p className="text-sm font-medium">Variant B</p>
            <p className="text-3xl font-bold mt-2">{scoreB.toFixed ? scoreB.toFixed(1) : scoreB}</p>
            <p className="text-xs mt-1 opacity-70">score / 10</p>
          </div>
        </div>
      </div>

      <Button variant="outlined" onClick={() => window.print()}>
        <Download size={16} /> Export Results
      </Button>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add apps/ops_ui_v2/src/components/ExperimentResults.jsx
git commit -m "feat: ExperimentResults reads from API response shape"
```

---

## Task 5: Update `Experiments.jsx` — add past experiments table + mount fetch

**Files:**
- Modify: `apps/ops_ui_v2/src/pages/Experiments.jsx`

Key facts:
- Add `useEffect` on mount that calls `fetchExperiments()` from store
- Add a past-experiments table above the form: columns Name, Winner, Score A, Score B, Date
- Data source: `experiments` array from store (each item has `name`, `winner`, `variant_a.score`, `variant_b.score`, `created_at`)
- Existing conditional rendering (`!currentExperiment ? <ExperimentForm> : <ExperimentResults>`) stays intact
- Pass `experiment={currentExperiment}` to `ExperimentResults` (no `results` prop — removed in Task 4)
- Add a "New Experiment" button when `currentExperiment` is set (calls `resetExperiment()`)
- All classes use Tailwind v4 M3 tokens

- [ ] **Step 1: Rewrite Experiments.jsx**

```jsx
import { useEffect } from 'react';
import ExperimentForm from '../components/ExperimentForm';
import ExperimentResults from '../components/ExperimentResults';
import Button from '../components/Button';
import { useExperimentStore } from '../store/experimentStore';
import { Plus } from 'lucide-react';

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function Experiments() {
  const { currentExperiment, experiments, isRunning, fetchExperiments, resetExperiment } =
    useExperimentStore();

  useEffect(() => {
    fetchExperiments();
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <div className="eyebrow">ACOS EXPERIMENTS</div>
        <h1 className="text-3xl font-bold text-on-surface">Experiments</h1>
        <p className="muted">Design and run A/B experiments across workflow variants.</p>
      </div>

      {/* Past Experiments Table */}
      {experiments.length > 0 && (
        <div className="mb-8 bg-surface-container rounded-lg border border-outline-variant overflow-hidden">
          <div className="px-4 py-3 border-b border-outline-variant">
            <h2 className="text-base font-semibold text-on-surface">Past Experiments</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-outline-variant">
                  <th className="text-left px-4 py-2 text-on-surface-variant font-medium">Name</th>
                  <th className="text-left px-4 py-2 text-on-surface-variant font-medium">Winner</th>
                  <th className="text-right px-4 py-2 text-on-surface-variant font-medium">Score A</th>
                  <th className="text-right px-4 py-2 text-on-surface-variant font-medium">Score B</th>
                  <th className="text-right px-4 py-2 text-on-surface-variant font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp) => {
                  const scoreA = exp.variant_a?.score ?? '—';
                  const scoreB = exp.variant_b?.score ?? '—';
                  return (
                    <tr key={exp.id} className="border-b border-outline-variant last:border-0 hover:bg-surface-container-high transition-colors">
                      <td className="px-4 py-3 text-on-surface font-medium">{exp.name}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-container text-on-primary-container">
                          Variant {exp.winner || '—'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-on-surface-variant tabular-nums">
                        {typeof scoreA === 'number' ? scoreA.toFixed(1) : scoreA}
                      </td>
                      <td className="px-4 py-3 text-right text-on-surface-variant tabular-nums">
                        {typeof scoreB === 'number' ? scoreB.toFixed(1) : scoreB}
                      </td>
                      <td className="px-4 py-3 text-right text-on-surface-variant">
                        {formatDate(exp.created_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Form / Results */}
      {!currentExperiment ? (
        <ExperimentForm />
      ) : (
        <>
          {isRunning && (
            <div className="mb-6 p-4 bg-surface-container border border-outline-variant rounded-lg">
              <p className="text-sm text-on-surface-variant">Running experiment…</p>
            </div>
          )}
          <ExperimentResults experiment={currentExperiment} />
          <div className="mt-4">
            <Button variant="outlined" onClick={resetExperiment}>
              <Plus size={16} /> New Experiment
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify the UI builds without errors**

```bash
cd /c/Users/vrast/OneDrive/Apps/Documents/acos/apps/ops_ui_v2
npm run build 2>&1 | tail -20
```
Expected: build succeeds with no errors (warnings about unused vars are fine).

- [ ] **Step 3: Commit**

```bash
git add apps/ops_ui_v2/src/pages/Experiments.jsx
git commit -m "feat: Experiments page adds past-experiments table and live API fetch"
```

---

## Task 6: Full end-to-end verification

- [ ] **Step 1: Restart the ops API**

```bash
# In the acos root, stop and restart:
docker-compose restart ops-api
# or if running locally:
# kill the uvicorn process and re-run
```

- [ ] **Step 2: Run the full acceptance criteria sequence**

```bash
# AC1 — POST returns winner
curl -s -X POST http://localhost:8081/experiments \
  -H "Authorization: Bearer dev-ops-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"test-exp-1","workflow_family":"discovery","customer_id":"cust-1","tenant_id":"default","message":"show me headphones"}' \
  | python -m json.tool | grep winner

# AC2 — GET returns list
curl -s http://localhost:8081/experiments | python -m json.tool

# AC3 — GET by ID
curl -s http://localhost:8081/experiments/1/results | python -m json.tool

# AC4 — DB row count
psql acos -c "SELECT COUNT(*) FROM experiments;"
```

Expected:
- AC1: `"winner": "A"` or `"winner": "B"`
- AC2: `{"experiments": [...]}` with name/winner/variant_a/variant_b fields
- AC3: `{"experiment": {...}}`
- AC4: count > 0

- [ ] **Step 3: Open UI and verify Experiments page**

Navigate to `http://localhost:5173/experiments` (or prod URL):
1. Past experiments table loads on mount
2. Submit the form → loading state visible → results appear
3. Table refreshes with new row after submit
4. "New Experiment" button resets to form view

- [ ] **Step 4: Final commit (if any cleanup)**

```bash
git add -p  # only if any cleanup changes exist
git commit -m "chore: session 5 final cleanup"
```

---

## Acceptance Criteria Checklist

- [ ] `POST /experiments` with valid body returns 200 with `"winner"` field
- [ ] `GET /experiments` returns JSON array with name, winner, variant_a, variant_b
- [ ] `GET /experiments/1/results` returns `{"experiment": {...}}` (not hardcoded mock)
- [ ] `psql acos -c "SELECT COUNT(*) FROM experiments"` returns > 0
- [ ] UI Experiments page shows past experiments table loaded from API
- [ ] Submitting UI form runs experiment and refreshes table
