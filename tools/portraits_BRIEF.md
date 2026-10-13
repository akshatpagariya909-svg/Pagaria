# Finding free portraits of architects

Discover Architecture is a wall of buildings for architecture students. When a building opens, its
architect's portrait sits next to the byline, in black and white, with its credit. 514 architects
have one. `tools/portraits_todo.json` lists the people still without one, most buildings first. This
brief is for finding their portraits by hand on Wikimedia Commons.

## The job

Work through `tools/portraits_todo.json` from the top, the entries with `buildings` of 2 or more
first. For each name:

1. **Firm, not a person?** Some entries are firms or partnerships ("Coop Himmelbau", "Diller
   Scofidio", "Denton Corker Marshall", "Sauerbruch Hutton"). Don't look for them: record status
   `firm`. A name that is half of a partnership ("de Meuron") is a person: look for Pierre de Meuron.
2. **Who is it?** Find the person on Wikidata or Wikipedia and confirm they are the architect (or
   engineer) of the example building given. Note their Wikidata id (Q…).
3. **Find a portrait on Commons.** Use WebFetch (the sandbox's own network can't reach Wikimedia):
   - Wikidata's image: `https://www.wikidata.org/w/api.php?action=wbgetclaims&entity=<Q>&property=P18&format=json`
   - The person's Commons category: `https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtype=file&cmlimit=100&format=json&cmtitle=Category:<Name>`
   - File search: `https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srlimit=20&format=json&srsearch=<Name> architect`
   - A file's licence, author and size: `https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=size|extmetadata&format=json&titles=File:<name>`
4. **Check it.**
   - **Licence:** public domain, CC0, CC BY or CC BY-SA only. Never NC, ND, GFDL-only, FAL or "fair use".
   - **Who it shows:** the file must show this person. Rely on its description or categories naming them, not only the file name. One person, face clearly visible.
   - **What it shows:** a photo or drawn portrait of the person. Not a group photo where they are hard to pick out, not a statue, not a stamp or banknote, not a building.
   - **Size:** at least 300px on its short side.
5. **Record it** in `tools/portraits_found.json` (below). If nothing passes, record status `none`
   and say what you saw. A wrong face is far worse than no face: when unsure, it's `none`.

## Hard rules

- **No personal data in any request.** Never put an email address, name or account of the person
  you work for in a URL, header, User-Agent or search. Use WebFetch as it is.
- **Only what a source says.** Every `found` entry gives the URL that shows who the file depicts.
- **Change only `tools/portraits_found.json`.** Don't edit `site/`, `site/data/`, other tools,
  workflow files or request files (`tools/*_request.txt`). Commit and push only that file, to your
  own branch.

## Output: `tools/portraits_found.json`

A list, one object per name, in the order you checked them:

```json
{"name": "Jørn Utzon", "status": "found | none | firm",
 "wikidata": "Q…", "file": "File:….jpg", "license": "CC BY-SA 4.0", "author": "…",
 "evidence": "URL whose description or category names the person", "note": "anything a reviewer should know"}
```

Commit after every 20 names, so work isn't lost. Stop after the entries with 2 or more buildings
(about 130 names) and report how many you found, how many `none` and how many `firm`.

## Afterwards (done by the reviewing chat, not you)

The reviewer checks a sample by eye. Accepted portraits go into `tools/portraits_manual.json`
(`{"name as in the by line": "File:…"}`), and `tools/fetch_portraits.py` adds them to the site,
checking each licence again.
