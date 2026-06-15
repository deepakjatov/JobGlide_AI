import { useState, useEffect, useCallback } from 'react';
import { getProfile, saveProfile, getLLMProviders, uploadResumeFile } from '../api/applyApi';
import './ProfilePage.css';

const EMPTY_EXP = { company: '', role: '', duration: '', description: '' };

export default function ProfilePage() {
  const [profile, setProfile] = useState({
    name: '', email: '', phone: '', location: '',
    linkedin_url: '', github_url: '', portfolio_url: '',
    skills: [], resume_text: '', resume_filename: '', work_experience: [],
    llm_provider: 'ollama', llm_model: 'qwen2.5:14b',
  });
  const [skillInput, setSkillInput] = useState('');
  const [providers, setProviders] = useState([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // File Upload states
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploadError, setUploadError] = useState('');

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await handleUpload(e.target.files[0]);
    }
  };

  const handleUpload = async (file) => {
    setUploading(true);
    setUploadError('');
    try {
      const res = await uploadResumeFile(file);
      if (res.ok) {
        set('resume_filename', res.filename);
        // Load latest profile to get extracted resume text
        const latestProfile = await getProfile();
        if (latestProfile && Object.keys(latestProfile).length) {
          setProfile(prev => ({ ...prev, ...latestProfile }));
        }
      }
    } catch (err) {
      setUploadError(err.message || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  useEffect(() => {
    Promise.all([getProfile(), getLLMProviders()]).then(([p, provs]) => {
      setProviders(provs);
      setProfile(prev => {
        let updated = { ...prev };
        if (p && Object.keys(p).length) {
          updated = { ...updated, ...p };
        }
        // Check if the currently set LLM provider and model are available
        const activeProvider = provs.find(pr => pr.provider === updated.llm_provider && pr.available);
        if (!activeProvider || (updated.llm_model && !activeProvider.models.includes(updated.llm_model))) {
          // Fallback to the first available model from any provider
          const firstAvail = provs.find(pr => pr.available && pr.models.length > 0);
          if (firstAvail) {
            updated.llm_provider = firstAvail.provider;
            updated.llm_model = firstAvail.models[0];
          }
        }
        return updated;
      });
    });
  }, []);

  const set = (field, value) => setProfile(p => ({ ...p, [field]: value }));

  const addSkill = (e) => {
    if ((e.key === 'Enter' || e.key === ',') && skillInput.trim()) {
      e.preventDefault();
      const s = skillInput.trim().replace(/,$/, '');
      if (s && !profile.skills.includes(s)) set('skills', [...profile.skills, s]);
      setSkillInput('');
    }
  };
  const removeSkill = (s) => set('skills', profile.skills.filter(x => x !== s));

  const addExp = () => set('work_experience', [...profile.work_experience, { ...EMPTY_EXP }]);
  const removeExp = (i) => set('work_experience', profile.work_experience.filter((_, idx) => idx !== i));
  const updateExp = (i, field, value) => {
    const exps = [...profile.work_experience];
    exps[i] = { ...exps[i], [field]: value };
    set('work_experience', exps);
  };

  const handleSave = async () => {
    setSaving(true);
    await saveProfile(profile);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  // Build grouped model options
  const modelOptions = providers.flatMap(p =>
    p.models.map(m => ({ value: `${p.provider}::${m}`, label: m, provider: p.provider, providerLabel: p.label, available: p.available }))
  );

  const currentModelKey = `${profile.llm_provider}::${profile.llm_model}`;

  const handleModelChange = (val) => {
    const [prov, ...rest] = val.split('::');
    set('llm_provider', prov);
    set('llm_model', rest.join('::'));
  };

  return (
    <div className="profile-page">
      <div className="profile-hero">
        <h1>Your Profile</h1>
        <p>This information is used to pre-fill job applications and generate cover letters.</p>
      </div>

      <div className="profile-grid">
        {/* ── Personal Info ── */}
        <section className="profile-card">
          <h2><span className="card-icon">👤</span> Personal Info</h2>
          <div className="form-row">
            <div className="form-group">
              <label>Full Name</label>
              <input value={profile.name} onChange={e => set('name', e.target.value)} placeholder="Deepak Jatov" />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input type="email" value={profile.email} onChange={e => set('email', e.target.value)} placeholder="you@email.com" />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Phone</label>
              <input value={profile.phone} onChange={e => set('phone', e.target.value)} placeholder="+91 9876543210" />
            </div>
            <div className="form-group">
              <label>Location</label>
              <input value={profile.location} onChange={e => set('location', e.target.value)} placeholder="Delhi, India" />
            </div>
          </div>
        </section>

        {/* ── Online Presence ── */}
        <section className="profile-card">
          <h2><span className="card-icon">🔗</span> Online Presence</h2>
          <div className="form-group">
            <label>LinkedIn URL</label>
            <input value={profile.linkedin_url} onChange={e => set('linkedin_url', e.target.value)} placeholder="https://linkedin.com/in/yourhandle" />
          </div>
          <div className="form-group">
            <label>GitHub URL</label>
            <input value={profile.github_url} onChange={e => set('github_url', e.target.value)} placeholder="https://github.com/yourhandle" />
          </div>
          <div className="form-group">
            <label>Portfolio URL</label>
            <input value={profile.portfolio_url} onChange={e => set('portfolio_url', e.target.value)} placeholder="https://yourportfolio.dev" />
          </div>
        </section>

        {/* ── Skills ── */}
        <section className="profile-card">
          <h2><span className="card-icon">⚡</span> Skills</h2>
          <div className="form-group">
            <label>Add skills (press Enter or comma)</label>
            <input
              value={skillInput}
              onChange={e => setSkillInput(e.target.value)}
              onKeyDown={addSkill}
              placeholder="React, FastAPI, Python..."
            />
          </div>
          <div className="skills-tags">
            {profile.skills.map(s => (
              <span key={s} className="skill-tag">
                {s}
                <button onClick={() => removeSkill(s)}>×</button>
              </span>
            ))}
            {profile.skills.length === 0 && <span className="no-skills">No skills added yet</span>}
          </div>
        </section>

        {/* ── LLM Settings ── */}
        <section className="profile-card">
          <h2><span className="card-icon">🤖</span> AI Model for Cover Letters</h2>
          <div className="form-group">
            <label>Select Model</label>
            <select
              value={currentModelKey}
              onChange={e => handleModelChange(e.target.value)}
              className="model-select"
            >
              {providers.map(p => (
                <optgroup key={p.provider} label={`${p.label}${!p.available ? ' 🔒' : ''}`} disabled={!p.available}>
                  {p.models.map(m => (
                    <option key={`${p.provider}::${m}`} value={`${p.provider}::${m}`} disabled={!p.available}>
                      {m}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
            {providers.length === 0 && <span className="hint">Loading available models…</span>}
          </div>
          {providers.map(p => !p.available && (
            <div key={p.provider} className="provider-warning">
              ⚠️ {p.label}: {p.reason}
            </div>
          ))}
        </section>

        {/* ── Resume / Summary ── */}
        <section className="profile-card full-width">
          <h2><span className="card-icon">📄</span> Resume / Summary</h2>
          
          <div className="resume-upload-container">
            <div 
              className={`drag-drop-zone ${dragActive ? "drag-active" : ""} ${profile.resume_filename ? "has-file" : ""}`}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
            >
              <input 
                type="file" 
                id="resume-file-input" 
                className="file-input-hidden" 
                accept=".pdf,.txt"
                onChange={handleFileChange}
                disabled={uploading}
              />
              <label htmlFor="resume-file-input" className="file-input-label">
                {uploading ? (
                  <span className="upload-spinner">Uploading & parsing PDF... ⏳</span>
                ) : profile.resume_filename ? (
                  <div className="file-info-view">
                    <span className="file-icon">📄</span>
                    <span className="file-name">{profile.resume_filename}</span>
                    <span className="file-hint">(Drag & drop or click to replace resume PDF/TXT)</span>
                  </div>
                ) : (
                  <div className="upload-prompt">
                    <span className="upload-icon">📤</span>
                    <span className="upload-text">Drag & drop your resume PDF here, or <strong>browse</strong></span>
                    <span className="file-hint">Accepts PDF or TXT formats. Text will be extracted automatically.</span>
                  </div>
                )}
              </label>
            </div>
            {uploadError && <div className="upload-error-msg">❌ {uploadError}</div>}
          </div>

          <div className="form-group" style={{ marginTop: '1.5rem' }}>
            <label>Extracted Resume Text (used for AI Cover Letter generation)</label>
            <textarea
              value={profile.resume_text}
              onChange={e => set('resume_text', e.target.value)}
              placeholder="Paste your resume text here, or upload a PDF above..."
              rows={12}
            />
          </div>
        </section>

        {/* ── Work Experience ── */}
        <section className="profile-card full-width">
          <h2><span className="card-icon">💼</span> Work Experience</h2>
          {profile.work_experience.map((exp, i) => (
            <div key={i} className="exp-block">
              <div className="exp-header">
                <span>Experience #{i + 1}</span>
                <button className="btn-remove-exp" onClick={() => removeExp(i)}>Remove</button>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Company</label>
                  <input value={exp.company} onChange={e => updateExp(i, 'company', e.target.value)} placeholder="Google" />
                </div>
                <div className="form-group">
                  <label>Role</label>
                  <input value={exp.role} onChange={e => updateExp(i, 'role', e.target.value)} placeholder="Software Engineer" />
                </div>
                <div className="form-group">
                  <label>Duration</label>
                  <input value={exp.duration} onChange={e => updateExp(i, 'duration', e.target.value)} placeholder="Jan 2023 – Present" />
                </div>
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={exp.description}
                  onChange={e => updateExp(i, 'description', e.target.value)}
                  placeholder="Key responsibilities and achievements..."
                  rows={3}
                />
              </div>
            </div>
          ))}
          <button className="btn-add-exp" onClick={addExp}>+ Add Experience</button>
        </section>
      </div>

      <div className="profile-save-bar">
        <button className={`btn-save ${saved ? 'saved' : ''}`} onClick={handleSave} disabled={saving}>
          {saving ? '⏳ Saving…' : saved ? '✅ Saved!' : '💾 Save Profile'}
        </button>
      </div>
    </div>
  );
}
