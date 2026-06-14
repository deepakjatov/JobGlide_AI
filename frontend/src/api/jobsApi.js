const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export async function fetchDefaultFilters() {
  const res = await fetch(`${API_BASE}/filters/default`);
  if (!res.ok) throw new Error('Failed to fetch default filters');
  return res.json();
}

export async function searchJobs(filters) {
  const res = await fetch(`${API_BASE}/jobs/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filters)
  });
  if (!res.ok) throw new Error('Failed to search jobs');
  return res.json();
}

export async function fetchSources() {
  const res = await fetch(`${API_BASE}/jobs/sources`);
  if (!res.ok) throw new Error('Failed to fetch sources');
  return res.json();
}
