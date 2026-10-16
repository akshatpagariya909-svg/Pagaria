# Architect write-ups: progress

## Done
- `results/bios_01.json` (16 Oct 2026), first ten for the owner to approve the voice: Norman Foster, Renzo Piano,
  Oscar Niemeyer, Zaha Hadid, Le Corbusier, Alvar Aalto, Frank Gehry, Herzog & de Meuron, OMA, Glenn Murcutt.
  Bios 161–190 words. Every fact sourced (Wikipedia/Wikidata, fetched by `tools/fetch_architect_sources.py` into
  `sources.json`, plus the buildings' own Wikipedia articles). Unsourced facts: 0.
  Links: 46 tried, 39 kept, all checked 16 Oct 2026 by `tools/check_overview_links.py` (report: `links_report.json`).

## Skipped
- None yet.

## Links that failed and were left out
- Encyclopaedia Britannica (all ten): answers automated checks with 403. Probably fine in a browser, but unchecked.
- Pritzker page for Oscar Niemeyer (1988, shared with Gordon Bunshaft): `/laureates/1988`, `/1988-0`, `/1988-1`,
  `/oscar-niemeyer` all 404. Find the real address before the Bunshaft batch.
- herzogdemeuron.com: redirect loop for the checker (302).
- zaha-hadid.com/architecture/ 404 (the home page, now zha.com, is used instead).

## Weak spots to note
- Glenn Murcutt: Wikipedia has no articles on his houses, so the bio says little about each one. His materials list
  carries a "citation needed" tag on Wikipedia.
- Delirious New York: the OMA article says 1975, the Koolhaas article 1978 (publication). No year used.
- Paimio Sanatorium: wall says 1933, Wikipedia 1929–32. The wall's year is used.

## How to run the tools
Put the command on the first line of `tools/architect_bios/request.txt` and push to `claude/architect-bios`
(workflow `.github/workflows/architect-bios.yml`):
- `python -u tools/fetch_architect_sources.py --ranks 11-40` (Wikidata + Wikipedia into `sources.json`)
- `python -u tools/check_overview_links.py --files bios_02.json`
