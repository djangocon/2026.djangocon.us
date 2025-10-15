const fs = require('fs');
const path = require('path');

const directory = 'src/_content/schedule/talks';

function renameFilesInDirectory(directory) {
  const files = fs.readdirSync(directory);

  files.forEach(file => {
    const filePath = path.join(directory, file);
    const stat = fs.statSync(filePath);

    if (stat.isFile() && filePath.endsWith('.md')) {
      // Extract the slug from the filename
      const slug = file.replace(/^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-t[0-2]-/, '').replace('.md', '');
      const newFilePath = path.join(directory, `${slug}.md`);

      // Rename the file
      fs.renameSync(filePath, newFilePath);
      console.log(`Renamed ${filePath} to ${newFilePath}`);
    }
  });
}

function main() {
  renameFilesInDirectory(directory);
}

main();
