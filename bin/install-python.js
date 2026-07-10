#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

const userHome = path.join(os.homedir(), '.crewlyze');
if (!fs.existsSync(userHome)) {
  fs.mkdirSync(userHome, { recursive: true });
}

const venvDir = path.join(userHome, 'venv');
const projectRoot = path.join(__dirname, '..');
const requirementsPath = path.join(projectRoot, 'requirements.txt');


// 1. Check if Python is installed
let pythonCmd = 'python3';
try {
  execSync('python3 --version', { stdio: 'ignore' });
} catch (e) {
  try {
    execSync('python --version', { stdio: 'ignore' });
    pythonCmd = 'python';
  } catch (err) {
    console.error('\x1b[31m❌ Error: Python 3 is not installed or not in PATH.\x1b[0m');
    process.exit(1);
  }
}

// 2. Create virtual environment inside user's home folder if it doesn't exist
if (!fs.existsSync(venvDir)) {
  console.log(`\x1b[36m📦 Creating Python virtual environment in ${venvDir}...\x1b[0m`);
  execSync(`"${pythonCmd}" -m venv "${venvDir}"`, { stdio: 'inherit' });
}

const pipCmd = process.platform === 'win32'
  ? path.join(venvDir, 'Scripts', 'pip.exe')
  : path.join(venvDir, 'bin', 'pip');

// 3. Install requirements
console.log(`\x1b[36m📥 Installing Python dependencies from ${requirementsPath}...\x1b[0m`);
console.log('\x1b[90mThis may take a few minutes on the first run.\x1b[0m\n');
try {
  execSync(`"${pipCmd}" install -r "${requirementsPath}"`, { stdio: 'inherit' });
  console.log('\x1b[32m✅ Dependencies installed successfully!\x1b[0m');
} catch (e) {
  console.error('\x1b[31m❌ Error installing Python dependencies.\x1b[0m');
  process.exit(1);
}

// 4. Auto-elevate to global install if run locally
const isGlobal = process.env.npm_config_global === 'true' || process.env.npm_config_global === '1' || process.env.npm_config_global === true || process.env.npm_config_global === 1;
const isNpm = !!process.env.npm_lifecycle_event;
const isElevating = process.env.CREWLYZE_ELEVATING === 'true';

if (!isGlobal && isNpm && !isElevating) {
  console.log('\x1b[33m⚠️ Local install detected. Elevating to global install automatically to make "crewlyze" available everywhere...\x1b[0m');
  try {
    const envCopy = Object.assign({}, process.env, { CREWLYZE_ELEVATING: 'true' });
    execSync('npm install -g .', { stdio: 'inherit', cwd: projectRoot, env: envCopy });
    console.log('\x1b[32m✅ Successfully installed globally. You can now use the "crewlyze" command from anywhere.\x1b[0m');
  } catch (err) {
    console.error('\x1b[31m❌ Failed to automatically elevate to global install.\x1b[0m');
  }
}

