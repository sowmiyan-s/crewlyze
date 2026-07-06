const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const readmePath = path.join(root, 'README.md');
const readmeBackupPath = path.join(root, 'README-GITHUB.md');
const npmReadmePath = path.join(root, 'README-NPM.md');

try {
  if (fs.existsSync(npmReadmePath)) {
    if (fs.existsSync(readmePath)) {
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
