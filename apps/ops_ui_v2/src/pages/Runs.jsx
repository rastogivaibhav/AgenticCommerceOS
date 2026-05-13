import { useEffect, useMemo, useState } from 'react';
import { Activity, Bot, Clock, Eye, GitBranch, Handshake, RefreshCw, Search, Wrench } from 'lucide-react';
import { getNorthstarRuns, getNorthstarRun, rerunNorthstarReplay, runNorthstarMessage, getV2A2ATraces } from '../api/northstarAPI';
import './StudioProof.css';

function Pill({ children, warning = false }) {
  return <span className={warning ? 'proof-pill warning' : 'proof-pill'}>{children}</span>;
}

function Card({ title, icon, children }) {
  return (
    <section className="studio-card">
      <h2>{icon}{title}</h2>
      {children}
    </section>
  );
}

function formatDate(value) {
  if (!value) return '—';
  try {
    return new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
  } catch {
    return value;
  }
}

const DEMO_MESSAGE = 'I need an outfit for a winter wedding under £200, available for pickup near Reading';

export default function Runs() {
  const [payload, setPayload] = useState(null);
  const [selected, setSelected] = useState(null);
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('all');
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [a2aTraces, setA2ATraces] = useState([]);

  const refresh = async () => {
    setError('');
    try {
      const data = await getNorthstarRuns();
      setPayload(data);
      try { const a2a = await getV2A2ATraces(); setA2ATraces(a2a.traces || []); } catch (_) { setA2ATraces([]); }
      if (!selected && data.runs?.length) {
        const detail = await getNorthstarRun(data.runs[0].id);
        setSelected(detail);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);

  const runs = payload?.runs || [];
  const filteredRuns = useMemo(() => {
    return runs.filter((run) => {
      const haystack = `${run.id} ${run.intent} ${run.primary_agent} ${run.customer_id} ${run.response_preview}`.toLowerCase();
      const matchesQuery = !query || haystack.includes(query.toLowerCase());
      const matchesStatus = status === 'all' || run.status === status;
      return matchesQuery && matchesStatus;
    });
  }, [runs, query, status]);

  const selectRun = async (runId) => {
    setError('');
    try {
      setSelected(await getNorthstarRun(runId));
    } catch (err) {
      setError(err.message);
    }
  };

  const runDemoJourney = async () => {
    setRunning(true);
    setError('');
    try {
      const result = await runNorthstarMessage({
        tenant_id: 'default',
        channel: 'web',
        channel_user_id: `runs-screen-${Date.now()}`,
        customer_id: 'runs-screen-customer',
        text: DEMO_MESSAGE,
      });
      await refresh();
      const replayId = result?.evidence?.[0]?.correlation_id;
      if (replayId) setQuery(replayId);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  const replaySelected = async () => {
    if (!selected?.run?.id) return;
    setRunning(true);
    setError('');
    try {
      await rerunNorthstarReplay(selected.run.id);
      await refresh();
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  const detail = selected?.result || {};
  const evidence = detail.evidence || [];
  const tools = detail.tool_trace || [];
  const agents = detail.participating_agents || [];
  const summary = payload?.summary || {};

  if (loading) return <div className="studio-proof-page">Loading runs…</div>;

  return (
    <div className="studio-proof-page">
      <div className="studio-proof-hero">
        <Card title="Runs Command Centre" icon={<Activity size={18} />}>
          <div className="studio-proof-title">Live Agent Runs</div>
          <p className="studio-proof-muted">
            Review every captured north-star orchestration run: session, journey, intent, agents, tool calls, evidence, handoff and replay.
          </p>
          {error && <p className="studio-proof-muted" style={{ color: 'var(--md-error)' }}>{error}</p>}
          <div className="pill-row">
            <Pill>{summary.total || 0} runs</Pill>
            <Pill>{summary.successful || 0} successful</Pill>
            <Pill>{summary.with_handoff || 0} handoffs</Pill>
            <Pill>{summary.tool_calls || 0} tool calls</Pill>
            <Pill>{summary.evidence_events || 0} evidence events</Pill>
          </div>
        </Card>
        <Card title="Create Demo Run" icon={<GitBranch size={18} />}>
          <p className="studio-proof-muted">Run the winter-wedding journey and immediately inspect it in the run timeline.</p>
          <button className="primary-button" onClick={runDemoJourney} disabled={running}>{running ? 'Running…' : 'Run golden journey'}</button>
          <button className="secondary-button" onClick={refresh} style={{ marginLeft: 8 }}><RefreshCw size={14} /> Refresh</button>
        </Card>
      </div>

      <div className="studio-proof-grid" style={{ gridTemplateColumns: 'minmax(360px, 0.9fr) minmax(420px, 1.1fr)' }}>
        <Card title="Run List" icon={<Search size={18} />}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <input className="proof-input" placeholder="Search run, intent, agent, customer…" value={query} onChange={(e) => setQuery(e.target.value)} />
            <select className="proof-input" value={status} onChange={(e) => setStatus(e.target.value)} style={{ maxWidth: 140 }}>
              <option value="all">All</option>
              <option value="success">Success</option>
              <option value="captured">Captured</option>
              <option value="failed">Failed</option>
            </select>
          </div>
          <div className="timeline-list">
            {filteredRuns.map((run) => (
              <button key={run.id} className="run-row" onClick={() => selectRun(run.id)}>
                <span>
                  <strong>{run.intent || 'unknown intent'}</strong>
                  <span className="studio-proof-muted">{run.id}</span>
                  <span className="studio-proof-muted">{formatDate(run.created_at)}</span>
                </span>
                <span className="run-row-metrics">
                  <Pill>{run.agent_count} agents</Pill>
                  <Pill>{run.tool_count} tools</Pill>
                  <Pill warning={run.failed_tool_count > 0}>{run.status}</Pill>
                </span>
              </button>
            ))}
            {!filteredRuns.length && <p className="studio-proof-muted">No runs match the current filter. Create a demo run to populate this screen.</p>}
          </div>
        </Card>

        <Card title="Run Detail" icon={<Eye size={18} />}>
          {selected?.run ? (
            <>
              <div className="pill-row">
                <Pill>{selected.run.status}</Pill>
                <Pill>{selected.run.intent}</Pill>
                <Pill>{selected.run.channel}</Pill>
                <Pill>{selected.run.customer_id}</Pill>
              </div>
              <p className="studio-proof-muted"><strong>Run:</strong> {selected.run.id}</p>
              <p className="studio-proof-muted"><strong>Session:</strong> {selected.run.conversation_session_id}</p>
              <p className="studio-proof-muted"><strong>Journey:</strong> {selected.run.journey_id}</p>
              <p className="studio-proof-muted"><strong>Correlation:</strong> {selected.run.correlation_id}</p>
              <p className="studio-proof-muted"><strong>Response:</strong> {detail.response_text}</p>
              <button className="secondary-button" onClick={replaySelected} disabled={running}><RefreshCw size={14} /> Replay this run</button>
            </>
          ) : <p className="studio-proof-muted">Select a run to inspect it.</p>}
        </Card>
      </div>

      <div className="studio-proof-grid">
        <Card title="Agents" icon={<Bot size={18} />}>
          {(agents || []).map((agent) => (
            <div className="agent-item" key={agent.id}>
              <strong>{agent.name}</strong>
              <div className="studio-proof-muted">{agent.id} · {agent.role}</div>
            </div>
          ))}
        </Card>
        <Card title="Tool Calls" icon={<Wrench size={18} />}>
          <div className="tool-list">
            {(tools || []).map((tool) => (
              <div className="tool-item" key={tool.tool_trace_id || `${tool.tool_name}-${tool.latency_ms}`}>
                <strong>{tool.tool_name}</strong>
                <div className="studio-proof-muted">{tool.protocol} · {tool.status} · {tool.latency_ms}ms · {tool.policy_verdict}</div>
              </div>
            ))}
          </div>
        </Card>
        <Card title="Evidence Timeline" icon={<Clock size={18} />}>
          <div className="timeline-list">
            {(evidence || []).map((event) => (
              <div className="timeline-item" key={event.id}>
                <strong>{event.event_type}</strong>
                <div className="studio-proof-muted">{event.agent_id || 'system'} · {event.tool_name || 'no tool'} · {formatDate(event.created_at)}</div>
              </div>
            ))}
          </div>
        </Card>

        <Card title="A2A Trace" icon={<GitBranch size={18} />}>
          {(a2aTraces || []).slice(0, 4).map((trace) => (
            <div className="timeline-item" key={trace.trace_id}>
              <strong>{trace.trace_id}</strong>
              <div className="studio-proof-muted">{(trace.agents || []).map((a) => a.name || a.agent_id).join(' → ')}</div>
              <div className="studio-proof-muted">£{trace.cost_estimate} · {(trace.policy_decisions || []).length} policy decisions · {(trace.memory_access || []).length} memory reads</div>
            </div>
          ))}
          {!a2aTraces.length && <p className="studio-proof-muted">No ACOS v2 A2A traces captured yet. Run the ACOS v2 demo from A2A Trace.</p>}
        </Card>
        <Card title="Human Handoff" icon={<Handshake size={18} />}>
          {(evidence || []).filter((event) => event.event_type === 'human.handoff.created').map((event) => (
            <div className="timeline-item" key={event.id}>
              <strong>{event.agent_id}</strong>
              <div className="studio-proof-muted">{event.payload?.reason || 'handoff created'}</div>
            </div>
          ))}
          {!evidence.some((event) => event.event_type === 'human.handoff.created') && <p className="studio-proof-muted">No human handoff for this run.</p>}
        </Card>
      </div>
    </div>
  );
}
