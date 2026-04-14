import { useEffect, useState } from 'react';
import { MessageSquareText, PlayCircle, Route as RouteIcon, Send, ShieldCheck } from 'lucide-react';
import { listDemoRoutes, simulateDemoRoute } from '../api/demoRoutesAPI';
import { getRuntimeProviders } from '../api/opsAPI';
import { listChannels } from '../api/channelsAPI';
import './Lists.css';

const RUNTIME_LABELS = {
  google_genai: 'Google GenAI',
  local_openai_host: 'Local LLM (host)',
  local_openai_docker: 'Local LLM (docker)',
  local_fallback: 'Local fallback',
};

export default function DemoRoutes() {
  const [payload, setPayload] = useState({ routes: [], mode: 'sandbox' });
  const [channelsPayload, setChannelsPayload] = useState({ channels: [] });
  const [runtime, setRuntime] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [dispatchForm, setDispatchForm] = useState({
    message: 'Where is my order ORD-1001?',
    channel_binding_id: 'whatsapp-support',
    sender_external_id: 'whatsapp:+447700900001',
    display_name: 'Ava Morgan',
    tenant_id: 'default',
    environment: 'dev',
  });
  const [dispatchResult, setDispatchResult] = useState(null);

  useEffect(() => {
    Promise.all([listDemoRoutes(), getRuntimeProviders(), listChannels()])
      .then(([routesPayload, runtimePayload, linkedChannels]) => {
        setPayload(routesPayload);
        setSelectedRoute(routesPayload.routes?.[0] || null);
        setRuntime(runtimePayload);
        setChannelsPayload(linkedChannels);
      })
      .catch(console.error);
  }, []);

  const handleDispatch = async () => {
    if (!selectedRoute) return;
    const result = await simulateDemoRoute(selectedRoute.id, dispatchForm);
    setDispatchResult(result);
  };

  const liveChannelCount = (channelsPayload.channels || []).filter((channel) => channel.mode === 'live').length;
  const selectedBinding = (channelsPayload.channels || []).find((channel) => channel.id === dispatchForm.channel_binding_id);

  return (
    <div className="page-container list-view">
      <header className="page-header sticky-header">
        <div>
          <div className="eyebrow">Retail Demo Dispatch</div>
          <h1>Channel-Triggered Demo Routes</h1>
          <p className="muted">
            Trigger one of the supported retail routes from WhatsApp or Telegram, inspect tool traces,
            and verify that the reply and ops notification were both produced.
          </p>
        </div>
      </header>

      <section className="summary-grid">
        <div className="summary-card">
          <span className="summary-label">Available routes</span>
          <strong>{payload.routes?.length || 0}</strong>
          <span className="summary-meta">Canonical retail scenarios currently exposed for safe dispatch testing.</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Linked channel bindings</span>
          <strong>{channelsPayload.channels?.length || 0}</strong>
          <span className="summary-meta">Bindings that can be used to simulate inbound route dispatch.</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Live messaging paths</span>
          <strong>{liveChannelCount}</strong>
          <span className="summary-meta">Linked channels whose most recent probe is healthy and live-capable.</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Preferred runtime</span>
          <strong>{selectedRoute?.preferred_runtime || 'Select a route'}</strong>
          <span className="summary-meta">The runtime hint currently attached to the selected route.</span>
        </div>
      </section>

      <div className="content-split" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <div className="left-panel">
          <section className="transparent-panel">
            <div className="glass-card">
              <div className="eyebrow">Available Routes</div>
              <h2 style={{ marginTop: 6 }}>Supported Paths</h2>
              <div className="history-list" style={{ marginTop: 18 }}>
                {(payload.routes || []).map((route) => (
                  <div
                    key={route.id}
                    className="history-item"
                    style={{
                      cursor: 'pointer',
                      border: selectedRoute?.id === route.id ? '1px solid var(--md-primary)' : undefined,
                      borderRadius: 12,
                      padding: 12,
                    }}
                    onClick={() => setSelectedRoute(route)}
                  >
                    <div className="h-left">
                      <RouteIcon size={14} />
                      <div>
                        <div className="h-id">{route.name}</div>
                        <div className="secondary-cell">{route.description}</div>
                        <div className="secondary-cell mono">{route.sample_trigger}</div>
                        <div className="secondary-cell" style={{ marginTop: 6 }}>
                          Systems: {(route.systems || []).join(', ')}
                        </div>
                      </div>
                    </div>
                    <span className={`status-badge ${route.mode === 'live' ? 'healthy' : 'degraded'}`}>
                      {route.mode === 'live' ? 'Live-capable' : 'Sandbox-first'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>

        <div className="right-panel">
          <div className="editor-widget glass-card">
            <div className="widget-header">
              <div>
                <div className="eyebrow">Dispatch</div>
                <h2 className="text-on-surface">{selectedRoute?.name || 'Select a route'}</h2>
              </div>
            </div>
            <div className="widget-content" style={{ gap: 20 }}>
              <div className="widget-section" style={{ marginTop: 0 }}>
                <h3 className="text-on-surface">Runtime Truth</h3>
                <div className="secondary-cell">
                  Platform mode: {runtime?.platform_mode || 'normal'} | Data mode: {runtime?.data_mode === 'live' ? 'live' : 'fallback'}
                </div>
                <div className="secondary-cell" style={{ marginTop: 8 }}>
                  Preferred LLM: {RUNTIME_LABELS[runtime?.providers?.preferred_provider_resolved] || runtime?.providers?.preferred_provider_resolved || 'auto'}
                </div>
                <div className="secondary-cell" style={{ marginTop: 8 }}>
                  Host local: {runtime?.local_openai_profiles?.local_openai_host?.available
                    ? `available (${runtime.local_openai_profiles.local_openai_host.model || 'loaded model'})`
                    : 'unavailable'}
                </div>
                <div className="secondary-cell" style={{ marginTop: 8 }}>
                  Docker local: {runtime?.local_openai_profiles?.local_openai_docker?.available
                    ? `available (${runtime.local_openai_profiles.local_openai_docker.model || 'loaded model'})`
                    : 'unavailable'}
                </div>
                <div className="secondary-cell" style={{ marginTop: 8 }}>
                  Route mode: {selectedRoute?.mode || 'sandbox'} | Supported channels: {(selectedRoute?.supported_channels || []).join(', ') || 'n/a'}
                </div>
              </div>

              <div className="widget-section">
                <h3 className="text-on-surface">Simulate inbound message</h3>
                <select className="search-input" value={dispatchForm.channel_binding_id} onChange={(e) => setDispatchForm((c) => ({ ...c, channel_binding_id: e.target.value }))}>
                  {(channelsPayload.channels || []).map((channel) => (
                    <option key={channel.id} value={channel.id}>
                      {channel.id}
                    </option>
                  ))}
                </select>
                <input className="search-input mt-3" value={dispatchForm.sender_external_id} onChange={(e) => setDispatchForm((c) => ({ ...c, sender_external_id: e.target.value }))} placeholder="Sender external id" />
                <input className="search-input mt-3" value={dispatchForm.display_name} onChange={(e) => setDispatchForm((c) => ({ ...c, display_name: e.target.value }))} placeholder="Display name" />
                <textarea className="search-input mt-3" rows="4" value={dispatchForm.message} onChange={(e) => setDispatchForm((c) => ({ ...c, message: e.target.value }))} />
                {selectedBinding && (
                  <div className="secondary-cell" style={{ marginTop: 10 }}>
                    Dispatching via <strong>{selectedBinding.identity || selectedBinding.id}</strong> in {selectedBinding.mode} mode.
                  </div>
                )}
                <button className="primary-button mt-3" onClick={handleDispatch}>
                  <PlayCircle size={16} />
                  Run Route
                </button>
              </div>

              {dispatchResult && (
                <>
                  <div className="widget-section">
                    <h3 className="text-on-surface">Customer Reply</h3>
                    <div className="secondary-cell">{dispatchResult.response_text}</div>
                    <div className="secondary-cell" style={{ marginTop: 8 }}>
                      Delivery: {dispatchResult.channel_reply?.mode || 'sandbox'} {dispatchResult.channel_reply?.note ? `| ${dispatchResult.channel_reply.note}` : ''}
                    </div>
                  </div>

                  <div className="widget-section">
                    <h3 className="text-on-surface">Visible Tool Trace</h3>
                    <div className="history-list">
                      {(dispatchResult.tool_trace || []).map((step, index) => (
                        <div key={`${step.system}-${step.tool}-${index}`} className="history-item">
                          <div className="h-left">
                            <ShieldCheck size={14} />
                            <div>
                              <div className="h-id">{step.system} / {step.tool}</div>
                              <div className="secondary-cell">mode: {step.mode} | status: {step.status}</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="widget-section">
                    <h3 className="text-on-surface">Ops Notifications</h3>
                    <div className="history-list">
                      {(dispatchResult.notifications || []).map((item, index) => (
                        <div key={`${item.target}-${index}`} className="history-item">
                          <div className="h-left">
                            <Send size={14} />
                            <div>
                              <div className="h-id">{item.target}</div>
                              <div className="secondary-cell">{item.delivery?.mode || 'sandbox'} {item.delivery?.note || 'delivered'}</div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="widget-section">
                    <h3 className="text-on-surface">Workflow + Agent</h3>
                    <div className="secondary-cell">Run: {dispatchResult.run_id || 'n/a'}</div>
                    <div className="secondary-cell">Workflow: {dispatchResult.workflow?.workflow_id || 'n/a'}</div>
                    <div className="secondary-cell">
                      Runtime: {RUNTIME_LABELS[dispatchResult.agent?.runtime?.provider] || RUNTIME_LABELS[dispatchResult.route?.preferred_runtime] || dispatchResult.agent?.runtime?.provider || dispatchResult.route?.preferred_runtime}
                    </div>
                    <div className="secondary-cell" style={{ marginTop: 8 }}>
                      {(dispatchResult.agent?.explanation?.explanation_text || dispatchResult.agent?.recommendation?.recommendation_text || '').trim()}
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
