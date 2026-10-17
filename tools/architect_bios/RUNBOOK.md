# Architect pages: how to make the next batch (for the data collection chat)

Owner's decision, 17 Oct 2026: from now on the data collection chat gets the architect pages done. This is everything it
needs. The first ten pages are live (design v24, option B); the machinery is built, so a new batch is mostly a merge,
a rebuild and a check.

## What exists

- **The list**: `tools/architect_bios/todo.json`, 256 architects in priority order (everyone with 3 or more buildings on
  the wall, plus every Pritzker laureate). Entry fields: `name` (as the wall names them), `buildings`, `pritzker`, `qid`,
  `building_ids`, `building_names`. Everyone else comes later; the aim is all architects.
- **The words**: `tools/architect_bios/BRIEF.md` is the full brief for the writer: a 110 to 190 word write-up per
  architect, sourced facts, 3 to 6 checked links about the whole body of work. Results go in
  `tools/architect_bios/results/bios_NN.json` (`bios_01.json` has the first ten; use it as the model).
  Writing is an **Opus** job. The writer chat is "Architect write-ups (Opus)", session
  `session_01DXucim65YPKmM3eYE1YStE`, branch `claude/architect-bios`; it stopped after the first ten to wait for the
  owner's yes on the voice. Ask the owner whether the voice is approved before starting batch 2.
- **The tools the writer made** (all run on GitHub Actions, see `CLAUDE.md`): `tools/fetch_architect_sources.py`
  (Wikidata and Wikipedia facts into `sources.json`), `tools/check_overview_links.py` (a link must load and be about the
  architect), `tools/architect_bios/request.txt` and `.github/workflows/architect-bios.yml` (the trigger). These fire
  only on the branch named in the workflow, so they may need pointing at the data collection branch.
- **The page generator**: `tools/architect_pages.py`, called by `tools/build_pages.py`. It builds one page per architect
  that has an approved write-up, at `site/architects/<slug>/`, plus the A to Z index `site/architects/`, and writes
  `site/data/arch_pages.js` (which tells the wall who has a page). `tools/names_py.py` applies the wall's
  one-name-per-architect rule (it reads `site/data/names.js`; `node tools/check_names_parity.js` proves they agree).
  Style: `site/architect.css`. Nothing is typed per architect.

## Making a batch

1. The writer produces `bios_NN.json` (about 30 architects), links checked (`checked` date on each link; unchecked links
   are kept off the page). The owner approves the first file of each new kind of architect, then batches go through.
2. On your branch: merge the batch file, then `python3 tools/build_pages.py` (Python 3.12). It rewrites the architect
   pages, `site/sitemap.xml`, `site/data/arch_pages.js` and the building pages (each building now links its architect).
3. Check by eye at about 400 px and at desktop width (phone first), on at least three of the new pages:
   - the portrait shows (black and white, credited); practices without a portrait are fine,
   - the write-up reads right, "Read more" opens the second paragraph,
   - the links open the right pages and have logos (a letter stands in for Pritzker; see below),
   - the buildings are all there, in two columns; the idea keywords row filters; Year / A to Z / Place sort,
   - hover arrows and swipe flip photos; the red dots show on "worth the swipe" tiles,
   - a tap on a building opens the popup over the wall and closing it returns to the architect page,
   - the title is under 60 characters and the description under 155 (`build_pages.py` shortens them itself).
4. Open a pull request to `main`, say in plain words what changed, wait for the owner's "merge".
5. After it is live, the owner requests indexing in Search Console for the new pages (list the new addresses for them),
   and a week or two later reads which pages Google shows (Performance report).

## Rules to keep (from `CLAUDE.md`)

Worldwide audience, Western-first. No invented facts: every date, award and place in a write-up has a source in `facts`.
Portraits are always black and white, free licence, credited and linked. Never a total of buildings on the site (counts
per architect are fine). Phone first.

## Open items

- Logos: the Pritzker Prize and Britannica logos are not on the site, a letter stands in (`site/images/logos/c/`
  holds the ones we have: Wikipedia, ArchDaily, Dezeen, Divisare, WikiArquitectura, archINFORM). Britannica blocks the
  link checker, so the writer dropped it; the Pritzker page can get a logo when someone adds one.
- Practices (OMA, Herzog & de Meuron) take the first portrait found for their name, if any.
- Pages with very few buildings (3) are thin; keep an eye on Search Console's "Crawled, currently not indexed" count
  (about 700 building pages were in it on 16 Oct), and tell the owner if architect pages land there too.
- The wall's filter, byline and "All N" open the architect page when one exists, otherwise they filter the wall.
