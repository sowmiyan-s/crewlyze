/**
 * Crewlyze - AI Copilot Chat Controller (ES6 Module)
 * Manages conversational queries, slash commands, chat rendering, and conversation exports.
 */

import { state, $, escHtml } from './state.js';
import { api } from './api.js';

export function removeFilePathInfo(text) {
  if (!text) return '';
  return text.replace(/(?:file:\/\/\/|[a-zA-Z]:[\\/]|(?:\/[a-zA-Z0-9_.-]+)+)[^\s)]+/g, match => {
    const parts = match.split(/[\\/]/);
    return parts[parts.length - 1];
  });
}

export function resetChat() {
  state.chatHistory = [];
  const container = $('chatMessages');
  if (container) container.innerHTML = '';
  appendChatMsg('assistant', `Hi! I'm your Crew Chat assistant. Ask me anything about your dataset — aggregations, trends, plots, or specific columns.\n\nType **/** to insert a column name directly.`, null, false);
}

export function appendChatMsg(role, content, plotUrl = null, saveToBackend = true) {
  const container = $('chatMessages');
  if (!container) return;

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
  if (typeof window.marked !== 'undefined') {
    formatted = window.marked.parse(cleanedContent);
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
        <div class="chat-chart-card" style="margin-top: 12px; position: relative; border-radius: 12px; overflow: hidden; border: 1px solid var(--border-low); background: rgba(0,0,0,0.2);">
          <img src="${plotUrl}" alt="Generated Visualization" style="width: 100%; display: block; border-radius: 12px;" />
          <div class="chat-chart-actions" style="position: absolute; bottom: 8px; right: 8px; background: rgba(18, 18, 22, 0.85); padding: 4px 8px; border-radius: 8px; backdrop-filter: blur(8px); border: 1px solid var(--border-low);">
            <a href="${plotUrl}" download class="btn-xs btn-secondary" style="font-size: 0.72rem; display: flex; align-items: center; gap: 4px; text-decoration: none;">
              <i data-lucide="download" style="width: 11px; height: 11px;"></i> Download PNG
            </a>
          </div>
        </div>
      ` : ''}
    </div>`;

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;

  if (window.lucide) {
    window.lucide.createIcons({ attrs: { class: 'icon-svg' } });
  }

  const sessionId = state.activeProject?.id || state.uploadedSession;
  if (saveToBackend && sessionId) {
    api.saveChatHistory(sessionId, state.chatHistory);
  }
}

export function showTypingIndicator() {
  removeTypingIndicator();
  const container = $('chatMessages');
  if (!container) return;

  const div = document.createElement('div');
  div.className = 'chat-msg assistant typing-indicator';
  div.id = 'typingIndicator';
  div.innerHTML = `
    <div class="chat-select-wrap" style="visibility: hidden;">
      <input type="checkbox" class="chat-select-check" />
    </div>
    <div class="chat-avatar" style="overflow: hidden; display: flex; align-items: center; justify-content: center;"><img src="/assets/chat_logo.png" style="width: 22px; height: 22px; object-fit: contain; border-radius: 50%;" /></div>
    <div class="chat-bubble" style="color:var(--text-muted)">
      <span style="animation:pulse 1.2s infinite;display:inline-block">Analysing</span>…
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

export function removeTypingIndicator() {
  const ind = $('typingIndicator');
  if (ind) ind.remove();
}

export async function sendChatQuery(query, provider, model, apiKey) {
  if (!query || !query.trim()) return;
  const sessionId = state.activeProject?.id || state.uploadedSession;
  if (!sessionId) {
    if (typeof window.toast === 'function') window.toast('No active session. Please select or analyze a project first.', 'warning');
    return;
  }

  appendChatMsg('user', query.trim());
  showTypingIndicator();

  try {
    const fd = new FormData();
    fd.append('session_id', sessionId);
    fd.append('query', query.trim());
    fd.append('provider', provider || 'groq');
    fd.append('model', model || 'groq/llama-3.3-70b-versatile');
    fd.append('api_key', apiKey || '');

    const res = await api.askCopilot(fd);
    removeTypingIndicator();
    appendChatMsg('assistant', res.text, res.plot_url || null);
  } catch (err) {
    removeTypingIndicator();
    appendChatMsg('assistant', `⚠️ **Error:** ${err.message}`);
  }
}

export async function loadChatHistory(sessionId) {
  if (!sessionId) return;
  const data = await api.fetchChatHistory(sessionId);
  state.chatHistory = data.messages || [];
  const container = $('chatMessages');
  if (!container) return;
  container.innerHTML = '';
  if (!state.chatHistory.length) {
    resetChat();
  } else {
    const history = [...state.chatHistory];
    state.chatHistory = [];
    history.forEach(m => appendChatMsg(m.role, m.content, m.plot_url, false));
  }
}
