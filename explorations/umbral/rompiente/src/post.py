"""Acabado de las vistas II y III.

1. Reduce el render (supermuestreado) a 1600×1000.
2. Pinta encima un filtro de Kuwahara suave: agrupa el detalle en manchas de
   color, como pinceladas, para que el blockout no se lea como CG.
3. Añade lo que no es geografía: aves sobre los farallones (en ambas mareas)
   y, solo en bajamar, una figura con farol camino de la cueva: la escala.

uso: python3 post.py <render.png> <height.png> <L> <salida.png>
"""

import math
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

src, hpath, L, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
W, H = 1600, 1000
CAM, TGT, FOV = np.array([-200.0, 7, 220]), np.array([10.0, 30, 430]), 52.0

img = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
a = np.asarray(img, np.float32) / 255


def box(x, r):
    """Media en ventana (2r+1)² con imagen integral."""
    p = np.pad(x, ((r + 1, r), (r + 1, r)) + ((0, 0),) * (x.ndim - 2), mode="edge")
    c = p.cumsum(0).cumsum(1)
    k = 2 * r + 1
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def kuwahara(a, r):
    lum = a @ np.array([0.3, 0.59, 0.11], np.float32)
    m = box(a, r)
    m2 = box(lum[..., None] ** 2, r)[..., 0]
    ml = box(lum[..., None], r)[..., 0]
    var = m2 - ml ** 2
    best = None
    bestv = None
    for dy in (-r, r):
        for dx in (-r, r):
            mv = np.roll(np.roll(m, dy, 0), dx, 1)
            vv = np.roll(np.roll(var, dy, 0), dx, 1)
            if best is None:
                best, bestv = mv.copy(), vv.copy()
            else:
                sel = vv < bestv
                best[sel] = mv[sel]
                bestv[sel] = vv[sel]
    return best


k = kuwahara(a, 3)
a = a * 0.45 + k * 0.55
img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


# --- proyección (misma cámara que el shader) ---------------------------------
fw = (TGT - CAM) / np.linalg.norm(TGT - CAM)
rt = np.cross([0, 1, 0], fw)
rt /= np.linalg.norm(rt)
up = np.cross(fw, rt)
foc = 0.5 / math.tan(math.radians(FOV) / 2)


def proj(p):
    d = np.array(p, float) - CAM
    z = d @ fw
    return W / 2 + (d @ rt) / z * foc * H, H / 2 - (d @ up) / z * foc * H, z


hraw = np.asarray(Image.open(hpath).convert("RGB"), np.float32) / 255
hgt = (hraw[..., 0] + hraw[..., 1] / 255) * 200 - 60


def ground(x, z):
    return float(hgt[int(round(900 - z)), int(round(x + 450))])


d = ImageDraw.Draw(img, "RGBA")

# aves: un pequeño grupo sobre los farallones
rng = np.random.default_rng(4)
for i in range(9):
    x, y, _ = proj((-110 + rng.normal(0, 18), 62 + rng.normal(0, 9), 500 + rng.normal(0, 25)))
    s = 2.2 + rng.random() * 1.6
    d.line([(x - s, y - s * 0.5), (x, y), (x + s, y - s * 0.6)], fill=(232, 228, 238, 230), width=1)

if L < -10:
    # figura con farol: camina sobre la rasa hacia la boca de la cueva
    for (fx, fz) in [(-40, 330), (-45, 325), (-36, 338), (-50, 318), (-30, 342)]:
        g = ground(fx, fz)
        if -19.5 < g < -14.0:
            break
    bx, by, z = proj((fx, g, fz))
    hpx = 1.8 / z * foc * H                       # altura de una persona en píxeles
    hp = max(hpx * 1.25, 13.0)                    # se exagera un poco para que se lea
    w = hp * 0.28
    body = [(bx - w, by), (bx - w * 0.7, by - hp * 0.78), (bx, by - hp * 0.86), (bx + w * 0.7, by - hp * 0.78), (bx + w, by)]
    d.polygon(body, fill=(24, 22, 30, 255))
    d.ellipse([bx - w * 0.55, by - hp * 1.08, bx + w * 0.55, by - hp * 0.84], fill=(24, 22, 30, 255))
    # farol: la única luz cálida dentro de la sombra
    lx, ly = bx + w * 1.4, by - hp * 0.45
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r_, al in ((22, 40), (11, 80), (5, 170)):
        gd.ellipse([lx - r_, ly - r_, lx + r_, ly + r_], fill=(255, 196, 130, al))
    glow = glow.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    d.ellipse([lx - 1.6, ly - 1.6, lx + 1.6, ly + 1.6], fill=(255, 236, 200, 255))
    print("figura en", fx, fz, "suelo", round(g, 1), "px", round(bx), round(by), "altura real px", round(hpx, 1))

img.save(out)
