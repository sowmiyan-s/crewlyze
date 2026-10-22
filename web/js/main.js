/**
 * Crewlyze - Application Bootstrap & Master Controller (ES6 Module)
 * Orchestrates modules, event delegation, and lifecycle hooks.
 */

import { state, $, $$, MODEL_OPTIONS, escHtml } from './state.js';
import { api } from './api.js';
import { renderCharts, initPlotlyResizeWatcher, resizeAllCharts } from './charts.js';
import { initCommandCenter, applyAnalysisPreset, updateActiveAgentsBadge, getSelectedAgents, getSelectedCategories, updateCardsDatasetInfo } from './command_center.js';
import { initTabs, renderStats, renderPreview, renderDashboard, switchTab } from './dashboard.js';
import { sendChatQuery, loadChatHistory, resetChat } from './chat.js';
import { initExportHandlers, downloadPdf } from './export_ui.js';

let activeSseSource = null;

export function toast(msg, type = 'info', durationMs = 2500) {
  const container = $('toastContainer');
  if (!container) return;
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => {
    t.classList.add('hide');
    setTimeout(() => t.remove(), 250);
  }, durationMs);
}
window.toast = toast;

export function showScreen(name) {
  const targetId = (name === 'home' || name === 'landing') ? 'landingScreen' : name + 'Screen';
  ['landingScreen', 'runningScreen', 'resultsScreen', 'metricsScreen'].forEach(id => {
    const el = $(id);
    if (el) el.classList.toggle('active', id === targetId);
  });
}
window.showScreen = showScreen;

export function switchWorkspaceMode(mode) {
  const hub = $('areaHub');
  const chat = $('areaChat');
  const agentic = $('areaAgentic');

  if (mode === 'chat') {
    hub?.classList.add('hidden');
    chat?.classList.remove('hidden');
    agentic?.classList.add('hidden');
  } else if (mode === 'agentic') {
    hub?.classList.add('hidden');
    chat?.classList.add('hidden');
    agentic?.classList.remove('hidden');
    updateCardsDatasetInfo(state.activeProject);
    updateActiveAgentsBadge();
    if (window.lucide) window.lucide.createIcons();
  } else {
    hub?.classList.remove('hidden');
    chat?.classList.add('hidden');
    agentic?.classList.add('hidden');
  }
}

export async function loadProjects() {
  try {
    const projects = await api.fetchProjects();
    state.projects = projects;
    renderProjectsList(projects);
  } catch (err) {
    console.error('Failed to load projects:', err);
  }
}

export function renderProjectsList(projects) {
  const listEl = $('projectsList');
  const countEl = $('dashboardProjectsCount');
  if (countEl) countEl.textContent = `${projects.length} Projects`;
  if (!listEl) return;

  if (!projects.length) {
    listEl.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:0.8rem;">No projects yet.</div>';
    return;
  }

  listEl.innerHTML = projects.map(p => `
    <div class="project-item ${state.activeProject?.id === p.id ? 'active' : ''}" data-id="${p.id}">
      <div class="project-item-title">${p.name || 'Untitled Project'}</div>
      <div class="project-item-meta">${p.filename || 'dataset.csv'} • ${p.status || 'idle'}</div>
    </div>
  `).join('');

  listEl.querySelectorAll('.project-item').forEach(item => {
    item.addEventListener('click', () => {
      const id = item.getAttribute('data-id');
      const proj = state.projects.find(x => x.id === id);
      if (proj) selectProject(proj);
    });
  });
}

export async function selectProject(project) {
  state.activeProject = project;
  state.uploadedSession = project.id;
  renderProjectsList(state.projects);
  updateCardsDatasetInfo(project);

  const topbarStopBtn = $('topbarStopBtn');
  if (topbarStopBtn) topbarStopBtn.classList.add('hidden');

  if (project.status === 'completed') {
    try {
      const results = await api.fetchResults(project.id);
      state.results = results;
      showScreen('results');
      switchWorkspaceMode('agentic');
      renderDashboard(results, project.id);
      renderCharts(results.plotly_charts || [], results.png_charts || [], project.id);
      loadChatHistory(project.id);
      updateCardsDatasetInfo({ ...project, rows_count: results.rows_count, cols_count: results.cols_count });
    } catch (err) {
      toast('Failed to load project results: ' + err.message, 'error');
    }
  } else {
    try {
      const prev = await api.fetchPreview(project.id);
      showScreen('landing');
      renderPreview(prev.preview || []);
      updateCardsDatasetInfo({
        ...project,
        rows_count: prev.rows_count || project.rows_count,
        cols_count: prev.cols_count || project.cols_count,
        numeric_count: prev.numeric_count || project.numeric_count,
        cat_count: prev.cat_count || project.cat_count
      });
    } catch (err) {
      showScreen('landing');
    }
  }
}

export function openConfigModal() {
  const modal = $('configModal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
  }
}
window.openConfigModal = openConfigModal;

export function closeConfigModal() {
  const modal = $('configModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
}
window.closeConfigModal = closeConfigModal;

export async function checkUpdates() {
  try {
    const data = await api.checkVersion();
    if (data.update_available) {
      const popup = $('crewlyzeUpdatePopup');
      const curEl = $('updateCurrentVerText');
      const latEl = $('updateLatestVerText');
      if (curEl) curEl.textContent = `v${data.current_version}`;
      if (latEl) latEl.textContent = `v${data.latest_version}`;
      if (popup) popup.classList.remove('hidden');
    }
  } catch (e) {
    // offline or rate limited
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Stepper & Analysis Progress Tracking
// ────────────────────────────────────────────────────────────────────────────

const STAGE_ORDER = ['data_analysis', 'business_analysis', 'data_mining', 'predictive_analysis', 'eda'];

export function updateProgressTrack(newStage) {
  const newIdx = STAGE_ORDER.indexOf(newStage);
  if (newIdx === -1) return;

  STAGE_ORDER.forEach((stage, idx) => {
    const item = document.querySelector(`.stage-item[data-stage="${stage}"]`);
    if (!item) return;
    if (idx < newIdx) {
      item.className = 'stage-item done';
    } else if (idx === newIdx) {
      item.className = 'stage-item active';
    } else {
      item.className = 'stage-item';
    }
  });

  const labels = {
    data_analysis: 'Running Data Analysis Domain...',
    business_analysis: 'Running Business Analysis Domain...',
    data_mining: 'Running Data Mining Domain...',
    predictive_analysis: 'Running Predictive Analysis Domain...',
    eda: 'Compiling Visualizations & EDA...'
  };

  const text = labels[newStage] || 'Analysing...';
  const el = $('notifActiveJob');
  if (el) el.textContent = text;
}

export function inferStageFromLog(line) {
  const ll = line.toLowerCase();
  
  const execMatch = line.match(/\[(\d+\/\d+)\]\s+Executing\s+([^\n(]+)/i);
  if (execMatch) {
    const curAgentEl = $('currentAgentRunningText');
    const counterEl = $('agentsProgressCounter');
    if (curAgentEl) curAgentEl.textContent = `⚡ Executing: ${execMatch[2].trim()}`;
    if (counterEl) counterEl.textContent = `Agent ${execMatch[1]}`;
  }

  if (ll.includes('data_analysis') || ll.includes('data cleaner') || ll.includes('statistical analysis') || ll.includes('comparative analysis') || ll.includes('trend analysis') || ll.includes('insight discovery')) {
    return 'data_analysis';
  }
  if (ll.includes('business_analysis') || ll.includes('sales analysis') || ll.includes('profitability') || ll.includes('expense optimization') || ll.includes('customer intelligence') || ll.includes('decision support')) {
    return 'business_analysis';
  }
  if (ll.includes('data_mining') || ll.includes('pattern discovery') || ll.includes('relationship analysis') || ll.includes('segmentation') || ll.includes('anomaly detection') || ll.includes('association mining')) {
    return 'data_mining';
  }
  if (ll.includes('predictive_analysis') || ll.includes('sales forecasting') || ll.includes('budget forecasting') || ll.includes('demand forecasting') || ll.includes('risk prediction') || ll.includes('what-if') || ll.includes('simulation')) {
    return 'predictive_analysis';
  }
  if (ll.includes('eda') || ll.includes('visualization') || ll.includes('plotly') || ll.includes('charts') || ll.includes('storytelling')) {
    return 'eda';
  }
  return null;
}

// ────────────────────────────────────────────────────────────────────────────
// Analysis Pipeline Launch & SSE Streaming
// ────────────────────────────────────────────────────────────────────────────

export async function launchAnalysisPipeline(options = {}) {
  const sessionId = state.activeProject?.id || state.uploadedSession;
  if (!sessionId) {
    toast('Please upload or select a dataset first.', 'error');
    openConfigModal();
    return;
  }

  closeConfigModal();

  const selectedAgents = (options && options.agents && options.agents.length) ? options.agents : getSelectedAgents();
  const targetCategory = options?.category || null;

  const provider = $('llmProvider')?.value || 'nvidia';
  const model = $('llmModel')?.value || 'nvidia_nim/meta/llama-3.1-70b-instruct';
  const apiKey = $('apiKey')?.value || '';
  const reportTitle = $('configReportTitle')?.value || state.activeProject?.report_title || `${state.activeProject?.name || 'Dataset'} Executive Report`;
  const goal = $('configGoal')?.value || state.activeProject?.goal || '';

  const fd = new FormData();
  fd.append('session_id', sessionId);
  fd.append('provider', provider);
  fd.append('model', model);
  fd.append('api_key', apiKey);
  fd.append('report_title', reportTitle);
  fd.append('goal', goal);
  if (selectedAgents.length) {
    fd.append('tasks', selectedAgents.join(','));
  }

  try {
    const res = await api.triggerAnalysis(fd);
    showScreen('running');
    $('topbarStopBtn')?.classList.remove('hidden');

    const logOutput = $('logOutput');
    if (logOutput) logOutput.innerHTML = '';

    toast(targetCategory ? `Step ${targetCategory.replace(/_/g, ' ')} initiated.` : 'Analysis suite initialized. Multi-agent swarm active.', 'info');

    if (activeSseSource) {
      activeSseSource.close();
    }

    activeSseSource = api.streamLogs(
      sessionId,
      line => {
        if (!line) return;
        if (logOutput) {
          const row = document.createElement('div');
          row.className = 'log-line';
          row.textContent = line;
          logOutput.appendChild(row);
          logOutput.scrollTop = logOutput.scrollHeight;
        }

        const stage = inferStageFromLog(line);
        if (stage) {
          updateProgressTrack(stage);
        }
      },
      async () => {
        // EOF
        $('topbarStopBtn')?.classList.add('hidden');
        toast('Multi-agent analysis completed!', 'success');
        try {
          const results = await api.fetchResults(sessionId);
          state.results = results;
          showScreen('results');
          switchWorkspaceMode('agentic');
          renderDashboard(results, sessionId);
          renderCharts(results.plotly_charts || [], results.png_charts || [], sessionId);
          loadChatHistory(sessionId);
          loadProjects();

          // If a specific step/category was executed, immediately switch to its domain tab
          if (targetCategory) {
            switchTab(targetCategory);
          } else {
            switchTab('storyboard');
          }
        } catch (loadErr) {
          toast('Error loading results: ' + loadErr.message, 'error');
        }
      },
      err => {
        $('topbarStopBtn')?.classList.add('hidden');
      }
    );
  } catch (err) {
    toast('Failed to start analysis: ' + err.message, 'error');
  }
}

export async function stopCurrentAnalysis() {
  const sessionId = state.activeProject?.id || state.uploadedSession;
  if (!sessionId) return;
  try {
    await api.stopAnalysis(sessionId);
    if (activeSseSource) {
      activeSseSource.close();
      activeSseSource = null;
    }
    $('topbarStopBtn')?.classList.add('hidden');
    toast('Analysis stopped.', 'warning');
    loadProjects();
  } catch (err) {
    toast('Error stopping analysis: ' + err.message, 'error');
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Upload Flow Setup
// ────────────────────────────────────────────────────────────────────────────

export function initUploadWizard() {
  const uploadZone = $('uploadZone');
  const fileInput = $('fileInput');

  if (uploadZone && fileInput) {
    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', e => {
      e.preventDefault();
      uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
      uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', e => {
      e.preventDefault();
      uploadZone.classList.remove('dragover');
      const files = e.dataTransfer?.files;
      if (files && files[0]) {
        handleUploadFile(files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files[0]) {
        handleUploadFile(fileInput.files[0]);
      }
    });
  }
}

async function handleUploadFile(file) {
  const fd = new FormData();
  const projName = file.name.rsplit ? file.name.rsplit('.', 1)[0] : file.name.replace(/\.[^/.]+$/, "");
  fd.append('name', projName);
  fd.append('report_title', `${projName} Executive Intelligence`);
  fd.append('goal', '');
  fd.append('file', file);

  toast('Uploading dataset...', 'info');

  try {
    const res = await api.createProject(fd);
    state.uploadedSession = res.id;

    if (res.status === 'awaiting_sheet' && res.sheets && res.sheets.length > 1) {
      openSheetSelector(res.id, res.sheets);
    } else if (res.status === 'awaiting_table' && res.tables && res.tables.length > 1) {
      openTableSelector(res.id, res.tables);
    } else {
      toast('Dataset uploaded successfully!', 'success');
      await loadProjects();
      const proj = state.projects.find(p => p.id === res.id) || res;
      selectProject(proj);
      updateCardsDatasetInfo(proj);
    }
  } catch (err) {
    toast('Upload failed: ' + err.message, 'error');
  }
}

function openSheetSelector(sessionId, sheets) {
  const modal = $('sheetSelectorModal');
  const select = $('sheetSelect');
  if (!modal || !select) return;
  select.innerHTML = sheets.map(s => `<option value="${escHtml(s)}">${escHtml(s)}</option>`).join('');
  modal.classList.remove('hidden');
  modal.style.display = 'flex';

  const confirmBtn = $('confirmSheetBtn');
  if (confirmBtn) {
    confirmBtn.onclick = async () => {
      modal.classList.add('hidden');
      modal.style.display = 'none';
      const sheetName = select.value;
      const sfd = new FormData();
      sfd.append('session_id', sessionId);
      sfd.append('sheet_name', sheetName);
      try {
        await fetch('/api/upload/select-sheet', { method: 'POST', body: sfd });
        toast(`Loaded sheet '${sheetName}'`, 'success');
        await loadProjects();
        const proj = state.projects.find(p => p.id === sessionId);
        if (proj) selectProject(proj);
      } catch (err) {
        toast('Failed to load sheet: ' + err.message, 'error');
      }
    };
  }
}

function openTableSelector(sessionId, tables) {
  const modal = $('tableSelectorModal');
  const select = $('tableSelect');
  if (!modal || !select) return;
  select.innerHTML = tables.map(t => `<option value="${escHtml(t)}">${escHtml(t)}</option>`).join('');
  modal.classList.remove('hidden');
  modal.style.display = 'flex';

  const confirmBtn = $('confirmTableBtn');
  if (confirmBtn) {
    confirmBtn.onclick = async () => {
      modal.classList.add('hidden');
      modal.style.display = 'none';
      const tableName = select.value;
      const tfd = new FormData();
      tfd.append('session_id', sessionId);
      tfd.append('table_name', tableName);
      try {
        await fetch('/api/upload/select-table', { method: 'POST', body: tfd });
        toast(`Loaded table '${tableName}'`, 'success');
        await loadProjects();
        const proj = state.projects.find(p => p.id === sessionId);
        if (proj) selectProject(proj);
      } catch (err) {
        toast('Failed to load table: ' + err.message, 'error');
      }
    };
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Bootstrap
// ────────────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    window.lucide.createIcons();
  }

  initTabs();
  initExportHandlers();
  initPlotlyResizeWatcher();
  initUploadWizard();
  initCommandCenter(openConfigModal, launchAnalysisPipeline);
  loadProjects();
  checkUpdates();

  // Navigation and modal dismissals
  document.addEventListener('click', e => {
    if (e.target.closest('#closeConfigModal') || e.target.closest('#cancelConfigBtn')) {
      closeConfigModal();
    } else if (e.target === $('configModal')) {
      closeConfigModal();
    } else if (e.target.closest('#updatePopupCloseBtn') || e.target.closest('#updatePopupRemindBtn')) {
      $('crewlyzeUpdatePopup')?.classList.add('hidden');
    } else if (e.target.closest('#closeChartZoomBtn') || e.target === $('chartZoomModal')) {
      $('chartZoomModal')?.classList.add('hidden');
    } else if (e.target.closest('#topbarStopBtn') || e.target.closest('#clearLogBtn')) {
      stopCurrentAnalysis();
    } else if (e.target.closest('#btnEnterChat')) {
      switchWorkspaceMode('chat');
    } else if (e.target.closest('#btnEnterAgentic')) {
      switchWorkspaceMode('agentic');
    } else if (e.target.closest('#sidebarSettingsBtn')) {
      openConfigModal();
    } else if (e.target.closest('#sidebarSaveLlmBtn') || e.target.closest('#saveSettingsBtn')) {
      const provider = $('llmProvider')?.value || 'nvidia';
      const model = $('llmModel')?.value || '';
      const apiKey = $('apiKey')?.value || '';
      api.saveConfig({ default_provider: provider, default_model: model, api_key: apiKey })
        .then(() => toast('LLM settings saved successfully.', 'success'))
        .catch(err => toast('Failed to save settings: ' + err.message, 'error'));
    } else if (e.target.closest('#settingsTestConnectionBtn') || e.target.closest('#testConnectionBtn')) {
      const provider = $('llmProvider')?.value || 'nvidia';
      const model = $('llmModel')?.value || '';
      const apiKey = $('apiKey')?.value || '';
      const statusEl = $('connectionStatus');
      if (statusEl) {
        statusEl.style.display = 'block';
        statusEl.textContent = 'Testing connection...';
      }
      api.validateKey(provider, model, apiKey)
        .then(res => {
          if (statusEl) statusEl.textContent = res.message || 'Connection verified successfully!';
          toast('Connection verified!', 'success');
        })
        .catch(err => {
          if (statusEl) statusEl.textContent = 'Connection failed: ' + err.message;
          toast('Validation failed: ' + err.message, 'error');
        });
    } else if (e.target.closest('#downloadCsvBtn') || e.target.closest('#sidebarDownloadCsvBtn')) {
      const pId = state.activeProject?.id;
      if (pId) {
        window.location.href = `/api/projects/${encodeURIComponent(pId)}/download-csv`;
      } else {
        toast('No active project to download.', 'warning');
      }
    } else if (e.target.closest('#reRunBtn') || e.target.closest('#sidebarReRunBtn')) {
      openConfigModal();
    } else if (e.target.closest('#sendChatBtn')) {
      const q = $('chatInput')?.value;
      if (q) {
        $('chatInput').value = '';
        sendChatQuery(q, $('llmProvider')?.value, $('llmModel')?.value, $('apiKey')?.value);
      }
    } else if (e.target.closest('#clearChatBtn')) {
      resetChat();
    }
  });

  // Chat enter key
  $('chatInput')?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const q = $('chatInput')?.value;
      if (q) {
        $('chatInput').value = '';
        sendChatQuery(q, $('llmProvider')?.value, $('llmModel')?.value, $('apiKey')?.value);
      }
    }
  });
});
