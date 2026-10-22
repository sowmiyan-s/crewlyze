/**
 * Crewlyze - Charts & Visualizations Engine (ES6 Module)
 * Renders interactive Plotly charts with custom dark/neon/light styling,
 * full-screen zoom inspect, PNG export, and automatic tab ResizeObserver.
 */

import { $, escHtml } from './state.js';

let chartResizeObserver = null;

export function initPlotlyResizeWatcher() {
  if (typeof window === 'undefined' || !window.ResizeObserver) return;
  if (chartResizeObserver) {
    chartResizeObserver.disconnect();
  }

  chartResizeObserver = new ResizeObserver(entries => {
    for (const entry of entries) {
      if (entry.target && entry.contentRect.width > 50) {
        const plotDivs = entry.target.querySelectorAll('.js-plotly-plot');
        plotDivs.forEach(div => {
          try {
            if (window.Plotly && typeof window.Plotly.Plots.resize === 'function') {
              window.Plotly.Plots.resize(div);
            }
          } catch (err) {
            // ignore non-rendered
          }
        });
      }
    }
  });

  // Watch all domain tab panels and chart containers
  document.querySelectorAll('.tab-panel, .results-content, #plotlyChartsWrap, #chartsTab').forEach(el => {
    chartResizeObserver.observe(el);
  });
}

export function resizeAllCharts() {
  if (!window.Plotly) return;
  document.querySelectorAll('.js-plotly-plot').forEach(div => {
    try {
      window.Plotly.Plots.resize(div);
    } catch (e) {}
  });
}

export function renderCharts(plotlyCharts, pngCharts, sessionId) {
  const wrap = $('plotlyChartsWrap');
  if (!wrap) return;
  wrap.innerHTML = '';

  if (plotlyCharts && plotlyCharts.length) {
    plotlyCharts.forEach((chart, idx) => {
      const card = document.createElement('div');
      card.className = 'chart-card';

      const typeLabel = chart.fig_json?.data?.[0]?.type || 'chart';
      card.innerHTML = `
        <div class="chart-card-header">
          <div class="chart-card-title">${escHtml(chart.title)}</div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <select class="chart-theme-select chart-card-action-btn" data-index="${idx}" style="cursor: pointer;">
              <option value="dark">🌙 Dark Obsidian</option>
              <option value="neon">⚡ Electric Neon</option>
              <option value="light">☀️ Clean Light</option>
            </select>
            <button class="zoom-plotly-btn chart-card-action-btn" data-index="${idx}" style="cursor: pointer; display: flex; align-items: center; gap: 4px;">🔍 Inspect</button>
            <button class="download-plotly-btn chart-card-action-btn" data-index="${idx}" style="cursor: pointer; display: flex; align-items: center; gap: 4px;"><i data-lucide="download" style="width: 12px; height: 12px;"></i> Download</button>
            <div class="chart-card-type">${typeLabel}</div>
          </div>
        </div>
        <div class="chart-card-body">
          <div id="plotly_chart_${idx}" style="width:100%;height:380px;"></div>
        </div>`;
      wrap.appendChild(card);

      try {
        const figData = chart.fig_json.data || [];
        const figLayout = chart.fig_json.layout || {};
        figLayout.paper_bgcolor = 'rgba(9,9,11,0)';
        figLayout.plot_bgcolor = 'rgba(15,23,42,0.4)';
        figLayout.font = { color: '#e2e8f0', family: 'Inter, sans-serif' };
        figLayout.margin = figLayout.margin || { l: 50, r: 20, t: 50, b: 50 };

        if (window.Plotly) {
          Plotly.newPlot(`plotly_chart_${idx}`, figData, figLayout, {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['toImage', 'sendDataToCloud'],
            displaylogo: false,
          });
        }

        const themeSelect = card.querySelector('.chart-theme-select');
        if (themeSelect) {
          themeSelect.addEventListener('change', () => {
            const theme = themeSelect.value;
            const gd = document.getElementById(`plotly_chart_${idx}`);
            if (!gd || !window.Plotly) return;
            const bg = theme === 'neon' ? '#0a0a14' : theme === 'light' ? '#ffffff' : 'rgba(9,9,11,0)';
            const plotBg = theme === 'neon' ? 'rgba(255,37,42,0.06)' : theme === 'light' ? '#f8fafc' : 'rgba(15,23,42,0.4)';
            const fontColor = theme === 'light' ? '#0f172a' : '#e2e8f0';
            Plotly.relayout(gd, {
              paper_bgcolor: bg,
              plot_bgcolor: plotBg,
              font: { color: fontColor, family: 'Inter, sans-serif' }
            });
          });
        }

        const zoomBtn = card.querySelector('.zoom-plotly-btn');
        if (zoomBtn) {
          zoomBtn.addEventListener('click', () => {
            const zoomModal = document.getElementById('chartZoomModal');
            const zoomBody = document.getElementById('zoomChartBody');
            const zoomTitle = document.getElementById('zoomChartTitle');
            if (!zoomModal || !zoomBody || !window.Plotly) return;

            if (zoomTitle) zoomTitle.textContent = chart.title || 'Chart Inspector';
            zoomModal.classList.remove('hidden');

            const zData = JSON.parse(JSON.stringify(chart.fig_json.data || []));
            const zLayout = JSON.parse(JSON.stringify(chart.fig_json.layout || {}));
            delete zLayout.width;
            zLayout.autosize = true;
            zLayout.paper_bgcolor = '#111115';
            zLayout.plot_bgcolor = 'rgba(255,255,255,0.02)';
            zLayout.font = { color: '#ffffff', family: 'Inter, sans-serif' };
            zLayout.height = 620;
            zLayout.margin = zLayout.margin || { l: 60, r: 40, t: 60, b: 60 };

            Plotly.newPlot('zoomChartBody', zData, zLayout, {
              responsive: true,
              displayModeBar: true,
              displaylogo: false
            });

            setTimeout(() => {
              const gd = document.getElementById('zoomChartBody');
              if (gd && window.Plotly) Plotly.Plots.resize(gd);
            }, 100);
          });
        }

        const dlBtn = card.querySelector('.download-plotly-btn');
        if (dlBtn) {
          dlBtn.addEventListener('click', () => {
            const gd = document.getElementById(`plotly_chart_${idx}`);
            if (gd && window.Plotly) {
              Plotly.downloadImage(gd, {
                format: 'png',
                width: 1200,
                height: 700,
                filename: (chart.title || 'plotly_chart').replace(/[^a-z0-9]/gi, '_')
              });
            }
          });
        }
      } catch (e) {
        card.querySelector('.chart-card-body').innerHTML = `<p style="color:var(--rose);padding:16px;">Failed to render chart: ${escHtml(String(e))}</p>`;
      }
    });
  } else {
    wrap.innerHTML = '<p style="color:var(--text-muted);padding:8px 0">No interactive charts available. Run with Relationship Analysis enabled.</p>';
  }

  // PNG Fallback / Gallery
  const pngWrap = $('pngChartsWrap');
  if (pngWrap) {
    pngWrap.innerHTML = '';
    if (pngCharts && pngCharts.length) {
      pngCharts.forEach(filename => {
        const item = document.createElement('div');
        item.className = 'png-chart-item';
        item.innerHTML = `
          <img src="/api/charts/${sessionId}/${encodeURIComponent(filename)}" alt="${escHtml(filename)}" loading="lazy" style="width:100%;border-radius:8px;border:1px solid rgba(255,255,255,0.08);" />
          <div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;">${escHtml(filename)}</div>
        `;
        pngWrap.appendChild(item);
      });
    }
  }

  initPlotlyResizeWatcher();
}
