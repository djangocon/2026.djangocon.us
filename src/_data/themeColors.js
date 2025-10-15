/*
  This file adds the list of all colors to the global data object.
  This is useful if you need to dynamically generate a list of colors in your templates.
  For example, this data is used to generate the full color palette in the styleguide.
*/

const path = require('path');

// Add a shortcode to import JSON from tailwind.config.js at the root of the project
module.exports = () => {
  const configPath = path.resolve(__dirname, '../../tailwind.config.js');
  const config = require(configPath);
  const colorsObject = config.theme.extend.colors;

  // Transform the colors object into an array and filter out the 'social' entry
  const colorsArray = Object.entries(colorsObject)
    .map(([id, value]) => ({
      id,
      value: typeof value === 'object'
        ? Object.entries(value).map(([id, color]) => ({ id, color }))
        : value
    }))
    .filter(color => color.id !== 'social');

  return colorsArray;
};
