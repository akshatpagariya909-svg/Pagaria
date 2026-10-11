# Social posts

Instagram carousels made from the site's own buildings, photos and "Key features" lines.

- `carousels.json` lists each carousel: which buildings, which photo (`img` is the photo's number on the building), the title and hashtags.
  - `"kind": "idea"`: a cover, one slide per building, and an end slide. `idea` should match an idea on the site so "Find more with" works.
  - `"kind": "guess"`: a cover, one zoomed detail per building (`zoom`, and `x`/`y` in % to aim the crop), the answers and an end slide.
- `node social/render.js` draws every carousel into `social/out/<id>/` as 1080 × 1350 JPGs plus `caption.txt`. `node social/render.js <id>` draws just one. It needs Playwright (`NODE_PATH=$(npm root -g)` in Claude's sandbox).

Every slide carries its photo credit and licence, and `caption.txt` ends with the full credits and source links. Keep both when posting: the CC BY and CC BY-SA licences require them.

This folder is not part of the website and is not deployed.
