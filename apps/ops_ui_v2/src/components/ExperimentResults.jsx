import Button from './Button';
import { Download } from 'lucide-react';

export default function ExperimentResults({ experiment, results }) {
  if (!experiment || !results.length) {
    return (
      <div className="bg-white dark:bg-gray-900 rounded-lg border dark:border-gray-800 p-6 max-w-2xl">
        <p className="text-gray-500 dark:text-gray-400">No results available</p>
      </div>
    );
  }

  const variantA = results.filter((r) => r.variant === 'a');
  const variantB = results.filter((r) => r.variant === 'b');

  const scoreA = variantA.reduce((sum, r) => sum + (r.score || 0), 0) / Math.max(variantA.length, 1);
  const scoreB = variantB.reduce((sum, r) => sum + (r.score || 0), 0) / Math.max(variantB.length, 1);

  const winner = scoreA > scoreB ? 'A' : scoreB > scoreA ? 'B' : 'Tie';

  return (
    <div className="space-y-6">
      <div className="bg-white dark:bg-gray-900 rounded-lg border dark:border-gray-800 p-6">
        <h2 className="text-2xl font-bold dark:text-white mb-6">{experiment.name} - Results</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 dark:bg-blue-900 rounded-lg p-4">
            <p className="text-sm font-medium text-blue-900 dark:text-blue-100">Variant A</p>
            <p className="text-3xl font-bold text-blue-900 dark:text-blue-100 mt-2">{scoreA.toFixed(2)}</p>
            <p className="text-xs text-blue-700 dark:text-blue-300 mt-1">{variantA.length} runs</p>
          </div>

          <div className="bg-green-50 dark:bg-green-900 rounded-lg p-4 flex items-center justify-center">
            <div className="text-center">
              <p className="text-sm font-medium text-green-900 dark:text-green-100">Winner</p>
              <p className="text-3xl font-bold text-green-900 dark:text-green-100 mt-2">Variant {winner}</p>
            </div>
          </div>

          <div className="bg-purple-50 dark:bg-purple-900 rounded-lg p-4">
            <p className="text-sm font-medium text-purple-900 dark:text-purple-100">Variant B</p>
            <p className="text-3xl font-bold text-purple-900 dark:text-purple-100 mt-2">{scoreB.toFixed(2)}</p>
            <p className="text-xs text-purple-700 dark:text-purple-300 mt-1">{variantB.length} runs</p>
          </div>
        </div>
      </div>

      <Button variant="outline" onClick={() => window.print()}>
        <Download size={16} /> Export Results
      </Button>
    </div>
  );
}
