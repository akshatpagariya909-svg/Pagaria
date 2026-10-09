import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 2


def hexc(c, a=None):
    if isinstance(c, tuple):
        if a is None:
            return c
        return (c[0], c[1], c[2], int(a * 255))
    c = c.lstrip('#')
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return (r, g, b) if a is None else (r, g, b, int(a * 255))


def mix(c1, c2, t):
    a, b = hexc(c1), hexc(c2)
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def jit(c, amt, rnd=random):
    a = hexc(c)
    d = rnd.randint(-amt, amt)
    return tuple(max(0, min(255, v + d + rnd.randint(-amt // 3, amt // 3))) for v in a)


class Art:
    def __init__(self, w, h, seed=1):
        self.w, self.h = w, h
        self.W, self.H = w * SS, h * SS
        self.img = Image.new('RGB', (self.W, self.H), 'white')
        self.d = ImageDraw.Draw(self.img, 'RGBA')
        self.r = random.Random(seed)
        self.ar = w / h

    def p(self, x, y):
        return (x * self.W, y * self.H)

    def pts(self, pts):
        return [self.p(x, y) for x, y in pts]

    def poly(self, pts, c, a=None):
        self.d.polygon(self.pts(pts), fill=hexc(c, a))

    def rect(self, x0, y0, x1, y1, c, a=None):
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        self.d.rectangle([*self.p(x0, y0), *self.p(x1, y1)], fill=hexc(c, a))

    def ell(self, x0, y0, x1, y1, c, a=None):
        self.d.ellipse([*self.p(x0, y0), *self.p(x1, y1)], fill=hexc(c, a))

    def line(self, pts, c, wd=0.002, a=None):
        self.d.line(self.pts(pts), fill=hexc(c, a), width=max(1, int(wd * self.W)))

    def grad(self, x0, y0, x1, y1, c0, c1, horiz=False):
        X0, Y0 = int(x0 * self.W), int(y0 * self.H)
        X1, Y1 = int(x1 * self.W), int(y1 * self.H)
        w, h = max(1, X1 - X0), max(1, Y1 - Y0)
        a, b = np.array(hexc(c0), float), np.array(hexc(c1), float)
        if horiz:
            t = np.linspace(0, 1, w)[None, :, None]
            arr = a + (b - a) * t
            arr = np.repeat(arr, h, axis=0)
        else:
            t = np.linspace(0, 1, h)[:, None, None]
            arr = a + (b - a) * t
            arr = np.repeat(arr, w, axis=1)
        self.img.paste(Image.fromarray(arr.astype('uint8')), (X0, Y0))

    def _layer(self):
        return Image.new('RGBA', (self.W, self.H), (0, 0, 0, 0))

    def _comp(self, layer):
        base = self.img.convert('RGBA')
        base.alpha_composite(layer)
        self.img = base.convert('RGB')
        self.d = ImageDraw.Draw(self.img, 'RGBA')

    def glow(self, cx, cy, rx, ry, c, a=0.6, blur=0.04):
        L = self._layer()
        d = ImageDraw.Draw(L)
        d.ellipse([*self.p(cx - rx, cy - ry), *self.p(cx + rx, cy + ry)], fill=hexc(c, a))
        L = L.filter(ImageFilter.GaussianBlur(blur * self.W))
        self._comp(L)

    def soft_poly(self, pts, c, a=0.5, blur=0.02):
        L = self._layer()
        d = ImageDraw.Draw(L)
        d.polygon(self.pts(pts), fill=hexc(c, a))
        L = L.filter(ImageFilter.GaussianBlur(blur * self.W))
        self._comp(L)

    def soft_line(self, pts, c, wd, a=0.6, blur=0.01):
        L = self._layer()
        d = ImageDraw.Draw(L)
        d.line(self.pts(pts), fill=hexc(c, a), width=max(1, int(wd * self.W)))
        L = L.filter(ImageFilter.GaussianBlur(blur * self.W))
        self._comp(L)

    def masked(self, pts, draw_fn):
        """draw_fn(art_like_draw) draws onto a full layer; result clipped to polygon."""
        L = self._layer()
        d = ImageDraw.Draw(L, 'RGBA')
        draw_fn(d)
        M = Image.new('L', (self.W, self.H), 0)
        ImageDraw.Draw(M).polygon(self.pts(pts), fill=255)
        alpha = Image.fromarray((np.array(L.split()[3], float) * np.array(M, float) / 255).astype('uint8'))
        L.putalpha(alpha)
        self._comp(L)

    def noise(self, x0, y0, x1, y1, amt=10, scale=1):
        X0, Y0 = int(x0 * self.W), int(y0 * self.H)
        X1, Y1 = int(x1 * self.W), int(y1 * self.H)
        region = np.array(self.img.crop((X0, Y0, X1, Y1)), float)
        h, w = region.shape[:2]
        if scale > 1:
            n = np.random.default_rng(self.r.randint(0, 9999)).normal(0, amt, (h // scale + 1, w // scale + 1, 1))
            n = np.repeat(np.repeat(n, scale, 0), scale, 1)[:h, :w]
        else:
            n = np.random.default_rng(self.r.randint(0, 9999)).normal(0, amt, (h, w, 1))
        region = np.clip(region + n, 0, 255)
        self.img.paste(Image.fromarray(region.astype('uint8')), (X0, Y0))
        self.d = ImageDraw.Draw(self.img, 'RGBA')

    def reflect(self, ywater, yend, tint, a=0.45, ripple=True):
        Yw, Ye = int(ywater * self.H), int(yend * self.H)
        h = Ye - Yw
        src = self.img.crop((0, max(0, Yw - h), self.W, Yw)).transpose(Image.FLIP_TOP_BOTTOM)
        if src.size[1] < h:
            src = src.resize((self.W, h))
        arr = np.array(src, float)
        if ripple:
            rows = arr.shape[0]
            for y in range(rows):
                off = int(math.sin(y * 0.35) * 3 * SS * (y / rows + 0.2))
                arr[y] = np.roll(arr[y], off, axis=0)
        t = np.array(hexc(tint), float)
        arr = arr * (1 - a) + t * a
        # darken with depth
        fade = np.linspace(0, 0.25, arr.shape[0])[:, None, None]
        arr = arr * (1 - fade) + t * fade
        self.img.paste(Image.fromarray(arr.astype('uint8')), (0, Yw))
        self.d = ImageDraw.Draw(self.img, 'RGBA')
        if ripple:
            for _ in range(int(60 * (yend - ywater) * 4)):
                y = self.r.uniform(ywater + 0.005, yend)
                x = self.r.uniform(0, 1)
                L = self.r.uniform(0.02, 0.08)
                self.line([(x, y), (x + L, y)], '#ffffff', 0.0012, a=self.r.uniform(0.05, 0.18))

    def people(self, y, xs, h=0.03, c='#2a2622'):
        for x in xs:
            hh = h * self.r.uniform(0.85, 1.1)
            self.rect(x - hh * 0.09 / self.ar, y - hh * 0.78, x + hh * 0.09 / self.ar, y, c)
            r = hh * 0.11
            self.ell(x - r / self.ar, y - hh, x + r / self.ar, y - hh + 2 * r, c)

    def tree(self, x, y, r, c='#3f5a32', c2='#5d7a45', trunk='#4a3a2c'):
        self.rect(x - r * 0.06, y - r * 0.6, x + r * 0.06, y, trunk)
        for i in range(7):
            dx = self.r.uniform(-r * 0.6, r * 0.6)
            dy = self.r.uniform(-r * 1.4, -r * 0.6)
            rr = r * self.r.uniform(0.45, 0.7)
            self.ell(x + dx - rr, y + dy * self.ar - rr * self.ar, x + dx + rr, y + dy * self.ar + rr * self.ar,
                     c if i % 2 else c2)

    def clouds(self, n, y0, y1, a=0.5):
        for _ in range(n):
            x = self.r.uniform(-0.1, 1.0)
            y = self.r.uniform(y0, y1)
            w = self.r.uniform(0.15, 0.35)
            self.glow(x + w / 2, y, w / 2, w * 0.12 * self.ar, '#ffffff', a=a * self.r.uniform(0.5, 1), blur=0.02)

    def save(self, path, grain=6, vignette=0.12):
        im = self.img.resize((self.w, self.h), Image.LANCZOS)
        arr = np.array(im, float)
        h, w = arr.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        rr = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / math.sqrt(2)
        arr *= (1 - vignette * rr ** 2)[:, :, None]
        arr += np.random.default_rng(7).normal(0, grain, (h, w, 1))
        Image.fromarray(np.clip(arr, 0, 255).astype('uint8')).save(path, quality=84, optimize=True, progressive=True)


def ellipse_pts(cx, cy, rx, ry, rot=0, n=48, ar=1.0):
    out = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        xr = x * math.cos(rot) - y * math.sin(rot)
        yr = x * math.sin(rot) + y * math.cos(rot)
        out.append((cx + xr, cy + yr * ar))
    return out


def arch_pts(x0, x1, ybase, ytop, n=20, pointed=False):
    """Arch outline (closed) from base-left up over to base-right."""
    cx = (x0 + x1) / 2
    rx = (x1 - x0) / 2
    pts = [(x0, ybase)]
    spring = ytop + (ybase - ytop) * 0.0
    for i in range(n + 1):
        t = math.pi - math.pi * i / n
        x = cx + rx * math.cos(t)
        y = ybase - (ybase - ytop) * math.sin(t) ** (0.6 if pointed else 1.0)
        if pointed:
            # sharpen near crown
            y = ybase - (ybase - ytop) * (math.sin(t) ** 0.5)
        pts.append((x, y))
    pts.append((x1, ybase))
    return pts
