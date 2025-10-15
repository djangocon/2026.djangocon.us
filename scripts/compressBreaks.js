const fs = require('fs');
const path = require('path');
const grayMatter = require('gray-matter');
const marked = require('marked');
const yaml = require('js-yaml');

function processFiles(dirPath) {
  const filenames = fs.readdirSync(dirPath);
  const collections = [];

  for (const filename of filenames) {
    const filePath = path.join(dirPath, filename);
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const { data, content } = grayMatter(fileContent);

    data.abstract = content.trim();
    collections.push(data);
  }

  const yamlString = yaml.dump(collections);
  fs.writeFileSync('output.yaml', yamlString);
}

processFiles('src/_content/schedule/custom/');
