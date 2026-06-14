import { useState, useMemo } from 'react';
import JobCard from './JobCard';
import './JobList.css';

const SOURCE_TABS = [
  { key: 'all', label: 'All' },
  { key: 'linkedin', label: 'LinkedIn' },
  { key: 'indeed', label: 'Indeed' },
  { key: 'google', label: 'Google Jobs' },
  { key: 'jsearch', label: 'JSearch' },
  { key: 'himalayas', label: 'Himalayas' },
  { key: 'adzuna', label: 'Adzuna' },
  { key: 'remotive', label: 'Remotive' },
];

function SkeletonCard({ index }) {
  return (
    <div className="skeleton-card glass" style={{ animationDelay: `${index * 0.1}s` }}>
      <div className="skeleton-header">
        <div className="skeleton skeleton-avatar"></div>
        <div className="skeleton-text-group">
          <div className="skeleton skeleton-title"></div>
          <div className="skeleton skeleton-subtitle"></div>
        </div>
      </div>
      <div className="skeleton-badges">
        <div className="skeleton skeleton-badge"></div>
        <div className="skeleton skeleton-badge"></div>
      </div>
      <div className="skeleton-skills">
        <div className="skeleton skeleton-skill"></div>
        <div className="skeleton skeleton-skill"></div>
        <div className="skeleton skeleton-skill"></div>
      </div>
      <div className="skeleton-footer">
        <div className="skeleton skeleton-btn"></div>
      </div>
    </div>
  );
}

export default function JobList({ jobs, loading, error, onRetry, skills }) {
  const [activeSource, setActiveSource] = useState('all');

  const sourceCounts = useMemo(() => {
    const counts = { all: jobs.length };
    jobs.forEach(job => {
      const src = (job.source || '').toLowerCase();
      counts[src] = (counts[src] || 0) + 1;
    });
    return counts;
  }, [jobs]);

  const filteredJobs = useMemo(() => {
    if (activeSource === 'all') return jobs;
    return jobs.filter(job => (job.source || '').toLowerCase() === activeSource);
  }, [jobs, activeSource]);

  // Loading state
  if (loading) {
    return (
      <div className="job-list-container">
        <div className="source-tabs">
          {SOURCE_TABS.map(tab => (
            <button key={tab.key} className="source-tab" disabled>
              {tab.label}
            </button>
          ))}
        </div>
        <div className="job-grid">
          {[...Array(6)].map((_, i) => (
            <SkeletonCard key={i} index={i} />
          ))}
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="job-list-container">
        <div className="job-list-state glass">
          <span className="state-icon">⚠️</span>
          <h3 className="state-title">Something went wrong</h3>
          <p className="state-text">{error}</p>
          <button className="btn-primary" onClick={onRetry}>
            🔄 Retry Search
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (jobs.length === 0) {
    return (
      <div className="job-list-container">
        <div className="job-list-state glass">
          <span className="state-icon">🔍</span>
          <h3 className="state-title">No jobs found</h3>
          <p className="state-text">Try adjusting your filters or adding different keywords.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="job-list-container">
      <div className="source-tabs">
        {SOURCE_TABS.map(tab => (
          <button
            key={tab.key}
            className={`source-tab ${activeSource === tab.key ? 'active' : ''}`}
            onClick={() => setActiveSource(tab.key)}
          >
            {tab.label}
            {(sourceCounts[tab.key] || 0) > 0 && (
              <span className="source-tab-count">{sourceCounts[tab.key]}</span>
            )}
          </button>
        ))}
      </div>

      <div className="job-grid">
        {filteredJobs.map((job, index) => (
          <JobCard
            key={job.id || job.apply_url || index}
            job={job}
            index={index}
            filterSkills={skills}
          />
        ))}
      </div>

      {filteredJobs.length === 0 && (
        <div className="job-list-state glass" style={{ marginTop: '20px' }}>
          <span className="state-icon">📭</span>
          <h3 className="state-title">No jobs from this source</h3>
          <p className="state-text">Try selecting a different source tab.</p>
        </div>
      )}
    </div>
  );
}
