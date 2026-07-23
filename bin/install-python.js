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


// 1. Check if Python is installed and check version compatibility
let pythonCmd = 'python3';
try {
  execSync('python3 --version', { stdio: 'ignore' });
} catch (e) {
  try {
    execSync('python --version', { stdio: 'ignore' });
    pythonCmd = 'python';
  } catch (err) {
    console.error('\x1b[31m❌ Error: Python 3 is not installed or not added to system PATH.\x1b[0m');
    console.error('\x1b[33mPlease download & install Python 3.10 to 3.13 from https://www.python.org/downloads/\x1b[0m');
    process.exit(1);
  }
}

try {
  const verStr = execSync(`"${pythonCmd}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"`).toString().trim();
  const [major, minor] = verStr.split('.').map(Number);
  if (major < 3 || (major === 3 && minor < 10)) {
    console.error(`\x1b[31m❌ Error: Python ${verStr} detected. Crewlyze requires Python 3.10 or higher.\x1b[0m`);
    process.exit(1);
  } else if (major === 3 && minor >= 14) {
    console.warn(`\x1b[33m⚠️ Warning: Python ${verStr} detected. Crewlyze is optimized for Python 3.10–3.13.\x1b[0m`);
  }
} catch (err) {}

// 2. Create virtual environment inside user's home folder if it doesn't exist
if (!fs.existsSync(venvDir)) {
  console.log(`\x1b[36m📦 Creating Python virtual environment in ${venvDir}...\x1b[0m`);
  try {
    execSync(`"${pythonCmd}" -m venv "${venvDir}"`, { stdio: 'inherit' });
  } catch (err) {
    console.error('\x1b[31m❌ Error creating Python virtual environment.\x1b[0m');
    if (process.platform !== 'win32') {
      console.error('\x1b[33mHint: On Debian/Ubuntu based systems, you may need to install the venv package first:\x1b[0m');
      console.error('  sudo apt-get install python3-venv\n');
    }
    process.exit(1);
  }
}

const pipCmd = process.platform === 'win32'
  ? path.join(venvDir, 'Scripts', 'pip.exe')
  : path.join(venvDir, 'bin', 'pip');

// 3. Upgrade pip to ensure latest wheel tag compatibility and install prebuilt binaries
try {
  execSync(`"${pipCmd}" install --upgrade pip`, { stdio: 'ignore' });
} catch (e) {
  // Continue if pip upgrade fails silently
}

console.log(`\x1b[36m📥 Installing prebuilt Python dependencies from ${requirementsPath}...\x1b[0m`);
console.log('\x1b[90mThis may take a moment on the first run.\x1b[0m\n');
try {
  execSync(`"${pipCmd}" install --no-input --prefer-binary --retries 5 -r "${requirementsPath}"`, { stdio: 'inherit' });
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

