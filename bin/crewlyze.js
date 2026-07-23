#!/usr/bin/env node
const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');
const net = require('net');


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

function checkPort(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.once('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        resolve(false);
      } else {
        resolve(true);
      }
    });
    server.once('listening', () => {
      server.close(() => {
        resolve(true);
      });
    });
    server.listen(port, '127.0.0.1');
  });
}

async function getFreePort(startPort) {
  let port = startPort;
  while (true) {
    const isFree = await checkPort(port);
    if (isFree) {
      return port;
    }
    port++;
  }
}

(async () => {
  const port = await getFreePort(8000);
  console.log(`\x1b[36m🚀 Starting Crewlyze engine on port ${port}...\x1b[0m\n`);

  const serverProcess = spawn(uvicornCmd, ['main:app', '--host', '127.0.0.1', '--port', port.toString()], {
    cwd: projectRoot,
    stdio: 'inherit',
    env: process.env
  });

  const killServer = () => {
    if (serverProcess) {
      console.log('\nStopping Crewlyze engine...');
      if (process.platform === 'win32') {
        try {
          execSync(`taskkill /pid ${serverProcess.pid} /t /f`, { stdio: 'ignore' });
        } catch (e) {
          try {
            serverProcess.kill('SIGTERM');
          } catch (err) {}
        }
      } else {
        try {
          serverProcess.kill('SIGTERM');
        } catch (err) {}
      }
    }
  };

  process.on('SIGINT', () => {
    killServer();
    process.exit();
  });
  process.on('SIGTERM', () => {
    killServer();
    process.exit();
  });
  process.on('exit', () => {
    killServer();
  });

  serverProcess.on('close', (code) => {
    console.log(`Server exited with code ${code}`);
    process.exit(code || 0);
  });

  const url = `http://127.0.0.1:${port}`;
  console.log(`🔗 Crewlyze is starting at: ${url}`);

  // Poll port until server is active (handles low-end & high-end devices dynamically)
  let attempts = 0;
  const maxAttempts = 100; // up to 20 seconds
  const interval = setInterval(async () => {
    attempts++;
    const isReady = !(await checkPort(port)); // Port occupied = server is listening!
    if (isReady || attempts >= maxAttempts) {
      clearInterval(interval);
      console.log(`\x1b[32m✅ Server ready! Opening workspace at ${url}\x1b[0m`);
      const startCmd = process.platform === 'win32' ? 'start' : process.platform === 'darwin' ? 'open' : 'xdg-open';
      try {
        spawn(startCmd, [url], { shell: true });
      } catch (err) {}
    }
  }, 200);
})();
