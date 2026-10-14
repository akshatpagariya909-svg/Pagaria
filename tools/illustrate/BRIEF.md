# Illustrating buildings with no free photo

Discover Architecture is a wall of buildings for architecture students. Some important buildings
have no freely licensed photo on Wikimedia Commons (often because of freedom-of-panorama laws, or
because nobody has uploaded one). For those, the wall shows our own line drawing, tagged
"Drawing, not a photo". This folder holds that work.

## Step 1: check Commons first (a photo always beats a drawing)

For each building, look on Wikimedia Commons with WebFetch (the sandbox's own network can't reach
Wikimedia; WebFetch can). Useful API calls (URL-encode the search text):

- Category search: `https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=14&srlimit=10&format=json&srsearch=<name>`
- File search: `https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srlimit=20&format=json&srsearch=<name> <city>`
- Files in a category: `https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtype=file&cmlimit=100&format=json&cmtitle=Category:<name>`
- A file's licence and size: `https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=size|extmetadata&format=json&titles=File:<name>`

A free photo means: licence is public domain, CC0, CC BY or CC BY-SA (never NC or ND), at least
1200px on its long side, and it clearly shows THIS building's outside (judge from the file name,
description and category; a file about a different building with a similar name doesn't count).

Also note any free plan, section, elevation, sketch or model of the building (≥700px, same licences).
These are welcome extras next to a drawing.

If a free exterior photo exists, don't draw: record the files and the Commons category instead.

## Step 2: draw (only when there is no free photo)

First find out what the building looks like. Read its Wikipedia article and other descriptions
with WebFetch (Wikipedia, the architect's site, ArchDaily, WikiArquitectura, Divisare, archINFORM,
news articles). Combine that with what you already know. Draw only what you are confident of: the
overall massing, the roof shape, the main openings, the defining feature. **If you can't establish
the building's form with confidence, don't guess. Mark it "unsure" and move on.** A wrong drawing
misleads students and breaks the site's rule against invented facts.

### The drawing language (locked; match the existing drawings exactly)

Reference drawings already live: `site/images/sangath/drawing.svg`, `site/images/kanchanjunga-apartments/drawing.svg`,
`site/images/quinta-monroy/drawing.svg`, `site/images/icd-itke-research-pavilion-2012/drawing.svg`,
`site/images/stacking-green/drawing.svg`, `site/images/golconde/drawing.svg`. Read two or three before you start.

- File: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 260" width="400" height="260">`, then
  `<rect width="400" height="260" fill="#fff"/>`, then ONE `<g fill="none" stroke="#111110" stroke-linecap="round" stroke-linejoin="round">` holding `<path>`s.
- Lines only. No fills, no shading, no hatching beyond a few parallel lines that describe real
  elements (louvres, slats, steps, roof ribs). No text, no people, no cars, no trees (a single
  simple line of landscape is fine when the setting defines the building: a hill, water, a cliff).
- Stroke widths: 1.6 for the ground line and the main outlines; 1.0–1.2 for openings and secondary lines.
- View: a flat front or side elevation is the default. Use a simple two-point or axonometric view
  only when an elevation can't show the defining idea (a twisting tower, a dome, a courtyard plan).
- One ground line, spanning most of the width (about x 30–370), near y 195–210. The building sits
  centred, with generous white space; it fills roughly 50–80% of the width.
- Proportions matter more than detail: count storeys, bays and towers right when sources say how
  many. Keep it to the few lines that make the building recognisable to someone who knows it.
- Composition on the wall is handled afterwards by `tools/fit_drawings.py`, which scales and lifts each
  drawing above the tile's caption fade; draw at the size above and don't fit it yourself.
- Coordinates rounded to whole or .5 numbers; keep the file small (under ~6 KB), valid XML.

### Check your work

Render each SVG to PNG and look at it before you finish:

```
/opt/pw-browsers/chromium-1194/chrome-linux/chrome --headless --no-sandbox --disable-gpu \
  --window-size=400,260 --screenshot=/tmp/<scratch>/<id>.png tools/illustrate/svg/<id>.svg
```

Then read the PNG. Fix anything clipped, crooked, overlapping or unbalanced. Ask: would an
architecture student who knows this building recognise it?

## Output

- Drawings: `tools/illustrate/svg/<id>.svg` (the id is given in the part file).
- One results file per part, `tools/illustrate/results/partN.json`, a list with one object per building:

```json
{"id": "magney-house", "name": "Magney House",
 "status": "drawn | photo | unsure",
 "commons_category": "Category:… or null",
 "photos": [{"file": "File:….jpg", "license": "CC BY-SA 4.0"}],
 "extras": [{"file": "File:….jpg", "kind": "Plan | Section | Elevation | Sketch | Model | Drawing", "license": "…"}],
 "view": "front elevation from the south (what the drawing shows)",
 "sources": ["URLs you used to learn the form"],
 "note": "anything the owner should know, e.g. why unsure"}
```

`photos` is filled only for status "photo"; `extras` for any status. Don't edit any other file:
not `site/`, not `site/data/buildings.js`, not git (no commits, no pushes).
