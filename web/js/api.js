/**
 * Crewlyze - API Service Layer (ES6 Module)
 * Handles all HTTP requests and SSE streams to the FastAPI backend.
 */

export const api = {
  async fetchProjects() {
    const res = await fetch('/api/projects');
    if (!res.ok) throw new Error('Failed to fetch projects');
    return await res.json();
  },

  async createProject(formData) {
    const res = await fetch('/api/projects', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create project' }));
      throw new Error(err.detail || 'Upload failed');
    }
    return await res.json();
  },

  async renameProject(projectId, name) {
    const fd = new FormData();
    fd.append('name', name);
    const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/rename`, {
      method: 'POST',
      body: fd,
    });
    if (!res.ok) throw new Error('Failed to rename project');
    return await res.json();
  },

  async deleteProject(projectId) {
    const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete project');
    return await res.json();
  },

  async fetchPreview(projectId) {
    const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/preview`);
    if (!res.ok) throw new Error('Failed to fetch data preview');
    return await res.json();
  },

  async fetchResults(sessionId) {
    const res = await fetch(`/api/results?session_id=${encodeURIComponent(sessionId)}`);
    if (!res.ok) throw new Error('Failed to load analysis results');
    return await res.json();
  },

  async triggerAnalysis(formData) {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to start analysis' }));
      throw new Error(err.detail || 'Analysis start failed');
    }
    return await res.json();
  },

  async stopAnalysis(sessionId) {
    const fd = new FormData();
    fd.append('session_id', sessionId);
    const res = await fetch('/api/analyze/stop', {
      method: 'POST',
      body: fd,
    });
    return await res.json();
  },

  streamLogs(sessionId, onMessage, onEof, onError) {
    const url = `/api/analyze/stream?session_id=${encodeURIComponent(sessionId)}`;
    const evtSource = new EventSource(url);
    
    evtSource.onmessage = e => {
      const text = e.data;
      if (text === '[EOF]') {
        evtSource.close();
        if (onEof) onEof();
      } else {
        if (onMessage) onMessage(text);
      }
    };

    evtSource.onerror = err => {
      evtSource.close();
      if (onError) onError(err);
    };

    return evtSource;
  },

  async validateKey(provider, model, apiKey) {
    const fd = new FormData();
    fd.append('provider', provider);
    fd.append('model', model);
    fd.append('api_key', apiKey || '');
    const res = await fetch('/api/validate-key', {
      method: 'POST',
      body: fd,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Connection check failed' }));
      throw new Error(err.detail || 'Validation failed');
    }
    return await res.json();
  },

  async fetchConfig() {
    const res = await fetch('/api/config');
    if (!res.ok) throw new Error('Failed to load configurations');
    return await res.json();
  },

  async saveConfig(payload) {
    const res = await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to save settings');
    return await res.json();
  },

  async querySql(sessionId, sqlQuery) {
    const fd = new FormData();
    fd.append('session_id', sessionId);
    fd.append('sql_query', sqlQuery);
    const res = await fetch('/api/query-sql', {
      method: 'POST',
      body: fd,
    });
    return await res.json();
  },

  async queryRelationalSql(sessionId, sqlQuery) {
    const fd = new FormData();
    fd.append('session_id', sessionId);
    fd.append('sql_query', sqlQuery);
    const res = await fetch('/api/query-relational-sql', {
      method: 'POST',
      body: fd,
    });
    return await res.json();
  },

  async fetchChatHistory(sessionId) {
    const res = await fetch(`/api/chat-history?session_id=${encodeURIComponent(sessionId)}`);
    if (!res.ok) return { messages: [] };
    return await res.json();
  },

  async saveChatHistory(sessionId, messages) {
    const fd = new FormData();
    fd.append('session_id', sessionId);
    fd.append('messages_json', JSON.stringify(messages));
    const res = await fetch('/api/chat-history', {
      method: 'POST',
      body: fd,
    });
    return await res.json();
  },

  async askCopilot(formData) {
    const res = await fetch('/api/copilot', {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Copilot request failed' }));
      throw new Error(err.detail || 'Chat query failed');
    }
    return await res.json();
  },

  async checkVersion() {
    const res = await fetch('/api/system/version');
    if (!res.ok) throw new Error('Version check failed');
    return await res.json();
  },

  async triggerUpdate() {
    const res = await fetch('/api/system/update', { method: 'POST' });
    return await res.json();
  }
};
