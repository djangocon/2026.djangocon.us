const pluginRss = require("@11ty/eleventy-plugin-rss");

module.exports = function(config) {
  config.addPlugin(pluginRss);

  // eleventy-plugin-rss is Nunjucks-only, so add filters for Liquid
  config.addLiquidFilter(
    "dateToRfc3339",
    pluginRss.dateToRfc3339
  );

  config.addLiquidFilter(
    "getNewestCollectionItemDate",
    pluginRss.getNewestCollectionItemDate
  );

  config.addLiquidFilter(
    "htmlToAbsoluteUrls",
    pluginRss.htmlToAbsoluteUrls
  );
}
