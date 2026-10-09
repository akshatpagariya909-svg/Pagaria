# Pagaria
Its my personal work repository

## Discover Architecture (working name)

A wall of 100 buildings you wander instead of search. Each tile shows one free image (photographs, paintings, prints, drawings and archive photos) and opens to links that take you elsewhere to read more.

- `site/` is the website. Plain HTML, CSS and JavaScript with no build step.
  - Open `site/index.html` in a browser to try it locally.
  - All content lives in `site/data/buildings.js`, one object per building.
- `tools/build_pages.py` builds one page per building (`site/buildings/<id>/`), an A–Z index, link previews, `sitemap.xml` and `robots.txt`. Run it after changing `buildings.js`.
- `tools/fetch_images.py` downloads a free image for each building from Wikimedia, with licence and credit, and writes `tools/review.html` so you can check every pick. It needs network access to Wikimedia.
- `design/` holds the design canvas source and drawn placeholder images from the exploration.

### Putting it online (free)

`.github/workflows/pages.yml` publishes `site/` to GitHub Pages whenever `main` changes. To set it up once:

1. In the repo, open Settings → Pages and set Source to GitHub Actions.
2. Merge this branch into `main`.

The site then appears at `https://akshatpagariya909-svg.github.io/Pagaria/`.
