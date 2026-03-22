import { create } from 'zustand';

export const useExperimentStore = create((set) => ({
  experiments: [],
  currentExperiment: null,
  results: [],
  isRunning: false,

  createExperiment: (exp) => set((state) => ({
    experiments: [...state.experiments, {
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
      status: 'draft',
      ...exp,
    }],
  })),

  setCurrentExperiment: (exp) => set({ currentExperiment: exp }),

  runExperiment: () => set({ isRunning: true }),

  setResults: (results) => set((state) => ({
    results,
    isRunning: false,
    currentExperiment: state.currentExperiment ? {
      ...state.currentExperiment,
      status: 'completed',
    } : null,
  })),

  resetExperiment: () => set({
    currentExperiment: null,
    results: [],
    isRunning: false,
  }),
}));
