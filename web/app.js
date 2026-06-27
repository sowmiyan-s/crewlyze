/* Multi Agent Data Analysis with Crew AI
 * Copyright (c) 2025 Sowmiyan S
 * Licensed under the MIT License
 */

// ── State variables ───────────────────────────────────────────────────────
let sessionId = null;
let uploadSize = 0;
let results = null;

const modelOptions = {
    nvidia:      ["nvidia_nim/mistralai/mistral-medium-3.5-128b", "nvidia_nim/mistralai/mistral-large-2407"],
    minimax:     ["minimaxai/minimax-m3"],
    groq:        ["groq/llama-3.1-8b-instant", "groq/llama-3.3-70b-versatile", "groq/mixtral-8x7b-32768", "groq/gemma2-9b-it"],
    openai:      ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    anthropic:   ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
    huggingface: ["huggingface/HuggingFaceH4/zephyr-7b-beta", "huggingface/meta-llama/Llama-2-7b-chat-hf", "huggingface/tiiuae/falcon-7b-instruct"],
    mistral:     ["mistral/mistral-tiny", "mistral/mistral-small", "mistral/mistral-medium", "mistral/mistral-large-latest"],
    gemini:      ["gemini/gemini-pro", "gemini/gemini-1.5-pro", "gemini/gemini-1.5-flash"],
    ollama:      ["ollama/llama3", "ollama/mistral", "ollama/gemma2"]
};

// ── Initial Setup & Listeners ──────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    initElements();
    setupDropdowns();
    setupDropzone();
    setupTabs();
    setupChat();
});


// ── Element selectors ─────────────────────────────────────────────────────
let elements = {};
function initElements() {
    elements = {
        provider: document.getElementById("provider"),
        modelSelect: document.getElementById("model"),
        overrideCheckbox: document.getElementById("override-model-checkbox"),
        modelSelectGroup: document.getElementById("model-select-group"),
        modelTextGroup: document.getElementById("model-text-group"),
        modelInput: document.getElementById("model-input"),
        keyLabel: document.getElementById("key-label"),
        apiKey: document.getElementById("api-key"),
        cooldown: document.getElementById("cooldown"),
        cooldownVal: document.getElementById("cooldown-val"),
        
        dropzone: document.getElementById("dropzone"),
        fileInput: document.getElementById("file-input"),
        fileInfo: document.getElementById("file-info"),
        fileName: document.getElementById("file-name"),
        fileSize: document.getElementById("file-size"),
        removeFileBtn: document.getElementById("remove-file-btn"),
        runBtn: document.getElementById("run-btn"),
        
        terminalSection: document.getElementById("terminal-section"),
        terminalLog: document.getElementById("terminal-log"),
        terminalStatus: document.getElementById("terminal-status"),
        
        dashboardSection: document.getElementById("dashboard-section"),
        statRecords: document.getElementById("stat-records"),
        statColumns: document.getElementById("stat-columns"),
        statNumeric: document.getElementById("stat-numeric"),
        statCategorical: document.getElementById("stat-categorical"),
        
        previewTable: document.getElementById("preview-table"),
        cleaningTimeline: document.getElementById("cleaning-timeline"),
        relationsGrid: document.getElementById("relations-grid"),
        insightsContainer: document.getElementById("insights-container"),
        plotlyGallery: document.getElementById("plotly-gallery"),
        plotlySection: document.getElementById("plotly-charts-section"),
        staticSection: document.getElementById("static-charts-section"),
        staticGallery: document.getElementById("static-gallery"),
        codeContent: document.getElementById("code-content"),
        
        downloadPdfBtn: document.getElementById("download-pdf-btn"),
        downloadCsvBtn: document.getElementById("download-csv-btn"),
        
        chatHistory: document.getElementById("chat-history"),
        chatInput: document.getElementById("chat-input"),
        chatSendBtn: document.getElementById("chat-send-btn")
    };
}


// ── Settings configurations ───────────────────────────────────────────────

function setupDropdowns() {
    // Populate model options based on selected provider
    const updateModels = () => {
        const prov = elements.provider.value;
        const options = modelOptions[prov] || [];
        elements.modelSelect.innerHTML = "";
        options.forEach(opt => {
            const el = document.createElement("option");
            el.value = opt;
            el.textContent = opt;
            elements.modelSelect.appendChild(el);
        });

        // Update key input labels
        if (prov === "ollama") {
            elements.keyLabel.textContent = "Ollama Base URL";
            elements.apiKey.placeholder = "http://localhost:11434";
            elements.apiKey.value = "http://localhost:11434";
            elements.apiKey.type = "text";
            elements.cooldown.value = 0;
            elements.cooldownVal.textContent = 0;
        } else {
            elements.keyLabel.textContent = `${prov.toUpperCase()} API Key`;
            elements.apiKey.placeholder = "Enter key...";
            elements.apiKey.value = "";
            elements.apiKey.type = "password";
            elements.cooldown.value = 5;
            elements.cooldownVal.textContent = 5;
        }
    };

    elements.provider.addEventListener("change", updateModels);
    updateModels(); // Initial run

    // Toggle custom model input override
    elements.overrideCheckbox.addEventListener("change", () => {
        if (elements.overrideCheckbox.checked) {
            elements.modelSelectGroup.style.display = "none";
            elements.modelTextGroup.style.display = "block";
            // Pre-fill input value
            elements.modelInput.value = elements.modelSelect.value;
        } else {
            elements.modelSelectGroup.style.display = "block";
            elements.modelTextGroup.style.display = "none";
        }
    });

    // Sync slider value text
    elements.cooldown.addEventListener("input", () => {
        elements.cooldownVal.textContent = elements.cooldown.value;
    });
}


// ── File upload & dropzone ────────────────────────────────────────────────

function setupDropzone() {
    const dropzone = elements.dropzone;
    const fileInput = elements.fileInput;

    dropzone.addEventListener("click", () => fileInput.click());

    // Drag-over styling overrides
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            handleFileSelection(fileInput.files[0]);
        }
    });

    elements.removeFileBtn.addEventListener("click", () => {
        sessionId = null;
        elements.fileInput.value = "";
        elements.fileInfo.style.display = "none";
        elements.dropzone.style.display = "block";
        elements.dashboardSection.style.display = "none";
    });

    elements.runBtn.addEventListener("click", () => {
        if (sessionId) {
            startAnalysis();
        }
    });
}

async function handleFileSelection(file) {
    elements.dropzone.style.display = "none";
    elements.fileInfo.style.display = "block";
    elements.fileName.textContent = file.name;
    
    // Format human-readable byte sizes
    let size = file.size;
    let units = ["B", "KB", "MB"];
    let unitIdx = 0;
    while (size > 1024 && unitIdx < units.length - 1) {
        size /= 1024;
        unitIdx++;
    }
    elements.fileSize.textContent = `(${size.toFixed(1)} ${units[unitIdx]})`;
    
    // Perform AJx Upload immediately to obtain session token
    const formData = new FormData();
    formData.append("file", file);

    elements.runBtn.disabled = true;
    elements.runBtn.textContent = "Uploading...";

    try {
        const res = await fetch("/api/upload", { method: "POST", body: formData });
        if (!res.ok) throw new Error("Upload failed");
        const data = await res.json();
        sessionId = data.session_id;
        uploadSize = data.size;
        
        elements.runBtn.disabled = false;
        elements.runBtn.textContent = "▶️ Run Analysis";
    } catch (err) {
        alert("Failed to upload file to backend. Check console logs.");
        elements.fileInfo.style.display = "none";
        elements.dropzone.style.display = "block";
        console.error(err);
    }
}


// ── Run Analysis & Listen to SSE Logs ─────────────────────────────────────

async function startAnalysis() {
    elements.runBtn.disabled = true;
    elements.runBtn.textContent = "Analyzing...";
    elements.terminalSection.style.display = "block";
    elements.terminalLog.textContent = "$ initializing_pipeline_engine...\n";
    elements.terminalStatus.textContent = "RUNNING";
    elements.terminalStatus.className = "terminal-status";
    
    // 1. Trigger the analysis call
    const modelName = elements.overrideCheckbox.checked ? elements.modelInput.value : elements.modelSelect.value;
    
    const formData = new FormData();
    formData.append("session_id", sessionId);
    formData.append("provider", elements.provider.value);
    formData.append("model", modelName);
    formData.append("api_key", elements.apiKey.value);
    formData.append("cooldown", elements.cooldown.value);

    try {
        const startRes = await fetch("/api/analyze", { method: "POST", body: formData });
        if (!startRes.ok) throw new Error("Could not start analysis");
        
        // 2. Open Server-Sent Events (SSE) stream listener
        const eventSource = new EventSource(`/api/analyze/stream?session_id=${sessionId}`);
        
        eventSource.onmessage = (event) => {
            if (event.data === "[EOF]") {
                eventSource.close();
                elements.terminalStatus.textContent = "COMPLETE";
                elements.terminalStatus.className = "terminal-status complete";
                elements.runBtn.disabled = false;
                elements.runBtn.textContent = "▶️ Run Analysis";
                
                // Fetch final cached results
                fetchResults();
            } else {
                // Append log lines
                elements.terminalLog.textContent += event.data + "\n";
                // Auto scroll
                elements.terminalLog.scrollTop = elements.terminalLog.scrollHeight;
            }
        };

        eventSource.onerror = (err) => {
            console.error("SSE stream error: ", err);
            eventSource.close();
            elements.terminalStatus.textContent = "ERROR";
            elements.runBtn.disabled = false;
        };

    } catch (err) {
        alert("Failed to trigger data analysis: " + err.message);
        elements.runBtn.disabled = false;
        console.error(err);
    }
}


// ── Fetch & Render Results ───────────────────────────────────────────────

async function fetchResults() {
    try {
        const res = await fetch(`/api/results?session_id=${sessionId}`);
        if (!res.ok) throw new Error("Could not retrieve results");
        
        results = await res.json();
        renderDashboard();
    } catch (err) {
        alert("Error loading final analysis metrics: " + err.message);
        console.error(err);
    }
}

function renderDashboard() {
    elements.dashboardSection.style.display = "block";
    
    // 1. Populate Scorecard Stats
    elements.statRecords.textContent = results.rows_count.toLocaleString();
    elements.statColumns.textContent = results.cols_count;
    elements.statNumeric.textContent = results.numeric_count;
    elements.statCategorical.textContent = results.cat_count;

    // 2. Tab: Data Preview Table
    renderTable(results.preview);

    // 3. Tab: Clean timeline step cards
    renderCleaningTimeline(results.cleaning_steps);

    // 4. Tab: Relations map items
    renderRelations(results.relations);

    // 5. Tab: McKinsey insights cards
    renderInsights(results.insights);

    // 6. Tab: Visual Intelligence charts (Plotly.js + agent PNGs)
    renderPlots();

    // 7. Expander Code Block
    elements.codeContent.textContent = results.code || "Automatic visualization generation script.";

    // 8. Configure downloads buttons
    elements.downloadPdfBtn.onclick = () => {
        window.open(`/api/export-pdf?session_id=${sessionId}`, "_blank");
    };
    
    elements.downloadCsvBtn.onclick = () => {
        // Stream CSV file directly
        const fileContent = "data:text/csv;charset=utf-8," + encodeURIComponent(JSON.stringify(results.preview));
        const dlAnchor = document.createElement('a');
        dlAnchor.setAttribute("href", `/api/export-pdf?session_id=${sessionId}`); // PDF is safer via endpoint
        // Let's create an direct CSV downloader anchor:
        window.open(`/api/charts/${sessionId}/../cleaned.csv`, "_blank"); // fastapi serves file
    };

    // Auto scroll down to dashboard banner
    elements.dashboardSection.scrollIntoView({ behavior: "smooth" });
}


// ── Tab Layout Renderers ──────────────────────────────────────────────────

function renderTable(previewRows) {
    if (!previewRows || previewRows.length === 0) {
        elements.previewTable.innerHTML = "<tr><td>No data available</td></tr>";
        return;
    }
    const headers = Object.keys(previewRows[0]);
    let tableHtml = "<tr>" + headers.map(h => `<th>${escapeHtml(h)}</th>`).join("") + "</tr>";
    
    previewRows.forEach(row => {
        tableHtml += "<tr>" + headers.map(h => `<td>${escapeHtml(String(row[h] !== null ? row[h] : ""))}</td>`).join("") + "</tr>";
    });
    elements.previewTable.innerHTML = tableHtml;
}

function renderCleaningTimeline(stepsText) {
    if (!stepsText || !stepsText.trim()) {
        elements.cleaningTimeline.innerHTML = "<p>No cleaning operations recorded.</p>";
        return;
    }
    
    let htmlContent = "";
    let stepCount = 1;
    
    stepsText.split("\n").forEach(line => {
        let cleanLine = line.trim();
        if (!cleanLine) return;
        
        // Strip prefixes
        cleanLine = cleanLine.replace(/^[\d]+\.\s+/, "").replace(/^[-*•]\s*/, "").trim();
        
        if (cleanLine) {
            htmlContent += `
            <div class="timeline-item">
                <div class="timeline-step">Step ${stepCount}</div>
                <p class="timeline-desc">${escapeHtml(cleanLine)}</p>
            </div>
            `;
            stepCount++;
        }
    });
    
    elements.cleaningTimeline.innerHTML = htmlContent || "<p>Prístine dataset structure validated.</p>";
}

function renderRelations(relationsText) {
    if (!relationsText || !relationsText.trim()) {
        elements.relationsGrid.innerHTML = "<p>No relationships recorded.</p>";
        return;
    }
    
    let htmlContent = "";
    
    relationsText.split("\n").forEach(line => {
        let cleanLine = line.trim();
        if (!cleanLine) return;
        
        let rendered = false;
        if (cleanLine.includes("|") && cleanLine.includes("X:")) {
            try {
                const parts = cleanLine.replace("- ", "").split("|").map(p => p.trim());
                const xVal = parts[0].split(":", 2)[1].trim();
                const yVal = parts[1].split(":", 2)[1].trim();
                const plotType = parts[2].split(":", 2)[1].trim();
                
                // Style type badges
                let badgeClass = "label-obs";
                let pt = plotType.toLowerCase();
                if (pt.includes("bar")) badgeClass = "label-strat";
                else if (pt.includes("scatter") || pt.includes("relation")) badgeClass = "label-imp";
                
                htmlContent += `
                <div class="relation-item">
                    <span class="icon">🔗</span>
                    <span style="color: #e2e8f0; font-weight: 600;">${escapeHtml(xVal)}</span>
                    <span style="color: var(--text-muted); margin: 0 8px; font-size: 0.9em;">vs</span>
                    <span style="color: #e2e8f0; font-weight: 600;">${escapeHtml(yVal)}</span>
                    <span class="insight-label ${badgeClass}" style="margin-left: 12px; font-size: 0.75rem;">${escapeHtml(plotType)}</span>
                </div>
                `;
                rendered = true;
            } catch (e) {}
        }
        
        if (!rendered) {
            htmlContent += `
            <div class="relation-item">
                <span class="icon">🔗</span>
                <span style="color: #e2e8f0;">${escapeHtml(cleanLine.replace("- ", ""))}</span>
            </div>
            `;
        }
    });
    
    elements.relationsGrid.innerHTML = htmlContent;
}

function renderInsights(insightsText) {
    if (!insightsText || !insightsText.trim()) {
        elements.insightsContainer.innerHTML = "<p>No strategic business insights generated.</p>";
        return;
    }
    
    let htmlContent = "";
    const items = insightsText.split(/\n\d+\.\s+|\b\d+\.\s+/);
    let count = 0;
    
    items.forEach(item => {
        const cleanItem = item.trim();
        if (!cleanItem) return;
        count++;
        
        // Extract McKinsey sections
        const obsMatch = cleanItem.match(/\*\*(?:Observation)\*\*:\s*(.*?)(?=\*\*(?:Business\s+)?Implication\*\*|\*\*(?:Actionable\s+)?Strategy\*\*|$)/s);
        const impMatch = cleanItem.match(/\*\*(?:Business\s+)?Implication\*\*:\s*(.*?)(?=\*\*(?:Actionable\s+)?Strategy\*\*|$)/s);
        const stratMatch = cleanItem.match(/\*\*(?:Actionable\s+)?Strategy\*\*:\s*(.*?)$/s);
        
        let obs = obsMatch ? obsMatch[1].trim() : "";
        let imp = impMatch ? impMatch[1].trim() : "";
        let strat = stratMatch ? stratMatch[1].trim() : "";
        
        if (!obs && !imp && !strat) {
            obs = cleanItem;
        }
        
        let sectionsHtml = "";
        if (obs) {
            sectionsHtml += `
            <div class="insight-section">
                <span class="insight-label label-obs">🔍 Observation</span>
                <p class="insight-text">${escapeHtml(obs)}</p>
            </div>
            `;
        }
        if (imp) {
            sectionsHtml += `
            <div class="insight-section">
                <span class="insight-label label-imp">⚠️ Business Implication</span>
                <p class="insight-text" style="color: #fbbf24;">${escapeHtml(imp)}</p>
            </div>
            `;
        }
        if (strat) {
            sectionsHtml += `
            <div class="insight-section">
                <span class="insight-label label-strat">⚡ Actionable Strategy</span>
                <p class="insight-text insight-text-strat">${escapeHtml(strat)}</p>
            </div>
            `;
        }
        
        htmlContent += `
        <div class="insight-card">
            <div class="insight-header">💡 STRATEGIC INSIGHT #${count}</div>
            ${sectionsHtml}
        </div>
        `;
    });
    
    elements.insightsContainer.innerHTML = htmlContent;
}

function renderPlots() {
    // 1. Draw Plotly interactive charts
    const plotlyData = results.plotly_charts || [];
    if (plotlyData.length > 0) {
        elements.plotlySection.style.display = "block";
        elements.plotlyGallery.innerHTML = "";
        
        plotlyData.forEach((chart, idx) => {
            const containerId = `plotly-chart-${idx}`;
            
            const div = document.createElement("div");
            div.className = "plotly-chart-container";
            div.innerHTML = `<h4>${escapeHtml(chart.title)}</h4><div id="${containerId}"></div>`;
            elements.plotlyGallery.appendChild(div);
            
            // Re-render plotly figs using Plotly.js engine
            const fig = chart.fig_json;
            Plotly.newPlot(containerId, fig.data, fig.layout, { responsive: true, displayModeBar: false });
        });
    } else {
        elements.plotlySection.style.display = "none";
    }

    // 2. Fetch fallback static PNGs
    fetchFallbackPNGs();
}

function fetchFallbackPNGs() {
    const pngCharts = results.png_charts || [];
    if (pngCharts.length > 0) {
        elements.staticSection.style.display = "block";
        elements.staticGallery.innerHTML = "";
        
        pngCharts.forEach(filename => {
            const card = document.createElement("div");
            card.className = "static-card";
            card.innerHTML = `
                <img src="/api/charts/${sessionId}/${filename}" alt="${escapeHtml(filename)}">
                <div class="static-title">${escapeHtml(filename.replace(".png", ""))}</div>
            `;
            elements.staticGallery.appendChild(card);
        });
    } else {
        elements.staticSection.style.display = "none";
    }
}


// ── Tab Management ────────────────────────────────────────────────────────

function setupTabs() {
    const tabButtons = document.querySelectorAll(".tab-btn");
    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const tabId = btn.getAttribute("data-tab");
            
            // Remove active class
            tabButtons.forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
            
            // Add active class
            btn.classList.add("active");
            document.getElementById(`tab-${tabId}`).classList.add("active");
            
            // Relayout Plotly charts to adapt to hidden parent resize
            if (tabId === "visual") {
                const charts = document.querySelectorAll(".plotly-chart-container div[id^='plotly-chart-']");
                charts.forEach(c => {
                    Plotly.Plots.resize(c.id);
                });
            }
        });
    });
}


// ── Copilot Chat System ───────────────────────────────────────────────────

function setupChat() {
    const sendBtn = elements.chatSendBtn;
    const chatInput = elements.chatInput;

    const sendMessage = async () => {
        const text = chatInput.value.trim();
        if (!text) return;
        chatInput.value = "";

        // 1. Append User Bubble
        appendBubble("user", text);

        // 2. Append Assistant Loading Bubble
        const loadBubble = appendBubble("assistant", "Thinking...", true);

        // 3. Post to Copilot Endpoint
        const modelName = elements.overrideCheckbox.checked ? elements.modelInput.value : elements.modelSelect.value;
        const formData = new FormData();
        formData.append("session_id", sessionId);
        formData.append("query", text);
        formData.append("provider", elements.provider.value);
        formData.append("model", modelName);
        formData.append("api_key", elements.apiKey.value);

        try {
            const res = await fetch("/api/copilot", { method: "POST", body: formData });
            if (!res.ok) throw new Error("Query execution error");
            const data = await res.json();
            
            // Remove loading
            loadBubble.remove();

            // Append Assistant Response
            appendBubble("assistant", data.text, false, data.plot_url);
        } catch (err) {
            loadBubble.textContent = "Error executing query: " + err.message;
            console.error(err);
        }
    };

    sendBtn.addEventListener("click", sendMessage);
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") sendMessage();
    });
}

function appendBubble(role, content, isLoading = false, plotUrl = null) {
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;
    
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = content;
    
    messageDiv.appendChild(bubble);

    if (plotUrl) {
        const img = document.createElement("img");
        img.src = plotUrl;
        img.alt = "Copilot Generated Chart";
        img.onload = () => {
            elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
        };
        messageDiv.appendChild(img);
    }

    elements.chatHistory.appendChild(messageDiv);
    elements.chatHistory.scrollTop = elements.chatHistory.scrollHeight;
    
    return bubble;
}


// ── Utilities ─────────────────────────────────────────────────────────────

function escapeHtml(str) {
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
