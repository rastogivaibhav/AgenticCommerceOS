import { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import { getOpsContext, updateRuntimePreferences } from '../api/opsAPI';
import { canOperate } from '../lib/rbac';
import './Layout.css';

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [context, setContext] = useState(null);
  const [contextError, setContextError] = useState(null);
  const [isUpdatingPreferences, setIsUpdatingPreferences] = useState(false);

  const refreshContext = async () => {
    const payload = await getOpsContext();
    setContext(payload);
    setContextError(null);
    return payload;
  };

  useEffect(() => {
    let isMounted = true;
    refreshContext()
      .then((payload) => {
        if (!isMounted) return;
        setContext(payload);
        setContextError(null);
      })
      .catch((error) => {
        if (!isMounted) return;
        setContextError({ message: error.message, status: error.status });
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const handlePreferencesUpdate = async (nextPreferences) => {
    if (!canOperate()) return;
    setIsUpdatingPreferences(true);
    try {
      const payload = await updateRuntimePreferences(nextPreferences);
      setContext(payload.context || null);
      setContextError(null);
    } catch (error) {
      setContextError({ message: error.message, status: error.status });
    } finally {
      setIsUpdatingPreferences(false);
    }
  };

  const authRequired = !context && contextError?.status === 401;

  if (authRequired) {
    return (
      <div className="login-shell">
        <div className="login-card">
          <div className="eyebrow">Ops Authentication</div>
          <h1>Sign in required</h1>
          <p className="muted">
            The UI is loading correctly, but the control-plane APIs are refusing unauthenticated access.
            Bootstrap a local role token before using the registry or workflow designer.
          </p>
          <div className="form-actions" style={{ justifyContent: 'flex-start', gap: 12, marginTop: 24 }}>
            <a className="primary-button" href="/dev/auth/bootstrap/admin?redirect=%2Fui%2Fworkflows">
              Sign in as local admin
            </a>
            <a className="secondary-button" href="/dev/auth/bootstrap/ops?redirect=%2Fui%2Fworkflows">
              Sign in as ops user
            </a>
          </div>
          <p className="muted" style={{ marginTop: 16 }}>
            If local bootstrap is unavailable, check `OPS_JWT_SECRET` or `ALLOW_INSECURE_DEV_AUTH` in the
            running `ops-api` service.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-surface">
      <Sidebar isOpen={menuOpen} onClose={() => setMenuOpen(false)} />
      <div className="flex flex-col flex-1 overflow-hidden">
        <Header
          context={context}
          contextError={contextError}
          canOperate={canOperate()}
          isUpdatingPreferences={isUpdatingPreferences}
          onPreferencesUpdate={handlePreferencesUpdate}
          onMenuToggle={() => setMenuOpen(!menuOpen)}
        />
        <main className="flex-1 overflow-auto bg-surface">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
