import { useState, useEffect, useCallback } from 'react';
import { fetchDefaultFilters, searchJobs as searchJobsApi } from '../api/jobsApi';

export function useJobs() {
  const [keywords, setKeywords] = useState([]);
  const [skills, setSkills] = useState([]);
  const [experience, setExperience] = useState('');
  const [locations, setLocations] = useState([]);
  const [datePosted, setDatePosted] = useState('past_3d');
  const [jobTypes, setJobTypes] = useState([]);
  const [experienceLevels, setExperienceLevels] = useState([]);
  const [workplaceTypes, setWorkplaceTypes] = useState(['Remote']);

  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchStats, setSearchStats] = useState({
    total: 0,
    sources_searched: 0,
    cached: false
  });

  const [filtersLoaded, setFiltersLoaded] = useState(false);

  const searchJobs = useCallback(async (overrideFilters, forceRefresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const filters = overrideFilters || {
        keywords,
        skills,
        experience,
        locations,
        date_posted: datePosted,
        job_types: jobTypes,
        experience_levels: experienceLevels,
        workplace_types: workplaceTypes,
        force_refresh: forceRefresh
      };
      if (forceRefresh) {
        filters.force_refresh = true;
      }
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
  }, [keywords, skills, experience, locations, datePosted, jobTypes, experienceLevels, workplaceTypes]);

  const loadDefaults = useCallback(async () => {
    try {
      const defaults = await fetchDefaultFilters();
      const kw = defaults.keywords || [];
      const sk = defaults.skills || [];
      const exp = defaults.experience || '';
      const loc = defaults.locations || [];
      const dp = defaults.date_posted || 'past_3d';
      const jt = defaults.job_types || [];
      const el = defaults.experience_levels || [];
      const wt = defaults.workplace_types || ['Remote'];

      setKeywords(kw);
      setSkills(sk);
      setExperience(exp);
      setLocations(loc);
      setDatePosted(dp);
      setJobTypes(jt);
      setExperienceLevels(el);
      setWorkplaceTypes(wt);

      setFiltersLoaded(true);
      return {
        keywords: kw,
        skills: sk,
        experience: exp,
        locations: loc,
        date_posted: dp,
        job_types: jt,
        experience_levels: el,
        workplace_types: wt
      };
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
    setDatePosted('anytime');
    setJobTypes([]);
    setExperienceLevels([]);
    setWorkplaceTypes([]);
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
    datePosted,
    jobTypes,
    experienceLevels,
    workplaceTypes,
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
    setExperience,
    setDatePosted,
    setJobTypes,
    setExperienceLevels,
    setWorkplaceTypes
  };
}
