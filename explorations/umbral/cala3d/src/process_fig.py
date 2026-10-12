"""Lámina de proceso: el suelo heredado (frentes de colada) y las Gradas tras la simulación.

Salida: img/proceso-gradas.png (dos plantas sombreadas del anfiteatro, misma luz).
"""

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
IMG = os.path.join(ROOT, "img")
os.makedirs(IMG, exist_ok=True)

h0 = np.load(os.path.join(WORK, "gours_h0.npy")).astype(np.float64)
h = np.load(os.path.join(WORK, "gours_h.npy")).astype(np.float64)
w = np.load(os.path.join(WORK, "gours_w.npy")).astype(np.float64)
q = np.load(os.path.join(WORK, "gours_q.npy")).astype(np.float64)
CELL, EXT = 0.25, 64.0
# recorte: el anfiteatro (x de −6 a 62, y de −6 a 62)
i0, i1 = int((-6 + EXT) / CELL), int((62 + EXT) / CELL)
crop = np.s_[i0:i1, i0:i1]


def shade(H, water=None, dep=None, flow=None):
    gy, gx = np.gradient(H, CELL)
    n = np.stack([-gx, -gy, np.ones_like(H)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.55, -0.45, 0.70])
    L /= np.linalg.norm(L)
    lit = np.clip(n @ L, 0, 1)
    base = np.array([0.17, 0.17, 0.19])
    col = base * (0.35 + 0.9 * lit[..., None])
    if dep is not None:
        t = np.clip(dep / 0.6, 0, 1)[..., None]
        trav = np.array([0.80, 0.72, 0.56]) * (0.45 + 0.75 * lit[..., None])
        col = col * (1 - t) + trav * t
    if water is not None:
        d = water - H
        wm = np.clip(d / 0.12, 0, 1)[..., None]
        wc = np.array([0.36, 0.30, 0.10]) * 0.7 + 0.3 * np.array([0.15, 0.30, 0.32])
        col = col * (1 - 0.8 * wm) + wc * 0.8 * wm
        sea = (H < -24.0)[..., None]
        col = np.where(sea, np.array([0.05, 0.13, 0.15]), col)
    if flow is not None:
        f = np.clip(np.log10(flow / flow.max() * 1e5 + 1) / 5, 0, 1)[..., None] ** 2
        col = col * (1 - 0.25 * f) + np.array([0.95, 0.97, 1.0]) * 0.25 * f
    return (np.clip(col[::-1], 0, 1) * 255).astype(np.uint8)


a = shade(h0[crop])
b = shade(h[crop], w[crop], (h - h0)[crop], q[crop])
S = 620
ia = Image.fromarray(a).resize((S, S), Image.LANCZOS)
ib = Image.fromarray(b).resize((S, S), Image.LANCZOS)
W, H = S * 2 + 60, S + 70
canvas = Image.new("RGB", (W, H), (14, 12, 19))
canvas.paste(ia, (20, 50))
canvas.paste(ib, (S + 40, 50))
d = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
except OSError:
    font = ImageFont.load_default()
d.text((20, 18), "1 · suelo heredado: frentes lobulados de coladas", fill=(220, 218, 230), font=font)
d.text((S + 40, 18), "2 · tras 1200 pasos de llenado, desborde y precipitación", fill=(220, 218, 230), font=font)
# escala: 10 m
px = S / ((i1 - i0) * CELL) * 10
for x0 in (20, S + 40):
    d.rectangle([x0 + 16, 50 + S - 26, x0 + 16 + px, 50 + S - 22], fill=(233, 230, 242))
    d.text((x0 + 16, 50 + S - 46), "10 m", fill=(233, 230, 242), font=font)
canvas.save(os.path.join(IMG, "proceso-gradas.png"))
print("ok")
