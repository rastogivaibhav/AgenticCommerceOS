import { useEffect, useMemo, useState } from 'react';
import { Cable, CheckCircle2, Database, GitBranch, RefreshCcw, ShieldCheck, TerminalSquare, Zap } from 'lucide-react';
import Button from '../components/Button';
import { getNorthstarApiPlane, runGraphQLProbe } from '../api/northstarAPI';
import './StudioProof.css';

const planeIcons = {
  REST: Database,
  'North-star REST': Zap,
  'North-star REST + GraphQL': GitBranch,
};

export default function APIPlane() {
  const [payload, setPayload] = useState(null);
  const [graphqlPayload, setGraphqlPayload] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('{ tools { name protocol } }');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [apiPlane, gql] = await Promise.all([
        getNorthstarApiPlane(),
        runGraphQLProbe(query),
      ]);
      setPayload(apiPlane);
      setGraphqlPayload(gql);
    } catch (err) {
      setError(err.message || 'API plane probe failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const screens = payload?.screens || [];
  const grouped = useMemo(() => screens.reduce((acc, item) => {
    const key = item.api_plane || 'Other';
    acc[key] = acc[key] || [];
    acc[key].push(item);
    return acc;
  }, {}), [screens]);

  const gqlTools = graphqlPayload?.data?.tools || [];

  return (
    <div className="studio-proof-page page-container">
      <header className="page-header">
        <div>
          <div className="eyebrow">ACOS API Plane</div>
          <h1>Screen-to-API Connectivity</h1>
          <p className="muted">
            Verify that every operator screen is backed by a real API plane: REST, North-star REST,
            GraphQL, or MCP/server-side tool execution.
          </p>
          <div className="proof-chip-row">
            <span className="proof-chip"><Cable size={14} /> {payload?.summary?.screens || 0} screens mapped</span>
            <span className="proof-chip"><ShieldCheck size={14} /> RBAC headers via shared API client</span>
            <span className="proof-chip"><GitBranch size={14} /> GraphQL probe included</span>
          </div>
        </div>
        <div className="header-actions">
          <Button variant="outline" onClick={load} disabled={loading}>
            <RefreshCcw size={16} /> {loading ? 'Checking…' : 'Refresh checks'}
          </Button>
        </div>
      </header>

      {error && (
        <section className="surface-card hero-panel" style={{ borderColor: 'rgba(180, 35, 24, 0.2)' }}>
          <strong>Connectivity issue</strong>
          <p className="muted">{error}</p>
        </section>
      )}

      <section className="summary-grid">
        <div className="summary-card">
          <span className="summary-label">Mapped screens</span>
          <strong>{payload?.summary?.screens || 0}</strong>
          <span className="summary-meta">Screens with explicit API connections.</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">REST plane</span>
          <strong>{payload?.summary?.rest_plane ? 'Connected' : 'Unknown'}</strong>
          <span className="summary-meta">Operational APIs for workflows, agents, skills and ops.</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">GraphQL plane</span>
          <strong>{gqlTools.length > 0 ? 'Responding' : 'Pending'}</strong>
          <span className="summary-meta">Probe returns {gqlTools.length} tools.</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">MCP plane</span>
          <strong>{payload?.summary?.mcp_plane ? 'Server-side' : 'Unknown'}</strong>
          <span className="summary-meta">Surfaced through Studio/API proof; not exposed directly to browser.</span>
        </div>
      </section>

      <section className="surface-card" style={{ padding: 20 }}>
        <div className="section-title-row">
          <div>
            <div className="eyebrow">GraphQL probe</div>
            <h2>Studio query check</h2>
          </div>
          <Button variant="outline" onClick={load} disabled={loading}>
            <TerminalSquare size={16} /> Run GraphQL probe
          </Button>
        </div>
        <textarea
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          rows={3}
          style={{ width: '100%', marginTop: 12, borderRadius: 12, padding: 12, border: '1px solid var(--md-outline-variant)', background: 'var(--md-surface-container)', color: 'var(--md-on-surface)' }}
        />
        <div className="evidence-list" style={{ marginTop: 12 }}>
          {gqlTools.map((tool) => (
            <div key={tool.name} className="evidence-item">
              <CheckCircle2 size={16} />
              <div>
                <strong>{tool.name}</strong>
                <p className="muted">Protocol: {tool.protocol}</p>
              </div>
            </div>
          ))}
          {gqlTools.length === 0 && <p className="muted">Run the probe to verify GraphQL tool discovery.</p>}
        </div>
      </section>

      {Object.entries(grouped).map(([plane, items]) => {
        const Icon = planeIcons[plane] || Cable;
        return (
          <section className="surface-card" key={plane} style={{ padding: 20 }}>
            <div className="section-title-row">
              <div>
                <div className="eyebrow">{plane}</div>
                <h2><Icon size={20} /> {items.length} connected screens</h2>
              </div>
            </div>
            <div className="proof-grid two" style={{ marginTop: 14 }}>
              {items.map((item) => (
                <div className="proof-card" key={item.route}>
                  <div className="proof-card-title">
                    <CheckCircle2 size={16} />
                    <strong>{item.screen}</strong>
                  </div>
                  <p className="muted">Route: <span className="mono">{item.route}</span></p>
                  <div className="tool-list compact">
                    {(item.endpoints || []).map((endpoint) => (
                      <span className="tag" key={endpoint}>{endpoint}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        );
      })}

      {payload?.notes?.length > 0 && (
        <section className="surface-card" style={{ padding: 20 }}>
          <div className="eyebrow">Notes</div>
          <ul className="muted">
            {payload.notes.map((note) => <li key={note}>{note}</li>)}
          </ul>
        </section>
      )}
    </div>
  );
}
