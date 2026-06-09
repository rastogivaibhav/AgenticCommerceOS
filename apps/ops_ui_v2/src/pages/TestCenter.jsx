import { useEffect, useMemo, useState } from 'react';
import { FlaskConical, PlayCircle, ShieldCheck, TerminalSquare } from 'lucide-react';
import { getNorthstarTestPlan, runNorthstarMessage } from '../api/northstarAPI';
import './StudioProof.css';

function Card({ title, icon, children }) {
  return (
    <section className="studio-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        {icon}
        <h2 style={{ fontSize: 16, fontWeight: 800, margin: 0 }}>{title}</h2>
      </div>
      {children}
    </section>
  );
}

export default function TestCenter() {
  const [plan, setPlan] = useState(null);
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    getNorthstarTestPlan().then(setPlan).catch((err) => setError(err.message));
  }, []);

  const grouped = useMemo(() => {
    const groups = {};
    for (const check of plan?.checks || []) {
      groups[check.area] = groups[check.area] || [];
      groups[check.area].push(check);
    }
    return groups;
  }, [plan]);

  async function runSmoke() {
    setRunning(true);
    setError(null);
    try {
      const payload = {
        tenant_id: plan?.demo_data?.tenant_id || 'default',
        channel: 'web',
        channel_user_id: 'test-center-user',
        customer_id: 'test-center-customer',
        text: plan?.demo_data?.message,
      };
      setResult(await runNorthstarMessage(payload));
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  }

  if (!plan && !error) return <div className="studio-proof-page">Loading Test Center...</div>;

  return (
    <div className="studio-proof-page">
      <div className="studio-proof-hero">
        <Card title="Test Center" icon={<FlaskConical size={18} />}>
          <div className="studio-proof-title">Engineering Test Hub</div>
          <p className="studio-proof-muted">
            This screen explains exactly how to test ACOS locally, in CI, and in a Docker-enabled production runtime.
          </p>
          {error && <p style={{ color: 'var(--md-error)' }}>{error}</p>}
          <div className="pill-row">
            <span className="status-pill">{plan?.checks?.length || 0} checks</span>
            <span className="status-pill">sample run from UI</span>
            <span className="status-pill">CI command map</span>
          </div>
        </Card>

        <Card title="Create Sample Smoke Run" icon={<PlayCircle size={18} />}>
          <p className="studio-proof-muted">Creates a real sample execution through the north-star API so QA can inspect the returned evidence.</p>
          <button className="primary-button" onClick={runSmoke} disabled={running}>{running ? 'Running...' : 'Create smoke sample'}</button>
          {result && (
            <div className="pill-row" style={{ marginTop: 10 }}>
              <span className="status-pill">{result.status}</span>
              <span className="status-pill">{result.intent?.intent}</span>
              <span className="status-pill">{result.participating_agents?.length || 0} agents</span>
              <span className="status-pill">{result.tool_trace?.length || 0} tools</span>
              <span className="status-pill">{result.evidence?.length || 0} evidence</span>
            </div>
          )}
        </Card>
      </div>

      <div className="studio-proof-grid">
        {Object.entries(grouped).map(([area, checks]) => (
          <Card title={area} icon={<ShieldCheck size={18} />} key={area}>
            <div className="timeline-list">
              {checks.map((check) => (
                <div className="timeline-item" key={check.id}>
                  <strong>{check.id}</strong>
                  <div className="studio-proof-muted">Expected: {check.expected}</div>
                  <code>{check.command}</code>
                </div>
              ))}
            </div>
          </Card>
        ))}
        <Card title="Acceptance Commands" icon={<TerminalSquare size={18} />}>
          <p className="studio-proof-muted">Run these before every production-readiness review:</p>
          <code>make test-northstar && make smoke-northstar && make runtime-check && make ui-build</code>
        </Card>
      </div>
    </div>
  );
}
