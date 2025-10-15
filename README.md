# DjangoCon.us Conference Website

## Installation

This project requires Node v20 or greater.

1. Run `npm install` to install Node packages.

## Building & Development

This project uses Liquid for templating (except dates, see below). As such, you may wish to install syntax highlighting for Liquid in your text editor.

* VS Code: [Liquid Language Support](https://marketplace.visualstudio.com/items?itemName=neilding.language-liquid)
* [Liquid documentation](https://liquidjs.com/)

Build and watch for local changes by running:

`npm run serve`

This opens a local server at `http://localhost:8080/` and watches for changes to the source files.

## Conference Phases

The conference can be in 3 separate phases, controlled under `site.json`:

* `landing`: The conference site consists of a landing page.
* `active`: The conference site is live and registration may occur.
* `archived`: The conference is over.

This impacts the rendering of the homepage and display of content in various locations.

NOTE: Various pages are still compiled when in `landing` mode, but are not linked to from the homepage.

Reference:

* `src/index.html`
* `src/_includes/home/`

## Date Formatting

Dates are formatted with [date-fns](https://date-fns.org/), due to some wonkiness with Eleventy's date formatting. You can use the `formatDateTime` shortcode in your templates to format dates. Note, that this will take into consideration the timezone defined in `site.json`, under `timezone`. Example:

```liquid
{{ post.data.published_datetime | formatDateTime: "MMMM d, yyyy" }}
```

## Social Media Images

1. Presenter images are created at `/presenters/{{ slug }}/`
2. Session images are created at `/{{ talks,tutorials }}/{{ slug }}/social/`

The graphics that are used to build these are stored in `src/assets/img/theme/social-cards`. They are built with `default-social.html`.

## Considerations when updating content

1. When adding images, if they are below the "fold", consider adding a `loading="lazy"` attribute to the image tag.
2. When adding images, consider adding an `alt` attribute to the image tag.
3. Keep copy short and to the point. The site is most likely scanned, not read.
4. Make sure to keep the styleguide up-to-date with any new components or styles.

## Styleguide

The styleguide lives at `/styleguide/` (respectively `styleguide.html`). The guide is built from content within `src/_content/styleguide/`. Each HTML page represents a section. Sections can be ordered with `order`. Each section can have a `description`.

When using code samples, be sure to use `{% capture code %}` to capture sample and pass it to the `code-snippet.html` include like so:

```liquid
{% include "code-snippet.html", code:code, lang:'html' %}
```

## Setup a new year

1. Copy `durham.djangocon.us` to a new repo.
2. Check `src/_data/site.json` for the current year and any starting information and update as necessary.
3. Update CNAME with the correct domain (usually `YYYY.djangocon.us`).
4. Update `CODE_OF_CONDUCT.md` with the correct year.
5. Update content within `src/_includes/home/landing-conf-home.html` to reflect hotel information, year, etc.
6. Deploy the site to the new domain via GH pages.
