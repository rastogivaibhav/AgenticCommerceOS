import { useState } from 'react';
import ExperimentForm from '../components/ExperimentForm';
import ExperimentResults from '../components/ExperimentResults';
import { useExperimentStore } from '../store/experimentStore';

export default function Experiments() {
  const { currentExperiment, results, isRunning } = useExperimentStore();

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold dark:text-white mb-8">Experiments</h1>

      {!currentExperiment ? (
        <ExperimentForm />
      ) : (
        <>
          {isRunning && (
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900 rounded-lg border border-blue-200 dark:border-blue-700">
              <p className="text-sm text-blue-900 dark:text-blue-200">Running experiment...</p>
            </div>
          )}
          <ExperimentResults experiment={currentExperiment} results={results} />
        </>
      )}
    </div>
  );
}
