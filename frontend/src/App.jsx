import { useState } from 'react';
import { useJobs } from './hooks/useJobs';
import Header from './components/Header';
import FilterPanel from './components/FilterPanel';
import SearchStats from './components/SearchStats';
import JobList from './components/JobList';
import './App.css';

function App() {
  const {
    keywords,
    skills,
    experience,
    locations,
    jobs,
    loading,
    error,
    searchStats,
    searchJobs,
    addFilter,
    removeFilter,
    clearFilters,
    resetToResume,
    setExperience
  } = useJobs();

  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app">
      {/* Mobile hamburger */}
      <button
        className={`mobile-menu-btn ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle filters"
      >
        <span></span>
        <span></span>
        <span></span>
      </button>

      {/* Sidebar overlay for mobile */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`app-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <FilterPanel
          keywords={keywords}
          skills={skills}
          experience={experience}
          locations={locations}
          onAddFilter={addFilter}
          onRemoveFilter={removeFilter}
          onSetExperience={setExperience}
          onSearch={() => {
            searchJobs();
            setSidebarOpen(false);
          }}
          onClear={clearFilters}
          onReset={resetToResume}
          loading={loading}
        />
      </aside>

      {/* Main content */}
      <main className="app-main">
        <Header totalJobs={searchStats.total} />
        <SearchStats stats={searchStats} />
        <JobList
          jobs={jobs}
          loading={loading}
          error={error}
          onRetry={searchJobs}
          skills={skills}
        />
      </main>
    </div>
  );
}

export default App;
