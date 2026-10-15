# Quality watch, round by round

The owner's rule (CLAUDE.md, 14 Oct 2026): every round reports these five numbers and warns before quality drops.

| Signal | Warn | Stop |
|---|---|---|
| Leads held back in photo review | 8% | 15% |
| Proposals with no free photo | 35% | 50% |
| Proposals already on the wall | 25% | 40% |
| Facts failing the source check | 3% | 6% |
| Ordinary types (offices, housing, hotels, malls) | 20% | 30% |

A steady rise across rounds is also a warning, even below the levels.

## Round 7 (14 Oct 2026), first batch: UK and Ireland, France and Italy, USA east and west, Eastern Europe (first 10), Canada and Mexico

395 proposals from six Sonnet chats.

| Signal | Number | Level |
|---|---|---|
| Leads held back in photo review | 8 of 334 (2%) | fine |
| No free photo | 39 of 395 (10%) | fine |
| Already on the wall | 4 of 395 (1%): Grand Théâtre de Rabat, Neutra VDL House, San Antonio Central Library, and the Bourse de Commerce proposed twice | fine |
| Facts failing the source check | 0 of 40 checked at random (0%) | fine |
| Ordinary types | 76 of 358 with full facts (21%) as proposed; 15% after 23 ordinary towers and hotels were held back | **warned** (owner told on 14 Oct) |

Also found: five older pairs on the wall were the same building under two names (Klippan church, MuBE, Anacleto Angelini centre, Yamanashi centre, Smiling Lion); the second of each was removed, and `add_illustrated.py` now skips a proposal whose Commons category and year match a building already on the wall.

Galleries: about 370 off-topic pictures (people, signs, artworks, street views, other buildings) were taken out of the new buildings' galleries by eye.

## Round 7, second batch (14 Oct 2026): USA east (rest), Eastern Europe (rest), Benelux, Southeast Asia

184 new proposals from four Sonnet chats.

| Signal | Number | Level |
|---|---|---|
| Leads held back in photo review | 7 of 162 (4%): Kozara monument, Manila Film Center, Pasig Revolving Tower, Capitan Luis Gonzaga Building, IFI Cathedral, Blue Cross-Blue Shield Chicago, Highfield House (its photos showed other buildings) | fine, but up from 2% |
| No free photo | 6 of 184 (3%) | fine |
| Already on the wall | 0 | fine |
| Facts failing the source check | 0 of 35 checked at random | fine |
| Ordinary types | 43 of 184 (23%) as proposed, Southeast Asia about 30%; 17% after 15 generic towers were held back | **warned**, and rising (21% → 23%) |

For the next round: the brief should ask Southeast Asian and other skyline-heavy themes for fewer office towers, and the photo check should open the Commons category, not only file names (the Southeast Asia and Manila chats could not see thumbnails).

## Round 8, first batch (14 Oct 2026): South America, Middle East and Turkey, South Asia

276 proposals from three Sonnet chats, under the round 8 brief (few ordinary types, photos seen, not picked by name).

| Signal | Number | Level |
|---|---|---|
| Leads held back in photo review | 9 of 243 (4%): Troy Museum, Abboud Building, Mohammed Bin Rashid Library, Mathaf, Education City Stadium, Hamad Airport, Tbilisi Wedding Palace, Vigyan Bhawan, Visvesvaraya Centre | fine, level with round 7b |
| No free photo | 30 of 276 (11%), South Asia 18% | fine |
| Already on the wall | 2 of 276 (1%): Tomb of Avicenna, NCPA Mumbai | fine |
| Facts failing the source check | 0 of 40 checked at random | fine |
| Ordinary types | 21 of 276 (8%) as proposed | fine, down from 23%: the brief change worked |

Galleries are still the weak spot: 348 off-topic pictures (tourists, plaques, other buildings, one gallery of the Empire State Building) taken out by eye.

## Round 8, second batch (14 Oct 2026): Africa, Japan and Korea

89 proposals from two Sonnet chats (the Africa chat picked from Commons categories without seeing thumbnails).

| Signal | Number | Level |
|---|---|---|
| Leads held back in photo review | 1 of 82 (1%): Heroes' Acre, Windhoek | fine |
| No free photo | 6 of 89 (7%) | fine |
| Already on the wall | 0 | fine |
| Facts failing the source check | 1 of 81, every building checked (1%): Daejeon science museum year 1984 → 1990, corrected. The first random 25 showed 4%, over the warning level, so the whole batch was checked. | fine |
| Ordinary types | 3 of 89 (3%); Carlton Centre held back | fine |

110 off-topic gallery pictures out; 26 buildings got a better lead from their own gallery.

## Gallery clean-up (15 Oct 2026), after the owner's and tester's reports

Every gallery photo on the wall was checked again (13,471 photos from rounds 1–6 by seven Sonnet helpers, every flag then checked by eye; every round 7–8 main photo re-checked by eye with the stricter rule).

- 1,626 photos taken out: people, events, sculptures, paintings, objects, signs, streets and unrelated views. 269 interiors that were labelled "Exterior" were relabelled.
- 193 buildings got a new main photo of the building itself, chosen from their own gallery.
- 54 buildings came off the wall because no photo shows the building (listed in `recheck.md`; the photo rescue looks for them later). Of these, 14 were added in rounds 7–8.
- 3 duplicates merged (Omar Khayyam mausoleum, Yale A&A Building, Entebbe hospital); `add_illustrated.py` now also catches the same architect, year and place under reworded names.

What went wrong in rounds 7–8: the review looked at leads and galleries in one pass, at small size, and let through main photos where the building was small, far off, at night or seen from inside a stadium. From now on a main photo must show the whole building from outside, in daylight, as the clear subject; a building whose only photos fail this stays off the wall.

## Design chat flags (15 Oct 2026)

The Design chat, checking galleries for the "Worth the swipe" dots, flagged 43 problems in 40 buildings (`tools/worth_swipe_flags.md` on `claude/design`). Each was checked by eye; 39 were right.

- 17 buildings got a new main photo: 11 from their own gallery, and 6 from photos newly picked on Commons and checked by eye (Park Güell, Széchenyi Bath, the Art Institute's Modern Wing, Fondazione Prada, 330 North Wabash, Cleo Rogers Library).
- 70 photos taken out: other buildings (Tower of London in the Curtain Wall House, a pagoda forest in the Centre for Earth Architecture, Trump Tower in 330 North Wabash, Emerson's Boston buildings, Hotel Adlon, the Bundeskunsthalle), plus artworks, people, night shots and a satellite view.
- 4 buildings came off the wall because no free photo shows them from outside: Grande Arche (France has no freedom of panorama, so Commons keeps only details), Athens Olympic Stadium roof, Notre-Dame-de-Lourdes in Casablanca, and the Fagnano Olona school. The photo rescue will look again.
- Left as it is: the Capanema Palace main photo (the pilotis are the subject; the child is tiny).
