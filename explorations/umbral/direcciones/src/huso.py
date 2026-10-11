"""B · El Huso — una silueta singular sin formaciones verticales.

Umbral gira tan rápido que se ha achatado como una lente. El mar se acumula
en el ecuador, donde el planeta es más ancho, y deja al aire dos tierras
polares de roca rosada y hielo. Desde la costa polar el mar parece subir
hacia el horizonte: el océano está cuesta arriba. Las estrellas dejan
estela porque el cielo gira deprisa.
"""

import math
import random
from pathlib import Path

from common import H, W, filters, grain, stars
from paint import f, smooth, svg_to_png, write_svg

OUT = Path(__file__).resolve().parent.parent / "img"


def orbital():
    rng = random.Random(3)
    CX, CY, RX, RY, ROT = 760, 520, 420, 262, -18
    defs = filters(f"""
<linearGradient id="shade" x1="{CX - 300}" y1="{CY - 250}" x2="{CX + 330}" y2="{CY + 230}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#05040c" stop-opacity="0"/><stop offset="0.35" stop-color="#05040c" stop-opacity="0.12"/>
  <stop offset="0.55" stop-color="#05040c" stop-opacity="0.6"/><stop offset="0.7" stop-color="#05040c" stop-opacity="0.9"/>
  <stop offset="1" stop-color="#05040c" stop-opacity="0.97"/>
</linearGradient>
<radialGradient id="limbdark" cx="{CX}" cy="{CY}" r="{RX}" gradientUnits="userSpaceOnUse" gradientTransform="translate({CX} {CY}) rotate({ROT}) scale(1 {RY / RX}) translate({-CX} {-CY})">
  <stop offset="0.7" stop-color="#05040c" stop-opacity="0"/><stop offset="1" stop-color="#05040c" stop-opacity="0.45"/>
</radialGradient>
<linearGradient id="sea" x1="0" y1="{CY - 110}" x2="0" y2="{CY + 110}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#2c5bb0"/><stop offset="0.5" stop-color="#173c86"/><stop offset="1" stop-color="#2a56a8"/>
</linearGradient>
<linearGradient id="land" x1="0" y1="{CY - RY}" x2="0" y2="{CY + RY}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#eef0f4"/><stop offset="0.12" stop-color="#cbb3b0"/><stop offset="0.3" stop-color="#b18f8d"/>
  <stop offset="0.7" stop-color="#b18f8d"/><stop offset="0.88" stop-color="#cbb3b0"/><stop offset="1" stop-color="#eef0f4"/>
</linearGradient>
<radialGradient id="moon" cx="0.35" cy="0.35" r="0.8">
  <stop offset="0" stop-color="#e9e3f2"/><stop offset="0.5" stop-color="#a9a1bf"/><stop offset="1" stop-color="#3f3a55"/>
</radialGradient>
<clipPath id="body"><ellipse cx="{CX}" cy="{CY}" rx="{RX}" ry="{RY}" transform="rotate({ROT} {CX} {CY})"/></clipPath>
""")
    b = [f'<rect width="{W}" height="{H}" fill="#0e0c13"/>', stars(rng, 420, H, avoid=[(CX, CY, RX + 40)])]
    # halo atmosférico fino
    b.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{RX + 8}" ry="{RY + 8}" fill="none" stroke="#9bb7ff" stroke-width="10" opacity="0.35" '
             f'filter="url(#b8)" transform="rotate({ROT} {CX} {CY})"/>')
    g = [f'<g clip-path="url(#body)"><g transform="rotate({ROT} {CX} {CY})">',
         f'<rect x="{CX - RX - 20}" y="{CY - RY - 20}" width="{2 * RX + 40}" height="{2 * RY + 40}" fill="url(#land)"/>']
    # mar ecuatorial: costa recortada con golfos y fiordos que miran a los polos
    top, bot = [], []
    for i in range(61):
        x = CX - RX - 20 + i * (2 * RX + 40) / 60
        sag = 46 * (1 - ((x - CX) / RX) ** 2)
        top.append((x, CY - 96 - 22 * math.sin(i * 0.21) - 9 * math.sin(i * 0.53 + 1) + sag))
        bot.append((x, CY + 98 + 20 * math.sin(i * 0.19 + 2) + 8 * math.sin(i * 0.47) + sag * 0.6))
    sea = smooth(top + bot[::-1], tension=0.4)
    g.append(f'<path d="{sea}" fill="none" stroke="#efe2d6" stroke-width="6" opacity="0.6" filter="url(#roughS)"/>')
    g.append(f'<path d="{sea}" fill="url(#sea)" filter="url(#roughS)"/>')
    # oleaje largo y niebla ecuatorial
    for k in range(9):
        y = CY - 70 + k * 18
        pts = [(x, y + 4 * math.sin(x * 0.01 + k) + 40 * (1 - ((x - CX) / RX) ** 2)) for x in range(CX - RX, CX + RX + 1, 30)]
        g.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#8fb4ff" stroke-width="{1.2 + (k % 3) * 0.5:.1f}" opacity="0.18"/>')
    # nubes: bandas finas a lo largo de los paralelos
    for (dy, x0, x1, op) in [(-150, -300, 120, 0.5), (-60, 0, 380, 0.35), (10, -380, -60, 0.3), (130, -120, 300, 0.45), (190, 120, 380, 0.4)]:
        pts = [(CX + x, CY + dy + 40 * (1 - (x / RX) ** 2) + 4 * math.sin(x * 0.03)) for x in range(x0, x1, 20)]
        g.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#f4f6ff" stroke-width="7" opacity="{op}" stroke-linecap="round" filter="url(#b3)"/>')
    # fiordos y valles de hielo que bajan de los polos
    for i in range(9):
        x = CX - RX * 0.8 + i * RX * 1.6 / 8 + rng.uniform(-14, 14)
        for sgn in (-1, 1):
            y0 = CY + sgn * (RY * 0.86)
            y1 = CY + sgn * (100 + rng.uniform(0, 30))
            g.append(f'<path d="M{f(x)},{f(y0)} q{f(rng.uniform(-14, 14))},{f((y1 - y0) * 0.5)} {f(rng.uniform(-10, 10))},{f(y1 - y0)}" '
                     f'stroke="#8e7682" stroke-width="{rng.uniform(1.5, 3.5):.1f}" fill="none" opacity="0.55"/>')
    # casquetes polares
    for sgn in (-1, 1):
        cap = [(CX - RX, CY + sgn * RY * 0.92), (CX - RX * 0.5, CY + sgn * (RY * 0.78 + 8 * math.sin(3))), (CX - RX * 0.1, CY + sgn * RY * 0.74),
               (CX + RX * 0.3, CY + sgn * RY * 0.8), (CX + RX * 0.7, CY + sgn * RY * 0.76), (CX + RX, CY + sgn * RY * 0.9),
               (CX + RX, CY + sgn * (RY + 30)), (CX - RX, CY + sgn * (RY + 30))]
        g.append(f'<path d="{smooth(cap, tension=0.4)}" fill="#f2f4f7" opacity="0.92" filter="url(#roughS)"/>')
    g.append("</g>")
    # luz y sombra encima de todo (no rota con el cuerpo)
    g.append(f'<rect width="{W}" height="{H}" fill="url(#limbdark)"/>')
    g.append(f'<rect width="{W}" height="{H}" fill="url(#shade)"/>')
    g.append(f'<ellipse cx="{CX - 200}" cy="{CY - 130}" rx="120" ry="60" fill="#ffffff" opacity="0.1" filter="url(#b20)" transform="rotate({ROT} {CX} {CY})"/>')
    g.append("</g>")
    b += g
    b.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{RX}" ry="{RY}" fill="none" stroke="#c9d8ff" stroke-width="1.6" opacity="0.5" '
             f'transform="rotate({ROT} {CX} {CY})" stroke-dasharray="{2 * math.pi * RX * 0.38} 9999" stroke-dashoffset="{2 * math.pi * RX * 0.62}"/>')
    b.append('<circle cx="1330" cy="250" r="40" fill="url(#moon)"/>')
    b.append(grain(0.05))
    return b, defs


def key_art():
    rng = random.Random(7)
    HZ = 230   # el horizonte está alto y se curva hacia arriba en los bordes: el mar sube
    defs = filters(f"""
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#0c0d24"/><stop offset="0.7" stop-color="#2d3168"/><stop offset="1" stop-color="#8d86b8"/>
</linearGradient>
<linearGradient id="sea" x1="0" y1="{HZ}" x2="0" y2="760" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#9fb6e6"/><stop offset="0.08" stop-color="#4f73c2"/><stop offset="0.45" stop-color="#1f428e"/>
  <stop offset="1" stop-color="#132a63"/>
</linearGradient>
<linearGradient id="sand" x1="0" y1="700" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#c9aba3"/><stop offset="1" stop-color="#8f7177"/>
</linearGradient>
<radialGradient id="moon" cx="0.35" cy="0.35" r="0.8">
  <stop offset="0" stop-color="#eef0f6"/><stop offset="0.6" stop-color="#b3b6cf"/><stop offset="1" stop-color="#6b6c8c"/>
</radialGradient>
""")
    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']
    # estrellas con estela: el cielo gira deprisa
    for _ in range(170):
        x, y = rng.uniform(0, W), rng.uniform(0, HZ - 30)
        ln = rng.uniform(6, 22)
        b.append(f'<path d="M{f(x)},{f(y)} q{f(ln * 0.5)},{f(-ln * 0.08)} {f(ln)},0" stroke="#e8ebff" stroke-width="{rng.choice([0.6, 0.8, 1.1])}" '
                 f'fill="none" opacity="{rng.uniform(0.25, 0.75):.2f}" stroke-linecap="round"/>')
    b.append('<circle cx="1250" cy="120" r="34" fill="url(#moon)"/>')
    # el mar cuesta arriba: una superficie que sube hasta el horizonte alto
    sea_top = [(x, HZ + 40 - 110 * ((x - 800) / 800) ** 2) for x in range(-40, W + 41, 40)]
    b.append(f'<path d="M-40,{H} L{" L".join(f"{f(x)},{f(y)}" for x, y in sea_top)} L{W + 40},{H} Z" fill="url(#sea)"/>')
    # bandas de mar de fondo: se comprimen al subir hacia el horizonte
    for k in range(34):
        t = k / 33
        y = HZ + 6 + (t ** 2.2) * 520
        amp = 1 + t * 7
        bowl = (40 - 110 * ((x0 := 0) or 0))
        pts = [(x, y + 40 * (1 - t) + amp * math.sin(x * (0.004 + 0.004 * (1 - t)) + k * 1.3) - 110 * (1 - t) ** 1.5 * ((x - 800) / 800) ** 2)
               for x in range(-40, W + 41, 40)]
        b.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="{"#c9dcff" if k % 4 == 0 else "#7c9ee6"}" '
                 f'stroke-width="{0.6 + t * 2.4:.1f}" opacity="{0.18 + t * 0.2:.2f}"/>')
    # islas lejanas colgadas sobre la pendiente del mar: están más arriba que nosotros
    for (x, y, w, h) in [(200, 236, 90, 12), (520, 300, 110, 14), (980, 290, 70, 9), (1330, 250, 150, 20), (1450, 210, 60, 8)]:
        b.append(f'<path d="M{x - w / 2},{y} q{w * 0.25},{-h} {w * 0.5},{-h * 0.8} t{w * 0.5},{h * 0.8} Z" fill="#5b4f73" opacity="0.9"/>')
        b.append(f'<rect x="{x - w / 2 - 6}" y="{y - 1}" width="{w + 12}" height="2.4" fill="#e8f0ff" opacity="0.6"/>')
    b.append(f'<path d="{smooth([(x, y + 4) for x, y in sea_top], closed=False)}" fill="none" stroke="#d6e0fb" stroke-width="22" opacity="0.4" filter="url(#b20)"/>')
    # rompientes largas que bajan la pendiente hacia la orilla
    for (y, x0, x1) in [(560, 200, 700), (610, 820, 1400), (660, 80, 520), (640, 1100, 1560)]:
        pts = [(x, y + 6 * math.sin(x * 0.02)) for x in range(x0, x1, 20)]
        b.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#e6eeff" stroke-width="3" opacity="0.55"/>')
    # rompiente en la orilla y lámina de agua sobre la arena
    shore = [(x, 720 + 18 * math.sin(x * 0.004 + 1) + 8 * math.sin(x * 0.013)) for x in range(-40, W + 41, 40)]
    b.append(f'<path d="M-40,{H} L{" L".join(f"{f(x)},{f(y)}" for x, y in shore)} L{W + 40},{H} Z" fill="url(#sand)"/>')
    b.append(f'<path d="{smooth(shore, closed=False)}" fill="none" stroke="#f3f6ff" stroke-width="5" opacity="0.8" filter="url(#b1)"/>')
    b.append(f'<path d="{smooth([(x, y + 14) for x, y in shore], closed=False)}" fill="none" stroke="#9fb6e6" stroke-width="14" opacity="0.35" filter="url(#b3)"/>')
    for k in range(5):
        pts = [(x, y + 40 + k * 26 + 4 * math.sin(x * 0.01 + k)) for x, y in shore]
        b.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#e7d3cc" stroke-width="1.4" opacity="{0.35 - k * 0.05:.2f}"/>')
    # cantos rodados redondeados por el oleaje y hielo varado
    for (x, y, rx, ry, col) in [(220, 880, 70, 34, "#7d6670"), (310, 905, 40, 20, "#937a83"), (1260, 860, 90, 40, "#76606a"),
                                (1380, 900, 46, 22, "#8c737c"), (760, 940, 30, 12, "#937a83"), (1060, 790, 36, 14, "#e9eef6")]:
        b.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{col}"/>')
        b.append(f'<ellipse cx="{x - rx * 0.25}" cy="{y - ry * 0.35}" rx="{rx * 0.55}" ry="{ry * 0.35}" fill="#ffffff" opacity="0.18"/>')
        b.append(f'<ellipse cx="{x + 6}" cy="{y + ry * 0.9}" rx="{rx * 1.05}" ry="{ry * 0.25}" fill="#4e3d47" opacity="0.4"/>')
    # escala: una figura frente al mar que sube
    fx, fy = 640, 830
    b.append(f'<path d="M{fx - 4},{fy} L{fx - 2.6},{fy - 15} Q{fx},{fy - 22} {fx + 2.6},{fy - 15} L{fx + 4},{fy} Z" fill="#241c2a"/>'
             f'<circle cx="{fx}" cy="{fy - 24}" r="3.2" fill="#241c2a"/><ellipse cx="{fx + 10}" cy="{fy + 2}" rx="12" ry="2.4" fill="#241c2a" opacity="0.35"/>')
    b.append(grain(0.05))
    return b, defs


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, fn in (("b-huso-clave", key_art), ("b-huso-orbita", orbital)):
        body, defs = fn()
        p = write_svg(name, W, H, "".join(body), defs)
        svg_to_png(p, OUT / f"{name}.png", W, H)
