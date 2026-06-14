import { useState, useEffect, useCallback } from 'react';
import { fetchDefaultFilters, searchJobs as searchJobsApi } from '../api/jobsApi';

export function useJobs() {
  const [keywords, setKeywords] = useState([]);
  const [skills, setSkills] = useState([]);
  const [experience, setExperience] = useState('');
  const [locations, setLocations] = useState([]);

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchStats, setSearchStats] = useState({
    total: 0,
    sources_searched: 0,
    cached: false
  });

  const [filtersLoaded, setFiltersLoaded] = useState(false);

  const searchJobs = useCallback(async (overrideFilters) => {
    setLoading(true);
    setError(null);
    try {
      const filters = overrideFilters || { keywords, skills, experience, locations };
      const data = await searchJobsApi(filters);
      setJobs(data.jobs || []);
      setSearchStats({
        total: data.total || (data.jobs ? data.jobs.length : 0),
        sources_searched: data.sources_searched || 0,
        cached: data.cached || false
      });
    } catch (err) {
      setError(err.message);
      setJobs([]);
    } finally {
      setLoading(false);
    }
  }, [keywords, skills, experience, locations]);

  const loadDefaults = useCallback(async () => {
    try {
      const defaults = await fetchDefaultFilters();
      const kw = defaults.keywords || [];
      const sk = defaults.skills || [];
      const exp = defaults.experience || '';
      const loc = defaults.locations || [];
      setKeywords(kw);
      setSkills(sk);
      setExperience(exp);
      setLocations(loc);
      setFiltersLoaded(true);
      return { keywords: kw, skills: sk, experience: exp, locations: loc };
    } catch (err) {
      setError(err.message);
      setFiltersLoaded(true);
      return null;
    }
  }, []);

  // Load defaults and auto-search on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const filters = await loadDefaults();
      if (!cancelled && filters) {
        await searchJobsApi(filters)
          .then(data => {
            if (!cancelled) {
              setJobs(data.jobs || []);
              setSearchStats({
                total: data.total || (data.jobs ? data.jobs.length : 0),
                sources_searched: data.sources_searched || 0,
                cached: data.cached || false
              });
            }
          })
          .catch(err => {
            if (!cancelled) setError(err.message);
          });
      }
    })();
    return () => { cancelled = true; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const addFilter = useCallback((type, value) => {
    const trimmed = value.trim();
    if (!trimmed) return;
    switch (type) {
      case 'keywords':
        setKeywords(prev => prev.includes(trimmed) ? prev : [...prev, trimmed]);
        break;
      case 'skills':
        setSkills(prev => prev.includes(trimmed) ? prev : [...prev, trimmed]);
        break;
      case 'locations':
        setLocations(prev => prev.includes(trimmed) ? prev : [...prev, trimmed]);
        break;
      default:
        break;
    }
  }, []);

  const removeFilter = useCallback((type, value) => {
    switch (type) {
      case 'keywords':
        setKeywords(prev => prev.filter(v => v !== value));
        break;
      case 'skills':
        setSkills(prev => prev.filter(v => v !== value));
        break;
      case 'locations':
        setLocations(prev => prev.filter(v => v !== value));
        break;
      default:
        break;
    }
  }, []);

  const clearFilters = useCallback(() => {
    setKeywords([]);
    setSkills([]);
    setExperience('');
    setLocations([]);
  }, []);

  const resetToResume = useCallback(async () => {
    const filters = await loadDefaults();
    if (filters) {
      searchJobsApi(filters)
        .then(data => {
          setJobs(data.jobs || []);
          setSearchStats({
            total: data.total || (data.jobs ? data.jobs.length : 0),
            sources_searched: data.sources_searched || 0,
            cached: data.cached || false
          });
        })
        .catch(err => setError(err.message));
    }
  }, [loadDefaults]);

  return {
    // Filter state
    keywords,
    skills,
    experience,
    locations,
    filtersLoaded,
    // Job state
    jobs,
    loading,
    error,
    searchStats,
    // Actions
    searchJobs,
    addFilter,
    removeFilter,
    clearFilters,
    resetToResume,
    setExperience
  };
}
