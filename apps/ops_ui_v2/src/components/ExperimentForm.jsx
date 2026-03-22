import { useState } from 'react';
import Button from './Button';
import { useExperimentStore } from '../store/experimentStore';
import { Play, Plus, X } from 'lucide-react';

export default function ExperimentForm() {
  const { createExperiment, runExperiment } = useExperimentStore();
  const [formData, setFormData] = useState({
    name: '',
    workflow: '',
    sampleSize: 100,
  });

  const [variants, setVariants] = useState({
    a: [{ key: 'param1', value: 'value1' }],
    b: [{ key: 'param1', value: 'value2' }],
  });

  const handleAddVariant = (side) => {
    setVariants((prev) => ({
      ...prev,
      [side]: [...prev[side], { key: '', value: '' }],
    }));
  };

  const handleUpdateVariant = (side, index, field, value) => {
    setVariants((prev) => ({
      ...prev,
      [side]: prev[side].map((v, i) =>
        i === index ? { ...v, [field]: value } : v
      ),
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const variantA = Object.fromEntries(variants.a.filter(v => v.key).map(v => [v.key, v.value]));
    const variantB = Object.fromEntries(variants.b.filter(v => v.key).map(v => [v.key, v.value]));

    createExperiment({
      name: formData.name,
      workflowId: formData.workflow,
      variantA,
      variantB,
      sampleSize: formData.sampleSize,
    });

    runExperiment();
    setFormData({ name: '', workflow: '', sampleSize: 100 });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-900 rounded-lg border dark:border-gray-800 p-4 md:p-6 max-w-2xl animate-slideIn transition-theme">
      <h2 className="text-xl md:text-2xl font-bold dark:text-white mb-6">Create Experiment</h2>

      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium dark:text-gray-300 mb-2">Experiment Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g., Checkout Flow Test"
            className="w-full px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700 dark:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium dark:text-gray-300 mb-2">Workflow</label>
          <select
            value={formData.workflow}
            onChange={(e) => setFormData({ ...formData, workflow: e.target.value })}
            className="w-full px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700 dark:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Select workflow</option>
            <option value="checkout">Checkout Flow</option>
            <option value="recommendation">Recommendation Engine</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium dark:text-gray-300 mb-2">Sample Size</label>
          <input
            type="number"
            value={formData.sampleSize}
            onChange={(e) => setFormData({ ...formData, sampleSize: parseInt(e.target.value) })}
            min="10"
            className="w-full px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700 dark:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-6">
        {['a', 'b'].map((side, idx) => (
          <div
            key={side}
            className="border rounded-lg p-4 dark:border-gray-700 animate-fadeInUp transition-theme"
            style={{ animationDelay: `${idx * 50}ms` }}
          >
            <h3 className="font-semibold dark:text-white mb-4">Variant {side.toUpperCase()}</h3>
            <div className="space-y-3">
              {variants[side].map((variant, idx) => (
                <div key={idx} className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Key"
                    value={variant.key}
                    onChange={(e) => handleUpdateVariant(side, idx, 'key', e.target.value)}
                    className="flex-1 px-2 py-1 border rounded text-sm dark:bg-gray-800 dark:border-gray-700 dark:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <input
                    type="text"
                    placeholder="Value"
                    value={variant.value}
                    onChange={(e) => handleUpdateVariant(side, idx, 'value', e.target.value)}
                    className="flex-1 px-2 py-1 border rounded text-sm dark:bg-gray-800 dark:border-gray-700 dark:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {variants[side].length > 1 && (
                    <button
                      type="button"
                      onClick={() =>
                        setVariants((prev) => ({
                          ...prev,
                          [side]: prev[side].filter((_, i) => i !== idx),
                        }))
                      }
                      className="p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded transition-colors"
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => handleAddVariant(side)}
                className="w-full"
              >
                <Plus size={16} /> Add Parameter
              </Button>
            </div>
          </div>
        ))}
      </div>

      <Button type="submit" variant="default" className="w-full">
        <Play size={16} /> Run Experiment
      </Button>
    </form>
  );
}
