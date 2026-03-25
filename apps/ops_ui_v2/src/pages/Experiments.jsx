import { useEffect } from 'react';
import ExperimentForm from '../components/ExperimentForm';
import ExperimentResults from '../components/ExperimentResults';
import Button from '../components/Button';
import { useExperimentStore } from '../store/experimentStore';
import { Plus } from 'lucide-react';

function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export default function Experiments() {
  const { currentExperiment, experiments, isRunning, fetchExperiments, resetExperiment } =
    useExperimentStore();

  useEffect(() => {
    fetchExperiments();
  }, []);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <div className="eyebrow">ACOS EXPERIMENTS</div>
        <h1 className="text-3xl font-bold text-on-surface">Experiments</h1>
        <p className="muted">Design and run A/B experiments across workflow variants.</p>
      </div>

      {/* Past Experiments Table */}
      {experiments.length > 0 && (
        <div className="mb-8 bg-surface-container rounded-lg border border-outline-variant overflow-hidden">
          <div className="px-4 py-3 border-b border-outline-variant">
            <h2 className="text-base font-semibold text-on-surface">Past Experiments</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-outline-variant">
                  <th className="text-left px-4 py-2 text-on-surface-variant font-medium">Name</th>
                  <th className="text-left px-4 py-2 text-on-surface-variant font-medium">Winner</th>
                  <th className="text-right px-4 py-2 text-on-surface-variant font-medium">Score A</th>
                  <th className="text-right px-4 py-2 text-on-surface-variant font-medium">Score B</th>
                  <th className="text-right px-4 py-2 text-on-surface-variant font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp) => {
                  const scoreA = exp.variant_a?.score ?? '—';
                  const scoreB = exp.variant_b?.score ?? '—';
                  return (
                    <tr
                      key={exp.id}
                      className="border-b border-outline-variant last:border-0 hover:bg-surface-container-high transition-colors"
                    >
                      <td className="px-4 py-3 text-on-surface font-medium">{exp.name}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-container text-on-primary-container">
                          Variant {exp.winner || '—'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-on-surface-variant tabular-nums">
                        {typeof scoreA === 'number' ? scoreA.toFixed(1) : scoreA}
                      </td>
                      <td className="px-4 py-3 text-right text-on-surface-variant tabular-nums">
                        {typeof scoreB === 'number' ? scoreB.toFixed(1) : scoreB}
                      </td>
                      <td className="px-4 py-3 text-right text-on-surface-variant">
                        {formatDate(exp.created_at)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Form / Results */}
      {!currentExperiment ? (
        <ExperimentForm />
      ) : (
        <>
          {isRunning && (
            <div className="mb-6 p-4 bg-surface-container border border-outline-variant rounded-lg">
              <p className="text-sm text-on-surface-variant">Running experiment…</p>
            </div>
          )}
          <ExperimentResults experiment={currentExperiment} />
          <div className="mt-4">
            <Button variant="outlined" onClick={resetExperiment}>
              <Plus size={16} /> New Experiment
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
