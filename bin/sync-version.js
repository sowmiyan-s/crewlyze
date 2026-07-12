#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const packageJsonPath = path.join(root, 'package.json');
const packageLockPath = path.join(root, 'package-lock.json');
const pyprojectPath = path.join(root, 'pyproject.toml');
const mainPyPath = path.join(root, 'main.py');

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
    const fastapiVersionRegex = /(\bversion\s*=\s*["'])([^"']*)(["']\s*,?\s*\n?\s*\))/m;
    const versionMatchRegex = /(\bversion\s*=\s*["'])([^"']*)(["'])/g;
    
    // We want to replace only the version="..." string in FastAPI instantiation or simple declarations
    let updatedContent = content;
    let replaced = false;
    
    // Specifically target version in FastAPI app declaration
    if (content.includes('FastAPI(')) {
      const startIndex = content.indexOf('FastAPI(');
      const endIndex = content.indexOf(')', startIndex);
      if (startIndex !== -1 && endIndex !== -1) {
        const fastapiSnippet = content.substring(startIndex, endIndex + 1);
        const updatedSnippet = fastapiSnippet.replace(versionMatchRegex, `$1${version}$3`);
        if (fastapiSnippet !== updatedSnippet) {
          updatedContent = content.substring(0, startIndex) + updatedSnippet + content.substring(endIndex + 1);
          replaced = true;
        }
      }
    }
    
    // Fallback if not inside FastAPI instantiation specifically
    if (!replaced) {
      const match = versionMatchRegex.exec(content);
      if (match) {
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

console.log('✨ Version synchronization complete!');
