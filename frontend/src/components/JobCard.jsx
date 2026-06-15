import { useState, useEffect } from 'react';
import { quickApply, getAppliedJobIds } from '../api/applyApi';
import CoverLetterModal from './CoverLetterModal';
import './JobCard.css';

const SOURCE_COLORS = {
  jsearch:   { bg: 'rgba(59, 130, 246, 0.15)',  color: '#60a5fa', border: 'rgba(59, 130, 246, 0.3)',   label: 'JSearch' },
  himalayas: { bg: 'rgba(16, 185, 129, 0.15)',  color: '#34d399', border: 'rgba(16, 185, 129, 0.3)',   label: 'Himalayas' },
  adzuna:    { bg: 'rgba(245, 158, 11, 0.15)',   color: '#fbbf24', border: 'rgba(245, 158, 11, 0.3)',   label: 'Adzuna' },
  remotive:  { bg: 'rgba(124, 58, 237, 0.15)',   color: '#a78bfa', border: 'rgba(124, 58, 237, 0.3)',   label: 'Remotive' },
  linkedin:  { bg: 'rgba(10, 102, 194, 0.15)',   color: '#0a66c2', border: 'rgba(10, 102, 194, 0.3)',   label: 'LinkedIn' },
  indeed:    { bg: 'rgba(37, 87, 167, 0.15)',    color: '#2557a7', border: 'rgba(37, 87, 167, 0.3)',    label: 'Indeed' },
  google:    { bg: 'rgba(219, 68, 85, 0.15)',    color: '#db4437', border: 'rgba(219, 68, 85, 0.3)',    label: 'Google Jobs' },
};

function getRelativeTime(dateStr) {
  if (!dateStr) return '';
  const now = new Date();
  const date = new Date(dateStr);
  const diffDay = Math.floor((now - date) / 86400000);
  const diffWeek = Math.floor(diffDay / 7);
  const diffMonth = Math.floor(diffDay / 30);
  if (diffDay < 1) return 'Today';
  if (diffDay === 1) return 'Yesterday';
  if (diffDay < 7) return `${diffDay} days ago`;
  if (diffWeek === 1) return '1 week ago';
  if (diffWeek < 5) return `${diffWeek} weeks ago`;
  if (diffMonth === 1) return '1 month ago';
  return `${diffMonth} months ago`;
}

function getInitialColor(letter) {
  const colors = [
    'linear-gradient(135deg, #00d4ff, #7c3aed)',
    'linear-gradient(135deg, #ec4899, #f59e0b)',
    'linear-gradient(135deg, #10b981, #00d4ff)',
    'linear-gradient(135deg, #7c3aed, #ec4899)',
    'linear-gradient(135deg, #f59e0b, #10b981)',
  ];
  const idx = (letter || 'A').charCodeAt(0) % colors.length;
  return colors[idx];
}


export default function JobCard({ job, index, filterSkills = [], profile, isInitiallyApplied, onApplied }) {
  const source = (job.source || '').toLowerCase();
  const sourceStyle = SOURCE_COLORS[source] || {
    bg: 'rgba(156, 163, 175, 0.15)', color: '#9ca3af',
    border: 'rgba(156, 163, 175, 0.3)', label: source.toUpperCase()
  };

  const matchedSet = new Set((job.skills_matched || []).map(s => s.toLowerCase()));
  const allSkills = [...new Set([...(job.skills_matched || []), ...filterSkills])];

  const [applied, setApplied] = useState(isInitiallyApplied);
  const [applyLoading, setApplyLoading] = useState(false);
  const [showCoverLetter, setShowCoverLetter] = useState(false);

  useEffect(() => {
    setApplied(isInitiallyApplied);
  }, [isInitiallyApplied]);

  const handleQuickApply = async () => {
    setApplyLoading(true);
    window.open(job.apply_url || job.url || '#', '_blank', 'noopener,noreferrer');
    await quickApply(job);
    setApplied(true);
    if (onApplied) onApplied();
    setApplyLoading(false);
  };

  const handleTrack = async () => {
    await quickApply({ ...job, apply_url: job.apply_url || '' });
    setApplied(true);
    if (onApplied) onApplied();
  };

  return (
    <>
      <div
        className={`job-card glass-card ${applied ? 'applied' : ''}`}
        style={{ animationDelay: `${(index % 12) * 0.07}s` }}
      >
        {applied && <div className="applied-badge">✅ Applied</div>}

        <span className="job-source-badge" style={{
          background: sourceStyle.bg, color: sourceStyle.color, borderColor: sourceStyle.border
        }}>
          {sourceStyle.label}
        </span>

        <div className="job-card-top">
          <div className="job-company-logo">
            {job.company_logo ? (
              <img src={job.company_logo} alt={job.company} className="job-logo-img" />
            ) : (
              <div className="job-logo-initial" style={{ background: getInitialColor((job.company || 'J')[0]) }}>
                {(job.company || 'J')[0].toUpperCase()}
              </div>
            )}
          </div>
          <div className="job-card-info">
            <h3 className="job-title">{job.title || 'Untitled Position'}</h3>
            <p className="job-company">{job.company || 'Unknown Company'}</p>
          </div>
        </div>

        <div className="job-badges">
          {job.location && <span className="badge badge-location">📍 {job.location}</span>}
          {job.job_type && <span className="badge badge-type">💼 {job.job_type}</span>}
          {job.posted_date && <span className="badge badge-date">🕐 {getRelativeTime(job.posted_date)}</span>}
        </div>

        {allSkills.length > 0 && (
          <div className="job-skills">
            {allSkills.slice(0, 8).map((skill) => (
              <span key={skill} className={`job-skill-chip ${matchedSet.has(skill.toLowerCase()) ? 'matched' : 'unmatched'}`}>
                {skill}
              </span>
            ))}
            {allSkills.length > 8 && <span className="job-skill-chip unmatched">+{allSkills.length - 8}</span>}
          </div>
        )}

        <div className="job-card-footer">
          {job.salary && <span className="job-salary">{job.salary}</span>}
          <div className="job-action-buttons">
            <button className="btn-icon-action" onClick={handleTrack} disabled={applied} title="Track (no apply)">
              🔖
            </button>
            <button className="btn-icon-action" onClick={() => setShowCoverLetter(true)} title="Generate AI Cover Letter">
              ✨
            </button>
            <button
              className={`btn-apply ${applied ? 'applied' : ''}`}
              onClick={handleQuickApply}
              disabled={applyLoading}
            >
              {applyLoading ? '⏳' : applied ? '✅ Applied' : <>Quick Apply <span className="apply-arrow">→</span></>}
            </button>
          </div>
        </div>
      </div>

      {showCoverLetter && (
        <CoverLetterModal job={job} profile={profile} onClose={() => setShowCoverLetter(false)} />
      )}
    </>
  );
}
