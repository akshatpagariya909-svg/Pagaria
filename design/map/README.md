# Map prototype

The playable prototype of the Map (the dock button next to "Surprise me"), built to decide how the
feature should feel before it goes into `site/`. Published for review at
https://claude.ai/artifact/RA79HdVViCSRVUetMUXHg6; the design canvas page "v10 · Map" shows the
same screens with the decisions still open.

## What it does

- Every building is a photo on the map. Close together they stack: the stack shows the best-known
  building in it and a count, and splits into more photos as you zoom (like the Photos app on a phone).
- Two openings to compare: **Atlas** (the site's flat Natural Earth map) and **Globe** (a sphere you turn).
  Same photos, same stacks, same list; only the map underneath changes.
- Country names show their count while the country is small on screen; city names take over as you get close.
  Names never sit on a photo. Click a name to fly to its buildings.
- "In view" lists what is on the map right now, best known first; on a phone it is a strip under the map.
- Click a photo to open the building; click a stack to zoom into it; at the deepest zoom a stack fans out.
- "Show only…" keeps just the matching buildings on the map (an architect, a material, a type) and flies to them.
- Drag with inertia, scroll or pinch to zoom at the cursor, double-click to zoom in, arrow keys and + − 0.

## Files

- `index.html`, `map.css`, `map.js`: the prototype. Plain HTML/CSS/JS, no libraries, same tokens as `site/styles.css`.
  `map.js` is written so it can move into `site/` with small changes (it reads `window.MAPDATA`; the site would read
  `window.BUILDINGS` and `window.WORLD` instead).
- `build_data.py`: builds `data.js` (one compact row per building plus the world map) and the photo sheets
  (`sprite.webp`, 128 px squares for the tiles; `m0.webp`…, 320 × 240 for the opened card). The sheets are not
  committed; rebuild them with:

      python3 design/map/build_data.py <out_dir> <drawings_dir>

  `drawings_dir` holds a PNG of each SVG stand-in drawing (ten buildings have no free photo); render them in a browser
  first, this environment has no SVG rasteriser.

## Known gaps, for the real build

- 118 buildings (mostly the hand-picked first 100) have no coordinates in `buildings.js`. The prototype places them
  at city level (`approx: 1`, the card says "pin shows the city"). The data-collection chat should fetch exact
  coordinates (Wikidata P625) for them; `qid` is missing for most of these, so it needs a name lookup first.
- The country shapes are the whole-world ones from `world.js`; close up they are coarse, so the land fades towards
  the sea colour as you zoom in. If a real street map is ever wanted, it needs an outside tile provider.
- On the live site the photos can load one by one from `site/images/<id>/thumbs/`; the sprite sheets exist only so
  the review page can hold every photo (its sandbox cannot load images from the site).
