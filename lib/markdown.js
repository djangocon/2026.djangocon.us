const markdownIt = require("markdown-it");
const markdownItAnchor = require("markdown-it-anchor");

const markdown = markdownIt({
    html: true,
    breaks: true,
    linkify: true
  })
  .use(markdownItAnchor, {
    // The level option defines the minimum level of headings to apply anchors to.
    // 1 applies to all headings. 2 will apply to h2 and below, etc.
    level: 1,
    // The slugify option is a function that transforms the heading text into a URL fragment identifier.
    slugify: markdownItAnchor.defaults.slugify
});

module.exports = markdown;
