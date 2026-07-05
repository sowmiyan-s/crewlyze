#!/usr/bin/env node
const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

console.log('🚀 Starting Crewlyze...');

const projectRoot = path.resolve(__dirname, '..');
const userHome = path.join(os.homedir(), '.crewlyze');

// Ensure home directory configuration folder exists
if (!fs.existsSync(userHome)) {
  fs.mkdirSync(userHome, { recursive: true });
}

// Redirect runtime workspace folders to home directory
process.env.CREWLYZE_DATA_DIR = path.join(userHome, 'data');
process.env.CREWLYZE_OUTPUTS_DIR = path.join(userHome, 'outputs');

const venvDir = path.join(userHome, 'venv');
const requirementsPath = path.join(projectRoot, 'requirements.txt');
const mainPyPath = path.join(projectRoot, 'main.py');

// 1. Check if Python is installed
let pythonCmd = 'python3';
try {
  execSync('python3 --version', { stdio: 'ignore' });
} catch (e) {
  try {
    execSync('python --version', { stdio: 'ignore' });
    pythonCmd = 'python';
  } catch (err) {
    console.error('❌ Error: Python 3 is not installed or not in PATH.');
    process.exit(1);
  }
}

// 2. Create virtual environment inside user's home folder if it doesn't exist
if (!fs.existsSync(venvDir)) {
  console.log(`📦 Creating Python virtual environment in ${venvDir}...`);
  execSync(`"${pythonCmd}" -m venv "${venvDir}"`, { stdio: 'inherit' });
}

const pipCmd = process.platform === 'win32'
  ? path.join(venvDir, 'Scripts', 'pip')
  : path.join(venvDir, 'bin', 'pip');

const uvicornCmd = process.platform === 'win32'
  ? path.join(venvDir, 'Scripts', 'uvicorn')
  : path.join(venvDir, 'bin', 'uvicorn');

// 3. Install dependencies
console.log('📦 Installing/Verifying Python dependencies... This may take a moment.');
execSync(`"${pipCmd}" install -r "${requirementsPath}"`, { cwd: projectRoot, stdio: 'inherit' });

// 4. Start the server
console.log('🚀 Starting Crewlyze server...');
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
