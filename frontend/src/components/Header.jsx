import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import logo from '../assets/logo.png';
import AutoApplyPanel from './AutoApplyPanel';
import './Header.css';

export default function Header({ totalJobs, filters }) {
  const [showAutoApply, setShowAutoApply] = useState(false);

  return (
    <>
      <header className="header">
        <div className="header-left">
          <div className="header-icon">
            <img src={logo} alt="JobGlide AI Logo" className="header-logo-img" />
          </div>
          <div className="header-text">
            <h1 className="header-title">
              <span className="gradient-text">JobGlide AI</span>
            </h1>
            <p className="header-subtitle">Resume-Powered Job Search</p>
          </div>
        </div>

        <nav className="header-nav">
          <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} end>
            🔍 Jobs
          </NavLink>
          <NavLink to="/applications" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            📊 Applications
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            👤 Profile
          </NavLink>
        </nav>

        <div className="header-right">
          {totalJobs > 0 && (
            <div className="header-badge">
              <span className="header-badge-count">{totalJobs}</span>
              <span className="header-badge-label">jobs found</span>
            </div>
          )}
          <button className="btn-auto-apply" onClick={() => setShowAutoApply(true)}>
            🤖 Auto Apply
          </button>
        </div>
      </header>

      {showAutoApply && (
        <AutoApplyPanel onClose={() => setShowAutoApply(false)} filters={filters} />
      )}
    </>
  );
}
