import { useEffect, useState } from 'react';
import { useAnalyticsStore } from '../store/analyticsStore';
import MetricsCard from '../components/MetricsCard';
import ChartPanel from '../components/ChartPanel';
import Button from '../components/Button';
import ExportDialog from '../components/ExportDialog';
import { Download } from 'lucide-react';

export default function Analytics() {
  const { metrics, timeSeries, workflowMetrics, isLoading, fetchAnalytics } =
    useAnalyticsStore();
  const [exportOpen, setExportOpen] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-on-surface">Analytics Dashboard</h1>
        <Button variant="outline" onClick={() => setExportOpen(true)}>
          <Download size={16} /> Export Data
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-on-surface-variant">Loading analytics...</p>
        </div>
      ) : (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricsCard title="Total Runs" value={metrics.totalRuns} trend={12} index={0} />
            <MetricsCard title="Avg Score" value={metrics.avgScore} unit="/ 10" trend={5} index={1} />
            <MetricsCard title="Total Cost" value={metrics.totalCost} unit="$" trend={-3} index={2} />
            <MetricsCard title="Success Rate" value={metrics.successRate} unit="%" trend={8} index={3} />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-surface-container rounded-2xl p-5">
              <ChartPanel
                title="Daily Activity"
                data={timeSeries}
                type="line"
                xKey="date"
                yKeys={['runs', 'cost']}
              />
            </div>
            <div className="bg-surface-container rounded-2xl p-5">
              <ChartPanel
                title="Workflow Performance"
                data={workflowMetrics}
                type="bar"
                xKey="name"
                yKeys={['runs', 'score']}
              />
            </div>
          </div>

          {/* Table */}
          <div className="bg-surface-container rounded-2xl overflow-hidden">
            <table className="w-full">
              <thead className="bg-surface-container-high border-b border-outline-variant">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-on-surface">Workflow</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-on-surface">Runs</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-on-surface">Score</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-on-surface">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant">
                {workflowMetrics.map((wf) => (
                  <tr key={wf.name} className="hover:bg-surface">
                    <td className="px-6 py-3 text-sm text-on-surface">{wf.name}</td>
                    <td className="px-6 py-3 text-sm text-on-surface-variant">{wf.runs}</td>
                    <td className="px-6 py-3 text-sm text-on-surface-variant">{wf.score.toFixed(1)}</td>
                    <td className="px-6 py-3 text-sm text-on-surface-variant">${wf.cost.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

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
