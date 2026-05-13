import { useEffect, useMemo, useState } from 'react';
import { Bot, CheckCircle2, GitBranch, Handshake, PlayCircle, ShieldCheck, Wrench } from 'lucide-react';
import { getStudioProof, getNorthstarReplays, rerunNorthstarReplay, runNorthstarMessage } from '../api/northstarAPI';
import './StudioProof.css';

const TABS = ['Node', 'Prompts', 'Connectors', 'Evidence', 'Tests', 'Deployment'];

function Pill({ children, warning = false }) {
  return <span className={`status-pill ${warning ? 'warning' : ''}`}>{children}</span>;
}

function Card({ title, icon, children }) {
  return (
    <section className="studio-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        {icon}
        <h2 style={{ fontSize: 15, fontWeight: 800, margin: 0 }}>{title}</h2>
      </div>
      {children}
    </section>
  );
}

export default function StudioProof() {
  const [proof, setProof] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('Evidence');
  const [message, setMessage] = useState('I need an outfit for a winter wedding under £200, available for pickup near Reading');
  const [dryRun, setDryRun] = useState(null);
  const [running, setRunning] = useState(false);
  const [replays, setReplays] = useState([]);
  const [replayResult, setReplayResult] = useState(null);

  const refresh = () => {
    setLoading(true);
    Promise.all([getStudioProof(), getNorthstarReplays().catch(() => ({ replays: [] }))])
      .then(([proofPayload, replayPayload]) => {
        setProof(proofPayload);
        setReplays(replayPayload.replays || []);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(refresh, []);

  const journey = proof?.golden_journey;
  const evidence = journey?.evidence || [];
  const tools = journey?.tool_trace || [];
  const agents = journey?.participating_agents || [];
  const readiness = proof?.readiness || {};
  const readinessScore = useMemo(() => {
    const values = Object.values(readiness);
    if (!values.length) return 0;
    return Math.round((values.filter(Boolean).length / values.length) * 100);
  }, [readiness]);


  const handleReplay = async (replayId) => {
    setReplayResult(null);
    try {
      const result = await rerunNorthstarReplay(replayId);
      setReplayResult(result);
      refresh();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDryRun = async () => {
    setRunning(true);
    setDryRun(null);
    try {
      const result = await runNorthstarMessage({
        tenant_id: 'studio-ui',
        channel: 'web',
        channel_user_id: 'studio-ui-user',
        customer_id: 'studio-ui-customer',
        text: message,
      });
      setDryRun(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return <div className="studio-proof-page">Loading Studio Proof…</div>;
  }

  return (
    <div className="studio-proof-page">
      <div className="studio-proof-hero">
        <Card title="North-Star Studio Proof" icon={<GitBranch size={18} />}>
          <div className="studio-proof-title">Agentic Retail Control Plane</div>
          <p className="studio-proof-muted">
            This screen proves the target Studio experience: canvas-ready orchestration, tabbed inspector,
            MCP tool discovery, run timeline, evidence, human handoff and deployment readiness from live APIs.
          </p>
          {error && <p className="studio-proof-muted" style={{ color: 'var(--md-error)' }}>{error}</p>}
          <div className="pill-row">
            <Pill>{proof?.status || 'unknown'}</Pill>
            <Pill>{readinessScore}% readiness</Pill>
            <Pill>{agents.length} agents</Pill>
            <Pill>{tools.length} tool calls</Pill>
            <Pill>{evidence.length} evidence events</Pill>
          </div>
        </Card>

        <Card title="Deployment Readiness" icon={<ShieldCheck size={18} />}>
          <div className="studio-proof-kpi">
            <strong>{readinessScore}%</strong>
            <span className="studio-proof-muted">Production Runtime + Studio Proof score</span>
          </div>
          <div className="pill-row">
            {Object.entries(readiness).map(([key, value]) => (
              <Pill key={key} warning={!value}>{key.replaceAll('_', ' ')}: {value ? 'yes' : 'no'}</Pill>
            ))}
          </div>
        </Card>
      </div>

      <div className="studio-proof-grid">
        <Card title="Retail Simulation Console" icon={<PlayCircle size={18} />}>
          <textarea className="proof-textarea" value={message} onChange={(e) => setMessage(e.target.value)} />
          <button className="primary-button" onClick={handleDryRun} disabled={running} style={{ marginTop: 10 }}>
            {running ? 'Running…' : 'Run dry test'}
          </button>
          {dryRun && (
            <p className="studio-proof-muted">
              Result: {dryRun.intent?.intent} · {dryRun.participating_agents?.length || 0} agents · {dryRun.tool_trace?.length || 0} tools
            </p>
          )}
        </Card>

        <Card title="Agent Registry" icon={<Bot size={18} />}>
          <div className="agent-list">
            {agents.map((agent) => (
              <div className="agent-item" key={agent.id}>
                <strong>{agent.name}</strong>
                <div className="studio-proof-muted">{agent.id} · {agent.role}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="MCP Tool Browser" icon={<Wrench size={18} />}>
          <div className="tool-list">
            {(proof?.tools || []).map((tool) => (
              <div className="tool-item" key={tool.name}>
                <strong>{tool.name}</strong>
                <div className="studio-proof-muted">{tool.protocol} · {tool.description}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Human Handoff Queue" icon={<Handshake size={18} />}>
          {(proof?.handoffs || []).length ? (
            proof.handoffs.map((handoff) => (
              <div className="timeline-item" key={handoff.id}>
                <strong>{handoff.event_type}</strong>
                <div className="studio-proof-muted">{handoff.agent_id} · {handoff.created_at}</div>
              </div>
            ))
          ) : (
            <p className="studio-proof-muted">No handoffs created yet.</p>
          )}
        </Card>

        <Card title="Replay Proof" icon={<PlayCircle size={18} />}>
          {(replays || []).length ? (
            <div className="timeline-list">
              {replays.slice(0, 5).map((replay) => (
                <div className="timeline-item" key={replay.id}>
                  <strong>{replay.id}</strong>
                  <div className="studio-proof-muted">{replay.tenant_id} · {replay.status} · {replay.created_at}</div>
                  <button className="secondary-button" onClick={() => handleReplay(replay.id)}>Replay</button>
                </div>
              ))}
            </div>
          ) : (
            <p className="studio-proof-muted">No replay snapshots captured yet.</p>
          )}
          {replayResult && <p className="studio-proof-muted">Replay completed: {replayResult.result?.intent?.intent}</p>}
        </Card>
      </div>

      <section className="studio-card" style={{ marginTop: 16 }}>
        <h2 style={{ fontSize: 16, fontWeight: 800, margin: 0 }}>Tabbed Inspector</h2>
        <div className="studio-tabs">
          {TABS.map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)} className={activeTab === tab ? 'active' : ''}>{tab}</button>
          ))}
        </div>
        {activeTab === 'Evidence' && (
          <div className="timeline-list">
            {evidence.map((event) => (
              <div className="timeline-item" key={event.id}>
                <strong>{event.event_type}</strong>
                <div className="studio-proof-muted">
                  {event.agent_id || 'system'} · {event.tool_name || 'no tool'} · {event.policy_verdict || 'recorded'}
                </div>
              </div>
            ))}
          </div>
        )}
        {activeTab === 'Connectors' && (
          <div className="tool-list">
            {tools.map((tool) => (
              <div className="tool-item" key={tool.tool_trace_id}>
                <strong>{tool.tool_name}</strong>
                <div className="studio-proof-muted">{tool.protocol} · {tool.status} · {tool.latency_ms}ms</div>
              </div>
            ))}
          </div>
        )}
        {activeTab === 'Deployment' && (
          <div className="timeline-list">
            {Object.entries(readiness).map(([key, value]) => (
              <div className="timeline-item" key={key}>
                <strong>{value ? <CheckCircle2 size={15} /> : '⚠'} {key.replaceAll('_', ' ')}</strong>
                <div className="studio-proof-muted">{value ? 'Ready' : 'Needs completion'}</div>
              </div>
            ))}
          </div>
        )}
        {!['Evidence', 'Connectors', 'Deployment'].includes(activeTab) && (
          <p className="studio-proof-muted">
            {activeTab} inspector is wired into the Studio Proof shell. It gives the UX pattern for business users to inspect workflow nodes, prompts, test coverage and deployment state.
          </p>
        )}
      </section>
    </div>
  );
}
