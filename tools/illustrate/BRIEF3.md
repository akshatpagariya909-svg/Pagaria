# Round 3: award-winning buildings

Rounds 1 and 2 (`BRIEF.md`, `BRIEF2.md`) showed that the best source of buildings worth a student's
time is not a database score but a list chosen by people who know architecture. Round 3 takes
**architecture award lists**: juried, documented, and mostly well photographed.

Follow `BRIEF2.md` exactly (Commons check, drawing language, facts from `vocab.json`, output format,
800px rule), with these changes:

1. **Source**: your award's winners and shortlists, from its English Wikipedia list article (WebFetch
   reaches en.wikipedia.org), plus the award's own site if reachable. Work through winners first, then
   shortlisted or commended buildings if you have time. Built works only (no unbuilt projects,
   urban plans without a building, landscapes without architecture, or restorations where the
   original building is the point unless the award is for the intervention).
2. **Skip** anything in `tools/illustrate/taken.txt` (already on the wall or already checked); match by name loosely.
3. **Photos**: a photo must clearly show the building's outside. If you can, look at the thumbnail
   (Commons imageinfo with `iiurlwidth=640` gives a thumbnail URL you can fetch) and set `"seen": true`
   on photos you looked at. Prefer files in the building's own Commons category.
4. Add an `"award"` field: e.g. `"Aga Khan Award 2019"`, `"RIBA Stirling Prize 2008 shortlist"`.
5. Aim for about 40 buildings. Rewrite your results file after every building.

Results: `tools/illustrate/results/r3_<award>.json`; drawings: `tools/illustrate/svg/<id>.svg`.
Don't edit anything outside `tools/illustrate/`; no commits, no pushes.

## Two hard rules (added 13 October after round 6)

- **No personal data in requests.** Use a generic User-Agent such as `DiscoverArchitecture/1.0 (research)`.
  Never put the owner's name, email or any account detail in a request, header or file.
- **Only sourced facts.** `by`, `year` and the `features` line must each be supported by a source you
  read (Wikipedia, a Commons file or category page, an official or press page). Don't write features
  from memory or from what a photo seems to show. If you can't source them, leave the building out.
