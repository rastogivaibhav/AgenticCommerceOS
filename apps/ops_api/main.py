"""Ops API – operations dashboard, run management, and React UI serving.

Security hardening (Sprint 0):
- FIX-01: JWT Bearer auth on all sensitive endpoints
- FIX-03: CORS restricted to ALLOWED_ORIGINS env var
- MED-07: Generic exception handler, no internal detail in responses
"""

import os
import logging
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from acosplatform.auth.api_key import require_ops_token
from acosplatform.db.connection import ensure_schema
from acosplatform.db.repository import get_runs, get_run, get_dashboard, get_events
from acosplatform.replay.replay_engine import replay
from acosplatform.billing.engine import get_usage, get_cost_summary
from acosplatform.evaluation.scorer import get_experiment_results
from acosplatform.middleware.rate_limit import limiter, rate_limit_error_handler, OPS_LIMIT, REPLAY_LIMIT
from acosplatform.observability.metrics import metrics_endpoint
from slowapi.errors import RateLimitExceeded

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ACOS Ops API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)

# Mount static files for React UI (FIX-12)
app.mount("/static", StaticFiles(directory="apps/ops_api/static"), name="static")

# ── CORS — whitelist only (FIX-03) ────────────────────────────────────────────
_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# ── Global exception handler — no internal detail to caller (MED-07) ──────────
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )


@app.on_event("startup")
def startup():
    logger.info("Ops API starting up...")
    ensure_schema()
    logger.info("Ops API ready")


# ── Run Management (auth required) ────────────────────────────────────────────

@app.get("/runs")
def list_runs(
    tenant_id: str = None,
    limit: int = 100,
    _token: dict = Depends(require_ops_token),   # FIX-01
):
    """List all journey runs. Requires Bearer token."""
    if limit > 1000:
        limit = 1000   # hard cap — no unbounded queries
    return {"runs": get_runs(tenant_id=tenant_id, limit=limit)}


@app.get("/runs/{run_id}")
def get_run_detail(
    run_id: str,
    _token: dict = Depends(require_ops_token),
):
    run = get_run(run_id)
    if not run:
        # Generic 404 — don't confirm whether run_id format is valid
        return JSONResponse(status_code=404, content={"error": "Not found"})
    events = get_events(run_id)
    return {"run": run, "events": events}


@app.post("/replay/{run_id}")
@app.post("/v1/replay/{run_id}")
@limiter.limit(REPLAY_LIMIT)
def replay_run(
    request: Request,
    run_id: str,
    _token: dict = Depends(require_ops_token),
):
    """Replay a previous run. Rate-limited to 10/min to prevent DoS (HIGH-04)."""
    return replay(run_id)


@app.get("/metrics")
def ops_metrics():
    """Prometheus metrics scrape endpoint (FIX-18)."""
    return metrics_endpoint()


# ── Dashboard & Billing (auth required) ───────────────────────────────────────

@app.get("/dashboard")
def dashboard(_token: dict = Depends(require_ops_token)):
    dash = get_dashboard()
    billing = get_cost_summary()
    experiments = get_experiment_results()
    return {"metrics": dash, "billing": billing, "experiments": experiments}


@app.get("/billing")
def billing(tenant_id: str = None, _token: dict = Depends(require_ops_token)):
    if tenant_id:
        return {"usage": get_usage(tenant_id)}
    return {"summary": get_cost_summary(), "by_tenant": get_usage()}


# ── Health (no auth) ──────────────────────────────────────────────────────────

@app.get("/health")
def health():
    from acosplatform.db.connection import get_connection
    db_ok = get_connection() is not None
    return {
        "status": "ok" if db_ok else "degraded",
        "db": "connected" if db_ok else "unavailable",
        "service": "ops-api",
        "version": os.environ.get("APP_VERSION", "1.0.0"),
    }


# ── React UI (no auth — static serving, no sensitive data) ───────────────────

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Serve the React Ops UI. Auth is enforced client-side via API calls."""
    return _get_ui_html()


def _get_ui_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ACOS Ops Dashboard</title>
<script crossorigin src="/static/react.min.js"></script>
<script crossorigin src="/static/react-dom.min.js"></script>
<script src="/static/babel.min.js"></script>
<style>
  :root {
    --bg: #0f1117;
    --surface: #1a1d27;
    --surface2: #242836;
    --border: #2e3348;
    --primary: #6c63ff;
    --primary-hover: #8078ff;
    --success: #2dd4a8;
    --warning: #f5a623;
    --error: #ef4444;
    --text: #e4e6f0;
    --text-dim: #8b8fa3;
    --text-bright: #ffffff;
    --radius: 12px;
    --shadow: 0 4px 24px rgba(0,0,0,0.3);
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    line-height: 1.6;
  }

  .app { max-width: 1280px; margin: 0 auto; padding: 24px; }
  .header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 0; margin-bottom: 24px; border-bottom: 1px solid var(--border);
  }
  .header h1 {
    font-size: 24px; font-weight: 700; color: var(--text-bright);
    background: linear-gradient(135deg, var(--primary), var(--success));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .header .subtitle { font-size: 13px; color: var(--text-dim); margin-top: 2px; }

  .nav { display: flex; gap: 8px; }
  .nav button {
    padding: 8px 20px; border: 1px solid var(--border); border-radius: 8px;
    background: var(--surface); color: var(--text); cursor: pointer;
    font-size: 13px; font-weight: 500; transition: all 0.2s;
  }
  .nav button:hover { background: var(--surface2); border-color: var(--primary); }
  .nav button.active { background: var(--primary); color: white; border-color: var(--primary); }

  .metrics-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px; margin-bottom: 24px;
  }
  .metric-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 20px; transition: all 0.2s;
  }
  .metric-card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: var(--shadow); }
  .metric-label { font-size: 12px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
  .metric-value { font-size: 28px; font-weight: 700; color: var(--text-bright); }
  .metric-value.primary { color: var(--primary); }
  .metric-value.success { color: var(--success); }
  .metric-value.warning { color: var(--warning); }

  .card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 20px; margin-bottom: 16px;
  }
  .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
  .card-header h2 { font-size: 16px; font-weight: 600; color: var(--text-bright); }

  .table { width: 100%; border-collapse: collapse; }
  .table th { text-align: left; padding: 12px; font-size: 12px; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
  .table td { padding: 12px; font-size: 13px; border-bottom: 1px solid var(--border); }
  .table tr { transition: background 0.15s; cursor: pointer; }
  .table tr:hover { background: var(--surface2); }

  .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
  .badge.discovery { background: rgba(108,99,255,0.15); color: var(--primary); }
  .badge.purchase { background: rgba(45,212,168,0.15); color: var(--success); }
  .badge.post_purchase { background: rgba(245,166,35,0.15); color: var(--warning); }
  .badge.service { background: rgba(239,68,68,0.15); color: var(--error); }
  .badge.engagement { background: rgba(59,130,246,0.15); color: #3b82f6; }

  .btn { padding: 8px 16px; border: none; border-radius: 8px; font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.2s; }
  .btn-primary { background: var(--primary); color: white; }
  .btn-primary:hover { background: var(--primary-hover); }
  .btn-sm { padding: 5px 12px; font-size: 12px; }

  .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .detail-section { margin-bottom: 16px; }
  .detail-section h3 { font-size: 13px; color: var(--text-dim); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
  .detail-section pre { background: var(--surface2); padding: 12px; border-radius: 8px; font-size: 12px; overflow-x: auto; max-height: 300px; overflow-y: auto; color: var(--text); }

  .back-btn { background: none; border: none; color: var(--primary); cursor: pointer; font-size: 13px; margin-bottom: 16px; display: inline-flex; align-items: center; gap: 4px; }
  .back-btn:hover { color: var(--primary-hover); }

  .loading { text-align: center; padding: 40px; color: var(--text-dim); }
  .empty { text-align: center; padding: 40px; color: var(--text-dim); }

  .journey-breakdown { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
  .journey-chip { display: flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 6px; background: var(--surface2); font-size: 12px; }
  .journey-chip .count { font-weight: 700; color: var(--text-bright); }

  .auth-banner { background: rgba(239,68,68,0.1); border: 1px solid var(--error); border-radius: 8px; padding: 12px 16px; margin-bottom: 16px; color: var(--error); font-size: 13px; }

  @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
  .fade-in { animation: fadeIn 0.3s ease; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
  .status-dot.ok { background: var(--success); }
</style>
</head>
<body>
<div id="root"></div>
<script type="text/babel">
const { useState, useEffect, useCallback } = React;
const API = '';

// Simple token store (in-memory — cleared on page refresh)
let _authToken = null;

function getAuthHeaders() {
  return _authToken ? { 'Authorization': `Bearer ${_authToken}` } : {};
}

function LoginForm({ onLogin }) {
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token.trim()) { setError('Token is required'); return; }
    // Test the token against /runs
    try {
      const r = await fetch(`${API}/runs`, { headers: { 'Authorization': `Bearer ${token}` } });
      if (r.status === 200) { _authToken = token; onLogin(); }
      else { setError('Invalid token (HTTP ' + r.status + ')'); }
    } catch { setError('Could not reach Ops API'); }
  };
  return (
    <div style={{maxWidth:'400px',margin:'120px auto'}}>
      <div className="card fade-in">
        <h2 style={{marginBottom:'16px',color:'var(--text-bright)'}}>ACOS Ops Dashboard</h2>
        <p style={{color:'var(--text-dim)',fontSize:'13px',marginBottom:'16px'}}>Enter your JWT bearer token to continue.</p>
        {error && <div className="auth-banner">{error}</div>}
        <form onSubmit={handleSubmit}>
          <input type="password" value={token} onChange={e=>setToken(e.target.value)}
            placeholder="Bearer token"
            style={{width:'100%',padding:'10px 12px',background:'var(--surface2)',border:'1px solid var(--border)',borderRadius:'8px',color:'var(--text)',fontSize:'13px',marginBottom:'12px'}}/>
          <button type="submit" className="btn btn-primary" style={{width:'100%'}}>Sign in</button>
        </form>
      </div>
    </div>
  );
}

function App() {
  const [authed, setAuthed] = useState(false);
  const [page, setPage] = useState('dashboard');
  const [runs, setRuns] = useState([]);
  const [dash, setDash] = useState(null);
  const [selectedRun, setSelectedRun] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchRuns = useCallback(async () => {
    try {
      const r = await fetch(`${API}/runs`, { headers: getAuthHeaders() });
      if (r.status === 401) { _authToken = null; setAuthed(false); return; }
      const data = await r.json();
      setRuns(data.runs || []);
    } catch (e) { console.error('Failed to fetch runs', e); }
  }, []);

  const fetchDashboard = useCallback(async () => {
    try {
      const r = await fetch(`${API}/dashboard`, { headers: getAuthHeaders() });
      if (r.status === 401) { _authToken = null; setAuthed(false); return; }
      setDash(await r.json());
    } catch (e) { console.error('Failed to fetch dashboard', e); }
  }, []);

  const fetchRunDetail = useCallback(async (id) => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/runs/${id}`, { headers: getAuthHeaders() });
      setSelectedRun(await r.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  const replayRun = useCallback(async (id) => {
    setLoading(true);
    try {
      const r = await fetch(`${API}/replay/${id}`, { method: 'POST', headers: getAuthHeaders() });
      const data = await r.json();
      alert(`Replay complete! New run: ${data.new_run_id || 'N/A'}`);
      fetchRuns();
    } catch { alert('Replay failed'); }
    setLoading(false);
  }, [fetchRuns]);

  useEffect(() => { if (authed) { fetchRuns(); fetchDashboard(); } }, [authed]);

  if (!authed) return <LoginForm onLogin={() => setAuthed(true)} />;

  return (
    <div className="app">
      <div className="header">
        <div>
          <h1>ACOS Ops Dashboard</h1>
          <div className="subtitle"><span className="status-dot ok"></span>Agentic Commerce Operating System</div>
        </div>
        <div className="nav">
          <button className={page==='dashboard'?'active':''} onClick={()=>{setPage('dashboard');fetchDashboard();}}>Dashboard</button>
          <button className={page==='runs'?'active':''} onClick={()=>{setPage('runs');fetchRuns();}}>Runs</button>
          <button onClick={()=>{_authToken=null;setAuthed(false);}} style={{background:'var(--error)',color:'white',border:'none'}}>Sign out</button>
        </div>
      </div>
      {page === 'dashboard' && <Dashboard data={dash} />}
      {page === 'runs' && !selectedRun && <RunsList runs={runs} onSelect={(id)=>{fetchRunDetail(id);}} onReplay={replayRun} />}
      {page === 'runs' && selectedRun && <RunDetail data={selectedRun} onBack={()=>setSelectedRun(null)} onReplay={replayRun} loading={loading} />}
    </div>
  );
}

function Dashboard({ data }) {
  if (!data) return <div className="loading">Loading dashboard...</div>;
  const m = data.metrics || {};
  const b = data.billing || {};
  return (
    <div className="fade-in">
      
      {/* JLP Superpowers Banner */}
      <div className="card fade-in" style={{marginBottom: '24px', background: 'linear-gradient(135deg, rgba(26,29,39,1) 0%, rgba(26,29,39,0.8) 100%)', border: '1px solid var(--primary)', position: 'relative', overflow: 'hidden'}}>
        <div style={{position: 'absolute', top: '-50px', right: '-50px', width: '300px', height: '300px', background: 'radial-gradient(circle, var(--primary) 0%, transparent 70%)', opacity: '0.1', borderRadius: '50%'}}></div>
        <h2 style={{fontSize: '22px', color: 'var(--text-bright)', marginBottom: '16px', display:'flex', alignItems:'center', gap:'10px'}}>
          ACOS x John Lewis Partnership 
          <span style={{fontSize: '12px', padding: '4px 10px', background: 'var(--primary)', borderRadius: '20px', fontWeight: 'bold'}}>✨ Superpowers Active</span>
        </h2>
        
        <p style={{color: 'var(--text-dim)', marginBottom: '24px', fontSize: '14px', maxWidth: '850px', lineHeight: '1.6'}}>
          ACOS (Agentic Commerce Operating System) is silently transforming the JLP omnichannel experience by orchestrating autonomous AI agents that handle discovery, checkout, and post-purchase customer service at scale.
        </p>
        
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px'}}>
          <div style={{padding: '16px', background: 'rgba(45,212,168,0.05)', borderRadius: '8px', borderLeft: '3px solid var(--success)'}}>
             <h4 style={{color: 'var(--success)', marginBottom: '8px', fontSize: '13px'}}>100x Cost Reduction</h4>
             <p style={{fontSize: '12px', color: 'var(--text-dim)', lineHeight: '1.5'}}>Resolves customer queries for fractions of a penny via localized LLM grounding, compared to human CSR costs of £3-£5 per ticket.</p>
          </div>
          <div style={{padding: '16px', background: 'rgba(108,99,255,0.05)', borderRadius: '8px', borderLeft: '3px solid var(--primary)'}}>
             <h4 style={{color: 'var(--primary)', marginBottom: '8px', fontSize: '13px'}}>Multi-Agent Orchestration</h4>
             <p style={{fontSize: '12px', color: 'var(--text-dim)', lineHeight: '1.5'}}>Seamlessly and autonomously routes shopper intent across Catalog, Billing, Returns, and Loyalty subsystems without human intervention.</p>
          </div>
          <div style={{padding: '16px', background: 'rgba(245,166,35,0.05)', borderRadius: '8px', borderLeft: '3px solid var(--warning)'}}>
             <h4 style={{color: 'var(--warning)', marginBottom: '8px', fontSize: '13px'}}>Fraud & Injection Hardened</h4>
             <p style={{fontSize: '12px', color: 'var(--text-dim)', lineHeight: '1.5'}}>Active prompt injection detection and context isolation securely protects JLP tenant data from rogue inputs and malicious payloads.</p>
          </div>
        </div>
      </div>

      {/* Live System Metrics */}
      <h3 style={{fontSize: '16px', color: 'var(--text-bright)', marginBottom: '16px'}}>JLP Fleet Telemetry</h3>
      <div className="metrics-grid">
        <div className="metric-card"><div className="metric-label">Total Orchestrations</div><div className="metric-value primary">{m.total_runs || 0}</div></div>
        <div className="metric-card"><div className="metric-label">Unique Shoppers</div><div className="metric-value success">{m.unique_customers || 0}</div></div>
        <div className="metric-card"><div className="metric-label">LLM Inference Cost</div><div className="metric-value warning">${(m.total_cost || 0).toFixed(4)}</div></div>
        <div className="metric-card"><div className="metric-label">Est. Savings (£3/ticket)</div><div className="metric-value success" style={{color:'#2dd4a8'}}>£{((m.total_runs || 0) * 3).toFixed(2)}</div></div>
        <div className="metric-card"><div className="metric-label">API Calls Orchestrated</div><div className="metric-value primary">{b.total_api_calls || 0}</div></div>
        <div className="metric-card"><div className="metric-label">Avg CSAT Score</div><div className="metric-value">{(m.avg_score || 0).toFixed(1)} / 10</div></div>
      </div>
      
      <div className="card" style={{marginTop:'16px'}}>
        <div className="card-header"><h2>Autonomous Intent Routing Logs (JLP)</h2></div>
        <div className="journey-breakdown">
          {Object.entries(m.runs_by_journey || {}).map(([j,c]) => (
            <div key={j} className="journey-chip"><span className={`badge ${j}`}>{j}</span> <span className="count">{c}</span></div>
          ))}
        </div>
        {Object.keys(m.runs_by_journey||{}).length===0 && <div className="empty"><p>No shopper intents processed yet.</p></div>}
      </div>
    </div>
  );
}

function RunsList({ runs, onSelect, onReplay }) {
  if (!runs.length) return <div className="empty fade-in"><p>No runs found</p></div>;
  return (
    <div className="card fade-in">
      <div className="card-header"><h2>Journey Runs ({runs.length})</h2></div>
      <table className="table">
        <thead><tr><th>Run ID</th><th>Journey</th><th>Customer</th><th>Tenant</th><th>Score</th><th>Cost</th><th>Time</th><th>Actions</th></tr></thead>
        <tbody>{runs.map(r => (
          <tr key={r.id} onClick={()=>onSelect(r.id)}>
            <td style={{fontFamily:'monospace',fontSize:'12px'}}>{r.id}</td>
            <td><span className={`badge ${r.journey}`}>{r.journey}</span></td>
            <td>{r.customer_id}</td>
            <td>{r.tenant_id}</td>
            <td>{(r.score||0).toFixed(1)}</td>
            <td>${(r.cost||0).toFixed(4)}</td>
            <td style={{fontSize:'12px',color:'var(--text-dim)'}}>{r.created_at ? new Date(r.created_at).toLocaleString() : '-'}</td>
            <td><button className="btn btn-primary btn-sm" onClick={(e)=>{e.stopPropagation();onReplay(r.id);}}>Replay</button></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function RunDetail({ data, onBack, onReplay, loading }) {
  if (loading) return <div className="loading">Loading...</div>;
  if (!data || !data.run) return <div className="empty">Run not found</div>;
  const r = data.run;
  const events = data.events || [];
  return (
    <div className="fade-in">
      <button className="back-btn" onClick={onBack}>← Back to runs</button>
      <div className="card">
        <div className="card-header">
          <h2>Run: {r.id}</h2>
          <button className="btn btn-primary" onClick={()=>onReplay(r.id)}>Replay Run</button>
        </div>
        <div className="metrics-grid" style={{marginBottom:'0'}}>
          <div className="metric-card"><div className="metric-label">Journey</div><div className="metric-value"><span className={`badge ${r.journey}`}>{r.journey}</span></div></div>
          <div className="metric-card"><div className="metric-label">Customer</div><div className="metric-value" style={{fontSize:'18px'}}>{r.customer_id}</div></div>
          <div className="metric-card"><div className="metric-label">Score</div><div className="metric-value success">{(r.score||0).toFixed(1)}</div></div>
          <div className="metric-card"><div className="metric-label">Cost</div><div className="metric-value warning">${(r.cost||0).toFixed(4)}</div></div>
        </div>
      </div>
      <div className="detail-grid">
        <div className="card"><div className="detail-section"><h3>Input</h3><pre>{JSON.stringify(r.input, null, 2)}</pre></div></div>
        <div className="card"><div className="detail-section"><h3>Output</h3><pre>{JSON.stringify(r.output, null, 2)}</pre></div></div>
      </div>
      {events.length > 0 && (
        <div className="card">
          <div className="card-header"><h2>Events ({events.length})</h2></div>
          <table className="table">
            <thead><tr><th>Type</th><th>Payload</th><th>Time</th></tr></thead>
            <tbody>{events.map((e,i) => (
              <tr key={i}><td><span className="badge discovery">{e.event_type}</span></td><td style={{fontSize:'12px',fontFamily:'monospace',maxWidth:'400px',overflow:'hidden',textOverflow:'ellipsis'}}>{JSON.stringify(e.payload)}</td><td style={{fontSize:'12px',color:'var(--text-dim)'}}>{e.created_at}</td></tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
</script>
</body>
</html>"""
