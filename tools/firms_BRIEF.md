# Faces for firms: their founders, together if possible

Read `tools/portraits_BRIEF.md` first: the same checks, licences and hard rules apply here.

The wall shows a firm's founders in place of a face for the firm (the owner's choice). Best of all is
**one free photo of all the founders together**: Herzog & de Meuron side by side, Sejima and
Nishizawa of SANAA, Diller and Scofidio. Failing that, a portrait of each founder.

`tools/firms_todo.json` lists the firms, most buildings first. `founders_we_list` is our current
list of founders (it may be empty or wrong: check it); `face_now` is the face the wall shows today.

For each firm:

1. **Who founded it?** Confirm the founders from a source (the firm's Wikipedia article or its
   own website) and give that URL. If the firm was founded by one person, the list has one name.
   If a source names no founders, write `founders: []` and say so.
2. **Together:** look on Commons for one photo showing all the founders (a partnership of two or
   three). Search the firm's Commons category, each founder's category and a file search with
   both surnames. It counts only if the description or categories name every founder shown, they
   are the main subject, and no one else is as prominent. A group of 10 at an award ceremony does
   not count.
3. **Each founder:** for each founder still without a face (see `face_now`), look for a single
   portrait as in `tools/portraits_BRIEF.md`.

Record every firm in `tools/firms_found.json`, in the order checked:

```json
{"firm": "Herzog & de Meuron",
 "founders": ["Jacques Herzog", "Pierre de Meuron"], "founders_source": "URL",
 "together": {"file": "File:….jpg", "license": "…", "author": "…", "evidence": "URL", "shows": "left to right: …"} ,
 "portraits": {"Jacques Herzog": {"file": "File:….jpg", "license": "…", "author": "…", "evidence": "URL"}},
 "note": "…"}
```

Use `null` for `together` and leave out a founder in `portraits` when nothing passes. Change only
`tools/firms_found.json`; commit after every 10 firms and push to your branch.
