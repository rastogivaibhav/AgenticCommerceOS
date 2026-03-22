import { useEffect } from 'react';
import { useAnalyticsStore } from '../store/analyticsStore';
import MetricsCard from '../components/MetricsCard';
import ChartPanel from '../components/ChartPanel';
import Button from '../components/Button';
import { Download } from 'lucide-react';

export default function Analytics() {
  const { metrics, timeSeries, workflowMetrics, isLoading, fetchAnalytics } =
    useAnalyticsStore();

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const handleExport = async () => {
    try {
      const blob = await fetch('http://localhost:8000/analytics/export?format=csv').then(r => r.blob());
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold dark:text-white">Analytics Dashboard</h1>
        <Button variant="outline" onClick={handleExport}>
          <Download size={16} /> Export Data
        </Button>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">Loading analytics...</p>
        </div>
      ) : (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricsCard title="Total Runs" value={metrics.totalRuns} trend={12} />
            <MetricsCard title="Avg Score" value={metrics.avgScore} unit="/ 10" trend={5} />
            <MetricsCard title="Total Cost" value={metrics.totalCost} unit="$" trend={-3} />
            <MetricsCard title="Success Rate" value={metrics.successRate} unit="%" trend={8} />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartPanel
              title="Daily Activity"
              data={timeSeries}
              type="line"
              xKey="date"
              yKeys={['runs', 'cost']}
            />
            <ChartPanel
              title="Workflow Performance"
              data={workflowMetrics}
              type="bar"
              xKey="name"
              yKeys={['runs', 'score']}
            />
          </div>

          {/* Table */}
          <div className="bg-white dark:bg-gray-900 rounded-lg border dark:border-gray-800 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold dark:text-white">Workflow</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold dark:text-white">Runs</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold dark:text-white">Score</th>
                  <th className="px-6 py-3 text-left text-sm font-semibold dark:text-white">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y dark:divide-gray-800">
                {workflowMetrics.map((wf) => (
                  <tr key={wf.name} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-6 py-3 text-sm dark:text-white">{wf.name}</td>
                    <td className="px-6 py-3 text-sm dark:text-gray-400">{wf.runs}</td>
                    <td className="px-6 py-3 text-sm dark:text-gray-400">{wf.score.toFixed(1)}</td>
                    <td className="px-6 py-3 text-sm dark:text-gray-400">${wf.cost.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
