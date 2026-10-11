"""C · Las Dolinas — estudio cercano: el borde del Ojo durante la sombra.

De pie en el banco somero, al borde de la dolina mayor. La luz del eclipse
enfría todo y deja un horizonte cálido alrededor (el «atardecer de 360°» de
un eclipse total). El agua de la dolina flota sobre ella como una lente:
oscura, con la banda lechosa de la capa de azufre y la base encendida por el
plancton. Debajo, el pozo vacío enseña su pared: estratos de caliza,
repisas con estalactitas (fue una cueva al aire) y bocas de túnel que van
hacia las otras dolinas.
"""

import math
import random
from pathlib import Path

from paint import f, smooth, svg_to_png, write_svg

OUTD = Path(__file__).resolve().parent.parent / "renders"
W, H = 1600, 1000
HZ = 432          # horizonte
CX, CY, RX, RY = 800, 648, 690, 150   # la dolina en perspectiva


def ell_y(x, top=True, cx=CX, cy=CY, rx=RX, ry=RY):
    t = max(0.0, 1 - ((x - cx) / rx) ** 2)
    return cy - ry * math.sqrt(t) if top else cy + ry * math.sqrt(t)


def arc_path(cy, rx, ry, x0, x1, n=60, top=True, cx=CX):
    pts = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        pts.append((x, ell_y(x, top, cx, cy, rx, ry)))
    return pts


def build():
    rng = random.Random(12)
    FU = f'filterUnits="userSpaceOnUse" x="-200" y="-200" width="{W + 400}" height="{H + 400}"'
    defs = f"""
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#0f1130"/><stop offset="0.55" stop-color="#262a58"/>
  <stop offset="0.86" stop-color="#4f5482"/><stop offset="0.95" stop-color="#b98a9a"/><stop offset="1" stop-color="#eaa47a"/>
</linearGradient>
<linearGradient id="farsea" x1="0" y1="{HZ}" x2="0" y2="520" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#7a6f8a"/><stop offset="0.15" stop-color="#3d6f7c"/><stop offset="1" stop-color="#3e9a98"/>
</linearGradient>
<linearGradient id="near" x1="0" y1="{CY}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#3e9a98"/><stop offset="0.4" stop-color="#4bb0a9"/><stop offset="1" stop-color="#2d7f86"/>
</linearGradient>
<linearGradient id="wall" x1="0" y1="{CY - RY}" x2="0" y2="{CY + RY}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#cdbf9f"/><stop offset="0.25" stop-color="#9c8f7d"/>
  <stop offset="0.55" stop-color="#4a4658"/><stop offset="1" stop-color="#0b0b16"/>
</linearGradient>
<linearGradient id="lensBody" x1="0" y1="200" x2="0" y2="400" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#3e4f7d"/><stop offset="0.22" stop-color="#14305a"/>
  <stop offset="0.7" stop-color="#0a2140"/><stop offset="1" stop-color="#1f6d78"/>
</linearGradient>
<radialGradient id="void" cx="{CX}" cy="{CY + RY * 0.75}" r="{RX * 0.95}" gradientUnits="userSpaceOnUse" gradientTransform="translate(0 {CY + RY * 0.75}) scale(1 0.32) translate(0 {-(CY + RY * 0.75)})">
  <stop offset="0" stop-color="#03030a"/><stop offset="0.55" stop-color="#05050d" stop-opacity="0.97"/><stop offset="1" stop-color="#05050d" stop-opacity="0"/>
</radialGradient>
<radialGradient id="corona" cx="1268" cy="132" r="80" gradientUnits="userSpaceOnUse">
  <stop offset="0.3" stop-color="#ffffff" stop-opacity="0"/><stop offset="0.34" stop-color="#fff4e2" stop-opacity="0.95"/>
  <stop offset="0.5" stop-color="#d6cfff" stop-opacity="0.35"/><stop offset="1" stop-color="#8b80d0" stop-opacity="0"/>
</radialGradient>
<filter id="b2" {FU}><feGaussianBlur stdDeviation="2"/></filter>
<filter id="b6" {FU}><feGaussianBlur stdDeviation="6"/></filter>
<filter id="b14" {FU}><feGaussianBlur stdDeviation="14"/></filter>
<filter id="b30" {FU}><feGaussianBlur stdDeviation="30"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.9  0 0 0 0 0.9  0 0 0 0 1  0 0 0 0.7 -0.3"/>
</filter>
<filter id="rough" {FU}>
  <feTurbulence type="fractalNoise" baseFrequency="0.04 0.012" numOctaves="3" seed="7" result="t"/>
  <feDisplacementMap in="SourceGraphic" in2="t" scale="10" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<clipPath id="hole"><ellipse cx="{CX}" cy="{CY}" rx="{RX}" ry="{RY}"/></clipPath>
"""
    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']
    # estrellas: en la totalidad se ven
    for _ in range(140):
        x, y = rng.uniform(0, W), rng.uniform(0, HZ - 60)
        b.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{rng.choice([0.5, 0.7, 0.9, 1.1])}" fill="#e8e6ff" opacity="{rng.uniform(0.25, 0.8):.2f}"/>')
    # el eclipse
    b.append('<circle cx="1268" cy="132" r="80" fill="url(#corona)"/>')
    b.append('<circle cx="1268" cy="132" r="24" fill="#0b0c1c"/>')
    b.append('<circle cx="1287" cy="118" r="3" fill="#fff1d6"/><circle cx="1287" cy="118" r="9" fill="#ffd9a8" opacity="0.4" filter="url(#b2)"/>')
    # mar lejano y bancos lejanos
    b.append(f'<rect x="0" y="{HZ}" width="{W}" height="{CY - HZ}" fill="url(#farsea)"/>')
    for i in range(16):
        y = HZ + 6 + i * i * 0.28 + i * 1.5
        b.append(f'<rect x="0" y="{f(y)}" width="{W}" height="{0.8 + i * 0.12:.1f}" fill="#c9eee0" opacity="{0.05 + i * 0.012:.3f}"/>')
    # cayos en el horizonte
    for (x0, w, h) in [(120, 140, 7), (300, 60, 5), (1080, 90, 6), (1330, 190, 8), (1520, 50, 4)]:
        b.append(f'<path d="M{x0},{HZ + 3} q{w * 0.2},{-h} {w * 0.5},{-h * 1.1} t{w * 0.5},{h * 1.1} Z" fill="#283c45"/>')
        b.append(f'<rect x="{x0 - 8}" y="{HZ + 2}" width="{w + 16}" height="2" fill="#e8dcc2" opacity="0.7"/>')
    # el banco del otro lado: arenas y praderas en franjas
    for (y, x0, x1, col, op) in [(470, 0, 520, "#7ccfc0", 0.6), (478, 980, 1600, "#7ccfc0", 0.55), (488, 160, 700, "#2f7f7a", 0.5),
                                 (492, 900, 1450, "#d7eadf", 0.35), (506, 0, 300, "#d7eadf", 0.4)]:
        b.append(f'<ellipse cx="{(x0 + x1) / 2}" cy="{y}" rx="{(x1 - x0) / 2}" ry="5" fill="{col}" opacity="{op}" filter="url(#b6)"/>')
    # la dolina: pared lejana
    hole = [f'<g clip-path="url(#hole)">',
            f'<rect x="0" y="{CY - RY}" width="{W}" height="{2 * RY}" fill="url(#wall)"/>']
    # estratos: arcos que siguen la curvatura del pozo
    for k in range(1, 12):
        dy = k * 11 + k * k * 0.6
        pts = arc_path(CY + dy - 2, RX * (1 - k * 0.012), RY * 0.98, CX - RX, CX + RX)
        op = max(0.0, 0.5 - k * 0.03)
        hole.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#e9dcc0" stroke-width="{1.4 if k % 3 else 2.4}" '
                    f'opacity="{op:.2f}" filter="url(#rough)"/>')
        if k in (2, 5, 9):
            hole.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#2b2a38" stroke-width="7" opacity="{0.55 - k * 0.03:.2f}" '
                        f'transform="translate(0,6)" filter="url(#b2)"/>')
            # estalactitas bajo la repisa
            for i in range(120):
                x = CX - RX + 40 + i * (2 * RX - 80) / 120 + rng.uniform(-3, 3)
                y = ell_y(x, True, CX, CY + dy - 2, RX * (1 - k * 0.012), RY * 0.98) + 4
                ln = rng.uniform(4, 14) * (1 - k * 0.05)
                hole.append(f'<path d="M{f(x - 1.6)},{f(y)} L{f(x)},{f(y + ln)} L{f(x + 1.6)},{f(y)} Z" fill="#d9ccae" opacity="{0.5 - k * 0.035:.2f}"/>')
    # bocas de túnel hacia otras dolinas
    for (x, dy, w, h) in [(420, 38, 60, 46), (1130, 52, 80, 58), (760, 70, 42, 34), (1310, 30, 34, 30)]:
        y = ell_y(x) + dy
        pts = [(x - w * 0.5, y + h), (x - w * 0.56, y + h * 0.62), (x - w * 0.38, y + h * 0.2), (x - w * 0.08, y + h * 0.04),
               (x + w * 0.22, y + h * 0.12), (x + w * 0.48, y + h * 0.4), (x + w * 0.52, y + h * 0.8), (x + w * 0.3, y + h * 1.02),
               (x - w * 0.1, y + h * 0.92)]
        hole.append(f'<path d="{smooth(pts)}" fill="#07070f"/>')
        hole.append(f'<path d="{smooth(pts[:5], closed=False)}" fill="none" stroke="#e1d4b6" stroke-width="1.2" opacity="0.35"/>')
    # jardines de lirios de mar en las repisas
    for (x0, x1, k) in [(260, 520, 2), (980, 1240, 2), (600, 880, 5)]:
        dy = k * 11 + k * k * 0.6
        for i in range(26):
            x = x0 + (x1 - x0) * i / 26 + rng.uniform(-4, 4)
            y = ell_y(x, True, CX, CY + dy - 2, RX * (1 - k * 0.012), RY * 0.98) - 1
            h = rng.uniform(10, 22) * (1 - k * 0.08)
            sway = rng.uniform(-4, 4)
            hole.append(f'<path d="M{f(x)},{f(y)} q{f(sway)},{f(-h * 0.6)} {f(sway * 0.5)},{f(-h)}" stroke="#e7e0cc" stroke-width="1" fill="none" opacity="0.75"/>')
            hole.append(f'<circle cx="{f(x + sway * 0.5)}" cy="{f(y - h)}" r="{rng.uniform(2, 3.6):.1f}" fill="#f0e6cf" opacity="0.8"/>')
    # el vacío: la pared cercana no se ve y el fondo queda en negro
    hole.append(f'<rect x="0" y="{CY - RY}" width="{W}" height="{2 * RY + 10}" fill="url(#void)"/>')
    # neblina lechosa de azufre en el fondo
    hole.append(f'<ellipse cx="{CX}" cy="{CY + 110}" rx="{RX * 0.85}" ry="60" fill="#c9d6c6" opacity="0.18" filter="url(#b14)"/>')
    # sombra de la lente sobre la pared
    hole.append(f'<ellipse cx="{CX + 40}" cy="{CY - 70}" rx="{RX * 0.9}" ry="50" fill="#060814" opacity="0.35" filter="url(#b30)"/>')
    hole.append("</g>")
    b += hole
    # borde lejano del pozo: filo claro y hilos de agua que se descuelgan
    rim = arc_path(CY, RX, RY, CX - RX, CX + RX)
    b.append(f'<path d="{smooth(rim, closed=False)}" fill="none" stroke="#e6f3e6" stroke-width="2.4" opacity="0.85"/>')
    for i in range(34):
        x = CX - RX + 60 + i * (2 * RX - 120) / 34 + rng.uniform(-8, 8)
        y = ell_y(x)
        ln = rng.uniform(18, 70)
        b.append(f'<path d="M{f(x)},{f(y)} q{f(rng.uniform(-2, 2))},{f(ln * 0.5)} {f(rng.uniform(-3, 3))},{f(ln)}" stroke="#bfe8e2" '
                 f'stroke-width="{rng.uniform(0.8, 1.8):.1f}" fill="none" opacity="{rng.uniform(0.35, 0.7):.2f}"/>')
    # escala: una figura diminuta en el borde lejano
    fx, fy = 1186, ell_y(1186) - 1
    b.append(f'<path d="M{fx - 2.2},{fy} L{fx - 1.4},{fy - 7} Q{fx},{fy - 11} {fx + 1.4},{fy - 7} L{fx + 2.2},{fy} Z" fill="#141522"/>'
             f'<circle cx="{fx}" cy="{fy - 11.5}" r="1.7" fill="#141522"/>')
    b.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{RX}" ry="{RY}" fill="none" stroke="#dff1e6" stroke-width="1.6" opacity="0.5"/>')
    # banco cercano: agua somera sobre arena, con ondulaciones en perspectiva
    near = f"M0,{H} L0,{CY} " + " ".join(f"L{f(x)},{f(y)}" for x, y in arc_path(CY, RX, RY, CX - RX, CX + RX, top=False)) + f" L{W},{CY} L{W},{H} Z"
    b.append(f'<path d="{near}" fill="url(#near)"/>')
    for k in range(22):
        y = CY + RY + 8 + k * k * 0.42 + k * 3
        amp = 1.5 + k * 0.25
        pts = []
        for i in range(41):
            x = i * W / 40
            yy = y + amp * math.sin(i * 1.1 + k) - max(0, (RY - abs(x - CX) * RY / RX)) * 0.0
            pts.append((x, yy))
        b.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#d6f6ea" stroke-width="{0.8 + k * 0.09:.2f}" opacity="{0.18 + k * 0.012:.2f}"/>')
    # lengüetas de arena seca y matas de fanerógama en primer plano
    for (x, y, w, h) in [(160, 910, 240, 26), (1250, 940, 300, 30), (620, 975, 200, 18)]:
        b.append(f'<ellipse cx="{x}" cy="{y}" rx="{w / 2}" ry="{h / 2}" fill="#eae6d4" opacity="0.75" filter="url(#b6)"/>')
    for i in range(70):
        x = rng.uniform(0, W)
        y = rng.uniform(830, H)
        if 520 < x < 1080 and y < 860:
            continue
        hgt = (y - 800) * 0.09
        for j in range(4):
            b.append(f'<path d="M{f(x + j * 2)},{f(y)} q{f(rng.uniform(-3, 3))},{f(-hgt * 0.6)} {f(rng.uniform(-5, 5))},{f(-hgt)}" '
                     f'stroke="#1f5e58" stroke-width="1.2" fill="none" opacity="0.7"/>')
    # labio cercano: el agua del banco cae hacia el pozo en hilos
    lip = arc_path(CY, RX, RY, CX - RX * 0.95, CX + RX * 0.95, top=False)
    b.append(f'<path d="{smooth(lip, closed=False)}" fill="none" stroke="#eaf7ee" stroke-width="3" opacity="0.6"/>')

    # la lente: el agua de la dolina flotando
    LX, LY, LRX, LRY = 800, 292, 600, 92
    lens = (f"M{LX - LRX},{LY + 10} C{LX - LRX * 0.7},{LY - LRY * 0.9} {LX + LRX * 0.45},{LY - LRY * 1.2} {LX + LRX},{LY - 2} "
            f"C{LX + LRX * 0.78},{LY + LRY * 0.55} {LX + LRX * 0.3},{LY + LRY * 1.35} {LX - LRX * 0.05},{LY + LRY * 1.25} "
            f"C{LX - LRX * 0.4},{LY + LRY * 1.15} {LX - LRX * 0.85},{LY + LRY * 0.6} {LX - LRX},{LY + 10} Z")
    b.append(f'<path d="{lens}" fill="#0a1a33" opacity="0.5" filter="url(#b30)" transform="translate(0,30)"/>')
    b.append(f'<path d="{lens}" fill="url(#lensBody)" opacity="0.95"/>')
    b.append(f'<clipPath id="lensClip"><path d="{lens}"/></clipPath>')
    lc = ['<g clip-path="url(#lensClip)">']
    lc.append(f'<ellipse cx="{LX}" cy="{LY - 74}" rx="{LRX * 0.9}" ry="30" fill="#6f6f9c" opacity="0.5" filter="url(#b14)"/>')
    lc.append(f'<ellipse cx="{LX + 250}" cy="{LY - 56}" rx="130" ry="9" fill="#e7b9a2" opacity="0.4" filter="url(#b6)"/>')
    # la capa de azufre: una franja lechosa, suave y algo inclinada
    band = []
    for i in range(61):
        x = LX - LRX + i * 2 * LRX / 60
        band.append((x, LY + 18 + 0.03 * (x - LX) + 5 * math.sin(i * 0.22)))
    lc.append(f'<path d="{smooth(band, closed=False)}" fill="none" stroke="#d3dfcf" stroke-width="22" opacity="0.42" filter="url(#b6)"/>')
    lc.append(f'<path d="{smooth(band, closed=False)}" fill="none" stroke="#e9efe2" stroke-width="5" opacity="0.28" filter="url(#b2)"/>')
    # vida que viajó con su agua
    for (x, y, s, rot) in [(560, 300, 1.0, -6), (590, 312, 0.7, -10), (612, 296, 0.6, -2), (980, 330, 1.6, 8), (1090, 288, 0.8, 4)]:
        lc.append(f'<path d="M0,0 c8,-4 16,-4 22,0 l6,-4 l0,8 l-6,-4 c-6,4 -14,4 -22,0 Z" fill="#06101f" opacity="0.8" '
                  f'transform="translate({x},{y}) rotate({rot}) scale({s})"/>')
    lc.append(f'<path d="M0,0 C30,-22 60,-22 90,0 C60,8 30,8 0,0 Z M88,0 l40,-3" fill="#050d1b" stroke="#050d1b" stroke-width="1.5" opacity="0.85" '
              f'transform="translate(330,330) rotate(-4)"/>')
    # base encendida por el plancton
    lc.append(f'<ellipse cx="{LX - 40}" cy="{LY + LRY * 1.05}" rx="{LRX * 0.7}" ry="34" fill="#7fe6d4" opacity="0.55" filter="url(#b14)"/>')
    lc.append("</g>")
    b += lc
    b.append(f'<path d="{lens}" fill="none" stroke="#a9c6e8" stroke-width="1.4" opacity="0.55"/>')
    # hilos que caen de la lente al pozo
    for i in range(46):
        x = LX - LRX * 0.8 + i * LRX * 1.6 / 46 + rng.uniform(-6, 6)
        y0 = LY + LRY * 1.05 * math.sqrt(max(0, 1 - ((x - LX + 30) / LRX) ** 2)) - 4
        ln = rng.uniform(40, 200)
        b.append(f'<line x1="{f(x)}" y1="{f(y0)}" x2="{f(x + rng.uniform(-2, 2))}" y2="{f(y0 + ln)}" stroke="#8fe0d8" '
                 f'stroke-width="{rng.uniform(0.6, 1.4):.1f}" opacity="{rng.uniform(0.15, 0.45):.2f}" stroke-dasharray="{rng.randint(4, 14)} {rng.randint(3, 9)}"/>')
    # columnas de luz del plancton hacia el pozo
    b.append(f'<path d="M{LX - 420},{LY + 70} L{LX + 420},{LY + 70} L{LX + 560},{CY + 40} L{LX - 560},{CY + 40} Z" fill="#7fe6d4" opacity="0.05" filter="url(#b14)"/>')
    b.append(f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="0.06"/>')
    return b, defs


if __name__ == "__main__":
    OUTD.mkdir(exist_ok=True)
    body, defs = build()
    p = write_svg("study_dolinas", W, H, "".join(body), defs)
    svg_to_png(p, OUTD / "i-c-estudio.png", W, H)
