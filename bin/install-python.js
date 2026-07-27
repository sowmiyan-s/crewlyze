#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Colors
const CLR_RESET = '\x1b[0m';
const CLR_BOLD = '\x1b[1m';
const CYAN = '\x1b[38;5;51m';
const GREEN = '\x1b[38;5;82m';
const YELLOW = '\x1b[38;5;220m';
const RED = '\x1b[38;5;196m';
const GRAY = '\x1b[38;5;245m';

console.log(`\n${CYAN}${CLR_BOLD}⚙️  Crewlyze Python Environment Setup${CLR_RESET}`);

const userHome = path.join(os.homedir(), '.crewlyze');
if (!fs.existsSync(userHome)) {
  fs.mkdirSync(userHome, { recursive: true });
}

const venvDir = path.join(userHome, 'venv');
const projectRoot = path.resolve(__dirname, '..');
const requirementsPath = path.join(projectRoot, 'requirements.txt');

// 1. Python Executable Auto-Discovery
const candidates = process.platform === 'win32'
  ? ['python', 'py -3', 'python3', 'py']
  : ['python3', 'python'];

let pythonCmd = null;
let pythonVersion = '';

for (const cmd of candidates) {
  try {
    const verStr = execSync(`${cmd} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"`, {
      stdio: ['pipe', 'pipe', 'ignore'],
      timeout: 5000
    }).toString().trim();
    if (verStr && verStr.includes('.')) {
      const [major, minor] = verStr.split('.').map(Number);
      if (major >= 3) {
        pythonCmd = cmd;
        pythonVersion = verStr;
        break;
      }
    }
  } catch (e) {}
}

if (!pythonCmd) {
  console.error(`${RED}❌ Error: Python 3 was not detected on your system PATH.${CLR_RESET}`);
  console.error(`${YELLOW}Please download and install Python 3.9 – 3.13 from https://www.python.org/downloads/${CLR_RESET}\n`);
  process.exit(1);
}

const [major, minor] = pythonVersion.split('.').map(Number);
console.log(`${GREEN}✔ Detected Python ${pythonVersion} (${pythonCmd})${CLR_RESET}`);

if (minor < 9) {
  console.warn(`${YELLOW}⚠️ Warning: Python ${pythonVersion} detected. Crewlyze is optimized for Python 3.9 – 3.13.${CLR_RESET}`);
}

// 2. Virtual Environment Creation
if (!fs.existsSync(venvDir)) {
  console.log(`${CYAN}📦 Creating Python virtual environment in ${venvDir}...${CLR_RESET}`);
  try {
    execSync(`${pythonCmd} -m venv "${venvDir}"`, { stdio: 'inherit' });
  } catch (err) {
    console.error(`${RED}❌ Error creating Python virtual environment.${CLR_RESET}`);
    if (process.platform !== 'win32') {
      console.error(`${YELLOW}Hint: On Debian/Ubuntu based systems, run: sudo apt-get install python3-venv${CLR_RESET}\n`);
    }
    process.exit(1);
  }
}

const pipCmd = process.platform === 'win32'
  ? path.join(venvDir, 'Scripts', 'pip.exe')
  : path.join(venvDir, 'bin', 'pip');

// 3. Upgrade Build Tools (pip, setuptools, wheel)
console.log(`${CYAN}⚡ Upgrading package installation tools (pip, setuptools, wheel)...${CLR_RESET}`);
try {
  execSync(`"${pipCmd}" install --upgrade pip setuptools wheel --quiet`, { stdio: 'ignore' });
} catch (e) {}

// 4. Install Dependencies with Prefer-Binary & Fallback
console.log(`${CYAN}📥 Installing Python dependencies from requirements.txt...${CLR_RESET}`);
console.log(`${GRAY}Using prebuilt binary wheels for maximum speed and compatibility.${CLR_RESET}\n`);

let installSuccess = false;
try {
  execSync(`"${pipCmd}" install --no-input --prefer-binary --retries 5 -r "${requirementsPath}"`, { stdio: 'inherit' });
  installSuccess = true;
} catch (e) {
  console.warn(`\n${YELLOW}⚠️  Full requirements installation had warnings/errors. Attempting resilient fallback install...${CLR_RESET}`);
}

if (!installSuccess) {
  // Core essential packages list for fallback installation
  const corePackages = [
    'crewai>=0.5.0',
    'fastapi',
    'uvicorn',
    'python-multipart',
    'pandas',
    'matplotlib',
    'seaborn',
    'plotly',
    'requests',
    'python-dotenv',
    'Pillow',
    'reportlab',
    'duckdb',
    'scikit-learn',
    'scipy',
    'statsmodels',
    'openpyxl',
    'xlrd',
    'python-pptx'
  ];

  for (const pkg of corePackages) {
    try {
      execSync(`"${pipCmd}" install --no-input --prefer-binary "${pkg}"`, { stdio: 'ignore' });
      console.log(` ${GREEN}✔ Installed ${pkg}${CLR_RESET}`);
    } catch (err) {
      console.warn(` ${YELLOW}⚠️ Could not install optional wheel ${pkg}${CLR_RESET}`);
    }
  }
}

console.log(`\n${GREEN}${CLR_BOLD}✅ Python environment setup complete!${CLR_RESET}\n`);
