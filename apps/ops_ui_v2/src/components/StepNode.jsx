import { X, GripVertical } from 'lucide-react';
import Button from './Button';

export default function StepNode({
  id,
  data,
  isSelected,
  onSelect,
  onDelete,
  onUpdate,
}) {
  return (
    <div
      onClick={() => onSelect(id)}
      className={`bg-white dark:bg-gray-900 border-2 rounded-lg p-4 cursor-move transition-all hover:shadow-md ${
        isSelected
          ? 'border-blue-500 shadow-lg'
          : 'border-gray-300 dark:border-gray-700 hover:border-gray-400'
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <GripVertical size={16} className="text-gray-400 cursor-grab" />
          <span className="font-semibold text-sm dark:text-white uppercase tracking-wider">{data.type}</span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(id);
          }}
          className="p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded text-red-600 dark:text-red-400 transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      <input
        type="text"
        placeholder="Step name"
        value={data.name || ''}
        onChange={(e) => onUpdate(id, { name: e.target.value })}
        className="w-full px-2 py-1 text-sm border rounded dark:bg-gray-800 dark:border-gray-700 dark:text-white mb-2 bg-white"
      />

      <textarea
        placeholder="Configuration (JSON)"
        value={data.config || '{}'}
        onChange={(e) => onUpdate(id, { config: e.target.value })}
        className="w-full px-2 py-1 text-xs border rounded font-mono dark:bg-gray-800 dark:border-gray-700 dark:text-white bg-white"
        rows="3"
      />
    </div>
  );
}
