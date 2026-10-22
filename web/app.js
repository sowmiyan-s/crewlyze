/**
 * Crewlyze — Web Frontend Entry Point (Backward Compatibility)
 * The monolithic codebase has been decomposed into modular ES6 modules under /js/:
 *  - js/main.js            (Bootstrap & Lifecycle)
 *  - js/state.js           (State Store & Models)
 *  - js/api.js             (Unified API & SSE client)
 *  - js/command_center.js  (25-Agent 5-Step Command Center)
 *  - js/dashboard.js       (Tabs, Metrics & Data Preview)
 *  - js/charts.js          (Plotly & ResizeObserver)
 *  - js/chat.js            (AI Copilot & History)
 *  - js/export_ui.js       (PDF, CSV, ZIP, Notebook exports)
 */

import './js/main.js';
