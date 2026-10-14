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
