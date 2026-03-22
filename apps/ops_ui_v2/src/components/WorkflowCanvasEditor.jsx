import { useState } from 'react';
import { useWorkflowStore } from '../store/workflowStore';
import StepNode from './StepNode';
import ToolPanel from './ToolPanel';
import Button from './Button';
import { Save, Play, AlertCircle } from 'lucide-react';

export default function WorkflowCanvasEditor() {
  const {
    workflow,
    nodes,
    updateWorkflow,
    addNode,
    updateNode,
    deleteNode,
    selectedNode,
    setSelectedNode,
    setSaving,
    isSaving,
  } = useWorkflowStore();

  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleAddStep = (type) => {
    addNode({
      type,
      name: `${type}-${nodes.length + 1}`,
      config: '{}',
    });
  };

  const handleSave = async () => {
    if (!workflow.name.trim()) {
      setError('Workflow name is required');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      // Simulate API call - would call API in real implementation
      await new Promise(r => setTimeout(r, 500));
      setSuccess('Workflow saved as draft');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message || 'Failed to save workflow');
    } finally {
      setSaving(false);
    }
  };

  const handleDeploy = () => {
    if (nodes.length === 0) {
      setError('Add at least one step before deploying');
      return;
    }
    setSuccess('Deploy workflow (feature coming soon)');
  };

  return (
    <div className="flex h-full bg-white dark:bg-gray-950">
      {/* Tool Panel - visible on lg+ screens */}
      <ToolPanel onAddStep={handleAddStep} />

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-800 p-6 bg-white dark:bg-gray-950">
          <div className="max-w-7xl mx-auto space-y-4">
            <input
              type="text"
              placeholder="Workflow name"
              value={workflow.name}
              onChange={(e) => updateWorkflow({ name: e.target.value })}
              className="text-2xl font-bold px-2 py-1 border rounded dark:bg-gray-900 dark:border-gray-700 dark:text-white bg-white w-full md:w-1/2"
            />
            <textarea
              placeholder="Workflow description (optional)"
              value={workflow.description}
              onChange={(e) => updateWorkflow({ description: e.target.value })}
              className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-900 dark:border-gray-700 dark:text-white bg-white"
              rows="2"
            />
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 dark:bg-red-900 border border-red-200 dark:border-red-800 rounded-lg flex gap-3">
            <AlertCircle size={20} className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-red-900 dark:text-red-100">{error}</p>
          </div>
        )}

        {success && (
          <div className="mx-6 mt-4 p-4 bg-green-50 dark:bg-green-900 border border-green-200 dark:border-green-800 rounded-lg flex gap-3">
            <p className="text-sm text-green-900 dark:text-green-100">{success}</p>
          </div>
        )}

        {/* Canvas */}
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-7xl mx-auto">
            {nodes.length === 0 ? (
              <div className="flex items-center justify-center h-64 bg-gray-50 dark:bg-gray-900 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700">
                <p className="text-gray-500 dark:text-gray-400">
                  Click the button below or use the right panel to add your first step
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {nodes.map((node) => (
                  <StepNode
                    key={node.id}
                    id={node.id}
                    data={node}
                    isSelected={selectedNode === node.id}
                    onSelect={setSelectedNode}
                    onDelete={deleteNode}
                    onUpdate={updateNode}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="border-t border-gray-200 dark:border-gray-800 p-6 bg-white dark:bg-gray-950">
          <div className="max-w-7xl mx-auto flex gap-2 justify-end">
            <Button
              variant="outline"
              onClick={handleSave}
              disabled={isSaving}
            >
              <Save size={16} />
              {isSaving ? 'Saving...' : 'Save Draft'}
            </Button>
            <Button
              variant="default"
              onClick={handleDeploy}
            >
              <Play size={16} />
              Deploy Workflow
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Tool Panel - horizontal scroll on small screens */}
      <div className="lg:hidden fixed bottom-20 left-0 right-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 p-4 overflow-x-auto">
        <div className="flex gap-2">
          {['input', 'agent_call', 'data_transform', 'decision', 'output'].map((type) => (
            <Button
              key={type}
              variant="outline"
              size="sm"
              onClick={() => handleAddStep(type)}
              className="flex-shrink-0"
            >
              <Plus size={16} />
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
