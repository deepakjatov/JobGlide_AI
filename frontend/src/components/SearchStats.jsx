import './SearchStats.css';

export default function SearchStats({ stats }) {
  return (
    <div className="search-stats glass">
      <div className="stat-item">
        <span className="stat-value">{stats.total}</span>
        <span className="stat-label">jobs found</span>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <span className="stat-value">{stats.sources_searched}</span>
        <span className="stat-label">sources searched</span>
      </div>
      <div className="stat-divider"></div>
      <div className="stat-item">
        <span className={`stat-badge ${stats.cached ? 'cached' : 'fresh'}`}>
          {stats.cached ? '⚡ Cached' : '🔄 Fresh'}
        </span>
        <span className="stat-label">results</span>
      </div>
    </div>
  );
}
