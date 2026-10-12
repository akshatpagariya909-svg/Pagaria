"""Draw the YouTube channel art for Discover Architecture.

    python3 tools/youtube_art.py

Writes into brand/youtube/:
  avatar.png              800 x 800   channel picture (YouTube shows it as a circle)
  banner.png              2560 x 1440 channel banner; the 1546 x 423 centre is the part every device shows
  watermark.png           150 x 150   small transparent mark shown on videos
  thumbnail-template.png  1280 x 720  a starting point for video thumbnails
  banner-credits.md       the photos used in the banner, with author and licence

Uses the site's own fonts (Archivo for the mark, IBM Plex Mono for small labels) and
only public-domain or CC0 photos already on the site, so nothing needs a credit line
inside the image. Fonts are fetched from Google Fonts into brand/youtube/fonts/ if missing.
"""
import json, random, re, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
OUT = ROOT / 'brand' / 'youtube'
FONTS = OUT / 'fonts'
WHITE, INK, RED, PAPER, HAIR = (255, 255, 255), (17, 17, 16), (218, 58, 38), (247, 247, 245), (230, 228, 223)

FONT_CSS = {
    'archivo-black.ttf': 'https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@125,850',
    'plex-mono.ttf': 'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500',
}


def font(name, size):
    path = FONTS / name
    if not path.exists():
        FONTS.mkdir(parents=True, exist_ok=True)
        css = urllib.request.urlopen(FONT_CSS[name], timeout=30).read().decode()
        url = re.findall(r'url\((https://[^)]+\.ttf)\)', css)[-1]
        path.write_bytes(urllib.request.urlopen(url, timeout=60).read())
    return ImageFont.truetype(str(path), size)


def buildings():
    s = (SITE / 'data' / 'buildings.js').read_text()
    return json.loads(s[s.index('['):s.rindex(']') + 1])


def free_photos():
    """Photos the site hosts itself that need no credit line: public domain or CC0."""
    pics = []
    for b in buildings():
        for im in b.get('images', [])[:1]:  # the main photo only: the one the wall shows
            # Exterior photos only: the public-domain set also holds portraits, paintings and events.
            if im.get('license') in ('CC0', 'Public domain') and im.get('kind') == 'Exterior' \
                    and not im['thumb'].endswith('.svg') and (SITE / im['thumb']).exists():
                pics.append((b, im))
    random.Random(7).shuffle(pics)
    return pics


def cover(im, w, h):
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1))
    left, top = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((left, top, left + w, top + h))


def mark(draw, x, y, size, anchor='la'):
    """The site's wordmark: DISCOVER over ARCHITECTURE. with the second word in sunset red."""
    f = font('archivo-black.ttf', size)
    draw.text((x, y), 'DISCOVER', font=f, fill=INK, anchor=anchor)
    draw.text((x, y + size * 0.98), 'ARCHITECTURE.', font=f, fill=RED, anchor=anchor)
    return draw.textbbox((x, y + size * 0.98), 'ARCHITECTURE.', font=f, anchor=anchor)


def avatar():
    im = Image.new('RGB', (800, 800), WHITE)
    d = ImageDraw.Draw(im)
    # Big "DA." monogram reads at 36 px; the full name does not.
    f = font('archivo-black.ttf', 300)
    d.text((400, 372), 'DA', font=f, fill=INK, anchor='mm')
    d.text((400, 372), 'DA', font=f, fill=INK, anchor='mm')
    small = font('plex-mono.ttf', 34)
    d.text((400, 585), 'DISCOVER ARCHITECTURE', font=small, fill=INK, anchor='mm')
    d.rectangle((330, 535, 470, 541), fill=RED)
    im.save(OUT / 'avatar.png')


def banner():
    W, H = 2560, 1440
    canvas = Image.new('RGB', (W, H), PAPER)
    pics = free_photos()
    # Equal-width columns, like the wall. Tiles are square-cornered. Photos never hit the safe area.
    cols, gap = 10, 8
    cw = (W - gap * (cols + 1)) // cols
    used = []
    k = 0
    heights = [0] * cols
    y0 = gap
    while min(heights) < H:
        c = heights.index(min(heights))
        b, im = pics[k % len(pics)]
        k += 1
        pic = Image.open(SITE / im['thumb']).convert('RGB')  # 520 px thumbs are plenty for 248 px columns
        th = int(cw * min(max(pic.height / pic.width, 0.75), 1.5))
        x, y = gap + c * (cw + gap), y0 + heights[c]
        canvas.paste(cover(pic, cw, th), (x, y))
        heights[c] += th + gap
        used.append((b, im))
    # Soften the wall so the name sits on a calm centre, like a sheet opening over the wall.
    veil = Image.new('RGB', (W, H), WHITE)
    canvas = Image.blend(canvas, veil, 0.3)
    # Safe area: 1546 x 423, centred. Everything that matters stays inside it.
    sx, sy, sw, sh = (W - 1546) // 2, (H - 423) // 2, 1546, 423
    d = ImageDraw.Draw(canvas)
    d.rectangle((sx, sy, sx + sw, sy + sh), fill=WHITE)
    d.rectangle((sx, sy, sx + sw, sy + sh), outline=HAIR, width=2)
    mark(d, sx + 70, sy + 78, 118)
    f = font('plex-mono.ttf', 30)
    d.text((sx + sw - 70, sy + 94), 'A WALL OF 1,000 BUILDINGS', font=f, fill=INK, anchor='ra')
    d.text((sx + sw - 70, sy + 142), 'FOR ARCHITECTURE STUDENTS', font=f, fill=INK, anchor='ra')
    d.text((sx + sw - 70, sy + sh - 94), 'AKSHATPAGARIYA909-SVG.GITHUB.IO/PAGARIA', font=f, fill=INK, anchor='ra')
    canvas.save(OUT / 'banner.png')
    # Also save a crop of exactly what phones show, to check it.
    canvas.crop((sx, sy, sx + sw, sy + sh)).save(OUT / 'banner-phone-preview.png')
    lines = ['# Photos in banner.png', '', 'All public domain or CC0 from Wikimedia Commons, so no credit is required; listed here anyway.', '']
    seen = set()
    for b, im in used:
        if im['source'] in seen:
            continue
        seen.add(im['source'])
        lines.append(f"- {b['name']} ({b['by']}) · {im.get('credit') or 'unknown'} · {im['license']} · {im['source']}")
    (OUT / 'banner-credits.md').write_text('\n'.join(lines) + '\n')


def watermark():
    im = Image.new('RGBA', (150, 150), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 149, 149), radius=16, fill=(255, 255, 255, 235))
    f = font('archivo-black.ttf', 64)
    d.text((75, 68), 'DA', font=f, fill=INK, anchor='mm')
    d.rectangle((48, 108, 102, 113), fill=RED)
    im.save(OUT / 'watermark.png')


def thumbnail_template():
    """One building photo, square-cornered, with the name big and the architect small. Copy, swap the photo and text."""
    W, H = 1280, 720
    im = Image.new('RGB', (W, H), WHITE)
    b, pic = next((b, p) for b, p in free_photos() if p.get('kind') == 'Exterior' and (SITE / p['src']).exists())
    photo = cover(Image.open(SITE / pic['src']).convert('RGB'), 760, H)
    im.paste(photo, (W - 760, 0))
    d = ImageDraw.Draw(im)
    mark(d, 56, 56, 34)
    words = b['name'].upper().split()
    size = 58
    while size > 30 and max(d.textlength(w, font=font('archivo-black.ttf', size)) for w in words) > 410:
        size -= 2  # shrink until the longest word fits the left column
    f = font('archivo-black.ttf', size)
    lines, cur = [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=f) > 410 and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    lines.append(cur)
    y = 270
    for ln in lines[:4]:
        d.text((56, y), ln, font=f, fill=INK); y += int(size * 1.1)
    small = font('plex-mono.ttf', 26)
    d.text((56, y + 18), f"{b['by']} · {b['year']}".upper(), font=small, fill=INK)
    d.rectangle((56, H - 70, 56 + 120, H - 62), fill=RED)
    im.save(OUT / 'thumbnail-template.png')


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    avatar(); banner(); watermark(); thumbnail_template()
    print('Wrote', sorted(p.name for p in OUT.iterdir() if p.is_file()))
