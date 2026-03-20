import { useEffect, useState } from 'react'
import './App.css'

const DEFAULT_ENVIRONMENT = 'dev'
const TOKEN_KEY = 'acos_ops_token'

function request(path, token, options = {}) {
  return fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  })
}

function formatTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString()
}

function Login({ onLogin }) {
  const [token, setToken] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const response = await request('/workflows', token)
      if (!response.ok) {
        setError(`Authentication failed (${response.status})`)
      } else {
        sessionStorage.setItem(TOKEN_KEY, token)
        onLogin(token)
      }
    } catch {
      setError('Could not reach the ACOS Ops API')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="eyebrow">ACOS Control Plane</div>
        <h1>Workflow Registry</h1>
        <p className="muted">
          Sign in with an ops bearer token to review workflow versions, promotions, and audit history.
        </p>
        <form onSubmit={handleSubmit} className="login-form">
          <label htmlFor="token">Bearer token</label>
          <input
            id="token"
            type="password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="Paste bearer token"
          />
          {error ? <div className="error-banner">{error}</div> : null}
          <button className="primary-button" type="submit" disabled={loading || !token.trim()}>
            {loading ? 'Signing in...' : 'Enter control plane'}
          </button>
        </form>
      </div>
    </div>
  )
}

function Header({ environment, onRefresh, onSignOut }) {
  return (
    <header className="page-header">
      <div>
        <div className="eyebrow">ACOS Operating System</div>
        <h1>Workflow Registry</h1>
        <p className="muted">
          Govern active workflow versions, track promotions, and inspect control-plane audit history.
        </p>
      </div>
      <div className="header-actions">
        <div className="environment-badge">Environment: {environment}</div>
        <button className="secondary-button" onClick={onRefresh}>Refresh</button>
        <button className="danger-button" onClick={onSignOut}>Sign out</button>
      </div>
    </header>
  )
}

function SummaryCards({ workflows }) {
  const active = workflows.filter((workflow) => workflow.active_version).length
  const drafts = workflows.filter((workflow) => workflow.status === 'draft').length
  const totalVersions = workflows.reduce((count, workflow) => count + (workflow.version_count || 0), 0)

  return (
    <section className="summary-grid">
      <article className="summary-card">
        <span className="summary-label">Registered workflows</span>
        <strong>{workflows.length}</strong>
      </article>
      <article className="summary-card">
        <span className="summary-label">Active in environment</span>
        <strong>{active}</strong>
      </article>
      <article className="summary-card">
        <span className="summary-label">Draft workflows</span>
        <strong>{drafts}</strong>
      </article>
      <article className="summary-card">
        <span className="summary-label">Tracked versions</span>
        <strong>{totalVersions}</strong>
      </article>
    </section>
  )
}

function CreateWorkflowForm({ onCreate, busy }) {
  const [form, setForm] = useState({
    tenant_id: 'default',
    name: '',
    workflow_family: 'discovery',
    description: '',
    business_owner: 'acos-team',
    change_summary: 'Initial workflow draft',
  })

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    await onCreate(form)
    setForm((current) => ({ ...current, name: '', description: '' }))
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Create workflow draft</div>
          <p className="muted compact">Seed a new workflow identity and its first draft version.</p>
        </div>
      </div>
      <form className="create-grid" onSubmit={handleSubmit}>
        <label>
          <span>Name</span>
          <input value={form.name} onChange={(event) => updateField('name', event.target.value)} required />
        </label>
        <label>
          <span>Tenant</span>
          <input value={form.tenant_id} onChange={(event) => updateField('tenant_id', event.target.value)} />
        </label>
        <label>
          <span>Workflow family</span>
          <select value={form.workflow_family} onChange={(event) => updateField('workflow_family', event.target.value)}>
            <option value="discovery">Discovery</option>
            <option value="purchase">Purchase</option>
            <option value="post_purchase">Post purchase</option>
            <option value="service">Service</option>
            <option value="engagement">Engagement</option>
          </select>
        </label>
        <label>
          <span>Business owner</span>
          <input value={form.business_owner} onChange={(event) => updateField('business_owner', event.target.value)} />
        </label>
        <label className="full-width">
          <span>Description</span>
          <textarea
            value={form.description}
            onChange={(event) => updateField('description', event.target.value)}
            rows={3}
          />
        </label>
        <label className="full-width">
          <span>Change summary</span>
          <input value={form.change_summary} onChange={(event) => updateField('change_summary', event.target.value)} />
        </label>
        <div className="full-width form-actions">
          <button className="primary-button" type="submit" disabled={busy || !form.name.trim()}>
            {busy ? 'Creating...' : 'Create draft'}
          </button>
        </div>
      </form>
    </section>
  )
}

function CreateVersionForm({ onCreateVersion, busy }) {
  const [form, setForm] = useState({
    change_summary: 'Workflow revision',
    validation_status: 'draft',
  })

  async function handleSubmit(event) {
    event.preventDefault()
    await onCreateVersion(form)
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <label className="inline-field grow">
        <span>Change summary</span>
        <input
          value={form.change_summary}
          onChange={(event) => setForm((current) => ({ ...current, change_summary: event.target.value }))}
          required
        />
      </label>
      <label className="inline-field">
        <span>Status</span>
        <select
          value={form.validation_status}
          onChange={(event) => setForm((current) => ({ ...current, validation_status: event.target.value }))}
        >
          <option value="draft">Draft</option>
          <option value="validated">Validated</option>
          <option value="approved">Approved</option>
        </select>
      </label>
      <button className="primary-button" type="submit" disabled={busy || !form.change_summary.trim()}>
        {busy ? 'Saving version...' : 'Create version'}
      </button>
    </form>
  )
}

function WorkflowTable({ workflows, selectedId, onSelect }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Workflow inventory</div>
          <p className="muted compact">Versioned workflows currently tracked by the control plane.</p>
        </div>
      </div>
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Family</th>
              <th>Tenant</th>
              <th>Status</th>
              <th>Active version</th>
              <th>Versions</th>
              <th>Last promoted</th>
            </tr>
          </thead>
          <tbody>
            {workflows.map((workflow) => (
              <tr
                key={workflow.id}
                className={workflow.id === selectedId ? 'selected-row' : ''}
                onClick={() => onSelect(workflow.id)}
              >
                <td>
                  <div className="primary-cell">{workflow.name}</div>
                  <div className="secondary-cell">{workflow.id}</div>
                </td>
                <td><span className={`tag tag-${workflow.workflow_family}`}>{workflow.workflow_family}</span></td>
                <td>{workflow.tenant_id}</td>
                <td>{workflow.status}</td>
                <td>{workflow.active_version || '-'}</td>
                <td>{workflow.version_count || 0}</td>
                <td>{formatTime(workflow.last_promoted_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function VersionsPanel({ detail, environment, onCreateVersion, creatingVersion, onPromote, promoting }) {
  const versions = detail?.versions || []
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Versions</div>
          <p className="muted compact">Create revisions, track approval state, and promote approved versions.</p>
        </div>
      </div>
      <CreateVersionForm onCreateVersion={onCreateVersion} busy={creatingVersion} />
      <div className="list-stack">
        {versions.map((version) => (
          <div className="list-card" key={version.id}>
            <div>
              <div className="primary-cell">{version.version}</div>
              <div className="secondary-cell">{version.change_summary}</div>
            </div>
            <div className="list-meta">
              <span>{version.validation_status}</span>
              <span>{version.lifecycle_state}</span>
              <button
                className="secondary-button"
                disabled={promoting === version.version || version.validation_status !== 'approved'}
                onClick={() => onPromote(version.version)}
              >
                {promoting === version.version
                  ? `Promoting to ${environment}...`
                  : version.validation_status !== 'approved'
                    ? 'Approval required'
                    : `Promote to ${environment}`}
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

function PromotionsPanel({ promotions }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Promotion history</div>
          <p className="muted compact">Environment-aware activations and roll-forward history.</p>
        </div>
      </div>
      <div className="list-stack">
        {promotions.length ? promotions.map((promotion) => (
          <div className="list-card" key={`${promotion.workflow_id}-${promotion.version}-${promotion.id}`}>
            <div>
              <div className="primary-cell">{promotion.version} to {promotion.target_environment}</div>
              <div className="secondary-cell">{promotion.note || 'No approval note recorded'}</div>
            </div>
            <div className="list-meta">
              <span>{promotion.status}</span>
              <span>{promotion.is_active ? 'active' : 'superseded'}</span>
              <span>{formatTime(promotion.promoted_at)}</span>
            </div>
          </div>
        )) : <div className="empty-state">No promotions recorded yet.</div>}
      </div>
    </section>
  )
}

function AuditPanel({ audits }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Audit trail</div>
          <p className="muted compact">Control-plane mutations recorded for workflow governance.</p>
        </div>
      </div>
      <div className="list-stack">
        {audits.length ? audits.map((audit) => (
          <div className="list-card" key={`${audit.resource_id}-${audit.id}`}>
            <div>
              <div className="primary-cell">{audit.action}</div>
              <div className="secondary-cell">{audit.actor} at {formatTime(audit.created_at)}</div>
            </div>
          </div>
        )) : <div className="empty-state">No audit entries for this workflow.</div>}
      </div>
    </section>
  )
}

function RecentRunsPanel({ runs }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <div className="panel-title">Recent runs</div>
          <p className="muted compact">Latest executions tied to this workflow identity.</p>
        </div>
      </div>
      <div className="list-stack">
        {runs.length ? runs.map((run) => (
          <div className="list-card" key={run.id}>
            <div>
              <div className="primary-cell">{run.id}</div>
              <div className="secondary-cell">{run.customer_id} | {run.journey}</div>
            </div>
            <div className="list-meta">
              <span>{run.workflow_version || '-'}</span>
              <span>{formatTime(run.created_at)}</span>
            </div>
          </div>
        )) : <div className="empty-state">No runs linked to this workflow yet.</div>}
      </div>
    </section>
  )
}

function DetailPane({
  detail,
  environment,
  onCreateVersion,
  creatingVersion,
  onPromote,
  promoting,
}) {
  if (!detail) {
    return (
      <section className="panel detail-empty">
        <div className="panel-title">Workflow detail</div>
        <p className="muted">Select a workflow from the inventory to inspect versions, promotions, audit events, and recent runs.</p>
      </section>
    )
  }

  const workflow = detail.workflow
  return (
    <div className="detail-grid">
      <section className="panel hero-panel">
        <div className="eyebrow">Workflow detail</div>
        <h2>{workflow.name}</h2>
        <p className="muted">{workflow.description || 'No description provided.'}</p>
        <div className="hero-meta">
          <span className={`tag tag-${workflow.workflow_family}`}>{workflow.workflow_family}</span>
          <span>Tenant: {workflow.tenant_id}</span>
          <span>Status: {workflow.status}</span>
          <span>Active: {workflow.active_version || '-'}</span>
        </div>
      </section>
      <VersionsPanel
        detail={detail}
        environment={environment}
        onCreateVersion={onCreateVersion}
        creatingVersion={creatingVersion}
        onPromote={onPromote}
        promoting={promoting}
      />
      <PromotionsPanel promotions={detail.promotions || []} />
      <AuditPanel audits={detail.audits || []} />
      <RecentRunsPanel runs={detail.runs || []} />
    </div>
  )
}

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY) || '')
  const [environment, setEnvironment] = useState(DEFAULT_ENVIRONMENT)
  const [workflows, setWorkflows] = useState([])
  const [selectedWorkflowId, setSelectedWorkflowId] = useState('')
  const [detail, setDetail] = useState(null)
  const [busyCreate, setBusyCreate] = useState(false)
  const [busyVersionCreate, setBusyVersionCreate] = useState(false)
  const [promotingVersion, setPromotingVersion] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function loadWorkflows(preferredId) {
    if (!token) return
    setLoading(true)
    setError('')
    try {
      const response = await request('/workflows', token)
      if (response.status === 401 || response.status === 403) {
        handleSignOut()
        return
      }
      const data = await response.json()
      const nextEnvironment = data.environment || DEFAULT_ENVIRONMENT
      const items = data.workflows || []
      setEnvironment(nextEnvironment)
      setWorkflows(items)
      const nextSelectedId = preferredId || selectedWorkflowId || items[0]?.id || ''
      setSelectedWorkflowId(nextSelectedId)
      if (nextSelectedId) {
        await loadWorkflowDetail(nextSelectedId, nextEnvironment)
      } else {
        setDetail(null)
      }
    } catch {
      setError('Could not load workflow inventory')
    } finally {
      setLoading(false)
    }
  }

  async function loadWorkflowDetail(workflowId, nextEnvironment = environment) {
    if (!workflowId || !token) return
    try {
      const response = await request(`/workflows/${workflowId}?environment=${nextEnvironment}`, token)
      if (!response.ok) {
        setError('Could not load workflow detail')
        return
      }
      const data = await response.json()
      setDetail(data)
      setSelectedWorkflowId(workflowId)
    } catch {
      setError('Could not load workflow detail')
    }
  }

  async function handleCreate(form) {
    setBusyCreate(true)
    setError('')
    try {
      const response = await request('/workflows', token, {
        method: 'POST',
        body: JSON.stringify(form),
      })
      if (!response.ok) {
        const data = await response.json()
        setError(data.error || 'Could not create workflow draft')
      } else {
        const data = await response.json()
        await loadWorkflows(data.workflow.id)
      }
    } catch {
      setError('Could not create workflow draft')
    } finally {
      setBusyCreate(false)
    }
  }

  async function handleCreateVersion(form) {
    if (!detail?.workflow?.id) return
    setBusyVersionCreate(true)
    setError('')
    try {
      const response = await request(`/workflows/${detail.workflow.id}/versions`, token, {
        method: 'POST',
        body: JSON.stringify(form),
      })
      if (!response.ok) {
        const data = await response.json()
        setError(data.error || 'Could not create workflow version')
      } else {
        await loadWorkflows(detail.workflow.id)
      }
    } catch {
      setError('Could not create workflow version')
    } finally {
      setBusyVersionCreate(false)
    }
  }

  async function handlePromote(version) {
    if (!detail?.workflow?.id) return
    setPromotingVersion(version)
    setError('')
    try {
      const response = await request(`/workflows/${detail.workflow.id}/versions/${version}/promote`, token, {
        method: 'POST',
        body: JSON.stringify({
          target_environment: environment,
          approval_note: `Promoted from control plane to ${environment}`,
        }),
      })
      if (!response.ok) {
        const data = await response.json()
        setError(data.error || 'Could not promote workflow version')
      } else {
        await loadWorkflows(detail.workflow.id)
      }
    } catch {
      setError('Could not promote workflow version')
    } finally {
      setPromotingVersion('')
    }
  }

  function handleSignOut() {
    sessionStorage.removeItem(TOKEN_KEY)
    setToken('')
    setWorkflows([])
    setDetail(null)
    setSelectedWorkflowId('')
  }

  useEffect(() => {
    if (token) {
      loadWorkflows()
    }
  }, [token])

  if (!token) {
    return <Login onLogin={setToken} />
  }

  return (
    <div className="app-shell">
      <Header environment={environment} onRefresh={() => loadWorkflows(selectedWorkflowId)} onSignOut={handleSignOut} />
      {error ? <div className="error-banner app-banner">{error}</div> : null}
      <SummaryCards workflows={workflows} />
      <div className="content-grid">
        <div className="left-column">
          <CreateWorkflowForm onCreate={handleCreate} busy={busyCreate} />
          <WorkflowTable
            workflows={workflows}
            selectedId={selectedWorkflowId}
            onSelect={(workflowId) => loadWorkflowDetail(workflowId)}
          />
        </div>
        <div className="right-column">
          {loading ? <section className="panel detail-empty">Loading workflows...</section> : null}
          {!loading ? (
            <DetailPane
              detail={detail}
              environment={environment}
              onCreateVersion={handleCreateVersion}
              creatingVersion={busyVersionCreate}
              onPromote={handlePromote}
              promoting={promotingVersion}
            />
          ) : null}
        </div>
      </div>
    </div>
  )
}

export default App
