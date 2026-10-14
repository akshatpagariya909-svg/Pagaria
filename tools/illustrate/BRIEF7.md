# Round 7 onwards: more buildings, from lists people chose (Sonnet chats)

The owner wants 500–1,000 new buildings a day. Each round, several chats each take one theme (a region
or a list) and propose about **100 buildings** worth an architecture student's time, with free photos
and sourced facts. An Opus chat reviews every photo by eye and adds the good ones to the wall.

Read `BRIEF2.md` for the results format and the facts (`vocab.json`), and `BRIEF3.md` for its two hard
rules. The changes for these rounds:

1. **Where buildings come from.** Lists people chose: your theme's English Wikipedia list articles and
   categories (for example "List of buildings and structures in …", "Modernist architecture in …",
   "Brutalist architecture in …"), architecture award lists, and national registers of modern
   architecture (Docomomo). WebFetch reaches en.wikipedia.org and commons.wikimedia.org.
2. **Which ones.** Each building needs its own Wikipedia article (any language) and a named architect.
   Favour what the site is for: modern, contemporary, parametric, brutalist and regionalist work, plus a
   few historic precedents. Skip ordinary office blocks, malls, hotels and housing estates unless a
   source says why they matter. Quality over count: 70 good ones beat 100 with filler.
3. **Skip** anything in `tools/illustrate/taken.txt` (already on the wall or already checked), matching by
   name loosely (other languages, with or without the city).
4. **Photos only, no drawings.** A building qualifies with a free photo of its outside: PD, CC0, CC BY or
   CC BY-SA, at least 1200px on its long side (800px only if nothing bigger exists), clearly this
   building. Look at the thumbnail (Commons imageinfo with `iiurlwidth=640`) and set `"seen": true` on
   photos you looked at. Prefer the building's own Commons category and give it as `commons_category`.
   Give 2–4 photos when there are good ones, the best exterior first.
   No usable photo: record it with `"status": "unsure"` and `"note": "no free photo"`. Don't draw it.
5. **Facts** for every building: `name, by, city, cc, year, type, movement, concepts (3), features`, using
   only `vocab.json` for type, movement and concepts, and only facts a source you read gives (Wikipedia,
   Commons, an official or press page). List those pages in `sources`. If you can't source `by` and
   `year`, leave the building out.
6. **Ids**: lower-case ASCII words joined by `-`, not already used in `site/images/` or in another results
   file.

## Output

`tools/illustrate/results/r<round>_<theme>.json` (your task names it), a list in `BRIEF2.md`'s format
with `"status": "photo"` or `"unsure"`. Rewrite it after every 10 buildings, commit and push it to your
own branch (your task names it). Change nothing else; never open a pull request.

When done, end with a short report: how many with photos, how many without, and anything a reviewer
should check first.
