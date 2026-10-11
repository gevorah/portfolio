"""Láminas finales: vista orbital (A), estados de eclipse vistos desde la
órbita y comparaciones (misma escala y escala de carta planetaria)."""

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from globe import view_matrix

ROOT = Path(__file__).resolve().parent.parent
WORK, OUT = ROOT / "work", ROOT / "renders"
BG = (14, 12, 19, 255)

# escala común: px por radio planetario en las imágenes de 1400 px
SPHERE_PX_PER_UNIT = 1400 / 2 * 0.82
PEANUT_PX_PER_UNIT = 1400 / 2 / 2.2


def starfield(w, h, n, seed=1):
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), BG)
    d = ImageDraw.Draw(im)
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        r = rng.choice([0.5, 0.7, 0.9, 1.2])
        a = int(rng.uniform(60, 220))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(232, 230, 255, a))
    return im


def moon_img(size, base=(150, 148, 162), light=(-0.66, 0.48, 0.58)):
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    x = (xs + 0.5 - size / 2) / (size / 2)
    y = -(ys + 0.5 - size / 2) / (size / 2)
    r2 = x * x + y * y
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    L = np.array(light) / np.linalg.norm(light)
    d = np.clip(x * L[0] + y * L[1] + z * L[2], 0, 1) ** 0.8
    col = np.stack([d * base[0] + 6, d * base[1] + 6, d * base[2] + 10], -1)
    a = np.clip((1 - np.sqrt(r2)) * size / 2, 0, 1) * 255
    return Image.fromarray(np.dstack([np.clip(col, 0, 255), a]).astype(np.uint8), "RGBA")


def project(lon, lat, lon0, lat0, roll, size, radius=0.82):
    M = view_matrix(lon0, lat0, roll)
    la, lo = math.radians(lat), math.radians(lon)
    w = np.array([math.cos(la) * math.sin(lo), math.sin(la), math.cos(la) * math.cos(lo)])
    v = M @ w
    s = size / 2 * radius
    return size / 2 + v[0] * s, size / 2 - v[1] * s, v[2]


def soft_ellipse(size, cx, cy, rx, ry, color, blur, rot=0):
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color)
    if rot:
        lay = lay.rotate(rot, center=(cx, cy), resample=Image.BICUBIC)
    return lay.filter(ImageFilter.GaussianBlur(blur))


def orbit_panel(name, planet_png, moon_pos, moon_r, planet_scale=0.62, offset=(0, 0)):
    W, H = 1600, 1000
    bg = starfield(W, H, 420, seed=hash(name) % 1000)
    pl = Image.open(planet_png)
    s = int(pl.width * planet_scale)
    pl = pl.resize((s, s), Image.LANCZOS)
    bg.alpha_composite(pl, (W // 2 - s // 2 + offset[0], H // 2 - s // 2 + offset[1]))
    m = moon_img(moon_r * 2)
    bg.alpha_composite(m, (moon_pos[0] - moon_r, moon_pos[1] - moon_r))
    bg.convert("RGB").save(OUT / f"{name}-a-orbita.jpg", quality=92)
    return bg


def silhouette(img, size, color=(14, 12, 19)):
    a = img.split()[-1].point(lambda v: 255 if v > 140 else 0)
    bbox = a.getbbox()
    a = a.crop(bbox)
    k = size / max(a.size)
    a = a.resize((max(1, int(a.width * k)), max(1, int(a.height * k))), Image.LANCZOS)
    out = Image.new("RGBA", a.size, color + (0,))
    out.putalpha(a)
    return out


def eclipse_dolinas(base):
    im = base.copy()
    S = im.width
    lon0, lat0, roll = -45, 18, -14
    x, y, z = project(-57.5, 28, lon0, lat0, roll, S)
    im.alpha_composite(soft_ellipse(im.size, x + 10, y + 6, 190, 140, (8, 6, 22, 170), 40))
    # las lentes: agua de cada dolina flotando, con su sombra
    from map_dolinas import DOLINAS
    for lo, la, r in DOLINAS:
        px, py, pz = project(lo, la, lon0, lat0, roll, S)
        rr = r * 9
        im.alpha_composite(soft_ellipse(im.size, px + 8, py + 6, rr * 1.2, rr * 0.5, (2, 8, 20, 150), 4))
        im.alpha_composite(soft_ellipse(im.size, px - 14, py - 22, rr * 1.25, rr * 0.55, (14, 42, 80, 255), 1))
        im.alpha_composite(soft_ellipse(im.size, px - 14, py - 18, rr * 1.1, rr * 0.2, (127, 230, 212, 180), 3))
    return im


def eclipse_dosmares(base):
    im = base.copy()
    S = im.width
    x, y, z = project(-12, 9, -10, 12, 16, S)
    im.alpha_composite(soft_ellipse(im.size, x, y, 260, 200, (6, 6, 22, 150), 50))
    # el mar ligero levantado: una lámina clara sobre el Lago Hondo
    im.alpha_composite(soft_ellipse(im.size, x - 18, y - 30, 210, 150, (150, 220, 190, 120), 6))
    im.alpha_composite(soft_ellipse(im.size, x - 18, y - 30, 210, 150, (210, 255, 230, 0), 0))
    ring = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse([x - 228, y - 198, x + 192, y + 138], outline=(210, 255, 232, 200), width=4)
    im.alpha_composite(ring.filter(ImageFilter.GaussianBlur(2)))
    return im


def eclipse_cintura(base):
    """El agua del estrecho levantada en un arco sobre el cuello, en 3D."""
    from globe import Peanut
    from orbits import RC
    im = base.copy()
    S = im.width
    ext = 2.2
    body = Peanut()

    def scr(p):
        v = RC @ np.asarray(p, float)
        return S / 2 + v[0] / ext * S / 2, S / 2 - v[1] / ext * S / 2, v[2]

    xn = 0.2
    # radio del cuello en esa x
    rn = 0.0
    for r in np.linspace(0.2, 1.2, 400):
        if body.sd(np.array([[xn, r, 0.0]], np.float32))[0] > 0:
            rn = r
            break
    # el arco se coloca en el limbo superior del cuello para que se lea en la silueta
    vdir = RC.T @ np.array([0, 0, 1.0])
    nrm = np.cross([1.0, 0, 0], vdir)
    nrm /= np.linalg.norm(nrm)
    if (RC @ nrm)[1] < 0:
        nrm = -nrm
    nrm = nrm * 0.94 + vdir * 0.34
    nrm /= np.linalg.norm(nrm)
    c = scr([xn, 0, 0])
    im.alpha_composite(soft_ellipse(im.size, c[0], c[1] - 40, 170, 200, (6, 6, 22, 150), 40))
    arc = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(arc)
    pts = []
    for i in range(41):
        t = i / 40
        x = xn - 0.42 + 0.84 * t
        h = 0.04 + 0.5 * math.sin(math.pi * t)
        # el arco nace en cada orilla (radio del cuerpo en esa x) y sube
        rr = 0.0
        for r in np.linspace(0.1, 1.3, 300):
            if body.sd(np.array([[x, *(nrm[1:] * r)]], np.float32))[0] > 0:
                rr = r
                break
        p3 = np.array([x, 0, 0]) + nrm * (rr + h)
        pts.append(scr(p3)[:2])
    for col, w in [((32, 110, 110, 235), 30), ((96, 190, 176, 220), 13), ((215, 250, 240, 230), 4)]:
        d.line(pts, fill=col, width=w, joint="curve")
    im.alpha_composite(arc.filter(ImageFilter.GaussianBlur(0.8)))
    return im


def main():
    OUT.mkdir(exist_ok=True)
    dol = Image.open(WORK / "orbit_dolinas.png")
    cin = Image.open(WORK / "orbit_cintura.png")
    mar = Image.open(WORK / "orbit_dosmares.png")
    orbit_panel("i", WORK / "orbit_dolinas.png", (1290, 760), 34)
    orbit_panel("ii", WORK / "orbit_cintura.png", (1330, 240), 26, planet_scale=0.9)
    orbit_panel("iii", WORK / "orbit_dosmares.png", (360, 230), 38)

    # el eclipse visto desde la órbita (sólo para leer el fenómeno a escala)
    for name, base, fn in (("i", dol, eclipse_dolinas), ("ii", cin, eclipse_cintura), ("iii", mar, eclipse_dosmares)):
        im = fn(base)
        bg = starfield(im.width, im.height, 300, seed=7)
        bg.alpha_composite(im)
        bg.convert("RGB").resize((800, 800), Image.LANCZOS).save(OUT / f"{name}-a-eclipse.jpg", quality=90)

    # comparación a la misma escala (px por unidad de radio)
    unit = 150
    items = [dol.resize((int(1400 * unit / SPHERE_PX_PER_UNIT),) * 2, Image.LANCZOS),
             cin.resize((int(1400 * unit / PEANUT_PX_PER_UNIT),) * 2, Image.LANCZOS),
             mar.resize((int(1400 * unit / SPHERE_PX_PER_UNIT),) * 2, Image.LANCZOS)]
    W, H = 1600, 640
    bg = starfield(W, H, 260, seed=3)
    xs = [270, 800, 1330]
    for x, it in zip(xs, items):
        bg.alpha_composite(it, (x - it.width // 2, H // 2 - it.height // 2))
    bg.convert("RGB").save(OUT / "comparacion-escala.jpg", quality=92)

    # escala de carta: ~60 px por planeta, con su luna y la órbita de la luna
    W, H = 1600, 520
    bg = starfield(W, H, 340, seed=11)
    d = ImageDraw.Draw(bg)
    for x, it, mr in zip(xs, [dol, cin, mar], [7, 6, 8]):
        bb = it.split()[-1].getbbox()
        crop = it.crop(bb)
        k = 64 / max(crop.size)
        sm = crop.resize((int(crop.width * k), int(crop.height * k)), Image.LANCZOS)
        cy = 190
        R = 70
        for a in range(0, 360, 8):
            a0, a1 = math.radians(a), math.radians(a + 4)
            d.line([x + R * math.cos(a0), cy + R * math.sin(a0), x + R * math.cos(a1), cy + R * math.sin(a1)], fill=(220, 220, 235, 150), width=1)
        bg.alpha_composite(sm, (x - sm.width // 2, cy - sm.height // 2))
        m = moon_img(mr * 2)
        bg.alpha_composite(m, (int(x + R * math.cos(math.radians(40))) - mr, int(cy + R * math.sin(math.radians(40))) - mr))
        # silueta en negro a 48 y 24 px sobre papel
        paper = Image.new("RGBA", (200, 90), (236, 233, 242, 255))
        s48 = silhouette(it, 48)
        s24 = silhouette(it, 24)
        paper.alpha_composite(s48, (60 - s48.width // 2, 45 - s48.height // 2))
        paper.alpha_composite(s24, (150 - s24.width // 2, 45 - s24.height // 2))
        bg.alpha_composite(paper, (x - 100, 360))
    bg.convert("RGB").save(OUT / "comparacion-carta.jpg", quality=92)

    # siluetas grandes (prueba de forma sin color)
    W, H = 1600, 420
    paper = Image.new("RGBA", (W, H), (236, 233, 242, 255))
    for x, it in zip(xs, [dol, cin, mar]):
        s = silhouette(it, 300 if it is not cin else 360)
        paper.alpha_composite(s, (x - s.width // 2, H // 2 - s.height // 2))
    paper.convert("RGB").save(OUT / "comparacion-siluetas.png")


if __name__ == "__main__":
    main()
