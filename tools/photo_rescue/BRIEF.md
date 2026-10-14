# Photo rescue (Sonnet routine, every 300 buildings added)

Some important buildings are off the wall only because no free photo of the building itself was found.
For example, the only photos showed people, an event, artworks or signs, or nothing could be found at all.
Each rescue round looks again for photos.

## Steps

1. Run `python3 tools/photo_rescue.py due`. If it prints `NOT DUE`, stop there and do nothing else.
2. Run `python3 tools/photo_rescue.py todo` and open `tools/photo_rescue/todo.json`.
   Never-tried buildings come first.
3. Take the **first 60**. For each one, search Wikimedia Commons (WebFetch reaches commons.wikimedia.org
   and en.wikipedia.org):
   - Check the building's own Commons category and its Wikipedia article's images, in any language.
     Then try a Commons search for its name and city.
   - A photo qualifies only if it meets all of these:
     - Its licence is PD, CC0, CC BY or CC BY-SA. Never NC or ND.
     - It is at least 1200px on its long side, or 800px if nothing bigger exists.
     - It clearly shows **this building**, with the outside first.
     - **No people are its subject**: no crowds, events, portraits, artworks, signs or plaques.
   - This routine's sandbox cannot load Wikimedia images (thumb.wikimedia.org is blocked), so choose from what the
     Commons API says about each file instead: `action=query&prop=imageinfo|categories&iiprop=size|extmetadata`.
     Read the file's description and categories, not just its name. Skip any file whose description or categories
     mention people, portraits, events, ceremonies, concerts, exhibitions, artworks, sculptures, plaques, signs,
     interiors of other buildings or another building's name. Prefer files described as an exterior or facade view
     of this building, and files in "Quality images" or "Featured pictures".
     Set `"seen": false` on every photo: the data-collection chat fetches each one on GitHub Actions and checks it
     by eye before anything goes on the site.
   - Pick 2 to 4 photos, with the best exterior first, and give the building's `commons_category`.
4. Write `tools/illustrate/results/rescue_<YYYY-MM-DD>.json`. It is a list in the results format
   (see `tools/illustrate/BRIEF2.md`).
   - For a building **with** photos, copy its facts (`id, name, by, city, cc, year, type, movement, concepts, features`)
     from todo.json unchanged. Then add `"status": "photo"`, `"commons_category"` and `"photos": [{"file", "license", "seen": false}]`.
     Also add `"sources"` with the pages you used.
   - For a building with **no** usable photo, leave it out of the results file. Add today's date to its list in
     `tools/photo_rescue/tried.json` (`{"<id>": ["YYYY-MM-DD", ...]}`), so the next round tries others first.
5. Run `python3 tools/photo_rescue.py mark`.
6. Commit only these files:
   - `tools/illustrate/results/rescue_*.json`
   - `tools/photo_rescue/tried.json`
   - `tools/photo_rescue/state.json`
   - `tools/photo_rescue/todo.json`

   Push them to the branch `claude/photo-rescue`. Create it from `claude/awesome-clarke-vqongx` if it doesn't
   exist; otherwise merge `claude/awesome-clarke-vqongx` into it first. Change nothing else, and never touch `site/`.
   Never open a pull request.
7. End with one line: how many buildings were tried, how many have photos, and the results file name.

Never put personal data (email addresses, names or accounts of the person you work for) into any request or file.

## After a round (the data-collection chat, Opus)

The data-collection chat brings the results file into its branch and checks every photo by eye. For each
building it accepts, it deletes the line in `tools/illustrate/rejected.txt`. Then it runs the usual
pipeline: `add_illustrated.py`, the photo fetch, the review, links, `build_pages`, a pull request and the merge.
