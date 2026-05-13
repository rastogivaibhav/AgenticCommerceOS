import { useWorkflowStore } from '../store/workflowStore';

export function useWorkflow() {
  return useWorkflowStore();
}
