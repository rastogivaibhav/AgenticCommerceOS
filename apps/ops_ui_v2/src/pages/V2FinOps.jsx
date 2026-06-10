import { useEffect, useState } from 'react';
import { getV2Finops } from '../api/northstarAPI';
import './StudioProof.css';
export default function V2FinOps(){const [data,setData]=useState(null);useEffect(()=>{getV2Finops().then(setData)},[]);return <div className="studio-proof-page"><h1 className="studio-proof-title">FinOps</h1><div className="studio-grid"><section className="studio-card"><h2>Summary</h2><p>Cost today: £{data?.summary?.cost_today}</p><p>Avg cost/run: £{data?.summary?.avg_cost_per_run}</p><p>Highest cost agent: {data?.summary?.highest_cost_agent}</p></section><section className="studio-card"><h2>By Agent</h2>{(data?.by_agent||[]).map(a=><p key={a.agent_id}>{a.agent_id}: avg £{a.avg_cost} / budget £{a.budget} — {a.budget_status}</p>)}</section></div></div>}
