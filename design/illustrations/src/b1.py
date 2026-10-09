from lib import *

P = (900, 1125)   # portrait 4:5
T = (800, 1200)   # tall 2:3
L = (1200, 900)   # landscape 4:3
W = (1400, 900)   # wide
S = (1000, 1000)  # square


def casa_gilardi():
    a = Art(*P, seed=1)
    a.grad(0, 0, 1, 0.66, '#2D4FB4', '#1B3584')
    a.poly([(0, 0), (1, 0), (0.84, 0.09), (0.2, 0.09)], '#EDE4DA')
    a.soft_poly([(0.24, 0.0), (0.46, 0.0), (0.46, 0.09), (0.24, 0.09)], '#FFF6D8', 0.9, 0.01)
    # yellow corridor slot
    a.rect(0.25, 0.2, 0.33, 0.62, '#F0BE2C')
    a.grad(0.25, 0.2, 0.33, 0.62, '#F7D35A', '#D99A12')
    # left wall
    a.poly([(0, 0), (0.2, 0.09), (0.2, 0.62), (0, 0.74)], '#F0D6DA')
    a.grad(0, 0.0, 0.2, 0.74, '#F6E3E4', '#DCB5BC', horiz=True)
    a.poly([(0.2, 0.62), (0, 0.74), (0, 0.0), (-0.01, 0)], '#EDE4DA', 0)  # noop keeps shape
    # mask left wall with trapezoid edges
    a.poly([(0, 0), (0.2, 0.09), (0, 0.09)], '#EDE4DA')
    a.poly([(0, 0.74), (0.2, 0.62), (0.2, 0.66), (0, 0.8)], '#1B3584')
    # right wall magenta in shadow
    a.poly([(1, 0), (0.84, 0.09), (0.84, 0.62), (1, 0.74)], '#B93766')
    a.poly([(1, 0), (0.84, 0.09), (1, 0.09)], '#EDE4DA')
    # light beam
    a.soft_poly([(0.24, 0.09), (0.46, 0.09), (0.7, 0.64), (0.4, 0.64)], '#FFE7A0', 0.28, 0.03)
    # red column
    a.rect(0.52, 0.16, 0.65, 0.65, '#D5263F')
    a.grad(0.52, 0.16, 0.65, 0.65, '#E23A4E', '#B81B34')
    a.poly([(0.65, 0.16), (0.69, 0.18), (0.69, 0.64), (0.65, 0.65)], '#8F1530')
    a.soft_poly([(0.52, 0.16), (0.56, 0.16), (0.58, 0.65), (0.52, 0.65)], '#FFD9A0', 0.25, 0.01)
    # water
    a.grad(0, 0.62, 1, 1, '#2C9CC2', '#0B4F78')
    a.poly([(0, 0.74), (0.2, 0.62), (0, 0.62)], '#F0D6DA')
    a.poly([(1, 0.74), (0.84, 0.62), (1, 0.62)], '#B93766')
    a.rect(0.2, 0.615, 0.84, 0.625, '#F4EEE6')
    # column reflection
    for i in range(40):
        y = 0.63 + i * 0.0085
        off = math.sin(i * 0.9) * 0.012
        a.rect(0.52 + off, y, 0.65 + off, y + 0.006, '#E8566E', a=0.55 - i * 0.011)
    a.rect(0.25, 0.63, 0.33, 0.7, '#F0BE2C', a=0.25)
    a.reflect(0.625, 1.0, '#13618C', a=0.25)
    a.noise(0, 0, 1, 1, 4)
    return a


def cuadra():
    a = Art(*L, seed=2)
    a.grad(0, 0, 1, 0.66, '#8DBBE2', '#E3ECEF')
    a.tree(0.06, 0.62, 0.12, '#405A35', '#56703F')
    a.rect(0.06, 0.2, 0.5, 0.66, '#E5859F')
    a.grad(0.06, 0.2, 0.5, 0.66, '#EE9AB0', '#D46F8D', horiz=True)
    a.rect(0.42, 0.34, 0.68, 0.66, '#7A4C8B')
    a.rect(0.6, 0.1, 0.94, 0.66, '#C5582F')
    a.grad(0.6, 0.1, 0.94, 0.66, '#D2683B', '#A9461F', horiz=True)
    a.rect(0.94, 0.3, 1.0, 0.66, '#E9B7C4')
    # chute
    a.rect(0.66, 0.28, 0.73, 0.31, '#8B3A1C')
    for i in range(14):
        x = 0.672 + i * 0.004
        a.soft_line([(x, 0.31), (x + 0.004, 0.68)], '#FFFFFF', 0.0016, a=0.5, blur=0.002)
    a.rect(0, 0.66, 1, 0.86, '#5E7F86')
    a.reflect(0.66, 0.86, '#3F6670', a=0.35)
    a.glow(0.69, 0.69, 0.05, 0.01, '#FFFFFF', 0.6, 0.01)
    a.grad(0, 0.86, 1, 1, '#D2BC93', '#B79E74')
    a.rect(0, 0.855, 1, 0.865, '#EADBC0')
    a.noise(0, 0, 1, 1, 4)
    return a


def masp():
    a = Art(*W, seed=3)
    a.grad(0, 0, 1, 0.72, '#7DB0DD', '#D7E5EC')
    for i in range(14):
        x = a.r.uniform(0, 0.95)
        hh = a.r.uniform(0.12, 0.32)
        a.rect(x, 0.72 - hh, x + a.r.uniform(0.03, 0.07), 0.72, mix('#9FB4C4', '#D7E5EC', a.r.uniform(0, 0.5)))
    a.grad(0, 0.72, 1, 1, '#BDB8AD', '#9C978C')
    a.tree(0.04, 0.78, 0.07)
    a.tree(0.96, 0.79, 0.08)
    a.soft_poly([(0.12, 0.74), (0.88, 0.74), (0.95, 0.86), (0.05, 0.86)], '#3a3833', 0.35, 0.01)
    # glass box
    a.grad(0.1, 0.3, 0.9, 0.56, '#4C5D68', '#2C363D')
    for i in range(41):
        x = 0.1 + i * 0.02
        a.line([(x, 0.3), (x, 0.56)], '#6E828E', 0.0012)
    a.line([(0.1, 0.43), (0.9, 0.43)], '#6E828E', 0.0012)
    a.soft_poly([(0.1, 0.3), (0.4, 0.3), (0.2, 0.56), (0.1, 0.56)], '#C6DCEA', 0.25, 0.01)
    red, red2 = '#D9271F', '#A51A15'
    a.rect(0.08, 0.235, 0.92, 0.3, red)
    a.rect(0.08, 0.285, 0.92, 0.3, red2)
    a.rect(0.08, 0.56, 0.92, 0.61, red)
    a.rect(0.08, 0.6, 0.92, 0.61, red2)
    for x in (0.1, 0.86):
        a.rect(x, 0.235, x + 0.04, 0.78, red)
        a.rect(x + 0.03, 0.235, x + 0.04, 0.78, red2)
    a.people(0.8, [0.22, 0.25, 0.33, 0.41, 0.52, 0.55, 0.63, 0.71, 0.77], 0.045)
    a.noise(0, 0, 1, 1, 4)
    return a


def sesc():
    a = Art(*T, seed=4)
    a.grad(0, 0, 1, 1, '#83B4DD', '#E1EAEC')
    conc, conc2 = '#A9A49B', '#88837A'

    def holes(x0, x1, y0, y1, n):
        for i in range(n):
            cx = a.r.uniform(x0 + 0.04, x1 - 0.04)
            cy = y0 + (i + 0.5) * (y1 - y0) / n + a.r.uniform(-0.01, 0.01)
            pts = []
            k = a.r.randint(6, 9)
            for j in range(k):
                t = 2 * math.pi * j / k
                rr = a.r.uniform(0.6, 1.0)
                pts.append((cx + math.cos(t) * 0.07 * rr, cy + math.sin(t) * 0.025 * rr))
            a.poly(pts, '#C93A2B')

            def lattice(d, pts=pts):
                for gx in range(0, a.W, 10):
                    d.line([(gx, 0), (gx + 600, a.H)], fill=(110, 24, 18, 200), width=3)
                    d.line([(gx, 0), (gx - 600, a.H)], fill=(110, 24, 18, 200), width=3)
            a.masked(pts, lattice)

    a.rect(0.06, 0.14, 0.44, 1, conc)
    a.rect(0.38, 0.14, 0.44, 1, conc2)
    a.noise(0.06, 0.14, 0.44, 1, 9, 2)
    holes(0.06, 0.38, 0.17, 0.95, 9)
    a.rect(0.62, 0.05, 0.9, 1, conc)
    a.rect(0.85, 0.05, 0.9, 1, conc2)
    a.noise(0.62, 0.05, 0.9, 1, 9, 2)
    holes(0.62, 0.86, 0.08, 0.95, 11)
    for y0, y1 in ((0.3, 0.42), (0.52, 0.4), (0.62, 0.72), (0.8, 0.7)):
        a.poly([(0.44, y0), (0.62, y1), (0.62, y1 + 0.03), (0.44, y0 + 0.03)], '#9C978E')
        a.poly([(0.44, y0 + 0.03), (0.62, y1 + 0.03), (0.62, y1 + 0.036), (0.44, y0 + 0.036)], '#6E6A63')
    return a


def brasilia():
    a = Art(*S, seed=5)
    a.grad(0, 0, 1, 0.8, '#2867BE', '#A4CBEA')
    a.grad(0, 0.78, 1, 0.86, '#E0DDD5', '#C9C5BB')
    cx = 0.5

    def rib(theta, back=False):
        pts_l, pts_r = [], []
        for i in range(41):
            t = i / 40
            y = 0.79 - 0.62 * t
            r = 0.3 * (1 - 1.45 * t + 1.6 * t * t)
            x = cx + r * math.sin(theta)
            wd = (0.022 - 0.012 * t) * (0.5 + 0.5 * abs(math.cos(theta)))
            pts_l.append((x - wd, y))
            pts_r.append((x + wd, y))
        return pts_l + pts_r[::-1]

    n = 16
    thetas = [2 * math.pi * i / n + 0.1 for i in range(n)]
    hull = []
    for i in range(41):
        t = i / 40
        r = 0.3 * (1 - 1.45 * t + 1.6 * t * t)
        hull.append((cx - r, 0.79 - 0.62 * t))
    for i in range(40, -1, -1):
        t = i / 40
        r = 0.3 * (1 - 1.45 * t + 1.6 * t * t)
        hull.append((cx + r, 0.79 - 0.62 * t))
    for th in thetas:
        if math.cos(th) < 0:
            a.poly(rib(th), '#C5CBD3')
    a.poly(hull, '#4F86C6', a=0.55)
    a.soft_poly(hull, '#BFE0FF', 0.15, 0.02)
    for th in sorted(thetas, key=lambda t: math.cos(t)):
        if math.cos(th) >= 0:
            c = mix('#F7F6F2', '#C9CCD3', max(0, -math.sin(th)) * 0.7)
            a.poly(rib(th), c)
    a.rect(0, 0.84, 1, 1, '#6F8EA8')
    a.reflect(0.84, 1.0, '#47698A', a=0.4)
    a.people(0.84, [0.12, 0.15, 0.82], 0.04)
    a.noise(0, 0, 1, 1, 4)
    return a


def torres():
    a = Art(*P, seed=6)
    a.grad(0, 0, 1, 0.6, '#A2B9CB', '#E4E6E2')
    a.poly([(0, 0.32), (0.2, 0.22), (0.45, 0.28), (0.7, 0.16), (1, 0.26), (1, 0.6), (0, 0.6)], '#5D7B55')
    a.poly([(0, 0.4), (0.3, 0.33), (0.6, 0.38), (1, 0.33), (1, 0.6), (0, 0.6)], '#3F5D3A')

    def tower(xc, ytop, wmax, shade):
        floors = 30
        fh = (0.98 - ytop) / floors
        for i in range(floors):
            y = 0.98 - (i + 1) * fh
            t = i / floors
            w = wmax * (1 - 0.55 * t ** 1.6)
            step = (i // 3) * 0.004
            x0, x1 = xc - w / 2 + step, xc + w / 2
            a.rect(x0, y, x1, y + fh, mix('#A9492A', '#D9C4B5', shade))
            a.rect(x0, y + fh * 0.55, x1, y + fh * 0.85, mix('#5A2618', '#D9C4B5', shade))
            a.rect(x0, y, x1, y + fh * 0.12, mix('#C6683F', '#E6D6C8', shade))
            a.rect(x1 - w * 0.25, y, x1, y + fh, mix('#86361D', '#D9C4B5', shade), a=0.5)
    tower(0.3, 0.2, 0.42, 0.35)
    tower(0.7, 0.12, 0.5, 0.0)
    for x in (0.05, 0.18, 0.86, 0.98):
        a.tree(x, 1.0, 0.09, '#2F4A2C', '#47663B')
    a.noise(0, 0, 1, 1, 5)
    return a


def hawa():
    a = Art(*P, seed=7)
    a.grad(0, 0, 1, 1, '#5C99D6', '#C4DCEF')
    widths = [1.04, 0.92, 0.8, 0.64, 0.46, 0.3]
    lh = 0.125
    for k, w in enumerate(widths):
        y = 1 - (k + 1) * lh
        x0 = 0.5 - w / 2
        a.rect(x0, y, x0 + w, y + lh, '#DD8D6C')
        u = 0.064
        n = int(w / u)
        sx = 0.5 - n * u / 2
        for i in range(n):
            x = sx + i * u
            a.rect(x + 0.006, y + 0.035, x + u - 0.006, y + lh - 0.008, '#EBA17F')
            a.rect(x + u - 0.016, y + 0.035, x + u - 0.006, y + lh - 0.008, '#C77555')
            a.poly(arch_pts(x + 0.02, x + u - 0.02, y + lh - 0.02, y + 0.06), '#5B2721')
            a.ell(x + 0.004, y + 0.006, x + u - 0.004, y + 0.05, '#F2B596')
            a.ell(x + u * 0.45, y - 0.002, x + u * 0.55, y + 0.01, '#F2B596')
            a.line([(x + 0.006, y + lh - 0.008), (x + u - 0.006, y + lh - 0.008)], '#F8E6D8', 0.003)
            a.line([(x + 0.006, y + 0.035), (x + u - 0.006, y + 0.035)], '#F8E6D8', 0.002)
    a.noise(0, 0, 1, 1, 5)
    return a


def iim():
    a = Art(*L, seed=8)
    a.grad(0, 0, 1, 0.1, '#BCD3E3', '#E6E3D8')
    a.rect(0, 0.08, 1, 0.92, '#A9553A')
    for i in range(160):
        y = 0.08 + i * 0.0053
        a.line([(0, y), (1, y)], '#7C3B27', 0.0008, a=0.35)
    a.noise(0, 0.08, 1, 0.92, 8)
    for cx in (0.3, 0.74):
        rx, ry = 0.17, 0.17 * a.ar
        a.ell(cx - rx, 0.47 - ry, cx + rx, 0.47 + ry, '#D07C5A')
        a.ell(cx - rx + 0.03, 0.47 - ry - 0.02, cx + rx + 0.012, 0.47 + ry - 0.06, '#2C140E')
        a.glow(cx - 0.02, 0.5, 0.06, 0.08, '#FFD3A6', 0.12, 0.03)
        a.rect(cx - rx - 0.01, 0.6, cx + rx + 0.01, 0.65, '#BDB7AA')
        a.rect(cx - rx - 0.01, 0.64, cx + rx + 0.01, 0.65, '#8D877C')
    a.soft_poly([(0, 0.08), (0.18, 0.08), (0.0, 0.5)], '#FFE2C2', 0.18, 0.04)
    a.grad(0, 0.92, 1, 1, '#7F6C56', '#5E4F3F')
    a.people(0.92, [0.52], 0.08, '#1E1410')
    return a


def chandigarh():
    a = Art(*W, seed=9)
    a.grad(0, 0, 1, 0.7, '#C5D2D6', '#EFE6D6')
    a.grad(0, 0.68, 1, 0.76, '#A49C7C', '#8C8566')
    # pyramid + hyperboloid
    a.poly([(0.3, 0.36), (0.38, 0.2), (0.45, 0.36)], '#A7A49B')
    a.poly([(0.38, 0.2), (0.45, 0.36), (0.41, 0.36)], '#8B887F')
    hy = []
    for i in range(21):
        t = i / 20
        y = 0.36 - 0.27 * t
        r = 0.07 * (1 - 0.9 * t + 0.95 * t * t)
        hy.append((0.66 - r, y))
    for i in range(20, -1, -1):
        t = i / 20
        y = 0.36 - 0.27 * t
        r = 0.07 * (1 - 0.9 * t + 0.95 * t * t)
        hy.append((0.66 + r, y))
    a.poly(hy, '#B4B1A8')
    a.grad(0.66, 0.08, 0.74, 0.36, '#9E9B92', '#86837A', horiz=True)
    a.poly([(0.6, 0.09), (0.72, 0.09), (0.71, 0.11), (0.61, 0.11)], '#8B887F')
    a.rect(0.12, 0.34, 0.88, 0.7, '#A4A198')
    for i in range(61):
        x = 0.12 + i * 0.0127
        a.line([(x, 0.34), (x, 0.7)], '#6E6B63', 0.0018)
    for j in range(7):
        a.line([(0.12, 0.34 + j * 0.05), (0.88, 0.34 + j * 0.05)], '#6E6B63', 0.0018)
    # portico with scoop roof
    top = [(0.22 + i * 0.03, 0.25 + 0.06 * math.sin(math.pi * i / 20)) for i in range(21)]
    a.poly(top + [(0.82, 0.31), (0.82, 0.335), (0.22, 0.335), (0.22, 0.31)], '#B9B6AD')
    a.poly(top + [(0.82, 0.27), (0.22, 0.27)][::-1], '#CBC8BF')
    for i in range(9):
        x = 0.24 + i * 0.07
        a.rect(x, 0.335, x + 0.012, 0.7, '#BDBAB1')
        a.rect(x + 0.008, 0.335, x + 0.012, 0.7, '#8E8B83')
    a.soft_poly([(0.22, 0.335), (0.82, 0.335), (0.82, 0.4), (0.22, 0.4)], '#3a3833', 0.35, 0.01)
    # enamel door
    a.rect(0.47, 0.5, 0.53, 0.7, '#E6A51E')
    a.rect(0.47, 0.5, 0.5, 0.56, '#C9372C')
    a.rect(0.5, 0.56, 0.53, 0.62, '#2D5DA8')
    a.rect(0.47, 0.62, 0.5, 0.66, '#2E7D4F')
    a.rect(0, 0.76, 1, 1, '#7E8C8E')
    a.reflect(0.76, 1.0, '#5E6E72', a=0.35)
    return a


def chand_baori():
    a = Art(*S, seed=10)
    lit, sh, deep = '#CE9F67', '#8F6440', '#5E4128'
    a.rect(0, 0, 1, 1, deep)
    rows = 13
    rh = 0.063
    for r in range(rows):
        y0 = 0.04 + r * rh
        y1 = y0 + rh
        off = 0.05 if r % 2 else 0
        x = -0.1 + off
        while x < 1.05:
            a.poly([(x, y1), (x + 0.05, y0), (x + 0.05, y1)], lit)
            a.poly([(x + 0.05, y0), (x + 0.1, y1), (x + 0.05, y1)], sh)
            for s in range(1, 7):
                yy = y0 + s * rh / 7
                xa = x + 0.05 * (1 - s / 7)
                a.line([(xa, yy), (x + 0.05, yy)], '#A5764A', 0.0012)
                a.line([(x + 0.05, yy), (x + 0.05 + 0.05 * s / 7, yy)], '#6C4A2E', 0.0012)
            x += 0.1
        a.rect(0, y1 - 0.004, 1, y1, '#E2B884')
    a.grad(0, 0.86, 1, 1, '#3F6D53', '#24432F')
    a.reflect(0.86, 1.0, '#2C513C', a=0.55)
    a.rect(0, 0, 1, 0.04, '#E6C898')
    a.noise(0, 0, 1, 1, 7)
    a.soft_poly([(0, 0), (1, 0), (1, 0.3), (0, 0.55)], '#FFE2B8', 0.18, 0.05)
    return a


def jkk():
    a = Art(*S, seed=11)
    a.grad(0, 0, 1, 0.3, '#7DAEDA', '#DDE7EB')
    a.rect(0.06, 0.12, 0.34, 0.3, '#B95C40')
    a.rect(0.06, 0.12, 0.34, 0.135, '#E7D0AE')
    a.rect(0, 0.26, 1, 1, '#B4533A')
    a.grad(0, 0.26, 1, 1, '#BF5D42', '#9E4530', horiz=True)
    for y in (0.26, 0.34, 0.62, 0.9):
        a.rect(0, y, 1, y + 0.014, '#E5CCA8')
    a.noise(0, 0.26, 1, 1, 7)
    cx, cy, r = 0.6, 0.6, 0.2
    a.ell(cx - r, cy - r, cx + r, cy + r, '#F2EADC')
    r2 = r - 0.025
    a.ell(cx - r2, cy - r2, cx + r2, cy + r2, '#231F1D')
    for i in range(8):
        t = 2 * math.pi * i / 8
        x, y = cx + math.cos(t) * 0.11, cy + math.sin(t) * 0.11
        a.ell(x - 0.012, y - 0.012, x + 0.012, y + 0.012, '#E9C46A' if i % 2 else '#F2EADC')
    a.rect(cx - 0.03, cy - 0.03, cx + 0.03, cy + 0.03, '#F2EADC')
    a.rect(0.1, 0.62, 0.28, 1, '#3A1A12')
    a.soft_poly([(0.1, 0.62), (0.28, 0.62), (0.28, 0.7), (0.1, 0.66)], '#000000', 0.4, 0.01)
    a.people(0.99, [0.2], 0.12, '#1A0D09')
    return a


def sangath():
    a = Art(*L, seed=12)
    a.grad(0, 0, 1, 0.5, '#9CC0DE', '#F0E8D5')
    for i in range(10):
        a.tree(a.r.uniform(0, 1), 0.5, a.r.uniform(0.07, 0.12), '#3E5A30', '#577443')
    a.grad(0, 0.48, 1, 1, '#86A251', '#5F7D37')

    def vault(x0, x1, ybase, depth):
        rx = (x1 - x0) / 2
        ry = rx * a.ar * 0.9
        top = []
        for i in range(25):
            t = math.pi - math.pi * i / 24
            top.append((x0 + rx + rx * math.cos(t), ybase - ry * math.sin(t)))
        back = [(x + depth, y - depth * 0.6) for x, y in top]
        a.poly(top + back[::-1], '#F2F0EA')

        def speck(d):
            rr = a.r
            for _ in range(900):
                px, py = rr.uniform(x0, x1 + depth) * a.W, rr.uniform(ybase - ry - depth, ybase) * a.H
                s = rr.uniform(3, 9)
                col = rr.choice([(255, 255, 255, 255), (214, 218, 222, 255), (190, 205, 215, 255), (235, 232, 225, 255)])
                d.polygon([(px, py), (px + s, py + rr.uniform(-2, 2)), (px + s * 0.6, py + s)], fill=col)
        a.masked(top + back[::-1], speck)
        a.poly(top + [(x1 - 0.012, ybase)] + [(x0 + rx + (rx - 0.012) * math.cos(math.pi - math.pi * i / 24), ybase - (ry - 0.02) * math.sin(math.pi - math.pi * i / 24)) for i in range(24, -1, -1)], '#E4E1D8')
        inner = [(x0 + rx + (rx - 0.012) * math.cos(math.pi - math.pi * i / 24), ybase - (ry - 0.02) * math.sin(math.pi - math.pi * i / 24)) for i in range(25)]
        a.poly(inner, '#3A3631')
        a.rect(x0 + rx * 0.6, ybase - ry * 0.5, x0 + rx * 1.4, ybase, '#C7B79A', a=0.6)
    vault(0.08, 0.38, 0.62, 0.12)
    vault(0.42, 0.66, 0.58, 0.1)
    vault(0.68, 0.98, 0.66, 0.12)
    for i in range(6):
        y = 0.72 + i * 0.045
        a.rect(0.0, y, 1, y + 0.02, '#BDB6A6')
        a.rect(0.44, y - 0.004, 0.52, y + 0.024, '#6FA6C4')
    a.noise(0, 0, 1, 1, 4)
    return a


def baker():
    a = Art(*P, seed=13)
    a.rect(0, 0, 1, 0.82, '#AE5A3A')
    bw, bh = 0.072, 0.034
    for row in range(26):
        y = row * bh
        off = (row % 2) * bw / 2
        for col in range(-1, 16):
            x = col * bw + off
            hole = (row % 4 in (1, 2)) and (col % 2 == (row // 4) % 2)
            if hole and y < 0.78:
                c = a.r.choice(['#21140F', '#21140F', '#5D7B3E', '#7C9A4C', '#E8E2C8'])
                a.rect(x + 0.004, y + 0.003, x + bw - 0.004, y + bh - 0.003, c)
            else:
                a.rect(x + 0.002, y + 0.002, x + bw - 0.002, y + bh - 0.002, jit('#B25E3C', 14, a.r))
    a.soft_poly([(0, 0), (0.7, 0), (0.0, 0.8)], '#FFD9A8', 0.18, 0.05)
    a.grad(0, 0.82, 1, 1, '#8F5034', '#6E3A25')
    for i in range(60):
        x = a.r.uniform(0, 1)
        y = a.r.uniform(0.84, 0.99)
        a.soft_poly([(x, y), (x + 0.04, y), (x + 0.03, y + 0.01), (x - 0.01, y + 0.01)], '#FFE0B0', 0.4, 0.002)
    a.noise(0, 0, 1, 1, 7)
    return a


def church_light():
    a = Art(*P, seed=14)
    a.grad(0, 0, 1, 1, '#1A1816', '#0D0C0B')
    a.poly([(0, 0), (0.18, 0.06), (0.18, 0.86), (0, 1)], '#2A2622')
    for i in range(7):
        for j in range(10):
            a.ell(0.25 + i * 0.09, 0.08 + j * 0.075, 0.256 + i * 0.09, 0.0848 + j * 0.075, '#2A2724')
    a.glow(0.5, 0.42, 0.1, 0.3, '#FFF1D0', 0.35, 0.06)
    a.glow(0.5, 0.42, 0.33, 0.04, '#FFF1D0', 0.35, 0.05)
    a.soft_poly([(0.485, 0.0), (0.515, 0.0), (0.515, 0.86), (0.485, 0.86)], '#FFF5DE', 0.9, 0.006)
    a.soft_poly([(0.18, 0.36), (1.0, 0.36), (1.0, 0.39), (0.18, 0.39)], '#FFF5DE', 0.9, 0.006)
    a.rect(0.493, 0.0, 0.507, 0.86, '#FFFDF6')
    a.rect(0.18, 0.368, 1.0, 0.382, '#FFFDF6')
    a.grad(0, 0.86, 1, 1, '#221A14', '#0A0807')
    for i in range(9):
        x = -0.4 + i * 0.22
        a.line([(0.5, 0.86), (x, 1.0)], '#3A2C22', 0.0015)
    for k in range(4):
        y = 0.89 + k * 0.03
        a.rect(0.12 - k * 0.04, y, 0.42 - k * 0.01, y + 0.012, '#0C0A09')
        a.rect(0.58 + k * 0.01, y, 0.88 + k * 0.04, y + 0.012, '#0C0A09')
    a.soft_poly([(0.485, 0.86), (0.515, 0.86), (0.56, 1), (0.44, 1)], '#FFE9C0', 0.25, 0.01)
    return a


def nakagin():
    a = Art(*P, seed=15)
    a.grad(0, 0, 1, 1, '#B5C5D0', '#E7EBEB')
    a.rect(0, 0.3, 0.12, 1, '#7F858A')
    a.rect(0.9, 0.42, 1, 1, '#6E7479')
    for cx in (0.36, 0.66):
        a.rect(cx - 0.05, 0.06, cx + 0.05, 1, '#9A9C9A')
    cw, ch = 0.13, 0.074
    for row in range(13):
        y = 0.07 + row * ch
        for cx, side in ((0.36, -1), (0.36, 1), (0.66, -1), (0.66, 1)):
            if a.r.random() < 0.12:
                continue
            jitx = a.r.uniform(-0.012, 0.012)
            x0 = cx + (0.04 if side > 0 else -0.04 - cw) + jitx
            y0 = y + a.r.uniform(-0.01, 0.01)
            a.rect(x0, y0, x0 + cw, y0 + ch * 0.92, '#E9E7E1')
            a.poly([(x0 + cw, y0), (x0 + cw + 0.02, y0 - 0.012), (x0 + cw + 0.02, y0 + ch * 0.92 - 0.012), (x0 + cw, y0 + ch * 0.92)], '#B8B6B0')
            a.poly([(x0, y0), (x0 + 0.02, y0 - 0.012), (x0 + cw + 0.02, y0 - 0.012), (x0 + cw, y0)], '#F6F5F2')
            r = ch * 0.3
            mx, my = x0 + cw / 2, y0 + ch * 0.46
            a.ell(mx - r / a.ar, my - r, mx + r / a.ar, my + r, '#C9C7C1')
            r2 = r * 0.82
            a.ell(mx - r2 / a.ar, my - r2, mx + r2 / a.ar, my + r2, '#2C3337')
            a.ell(mx - r2 * 0.6 / a.ar, my - r2 * 0.7, mx, my - r2 * 0.1, '#5C6E78', a=0.6)
    a.noise(0, 0, 1, 1, 4)
    return a


def moriyama():
    a = Art(*L, seed=16)
    a.grad(0, 0, 1, 0.22, '#CFDCE4', '#E9ECEB')
    a.rect(0, 0.0, 0.2, 0.3, '#B9B5AC')
    a.rect(0.78, 0.0, 1, 0.26, '#A8A69F')
    a.grad(0, 0.22, 1, 1, '#E1DDD3', '#CFCABE')
    a.noise(0, 0.22, 1, 1, 9)

    def box(x, y, w, h, dx=0.05, dy=0.05, win=None):
        a.poly([(x, y), (x + dx, y - dy), (x + w + dx, y - dy), (x + w, y)], '#FFFFFF')
        a.poly([(x + w, y), (x + w + dx, y - dy), (x + w + dx, y - dy + h), (x + w, y + h)], '#D2D0CA')
        a.rect(x, y, x + w, y + h, '#F3F2EE')
        a.soft_poly([(x, y + h), (x + w, y + h), (x + w + 0.06, y + h + 0.03), (x + 0.06, y + h + 0.03)], '#7A7464', 0.35, 0.006)
        if win:
            wx0, wy0, wx1, wy1 = win
            a.rect(x + w * wx0, y + h * wy0, x + w * wx1, y + h * wy1, '#353C41')
            a.rect(x + w * wx0, y + h * wy0, x + w * (wx0 + (wx1 - wx0) * 0.5), y + h * wy1, '#E9E1CF', a=0.5)
    box(0.05, 0.36, 0.16, 0.2, win=(0.15, 0.2, 0.85, 0.8))
    box(0.3, 0.3, 0.11, 0.36, win=(0.2, 0.55, 0.8, 0.9))
    box(0.52, 0.4, 0.2, 0.14, win=(0.1, 0.2, 0.5, 0.8))
    box(0.8, 0.34, 0.12, 0.28)
    box(0.18, 0.66, 0.22, 0.16, win=(0.55, 0.15, 0.95, 0.85))
    box(0.56, 0.68, 0.1, 0.24, win=(0.2, 0.3, 0.8, 0.95))
    box(0.76, 0.72, 0.18, 0.12)
    for x, y in ((0.26, 0.62), (0.47, 0.64), (0.73, 0.6), (0.44, 0.9), (0.08, 0.9)):
        for _ in range(6):
            dx, dy = a.r.uniform(-0.02, 0.02), a.r.uniform(-0.03, 0.0)
            a.ell(x + dx - 0.012, y + dy - 0.016, x + dx + 0.012, y + dy + 0.016, a.r.choice(['#4E6B39', '#6E8D49', '#3D5530']))
    return a


def teshima():
    a = Art(*L, seed=17)
    a.grad(0, 0, 1, 0.38, '#A6C9E2', '#ECF1F0')
    a.poly([(0, 0.36), (0.15, 0.3), (0.32, 0.35), (0.5, 0.33), (0.7, 0.36), (0, 0.4)], '#7E97A0')
    a.grad(0, 0.36, 1, 0.45, '#7FA5BF', '#A9C3D2')
    colors = ['#86A653', '#759948', '#93B25D', '#6C8E40', '#9BB866', '#7EA04C']
    for i in range(9):
        y = 0.44 + i * 0.065
        pts = [(x / 20, y + 0.012 * math.sin(x / 3 + i)) for x in range(21)] + [(1, 1), (0, 1)]
        a.poly(pts, colors[i % len(colors)])
        a.line([(x / 20, y + 0.012 * math.sin(x / 3 + i)) for x in range(21)], '#5C7A35', 0.0015, a=0.6)
    shell = ellipse_pts(0.5, 0.62, 0.33, 0.1, n=80, ar=1)
    shell = [(x, min(y, 0.64)) for x, y in shell]
    a.poly(shell, '#EFEFEC')
    a.grad(0.17, 0.52, 0.83, 0.64, '#FBFBFA', '#D6D7D3')
    a.poly([(0.17, 0.52), (0.17, 0.62)] + [(x, y) for x, y in ellipse_pts(0.5, 0.62, 0.33, 0.1, n=80) if y < 0.62] , '#EFEFEC', a=0)
    # mask outside shell by repainting terraces above shell top edge
    top = [p for p in ellipse_pts(0.5, 0.62, 0.33, 0.1, n=120) if p[1] <= 0.62]
    top.sort()
    a.poly([(0.17, 0.52)] + [(0.17, 0.62)] + [(0.17, 0.52)], '#EFEFEC', a=0)
    a.ell(0.42, 0.535, 0.52, 0.56, '#3E4A4F')
    a.ell(0.43, 0.538, 0.51, 0.553, '#9CB8C8')
    a.soft_poly([(0.17, 0.64), (0.83, 0.64), (0.8, 0.67), (0.2, 0.67)], '#3d4a2a', 0.3, 0.01)
    return a


def teshima_fix():
    # cleaner version: shell drawn as dome polygon, no stray rect
    a = Art(*L, seed=17)
    a.grad(0, 0, 1, 0.38, '#A6C9E2', '#ECF1F0')
    a.poly([(0, 0.36), (0.15, 0.3), (0.32, 0.35), (0.5, 0.33), (0.7, 0.36), (1, 0.34), (1, 0.4), (0, 0.4)], '#7E97A0')
    a.grad(0, 0.37, 1, 0.45, '#7FA5BF', '#A9C3D2')
    colors = ['#86A653', '#759948', '#93B25D', '#6C8E40', '#9BB866', '#7EA04C']
    for i in range(9):
        y = 0.44 + i * 0.065
        ln = [(x / 20, y + 0.012 * math.sin(x / 3 + i)) for x in range(21)]
        a.poly(ln + [(1, 1), (0, 1)], colors[i % len(colors)])
        a.line(ln, '#5C7A35', 0.0015, a=0.6)
    dome = []
    for i in range(61):
        t = math.pi - math.pi * i / 60
        dome.append((0.5 + 0.34 * math.cos(t), 0.64 - 0.13 * math.sin(t) ** 0.8))
    a.soft_poly(dome + [(0.86, 0.66), (0.14, 0.66)], '#3d4a2a', 0.35, 0.01)
    a.poly(dome, '#EFEFEC')

    def shade(d):
        for i in range(60):
            t = i / 60
            col = mix('#FDFDFC', '#CDD0CB', t)
            d.rectangle([0, (0.51 + 0.13 * t) * a.H, a.W, (0.51 + 0.13 * (t + 1 / 60)) * a.H + 2], fill=col + (255,))
    a.masked(dome, shade)
    a.ell(0.43, 0.535, 0.53, 0.556, '#2F3A40')
    a.ell(0.445, 0.538, 0.515, 0.55, '#A7C3D2')
    a.ell(0.7, 0.618, 0.76, 0.632, '#3A4448')
    a.people(0.66, [0.84, 0.86], 0.035)
    a.noise(0, 0, 1, 1, 4)
    return a


def katsura():
    a = Art(*L, seed=18)
    a.grad(0, 0, 1, 0.4, '#C9D6D3', '#E7E8E0')
    for i in range(14):
        a.tree(a.r.uniform(-0.05, 1.05), 0.42, a.r.uniform(0.08, 0.14), '#2F4529', '#47633A')
    a.grad(0, 0.4, 1, 1, '#5D7342', '#46582F')
    a.noise(0, 0.4, 1, 1, 10, 3)
    a.poly([(0.04, 0.3), (0.2, 0.14), (0.8, 0.14), (0.96, 0.3)], '#57524A')
    a.poly([(0.02, 0.3), (0.98, 0.3), (0.96, 0.33), (0.04, 0.33)], '#3B362F')
    for i in range(40):
        x = 0.1 + i * 0.02
        a.line([(x, 0.15), (x - 0.04 + 0.08 * (i / 40), 0.3)], '#6A655B', 0.0012)
    a.rect(0.08, 0.33, 0.92, 0.58, '#EDE8DC')
    a.soft_poly([(0.08, 0.33), (0.92, 0.33), (0.92, 0.38), (0.08, 0.38)], '#2a2520', 0.3, 0.008)
    for i in range(13):
        x = 0.08 + i * 0.07
        a.rect(x, 0.33, x + 0.008, 0.6, '#3A2E25')
        for j in range(1, 6):
            a.line([(x, 0.33 + j * 0.045), (x + 0.07, 0.33 + j * 0.045)], '#8F8576', 0.0012)
        for j in range(1, 3):
            a.line([(x + j * 0.0233, 0.33), (x + j * 0.0233, 0.58)], '#8F8576', 0.0012)
    a.rect(0.06, 0.58, 0.94, 0.61, '#8B6A48')
    for i in range(14):
        x = 0.07 + i * 0.066
        a.rect(x, 0.61, x + 0.01, 0.68, '#3D3026')
    a.soft_poly([(0.06, 0.61), (0.94, 0.61), (0.98, 0.7), (0.02, 0.7)], '#1f2a14', 0.45, 0.01)
    for x, y, r in ((0.3, 0.75, 0.04), (0.42, 0.8, 0.035), (0.53, 0.86, 0.045), (0.64, 0.93, 0.04)):
        a.ell(x - r, y - r * 0.4, x + r, y + r * 0.4, '#9C998F')
        a.ell(x - r, y - r * 0.4, x + r * 0.7, y + r * 0.1, '#B6B3A9')
    return a


def yoyogi():
    a = Art(*W, seed=19)
    a.grad(0, 0, 1, 0.68, '#93BADC', '#E8EDEE')
    a.grad(0, 0.68, 1, 1, '#BDB6A8', '#A39C8E')
    m1, m2 = (0.33, 0.12), (0.66, 0.18)
    ridge = [(m1[0] + (m2[0] - m1[0]) * t, m1[1] + (m2[1] - m1[1]) * t + 0.06 * math.sin(math.pi * t)) for t in [i / 20 for i in range(21)]]
    left_edge = [(0.33 - 0.28 * t, 0.12 + 0.52 * t ** 1.5) for t in [i / 20 for i in range(21)]]
    right_edge = [(0.66 + 0.3 * t, 0.18 + 0.46 * t ** 1.5) for t in [i / 20 for i in range(21)]]
    roof = left_edge[::-1] + ridge + right_edge + [(0.94, 0.66), (0.06, 0.66)]
    a.poly(roof, '#8C9395')

    def bands(d):
        for i in range(70):
            t = i / 69
            rx, ry = ridge[min(20, int(t * 20))]
            ex = 0.03 + 0.95 * t
            col = (160, 168, 171, 255) if i % 2 else (124, 132, 135, 255)
            d.line([(rx * a.W, ry * a.H), (ex * a.W, 0.68 * a.H)], fill=col, width=7)
    a.masked(roof, bands)
    a.soft_poly(roof[:21] + [(0.3, 0.66), (0.06, 0.66)], '#FFFFFF', 0.18, 0.02)
    a.line(ridge, '#4C5254', 0.006)
    for m in (m1, m2):
        a.rect(m[0] - 0.006, m[1] - 0.06, m[0] + 0.006, m[1] + 0.02, '#3B3F41')
    a.rect(0.05, 0.6, 0.95, 0.72, '#CFC9BB')
    a.rect(0.05, 0.63, 0.95, 0.67, '#3C4448')
    a.rect(0.05, 0.6, 0.95, 0.61, '#E3DED2')
    a.people(0.76, [0.2, 0.24, 0.5, 0.71], 0.04)
    a.noise(0, 0, 1, 1, 4)
    return a


def barbican():
    a = Art(*P, seed=20)
    a.grad(0, 0, 1, 0.8, '#B3C0C9', '#E3E5E2')
    conc = '#9A978F'
    a.rect(0.32, 0.04, 0.66, 0.6, conc)
    a.rect(0.56, 0.04, 0.66, 0.6, '#7F7C75')
    for i in range(30):
        y = 0.05 + i * 0.0185
        a.rect(0.32, y, 0.66, y + 0.006, '#BDB9B0')
        for x0, d in ((0.32, -1), (0.66, 1)):
            a.poly([(x0, y), (x0 + d * 0.035, y + 0.004), (x0 + d * 0.035, y + 0.01), (x0, y + 0.006)], '#B2AEA5')
        a.rect(0.335, y + 0.006, 0.56, y + 0.0185, '#5B5853', a=0.5)
    a.noise(0.28, 0.04, 0.7, 0.6, 9, 2)
    a.rect(0, 0.56, 1, 0.8, '#A29E95')
    for i in range(8):
        x = 0.02 + i * 0.125
        a.poly(arch_pts(x, x + 0.1, 0.8, 0.68), '#2E2C29')
    a.rect(0, 0.56, 1, 0.6, '#B8B4AA')
    for i in range(12):
        x = a.r.uniform(0, 1)
        a.ell(x - 0.03, 0.54, x + 0.03, 0.57, a.r.choice(['#55703F', '#6E8C4E', '#8BA35E', '#B85F5A']))
    a.noise(0, 0.56, 1, 0.8, 9, 2)
    a.rect(0, 0.8, 1, 1, '#566A6E')
    a.reflect(0.8, 1.0, '#41575C', a=0.4)
    for x in (0.18, 0.42, 0.7):
        a.soft_line([(x, 0.9), (x, 0.82)], '#FFFFFF', 0.008, a=0.7, blur=0.006)
    return a


def unite():
    a = Art(*W, seed=21)
    a.grad(0, 0, 1, 0.8, '#8DB6DA', '#E5ECEE')
    a.grad(0, 0.8, 1, 1, '#7D9256', '#5E7240')
    a.tree(0.03, 0.82, 0.1)
    a.tree(0.97, 0.84, 0.11)
    a.rect(0.08, 0.2, 0.92, 0.66, '#A9A398')
    cols, rows = 21, 11
    cw, rh = 0.84 / cols, 0.44 / rows
    palette = ['#C8352B', '#E7B826', '#2E5DA8', '#4E8A4A', '#E9E4D8', '#E9E4D8', '#8C8578']
    for r in range(rows):
        for c in range(cols):
            x, y = 0.08 + c * cw, 0.21 + r * rh
            a.rect(x + 0.002, y, x + cw - 0.002, y + rh * 0.8, '#3F3B36')
            a.rect(x + 0.002, y, x + 0.008, y + rh * 0.8, a.r.choice(palette))
            a.rect(x + 0.002, y + rh * 0.55, x + cw - 0.002, y + rh * 0.8, '#B8B2A6')
    a.noise(0.08, 0.2, 0.92, 0.66, 8, 2)
    for i in range(9):
        x = 0.12 + i * 0.095
        a.poly([(x, 0.66), (x + 0.04, 0.66), (x + 0.03, 0.8), (x + 0.012, 0.8)], '#8E897F')
        a.poly([(x + 0.03, 0.66), (x + 0.04, 0.66), (x + 0.03, 0.8)], '#6E6A62')
    a.soft_poly([(0.08, 0.66), (0.92, 0.66), (0.92, 0.72), (0.08, 0.72)], '#2a2723', 0.4, 0.01)
    a.poly([(0.76, 0.2), (0.78, 0.12), (0.84, 0.12), (0.82, 0.2)], '#B5AFA4')
    a.rect(0.2, 0.15, 0.32, 0.2, '#B5AFA4')
    a.poly(arch_pts(0.5, 0.58, 0.2, 0.16), '#C2BCB1')
    return a


def ronchamp():
    a = Art(*L, seed=22)
    a.grad(0, 0, 1, 0.7, '#6AA0D2', '#DCE7EE')
    a.clouds(6, 0.08, 0.3, 0.5)
    hill = [(x / 20, 0.68 - 0.06 * math.sin(math.pi * x / 20)) for x in range(21)] + [(1, 1), (0, 1)]
    a.poly(hill, '#6F8E48')
    a.grad(0, 0.75, 1, 1, '#6F8E48', '#4E6A30')
    # tower
    a.rect(0.12, 0.18, 0.22, 0.66, '#EFEBE2')
    a.ell(0.12, 0.14, 0.22, 0.22, '#EFEBE2')
    a.rect(0.19, 0.18, 0.22, 0.66, '#D2CEC4')
    # south wall wedge
    a.poly([(0.22, 0.34), (0.86, 0.3), (0.8, 0.68), (0.22, 0.66)], '#F2EEE6')
    a.grad(0.22, 0.3, 0.86, 0.68, '#F7F4EE', '#DAD5CB', horiz=True)
    a.poly([(0.22, 0.34), (0.86, 0.3), (0.22, 0.3)], '#E8EEF3', a=0)
    for i in range(22):
        x = a.r.uniform(0.27, 0.76)
        y = a.r.uniform(0.4, 0.6)
        w = a.r.uniform(0.008, 0.03)
        h = a.r.uniform(0.02, 0.06)
        a.rect(x, y, x + w, y + h, '#3B3A40')
        a.rect(x, y, x + w * 0.3, y + h, a.r.choice(['#C8352B', '#E7B826', '#2E5DA8', '#E6E2D8']), a=0.8)
    roof_top = [(0.2 + 0.7 * t, 0.26 - 0.12 * t ** 3 + 0.04 * math.sin(math.pi * t)) for t in [i / 30 for i in range(31)]]
    roof_bot = [(0.2 + 0.68 * t, 0.33 - 0.06 * t ** 3 + 0.02 * math.sin(math.pi * t)) for t in [i / 30 for i in range(31)]]
    a.poly(roof_top + roof_bot[::-1], '#5C4B3E')
    a.poly(roof_top + [(x, y + 0.02) for x, y in roof_top][::-1], '#7A6655')
    a.line(roof_bot, '#FFFFFF', 0.003, a=0.7)
    a.people(0.74, [0.5, 0.53], 0.05)
    a.noise(0, 0, 1, 1, 4)
    return a


def vals():
    a = Art(*P, seed=23)
    a.rect(0, 0, 1, 1, '#4C524B')
    y = 0.08
    while y < 0.7:
        h = a.r.uniform(0.006, 0.016)
        a.rect(0, y, 1, y + h, jit('#5E655D', 10, a.r))
        y += h
    a.rect(0, 0, 1, 0.08, '#2A2E2A')
    for x in (0.18, 0.47, 0.81):
        a.soft_line([(x, 0.0), (x + 0.004, 0.08)], '#F2F7EE', 0.008, a=0.9, blur=0.004)
        a.soft_poly([(x - 0.01, 0.08), (x + 0.02, 0.08), (x + 0.07, 0.7), (x - 0.04, 0.7)], '#E9F2E2', 0.12, 0.03)
    a.rect(0.32, 0.18, 0.62, 0.7, '#3D423C')
    y = 0.18
    while y < 0.7:
        h = a.r.uniform(0.006, 0.014)
        a.rect(0.32, y, 0.62, y + h, jit('#474D46', 8, a.r))
        y += h
    a.rect(0.4, 0.42, 0.54, 0.7, '#1A1D1A')
    a.glow(0.47, 0.6, 0.05, 0.08, '#6FB5B8', 0.3, 0.03)
    a.grad(0, 0.7, 1, 1, '#2F7280', '#173E47')
    a.reflect(0.7, 1.0, '#1F5560', a=0.45)
    a.glow(0.5, 0.75, 0.5, 0.06, '#FFFFFF', 0.12, 0.06)
    a.noise(0, 0, 1, 1, 5)
    return a


def brion():
    a = Art(*S, seed=24)
    a.grad(0, 0, 1, 0.18, '#C4D4DD', '#E6E7E1')
    a.rect(0, 0.14, 1, 0.74, '#B9B3A7')
    for i in range(60):
        y = 0.14 + i * 0.01
        a.line([(0, y), (1, y)], '#9F998D', 0.001, a=0.5)
    for k in range(5):
        a.rect(0, 0.14 + k * 0.012, 1, 0.146 + k * 0.012, '#A49E92')
    a.noise(0, 0.14, 1, 0.74, 7, 2)
    for cx in (0.41, 0.59):
        r = 0.17
        a.ell(cx - r - 0.016, 0.44 - r - 0.016, cx + r + 0.016, 0.44 + r + 0.016, '#2C5C8A')
        a.ell(cx - r - 0.008, 0.44 - r - 0.008, cx + r + 0.008, 0.44 + r + 0.008, '#D1A93E')
    for cx in (0.41, 0.59):
        r = 0.17
        a.ell(cx - r, 0.44 - r, cx + r, 0.44 + r, '#6E8D4D')
    a.grad(0.24, 0.27, 0.76, 0.61, '#8EAA62', '#4B6A33')
    a.masked(ellipse_pts(0.41, 0.44, 0.17, 0.17) + ellipse_pts(0.59, 0.44, 0.17, 0.17), lambda d: None)
    # re-cut: paint wall outside circles over gradient box
    def wallmask():
        pass
    a.grad(0, 0.74, 1, 1, '#4A635D', '#2E433E')
    a.reflect(0.74, 1.0, '#3A534D', a=0.4)
    for _ in range(9):
        x = a.r.uniform(0.05, 0.95)
        y = a.r.uniform(0.8, 0.97)
        a.ell(x - 0.035, y - 0.012, x + 0.035, y + 0.012, '#5F8A44')
        a.ell(x - 0.006, y - 0.006, x + 0.006, y + 0.006, '#F1E6E9')
    return a


def brion_fix():
    a = Art(*S, seed=24)
    a.grad(0, 0, 1, 0.74, '#9DB86A', '#4B6A33')
    for _ in range(30):
        x = a.r.uniform(0, 1)
        y = a.r.uniform(0.2, 0.7)
        a.ell(x - 0.05, y - 0.05, x + 0.05, y + 0.05, a.r.choice(['#5D7E3F', '#749552', '#88A85F']))
    wall = [(0, 0.14), (1, 0.14), (1, 0.74), (0, 0.74)]
    circles = ellipse_pts(0.41, 0.44, 0.17, 0.17, n=90) + ellipse_pts(0.59, 0.44, 0.17, 0.17, n=90)

    def wall_paint(d):
        d.rectangle([0, 0.14 * a.H, a.W, 0.74 * a.H], fill=(185, 179, 167, 255))
        for i in range(60):
            y = (0.14 + i * 0.01) * a.H
            d.line([(0, y), (a.W, y)], fill=(159, 153, 141, 140), width=2)
        for k in (0.41, 0.59):
            r = 0.17 + 0.018
            d.ellipse([(k - r) * a.W, (0.44 - r) * a.H, (k + r) * a.W, (0.44 + r) * a.H], fill=(44, 92, 138, 255))
        for k in (0.41, 0.59):
            r = 0.17 + 0.009
            d.ellipse([(k - r) * a.W, (0.44 - r) * a.H, (k + r) * a.W, (0.44 + r) * a.H], fill=(209, 169, 62, 255))
        for k in (0.41, 0.59):
            r = 0.17
            d.ellipse([(k - r) * a.W, (0.44 - r) * a.H, (k + r) * a.W, (0.44 + r) * a.H], fill=(0, 0, 0, 0))
    L = a._layer()
    wall_paint(ImageDraw.Draw(L))
    a._comp(L)
    a.grad(0, 0, 1, 0.14, '#C4D4DD', '#E6E7E1')
    for k in range(4):
        a.rect(0.0, 0.14 + k * 0.014, 1, 0.148 + k * 0.014, '#A39D91')
    a.noise(0, 0.14, 1, 0.74, 6, 2)
    a.grad(0, 0.74, 1, 1, '#4A635D', '#2E433E')
    a.reflect(0.74, 1.0, '#3A534D', a=0.45)
    for _ in range(9):
        x = a.r.uniform(0.05, 0.95)
        y = a.r.uniform(0.8, 0.97)
        a.ell(x - 0.035, y - 0.012, x + 0.035, y + 0.012, '#5F8A44')
        a.ell(x - 0.006, y - 0.006, x + 0.006, y + 0.006, '#F1E6E9')
    return a
