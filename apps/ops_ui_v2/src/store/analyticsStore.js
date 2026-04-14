import { create } from 'zustand';
import { getMetrics, getTimeSeries, getWorkflowMetrics } from '../api/analyticsAPI';

const STATIC_FALLBACK = {
  metrics: {
    totalRuns: 1523,
    avgScore: 8.7,
    totalCost: 234.56,
    successRate: 94.2,
  },
  timeSeries: [
    { date: 'Mon', runs: 120, cost: 45.2 },
    { date: 'Tue', runs: 145, cost: 52.1 },
    { date: 'Wed', runs: 135, cost: 48.9 },
    { date: 'Thu', runs: 165, cost: 61.3 },
    { date: 'Fri', runs: 190, cost: 72.1 },
    { date: 'Sat', runs: 98, cost: 38.4 },
    { date: 'Sun', runs: 72, cost: 29.2 },
  ],
  workflowMetrics: [
    { name: 'Checkout', runs: 450, score: 9.1, cost: 89.2 },
    { name: 'Recommendation', runs: 380, score: 8.4, cost: 71.5 },
    { name: 'Payment', runs: 320, score: 9.3, cost: 60.1 },
    { name: 'Shipping', runs: 373, score: 8.2, cost: 57.3 },
  ],
};

export const useAnalyticsStore = create((set) => ({
  metrics: {
    totalRuns: 0,
    avgScore: 0,
    totalCost: 0,
    successRate: 0,
  },
  timeSeries: [],
  workflowMetrics: [],
  isLoading: false,
  dataSource: 'live',
  loadError: null,
  lastUpdated: null,

  setMetrics: (metrics) => set({ metrics }),
  setTimeSeries: (timeSeries) => set({ timeSeries }),
  setWorkflowMetrics: (workflowMetrics) => set({ workflowMetrics }),
  setIsLoading: (isLoading) => set({ isLoading }),

  fetchAnalytics: async () => {
    set({ isLoading: true, loadError: null });
    try {
      const [metrics, timeSeries, workflowMetrics] = await Promise.all([
        getMetrics(),
        getTimeSeries(),
        getWorkflowMetrics(),
      ]);
      set({
        metrics,
        timeSeries,
        workflowMetrics,
        dataSource: 'live',
        loadError: null,
        lastUpdated: new Date().toISOString(),
        isLoading: false,
      });
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      set({
        ...STATIC_FALLBACK,
        dataSource: 'fallback',
        loadError: error.message || 'Analytics request failed.',
        lastUpdated: new Date().toISOString(),
        isLoading: false,
      });
    }
  },
}));
