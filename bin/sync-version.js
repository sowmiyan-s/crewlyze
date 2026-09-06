#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const packageJsonPath = path.join(root, 'package.json');
const packageLockPath = path.join(root, 'package-lock.json');
const pyprojectPath = path.join(root, 'pyproject.toml');
const mainPyPath = path.join(root, 'main.py');
const readmePath = path.join(root, 'README.md');
const webIndexPath = path.join(root, 'web', 'index.html');

// 1. Read version from package.json
if (!fs.existsSync(packageJsonPath)) {
  console.error('❌ package.json not found!');
  process.exit(1);
}

const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
const version = packageJson.version;

if (!version) {
  console.error('❌ No version found in package.json!');
  process.exit(1);
}

console.log(`🔄 Syncing version ${version} across the project...`);

// 2. Sync package-lock.json
if (fs.existsSync(packageLockPath)) {
  try {
    const packageLock = JSON.parse(fs.readFileSync(packageLockPath, 'utf8'));
    let changed = false;
    
    if (packageLock.version !== version) {
      packageLock.version = version;
      changed = true;
    }
    
    if (packageLock.packages && packageLock.packages[''] && packageLock.packages[''].version !== version) {
      packageLock.packages[''].version = version;
      changed = true;
    }
    
    if (changed) {
      fs.writeFileSync(packageLockPath, JSON.stringify(packageLock, null, 2) + '\n');
      console.log('✅ Updated package-lock.json');
    } else {
      console.log('➖ package-lock.json is already up to date');
    }
  } catch (err) {
    console.error('❌ Error updating package-lock.json:', err.message);
  }
}

// 3. Sync pyproject.toml
if (fs.existsSync(pyprojectPath)) {
  try {
    let content = fs.readFileSync(pyprojectPath, 'utf8');
    const versionRegex = /^(version\s*=\s*["'])([^"']*)(["'])/m;
    
    if (versionRegex.test(content)) {
      const updatedContent = content.replace(versionRegex, `$1${version}$3`);
      if (content !== updatedContent) {
        fs.writeFileSync(pyprojectPath, updatedContent, 'utf8');
        console.log('✅ Updated pyproject.toml');
      } else {
        console.log('➖ pyproject.toml is already up to date');
      }
    } else {
      console.warn('⚠️ Could not find version line in pyproject.toml');
    }
  } catch (err) {
    console.error('❌ Error updating pyproject.toml:', err.message);
  }
}

// 4. Sync main.py (FastAPI version)
if (fs.existsSync(mainPyPath)) {
  try {
    let content = fs.readFileSync(mainPyPath, 'utf8');
    const versionMatchRegex = /(\bversion\s*=\s*["'])([^"']*)(["'])/;
    
    let updatedContent = content;
    let replaced = false;
    
    if (content.includes('FastAPI(')) {
      const startIndex = content.indexOf('FastAPI(');
      const endIndex = content.indexOf(')', startIndex);
      if (startIndex !== -1 && endIndex !== -1) {
        const fastapiSnippet = content.substring(startIndex, endIndex + 1);
        const updatedSnippet = fastapiSnippet.replace(versionMatchRegex, `$1${version}$3`);
        if (fastapiSnippet !== updatedSnippet) {
          updatedContent = content.substring(0, startIndex) + updatedSnippet + content.substring(endIndex + 1);
        }
        replaced = true;
      }
    }
    
    if (!replaced) {
      if (versionMatchRegex.test(content)) {
        updatedContent = content.replace(versionMatchRegex, `$1${version}$3`);
        replaced = true;
      }
    }

    if (replaced && content !== updatedContent) {
      fs.writeFileSync(mainPyPath, updatedContent, 'utf8');
      console.log('✅ Updated main.py');
    } else if (replaced) {
      console.log('➖ main.py is already up to date');
    } else {
      console.warn('⚠️ Could not find FastAPI version parameter in main.py');
    }
  } catch (err) {
    console.error('❌ Error updating main.py:', err.message);
  }
}

// 5. Sync README.md Release badge
if (fs.existsSync(readmePath)) {
  try {
    let content = fs.readFileSync(readmePath, 'utf8');
    const releaseBadgeRegex = /(img\.shields\.io\/badge\/Release-v)[^"-]+(-7c3aed)/;
    if (releaseBadgeRegex.test(content)) {
      const updatedContent = content.replace(releaseBadgeRegex, `$1${version}$2`);
      if (content !== updatedContent) {
        fs.writeFileSync(readmePath, updatedContent, 'utf8');
        console.log('✅ Updated README.md release badge');
      } else {
        console.log('➖ README.md release badge is already up to date');
      }
    }
  } catch (err) {
    console.error('❌ Error updating README.md:', err.message);
  }
}

// 6. Sync web/index.html asset query parameters
if (fs.existsSync(webIndexPath)) {
  try {
    let content = fs.readFileSync(webIndexPath, 'utf8');
    const styleVersionRegex = /(href="\/style\.css\?v=)[^"]+(")/;
    if (styleVersionRegex.test(content)) {
      const updatedContent = content.replace(styleVersionRegex, `$1${version}$2`);
      if (content !== updatedContent) {
        fs.writeFileSync(webIndexPath, updatedContent, 'utf8');
        console.log('✅ Updated web/index.html stylesheet version');
      } else {
        console.log('➖ web/index.html stylesheet version is already up to date');
      }
    }
  } catch (err) {
    console.error('❌ Error updating web/index.html:', err.message);
  }
}

// 7. Sync installer/crewlyze_installer.iss
const installerIssPath = path.join(root, 'installer', 'crewlyze_installer.iss');
if (fs.existsSync(installerIssPath)) {
  try {
    let content = fs.readFileSync(installerIssPath, 'utf8');
    const issVersionRegex = /(#define\s+MyAppVersion\s+["'])([^"']*)(["'])/;
    if (issVersionRegex.test(content)) {
      const updatedContent = content.replace(issVersionRegex, `$1${version}$3`);
      if (content !== updatedContent) {
        fs.writeFileSync(installerIssPath, updatedContent, 'utf8');
        console.log('✅ Updated installer/crewlyze_installer.iss MyAppVersion');
      } else {
        console.log('➖ installer/crewlyze_installer.iss is already up to date');
      }
    }
  } catch (err) {
    console.error('❌ Error updating installer/crewlyze_installer.iss:', err.message);
  }
}

// 8. Sync installer/updater.ps1
const updaterPsPath = path.join(root, 'installer', 'updater.ps1');
if (fs.existsSync(updaterPsPath)) {
  try {
    let content = fs.readFileSync(updaterPsPath, 'utf8');
    const psVersionRegex = /(\$LocalVersion\s*=\s*["'])([^"']*)(["'])/;
    if (psVersionRegex.test(content)) {
      const updatedContent = content.replace(psVersionRegex, `$1${version}$3`);
      if (content !== updatedContent) {
        fs.writeFileSync(updaterPsPath, updatedContent, 'utf8');
        console.log('✅ Updated installer/updater.ps1 $LocalVersion');
      } else {
        console.log('➖ installer/updater.ps1 is already up to date');
      }
    }
  } catch (err) {
    console.error('❌ Error updating installer/updater.ps1:', err.message);
  }
}

// 9. Sync installer/check_release.ps1
const checkReleasePsPath = path.join(root, 'installer', 'check_release.ps1');
if (fs.existsSync(checkReleasePsPath)) {
  try {
    let content = fs.readFileSync(checkReleasePsPath, 'utf8');
    const checkPsRegex = /(\[string\]\$CurrentVersion\s*=\s*["'])([^"']*)(["'])/;
    if (checkPsRegex.test(content)) {
      const updatedContent = content.replace(checkPsRegex, `$1${version}$3`);
      if (content !== updatedContent) {
        fs.writeFileSync(checkReleasePsPath, updatedContent, 'utf8');
        console.log('✅ Updated installer/check_release.ps1 $CurrentVersion');
      } else {
        console.log('➖ installer/check_release.ps1 is already up to date');
      }
    }
  } catch (err) {
    console.error('❌ Error updating installer/check_release.ps1:', err.message);
  }
}

// 10. Sync installer/build_installer.bat
const buildBatPath = path.join(root, 'installer', 'build_installer.bat');
if (fs.existsSync(buildBatPath)) {
  try {
    let content = fs.readFileSync(buildBatPath, 'utf8');
    const batVersionRegex = /(Crewlyze_Setup_v)[0-9]+\.[0-9]+\.[0-9]+(\.exe)/g;
    if (batVersionRegex.test(content)) {
      const updatedContent = content.replace(batVersionRegex, `$1${version}$2`);
      if (content !== updatedContent) {
        fs.writeFileSync(buildBatPath, updatedContent, 'utf8');
        console.log('✅ Updated installer/build_installer.bat output filename');
      } else {
        console.log('➖ installer/build_installer.bat is already up to date');
      }
    }
  } catch (err) {
    console.error('❌ Error updating installer/build_installer.bat:', err.message);
  }
}

console.log('✨ Version synchronization complete!');

