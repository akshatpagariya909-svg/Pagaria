# YouTube channel kit

Everything needed to open the channel for Discover Architecture. Creating the channel
needs you signed in to Google, so that part is yours; this folder has the rest ready to paste
or upload. Takes about 20 minutes.

## What is in this folder

| File | Use it for | Size |
|---|---|---|
| `avatar.png` | Channel picture (YouTube crops it to a circle) | 800 × 800 |
| `banner.png` | Channel banner. The centre strip is the only part phones show, and all text sits in it | 2560 × 1440 |
| `banner-phone-preview.png` | What the banner looks like on a phone, just to check | 1546 × 423 |
| `watermark.png` | The small mark YouTube overlays on every video (Customisation → Branding) | 150 × 150 |
| `thumbnail-template.png` | A starting point for video thumbnails: one building, name big, architect small | 1280 × 720 |
| `banner-credits.md` | The photos in the banner. All public domain or CC0, so no credit is required | |

Regenerate the images with `python3 tools/youtube_art.py` after the data changes.
To make a thumbnail for a new video, open the template in any editor, swap the photo and the text.

## Step by step

1. Sign in to YouTube with the Google account you want to own the channel. Use the account
   that also owns the site's GitHub, so there is one login to remember.
2. Click your picture (top right) → **Create a channel**. Choose **Use a custom name**,
   not your personal name.
3. Name: **Discover Architecture**. Handle: try `@discoverarchitecture` first; if taken,
   `@discover.architecture`, then `@discoverarch`.
4. Open YouTube Studio → **Customisation** → **Branding**. Upload `avatar.png`, `banner.png`
   and `watermark.png` (set the watermark to show for the whole video).
5. **Customisation** → **Basic info**. Paste the description below. Add the links: the site first,
   then the GitHub repository. Set the contact email if you want one shown.
6. **Settings** → **Channel** → **Basic info**: country, and the keywords below.
   **Settings** → **Upload defaults**: paste the default description and tags, and set videos to
   **Public**, category **Education**, licence **Standard YouTube**, comments **Hold for review**.
7. **Settings** → **Channel** → **Advanced settings**: say the channel is *not* made for kids
   (it is for students; "made for kids" switches off comments and playlists).
8. Verify the channel (Settings → Channel → Feature eligibility → phone number). This unlocks
   custom thumbnails, videos longer than 15 minutes and the handle.
9. Send me the channel URL. I will add a YouTube link to the site and to every building's
   "Go deeper" list where a video exists.

## Text to paste

**Channel name**
Discover Architecture

**Description** (about section)

> A wall of 1,000 buildings for architecture students. Wander instead of search, find
> precedents by idea, and follow the links to drawings and articles.
>
> Short videos here walk through one building, one architect or one idea at a time,
> with the same free photos the site uses.
>
> The site: https://akshatpagariya909-svg.github.io/Pagaria/
>
> Photos are public domain or Creative Commons from Wikimedia Commons; each video credits
> them in the description.

**Keywords** (Settings → Channel → Basic info; comma separated)

architecture, architecture students, modern architecture, brutalism, parametric architecture,
architectural precedents, famous buildings, Le Corbusier, Mies van der Rohe, Louis Kahn,
Zaha Hadid, Tadao Ando, SANAA, OMA, case study, studio precedent, architecture history

**Links** (Customisation → Basic info → Links)

- Discover Architecture: https://akshatpagariya909-svg.github.io/Pagaria/
- All buildings A–Z: https://akshatpagariya909-svg.github.io/Pagaria/buildings/
- Source code: https://github.com/akshatpagariya909-svg/Pagaria

**Default video description** (Settings → Upload defaults)

> Open this building on the wall: https://akshatpagariya909-svg.github.io/Pagaria/buildings/BUILDING-ID/
>
> Discover Architecture is a wall of 1,000 buildings for architecture students: wander
> instead of search, find precedents by idea, and follow links to drawings and articles.
> https://akshatpagariya909-svg.github.io/Pagaria/
>
> Photo credits (Wikimedia Commons):
> PHOTOGRAPHER · LICENCE · LINK

Replace `BUILDING-ID` with the id from the site's URL (for example `villa-savoye`), and list
each photo you used with its credit, licence and source link, exactly as the site shows them.
CC BY and CC BY-SA photos must be credited; public domain and CC0 need not be, but do it anyway.

**Default tags**

architecture, architecture students, building, precedent, discover architecture

## First ten videos

Each one is 60 to 90 seconds: the building's photos from the site, the "Key features" line
read aloud or shown as text, then the three idea keywords. Vertical (Shorts) and landscape both
work; Shorts get found faster by new channels.

1. Villa Savoye · Le Corbusier · the Five Points in one house (`villa-savoye`)
2. Barcelona Pavilion · Mies van der Rohe and Lilly Reich · walls that stand free under a floating roof (`barcelona-pavilion`)
3. Salk Institute · Louis Kahn · the plaza and the sky (`salk-institute`)
4. Fallingwater · Frank Lloyd Wright · the cantilever (`fallingwater`)
5. Heydar Aliyev Center · Zaha Hadid · one continuous surface (`heydar-aliyev-center`)
6. Church of the Light · Tadao Ando · a cross cut from concrete (`church-of-the-light`)
7. Seagram Building · Mies van der Rohe · the plaza and the bronze mullions (`seagram-building`)
8. Indian Institute of Management Bangalore · Balkrishna Doshi · corridors under open pergolas (`indian-institute-of-management-bangalore`)
9. Gando Primary School · Francis Kéré · a roof that cools (`gando-primary-school`)
10. Habitat 67 · Moshe Safdie · stacked houses, each with a garden (`habitat-67`)

The id in brackets is the building's page: `https://akshatpagariya909-svg.github.io/Pagaria/buildings/<id>/`.

Three series ideas after that: **One idea, five buildings** (Courtyard, Pilotis, Light from
above), **One architect in three minutes**, and **Daily five** clips once the game ships.

## Rules the channel keeps, same as the site

- Free photos only: public domain, CC0, CC BY or CC BY-SA from Wikimedia Commons, never NC or ND.
  Credit every photo in the description.
- Music must be free too: YouTube's Audio Library (no attribution needed) is the simplest source.
- Building photos stay square-cornered in thumbnails; the mark, the red rule and the rest match the site.
- No invented facts. Say only what a source says, and link the source.
- Keep the on-screen text short.
