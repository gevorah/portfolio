"""La Cala Interior · corte de continuidad.

Corte vertical a z = 404 m (por el centro de la poza madre) medido sobre los
dos volúmenes: rompiente.frag (la isla, el alero, la rasa) y cala.frag (la
sala, el jameo, las gradas y sus pozas). Se dibujan las tres mareas.

uso: python3 cala_section.py <corte_rompiente.png> <corte_cala.png>  → img/cala-corte.png
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

r = np.asarray(Image.open(sys.argv[1]).convert("RGB"), np.float32) / 255
c = np.asarray(Image.open(sys.argv[2]).convert("RGB"), np.float32) / 255
H, W = r.shape[:2]                      # x ∈ [−110, 190], y ∈ [−45, 90] (fila 0 = arriba)
X0, X1, Y0, Y1 = -110.0, 190.0, -45.0, 90.0
xs = np.linspace(X0, X1, W)
ys = np.linspace(Y1, Y0, H)
XX, YY = np.meshgrid(xs, ys)

island = r[..., 0] > 0.5
rockC = c[..., 0] > 0.5
floorC = c[..., 1] > 0.5
poolC = c[..., 2] > 0.5
# la costra de las gradas: los 2,5 m bajo su superficie; debajo, la misma roca de la isla
solidC = rockC | floorC
top_of_floor = np.zeros(W, int)
grad = np.zeros_like(floorC)
for j in range(W):
    col = np.nonzero(floorC[:, j])[0]
    if len(col):
        k = col[0]
        grad[k:k + int(2.5 * H / (Y1 - Y0)), j] = floorC[k:k + int(2.5 * H / (Y1 - Y0)), j]
grad &= island
rock = island & solidC & ~grad
air = ~(rock | grad)


def hexc(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255


img = np.zeros((H, W, 3), np.float32)
img[:] = hexc("#0e0c13")
# el mar exterior: bajo −24 siempre; entre −24 y 0 rayado (solo en pleamar)
outside = air & ~poolC
sea_low = outside & (YY < -24)
inter = outside & (YY >= -24) & (YY < 0)
img[sea_low] = hexc("#123c48")
hatch = ((np.arange(W)[None, :] + np.arange(H)[:, None]) % 10) < 2
img[inter] = hexc("#0e0c13")
img[inter & hatch] = hexc("#2c7a7c")
# dentro de la sala: lo que el túnel deja entrar (la marea) y las pozas propias
img[poolC] = hexc("#3f9e98")
img[rock] = hexc("#2b2e3b")
img[grad] = hexc("#d6c3a0")
# estratos sugeridos en la roca
bands = (np.floor((YY + 46) / 3.1) % 2 == 0)
img[rock & bands] = hexc("#262935")

buf = io.BytesIO()
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((W, H)).save(buf, "PNG")
base = base64.b64encode(buf.getvalue()).decode()

SX = W / (X1 - X0)
SY = H / (Y1 - Y0)


def P(x, y):
    return (x - X0) * SX, (Y1 - y) * SY


def lab(x, y, txt, anchor="start", dx=0, dy=0, cls=""):
    px, py = P(x, y)
    return f'<text x="{px + dx:.0f}" y="{py + dy:.0f}" text-anchor="{anchor}" class="lab {cls}">{txt}</text>'


lines = []
for lv, name in ((0, "pleamar · 0 m"), (-12, "media marea · −12 m"), (-24, "bajamar · −24 m")):
    _, py = P(0, lv)
    lines.append(f'<line x1="0" x2="{W}" y1="{py:.0f}" y2="{py:.0f}" class="tide"/>'
                 f'<text x="{W - 8}" y="{py - 6:.0f}" text-anchor="end" class="lab tl">{name}</text>')

labels = [
    lab(-6, 66, "LA ROMPIENTE", "middle", cls="big"),
    lab(-40, -15, "la Bóveda · bajo el alero", "middle"),
    lab(56, 32, "jameo", "middle", dy=-6),
    lab(84, 10, "LA CALA INTERIOR", "middle", cls="big"),
    lab(110, -4, "las Gradas", "start", dx=6),
    lab(128, 4, "manantial", "start", dx=6),
    lab(66, -30, "poza madre", "middle", dy=6),
    lab(172, -34, "bahía", "middle"),
]
mark_tunnel = (f'<path d="M{P(10, -17)[0]:.0f} {P(10, -17)[1]:.0f} C {P(28, -24)[0]:.0f} {P(28, -24)[1]:.0f}, '
               f'{P(36, -22)[0]:.0f} {P(36, -22)[1]:.0f}, {P(46, -20)[0]:.0f} {P(46, -20)[1]:.0f}" class="tun"/>'
               + lab(26, -36, "túnel (corte oblicuo)", "middle"))

html = f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<style>
html,body{{margin:0;background:#0e0c13;width:{W}px;height:{H + 60}px;overflow:hidden}}
.w{{position:absolute;left:0;top:30px;width:{W}px;height:{H}px}}
svg{{position:absolute;left:0;top:0}}
.lab{{font:400 15px 'JetBrains Mono',monospace;fill:#e9e6f2;paint-order:stroke;stroke:#0e0c13;stroke-width:4px}}
.big{{font:600 19px 'Space Grotesk',sans-serif;letter-spacing:.14em}}
.tl{{fill:#79c9b8;font-size:13px}}
.tide{{stroke:#79c9b8;stroke-width:1;stroke-dasharray:4 5;opacity:.7}}
.tun{{fill:none;stroke:#efb68c;stroke-width:2;stroke-dasharray:3 5}}
</style></head><body><div class="w"><img src="data:image/png;base64,{base}" width="{W}" height="{H}">
<svg width="{W}" height="{H}">{''.join(lines)}{mark_tunnel}{''.join(labels)}</svg></div></body></html>"""
out = os.path.join(WORK, "cala-corte.html")
open(out, "w").write(html)
subprocess.run(["node", os.path.join(SRC, "render.mjs"), out, os.path.join(IMG, "cala-corte.png"), str(W), str(H + 60), "1"],
               check=True, env={**os.environ, "PW_PATH": os.environ.get("PW_PATH", "/opt/node-tools/node_modules/playwright")})
