/*
  Move Social
  ===========

  This script moves the twitter, website, mastodon, and
  github entries under a social variable for all people.

  Requires the following Node packages:
    - gray-matter
    - yaml
 */

const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const stringify = require('yaml').stringify;

const dirs = [
  'src/_content/organizers',
  'src/_content/presenters'
];

dirs.forEach(dir => {
  fs.readdirSync(dir).forEach(file => {
    if (path.extname(file) === '.md') {
      const filePath = path.join(dir, file);
      const fileContent = fs.readFileSync(filePath, 'utf8');
      const parsed = matter(fileContent);

      // Move twitter, website, mastodon, and github entries under a social variable
      parsed.data.social = {
        twitter: parsed.data.twitter,
        website: parsed.data.website,
        mastodon: parsed.data.mastodon,
        github: parsed.data.github,
      };
      delete parsed.data.twitter;
      delete parsed.data.website;
      delete parsed.data.mastodon;
      delete parsed.data.github;

      // Write the updated metadata and the original content back to the file
      const newContent = '---\n' + stringify(parsed.data, { indent: 4 }) + '---\n' + parsed.content;
      fs.writeFileSync(filePath, newContent, 'utf8');
    }
  });
});
