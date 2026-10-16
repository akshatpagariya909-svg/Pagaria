# Architect pages: write-ups and overview links (Opus task)

Owner's request, 16 Oct 2026. The site gets a page for each architect ("Zaha Hadid buildings"), built to rank in Google
for searches about that architect and to be useful to architecture students. This brief covers the **words**: a short
write-up per architect, and links to articles about their whole body of work. The page design, the generator and the
wall of buildings are done elsewhere (workstream "Building page"); do not touch `site/`.

Audience: architecture students worldwide, Western countries the biggest target. Plain English, short sentences.
Read `CLAUDE.md` first, especially "Rules that never change".

## The list

`tools/architect_bios/todo.json`: 256 architects in priority order (every architect with 3 or more buildings on the wall,
plus every Pritzker laureate). Each entry has the name as the wall uses it (a practice named after one person goes under
that person: "Zaha Hadid Architects" is "Zaha Hadid"; firms such as OMA, SANAA, BIG keep the firm's name), the number of
buildings, whether they won the Pritzker, a Wikidata `qid` when known (`null` or `manual:` means look it up), and the
buildings on the wall (`building_ids`, `building_names`).

Some entries are not people or not notable enough for a page (a "Public Works Department", a regional firm with no
sources). Do not invent anything for those: mark them `"skip": true` with a one-line `reason`, and carry on.

## What to produce, per architect

Write into `tools/architect_bios/results/bios_<NN>.json` (a list, about 30 per file), one object each:

```json
{
  "name": "Zaha Hadid",
  "qid": "Q...",
  "kind": "person" | "practice",
  "born_died": "1950–2016",
  "country": "Iraq-born British",
  "bio": "110 to 190 words, 2 short paragraphs.",
  "facts": [{"claim": "First woman to win the Pritzker Prize, in 2004", "source": "https://www.pritzkerprize.com/..."}],
  "overview_links": [{"site": "Pritzker Prize", "title": "Laureate page", "url": "https://...", "why": "jury citation and biography"}],
  "skip": false
}
```

### 1. The write-up (`bio`)

110 to 190 words, in two short paragraphs. It sits under the architect's portrait on their page and must read well to a
student and rank well in Google.

- First sentence: the full name, dates, nationality or base, and what they are known for, so the page answers
  "who is X" at once. Example shape: "Zaha Hadid (1950–2016) was an Iraqi-British architect known for flowing, curved
  concrete and steel buildings that broke with straight-edged modernism."
- Second paragraph: three to five key works, **chosen from the buildings of theirs on the wall** (name them exactly as the
  wall does, so the page can link them), what each shows, and the ideas a student can take from them (structure, light,
  materials, form). Mention places and years.
- Say why the architect is studied: a style they shaped, a method, a prize, a famous argument. Only what a source supports.
- Use the words people search for, naturally: the architect's name once or twice more, "buildings", "projects", the
  style ("deconstructivism", "brutalism"), key building names. No keyword stuffing, no list of keywords.
- Good writing: concrete nouns and verbs, one idea per sentence, no filler ("iconic", "visionary", "world-renowned",
  "legendary", "pushes the boundaries"), no opening with a question, no closing summary sentence, no emoji, no "In
  conclusion". Numbers and dates only from a source.
- Original wording. Facts are free to use but do not copy Wikipedia's sentences; if a sentence must be quoted, put it in
  quotation marks and say where it is from.
- Worldwide voice. Never frame an architect through India or any one country unless the facts say so.

### 2. The facts (`facts`)

Every date, award, place, role and number in the `bio` appears in `facts` with a source URL: Wikipedia, Wikidata,
pritzkerprize.com, Encyclopaedia Britannica, the architect's own site or foundation, or a museum. No source, no sentence.
Where sources disagree, say so in a `"note"` on that fact and prefer the more careful claim.

### 3. Links about the whole portfolio (`overview_links`)

Three to six links per architect to pages about the architect's **entire body of work**, never one building or one
article about a single project. Good kinds: Wikipedia article, Britannica entry, the Pritzker Prize laureate page, the
architect's or practice's own site or foundation (works list), an ArchDaily office or architect profile, a Dezeen,
Architectural Review, Architecture Today or Guardian profile or obituary, Google Arts & Culture, a museum retrospective
page, Wikiarquitectura, Archinect. Prefer pages free to read. Each gets a `why` of a few words.

Links must be checked: they load (HTTP 200, not a search page, not a paywall wall) and are about this architect. The
sandbox cannot reach these sites; run the check as a GitHub Actions job (see below) and record `"checked": "<date>"`.

### 4. Not in this task

Books: `tools/books_seed.json` already ties books to architects; the page generator reads it. Portraits: done
(`site/data/architects.js`). Page layout and code: other chat.

## How to get the facts (network)

The sandbox cannot reach Wikipedia, Wikidata or most architecture sites. Network work runs on GitHub Actions (see "Tools
and GitHub Actions" in `CLAUDE.md`; `tools/fetch_summaries.py` and `tools/fetch_portraits.py` are working examples).
`tools/run_request.txt` only triggers on the data-collection branch, so either ask the owner to have the data-collection
chat run your tool, or add your own workflow on your branch. Suggested tools:

1. `tools/fetch_architect_sources.py`: for each architect, Wikidata (birth and death, citizenship, awards, practice,
   notable works) and the Wikipedia introduction, into `tools/architect_bios/sources.json`. A Sonnet chat can run and
   check this; you write from what it returns.
2. `tools/check_overview_links.py`: opens each candidate link, records status and page title.

## Order and review

1. First file `bios_01.json`: ten architects only, from the top of the list, mixing a famous person (Le Corbusier), a
   living practice (OMA), a Pritzker laureate with few buildings, and Zaha Hadid. Stop and report so the owner can
   approve the voice before you write the other 246.
2. Then batches of about 30. Keep `tools/architect_bios/progress.md` (done, skipped with reason, links failing).
3. Report quality problems in plain words: facts you could not source, architects with only a firm and no history.
   Warn at 5% unsourced facts in a batch, stop at 10%.

Work on branch `claude/architect-bios`, change only `tools/architect_bios/` and any new tool under `tools/`, and open a
pull request to `main` for each approved batch. Do not edit `site/` or `buildings.js`.
