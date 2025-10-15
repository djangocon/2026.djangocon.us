const fs = require('fs');

if (fs.existsSync('dist')) {
  fs.rmSync('dist', { recursive: true, force: true });
  console.log('Cleared dist folder');
} else {
  console.log('dist folder does not exist');
}
