import Button from './Button';
import { Download } from 'lucide-react';

export default function ExperimentResults({ experiment, results }) {
  if (!experiment || !results.length) {
    return (
      <div className="bg-surface-container rounded-lg border border-outline-variant p-6 max-w-2xl">
        <p className="text-on-surface-variant">No results available</p>
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
      <div className="bg-surface-container rounded-2xl overflow-hidden border border-outline-variant p-6">
        <h2 className="text-2xl font-bold text-on-surface mb-6">{experiment.name} - Results</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-primary-container text-on-primary-container rounded-2xl p-5">
            <p className="text-sm font-medium">Variant A</p>
            <p className="text-3xl font-bold mt-2">{scoreA.toFixed(2)}</p>
            <p className="text-xs mt-1">{variantA.length} runs</p>
          </div>

          <div className="bg-success-container text-on-success-container rounded-2xl p-5 flex items-center justify-center">
            <div className="text-center">
              <p className="text-sm font-medium">Winner</p>
              <p className="text-3xl font-bold mt-2">Variant {winner}</p>
            </div>
          </div>

          <div className="bg-secondary-container text-on-secondary-container rounded-2xl p-5">
            <p className="text-sm font-medium">Variant B</p>
            <p className="text-3xl font-bold mt-2">{scoreB.toFixed(2)}</p>
            <p className="text-xs mt-1">{variantB.length} runs</p>
          </div>
        </div>
      </div>

      <Button variant="outlined" onClick={() => window.print()}>
        <Download size={16} /> Export Results
      </Button>
    </div>
  );
}
