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
from PIL import Image, ImageDraw

from paintfx import figure, paint

src, hpath, L, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
W, H = 1600, 1000
CAM, TGT, FOV = np.array([-200.0, 7, 220]), np.array([10.0, 30, 430]), 52.0

img = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)


img = paint(img)


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
    img = figure(img, bx, by, max(hpx * 1.25, 13.0))   # se exagera un poco para que se lea
    print("figura en", fx, fz, "suelo", round(g, 1), "px", round(bx), round(by), "altura real px", round(hpx, 1))

img.save(out)
