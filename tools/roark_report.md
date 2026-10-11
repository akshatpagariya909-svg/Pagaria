# roark.archi: feasibility as a photo and building source

*Research only, 11 October 2026. No images were downloaded or committed, and nothing under `site/` was changed.*

**Verdict**
1. **Photos: don't take them from Roark, but nearly all of them are free Commons files we can take from the source.** In the sample, 510 of 518 photos (98.5%) are Wikimedia Commons files, and 507 of those pass our licence rules.
2. **Building list: useful as a cross-check, mainly for Europe and the US.** 2 of 40 random Roark buildings are on our wall, and about half the rest are worth studying. Roark is thin where we are strong (South Asia, Africa, Southeast Asia).
3. **Photo picker: the real win is how Roark chooses photos, not the photos themselves.** It offers more candidates per building (median 14.5 against our 6) and sorts them by type. In 6 of 20 shared buildings its page holds a clearly better lead photo than ours, and 1 of those 6 exposes a bug in our own lead choice (Millau Viaduct).

---

## How this was done

- **robots.txt** (`https://roark.archi/robots.txt`) allows all pages except `/api/`, `/me`, `/saved`, `/login`, `/admin` and `/m/`. None of those were requested.
- **71 requests to roark.archi in total**, at least 1.2 seconds apart, with the User-Agent `DiscoverArchitectureResearch/1.0 (https://github.com/akshatpagariya909-svg/Pagaria; one-off feasibility study)`. They were: robots.txt, the sitemap index (twice), 3 sub-sitemaps, 4 terms and about pages, and 61 building pages. No login was used and no limit was worked around.
- Each Roark building page carries its photo records in the page data: file URL, size, author, licence, licence URL, source URL and a type such as `photo_exterior`, `plan` or `section`. Those records were parsed; no image file was opened.
- Licences, sizes and quality marks come from the **Commons API**: 834 files in batches of 50 (17 batches), plus 1 more for our Fondazione Prada lead. Quality marks were read from both the file's categories and Commons' `Assessments` metadata. They are Featured picture (FP), Quality image (QI) and Valued image (VI).
- **Samples:**
  - **Main sample:** 40 buildings spaced evenly through Roark's whole sitemap list (every ~175th entry). It is used for every share and count below.
  - **Overlap sample:** 20 more buildings whose names match ours, spread evenly through the 400-odd name matches. They exist only so step 5 has enough shared buildings to compare. The main sample alone has just 2.

## 1. What Roark's terms say about sources and reuse

- About page (https://roark.archi/about): "Structure from Wikidata; photographs, plans and drawings from Wikimedia Commons, Europeana and the Art Institute of Chicago, each shown with its author, licence and source."
- Terms (https://roark.archi/terms), on reuse: "Images in the archive come from open collections under their own licences … Those licences, not these terms, say how you may reuse them."
- Terms, on use of the site: "use what you find for study and work, within the licence of each image. Do not: download or copy the archive in bulk, by script or otherwise …"
- Content and rights (https://roark.archi/legal): archive images come "from open collections: Wikimedia Commons, Europeana, the Art Institute of Chicago, and OpenStreetMap for site plans". Member uploads are separate: "Rights stay with the author."
- Legal notice (https://roark.archi/legal-notice): published by Soliton Co, Montrouge, France.

**In short:** Roark claims no rights over archive photos and sends you to each photo's own licence. It forbids bulk copying from its site. Member uploads (architects' and photographers' own work) remain under the uploader's copyright.

## 2. How big Roark is

**6,988 buildings.** This is the count of `/p/` building URLs in its two project sitemaps: https://roark.archi/sitemaps/projects-0.xml has 5,000 and projects-1.xml has 1,988. The home page says "6,980 buildings in 110 countries", and the architects page lists 385 architects.

Each sitemap entry also names the building's lead photo. **6,949 of the 6,988 lead photos (99.4%) are hosted on upload.wikimedia.org.** The other 39 come from European archives reached through Europeana, such as fotothek.slub-dresden.de and rs.cms.hu-berlin.de.

## (a) Can we use their photos directly?

**No.**
1. Our rule is to take every photo from its original Commons file, never from a third-party site.
2. Roark's terms forbid copying from the site by script.
3. Roark isn't the rights holder, so it adds nothing a Commons file doesn't already give us. Its credit and licence line is a copy of the Commons data: for all 831 Commons photos checked, Roark's licence label matched the Commons API exactly.
4. Some images on Roark are member uploads that stay the uploader's copyright, and the 8 Europeana photos in the sample aren't on Commons at all.

## (b) What share of their photos are free Commons files we could fetch ourselves?

Main sample: 40 buildings, 518 photos.

| | Count | Share |
|---|---|---|
| Photos from Wikimedia Commons | 510 | 98.5% |
| Photos from Europeana (not Commons, so outside our rule) | 8 | 1.5% |
| From ArchDaily, Dezeen, architects' sites, Roark itself, or unknown | 0 | 0% |
| Commons photos whose licence passes our rule (PD, CC0, CC BY, CC BY-SA) | 507 of 510 | 99.4% |
| NC or ND licences | 0 | 0% |
| **Commons photos with a Featured, Quality or Valued mark** | **2 of 510** (both QI) | **0.4%** |
| Buildings with at least one marked photo | 2 of 40 | 5% |

**The 3 Commons photos that need a look by hand:**
- `File:Ankara asv2021-10 img03 General Staff building.jpg` is under the Free Art Licence. That's a free licence, but not on our list.
- `File:Irwin Union Bank and Trust.JPG` is labelled only "Attribution".
- `File:A Column Capital, Kadırga Sokullu Mehmet Pasha Mosque, İstanbul (12966563613).jpg` is labelled "No restrictions", a Flickr Commons label.

**Licence mix** of the 510: CC BY-SA 4.0 ×232, CC BY-SA 3.0 ×117, public domain ×53, CC BY 2.0 ×49, CC0 ×25, CC BY 3.0 ×18, CC BY-SA 2.0 ×17, CC BY 4.0 ×3, CC BY 2.5 ×1, plus the 3 above.

**Resolution is high:**
- The median photo is 4,000 px on its long edge (12 megapixels).
- 385 of 510 are at least 3,000 px on the long edge.
- 32 are under 1,600 px.

**Photo types**, as Roark tags them: exterior 285, interior 115, detail 43, historical 23, aerial 21, drawing 15, construction 12, plan 2, section 2.

The overlap sample tells the same story. Of 324 photos, 321 are Commons, all 321 pass our rule, and 4 carry a mark: 4 QI, 1 of them also FP.

Quality marks are too rare to be a main filter. Free Commons photos are not: every building in the sample had at least one, and most had more than ten.

## (c) Is their building list useful as a cross-check?

**Yes, with a filter.**
- Of our 926 buildings, about **403 have a name that also appears on Roark**. That's a name-only match, so treat it as approximate.
- Roark's coverage follows Commons and Wikidata. Here's the share of our buildings it has, by region:

| Our region | On Roark (by name) |
|---|---|
| Europe | 201 of 421 |
| Americas | 89 of 169 |
| East Asia | 62 of 116 |
| Middle East | 23 of 76 |
| Oceania | 12 of 38 |
| South Asia | 11 of 49 |
| Southeast Asia | 4 of 30 |
| Africa | 1 of 27 |

So it is a good cross-check for Europe and North America and nearly useless for South Asia and Africa. Its own explore page lists only 47 buildings in India.

- **Main sample:** 2 of 40 are on our wall (30 St Mary Axe and Fondazione Prada), so 38 are missing. **18 of those 38 are worth studying** by the standard in (6), against 20 average.
- Missing buildings by architects we already feature:
  - Riverside Museum, Glasgow: Zaha Hadid, 13 of hers on our wall.
  - Kunsten, Aalborg: Alvar Aalto, 11 on our wall.
  - Tour Duo, Paris: Jean Nouvel, 14 on our wall.
  - Casa Caccia, Cadenazzo: Mario Botta, 10 on our wall.
  - Irwin Conference Center, Columbus: Eero Saarinen.
  - Becton Center, Yale: Marcel Breuer.
  - Danish Embassy, London: Arne Jacobsen.
  - Herbert and Katherine Jacobs First House: Frank Lloyd Wright.
  - Llotja de Sant Jordi, Alcoy: Santiago Calatrava.
- Missing architects, with none of their buildings on our wall:
  - Morphosis (Wayne L. Morse Courthouse)
  - Minoru Yamasaki (World Trade Center)
  - Angelo Mangiarotti (Milano Rogoredo station)
  - Rudolf Schwarz (Maria Königin, Saarbrücken)
  - Fernando Távora (Escola Primária do Cedro)
- If the sample holds, roughly 45% of Roark's list (on the order of 3,000 buildings) would pass a quality filter. That's an estimate from 40 buildings and could be well off. A practical use would be to run Roark's sitemap names against our list and Wikidata, and review the gaps by architect.

**Watch for name collisions and attribution differences.** Of the 20 name matches in the overlap sample:
- **17 are the same building, credited to the same architect.**
- **Liverpool Metropolitan Cathedral** is the same building, but Roark credits Edwin Lutyens (whose unbuilt design gave it the crypt) where we credit Frederick Gibberd.
- **Casa del Fascio** (Roark: Carlo Mollino, Voghera; ours: Giuseppe Terragni, Como) is a different building.
- **St Mary's Cathedral** (Roark: Pugin, Newcastle; ours: Kenzo Tange, Tokyo) is a different building.

Always match on name **and** architect, or on Wikidata ID.

**Roark's own data has some gaps**, so check before copying facts:
- Červený Hrádek's city shows as a raw Wikidata ID, "Q56416090".
- The World Trade Center has no city.
- The Allen Memorial Art Museum and MCA San Diego (La Jolla) are credited only to Venturi Scott Brown, who designed the additions.

## (d) What our photo picker should learn from Roark

All 20 shared buildings were compared: 2 from the main sample and 18 from the overlap sample. The 18 are the 17 exact matches plus Liverpool.
- **Our lead photo is among Roark's photos for 16 of 20.**
- **Roark's first photo is the same file as our lead for 13 of 20.** Both sites seem to start from Wikidata's main image (P18).
- Roark offers a median of 16.5 Commons photos per shared building; we keep 6.

| Verdict | Buildings |
|---|---|
| **Roark's page has a clearly better lead (6)** | **Asakusa Culture Tourist Information Center**: ours 914×1500; Roark has `…Center dllu.jpg` at 5780×4682. **Convention Centre Dublin**: ours 1772×2662; Roark has a 2025 photo at 4344×5792. **Van Gogh Museum**: ours 2052×1368; Roark has `Van Gogh Museum 2537.jpg`, a Quality image at 4632×3464. **Liverpool Metropolitan Cathedral**: ours 1944×2592; Roark has 6000×4000 (worth checking that it shows the cathedral). **The Glasshouse, Gateshead**: our lead is tagged Interior at 3008×2000; Roark has an exterior at 6655×4440. **Millau Viaduct**: our lead is `St Christopher church in Peyre (4).jpg`, a Quality image of a church. Roark has a Quality-image panorama of the valley (5994×3781), and our second photo is the viaduct. |
| **Possibly better, needs a look (4)** | **Glass House, New Canaan**: our lead `Relacion con la quebrada.jpg` is the right building (Commons files it under *Exterior of the Glass House, New Canaan*) and a good view, but only 1950×1350. Roark leads with Carol Highsmith's `Glass House 2006.jpg` (6248×4470), which is already our second photo. *(Corrected: an earlier draft of this report took the Spanish file name to mean a different building.)* **30 St Mary Axe**: ours 2631×3607 and tagged Interior though it's a street view; Roark has 5776×4336 from 2025. **Fondazione Prada**: ours 2708×3611; Roark has an entrance view at 3472×4640. **Belém Cultural Center**: ours is only 1280×959. Roark's largest file is titled after the Jerónimos Monastery, so pick by hand. |
| **Ours is as good or better (9)** | Elbphilharmonie, Kimbell Art Museum (same file), Isokon Building (same file), Torre Glòries (same Featured picture), Selimiye Mosque (ours 5538×3692; Roark's lead is 731×509), Rolex Learning Center (ours 5472×3648; Roark's lead is 1024×683), Nobel Peace Center, Nagasaki Prefectural Art Museum, Wexner Center |
| **Neither is good (1)** | Paul VI Audience Hall: both leads are views from St Peter's dome |

**Lessons for `tools/fetch_images.py`:**
1. **Gather a wider pool before choosing.** Roark pulls about 15 Commons photos per building; we choose from fewer. A bigger pool (the Commons category plus Wikidata P18 plus depicts/P180 searches) gives the picker better options. Choose from the pool, don't just accept Wikidata's main image: that image was small or weak in Asakusa, Dublin and Van Gogh.
2. **Set a minimum size for the lead photo,** for example 2,500 px on the long edge. Roark's median is 4,000 px, and every weak lead of ours above was 914–2,052 px. Use size before quality marks.
3. **Use FP, QI and VI as a tie-breaker, not a filter.** Only 0.4% of sampled photos carry one, and one mark sat on the wrong subject (the Peyre church).
4. **Check the photo shows the building.** Require the file title, description or Commons "depicts" data to name the building. That would have caught our Millau lead, a Quality image of a village church with the viaduct in the distance. Don't judge by file name alone, though: our Glass House lead has a Spanish name but is filed in the right Commons category.
5. **Classify photo type properly.** Roark tags each photo as exterior, interior, aerial, detail, historical, construction, plan, section, drawing or model with a vision model and a confidence score. Our tags put "Interior" on two street views (30 St Mary Axe, The Glasshouse). Prefer a recent exterior for the lead.
6. **Keep plans, sections and drawings.** Roark makes them first-class: 41 drawings, models, plans and sections across the 60 pages sampled. For students they are often worth more than a seventh exterior.
7. **Keep reading licences from Commons.** Roark's labels were faithful, but the Commons API is the source, and it is how the 3 edge cases above surfaced.

## The 40 sampled buildings (main sample)

"Worth studying" is a judgement for our audience (modern, contemporary, parametric, brutalism, regionalism, key historic precedents). It is not a statement about the building's merit in general. Licences are as Commons gives them; PD means public domain.

| # | Building | Architect (as Roark gives it) | City | Photos: source | Licences (Commons) | FP/QI/VI | On our wall | Worth studying? |
|---|---|---|---|---|---|---|---|---|
| 1 | [30 St Mary Axe](https://roark.archi/p/30-st-mary-axe) | Norman Foster | City of London | Commons 23 | CC BY-SA 4.0 ×9, CC BY 2.0 ×5, CC BY-SA 2.0 ×4, CC BY-SA 3.0 ×3, CC BY 3.0 ×2 | — | yes | worth |
| 2 | [Allen Memorial Art Museum](https://roark.archi/p/allen-memorial-art-museum) | Venturi Scott Brown | Ohio | Commons 8 | PD ×5, CC BY-SA 4.0 ×3 | — | no | worth |
| 3 | [Asilomar Conference Grounds](https://roark.archi/p/asilomar-conference-grounds) | Julia Morgan | Pacific Grove | Commons 15 | CC0 ×5, CC BY 2.0 ×4, CC BY-SA 4.0 ×2, CC BY-SA 2.0 ×2, CC BY-SA 3.0 ×1, PD ×1 | — | no | worth |
| 4 | [Becton Engineering and Applied Science Center](https://roark.archi/p/becton-engineering-and-applied-science-center) | Marcel Breuer | New Haven | Commons 18 | CC BY-SA 4.0 ×9, CC BY 2.0 ×7, CC BY-SA 3.0 ×1, PD ×1 | — | no | worth |
| 5 | [Brickell Flatiron](https://roark.archi/p/brickell-flatiron) | Enrique Norten / TEN Arquitectos | Miami | Commons 9 | CC BY-SA 4.0 ×6, CC BY 2.0 ×2, CC BY 3.0 ×1 | 1 | no | average |
| 6 | [Casa Caccia](https://roark.archi/p/casa-caccia) | Mario Botta | Cadenazzo | Commons 5 | CC BY-SA 3.0 ×5 | — | no | worth |
| 7 | [Červený Hrádek](https://roark.archi/p/cerveny-hradek) | Jan Kotěra | Jirkov (shown as “Q56416090”) | Commons 18 | CC BY-SA 3.0 ×11, CC BY-SA 4.0 ×5, PD ×2 | — | no | average |
| 8 | [Circles Pavilion](https://roark.archi/p/circles-pavilion) | Claude-Nicolas Ledoux | Arc-et-Senans | Commons 1 | CC BY 2.5 ×1 | — | no | average |
| 9 | [Danish Embassy building](https://roark.archi/p/danish-embassy-building) | Arne Jacobsen | Kensington | Commons 4 | CC BY-SA 3.0 ×2, CC BY-SA 4.0 ×1, CC BY-SA 2.0 ×1 | — | no | worth |
| 10 | [E. Clarke and Julia Arnold House](https://roark.archi/p/e-clarke-and-julia-arnold-house) | Frank Lloyd Wright | Columbus | Commons 15 | CC BY 2.0 ×10, CC BY 3.0 ×4, CC BY-SA 3.0 ×1 | — | no | average |
| 11 | [Escola Primária do Cedro](https://roark.archi/p/escola-primaria-do-cedro) | Fernando Távora | Vila Nova de Gaia | Commons 18 | CC BY-SA 4.0 ×18 | — | no | worth |
| 12 | [Fondazione Prada Building](https://roark.archi/p/fondazione-prada-building) | Rem Koolhaas / OMA | Milan | Commons 17 | CC BY-SA 4.0 ×11, CC BY 2.0 ×3, CC BY 3.0 ×3 | — | yes | worth |
| 13 | [General Staff Building](https://roark.archi/p/general-staff-building) | Clemens Holzmeister | Çankaya | Commons 6 | CC BY-SA 4.0 ×3, CC BY-SA 3.0 ×2, FAL ×1 | — | no | average |
| 14 | [Hadim Ibrahim Pasha Mosque](https://roark.archi/p/hadim-ibrahim-pasha-mosque) | Mimar Sinan | Istanbul | Commons 29 | CC BY-SA 4.0 ×29 | — | no | average |
| 15 | [Herbert and Katherine Jacobs First House](https://roark.archi/p/herbert-and-katherine-jacobs-first-house) | Frank Lloyd Wright | Madison | Commons 18 | CC BY-SA 4.0 ×7, CC BY 2.0 ×5, CC BY-SA 3.0 ×2, CC BY-SA 2.0 ×2, CC BY 3.0 ×1, CC0 ×1 | — | no | worth |
| 16 | [Hôtel Otlet](https://roark.archi/p/hotel-otlet) | Henry van de Velde | Brussels | Commons 20 | CC BY-SA 3.0 ×19, CC0 ×1 | — | no | average |
| 17 | [Irwin Conference Center](https://roark.archi/p/irwin-conference-center) | Eero Saarinen | Columbus | Commons 14 | PD ×9, CC BY-SA 3.0 ×2, CC BY 2.0 ×2, Attribution ×1 | — | no | worth |
| 18 | [Kara Ahmed Pasha Mosque](https://roark.archi/p/kara-ahmed-pasha-mosque) | Mimar Sinan | Istanbul | Commons 19 | CC BY-SA 4.0 ×18, PD ×1 | — | no | average |
| 19 | [Kunsten Museum of Modern Art Aalborg](https://roark.archi/p/kunsten-museum-of-modern-art-aalborg) | Alvar Aalto | Aalborg Municipality | Commons 13 | CC BY 2.0 ×7, CC BY-SA 3.0 ×3, CC BY-SA 4.0 ×3 | — | no | worth |
| 20 | [Llotja de Sant Jordi](https://roark.archi/p/llotja-de-sant-jordi) | Santiago Calatrava | Alcoy | Commons 5 | CC BY-SA 4.0 ×4, CC BY 3.0 ×1 | — | no | worth |
| 21 | [Maria Königin (Saarbrücken)](https://roark.archi/p/maria-konigin-saarbrucken) | Rudolf Schwarz | Saarbrücken | Commons 15 | CC BY-SA 3.0 ×11, CC0 ×2, CC BY 2.0 ×2 | — | no | worth |
| 22 | [Milano Rogoredo railway station](https://roark.archi/p/milano-rogoredo-railway-station) | Angelo Mangiarotti | Milan | Commons 12 | CC BY-SA 4.0 ×9, PD ×3 | — | no | worth |
| 23 | [Museum of Contemporary Art San Diego (La Jolla branch)](https://roark.archi/p/museum-of-contemporary-art-san-diego-la-jolla-branch) | Venturi Scott Brown | San Diego | Commons 8 | CC BY-SA 3.0 ×6, CC0 ×1, CC BY-SA 4.0 ×1 | — | no | average |
| 24 | [New London Union Station](https://roark.archi/p/new-london-union-station) | H. H. Richardson | New London | Commons 29 | PD ×18, CC BY-SA 4.0 ×7, CC BY-SA 3.0 ×4 | — | no | average |
| 25 | [One Detroit Center](https://roark.archi/p/one-detroit-center) | Philip Johnson | Detroit | Commons 17 | CC BY-SA 4.0 ×7, CC BY-SA 3.0 ×4, CC BY-SA 2.0 ×3, CC0 ×2, CC BY 2.0 ×1 | — | no | average |
| 26 | [Palazzi Bernini](https://roark.archi/p/palazzi-bernini) | Gian Lorenzo Bernini | Rome | Commons 2 | CC BY-SA 4.0 ×1, CC BY-SA 3.0 ×1 | 1 | no | average |
| 27 | [Peterkův dům](https://roark.archi/p/peterkuv-dum) | Jan Kotěra | Prague | Commons 9 | CC BY-SA 3.0 ×8, CC BY 3.0 ×1 | — | no | average |
| 28 | [Prokop Diviš museum in Přímětice](https://roark.archi/p/prokop-divis-museum-in-primetice) | Bohuslav Fuchs | Přímětice | Commons 2 | CC BY-SA 3.0 ×2 | — | no | average |
| 29 | [Riverside Museum](https://roark.archi/p/riverside-museum) | Zaha Hadid | Glasgow City | Commons 7 | CC BY-SA 4.0 ×4, CC BY-SA 2.0 ×2, CC BY 2.0 ×1 | — | no | worth |
| 30 | [Samuel Merrill House](https://roark.archi/p/samuel-merrill-house) | Greene and Greene | Pasadena | Commons 1 | CC BY-SA 3.0 ×1 | — | no | average |
| 31 | [Secondo palazzo Montecatini](https://roark.archi/p/secondo-palazzo-montecatini) | Gio Ponti | Milan | Commons 2 | CC BY 4.0 ×1, CC0 ×1 | — | no | worth |
| 32 | [Sokollu Mehmed Pasha I Mosque](https://roark.archi/p/sokollu-mehmed-pasha-i-mosque) | Mimar Sinan | Istanbul | Commons 21 | CC BY-SA 4.0 ×14, PD ×4, CC BY-SA 3.0 ×1, CC BY 4.0 ×1, No restrictions ×1 | — | no | worth |
| 33 | [St. George's Church](https://roark.archi/p/st-george-s-church) | Clemens Holzmeister | Cologne | Commons 20, Europeana 1 | CC BY-SA 4.0 ×13, PD ×5, CC0 ×1, CC BY 4.0 ×1 | — | no | average |
| 34 | [Suzhou Culture and Arts Centre](https://roark.archi/p/suzhou-culture-and-arts-centre) | Paul Andreu | Suzhou | Commons 17 | CC BY-SA 4.0 ×11, CC BY-SA 3.0 ×4, CC BY 3.0 ×2 | — | no | average |
| 35 | [The Grange, Ramsgate](https://roark.archi/p/the-grange-ramsgate) | Augustus Pugin | Ramsgate | Commons 19, Europeana 1 | CC0 ×10, CC BY-SA 2.0 ×3, CC BY-SA 4.0 ×3, CC BY-SA 3.0 ×2, PD ×1 | — | no | average |
| 36 | [Tour Duo](https://roark.archi/p/tour-duo) | Jean Nouvel | Paris | Commons 18 | CC BY-SA 4.0 ×16, CC0 ×1, CC BY-SA 3.0 ×1 | — | no | worth |
| 37 | [Vajda Péter Music Elementary School and Sports School](https://roark.archi/p/vajda-peter-music-elementary-school-and-sports-school) | Ödön Lechner | Budapest District VIII | Commons 14 | CC BY-SA 4.0 ×13, CC BY-SA 3.0 ×1 | — | no | average |
| 38 | [Villa Pavlíček](https://roark.archi/p/villa-pavlicek) | Bohuslav Fuchs | Brno | Commons 4 | CC BY-SA 3.0 ×4 | — | no | average |
| 39 | [Wayne L. Morse United States Courthouse](https://roark.archi/p/wayne-l-morse-united-states-courthouse) | Morphosis | Eugene | Commons 18 | CC BY-SA 3.0 ×15, CC BY 3.0 ×3 | — | no | worth |
| 40 | [World Trade Center twin towers](https://roark.archi/p/world-trade-center-twin-towers) | Minoru Yamasaki | New York (no city shown) | Europeana 6 |  | — | no | worth |

**Quality of the list (step 6):** **20 of 40 are worth studying**, and 20 are average or generic for our audience.
- **Worth studying:** clear precedents such as Riverside Museum, Fondazione Prada, Kunsten, Escola do Cedro, the Becton Center and the Wayne L. Morse Courthouse.
- **Average or generic:** commercial towers (Brickell Flatiron, One Detroit Center), lesser works by famous names (E. Clarke Arnold House, Samuel Merrill House), and regional heritage buildings of local interest (Červený Hrádek, Villa Pavlíček, Prokop Diviš museum).
- **Thin pages:** 2 buildings have a single photo (Circles Pavilion, Samuel Merrill House), and 3 have two (Palazzi Bernini, Prokop Diviš museum, Secondo palazzo Montecatini).

This matches the owner's impression: some excellent buildings, but many average ones. Filter by architect and type before adding anything from Roark.
