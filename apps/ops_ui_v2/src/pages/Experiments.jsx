import { useState } from 'react';
import ExperimentForm from '../components/ExperimentForm';
import ExperimentResults from '../components/ExperimentResults';
import { useExperimentStore } from '../store/experimentStore';

export default function Experiments() {
  const { currentExperiment, results, isRunning } = useExperimentStore();

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="page-header" style={{ marginBottom: '2rem' }}>
        <div className="eyebrow">ACOS EXPERIMENTS</div>
        <h1 className="text-3xl font-bold text-on-surface">Experiments</h1>
        <p className="muted">Design and run A/B experiments across workflow variants.</p>
      </div>

      {!currentExperiment ? (
        <ExperimentForm />
      ) : (
        <>
          {isRunning && (
            <div className="mb-6 p-4 bg-surface-container border border-outline-variant rounded-lg">
              <p className="text-sm text-on-surface-variant">Running experiment...</p>
            </div>
          )}
          <ExperimentResults experiment={currentExperiment} results={results} />
        </>
      )}
    </div>
  );
}
