import { useState } from 'react';
import './FilterPanel.css';

function ChipInput({ label, emoji, items, onAdd, onRemove, placeholder }) {
  const [value, setValue] = useState('');

  const handleAdd = () => {
    if (value.trim()) {
      onAdd(value.trim());
      setValue('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="filter-section">
      <label className="filter-label">
        <span className="filter-label-emoji">{emoji}</span>
        {label}
      </label>
      <div className="chip-container">
        {items.map((item, idx) => (
          <span key={item + idx} className="chip fade-in">
            <span className="chip-text">{item}</span>
            <button
              className="chip-remove"
              onClick={() => onRemove(item)}
              aria-label={`Remove ${item}`}
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <div className="filter-input-row">
        <input
          type="text"
          className="filter-input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
        />
        <button className="filter-add-btn" onClick={handleAdd} aria-label="Add">
          +
        </button>
      </div>
    </div>
  );
}

export default function FilterPanel({
  keywords,
  skills,
  experience,
  locations,
  datePosted,
  jobTypes,
  experienceLevels,
  workplaceTypes,
  onAddFilter,
  onRemoveFilter,
  onSetExperience,
  onSetDatePosted,
  onSetJobTypes,
  onSetExperienceLevels,
  onSetWorkplaceTypes,
  onSearch,
  onClear,
  onReset,
  loading
}) {
  return (
    <aside className="filter-panel glass">
      <div className="filter-panel-header">
        <h2 className="filter-panel-title">
          <span className="filter-icon">⚡</span>
          Filters
        </h2>
      </div>

      <div className="filter-panel-body">
        <ChipInput
          label="Keywords"
          emoji="🔑"
          items={keywords}
          onAdd={(v) => onAddFilter('keywords', v)}
          onRemove={(v) => onRemoveFilter('keywords', v)}
          placeholder="e.g. React Developer"
        />

        <ChipInput
          label="Skills"
          emoji="💡"
          items={skills}
          onAdd={(v) => onAddFilter('skills', v)}
          onRemove={(v) => onRemoveFilter('skills', v)}
          placeholder="e.g. TypeScript"
        />

        <div className="filter-section">
          <label className="filter-label">
            <span className="filter-label-emoji">📊</span>
            Experience
          </label>
          <select
            className="filter-select"
            value={experience}
            onChange={(e) => onSetExperience(e.target.value)}
          >
            <option value="">Any Experience</option>
            <option value="0-1">0-1 Years</option>
            <option value="1-2">1-2 Years</option>
            <option value="0-3">0-3 Years</option>
            <option value="3-5">3-5 Years</option>
            <option value="5+">5+ Years</option>
          </select>
        </div>

        <div className="filter-section">
          <label className="filter-label">
            <span className="filter-label-emoji">🕐</span>
            Job Freshness
          </label>
          <select
            className="filter-select"
            value={datePosted}
            onChange={(e) => onSetDatePosted(e.target.value)}
          >
            <option value="anytime">Anytime</option>
            <option value="past_24h">Past 24 hours</option>
            <option value="past_3d">Past 3 days (Default)</option>
            <option value="past_week">Past week</option>
            <option value="past_month">Past month</option>
          </select>
        </div>

        <div className="filter-section">
          <label className="filter-label">
            <span className="filter-label-emoji">🏢</span>
            Workplace Type
          </label>
          <div className="checkbox-group">
            {['On-site', 'Hybrid', 'Remote'].map(type => (
              <label key={type} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={workplaceTypes.includes(type)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      onSetWorkplaceTypes([...workplaceTypes, type]);
                    } else {
                      onSetWorkplaceTypes(workplaceTypes.filter(t => t !== type));
                    }
                  }}
                />
                <span>{type}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="filter-section">
          <label className="filter-label">
            <span className="filter-label-emoji">💼</span>
            Job Type
          </label>
          <div className="checkbox-group">
            {['Full-time', 'Part-time', 'Contract', 'Internship'].map(type => (
              <label key={type} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={jobTypes.includes(type)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      onSetJobTypes([...jobTypes, type]);
                    } else {
                      onSetJobTypes(jobTypes.filter(t => t !== type));
                    }
                  }}
                />
                <span>{type}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="filter-section">
          <label className="filter-label">
            <span className="filter-label-emoji">🎓</span>
            Experience Level
          </label>
          <div className="checkbox-group">
            {['Internship', 'Entry level', 'Associate', 'Mid-Senior level', 'Director', 'Executive'].map(level => (
              <label key={level} className="checkbox-label">
                <input
                  type="checkbox"
                  checked={experienceLevels.includes(level)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      onSetExperienceLevels([...experienceLevels, level]);
                    } else {
                      onSetExperienceLevels(experienceLevels.filter(l => l !== level));
                    }
                  }}
                />
                <span>{level}</span>
              </label>
            ))}
          </div>
        </div>

        <ChipInput
          label="Location"
          emoji="📍"
          items={locations}
          onAdd={(v) => onAddFilter('locations', v)}
          onRemove={(v) => onRemoveFilter('locations', v)}
          placeholder="e.g. Remote, New York"
        />
      </div>

      <div className="filter-panel-actions">
        <button
          className="btn-primary filter-btn"
          onClick={onSearch}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="btn-spinner"></span>
              Searching…
            </>
          ) : (
            <>
              <span>🔍</span>
              Apply Filters
            </>
          )}
        </button>
        <div className="filter-btn-row">
          <button className="btn-ghost filter-btn-half" onClick={onClear}>
            ✕ Clear All
          </button>
          <button className="btn-secondary filter-btn-half" onClick={onReset}>
            📄 Reset To Resume
          </button>
        </div>
      </div>
    </aside>
  );
}
