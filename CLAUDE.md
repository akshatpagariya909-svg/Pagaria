# Discover Architecture

A wall of buildings that architecture students wander instead of search, with free photos and links that take them deeper. The owner is new to coding. Explain things plainly, show designs before building them when asked, and keep the site's own text short.

- Live site: https://findgreatarchitecture.com/ (GitHub Pages, deploys from `main` when `site/**` changes)
- Domain: findgreatarchitecture.com, bought Oct 2026 at Spaceship (the owner's account, auto-renew on). DNS there points to GitHub Pages (4 A + 4 AAAA records on @, www CNAME to discoverarchitecture.github.io, and the org's GitHub verification TXT). The custom domain is set in the repository's Settings → Pages, not a CNAME file, because the site deploys with GitHub Actions. discoverarchitecture.github.io forwards to it. The site is called **Find Great Architecture** (renamed from Discover Architecture on 14 Oct 2026).
- Repository: https://github.com/discoverarchitecture/discoverarchitecture.github.io (moved from akshatpagariya909-svg/Pagaria in Oct 2026; the old address forwards)
- Design canvas (all artboards and decisions): https://claude.ai/artifact/SzZZi9iaMGvAX85z3zNEDK
- Audience: architecture students. Favour modern, contemporary and parametric work, brutalism, regionalism and a few historic precedents.
- **Phone first.** User feedback shows most visitors are on phones, so the phone site matters as much as the computer site, if not more.

## Rules that never change

- **Every design is drawn for both phone and computer, phone first.** Each new canvas board shows the phone version (390px wide) next to the computer version, and nothing is built until both have been seen. Every change is checked at about 400px and at desktop width before its pull request.

- **Free images only**: public domain, CC0, CC BY or CC BY-SA, from Wikimedia Commons. Never NC or ND. Every photo shows its credit and licence and links to its source.
- About ten buildings have no free photos. The owner will decide later how to handle licensed photos: remind them, don't solve it alone.
- **The main photo (the wall tile) shows the building**, never people as the subject, an event, a crowd, artworks, objects or a sign (owner's rule, 14 Oct 2026). Every new lead is checked by eye for this; a building with no such photo stays off the wall until one is found.
- Building photos are always **square-cornered**. Everything else in the UI is rounded: buttons, filters and tags are **rectangles with rounded corners** (`--r`, 10px), not round pills; panels get softer corners (`--r-panel`, 18px).
- Colour (v6 "Sunset red"): mostly white with black text. Sunset red `#DA3A26` is used sparingly, for contrast: "Architecture." in the name, the main action button (Surprise me), the chosen half of the Buildings | Books switch, and hover. Anything clickable turns sunset red on hover, and a hovered photo tile gets a thin red underline. Small text is never red. No black fills.
- Architect portraits are always **black and white** and link to the architect's page.
- Never show exact totals of buildings or books on the site (no "2,604 buildings"); say "a huge collection" or similar (owner's rule, 14 Oct 2026). Counts per architect or per filter are fine.
- Minimal text on the site. No invented facts: show height, floors, materials and similar only when a source gives them.

## Design decisions already made (see the canvas before changing any)

- Wall: **equal-width columns, scroll down only** (v3 "Columns", locked). Tile caption: short dark fade, building name left, architect right, then year · city underneath.
- Opened building: "Key features" (never "Study it for"); no "015/100" numbering, just "Museum · Modernism"; portrait byline (option 3) with the portrait full column width on the architect page; official website and location with a map link are in.
- "Go deeper": at least 10 links, show 6 and "see more". Right column scrolls and holds "More by [architect]" and "More [typology]", each linking to its own page. Idea keywords sit at the bottom under "Find more with", with a line saying what they do.
- Books (v12): a Buildings | Books switch; books are a second wall with the same columns and opened card, and shelves replace the ideas row. Built.
- "Related books" in the opened building (v12 · 04, approved 13 Oct and built): a small sliding strip of covers below "More by [architect]". Books about the building first, then about its architect, then up to four general books on its movement (place-tagged books only for buildings in that place). Arrows on a computer, swipe on a phone; hidden when nothing matches.
- Top panel (v13): **A · As you drew it** (picked by the owner on 13 Oct, replacing C). Buildings is on by default; the chosen half of the Buildings | Books switch is filled sunset red, with a thin line between the two. On a phone: row 1 is the name, search and a filter icon; row 2 is the switch on the left and "▶ Guess the building? ⌄" on the right; row 3 is the ideas row, which slides away while you scroll down and comes back when you scroll up. On a computer it is one row, with the ideas row below behaving the same. No building count in the bar.
- Game (v5 · 05–07): the top-bar button "▶ Guess the building?" opens a menu with two games, **Daily five** (the same five for everyone each day, picked from the date) and **Endless** (keep going until you miss one; personal best kept in the browser). Both live on `site/play/`.
- Still open: the opened-building look (v4 A, B or C; Claude recommended B with A's dotted link cells). Ask before building it.

## How the code is laid out

- `site/` is the website: plain HTML, CSS and JavaScript, no build step, no framework.
  - `site/data/buildings.js` holds every building (`window.BUILDINGS`); `site/data/links.js` holds found links (`window.LINKS`), merged in `app.js`. `site/data/books.js` holds the books (`window.BOOKS`), generated from `tools/books_seed.json` by `tools/fetch_books.py`; edit the seed, not the data file.
  - `site/app.js` draws the wall (batches of 60 tiles as you scroll), filters, search and the opened-building sheet.
  - `site/play/` is the game page (`play.js`, `play.css`): Daily five and Endless. It reads `data/buildings.js`; photos are shown from blob: addresses with neutral alt text, so file names never give the answer away.
  - `site/buildings/<id>/` pages, the A–Z index, `sitemap.xml` and `og.jpg` are generated by `tools/build_pages.py`. Rerun it after changing the data. The wall's scripts and styles carry `?v=<fingerprint>` so visitors get new versions at once; the deploy workflow refreshes these with `build_pages.py --stamp`. It needs Python 3.12 (on the owner's Mac: `~/.venvs/pagaria/bin/python`).
  - Page titles follow one rule, written by the generator: `Name — Architect, Year: photos, plans & sections for a case study`, where "plans & sections" appears only when a verified link leads to drawings (WikiArquitectura or ArchDaily). Descriptions say "Key features:" and the same offer. Don't hand-write titles.
  - `site/data/summaries.js` holds short descriptions quoted from Wikipedia (CC BY-SA 4.0, credited on the page) for the most looked-up buildings and every South Asian one; `tools/fetch_summaries.py` makes it from `tools/pageviews.json` (Wikipedia pageviews per building, from the SEO research in `tools/seo_research.md`). Pages with an entry get an "About" section. The home page's "About this wall" block, between `<!-- about:start -->` and `<!-- about:end -->` in `site/index.html`, is rewritten by the generator so search engines see text and the most looked-up buildings.
  - Getting into Google and Bing: `tools/search_console.md`.
- Building fields: `id, n, name, by, place ("City, CC"), year, y, type, movement, region, era, concepts[3], study (the Key features line), images[], commons`; buildings added from Wikidata also carry `qid, lead, coords, hotlink`.
- Book covers come from Open Library (a small thumbnail in `site/images/books/`, the full cover hotlinked). Covers are the publisher's artwork, not free images; the owner knows and may change this.
- Photos: the first hundred host their photos in `site/images/<id>/`. Later buildings (`hotlink: true`) host only the small wall thumbnail; their full photo loads from upload.wikimedia.org. This keeps the site under GitHub Pages' 1 GB limit.

## Tools and GitHub Actions

Claude's sandbox cannot reach Wikidata, Wikimedia or most architecture sites, so network jobs run on GitHub Actions and commit their results back:

- `tools/run_request.txt`: its first line is a command (`python -u tools/<script>.py ...`); pushing a change to it runs `.github/workflows/run-tool.yml`.
- `tools/fetch_request.txt` runs the photo fetcher; `tools/links_request.txt` runs the link finder; `tools/books_request.txt` runs the book-cover fetcher (`fetch-books.yml`, on the books branch).
- These triggers only fire on the branch named in the workflow files (the data-collection branch). Other workstreams should not run them.
- Tools write their reports into committed files (`tools/*_report.*`). Claude can also read a finished job's log through the GitHub tools (`actions_list` for the run, then `get_job_logs`).

Books pipeline (books branch): `tools/harvest_books.py` collects candidates from Wikidata and Open Library into `tools/books_candidates.json` (run it by putting `python -u tools/harvest_books.py` on the first line of `tools/books_request.txt`). `tools/books_batch.py next | add | stats | count` hands out unreviewed candidates, checks a curated batch against the wall before adding it to `tools/books_seed.json`, remembers reviewed candidates in `tools/books_reviewed.json`, and writes `tools/books_progress.md`. Any other first line in `tools/books_request.txt` fetches covers. A routine (`trig_01QFDy6bSHi4u4U3YHgnoGgJ`) wakes the "Books curator" session (`session_01Hjjp7iUDCYZ1WXmhEC1wjf`, which has the repository attached) every 3 hours until 19 Oct 2026; it curates a batch and pushes to the books branch.

Visitor numbers: `site/analytics.js` loads GoatCounter (site code `akshatpagaria`; dashboard https://akshatpagaria.goatcounter.com). `.github/workflows/analytics.yml` runs `tools/fetch_analytics.py` every day at 03:17 UTC and saves `daily.csv` (day, visits) and `latest.json` (pages, referrers, browsers, systems, locations, last 30 days) on the `analytics-data` branch, never on `main`. It needs the repository secret `GOATCOUNTER_TOKEN` (a read-only key from GoatCounter Settings, API). A failed run means the numbers are stale, not zero: check the Actions tab.

Photo rescue (owner's request, 14 Oct 2026): every 300 buildings added, a Sonnet routine (`trig_` id in `tools/photo_rescue/BRIEF.md`'s history; runs daily at 06:07 UTC and stops at once unless `python tools/photo_rescue.py due` says DUE) looks again on Commons for buildings held back for want of a photo of the building itself, following `tools/photo_rescue/BRIEF.md`, and pushes `tools/illustrate/results/rescue_<date>.json` to `claude/photo-rescue`. The data-collection chat checks those photos by eye, takes accepted buildings out of `tools/illustrate/rejected.txt`, and runs the usual pipeline.

Wrong links found by hand go in `tools/link_blocklist.txt` (building | url); `tools/clean_links.py` re-checks existing links without searching again.

Key scripts: `fetch_images.py` (photos, with `tools/image_choices.json` for hand-picked galleries), `find_links.py` (ArchDaily, WikiArquitectura, Divisare, official sites, maps), `harvest.py` / `select_1000.py` / `resolve_list.py` / `merge_1000.py` (growing the list to 1,000), `photo_gaps.py` (writes `tools/photo_gaps.md`, the buildings still short of free photos).

## Working together

Work is split into separate chats, one per workstream, each on its own branch with its own pull request to `main`:

| Workstream | Branch | Covers |
|---|---|---|
| Data collection | `claude/awesome-clarke-vqongx` | The 1,000 list, photos, links, filter information, Actions tools. Goals and progress: [Data collection goals](https://claude.ai/code/artifact/a2e6b9ab-4f72-4ec7-bcf9-8de357b18538) |
| Building page | `claude/building-page` | Opened-building sheet, architect and typology pages |
| Game | `claude/game` | "Play · Daily five" and its share card |
| Design | `claude/design` | New artboards on the design canvas |
| Books | `claude/determined-wozniak-162nu7` | The books shelf: `tools/books_seed.json` (curated list, links to architects and buildings), `fetch_books.py` (covers from Open Library), the Books switch and opened book |

- Progress dashboard for the whole project: https://claude.ai/artifact/HSt3top2Y7Pzb36MbrKMWD (buildings per day, photos, links, portraits, Pritzker, books, and every merged pull request by chat). After your work is merged, refresh it: run `python tools/make_dashboard_data.py`, upload each changed `tools/dashboard/*.json` to the dashboard and point its source at the new file (the dashboard's own instructions say how). Work that isn't a merge can go in `tools/progress_log.json` as `{date, workstream, note}`. At the start of each working day, write your goals for the day in `tools/plan.json` (`{date, workstream, goal, target?, metric?, status?, note?}`; metric is one of buildings_added, buildings, with_photo, with_links, portraits, with_face, books, so the dashboard can show the real number beside the target) and refresh the dashboard. Write plans before the work, never after it.
- **Quality watch** (owner's rule, 14 Oct 2026: warn before quality drops, not after). Every round of new buildings reports five numbers, with a warning level (tell the owner at once, in plain words) and a stop level (stop adding and ask): leads held back in photo review (warn 8%, stop 15%), proposals with no free photo (warn 35%, stop 50%), proposals already on the wall (warn 25%, stop 40%), facts failing the source check (warn 3%, stop 6%), ordinary types such as offices, housing, hotels and malls (warn 20%, stop 30%). A steady rise across rounds is also a warning, even below the levels.
- Who does what in data collection (owner's choice, Oct 2026): **Sonnet** chats do the high-volume work that follows a brief and is checked afterwards (Commons searches for photos, drawings and portraits; gathering facts with sources; running tools, merging and rebuilding). **Opus** chats do the judgement: choosing buildings, line drawings, the final yes or no on covers and portraits by eye, fact checks where sources disagree, briefs, quality flags and merges. A Sonnet chat works on its own branch and changes only its results file; Opus reviews before anything reaches `site/`. Briefs: `tools/illustrate/BRIEF*.md`, `tools/portraits_BRIEF.md`.
- Keep each change small and focused; open a pull request, check it on the live site after merging, then move on.
- Before building something visual that the owner hasn't seen, put it on the design canvas first.
- Check the site at phone width (about 400px) first, then desktop, before opening a pull request. A change that only works on desktop is not done.
- Don't edit `site/data/buildings.js` by hand outside the data-collection workstream; it is generated.
