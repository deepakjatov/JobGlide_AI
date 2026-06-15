import { useState, useEffect, useRef, useCallback } from 'react';
import { startAutoApply, stopAutoApply, getAutoApplyStatus } from '../api/applyApi';
import './AutoApplyPanel.css';

export default function AutoApplyPanel({ onClose, filters }) {
  const [agreed, setAgreed] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [maxApps, setMaxApps] = useState(5);
  const [status, setStatus] = useState({ running: false, applied: 0, skipped: 0, errors: 0, events: [] });
  const [starting, setStarting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const logRef = useRef(null);
  const pollRef = useRef(null);

  // Poll for status when running
  const pollStatus = useCallback(async () => {
    const s = await getAutoApplyStatus();
    setStatus(s);
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    if (!s.running) {
      clearInterval(pollRef.current);
    }
  }, []);

  useEffect(() => {
    pollStatus();
    return () => clearInterval(pollRef.current);
  }, [pollStatus]);

  const handleStart = async () => {
    if (!agreed) return;
    setErrorMsg('');
    setStarting(true);
    try {
      const backendFilters = filters ? {
        keywords: filters.keywords || [],
        skills: filters.skills || [],
        experience: filters.experience || '1-2',
        locations: filters.locations || [],
        date_posted: filters.datePosted || filters.date_posted || 'past_3d',
        job_types: filters.jobTypes || filters.job_types || [],
        experience_levels: filters.experienceLevels || filters.experience_levels || [],
        workplace_types: filters.workplaceTypes || filters.workplace_types || []
      } : {
        keywords: ['Software Engineer'],
        skills: [],
        locations: ['Remote'],
        experience: '1-2',
        date_posted: 'past_3d',
        job_types: [],
        experience_levels: [],
        workplace_types: []
      };

      await startAutoApply({
        filters: backendFilters,
        max_applications: maxApps,
        linkedin_email: email,
        linkedin_password: password,
      });
      clearInterval(pollRef.current);
      pollRef.current = setInterval(pollStatus, 2000);
    } catch (e) {
      setErrorMsg(e.message);
    }
    setStarting(false);
  };

  const handleStop = async () => {
    await stopAutoApply();
    clearInterval(pollRef.current);
    pollStatus();
  };

  const EVENT_ICONS = { info: 'ℹ️', success: '✅', warning: '⚠️', error: '❌' };

  return (
    <div className="aap-overlay" onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="aap-panel">
        <div className="aap-header">
          <div className="aap-title-row">
            <span className="aap-icon">🤖</span>
            <h3>LinkedIn Auto Apply</h3>
          </div>
          <button className="aap-close" onClick={onClose}>×</button>
        </div>

        {/* ── Disclaimer ── */}
        <div className="aap-disclaimer">
          <div className="disclaimer-icon">⚠️</div>
          <div>
            <p><strong>Use Responsibly.</strong> This tool automates LinkedIn Easy Apply on your behalf.</p>
            <ul>
              <li>LinkedIn's ToS prohibits automation. Use at your own risk.</li>
              <li>A visible browser window will open — do not close it during the run.</li>
              <li>Max 20 applications per session. Includes human-like random delays.</li>
              <li>Only applies to <strong>Easy Apply</strong> jobs (1-click forms).</li>
              <li>Your credentials are never stored — used only for this session.</li>
            </ul>
            <label className="disclaimer-agree">
              <input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} />
              I understand and agree to use this tool responsibly.
            </label>
          </div>
        </div>

        <div className={`aap-body ${!agreed ? 'locked' : ''}`}>
          {/* ── Credentials ── */}
          <div className="aap-section">
            <h4>LinkedIn Credentials</h4>
            <div className="aap-form-row">
              <div className="aap-form-group">
                <label>Email</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                  placeholder="your@email.com" disabled={status.running} />
              </div>
              <div className="aap-form-group">
                <label>Password</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••" disabled={status.running} />
              </div>
            </div>
            <p className="aap-hint">Leave blank to use credentials from backend/.env</p>
          </div>

          {/* ── Settings ── */}
          <div className="aap-section">
            <h4>Settings</h4>
            <div className="aap-slider-row">
              <label>Max Applications: <strong>{maxApps}</strong></label>
              <input type="range" min={1} max={20} value={maxApps}
                onChange={e => setMaxApps(+e.target.value)} disabled={status.running} />
              <div className="slider-ticks">
                <span>1</span><span>10</span><span>20</span>
              </div>
            </div>
          </div>

          {/* ── Stats ── */}
          {(status.applied > 0 || status.skipped > 0 || status.errors > 0) && (
            <div className="aap-stats">
              <div className="stat-chip success">✅ {status.applied} Applied</div>
              <div className="stat-chip warning">⏭ {status.skipped} Skipped</div>
              <div className="stat-chip error">❌ {status.errors} Errors</div>
            </div>
          )}

          {/* ── Live Log ── */}
          {status.events.length > 0 && (
            <div className="aap-log" ref={logRef}>
              {status.events.map((ev, i) => (
                <div key={i} className={`log-entry log-${ev.type}`}>
                  <span className="log-icon">{EVENT_ICONS[ev.type] || 'ℹ️'}</span>
                  <span className="log-msg">{ev.msg}</span>
                  <span className="log-time">{new Date(ev.time).toLocaleTimeString()}</span>
                </div>
              ))}
            </div>
          )}

          {errorMsg && <div className="aap-error">❌ {errorMsg}</div>}

          {/* ── Controls ── */}
          <div className="aap-controls">
            {status.running ? (
              <button className="btn-stop" onClick={handleStop}>⏹ Stop Auto Apply</button>
            ) : (
              <button
                className="btn-start"
                onClick={handleStart}
                disabled={!agreed || starting}
              >
                {starting ? '⏳ Starting…' : '🚀 Start Auto Apply'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
