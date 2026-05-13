import { create } from 'zustand';
import { apiFetch } from '../api/client';

export const useExperimentStore = create((set, get) => ({
  experiments: [],
  currentExperiment: null,
  isRunning: false,

  fetchExperiments: async () => {
    try {
      const res = await apiFetch('/experiments');
      if (!res.ok) return;
      const data = await res.json();
      set({ experiments: data.experiments || [] });
    } catch (e) {
      console.error('fetchExperiments error', e);
    }
  },

  createExperiment: async (formData) => {
    set({ isRunning: true });
    try {
      const res = await apiFetch('/experiments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        console.error('createExperiment API error', err);
        return;
      }
      const result = await res.json();
      set({ currentExperiment: result });
      await get().fetchExperiments();
    } catch (e) {
      console.error('createExperiment error', e);
    } finally {
      set({ isRunning: false });
    }
  },

  setCurrentExperiment: (exp) => set({ currentExperiment: exp }),

  resetExperiment: () => set({
    currentExperiment: null,
    isRunning: false,
  }),
}));
