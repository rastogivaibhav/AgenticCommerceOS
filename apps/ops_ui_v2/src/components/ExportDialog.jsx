import { useState, useCallback } from 'react';
import Button from './Button';
import { Download, X, AlertCircle } from 'lucide-react';
import { exportToCSV, exportToJSON } from '../utils/export';

export default function ExportDialog({ data, isOpen, onClose }) {
  const [format, setFormat] = useState('csv');
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const MAX_RETRIES = 3;

  const handleExport = useCallback(async () => {
    setIsExporting(true);
    setError(null);

    try {
      // DEF-004: Add timeout to prevent indefinite exports
      const exportPromise = new Promise((resolve, reject) => {
        try {
          const timestamp = new Date().toISOString().split('T')[0];
          const filename = `analytics-${timestamp}.${format === 'csv' ? 'csv' : 'json'}`;

          if (format === 'csv') {
            exportToCSV(data, filename);
          } else if (format === 'json') {
            exportToJSON(data, filename);
          }

          resolve();
        } catch (err) {
          reject(err);
        }
      });

      // 30-second timeout for export
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(
          () => reject(new Error('Export timeout - took longer than 30 seconds')),
          30000
        )
      );

      await Promise.race([exportPromise, timeoutPromise]);

      // Success - just close the dialog
      setIsExporting(false);
      setRetryCount(0);
      onClose();
    } catch (error) {
      console.error('Export failed:', error);
      setError({
        message: error.message || 'Failed to export analytics',
        details: error.toString(),
      });
      setIsExporting(false);
    }
  }, [format, data, onClose]);

  const handleRetry = useCallback(() => {
    if (retryCount < MAX_RETRIES) {
      setRetryCount((prev) => prev + 1);
      handleExport();
    } else {
      setError({
        ...error,
        message: 'Export failed after 3 attempts. Please try again later or contact support.',
      });
    }
  }, [retryCount, handleExport, error]);

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
              disabled={isExporting}
            >
              <X size={20} />
            </button>
          </div>

          <div className="p-6 space-y-4">
            {/* Format Selection */}
            {!error && (
              <div>
                <label className="block text-sm font-medium text-on-surface-variant mb-2">
                  Format
                </label>
                <select
                  value={format}
                  onChange={(e) => setFormat(e.target.value)}
                  className="w-full px-3 py-2 border rounded bg-surface-variant text-on-surface border-outline-variant"
                  disabled={isExporting}
                >
                  <option value="csv">CSV (.csv)</option>
                  <option value="json">JSON (.json)</option>
                </select>
              </div>
            )}

            {/* Info Message */}
            {!error && (
              <div className="bg-blue-50 dark:bg-blue-900 p-3 rounded text-sm text-blue-900 dark:text-blue-200">
                {isExporting ? (
                  <>
                    <span className="inline-block mr-2 animate-spin">⟳</span>
                    Exporting analytics data in {format.toUpperCase()} format...
                  </>
                ) : (
                  <>Exporting analytics data in {format.toUpperCase()} format</>
                )}
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 dark:bg-red-900 p-4 rounded border border-red-200 dark:border-red-700">
                <div className="flex gap-3">
                  <AlertCircle size={20} className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-red-900 dark:text-red-200 mb-1">
                      Export failed
                    </h3>
                    <p className="text-sm text-red-800 dark:text-red-300 mb-2">
                      {error.message}
                    </p>
                    {retryCount < MAX_RETRIES && (
                      <p className="text-xs text-red-700 dark:text-red-400">
                        Retry attempt {retryCount} of {MAX_RETRIES}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-6 border-t border-outline-variant flex gap-2 justify-end">
            {error ? (
              <>
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                {retryCount < MAX_RETRIES && (
                  <Button variant="default" onClick={handleRetry} disabled={isExporting}>
                    🔄 Retry ({retryCount}/{MAX_RETRIES})
                  </Button>
                )}
              </>
            ) : (
              <>
                <Button variant="outline" onClick={onClose} disabled={isExporting}>
                  Cancel
                </Button>
                <Button variant="default" onClick={handleExport} disabled={isExporting}>
                  <Download size={16} />
                  {isExporting ? 'Exporting...' : 'Export'}
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
