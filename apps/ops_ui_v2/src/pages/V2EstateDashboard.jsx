import { useEffect, useState } from 'react';
import { getV2EstateSummary, invokeV2A2A } from '../api/northstarAPI';
import './StudioProof.css';

export default function V2EstateDashboard() {
  const [data, setData] = useState(null); const [trace, setTrace] = useState(null); const [error,setError]=useState(null);
  useEffect(()=>{ getV2EstateSummary().then(setData).catch(e=>setError(e.message)); },[]);
  const runDemo = async () => {
    setError(null);
    try { const r = await invokeV2A2A({ tenant_id:'default', channel:'store_partner', actor_type:'partner', channel_mode:'store_partner_assist', message:data?.demo_message || 'I’m buying a cot mattress for a newborn under £250, and I need to know if my previous nursery order can be returned.' }); setTrace(r.trace); }
    catch(e){ setError(e.message); }
  };
  const s=data?.summary||{};
  return <div className="studio-proof-page"><div className="studio-proof-hero"><section className="studio-card"><h1 className="studio-proof-title">ACOS v2 Estate Dashboard</h1><p className="studio-proof-muted">Shared control plane for John Lewis-style specialist agents across customer, Partner, contact-centre and vendor channels.</p>{error&&<p style={{color:'var(--md-error)'}}>{error}</p>}<div className="pill-row"><span className="status-pill">{s.agents||0} agents</span><span className="status-pill">{s.capabilities||0} capabilities</span><span className="status-pill">{s.covered_capabilities||0} covered</span><span className="status-pill">{s.shared_tools||0} shared tools</span><span className="status-pill">{s.a2a_traces||0} A2A traces</span></div><button className="primary-btn" onClick={runDemo}>Run nursery + mattress + returns A2A demo</button></section><section className="studio-card"><h2>North-star proof journey</h2><p>{data?.demo_message}</p>{trace&&<><h3>Final merged response</h3><p>{trace.final_response}</p><div className="pill-row">{trace.agents.map(a=><span className="status-pill" key={a.agent_id}>{a.name}</span>)}</div></>}</section></div></div>;
}
