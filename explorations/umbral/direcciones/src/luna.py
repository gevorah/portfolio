"""C · La Luna de Agua — la que cuestiona la premisa.

¿Y si el mar ya no está en el planeta? Umbral fue oceánico; su mar se
levantó entero y hoy orbita como una luna de agua, con su fauna dentro.
Abajo queda un fondo marino seco: llanuras de sal, arrecifes muertos,
fosas vacías. Cuando la luna de agua tapa la estrella, su sombra no es
negra sino azul y llena de cáusticas: durante unos minutos el planeta
vuelve a estar «bajo el agua», y lo que quedó en el fondo despierta.
"""

import math
import random
from pathlib import Path

from common import H, W, filters, grain, stars
from paint import blob, f, smooth, svg_to_png, write_svg

OUT = Path(__file__).resolve().parent.parent / "img"

CAUSTIC = """
<filter id="caustic" filterUnits="userSpaceOnUse" x="0" y="0" width="1600" height="1000">
  <feTurbulence type="turbulence" baseFrequency="{bf}" numOctaves="2" seed="{seed}" result="t"/>
  <feColorMatrix in="t" type="matrix" values="0 0 0 0 0.8  0 0 0 0 0.98  0 0 0 0 1  -11 0 0 0 1.35" result="c"/>
  <feGaussianBlur in="c" stdDeviation="0.6" result="c2"/>
  <feComposite in="c2" in2="SourceAlpha" operator="in"/>
</filter>"""


def water_moon(cx, cy, r, sun_dir=(-1, 0.2), fish=True, rng=None, idp="wm"):
    """Una esfera de agua: núcleo oscuro, foco brillante en el lado opuesto
    a la estrella (la luz la atraviesa), borde que refracta."""
    sx, sy = sun_dir
    fx, fy = cx - sx * r * 0.45, cy - sy * r * 0.45
    defs = f"""
<radialGradient id="{idp}Body" cx="{cx}" cy="{cy}" r="{r}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#0f3c78"/><stop offset="0.7" stop-color="#0b2a5c"/><stop offset="0.93" stop-color="#2f7fc0"/>
  <stop offset="1" stop-color="#9fe0ff"/>
</radialGradient>
<radialGradient id="{idp}Focus" cx="{fx}" cy="{fy}" r="{r * 0.55}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#e9fbff" stop-opacity="0.95"/><stop offset="0.25" stop-color="#7fe0ff" stop-opacity="0.55"/>
  <stop offset="1" stop-color="#2a7fc8" stop-opacity="0"/>
</radialGradient>
<clipPath id="{idp}Clip"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>
"""
    b = [f'<circle cx="{cx}" cy="{cy}" r="{r * 1.08}" fill="#4fa8e8" opacity="0.18" filter="url(#b20)"/>',
         f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{idp}Body)"/>',
         f'<g clip-path="url(#{idp}Clip)">']
    # corrientes internas
    for k in range(6):
        rr = r * (0.3 + k * 0.11)
        b.append(f'<ellipse cx="{f(cx + r * 0.05)}" cy="{f(cy - r * 0.03)}" rx="{f(rr)}" ry="{f(rr * 0.42)}" fill="none" stroke="#7fc8f0" '
                 f'stroke-width="{1 + k * 0.4:.1f}" opacity="0.14" transform="rotate({-18 + k * 6} {cx} {cy})"/>')
    b.append(f'<circle cx="{f(fx)}" cy="{f(fy)}" r="{r * 0.55}" fill="url(#{idp}Focus)"/>')
    if fish and rng:
        for i in range(36):
            a = rng.uniform(0, math.tau)
            d = rng.uniform(0.15, 0.65) * r
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.6
            s = r / 260
            b.append(f'<path d="M0,0 c5,-3 10,-3 14,0 l4,-3 l0,6 l-4,-3 c-4,3 -9,3 -14,0 Z" fill="#06203f" opacity="0.6" '
                     f'transform="translate({f(x)},{f(y)}) rotate({math.degrees(a) + 90:.0f}) scale({s:.2f})"/>')
        b.append(f'<path d="M0,0 C40,-26 80,-26 120,0 C80,10 40,10 0,0 Z M118,0 l56,3" fill="#06203f" stroke="#06203f" stroke-width="2" opacity="0.55" '
                 f'transform="translate({f(cx - r * 0.35)},{f(cy + r * 0.2)}) rotate(-12) scale({r / 300:.2f})"/>')
    b.append("</g>")
    b.append(f'<path d="M{f(cx + r * 0.62)},{f(cy - r * 0.62)} A{r},{r} 0 0 1 {f(cx + r * 0.95)},{f(cy + r * 0.1)}" stroke="#f2fbff" stroke-width="{r * 0.03:.1f}" fill="none" opacity="0.7" stroke-linecap="round"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#c9f1ff" stroke-width="1.6" opacity="0.6"/>')
    return defs, "".join(b)


def orbital():
    rng = random.Random(5)
    CX, CY, R = 620, 610, 300
    wm_defs, wm = water_moon(1190, 290, 150, sun_dir=(-0.9, 0.3), rng=rng)
    defs = filters(wm_defs + CAUSTIC.format(bf="0.03 0.04", seed=4) + f"""
<radialGradient id="dry" cx="{CX + 120}" cy="{CY - 130}" r="{R * 1.5}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#f1e7da"/><stop offset="0.35" stop-color="#d9c3b2"/><stop offset="0.7" stop-color="#8f7276"/><stop offset="1" stop-color="#2b2130"/>
</radialGradient>
<clipPath id="disc"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>
""")
    b = [f'<rect width="{W}" height="{H}" fill="#0e0c13"/>', stars(rng, 420, H, avoid=[(CX, CY, R + 30), (1190, 290, 170)])]
    b.append(f'<circle cx="{CX}" cy="{CY}" r="{R + 6}" fill="none" stroke="#e8c6a6" stroke-width="8" opacity="0.3" filter="url(#b8)"/>')
    b.append(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#dry)"/>')
    g = ['<g clip-path="url(#disc)">']
    # antiguas cuencas abisales: manchas más oscuras y frías
    for (x, y, r, lobes) in [(CX - 120, CY + 90, 110, [(2, 0.2, 0.4), (3, 0.12, 1.1)]), (CX + 150, CY + 170, 70, [(2, 0.25, 1.4)]),
                             (CX - 40, CY - 170, 60, [(3, 0.2, 0.2)])]:
        g.append(f'<path d="{smooth(blob(x, y, r, lobes))}" fill="#6f5a66" opacity="0.55" filter="url(#b8)"/>')
        g.append(f'<path d="{smooth(blob(x, y, r * 0.8, lobes))}" fill="none" stroke="#efe4d8" stroke-width="1.4" opacity="0.4" stroke-dasharray="3 5"/>')
    # fosas secas: cicatrices largas
    for pts in ([(CX - 260, CY - 40), (CX - 120, CY - 70), (CX + 20, CY - 60), (CX + 140, CY - 110), (CX + 240, CY - 180)],
                [(CX - 200, CY + 220), (CX - 60, CY + 210), (CX + 60, CY + 250)]):
        g.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#5a4552" stroke-width="7" opacity="0.6" stroke-linecap="round"/>')
        g.append(f'<path d="{smooth([(x, y - 4) for x, y in pts], closed=False)}" fill="none" stroke="#f6ece0" stroke-width="1.5" opacity="0.5"/>')
    # fantasmas de atolones: anillos de arrecife muerto, rosados
    for (x, y, r) in [(CX + 60, CY + 20, 34), (CX - 170, CY - 120, 22), (CX + 180, CY + 40, 18), (CX - 30, CY + 120, 14), (CX + 90, CY - 150, 16)]:
        g.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="#d68f86" stroke-width="{max(2, r * 0.18):.1f}" opacity="0.85" stroke-dasharray="{r * 0.5:.0f} 3"/>')
        g.append(f'<circle cx="{x}" cy="{y}" r="{r * 0.7}" fill="#efe6da" opacity="0.6"/>')
    # la sombra azul de la luna de agua, con cáusticas
    sx_, sy_, sr = CX + 70, CY - 30, 92
    g.append(f'<circle cx="{sx_}" cy="{sy_}" r="{sr * 1.2}" fill="#2a7fc8" opacity="0.35" filter="url(#b20)"/>')
    g.append(f'<circle cx="{sx_}" cy="{sy_}" r="{sr}" fill="#1d5c9e" opacity="0.8" filter="url(#b8)"/>')
    g.append(f'<mask id="sm"><circle cx="{sx_}" cy="{sy_}" r="{sr * 0.95}" fill="white" filter="url(#b8)"/></mask>')
    g.append(f'<g mask="url(#sm)"><circle cx="{sx_}" cy="{sy_}" r="{sr}" fill="#fff" filter="url(#caustic)" opacity="0.9"/></g>')
    # noche
    g.append(f'<circle cx="{CX - 250}" cy="{CY + 210}" r="{R * 1.1}" fill="#0a0710" opacity="0.65" filter="url(#b50)"/>')
    g.append("</g>")
    b += g
    b.append(wm)
    # haz de luz que la luna enfoca hacia el planeta
    b.append(f'<path d="M1060,330 L{CX + 130},{CY - 80} L{CX + 20},{CY + 30} L1080,380 Z" fill="#7fe0ff" opacity="0.06" filter="url(#b20)"/>')
    b.append(grain(0.05))
    return b, defs


def key_art():
    rng = random.Random(14)
    HZ = 620
    wm_defs, wm = water_moon(980, 230, 250, sun_dir=(-0.8, 0.5), rng=rng, idp="km")
    defs = filters(wm_defs + CAUSTIC.format(bf="0.008 0.022", seed=9) + f"""
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#121433"/><stop offset="0.6" stop-color="#3d3a66"/><stop offset="0.9" stop-color="#c49a92"/><stop offset="1" stop-color="#f0c9a2"/>
</linearGradient>
<linearGradient id="salt" x1="0" y1="{HZ}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#e7d4c4"/><stop offset="1" stop-color="#cdb2a6"/>
</linearGradient>
<radialGradient id="pool" cx="760" cy="840" r="620" gradientUnits="userSpaceOnUse" gradientTransform="translate(760 840) scale(1 0.42) translate(-760 -840)">
  <stop offset="0" stop-color="#1f5ea8" stop-opacity="0.88"/><stop offset="0.75" stop-color="#1f5ea8" stop-opacity="0.75"/><stop offset="1" stop-color="#1f5ea8" stop-opacity="0"/>
</radialGradient>
<mask id="poolMask"><ellipse cx="760" cy="840" rx="600" ry="240" fill="white" filter="url(#b50)"/></mask>
""")
    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>', stars(rng, 200, HZ - 220)]
    b.append(wm)
    # luz que la luna de agua derrama hacia el suelo
    b.append(f'<path d="M820,420 L1140,420 L1380,{H} L140,{H} Z" fill="#6fd0ff" opacity="0.07" filter="url(#b50)"/>')
    # horizonte: arrecifes muertos en silueta, cálidos por el sol bajo
    far = [(-40, HZ), (60, 596), (140, 604), (220, 570), (300, 590), (380, 600), (1180, 604), (1260, 560), (1320, 576), (1400, 540),
           (1460, 566), (1560, 590), (1640, HZ)]
    b.append(f'<path d="{smooth(far, tension=0.3)} " fill="#a9787a" opacity="0.8"/>')
    b.append(f'<rect x="0" y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#salt)"/>')
    # ondulaciones fósiles de arena y grietas de sal
    for k in range(18):
        y = HZ + 8 + k * k * 1.1 + k * 3
        pts = [(x, y + (1.5 + k * 0.2) * math.sin(x * 0.02 + k)) for x in range(-40, W + 41, 30)]
        b.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#b39486" stroke-width="{0.8 + k * 0.08:.1f}" opacity="0.5"/>')
    # corales muertos ramificados, blanco hueso: un bosque que fue arrecife
    def coral(x, y, ang, ln, w, depth, out):
        if depth == 0 or ln < 4:
            return
        x2 = x + math.cos(ang) * ln
        y2 = y + math.sin(ang) * ln
        out.append(f'<path d="M{f(x)},{f(y)} L{f(x2)},{f(y2)}" stroke="#eadfd2" stroke-width="{w:.1f}" stroke-linecap="round"/>')
        for da in (-0.42, 0.38):
            coral(x2, y2, ang + da + rng.uniform(-0.15, 0.15), ln * rng.uniform(0.62, 0.8), w * 0.7, depth - 1, out)
    for (x, y, sc) in [(210, 720, 1.0), (1380, 740, 1.25), (520, 650, 0.45), (1060, 640, 0.4), (90, 660, 0.5), (1540, 680, 0.6)]:
        out = []
        for k in range(3):
            coral(x + (k - 1) * 18 * sc, y, -math.pi / 2 + (k - 1) * 0.35, 70 * sc, 12 * sc, 6, out)
        b.append('<g filter="url(#roughS)">' + "".join(out) + '</g>')
        b.append(f'<ellipse cx="{x}" cy="{y + 2}" rx="{60 * sc}" ry="{9 * sc}" fill="#a88e86" opacity="0.5"/>')
    for (x, y, r) in [(1000, 760, 46), (1080, 790, 28), (170, 860, 60), (600, 900, 34)]:
        b.append(f'<ellipse cx="{x}" cy="{y}" rx="{r}" ry="{r * 0.6}" fill="#e3d5c6"/>')
        for k in range(6):
            b.append(f'<path d="M{x - r * 0.8},{y - r * 0.1 + k * r * 0.1} q{r * 0.4},{-r * 0.25} {r * 0.8},0 t{r * 0.8},0" fill="none" stroke="#b9a596" stroke-width="1.4" opacity="0.7"/>')
    # una concha espiral gigante, medio enterrada
    sx, sy = 1180, 900
    spiral = []
    for i in range(140):
        a = i * 0.11
        rr = 6 * math.exp(0.16 * a)
        spiral.append((sx + rr * math.cos(a), sy + rr * math.sin(a) * 0.55))
    b.append(f'<path d="{smooth(spiral, closed=False)}" fill="none" stroke="#f1e6d8" stroke-width="10" stroke-linecap="round"/>')
    b.append(f'<path d="{smooth(spiral, closed=False)}" fill="none" stroke="#b8968a" stroke-width="2" stroke-linecap="round" opacity="0.8"/>')
    # la sombra azul: el suelo vuelve a estar bajo el agua, con cáusticas que se mueven
    b.append(f'<ellipse cx="760" cy="840" rx="620" ry="250" fill="url(#pool)" filter="url(#b20)"/>')
    b.append(f'<g mask="url(#poolMask)"><rect x="0" y="560" width="{W}" height="{H - 560}" fill="#fff" filter="url(#caustic)" opacity="0.75"/></g>')
    # el fondo despierta: pólipos que se encienden donde llega la luz azul
    for i in range(160):
        a = rng.uniform(0, math.tau)
        d = math.sqrt(rng.random())
        x, y = 760 + math.cos(a) * d * 560, 840 + math.sin(a) * d * 220
        b.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{rng.uniform(1, 2.6):.1f}" fill="#bff6ff" opacity="{rng.uniform(0.4, 0.95):.2f}"/>')
    # escala: una figura dentro del círculo de luz azul
    fx, fy = 820, 830
    b.append(f'<path d="M{fx - 4},{fy} L{fx - 2.6},{fy - 15} Q{fx},{fy - 22} {fx + 2.6},{fy - 15} L{fx + 4},{fy} Z" fill="#0d1c33"/>'
             f'<circle cx="{fx}" cy="{fy - 24}" r="3.2" fill="#0d1c33"/>')
    b.append(grain(0.05))
    return b, defs


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, fn in (("c-luna-clave", key_art), ("c-luna-orbita", orbital)):
        body, defs = fn()
        p = write_svg(name, W, H, "".join(body), defs)
        svg_to_png(p, OUT / f"{name}.png", W, H)
