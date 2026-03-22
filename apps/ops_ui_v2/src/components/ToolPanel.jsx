import Button from './Button';
import { Plus } from 'lucide-react';

const stepTypes = [
  'input',
  'agent_call',
  'data_transform',
  'decision',
  'output',
];

export default function ToolPanel({ onAddStep }) {
  return (
    <div className="w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 p-4 overflow-y-auto hidden lg:block">
      <h3 className="font-semibold dark:text-white mb-4 text-sm uppercase tracking-wide">Add Steps</h3>
      <div className="space-y-2">
        {stepTypes.map((type) => (
          <Button
            key={type}
            variant="outline"
            size="sm"
            className="w-full justify-start text-left"
            onClick={() => onAddStep(type)}
          >
            <Plus size={16} />
            {type.replace(/_/g, ' ')}
          </Button>
        ))}
      </div>
    </div>
  );
}
