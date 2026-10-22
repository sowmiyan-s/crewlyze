/**
 * Crewlyze - 25-Agent 5-Step Command Center (ES6 Module)
 * Orchestrates use case cards, embedded dataset telemetry, agent selection chips, presets, and isolated step runs.
 */

import { state } from './state.js';

export const PRESET_MAP = {
  growth_bi: ['data_cleaner', 'dataset_explorer', 'sales_analysis', 'profitability_analysis', 'customer_intelligence', 'relationship_analysis', 'visualization', 'decision_support', 'storytelling'],
  quick_brief: ['dataset_explorer', 'quality_inspector', 'statistical_analysis', 'visualization', 'insight_discovery', 'storytelling'],
  deep_mining: ['data_cleaner', 'statistical_analysis', 'pattern_discovery', 'relationship_analysis', 'segmentation', 'anomaly_detection', 'association_mining', 'risk_prediction', 'visualization'],
  predictive_suite: ['dataset_explorer', 'trend_analysis', 'sales_forecasting', 'budget_forecasting', 'demand_forecasting', 'risk_prediction', 'whatif_simulation', 'visualization'],
  full_audit: 'all'
};

const CATEGORIES = ['data_analysis', 'business_analysis', 'data_mining', 'predictive_analysis', 'eda'];

/**
 * Updates the global agent count badges and each individual card's selected agent counter badge and toggle button text.
 */
export function updateActiveAgentsBadge() {
  const uniqueChecked = new Set();
  document.querySelectorAll('input[name="agents"]:checked').forEach(cb => uniqueChecked.add(cb.value));
  const count = uniqueChecked.size;
  const totalPossible = 25;

  const badge = document.getElementById('selectedAgentsCount');
  if (badge) {
    badge.textContent = `Selected (${count}/${totalPossible})`;
  }

  const topBadge = document.getElementById('activeAgentsBadgeTop');
  if (topBadge) {
    topBadge.textContent = `${count} of ${totalPossible} Agents Active`;
  }

  // Update each of the 5 individual use case cards
  CATEGORIES.forEach(cat => {
    const card = document.querySelector(`.usecase-card[data-step="${cat}"]`);
    if (card) {
      const agentCbs = card.querySelectorAll('input[name="agents"]');
      const activeCount = Array.from(agentCbs).filter(cb => cb.checked).length;
      
      // Update card counter badge (e.g. "3/5 Selected")
      const countEl = card.querySelector(`.card-agent-badge[data-badge-for="${cat}"]`) || card.querySelector('.card-agent-badge');
      if (countEl) {
        countEl.textContent = `${activeCount}/${agentCbs.length} Selected`;
      }

      // Update card toggle button text
      const toggleBtn = card.querySelector(`.btn-card-toggle[data-cat="${cat}"]`) || card.querySelector('.btn-card-toggle');
      if (toggleBtn) {
        toggleBtn.textContent = (activeCount === agentCbs.length && agentCbs.length > 0) ? 'Deselect All' : 'Select All';
      }
    }
  });
}

/**
 * Dynamically updates the embedded Database Telemetry info strip on each of the 5 cards
 * based on the active dataset's shape, filename, and detected columns.
 */
export function updateCardsDatasetInfo(metadata) {
  const meta = metadata || state.activeProject || {};
  const filename = meta.filename || meta.name || 'Active Dataset';
  const rows = meta.rows_count || 0;
  const cols = meta.cols_count || (state.columns ? state.columns.length : 0);
  const numeric = meta.numeric_count || 0;
  const cat = meta.cat_count || Math.max(0, cols - numeric);
  const hasData = Boolean(rows > 0 || cols > 0 || meta.id || state.uploadedSession);

  CATEGORIES.forEach(c => {
    const card = document.querySelector(`.usecase-card[data-step="${c}"]`);
    if (!card) return;

    const fileEl = card.querySelector('.db-val-file');
    const dimsEl = card.querySelector('.db-val-dims');
    const focusEl = card.querySelector('.db-val-focus');
    const statusEl = card.querySelector('.db-meta-status');

    if (fileEl) fileEl.textContent = hasData ? filename : 'No dataset loaded';
    if (statusEl) {
      statusEl.textContent = hasData ? '● Ready' : '○ Idle';
      statusEl.className = hasData ? 'db-meta-status ready' : 'db-meta-status';
    }

    if (c === 'data_analysis') {
      if (dimsEl) dimsEl.textContent = hasData ? `${rows.toLocaleString()} rows × ${cols} columns` : '-- rows × -- cols';
      if (focusEl) focusEl.textContent = hasData ? `${numeric} numeric, ${cat} categorical • Hygiene ready` : 'Null audit, IQR outliers & sanitization';
    } else if (c === 'business_analysis') {
      if (dimsEl) dimsEl.textContent = hasData ? `${rows.toLocaleString()} transactions mapped` : '-- transactions';
      if (focusEl) focusEl.textContent = hasData ? 'Pareto 80/20, unit margins & RFM tiers' : 'Commercial levers & unit economics';
    } else if (c === 'data_mining') {
      if (dimsEl) dimsEl.textContent = hasData ? `${numeric} continuous feature dimensions` : '-- feature dimensions';
      if (focusEl) focusEl.textContent = hasData ? 'Pearson matrix, outlier vectors & KMeans' : 'Feature correlation matrix & clusters';
    } else if (c === 'predictive_analysis') {
      if (dimsEl) dimsEl.textContent = hasData ? '4-Period forward trajectory & bounds' : '4-period projection horizon';
      if (focusEl) focusEl.textContent = hasData ? 'Linear regression, downside VaR & stress tests' : 'Trend extrapolation & downside risk';
    } else if (c === 'eda') {
      if (dimsEl) dimsEl.textContent = hasData ? `${cols} chartable visual dimensions` : '-- visualizable columns';
      if (focusEl) focusEl.textContent = hasData ? 'Plotly interactive charts & Storyboard' : 'Interactive graphics & executive narrative';
    }
  });
}

/**
 * Applies a global analysis preset across all 5 cards.
 */
export function applyAnalysisPreset(preset) {
  const targetList = PRESET_MAP[preset] || PRESET_MAP.growth_bi;
  const checkboxes = document.querySelectorAll('input[name="agents"]');

  checkboxes.forEach(cb => {
    const isTarget = (targetList === 'all' || targetList.includes(cb.value));
    cb.checked = isTarget;
    cb.closest('.agent-chip')?.classList.toggle('checked', isTarget);
  });

  updateActiveAgentsBadge();
}

/**
 * Returns all currently selected agent IDs across the system.
 */
export function getSelectedAgents() {
  const selected = new Set();
  document.querySelectorAll('input[name="agents"]:checked').forEach(cb => selected.add(cb.value));
  return Array.from(selected);
}

/**
 * Returns all categories where at least one agent is checked.
 */
export function getSelectedCategories() {
  const selected = new Set();
  CATEGORIES.forEach(cat => {
    const card = document.querySelector(`.usecase-card[data-step="${cat}"]`);
    if (card) {
      const anyChecked = Array.from(card.querySelectorAll('input[name="agents"]')).some(cb => cb.checked);
      if (anyChecked) selected.add(cat);
    }
  });
  return Array.from(selected);
}

/**
 * Initializes the Command Center event listeners for presets, card-level agent toggling,
 * and isolated step-run triggers.
 */
export function initCommandCenter(openConfigModalFn, onRunPipelineFn) {
  // 1. Full Swarm Run Buttons Listener
  document.addEventListener('click', e => {
    if (e.target.closest('#btnRunAgenticPipeline') || e.target.closest('#startAnalysisBtn') || e.target.closest('#runAnalysisBtn')) {
      if (typeof onRunPipelineFn === 'function') {
        const allAgents = getSelectedAgents();
        if (!allAgents.length) {
          if (typeof window.toast === 'function') {
            window.toast('Please select at least 1 agent to run analysis.', 'warning');
          } else {
            alert('Please select at least 1 agent to run analysis.');
          }
          return;
        }
        onRunPipelineFn({ agents: allAgents });
      }
    }
  });

  // 2. Preset Chips Listener
  document.addEventListener('click', e => {
    const btn = e.target.closest('.preset-chip');
    if (!btn) return;
    const preset = btn.getAttribute('data-preset');
    document.querySelectorAll('.preset-chip').forEach(b => {
      b.classList.toggle('active', b.getAttribute('data-preset') === preset);
    });
    applyAnalysisPreset(preset);
  });

  // 3. Card-Level "Select All / Deselect All" Toggle Listener
  document.addEventListener('click', e => {
    const toggleBtn = e.target.closest('.btn-card-toggle');
    if (!toggleBtn) return;
    const cat = toggleBtn.getAttribute('data-cat');
    if (!cat) return;

    const card = document.querySelector(`.usecase-card[data-step="${cat}"]`);
    if (!card) return;

    const agentCbs = card.querySelectorAll('input[name="agents"]');
    const allChecked = Array.from(agentCbs).every(cb => cb.checked);
    const newCheckedState = !allChecked;

    agentCbs.forEach(cb => {
      cb.checked = newCheckedState;
      cb.closest('.agent-chip')?.classList.toggle('checked', newCheckedState);
    });

    // Remove active preset highlight since user customized
    document.querySelectorAll('.preset-chip').forEach(b => b.classList.remove('active'));

    updateActiveAgentsBadge();
  });

  // 4. Individual Card "⚡ Run Step [X] Analysis" Button Listener
  document.addEventListener('click', e => {
    const stepBtn = e.target.closest('.btn-step-run');
    if (!stepBtn) return;
    const cat = stepBtn.getAttribute('data-cat');
    if (!cat) return;

    const card = document.querySelector(`.usecase-card[data-step="${cat}"]`);
    if (!card) return;

    const checkedAgents = Array.from(card.querySelectorAll('input[name="agents"]:checked')).map(cb => cb.value);
    
    if (!checkedAgents.length) {
      const stepName = cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      if (typeof window.toast === 'function') {
        window.toast(`Please select at least 1 agent in Step ${stepName} to run.`, 'warning');
      } else {
        alert(`Please select at least 1 agent in Step ${stepName} to run.`);
      }
      return;
    }

    const sessionId = state.activeProject?.id || state.uploadedSession;
    if (!sessionId) {
      if (typeof window.toast === 'function') {
        window.toast('Please upload or select a dataset first.', 'error');
      }
      if (typeof openConfigModalFn === 'function') openConfigModalFn();
      return;
    }

    // Launch pipeline specifically for this use-case step and its checked agents
    if (typeof onRunPipelineFn === 'function') {
      onRunPipelineFn({ category: cat, agents: checkedAgents });
    }
  });

  // 5. Individual Agent Chip Checkbox Listener
  document.addEventListener('change', e => {
    const agentCb = e.target.closest('input[name="agents"]');
    if (!agentCb) return;

    agentCb.closest('.agent-chip')?.classList.toggle('checked', agentCb.checked);

    // Sync any other checkboxes with the same agent ID (e.g. if present in multiple modals)
    document.querySelectorAll(`input[name="agents"][value="${agentCb.value}"]`).forEach(cb => {
      if (cb !== agentCb) {
        cb.checked = agentCb.checked;
        cb.closest('.agent-chip')?.classList.toggle('checked', agentCb.checked);
      }
    });

    // Remove active preset highlight since user customized
    document.querySelectorAll('.preset-chip').forEach(b => b.classList.remove('active'));

    updateActiveAgentsBadge();
  });

  // Initial badge update
  updateActiveAgentsBadge();
  updateCardsDatasetInfo();
}
