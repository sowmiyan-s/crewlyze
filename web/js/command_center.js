/**
 * Crewlyze - 5-Crew Command Center & Analysis Modal Controller (ES6 Module)
 * Orchestrates the 5 clean analysis cards, detailed brief modal, CSV telemetry,
 * selective agent activation across all 5 crews, and execution pipeline.
 */

import { state } from './state.js';
import { downloadPdf } from './export_ui.js';

export const CREW_METADATA = {
  data_analysis: {
    id: 'data_analysis',
    stepNumber: 1,
    title: 'Data Analysis',
    icon: 'bar-chart-2',
    badge: 'Hygiene & Baseline Stats',
    color: 'var(--amber)',
    desc: 'Sanitizes anomalies, calculates statistical distributions, measures velocity trends, and sets baseline benchmarks.',
    brief: '<strong>Data Analysis Domain:</strong> Performs automated schema cleansing, sanitizes null and duplicate records, evaluates continuous feature distributions (IQR, skewness, variance), tracks velocity momentum over time, and synthesizes baseline empirical insights.',
    highlights: ['🧹 Automated Hygiene & Imputation', '📊 IQR Variance & Skewness', '📈 Velocity & Growth Momentum'],
    agents: [
      { id: 'data_cleaner', name: 'Data Cleaner', icon: '🧹', desc: 'Null imputation, deduplication & data type normalization' },
      { id: 'statistical_analysis', name: 'Statistical Analysis', icon: '📊', desc: 'IQR variance, quartiles, skewness & continuous dispersion' },
      { id: 'trend_analysis', name: 'Trend Analysis', icon: '📈', desc: 'Directional momentum, moving averages & growth velocity' },
      { id: 'comparative_analysis', name: 'Comparative Analysis', icon: '⚖️', desc: 'Cross-cohort benchmarks, categorical spreads & peer deltas' },
      { id: 'insight_discovery', name: 'Insight Discovery', icon: '💡', desc: 'High-leverage empirical findings & baseline discoveries' }
    ]
  },
  business_analysis: {
    id: 'business_analysis',
    stepNumber: 2,
    title: 'Business Analysis',
    icon: 'briefcase',
    badge: 'Commercial Levers & Margins',
    color: 'var(--emerald)',
    desc: 'Identifies revenue concentration, unit profitability, cost reduction targets, customer RFM, and decision models.',
    brief: '<strong>Business Analysis Domain:</strong> Evaluates your dataset from a strategic commercial perspective. Decomposes revenue via Pareto 80/20 analysis, inspects unit product margins, pinpoints operational expense creep, clusters customer retention loyalty tiers, and formulates an executive decision matrix.',
    highlights: ['💰 Pareto 80/20 Sales Decomp', '💵 Unit Profitability Margins', '👥 RFM Customer Loyalty Tiers'],
    agents: [
      { id: 'sales_analysis', name: 'Sales Analysis', icon: '💰', desc: 'Pareto 80/20 volume concentration, top performers & revenue splits' },
      { id: 'profitability_analysis', name: 'Profitability Analysis', icon: '💵', desc: 'Gross margin distribution, unit economics & profit drivers' },
      { id: 'expense_optimization', name: 'Expense Optimization', icon: '✂️', desc: 'Operational cost leaks, budget overruns & efficiency levers' },
      { id: 'customer_intelligence', name: 'Customer Intelligence', icon: '👥', desc: 'RFM segmentation, churn propensity & high-LTV identification' },
      { id: 'decision_support', name: 'Decision Support', icon: '🎯', desc: 'Prioritized McKinsey-style executive action matrix' }
    ]
  },
  data_mining: {
    id: 'data_mining',
    stepNumber: 3,
    title: 'Data Mining',
    icon: 'layers',
    badge: 'Structural Patterns & Clusters',
    color: 'var(--cyan)',
    desc: 'Discovers structural feature relationships, multivariate anomaly vectors, KMeans clusters, and affinity rules.',
    brief: '<strong>Data Mining Domain:</strong> Uses unsupervised machine learning to surface latent structures. Uncovers cross-feature correlation drivers via Pearson matrices, segments natural cohorts with KMeans clustering, isolates high-dimensional anomaly vectors, and mines transactional affinity rules.',
    highlights: ['🧩 Unsupervised Clustering', '🔗 Cross-Feature Correlations', '🛡️ Outlier & Anomaly Isolation'],
    agents: [
      { id: 'pattern_discovery', name: 'Pattern Discovery', icon: '🧩', desc: 'Unsupervised latent grouping & high-dimensional clustering' },
      { id: 'relationship_analysis', name: 'Relationship Analysis', icon: '🔗', desc: 'Multivariate correlation matrix & cross-feature drivers' },
      { id: 'segmentation', name: 'Segmentation', icon: '🏷️', desc: 'KMeans cohort clustering & multi-variable segment profiling' },
      { id: 'anomaly_detection', name: 'Anomaly Detection', icon: '🛡️', desc: 'Multivariate outlier isolation & statistical anomaly scoring' },
      { id: 'association_mining', name: 'Association Mining', icon: '🤝', desc: 'Market basket affinity rules & co-occurrence frequencies' }
    ]
  },
  predictive_analysis: {
    id: 'predictive_analysis',
    stepNumber: 4,
    title: 'Predictive Analysis',
    icon: 'cpu',
    badge: 'Auto-ML & Forecasts',
    color: '#c084fc',
    desc: 'Generates forward-looking revenue trajectories, optimal budget allocations, capacity demand, and risk scenarios.',
    brief: '<strong>Predictive Analysis Domain:</strong> Deploys predictive modeling to forecast upcoming trends and stress-test scenarios. Generates multi-period sales trajectories with confidence bands, recommends optimal budget run-rates, forecasts inventory demand buffers, and models downside Value-at-Risk (VaR).',
    highlights: ['📉 Multi-Period Sales Forecast', '🏦 Optimal Budget Allocation', '🎲 What-If Stress Testing'],
    agents: [
      { id: 'sales_forecasting', name: 'Sales Forecasting', icon: '📉', desc: 'Forward trajectory projections with statistical confidence bands' },
      { id: 'budget_forecasting', name: 'Budget Forecasting', icon: '🏦', desc: 'Capital run-rates & forward budget allocation modeling' },
      { id: 'demand_forecasting', name: 'Demand Forecasting', icon: '📦', desc: 'Operational capacity buffers & inventory demand modeling' },
      { id: 'risk_prediction', name: 'Risk Prediction', icon: '⚠️', desc: 'Downside Value-at-Risk (VaR) & volatility sensitivity scoring' },
      { id: 'whatif_simulation', name: 'What-If Simulation', icon: '🎲', desc: 'Scenario stress-testing & macroeconomic sensitivity simulation' }
    ]
  },
  eda: {
    id: 'eda',
    stepNumber: 5,
    title: 'Visuals & EDA',
    icon: 'trending-up',
    badge: 'Interactive Graphics & Story',
    color: '#38bdf8',
    desc: 'Constructs interactive Plotly visual charts, answers natural-language queries, audits schemas, and composes stories.',
    brief: '<strong>Exploratory Data Analysis (EDA) Domain:</strong> Profiles the full dataset schema and cardinality, renders interactive Plotly charts (bar, scatter, line, heatmaps), answers natural-language business questions using SQL, audits data integrity scores, and crafts a cohesive executive intelligence storyboard.',
    highlights: ['🎨 Interactive Plotly Visuals', '💬 Conversational SQL Queries', '📖 Strategic Intelligence Narrative'],
    agents: [
      { id: 'dataset_explorer', name: 'Dataset Explorer', icon: '🔭', desc: 'Complete schema exploration, cardinality & data profiling' },
      { id: 'natural_query', name: 'Natural-Language Query', icon: '💬', desc: 'Translates plain-English business queries into executable SQL' },
      { id: 'visualization', name: 'Visualization Agent', icon: '🎨', desc: 'Synthesizes interactive Plotly graphics & executive visuals' },
      { id: 'quality_inspector', name: 'Quality Inspector', icon: '🩺', desc: 'Systemic health scoring, schema anomalies & integrity checks' },
      { id: 'storytelling', name: 'Storytelling Agent', icon: '📖', desc: 'Cohesive executive intelligence narrative & storyboard' }
    ]
  }
};

export const CATEGORIES = ['data_analysis', 'business_analysis', 'data_mining', 'predictive_analysis', 'eda'];

// Set of all currently selected agents across all 5 crews
export const selectedAgentsSet = new Set([
  'data_cleaner', 'statistical_analysis', 'insight_discovery',
  'sales_analysis', 'profitability_analysis', 'customer_intelligence', 'decision_support',
  'relationship_analysis',
  'dataset_explorer', 'visualization', 'storytelling'
]);

let currentModalCrew = 'data_analysis';
let currentModalTab = 'data_analysis';
let onRunPipelineCallback = null;

/**
 * Returns all currently selected agent IDs.
 */
export function getSelectedAgents() {
  return Array.from(selectedAgentsSet);
}

/**
 * Returns all categories where at least one agent is selected.
 */
export function getSelectedCategories() {
  const cats = new Set();
  CATEGORIES.forEach(cat => {
    const agents = CREW_METADATA[cat]?.agents || [];
    if (agents.some(a => selectedAgentsSet.has(a.id))) {
      cats.add(cat);
    }
  });
  return Array.from(cats);
}

/**
 * Opens the Crew Analysis Detail & Agent Selection Modal
 * displaying brief info about the analysis, basic CSV telemetry,
 * and selective agents across the 5 crews.
 */
export function openCrewModal(category = 'data_analysis') {
  currentModalCrew = category;
  currentModalTab = category;

  const meta = CREW_METADATA[category] || CREW_METADATA.data_analysis;
  const modal = document.getElementById('crewDetailModal');
  if (!modal) return;

  // 1. Update Title, Domain Badge, and Icon
  const titleEl = document.getElementById('crewModalTitle');
  const badgeEl = document.getElementById('crewModalBadge');
  const iconWrap = document.getElementById('crewModalIconWrap');
  if (titleEl) titleEl.textContent = `${meta.stepNumber}. ${meta.title} Crew`;
  if (badgeEl) {
    badgeEl.textContent = meta.badge;
    badgeEl.style.color = meta.color;
  }
  if (iconWrap) {
    iconWrap.innerHTML = `<i data-lucide="${meta.icon}" style="width: 22px; height: 22px; color: ${meta.color};"></i>`;
  }

  // 2. Update Brief Info about the Analysis
  const briefEl = document.getElementById('crewModalBriefText');
  if (briefEl) {
    briefEl.innerHTML = `
      <p style="margin: 0 0 10px 0;">${meta.brief}</p>
      <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px;">
        ${meta.highlights.map(h => `<span class="highlight-chip" style="background: rgba(255,255,255,0.04);">${h}</span>`).join('')}
      </div>
    `;
  }

  // 3. Update Basic CSV Telemetry
  updateCrewModalTelemetry(state.activeProject);

  // 4. Update Modal Crew Switcher Tabs
  updateCrewModalTabs();

  // 5. Render Agents for the Active Tab
  renderCrewModalAgents(currentModalTab);

  // 6. Update Badges & Launch Button
  updateModalBadges();

  modal.classList.remove('hidden');
  modal.style.display = 'flex';

  if (window.lucide) {
    window.lucide.createIcons();
  }
}

/**
 * Closes the Crew Analysis Detail Modal.
 */
export function closeCrewModal() {
  const modal = document.getElementById('crewDetailModal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
}

/**
 * Updates basic CSV info inside the detail modal.
 */
export function updateCrewModalTelemetry(projectMeta) {
  const proj = projectMeta || state.activeProject || {};
  const filename = proj.filename || proj.name || 'dataset.csv';
  const rows = proj.rows_count ? proj.rows_count.toLocaleString() : '--';
  const cols = proj.cols_count ? proj.cols_count : (state.columns ? state.columns.length : '--');
  const num = proj.numeric_count || 0;
  const cat = proj.cat_count || Math.max(0, (proj.cols_count || 0) - num);
  const featStr = (proj.cols_count > 0) ? `${num} Numeric, ${cat} Categorical` : '--';

  const fnEl = document.getElementById('crewModalFileName');
  const rEl = document.getElementById('crewModalRows');
  const cEl = document.getElementById('crewModalCols');
  const fEl = document.getElementById('crewModalFeatures');
  const sEl = document.getElementById('crewModalStatus');

  if (fnEl) fnEl.textContent = filename;
  if (rEl) rEl.textContent = `${rows} rows`;
  if (cEl) cEl.textContent = `${cols} columns`;
  if (fEl) fEl.textContent = featStr;
  if (sEl) sEl.innerHTML = '<span style="color: #10b981;">● Ready</span>';
}

/**
 * Updates the 5 crew switcher tabs inside the modal.
 */
function updateCrewModalTabs() {
  const tabsContainer = document.getElementById('crewModalTabs');
  if (!tabsContainer) return;

  const tabButtons = tabsContainer.querySelectorAll('.crew-modal-tab');
  tabButtons.forEach(btn => {
    const crewId = btn.getAttribute('data-crew');
    btn.classList.toggle('active', crewId === currentModalTab);
  });
}

/**
 * Renders the selective agent items for the specified crew tab.
 */
export function renderCrewModalAgents(category) {
  currentModalTab = category;
  updateCrewModalTabs();

  const container = document.getElementById('crewModalAgentsList');
  if (!container) return;

  const meta = CREW_METADATA[category];
  if (!meta || !meta.agents) return;

  container.innerHTML = meta.agents.map(agent => {
    const isChecked = selectedAgentsSet.has(agent.id);
    return `
      <label class="crew-agent-item ${isChecked ? 'checked' : ''}" data-agent-id="${agent.id}">
        <input type="checkbox" name="crew_modal_agents" value="${agent.id}" ${isChecked ? 'checked' : ''} />
        <span style="font-size: 1.2rem; line-height: 1;">${agent.icon}</span>
        <div class="crew-agent-info" style="flex: 1;">
          <div class="crew-agent-name">${agent.name}</div>
          <div class="crew-agent-desc">${agent.desc}</div>
        </div>
      </label>
    `;
  }).join('');

  updateModalBadges();
}

/**
 * Updates the selected agents count badge and start analysis button text.
 */
function updateModalBadges() {
  const totalSelected = selectedAgentsSet.size;
  const meta = CREW_METADATA[currentModalTab];
  const tabAgents = meta?.agents || [];
  const tabSelectedCount = tabAgents.filter(a => selectedAgentsSet.has(a.id)).length;

  const badgeEl = document.getElementById('crewModalSelectedAgentsBadge');
  if (badgeEl) {
    badgeEl.textContent = `${tabSelectedCount}/${tabAgents.length} Active in Tab (${totalSelected} Total)`;
  }

  const btnText = document.getElementById('startCrewAnalysisBtnText');
  if (btnText) {
    btnText.textContent = `Start Analysis (${totalSelected} Agents Selected)`;
  }

  // Update top active badge if present
  const topBadge = document.getElementById('activeAgentsBadgeTop');
  if (topBadge) {
    topBadge.textContent = `${totalSelected} of 25 Agents Active`;
  }
}

/**
 * Toggles all agents in the current active modal tab.
 */
export function toggleSelectAllInCrew(selectAll = true) {
  const meta = CREW_METADATA[currentModalTab];
  if (!meta || !meta.agents) return;

  meta.agents.forEach(agent => {
    if (selectAll) {
      selectedAgentsSet.add(agent.id);
    } else {
      selectedAgentsSet.delete(agent.id);
    }
  });

  renderCrewModalAgents(currentModalTab);
}

/**
 * Updates telemetry on the main cards and workspace hub.
 */
export function updateCardsDatasetInfo(metadata) {
  const meta = metadata || state.activeProject || {};
  const filename = meta.filename || meta.name || 'dataset.csv';
  const rows = meta.rows_count ? meta.rows_count.toLocaleString() : '--';
  const cols = meta.cols_count ? meta.cols_count : (state.columns ? state.columns.length : '--');

  // Hub banner
  const hubFn = document.getElementById('hubDatasetFilename');
  const hubDims = document.getElementById('hubDatasetDims');
  if (hubFn) hubFn.textContent = filename;
  if (hubDims) hubDims.textContent = `${rows} rows × ${cols} cols`;

  // Agentic summary pill
  const pillText = document.getElementById('agenticDatasetSummaryText');
  if (pillText) {
    pillText.textContent = `Dataset: ${filename} (${rows} rows × ${cols} columns)`;
  }

  // Modal telemetry
  updateCrewModalTelemetry(meta);
}

/**
 * Initializes all event listeners for the 5-Crew Command Center and detail modal.
 */
export function initCommandCenter(openConfigModalFn, onRunPipelineFn) {
  onRunPipelineCallback = onRunPipelineFn;

  // 1. Click on any of the 5 usecase cards -> opens Crew Detail Modal
  document.addEventListener('click', e => {
    const card = e.target.closest('.usecase-card');
    if (card) {
      const cat = card.getAttribute('data-step');
      if (cat && CREW_METADATA[cat]) {
        openCrewModal(cat);
      }
    }
  });

  // 2. Modal Close / Cancel Buttons
  document.addEventListener('click', e => {
    if (e.target.closest('#closeCrewModal') || e.target.closest('#cancelCrewModalBtn')) {
      closeCrewModal();
    } else if (e.target === document.getElementById('crewDetailModal')) {
      closeCrewModal();
    }
  });

  // 3. Crew Modal Tabs Switcher
  document.addEventListener('click', e => {
    const tabBtn = e.target.closest('.crew-modal-tab');
    if (tabBtn) {
      const crewId = tabBtn.getAttribute('data-crew');
      if (crewId && CREW_METADATA[crewId]) {
        renderCrewModalAgents(crewId);
      }
    }
  });

  // 4. Modal "Select All in Crew" / "Deselect All" Buttons
  document.addEventListener('click', e => {
    if (e.target.closest('#crewModalSelectAllBtn')) {
      toggleSelectAllInCrew(true);
    } else if (e.target.closest('#crewModalDeselectAllBtn')) {
      toggleSelectAllInCrew(false);
    }
  });

  // 4b. Modal "Export Dedicated PDF" Button
  document.addEventListener('click', e => {
    if (e.target.closest('#exportCrewPdfBtn')) {
      const meta = CREW_METADATA[currentModalTab];
      const tabAgents = meta?.agents || [];
      const selectedInTab = tabAgents.filter(a => selectedAgentsSet.has(a.id));
      const targetAid = selectedInTab.length > 0 ? selectedInTab[0].id : (tabAgents[0]?.id || currentModalTab);
      downloadPdf(null, `${meta?.title || 'Crew'} Dedicated Report`, targetAid);
    }
  });

  // 5. Agent item checkbox change inside modal
  document.addEventListener('change', e => {
    if (e.target.name === 'crew_modal_agents') {
      const agentId = e.target.value;
      if (e.target.checked) {
        selectedAgentsSet.add(agentId);
      } else {
        selectedAgentsSet.delete(agentId);
      }
      e.target.closest('.crew-agent-item')?.classList.toggle('checked', e.target.checked);
      updateModalBadges();
    }
  });

  // 6. Analysis Depth Chips inside modal
  document.addEventListener('click', e => {
    const depthChip = e.target.closest('.depth-chip');
    if (depthChip) {
      document.querySelectorAll('.depth-chip').forEach(c => c.classList.remove('active'));
      depthChip.classList.add('active');
      const radio = depthChip.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    }
  });

  // 7. Start Analysis Button inside Modal
  document.addEventListener('click', e => {
    if (e.target.closest('#startCrewAnalysisBtn')) {
      const selected = getSelectedAgents();
      if (!selected.length) {
        if (typeof window.toast === 'function') {
          window.toast('Please select at least 1 agent to start the analysis.', 'warning');
        } else {
          alert('Please select at least 1 agent to start the analysis.');
        }
        return;
      }

      closeCrewModal();

      const depthRadio = document.querySelector('input[name="crewDepth"]:checked');
      const isDeep = depthRadio ? depthRadio.value === 'true' : false;
      const objectiveText = document.getElementById('crewModalObjective')?.value || '';

      if (typeof onRunPipelineCallback === 'function') {
        onRunPipelineCallback({
          category: currentModalCrew,
          agents: selected,
          deep: isDeep,
          goal: objectiveText
        });
      }
    }
  });

  // 8. "Run All 25 Agents" Swarm Button in header
  document.addEventListener('click', e => {
    if (e.target.closest('#btnRunAgenticPipeline')) {
      // Select all 25 agents
      CATEGORIES.forEach(c => {
        CREW_METADATA[c]?.agents?.forEach(a => selectedAgentsSet.add(a.id));
      });
      if (typeof onRunPipelineCallback === 'function') {
        onRunPipelineCallback({
          agents: getSelectedAgents()
        });
      }
    }
  });

  // Initial update
  updateCardsDatasetInfo();
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

export function updateActiveAgentsBadge() {
  const count = selectedAgentsSet.size;
  const badge = document.getElementById('activeAgentsBadge');
  if (badge) badge.textContent = `${count} of 25 Active Agents`;
}

export function applyAnalysisPreset(preset) {
  const PRESET_MAP = {
    growth_bi: ['data_cleaner', 'statistical_analysis', 'insight_discovery', 'sales_analysis', 'profitability_analysis', 'customer_intelligence', 'decision_support', 'relationship_analysis', 'dataset_explorer', 'visualization', 'storytelling'],
    quick_brief: ['data_cleaner', 'statistical_analysis', 'insight_discovery', 'sales_analysis', 'decision_support', 'dataset_explorer', 'visualization', 'storytelling'],
    deep_mining: ['data_cleaner', 'statistical_analysis', 'pattern_discovery', 'relationship_analysis', 'segmentation', 'anomaly_detection', 'association_mining', 'dataset_explorer', 'visualization'],
    predictive_suite: ['dataset_explorer', 'trend_analysis', 'sales_forecasting', 'budget_forecasting', 'demand_forecasting', 'risk_prediction', 'whatif_simulation', 'visualization'],
    full_audit: 'all'
  };

  const targetList = PRESET_MAP[preset] || PRESET_MAP.growth_bi;
  selectedAgentsSet.clear();
  CATEGORIES.forEach(c => {
    CREW_METADATA[c]?.agents?.forEach(a => {
      if (targetList === 'all' || targetList.includes(a.id)) {
        selectedAgentsSet.add(a.id);
      }
    });
  });

  updateActiveAgentsBadge();
}
