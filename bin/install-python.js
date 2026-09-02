#!/usr/bin/env node

const { execSync, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');

// ANSI Colors & Formatting
const CLR_RESET = '\x1b[0m';
const CLR_BOLD = '\x1b[1m';
const CYAN = '\x1b[38;5;51m';
const BRIGHT_CYAN = '\x1b[38;5;87m';
const PURPLE = '\x1b[38;5;141m';
const GREEN = '\x1b[38;5;82m';
const YELLOW = '\x1b[38;5;220m';
const RED = '\x1b[38;5;196m';
const GRAY = '\x1b[38;5;245m';
const WHITE = '\x1b[38;5;255m';

// Setup directories & Log file
const userHome = path.join(os.homedir(), '.crewlyze');
if (!fs.existsSync(userHome)) {
  fs.mkdirSync(userHome, { recursive: true });
}

const venvDir = path.join(userHome, 'venv');
const logFile = path.join(userHome, 'install.log');
const projectRoot = path.resolve(__dirname, '..');
const requirementsPath = path.join(projectRoot, 'requirements.txt');

// Initialize Logger
function log(msg) {
  const timestamp = new Date().toISOString();
  const cleanMsg = msg.replace(/\x1b\[[0-9;]*m/g, ''); // strip ANSI codes
  fs.appendFileSync(logFile, `[${timestamp}] ${cleanMsg}\n`);
}

// Start install session log header
fs.appendFileSync(logFile, `\n==================== CREWLYZE INSTALLATION SESSION: ${new Date().toISOString()} ====================\n`);
log(`Platform: ${os.platform()} (${os.arch()}) | Node: ${process.version} | Project: ${projectRoot}`);

console.log(`
${CYAN}${CLR_BOLD}═══════════════════════════════════════════════════════════════${CLR_RESET}
${BRIGHT_CYAN}${CLR_BOLD}   ⚙️  CREWLYZE UNIVERSAL ENVIRONMENT INSTALLER & REPAIR${CLR_RESET}
${CYAN}${CLR_BOLD}═══════════════════════════════════════════════════════════════${CLR_RESET}
${GRAY}Installation logs are saved in real-time to:${CLR_RESET}
${WHITE}${logFile}${CLR_RESET}
`);

// Visual Progress Bar Helper
function renderProgressBar(current, total, label = '', barLength = 28) {
  const percent = Math.min(100, Math.round((current / total) * 100));
  const filled = Math.min(barLength, Math.round((current / total) * barLength));
  const empty = barLength - filled;
  const bar = `${PURPLE}${'█'.repeat(filled)}${GRAY}${'░'.repeat(empty)}${CLR_RESET}`;
  const text = `\r ${CYAN}⏳${CLR_RESET} [${bar}] ${WHITE}${percent}%${CLR_RESET}  ${GRAY}${label}${CLR_RESET}          `;
  
  if (process.stdout.isTTY) {
    process.stdout.write(text);
  } else {
    console.log(`[${percent}%] ${label}`);
  }
}

function clearProgressLine() {
  if (process.stdout.isTTY) {
    readline.clearLine(process.stdout, 0);
    readline.cursorTo(process.stdout, 0);
  }
}

// Animated spinner during long command execution
function runWithSpinner(label, taskFn) {
  const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
  let i = 0;
  let timer = null;

  if (process.stdout.isTTY) {
    timer = setInterval(() => {
      process.stdout.write(`\r ${CYAN}${frames[i]}${CLR_RESET} ${label} `);
      i = (i + 1) % frames.length;
    }, 80);
  } else {
    console.log(` -> ${label}...`);
  }

  try {
    const result = taskFn();
    if (timer) clearInterval(timer);
    clearProgressLine();
    console.log(` ${GREEN}✔${CLR_RESET} ${label}`);
    log(`SUCCESS: ${label}`);
    return result;
  } catch (err) {
    if (timer) clearInterval(timer);
    clearProgressLine();
    console.log(` ${RED}✖${CLR_RESET} ${label} ${RED}(warning/failed)${CLR_RESET}`);
    log(`FAILED: ${label}\nError: ${err.message}\nStderr: ${err.stderr ? err.stderr.toString() : ''}`);
    throw err;
  }
}

// Execute command safely and capture output to log
function execLogged(cmd, options = {}) {
  log(`RUN: ${cmd}`);
  try {
    const output = execSync(cmd, {
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: options.timeout || 300000,
      ...options
    });
    const stdout = output ? output.toString() : '';
    if (stdout.trim()) log(`STDOUT: ${stdout}`);
    return stdout;
  } catch (err) {
    const stdout = err.stdout ? err.stdout.toString() : '';
    const stderr = err.stderr ? err.stderr.toString() : '';
    log(`ERROR executing "${cmd}": ${err.message}\nSTDOUT: ${stdout}\nSTDERR: ${stderr}`);
    throw err;
  }
}

// STEP 1: Python Runtime Auto-Discovery & Auto-Installation
console.log(`${CLR_BOLD}${BRIGHT_CYAN}[Step 1/5] Checking Python Runtime (3.9 – 3.13)...${CLR_RESET}`);

function discoverPython() {
  const candidateCommands = process.platform === 'win32'
    ? [
        path.join(os.homedir(), 'AppData', 'Local', 'Programs', 'Python', 'Python310', 'python.exe'),
        path.join(os.homedir(), 'AppData', 'Local', 'Programs', 'Python', 'Python311', 'python.exe'),
        path.join(os.homedir(), 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'python.exe'),
        path.join(os.homedir(), 'AppData', 'Local', 'Programs', 'Python', 'Python313', 'python.exe'),
        'py -3.10', 'py -3.11', 'py -3.12', 'py -3', 'python3', 'python', 'py'
      ]
    : ['python3', 'python3.11', 'python3.12', 'python3.10', 'python', '/usr/bin/python3', '/usr/local/bin/python3'];

  for (const cmd of candidateCommands) {
    try {
      const verStr = execSync(`${cmd} -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"`, {
        stdio: ['pipe', 'pipe', 'ignore'],
        timeout: 4000
      }).toString().trim();
      if (verStr && verStr.includes('.')) {
        const [major, minor] = verStr.split('.').map(Number);
        if (major === 3 && minor >= 9 && minor <= 13) {
          return { pythonCmd: cmd, pythonVersion: verStr };
        }
      }
    } catch (e) {}
  }
  return { pythonCmd: null, pythonVersion: '' };
}

let { pythonCmd, pythonVersion } = discoverPython();

if (!pythonCmd) {
  console.log(`${YELLOW}⚠️  No compatible Python (3.9–3.13) found on PATH. Attempting automated runtime setup...${CLR_RESET}`);
  log('No local Python detected. Initiating automated installation...');

  if (process.platform === 'win32') {
    try {
      runWithSpinner('Installing Python 3.11 via Winget', () => {
        execLogged('winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements --override "/quiet InstallAllUsers=0 PrependPath=1 Include_pip=1"');
      });
    } catch (e1) {
      try {
        const downloadUrl = 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe';
        const installerPath = path.join(os.tmpdir(), 'python-3.11-installer.exe');
        
        runWithSpinner('Downloading official Python 3.11 installer', () => {
          execLogged(`powershell -Command "Invoke-WebRequest -Uri '${downloadUrl}' -OutFile '${installerPath}'"`);
        });

        runWithSpinner('Installing Python 3.11 silently', () => {
          execLogged(`"${installerPath}" /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 SimpleInstall=1`);
        });
      } catch (e2) {
        log(`Automated Windows Python install failed: ${e2.message}`);
      }
    }
  } else if (process.platform === 'darwin') {
    try {
      runWithSpinner('Installing Python 3.11 via Homebrew', () => {
        execLogged('brew install python@3.11');
      });
    } catch (e) {
      log(`Mac brew install failed: ${e.message}`);
    }
  } else {
    try {
      runWithSpinner('Installing Python 3 via apt-get / dnf', () => {
        try {
          execLogged('sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv');
        } catch (aptErr) {
          execLogged('sudo dnf install -y python3 python3-pip');
        }
      });
    } catch (e) {
      log(`Linux package manager install failed: ${e.message}`);
    }
  }

  // Retry discovery
  const retry = discoverPython();
  pythonCmd = retry.pythonCmd;
  pythonVersion = retry.pythonVersion;
}

if (!pythonCmd) {
  console.error(`\n${RED}${CLR_BOLD}❌ Python 3.9+ was not found on your system.${CLR_RESET}`);
  console.error(`${YELLOW}Please download and install Python 3.10 or 3.11 with 'Add to PATH' checked:${CLR_RESET}`);
  console.error(`${WHITE}👉 https://www.python.org/downloads/${CLR_RESET}`);
  console.error(`${GRAY}Log file details: ${logFile}${CLR_RESET}\n`);
  process.exit(1);
}

console.log(` ${GREEN}✔${CLR_RESET} Found active Python: ${WHITE}${pythonCmd}${CLR_RESET} ${GRAY}(v${pythonVersion})${CLR_RESET}\n`);
log(`Selected Python: ${pythonCmd} (version ${pythonVersion})`);

// STEP 2: Virtual Environment Setup
console.log(`${CLR_BOLD}${BRIGHT_CYAN}[Step 2/5] Initializing Isolated Virtual Environment (.crewlyze/venv)...${CLR_RESET}`);

const venvPython = process.platform === 'win32'
  ? path.join(venvDir, 'Scripts', 'python.exe')
  : path.join(venvDir, 'bin', 'python');

if (!fs.existsSync(venvPython)) {
  runWithSpinner('Creating isolated virtual environment', () => {
    if (fs.existsSync(venvDir)) {
      try { fs.rmSync(venvDir, { recursive: true, force: true }); } catch (e) {}
    }
    execLogged(`${pythonCmd} -m venv "${venvDir}"`);
  });
} else {
  console.log(` ${GREEN}✔${CLR_RESET} Existing virtual environment verified at ${GRAY}${venvDir}${CLR_RESET}`);
}
log(`Virtual environment ready: ${venvDir}`);
console.log('');

// STEP 3: Upgrading Core Toolchain via python -m pip
console.log(`${CLR_BOLD}${BRIGHT_CYAN}[Step 3/5] Upgrading Toolchain (pip, setuptools, wheel)...${CLR_RESET}`);
try {
  runWithSpinner('Updating package managers to latest prebuilt wheel standards', () => {
    execLogged(`"${venvPython}" -m pip install --upgrade pip setuptools wheel --no-warn-script-location --prefer-binary --quiet`);
  });
} catch (toolErr) {
  log(`Toolchain upgrade warning: ${toolErr.message}`);
}
console.log('');

// STEP 4: Installing Core Dependencies with Live Progress Bar
console.log(`${CLR_BOLD}${BRIGHT_CYAN}[Step 4/5] Installing Backend Packages & Binary Wheels...${CLR_RESET}`);

// Core packages list with guaranteed compatible wheel specifications
const dependencies = [
  { name: 'numpy', spec: 'numpy>=1.24.0,<2.1.0', critical: true },
  { name: 'pandas', spec: 'pandas>=2.0.0,<3.0.0', critical: true },
  { name: 'fastapi', spec: 'fastapi>=0.100.0', critical: true },
  { name: 'uvicorn', spec: 'uvicorn[standard]>=0.23.0', critical: true },
  { name: 'python-multipart', spec: 'python-multipart>=0.0.6', critical: true },
  { name: 'crewai', spec: 'crewai>=0.5.0', critical: true },
  { name: 'litellm', spec: 'litellm>=1.0.0', critical: true },
  { name: 'plotly', spec: 'plotly>=5.15.0', critical: true },
  { name: 'matplotlib', spec: 'matplotlib>=3.6.0', critical: false },
  { name: 'seaborn', spec: 'seaborn>=0.12.0', critical: false },
  { name: 'duckdb', spec: 'duckdb>=0.9.0', critical: false },
  { name: 'scikit-learn', spec: 'scikit-learn>=1.1.0', critical: false },
  { name: 'scipy', spec: 'scipy>=1.9.0', critical: false },
  { name: 'statsmodels', spec: 'statsmodels>=0.14.0', critical: false },
  { name: 'requests', spec: 'requests>=2.31.0', critical: true },
  { name: 'python-dotenv', spec: 'python-dotenv', critical: true },
  { name: 'Pillow', spec: 'Pillow', critical: false },
  { name: 'reportlab', spec: 'reportlab', critical: false },
  { name: 'openpyxl', spec: 'openpyxl>=3.1.0', critical: false },
  { name: 'xlrd', spec: 'xlrd>=2.0.1', critical: false },
  { name: 'python-pptx', spec: 'python-pptx>=0.6.21', critical: false }
];

// First attempt fast bulk install with requirements.txt if present
let bulkSuccess = false;
try {
  runWithSpinner('Installing bulk dependencies via precompiled wheels', () => {
    execLogged(`"${venvPython}" -m pip install --no-input --prefer-binary --retries 5 -r "${requirementsPath}"`);
  });
  bulkSuccess = true;
} catch (bulkErr) {
  log(`Bulk install note: ${bulkErr.message}. Running resilient itemized installer...`);
  console.log(` ${YELLOW}⚠️  Switching to resilient item-by-item installer with live progress...${CLR_RESET}\n`);
}

if (!bulkSuccess) {
  let completed = 0;
  const total = dependencies.length;

  for (const dep of dependencies) {
    completed++;
    renderProgressBar(completed, total, `Installing ${dep.name} (${completed}/${total})`);
    
    try {
      execLogged(`"${venvPython}" -m pip install --no-input --prefer-binary --no-warn-script-location "${dep.spec}"`);
      log(`Package installed successfully: ${dep.spec}`);
    } catch (err) {
      log(`Warning: Failed to install ${dep.spec}. Trying relaxed fallback without version constraints...`);
      try {
        execLogged(`"${venvPython}" -m pip install --no-input --prefer-binary --no-warn-script-location "${dep.name}"`);
        log(`Fallback package installed successfully: ${dep.name}`);
      } catch (err2) {
        log(`ERROR: Could not install package ${dep.name}`);
        if (dep.critical) {
          clearProgressLine();
          console.error(`\n${RED}❌ Critical package '${dep.name}' could not be installed.${CLR_RESET}`);
          console.error(`${YELLOW}Details logged to: ${logFile}${CLR_RESET}\n`);
        }
      }
    }
  }
  clearProgressLine();
  console.log(` ${GREEN}✔${CLR_RESET} Completed individual package provisioning pipeline`);
}

console.log('');

// STEP 5: Integrity Verification & Self-Healing
console.log(`${CLR_BOLD}${BRIGHT_CYAN}[Step 5/5] Verifying System Health & Self-Healing...${CLR_RESET}`);

function verifyModules() {
  const checkCode = [
    'import sys',
    'modules = ["fastapi", "uvicorn", "pandas", "numpy", "crewai", "plotly", "requests"]',
    'failed = []',
    'for m in modules:',
    '    try:',
    '        __import__(m)',
    '    except Exception as e:',
    '        failed.append(f"{m}: {e}")',
    'if failed:',
    '    print("FAILED: " + " | ".join(failed))',
    '    sys.exit(1)',
    'else:',
    '    print("ALL_OK")'
  ].join('\n');

  try {
    const proc = spawnSync(venvPython, ['-c', checkCode], {
      encoding: 'utf8',
      timeout: 20000
    });
    const stdout = (proc.stdout || '').trim();
    const stderr = (proc.stderr || '').trim();
    
    if (proc.status === 0 && stdout.includes('ALL_OK')) {
      return { ok: true, output: stdout };
    }
    return { ok: false, error: stderr || stdout || `Process exited with code ${proc.status}` };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

let health = verifyModules();

if (!health.ok) {
  console.log(` ${YELLOW}⚠️  Detected module conflict during verification. Running self-healing auto-repair...${CLR_RESET}`);
  log(`Verification warning: ${health.error}. Attempting automated repair for pandas/numpy ABI compatibility...`);
  
  try {
    runWithSpinner('Auto-repairing numpy & pandas binary compatibility', () => {
      execLogged(`"${venvPython}" -m pip install --upgrade --force-reinstall --prefer-binary "numpy>=1.26.0,<2.1.0" "pandas>=2.2.0,<3.0.0"`);
    });
  } catch (repairErr) {
    log(`Repair attempt log: ${repairErr.message}`);
  }

  // Re-verify
  health = verifyModules();
}

if (health.ok) {
  console.log(` ${GREEN}✔${CLR_RESET} All core modules verified successfully (FastAPI, Uvicorn, Pandas, NumPy, CrewAI)`);
  log('Verification passed: All core dependencies are operational.');
  
  console.log(`
${GREEN}${CLR_BOLD}═══════════════════════════════════════════════════════════════${CLR_RESET}
${GREEN}${CLR_BOLD}  🎉 CREWLYZE ENVIRONMENT READY!${CLR_RESET}
${GRAY}  Run ${WHITE}${CLR_BOLD}npx crewlyze${CLR_RESET}${GRAY} or ${WHITE}${CLR_BOLD}npm start${CLR_RESET}${GRAY} to launch.${CLR_RESET}
${GREEN}${CLR_BOLD}═══════════════════════════════════════════════════════════════${CLR_RESET}
`);
} else {
  console.log(`\n${YELLOW}⚠️ Environment installed with warnings. You can still test launching Crewlyze.${CLR_RESET}`);
  console.log(`${GRAY}Detailed logs available at: ${WHITE}${logFile}${CLR_RESET}\n`);
  log(`Verification exited with warnings: ${health.error}`);
}

process.exit(0);
