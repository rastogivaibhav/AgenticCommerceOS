import { create } from 'zustand';

export const useWorkflowStore = create((set) => ({
  // Workflow metadata
  workflow: {
    id: '',
    name: '',
    description: '',
    family: 'default',
    owner: 'analyst',
  },

  // Canvas state
  nodes: [],
  edges: [],
  selectedNode: null,

  // UI state
  isDraft: true,
  isSaving: false,

  // Workflow actions
  setWorkflowId: (id) => set((state) => ({
    workflow: { ...state.workflow, id }
  })),

  updateWorkflow: (updates) => set((state) => ({
    workflow: { ...state.workflow, ...updates }
  })),

  // Node actions
  addNode: (node) => set((state) => ({
    nodes: [...state.nodes, { id: Date.now().toString(), ...node }]
  })),

  updateNode: (id, updates) => set((state) => ({
    nodes: state.nodes.map(n => n.id === id ? { ...n, ...updates } : n)
  })),

  deleteNode: (id) => set((state) => ({
    nodes: state.nodes.filter(n => n.id !== id),
    edges: state.edges.filter(e => e.source !== id && e.target !== id)
  })),

  setSelectedNode: (id) => set({ selectedNode: id }),

  // Edge actions
  addEdge: (edge) => set((state) => ({
    edges: [...state.edges, edge]
  })),

  deleteEdge: (edgeId) => set((state) => ({
    edges: state.edges.filter(e => e.id !== edgeId)
  })),

  // Save state
  setSaving: (saving) => set({ isSaving: saving }),

  // Reset
  reset: () => set({
    workflow: { id: '', name: '', description: '', family: 'default', owner: 'analyst' },
    nodes: [],
    edges: [],
    selectedNode: null,
    isDraft: true,
    isSaving: false,
  }),
}));
