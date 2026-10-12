"""Estudio IV · Continuidad geográfica.

La planta sale de la misma geometría que pintan las vistas II y III: se mide
la altura del modelo cada metro (shader/rompiente.frag, modo DBG = −2) y se
trazan dos costas, la de pleamar (0 m) y la de bajamar (−24 m). Lo que queda
entre ambas es lo que la marea esconde y revela.

uso: python3 continuity.py <height.png>   → img/iv-continuidad.png
"""

import base64
import io
import os
import subprocess
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(ROOT, "work")
IMG = os.path.join(ROOT, "img")

raw = np.asarray(Image.open(sys.argv[1]).convert("RGB"), np.float32) / 255.0
v = raw[..., 0] + raw[..., 1] / 255.0
H = v * 200.0 - 60.0                      # altura en metros
# la fila 0 del PNG ya es el norte (z = 900)
N = H.shape[0]                            # 1 px = 1 m; x ∈ [−450, 450], z ∈ [0, 900]


def hexc(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255


# --- relleno -----------------------------------------------------------------
img = np.zeros((N, N, 3), np.float32)
deep, mid, tidal, land, high = hexc("#0d2f3a"), hexc("#17505c"), hexc("#3f9e98"), hexc("#5d6878"), hexc("#8a9585")
d = np.clip((-24 - H) / 22, 0, 1)[..., None]
img[:] = mid * (1 - d) + deep * d
it = ((H > -24) & (H <= 0))[..., None]
img = np.where(it, tidal * 0.55 + mid * 0.45, img)
# rayado diagonal en la franja intermareal: «solo existe en bajamar»
yy, xx = np.mgrid[0:N, 0:N]
hatch = (((xx + yy) % 9) < 2)[..., None] & it
img = np.where(hatch, tidal * 0.9, img)
up = (H > 0)[..., None]
t = np.clip(H / 90, 0, 1)[..., None]
img = np.where(up, land * (1 - t) + high * t, img)
# sombreado suave de relieve
gy, gx = np.gradient(np.where(H > 0, H, 0))
hs = np.clip(1 + (-gx + gy) * 0.05, 0.75, 1.2)[..., None]
img = np.where(up, img * hs, img)

buf = io.BytesIO()
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(buf, "PNG")
base = base64.b64encode(buf.getvalue()).decode()


# --- costas: marching squares → segmentos SVG -------------------------------
def contour(level, step=2):
    A = H[::step, ::step] - level
    s = []
    h, w = A.shape
    for j in range(h - 1):
        a, b, c, e = A[j, :-1], A[j, 1:], A[j + 1, 1:], A[j + 1, :-1]
        for i in np.nonzero((np.sign(a) != np.sign(b)) | (np.sign(b) != np.sign(c)) |
                            (np.sign(c) != np.sign(e)) | (np.sign(e) != np.sign(a)))[0]:
            pts = []
            corners = [(i, j, a[i]), (i + 1, j, b[i]), (i + 1, j + 1, c[i]), (i, j + 1, e[i])]
            for k in range(4):
                (x0, y0, v0), (x1, y1, v1) = corners[k], corners[(k + 1) % 4]
                if (v0 < 0) != (v1 < 0):
                    f = v0 / (v0 - v1)
                    pts.append(((x0 + (x1 - x0) * f) * step, (y0 + (y1 - y0) * f) * step))
            if len(pts) >= 2:
                s.append(f"M{pts[0][0]:.1f} {pts[0][1]:.1f}L{pts[1][0]:.1f} {pts[1][1]:.1f}")
            if len(pts) == 4:
                s.append(f"M{pts[2][0]:.1f} {pts[2][1]:.1f}L{pts[3][0]:.1f} {pts[3][1]:.1f}")
    return "".join(s)


hw = contour(0.0)
lw = contour(-24.0)


def P(x, z):
    return x + 450, 900 - z


cam = P(-200, 220)
# cono de visión (FOV vertical 52°, 16:10 → ±37,5° en horizontal) hacia (10, 430)
import math
fw = math.atan2(430 - 220, 10 + 200)
half = math.atan(math.tan(math.radians(26)) * 1.6)
cone = []
for a in (fw - half, fw + half):
    ex, ez = -200 + 700 * math.cos(a), 220 + 700 * math.sin(a)
    cone.append(P(ex, ez))

labels = [
    # (x, z, texto, anclaje, dx, dy)
    (-60, 400, "LA ROMPIENTE", "end", -14, 0, "big"),
    (-60, 400, "alero de 54 m sobre la rasa", "end", -14, 16, ""),
    (-2, 350, "cueva · la Bóveda", "start", 16, 34, ""),
    (-70, 300, "canal", "end", -10, 6, ""),
    (-92, 482, "farallones", "end", -22, -4, ""),
    (-60, 650, "barra de arena · tómbolo", "end", -10, 0, ""),
    (160, 840, "isleta", "start", 72, 4, ""),
    (-120, 360, "rasa mareal", "end", 0, 0, ""),
    (300, 520, "bahía", "start", 0, 0, ""),
]

lab_svg = []
for (x, z, txt, anc, dx, dy, cls) in labels:
    px, pz = P(x, z)
    lab_svg.append(f'<text x="{px + dx:.0f}" y="{pz + dy:.0f}" text-anchor="{anc}" class="lab {cls}">{txt}</text>')

marks = []
for (x, z) in [(-58, 432), (-92, 482), (-130, 542)]:
    px, pz = P(x, z)
    marks.append(f'<circle cx="{px}" cy="{pz}" r="4" class="stk"/>')
cx_, cz_ = P(-2, 350)
marks.append(f'<circle cx="{cx_}" cy="{cz_}" r="7" class="cave"/>')

html = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<style>
html,body{{margin:0;background:#0e0c13;width:1600px;height:1000px;overflow:hidden;color:#cfd3e6;font-family:'Space Grotesk',sans-serif}}
.map{{position:absolute;left:50px;top:50px;width:900px;height:900px}}
.map svg{{position:absolute;left:0;top:0}}
.hw{{fill:none;stroke:#f1ede4;stroke-width:1.6}}
.lw{{fill:none;stroke:#79c9b8;stroke-width:1.4;stroke-dasharray:5 4}}
.lab{{font:500 13px 'JetBrains Mono',monospace;fill:#e9e6f2;paint-order:stroke;stroke:#0e0c13;stroke-width:3px;letter-spacing:.02em}}
.big{{font:600 17px 'Space Grotesk',sans-serif;letter-spacing:.12em}}
.cone{{fill:rgba(239,182,140,.10);stroke:#efb68c;stroke-width:1;stroke-dasharray:2 4}}
.cam{{fill:#efb68c}}
.stk{{fill:#e9e6f2;stroke:#0e0c13;stroke-width:1.5}}
.cave{{fill:none;stroke:#7ff0d8;stroke-width:2}}
.side{{position:absolute;left:1010px;top:70px;width:540px}}
h1{{font:600 15px 'Space Grotesk';letter-spacing:.24em;margin:0 0 6px;color:#9aa6d8}}
h2{{font:600 34px 'Space Grotesk';margin:0 0 26px;color:#f1ede4;letter-spacing:.01em}}
.k{{display:flex;align-items:center;gap:14px;margin:14px 0;font-size:16px;line-height:1.35}}
.sw{{flex:0 0 38px;height:18px;border-radius:2px}}
p{{font-size:16px;line-height:1.55;color:#b8bdd6;margin:22px 0 0}}
.mono{{font:400 13px 'JetBrains Mono';color:#8c90aa;letter-spacing:.04em}}
</style></head><body>
<div class="map"><img src="data:image/png;base64,{base}" width="900" height="900">
<svg width="900" height="900" viewBox="0 0 900 900">
<path class="lw" d="{lw}"/><path class="hw" d="{hw}"/>
<polygon class="cone" points="{cam[0]},{cam[1]} {cone[0][0]:.0f},{cone[0][1]:.0f} {cone[1][0]:.0f},{cone[1][1]:.0f}"/>
<circle class="cam" cx="{cam[0]}" cy="{cam[1]}" r="6"/>
<text x="{cam[0] - 10}" y="{cam[1] + 24}" text-anchor="end" class="lab">cámara · vistas II y III</text>
{''.join(marks)}{''.join(lab_svg)}
<g transform="translate(840,60)"><path d="M0 18 L8 -6 L16 18 L8 12Z" fill="#e9e6f2"/><text x="8" y="36" text-anchor="middle" class="lab">N</text></g>
<g transform="translate(40,860)"><rect width="100" height="4" fill="#e9e6f2"/><rect x="50" width="50" height="4" fill="#0e0c13" stroke="#e9e6f2"/>
<text x="0" y="-8" class="lab">0</text><text x="100" y="-8" class="lab" text-anchor="middle">100 m</text></g>
</svg></div>
<div class="side">
<h1>UMBRAL · ESTUDIO IV</h1>
<h2>Un solo lugar, dos costas</h2>
<div class="k"><svg width="38" height="18"><line x1="0" y1="9" x2="38" y2="9" stroke="#f1ede4" stroke-width="2"/></svg>Costa de pleamar · nivel 0 m</div>
<div class="k"><svg width="38" height="18"><line x1="0" y1="9" x2="38" y2="9" stroke="#79c9b8" stroke-width="2" stroke-dasharray="5 4"/></svg>Costa de bajamar · nivel −24 m</div>
<div class="k"><div class="sw" style="background:repeating-linear-gradient(135deg,#3f9e98 0 3px,#2c7a7c 3px 9px)"></div>Franja intermareal: sumergida en pleamar, transitable en bajamar</div>
<div class="k"><div class="sw" style="background:#5d6878"></div>Tierra firme · la isla y sus farallones</div>
<div class="k"><div class="sw" style="background:#0d2f3a"></div>Mar que nunca se retira: canales y océano</div>
<p>La Rompiente es la costa oeste del brazo de la isla. Al pie del alero, el mar talló una rasa de 60 a 110 m de ancho que la pleamar cubre con 18 m de agua. En bajamar aparece entera: une la isla con los tres farallones y, a través de la barra de arena, con la isleta.</p>
<p>Un canal cruza la rasa y conserva agua incluso en bajamar; conduce a la boca de la cueva, que atraviesa el brazo por debajo del alero hasta la bahía. En pleamar la boca queda casi sumergida: solo asoma una ranura oscura.</p>
<p class="mono">Planta medida sobre el mismo modelo que generan las vistas II y III · 1 px = 1 m</p>
</div>
</body></html>"""

os.makedirs(WORK, exist_ok=True)
out_html = os.path.join(WORK, "continuidad.html")
open(out_html, "w").write(html)
subprocess.run(["node", os.path.join(SRC, "render.mjs"), out_html, os.path.join(IMG, "iv-continuidad.png"), "1600", "1000", "1"],
               check=True, env={**os.environ, "PW_PATH": "/opt/node-tools/node_modules/playwright"})
