import { useState } from 'react';
import Button from './Button';
import { Download, X } from 'lucide-react';
import { exportToCSV, exportToJSON } from '../utils/export';

export default function ExportDialog({ data, isOpen, onClose }) {
  const [format, setFormat] = useState('csv');
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const timestamp = new Date().toISOString().split('T')[0];
      if (format === 'csv') {
        exportToCSV(data, `analytics-${timestamp}.csv`);
      } else if (format === 'json') {
        exportToJSON(data, `analytics-${timestamp}.json`);
      }
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />

      {/* Dialog */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-surface-container rounded-lg shadow-lg max-w-sm w-full">
          <div className="flex items-center justify-between p-6 border-b border-outline-variant">
            <h2 className="text-lg font-semibold dark:text-white">Export Analytics</h2>
            <button
              onClick={onClose}
              className="p-1 hover:bg-surface-container-high rounded"
            >
              <X size={20} />
            </button>
          </div>

          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-on-surface-variant mb-2">
                Format
              </label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="w-full px-3 py-2 border rounded bg-surface-variant text-on-surface border-outline-variant"
              >
                <option value="csv">CSV (.csv)</option>
                <option value="json">JSON (.json)</option>
              </select>
            </div>

            <div className="bg-blue-50 dark:bg-blue-900 p-3 rounded text-sm text-blue-900 dark:text-blue-200">
              Exporting analytics data in {format.toUpperCase()} format
            </div>
          </div>

          <div className="p-6 border-t border-outline-variant flex gap-2 justify-end">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button variant="default" onClick={handleExport} disabled={isExporting}>
              <Download size={16} />
              {isExporting ? 'Exporting...' : 'Export'}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
