import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useJobs } from './hooks/useJobs';
import Header from './components/Header';
import FilterPanel from './components/FilterPanel';
import SearchStats from './components/SearchStats';
import JobList from './components/JobList';
import ProfilePage from './pages/ProfilePage';
import ApplicationsPage from './pages/ApplicationsPage';
import './App.css';

function JobsPage({ }) {
  const {
    keywords, skills, experience, locations,
    datePosted, jobTypes, experienceLevels, workplaceTypes,
    jobs, loading, error, searchStats,
    searchJobs, addFilter, removeFilter, clearFilters, resetToResume,
    setExperience, setDatePosted, setJobTypes, setExperienceLevels, setWorkplaceTypes,
  } = useJobs();

  const [sidebarOpen, setSidebarOpen] = useState(false);

  const filters = { keywords, skills, experience, locations, datePosted, jobTypes, experienceLevels, workplaceTypes };

  return (
    <div className="app">
      <button
        className={`mobile-menu-btn ${sidebarOpen ? 'open' : ''}`}
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle filters"
      >
        <span></span><span></span><span></span>
      </button>

      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}

      <aside className={`app-sidebar ${sidebarOpen ? 'open' : ''}`}>
        <FilterPanel
          keywords={keywords} skills={skills} experience={experience}
          locations={locations} datePosted={datePosted} jobTypes={jobTypes}
          experienceLevels={experienceLevels} workplaceTypes={workplaceTypes}
          onAddFilter={addFilter} onRemoveFilter={removeFilter}
          onSetExperience={setExperience} onSetDatePosted={setDatePosted}
          onSetJobTypes={setJobTypes} onSetExperienceLevels={setExperienceLevels}
          onSetWorkplaceTypes={setWorkplaceTypes}
          onSearch={() => { searchJobs(); setSidebarOpen(false); }}
          onClear={clearFilters} onReset={resetToResume} loading={loading}
        />
      </aside>

      <main className="app-main">
        <Header totalJobs={searchStats.total} filters={filters} />
        <SearchStats stats={searchStats} onRefresh={searchJobs} loading={loading} />
        <JobList jobs={jobs} loading={loading} error={error} onRetry={searchJobs} skills={skills} />
      </main>
    </div>
  );
}

function AppShell() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<JobsPage />} />
        <Route path="/profile" element={<ProfilePageWrapper />} />
        <Route path="/applications" element={<ApplicationsPageWrapper />} />
      </Routes>
    </BrowserRouter>
  );
}

// Wrappers that include the header for non-jobs pages
function ProfilePageWrapper() {
  return (
    <div style={{ minHeight: '100vh' }}>
      <div style={{ padding: '0 1.5rem' }}>
        <Header totalJobs={0} />
      </div>
      <ProfilePage />
    </div>
  );
}

function ApplicationsPageWrapper() {
  return (
    <div style={{ minHeight: '100vh' }}>
      <div style={{ padding: '0 1.5rem' }}>
        <Header totalJobs={0} />
      </div>
      <ApplicationsPage />
    </div>
  );
}

export default AppShell;
