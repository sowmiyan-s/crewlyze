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

  if (listEl) {
    if (!projects.length) {
      listEl.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:0.8rem;">No projects yet.</div>';
    } else {
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
  }

  // Also render into dashboard projects grid on landing screen
  const dashGrid = $('dashboardProjectsGrid');
  if (dashGrid) {
    if (!projects.length) {
      dashGrid.innerHTML = '<div style="grid-column: 1/-1; padding: 24px; text-align: center; color: var(--text-secondary); background: rgba(255,255,255,0.01); border-radius: var(--r-md); border: 1px dashed var(--border-low);">No recent projects found. Upload a CSV to get started.</div>';
    } else {
      dashGrid.innerHTML = projects.map(p => `
        <div class="project-card card" data-id="${p.id}" style="padding: 18px; background: var(--bg-elevated); border: 1px solid var(--border-mid); border-radius: var(--r-md); cursor: pointer; transition: all 0.25s; display: flex; flex-direction: column; gap: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div style="font-weight: 700; color: #fff; font-size: 0.95rem;">${p.name || 'Untitled Project'}</div>
            <span style="font-size: 0.7rem; padding: 2px 8px; border-radius: 10px; background: ${p.status === 'completed' ? 'rgba(16,185,129,0.15)' : 'rgba(255,37,42,0.1)'}; color: ${p.status === 'completed' ? '#10b981' : 'var(--crimson-light)'}; border: 1px solid ${p.status === 'completed' ? 'rgba(16,185,129,0.3)' : 'rgba(255,37,42,0.2)'}; font-weight: 600;">${p.status || 'idle'}</span>
          </div>
          <div style="font-size: 0.78rem; color: var(--text-secondary);">${p.filename || 'dataset.csv'} ${p.rows_count ? `• ${p.rows_count.toLocaleString()} rows` : ''}</div>
          <div style="margin-top: auto; padding-top: 8px; font-size: 0.72rem; color: var(--text-muted); display: flex; justify-content: space-between;">
            <span>${p.created_at ? new Date(p.created_at > 1e11 ? p.created_at : p.created_at * 1000).toLocaleDateString() : ''}</span>
            <span style="color: var(--crimson, #ff252a); font-weight: 600;">Select →</span>
          </div>
        </div>
      `).join('');

      dashGrid.querySelectorAll('.project-card').forEach(item => {
        item.addEventListener('click', () => {
          const id = item.getAttribute('data-id');
          const proj = state.projects.find(x => x.id === id);
          if (proj) selectProject(proj);
        });
      });
    }
  }
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
      renderPreview(prev.preview || []);
      const updatedMeta = {
        ...project,
        rows_count: prev.rows_count || project.rows_count,
        cols_count: prev.cols_count || project.cols_count,
        numeric_count: prev.numeric_count || project.numeric_count,
        cat_count: prev.cat_count || project.cat_count
      };
      state.activeProject = updatedMeta;
      updateCardsDatasetInfo(updatedMeta);
      showScreen('results');
      switchWorkspaceMode('hub');
    } catch (err) {
      showScreen('results');
      switchWorkspaceMode('hub');
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
  const goal = options?.goal || $('configGoal')?.value || state.activeProject?.goal || '';

  const fd = new FormData();
  fd.append('session_id', sessionId);
  fd.append('provider', provider);
  fd.append('model', model);
  fd.append('api_key', apiKey);
  fd.append('report_title', reportTitle);
  fd.append('goal', goal);
  if (selectedAgents.length) {
    fd.append('tasks', selectedAgents.join(','));
    fd.append('selected_tasks', selectedAgents.join(','));
  }
  if (options?.deep !== undefined) {
    fd.append('deep_analysis', options.deep ? 'true' : 'false');
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
  const fileInput = $('fileInput');
  const startWizardCard = $('startWizardCard');
  const uploadZone = $('uploadZone');
  const importProjectCard = $('importProjectCard');
  const importModal = $('importProjectModal');
  const closeImportModal = $('closeImportModal');
  const importZipZone = $('importZipZone');
  const importZipFileInput = $('importZipFileInput');

  // Trigger CSV/Excel/SQLite file picker when clicking "Create New Project"
  if (startWizardCard && fileInput) {
    startWizardCard.addEventListener('click', () => fileInput.click());

    startWizardCard.addEventListener('dragover', e => {
      e.preventDefault();
      startWizardCard.style.borderColor = 'var(--crimson, #ff252a)';
      startWizardCard.style.background = 'rgba(255, 37, 42, 0.08)';
    });

    startWizardCard.addEventListener('dragleave', () => {
      startWizardCard.style.borderColor = '';
      startWizardCard.style.background = '';
    });

    startWizardCard.addEventListener('drop', e => {
      e.preventDefault();
      startWizardCard.style.borderColor = '';
      startWizardCard.style.background = '';
      const files = e.dataTransfer?.files;
      if (files && files[0]) {
        handleUploadFile(files[0]);
      }
    });
  }

  // Also support any legacy upload zone
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
  }

  if (fileInput) {
    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files[0]) {
        handleUploadFile(fileInput.files[0]);
      }
    });
  }

  // Import project (.zip) handlers
  if (importProjectCard && importModal) {
    importProjectCard.addEventListener('click', () => {
      importModal.classList.remove('hidden');
      importModal.style.display = 'flex';
    });
  }

  if (closeImportModal && importModal) {
    closeImportModal.addEventListener('click', () => {
      importModal.classList.add('hidden');
      importModal.style.display = 'none';
    });
  }

  if (importZipZone && importZipFileInput) {
    importZipZone.addEventListener('click', () => importZipFileInput.click());
    importZipFileInput.addEventListener('change', () => {
      if (importZipFileInput.files && importZipFileInput.files[0]) {
        handleUploadFile(importZipFileInput.files[0]);
        importModal?.classList.add('hidden');
        if (importModal) importModal.style.display = 'none';
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
// LLM Provider & Model Initialization
// ────────────────────────────────────────────────────────────────────────────

export async function initLlmSettings() {
  const providerSelect = $('llmProvider');
  const modelInput = $('llmModel');
  const modelList = $('modelList');
  const apiKeyInput = $('apiKey');
  const apiKeyStatus = $('sidebarApiKeyStatus');

  if (!providerSelect) return;

  let serverConfig = {};
  try {
    const res = await fetch('/api/config');
    if (res.ok) {
      serverConfig = await res.json();
    }
  } catch (e) {
    console.warn('Could not load server config:', e);
  }

  const PROVIDER_NAMES = {
    nvidia: 'NVIDIA NIM',
    groq: 'Groq',
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    gemini: 'Google Gemini',
    mistral: 'Mistral AI',
    minimax: 'MiniMax',
    ollama: 'Ollama (Local)',
    openrouter: 'OpenRouter',
    deepseek: 'DeepSeek',
    together: 'Together AI',
    cohere: 'Cohere',
    huggingface: 'Hugging Face',
    custom: 'Custom LLM'
  };

  const providers = Object.keys(MODEL_OPTIONS);
  providerSelect.innerHTML = providers.map(p => {
    const label = PROVIDER_NAMES[p] || p.toUpperCase();
    return `<option value="${p}">${label}</option>`;
  }).join('');

  const savedProvider = localStorage.getItem('llm_provider') || serverConfig.default_provider || 'nvidia';
  providerSelect.value = providers.includes(savedProvider) ? savedProvider : 'nvidia';

  function syncProviderAndModel() {
    const currentProvider = providerSelect.value;
    const models = MODEL_OPTIONS[currentProvider] || [];

    if (modelList) {
      modelList.innerHTML = models.map(m => `<option value="${m}">${m}</option>`).join('');
    }

    const savedModel = localStorage.getItem(`llm_model_${currentProvider}`) || localStorage.getItem('llm_model');
    if (savedModel && models.includes(savedModel)) {
      if (modelInput) modelInput.value = savedModel;
    } else if (models.length) {
      if (modelInput) modelInput.value = models[0];
    }

    let activeKey = '';
    if (currentProvider === 'nvidia') {
      activeKey = serverConfig.NVIDIA_API_KEY || serverConfig.NVIDIA_NIM_API_KEY || localStorage.getItem('key_nvidia') || '';
    } else if (currentProvider === 'mistral') {
      activeKey = serverConfig.MISTRAL_API_KEY || localStorage.getItem('key_mistral') || '';
    } else {
      const envKey = `${currentProvider.toUpperCase()}_API_KEY`;
      activeKey = serverConfig[envKey] || localStorage.getItem(`key_${currentProvider}`) || '';
    }

    if (apiKeyInput) apiKeyInput.value = activeKey;

    if (apiKeyStatus) {
      if (currentProvider === 'ollama') {
        apiKeyStatus.innerHTML = '<span style="color: #10b981; font-size: 0.75rem;">● Local Ollama</span>';
      } else if (activeKey) {
        apiKeyStatus.innerHTML = '<span style="color: #10b981; font-size: 0.75rem;">● API Key Configured</span>';
      } else {
        apiKeyStatus.innerHTML = '<span style="color: var(--crimson-light); font-size: 0.75rem;">○ No Key Set (Click Add Provider)</span>';
      }
    }
  }

  syncProviderAndModel();

  providerSelect.addEventListener('change', () => {
    localStorage.setItem('llm_provider', providerSelect.value);
    syncProviderAndModel();
  });

  if (modelInput) {
    modelInput.addEventListener('change', () => {
      localStorage.setItem(`llm_model_${providerSelect.value}`, modelInput.value);
      localStorage.setItem('llm_model', modelInput.value);
    });
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
  initLlmSettings();
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
    } else if (e.target.closest('#btnChatBackToHub') || e.target.closest('#btnAgenticBackToHub')) {
      switchWorkspaceMode('hub');
    } else if (e.target.closest('#sidebarLogo')) {
      showScreen('landing');
    } else if (e.target.closest('#sidebarSettingsBtn') || e.target.closest('#sidebarAddProviderBtn')) {
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
