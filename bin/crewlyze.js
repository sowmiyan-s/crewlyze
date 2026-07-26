#!/usr/bin/env node
const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');
const net = require('net');

const projectRoot = path.resolve(__dirname, '..');
const userHome = path.join(os.homedir(), '.crewlyze');

// ANSI Color Constants
const CLR_RESET = '\x1b[0m';
const CLR_BOLD = '\x1b[1m';
const CYAN = '\x1b[38;5;51m';
const BRIGHT_CYAN = '\x1b[38;5;87m';
const PURPLE = '\x1b[38;5;141m';
const MAGENTA = '\x1b[38;5;201m';
const RED = '\x1b[38;5;196m';
const GREEN = '\x1b[38;5;82m';
const YELLOW = '\x1b[38;5;220m';
const WHITE = '\x1b[38;5;255m';
const GRAY = '\x1b[38;5;245m';

const banner = `
${CYAN}   ██████╗██████╗ ███████╗██╗    ██╗██╗  ██╗   ██╗███████╗███████╗${CLR_RESET}
${BRIGHT_CYAN}  ██╔════╝██╔══██╗██╔════╝██║    ██║██║  ╚██╗ ██╔╝╚══███╔╝██╔════╝${CLR_RESET}
${PURPLE}  ██║     ██████╔╝█████╗  ██║ █╗ ██║██║   ╚████╔╝   ███╔╝ █████╗  ${CLR_RESET}
${MAGENTA}  ██║     ██╔══██╗██╔══╝  ██║███╗██║██║    ╚██╔╝   ███╔╝  ██╔══╝  ${CLR_RESET}
${RED}  ╚██████╗██║  ██║███████╗╚███╔███╔╝███████╗██║   ███████╗███████╗${CLR_RESET}

${CLR_BOLD}${WHITE}  Autonomous Multi-Agent Business Intelligence & Data Engineering Platform${CLR_RESET}
${GRAY}  Powered by CrewAI & FastAPI • v1.0.9${CLR_RESET}
`;

console.log(banner);

// Ensure home directory configuration folder exists
if (!fs.existsSync(userHome)) {
  fs.mkdirSync(userHome, { recursive: true });
}

// Set runtime environment variable defaults
process.env.CREWLYZE_DATA_DIR = process.env.CREWLYZE_DATA_DIR || path.join(userHome, 'data');
process.env.CREWLYZE_OUTPUTS_DIR = process.env.CREWLYZE_OUTPUTS_DIR || path.join(userHome, 'outputs');

const venvDir = path.join(userHome, 'venv');
const mainPyPath = path.join(projectRoot, 'main.py');

// Virtualenv and uvicorn executable resolution
let uvicornCmd = process.platform === 'win32'
  ? path.join(venvDir, 'Scripts', 'uvicorn.exe')
  : path.join(venvDir, 'bin', 'uvicorn');

if (!fs.existsSync(uvicornCmd)) {
  const altUvicorn = process.platform === 'win32'
    ? path.join(venvDir, 'Scripts', 'uvicorn')
    : path.join(venvDir, 'bin', 'uvicorn');
  if (fs.existsSync(altUvicorn)) {
    uvicornCmd = altUvicorn;
  } else {
    // If venv uvicorn is missing, attempt auto-install or use system uvicorn
    console.log(`${YELLOW}📦 Virtual environment not found. Running automatic setup...${CLR_RESET}`);
    try {
      const installScript = path.join(__dirname, 'install-python.js');
      execSync(`node "${installScript}"`, { stdio: 'inherit' });
    } catch (err) {
      console.warn(`${YELLOW}⚠️ Automatic environment setup finished with warnings. Continuing boot...${CLR_RESET}`);
    }

    if (!fs.existsSync(uvicornCmd)) {
      uvicornCmd = 'uvicorn'; // Fallback to system PATH uvicorn
    }
  }
}

function checkPort(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', () => resolve(false));
    server.once('listening', () => {
      server.close(() => resolve(true));
    });
    server.listen(port, '127.0.0.1');
  });
}

async function getFreePort(startPort) {
  let port = startPort;
  while (true) {
    const isFree = await checkPort(port);
    if (isFree) return port;
    port++;
  }
}

(async () => {
  const port = await getFreePort(8000);
  console.log(`${CYAN}🚀 Launching Crewlyze server on port ${YELLOW}${port}${CYAN}...${CLR_RESET}\n`);

  const serverProcess = spawn(uvicornCmd, ['main:app', '--host', '127.0.0.1', '--port', port.toString()], {
    cwd: projectRoot,
    stdio: 'inherit',
    env: process.env
  });

  const killServer = () => {
    if (serverProcess) {
      console.log(`\n${YELLOW}Stopping Crewlyze engine...${CLR_RESET}`);
      if (process.platform === 'win32') {
        try {
          execSync(`taskkill /pid ${serverProcess.pid} /t /f`, { stdio: 'ignore' });
        } catch (e) {
          try { serverProcess.kill('SIGTERM'); } catch (err) {}
        }
      } else {
        try { serverProcess.kill('SIGTERM'); } catch (err) {}
      }
    }
  };

  process.on('SIGINT', () => { killServer(); process.exit(); });
  process.on('SIGTERM', () => { killServer(); process.exit(); });
  process.on('exit', () => { killServer(); });

  serverProcess.on('close', (code) => {
    if (code !== 0 && code !== null) {
      console.log(`${YELLOW}Server exited with code ${code}${CLR_RESET}`);
    }
    process.exit(code || 0);
  });

  const url = `http://127.0.0.1:${port}`;
  console.log(`${BRIGHT_CYAN}🔗 Crewlyze dashboard URL: ${WHITE}${CLR_BOLD}${url}${CLR_RESET}\n`);

  // Poll port until server is active
  let attempts = 0;
  const maxAttempts = 100; // up to 20 seconds
  const interval = setInterval(async () => {
    attempts++;
    const isOccupied = !(await checkPort(port));
    if (isOccupied || attempts >= maxAttempts) {
      clearInterval(interval);
      console.log(`${GREEN}✅ Server is active and listening! Opening web browser at ${url}${CLR_RESET}`);
      const startCmd = process.platform === 'win32' ? 'start' : process.platform === 'darwin' ? 'open' : 'xdg-open';
      try {
        spawn(startCmd, [url], { shell: true });
      } catch (err) {}
    }
  }, 200);
})();
