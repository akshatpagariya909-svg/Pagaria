from lib import *
from b1 import P, T, L, W, S


def barcelona():
    a = Art(*W, seed=25)
    a.grad(0, 0, 1, 0.62, '#9AC0DD', '#E8EDEE')
    for i in range(12):
        a.tree(a.r.uniform(-0.05, 1.05), 0.62, a.r.uniform(0.07, 0.12), '#2E4728', '#43603A')
    a.rect(0, 0.62, 1, 0.72, '#E3DCCB')
    for i in range(30):
        a.line([(i * 0.035, 0.62), (i * 0.035, 0.72)], '#C9C0AC', 0.001)
    a.line([(0, 0.67), (1, 0.67)], '#C9C0AC', 0.001)
    # walls
    a.rect(0.1, 0.235, 0.3, 0.62, '#3D5C4D')

    def veins(x0, x1, c):
        def f(d):
            for _ in range(40):
                x = a.r.uniform(x0, x1) * a.W
                y = a.r.uniform(0.23, 0.62) * a.H
                pts = [(x, y)]
                for k in range(8):
                    x += a.r.uniform(-30, 30); y += a.r.uniform(10, 40)
                    pts.append((x, y))
                d.line(pts, fill=c, width=2)
        return f
    a.masked([(0.1, 0.235), (0.3, 0.235), (0.3, 0.62), (0.1, 0.62)], veins(0.1, 0.3, (140, 170, 150, 140)))
    a.rect(0.46, 0.235, 0.63, 0.62, '#D6AE77')
    a.masked([(0.46, 0.235), (0.63, 0.235), (0.63, 0.62), (0.46, 0.62)], veins(0.46, 0.63, (245, 220, 170, 170)))
    a.glow(0.545, 0.42, 0.06, 0.12, '#FFE8B8', 0.3, 0.03)
    a.rect(0.3, 0.235, 0.46, 0.62, '#6F8E9C', a=0.45)
    a.rect(0.63, 0.235, 0.84, 0.62, '#5E7F8E', a=0.5)
    for x in (0.38, 0.72):
        a.rect(x, 0.235, x + 0.005, 0.62, '#E8EDF0')
        a.rect(x + 0.003, 0.235, x + 0.005, 0.62, '#7D8890')
    a.rect(0.04, 0.2, 0.86, 0.235, '#F2F0EA')
    a.soft_poly([(0.04, 0.235), (0.86, 0.235), (0.86, 0.27), (0.04, 0.27)], '#2a2723', 0.35, 0.01)
    a.rect(0, 0.72, 1, 1, '#2F3F43')
    a.reflect(0.72, 1.0, '#26353A', a=0.45)
    a.rect(0, 0.715, 1, 0.725, '#EDE6D6')
    return a


def trellick():
    a = Art(*T, seed=26)
    a.grad(0, 0, 1, 1, '#98B6D0', '#E6EAEB')
    a.rect(0.1, 0.13, 0.6, 1, '#A0998E')
    for r in range(38):
        y = 0.14 + r * 0.0225
        for c in range(9):
            x = 0.115 + c * 0.054
            a.rect(x, y, x + 0.048, y + 0.012, '#3F3D3A')
            if a.r.random() < 0.3:
                a.rect(x, y + 0.012, x + 0.048, y + 0.02, a.r.choice(['#C8553B', '#B88A3A', '#4F6E8C', '#8A7F70']))
            else:
                a.rect(x, y + 0.012, x + 0.048, y + 0.02, '#B5AEA2')
    a.rect(0.55, 0.13, 0.6, 1, '#7E776D')
    a.rect(0.72, 0.06, 0.84, 1, '#A39C90')
    a.rect(0.8, 0.06, 0.84, 1, '#7E776D')
    for i in range(30):
        y = 0.1 + i * 0.03
        a.rect(0.77, y, 0.785, y + 0.02, '#3F3D3A')
    for i in range(12):
        y = 0.16 + i * 0.0675
        a.rect(0.6, y, 0.72, y + 0.018, '#8F887D')
        a.rect(0.6, y + 0.004, 0.72, y + 0.012, '#3F3D3A')
    a.rect(0.66, 0.01, 0.92, 0.065, '#A9A296')
    a.rect(0.66, 0.05, 0.92, 0.065, '#7E776D')
    for i in range(8):
        a.rect(0.68 + i * 0.03, 0.02, 0.69 + i * 0.03, 0.045, '#3F3D3A')
    a.noise(0, 0, 1, 1, 6, 2)
    return a


def kolumba():
    a = Art(*L, seed=27)
    a.grad(0, 0, 1, 0.2, '#C6D0D7', '#EEF0EF')
    a.rect(0.04, 0.12, 0.96, 0.92, '#ABA8A1')
    for i in range(150):
        y = 0.12 + i * 0.0054
        a.line([(0.04, y), (0.96, y)], '#9A978F', 0.0008, a=0.6)
    for r in range(28):
        for c in range(60):
            x = 0.06 + c * 0.0095 + (r % 2) * 0.0047
            y = 0.34 + r * 0.0135
            if x < 0.6:
                a.rect(x, y, x + 0.004, y + 0.006, '#2F2D2A')
    a.rect(0.66, 0.26, 0.92, 0.52, '#3A3F44')
    a.soft_poly([(0.66, 0.26), (0.75, 0.26), (0.7, 0.52), (0.66, 0.52)], '#D7E0E6', 0.3, 0.01)
    # gothic ruin base
    for i in range(160):
        x = a.r.uniform(0.04, 0.96)
        y = a.r.uniform(0.76, 0.92)
        a.rect(x, y, x + a.r.uniform(0.02, 0.05), y + a.r.uniform(0.015, 0.03), jit('#8E8270', 14, a.r))
    a.poly(arch_pts(0.7, 0.8, 0.92, 0.72, pointed=True), '#2C2925')
    a.grad(0, 0.92, 1, 1, '#8C8A84', '#6E6C66')
    a.people(0.95, [0.3, 0.33], 0.07)
    a.noise(0, 0, 1, 1, 4)
    return a


def tate():
    a = Art(*P, seed=28)
    a.grad(0, 0, 1, 1, '#AAC1D4', '#EEEAE2')
    a.rect(0.43, 0.04, 0.57, 0.62, '#6F432D')
    a.rect(0.53, 0.04, 0.57, 0.62, '#57331F')
    for i in range(5):
        x = 0.45 + i * 0.022
        a.rect(x, 0.07, x + 0.006, 0.6, '#4E2E1C')
    a.rect(0.42, 0.03, 0.58, 0.045, '#5A3824')
    a.rect(0.02, 0.4, 0.98, 0.46, '#E8EFF0')
    a.glow(0.5, 0.43, 0.48, 0.03, '#FFFFFF', 0.4, 0.02)
    for i in range(30):
        x = 0.02 + i * 0.032
        a.line([(x, 0.4), (x, 0.46)], '#9DB0B6', 0.0012)
    a.rect(0.02, 0.46, 0.98, 0.86, '#7A4B33')
    a.grad(0.02, 0.46, 0.98, 0.86, '#86553B', '#694029')
    for i in range(9):
        x = 0.06 + i * 0.105
        a.rect(x, 0.5, x + 0.025, 0.84, '#3B2418')
    a.noise(0, 0.04, 1, 0.86, 8, 2)
    a.grad(0, 0.86, 1, 1, '#B9B3A6', '#9C968A')
    for x in (0.08, 0.92):
        a.tree(x, 0.95, 0.07, '#5F7A3D', '#7B9650', '#E9E6DE')
    a.people(0.94, [0.3, 0.34, 0.52, 0.66, 0.7], 0.05)
    return a


def can_lis():
    a = Art(*L, seed=29)
    a.rect(0, 0, 1, 1, '#C79A5F')
    for i in range(18):
        y = i * 0.06
        a.line([(0, y), (1, y)], '#A97F49', 0.0015)
        off = 0.06 if i % 2 else 0
        for k in range(12):
            a.line([(off + k * 0.12, y), (off + k * 0.12, y + 0.06)], '#A97F49', 0.0015)
    a.noise(0, 0, 1, 1, 8, 2)

    def win(x0, y0, x1, y1, depth=0.03):
        a.rect(x0, y0, x1, y1, '#5A4128')
        ix0, iy0, ix1, iy1 = x0 + depth, y0 + depth * a.ar, x1 - depth * 0.3, y1 - depth * 0.3 * a.ar
        a.poly([(x0, y0), (x1, y0), (ix1, iy0), (ix0, iy0)], '#8A6A42')
        a.poly([(x0, y0), (ix0, iy0), (ix0, iy1), (x0, y1)], '#6E5233')
        hz = iy0 + (iy1 - iy0) * 0.48
        a.grad(ix0, iy0, ix1, hz, '#9EC7E6', '#E6EEF0')
        a.grad(ix0, hz, ix1, iy1, '#2E73A8', '#1B4E7C')
    win(0.06, 0.2, 0.3, 0.6)
    win(0.36, 0.2, 0.6, 0.6)
    win(0.66, 0.2, 0.94, 0.6)
    a.rect(0, 0.78, 1, 1, '#A88052')
    a.poly([(0.06, 0.78), (0.34, 0.78), (0.42, 1), (0.1, 1)], '#E8C88E', a=0.6)
    a.rect(0.08, 0.66, 0.92, 0.72, '#B38956')
    a.rect(0.08, 0.72, 0.92, 0.74, '#8A6A42')
    return a


def habitat():
    a = Art(*L, seed=30)
    a.grad(0, 0, 1, 0.76, '#9BC0DE', '#E5ECEE')
    a.grad(0, 0.76, 1, 0.8, '#8C8A6C', '#77755A')
    w, h, dx, dy = 0.1, 0.075, 0.03, 0.022
    levels = [(0.08, 0.92, 8), (0.14, 0.86, 7), (0.2, 0.8, 6), (0.26, 0.74, 5), (0.32, 0.68, 4), (0.4, 0.6, 3), (0.48, 0.54, 1)]
    for lv, (x0, x1, n) in enumerate(levels):
        y = 0.76 - (lv + 1) * h
        xs = [x0 + i * (x1 - x0 - w) / max(1, n - 1) for i in range(n)]
        a.r.shuffle(xs)
        xs = sorted(xs[:max(1, n - a.r.randint(0, 2))], reverse=True)
        for x in xs:
            x += a.r.uniform(-0.02, 0.02)
            a.poly([(x, y), (x + dx, y - dy), (x + w + dx, y - dy), (x + w, y)], '#E2DCCF')
            a.poly([(x + w, y), (x + w + dx, y - dy), (x + w + dx, y + h - dy), (x + w, y + h)], '#A49C8D')
            a.rect(x, y, x + w, y + h, '#CFC7B8')
            if a.r.random() < 0.6:
                a.rect(x + 0.015, y + 0.02, x + w - 0.02, y + h - 0.015, '#3E4549')
            if a.r.random() < 0.4:
                for _ in range(3):
                    gx = x + a.r.uniform(0.01, w)
                    a.ell(gx - 0.01, y - 0.016, gx + 0.012, y + 0.002, '#5E7D45')
    a.rect(0, 0.8, 1, 1, '#5A7E96')
    a.reflect(0.8, 1.0, '#41657E', a=0.45)
    return a


def salk():
    a = Art(*W, seed=31)
    vx, vy = 0.5, 0.44
    a.grad(0, 0, 1, vy, '#6F8FBE', '#F4C27A')
    a.glow(vx, vy, 0.12, 0.05, '#FFE2A8', 0.8, 0.03)
    a.grad(0, vy, 1, vy + 0.04, '#E9A766', '#6C7FA0')

    def pr(X, Y, Z):
        f = 0.55
        return (vx + X / Z * f, vy + Y / Z * f * a.ar)

    a.poly([pr(-1, 0.5, 1.2), pr(1, 0.5, 1.2), pr(1, 0.5, 400), pr(-1, 0.5, 400)], '#E2D6C1')
    a.grad(0, vy, 1, 1, '#E8D9BE', '#D5C6AC')
    for z in [1.2 * 1.25 ** k for k in range(30)]:
        a.line([pr(-1, 0.5, z), pr(1, 0.5, z)], '#BFAF94', 0.0012, a=0.7)
    for X in [-0.75, -0.5, -0.25, 0.25, 0.5, 0.75]:
        a.line([pr(X, 0.5, 1.0), pr(X, 0.5, 400)], '#BFAF94', 0.0012, a=0.7)
    a.poly([pr(-0.012, 0.5, 1.0), pr(0.012, 0.5, 1.0), pr(0.012, 0.5, 400), pr(-0.012, 0.5, 400)], '#F9DDA2')
    for s in (-1, 1):
        a.poly([pr(s * 1, 0.5, 1.0), pr(s * 1, -0.8, 1.0), pr(s * 1, -0.8, 60), pr(s * 1, 0.5, 60)], '#9C968C')
        z = 1.6
        while z < 30:
            zl = z * 1.18
            front = '#BDB6AA' if s < 0 else '#ADA69A'
            a.poly([pr(s * 1, 0.5, z), pr(s * 0.8, 0.5, z), pr(s * 0.8, -0.65, z), pr(s * 1, -0.65, z)], '#CFC8BC' if s < 0 else '#D9D2C6')
            a.poly([pr(s * 0.8, 0.5, z), pr(s * 0.8, 0.5, zl), pr(s * 0.8, -0.65, zl), pr(s * 0.8, -0.65, z)], front)
            a.poly([pr(s * 0.8, -0.2, z * 1.03), pr(s * 0.8, -0.2, zl * 0.98), pr(s * 0.8, -0.55, zl * 0.98), pr(s * 0.8, -0.55, z * 1.03)], '#8A5A36')
            z = zl * 1.22
    a.noise(0, 0, 1, 1, 4)
    return a


def gando():
    a = Art(*W, seed=32)
    a.grad(0, 0, 1, 0.72, '#3C7AC6', '#C2D9EB')
    a.grad(0, 0.72, 1, 1, '#C98A4B', '#A86A33')
    a.noise(0, 0.72, 1, 1, 12, 2)
    # tree
    a.rect(0.87, 0.45, 0.885, 0.74, '#4A3828')
    a.poly([(0.75, 0.42), (0.99, 0.4), (1.02, 0.46), (0.73, 0.47)], '#3F5A2E')
    a.poly([(0.78, 0.39), (0.96, 0.37), (0.98, 0.42), (0.76, 0.43)], '#557540')
    a.rect(0.12, 0.46, 0.84, 0.74, '#B76D44')
    for i in range(30):
        a.line([(0.12, 0.46 + i * 0.0095), (0.84, 0.46 + i * 0.0095)], '#94512F', 0.0009, a=0.6)
    for i in range(7):
        x = 0.16 + i * 0.1
        a.rect(x, 0.54, x + 0.04, 0.66, '#3A2216')
        a.rect(x, 0.54, x + 0.04, 0.56, '#8C8F92')
    a.rect(0.1, 0.44, 0.86, 0.46, '#8E5536')
    for i in range(37):
        x = 0.1 + i * 0.02
        a.line([(x, 0.44), (x + 0.01, 0.33), (x + 0.02, 0.44)], '#5E6266', 0.0015)
    roof = [(0.04, 0.33), (0.96, 0.3), (0.96, 0.325), (0.04, 0.355)]
    a.poly(roof, '#A9AEB2')

    def corr(d):
        for i in range(140):
            x = (0.04 + i * 0.0066) * a.W
            d.line([(x, 0.28 * a.H), (x, 0.37 * a.H)], fill=(130, 136, 142, 255) if i % 2 else (198, 202, 206, 255), width=5)
    a.masked(roof, corr)
    a.soft_poly([(0.1, 0.355), (0.9, 0.33), (0.9, 0.38), (0.1, 0.4)], '#1a1a1a', 0.3, 0.01)
    a.people(0.8, [0.3, 0.33, 0.36, 0.55, 0.58], 0.04, '#2A1A10')
    return a


def djenne():
    a = Art(*W, seed=33)
    a.grad(0, 0, 1, 0.75, '#E6C69C', '#F6E8D4')
    a.grad(0, 0.75, 1, 1, '#CBA678', '#B08B5E')
    a.noise(0, 0.75, 1, 1, 10, 2)
    lit, sh = '#B07B4F', '#8E5E3B'
    a.rect(0.04, 0.4, 0.96, 0.78, lit)
    for x in [0.04 + i * 0.03 for i in range(31)]:
        a.poly([(x, 0.4), (x + 0.012, 0.32), (x + 0.024, 0.4)], lit)
        a.ell(x + 0.008, 0.31, x + 0.016, 0.325, '#F2EAD8')
    for cx, w, top in ((0.25, 0.1, 0.12), (0.5, 0.12, 0.08), (0.75, 0.1, 0.12)):
        a.poly([(cx - w / 2, 0.78), (cx - w / 2 + 0.01, top + 0.06), (cx, top), (cx + w / 2 - 0.01, top + 0.06), (cx + w / 2, 0.78)], lit)
        a.poly([(cx + 0.01, top + 0.02), (cx + w / 2 - 0.01, top + 0.06), (cx + w / 2, 0.78), (cx + 0.02, 0.78)], sh)
        a.ell(cx - 0.008, top - 0.025, cx + 0.008, top + 0.005, '#F4ECDC')
        for k in range(10):
            y = top + 0.08 + k * 0.06
            for j in range(3):
                x = cx - w / 3 + j * w / 3
                a.rect(x, y, x + 0.016, y + 0.006, '#4A3020')
    for k in range(5):
        y = 0.45 + k * 0.065
        for j in range(30):
            x = 0.06 + j * 0.03
            a.rect(x, y, x + 0.012, y + 0.005, '#4A3020')
    a.noise(0.04, 0.08, 0.96, 0.78, 8, 2)
    a.people(0.86, [0.1, 0.14, 0.2, 0.38, 0.44, 0.6, 0.62, 0.8, 0.9], 0.05, '#2A1A10')
    return a


def kicc():
    a = Art(*P, seed=34)
    a.grad(0, 0, 1, 0.85, '#79AEDB', '#DEEAEF')
    a.tree(0.06, 0.9, 0.09)
    a.tree(0.95, 0.9, 0.1)
    a.grad(0.36, 0.17, 0.64, 0.86, '#C9694C', '#8E3B25', horiz=True)
    for i in range(22):
        x = 0.36 + i * 0.0128
        a.line([(x, 0.17), (x, 0.86)], '#6E2D1C', 0.002, a=0.5)
    a.rect(0.47, 0.13, 0.53, 0.18, '#A84A32')
    a.ell(0.22, 0.09, 0.78, 0.15, '#B65A3E')
    a.ell(0.22, 0.08, 0.78, 0.13, '#D47A5C')
    cone = [(0.0, 0.88), (0.06, 0.7), (0.34, 0.66), (0.4, 0.88)]
    a.poly(cone, '#B6553B')
    for i in range(12):
        x = 0.02 + i * 0.032
        a.line([(0.2, 0.62), (x, 0.88)], '#7E301C', 0.002)
    a.grad(0, 0.86, 1, 1, '#B6B0A2', '#8E887C')
    a.people(0.92, [0.45, 0.5, 0.62], 0.05)
    a.noise(0, 0, 1, 1, 4)
    return a


def zeitz():
    a = Art(*P, seed=35)
    a.grad(0, 0, 1, 1, '#5C9AD6', '#CBDFEE')
    a.rect(0.2, 0.04, 0.8, 1, '#C3BCB1')
    for i in range(8):
        x = 0.2 + i * 0.075
        a.grad(x, 0.4, x + 0.075, 1, '#D6D0C6', '#958E83', horiz=True)
    for r in range(7):
        for c in range(6):
            x0, y0 = 0.22 + c * 0.093, 0.06 + r * 0.05
            x1, y1 = x0 + 0.088, y0 + 0.046
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            shades = ['#9EC4E4', '#6E9CC8', '#C7DDEE', '#4F7EAD']
            a.poly([(x0, y0), (x1, y0), (cx, cy)], shades[0])
            a.poly([(x1, y0), (x1, y1), (cx, cy)], shades[1])
            a.poly([(x0, y1), (x1, y1), (cx, cy)], shades[3])
            a.poly([(x0, y0), (x0, y1), (cx, cy)], shades[2])
            a.rect(x0, y0, x1, y0 + 0.002, '#5A5A58')
    a.rect(0.2, 0.39, 0.8, 0.41, '#8E877C')
    a.noise(0.2, 0.4, 0.8, 1, 7, 2)
    a.grad(0, 0.92, 1, 1, '#4D6B82', '#2E4A60')
    return a


def lalibela():
    a = Art(*S, seed=36)
    a.rect(0, 0, 1, 1, '#A8714C')
    a.noise(0, 0, 1, 1, 16, 4)
    for _ in range(25):
        x, y = a.r.uniform(0, 1), a.r.uniform(0, 1)
        if 0.12 < x < 0.88 and 0.12 < y < 0.88:
            continue
        a.ell(x - 0.025, y - 0.025, x + 0.025, y + 0.025, a.r.choice(['#4F6B33', '#6B8445']))
    a.rect(0.12, 0.12, 0.88, 0.88, '#4E2D1D')
    a.soft_poly([(0.12, 0.12), (0.88, 0.12), (0.88, 0.2), (0.2, 0.2), (0.2, 0.88), (0.12, 0.88)], '#1E0F08', 0.6, 0.01)

    def cross(c, r, w, col):
        a.rect(c - w, c - r, c + w, c + r, col)
        a.rect(c - r, c - w, c + r, c + w, col)
    a.poly([(0.5 - 0.11 + 0.04, 0.18 + 0.04), (0.5 + 0.11 + 0.04, 0.18 + 0.04), (0.5 + 0.11 + 0.04, 0.82 + 0.04), (0.5 - 0.11 + 0.04, 0.82 + 0.04)], '#2B170D', a=0.7)
    a.poly([(0.18 + 0.04, 0.39 + 0.04), (0.82 + 0.04, 0.39 + 0.04), (0.82 + 0.04, 0.61 + 0.04), (0.18 + 0.04, 0.61 + 0.04)], '#2B170D', a=0.7)
    cross(0.5, 0.32, 0.11, '#B9805A')
    cross(0.5, 0.26, 0.075, '#C78E66')
    cross(0.5, 0.2, 0.045, '#D39D74')
    cross(0.5, 0.14, 0.018, '#B9805A')
    a.noise(0.18, 0.18, 0.82, 0.82, 6, 2)
    return a


def nasir():
    a = Art(*L, seed=37)
    a.rect(0, 0, 1, 1, '#3A2A2A')
    a.rect(0, 0.0, 1, 0.6, '#5A4A44')
    for i in range(4):
        x0 = 0.04 + i * 0.245
        x1 = x0 + 0.2
        pts = arch_pts(x0, x1, 0.58, 0.06, pointed=True)

        def glass(d, x0=x0, x1=x1):
            rr = a.r
            for gy in range(0, int(0.6 * a.H), 14):
                for gx in range(int(x0 * a.W), int(x1 * a.W), 14):
                    col = rr.choice([(214, 46, 60), (246, 196, 60), (44, 98, 190), (60, 160, 120), (240, 120, 50), (250, 240, 220)])
                    d.rectangle([gx, gy, gx + 12, gy + 12], fill=col + (255,))
        a.masked(pts, glass)
        a.line(pts, '#D8C9A8', 0.003)
    a.grad(0, 0.6, 1, 1, '#7E1E2A', '#5A121C')
    for r in range(8):
        for c in range(24):
            if (r + c) % 2:
                a.rect(c / 24, 0.6 + r * 0.05, c / 24 + 0.02, 0.6 + r * 0.05 + 0.02, '#A23A3E', a=0.6)
    cols = [(214, 46, 60), (246, 196, 60), (44, 98, 190), (60, 160, 120), (240, 120, 50)]
    for i in range(4):
        x0 = 0.04 + i * 0.245
        for k in range(18):
            x = x0 + a.r.uniform(0, 0.2) + 0.12
            y = a.r.uniform(0.66, 0.98)
            c = '#%02x%02x%02x' % a.r.choice(cols)
            a.soft_poly([(x, y), (x + 0.03, y), (x + 0.05, y + 0.04), (x + 0.02, y + 0.04)], c, 0.5, 0.004)
    for i in range(5):
        x = 0.02 + i * 0.245
        a.rect(x, 0.0, x + 0.018, 0.72, '#B9A88A')
        for k in range(30):
            y = k * 0.024
            a.line([(x, y), (x + 0.018, y + 0.012)], '#8E7C60', 0.002)
    a.noise(0, 0, 1, 1, 5)
    return a


def ima():
    a = Art(*S, seed=38)
    a.rect(0, 0, 1, 1, '#283139')
    n = 4
    cs = 1 / n
    for r in range(n):
        for c in range(n):
            x0, y0 = c * cs, r * cs
            a.rect(x0 + 0.004, y0 + 0.004, x0 + cs - 0.004, y0 + cs - 0.004, '#7C8A93')
            cx, cy = x0 + cs / 2, y0 + cs / 2
            R = cs * 0.3
            a.ell(cx - R, cy - R, cx + R, cy + R, '#A9B5BC')
            blades = 8
            open_r = R * (0.25 + 0.5 * a.r.random())
            for b in range(blades):
                t0 = 2 * math.pi * b / blades
                t1 = t0 + 2 * math.pi / blades
                a.poly([(cx + R * math.cos(t0), cy + R * math.sin(t0)), (cx + R * math.cos(t1), cy + R * math.sin(t1)),
                        (cx + open_r * math.cos(t1 + 0.6), cy + open_r * math.sin(t1 + 0.6))], '#93A1AA' if b % 2 else '#B8C3C9')
            a.ell(cx - open_r * 0.8, cy - open_r * 0.8, cx + open_r * 0.8, cy + open_r * 0.8, '#1C252C')
            a.glow(cx, cy, open_r * 0.5, open_r * 0.5, '#9FD3F0', 0.4, 0.01)
            for k in range(4):
                sx = x0 + (0.03 if k % 2 == 0 else cs - 0.06)
                sy = y0 + (0.03 if k < 2 else cs - 0.06)
                a.rect(sx, sy, sx + 0.03, sy + 0.03, '#5D6B74')
                a.ell(sx + 0.008, sy + 0.008, sx + 0.022, sy + 0.022, '#1C252C')
    a.soft_poly([(0, 0), (0.6, 0), (0, 0.6)], '#FFFFFF', 0.12, 0.05)
    return a


def azadi():
    a = Art(*P, seed=39)
    a.grad(0, 0, 1, 0.86, '#84B2DD', '#E3ECEF')
    outer = [(0.06, 0.86), (0.2, 0.62), (0.34, 0.36), (0.4, 0.2), (0.4, 0.1), (0.6, 0.1), (0.6, 0.2), (0.66, 0.36), (0.8, 0.62), (0.94, 0.86)]
    a.poly(outer, '#ECE6DA')
    a.poly([(0.5, 0.1), (0.6, 0.1), (0.6, 0.2), (0.66, 0.36), (0.8, 0.62), (0.94, 0.86), (0.5, 0.86)], '#D6CFC1')
    inner = [(0.26, 0.86)] + [(0.5 - 0.24 * math.cos(t), 0.86 - 0.42 * math.sin(t) ** 0.55) for t in [math.pi / 2 * i / 20 for i in range(21)]]
    inner += [(0.5 + 0.24 * math.cos(t), 0.86 - 0.42 * math.sin(t) ** 0.55) for t in [math.pi / 2 * i / 20 for i in range(20, -1, -1)]]
    a.poly(inner, '#B9D3EC')
    a.grad(0.26, 0.44, 0.74, 0.86, '#9BC2E6', '#DCE8EF')
    a.masked([(0, 0), (1, 0), (1, 1), (0, 1)], lambda d: None)
    inner2 = [(x, y) for x, y in inner]
    a.poly(inner2[:3] + [(0.5, 0.44)] + inner2[-3:], '#2E9AAE', a=0)
    for i in range(6):
        y = 0.46 + i * 0.012
        a.line([(0.46 - i * 0.02, y), (0.54 + i * 0.02, y)], '#2E9AAE', 0.004)
    for i in range(14):
        x = 0.41 + i * 0.014
        a.line([(x, 0.1), (x, 0.2)], '#C3BBAB', 0.002)
    a.grad(0, 0.86, 1, 1, '#D3CFC4', '#B8B3A7')
    a.people(0.9, [0.3, 0.42, 0.58, 0.7], 0.045)
    a.noise(0, 0, 1, 1, 4)
    return a


def azadi_fix():
    a = Art(*P, seed=39)
    a.grad(0, 0, 1, 0.86, '#84B2DD', '#E3ECEF')
    a.clouds(4, 0.05, 0.3, 0.4)
    outer = [(0.06, 0.86), (0.2, 0.62), (0.34, 0.36), (0.4, 0.2), (0.4, 0.1), (0.6, 0.1), (0.6, 0.2), (0.66, 0.36), (0.8, 0.62), (0.94, 0.86)]
    a.poly(outer, '#ECE6DA')
    a.poly([(0.5, 0.1), (0.6, 0.1), (0.6, 0.2), (0.66, 0.36), (0.8, 0.62), (0.94, 0.86), (0.5, 0.86)], '#D9D2C4')
    arch = [(0.5 - 0.25 * math.cos(t), 0.86 - 0.44 * math.sin(t) ** 0.5) for t in [math.pi / 2 * i / 30 for i in range(31)]]
    arch += [(0.5 + 0.25 * math.cos(t), 0.86 - 0.44 * math.sin(t) ** 0.5) for t in [math.pi / 2 * i / 30 for i in range(30, -1, -1)]]
    band = [(0.5 - 0.29 * math.cos(t), 0.86 - 0.5 * math.sin(t) ** 0.5) for t in [math.pi / 2 * i / 30 for i in range(31)]]
    band += [(0.5 + 0.29 * math.cos(t), 0.86 - 0.5 * math.sin(t) ** 0.5) for t in [math.pi / 2 * i / 30 for i in range(30, -1, -1)]]
    a.poly(band, '#2E8FA3')
    a.poly(arch, '#A9CBEA')

    def sky(d):
        for i in range(100):
            t = i / 99
            col = mix('#8DB8E0', '#DCE8EF', t)
            d.rectangle([0, (0.42 + 0.44 * t) * a.H, a.W, (0.42 + 0.44 * (t + 0.011)) * a.H], fill=col + (255,))
    a.masked(arch, sky)
    for i in range(12):
        x = 0.41 + i * 0.016
        a.line([(x, 0.1), (x, 0.2)], '#C3BBAB', 0.002)
    a.grad(0, 0.86, 1, 1, '#D3CFC4', '#B8B3A7')
    a.people(0.92, [0.3, 0.42, 0.58, 0.7], 0.045)
    a.noise(0, 0, 1, 1, 4)
    return a


def qatar():
    a = Art(*W, seed=40)
    a.grad(0, 0, 1, 0.7, '#D9C4A4', '#F5EDE0')
    a.glow(0.85, 0.2, 0.06, 0.08, '#FFF4D8', 0.8, 0.03)
    a.grad(0, 0.7, 1, 1, '#D8BD92', '#C2A276')
    a.noise(0, 0.7, 1, 1, 8, 2)
    discs = []
    for i in range(26):
        cx = a.r.uniform(0.1, 0.9)
        cy = a.r.uniform(0.32, 0.68) + (abs(cx - 0.5)) * 0.15
        rx = a.r.uniform(0.06, 0.14)
        ry = rx * a.r.uniform(0.2, 0.45)
        rot = a.r.uniform(-0.6, 0.6)
        discs.append((cy, cx, rx, ry, rot))
    discs.sort()
    a.rect(0.12, 0.5, 0.88, 0.72, '#4A4642')
    for cy, cx, rx, ry, rot in discs:
        a.poly(ellipse_pts(cx, cy + 0.015, rx, ry, rot, ar=a.ar), '#A88A62')
        a.poly(ellipse_pts(cx, cy, rx, ry, rot, ar=a.ar), '#E6D2AE')
        a.poly(ellipse_pts(cx - rx * 0.1, cy - 0.005, rx * 0.7, ry * 0.6, rot, ar=a.ar), '#EEDDBF', a=0.6)
    return a


def gourna():
    a = Art(*L, seed=41)
    a.grad(0, 0, 1, 0.75, '#5B9CD6', '#D0E2EE')
    a.grad(0, 0.75, 1, 1, '#D9B98C', '#C29D6C')
    lit, sh = '#CFA170', '#A87C4E'
    a.rect(0.05, 0.42, 0.55, 0.76, lit)
    a.rect(0.42, 0.42, 0.55, 0.76, sh)
    a.ell(0.1, 0.3, 0.3, 0.5, lit)
    a.rect(0.1, 0.4, 0.3, 0.44, lit)
    a.ell(0.22, 0.3, 0.3, 0.5, sh, a=0.5)
    a.rect(0.32, 0.36, 0.5, 0.43, lit)
    for i in range(3):
        x = 0.33 + i * 0.06
        a.poly(arch_pts(x, x + 0.05, 0.43, 0.38), '#E2BB8A')
    a.rect(0.55, 0.5, 0.95, 0.76, lit)
    for i in range(4):
        x = 0.57 + i * 0.095
        a.poly(arch_pts(x, x + 0.085, 0.52, 0.42), '#D7AC7A')
        a.poly(arch_pts(x + 0.02, x + 0.065, 0.74, 0.62), '#3E2818')
    for x, y in ((0.12, 0.55), (0.2, 0.55), (0.3, 0.6)):
        a.rect(x, y, x + 0.03, y + 0.05, '#3E2818')
    a.poly(arch_pts(0.08, 0.16, 0.76, 0.62), '#3E2818')
    # palm
    a.line([(0.86, 0.76), (0.84, 0.5), (0.85, 0.24)], '#6C5236', 0.008)
    for t in range(9):
        ang = -math.pi + t * math.pi / 8
        a.line([(0.85, 0.24), (0.85 + 0.09 * math.cos(ang), 0.24 + 0.09 * a.ar * math.sin(ang) * 0.5 + 0.03)], '#3F6A32', 0.006)
    a.noise(0.05, 0.3, 0.95, 0.76, 9, 2)
    return a


def shibam():
    a = Art(*W, seed=42)
    a.grad(0, 0, 1, 0.75, '#CDB896', '#F1E7D6')
    a.poly([(0, 0.25), (0.3, 0.2), (0.6, 0.24), (0.9, 0.18), (1, 0.2), (1, 0.72), (0, 0.72)], '#B48F66')
    a.poly([(0, 0.25), (0.3, 0.2), (0.6, 0.24), (0.9, 0.18), (1, 0.2), (1, 0.26), (0, 0.3)], '#C9A67C')
    xs = sorted([a.r.uniform(0.05, 0.92) for _ in range(30)])
    for k, x in enumerate(xs):
        w = a.r.uniform(0.05, 0.09)
        top = a.r.uniform(0.28, 0.5)
        a.rect(x, top, x + w, 0.8, '#B98A5E')
        a.rect(x + w * 0.7, top, x + w, 0.8, '#9A6F48')
        a.rect(x, top, x + w, top + (0.8 - top) * 0.16, '#EDE7DA')
        a.rect(x + w * 0.7, top, x + w, top + (0.8 - top) * 0.16, '#CFC8B9')
        for r in range(int((0.8 - top) / 0.04)):
            for c in range(2):
                wx, wy = x + 0.01 + c * w * 0.35, top + 0.03 + r * 0.04
                a.rect(wx, wy, wx + 0.007, wy + 0.012, '#3A2618')
                a.rect(wx - 0.002, wy - 0.003, wx + 0.009, wy, '#F0EBE0')
    a.grad(0, 0.8, 1, 1, '#B89A70', '#9E8058')
    for x in (0.04, 0.12, 0.88, 0.95):
        a.line([(x, 0.86), (x + 0.01, 0.7)], '#5C4630', 0.004)
        for t in range(7):
            ang = -math.pi + t * math.pi / 6
            a.line([(x + 0.01, 0.7), (x + 0.01 + 0.04 * math.cos(ang), 0.7 + 0.03 * math.sin(ang) + 0.02)], '#4F6E36', 0.004)
    a.noise(0, 0, 1, 1, 5)
    return a


def bruder():
    a = Art(*P, seed=43)
    a.grad(0, 0, 1, 0.7, '#97A9B6', '#E4E3DA')
    a.clouds(8, 0.05, 0.4, 0.45)
    a.grad(0, 0.68, 1, 1, '#C7AE5C', '#8E8A3E')
    for i in range(30):
        y = 0.7 + i * 0.01
        a.line([(0, y), (1, y + 0.02)], '#A68F44', 0.0015, a=0.6)
    a.poly([(0.36, 0.72), (0.38, 0.18), (0.56, 0.18), (0.58, 0.74), (0.5, 0.76)], '#7A6F62')
    a.poly([(0.56, 0.18), (0.66, 0.2), (0.66, 0.72), (0.58, 0.74)], '#5E554A')
    for i in range(60):
        y = 0.18 + i * 0.0092
        a.line([(0.37, y), (0.66, y + 0.002)], '#655B4F', 0.0012, a=0.6)
    a.poly([(0.44, 0.74), (0.47, 0.6), (0.5, 0.75)], '#2E2A26')
    a.people(0.8, [0.72], 0.05)
    a.noise(0, 0, 1, 1, 5)
    return a


def superkilen():
    a = Art(*L, seed=44)
    a.rect(0, 0, 1, 1, '#D8344A')
    a.poly([(0, 0), (0.55, 0), (0.25, 0.5), (0, 0.6)], '#EB6E8B')
    a.poly([(0.6, 0.55), (1, 0.4), (1, 1), (0.45, 1)], '#1C1C1E')
    for k in range(16):
        pts = [(x / 40, 0.06 * k + 0.08 * math.sin(x / 40 * 6 + k * 0.4) - 0.1) for x in range(41)]
        a.line(pts, '#F8F3F0', 0.003, a=0.9)
    def lines(d):
        for k in range(20):
            pts = [((0.4 + x / 40 * 0.7) * a.W, (0.35 + 0.05 * k + 0.05 * math.sin(x / 6 + k)) * a.H) for x in range(41)]
            d.line(pts, fill=(240, 240, 240, 230), width=5)
    a.masked([(0.6, 0.55), (1, 0.4), (1, 1), (0.45, 1)], lines)
    for x, y in ((0.2, 0.3), (0.72, 0.2), (0.35, 0.75), (0.85, 0.75)):
        a.ell(x - 0.035, y - 0.035 * a.ar + 0.02, x + 0.045, y + 0.035 * a.ar + 0.03, '#000000', a=0.25)
        a.ell(x - 0.04, y - 0.04 * a.ar, x + 0.04, y + 0.04 * a.ar, '#4F7A3A')
        a.ell(x - 0.025, y - 0.03 * a.ar, x + 0.02, y + 0.01, '#6E9A4E')
    for x, y in ((0.5, 0.25), (0.53, 0.27), (0.56, 0.29)):
        a.ell(x - 0.012, y - 0.016, x + 0.012, y + 0.016, '#111111')
        a.ell(x + 0.02, y - 0.016, x + 0.044, y + 0.016, '#111111')
    a.rect(0.1, 0.62, 0.24, 0.66, '#F2C230')
    a.rect(0.62, 0.12, 0.7, 0.14, '#2EB2C9')
    a.people(0.5, [0.3, 0.44, 0.62], 0.05, '#111111')
    a.noise(0, 0, 1, 1, 6)
    return a


def malaparte():
    a = Art(*W, seed=45)
    a.grad(0, 0, 1, 0.36, '#96C3E6', '#E3EEF2')
    a.grad(0, 0.36, 1, 1, '#2F74AA', '#174876')
    for i in range(80):
        x, y = a.r.uniform(0, 1), a.r.uniform(0.4, 1)
        a.line([(x, y), (x + 0.03, y)], '#FFFFFF', 0.0012, a=0.2)
    rock = [(0.0, 0.52), (0.1, 0.48), (0.25, 0.47), (0.55, 0.46), (0.7, 0.48), (0.82, 0.55), (0.9, 0.7), (0.95, 0.95), (0.96, 1.0), (0, 1)]
    a.poly(rock, '#8E8064')
    a.poly([(0.6, 0.47), (0.7, 0.48), (0.82, 0.55), (0.9, 0.7), (0.95, 1), (0.7, 1), (0.66, 0.7)], '#6F634C')
    a.noise(0, 0.46, 1, 1, 10, 3)
    for i in range(14):
        x = a.r.uniform(0.02, 0.6)
        y = a.r.uniform(0.5, 0.9)
        a.ell(x - 0.03, y - 0.02, x + 0.03, y + 0.02, a.r.choice(['#3E5A30', '#506F3C']))
    a.rect(0.3, 0.37, 0.72, 0.47, '#B8402E')
    a.rect(0.62, 0.37, 0.72, 0.47, '#91301F')
    for i in range(6):
        x = 0.34 + i * 0.045
        a.rect(x, 0.4, x + 0.025, 0.44, '#3A1A12')
    a.poly([(0.3, 0.37), (0.36, 0.37), (0.12, 0.47), (0.06, 0.47)], '#B8402E')
    for i in range(10):
        t = i / 10
        a.line([(0.3 - 0.24 * t, 0.37 + 0.1 * t), (0.36 - 0.24 * t, 0.37 + 0.1 * t)], '#8E2E1E', 0.002)
    a.poly([(0.52, 0.37), (0.54, 0.31), (0.6, 0.31), (0.61, 0.37)], '#F2EEE6')
    a.noise(0, 0, 1, 1, 3)
    return a


def muralla():
    a = Art(*P, seed=46)
    a.grad(0, 0, 1, 0.3, '#1D5BB6', '#4C8ED6')
    a.rect(0, 0.15, 0.34, 1, '#E05A63')
    a.rect(0.34, 0.25, 0.68, 1, '#C93F4E')
    a.rect(0.68, 0.1, 1, 1, '#E8737A')

    def stair(x0, y0, x1, y1, col, steps=10):
        pts = [(x0, y0)]
        dx, dy = (x1 - x0) / steps, (y1 - y0) / steps
        for i in range(steps):
            pts.append((x0 + dx * i, y0 + dy * (i + 1)))
            pts.append((x0 + dx * (i + 1), y0 + dy * (i + 1)))
        pts.append((x1, y1 + 0.06))
        pts.append((x0, y0 + 0.06))
        a.poly(pts, col)
    stair(0.02, 0.3, 0.32, 0.62, '#6A5CB4')
    stair(0.36, 0.42, 0.66, 0.74, '#7FB5E6', 8)
    stair(0.98, 0.2, 0.7, 0.5, '#5A4CA8', 9)
    a.rect(0.68, 0.6, 1, 0.66, '#7FB5E6')
    a.soft_poly([(0.34, 0.25), (0.48, 0.25), (0.34, 0.6)], '#5A1F2E', 0.35, 0.01)
    a.soft_poly([(0.0, 0.7), (0.34, 0.8), (0.34, 1.0), (0, 1)], '#5A1F2E', 0.25, 0.01)
    a.rect(0.08, 0.8, 0.12, 0.92, '#3A1A2A')
    a.rect(0.8, 0.74, 0.86, 0.9, '#3A1A2A')
    a.noise(0, 0, 1, 1, 5)
    return a


def stacking():
    a = Art(*T, seed=47)
    a.grad(0, 0, 1, 0.12, '#C8D6DF', '#E9ECEB')
    a.rect(0, 0.08, 0.18, 1, '#C7C3BA')
    a.rect(0.82, 0.04, 1, 1, '#B8B3A9')
    for i in range(12):
        a.rect(0.84, 0.08 + i * 0.08, 0.96, 0.11 + i * 0.08, '#6E7378')
    a.rect(0.18, 0.08, 0.82, 1, '#3A4246')
    for i in range(13):
        y = 0.1 + i * 0.07
        for _ in range(16):
            x = a.r.uniform(0.18, 0.82)
            r = a.r.uniform(0.015, 0.035)
            a.ell(x - r, y - r * 0.8, x + r, y + r * 0.6, a.r.choice(['#3F6E2E', '#5C8E3E', '#7FAE52', '#2D5222']))
        for _ in range(6):
            x = a.r.uniform(0.2, 0.8)
            a.line([(x, y), (x + a.r.uniform(-0.01, 0.01), y + a.r.uniform(0.02, 0.05))], '#4C7A36', 0.004)
        a.rect(0.18, y, 0.82, y + 0.01, '#D9D6CF')
        a.rect(0.18, y + 0.01, 0.82, y + 0.014, '#9E9A92')
    a.noise(0, 0, 1, 1, 5)
    return a


def ningbo():
    a = Art(*W, seed=48)
    a.grad(0, 0, 1, 0.7, '#B9C4CB', '#E8E9E5')
    mass = [(0.06, 0.74), (0.1, 0.22), (0.38, 0.28), (0.52, 0.16), (0.7, 0.26), (0.94, 0.2), (0.96, 0.74)]

    def bricks(d):
        rr = a.r
        y = 0.14 * a.H
        while y < 0.76 * a.H:
            h = rr.choice([8, 10, 14])
            x = 0
            while x < a.W:
                w = rr.randint(18, 60)
                col = rr.choice([(120, 116, 108), (140, 132, 120), (98, 94, 90), (150, 110, 86), (170, 160, 146), (86, 80, 74)])
                d.rectangle([x, y, x + w - 2, y + h - 2], fill=col + (255,))
                x += w
            y += h
    a.masked(mass, bricks)
    a.soft_poly([(0.52, 0.16), (0.7, 0.26), (0.94, 0.2), (0.96, 0.74), (0.6, 0.74)], '#1a1a1a', 0.2, 0.01)
    for x, y in ((0.2, 0.4), (0.3, 0.55), (0.45, 0.36), (0.62, 0.5), (0.78, 0.38), (0.85, 0.58)):
        a.rect(x, y, x + 0.035, y + 0.055, '#8A5E3A')
        a.rect(x + 0.006, y + 0.008, x + 0.035, y + 0.055, '#1E1A17')
    a.rect(0, 0.74, 1, 1, '#6E7A74')
    a.reflect(0.74, 1.0, '#55625C', a=0.4)
    for i in range(40):
        x = a.r.uniform(0, 1)
        a.line([(x, 1), (x + a.r.uniform(-0.01, 0.01), a.r.uniform(0.86, 0.94))], '#9C9A66', 0.002)
    return a
