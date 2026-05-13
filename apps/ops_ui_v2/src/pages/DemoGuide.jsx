import { useEffect, useState } from 'react';
import { BookOpenCheck, CheckCircle2, ClipboardList, Play, TerminalSquare } from 'lucide-react';
import { getNorthstarDemoScript } from '../api/northstarAPI';
import './StudioProof.css';

function Section({ title, icon, children }) {
  return (
    <section className="studio-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        {icon}
        <h2 style={{ fontSize: 16, fontWeight: 800, margin: 0 }}>{title}</h2>
      </div>
      {children}
    </section>
  );
}

export default function DemoGuide() {
  const [script, setScript] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    getNorthstarDemoScript().then(setScript).catch((err) => setError(err.message));
  }, []);

  if (!script && !error) return <div className="studio-proof-page">Loading demo guide…</div>;

  return (
    <div className="studio-proof-page">
      <div className="studio-proof-hero">
        <Section title="Demo Guide" icon={<BookOpenCheck size={18} />}>
          <div className="studio-proof-title">{script?.title || 'ACOS North-Star Demo'}</div>
          <p className="studio-proof-muted">
            A guided CTO/buyer demo path showing how ACOS coordinates retail agents, tools, handoffs,
            evidence and runtime readiness. Duration: {script?.duration_minutes || 12} minutes.
          </p>
          {error && <p style={{ color: 'var(--md-error)' }}>{error}</p>}
          <div className="pill-row">
            <span className="status-pill">persona: {script?.persona || 'Retail CTO'}</span>
            <span className="status-pill">live demo message</span>
            <span className="status-pill">evidence-led proof</span>
          </div>
        </Section>

        <Section title="Demo Message" icon={<Play size={18} />}>
          <p className="proof-code">{script?.demo_message}</p>
          <p className="studio-proof-muted">Use this exact message in Studio Proof → Retail Simulation Console.</p>
        </Section>
      </div>

      <div className="studio-proof-grid">
        <Section title="Story Board" icon={<ClipboardList size={18} />}>
          <div className="timeline-list">
            {(script?.storyboard || []).map((item) => (
              <div className="timeline-item" key={item.step}>
                <strong>{item.step}. {item.screen}</strong>
                <div className="studio-proof-muted">Say: {item.say}</div>
                <div className="studio-proof-muted">Prove: {item.prove}</div>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Success Criteria" icon={<CheckCircle2 size={18} />}>
          <div className="timeline-list">
            {(script?.success_criteria || []).map((criterion) => (
              <div className="timeline-item" key={criterion}>
                <strong><CheckCircle2 size={14} /> {criterion}</strong>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Commands to Prove It" icon={<TerminalSquare size={18} />}>
          <div className="timeline-list">
            {(script?.demo_commands || []).map((command) => (
              <div className="timeline-item" key={command}>
                <code>{command}</code>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Demo Notes" icon={<BookOpenCheck size={18} />}>
          {(script?.notes || []).map((note) => <p className="studio-proof-muted" key={note}>• {note}</p>)}
        </Section>
      </div>
    </div>
  );
}
