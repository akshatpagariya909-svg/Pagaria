# Round 2: famous buildings that Commons can't show

Round 1 (`BRIEF.md`) started from our own hand lists and found that most "no photo" buildings did
have photos, and that obscure buildings are hard to draw from text alone. Round 2 starts from the
other end: **well-known, well-documented buildings that students study, which have no free photo on
Wikimedia Commons**. The usual reason is freedom-of-panorama law: France, Italy, Greece, Ukraine,
Russia and Central Asia, South Korea, the UAE, Qatar, Saudi Arabia, Iran, Egypt and several others don't let
photos of recent buildings be freely licensed, so Commons deletes them (for an architect who died
less than 70 years ago, or who is alive). Some are simply never uploaded (private houses, remote
buildings). Because these buildings are famous, their form is well known and well published, so
they can be drawn accurately.

Read `BRIEF.md` first: Step 1 (check Commons), Step 2 (the locked drawing language) and the
output format all still apply, with the changes below.

## Your job

1. **Propose about 35 buildings** in your theme (given in your task) that architecture students would
   recognise and study: modern, contemporary, parametric, brutalist, regionalist work and a few
   historic precedents. Quality over quantity: each should be worth a student's time. Skip anything
   in `tools/illustrate/taken.txt` (already on the wall or already checked); match by name loosely.
2. **Check Commons** for each, as in Step 1. Freedom-of-panorama countries often still have a few photos
   that survived; if there is a usable free exterior photo (≥1200px, PD/CC0/CC BY/CC BY-SA, clearly
   this building), record it as "photo": that's still a win, the building joins the wall with photos.
3. **Draw** the ones with no usable free photo, where you are confident of the form. Aim for
   accuracy a student who knows the building would accept. If not confident: "unsure".
4. **Fill in the facts** for every building you propose (drawn, photo or unsure), using only the
   vocabularies in `tools/illustrate/vocab.json`, and only facts your sources give:
   `name, by, city, cc (ISO two-letter country code), year (completion), type, movement, concepts (3),
   features` (one short "Key features" line, under 120 characters, what a student should look at).

## Drawing rules added for round 2

- Draw from your understanding of the building, not by tracing one photo. If your drawing follows
  one specific free photo closely, name it in an `"after"` field (`"File:….jpg"`, with its licence)
  so we can credit it.
- Render check: Chrome cuts off the bottom at a 400×260 window. Render at `--window-size=400,400` and look
  at the top 260px.
- Ids: lower-case, ASCII, words joined by `-` (e.g. `institut-du-monde-arabe`). Check the id isn't
  already used in `site/images/` or `tools/illustrate/svg/`.

## Output

- Drawings: `tools/illustrate/svg/<id>.svg`.
- Results: `tools/illustrate/results/r2_<theme>.json`, the BRIEF.md format plus the facts, one object per building:

```json
{"id": "institut-du-monde-arabe", "name": "Institut du Monde Arabe", "by": "Jean Nouvel",
 "city": "Paris", "cc": "FR", "year": "1987", "type": "Museum", "movement": "High-tech",
 "concepts": ["Facade as skin", "Light & shadow", "Steel & glass"],
 "features": "South wall of 240 camera-like metal diaphragms that open and close with the light.",
 "status": "drawn | photo | unsure", "commons_category": null, "photos": [], "extras": [],
 "view": "…", "after": null, "sources": ["…"], "note": "…"}
```

Save each SVG as soon as it's drawn, and rewrite the results file after every building, so nothing
is lost if you're interrupted. Don't edit anything outside `tools/illustrate/`; no commits, no pushes.
