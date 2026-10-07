# Dérive: visual discovery engine for architecture

Design exploration for a site where you open a wall of buildings and drift instead of searching.

**Live canvas:** https://claude.ai/artifact/SzZZi9iaMGvAX85z3zNEDK (private until shared from the canvas's Share menu)

## v2 · Real works (current)

The canvas now opens on the **v2 · Real works** page, with three boards:

- `WallV2.dc.html`: playable whiteboard wall. Scroll or two-finger swipe pans in every direction, drag pans, pinch or Ctrl/⌘ + scroll zooms, and clicking a tile opens the building over the wall.
- `OpenV2.dc.html`: an opened building (Eiffel Tower) with a *Through time* strip of older works.
- `HundredV2.dc.html`: the first 100 buildings and the exact work each tile will show (50 photographs, plus 50 paintings, prints, drawings and archive photos, all public domain or Creative Commons).

The tiles are captioned empty slots until the environment can reach Wikimedia Commons and the Library of Congress.

## What's here (v1)

- `canvas/` holds the source of every artboard (`*.dc.html`) and the layout index (`canvas.json`).
  - Row 1: cover, plus four homepage directions (A Editorial, B Playful Archive, C Digital Museum, D Playground)
  - Row 2: comparisons of tile walls, type, hover behaviour and building pages
  - Row 3: the chosen direction's mini design system
  - Row 4: MVP screens: Home (playable), Hover, Zoomed out, Building page, Rabbit hole, Search & filter, Surprise me
  - Row 5: future vision: 10,000-building universe, personal drift & collections, atlas & visual search
- `illustrations/` holds the 48 drawn stand-in images and the Python (Pillow + NumPy) that draws them.
  `asset-map.json` maps each image to the `/_blob/<id>` asset it was uploaded as on the canvas.

## Placeholders

Every building image is a drawn illustration, not a photograph, because this environment couldn't reach any
photo hosts. Swap in licensed photography before any user testing. Building names, architects, places and
years refer to real buildings. Counts in the future-vision screens (10,482 buildings, similarity scores,
collection curators) are illustrative.

Regenerate the images with
`python3 run.py b1,b2 <comma-separated function names> sheet.jpg` from `illustrations/src`.
