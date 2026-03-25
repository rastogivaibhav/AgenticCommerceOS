import { useState } from 'react';
import Button from './Button';
import { useExperimentStore } from '../store/experimentStore';
import { Play } from 'lucide-react';

const WORKFLOW_FAMILIES = [
  { value: 'discovery', label: 'Discovery' },
  { value: 'purchase', label: 'Purchase' },
  { value: 'post_purchase', label: 'Post Purchase' },
  { value: 'service', label: 'Service' },
  { value: 'engagement', label: 'Engagement' },
];

export default function ExperimentForm() {
  const { createExperiment, isRunning } = useExperimentStore();
  const [formData, setFormData] = useState({
    name: '',
    workflow_family: '',
    message: '',
    customer_id: 'cust-1',
    sampleSize: 2,
  });

  const set = (key, value) => setFormData((prev) => ({ ...prev, [key]: value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    await createExperiment({
      name: formData.name,
      workflow_family: formData.workflow_family,
      message: formData.message,
      customer_id: formData.customer_id,
      tenant_id: 'default',
    });
  };

  const inputCls =
    'w-full bg-surface-variant text-on-surface border-b border-outline focus:border-b-2 focus:border-primary rounded-t px-4 py-3 outline-none transition-colors';

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-surface-container rounded-lg border border-outline-variant p-4 md:p-6 max-w-2xl animate-slideIn transition-theme"
    >
      <h2 className="text-xl md:text-2xl font-bold text-on-surface mb-6">Create Experiment</h2>

      <div className="space-y-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-on-surface-variant mb-2">
            Experiment Name
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => set('name', e.target.value)}
            placeholder="e.g., Headphones Discovery Test"
            className={inputCls}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-on-surface-variant mb-2">
            Workflow Family
          </label>
          <select
            value={formData.workflow_family}
            onChange={(e) => set('workflow_family', e.target.value)}
            className={inputCls}
            required
          >
            <option value="">Select workflow family</option>
            {WORKFLOW_FAMILIES.map((wf) => (
              <option key={wf.value} value={wf.value}>
                {wf.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-on-surface-variant mb-2">
            Test Message
          </label>
          <input
            type="text"
            value={formData.message}
            onChange={(e) => set('message', e.target.value)}
            placeholder="e.g., show me noise-cancelling headphones"
            className={inputCls}
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-on-surface-variant mb-2">
            Customer ID
          </label>
          <input
            type="text"
            value={formData.customer_id}
            onChange={(e) => set('customer_id', e.target.value)}
            placeholder="cust-1"
            className={inputCls}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-on-surface-variant mb-2">
            Sample Size{' '}
            <span className="text-xs text-on-surface-variant">
              (informational — backend always runs 2 variants)
            </span>
          </label>
          <input
            type="number"
            value={formData.sampleSize}
            onChange={(e) => set('sampleSize', parseInt(e.target.value))}
            min="2"
            className={inputCls}
            disabled
          />
        </div>
      </div>

      <Button type="submit" variant="filled" className="w-full" disabled={isRunning}>
        <Play size={16} />
        {isRunning ? 'Running…' : 'Run Experiment'}
      </Button>
    </form>
  );
}
