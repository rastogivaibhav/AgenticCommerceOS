import { useEffect, useMemo, useState } from 'react';
import { useAnalyticsStore } from '../store/analyticsStore';
import MetricsCard from '../components/MetricsCard';
import ChartPanel from '../components/ChartPanel';
import Button from '../components/Button';
import ExportDialog from '../components/ExportDialog';
import { Activity, AlertTriangle, DatabaseZap, Download, Layers3, Wallet } from 'lucide-react';

export default function Analytics() {
  const {
    metrics,
    timeSeries,
    workflowMetrics,
    isLoading,
    dataSource,
    loadError,
    lastUpdated,
    fetchAnalytics,
  } =
    useAnalyticsStore();
  const [exportOpen, setExportOpen] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const topWorkflow = useMemo(
    () =>
      [...workflowMetrics].sort((left, right) => Number(right.runs || 0) - Number(left.runs || 0))[0] || null,
    [workflowMetrics],
  );

  const costliestWorkflow = useMemo(
    () =>
      [...workflowMetrics].sort((left, right) => Number(right.cost || 0) - Number(left.cost || 0))[0] || null,
    [workflowMetrics],
  );

  const sourceTone = dataSource === 'fallback' ? 'degraded' : 'healthy';
  const sourceLabel = dataSource === 'fallback' ? 'Fallback sample data' : 'Live analytics response';

  return (
    <div className="page-container">
      <header className="page-header">
        <div>
          <div className="eyebrow">Operational Readability</div>
          <h1>Analytics and Runtime Signal</h1>
          <p className="muted">
            Review workflow volume, service quality, and cost trends without losing sight of whether
            the numbers came from live platform state or a fallback sample.
          </p>
          <div style={{ display: 'flex', gap: 12, marginTop: 12, alignItems: 'center', flexWrap: 'wrap' }}>
            <span className={`status-badge ${sourceTone}`}>{sourceLabel}</span>
            {lastUpdated && (
              <span className="muted">
                Last refreshed {new Date(lastUpdated).toLocaleString()}
              </span>
            )}
          </div>
        </div>
        <div className="header-actions">
          <Button variant="outline" onClick={() => fetchAnalytics()}>
            <DatabaseZap size={16} /> Refresh
          </Button>
          <Button variant="outline" onClick={() => setExportOpen(true)}>
            <Download size={16} /> Export Data
          </Button>
        </div>
      </header>

      <section className="summary-grid">
        <div className="summary-card">
          <span className="summary-label">Workflow with most runs</span>
          <strong>{topWorkflow?.name || 'No run data'}</strong>
          <span className="summary-meta">
            {topWorkflow ? `${topWorkflow.runs} runs in the selected window` : 'No workflow metrics available yet.'}
          </span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Highest spend path</span>
          <strong>{costliestWorkflow?.name || 'No spend data'}</strong>
          <span className="summary-meta">
            {costliestWorkflow ? `$${costliestWorkflow.cost.toFixed(2)} total cost` : 'Spend data is currently empty.'}
          </span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Data provenance</span>
          <strong>{dataSource === 'fallback' ? 'Sampled' : 'Observed'}</strong>
          <span className="summary-meta">
            {dataSource === 'fallback'
              ? 'The UI is showing safe fallback values because analytics calls failed.'
              : 'The dashboard request completed successfully.'}
          </span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Coverage</span>
          <strong>{workflowMetrics.length}</strong>
          <span className="summary-meta">
            Workflows with recorded operating metrics in the current dataset.
          </span>
        </div>
      </section>

      {dataSource === 'fallback' && (
        <section className="surface-card hero-panel" style={{ borderColor: 'rgba(180, 35, 24, 0.18)' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 12,
                display: 'grid',
                placeItems: 'center',
                background: 'var(--md-error-container)',
                color: 'var(--md-on-error-container)',
              }}
            >
              <AlertTriangle size={18} />
            </div>
            <div>
              <h2 style={{ marginBottom: 10 }}>Analytics is in fallback mode</h2>
              <p className="muted">
                These cards and charts are still useful for UI validation, but they should not be used
                for operator decisions until the analytics API can read real platform data again.
              </p>
              {loadError && (
                <div className="secondary-cell" style={{ marginTop: 10 }}>
                  Latest error: {loadError}
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {isLoading ? (
        <section className="surface-card hero-panel">
          <p className="muted">Loading analytics...</p>
        </section>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricsCard title="Total Runs" value={metrics.totalRuns} trend={12} index={0} />
            <MetricsCard title="Avg Score" value={metrics.avgScore} unit="/ 10" trend={5} index={1} />
            <MetricsCard title="Total Cost" value={metrics.totalCost} unit="$" trend={-3} index={2} />
            <MetricsCard title="Success Rate" value={metrics.successRate} unit="%" trend={8} index={3} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="surface-card" style={{ padding: 20 }}>
              <ChartPanel
                title="Daily Activity"
                data={timeSeries}
                type="line"
                xKey="date"
                yKeys={['runs', 'cost']}
              />
            </div>
            <div className="surface-card" style={{ padding: 20 }}>
              <ChartPanel
                title="Workflow Performance"
                data={workflowMetrics}
                type="bar"
                xKey="name"
                yKeys={['runs', 'score']}
              />
            </div>
          </div>

          <section className="surface-card" style={{ overflow: 'hidden' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: 16,
                padding: '18px 20px 0',
                flexWrap: 'wrap',
              }}
            >
              <div>
                <div className="eyebrow" style={{ marginBottom: 8 }}>Workflow Breakdown</div>
                <h2 style={{ margin: 0, color: 'var(--md-on-surface)' }}>Runs, quality, and spend by workflow</h2>
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <span className="tag"><Activity size={14} /> Run volume</span>
                <span className="tag"><Layers3 size={14} /> Score</span>
                <span className="tag"><Wallet size={14} /> Cost</span>
              </div>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Workflow</th>
                  <th>Runs</th>
                  <th>Score</th>
                  <th>Cost</th>
                </tr>
              </thead>
              <tbody>
                {workflowMetrics.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="muted" style={{ padding: 24, textAlign: 'center' }}>
                      No workflow analytics are available yet.
                    </td>
                  </tr>
                ) : (
                  workflowMetrics.map((wf) => (
                    <tr key={wf.name}>
                      <td>
                        <div className="primary-cell">{wf.name}</div>
                        <div className="secondary-cell">
                          {wf.runs > 0 ? 'Observed in the current analytics window.' : 'No recent execution volume.'}
                        </div>
                      </td>
                      <td className="metric-cell">{wf.runs}</td>
                      <td className="metric-cell">{wf.score.toFixed(1)}</td>
                      <td className="metric-cell">${wf.cost.toFixed(2)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </section>

          <ExportDialog
            data={workflowMetrics}
            isOpen={exportOpen}
            onClose={() => setExportOpen(false)}
          />
        </>
      )}
    </div>
  );
}
