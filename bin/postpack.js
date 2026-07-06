const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const readmePath = path.join(root, 'README.md');
const readmeBackupPath = path.join(root, 'README-GITHUB.md');

try {
  if (fs.existsSync(readmeBackupPath)) {
    if (fs.existsSync(readmePath)) {
      fs.unlinkSync(readmePath);
    }
    fs.renameSync(readmeBackupPath, readmePath);
    console.log('Restored original GitHub README.md.');
  }
} catch (err) {
  console.error('Error in postpack README restore:', err);
  process.exit(1);
}
