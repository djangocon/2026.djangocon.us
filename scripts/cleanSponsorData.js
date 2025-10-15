const fs = require('fs');
const path = require('path');
const glob = require('glob');
const matter = require('gray-matter');

// Get all Markdown files in the src/_content/sponsors/ folder
const files = glob.sync('src/_content/sponsors/*.md');

files.forEach(file => {
    // Read the file and parse the front matter
    const content = fs.readFileSync(file, 'utf8');
    const parsed = matter(content);

    delete parsed.data.layout;

    // Move the description field into the content area
    parsed.content = parsed.data.description + '\n\n\n' + parsed.content;
    delete parsed.data.description;

    // Rename logo to filename and logo_orientation to orientation
    // Place both under a logo attribute
    parsed.data.logo = {
        filename: parsed.data.logo,
        orientation: parsed.data.logo_orientation
    };
    delete parsed.data.logo_orientation;

    // Move url_target and url_friendly under a url attribute
    // Remove the url_ prefix
    parsed.data.url = {
        target: parsed.data.url_target,
        friendly: parsed.data.url_friendly
    };
    delete parsed.data.url_target;
    delete parsed.data.url_friendly;

    // If there is a hiring or hiring_url attribute
    // Change hiring to active and hiring_url to url
    // Place both under a hiring attribute
    if (parsed.data.hiring || parsed.data.hiring_url) {
        parsed.data.hiring = {};
        if (parsed.data.hiring !== undefined) {
            parsed.data.hiring.active = parsed.data.hiring;
        }
        if (parsed.data.hiring_url !== undefined) {
            parsed.data.hiring.url = parsed.data.hiring_url;
        }
        delete parsed.data.hiring_url;
    }

    // Stringify the front matter and write the file back
    const newContent = matter.stringify(parsed.content, parsed.data, { indent: 4 });
    fs.writeFileSync(file, newContent, 'utf8');
});
