/**
 * Crewlyze - Export & Integrations UI Controller (ES6 Module)
 * Manages PDF reports, Project ZIP exports, Jupyter notebooks, and Webhook/Slack/Discord share modal.
 */

import { state } from './state.js';

export function downloadPdf(sessionId, reportTitle, analysisId) {
  const sid = sessionId || state.activeProject?.id || state.uploadedSession;
  if (!sid) {
    if (typeof window.toast === 'function') window.toast('No active project session to export.', 'error');
    return;
  }
  const titleParam = reportTitle ? `&report_title=${encodeURIComponent(reportTitle)}` : '';
  const analysisParam = analysisId ? `&analysis_id=${encodeURIComponent(analysisId)}` : '';
  window.location.href = `/api/export-pdf?session_id=${encodeURIComponent(sid)}${titleParam}${analysisParam}`;
}

export function downloadProjectZip(projectId) {
  const pid = projectId || state.activeProject?.id;
  if (!pid) {
    if (typeof window.toast === 'function') window.toast('No active project selected.', 'error');
    return;
  }
  window.location.href = `/api/projects/${encodeURIComponent(pid)}/export-zip`;
}

export function downloadCleanedCsv(projectId) {
  const pid = projectId || state.activeProject?.id;
  if (!pid) {
    if (typeof window.toast === 'function') window.toast('No active project selected.', 'error');
    return;
  }
  window.location.href = `/api/projects/${encodeURIComponent(pid)}/download-csv`;
}

export function downloadNotebook(sessionId) {
  const sid = sessionId || state.activeProject?.id || state.uploadedSession;
  if (!sid) {
    if (typeof window.toast === 'function') window.toast('No active project session.', 'error');
    return;
  }
  window.location.href = `/api/export-notebook?session_id=${encodeURIComponent(sid)}`;
}

export function initExportHandlers() {
  document.addEventListener('click', e => {
    if (e.target.closest('#downloadPdfBtn') || e.target.closest('#exportPdfBtn')) {
      downloadPdf();
    } else if (e.target.closest('#exportDistinctPdfBtn')) {
      const activeProj = state.activeProject || {};
      const targetAid = activeProj.primary_agent || 'sales_analysis';
      downloadPdf(null, null, targetAid);
    } else if (e.target.closest('#downloadCsvBtn')) {
      downloadCleanedCsv();
    } else if (e.target.closest('#downloadZipBtn') || e.target.closest('#exportZipBtn')) {
      downloadProjectZip();
    } else if (e.target.closest('#downloadNotebookBtn') || e.target.closest('#exportNotebookBtn')) {
      downloadNotebook();
    }
  });
}
