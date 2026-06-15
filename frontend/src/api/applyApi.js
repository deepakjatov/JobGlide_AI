const BASE = 'http://localhost:8000/api';

// ─────────────────────────── Profile ────────────────────────────────
export async function getProfile() {
  const r = await fetch(`${BASE}/profile`);
  return r.json();
}

export async function saveProfile(profile) {
  const r = await fetch(`${BASE}/profile`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile),
  });
  return r.json();
}

// ─────────────────────────── Applications ───────────────────────────
export async function getApplications(status = null) {
  const url = status ? `${BASE}/applications?status=${status}` : `${BASE}/applications`;
  const r = await fetch(url);
  return r.json();
}

export async function addApplication(app) {
  const r = await fetch(`${BASE}/applications`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(app),
  });
  return r.json();
}

export async function updateApplication(id, updates) {
  const r = await fetch(`${BASE}/applications/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  return r.json();
}

export async function deleteApplication(id) {
  const r = await fetch(`${BASE}/applications/${id}`, { method: 'DELETE' });
  return r.json();
}

export async function getAppliedJobIds() {
  const r = await fetch(`${BASE}/applications/applied-ids`);
  return r.json();
}

// ─────────────────────────── Quick Apply ────────────────────────────
export async function quickApply(job) {
  const r = await fetch(`${BASE}/apply/quick`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      job_id: job.id,
      job_title: job.title,
      company: job.company,
      apply_url: job.apply_url,
      source: job.source,
    }),
  });
  return r.json();
}

// ─────────────────────────── LLM Providers ──────────────────────────
export async function getLLMProviders() {
  const r = await fetch(`${BASE}/apply/llm-providers`);
  return r.json();
}

// Cover letter — streaming
export async function streamCoverLetter(job, provider, model, onChunk, onDone, onError) {
  try {
    const resp = await fetch(`${BASE}/apply/cover-letter`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_title: job.title,
        company: job.company,
        job_description: job.description,
        provider,
        model,
      }),
    });
    if (!resp.ok) {
      const err = await resp.text();
      onError(err);
      return;
    }
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      onChunk(decoder.decode(value, { stream: true }));
    }
    onDone();
  } catch (e) {
    onError(e.message);
  }
}

// ─────────────────────────── Auto Apply ─────────────────────────────
export async function startAutoApply(payload) {
  const r = await fetch(`${BASE}/apply/auto/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const err = await r.json();
    throw new Error(err.detail || 'Failed to start');
  }
  return r.json();
}

export async function stopAutoApply() {
  const r = await fetch(`${BASE}/apply/auto/stop`, { method: 'POST' });
  return r.json();
}

export async function getAutoApplyStatus() {
  const r = await fetch(`${BASE}/apply/auto/status`);
  return r.json();
}

export async function uploadResumeFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const r = await fetch(`${BASE}/profile/resume`, {
    method: 'POST',
    body: formData,
  });
  if (!r.ok) {
    const err = await r.json();
    throw new Error(err.detail || 'Failed to upload');
  }
  return r.json();
}
