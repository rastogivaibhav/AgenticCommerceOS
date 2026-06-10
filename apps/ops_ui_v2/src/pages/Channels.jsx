import { useEffect, useState } from 'react';
import { CheckCircle2, ExternalLink, MessageCircleMore, QrCode, Send, ShieldCheck, Smartphone, RadioTower, Link2 } from 'lucide-react';
import OAuthModal from '../components/OAuthModal';
import {
  approveChannelSender,
  linkTelegramChannel,
  listChannelPairings,
  linkWhatsAppChannel,
  listChannelApprovals,
  listChannels,
  sendChannelTest,
} from '../api/channelsAPI';
import './Lists.css';

function ModeBadge({ mode }) {
  return (
    <span className={`status-badge ${mode === 'live' ? 'healthy' : 'degraded'}`} style={{ textTransform: 'none' }}>
      {mode === 'live' ? 'Live' : 'Sandbox'}
    </span>
  );
}

export default function Channels() {
  const [channelsPayload, setChannelsPayload] = useState({ channels: [], mode: 'sandbox' });
  const [approvals, setApprovals] = useState([]);
  const [pairingsByChannel, setPairingsByChannel] = useState({});
  const [channelTestResults, setChannelTestResults] = useState({});
  const [linkFeedback, setLinkFeedback] = useState(null);
  // DEF-005: OAuth modal state for timeout handling
  const [oauthModalOpen, setOauthModalOpen] = useState(false);
  const [oauthChannel, setOauthChannel] = useState(null);
  const [whatsAppForm, setWhatsAppForm] = useState({
    identity: 'WhatsApp Support',
    verify_token: '',
    access_token: '',
    phone_number_id: '',
    start_chat_number: '',
    default_recipient: '',
  });
  const [telegramForm, setTelegramForm] = useState({
    identity: 'ACOS Ops Bot',
    bot_token: '',
    default_chat_id: '',
    bot_username: '',
  });

  const refresh = async () => {
    const [channels, approvalsPayload] = await Promise.all([listChannels(), listChannelApprovals()]);
    setChannelsPayload(channels);
    setApprovals(approvalsPayload.approvals || []);
    const pairingEntries = await Promise.all(
      (channels.channels || []).map(async (channel) => {
        try {
          const response = await listChannelPairings(channel.id);
          return [channel.id, response.pairings || []];
        } catch {
          return [channel.id, []];
        }
      }),
    );
    setPairingsByChannel(Object.fromEntries(pairingEntries));
  };

  useEffect(() => {
    refresh().catch(console.error);
  }, []);

  // DEF-005: Show OAuth modal for WhatsApp
  const handleWhatsAppLink = async (event) => {
    event.preventDefault();
    setLinkFeedback(null);
    setOauthChannel('whatsapp');
    setOauthModalOpen(true);
  };

  // DEF-005: Show OAuth modal for Telegram
  const handleTelegramLink = async (event) => {
    event.preventDefault();
    setLinkFeedback(null);
    setOauthChannel('telegram');
    setOauthModalOpen(true);
  };

  // DEF-005: Handle OAuth modal close
  const handleOAuthClose = () => {
    setOauthModalOpen(false);
    setOauthChannel(null);
  };

  // DEF-005: Handle OAuth success
  const handleOAuthSuccess = async () => {
    setLinkFeedback(null);
    try {
      if (oauthChannel === 'whatsapp') {
        const result = await linkWhatsAppChannel({
          type: 'whatsapp',
          identity: whatsAppForm.identity,
          metadata: {
            verify_token: whatsAppForm.verify_token,
            access_token: whatsAppForm.access_token,
            phone_number_id: whatsAppForm.phone_number_id,
            start_chat_number: whatsAppForm.start_chat_number,
            default_recipient: whatsAppForm.default_recipient,
          },
        });
        setLinkFeedback({ channel: 'whatsapp', result });
      } else if (oauthChannel === 'telegram') {
        const result = await linkTelegramChannel({
          type: 'telegram',
          identity: telegramForm.identity,
          metadata: {
            bot_token: telegramForm.bot_token,
            default_chat_id: telegramForm.default_chat_id,
            bot_username: telegramForm.bot_username,
          },
        });
        setLinkFeedback({ channel: 'telegram', result });
      }
      await refresh();
      handleOAuthClose();
    } catch (error) {
      setLinkFeedback({
        channel: oauthChannel,
        error: `OAuth failed: ${error.message}`,
      });
    }
  };

  const handleChannelTest = async (bindingId) => {
    const channel = (channelsPayload.channels || []).find((item) => item.id === bindingId);
    const metadata = channel?.metadata || {};
    const recipient = bindingId === 'telegram-ops'
      ? (telegramForm.default_chat_id || metadata.default_chat_id || '')
      : (whatsAppForm.default_recipient || metadata.default_recipient || metadata.start_chat_number || '');
    try {
      const delivery = await sendChannelTest(bindingId, {
        text: `ACOS test message sent at ${new Date().toISOString()}`,
        recipient,
      });
      setChannelTestResults((current) => ({ ...current, [bindingId]: delivery.delivery }));
    } catch (error) {
      if (error.status === 409) {
        const liveRecipient = error.payload?.recipient || recipient || 'the configured recipient';
        const confirmed = window.confirm(
          `This binding is live and will send a real message to ${liveRecipient}. Continue?`,
        );
        if (!confirmed) {
          setChannelTestResults((current) => ({
            ...current,
            [bindingId]: {
              mode: 'cancelled',
              note: 'Live send cancelled before any outbound message was sent.',
            },
          }));
          return;
        }
        const delivery = await sendChannelTest(bindingId, {
          text: `ACOS test message sent at ${new Date().toISOString()}`,
          recipient,
          confirm_live_send: true,
        });
        setChannelTestResults((current) => ({ ...current, [bindingId]: delivery.delivery }));
        return;
      }
      throw error;
    }
  };

  const handleApprove = async (sender) => {
    await approveChannelSender(sender.id, { display_name: sender.display_name });
    await refresh();
  };

  const totalChannels = (channelsPayload.channels || []).length;
  const liveChannels = (channelsPayload.channels || []).filter((channel) => channel.mode === 'live').length;
  const pendingApprovals = approvals.length;
  const totalPairings = Object.values(pairingsByChannel).reduce((total, entries) => total + entries.length, 0);

  return (
    <div className="page-container list-view">
      <header className="page-header sticky-header">
        <div>
          <div className="eyebrow">Channel Operations</div>
          <h1>WhatsApp and Telegram</h1>
          <p className="muted">
            Connect customer-facing messaging channels to governed workflows, verify health honestly,
            approve unknown senders without auto-linking them to a customer, and confirm live delivery
            before any outbound test is sent.
          </p>
        </div>
      </header>

      <section className="summary-grid">
        <div className="summary-card">
          <span className="summary-label">Linked channels</span>
          <strong>{totalChannels}</strong>
          <span className="summary-meta">Bindings saved in the control plane for operator use.</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Live probes</span>
          <strong>{liveChannels}</strong>
          <span className="summary-meta">Channels whose latest connector probe returned healthy live status.</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Pending approvals</span>
          <strong>{pendingApprovals}</strong>
          <span className="summary-meta">Unknown senders waiting for explicit operator approval.</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Pairing entrypoints</span>
          <strong>{totalPairings}</strong>
          <span className="summary-meta">Scan-to-start or deep-link entrypoints currently exposed.</span>
        </div>
      </section>

      <div className="content-split" style={{ gridTemplateColumns: '1.3fr 1fr' }}>
        <div className="left-panel">
          <section className="transparent-panel" style={{ display: 'grid', gap: 20 }}>
            <div className="glass-card">
              <div className="eyebrow">Linked Channels</div>
              <h2 style={{ marginTop: 6 }}>Current State</h2>
              <div style={{ display: 'grid', gap: 14, marginTop: 18 }}>
                {(channelsPayload.channels || []).map((channel) => (
                  <div key={channel.id} className="widget-section" style={{ marginTop: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
                      <div>
                        <div className="primary-cell">{channel.identity || channel.display_name || channel.id}</div>
                        <div className="secondary-cell mono">{channel.id}</div>
                      </div>
                      <ModeBadge mode={channel.mode} />
                    </div>
                    <div className="history-list" style={{ marginTop: 10 }}>
                      <div className="history-item">
                        <div className="h-left"><ShieldCheck size={14} /><span className="h-id">Status</span></div>
                        <span className="secondary-cell">{channel.status}</span>
                      </div>
                      <div className="history-item">
                        <div className="h-left"><MessageCircleMore size={14} /><span className="h-id">Default route</span></div>
                        <span className="secondary-cell">{channel.default_route}</span>
                      </div>
                      <div className="history-item">
                        <div className="h-left"><RadioTower size={14} /><span className="h-id">Health source</span></div>
                        <span className="secondary-cell">
                          {channel.health?.configured === false ? 'Unconfigured connector' : channel.health?.status || channel.mode}
                        </span>
                      </div>
                      {channel.type === 'whatsapp' && (
                        <div className="history-item">
                          <div className="h-left"><Link2 size={14} /><span className="h-id">Sender target</span></div>
                          <span className="secondary-cell mono">
                            {channel.metadata?.default_recipient || channel.metadata?.start_chat_number || 'Not configured'}
                          </span>
                        </div>
                      )}
                    </div>
                    <button className="secondary-button compact mt-3" onClick={() => handleChannelTest(channel.id)}>
                      <Send size={14} />
                      Send test message
                    </button>
                    <div className="secondary-cell" style={{ marginTop: 8 }}>
                      Sandbox bindings stay preview-only. Live bindings require explicit confirmation with the real recipient shown before the message is sent.
                    </div>
                    {channelTestResults[channel.id] && (
                      <div className="lint-panel" style={{ marginTop: 12 }}>
                        <div className="lint-header">Delivery mode: {channelTestResults[channel.id].mode || 'sandbox'}</div>
                        <div className="lint-success">{channelTestResults[channel.id].note || 'Message accepted by connector.'}</div>
                      </div>
                    )}
                    {(pairingsByChannel[channel.id] || []).length > 0 && (
                      <div className="widget-section" style={{ marginTop: 14 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <QrCode size={14} />
                          <strong>Scan / Start Routes</strong>
                        </div>
                        <div style={{ display: 'grid', gap: 12, marginTop: 12 }}>
                          {(pairingsByChannel[channel.id] || []).map((pairing) => (
                            <div key={pairing.id} className="lint-panel" style={{ marginTop: 0 }}>
                              <div className="lint-header">{pairing.route_name}</div>
                              <div className="secondary-cell">Pair code: <span className="mono">{pairing.pair_code}</span></div>
                              <div className="secondary-cell" style={{ marginTop: 6 }}>
                                Trigger after pairing: {pairing.sample_trigger || 'No sample trigger configured'}
                              </div>
                              <div style={{ display: 'grid', gridTemplateColumns: '112px 1fr', gap: 12, alignItems: 'start', marginTop: 12 }}>
                                <img
                                  src={pairing.qr_url}
                                  alt={`${pairing.route_name} QR`}
                                  style={{ width: 112, height: 112, borderRadius: 12, background: '#fff', padding: 8 }}
                                />
                                <div style={{ display: 'grid', gap: 8 }}>
                                  <div className="secondary-cell">
                                    {pairing.start_ready
                                      ? 'Scan the QR or open the start link from a phone to pair this sender and trigger the route.'
                                      : 'Start link is not ready yet. Add a bot username, start chat number, or default recipient, or send the manual pair text from the linked channel.'}
                                  </div>
                                  <div className="secondary-cell mono" style={{ wordBreak: 'break-all' }}>
                                    {pairing.start_link || pairing.manual_pair_text}
                                  </div>
                                  {pairing.start_ready && (
                                    <a className="secondary-button compact" href={pairing.start_link} target="_blank" rel="noreferrer" style={{ width: 'fit-content' }}>
                                      <ExternalLink size={14} />
                                      Open start link
                                    </a>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card">
              <div className="eyebrow">Approval Queue</div>
              <h2 style={{ marginTop: 6 }}>Unknown Senders</h2>
              <div className="history-list" style={{ marginTop: 18 }}>
                {approvals.length === 0 ? (
                  <div className="secondary-cell">No pending approvals.</div>
                ) : (
                  approvals.map((sender) => (
                    <div key={sender.id} className="history-item" style={{ alignItems: 'flex-start' }}>
                      <div className="h-left" style={{ alignItems: 'flex-start' }}>
                        <Smartphone size={14} />
                        <div>
                          <div className="h-id">{sender.display_name}</div>
                          <div className="secondary-cell mono">{sender.sender_external_id}</div>
                          <div className="secondary-cell">{sender.last_message}</div>
                        </div>
                      </div>
                      <button className="primary-button compact" onClick={() => handleApprove(sender)}>
                        <CheckCircle2 size={14} />
                        Approve
                      </button>
                    </div>
                  ))
                )}
              </div>
              <div className="secondary-cell" style={{ marginTop: 12 }}>
                Approval only marks a sender as trusted. Customer matching must be done deliberately later instead of silently binding every new sender to the same profile.
              </div>
            </div>
          </section>
        </div>

        <div className="right-panel">
          <div className="editor-widget glass-card">
            <div className="widget-header">
              <div>
                <div className="eyebrow">Onboarding</div>
                <h2 className="text-on-surface">Link Channels</h2>
              </div>
            </div>
            <div className="widget-content" style={{ gap: 20 }}>
              {linkFeedback && (
                <div className="widget-section" style={{ marginTop: 0 }}>
                  <h3 className="text-on-surface">Latest Link Result</h3>
                  {linkFeedback.error ? (
                    <div className="text-on-error-container">{linkFeedback.error}</div>
                  ) : (
                    <>
                      <div className="secondary-cell">
                        Saved {linkFeedback.channel} binding as{' '}
                        <strong>{linkFeedback.result?.channel?.identity || linkFeedback.result?.channel?.id}</strong>.
                      </div>
                      <div className="secondary-cell" style={{ marginTop: 8 }}>
                        Probe status:{' '}
                        <strong>{linkFeedback.result?.probe?.status || linkFeedback.result?.channel?.mode || 'unknown'}</strong>
                        {linkFeedback.result?.probe?.status_code ? ` (${linkFeedback.result.probe.status_code})` : ''}
                      </div>
                      {linkFeedback.result?.probe?.error && (
                        <div className="secondary-cell" style={{ marginTop: 8 }}>
                          Reason: {linkFeedback.result.probe.error}
                        </div>
                      )}
                      {linkFeedback.result?.channel?.mode !== 'live' && (
                        <div className="secondary-cell" style={{ marginTop: 8 }}>
                          Credentials may be saved, but this binding will stay in sandbox until the probe succeeds.
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}

              <form className="widget-section" onSubmit={handleWhatsAppLink} style={{ marginTop: 0 }}>
                <h3 className="text-on-surface">WhatsApp</h3>
                <input className="search-input" value={whatsAppForm.identity} onChange={(e) => setWhatsAppForm((c) => ({ ...c, identity: e.target.value }))} placeholder="Identity" />
                <input className="search-input mt-3" required value={whatsAppForm.verify_token} onChange={(e) => setWhatsAppForm((c) => ({ ...c, verify_token: e.target.value }))} placeholder="Verify token" />
                <input className="search-input mt-3" required value={whatsAppForm.access_token} onChange={(e) => setWhatsAppForm((c) => ({ ...c, access_token: e.target.value }))} placeholder="Access token" />
                <input className="search-input mt-3" required value={whatsAppForm.phone_number_id} onChange={(e) => setWhatsAppForm((c) => ({ ...c, phone_number_id: e.target.value }))} placeholder="Phone number ID" />
                <input className="search-input mt-3" value={whatsAppForm.start_chat_number} onChange={(e) => setWhatsAppForm((c) => ({ ...c, start_chat_number: e.target.value }))} placeholder="Start chat number (+447...)" />
                <input className="search-input mt-3" value={whatsAppForm.default_recipient} onChange={(e) => setWhatsAppForm((c) => ({ ...c, default_recipient: e.target.value }))} placeholder="Default test recipient (+447...)" />
                <div className="secondary-cell" style={{ marginTop: 10 }}>
                  Webhook verify URL: <span className="mono">{typeof window !== 'undefined' ? `${window.location.origin}/api/v1/connectors/whatsapp/webhook` : '/api/v1/connectors/whatsapp/webhook'}</span>
                </div>
                <div className="secondary-cell" style={{ marginTop: 6 }}>
                  Meta must call the URL above with your verify token. The channel only becomes live when the probe succeeds.
                </div>
                <div className="secondary-cell" style={{ marginTop: 6 }}>
                  Add a start chat number if you want scan-to-start QR links before live probe metadata is available.
                </div>
                <div className="secondary-cell" style={{ marginTop: 6 }}>
                  Add a default test recipient to make outbound validation predictable before a real customer sender is paired.
                </div>
                <button className="primary-button mt-3" type="submit">Link WhatsApp</button>
              </form>

              <form className="widget-section" onSubmit={handleTelegramLink}>
                <h3 className="text-on-surface">Telegram</h3>
                <input className="search-input" value={telegramForm.identity} onChange={(e) => setTelegramForm((c) => ({ ...c, identity: e.target.value }))} placeholder="Identity" />
                <input className="search-input mt-3" required value={telegramForm.bot_token} onChange={(e) => setTelegramForm((c) => ({ ...c, bot_token: e.target.value }))} placeholder="Bot token" />
                <input className="search-input mt-3" value={telegramForm.default_chat_id} onChange={(e) => setTelegramForm((c) => ({ ...c, default_chat_id: e.target.value }))} placeholder="Default chat ID" />
                <input className="search-input mt-3" value={telegramForm.bot_username} onChange={(e) => setTelegramForm((c) => ({ ...c, bot_username: e.target.value }))} placeholder="Bot username" />
                <div className="secondary-cell" style={{ marginTop: 10 }}>
                  Add the bot username if you want scan-to-start QR links for Telegram deep links.
                </div>
                <button className="primary-button mt-3" type="submit">Link Telegram</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* DEF-005: OAuth modal with timeout handling */}
      <OAuthModal
        isOpen={oauthModalOpen}
        channel={oauthChannel}
        onClose={handleOAuthClose}
        onSuccess={handleOAuthSuccess}
      />
    </div>
  );
}
