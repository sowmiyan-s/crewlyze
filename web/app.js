/**
 * Agentic Data Analyst — Web App JavaScript
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

const DEFAULT_THUMBNAIL_SVG = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMjAiIGhlaWdodD0iMTgwIiB2aWV3Qm94PSIwIDAgMzIwIDE4MCI+PHJlY3Qgd2lkdGg9IjMyMCIgaGVpZ2h0PSIxODAiIGZpbGw9IiMxODE4MWIiLz48Y2lyY2xlIGN4PSIxNjAiIGN5PSI5MCIgcj0iNDAiIGZpbGw9IiM3YzNhZWQiIGZpbGwtb3BhY2l0eT0iMC4xIi8+PHBhdGggZD0iTTE0MCAxMDAgTDE2MCA4MCBMMTgwIDEwMCIgc3Ryb2tlPSIjN2MzYWVkIiBzdHJva2Utd2lkdGg9IjMiIGZpbGw9Im5vbmUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjxwYXRoIGQ9Ik0xMzAgMTE1IEwxOTAgMTE1IiBzdHJva2U9IiMyMmQzZWUiIHN0cm9rZS13aWR0aD0iMiIgZmlsbD0ibm9uZSIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+PHRleHQgeD0iMTYwIiB5PSIxNTAiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXNpemU9IjExIiBmaWxsPSIjYTFhMWFhIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIj5BR0VOVElDIExPR1M8L3RleHQ+PC9zdmc+';

// ────────────────────────────────────────────────────────────────────────────
// Model catalogue (mirrors the sidebar in the old Streamlit app)
// ────────────────────────────────────────────────────────────────────────────
const MODEL_OPTIONS = {
  nvidia:      [
    'nvidia_nim/meta/llama-3.1-8b-instruct',
    'nvidia_nim/meta/llama-3.1-70b-instruct',
    'nvidia_nim/nvidia/mistral-nemo-minitron-8b-8k-instruct',
    'nvidia_nim/mistralai/mistral-large-2407',
  ],
  minimax:     ['minimaxai/minimax-m3'],
  groq:        ['groq/llama-3.1-8b-instant','groq/llama-3.3-70b-versatile','groq/mixtral-8x7b-32768','groq/gemma2-9b-it'],
  openai:      ['gpt-4o','gpt-4o-mini','gpt-4-turbo','gpt-3.5-turbo'],
  anthropic:   ['claude-3-5-sonnet-20241022','claude-3-opus-20240229','claude-3-sonnet-20240229','claude-3-haiku-20240307'],
  gemini:      ['gemini/gemini-pro','gemini/gemini-1.5-pro','gemini/gemini-1.5-flash'],
  mistral:     ['mistral/mistral-tiny','mistral/mistral-small','mistral/mistral-medium','mistral/mistral-large-latest'],
  huggingface: ['huggingface/HuggingFaceH4/zephyr-7b-beta','huggingface/meta-llama/Llama-2-7b-chat-hf'],
  ollama:      ['ollama/llama3','ollama/mistral','ollama/gemma2'],
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
  startWizardCard:    $('startWizardCard'),
  wizardStep1:       $('wizardStep1'),
  wizardBack1Btn:     $('wizardBack1Btn'),
  wizardStep2:       $('wizardStep2'),
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
  chatInput:         $('chatInput'),
  sendChatBtn:       $('sendChatBtn'),
  clearChatBtn:      $('clearChatBtn'),
  colPickerDropdown: $('colPickerDropdown'),

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
};

// ────────────────────────────────────────────────────────────────────────────
// Screen management
// ────────────────────────────────────────────────────────────────────────────
function showScreen(name) {
  ['landingScreen','runningScreen','resultsScreen'].forEach(id => {
    const el = $(id);
    el.classList.toggle('active', id === name + 'Screen');
  });
  if (name !== 'results') {
    if (els.sidebarProjectActions) els.sidebarProjectActions.classList.add('hidden');
  } else {
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
    const res = await fetch('/api/ollama-models');
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
const ALL_PROVIDERS = [
  { id: 'nvidia', name: 'NVIDIA NIM' },
  { id: 'groq', name: 'Groq' },
  { id: 'openai', name: 'OpenAI' },
  { id: 'anthropic', name: 'Anthropic' },
  { id: 'gemini', name: 'Google Gemini' },
  { id: 'mistral', name: 'Mistral' },
  { id: 'huggingface', name: 'HuggingFace' },
  { id: 'cohere', name: 'Cohere' },
  { id: 'together', name: 'TogetherAI' },
  { id: 'openrouter', name: 'OpenRouter' },
  { id: 'deepseek', name: 'DeepSeek' },
  { id: 'perplexity', name: 'Perplexity' },
  { id: 'ollama', name: 'Ollama (local)' }
];

const PROVIDER_TEST_MODELS = {
  nvidia: 'nvidia_nim/meta/llama-3.1-8b-instruct',
  groq: 'groq/llama-3.1-8b-instant',
  openai: 'gpt-4o-mini',
  anthropic: 'claude-3-5-sonnet-20241022',
  gemini: 'gemini/gemini-pro',
  mistral: 'mistral/mistral-tiny',
  huggingface: 'huggingface/HuggingFaceH4/zephyr-7b-beta',
  ollama: 'ollama/llama3',
  cohere: 'cohere/command-r-plus',
  together: 'together_ai/meta-llama/Llama-3-70b-chat-hf',
  openrouter: 'openrouter/google/gemma-2-9b-it',
  deepseek: 'deepseek/deepseek-chat',
  perplexity: 'perplexity/llama-3-sonar-large-32k-chat'
};

function getSavedKey(provider) {
  if (provider === 'ollama') {
    return localStorage.getItem('api_url_ollama') || 'http://localhost:11434';
  }
  return localStorage.getItem(`api_key_${provider}`) || '';
}

function syncActiveApiKey() {
  const provider = els.llmProvider.value;
  const key = getSavedKey(provider);
  els.apiKey.value = key;
}

function saveLlmSettings() {
  localStorage.setItem('llm_provider', els.llmProvider.value);
  localStorage.setItem('llm_model', els.llmModel.value);
}

function populateProvidersDropdown() {
  const currentVal = els.llmProvider.value;
  els.llmProvider.innerHTML = '';
  let selectedExists = false;
  
  ALL_PROVIDERS.forEach(p => {
    const isShown = localStorage.getItem(`show_provider_${p.id}`) !== 'false'; // defaults to true
    if (isShown) {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.name;
      els.llmProvider.appendChild(opt);
      if (p.id === currentVal) selectedExists = true;
    }
  });

  if (selectedExists) {
    els.llmProvider.value = currentVal;
  } else if (els.llmProvider.options.length > 0) {
    els.llmProvider.selectedIndex = 0;
  }
}

async function loadLlmSettings() {
  const savedProvider = localStorage.getItem('llm_provider');
  const savedCooldown = localStorage.getItem('llm_cooldown') || '5';

  populateProvidersDropdown();

  if (savedProvider && Array.from(els.llmProvider.options).some(opt => opt.value === savedProvider)) {
    els.llmProvider.value = savedProvider;
  } else if (els.llmProvider.options.length > 0) {
    els.llmProvider.selectedIndex = 0;
  }
  
  await populateModels(els.llmProvider.value);

  els.cooldown.value = savedCooldown;
  els.cooldownVal.textContent = savedCooldown;

  syncActiveApiKey();
}

// Populate Settings Modal text boxes
function populateSettingsModal() {
  // Checkbox show states
  ALL_PROVIDERS.forEach(p => {
    const showCheck = els[`show${p.id.charAt(0).toUpperCase() + p.id.slice(1)}`];
    if (showCheck) {
      showCheck.checked = localStorage.getItem(`show_provider_${p.id}`) !== 'false';
    }
  });

  // Keys
  els.keyNvidia.value = localStorage.getItem('api_key_nvidia') || '';
  els.keyGroq.value = localStorage.getItem('api_key_groq') || '';
  els.keyOpenai.value = localStorage.getItem('api_key_openai') || '';
  els.keyAnthropic.value = localStorage.getItem('api_key_anthropic') || '';
  els.keyGemini.value = localStorage.getItem('api_key_gemini') || '';
  els.keyMistral.value = localStorage.getItem('api_key_mistral') || '';
  els.keyHuggingface.value = localStorage.getItem('api_key_huggingface') || '';
  els.keyCohere.value = localStorage.getItem('api_key_cohere') || '';
  els.keyTogether.value = localStorage.getItem('api_key_together') || '';
  els.keyOpenrouter.value = localStorage.getItem('api_key_openrouter') || '';
  els.keyDeepseek.value = localStorage.getItem('api_key_deepseek') || '';
  els.keyPerplexity.value = localStorage.getItem('api_key_perplexity') || '';
  els.urlOllama.value = localStorage.getItem('api_url_ollama') || 'http://localhost:11434';

  const cooldown = localStorage.getItem('llm_cooldown') || '5';
  els.settingsCooldown.value = cooldown;
  els.settingsCooldownVal.textContent = cooldown;

  // Clear all individual statuses
  document.querySelectorAll('.individual-status').forEach(el => {
    el.textContent = '';
    el.className = 'individual-status';
    el.style.color = '';
  });
}

// Save Settings Modal inputs
function saveSettingsModal() {
  // Checkbox show states
  ALL_PROVIDERS.forEach(p => {
    const showCheck = els[`show${p.id.charAt(0).toUpperCase() + p.id.slice(1)}`];
    if (showCheck) {
      localStorage.setItem(`show_provider_${p.id}`, showCheck.checked ? 'true' : 'false');
    }
  });

  // Keys
  localStorage.setItem('api_key_nvidia', els.keyNvidia.value.trim());
  localStorage.setItem('api_key_groq', els.keyGroq.value.trim());
  localStorage.setItem('api_key_openai', els.keyOpenai.value.trim());
  localStorage.setItem('api_key_anthropic', els.keyAnthropic.value.trim());
  localStorage.setItem('api_key_gemini', els.keyGemini.value.trim());
  localStorage.setItem('api_key_mistral', els.keyMistral.value.trim());
  localStorage.setItem('api_key_huggingface', els.keyHuggingface.value.trim());
  localStorage.setItem('api_key_cohere', els.keyCohere.value.trim());
  localStorage.setItem('api_key_together', els.keyTogether.value.trim());
  localStorage.setItem('api_key_openrouter', els.keyOpenrouter.value.trim());
  localStorage.setItem('api_key_deepseek', els.keyDeepseek.value.trim());
  localStorage.setItem('api_key_perplexity', els.keyPerplexity.value.trim());
  localStorage.setItem('api_url_ollama', els.urlOllama.value.trim());

  const cooldown = els.settingsCooldown.value;
  localStorage.setItem('llm_cooldown', cooldown);
  els.cooldown.value = cooldown;
  els.cooldownVal.textContent = cooldown;

  // Re-populate sidebar provider list
  populateProvidersDropdown();
  syncActiveApiKey();
  
  toast('Settings saved permanently!', 'success');
  els.settingsModal.classList.add('hidden');
}

// Wire Settings Modal Buttons & Navigation
if (els.sidebarSettingsBtn) {
  els.sidebarSettingsBtn.addEventListener('click', () => {
    populateSettingsModal();
    els.settingsModal.classList.remove('hidden');
  });
}
if (els.closeSettingsModal) {
  els.closeSettingsModal.addEventListener('click', () => {
    els.settingsModal.classList.add('hidden');
  });
}
if (els.cancelSettingsBtn) {
  els.cancelSettingsBtn.addEventListener('click', () => {
    els.settingsModal.classList.add('hidden');
  });
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

// Eye button toggle for Settings modal
document.querySelectorAll('.toggle-setting-key').forEach(btn => {
  btn.addEventListener('click', e => {
    e.preventDefault();
    const input = btn.previousElementSibling;
    if (input) {
      input.type = input.type === 'password' ? 'text' : 'password';
    }
  });
});

// Test Connection individually inside Settings Modal
document.querySelectorAll('.test-individual-btn').forEach(btn => {
  btn.addEventListener('click', async (e) => {
    e.preventDefault();
    const provider = btn.dataset.provider;
    const model = PROVIDER_TEST_MODELS[provider];
    
    // Find the input element and status element for this provider
    let apiKey = '';
    const capId = provider.charAt(0).toUpperCase() + provider.slice(1);
    const inputEl = els[`key${capId}`] || els[`url${capId}`] || document.getElementById(`key${capId}`) || document.getElementById(`url${capId}`);
    const statusEl = document.getElementById(`status${capId}`);

    if (inputEl) {
      apiKey = inputEl.value.trim();
    }

    if (statusEl) {
      statusEl.className = 'individual-status loading';
      statusEl.textContent = 'Testing connection...';
      statusEl.style.color = 'var(--text-secondary)';
    }

    const fd = new FormData();
    fd.append('provider', provider);
    fd.append('model', model);
    fd.append('api_key', apiKey);

    try {
      const res = await fetch('/api/validate-key', { method: 'POST', body: fd });
      if (res.ok) {
        if (statusEl) {
          statusEl.className = 'individual-status ok';
          statusEl.textContent = '✓ Connection successful';
          statusEl.style.color = 'var(--emerald)';
        }
        toast(`${provider.toUpperCase()} connection verified!`, 'success');
      } else {
        const data = await res.json().catch(() => ({}));
        if (statusEl) {
          statusEl.className = 'individual-status error';
          statusEl.textContent = '✗ ' + (data.detail || 'Connection failed');
          statusEl.style.color = 'var(--rose)';
        }
      }
    } catch (err) {
      if (statusEl) {
        statusEl.className = 'individual-status error';
        statusEl.textContent = '✗ Network error';
        statusEl.style.color = 'var(--rose)';
      }
    }
  });
});

// ────────────────────────────────────────────────────────────────────────────
// LLM Provider & Model selector
// ────────────────────────────────────────────────────────────────────────────
async function populateModels(provider) {
  let models = MODEL_OPTIONS[provider] || [];

  if (provider === 'ollama') {
    const sel = els.llmModel;
    sel.innerHTML = '<option value="">🔄 Loading Ollama models...</option>';
    models = await fetchOllamaModels();
  }

  const sel = els.llmModel;
  sel.innerHTML = '';
  models.forEach(m => {
    const opt = document.createElement('option');
    opt.value = m; opt.textContent = m;
    sel.appendChild(opt);
  });
  // Add custom option
  const customOpt = document.createElement('option');
  customOpt.value = '__custom__';
  customOpt.textContent = '✏️ Custom model…';
  sel.appendChild(customOpt);

  // Restore saved model selection if applicable
  const savedModel = localStorage.getItem('llm_model');
  if (savedModel && provider === localStorage.getItem('llm_provider')) {
    const modelOptions = Array.from(sel.options).map(opt => opt.value);
    if (!modelOptions.includes(savedModel) && savedModel !== '__custom__') {
      const opt = document.createElement('option');
      opt.value = savedModel;
      opt.textContent = savedModel;
      sel.insertBefore(opt, sel.lastElementChild);
    }
    sel.value = savedModel;
  }
}

els.llmProvider.addEventListener('change', async () => {
  await populateModels(els.llmProvider.value);
  syncActiveApiKey();
  saveLlmSettings();
});
els.llmModel.addEventListener('change', async () => {
  if (els.llmModel.value === '__custom__') {
    const custom = await customPrompt('Enter full model identifier:', '', 'e.g. gpt-4o-mini', 'Custom Model');
    if (custom) {
      const opt = document.createElement('option');
      opt.value = custom; opt.textContent = custom; opt.selected = true;
      els.llmModel.insertBefore(opt, els.llmModel.lastElementChild);
      els.llmModel.value = custom;
    }
  }
  saveLlmSettings();
});


// ────────────────────────────────────────────────────────────────────────────
// Sidebar collapse
// ────────────────────────────────────────────────────────────────────────────
els.sidebarToggle.addEventListener('click', () => {
  const collapsed = els.sidebar.classList.toggle('collapsed');
  els.sidebarToggle.textContent = collapsed ? '›' : '‹';
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
// Projects sidebar
// ────────────────────────────────────────────────────────────────────────────
async function loadProjects() {
  try {
    const res = await fetch('/api/projects');
    state.projects = await res.json();
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
          <div class="empty-card-icon">📂</div>
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
  }
  // Resize Plotly charts when switching to agentic area
  if (sec === 'agentic') {
    setTimeout(() => Plotly.Plots?.resize?.(), 100);
  }
  updateSidebarProjectActionsVisibility(sec);
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
    switchSection('chat');
    showScreen('results');
    setStatus('● Idle', 'idle');
  }
}

async function deleteProject(id) {
  const confirmed = await customConfirm('Delete this project and all its data? This action cannot be undone.', 'Delete Project');
  if (!confirmed) return;
  delete state.resultsCache[id];
  await fetch(`/api/projects/${id}`, { method: 'DELETE' });
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
  if (els.wizardStep0) els.wizardStep0.classList.add('active');
  if (els.wizardStep1) els.wizardStep1.classList.remove('active');
  if (els.wizardStep2) els.wizardStep2.classList.remove('active');
  if (els.uploadedFileMeta) els.uploadedFileMeta.classList.add('hidden');
  if (els.uploadedFileActions) els.uploadedFileActions.classList.add('hidden');
}

// Import Project ZIP flow
if (els.importProjectCard && els.importZipFileInput) {
  els.importProjectCard.addEventListener('click', () => {
    els.importZipFileInput.click();
  });
  
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

// Wire wizard events
if (els.startWizardCard) {
  els.startWizardCard.addEventListener('click', () => {
    if (els.wizardStep0) els.wizardStep0.classList.remove('active');
    if (els.wizardStep1) els.wizardStep1.classList.add('active');
    if (els.wizardProjectName) els.wizardProjectName.focus();
  });
}

if (els.wizardBack1Btn) {
  els.wizardBack1Btn.addEventListener('click', () => {
    if (els.wizardStep1) els.wizardStep1.classList.remove('active');
    if (els.wizardStep0) els.wizardStep0.classList.add('active');
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
    if (els.wizardStep1) els.wizardStep1.classList.remove('active');
    if (els.wizardStep2) els.wizardStep2.classList.add('active');
  });
}

if (els.wizardBackBtn) {
  els.wizardBackBtn.addEventListener('click', () => {
    if (els.wizardStep2) els.wizardStep2.classList.remove('active');
    if (els.wizardStep1) els.wizardStep1.classList.add('active');
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

function setBreadcrumb(name) {
  els.breadcrumb.innerHTML = `
    <span class="breadcrumb-item" onclick="goToDashboardHome()" style="cursor:pointer">Dashboard</span>
    <span class="breadcrumb-sep">›</span>
    <span class="breadcrumb-item active">${escHtml(name)}</span>
  `;
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
    
    // Auto-enter project workspace
    resetWizardState();
    await loadProjects();
    const newProj = state.projects.find(p => p.id === data.id);
    if (newProj) {
      switchToProject(newProj);
    }
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

els.startAnalysisBtn.addEventListener('click', () => {
  if (!state.uploadedSession) { toast('No file uploaded yet.', 'warning'); return; }
  if (!checkApiKeySet()) return;
  openConfigModal();
});

// ────────────────────────────────────────────────────────────────────────────
// Config Modal
// ────────────────────────────────────────────────────────────────────────────
function openConfigModal() {
  els.configModal.classList.remove('hidden');
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
  if (ll.includes('💭') || ll.startsWith('thought:'))    return 'thought';
  if (ll.includes('🛠️') || ll.startsWith('action:'))    return 'action';
  if (ll.includes('📤') || ll.includes('observation:')) return 'response';
  if (ll.includes('✅') || ll.includes('complete'))      return 'done';
  if (ll.includes('❌') || ll.includes('error'))         return 'error';
  if (ll.includes('⚠️') || ll.includes('warning'))      return 'warning';
  return '';
}

function appendLog(line) {
  const div = document.createElement('div');
  div.className = `log-line ${classifyLine(line)}`;
  div.textContent = line;
  els.logOutput.appendChild(div);
  els.logOutput.scrollTop = els.logOutput.scrollHeight;
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
        <div class="pov-title">🧹 Data Sanitizer Active</div>
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
        <div class="pov-title">🔗 Correlation Detector Engaged</div>
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
        <div class="pov-title">💡 Strategic Business Insights</div>
        <div class="pov-desc">Correlating discovered patterns to business implications and drafting actionable McKinsey-level recommendation strategies...</div>
      </div>
      <div class="pov-content">
        <div class="pov-insight-bulb">
          <svg class="pov-bulb-icon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
          </svg>
          <div class="pov-insight-bullets">
            <div class="pov-bullet-text">🔍 Identifying key driver columns...</div>
            <div class="pov-bullet-text">📈 Formulating risk matrices...</div>
            <div class="pov-bullet-text">💡 Generating recommendations...</div>
          </div>
        </div>
      </div>`;

  } else if (stage === 'visualization') {
    els.stagePovPanel.innerHTML = `
      <div class="pov-header">
        <div class="pov-title">🎨 Visual Intelligence Compiler</div>
        <div class="pov-desc">Writing corporate Seaborn/Matplotlib visualization scripts and compiling high-resolution PNG plots...</div>
      </div>
      <div class="pov-content">
        <svg class="pov-compiler-svg" viewBox="0 0 150 90">
          <line x1="20" y1="10" x2="20" y2="80" class="pov-axis"></line>
          <line x1="20" y1="80" x2="140" y2="80" class="pov-axis"></line>
          
          <path d="M20 70 Q 50 20, 80 50 T 140 15" class="pov-compiler-path"></path>
          
          <circle cx="50" cy="38" r="3" class="pov-dot" style="animation-delay: 0.8s;"></circle>
          <circle cx="80" cy="50" r="3" class="pov-dot" style="animation-delay: 1.4s;"></circle>
          <circle cx="110" cy="28" r="3" class="pov-dot" style="animation-delay: 2s;"></circle>
          <circle cx="130" cy="20" r="3" class="pov-dot" style="animation-delay: 2.6s;"></circle>
        </svg>
      </div>`;

  } else if (stage === 'plotly') {
    els.stagePovPanel.innerHTML = `
      <div class="pov-header">
        <div class="pov-title">📊 Interactive Dashboard Builder</div>
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

function inferStageFromLog(line) {
  const ll = line.toLowerCase();
  for (const [stage, keywords] of Object.entries(STAGE_KEYWORDS)) {
    if (keywords.some(k => ll.includes(k))) return stage;
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

  const src = new EventSource(`/api/analyze/stream?session_id=${sessionId}`);
  state.sseSource = src;

  src.onmessage = e => {
    const line = e.data;

    if (line === '[EOF]') {
      src.close();
      state.sseSource = null;
      // Mark remaining active stage as done
      if (_activeStage) markStage(_activeStage, 'done');
      appendLog('✅ Analysis complete! Loading results…');
      setStatus('● Loading…', 'running');
      setTimeout(() => loadResults(sessionId), 1500);
      return;
    }

    appendLog(line);

    // Infer stage transitions
    const stage = inferStageFromLog(line);
    if (stage && stage !== _activeStage) {
      if (_activeStage) markStage(_activeStage, 'done');
      _activeStage = stage;
      markStage(stage, 'active');
    }
  };

  src.onerror = () => {
    src.close();
    state.sseSource = null;
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
    renderDashboard(data, sessionId);
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

    renderDashboard(data, sessionId);
    
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
    { val: (data.rows_count || 0).toLocaleString(), lbl: 'Total Records', icon: '🗂️', color: 'var(--violet)' },
    { val: data.cols_count || 0, lbl: 'Total Columns', icon: '📊', color: 'var(--cyan)' },
    { val: data.numeric_count || 0, lbl: 'Numeric Fields', icon: '🔢', color: 'var(--emerald)' },
    { val: data.cat_count || 0, lbl: 'Categorical Fields', icon: '🏷️', color: 'var(--amber)' },
    { val: (data.plotly_charts || []).length, lbl: 'Interactive Charts', icon: '📈', color: 'var(--rose)' },
  ];
  els.statsRow.innerHTML = stats.map(s => `
    <div class="stat-card" style="--accent:${s.color}">
      <div class="stat-icon">${s.icon}</div>
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
      <div class="cleaning-check">✔</div>
      <div class="cleaning-text">${escHtml(l.replace(/^[-*•]\s*/, ''))}</div>
    </div>`
  ).join('');
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
        <p style="margin-bottom: 8px;">No schema relationships mapped yet.</p>
        <button id="btnAddRelation" class="btn-primary btn-sm" style="font-weight: 600;">➕ Add Custom Relation</button>
      </div>`;
    
    const btn = document.getElementById('btnAddRelation');
    if (btn) btn.onclick = () => showRelationModal(null);
    return;
  }

  let html = '<div class="relation-mapper-container">';
  list.forEach((rel, index) => {
    const xType = state.colTypes[rel.xCol] || 'Numeric';
    const yType = state.colTypes[rel.yCol] || 'Numeric';

    html += `
      <div class="relation-card" style="position: relative; flex: 1 1 calc(50% - 16px); min-width: 380px; box-sizing: border-box;">
        <!-- Tweak Actions Toolbar -->
        <div style="position: absolute; top: 12px; right: 12px; display: flex; gap: 6px; z-index: 5;">
          <button class="btn-secondary btn-sm btn-rel-edit" data-idx="${index}" style="padding: 2px 6px; font-size: 0.72rem; border-color: rgba(34,211,238,0.2); color: var(--cyan);">✏️ Edit</button>
          <button class="btn-secondary btn-sm btn-rel-del" data-idx="${index}" style="padding: 2px 6px; font-size: 0.72rem; border-color: rgba(244,63,94,0.2); color: var(--rose);">🗑️ Delete</button>
        </div>

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

  // Footer Actions
  html += `
    <div style="display: flex; gap: 12px; margin-top: 16px; justify-content: flex-end; width: 100%;">
      <button id="btnAddRelation" class="btn-secondary" style="font-weight: 600; font-size: 0.85rem;">➕ Add Custom Relation</button>
      <button id="btnSaveRelations" class="btn-primary" style="font-weight: 600; font-size: 0.85rem;">💾 Save Schema Tweaks</button>
    </div>
  `;
  html += '</div>';
  
  els.relationsContent.innerHTML = html;

  // Wire buttons
  els.relationsContent.querySelectorAll('.btn-rel-edit').forEach(b => {
    b.onclick = () => showRelationModal(parseInt(b.dataset.idx, 10));
  });
  els.relationsContent.querySelectorAll('.btn-rel-del').forEach(b => {
    b.onclick = () => deleteRelationAt(parseInt(b.dataset.idx, 10));
  });
  
  document.getElementById('btnAddRelation').onclick = () => showRelationModal(null);
  document.getElementById('btnSaveRelations').onclick = () => saveTweakedRelations();
}

function showRelationModal(index) {
  const cols = state.columns || [];
  els.relationModalXSelect.innerHTML = cols.map(c => `<option value="${escHtml(c)}">${escHtml(c)}</option>`).join('');
  els.relationModalYSelect.innerHTML = cols.map(c => `<option value="${escHtml(c)}">${escHtml(c)}</option>`).join('');
  
  if (index !== null && state.relationsList[index]) {
    const rel = state.relationsList[index];
    els.relationModalTitle.textContent = '✏️ Edit Relationship Schema';
    els.relationModalXSelect.value = rel.xCol;
    els.relationModalYSelect.value = rel.yCol;
    els.relationModalTypeSelect.value = rel.typ;
    els.relationModalDetails.value = rel.details;
  } else {
    els.relationModalTitle.textContent = '➕ Add Custom Relationship';
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
        <div class="insight-header-title">🎯 Primary Objectives &amp; Goals</div>
        <div class="insight-header-text">${formatInsightsSubsections(objectivesText)}</div>
      </div>
    `;
  }

  // 2. Dataset Statistics Grid
  if (statsText) {
    const statLines = statsText.split('\n').map(l => l.trim()).filter(l => l.startsWith('-') || l.startsWith('*'));
    if (statLines.length > 0) {
      html += `<div class="insight-stats-grid">`;
      statLines.forEach(line => {
        const cleanLine = line.replace(/^[-*•]\s*/, '');
        const colIndex = cleanLine.indexOf(':');
        if (colIndex > -1) {
          const key = cleanLine.slice(0, colIndex).trim();
          const val = cleanLine.slice(colIndex + 1).trim();
          html += `
            <div class="insight-stat-card">
              <div class="insight-stat-val">${escHtml(val)}</div>
              <div class="insight-stat-lbl">${escHtml(key)}</div>
            </div>
          `;
        }
      });
      html += `</div>`;
    } else {
      html += `
        <div class="card" style="padding: 16px; margin-bottom: 20px; border-color: var(--border-mid);">
          <h4 style="margin-bottom: 8px; color: var(--cyan);">📊 Dataset Metrics</h4>
          <div style="font-size: 0.9rem; line-height: 1.5;">${formatInsightsSubsections(statsText)}</div>
        </div>
      `;
    }
  }

  // 3. Strategic Insights List
  if (strategicText) {
    html += `<h4 style="margin-bottom: 12px; color: var(--violet-light); font-size: 1.05rem;">💡 Strategic Business Insights</h4>`;
    const numberedSplit = strategicText.split(/\n(?=\s*(?:\*{0,2}\d+[.):]\*{0,2}|#{1,3}\s))/);
    let items = [];
    if (numberedSplit.length > 1) {
      items = numberedSplit.map(s => s.replace(/^\s*(?:\*{0,2}\d+[.):]\*{0,2}|#{1,3})\s*/, '').trim()).filter(Boolean);
    } else {
      items = strategicText.split(/\n{2,}/).map(s => s.trim()).filter(Boolean);
    }

    const LABEL_CFG = [
      { re: /^(?:observation|finding|pattern)[s]?[:]/i,          cls: 'obs',   icon: '🔍', label: 'Observation' },
      { re: /^(?:business\s+)?implication[s]?[:]/i,              cls: 'impl',  icon: '💼', label: 'Implication' },
      { re: /^(?:actionable\s+)?strateg(?:y|ies)[:]/i,          cls: 'strat', icon: '🚀', label: 'Strategy' },
      { re: /^(?:recommendation|action|next\s+step)[s]?[:]/i,   cls: 'strat', icon: '✅', label: 'Recommendation' },
      { re: /^(?:risk|concern|warning)[s]?[:]/i,                 cls: 'impl',  icon: '⚠️', label: 'Risk' },
      { re: /^(?:kpi|metric|measure)[s]?[:]/i,                   cls: 'obs',   icon: '📊', label: 'Metric' },
    ];

    html += items.map((item, i) => {
      const parts = item.split('\n').map(p => p.trim()).filter(Boolean);
      const sectionHtml = parts.map(p => {
        for (const cfg of LABEL_CFG) {
          if (cfg.re.test(p)) {
            const body = p.replace(cfg.re, '').trim();
            return `<div class="insight-section">
              <div class="insight-section-label ${cfg.cls}">${cfg.icon} ${cfg.label}</div>
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
        <div class="insight-warning-card-icon">⚠️</div>
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
          <div class="chart-card-type">${typeLabel}</div>
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
      return `
        <div class="chart-card png-chart-card">
          <div class="chart-card-header">
            <div class="chart-card-title">${escHtml(title)}</div>
            <div class="chart-card-type">agent chart</div>
          </div>
          <div class="chart-card-body png-chart-body">
            <img
              src="/api/charts/${sessionId}/${encodeURIComponent(name)}"
              alt="${escHtml(title)}"
              class="png-chart-img"
              loading="lazy"
              onerror="this.parentNode.innerHTML='<div class=\'chart-img-error\'>📊 Chart not available yet — rerun analysis to generate.</div>'"
            />
          </div>
        </div>`;
    }).join('');
  } else {
    els.pngChartsWrap.classList.add('hidden');
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
  appendChatMsg('assistant', `👋 Hi! I'm your AI Data Copilot. Ask me anything about your dataset — aggregations, trends, plots, or specific columns.\n\nType **/** to insert a column name directly.`);
}

function appendChatMsg(role, content, plotUrl = null) {
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  const avatar = role === 'user' ? '👤' : '🤖';

  // Format markdown-ish content: wrap code blocks
  let formatted = escHtml(content)
    .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
    .replace(/`([^`]+)`/g, '<code style="background:var(--bg-surface);padding:1px 5px;border-radius:3px;font-family:var(--font-mono);font-size:0.85em">$1</code>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');

  div.innerHTML = `
    <div class="chat-avatar">${avatar}</div>
    <div class="chat-bubble">
      ${formatted}
      ${plotUrl ? `<img src="${plotUrl}" alt="Generated chart" />` : ''}
    </div>`;
  els.chatMessages.appendChild(div);
  els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
}

function showTypingIndicator() {
  const div = document.createElement('div');
  div.className = 'chat-msg assistant';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="chat-avatar">🤖</div>
    <div class="chat-bubble" style="color:var(--text-muted)">
      <span style="animation:pulse 1.2s infinite;display:inline-block">Analysing</span>…
    </div>`;
  els.chatMessages.appendChild(div);
  els.chatMessages.scrollTop = els.chatMessages.scrollHeight;
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
    toast('No API key set. Go to ⚙️ Settings to add your key.', 'warning');
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
      appendChatMsg('assistant', `⚠️ ${errMsg}`);
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
    appendChatMsg('assistant', '⚠ Network error: ' + e.message);
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

  picker.innerHTML = `<div class="col-picker-header">📌 Insert Column — type to filter</div>` +
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

  // Wire section switcher
  if (els.btnSectionChat) els.btnSectionChat.addEventListener('click', () => switchSection('chat'));
  if (els.btnSectionAgentic) els.btnSectionAgentic.addEventListener('click', () => switchSection('agentic'));

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

  // Check if a running session exists on page load
  // (handles F5 refresh during analysis)
  setTimeout(async () => {
    const projects = state.projects;
    const running = projects.find(p => p.status === 'running');
    if (running) switchToProject(running);
  }, 500);
})();
