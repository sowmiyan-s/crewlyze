#!/usr/bin/env node
const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');


const projectRoot = path.resolve(__dirname, '..');
const userHome = path.join(os.homedir(), '.crewlyze');

// ─── CLI BANNER ─────────────────────────────────────────────────────────────
const banner = `
\x1b[38;5;196m
   ██████╗██████╗ ███████╗██╗    ██╗██╗  ██╗   ██╗███████╗███████╗
  ██╔════╝██╔══██╗██╔════╝██║    ██║██║  ╚██╗ ██╔╝╚══███╔╝██╔════╝
  ██║     ██████╔╝█████╗  ██║ █╗ ██║██║   ╚████╔╝   ███╔╝ █████╗  
  ██║     ██╔══██╗██╔══╝  ██║███╗██║██║    ╚██╔╝   ███╔╝  ██╔══╝  
  ╚██████╗██║  ██║███████╗╚███╔███╔╝███████╗██║   ███████╗███████╗
   ╚═════╝╚═╝  ╚═╝╚══════╝ ╚══╝╚══╝ ╚══════╝╚═╝   ╚══════╝╚══════╝\x1b[0m

\x1b[1m  Autonomous Multi-Agent Business Intelligence Platform\x1b[0m
\x1b[90m  Powered by CrewAI & FastAPI\x1b[0m
`;

console.log(banner);

// Check if running globally (simple heuristic)
const isGlobal = __dirname.includes('npm') || __dirname.includes('global') || __dirname.includes('Roaming') || __dirname.includes('AppData') || __dirname.includes('yarn') || __dirname.includes('pnpm');
if (!isGlobal) {
  console.log('\x1b[33m\x1b[1m⚠️  WARNING: Crewlyze should be installed globally.\x1b[0m');
  console.log('\x1b[33mPlease run: \x1b[1mnpm install -g crewlyze\x1b[0m\x1b[33m to ensure all features work correctly.\x1b[0m\n');
}

// Ensure home directory configuration folder exists
if (!fs.existsSync(userHome)) {
  fs.mkdirSync(userHome, { recursive: true });
}

// Redirect runtime workspace folders to home directory
process.env.CREWLYZE_DATA_DIR = path.join(userHome, 'data');
process.env.CREWLYZE_OUTPUTS_DIR = path.join(userHome, 'outputs');

const venvDir = path.join(userHome, 'venv');
const mainPyPath = path.join(projectRoot, 'main.py');

// Check venv exists (created by postinstall)
if (!fs.existsSync(venvDir)) {
  console.log('\x1b[31m❌ Error: Python virtual environment not found!\x1b[0m');
  console.log('\x1b[33mDependencies were not installed. Please reinstall crewlyze globally:\x1b[0m');
  console.log('  npm install -g .');
  process.exit(1);
}

const uvicornCmd = process.platform === 'win32'
  ? path.join(venvDir, 'Scripts', 'uvicorn')
  : path.join(venvDir, 'bin', 'uvicorn');

// Start the server
console.log('\x1b[36m🚀 Starting Crewlyze engine...\x1b[0m\n');
const serverProcess = spawn(uvicornCmd, ['main:app', '--host', '127.0.0.1', '--port', '8000', '--reload'], {
  cwd: projectRoot,
  stdio: 'inherit',
  env: process.env
});

serverProcess.on('close', (code) => {
  console.log(`Server exited with code ${code}`);
});

// 5. Auto-open default browser
const url = 'http://127.0.0.1:8000';
console.log(`🔗 Crewlyze is running at: ${url}`);
setTimeout(() => {
  const startCmd = process.platform === 'win32' ? 'start' : process.platform === 'darwin' ? 'open' : 'xdg-open';
  try {
    spawn(startCmd, [url], { shell: true });
  } catch (err) {
    // ignore
  }
}, 2500);
