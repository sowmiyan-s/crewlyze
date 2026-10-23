/**
 * Crewlyze - Dashboard & Preview UI Controller (ES6 Module)
 * Manages domain tabs, metric cards, preview table sorting/filtering, and column action modals.
 */

import { state, $, $$, escHtml } from './state.js';
import { resizeAllCharts } from './charts.js';
import { downloadPdf } from './export_ui.js';

export function switchTab(tabId) {
  $$('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
  });
  $$('.tab-panel').forEach(panel => {
    const isTarget = (panel.id === tabId || panel.id === `panel-${tabId}`);
    panel.classList.toggle('active', isTarget);
    if (isTarget) {
      panel.style.display = 'block';
    } else {
      panel.style.display = 'none';
    }
  });

  // Auto-resize Plotly charts in target tab to eliminate 0-width glitches
  setTimeout(() => {
    resizeAllCharts();
  }, 50);
}

export function initTabs() {
  document.addEventListener('click', e => {
    const btn = e.target.closest('.tab-btn');
    if (!btn) return;
    const tabId = btn.getAttribute('data-tab');
    if (tabId) {
      switchTab(tabId);
    }
  });
}

export function renderStats(data) {
  const row = $('statsRow');
  if (!row) return;
  const stats = [
    { val: (data.rows_count || 0).toLocaleString(), lbl: 'Total Records', color: 'var(--violet)' },
    { val: data.cols_count || 0, lbl: 'Total Columns', color: 'var(--cyan)' },
    { val: data.numeric_count || 0, lbl: 'Numeric Fields', color: 'var(--emerald)' },
    { val: data.cat_count || 0, lbl: 'Categorical Fields', color: 'var(--amber)' },
    { val: (data.plotly_charts || []).length, lbl: 'Interactive Charts', color: 'var(--rose)' },
  ];
  row.innerHTML = stats.map(s => `
    <div class="stat-card" style="--accent:${s.color}">
      <div class="stat-val">${s.val}</div>
      <div class="stat-lbl">${s.lbl}</div>
      <div class="stat-accent-bar"></div>
    </div>
  `).join('');
}

function getColumnType(rows, col) {
  for (let i = 0; i < Math.min(rows.length, 10); i++) {
    const val = rows[i]?.[col];
    if (val === null || val === undefined || val === '') continue;
    if (!isNaN(Number(val))) return 'num';
    if (!isNaN(Date.parse(val)) && String(val).length > 6) return 'date';
  }
  return 'txt';
}

export function renderPreviewTableCore() {
  const container = document.getElementById('previewTable');
  if (!container) return;

  let rows = [...(state.rawPreviewRows || [])];
  if (!rows.length) {
    container.innerHTML = '<p style="color:var(--text-muted);padding:16px">No preview data.</p>';
    const countTag = document.getElementById('previewTableRowCount');
    if (countTag) countTag.textContent = 'Rows: 0';
    return;
  }

  if (state.searchQuery) {
    const q = state.searchQuery.toLowerCase();
    rows = rows.filter(row =>
      Object.values(row).some(v => String(v ?? '').toLowerCase().includes(q))
    );
  }

  if (state.sortCol) {
    const col = state.sortCol;
    const dir = state.sortDir === 'asc' ? 1 : -1;
    rows.sort((a, b) => {
      const valA = a[col] ?? '';
      const valB = b[col] ?? '';
      const numA = Number(valA);
      const numB = Number(valB);
      if (!isNaN(numA) && !isNaN(numB)) {
        return (numA - numB) * dir;
      }
      return String(valA).localeCompare(String(valB)) * dir;
    });
  }

  const cols = state.columns || Object.keys(rows[0] || {});
  
  const thead = `<thead><tr>${cols.map(c => {
    const type = getColumnType(state.rawPreviewRows, c);
    const isSorted = state.sortCol === c;
    const arrow = isSorted ? (state.sortDir === 'asc' ? ' ▲' : ' ▼') : '';
    const badgeLabel = type === 'num' ? 'NUM' : type === 'date' ? 'DATE' : 'TXT';
    return `<th class="sortable-header" data-col="${c}" title="Click to sort by ${c}">
      ${c} <span class="col-type-badge ${type}">${badgeLabel}</span><span style="color:#ff6b6e;font-size:0.75rem;">${arrow}</span>
    </th>`;
  }).join('')}</tr></thead>`;

  const tbody = `<tbody>${rows.map(row =>
    `<tr>${cols.map(c => `<td title="${row[c] ?? ''}">${row[c] ?? ''}</td>`).join('')}</tr>`
  ).join('')}</tbody>`;

  container.innerHTML = `<table class="data-table">${thead}${tbody}</table>`;

  const countTag = document.getElementById('previewTableRowCount');
  if (countTag) {
    const totalRecs = state.totalDatasetRows || (state.results && state.results.rows_count) || (state.activeProject && state.activeProject.rows_count) || state.rawPreviewRows.length;
    if (totalRecs > rows.length) {
      countTag.innerHTML = `Showing first <strong>${rows.length}</strong> preview rows of <strong>${totalRecs.toLocaleString()}</strong> total dataset records`;
    } else {
      countTag.innerHTML = `Showing all <strong>${rows.length}</strong> dataset records`;
    }
  }

  container.querySelectorAll('th.sortable-header').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.getAttribute('data-col');
      if (state.sortCol === col) {
        state.sortDir = state.sortDir === 'asc' ? 'desc' : 'asc';
      } else {
        state.sortCol = col;
        state.sortDir = 'asc';
      }
      renderPreviewTableCore();
    });
  });
}

export function renderPreview(rows) {
  state.rawPreviewRows = rows || [];
  if (rows && rows.length) {
    state.columns = Object.keys(rows[0]);
  }
  renderPreviewTableCore();
}

export function renderCategories(categories) {
  if (!categories || typeof categories !== 'object') return;

  const domainGridMap = {
    data_analysis: $('dataAnalysisCardsGrid'),
    business_analysis: $('businessAnalysisCardsGrid'),
    data_mining: $('dataMiningCardsGrid'),
    predictive_analysis: $('predictiveAnalysisCardsGrid'),
    eda: $('edaCardsGrid'),
  };

  const domainIcons = {
    data_cleaner: '🧹',
    statistical_analysis: '📊',
    trend_analysis: '📈',
    comparative_analysis: '⚖️',
    insight_discovery: '💡',
    sales_analysis: '💰',
    profitability_analysis: '💵',
    expense_optimization: '✂️',
    customer_intelligence: '👥',
    decision_support: '🎯',
    pattern_discovery: '🧩',
    relationship_analysis: '🔗',
    segmentation: '🏷️',
    anomaly_detection: '🛡️',
    association_mining: '🤝',
    sales_forecasting: '📉',
    budget_forecasting: '🏦',
    demand_forecasting: '📦',
    risk_prediction: '⚠️',
    whatif_simulation: '🎲',
    dataset_explorer: '🔭',
    natural_query: '💬',
    visualization: '🎨',
    quality_inspector: '🩺',
    storytelling: '📖',
  };

  Object.entries(domainGridMap).forEach(([domain, gridEl]) => {
    if (!gridEl) return;
    const agentsList = categories[domain] || [];
    if (!agentsList.length) {
      gridEl.innerHTML = '<div style="grid-column: 1/-1; padding: 24px; text-align: center; color: var(--text-secondary); background: rgba(255,255,255,0.01); border-radius: var(--r-md); border: 1px dashed var(--border-low);">No agents in this category were executed for this run.</div>';
      return;
    }

    gridEl.innerHTML = agentsList.map(agent => {
      const icon = domainIcons[agent.agent_id] || '⚡';
      const statusBadge = agent.status === 'completed'
        ? '<span style="font-size:0.7rem; padding: 2px 8px; border-radius: 12px; background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); font-weight: 600;">✓ Completed</span>'
        : (agent.status === 'ineligible'
          ? '<span style="font-size:0.7rem; padding: 2px 8px; border-radius: 12px; background: rgba(255,255,255,0.06); color: var(--text-secondary); border: 1px solid var(--border-low);">⚪ Skipped</span>'
          : '<span style="font-size:0.7rem; padding: 2px 8px; border-radius: 12px; background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); font-weight: 600;">❌ Error</span>');

      const metricsChips = Object.entries(agent.metrics || {}).map(([k, v]) => {
        const cleanK = k.replace(/_/g, ' ');
        const cleanV = typeof v === 'number' ? v.toLocaleString() : v;
        return `<span style="font-size:0.73rem; background: rgba(255,255,255,0.04); border: 1px solid var(--border-low); padding: 3px 8px; border-radius: 4px; color: var(--text-primary);"><strong style="color:var(--text-secondary); font-weight:500;">${cleanK}:</strong> ${cleanV}</span>`;
      }).join(' ');

      const findingsHtml = (agent.findings || []).map(f => {
        return `<li style="margin-bottom: 6px; font-size: 0.83rem; line-height: 1.5; color: #e4e4e7;">${escHtml(f)}</li>`;
      }).join('');

      let tablesHtml = '';
      if (agent.tables && agent.tables.length) {
        tablesHtml = agent.tables.map(tbl => {
          const rows = tbl.rows || [];
          if (!rows.length) return '';
          const keys = Object.keys(rows[0]).slice(0, 5);
          const thead = keys.map(k => `<th style="padding: 6px 8px; text-align: left; font-size: 0.72rem; color: var(--text-secondary); border-bottom: 1px solid var(--border-low); text-transform: uppercase;">${k.replace(/_/g, ' ')}</th>`).join('');
          const tbody = rows.slice(0, 5).map(r => {
            const cells = keys.map(k => `<td style="padding: 6px 8px; font-size: 0.78rem; border-bottom: 1px solid rgba(255,255,255,0.02);">${typeof r[k] === 'number' ? r[k].toLocaleString() : escHtml(String(r[k]))}</td>`).join('');
            return `<tr>${cells}</tr>`;
          }).join('');
          return `
            <div style="margin-top: 10px; background: rgba(0,0,0,0.2); border-radius: var(--r-sm); border: 1px solid var(--border-low); overflow-x: auto;">
              <div style="font-size: 0.74rem; font-weight: 700; color: #fff; padding: 6px 8px; border-bottom: 1px solid var(--border-low);">${tbl.title || 'Summary Table'}</div>
              <table style="width: 100%; border-collapse: collapse;">
                <thead><tr>${thead}</tr></thead>
                <tbody>${tbody}</tbody>
              </table>
            </div>`;
        }).join('');
      }

      const artifactsHtml = (agent.artifacts && agent.artifacts.length)
        ? `<div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 6px; padding-top: 8px; border-top: 1px dashed var(--border-low);">
            ${agent.artifacts.map(a => `
              <a href="${a.download_url}" download class="artifact-download-chip" style="font-size: 0.72rem; padding: 4px 10px; background: rgba(255,37,42,0.06); border: 1px solid rgba(255,37,42,0.25); color: var(--crimson, #ff252a); border-radius: 4px; text-decoration: none; display: inline-flex; align-items: center; gap: 4px; font-weight: 600;">
                📥 ${escHtml(a.title || a.artifact_key)} <span style="opacity: 0.7; font-size: 0.65rem;">(${a.size_bytes ? (a.size_bytes < 1024 ? a.size_bytes + ' B' : (a.size_bytes / 1024).toFixed(1) + ' KB') : 'CSV'})</span>
              </a>
            `).join('')}
          </div>`
        : '';

      const pdfBtnHtml = (agent.status === 'completed')
        ? `<button type="button" class="btn-agent-pdf-export btn-secondary btn-xs" data-agent-id="${agent.agent_id}" style="align-self: flex-start; margin-top: 4px; display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; padding: 4px 10px; background: rgba(255,255,255,0.03); border: 1px solid var(--border-low); color: var(--text-primary); border-radius: 4px; cursor: pointer;">
            📄 Export ${agent.name || 'Agent'} PDF
          </button>`
        : '';

      return `
        <div class="card agent-delivery-card" style="padding: 18px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-low); border-radius: var(--r-md); display: flex; flex-direction: column; gap: 12px; transition: all 0.2s;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-low); padding-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.2rem;">${icon}</span>
              <div>
                <h4 style="margin: 0; font-size: 0.95rem; font-weight: 700; color: #fff;">${agent.name || agent.agent_id}</h4>
                <span style="font-size: 0.72rem; color: var(--text-secondary); text-transform: uppercase;">${agent.category?.replace(/_/g, ' ')} • ${agent.execution_time ? agent.execution_time.toFixed(2) + 's' : ''}</span>
              </div>
            </div>
            ${statusBadge}
          </div>
          ${agent.narrative ? `<p style="margin: 0; font-size: 0.84rem; color: var(--text-secondary); line-height: 1.5;">${escHtml(agent.narrative)}</p>` : ''}
          ${metricsChips ? `<div style="display: flex; flex-wrap: wrap; gap: 6px;">${metricsChips}</div>` : ''}
          ${findingsHtml ? `<ul style="margin: 0; padding-left: 18px;">${findingsHtml}</ul>` : ''}
          ${tablesHtml}
          ${artifactsHtml}
          ${pdfBtnHtml}
        </div>
      `;
    }).join('');
  });
}

export function renderStoryboard(data) {
  const narrEl = $('storyboardNarrativeText');
  if (narrEl) {
    narrEl.textContent = data.executive_narrative || (data.executive_findings && data.executive_findings[0]) || 'Analysis complete with verified multi-agent findings.';
  }

  const container = $('insightsContent');
  if (!container) return;

  const findings = data.executive_findings || [];
  if (!findings.length && !data.insights) {
    container.innerHTML = '<p style="color:var(--text-muted);padding:16px;">No executive insights generated.</p>';
    return;
  }

  // Render McKinsey-style 3-panel cards if findings available
  if (findings.length >= 3) {
    const cards = [];
    for (let i = 0; i < findings.length; i += 3) {
      const obs = findings[i] || 'Observed operational benchmark.';
      const imp = findings[i + 1] || 'Commercial impact observed across primary metrics.';
      const act = findings[i + 2] || 'Execute strategic optimization to capture upside.';
      cards.push(`
        <div class="insight-card" style="margin-bottom: 16px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-low); border-radius: var(--r-md); overflow: hidden;">
          <div style="display: flex; border-bottom: 1px solid var(--border-low); flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px; padding: 14px; border-right: 1px solid var(--border-low); background: rgba(59, 130, 246, 0.03);">
              <span style="font-size: 0.72rem; font-weight: 700; color: #60a5fa; text-transform: uppercase;">📊 Observation</span>
              <p style="margin: 6px 0 0; font-size: 0.84rem; line-height: 1.5; color: #f4f4f5;">${escHtml(obs)}</p>
            </div>
            <div style="flex: 1; min-width: 200px; padding: 14px; border-right: 1px solid var(--border-low); background: rgba(245, 158, 11, 0.03);">
              <span style="font-size: 0.72rem; font-weight: 700; color: #fbbf24; text-transform: uppercase;">💡 Implication</span>
              <p style="margin: 6px 0 0; font-size: 0.84rem; line-height: 1.5; color: #f4f4f5;">${escHtml(imp)}</p>
            </div>
            <div style="flex: 1; min-width: 200px; padding: 14px; background: rgba(16, 185, 129, 0.03);">
              <span style="font-size: 0.72rem; font-weight: 700; color: #34d399; text-transform: uppercase;">🎯 Actionable Strategy</span>
              <p style="margin: 6px 0 0; font-size: 0.84rem; line-height: 1.5; color: #f4f4f5;">${escHtml(act)}</p>
            </div>
          </div>
        </div>
      `);
    }
    container.innerHTML = cards.join('');
  } else if (data.insights) {
    container.innerHTML = `<div style="padding:16px;line-height:1.6;font-size:0.88rem;color:#f4f4f5;">${window.marked ? marked.parse(data.insights) : escHtml(data.insights)}</div>`;
  }
}

export function renderDashboard(data, sessionId) {
  renderStats(data);
  if (data.preview) renderPreview(data.preview);
  renderStoryboard(data);
  renderCategories(data.categories || {});
  
  // Set dimensions text in Chat Preview Explorer
  const dimsEl = $('chatPreviewDims');
  if (dimsEl) {
    dimsEl.textContent = `(${data.rows_count?.toLocaleString() || 0} rows × ${data.cols_count || 0} columns)`;
  }

  // Switch to results and activate Storyboard tab by default
  switchTab('storyboard');
}

// Delegated listener for per-agent PDF exports
document.addEventListener('click', e => {
  const btn = e.target.closest('.btn-agent-pdf-export');
  if (btn) {
    const aid = btn.getAttribute('data-agent-id');
    if (aid) {
      downloadPdf(null, null, aid);
    }
  }
});
