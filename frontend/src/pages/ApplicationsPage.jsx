import { useState, useEffect, useCallback } from 'react';
import { getApplications, updateApplication, deleteApplication, addApplication } from '../api/applyApi';
import './ApplicationsPage.css';

const COLUMNS = [
  { id: 'applied',   label: 'Applied',    icon: '📤', color: '#60a5fa' },
  { id: 'interview', label: 'Interview',  icon: '💬', color: '#34d399' },
  { id: 'offer',     label: 'Offer',      icon: '🎉', color: '#fbbf24' },
  { id: 'rejected',  label: 'Rejected',   icon: '❌', color: '#f87171' },
];

const SOURCE_COLORS = {
  linkedin: '#0a66c2', indeed: '#2557a7', google: '#db4437',
  jsearch: '#3b82f6', himalayas: '#10b981', adzuna: '#f59e0b',
  remotive: '#7c3aed',
};

function formatDate(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  } catch { return iso; }
}

function AppCard({ app, onStatusChange, onDelete, onNotesChange }) {
  const [editing, setEditing] = useState(false);
  const [notes, setNotes] = useState(app.notes || '');

  const saveNotes = async () => {
    await onNotesChange(app.id, notes);
    setEditing(false);
  };

  const srcColor = SOURCE_COLORS[app.source] || '#9ca3af';

  return (
    <div className="app-card">
      <div className="app-card-header">
        <div className="app-src-dot" style={{ background: srcColor }} title={app.source} />
        <button className="app-delete-btn" onClick={() => onDelete(app.id)} title="Remove">×</button>
      </div>
      <h4 className="app-job-title">{app.job_title}</h4>
      <p className="app-company">{app.company}</p>
      <div className="app-meta">
        <span className="app-date">🗓 {formatDate(app.applied_at)}</span>
        {app.apply_url && (
          <a href={app.apply_url} target="_blank" rel="noopener noreferrer" className="app-link">↗ View</a>
        )}
      </div>
      {editing ? (
        <div className="app-notes-edit">
          <textarea value={notes} onChange={e => setNotes(e.target.value)} rows={3} placeholder="Add notes..." />
          <div className="notes-actions">
            <button onClick={saveNotes} className="btn-notes-save">Save</button>
            <button onClick={() => setEditing(false)} className="btn-notes-cancel">Cancel</button>
          </div>
        </div>
      ) : (
        <div className="app-notes" onClick={() => setEditing(true)}>
          {notes || <span className="notes-placeholder">+ Add notes</span>}
        </div>
      )}
      <div className="app-status-row">
        {COLUMNS.filter(c => c.id !== app.status).map(c => (
          <button
            key={c.id}
            className="btn-move-status"
            style={{ '--clr': c.color }}
            onClick={() => onStatusChange(app.id, c.id)}
          >
            {c.icon} {c.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function AddModal({ onClose, onAdd }) {
  const [form, setForm] = useState({ job_title: '', company: '', apply_url: '', source: '', notes: '' });
  const set = (f, v) => setForm(p => ({ ...p, [f]: v }));

  const handleSubmit = async () => {
    if (!form.job_title || !form.company) return;
    await onAdd({
      ...form,
      id: crypto.randomUUID(),
      job_id: '',
      status: 'applied',
      applied_at: new Date().toISOString(),
      cover_letter: '',
    });
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="add-modal">
        <h3>Log a New Application</h3>
        <div className="form-group">
          <label>Job Title *</label>
          <input value={form.job_title} onChange={e => set('job_title', e.target.value)} placeholder="Software Engineer" />
        </div>
        <div className="form-group">
          <label>Company *</label>
          <input value={form.company} onChange={e => set('company', e.target.value)} placeholder="Acme Corp" />
        </div>
        <div className="form-group">
          <label>Apply URL</label>
          <input value={form.apply_url} onChange={e => set('apply_url', e.target.value)} placeholder="https://..." />
        </div>
        <div className="form-group">
          <label>Source</label>
          <input value={form.source} onChange={e => set('source', e.target.value)} placeholder="linkedin, indeed, etc." />
        </div>
        <div className="form-group">
          <label>Notes</label>
          <textarea value={form.notes} onChange={e => set('notes', e.target.value)} rows={3} placeholder="Any notes..." />
        </div>
        <div className="modal-actions">
          <button className="btn-cancel" onClick={onClose}>Cancel</button>
          <button className="btn-confirm" onClick={handleSubmit} disabled={!form.job_title || !form.company}>
            Add Application
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ApplicationsPage() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const data = await getApplications();
    setApps(data);
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleStatusChange = async (id, newStatus) => {
    await updateApplication(id, { status: newStatus });
    setApps(prev => prev.map(a => a.id === id ? { ...a, status: newStatus } : a));
  };

  const handleDelete = async (id) => {
    await deleteApplication(id);
    setApps(prev => prev.filter(a => a.id !== id));
  };

  const handleNotesChange = async (id, notes) => {
    await updateApplication(id, { notes });
    setApps(prev => prev.map(a => a.id === id ? { ...a, notes } : a));
  };

  const handleAdd = async (app) => {
    await addApplication(app);
    setApps(prev => [app, ...prev]);
  };

  const colApps = (colId) => apps.filter(a => a.status === colId);

  return (
    <div className="applications-page">
      <div className="apps-hero">
        <h1>Application Tracker</h1>
        <p>Track every job you've applied to — drag cards between columns to update status.</p>
        <button className="btn-add-app" onClick={() => setShowAddModal(true)}>+ Log Application</button>
      </div>

      <div className="apps-summary">
        {COLUMNS.map(col => (
          <div key={col.id} className="summary-pill" style={{ '--clr': col.color }}>
            <span className="pill-count">{colApps(col.id).length}</span>
            <span className="pill-label">{col.icon} {col.label}</span>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="apps-loading">Loading applications…</div>
      ) : (
        <div className="kanban-board">
          {COLUMNS.map(col => (
            <div key={col.id} className="kanban-col">
              <div className="kanban-col-header" style={{ '--clr': col.color }}>
                <span className="col-icon">{col.icon}</span>
                <span className="col-label">{col.label}</span>
                <span className="col-count">{colApps(col.id).length}</span>
              </div>
              <div className="kanban-col-body">
                {colApps(col.id).length === 0 ? (
                  <div className="kanban-empty">No applications here</div>
                ) : (
                  colApps(col.id).map(app => (
                    <AppCard
                      key={app.id}
                      app={app}
                      onStatusChange={handleStatusChange}
                      onDelete={handleDelete}
                      onNotesChange={handleNotesChange}
                    />
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {showAddModal && (
        <AddModal onClose={() => setShowAddModal(false)} onAdd={handleAdd} />
      )}
    </div>
  );
}
