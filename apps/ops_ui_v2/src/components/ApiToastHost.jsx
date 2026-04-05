import { useEffect, useState } from 'react';

const MAX_TOASTS = 4;
const TIMEOUT_MS = 5000;

export default function ApiToastHost() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    let seq = 0;

    const onToast = (event) => {
      const detail = event?.detail || {};
      const id = `${Date.now()}-${seq++}`;
      const toast = {
        id,
        message: detail.message || 'Request failed',
        tone: detail.tone || 'error',
      };
      setToasts((prev) => [toast, ...prev].slice(0, MAX_TOASTS));
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, TIMEOUT_MS);
    };

    window.addEventListener('ops-api-toast', onToast);
    return () => window.removeEventListener('ops-api-toast', onToast);
  }, []);

  if (!toasts.length) return null;

  return (
    <div className="api-toast-host" role="status" aria-live="polite">
      {toasts.map((toast) => (
        <div key={toast.id} className={`api-toast api-toast-${toast.tone}`}>
          {toast.message}
        </div>
      ))}
    </div>
  );
}
