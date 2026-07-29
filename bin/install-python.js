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

// Helper function to auto-install Python if missing
function tryInstallPythonSystem() {
  console.log(`${YELLOW}⚠️ Python 3 was not detected on your system. Attempting automatic installation...${CLR_RESET}`);
  const isWin = process.platform === 'win32';
  const isMac = process.platform === 'darwin';

  if (isWin) {
    // 1. Try winget first
    try {
      console.log(`${CYAN}📦 Installing Python 3.11 via Winget...${CLR_RESET}`);
      execSync('winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements --override "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1"', { stdio: 'inherit' });
    } catch (e1) {
      console.warn(`${YELLOW}Winget installation unavailable or failed. Downloading official Python 3.11 installer...${CLR_RESET}`);
      try {
        const https = require('https');
        const installerPath = path.join(os.tmpdir(), 'python-3.11-installer.exe');
        const file = fs.createWriteStream(installerPath);
        const downloadUrl = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe';
        
        execSync(`powershell -Command "Invoke-WebRequest -Uri '${downloadUrl}' -OutFile '${installerPath}'"`, { stdio: 'inherit' });
        console.log(`${CYAN}Running Python installer silently...${CLR_RESET}`);
        execSync(`"${installerPath}" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 SimpleInstall=1`, { stdio: 'inherit' });
      } catch (e2) {
        console.error(`${RED}❌ Could not automatically install Python on Windows: ${e2.message}${CLR_RESET}`);
      }
    }
  } else if (isMac) {
    try {
      console.log(`${CYAN}📦 Installing Python 3.11 via Homebrew...${CLR_RESET}`);
      execSync('brew install python@3.11', { stdio: 'inherit' });
    } catch (e) {
      console.error(`${RED}❌ Could not automatically install Python via Homebrew.${CLR_RESET}`);
    }
  } else {
    try {
      console.log(`${CYAN}📦 Installing Python 3 via package manager (apt/dnf)...${CLR_RESET}`);
      try {
        execSync('sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv', { stdio: 'inherit' });
      } catch (aptErr) {
        execSync('sudo dnf install -y python3 python3-pip', { stdio: 'inherit' });
      }
    } catch (e) {
      console.error(`${RED}❌ Could not automatically install Python on Linux.${CLR_RESET}`);
    }
  }
}

// 1. Python Executable Auto-Discovery
function discoverPython() {
  const customDirs = process.platform === 'win32'
    ? [
        path.join(os.homedir(), 'AppData', 'Local', 'Programs', 'Python', 'Python311', 'python.exe'),
        path.join(os.homedir(), 'AppData', 'Local', 'Programs', 'Python', 'Python310', 'python.exe'),
        path.join(os.homedir(), 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe'),
        'python', 'py -3', 'python3', 'py'
      ]
    : ['python3', 'python', '/usr/bin/python3', '/usr/local/bin/python3'];

  for (const cmd of customDirs) {
    try {
      const verStr = execSync(`${cmd} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"`, {
        stdio: ['pipe', 'pipe', 'ignore'],
        timeout: 5000
      }).toString().trim();
      if (verStr && verStr.includes('.')) {
        const [major, minor] = verStr.split('.').map(Number);
        if (major >= 3 && minor >= 9) {
          return { pythonCmd: cmd, pythonVersion: verStr };
        }
      }
    } catch (e) {}
  }
  return { pythonCmd: null, pythonVersion: '' };
}

let { pythonCmd, pythonVersion } = discoverPython();

if (!pythonCmd) {
  tryInstallPythonSystem();
  const retry = discoverPython();
  pythonCmd = retry.pythonCmd;
  pythonVersion = retry.pythonVersion;
}

if (!pythonCmd) {
  console.error(`${RED}❌ Error: Python 3.9+ was not detected on your system PATH.${CLR_RESET}`);
  console.error(`${YELLOW}Please download and install Python 3.9 – 3.13 from https://www.python.org/downloads/${CLR_RESET}\n`);
  process.exit(1);
}

console.log(`${GREEN}✔ Detected Python ${pythonVersion} (${pythonCmd})${CLR_RESET}`);

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
