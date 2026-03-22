import { useState, useEffect } from 'react';
import { Database, Zap, Lock, Globe, ChevronRight, Play, AlertOctagon } from 'lucide-react';
import Editor from '@monaco-editor/react';
import './Lists.css';

export default function Skills() {
  const [skills, setSkills] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSkillId, setSelectedSkillId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showAuthorModal, setShowAuthorModal] = useState(false);
  const [form, setForm] = useState({ 
    name: '', 
    category: 'Integration', 
    type: 'read',
    techStack: 'Python Requests',
    httpMethod: 'GET',
    deploymentCycle: 'Immediate'
  });
  const [isDeploying, setIsDeploying] = useState(false);

  const fetchSkills = () => {
    setIsLoading(true);
    fetch('http://localhost:8000/api/v1/skills')
      .then(res => res.json())
      .then(data => setSkills(data.skills || []))
      .catch(err => console.error('Failed to load skills:', err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchSkills();
  }, []);

  const handleAuthor = async (e) => {
    e.preventDefault();
    setIsDeploying(true);
    const newId = 'sk_' + form.name.toLowerCase().replace(/[^a-z0-9]/g, '_');
    const newSkill = {
      id: newId,
      name: form.name,
      category: form.category,
      type: form.type,
      tech_stack: form.techStack,
      status: form.deploymentCycle === 'Immediate' ? 'active' : 'staged',
      calls: '0',
      code: "def evaluate():\n    pass\n",
      linterWarnings: []
    };
    try {
      await fetch('http://localhost:8000/api/v1/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSkill)
      });
      setShowAuthorModal(false);
      setForm({ name: '', category: 'Integration', type: 'read', techStack: 'Python Requests', httpMethod: 'GET', deploymentCycle: 'Immediate' });
      fetchSkills();
      setSelectedSkillId(newId);
    } catch (err) {
      console.error(err);
    } finally {
      setIsDeploying(false);
    }
  };

  const filtered = skills.filter(s => s.name.toLowerCase().includes(searchTerm.toLowerCase()) || s.category.toLowerCase().includes(searchTerm.toLowerCase()));
  const selectedSkill = skills.find(s => s.id === selectedSkillId);

  const getTypeIcon = (category) => {
    switch(category) {
      case 'Integration': return <Database size={16} />;
      case 'Core': return <Zap size={16} />;
      case 'External': return <Globe size={16} />;
      default: return <Lock size={16} />;
    }
  };

  return (
    <div className="page-container list-view">
      {showAuthorModal && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: 640 }}>
            <h2>Create New Skill</h2>
            <p className="muted">Inject a new integration hook into the operational cluster.</p>
            <form onSubmit={handleAuthor} className="modal-form">
              <div className="form-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <label>
                  Skill Name
                  <input required value={form.name} onChange={e => setForm({...form, name: e.target.value})} placeholder="e.g. Check Warranty" />
                </label>
                <label>
                  Category
                  <select value={form.category} onChange={e => setForm({...form, category: e.target.value})}>
                    <option value="Integration">Integration</option>
                    <option value="Finance">Finance</option>
                    <option value="CRM">CRM</option>
                    <option value="Logistics">Logistics</option>
                  </select>
                </label>
                
                <label>
                  I/O Type
                  <select value={form.type} onChange={e => setForm({...form, type: e.target.value})}>
                    <option value="read">Read Only</option>
                    <option value="write">Write/Mutate</option>
                  </select>
                </label>

                <label>
                  Tech Stack Integration
                  <select value={form.techStack} onChange={e => setForm({...form, techStack: e.target.value})}>
                    <option value="Python Requests">Python Requests</option>
                    <option value="GCP Function">GCP Function (Serverless)</option>
                    <option value="Vertex AI Plugin">Vertex AI Plugin</option>
                  </select>
                </label>
              </div>

              {form.techStack === 'Python Requests' && (
                <div className="dynamic-fields" style={{ marginTop: 16, padding: 16, background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
                  <h4 style={{ margin: '0 0 12px 0', color: 'var(--accent)' }}>HTTP Request Configuration</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 3fr', gap: 16 }}>
                    <label>
                      Method
                      <select value={form.httpMethod} onChange={e => setForm({...form, httpMethod: e.target.value})}>
                        <option value="GET">GET</option>
                        <option value="POST">POST</option>
                        <option value="PUT">PUT</option>
                      </select>
                    </label>
                    <label>
                      Target Endpoint
                      <input type="url" placeholder="https://api.system.local/v1/..." />
                    </label>
                  </div>
                </div>
              )}

              {['GCP Function', 'Vertex AI Plugin'].includes(form.techStack) && (
                <div className="dynamic-fields" style={{ marginTop: 16, padding: 16, background: 'rgba(255,255,255,0.03)', borderRadius: 8 }}>
                  <h4 style={{ margin: '0 0 12px 0', color: 'var(--accent)' }}>Google Cloud Identity</h4>
                  <label>
                    Service Endpoint / URI
                    <input type="text" placeholder="https://REGION-PROJECT.cloudfunctions.net/..." />
                  </label>
                </div>
              )}

              <div className="lifecycle-options" style={{ marginTop: 24 }}>
                <h4 style={{ margin: '0 0 12px 0', color: '#fff' }}>Deployment Lifecycle Timing</h4>
                <div style={{ display: 'flex', gap: 24 }}>
                  <label className="radio-label" style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                    <input type="radio" value="Immediate" checked={form.deploymentCycle === 'Immediate'} onChange={e => setForm({...form, deploymentCycle: e.target.value})} />
                    Deploy Immediately (Active)
                  </label>
                  <label className="radio-label" style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                    <input type="radio" value="Next Cycle" checked={form.deploymentCycle === 'Next Cycle'} onChange={e => setForm({...form, deploymentCycle: e.target.value})} />
                    Stage for Next Release Cycle
                  </label>
                </div>
              </div>

              <div className="modal-actions" style={{ marginTop: 32 }}>
                <button type="button" className="secondary-button" onClick={() => setShowAuthorModal(false)}>Cancel Drop</button>
                <button type="submit" className="primary-button" disabled={isDeploying || !form.name.trim()}>
                  {isDeploying ? 'Deploying...' : form.deploymentCycle === 'Immediate' ? 'Deploy Now' : 'Stage Skill'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <header className="page-header sticky-header">
        <div>
          <div className="eyebrow">ACOS Capabilities</div>
          <h1>Skill Library</h1>
          <p className="muted">Browse and manage pluggable skills, API integrations, and utilities used by agents.</p>
        </div>
        <div className="header-actions">
          <input 
            className="search-input" 
            placeholder="Search skills..." 
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
          <button className="primary-button" onClick={() => setShowAuthorModal(true)}>Create Skill</button>
        </div>
      </header>

      <div className={`content-split ${selectedSkill ? 'panel-open' : ''}`}>
        <div className="left-panel">
          <section className="transparent-panel">
            <div className="table-wrap glass-table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Skill Name</th>
                    <th>Category</th>
                    <th>Type</th>
                    <th>Vol.</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    Array.from({length: 4}).map((_, i) => (
                      <tr key={`skel-${i}`}>
                        <td colSpan="5"><div className="skeleton-row" style={{width: '100%', height: '40px'}}></div></td>
                      </tr>
                    ))
                  ) : filtered.length === 0 ? (
                     <tr><td colSpan="5" style={{textAlign: 'center', padding: '32px'}} className="muted">No skills found.</td></tr>
                  ) : filtered.map(skill => (
                    <tr 
                      key={skill.id} 
                      className={`interactive-row ${selectedSkillId === skill.id ? 'selected-row' : ''}`}
                      onClick={() => setSelectedSkillId(skill.id)}
                    >
                      <td>
                        <div className="skill-name-cell">
                          <div className="skill-icon-wrap">{getTypeIcon(skill.category)}</div>
                          <div>
                            <div className="primary-cell">{skill.name}</div>
                            <div className="secondary-cell mono">{skill.id}</div>
                          </div>
                        </div>
                      </td>
                      <td><span className="tag-category">{skill.category}</span></td>
                      <td>
                        <span className={`tag-type ${skill.type}`}>{skill.type.toUpperCase()}</span>
                      </td>
                      <td className="metric-cell">{skill.calls}</td>
                      <td><ChevronRight size={16} className="text-muted" /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        {selectedSkill && (
          <div className="right-panel">
            <div className="editor-widget glass-card code-widget">
              <div className="widget-header">
                <div>
                  <div className="eyebrow">Skill Editor</div>
                  <div className="skill-title-group">
                    <h2 style={{color: '#fff', margin: 0}}>{selectedSkill.name}</h2>
                    <span className={`tag-type ${selectedSkill.type}`}>{selectedSkill.type.toUpperCase()}</span>
                  </div>
                </div>
                <button className="close-btn" onClick={() => setSelectedSkillId(null)}>×</button>
              </div>
              
              <div className="monaco-container">
                <Editor
                  height="100%"
                  defaultLanguage="python"
                  theme="vs-dark"
                  value={selectedSkill.code}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 13,
                    fontFamily: 'Consolas, monospace',
                    scrollBeyondLastLine: false,
                    padding: { top: 16 }
                  }}
                />
              </div>

              <div className="lint-panel">
                <div className="lint-header">
                  <AlertOctagon size={14} className={selectedSkill.linterWarnings?.length ? 'text-warn' : 'text-success'} /> 
                  Static Analysis {selectedSkill.linterWarnings?.length ? `(${selectedSkill.linterWarnings.length} Issues)` : '(Clean)'}
                </div>
                {selectedSkill.linterWarnings?.length > 0 ? (
                  <ul className="lint-list">
                    {selectedSkill.linterWarnings.map((w, i) => (
                      <li key={i}>{w}</li>
                    ))}
                  </ul>
                ) : (
                  <div className="lint-success">All validations passed. Ready for deployment.</div>
                )}
              </div>
              
              <div className="widget-footer">
                <div style={{display: 'flex', gap: '8px'}}>
                  <button className="primary-button compact">Commit Code</button>
                  <button className="secondary-button compact"><Play size={14} style={{marginRight: '6px'}}/> Test Run</button>
                </div>
                <button className="danger-button compact outline enable-btn">Disable Skill</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
