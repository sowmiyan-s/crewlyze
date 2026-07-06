/**
 * Crewlyze — Web App JavaScript
 * Connects to the FastAPI backend at the same origin.
 *
 * Features:
 *  - Multi-project sidebar with create / delete / switch
 *  - LLM provider + model picker with test-connection
 *  - Smart task-card selection with dependency enforcement
 *  - CSV upload + drag-and-drop
 *  - SSE-based live log streaming
 *  - Collapsible data preview table
 *  - Interactive Plotly chart rendering from JSON
 *  - AI Copilot chat with /column slash-command picker
 *  - PDF & CSV download
 *  - Toast notifications
 */

'use strict';

const DEFAULT_THUMBNAIL_SVG = '/assets/placeholder_thumbnail.png';

// ────────────────────────────────────────────────────────────────────────────
// Model catalogue (mirrors the sidebar in the old Streamlit app)
// ────────────────────────────────────────────────────────────────────────────
const MODEL_OPTIONS = {
  nvidia:      [
    'nvidia_nim/meta/llama-3.1-8b-instruct',
    'nvidia_nim/meta/llama-3.1-70b-instruct',
    'nvidia_nim/meta/llama-3.1-405b-instruct',
    'nvidia_nim/meta/llama-3.2-1b-instruct',
    'nvidia_nim/meta/llama-3.2-3b-instruct',
    'nvidia_nim/meta/llama-3.3-70b-instruct',
    'nvidia_nim/nvidia/llama-3.1-nemotron-70b-instruct',
    'nvidia_nim/nvidia/llama-3.1-nemotron-51b-instruct',
    'nvidia_nim/nvidia/mistral-nemo-minitron-8b-8k-instruct',
    'nvidia_nim/nvidia/nemotron-4-340b-instruct',
    'nvidia_nim/nvidia/nemotron-mini-4b-instruct',
    'nvidia_nim/mistralai/mistral-large-2407',
    'nvidia_nim/mistralai/mistral-7b-instruct-v0.3',
    'nvidia_nim/mistralai/mixtral-8x7b-instruct-v01',
    'nvidia_nim/mistralai/mixtral-8x22b-instruct-v01',
    'nvidia_nim/google/gemma-2-9b-it',
    'nvidia_nim/google/gemma-2-27b-it',
    'nvidia_nim/microsoft/phi-3-mini-128k-instruct',
    'nvidia_nim/microsoft/phi-3-medium-128k-instruct',
    'nvidia_nim/microsoft/phi-3-small-128k-instruct',
    'nvidia_nim/qwen/qwen2-7b-instruct',
    'nvidia_nim/databricks/dbrx-instruct',
    'nvidia_nim/01-ai/yi-large',
    'nvidia_nim/aisingapore/sea-lion-7b-instruct',
    'nvidia_nim/ibm/granite-34b-code-instruct',
    'nvidia_nim/upstage/solar-10.7b-instruct',
    'nvidia_nim/snowflake/arctic-instruct',
    'nvidia_nim/writer/palmyra-med-70b-32k',
    'nvidia_nim/writer/palmyra-fin-70b-32k',
  ],
  minimax:     ['minimaxai/minimax-m3'],
  groq:        ['groq/llama-3.1-8b-instant','groq/llama-3.3-70b-versatile','groq/mixtral-8x7b-32768','groq/gemma2-9b-it'],
  openai:      ['gpt-4o','gpt-4o-mini','gpt-4-turbo','gpt-3.5-turbo'],
  anthropic:   ['claude-3-5-sonnet-20241022','claude-3-opus-20240229','claude-3-sonnet-20240229','claude-3-haiku-20240307'],
  gemini:      ['gemini/gemini-pro','gemini/gemini-1.5-pro','gemini/gemini-1.5-flash'],
  mistral:     ['mistral/mistral-tiny','mistral/mistral-small','mistral/mistral-medium','mistral/mistral-large-latest'],
  huggingface: ['huggingface/HuggingFaceH4/zephyr-7b-beta','huggingface/meta-llama/Llama-2-7b-chat-hf'],
  ollama:      ['ollama/llama3','ollama/mistral','ollama/gemma2'],
  custom:      ['gpt-3.5-turbo', 'gpt-4'],
  cohere:      ['cohere/command-r-plus', 'cohere/command-r', 'cohere/command-light'],
  together:    ['together_ai/meta-llama/Llama-3-70b-chat-hf', 'together_ai/meta-llama/Llama-3-8b-chat-hf', 'together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1'],
  openrouter:  ['openrouter/google/gemma-2-9b-it', 'openrouter/meta-llama/llama-3-8b-instruct', 'openrouter/anthropic/claude-3.5-sonnet'],
  deepseek:    ['deepseek/deepseek-chat', 'deepseek/deepseek-coder'],
  perplexity:  ['perplexity/llama-3-sonar-large-32k-chat', 'perplexity/llama-3-sonar-small-32k-chat'],
};

// ────────────────────────────────────────────────────────────────────────────
// App state
// ────────────────────────────────────────────────────────────────────────────
const state = {
  projects:         [],   // array of project metadata from API
  activeProject:    null, // currently viewed project
  uploadedFile:     null, // File object pending analysis
  uploadedSession:  null, // session_id returned after upload
  results:          null, // latest results JSON
  columns:          [],   // column names from last preview
  colTypes:         {},   // column → dtype string
  chatHistory:      [],   // [{role, content, plot_url}]
  previewMinimized: false,
  sseSource:        null, // current EventSource
  resultsCache:     {},   // session_id -> results JSON cache
};

// ────────────────────────────────────────────────────────────────────────────
// DOM refs
// ────────────────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

const els = {
  sidebar:           $('sidebar'),
  sidebarToggle:     $('sidebarToggle'),
  mobileSidebarBtn:  $('mobileSidebarBtn'),
  projectsList:      $('projectsList'),
  newProjectBtn:     $('newProjectBtn'),
  sidebarLogo:       $('sidebarLogo'),
  newProjectWizard:  $('newProjectWizard'),
  wizardStep0:       $('wizardStep0'),
  startWizardCard:   $('startWizardCard'),
  wizardStep1:       $('modalStep1'),
  wizardBack1Btn:    $('wizardBack1Btn'),
  wizardStep2:       $('modalStep2'),
  wizardProjectName: $('wizardProjectName'),
  wizardNextBtn:     $('wizardNextBtn'),
  wizardBackBtn:     $('wizardBackBtn'),
  wizardUploadTitle: $('wizardUploadTitle'),
  dashboardProjectsGrid:  $('dashboardProjectsGrid'),
  dashboardProjectsCount: $('dashboardProjectsCount'),

  // Settings Modal elements
  sidebarSettingsBtn:       $('sidebarSettingsBtn'),
  settingsModal:            $('settingsModal'),
  closeSettingsModal:       $('closeSettingsModal'),
  cancelSettingsBtn:        $('cancelSettingsBtn'),
  saveSettingsBtn:          $('saveSettingsBtn'),
  settingsCooldown:         $('settingsCooldown'),
  settingsCooldownVal:      $('settingsCooldownVal'),
  settingsTestConnectionBtn: $('settingsTestConnectionBtn'),
  settingsConnectionStatus:  $('settingsConnectionStatus'),
  keyNvidia:                $('keyNvidia'),
  keyGroq:                  $('keyGroq'),
  keyOpenai:                $('keyOpenai'),
  keyAnthropic:             $('keyAnthropic'),
  keyGemini:                $('keyGemini'),
  keyMistral:               $('keyMistral'),
  keyHuggingface:           $('keyHuggingface'),
  urlOllama:                $('urlOllama'),
  urlCustom:                $('urlCustom'),
  keyCustom:                $('keyCustom'),
  showCustom:               $('showCustom'),
  keyCohere:                $('keyCohere'),
  keyTogether:              $('keyTogether'),
  keyOpenrouter:            $('keyOpenrouter'),
  keyDeepseek:              $('keyDeepseek'),
  keyPerplexity:            $('keyPerplexity'),

  // Checkboxes
  showNvidia:               $('showNvidia'),
  showGroq:                 $('showGroq'),
  showOpenai:               $('showOpenai'),
  showAnthropic:            $('showAnthropic'),
  showGemini:               $('showGemini'),
  showMistral:              $('showMistral'),
  showHuggingface:          $('showHuggingface'),
  showOllama:               $('showOllama'),
  showCohere:               $('showCohere'),
  showTogether:             $('showTogether'),
  showOpenrouter:           $('showOpenrouter'),
  showDeepseek:             $('showDeepseek'),
  showPerplexity:           $('showPerplexity'),

  llmProvider:       $('llmProvider'),
  llmModel:          $('llmModel'),
  apiKey:            $('apiKey'),
  toggleKey:         $('toggleKey'),
  keyLabel:          $('keyLabel'),
  cooldown:          $('cooldown'),
  cooldownVal:       $('cooldownVal'),
  testConnectionBtn: $('testConnectionBtn'),
  connectionStatus:  $('connectionStatus'),

  statusPill:        $('statusPill'),
  breadcrumb:        $('breadcrumb'),

  // Screens
  landingScreen:     $('landingScreen'),
  runningScreen:     $('runningScreen'),
  resultsScreen:     $('resultsScreen'),

  // Upload
  uploadZone:        $('uploadZone'),
  fileInput:         $('fileInput'),
  uploadedFileMeta:  $('uploadedFileMeta'),
  uploadedFileActions: $('uploadedFileActions'),
  startAnalysisBtn:  $('startAnalysisBtn'),

  // Config modal
  configModal:       $('configModal'),
  closeConfigModal:  $('closeConfigModal'),
  cancelConfigBtn:   $('cancelConfigBtn'),
  runAnalysisBtn:    $('runAnalysisBtn'),
  reportTitle:       $('reportTitle'),

  // Task cards
  taskCleaning:      $('taskCleaning'),
  taskRelations:     $('taskRelations'),
  taskInsights:      $('taskInsights'),
  taskViz:           $('taskViz'),
  taskCardCleaning:  $('taskCardCleaning'),
  taskCardRelations:  $('taskCardRelations'),
  taskCardInsights:  $('taskCardInsights'),
  taskCardViz:       $('taskCardViz'),

  // Running
  runningTitle:      $('runningTitle'),
  logOutput:         $('logOutput'),
  clearLogBtn:       $('clearLogBtn'),

  // Results
  statsRow:          $('statsRow'),
  tabBtns:           $$('.tab-btn'),
  tabPanels:         $$('.tab-panel'),

  // Preview
  previewTable:      $('previewTable'),
  togglePreviewBtn:  $('togglePreviewBtn'),
  previewTableWrap:  $('previewTableWrap'),

  // Panels
  cleaningContent:   $('cleaningContent'),
  relationsContent:  $('relationsContent'),
  insightsContent:   $('insightsContent'),
  plotlyChartsWrap:  $('plotlyChartsWrap'),
  pngChartsWrap:     $('pngChartsWrap'),
  pngCharts:         $('pngCharts'),
  vizCodeBlock:      $('vizCodeBlock'),
  vizCodeDetails:    $('vizCodeDetails'),

  // Chat
  chatMessages:      $('chatMessages'),
  chatBackBtn:       $('chatBackBtn'),
  chatInput:         $('chatInput'),
  sendChatBtn:       $('sendChatBtn'),
  clearChatBtn:      $('clearChatBtn'),
  colPickerDropdown: $('colPickerDropdown'),
  toggleExportModeBtn: $('toggleExportModeBtn'),

  // Export
  exportPdfBtn:      $('exportPdfBtn'),
  downloadCsvBtn:    $('downloadCsvBtn'),
  reRunBtn:          $('reRunBtn'),

  // Sidebar Export
  sidebarProjectActions: $('sidebarProjectActions'),
  sidebarExportPdfBtn:   $('sidebarExportPdfBtn'),
  sidebarExportZipBtn:   $('sidebarExportZipBtn'),
  sidebarDownloadCsvBtn: $('sidebarDownloadCsvBtn'),
  sidebarReRunBtn:       $('sidebarReRunBtn'),

  toastContainer:    $('toastContainer'),

  // API Warning Modal
  apiWarningModal:     $('apiWarningModal'),
  warningProviderName: $('warningProviderName'),
  guideToApiBtn:       $('guideToApiBtn'),
  closeApiWarningBtn:  $('closeApiWarningBtn'),

  // Custom dialog modal elements
  customDialogModal:           $('customDialogModal'),
  customDialogTitle:           $('customDialogTitle'),
  customDialogMessage:         $('customDialogMessage'),
  customDialogPromptContainer: $('customDialogPromptContainer'),
  customDialogInput:           $('customDialogInput'),
  customDialogCancelBtn:       $('customDialogCancelBtn'),
  customDialogConfirmBtn:      $('customDialogConfirmBtn'),
  closeCustomDialogBtn:        $('closeCustomDialogBtn'),
  stagePovPanel:               $('stagePovPanel'),
  wizardReportTitle:           $('wizardReportTitle'),
  wizardProjectGoal:           $('wizardProjectGoal'),
  importProjectCard:           $('importProjectCard'),
  importZipFileInput:          $('importZipFileInput'),
  exportZipBtn:                $('exportZipBtn'),
  btnSectionChat:              $('btnSectionChat'),
  btnSectionAgentic:           $('btnSectionAgentic'),
  areaChat:                    $('areaChat'),
  areaAgentic:                 $('areaAgentic'),
  areaHub:                     $('areaHub'),
  btnEnterChat:                $('btnEnterChat'),
  btnEnterAgentic:             $('btnEnterAgentic'),
  btnRenameColQuick:           $('btnRenameColQuick'),
  btnDeleteColQuick:           $('btnDeleteColQuick'),
  chatPreviewDims:             $('chatPreviewDims'),
  relationModal:               $('relationModal'),
  relationModalXSelect:        $('relationModalXSelect'),
  relationModalYSelect:        $('relationModalYSelect'),
  relationModalTypeSelect:     $('relationModalTypeSelect'),
  relationModalDetails:        $('relationModalDetails'),
  relationModalConfirmBtn:     $('relationModalConfirmBtn'),
  relationModalCancelBtn:      $('relationModalCancelBtn'),
  closeRelationModalBtn:       $('closeRelationModalBtn'),
  agenticPlaceholder:          $('agenticPlaceholder'),
  agenticTabsBar:              $('agenticTabsBar'),
  agenticTabPanels:            $('agenticTabPanels'),
  btnRunAgenticPipeline:       $('btnRunAgenticPipeline'),
  sidebarMetricsBtn:           $('sidebarMetricsBtn'),
  metricsScreen:               $('metricsScreen'),
  backToDashboardBtn:          $('backToDashboardBtn'),
  metricsTableBody:            $('metricsTableBody'),
};

// ────────────────────────────────────────────────────────────────────────────
// Screen management
// ────────────────────────────────────────────────────────────────────────────
function showScreen(name) {
  ['landingScreen','runningScreen','resultsScreen','metricsScreen'].forEach(id => {
    const el = $(id);
    if (el) el.classList.toggle('active', id === name + 'Screen');
  });
  if (name !== 'results' && name !== 'metrics') {
    if (els.sidebarProjectActions) els.sidebarProjectActions.classList.add('hidden');
  } else if (name === 'results') {
    updateSidebarProjectActionsVisibility();
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Status pill
// ────────────────────────────────────────────────────────────────────────────
function setStatus(label, cls) {
  els.statusPill.textContent = label;
  els.statusPill.className = `status-pill ${cls}`;
}

// ────────────────────────────────────────────────────────────────────────────
// Toast notifications
// ────────────────────────────────────────────────────────────────────────────
function toast(msg, type = 'info', durationMs = 3500) {
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.textContent = msg;
  els.toastContainer.appendChild(t);
  setTimeout(() => t.remove(), durationMs);
}

// ────────────────────────────────────────────────────────────────────────────
// Custom Dialog (Alert / Confirm / Prompt)
// ────────────────────────────────────────────────────────────────────────────
function showCustomDialog({ title, message, type = 'confirm', placeholder = '', defaultValue = '' }) {
  return new Promise((resolve) => {
    const modal = els.customDialogModal;
    const titleEl = els.customDialogTitle;
    const messageEl = els.customDialogMessage;
    const promptContainer = els.customDialogPromptContainer;
    const inputEl = els.customDialogInput;
    const cancelBtn = els.customDialogCancelBtn;
    const confirmBtn = els.customDialogConfirmBtn;
    const closeBtn = els.closeCustomDialogBtn;

    titleEl.textContent = title || (type === 'confirm' ? 'Confirm' : type === 'prompt' ? 'Input Required' : 'Alert');
    messageEl.textContent = message || '';

    if (type === 'prompt') {
      promptContainer.classList.remove('hidden');
      inputEl.value = defaultValue;
      inputEl.placeholder = placeholder;
    } else {
      promptContainer.classList.add('hidden');
    }

    if (type === 'alert') {
      cancelBtn.classList.add('hidden');
      confirmBtn.textContent = 'OK';
    } else {
      cancelBtn.classList.remove('hidden');
      confirmBtn.textContent = type === 'confirm' ? 'Confirm' : 'Submit';
    }

    modal.classList.remove('hidden');
    if (type === 'prompt') {
      setTimeout(() => inputEl.focus(), 50);
    }

    function cleanup() {
      modal.classList.add('hidden');
      confirmBtn.removeEventListener('click', onConfirm);
      cancelBtn.removeEventListener('click', onCancel);
      closeBtn.removeEventListener('click', onCancel);
      inputEl.removeEventListener('keydown', onKeyDown);
      modal.removeEventListener('click', onBackdropClick);
    }

    function onConfirm() {
      const val = type === 'prompt' ? inputEl.value : true;
      cleanup();
      resolve(val);
    }

    function onCancel() {
      cleanup();
      resolve(type === 'prompt' ? null : false);
    }

    function onKeyDown(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        onConfirm();
      } else if (e.key === 'Escape') {
        e.preventDefault();
        onCancel();
      }
    }

    function onBackdropClick(e) {
      if (e.target === modal) {
        onCancel();
      }
    }

    confirmBtn.addEventListener('click', onConfirm);
    cancelBtn.addEventListener('click', onCancel);
    closeBtn.addEventListener('click', onCancel);
    inputEl.addEventListener('keydown', onKeyDown);
    modal.addEventListener('click', onBackdropClick);
  });
}

function customConfirm(message, title = 'Confirm') {
  return showCustomDialog({ title, message, type: 'confirm' });
}

function customPrompt(message, defaultValue = '', placeholder = '', title = 'Input Required') {
  return showCustomDialog({ title, message, type: 'prompt', defaultValue, placeholder });
}

function customAlert(message, title = 'Alert') {
  return showCustomDialog({ title, message, type: 'alert' });
}

// ────────────────────────────────────────────────────────────────────────────
// Fetch Ollama Models
// ────────────────────────────────────────────────────────────────────────────
async function fetchOllamaModels() {
  try {
    const customUrl = localStorage.getItem('api_url_ollama') || 'http://localhost:11434';
    const res = await fetch(`/api/ollama-models?base_url=${encodeURIComponent(customUrl)}`);
    if (res.ok) {
      const data = await res.json();
      if (data && data.models && data.models.length > 0) {
        // Prepend 'ollama/' prefix to models if not already present
        const processedModels = data.models.map(m => {
          if (!m.startsWith('ollama/')) {
            return `ollama/${m}`;
          }
          return m;
        });
        MODEL_OPTIONS.ollama = processedModels;
        return processedModels;
      }
    }
  } catch (e) {
    console.error('Failed to fetch Ollama models:', e);
  }
  return MODEL_OPTIONS.ollama; // fallback
}

// ────────────────────────────────────────────────────────────────────────────
// LLM settings persistence & Settings Modal logic
// ────────────────────────────────────────────────────────────────────────────
let ALL_PROVIDERS = [];
let litellmProvidersList = [];

function getSavedKey(provider) {
  if (provider === 'ollama') return localStorage.getItem('api_url_ollama') || 'http://localhost:11434';
  if (provider === 'custom') return localStorage.getItem('api_url_custom') || 'https://api.openai.com/v1';
  return localStorage.getItem(`api_key_${provider}`) || '';
}

function syncActiveApiKey() {
  const provider = els.llmProvider.value;
  const key = getSavedKey(provider);
  els.apiKey.value = key;
  
  const statusEl = document.getElementById('sidebarApiKeyStatus');
  if (statusEl) {
    if (provider === 'ollama' || provider === 'custom') {
      const url = getSavedKey(provider);
      statusEl.innerHTML = `<i data-lucide="link" style="width: 14px; height: 14px; color: var(--cyan);"></i> <span style="color: var(--cyan); text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 160px;">${url}</span>`;
    } else if (key) {
      statusEl.innerHTML = `<i data-lucide="check-circle" style="width: 14px; height: 14px; color: var(--emerald);"></i> <span style="color: var(--emerald);">API Key Set</span>`;
    } else {
      statusEl.innerHTML = `<i data-lucide="alert-circle" style="width: 14px; height: 14px; color: var(--amber);"></i> <span style="color: var(--amber);">API Key Not Set</span>`;
    }
    if (window.lucide) {
      lucide.createIcons({ attrs: { class: 'icon-svg' } });
    }
  }
}

function saveLlmSettings() {
  localStorage.setItem('llm_provider', els.llmProvider.value);
  localStorage.setItem('llm_model', els.llmModel.value);
}

function populateProvidersDropdown() {
  const currentVal = els.llmProvider.value || localStorage.getItem('llm_provider');
  els.llmProvider.innerHTML = '';
  let selectedExists = false;
  
  ALL_PROVIDERS.forEach(p => {
    const isShown = localStorage.getItem(`show_provider_${p}`) !== 'false';
    if (isShown) {
      const opt = document.createElement('option');
      opt.value = p; opt.textContent = p.toUpperCase();
      els.llmProvider.appendChild(opt);
      if (p === currentVal) selectedExists = true;
    }
  });

  if (selectedExists) els.llmProvider.value = currentVal;
  else if (els.llmProvider.options.length > 0) els.llmProvider.selectedIndex = 0;
}

async function loadLlmSettings() {
  try {
    const res = await fetch('/api/llm/providers');
    if (res.ok) {
      const data = await res.json();
      litellmProvidersList = data.providers || [];
      const datalist = $('providerList');
      if (datalist) {
        datalist.innerHTML = '';
        litellmProvidersList.forEach(p => {
          const opt = document.createElement('option');
          opt.value = p;
          datalist.appendChild(opt);
        });
      }
    }
  } catch (e) { console.error('Failed to fetch litellm providers', e); }

  try {
    const res = await fetch('/api/config');
    if (res.ok) {
      const backendCfg = await res.json();
      Object.keys(backendCfg).forEach(k => {
        if (k.endsWith('_API_KEY')) {
          const prov = k.replace('_API_KEY', '').toLowerCase();
          localStorage.setItem(`api_key_${prov}`, backendCfg[k]);
          if (!ALL_PROVIDERS.includes(prov)) ALL_PROVIDERS.push(prov);
        }
      });
      if (backendCfg.OLLAMA_BASE_URL) {
        localStorage.setItem('api_url_ollama', backendCfg.OLLAMA_BASE_URL);
        if (!ALL_PROVIDERS.includes('ollama')) ALL_PROVIDERS.push('ollama');
      }
      if (backendCfg.CUSTOM_BASE_URL) {
        localStorage.setItem('api_url_custom', backendCfg.CUSTOM_BASE_URL);
        if (!ALL_PROVIDERS.includes('custom')) ALL_PROVIDERS.push('custom');
      }
    }
  } catch (err) { console.warn('Failed to load config:', err); }

  if (ALL_PROVIDERS.length === 0) {
    ALL_PROVIDERS = ['openai', 'anthropic', 'gemini', 'groq', 'nvidia'];
  }

  const savedCooldown = localStorage.getItem('llm_cooldown') || '5';
  populateProvidersDropdown();
  await populateModels(els.llmProvider.value);
  els.cooldown.value = savedCooldown;
  els.cooldownVal.textContent = savedCooldown;
  syncActiveApiKey();
}

function populateSettingsModal() {
  const container = $('dynamicProvidersList');
  if (!container) return;
  container.innerHTML = '';

  ALL_PROVIDERS.forEach(p => {
    const isOllama = (p === 'ollama');
    const isCustom = (p === 'custom');
    
    let inputHtml = '';
    if (isOllama) {
      const url = localStorage.getItem('api_url_ollama') || 'http://localhost:11434';
      inputHtml = `<input type="text" id="url_${p}" class="field-input setting-key" placeholder="http://localhost:11434" value="${url}" style="flex: 1;" />`;
    } else if (isCustom) {
      const url = localStorage.getItem('api_url_custom') || 'https://api.openai.com/v1';
      const key = localStorage.getItem('api_key_custom') || '';
      inputHtml = `
        <input type="text" id="url_${p}" class="field-input setting-key" placeholder="Base URL" value="${url}" style="flex: 1;" />
        <input type="password" id="key_${p}" class="field-input setting-key" placeholder="API Key" value="${key}" style="flex: 1;" />
      `;
    } else {
      const key = localStorage.getItem(`api_key_${p}`) || '';
      inputHtml = `
        <input type="password" id="key_${p}" class="field-input setting-key" placeholder="Enter key..." value="${key}" style="flex: 1;" />
        <button class="btn-eye toggle-setting-key" title="Show/hide key" style="padding: 0 10px;">👁</button>
      `;
    }

    const isShown = localStorage.getItem(`show_provider_${p}`) !== 'false';
    const row = document.createElement('div');
    row.className = 'setting-row';
    row.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <label class="field-label" style="margin-bottom: 0; font-weight: 600;">${p.toUpperCase()} ${isOllama ? 'URL' : 'API Key'}</label>
        <label style="display: inline-flex; align-items: center; gap: 6px; font-size: 0.72rem; color: var(--text-secondary); cursor: pointer;">
          <input type="checkbox" id="show_${p}" class="setting-show-checkbox" ${isShown ? 'checked' : ''} /> Show in sidebar
        </label>
      </div>
      <div class="key-input-wrap" style="display: flex; gap: 8px;">
        ${inputHtml}
      </div>
      <div class="individual-status" id="status_${p}" style="font-size: 0.72rem; margin-top: 4px; min-height: 14px;"></div>
    `;
    container.appendChild(row);
  });
  
  container.querySelectorAll('.toggle-setting-key').forEach(btn => {
    btn.addEventListener('click', e => {
      e.preventDefault();
      const input = btn.previousElementSibling;
      if (input) input.type = input.type === 'password' ? 'text' : 'password';
    });
  });

  const cooldown = localStorage.getItem('llm_cooldown') || '5';
  els.settingsCooldown.value = cooldown;
  els.settingsCooldownVal.textContent = cooldown;
}

if ($('addProviderBtn')) {
  $('addProviderBtn').addEventListener('click', () => {
    const input = $('providerSearchInput');
    if (!input) return;
    const p = input.value.trim().toLowerCase();
    if (!p) return;
    if (!ALL_PROVIDERS.includes(p)) {
      ALL_PROVIDERS.push(p);
      localStorage.setItem(`show_provider_${p}`, 'true');
      populateSettingsModal();
      input.value = '';
    } else {
      toast('Provider already in list', 'info');
    }
  });
}

async function saveSettingsModal() {
  const promises = [];
  
  ALL_PROVIDERS.forEach(p => {
    const showCheck = $('show_' + p);
    if (showCheck) localStorage.setItem(`show_provider_${p}`, showCheck.checked ? 'true' : 'false');
    
    const fd = new FormData();
    fd.append('provider', p);
    
    if (p === 'ollama') {
      const url = $('url_' + p)?.value.trim() || '';
      localStorage.setItem('api_url_ollama', url);
      fd.append('base_url', url);
    } else if (p === 'custom') {
      const url = $('url_' + p)?.value.trim() || '';
      const key = $('key_' + p)?.value.trim() || '';
      localStorage.setItem('api_url_custom', url);
      localStorage.setItem('api_key_custom', key);
      fd.append('base_url', url);
      fd.append('api_key', key);
    } else {
      const key = $('key_' + p)?.value.trim() || '';
      localStorage.setItem(`api_key_${p}`, key);
      fd.append('api_key', key);
    }
    promises.push(fetch('/api/config', { method: 'POST', body: fd }));
  });

  await Promise.allSettled(promises);
  
  const cooldown = els.settingsCooldown.value;
  localStorage.setItem('llm_cooldown', cooldown);
  els.cooldown.value = cooldown;
  els.cooldownVal.textContent = cooldown;

  populateProvidersDropdown();
  syncActiveApiKey();
  toast('Settings saved permanently!', 'success');
  els.settingsModal.classList.add('hidden');
}

if (els.sidebarSettingsBtn) {
  els.sidebarSettingsBtn.addEventListener('click', () => {
    try {
      populateSettingsModal();
    } catch (e) {
      if (typeof toast === 'function') {
        toast('Error in settings: ' + e.message, 'error');
      } else {
        alert('Error: ' + e.message);
      }
    }
    els.settingsModal.classList.remove('hidden');
  });
}
if (els.closeSettingsModal) {
  els.closeSettingsModal.addEventListener('click', () => els.settingsModal.classList.add('hidden'));
}
if (els.cancelSettingsBtn) {
  els.cancelSettingsBtn.addEventListener('click', () => els.settingsModal.classList.add('hidden'));
}
if (els.settingsModal) {
  els.settingsModal.addEventListener('click', e => {
    if (e.target === els.settingsModal) els.settingsModal.classList.add('hidden');
  });
}
if (els.saveSettingsBtn) {
  els.saveSettingsBtn.addEventListener('click', saveSettingsModal);
}
if (els.settingsCooldown) {
  els.settingsCooldown.addEventListener('input', () => {
    els.settingsCooldownVal.textContent = els.settingsCooldown.value;
  });
}

// ────────────────────────────────────────────────────────────────────────────
// LLM Provider & Model selector
// ────────────────────────────────────────────────────────────────────────────
// Substrings that identify non-text models (voice, image, embedding, etc.)
const _EXCLUDE_MODEL_PATTERNS = [
  'tts', 'whisper', 'audio', 'speech', 'realtime',
  'dall-e', 'stable-diffusion', 'imagen', 'image-generation',
  'embed', 'ada-002', 'text-embedding', 'search-',
  'moderation', 'content-filter', 'shield',
  'code-davinci', 'code-cushman', 'davinci-edit', 'text-davinci-edit',
  'text-ada', 'text-babbage', 'text-curie',
  'babbage-002', 'davinci-002',
  'text-davinci-001', 'text-davinci-002', 'text-davinci-003',
  'computer-use', 'ft:davinci', 'ft:babbage', 'ft:curie', 'ft:ada',
  'transcription', 'translation',
];
function _isTextModel(name) {
  const low = name.toLowerCase();
  return !_EXCLUDE_MODEL_PATTERNS.some(pat => low.includes(pat));
}

async function populateModels(provider) {
  if (!provider) return;
  const listEl = $('modelList');
  if (!listEl) return;
  
  listEl.innerHTML = '';
  els.llmModel.value = 'Fetching...';
  
  try {
    const key = getSavedKey(provider);
    const res = await fetch(`/api/llm/providers/${provider}/models?api_key=${encodeURIComponent(key)}`);
    let models = [];
    if (res.ok) {
      const data = await res.json();
      models = data.models || [];
    }
    
    // Merge with hardcoded MODEL_OPTIONS to ensure robust model lists (e.g. nvidia text models)
    if (typeof MODEL_OPTIONS !== 'undefined' && MODEL_OPTIONS[provider]) {
      models = [...new Set([...MODEL_OPTIONS[provider], ...models])];
    }

    // Filter: keep only text-to-text chat/completion models
    models = models.filter(_isTextModel);
    
    // Allow custom models typed by user to be saved locally
    const saved = localStorage.getItem('llm_model');
    if (saved && provider === localStorage.getItem('llm_provider')) {
      if (!models.includes(saved)) {
        models.unshift(saved); // Make sure the user's custom saved model is in the list
      }
    }
    
    models.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      listEl.appendChild(opt);
    });
    
    if (saved && provider === localStorage.getItem('llm_provider')) {
      els.llmModel.value = saved;
    } else {
      els.llmModel.value = models.length ? models[0] : '';
    }
  } catch (e) {
    els.llmModel.value = '';
  }
}

els.llmProvider.addEventListener('change', async () => {
  await populateModels(els.llmProvider.value);
  syncActiveApiKey();
  saveLlmSettings();
});
els.llmModel.addEventListener('change', () => {
  saveLlmSettings();
});
els.llmModel.addEventListener('input', () => {
  saveLlmSettings();
});


// ────────────────────────────────────────────────────────────────────────────
// Sidebar collapse
// ────────────────────────────────────────────────────────────────────────────
els.sidebarToggle.addEventListener('click', () => {
  const collapsed = els.sidebar.classList.toggle('collapsed');
  els.sidebarToggle.innerHTML = collapsed 
    ? '<i data-lucide="chevron-right" style="width: 16px; height: 16px;"></i>'
    : '<i data-lucide="chevron-left" style="width: 16px; height: 16px;"></i>';
  if (window.lucide) lucide.createIcons();
});
els.mobileSidebarBtn.addEventListener('click', () => {
  els.sidebar.classList.toggle('mobile-open');
});

// ────────────────────────────────────────────────────────────────────────────
// Test LLM Connection
// ────────────────────────────────────────────────────────────────────────────
els.testConnectionBtn.addEventListener('click', async () => {
  const provider = els.llmProvider.value;
  const model    = els.llmModel.value;
  const apiKey   = els.apiKey.value.trim();

  els.connectionStatus.className = 'connection-status loading';
  els.connectionStatus.textContent = 'Testing…';

  const fd = new FormData();
  fd.append('provider', provider);
  fd.append('model', model);
  fd.append('api_key', apiKey);

  try {
    const res = await fetch('/api/validate-key', { method: 'POST', body: fd });
    if (res.ok) {
      els.connectionStatus.className = 'connection-status ok';
      els.connectionStatus.textContent = '✓ Connection successful';
      toast('LLM connection verified!', 'success');
    } else {
      const data = await res.json().catch(() => ({}));
      els.connectionStatus.className = 'connection-status error';
      els.connectionStatus.textContent = '✗ ' + (data.detail || 'Connection failed');
    }
  } catch (e) {
    els.connectionStatus.className = 'connection-status error';
    els.connectionStatus.textContent = '✗ Network error';
  }
});

// ────────────────────────────────────────────────────────────────────────────
// Projects sidebar & Local Storage Tracking
// ────────────────────────────────────────────────────────────────────────────
function getMyProjects() {
  try {
    return JSON.parse(localStorage.getItem('owned_projects') || '[]');
  } catch {
    return [];
  }
}

function addMyProject(id) {
  const projects = getMyProjects();
  if (!projects.includes(id)) {
    projects.push(id);
    localStorage.setItem('owned_projects', JSON.stringify(projects));
  }
}

function removeMyProject(id) {
  let projects = getMyProjects();
  projects = projects.filter(p => p !== id);
  localStorage.setItem('owned_projects', JSON.stringify(projects));
}

async function loadProjects() {
  try {
    const res = await fetch('/api/projects');
    const allProjects = await res.json();
    const myProjectIds = getMyProjects();
    state.projects = allProjects.filter(p => myProjectIds.includes(p.id));
    renderProjectsList();
  } catch {
    // Server not ready yet, retry
    setTimeout(loadProjects, 2000);
  }
}

function formatBytes(bytes) {
  if (!bytes) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function renderProjectsList() {
  // 1. Render sidebar list
  const list = els.projectsList;
  if (list) {
    if (!state.projects.length) {
      list.innerHTML = '<div class="projects-empty">No projects yet.<br>Upload a CSV to begin.</div>';
    } else {
      list.innerHTML = '';
      state.projects.forEach(p => {
        const item = document.createElement('div');
        item.className = `project-item ${state.activeProject?.id === p.id ? 'active' : ''}`;
        item.dataset.id = p.id;
        item.innerHTML = `
          <div class="project-dot ${p.status}"></div>
          <div class="project-name" title="${p.name}">${p.name}</div>
          <button class="project-del" title="Delete project" data-id="${p.id}">✕</button>
        `;
        item.addEventListener('click', e => {
          if (e.target.classList.contains('project-del')) return;
          switchToProject(p);
        });
        item.querySelector('.project-del').addEventListener('click', e => {
          e.stopPropagation();
          deleteProject(p.id);
        });
        list.appendChild(item);
      });
    }
  }

  // 2. Render dashboard projects section
  const dbGrid = els.dashboardProjectsGrid;
  const dbCount = els.dashboardProjectsCount;
  
  if (dbGrid && dbCount) {
    dbCount.textContent = `(${state.projects.length})`;
    
    if (!state.projects.length) {
      dbGrid.innerHTML = `
        <div class="projects-empty-card">
          <div class="empty-card-icon"><i data-lucide="folder-open" style="width: 48px; height: 48px; color: var(--violet-light);"></i></div>
          <div class="empty-card-title">No projects yet</div>
          <div class="empty-card-desc">Upload a CSV dataset above to start your first agentic analysis.</div>
        </div>
      `;
    } else {
      dbGrid.innerHTML = '';
      state.projects.forEach(p => {
        const card = document.createElement('div');
        card.className = `dashboard-project-card ${state.activeProject?.id === p.id ? 'active' : ''}`;
        card.dataset.id = p.id;

        const d = p.created_at ? new Date(p.created_at) : new Date();
        const pad = (n) => String(n).padStart(2, '0');
        const formattedDate = `${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;

        const sizeStr = formatBytes(p.size);
        
        card.innerHTML = `
          <div class="db-project-card-header">
            <span class="db-project-date">${formattedDate}</span>
            <span class="db-project-status-badge ${p.status}">${p.status}</span>
          </div>
          <div class="db-project-preview-wrap">
            <img src="${p.thumbnail || DEFAULT_THUMBNAIL_SVG}" class="db-project-preview-img" alt="Project Preview" onerror="this.onerror=null; this.src=DEFAULT_THUMBNAIL_SVG;" />
            <div class="db-project-preview-overlay">
              <div class="db-project-folder-icon ${p.status}">
                <svg viewBox="0 0 24 24" class="folder-svg" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
            </div>
          </div>
          <h3 class="db-project-card-title" title="${p.name}">${p.name}</h3>
          <div class="db-project-card-footer">
            <span>SIZE: ${sizeStr}</span>
            <span class="db-project-filename" title="${p.filename || 'dataset.csv'}">${p.filename || 'dataset.csv'}</span>
          </div>
          <button class="db-project-btn-del" title="Delete project">✕</button>
        `;

        card.addEventListener('click', e => {
          if (e.target.classList.contains('db-project-btn-del')) return;
          switchToProject(p);
        });

        card.querySelector('.db-project-btn-del').addEventListener('click', e => {
          e.stopPropagation();
          deleteProject(p.id);
        });

        dbGrid.appendChild(card);
      });
    }
  }
}

async function refreshPreviewData(sessionId) {
  try {
    const res = await fetch(`/api/projects/${sessionId}/preview`);
    if (res.ok) {
      const data = await res.json();
      state.columns = data.columns || [];
      state.colTypes = data.col_types || {};
      renderPreview(data.preview || []);
      if (els.chatPreviewDims) {
        els.chatPreviewDims.textContent = `(${data.rows_count?.toLocaleString() || 0} rows × ${data.cols_count || 0} columns)`;
      }
    }
  } catch (e) {
    console.error('Failed to load dynamic preview:', e);
  }
}

function updateSidebarProjectActionsVisibility(sec) {
  const isProjectCompleted = state.activeProject && state.activeProject.status === 'completed';
  if (els.sidebarProjectActions) {
    if (isProjectCompleted) {
      els.sidebarProjectActions.classList.remove('hidden');
    } else {
      els.sidebarProjectActions.classList.add('hidden');
    }
  }
}

let preChatSidebarCollapsed = false;

function switchSection(sec) {
  const resultsScreen = document.getElementById('resultsScreen');
  if (sec === 'chat') {
    els.btnSectionChat.classList.add('active');
    els.btnSectionAgentic.classList.remove('active');
    els.areaChat.classList.remove('hidden');
    els.areaAgentic.classList.add('hidden');
    
    els.btnSectionChat.style.background = 'var(--violet)';
    els.btnSectionChat.style.color = '#fff';
    els.btnSectionAgentic.style.background = 'transparent';
    els.btnSectionAgentic.style.color = 'var(--text-secondary)';

    if (resultsScreen) resultsScreen.classList.add('ai-chat-mode');
    
    // Auto-collapse sidebar for full screen chat view
    preChatSidebarCollapsed = els.sidebar.classList.contains('collapsed');
    if (!preChatSidebarCollapsed) {
      els.sidebar.classList.add('collapsed');
      if (els.sidebarToggle) els.sidebarToggle.textContent = '›';
    }
  } else {
    els.btnSectionChat.classList.remove('active');
    els.btnSectionAgentic.classList.add('active');
    els.areaChat.classList.add('hidden');
    els.areaAgentic.classList.remove('hidden');
    
    els.btnSectionAgentic.style.background = 'var(--violet)';
    els.btnSectionAgentic.style.color = '#fff';
    els.btnSectionChat.style.background = 'transparent';
    els.btnSectionChat.style.color = 'var(--text-secondary)';

    if (resultsScreen) resultsScreen.classList.remove('ai-chat-mode');
    
    // Restore sidebar state when exiting chat mode
    if (preChatSidebarCollapsed === false && els.sidebar.classList.contains('collapsed')) {
      els.sidebar.classList.remove('collapsed');
      if (els.sidebarToggle) els.sidebarToggle.textContent = '‹';
    }
  }
  // Resize Plotly charts when switching to agentic area
  if (sec === 'agentic') {
    setTimeout(() => Plotly.Plots?.resize?.(), 100);
  }
  updateSidebarProjectActionsVisibility(sec);

  if (window.lucide) {
    lucide.createIcons({ attrs: { class: 'icon-svg' } });
  }
}

async function switchToProject(p) {
  state.activeProject = p;
  renderProjectsList();
  setBreadcrumb(p.name);
  setStatus('● Loading…', 'running');
  updateSidebarProjectActionsVisibility();

  if (p.status === 'completed') {
    if (els.agenticPlaceholder) els.agenticPlaceholder.classList.add('hidden');
    if (els.agenticTabsBar) els.agenticTabsBar.classList.remove('hidden');
    if (els.agenticTabPanels) els.agenticTabPanels.classList.remove('hidden');
    await loadResults(p.id);
    goToWorkspaceHub();
  } else if (p.status === 'running') {
    if (els.agenticPlaceholder) els.agenticPlaceholder.classList.add('hidden');
    if (els.agenticTabsBar) els.agenticTabsBar.classList.remove('hidden');
    if (els.agenticTabPanels) els.agenticTabPanels.classList.remove('hidden');
    showScreen('running');
    els.runningTitle.textContent = `Analysing "${p.name}"…`;
    setStatus('● Running', 'running');
    startSSEStream(p.id);
  } else {
    // Idle state
    if (els.agenticPlaceholder) els.agenticPlaceholder.classList.remove('hidden');
    if (els.agenticTabsBar) els.agenticTabsBar.classList.add('hidden');
    if (els.agenticTabPanels) els.agenticTabPanels.classList.add('hidden');

    state.results = null;
    await refreshPreviewData(p.id);
    setupExport(p.id);
    resetChat();
    goToWorkspaceHub();
    showScreen('results');
    setStatus('● Idle', 'idle');
  }
}

async function deleteProject(id) {
  const confirmed = await customConfirm('Delete this project and all its data? This action cannot be undone.', 'Delete Project');
  if (!confirmed) return;
  delete state.resultsCache[id];
  await fetch(`/api/projects/${id}`, { method: 'DELETE' });
  removeMyProject(id);
  if (state.activeProject?.id === id) {
    state.activeProject = null;
    showScreen('landing');
    setStatus('● Idle', 'idle');
  }
  loadProjects();
  toast('Project deleted.', 'info');
}

// ────────────────────────────────────────────────────────────────────────────
// Wizard Setup & Navigation
// ────────────────────────────────────────────────────────────────────────────
function resetWizardState() {
  state.newProjectName = '';
  if (els.wizardProjectName) {
    const d = new Date();
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    els.wizardProjectName.value = `Analysis - ${d.getDate()} ${months[d.getMonth()]}`;
  }
  const s1 = $('modalStep1');
  const s2 = $('modalStep2');
  if (s1) {
    s1.style.display = 'flex';
    s1.classList.add('active');
  }
  if (s2) {
    s2.style.display = 'none';
    s2.classList.remove('active');
  }
  if (els.uploadedFileMeta) els.uploadedFileMeta.classList.add('hidden');
  if (els.uploadedFileActions) els.uploadedFileActions.classList.add('hidden');
}

// Import Project ZIP flow
const importProjectModal = $('importProjectModal');
if (els.importProjectCard && importProjectModal) {
  els.importProjectCard.addEventListener('click', () => {
    importProjectModal.classList.remove('hidden');
  });
}
const closeImportModal = $('closeImportModal');
if (closeImportModal && importProjectModal) {
  closeImportModal.addEventListener('click', () => {
    importProjectModal.classList.add('hidden');
  });
}
if (importProjectModal) {
  importProjectModal.addEventListener('click', (e) => {
    if (e.target === importProjectModal) importProjectModal.classList.add('hidden');
  });
}
const importZipZone = $('importZipZone');
if (importZipZone && els.importZipFileInput) {
  importZipZone.addEventListener('click', () => {
    els.importZipFileInput.click();
  });
  ['dragover','dragleave','drop'].forEach(evt => {
    importZipZone.addEventListener(evt, e => {
      e.preventDefault();
      if (evt === 'dragover') importZipZone.classList.add('drag-over');
      else {
        importZipZone.classList.remove('drag-over');
        if (evt === 'drop' && e.dataTransfer.files[0]) {
          const zipFile = e.dataTransfer.files[0];
          if (!zipFile.name.endsWith('.zip')) {
            toast('Only ZIP files are supported.', 'error');
            return;
          }
          // Set file field programmatically
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(zipFile);
          els.importZipFileInput.files = dataTransfer.files;
          els.importZipFileInput.dispatchEvent(new Event('change'));
        }
      }
    });
  });
}

if (els.importZipFileInput) {
  
  els.importZipFileInput.addEventListener('change', async () => {
    const file = els.importZipFileInput.files[0];
    if (!file) return;
    if (!file.name.endsWith('.zip')) {
      toast('Only ZIP files are supported.', 'error');
      return;
    }
    
    setStatus('● Importing…', 'running');
    const fd = new FormData();
    fd.append('file', file);
    
    try {
      const res = await fetch('/api/projects/import-zip', { method: 'POST', body: fd });
      if (!res.ok) throw new Error((await res.json()).detail || 'Import failed');
      const data = await res.json();
      toast(`Project imported successfully: ${data.name}`, 'success');
      addMyProject(data.id);
      if (importProjectModal) importProjectModal.classList.add('hidden');
      
      // Reset input
      els.importZipFileInput.value = '';
      
      // Reload projects and open the imported project
      await loadProjects();
      const importedProj = state.projects.find(p => p.id === data.id);
      if (importedProj) {
        switchToProject(importedProj);
      } else {
        goToDashboardHome();
      }
    } catch (e) {
      toast('Import failed: ' + e.message, 'error');
      setStatus('● Idle', 'idle');
      els.importZipFileInput.value = '';
    }
  });
}

// Wire wizard events inside newProjectModal
const newProjectModal = $('newProjectModal');
if (els.startWizardCard && newProjectModal) {
  els.startWizardCard.addEventListener('click', () => {
    newProjectModal.classList.remove('hidden');
    resetWizardState();
    if (els.wizardProjectName) {
      setTimeout(() => els.wizardProjectName.focus(), 150);
    }
  });
}

const closeNewProjectModal = $('closeNewProjectModal');
if (closeNewProjectModal && newProjectModal) {
  closeNewProjectModal.addEventListener('click', () => {
    newProjectModal.classList.add('hidden');
  });
}
if (newProjectModal) {
  newProjectModal.addEventListener('click', (e) => {
    if (e.target === newProjectModal) newProjectModal.classList.add('hidden');
  });
}

if (els.wizardNextBtn) {
  els.wizardNextBtn.addEventListener('click', () => {
    const name = els.wizardProjectName.value.trim();
    if (!name) {
      toast('Please enter a project name.', 'warning');
      els.wizardProjectName.focus();
      return;
    }
    state.newProjectName = name;
    state.newProjectReportTitle = els.wizardReportTitle ? els.wizardReportTitle.value.trim() : '';
    state.newProjectGoal = els.wizardProjectGoal ? els.wizardProjectGoal.value.trim() : '';
    
    if (els.wizardUploadTitle) {
      els.wizardUploadTitle.innerHTML = `Upload CSV for <strong>${escHtml(name)}</strong>`;
    }
    if (els.reportTitle) {
      els.reportTitle.value = state.newProjectReportTitle || `${name} Executive Analysis`;
    }
    
    const s1 = $('modalStep1');
    const s2 = $('modalStep2');
    if (s1) {
      s1.style.display = 'none';
      s1.classList.remove('active');
    }
    if (s2) {
      s2.style.display = 'flex';
      s2.classList.add('active');
    }
  });
}

if (els.wizardBackBtn) {
  els.wizardBackBtn.addEventListener('click', () => {
    const s1 = $('modalStep1');
    const s2 = $('modalStep2');
    if (s1) {
      s1.style.display = 'flex';
      s1.classList.add('active');
    }
    if (s2) {
      s2.style.display = 'none';
      s2.classList.remove('active');
    }
  });
}

function goToDashboardHome() {
  resetWizardState();
  showScreen('landing');
  state.uploadedFile = null;
  state.uploadedSession = null;
  state.activeProject = null;
  if (els.fileInput) els.fileInput.value = '';
  setBreadcrumb('New Project');
  renderProjectsList();
}

window.goToDashboardHome = goToDashboardHome;

if (els.sidebarLogo) {
  els.sidebarLogo.addEventListener('click', () => {
    goToDashboardHome();
  });
}

if (els.newProjectBtn) {
  els.newProjectBtn.addEventListener('click', () => {
    goToDashboardHome();
  });
}

function goToWorkspaceHub() {
  const p = state.activeProject;
  if (!p) return;
  
  // Hide sections switcher
  if (els.btnSectionChat && els.btnSectionChat.parentNode) {
    els.btnSectionChat.parentNode.classList.add('hidden');
  }
  
  // Show areaHub, hide areaChat and areaAgentic
  if (els.areaHub) els.areaHub.classList.remove('hidden');
  if (els.areaChat) els.areaChat.classList.add('hidden');
  if (els.areaAgentic) els.areaAgentic.classList.add('hidden');
  
  if (els.resultsScreen) els.resultsScreen.classList.remove('ai-chat-mode');
  
  // Restore sidebar state when exiting chat mode
  if (preChatSidebarCollapsed === false && els.sidebar.classList.contains('collapsed')) {
    els.sidebar.classList.remove('collapsed');
    if (els.sidebarToggle) els.sidebarToggle.textContent = '‹';
  }
  
  setBreadcrumb(p.name);
}
window.goToWorkspaceHub = goToWorkspaceHub;

function setBreadcrumb(name, activeSection = '') {
  if (!activeSection) {
    els.breadcrumb.innerHTML = `
      <span class="breadcrumb-item" onclick="goToDashboardHome()" style="cursor:pointer">Dashboard</span>
      <span class="breadcrumb-sep">›</span>
      <span class="breadcrumb-item active">${escHtml(name)}</span>
    `;
  } else {
    els.breadcrumb.innerHTML = `
      <span class="breadcrumb-item" onclick="goToDashboardHome()" style="cursor:pointer">Dashboard</span>
      <span class="breadcrumb-sep">›</span>
      <span class="breadcrumb-item" onclick="goToWorkspaceHub()" style="cursor:pointer">${escHtml(name)}</span>
      <span class="breadcrumb-sep">›</span>
      <span class="breadcrumb-item active">${escHtml(activeSection)}</span>
    `;
  }
}

// ────────────────────────────────────────────────────────────────────────────
// File Upload
// ────────────────────────────────────────────────────────────────────────────
['dragover','dragleave','drop'].forEach(evt => {
  els.uploadZone.addEventListener(evt, e => {
    e.preventDefault();
    if (evt === 'dragover') els.uploadZone.classList.add('drag-over');
    else {
      els.uploadZone.classList.remove('drag-over');
      if (evt === 'drop' && e.dataTransfer.files[0]) handleFileSelected(e.dataTransfer.files[0]);
    }
  });
});
els.uploadZone.addEventListener('click', () => els.fileInput.click());
els.fileInput.addEventListener('change', () => {
  if (els.fileInput.files[0]) handleFileSelected(els.fileInput.files[0]);
});

async function handleFileSelected(file) {
  if (!file.name.endsWith('.csv')) { toast('Only CSV files are supported.', 'error'); return; }
  state.uploadedFile = file;

  // Create project immediately via projects endpoint
  const fd = new FormData();
  fd.append('name', state.newProjectName || file.name.replace(/\.csv$/i, ''));
  fd.append('report_title', state.newProjectReportTitle || '');
  fd.append('goal', state.newProjectGoal || '');
  fd.append('file', file);

  try {
    const res  = await fetch('/api/projects', { method: 'POST', body: fd });
    const data = await res.json();
    state.uploadedSession = data.id;

    els.uploadedFileMeta.textContent = `✓ ${file.name} — ${(file.size / 1024).toFixed(1)} KB uploaded`;
    els.uploadedFileMeta.classList.remove('hidden');
    els.uploadedFileActions.classList.remove('hidden');
    toast(`Project created: ${state.newProjectName || data.name}`, 'success');
    addMyProject(data.id);
    
    // Do NOT auto-enter project here. Wait for user to click "Create Project" button.
  } catch (e) {
    toast('Project creation failed: ' + e.message, 'error');
  }
}

// ────────────────────────────────────────────────────────────────────────────
// API Warning and Validation
// ────────────────────────────────────────────────────────────────────────────
function checkApiKeySet() {
  const provider = els.llmProvider.value;
  const apiKey = els.apiKey.value.trim();
  if (provider !== 'ollama' && !apiKey) {
    const providerNames = {
      nvidia: 'NVIDIA NIM',
      groq: 'Groq',
      openai: 'OpenAI',
      anthropic: 'Anthropic',
      gemini: 'Google Gemini',
      mistral: 'Mistral',
      huggingface: 'HuggingFace',
    };
    els.warningProviderName.textContent = providerNames[provider] || provider.toUpperCase();
    els.apiWarningModal.classList.remove('hidden');
    return false;
  }
  return true;
}

// API Warning Modal Event Listeners
if (els.closeApiWarningBtn) {
  els.closeApiWarningBtn.addEventListener('click', () => {
    els.apiWarningModal.classList.add('hidden');
  });
}
if (els.apiWarningModal) {
  els.apiWarningModal.addEventListener('click', e => {
    if (e.target === els.apiWarningModal) els.apiWarningModal.classList.add('hidden');
  });
}
if (els.guideToApiBtn) {
  els.guideToApiBtn.addEventListener('click', () => {
    els.apiWarningModal.classList.add('hidden');
    els.configModal.classList.add('hidden');
    
    // Open Settings Modal
    populateSettingsModal();
    els.settingsModal.classList.remove('hidden');
    
    // Find the input element for the active provider
    const provider = els.llmProvider.value;
    let targetInput = null;
    if (provider === 'nvidia') targetInput = els.keyNvidia;
    else if (provider === 'groq') targetInput = els.keyGroq;
    else if (provider === 'openai') targetInput = els.keyOpenai;
    else if (provider === 'anthropic') targetInput = els.keyAnthropic;
    else if (provider === 'gemini') targetInput = els.keyGemini;
    else if (provider === 'mistral') targetInput = els.keyMistral;
    else if (provider === 'huggingface') targetInput = els.keyHuggingface;
    else if (provider === 'ollama') targetInput = els.urlOllama;

    if (targetInput) {
      targetInput.classList.add('highlight-glowing');
      targetInput.focus();
      
      const removeHighlight = () => {
        targetInput.classList.remove('highlight-glowing');
        targetInput.removeEventListener('input', removeHighlight);
      };
      targetInput.addEventListener('input', removeHighlight);
    }
  });
}

els.startAnalysisBtn.addEventListener('click', async () => {
  if (!state.uploadedSession) { toast('No file uploaded yet.', 'warning'); return; }
  
  const modal = $('newProjectModal');
  if (modal) modal.classList.add('hidden');
  
  resetWizardState();
  await loadProjects();
  const newProj = state.projects.find(p => p.id === state.uploadedSession);
  if (newProj) {
    switchToProject(newProj);
  }
});

// ────────────────────────────────────────────────────────────────────────────
// Config Modal
// ────────────────────────────────────────────────────────────────────────────
function openConfigModal() {
  els.configModal.classList.remove('hidden');
  const modal = $('newProjectModal');
  if (modal) modal.classList.add('hidden');
}
function closeConfigModal() {
  els.configModal.classList.add('hidden');
}
els.closeConfigModal.addEventListener('click', closeConfigModal);
els.cancelConfigBtn.addEventListener('click', closeConfigModal);
els.configModal.addEventListener('click', e => {
  if (e.target === els.configModal) closeConfigModal();
});

// ── Task card dependency logic ───────────────────────────────────────────────
function syncTaskCards() {
  const cleanChecked    = els.taskCleaning.checked;
  const relationsChecked = els.taskRelations.checked;

  // Relations & Insights require Cleaning
  if (!cleanChecked) {
    els.taskRelations.checked = false;
    els.taskInsights.checked  = false;
  }
  // Viz requires Relations
  if (!relationsChecked) {
    els.taskViz.checked = false;
  }

  // Update visual state
  [
    [els.taskCleaning,  els.taskCardCleaning,  true],
    [els.taskRelations, els.taskCardRelations,  cleanChecked],
    [els.taskInsights,  els.taskCardInsights,   cleanChecked],
    [els.taskViz,       els.taskCardViz,        els.taskRelations.checked || relationsChecked],
  ].forEach(([chk, card, enabled]) => {
    card.classList.toggle('checked',  chk.checked);
    card.classList.toggle('disabled', !enabled);
    if (!enabled) chk.checked = false;
  });
}

['taskCleaning','taskRelations','taskInsights','taskViz'].forEach(id => {
  $(id).closest('.task-card').addEventListener('click', () => {
    const chk = $(id);
    if (!$(id).closest('.task-card').classList.contains('disabled')) {
      chk.checked = !chk.checked;
      syncTaskCards();
    }
  });
});
syncTaskCards();

// ── Depth selector ───────────────────────────────────────────────────────────
$$('.depth-option').forEach(opt => {
  opt.addEventListener('click', () => {
    $$('.depth-option').forEach(o => o.classList.remove('active'));
    opt.classList.add('active');
  });
});

// ── Run button ───────────────────────────────────────────────────────────────
els.runAnalysisBtn.addEventListener('click', async () => {
  if (!checkApiKeySet()) return;
  const tasks = [];
  if (els.taskCleaning.checked)  tasks.push('cleaning');
  if (els.taskRelations.checked) tasks.push('relations');
  if (els.taskInsights.checked)  tasks.push('insights');
  if (els.taskViz.checked)       tasks.push('visualization');

  if (!tasks.length) { toast('Select at least one task.', 'warning'); return; }

  const deep = $$('.depth-option.active')[0]?.querySelector('input')?.value === 'true';

  const provider = els.llmProvider.value;
  const model    = els.llmModel.value === '__custom__' ? '' : els.llmModel.value;
  const apiKey   = els.apiKey.value.trim();
  const cooldown = parseInt(els.cooldown.value, 10);
  const title    = els.reportTitle.value.trim();

  // 1. Pre-flight Validation
  const origBtnText = els.runAnalysisBtn.innerHTML;
  els.runAnalysisBtn.disabled = true;
  els.runAnalysisBtn.innerHTML = '<span style="animation: pulse 1.2s infinite; display: inline-block;">Validating Model Connection...</span>';

  try {
    const valFd = new FormData();
    valFd.append('provider', provider);
    valFd.append('model', model);
    valFd.append('api_key', apiKey);

    const valRes = await fetch('/api/validate-key', { method: 'POST', body: valFd });
    if (!valRes.ok) {
      const errData = await valRes.json().catch(() => ({}));
      throw new Error(errData.detail || 'Model validation failed. Please check your model name and API key.');
    }
  } catch (err) {
    els.runAnalysisBtn.disabled = false;
    els.runAnalysisBtn.innerHTML = origBtnText;
    toast('Pre-flight validation failed: ' + err.message, 'error');
    return;
  }

  // 2. Start Analysis Run
  const fd = new FormData();
  fd.append('session_id',     state.uploadedSession);
  fd.append('provider',       provider);
  fd.append('model',          model);
  fd.append('api_key',        apiKey);
  fd.append('cooldown',       cooldown);
  fd.append('selected_tasks', tasks.join(','));
  fd.append('deep_analysis',  String(deep));
  fd.append('report_title',   title);

  closeConfigModal();

  // Reset button state for next time modal is opened
  els.runAnalysisBtn.disabled = false;
  els.runAnalysisBtn.innerHTML = origBtnText;

  try {
    const res = await fetch('/api/analyze', { method: 'POST', body: fd });
    if (!res.ok) throw new Error((await res.json()).detail || 'Start failed');

    // Update project metadata locally in-place (or add if new)
    const projName = title || state.uploadedFile?.name?.replace(/\.csv$/i, '') || 'New Analysis';
    delete state.resultsCache[state.uploadedSession];
    const existingIdx = state.projects.findIndex(p => p.id === state.uploadedSession);
    if (existingIdx !== -1) {
      state.projects[existingIdx].status = 'running';
      state.projects[existingIdx].name = projName;
      state.activeProject = state.projects[existingIdx];
    } else {
      const newProj = {
        id:     state.uploadedSession,
        name:   projName,
        status: 'running',
      };
      state.activeProject = newProj;
      state.projects.unshift(newProj);
    }
    renderProjectsList();
    setBreadcrumb(projName);

    showScreen('running');
    els.runningTitle.textContent = `Analysing "${projName}"…`;
    setStatus('● Running', 'running');
    startSSEStream(state.uploadedSession);
    addNotification('Analysis Started', `Pipeline triggered for "${projName}"`);
    toast('Analysis started!', 'success');
  } catch (e) {
    toast('Failed to start analysis: ' + e.message, 'error');
  }
});

// ────────────────────────────────────────────────────────────────────────────
// SSE Live Log Stream
// ────────────────────────────────────────────────────────────────────────────
const STAGE_KEYWORDS = {
  cleaning:      ['cleaning', 'cleaned', 'data clean'],
  relations:     ['relation', 'correlation'],
  insights:      ['insight', 'business'],
  visualization: ['visualization', 'png', 'chart', 'plot'],
  plotly:        ['plotly', 'interactive chart'],
};

function classifyLine(line) {
  const ll = line.toLowerCase();
  if (ll.includes('[thought]') || ll.startsWith('thought:'))    return 'thought';
  if (ll.includes('[calling tool]') || ll.startsWith('action:'))    return 'action';
  if (ll.includes('[tool response]') || ll.includes('observation:')) return 'response';
  if (ll.includes('[task]') || ll.includes('complete'))      return 'done';
  if (ll.includes('[error]') || ll.includes('error'))         return 'error';
  if (ll.includes('[warning]') || ll.includes('warning'))      return 'warning';
  return '';
}

function appendLog(line) {
  const div = document.createElement('div');
  div.className = `log-line ${classifyLine(line)}`;
  div.textContent = line;
  els.logOutput.appendChild(div);
  els.logOutput.scrollTop = els.logOutput.scrollHeight;
}

function copyLogsToResults() {
  const resultsLog = $('resultsLogOutput');
  if (!resultsLog) return;
  
  // Clone all log lines from the running screen
  resultsLog.innerHTML = '';
  const logLines = els.logOutput.querySelectorAll('.log-line');
  logLines.forEach(line => {
    resultsLog.appendChild(line.cloneNode(true));
  });
  
  // Re-init lucide icons in the new panel
  if (window.lucide) lucide.createIcons();
}

let povInterval = null;

function renderStagePov(stage) {
  if (povInterval) {
    clearInterval(povInterval);
    povInterval = null;
  }
  
  if (!els.stagePovPanel) return;

  if (stage === 'cleaning') {
    els.stagePovPanel.innerHTML = `
      <div class="pov-header">
        <div class="pov-title"><i data-lucide="brush" style="width:18px; height:18px; color:var(--violet-light); vertical-align:middle; margin-right:8px;"></i> Data Sanitizer Active</div>
        <div class="pov-desc">Scanning column profiles, auditing data formatting anomalies, and executing Python sanitization code...</div>
      </div>
      <div class="pov-content">
        <div class="pov-scanner-wrap" id="povScannerWrap">
          <div class="pov-scanner-line"></div>
          <div class="pov-scanner-row active" data-idx="0"><span>[SCAN] Reading source CSV...</span><span>SCANNING</span></div>
          <div class="pov-scanner-row" data-idx="1"><span>[AUDIT] Assessing columns for missing cells...</span><span>PENDING</span></div>
          <div class="pov-scanner-row" data-idx="2"><span>[CLEAN] Executing auto-imputation models...</span><span>PENDING</span></div>
          <div class="pov-scanner-row" data-idx="3"><span>[EXPORT] Committing sanitized dataset...</span><span>PENDING</span></div>
        </div>
      </div>`;
    
    const rows = els.stagePovPanel.querySelectorAll('.pov-scanner-row');
    let currentIdx = 0;
    povInterval = setInterval(() => {
      if (currentIdx < rows.length) {
        rows.forEach((r, idx) => {
          r.classList.toggle('active', idx === currentIdx);
          const statusCol = r.querySelectorAll('span')[1];
          if (idx < currentIdx) {
            statusCol.textContent = 'COMPLETE';
            statusCol.style.color = '#10b981';
          } else if (idx === currentIdx) {
            statusCol.textContent = 'RUNNING';
            statusCol.style.color = '#ffffff';
          } else {
            statusCol.textContent = 'PENDING';
          }
        });
        currentIdx++;
      } else {
        rows.forEach(r => {
          const statusCol = r.querySelectorAll('span')[1];
          statusCol.textContent = 'COMPLETE';
          statusCol.style.color = '#10b981';
        });
        clearInterval(povInterval);
      }
    }, 2500);

  } else if (stage === 'relations') {
    els.stagePovPanel.innerHTML = `
      <div class="pov-header">
        <div class="pov-title"><i data-lucide="link" style="width:18px; height:18px; color:var(--cyan); vertical-align:middle; margin-right:8px;"></i> Correlation Detector Engaged</div>
        <div class="pov-desc">Computing Pearson/Spearman coefficients, identifying multi-variable dependencies, and mapping relationship strengths...</div>
      </div>
      <div class="pov-content">
        <svg class="pov-chords-svg" viewBox="0 0 160 100">
          <g class="pov-chords-rotate">
            <circle cx="80" cy="50" r="30" class="pov-chord-line" stroke-dasharray="2,2"></circle>
            <circle cx="80" cy="50" r="35" class="pov-chord-line active"></circle>
            
            <circle cx="50" cy="30" r="4" class="pov-node"></circle>
            <circle cx="110" cy="30" r="4" class="pov-node"></circle>
            <circle cx="50" cy="70" r="4" class="pov-node"></circle>
            <circle cx="110" cy="70" r="4" class="pov-node"></circle>
            <circle cx="80" cy="15" r="4" class="pov-node"></circle>
            <circle cx="80" cy="85" r="4" class="pov-node"></circle>
            
            <path d="M50 30 L110 70" class="pov-chord-line active" stroke-dasharray="none"></path>
            <path d="M110 30 L50 70" class="pov-chord-line" stroke-dasharray="4,4"></path>
            <path d="M80 15 L80 85" class="pov-chord-line active" stroke-dasharray="none"></path>
          </g>
        </svg>
      </div>`;

  } else if (stage === 'insights') {
    els.stagePovPanel.innerHTML = `
      <div class="pov-header">
        <div class="pov-title"><i data-lucide="lightbulb" style="width:18px; height:18px; color:var(--amber); vertical-align:middle; margin-right:8px;"></i> Strategic Business Insights</div>
        <div class="pov-desc">Correlating discovered patterns to business implications and drafting actionable McKinsey-level recommendation strategies...</div>
      </div>
      <div class="pov-content">
        <div class="pov-insight-bulb">
          <svg class="pov-bulb-icon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
          </svg>
          <div class="pov-insight-bullets">
            <div class="pov-bullet-text">Identifying key driver columns...</div>
            <div class="pov-bullet-text">Formulating risk matrices...</div>
            <div class="pov-bullet-text">Generating recommendations...</div>
          </div>
        </div>
      </div>`;

  } else if (stage === 'visualization') {
    els.stagePovPanel.innerHTML = `
      <div class="pov-header">
        <div class="pov-title"><i data-lucide="image" style="width:18px; height:18px; color:var(--rose); vertical-align:middle; margin-right:8px;"></i> Visual Intelligence Compiler</div>
        <div class="pov-desc">Writing corporate Seaborn/Matplotlib visualization scripts and compiling high-resolution PNG plots...</div>
      </div>
      <div class="pov-content">
        <div class="pov-futuristic-dashboard">
          <div class="futuristic-stream stream-1"></div>
          <div class="futuristic-stream stream-2"></div>
          <div class="futuristic-skeleton">
            <div class="futuristic-header"></div>
            <div class="futuristic-grid">
              <div class="futuristic-card"></div>
              <div class="futuristic-card"></div>
              <div class="futuristic-card wide"></div>
            </div>
          </div>
        </div>
      </div>`;

  } else if (stage === 'plotly') {
    els.stagePovPanel.innerHTML = `
      <div class="pov-header">
        <div class="pov-title"><i data-lucide="bar-chart-3" style="width:18px; height:18px; color:var(--emerald); vertical-align:middle; margin-right:8px;"></i> Interactive Dashboard Builder</div>
        <div class="pov-desc">Building zoomable, hoverable Plotly structures and generating the final analytical results suite...</div>
      </div>
      <div class="pov-content">
        <div class="pov-plotly-grid">
          <div class="pov-skeleton-card">
            <div class="pov-skeleton-header"></div>
            <div class="pov-skeleton-body">
              <div class="pov-skeleton-bar"></div>
              <div class="pov-skeleton-bar"></div>
              <div class="pov-skeleton-bar"></div>
            </div>
          </div>
          <div class="pov-skeleton-card">
            <div class="pov-skeleton-header"></div>
            <div class="pov-skeleton-body">
              <div class="pov-skeleton-bar" style="animation-delay:0.2s"></div>
              <div class="pov-skeleton-bar" style="animation-delay:0.5s"></div>
              <div class="pov-skeleton-bar" style="animation-delay:0.8s"></div>
            </div>
          </div>
          <div class="pov-skeleton-card">
            <div class="pov-skeleton-header"></div>
            <div class="pov-skeleton-body">
              <div class="pov-skeleton-bar" style="animation-delay:0.4s"></div>
              <div class="pov-skeleton-bar" style="animation-delay:0.7s"></div>
              <div class="pov-skeleton-bar" style="animation-delay:1.0s"></div>
            </div>
          </div>
        </div>
      </div>`;
  }

  if (window.lucide) {
    lucide.createIcons();
  }
}

function markStage(stage, status) {
  const el = document.querySelector(`.stage-item[data-stage="${stage}"]`);
  if (el) {
    el.classList.remove('active','done');
    el.classList.add(status);
  }
  if (status === 'active') {
    renderStagePov(stage);
  }
}

let _activeStage = null;
const STAGE_ORDER = ['cleaning', 'relations', 'insights', 'visualization', 'plotly'];

function updateProgressTrack(newStage) {
  const newIdx = STAGE_ORDER.indexOf(newStage);
  if (newIdx === -1) return;

  const currentIdx = STAGE_ORDER.indexOf(_activeStage);
  
  // We only progress forward. If newIdx is less than or equal to currentIdx, ignore.
  if (newIdx <= currentIdx) return;

  // Mark all stages before newStage as done
  for (let i = 0; i < newIdx; i++) {
    markStage(STAGE_ORDER[i], 'done');
  }

  // Mark newStage as active
  _activeStage = newStage;
  markStage(newStage, 'active');

  // Update notification stage text
  const labels = {
    cleaning:      'Cleaning dataset...',
    relations:     'Mapping relationships...',
    insights:      'Generating BI insights...',
    visualization: 'Exporting charts...',
    plotly:        'Building Plotly charts...'
  };
  const text = labels[newStage] || 'Analysing...';
  const el = $('notifActiveJob');
  if (el) el.textContent = text;
  addNotification('Stage Transition', `Analysis transitioned to stage: ${newStage}`);
}

function inferStageFromLog(line) {
  const ll = line.toLowerCase();
  
  // First, check for explicit stage indicators from stdout!
  if (ll.includes('[stage 1/4]') || ll.includes('running data cleaner') || ll.includes('data clean')) {
    return 'cleaning';
  }
  if (ll.includes('[stage 2/4]') || ll.includes('running relation analyst') || ll.includes('relation analyst + bi analyst')) {
    return 'relations';
  }
  if (ll.includes('running bi analyst') || ll.includes('business intelligence analyst') || ll.includes('generating recommendations') || ll.includes('insights complete')) {
    return 'insights';
  }
  if (ll.includes('[stage 3/4]') || ll.includes('running data visualizer') || ll.includes('visualization complete')) {
    return 'visualization';
  }
  if (ll.includes('[stage 4/4]') || ll.includes('building interactive plotly charts') || ll.includes('plotly_charts') || ll.includes('interactive chart')) {
    return 'plotly';
  }

  // Fallback to keywords but with strict boundary matching / ordering
  for (const stage of STAGE_ORDER) {
    const keywords = STAGE_KEYWORDS[stage];
    if (keywords.some(k => {
      if (k === 'chart' || k === 'plot') {
        return ll.includes(k) && !ll.includes('plotly');
      }
      return ll.includes(k);
    })) {
      return stage;
    }
  }
  return null;
}

function startSSEStream(sessionId) {
  // Close any existing stream
  if (state.sseSource) { state.sseSource.close(); state.sseSource = null; }

  // Reset stage indicators
  $$('.stage-item').forEach(el => el.classList.remove('active','done'));
  els.logOutput.innerHTML = '';
  _activeStage = null;

  if (povInterval) { clearInterval(povInterval); povInterval = null; }
  if (els.stagePovPanel) {
    els.stagePovPanel.innerHTML = `
      <div class="pov-initial-state">
        <div class="pov-pulse-ring"></div>
        <p>Awaiting analysis stream...</p>
      </div>`;
  }

  // Initialize and show the top-right notification toast
  const notif = $('analysisNotification');
  if (notif) {
    notif.classList.remove('hidden', 'complete');
    const notifTitle = notif.querySelector('.notif-title');
    if (notifTitle) notifTitle.textContent = 'Crewlyze Analysis Active';
    const activeJobEl = $('notifActiveJob');
    if (activeJobEl) activeJobEl.textContent = 'Initializing...';
    const timerEl = $('notifTimer');
    if (timerEl) timerEl.textContent = '00:00';
    const btnMax = $('btnMaximizeNotif');
    if (btnMax) {
      btnMax.textContent = 'View';
      btnMax.onclick = () => {
        showScreen('running');
      };
    }
  }

  // Setup the elapsed timer
  if (window.notifTimerInterval) { clearInterval(window.notifTimerInterval); }
  window.notifElapsedSeconds = 0;
  window.notifTimerInterval = setInterval(() => {
    window.notifElapsedSeconds++;
    const mins = Math.floor(window.notifElapsedSeconds / 60).toString().padStart(2, '0');
    const secs = (window.notifElapsedSeconds % 60).toString().padStart(2, '0');
    const timerEl = $('notifTimer');
    if (timerEl) timerEl.textContent = `${mins}:${secs}`;
  }, 1000);

  const src = new EventSource(`/api/analyze/stream?session_id=${sessionId}`);
  state.sseSource = src;

  src.onmessage = e => {
    const line = e.data;

    if (line === '[EOF]') {
      src.close();
      state.sseSource = null;
      // Mark all stages as done (green) on successful completion
      STAGE_ORDER.forEach(s => markStage(s, 'done'));

      // Finalize the notification toast
      if (window.notifTimerInterval) { clearInterval(window.notifTimerInterval); window.notifTimerInterval = null; }
      if (notif) {
        notif.classList.add('complete');
        const notifTitle = notif.querySelector('.notif-title');
        if (notifTitle) notifTitle.textContent = 'Analysis Completed!';
        const activeJobEl = $('notifActiveJob');
        if (activeJobEl) activeJobEl.textContent = 'Results are ready.';
        const btnMax = $('btnMaximizeNotif');
        if (btnMax) {
          btnMax.textContent = 'View Results';
          btnMax.onclick = () => {
            notif.classList.add('hidden');
            loadResults(sessionId);
          };
        }
      }

      appendLog('Analysis complete! Loading results…');
      setStatus('● Loading…', 'running');
      addNotification('Analysis Completed', 'Pipeline finished successfully!', 'success');
      setTimeout(() => loadResults(sessionId), 1500);
      return;
    }

    appendLog(line);

    // Infer stage transitions and update progress track
    const stage = inferStageFromLog(line);
    if (stage) {
      updateProgressTrack(stage);
    }
  };

  src.onerror = () => {
    src.close();
    state.sseSource = null;
    
    // Stop the timer on error
    if (window.notifTimerInterval) { clearInterval(window.notifTimerInterval); window.notifTimerInterval = null; }
    if (notif) {
      notif.classList.add('complete');
      const notifTitle = notif.querySelector('.notif-title');
      if (notifTitle) notifTitle.textContent = 'Analysis Finished';
      const activeJobEl = $('notifActiveJob');
      if (activeJobEl) activeJobEl.textContent = 'Stream finalized.';
      const btnMax = $('btnMaximizeNotif');
      if (btnMax) {
        btnMax.textContent = 'View Results';
        btnMax.onclick = () => {
          notif.classList.add('hidden');
          loadResults(sessionId);
        };
      }
    }

    addNotification('Analysis Finished', 'Pipeline stream finalized.', 'info');
    // Try to load results anyway
    setTimeout(() => loadResults(sessionId), 2000);
  };
}

els.clearLogBtn.addEventListener('click', () => { els.logOutput.innerHTML = ''; });

// ────────────────────────────────────────────────────────────────────────────
// Load & Render Results
// ────────────────────────────────────────────────────────────────────────────
async function loadResults(sessionId, retryCount = 0) {
  // Check if we have cached results for this session
  if (state.resultsCache[sessionId]) {
    const data = state.resultsCache[sessionId];
    state.results = data;
    if (data.preview && data.preview.length) {
      state.columns = Object.keys(data.preview[0]);
    }
    if (state.activeProject) state.activeProject.status = 'completed';
    setStatus('● Complete', 'complete');
    if (els.agenticPlaceholder) els.agenticPlaceholder.classList.add('hidden');
    if (els.agenticTabsBar) els.agenticTabsBar.classList.remove('hidden');
    if (els.agenticTabPanels) els.agenticTabPanels.classList.remove('hidden');
    renderDashboard(data, sessionId);
    copyLogsToResults();
    showScreen('results');
    return;
  }

  try {
    const res = await fetch(`/api/results?session_id=${sessionId}`);
    if (!res.ok) throw new Error('Results not ready');
    const data = await res.json();

    if (data.ready === false) {
      throw new Error('Results pending');
    }

    if (data.error) {
      setStatus('● Error', 'error');
      toast('Analysis failed: ' + data.error, 'error');
      if (state.activeProject) {
        state.activeProject.status = 'failed';
        loadProjects();
      }
      showScreen('landing');
      return;
    }

    // Cache the retrieved results
    state.resultsCache[sessionId] = data;

    const wasRunning = els.runningScreen.classList.contains('active');

    state.results = data;

    // Extract column info from preview
    if (data.preview && data.preview.length) {
      state.columns = Object.keys(data.preview[0]);
    }

    // Update project status
    if (state.activeProject) state.activeProject.status = 'completed';
    loadProjects();
    setStatus('● Complete', 'complete');

    if (els.agenticPlaceholder) els.agenticPlaceholder.classList.add('hidden');
    if (els.agenticTabsBar) els.agenticTabsBar.classList.remove('hidden');
    if (els.agenticTabPanels) els.agenticTabPanels.classList.remove('hidden');

    renderDashboard(data, sessionId);
    
    // Copy live agent logs to the results screen
    copyLogsToResults();
    
    if (wasRunning) {
      switchSection('agentic');
    }
    
    showScreen('results');
  } catch (e) {
    // Results not ready yet, retry up to 15 times (~37 seconds)
    if (retryCount < 15) {
      setTimeout(() => loadResults(sessionId, retryCount + 1), 2500);
    } else {
      setStatus('● Error', 'error');
      toast('Analysis failed: Server timed out producing results.', 'error');
      if (state.activeProject) {
        state.activeProject.status = 'failed';
        loadProjects();
      }
      showScreen('landing');
    }
  }
}

function renderDashboard(data, sessionId) {
  renderStats(data);
  renderPreview(data.preview || []);
  renderCleaning(data.cleaning_steps || '');
  renderRelations(data.relations || '');
  renderInsights(data.insights || '');
  renderCharts(data.plotly_charts || [], data.png_charts || [], sessionId);
  renderVizCode(data.code || '');
  setupExport(sessionId);
  resetChat();

  // Set dimensions text in Chat Preview
  if (els.chatPreviewDims) {
    els.chatPreviewDims.textContent = `(${data.rows_count?.toLocaleString() || 0} rows × ${data.cols_count || 0} columns)`;
  }
  
  // Default to AI Chat section
  switchSection('chat');

  // Activate first tab inside agentic area
  activateTab('cleaning');
}

// ── Stats row ────────────────────────────────────────────────────────────────
function renderStats(data) {
  const stats = [
    { val: (data.rows_count || 0).toLocaleString(), lbl: 'Total Records', color: 'var(--violet)' },
    { val: data.cols_count || 0, lbl: 'Total Columns', color: 'var(--cyan)' },
    { val: data.numeric_count || 0, lbl: 'Numeric Fields', color: 'var(--emerald)' },
    { val: data.cat_count || 0, lbl: 'Categorical Fields', color: 'var(--amber)' },
    { val: (data.plotly_charts || []).length, lbl: 'Interactive Charts', color: 'var(--rose)' },
  ];
  els.statsRow.innerHTML = stats.map(s => `
    <div class="stat-card" style="--accent:${s.color}">
      <div class="stat-val">${s.val}</div>
      <div class="stat-lbl">${s.lbl}</div>
      <div class="stat-accent-bar"></div>
    </div>
  `).join('');
}

// ── Data Preview ─────────────────────────────────────────────────────────────
function renderPreview(rows) {
  if (!rows.length) {
    els.previewTable.innerHTML = '<p style="color:var(--text-muted);padding:16px">No preview data.</p>';
    return;
  }
  const cols = Object.keys(rows[0]);
  state.columns = cols;

  const thead = `<thead><tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr></thead>`;
  const tbody = `<tbody>${rows.map(row =>
    `<tr>${cols.map(c => `<td title="${row[c] ?? ''}">${row[c] ?? ''}</td>`).join('')}</tr>`
  ).join('')}</tbody>`;

  els.previewTable.innerHTML = `<table class="data-table">${thead}${tbody}</table>`;
}

// Toggle preview minimize
if (els.togglePreviewBtn) {
  els.togglePreviewBtn.addEventListener('click', () => {
    state.previewMinimized = !state.previewMinimized;
    if (state.previewMinimized) {
      els.previewTableWrap.innerHTML = `
        <div class="preview-minimized">
          Preview minimized — ${state.results?.rows_count?.toLocaleString() ?? '?'} rows × ${state.columns.length} columns.
        </div>`;
      els.togglePreviewBtn.textContent = '🔼 Expand Preview';
    } else {
      els.previewTableWrap.innerHTML = '<div id="previewTable" class="data-table-container"></div>';
      renderPreview(state.results?.preview || []);
      els.togglePreviewBtn.textContent = '🔽 Minimize';
    }
  });
}

// ── Cleaning ─────────────────────────────────────────────────────────────────
function renderCleaning(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  if (!lines.length) {
    els.cleaningContent.innerHTML = '<p style="color:var(--text-muted)">No cleaning operations recorded.</p>';
    return;
  }
  els.cleaningContent.innerHTML = lines.map(l =>
    `<div class="cleaning-item">
      <div class="cleaning-check" style="display: flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 50%; background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.2);"><i data-lucide="check" style="width: 12px; height: 12px; color: var(--emerald);"></i></div>
      <div class="cleaning-text" style="flex: 1;">${escHtml(l.replace(/^[-*•]\s*/, ''))}</div>
    </div>`
  ).join('');
  
  if (window.lucide) {
    lucide.createIcons();
  }
}

// ── Relations ─────────────────────────────────────────────────────────────────
// ── Relations ─────────────────────────────────────────────────────────────────
function renderRelations(text) {
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
  
  // Parse lines into structured state.relationsList
  state.relationsList = [];
  lines.forEach(line => {
    const xMatch = line.match(/X:\s*([^|]+)/i);
    const yMatch = line.match(/Y:\s*([^|]+)/i);
    const typeMatch = line.match(/Type:\s*([^|]+)/i);
    const detailsMatch = line.match(/Details:\s*(.+)/i);

    if (xMatch && yMatch) {
      state.relationsList.push({
        xCol: xMatch[1].trim(),
        yCol: yMatch[1].trim(),
        typ: typeMatch ? typeMatch[1].trim() : 'Correlation',
        details: detailsMatch ? detailsMatch[1].trim() : 'Key relationship identified by analyst.'
      });
    }
  });

  renderRelationsListUI();
}

function renderRelationsListUI() {
  const list = state.relationsList || [];
  if (!list.length) {
    els.relationsContent.innerHTML = `
      <div style="text-align: center; padding: 24px; color: var(--text-secondary); background: var(--bg-card); border-radius: var(--r-md); border: 1px dashed var(--border-mid); width: 100%;">
        <p style="margin: 0;">No schema relationships mapped yet.</p>
      </div>`;
    return;
  }

  let html = '<div class="relation-mapper-container">';
  list.forEach((rel, index) => {
    const xType = state.colTypes[rel.xCol] || 'Numeric';
    const yType = state.colTypes[rel.yCol] || 'Numeric';

    html += `
      <div class="relation-card" style="position: relative; flex: 1 1 calc(50% - 16px); min-width: 380px; box-sizing: border-box;">
        <div class="relation-node">
          <span class="relation-node-type">${escHtml(xType)}</span>
          <strong>${escHtml(rel.xCol)}</strong>
        </div>
        
        <div class="relation-connector">
          <span style="font-size: 0.8rem; font-weight: 600; color: var(--cyan); margin-bottom: 4px;">${escHtml(rel.typ)}</span>
          <div class="relation-line"></div>
          <span class="relation-info">${escHtml(rel.details)}</span>
        </div>
        
        <div class="relation-node" style="border-color: rgba(34, 211, 238, 0.2);">
          <span class="relation-node-type" style="color: var(--cyan);">${escHtml(yType)}</span>
          <strong>${escHtml(rel.yCol)}</strong>
        </div>
      </div>
    `;
  });

  html += '</div>';
  els.relationsContent.innerHTML = html;
}

function showRelationModal(index) {
  const cols = state.columns || [];
  els.relationModalXSelect.innerHTML = cols.map(c => `<option value="${escHtml(c)}">${escHtml(c)}</option>`).join('');
  els.relationModalYSelect.innerHTML = cols.map(c => `<option value="${escHtml(c)}">${escHtml(c)}</option>`).join('');
  
  if (index !== null && state.relationsList[index]) {
    const rel = state.relationsList[index];
    els.relationModalTitle.innerHTML = '<i data-lucide="edit" style="width: 16px; height: 16px; vertical-align: middle; margin-right: 6px;"></i> Edit Relationship Schema';
    els.relationModalXSelect.value = rel.xCol;
    els.relationModalYSelect.value = rel.yCol;
    els.relationModalTypeSelect.value = rel.typ;
    els.relationModalDetails.value = rel.details;
  } else {
    els.relationModalTitle.innerHTML = '<i data-lucide="plus" style="width: 16px; height: 16px; vertical-align: middle; margin-right: 6px;"></i> Add Custom Relationship';
    if (cols.length > 1) {
      els.relationModalXSelect.selectedIndex = 0;
      els.relationModalYSelect.selectedIndex = 1;
    }
    els.relationModalTypeSelect.value = 'Scatter Plot';
    els.relationModalDetails.value = '';
  }

  els.relationModal.classList.remove('hidden');

  els.relationModalConfirmBtn.onclick = () => {
    const relObj = {
      xCol: els.relationModalXSelect.value,
      yCol: els.relationModalYSelect.value,
      typ: els.relationModalTypeSelect.value,
      details: els.relationModalDetails.value.trim() || 'Custom correlation defined by data scientist.'
    };

    if (index !== null) {
      state.relationsList[index] = relObj;
    } else {
      state.relationsList.push(relObj);
    }
    els.relationModal.classList.add('hidden');
    renderRelationsListUI();
  };

  els.relationModalCancelBtn.onclick = () => els.relationModal.classList.add('hidden');
  els.closeRelationModalBtn.onclick = () => els.relationModal.classList.add('hidden');
}

function deleteRelationAt(index) {
  state.relationsList.splice(index, 1);
  renderRelationsListUI();
  toast('Relationship removed from schema configuration.', 'info');
}

async function saveTweakedRelations() {
  const sessionId = state.activeProject?.id || state.uploadedSession;
  if (!sessionId) { toast('No active project context.', 'error'); return; }

  const textLines = state.relationsList.map(r => 
    `- X: ${r.xCol} | Y: ${r.yCol} | Type: ${r.typ} | Details: ${r.details}`
  ).join('\n');

  try {
    const fd = new FormData();
    fd.append('relations_text', textLines);

    const res = await fetch(`/api/projects/${sessionId}/tweak-relations`, {
      method: 'POST',
      body: fd
    });

    if (res.ok) {
      toast('Schema relationships committed successfully!', 'success');
      if (state.results) {
        state.results.relations = textLines;
      }
    } else {
      toast('Failed to save schema tweaks.', 'error');
    }
  } catch (e) {
    toast('Error saving schema tweaks: ' + e.message, 'error');
  }
}

// ── Insights Markdown Formatter ──────────────────────────────────────────────
function formatInlineMarkdown(content) {
  let isBullet = false;
  let cleanContent = content;
  if (/^[-*•]\s+/.test(content)) {
    isBullet = true;
    cleanContent = content.replace(/^[-*•]\s+/, '');
  }
  
  let formatted = escHtml(cleanContent)
    .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
    .replace(/`([^`]+)`/g, '<code style="background:var(--bg-surface);padding:1px 5px;border-radius:3px;font-family:var(--font-mono);font-size:0.85em">$1</code>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
  if (isBullet) {
    return `<div style="display: flex; gap: 8px; margin-left: 12px; margin-top: 4px; margin-bottom: 4px;">
              <span>•</span>
              <div>${formatted}</div>
            </div>`;
  }
  return formatted;
}

// ── Insights ─────────────────────────────────────────────────────────────────
function renderInsights(text) {
  if (!text || !text.trim() || text.toLowerCase().includes('skipped')) {
    els.insightsContent.innerHTML = '<p style="color:var(--text-muted)">No business insights generated.</p>';
    return;
  }

  // Parse sections
  let objectivesText = "";
  let statsText = "";
  let strategicText = "";
  let warningsText = "";

  const sections = text.split(/###\s+/);
  sections.forEach(sec => {
    const lines = sec.split('\n');
    if (lines.length === 0) return;
    const header = lines[0].trim().toLowerCase();
    const content = lines.slice(1).join('\n').trim();

    if (header.includes('objective') || header.includes('goal')) {
      objectivesText = content;
    } else if (header.includes('stat')) {
      statsText = content;
    } else if (header.includes('insight')) {
      strategicText = content;
    } else if (header.includes('warning') || header.includes('alert')) {
      warningsText = content;
    }
  });

  // If parsing didn't find specific sections, fallback to parsing as a single block
  if (!strategicText && !objectivesText) {
    strategicText = text;
  }

  let html = "";

  // 1. Objectives & Goals Banner
  if (objectivesText) {
    html += `
      <div class="insight-header-card">
        <div class="insight-header-title"><i data-lucide="target" style="width: 18px; height: 18px; vertical-align: middle; margin-right: 6px; color: var(--violet-light);"></i> Primary Objectives &amp; Goals</div>
        <div class="insight-header-text">${formatInsightsSubsections(objectivesText)}</div>
      </div>
    `;
  }

  // 2. Dataset Statistics Grid
  if (statsText) {
    const lines = statsText.split('\n').map(l => l.trim()).filter(Boolean);
    let summaryStats = [];
    let numericCols = [];
    let categoricalCols = [];
    
    let currentSection = "";
    
    lines.forEach(line => {
      const cleanLine = line.replace(/^[-*•]\s*/, '').trim();
      const lowerLine = cleanLine.toLowerCase();
      
      if (lowerLine.startsWith("numeric column")) {
        currentSection = "numeric";
        return;
      } else if (lowerLine.startsWith("categorical column")) {
        currentSection = "categorical";
        return;
      }
      
      const colIndex = cleanLine.indexOf(':');
      if (colIndex > -1) {
        const key = cleanLine.slice(0, colIndex).trim();
        const val = cleanLine.slice(colIndex + 1).trim();
        
        if (lowerLine.startsWith("total row") || lowerLine.startsWith("total record") || lowerLine.startsWith("total col")) {
          summaryStats.push({ key, val });
        } else {
          if (currentSection === "numeric") {
            numericCols.push({ col: key, stats: val });
          } else if (currentSection === "categorical") {
            categoricalCols.push({ col: key, stats: val });
          } else {
            if (lowerLine.includes("min") || lowerLine.includes("max") || lowerLine.includes("mean")) {
              numericCols.push({ col: key, stats: val });
            } else {
              categoricalCols.push({ col: key, stats: val });
            }
          }
        }
      } else {
        if (cleanLine) {
          if (currentSection === "numeric") {
            numericCols.push({ col: cleanLine, stats: "" });
          } else if (currentSection === "categorical") {
            categoricalCols.push({ col: cleanLine, stats: "" });
          }
        }
      }
    });

    // A. Summary Cards
    if (summaryStats.length > 0) {
      html += `<div class="insight-stats-grid" style="margin-bottom: 20px;">`;
      summaryStats.forEach(s => {
        html += `
          <div class="insight-stat-card">
            <div class="insight-stat-val">${escHtml(s.val)}</div>
            <div class="insight-stat-lbl">${escHtml(s.key)}</div>
          </div>
        `;
      });
      html += `</div>`;
    }
    
    // B. Side-by-Side Sections
    if (numericCols.length > 0 || categoricalCols.length > 0) {
      html += `
        <div style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 24px;">
          <!-- Numeric Columns -->
          <div class="card" style="flex: 1 1 calc(50% - 10px); min-width: 320px; padding: 18px; background: var(--bg-card); border: 1px solid var(--border-mid); box-sizing: border-box;">
            <h4 style="margin: 0 0 12px 0; color: var(--cyan); font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
              <i data-lucide="binary" style="width: 16px; height: 16px;"></i> Numeric Columns &amp; Distributions
            </h4>
            <div style="display: flex; flex-direction: column; gap: 10px;">
      `;
      if (numericCols.length > 0) {
        numericCols.forEach(c => {
          html += `
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed var(--border-low); padding-bottom: 8px; font-size: 0.85rem;">
              <strong style="color: #fff;">${escHtml(c.col)}</strong>
              <span style="color: var(--text-secondary); font-family: var(--font-mono); font-size: 0.8rem; text-align: right;">${escHtml(c.stats)}</span>
            </div>
          `;
        });
      } else {
        html += `<p style="color: var(--text-muted); font-size: 0.85rem; margin: 0;">None detected.</p>`;
      }
      html += `
            </div>
          </div>
          
          <!-- Categorical Columns -->
          <div class="card" style="flex: 1 1 calc(50% - 10px); min-width: 320px; padding: 18px; background: var(--bg-card); border: 1px solid var(--border-mid); box-sizing: border-box;">
            <h4 style="margin: 0 0 12px 0; color: var(--amber); font-size: 0.95rem; display: flex; align-items: center; gap: 6px;">
              <i data-lucide="tags" style="width: 16px; height: 16px;"></i> Categorical Columns
            </h4>
            <div style="display: flex; flex-direction: column; gap: 10px;">
      `;
      if (categoricalCols.length > 0) {
        categoricalCols.forEach(c => {
          const statsLabel = c.stats ? `: ${c.stats}` : '';
          html += `
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed var(--border-low); padding-bottom: 8px; font-size: 0.85rem;">
              <strong style="color: #fff;">${escHtml(c.col)}</strong>
              <span style="color: var(--text-secondary); font-family: var(--font-mono); font-size: 0.8rem;">${escHtml(statsLabel)}</span>
            </div>
          `;
        });
      } else {
        html += `<p style="color: var(--text-muted); font-size: 0.85rem; margin: 0;">None detected.</p>`;
      }
      html += `
            </div>
          </div>
        </div>
      `;
    }
  }

  // 3. Strategic Insights List
  if (strategicText) {
    html += `<h4 style="margin-bottom: 12px; color: var(--violet-light); font-size: 1.05rem; display: flex; align-items: center; gap: 6px;"><i data-lucide="lightbulb" style="width: 18px; height: 18px; color: var(--violet-light);"></i> Strategic Business Insights</h4>`;
    const numberedSplit = strategicText.split(/\n(?=\s*(?:\*{0,2}\d+[.):]\*{0,2}|#{1,3}\s))/);
    let items = [];
    if (numberedSplit.length > 1) {
      items = numberedSplit.map(s => s.replace(/^\s*(?:\*{0,2}\d+[.):]\*{0,2}|#{1,3})\s*/, '').trim()).filter(Boolean);
    } else {
      items = strategicText.split(/\n{2,}/).map(s => s.trim()).filter(Boolean);
    }

    const LABEL_CFG = [
      { re: /^(?:observation|finding|pattern)[s]?[:]/i,          cls: 'obs',   icon: 'search', label: 'Observation' },
      { re: /^(?:business\s+)?implication[s]?[:]/i,              cls: 'impl',  icon: 'briefcase', label: 'Implication' },
      { re: /^(?:actionable\s+)?strateg(?:y|ies)[:]/i,          cls: 'strat', icon: 'rocket', label: 'Strategy' },
      { re: /^(?:recommendation|action|next\s+step)[s]?[:]/i,   cls: 'strat', icon: 'check-circle', label: 'Recommendation' },
      { re: /^(?:risk|concern|warning)[s]?[:]/i,                 cls: 'impl',  icon: 'alert-triangle', label: 'Risk' },
      { re: /^(?:kpi|metric|measure)[s]?[:]/i,                   cls: 'obs',   icon: 'trending-up', label: 'Metric' },
    ];

    html += items.map((item, i) => {
      const parts = item.split('\n').map(p => p.trim()).filter(Boolean);
      const sectionHtml = parts.map(p => {
        for (const cfg of LABEL_CFG) {
          if (cfg.re.test(p)) {
            const body = p.replace(cfg.re, '').trim();
            return `<div class="insight-section">
              <div class="insight-section-label ${cfg.cls}"><i data-lucide="${cfg.icon}" style="width: 14px; height: 14px; vertical-align: middle; margin-right: 4px;"></i> ${cfg.label}</div>
              <div class="insight-section-text">${formatInlineMarkdown(body || p)}</div>
            </div>`;
          }
        }
        if (/^[-*•]/.test(p)) {
          return `<div class="insight-bullet">${formatInlineMarkdown(p)}</div>`;
        }
        if (/^#{1,3}\s/.test(p)) {
          return `<div class="insight-sub-heading">${escHtml(p.replace(/^#+\s*/, ''))}</div>`;
        }
        return `<div class="insight-section-text">${formatInlineMarkdown(p)}</div>`;
      }).join('');

      return `
        <div class="insight-card">
          <div class="insight-num-pill">${i + 1}</div>
          <div class="insight-body">${sectionHtml}</div>
        </div>
      `;
    }).join('');
  }

  // 4. Warnings & Alerts
  if (warningsText && !warningsText.toLowerCase().includes('no warnings') && !warningsText.toLowerCase().includes('none')) {
    html += `
      <div class="insight-warning-card">
        <div class="insight-warning-card-icon"><i data-lucide="alert-triangle" style="width: 24px; height: 24px; color: var(--amber);"></i></div>
        <div class="insight-warning-card-body">
          <div class="insight-warning-card-title">Business Risks &amp; Data Alerts</div>
          <div class="insight-warning-card-text">${formatInsightsSubsections(warningsText)}</div>
        </div>
      </div>
    `;
  }

  els.insightsContent.innerHTML = html;
}

function formatInsightsSubsections(text) {
  return text.split('\n').map(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith('-') || trimmed.startsWith('*')) {
      return `<div style="margin-left: 12px; margin-top: 4px; display: flex; gap: 6px;">
        <span>•</span>
        <span>${formatInlineMarkdown(trimmed.replace(/^[-*•]\s*/, ''))}</span>
      </div>`;
    }
    return `<p style="margin-top: 4px; margin-bottom: 4px;">${formatInlineMarkdown(trimmed)}</p>`;
  }).join('');
}

// ── Charts ────────────────────────────────────────────────────────────────────
function renderCharts(plotlyCharts, pngCharts, sessionId) {
  els.plotlyChartsWrap.innerHTML = '';

  if (plotlyCharts.length) {
    plotlyCharts.forEach((chart, idx) => {
      const card = document.createElement('div');
      card.className = 'chart-card';

      const typeLabel = chart.fig_json?.data?.[0]?.type || 'chart';
      card.innerHTML = `
        <div class="chart-card-header">
          <div class="chart-card-title">${escHtml(chart.title)}</div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <button class="btn-xs download-plotly-btn" data-index="${idx}" style="cursor: pointer; display: flex; align-items: center; gap: 4px; padding: 3px 8px; border: 1px solid var(--border-mid); background: var(--bg-surface); border-radius: var(--r-sm); color: var(--text-secondary);"><i data-lucide="download" style="width: 12px; height: 12px;"></i> Download</button>
            <div class="chart-card-type">${typeLabel}</div>
          </div>
        </div>
        <div class="chart-card-body">
          <div id="plotly_chart_${idx}" style="width:100%;height:380px;"></div>
        </div>`;
      els.plotlyChartsWrap.appendChild(card);

      try {
        const figData   = chart.fig_json.data   || [];
        const figLayout = chart.fig_json.layout || {};
        // Force dark theme
        figLayout.paper_bgcolor = 'rgba(9,9,11,0)';
        figLayout.plot_bgcolor  = 'rgba(15,23,42,0.4)';
        figLayout.font          = { color: '#e2e8f0', family: 'Inter, sans-serif' };
        figLayout.margin        = figLayout.margin || { l:50, r:20, t:50, b:50 };

        Plotly.newPlot(`plotly_chart_${idx}`, figData, figLayout, {
          responsive: true,
          displayModeBar: true,
          modeBarButtonsToRemove: ['toImage','sendDataToCloud'],
          displaylogo: false,
        });

        const dlBtn = card.querySelector('.download-plotly-btn');
        if (dlBtn) {
          dlBtn.addEventListener('click', () => {
            const gd = document.getElementById(`plotly_chart_${idx}`);
            if (gd) {
              Plotly.downloadImage(gd, {
                format: 'png',
                width: 1000,
                height: 600,
                filename: chart.title || 'plotly_chart'
              });
            }
          });
        }
      } catch (e) {
        card.querySelector('.chart-card-body').innerHTML =
          `<div class="chart-card-error">⚠ Could not render chart: ${escHtml(String(e))}</div>`;
      }
    });
  } else {
    els.plotlyChartsWrap.innerHTML =
      '<p style="color:var(--text-muted);padding:8px 0">No interactive charts available. Run with Relationship Analysis enabled.</p>';
  }

  // PNG charts — masonry-style grid with error fallback
  if (pngCharts.length) {
    els.pngChartsWrap.classList.remove('hidden');
    els.pngCharts.innerHTML = pngCharts.map((name, idx) => {
      const title = name.replace(/\.png$/i, '')
        .replace(/_/g, ' ')
        .replace(/\brelation\b/g, '')
        .replace(/^[a-z]/, c => c.toUpperCase())
        .trim();
      const chartUrl = `/api/charts/${sessionId}/${encodeURIComponent(name)}`;
      return `
        <div class="chart-card png-chart-card">
          <div class="chart-card-header">
            <div class="chart-card-title">${escHtml(title)}</div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <a href="${chartUrl}" download="${escHtml(name)}" class="btn-xs" style="cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border: 1px solid var(--border-mid); background: var(--bg-surface); border-radius: var(--r-sm); color: var(--text-secondary);"><i data-lucide="download" style="width: 12px; height: 12px;"></i> Download</a>
              <div class="chart-card-type">agent chart</div>
            </div>
          </div>
          <div class="chart-card-body png-chart-body">
            <img
              src="${chartUrl}"
              alt="${escHtml(title)}"
              class="png-chart-img"
              loading="lazy"
              onerror="this.parentNode.innerHTML='<div class=\'chart-img-error\'>Chart not available yet — rerun analysis to generate.</div>'"
            />
          </div>
        </div>`;
    }).join('');
  } else {
    els.pngChartsWrap.classList.add('hidden');
  }

  if (window.lucide) {
    lucide.createIcons();
  }
}

// ── Viz code ─────────────────────────────────────────────────────────────────
function renderVizCode(code) {
  els.vizCodeDetails.classList.add('hidden');
  if (code && code.trim()) {
    els.vizCodeBlock.textContent = code;
  }
}

// ── Export ────────────────────────────────────────────────────────────────────
function setupExport(sessionId) {
  const exportPdf = () => {
    window.location = `/api/export-pdf?session_id=${sessionId}`;
  };
  const exportZip = () => {
    window.location = `/api/projects/${sessionId}/export-zip`;
  };
  const downloadCsv = () => {
    window.location = `/api/projects/${sessionId}/download-csv`;
  };
  const reRun = () => {
    state.uploadedSession = sessionId;
    state.uploadedFile = { name: state.activeProject?.filename || 'dataset.csv' };
    openConfigModal();
  };

  els.exportPdfBtn.onclick = exportPdf;
  if (els.sidebarExportPdfBtn) els.sidebarExportPdfBtn.onclick = exportPdf;

  if (els.exportZipBtn) els.exportZipBtn.onclick = exportZip;
  if (els.sidebarExportZipBtn) els.sidebarExportZipBtn.onclick = exportZip;

  els.downloadCsvBtn.onclick = downloadCsv;
  if (els.sidebarDownloadCsvBtn) els.sidebarDownloadCsvBtn.onclick = downloadCsv;

  els.reRunBtn.onclick = reRun;
  if (els.sidebarReRunBtn) els.sidebarReRunBtn.onclick = reRun;
}

// ────────────────────────────────────────────────────────────────────────────
// Tabs
// ────────────────────────────────────────────────────────────────────────────
function activateTab(name) {
  els.tabBtns.forEach(btn => btn.classList.toggle('active', btn.dataset.tab === name));
  els.tabPanels.forEach(panel => panel.classList.toggle('active', panel.id === `panel-${name}`));
  if (name === 'charts') {
    setTimeout(() => {
      const chartElements = document.querySelectorAll('[id^="plotly_chart_"]');
      chartElements.forEach(el => Plotly.Plots?.resize?.(el));
    }, 100);
  }
}
els.tabBtns.forEach(btn => {
  btn.addEventListener('click', () => activateTab(btn.dataset.tab));
});

// Debounced Window Resize Plotly Listener
let resizeTimeout = null;
window.addEventListener('resize', () => {
  if (resizeTimeout) clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    const activeTabBtn = document.querySelector('.tab-btn.active');
    if (activeTabBtn && activeTabBtn.dataset.tab === 'charts') {
      const chartElements = document.querySelectorAll('[id^="plotly_chart_"]');
      chartElements.forEach(el => Plotly.Plots?.resize?.(el));
    }
  }, 200);
});

// ────────────────────────────────────────────────────────────────────────────
// AI Copilot Chat + /column picker
// ────────────────────────────────────────────────────────────────────────────
function resetChat() {
  state.chatHistory = [];
  els.chatMessages.innerHTML = '';
  // Seed with a welcome message
  appendChatMsg('assistant', `Hi! I'm your Crew Chat assistant. Ask me anything about your dataset — aggregations, trends, plots, or specific columns.\n\nType **/** to insert a column name directly.`);
}

function appendChatMsg(role, content, plotUrl = null) {
  const cleanedContent = removeFilePathInfo(content);
  const msgIdx = state.chatHistory.length;
  state.chatHistory.push({ role, content: cleanedContent, plot_url: plotUrl });

  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  
  const checkHtml = `
    <div class="chat-select-wrap">
      <input type="checkbox" class="chat-select-check" data-idx="${msgIdx}" />
    </div>
  `;

  const avatar = role === 'user' 
    ? '<i data-lucide="user" style="width: 18px; height: 18px;"></i>' 
    : '<img src="/assets/chat_logo.png" style="width: 30px; height: 30px; object-fit: contain;" />';

  let formatted = '';
  // Try to use marked.js, fallback if CDN fails
  if (typeof marked !== 'undefined') {
    formatted = marked.parse(cleanedContent);
  } else {
    formatted = escHtml(cleanedContent)
      .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
      .replace(/`([^`]+)`/g, '<code style="background:var(--bg-surface);padding:1px 5px;border-radius:3px;font-family:var(--font-mono);font-size:0.85em">$1</code>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
  }

  div.innerHTML = `
    ${checkHtml}
    <div class="chat-avatar" style="overflow: hidden; display: flex; align-items: center; justify-content: center;">${avatar}</div>
    <div class="chat-bubble markdown-body" style="position: relative;">
      ${formatted}
      ${plotUrl ? `
        <div style="position: relative; display: inline-block; max-width: 100%; margin-top: 1rem;">
          <img src="${plotUrl}" alt="Generated chart" style="border-radius:12px; border:1px solid var(--border-color); max-width:100%; box-shadow: 0 4px 15px var(--shadow-color);" />
          <a href="${plotUrl}" download style="position: absolute; bottom: 10px; right: 10px; display: flex; align-items: center; gap: 4px; padding: 4px 10px; font-size: 0.72rem; font-weight: 600; color: #fff; background: rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.15); border-radius: var(--r-sm); text-decoration: none; backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); transition: all 0.2s;"><i data-lucide="download" style="width: 12px; height: 12px;"></i> Download</a>
        </div>
      ` : ''}
    </div>`;
  els.chatMessages.appendChild(div);
  els.chatMessages.scrollTop = els.chatMessages.scrollHeight;

  if (window.lucide) {
    lucide.createIcons({ attrs: { class: 'icon-svg' } });
  }

  div.querySelector('.chat-select-check').addEventListener('change', updateExportChatPdfBtnVisibility);
}

function showTypingIndicator() {
  const div = document.createElement('div');
  div.className = 'chat-msg assistant';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="chat-select-wrap" style="visibility: hidden;">
      <input type="checkbox" class="chat-select-check" />
    </div>
    <div class="chat-avatar" style="overflow: hidden; display: flex; align-items: center; justify-content: center;"><img src="/assets/chat_logo.png" style="width: 22px; height: 22px; object-fit: contain; border-radius: 50%;" /></div>
    <div class="chat-bubble" style="color:var(--text-muted)">
      <span style="animation:pulse 1.2s infinite;display:inline-block">Analysing</span>…
    </div>`;
  els.chatMessages.appendChild(div);
  els.chatMessages.scrollTop = els.chatMessages.scrollHeight;

  if (window.lucide) {
    lucide.createIcons({ attrs: { class: 'icon-svg' } });
  }
}

function removeTypingIndicator() {
  const el = $('typingIndicator');
  if (el) el.remove();
}

async function sendChat() {
  const query = els.chatInput.value.trim();
  if (!query) return;

  const sessionId = state.activeProject?.id || state.uploadedSession;
  if (!sessionId) { toast('No active session. Run an analysis first.', 'warning'); return; }

  // Read API key directly from localStorage (not the hidden input which may be stale)
  const provider = els.llmProvider.value;
  const apiKey = getSavedKey(provider);

  // For non-Ollama providers, warn if no key
  if (provider !== 'ollama' && !apiKey) {
    toast('No API key set. Go to settings to add your key.', 'warning');
    return;
  }

  els.chatInput.value = '';
  hideColumnPicker();
  appendChatMsg('user', query);
  showTypingIndicator();

  const fd = new FormData();
  fd.append('session_id', sessionId);
  fd.append('query',      query);
  fd.append('provider',   provider);
  fd.append('model',      els.llmModel.value === '__custom__' ? '' : els.llmModel.value);
  fd.append('api_key',    apiKey);

  try {
    const res  = await fetch('/api/copilot', { method: 'POST', body: fd });
    removeTypingIndicator();

    if (!res.ok) {
      // Surface backend HTTP errors (422, 500, etc.)
      let errMsg = `Server error (${res.status})`;
      try {
        const errData = await res.json();
        errMsg = errData.detail || errData.message || errMsg;
      } catch (_) {}
      appendChatMsg('assistant', errMsg);
      return;
    }

    const data = await res.json();
    const text = data.text && data.text.trim() ? data.text : 'No response returned.';
    appendChatMsg('assistant', text, data.plot_url || null);
    
    // Reload dynamic preview if this query modified the dataset
    const qLower = query.toLowerCase();
    if (qLower.includes('delete') || qLower.includes('rename') || qLower.includes('replace') || qLower.includes('drop') || qLower.includes('fix') || qLower.includes('clean') || qLower.includes('modify') || qLower.includes('update')) {
      await refreshPreviewData(sessionId);
    }
  } catch (e) {
    removeTypingIndicator();
    appendChatMsg('assistant', 'Network error: ' + e.message);
  }
}

els.sendChatBtn.addEventListener('click', sendChat);
els.chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
});

// Quick hint chips
$$('.chat-hint-chip').forEach(chip => {
  chip.addEventListener('click', () => {
    els.chatInput.value = chip.dataset.query;
    activateTab('chat');
    sendChat();
  });
});

els.clearChatBtn.addEventListener('click', resetChat);

// ── /column slash picker ─────────────────────────────────────────────────────
function showColumnPicker(filter = '') {
  const cols = state.columns.filter(c =>
    c.toLowerCase().includes(filter.toLowerCase())
  );
  const picker = els.colPickerDropdown;

  if (!cols.length) { hideColumnPicker(); return; }

  picker.innerHTML = `<div class="col-picker-header"><i data-lucide="hash" style="width: 12px; height: 12px; vertical-align: middle; margin-right: 4px;"></i> Insert Column — type to filter</div>` +
    cols.slice(0, 20).map(c => {
      const dtype = state.colTypes[c] || '';
      return `<div class="col-picker-item" data-col="${escHtml(c)}">
        ${escHtml(c)}
        ${dtype ? `<span class="col-picker-item-type">${escHtml(dtype)}</span>` : ''}
      </div>`;
    }).join('');

  picker.querySelectorAll('.col-picker-item').forEach(item => {
    item.addEventListener('click', () => {
      const col = item.dataset.col;
      const textarea = els.chatInput;
      const val = textarea.value;
      // Replace the /... part with the column name
      const slashIdx = val.lastIndexOf('/');
      textarea.value = (slashIdx >= 0 ? val.slice(0, slashIdx) : val) + `\`${col}\` `;
      hideColumnPicker();
      textarea.focus();
    });
  });

  picker.classList.remove('hidden');
}

function hideColumnPicker() {
  els.colPickerDropdown.classList.add('hidden');
}

els.chatInput.addEventListener('input', () => {
  const val = els.chatInput.value;
  const slashIdx = val.lastIndexOf('/');
  if (slashIdx >= 0 && slashIdx === val.length - 1) {
    // Just typed /
    showColumnPicker('');
  } else if (slashIdx >= 0 && slashIdx < val.length) {
    // Typing after /
    showColumnPicker(val.slice(slashIdx + 1));
  } else {
    hideColumnPicker();
  }
});

document.addEventListener('click', e => {
  if (!els.colPickerDropdown.contains(e.target) && e.target !== els.chatInput) {
    hideColumnPicker();
  }
});


// Path locations cleanup helper to avoid showing raw local paths in UI
function removeFilePathInfo(text) {
  if (!text) return '';
  let cleaned = text.replace(/(?:[a-zA-Z]:)?[\\/][a-zA-Z0-9_\-\.\s\\/]+?\.(?:png|csv|zip|json|txt|py)/gi, '[File]');
  cleaned = cleaned.replace(/Plot saved to \[File\]/gi, 'Plot generated and saved successfully.');
  cleaned = cleaned.replace(/saved to \[File\]/gi, 'saved successfully.');
  
  // Strip Auto-Healing system headers, execution output dumps, and tracebacks
  cleaned = cleaned.replace(/\[Auto-Healing system resolved a code error!\][\s\S]*?(?:Successful Execution Output:\s*(?:\(no output\)|\S+)?)/gi, '');
  cleaned = cleaned.replace(/\[Auto-Healing system installed missing package[\s\S]*?(?:Output:\s*\S*)?/gi, '');
  cleaned = cleaned.replace(/Original Error:[\s\S]*?(?=(?:Successful Execution Output|$))/gi, '');
  cleaned = cleaned.replace(/Successful Execution Output:\s*\(no output\)/gi, '');
  cleaned = cleaned.replace(/Successful Execution Output:/gi, '');
  
  cleaned = cleaned.trim().replace(/\n{3,}/g, '\n\n');
  return cleaned;
}

// Local Notification Center
state.notifications = [];

function addNotification(title, text, type = 'info') {
  const notif = {
    id: Date.now() + Math.random(),
    title,
    text: removeFilePathInfo(text),
    time: new Date(),
    read: false,
    type
  };
  state.notifications.unshift(notif);
  renderNotifications();
}

function renderNotifications() {
  const badge = $('notifBadge');
  const list = $('notifsList');
  if (!badge || !list) return;
  
  const unreadCount = state.notifications.filter(n => !n.read).length;
  badge.textContent = unreadCount;
  if (unreadCount > 0) {
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
  
  if (state.notifications.length === 0) {
    list.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--text-secondary); font-size: 0.8rem;">No new notifications</div>`;
    return;
  }
  
  list.innerHTML = state.notifications.map(n => {
    const d = n.time;
    const timeStr = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
    return `
      <div class="notif-item ${n.read ? '' : 'unread'}" data-id="${n.id}">
        <div class="notif-item-title">
          <span>${escHtml(n.title)}</span>
          <span class="notif-item-time">${timeStr}</span>
        </div>
        <div class="notif-item-text">${escHtml(n.text)}</div>
      </div>
    `;
  }).join('');
  
  list.querySelectorAll('.notif-item').forEach(item => {
    item.addEventListener('click', () => {
      const id = parseFloat(item.dataset.id);
      const n = state.notifications.find(not => not.id === id);
      if (n) {
        n.read = true;
        renderNotifications();
      }
    });
  });
}

function updateExportChatPdfBtnVisibility() {
  const isExportActive = els.chatMessages.classList.contains('export-mode-active');
  const checked = document.querySelectorAll('.chat-select-check:checked');
  const btn = $('exportChatPdfBtn');
  if (btn) {
    btn.style.display = (isExportActive && checked.length > 0) ? 'inline-flex' : 'none';
  }
}

async function exportChatPdf() {
  const sessionId = state.activeProject?.id || state.uploadedSession;
  if (!sessionId) { toast('No active session. Run an analysis first.', 'warning'); return; }
  
  const checked = document.querySelectorAll('.chat-select-check:checked');
  const selectedMessages = [];
  checked.forEach(chk => {
    const idx = parseInt(chk.dataset.idx, 10);
    const msg = state.chatHistory[idx];
    if (msg) {
      selectedMessages.push(msg);
    }
  });
  
  if (selectedMessages.length === 0) {
    toast('Select at least one message to export.', 'warning');
    return;
  }
  
  try {
    toast('Generating PDF...', 'info');
    const fd = new FormData();
    fd.append('session_id', sessionId);
    fd.append('messages_json', JSON.stringify(selectedMessages));
    
    const res = await fetch('/api/export-chat-pdf', {
      method: 'POST',
      body: fd
    });
    
    if (!res.ok) throw new Error('PDF generation failed');
    
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat_history_${sessionId}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    toast('PDF exported successfully!', 'success');
  } catch (e) {
    toast('Error exporting PDF: ' + e.message, 'error');
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Utilities
// ────────────────────────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str ?? '')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

// ────────────────────────────────────────────────────────────────────────────
// Initialise
// ────────────────────────────────────────────────────────────────────────────
(async function init() {
  await loadLlmSettings();
  loadProjects();
  syncTaskCards();
  resetWizardState();
  showScreen('landing');
  setStatus('● Idle', 'idle');

  if (window.lucide) {
    lucide.createIcons();
  }

  // Wire Selection Hub Cards
  if (els.btnEnterChat) {
    els.btnEnterChat.addEventListener('click', () => {
      const p = state.activeProject;
      if (!p) return;
      if (els.btnSectionChat && els.btnSectionChat.parentNode) {
        els.btnSectionChat.parentNode.classList.remove('hidden');
      }
      if (els.areaHub) els.areaHub.classList.add('hidden');
      switchSection('chat');
      setBreadcrumb(p.name, 'Crew Chat');
    });
  }

  if (els.btnEnterAgentic) {
    els.btnEnterAgentic.addEventListener('click', () => {
      const p = state.activeProject;
      if (!p) return;
      if (p.status === 'running') {
        showScreen('running');
        return;
      }
      if (els.btnSectionChat && els.btnSectionChat.parentNode) {
        els.btnSectionChat.parentNode.classList.remove('hidden');
      }
      if (els.areaHub) els.areaHub.classList.add('hidden');
      switchSection('agentic');
      setBreadcrumb(p.name, 'Crew Analysis');
    });
  }

  // Wire section switcher
  if (els.btnSectionChat) {
    els.btnSectionChat.addEventListener('click', () => {
      const p = state.activeProject;
      if (els.areaHub) els.areaHub.classList.add('hidden');
      switchSection('chat');
      if (p) setBreadcrumb(p.name, 'Crew Chat');
    });
  }
  if (els.btnSectionAgentic) {
    els.btnSectionAgentic.addEventListener('click', () => {
      const p = state.activeProject;
      if (els.areaHub) els.areaHub.classList.add('hidden');
      switchSection('agentic');
      if (p) setBreadcrumb(p.name, 'Crew Analysis');
    });
  }
  if (els.chatBackBtn) {
    els.chatBackBtn.addEventListener('click', () => {
      const p = state.activeProject;
      if (els.areaHub) els.areaHub.classList.add('hidden');
      switchSection('agentic');
      if (p) setBreadcrumb(p.name, 'Crew Analysis');
    });
  }

  // Wire quick action buttons
  if (els.btnRenameColQuick) {
    els.btnRenameColQuick.addEventListener('click', async () => {
      const oldName = await customPrompt('Select or enter the column you want to rename:', '', 'e.g. Q3_Sales', 'Rename Column');
      if (!oldName) return;
      if (!state.columns.includes(oldName)) {
        toast(`Column "${oldName}" not found in dataset.`, 'error');
        return;
      }
      const newName = await customPrompt(`Enter the new name for column "${oldName}":`, '', 'e.g. Sales_Q3', 'Rename Column');
      if (!newName) return;
      
      // Command the copilot
      els.chatInput.value = `Rename column \`${oldName}\` to \`${newName}\` in the dataset`;
      sendChat();
    });
  }

  if (els.btnDeleteColQuick) {
    els.btnDeleteColQuick.addEventListener('click', async () => {
      const colName = await customPrompt('Enter the name of the column you want to delete:', '', 'e.g. Unwanted_Col', 'Delete Column');
      if (!colName) return;
      if (!state.columns.includes(colName)) {
        toast(`Column "${colName}" not found in dataset.`, 'error');
        return;
      }
      const confirmed = await customConfirm(`Are you sure you want to permanently delete column "${colName}"?`, 'Delete Column');
      if (!confirmed) return;
      
      // Command the copilot
      els.chatInput.value = `Delete column \`${colName}\` from the dataset`;
      sendChat();
    });
  }

  // Wire agentic pipeline launch button
  if (els.btnRunAgenticPipeline) {
    els.btnRunAgenticPipeline.addEventListener('click', () => {
      state.uploadedSession = state.activeProject?.id;
      state.uploadedFile = { name: state.activeProject?.filename || 'dataset.csv' };
      if (!checkApiKeySet()) return;
      openConfigModal();
    });
  }

  // Wire run in background and dismiss notification buttons
  const btnBg = $('btnRunInBackground');
  if (btnBg) {
    btnBg.addEventListener('click', () => {
      const p = state.activeProject;
      if (p) {
        goToWorkspaceHub();
        showScreen('results');
        toast('Running in background. Check notifications for progress.', 'info');
      }
    });
  }

  const btnDismiss = $('dismissNotif');
  if (btnDismiss) {
    btnDismiss.addEventListener('click', (e) => {
      e.stopPropagation();
      const notif = $('analysisNotification');
      if (notif) notif.classList.add('hidden');
    });
  }

  // Performance Metrics logic
  async function loadMetrics() {
    try {
      const res = await fetch('/api/metrics');
      if (!res.ok) throw new Error('Failed to fetch metrics');
      const data = await res.json();
      
      const totalRuns = data.length;
      let totalTime = 0;
      let totalTokens = 0;
      let totalCost = 0;
      
      data.forEach(run => {
        totalTime += run.total_time || 0;
        totalTokens += run.token_usage || 0;
        totalCost += run.estimated_cost || 0;
      });
      
      const avgTime = totalRuns > 0 ? (totalTime / totalRuns).toFixed(1) : 0;
      
      const runsEl = $('metricsTotalRuns');
      const timeEl = $('metricsAvgTime');
      const tokensEl = $('metricsTotalTokens');
      const costEl = $('metricsTotalCost');
      
      if (runsEl) runsEl.textContent = totalRuns;
      if (timeEl) timeEl.textContent = `${avgTime}s`;
      if (tokensEl) tokensEl.textContent = totalTokens.toLocaleString();
      if (costEl) costEl.textContent = `$${totalCost.toFixed(3)}`;
      
      const tbody = $('metricsTableBody');
      if (tbody) {
        tbody.innerHTML = '';
        
        if (data.length === 0) {
          tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 20px; color: var(--text-secondary);">No run history recorded yet.</td></tr>`;
          return;
        }
        
        const sorted = [...data].reverse();
        sorted.forEach(run => {
          const tr = document.createElement('tr');
          tr.style.borderBottom = '1px solid var(--border)';
          
          const ts = new Date(run.timestamp).toLocaleString();
          const statusText = run.success ? '✓ Success' : '✗ Failed';
          const statusStyle = run.success ? 'color: var(--emerald); font-weight: 600;' : 'color: var(--rose); font-weight: 600;';
          
          tr.innerHTML = `
            <td style="padding: 12px 20px; font-weight: 500;">${escHtml(run.dataset_name || 'dataset.csv')}</td>
            <td style="padding: 12px 20px; color: var(--text-secondary);">${run.rows || 0} x ${run.columns || 0}</td>
            <td style="padding: 12px 20px;">${(run.total_time || 0).toFixed(1)}s</td>
            <td style="padding: 12px 20px;">${(run.token_usage || 0).toLocaleString()}</td>
            <td style="padding: 12px 20px; color: var(--amber); font-weight: 500;">$${(run.estimated_cost || 0).toFixed(3)}</td>
            <td style="padding: 12px 20px; color: var(--text-secondary);">${ts}</td>
            <td style="padding: 12px 20px; ${statusStyle}">${statusText}</td>
          `;
          tbody.appendChild(tr);
        });
      }
    } catch (err) {
      console.error(err);
      toast('Failed to load performance metrics', 'error');
    }
  }

  if (els.sidebarMetricsBtn) {
    els.sidebarMetricsBtn.addEventListener('click', () => {
      showScreen('metrics');
      loadMetrics();
    });
  }
  
  if (els.backToDashboardBtn) {
    els.backToDashboardBtn.addEventListener('click', () => {
      if (state.activeProject) {
        showScreen('results');
      } else {
        showScreen('landing');
      }
    });
  }

  // Wire Notification Bell & Dropdown
  const bellBtn = $('notifBellBtn');
  const dropdown = $('notifDropdown');
  if (bellBtn && dropdown) {
    bellBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('hidden');
      if (!dropdown.classList.contains('hidden')) {
        state.notifications.forEach(n => n.read = true);
        renderNotifications();
      }
    });
    
    document.addEventListener('click', (e) => {
      if (!dropdown.contains(e.target) && e.target !== bellBtn) {
        dropdown.classList.add('hidden');
      }
    });
  }
  
  const clearNotifsBtn = $('clearNotifsBtn');
  if (clearNotifsBtn) {
    clearNotifsBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      state.notifications = [];
      renderNotifications();
    });
  }

  // Wire Terms of Service modal
  const tosModal = $('tosModal');
  const tosBtn = $('sidebarTosBtn');
  const closeTos = $('closeTosModal');
  const acceptTos = $('acceptTosBtn');
  
  if (tosBtn && tosModal) {
    tosBtn.addEventListener('click', () => {
      tosModal.classList.remove('hidden');
    });
  }
  if (closeTos && tosModal) {
    closeTos.addEventListener('click', () => {
      tosModal.classList.add('hidden');
    });
  }
  if (acceptTos && tosModal) {
    acceptTos.addEventListener('click', () => {
      tosModal.classList.add('hidden');
      toast('Thank you for accepting the Terms of Service.', 'success');
    });
  }
  if (tosModal) {
    tosModal.addEventListener('click', (e) => {
      if (e.target === tosModal) {
        tosModal.classList.add('hidden');
      }
    });
  }

  // Wire Export Chat PDF button & Toggle Export Mode
  const btnExportChat = $('exportChatPdfBtn');
  if (btnExportChat) {
    btnExportChat.addEventListener('click', () => {
      exportChatPdf();
      // Auto-exit export mode after successful download trigger
      if (els.toggleExportModeBtn) els.toggleExportModeBtn.click();
    });
  }

  if (els.toggleExportModeBtn) {
    els.toggleExportModeBtn.addEventListener('click', () => {
      const isActive = els.chatMessages.classList.toggle('export-mode-active');
      if (isActive) {
        els.toggleExportModeBtn.innerHTML = '<i data-lucide="x" style="width:12px; height:12px;"></i> Cancel';
        els.toggleExportModeBtn.style.background = 'rgba(255, 37, 42, 0.15)';
        els.toggleExportModeBtn.style.borderColor = 'rgba(255, 37, 42, 0.4)';
        els.toggleExportModeBtn.style.color = 'var(--rose)';
      } else {
        els.toggleExportModeBtn.innerHTML = '<i data-lucide="share-2" style="width:12px; height:12px;"></i> Export Chat';
        els.toggleExportModeBtn.style.background = '';
        els.toggleExportModeBtn.style.borderColor = '';
        els.toggleExportModeBtn.style.color = '';
        // Uncheck all
        document.querySelectorAll('.chat-select-check').forEach(chk => chk.checked = false);
      }
      updateExportChatPdfBtnVisibility();
      if (window.lucide) lucide.createIcons();
    });
  }

  // Check if a running session exists on page load
  // (handles F5 refresh during analysis)
  setTimeout(async () => {
    const projects = state.projects;
    const running = projects.find(p => p.status === 'running');
    if (running) switchToProject(running);
  }, 500);
})();
