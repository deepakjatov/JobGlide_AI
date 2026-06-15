import './SearchStats.css';

export default function SearchStats({ stats, onRefresh, loading }) {
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
          {stats.cached ? '⚡ Saved DB' : '🔄 Fresh Scrape'}
        </span>
        <span className="stat-label">results source</span>
      </div>
      {stats.cached && onRefresh && (
        <>
          <div className="stat-divider"></div>
          <button 
            className="btn-refresh-scrape" 
            onClick={() => onRefresh(null, true)} 
            disabled={loading}
          >
            {loading ? 'Scraping...' : '🔄 Scrape Latest Online'}
          </button>
        </>
      )}
    </div>
  );
}
