import logo from '../assets/logo.png';
import './Header.css';

export default function Header({ totalJobs }) {
  return (
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
      <div className="header-right">
        {totalJobs > 0 && (
          <div className="header-badge">
            <span className="header-badge-count">{totalJobs}</span>
            <span className="header-badge-label">jobs found</span>
          </div>
        )}
      </div>
    </header>
  );
}
