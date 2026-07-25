const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const readmePath = path.join(root, 'README.md');
const readmeBackupPath = path.join(root, 'README-GITHUB.md');
const npmReadmePath = path.join(root, 'README-NPM.md');

// 1. Normalize line endings to LF (\n) for CLI binaries in bin/ (prevents Windows CRLF errors on Unix/macOS)
const binDir = path.join(root, 'bin');
if (fs.existsSync(binDir)) {
  const files = fs.readdirSync(binDir);
  for (const file of files) {
    if (file.endsWith('.js')) {
      const filePath = path.join(binDir, file);
      try {
        let content = fs.readFileSync(filePath, 'utf8');
        if (content.includes('\r\n')) {
          content = content.replace(/\r\n/g, '\n');
          fs.writeFileSync(filePath, content, 'utf8');
          console.log(`Normalized line endings (LF) for bin/${file}`);
        }
      } catch (err) {
        console.warn(`Could not normalize line endings for bin/${file}:`, err.message);
      }
    }
  }
}

// 2. Safe README swap for NPM packaging
try {
  if (fs.existsSync(npmReadmePath)) {
    if (fs.existsSync(readmePath)) {
      if (fs.existsSync(readmeBackupPath)) {
        try { fs.unlinkSync(readmeBackupPath); } catch (e) {}
      }
      fs.renameSync(readmePath, readmeBackupPath);
      console.log('Backed up GitHub README.md to README-GITHUB.md');
    }
    fs.copyFileSync(npmReadmePath, readmePath);
    console.log('Copied README-NPM.md to README.md for NPM packaging.');
  } else {
    console.warn('README-NPM.md not found. Skipping README swap.');
  }
} catch (err) {
  console.error('Error in prepack README swap:', err);
  process.exit(1);
}
