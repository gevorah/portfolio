"""Tratamiento A — «Relicario».

Umbral como una reliquia tallada: un planeta de piedra calcárea partido por
una grieta vertical (la pupila), coronado por un arco apuntado (el umbral) y
una aguja. Lenguaje de aguafuerte: tramas de líneas que siguen la forma,
claroscuro teatral y grano de lámina impresa. La luna es lisa, oscura, casi
invisible hasta que tapa la estrella.

Las formas están dibujadas a mano en coordenadas de lámina; este script
sólo genera las tramas repetitivas (líneas de grabado, estrellas, marcas).

Salida: frames/a{1,2,3}.svg y frames/a{1,2,3}.json (anclas).
"""

import json
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "frames"
W, H = 1600, 1000
INK = "#0e0c13"

STONE_HI = "#e4dcef"
STONE_LT = "#b6abcf"
STONE_MD = "#6f6492"
STONE_DK = "#2c2442"
STONE_VD = "#15111f"
COLD = "#eef1ff"
REVEAL = "#a8bcff"   # luz fría que revela los senderos
GOLD = "#e2b46a"     # único acento cálido: corona, clave del arco, relicario
GOLD_HI = "#f6dca6"


def f(x):
    return f"{x:.1f}"


# ----------------------------------------------------------------- comunes
def defs(extra=""):
    return f"""<defs>
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="4" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.85  0 0 0 0 0.8  0 0 0 0 1  0 0 0 0.9 -0.35"/>
</filter>
<filter id="nebula" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.0016 0.0062" numOctaves="5" seed="12" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.36  0 0 0 0 0.3  0 0 0 0 0.62  1.6 0 0 0 -0.62"/>
  <feGaussianBlur stdDeviation="6"/>
</filter>
<filter id="glowS" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="2.4" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="glowL" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="9"/>
</filter>
<filter id="blurXL" x="-100%" y="-100%" width="300%" height="300%">
  <feGaussianBlur stdDeviation="28"/>
</filter>
<radialGradient id="starBloom">
  <stop offset="0" stop-color="#ffffff" stop-opacity="1"/>
  <stop offset="0.06" stop-color="#eef1ff" stop-opacity="0.85"/>
  <stop offset="0.25" stop-color="#b9c4ff" stop-opacity="0.25"/>
  <stop offset="1" stop-color="#6e63c9" stop-opacity="0"/>
</radialGradient>
<pattern id="hatch45" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(38)">
  <line x1="0" y1="0" x2="0" y2="6" stroke="{INK}" stroke-width="1.1"/>
</pattern>
<pattern id="hatch45L" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(-52)">
  <line x1="0" y1="0" x2="0" y2="5" stroke="#8e84b4" stroke-width="0.6"/>
</pattern>
{extra}
</defs>"""


def plate():
    """Marco de lámina grabada: doble filete y marcas de esquina."""
    m = 28
    return f"""<g fill="none" stroke="#d6cdea">
<rect x="{m}" y="{m}" width="{W - 2 * m}" height="{H - 2 * m}" stroke-width="1" opacity="0.32"/>
<rect x="{m + 6}" y="{m + 6}" width="{W - 2 * m - 12}" height="{H - 2 * m - 12}" stroke-width="0.6" opacity="0.16"/>
</g>"""


def grain(op=0.09):
    return f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="{op}"/>'


def stars(rng, n, region=(0, 0, W, H), avoid=(), bright=1.0):
    out = []
    x0, y0, x1, y1 = region
    for _ in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if any(math.hypot(x - ax, y - ay) < ar for ax, ay, ar in avoid):
            continue
        r = rng.choice([0.5, 0.6, 0.7, 0.8, 0.9, 1.2])
        o = rng.uniform(0.25, 0.85) * bright
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="#ece6ff" opacity="{min(o, 1):.2f}"/>')
    # estrellas «grabadas»: cruz de cuatro puntas, finas
    for _ in range(max(3, n // 60)):
        x, y = rng.uniform(x0 + 40, x1 - 40), rng.uniform(y0 + 40, y1 - 40)
        if any(math.hypot(x - ax, y - ay) < ar * 1.1 for ax, ay, ar in avoid):
            continue
        s = rng.choice([5, 7, 9])
        out.append(f'<path d="M{f(x - s)},{f(y)} Q{f(x)},{f(y)} {f(x)},{f(y - s)} Q{f(x)},{f(y)} {f(x + s)},{f(y)} '
                   f'Q{f(x)},{f(y)} {f(x)},{f(y + s)} Q{f(x)},{f(y)} {f(x - s)},{f(y)} Z" fill="#efeaff" opacity="{0.75 * bright:.2f}"/>')
    return "\n".join(out)


def star_flare(x, y, size, op=1.0):
    """Estrella principal: núcleo, halo y destellos grabados (líneas finas)."""
    return f"""<g opacity="{op}">
<circle cx="{f(x)}" cy="{f(y)}" r="{f(size * 9)}" fill="url(#starBloom)" opacity="0.55"/>
<circle cx="{f(x)}" cy="{f(y)}" r="{f(size * 2.8)}" fill="url(#starBloom)"/>
<path d="M{f(x - size * 26)},{f(y)} H{f(x + size * 26)} M{f(x)},{f(y - size * 14)} V{f(y + size * 14)}" stroke="#f3f1ff" stroke-width="0.8" opacity="0.55"/>
<path d="M{f(x - size * 9)},{f(y - size * 9)} L{f(x + size * 9)},{f(y + size * 9)} M{f(x - size * 9)},{f(y + size * 9)} L{f(x + size * 9)},{f(y - size * 9)}" stroke="#f3f1ff" stroke-width="0.6" opacity="0.3"/>
<circle cx="{f(x)}" cy="{f(y)}" r="{f(size)}" fill="#ffffff"/>
</g>"""


# --------------------------------------------------- A1 · vista orbital
def a1():
    """Contraluz: la estrella queda justo detrás del planeta. La luz sólo
    atraviesa la grieta, así que desde la órbita Umbral es un disco oscuro
    con una pupila vertical encendida, coronado por el arco y la aguja."""
    rng = random.Random(3)
    cx, cy, R = 800, 612, 168
    sx, sy = 842, 452  # la estrella, escondida tras el limbo

    def ly(x):  # y del limbo superior
        return cy - math.sqrt(max(R * R - (x - cx) ** 2, 0))

    # grieta: pupila vertical, ancha arriba, se cierra hacia el sur
    def edge(side):
        pts = []
        for i in range(31):
            t = i / 30
            y = cy - R - 4 + t * (2 * R * 0.86)
            # almendra: como la pupila del avatar, aguda en los extremos
            w = 1.5 + 17 * math.sin(math.pi * min(1, t * 1.08)) ** 0.85 + 6 * (1 - t) ** 3
            pts.append((cx + side * w + 2.5 * math.sin(t * 3.0), y))
        return pts
    le, re = edge(-1), edge(1)
    crack = ("M" + " L".join(f"{f(x)},{f(y)}" for x, y in le) + " L" +
             " L".join(f"{f(x)},{f(y)}" for x, y in reversed(re)) + " Z")

    extra = f"""
<radialGradient id="halo" cx="{sx}" cy="{sy}" r="560" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#c9c2ff" stop-opacity="0.55"/>
  <stop offset="0.18" stop-color="#7d70d6" stop-opacity="0.32"/>
  <stop offset="0.5" stop-color="#3b2f7a" stop-opacity="0.14"/>
  <stop offset="1" stop-color="#1b1535" stop-opacity="0"/>
</radialGradient>
<radialGradient id="disc" cx="{cx}" cy="{cy - R * 0.9}" r="{R * 2}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#2a2341"/>
  <stop offset="0.35" stop-color="#16121f"/>
  <stop offset="1" stop-color="#09080d"/>
</radialGradient>
<linearGradient id="slit" x1="0" y1="{cy - R}" x2="0" y2="{cy + R * 0.75}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#ffffff"/>
  <stop offset="0.25" stop-color="#d9dcff"/>
  <stop offset="0.7" stop-color="#8d84e6" stop-opacity="0.8"/>
  <stop offset="1" stop-color="#4d42a0" stop-opacity="0.2"/>
</linearGradient>
<radialGradient id="limbGlow" cx="{sx}" cy="{sy}" r="{R * 1.2}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="{COLD}" stop-opacity="1"/>
  <stop offset="0.6" stop-color="{COLD}" stop-opacity="0.65"/>
  <stop offset="1" stop-color="{COLD}" stop-opacity="0"/>
</radialGradient>
<mask id="engraveMask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
  <radialGradient id="emg" cx="{cx}" cy="{cy - R}" r="{R * 2}" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="white"/><stop offset="0.75" stop-color="black"/>
  </radialGradient>
  <rect width="{W}" height="{H}" fill="url(#emg)"/>
</mask>
<clipPath id="discClip"><circle cx="{cx}" cy="{cy}" r="{R}"/></clipPath>
<radialGradient id="moonG" cx="0.22" cy="0.2" r="0.95">
  <stop offset="0" stop-color="#cfc8ea"/>
  <stop offset="0.16" stop-color="#4c4470"/>
  <stop offset="0.6" stop-color="#16121f"/>
  <stop offset="1" stop-color="#0b0912"/>
</radialGradient>
"""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           defs(extra), f'<rect width="{W}" height="{H}" fill="{INK}"/>',
           f'<rect width="{W}" height="{H}" filter="url(#nebula)" opacity="0.26"/>',
           f'<rect width="{W}" height="{H}" fill="url(#halo)"/>',
           stars(rng, 280, avoid=[(cx, cy, R + 24), (sx, sy, 120)])]

    # rayos grabados que asoman tras el limbo (la estrella oculta)
    rays = []
    rr = random.Random(2)
    for k in range(90):
        a = math.radians(-180 + 180 * k / 89 + rr.uniform(-0.6, 0.6))
        r0 = R * 0.6
        r1 = R * (1.25 + rr.random() * (1.1 if k % 5 == 0 else 0.45))
        rays.append(f'<line x1="{f(sx + math.cos(a) * r0)}" y1="{f(sy + math.sin(a) * r0)}" '
                    f'x2="{f(sx + math.cos(a) * r1)}" y2="{f(sy + math.sin(a) * r1)}"/>')
    out.append(f'<g stroke="#e9e5ff" stroke-width="0.6" opacity="0.28">{"".join(rays)}</g>')

    # órbita: elipse grabada (mitad trasera, tapada por el planeta)
    ox, oy, orx, ory, rot = cx, cy + 10, 390, 92, -7

    def orbit_pt(t):
        a = math.radians(t)
        x, y = orx * math.cos(a), ory * math.sin(a)
        r = math.radians(rot)
        return ox + x * math.cos(r) - y * math.sin(r), oy + x * math.sin(r) + y * math.cos(r)

    def poly(pts):
        return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)

    out.append(f'<path d="{poly([orbit_pt(t) for t in range(180, 361, 2)])}" fill="none" stroke="#cfc6ea" stroke-width="0.9" opacity="0.3"/>')
    tb, tf = [], []
    for t in range(0, 360, 6):
        x, y = orbit_pt(t)
        nx, ny = x - ox, y - oy
        ln = math.hypot(nx, ny)
        L = 7 if t % 30 == 0 else 3.5
        (tf if t <= 180 else tb).append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x + nx / ln * L)}" y2="{f(y + ny / ln * L)}"/>')
    out.append(f'<g stroke="#cfc6ea" stroke-width="0.8" opacity="0.28">{"".join(tb)}</g>')

    # ---- aguja (detrás del disco, sobre el limbo izquierdo)
    a = math.radians(-128)
    bx, by = cx + (R - 8) * math.cos(a), cy + (R - 8) * math.sin(a)
    ux, uy = math.cos(a + 0.12), math.sin(a + 0.12)
    px_, py_ = -uy, ux
    Ls, wb, wt = 150, 8, 3.5
    tx, ty = bx + ux * Ls, by + uy * Ls
    out.append(f'<path d="M{f(bx - px_ * wb)},{f(by - py_ * wb)} L{f(tx - px_ * wt)},{f(ty - py_ * wt)} L{f(tx + ux * 14)},{f(ty + uy * 14)} '
               f'L{f(tx + px_ * wt)},{f(ty + py_ * wt)} L{f(bx + px_ * wb)},{f(by + py_ * wb)} Z" fill="#0c0a12"/>')
    out.append(f'<path d="M{f(bx + px_ * wb)},{f(by + py_ * wb)} L{f(tx + px_ * wt)},{f(ty + py_ * wt)} L{f(tx + ux * 14)},{f(ty + uy * 14)}" '
               f'stroke="{COLD}" stroke-width="1.1" fill="none" opacity="0.8"/>')
    spire_tip = (tx + ux * 14, ty + uy * 14)

    # ---- arco: patas sobre el limbo a ambos lados de la grieta
    lo, li = 74, 48
    base = ly(cx + lo) + 10
    apex = cy - R - 128
    arch = (f"M{cx - lo},{f(base)} C{cx - lo},{f(base - 96)} {cx - 40},{f(apex + 28)} {cx},{f(apex)} "
            f"C{cx + 40},{f(apex + 28)} {cx + lo},{f(base - 96)} {cx + lo},{f(base)} "
            f"L{cx + li},{f(base)} C{cx + li},{f(base - 84)} {cx + 24},{f(apex + 46)} {cx},{f(apex + 24)} "
            f"C{cx - 24},{f(apex + 46)} {cx - li},{f(base - 84)} {cx - li},{f(base)} Z")
    out.append(f'<path d="{arch}" fill="#0c0a12"/>')
    out.append(f'<path d="{arch}" fill="url(#hatch45L)" opacity="0.35"/>')
    for d in (f"M{cx + li},{f(base)} C{cx + li},{f(base - 84)} {cx + 24},{f(apex + 46)} {cx},{f(apex + 24)}",
              f"M{cx - li},{f(base)} C{cx - li},{f(base - 84)} {cx - 24},{f(apex + 46)} {cx},{f(apex + 24)}"):
        out.append(f'<path d="{d}" stroke="{COLD}" stroke-width="1.8" fill="none" opacity="0.95"/>')
    out.append(f'<path d="M{cx - lo},{f(base)} C{cx - lo},{f(base - 96)} {cx - 40},{f(apex + 28)} {cx},{f(apex)} '
               f'C{cx + 40},{f(apex + 28)} {cx + lo},{f(base - 96)} {cx + lo},{f(base)}" stroke="#a9a0d0" stroke-width="0.9" fill="none" opacity="0.7"/>')
    out.append(f'<path d="M{cx - 7},{f(apex - 4)} L{cx + 7},{f(apex - 4)} L{cx + 5},{f(apex + 14)} L{cx - 5},{f(apex + 14)} Z" fill="#0c0a12" stroke="{COLD}" stroke-width="0.8"/>')
    for side in (-1, 1):
        px0 = cx + side * (lo + 2)
        py0 = base - 70
        out.append(f'<path d="M{f(px0 - 6)},{f(py0 + 20)} L{f(px0 - 5)},{f(py0)} L{f(px0)},{f(py0 - 26)} L{f(px0 + 5)},{f(py0)} L{f(px0 + 6)},{f(py0 + 20)} Z" fill="#0c0a12"/>')
        out.append(f'<path d="M{f(px0 - side * 5)},{f(py0)} L{f(px0)},{f(py0 - 26)}" stroke="{COLD}" stroke-width="0.8" opacity="0.7"/>')
    for side in (-1, 1):
        x0 = cx + side * (lo + li) / 2
        out.append(f'<path d="M{f(x0 - 20)},{f(base + 8)} L{f(x0 + 20)},{f(base + 8)} L{f(x0 + 17)},{f(base - 6)} L{f(x0 - 17)},{f(base - 6)} Z" fill="#0c0a12"/>')
        out.append(f'<path d="M{f(x0 - 17)},{f(base - 6)} L{f(x0 + 17)},{f(base - 6)}" stroke="{COLD}" stroke-width="0.8" opacity="0.6"/>')

    # ---- disco
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="url(#disc)"/>')
    # buril: paralelos muy tenues, visibles sólo cerca del limbo iluminado
    lat = []
    for i in range(-int(R) + 4, int(R), 5):
        y = cy + i
        rx = math.sqrt(max(R * R - i * i, 0))
        lat.append(f'<path d="M{f(cx - rx)},{f(y)} A{f(rx)},{f(rx * 0.24)} 0 0 0 {f(cx + rx)},{f(y)}"/>')
    out.append(f'<g clip-path="url(#discClip)" mask="url(#engraveMask)" fill="none" stroke="#6f64a6" stroke-width="0.8" opacity="0.55">{"".join(lat)}</g>')
    # terrazas: escalones en la silueta superior (se leen sólo como filos)
    for k, (x0, x1, dy) in enumerate([(cx - 150, cx - 90, 4), (cx + 92, cx + 146, 4), (cx - 120, cx - 82, 10), (cx + 84, cx + 118, 10)]):
        pts = [(x, ly(x) + dy) for x in range(int(x0), int(x1) + 1, 3)]
        out.append(f'<path d="{poly(pts)}" stroke="{COLD}" stroke-width="0.9" fill="none" opacity="{0.55 - k * 0.08:.2f}"/>')
    # estelas diminutas sobre el limbo
    for x in (cx - 132, cx - 108, cx + 112, cx + 136):
        y = ly(x)
        out.append(f'<path d="M{x - 2.5},{f(y + 2)} L{x - 2},{f(y - 11)} L{x + 2},{f(y - 11)} L{x + 2.5},{f(y + 2)} Z" fill="#0c0a12"/>'
                   f'<line x1="{x + 2}" y1="{f(y - 11)}" x2="{x + 2.5}" y2="{f(y + 2)}" stroke="{COLD}" stroke-width="0.7" opacity="0.8"/>')

    # ---- la pupila: luz que atraviesa la grieta
    out.append(f'<path d="{crack}" fill="#8f86ea" opacity="0.5" filter="url(#glowL)" clip-path="url(#discClip)"/>')
    out.append(f'<path d="{crack}" fill="url(#slit)" clip-path="url(#discClip)"/>')
    # escalones tallados dentro de la grieta, a contraluz
    zz = []
    for i in range(5, 25, 1):
        x, y = le[i]
        wst = (re[i][0] - x) * (0.22 + 0.12 * (i % 2))
        zz.append(f"M{f(x)},{f(y)} h{f(wst)} v{f((le[i + 1][1] - y))}")
    out.append(f'<path d="{" ".join(zz)}" stroke="#3a3168" stroke-width="1" fill="none" opacity="0.75" clip-path="url(#discClip)"/>')

    # ---- filo del limbo: creciente fino, más intenso cerca de la estrella
    out.append(f'<path d="M{f(cx - R * 0.98)},{f(cy - R * 0.2)} A{R},{R} 0 0 1 {f(cx + R * 0.98)},{f(cy - R * 0.2)}" '
               f'fill="none" stroke="url(#limbGlow)" stroke-width="2.4"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{R - 0.5}" fill="none" stroke="#5a5090" stroke-width="1" opacity="0.5"/>')
    # la estrella asoma en el limbo: perla brillante
    gx, gy = sx, ly(sx) + 1
    out.append(f'<circle cx="{f(gx)}" cy="{f(gy)}" r="26" fill="#e9e6ff" opacity="0.5" filter="url(#glowL)"/>')
    out.append(f'<path d="M{f(gx - 60)},{f(gy)} H{f(gx + 60)} M{f(gx)},{f(gy - 34)} V{f(gy + 4)}" stroke="#ffffff" stroke-width="0.8" opacity="0.7"/>')
    out.append(f'<circle cx="{f(gx)}" cy="{f(gy)}" r="3" fill="#ffffff"/>')

    # fragmentos desprendidos bajo la grieta, captan la luz por arriba
    for (x, y, sz, r) in [(cx + 10, cy + R + 22, 9, 20), (cx - 26, cy + R + 48, 6, -30), (cx + 36, cy + R + 70, 4, 50),
                          (cx - 4, cy + R + 96, 3, 10)]:
        out.append(f'<g transform="translate({x},{y}) rotate({r})"><path d="M{-sz},{-sz * 0.3} L{-sz * 0.2},{-sz} L{sz},{-sz * 0.4} '
                   f'L{sz * 0.7},{sz * 0.6} L{-sz * 0.5},{sz * 0.8} Z" fill="#100d18"/>'
                   f'<path d="M{-sz},{-sz * 0.3} L{-sz * 0.2},{-sz} L{sz},{-sz * 0.4}" stroke="#bdb5e6" stroke-width="0.9" fill="none"/></g>')

    # órbita delantera y luna
    out.append(f'<path d="{poly([orbit_pt(t) for t in range(0, 181, 2)])}" fill="none" stroke="#cfc6ea" stroke-width="1" opacity="0.55"/>')
    out.append(f'<g stroke="#cfc6ea" stroke-width="0.8" opacity="0.5">{"".join(tf)}</g>')
    mx, my = orbit_pt(-14)
    mr = 30
    out.append(f'<circle cx="{f(mx)}" cy="{f(my)}" r="{mr}" fill="url(#moonG)"/>')
    out.append(f'<path d="M{f(mx - mr * 0.98)},{f(my - mr * 0.1)} A{mr},{mr} 0 0 1 {f(mx + mr * 0.1)},{f(my - mr * 0.98)}" '
               f'stroke="{COLD}" stroke-width="1.3" fill="none" opacity="0.85"/>')
    for rr_ in (0.45, 0.7):
        out.append(f'<circle cx="{f(mx)}" cy="{f(my)}" r="{f(mr * rr_)}" fill="none" stroke="#ffffff" stroke-width="0.6" opacity="0.07"/>')

    out.append(grain())
    out.append(plate())
    out.append("</svg>")
    anchors = dict(planet=[cx, cy, R], star=[sx, sy], moon=[round(mx, 1), round(my, 1), mr],
                   arch_apex=[cx, round(apex, 1)], spire=[round(spire_tip[0], 1), round(spire_tip[1], 1)])
    return "\n".join(out), anchors


# ------------------------------------- A2 / A3 · aproximación y eclipse
def scene(eclipse):
    rng = random.Random(21)
    hc, hR = (800, 1720), 1170  # el horizonte: un mundo diminuto se curva rápido
    top = hc[1] - hR
    sx, sy = 800, 432           # la estrella, vista a través del arco
    if eclipse:
        mx, my, mr = sx, sy, 88
    else:
        mx, my, mr = 1222, 236, 88

    def hy(x, r=hR):
        return hc[1] - math.sqrt(max(r * r - (x - hc[0]) ** 2, 0))

    # grieta en perspectiva: del horizonte hacia el espectador
    def lip(t, side):
        # t: 0 horizonte → 1 borde inferior
        y = top + 4 + t * (H - top + 40)
        w = 22 + 300 * t ** 1.35
        jag = 6 * math.sin(t * 23 + (0 if side < 0 else 1.7)) * t
        return cx_ + side * (w + jag), y

    cx_ = 800
    left_lip = [lip(i / 40, -1) for i in range(41)]
    right_lip = [lip(i / 40, 1) for i in range(41)]
    cleft = ("M" + " L".join(f"{f(x)},{f(y)}" for x, y in left_lip) + " L" +
             " L".join(f"{f(x)},{f(y)}" for x, y in reversed(right_lip)) + " Z")

    # paredes interiores visibles (bandas tras cada labio)
    def inner(side, depth):
        pts = []
        for i in range(41):
            t = i / 40
            x, y = lip(t, side)
            pts.append((x - side * depth * t ** 1.2, y + depth * 0.5 * t))
        return pts

    lw_in, rw_in = inner(-1, 70), inner(1, 70)

    extra = f"""
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{INK}"/>
  <stop offset="0.55" stop-color="{'#120f1e' if eclipse else '#17132a'}"/>
  <stop offset="1" stop-color="{'#16112a' if eclipse else '#231c40'}"/>
</linearGradient>
<radialGradient id="backGlow" cx="{sx}" cy="{sy + 60}" r="520" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="{'#3b3170' if eclipse else '#4a4190'}" stop-opacity="{0.55 if eclipse else 0.75}"/>
  <stop offset="1" stop-color="#3b3170" stop-opacity="0"/>
</radialGradient>
<linearGradient id="ground" x1="0" y1="{top}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="{'#16122a' if eclipse else '#2a2346'}"/>
  <stop offset="0.25" stop-color="{'#110e1f' if eclipse else '#1a1530'}"/>
  <stop offset="1" stop-color="#0b0912"/>
</linearGradient>
<linearGradient id="rimFade" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{COLD}" stop-opacity="0"/>
  <stop offset="0.5" stop-color="{COLD}" stop-opacity="1"/>
  <stop offset="1" stop-color="{COLD}" stop-opacity="0"/>
</linearGradient>
<clipPath id="groundClip"><path id="groundPath" d="M0,{H} L0,{f(hy(0))} A{hR},{hR} 0 0 1 {W},{f(hy(W))} L{W},{H} Z"/></clipPath>
<mask id="groundMask" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
  <path d="M0,{H} L0,{f(hy(0))} A{hR},{hR} 0 0 1 {W},{f(hy(W))} L{W},{H} Z" fill="white"/>
  <path d="{cleft}" fill="black"/>
</mask>
<clipPath id="cleftClip"><path d="{cleft}"/></clipPath>
<radialGradient id="corona" cx="{sx}" cy="{sy}" r="{mr * 2.1}" gradientUnits="userSpaceOnUse">
  <stop offset="0.45" stop-color="#ffffff" stop-opacity="0"/>
  <stop offset="0.475" stop-color="{GOLD_HI}" stop-opacity="1"/>
  <stop offset="0.52" stop-color="#f1ecff" stop-opacity="0.7"/>
  <stop offset="0.68" stop-color="#9d92ff" stop-opacity="0.22"/>
  <stop offset="1" stop-color="#6e63c9" stop-opacity="0"/>
</radialGradient>
<radialGradient id="moonDark" cx="0.62" cy="0.3" r="0.95">
  <stop offset="0" stop-color="#272038"/>
  <stop offset="0.6" stop-color="#14101f"/>
  <stop offset="1" stop-color="#0b0912"/>
</radialGradient>
<radialGradient id="relic" cx="800" cy="800" r="140" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="{GOLD}" stop-opacity="0.55"/>
  <stop offset="1" stop-color="{GOLD}" stop-opacity="0"/>
</radialGradient>
<linearGradient id="shaft" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#d9d4ff" stop-opacity="0.1"/>
  <stop offset="1" stop-color="#d9d4ff" stop-opacity="0"/>
</linearGradient>
"""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           defs(extra),
           f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
           f'<rect width="{W}" height="{H}" filter="url(#nebula)" opacity="{0.2 if eclipse else 0.3}"/>',
           f'<rect width="{W}" height="{H}" fill="url(#backGlow)"/>',
           stars(rng, 420 if eclipse else 260, region=(0, 0, W, 640), avoid=[(sx, sy, 150), (mx, my, mr + 6)],
                 bright=1.25 if eclipse else 0.9)]

    # órbita grabada en el cielo: de la posición de la luna al eclipse
    def bez(t, p0, p1, p2, p3):
        u = 1 - t
        return (u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1])

    P0, P1, P2, P3 = (1520, 330), (1360, 140), (1010, 150), (sx, sy)
    P4, P5, P6 = (600, 720), (330, 500), (60, 250)
    arc1 = [bez(i / 80, P0, P1, P2, P3) for i in range(81)]
    arc2 = [bez(i / 80, P3, (sx - 70, sy + 150), (420, 640), (90, 470)) for i in range(81)]
    orbit = arc1 + arc2[1:]
    d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in orbit)
    out.append(f'<path d="{d}" fill="none" stroke="#d6cdea" stroke-width="1" opacity="{0.3 if eclipse else 0.42}"/>')
    tk = []
    for i in range(0, len(orbit) - 1, 3):
        (x0, y0), (x1, y1) = orbit[i], orbit[i + 1]
        dx, dy = x1 - x0, y1 - y0
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        L = 8 if i % 15 == 0 else 4
        tk.append(f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x0 + nx * L)}" y2="{f(y0 + ny * L)}"/>')
    out.append(f'<g stroke="#d6cdea" stroke-width="0.8" opacity="{0.25 if eclipse else 0.38}">{"".join(tk)}</g>')

    # dial grabado alrededor del punto de eclipse (destino del gesto)
    if not eclipse:
        dial = []
        for k in range(72):
            a = 2 * math.pi * k / 72
            r0 = 132
            r1 = r0 + (10 if k % 6 == 0 else 5)
            dial.append(f'<line x1="{f(sx + math.cos(a) * r0)}" y1="{f(sy + math.sin(a) * r0)}" '
                        f'x2="{f(sx + math.cos(a) * r1)}" y2="{f(sy + math.sin(a) * r1)}"/>')
        out.append(f'<g stroke="#d6cdea" stroke-width="0.8" opacity="0.3">{"".join(dial)}</g>')
        out.append(f'<circle cx="{sx}" cy="{sy}" r="{mr}" fill="none" stroke="#d6cdea" stroke-width="0.8" '
                   f'stroke-dasharray="2 5" opacity="0.45"/>')

    # estrella / eclipse
    if eclipse:
        out.append(f'<circle cx="{sx}" cy="{sy}" r="{mr * 4}" fill="#8a7dff" opacity="0.12" filter="url(#blurXL)"/>')
        rays = []
        rr = random.Random(5)
        for k in range(120):
            a = 2 * math.pi * k / 120 + rr.uniform(-0.01, 0.01)
            r0 = mr * 1.08
            r1 = mr * (1.5 + rr.random() * (1.6 if k % 4 == 0 else 0.7))
            rays.append(f'<line x1="{f(sx + math.cos(a) * r0)}" y1="{f(sy + math.sin(a) * r0)}" '
                        f'x2="{f(sx + math.cos(a) * r1)}" y2="{f(sy + math.sin(a) * r1)}"/>')
        out.append(f'<g stroke="#efe9ff" stroke-width="0.7" opacity="0.45">{"".join(rays)}</g>')
        out.append(f'<circle cx="{sx}" cy="{sy}" r="{mr * 2.1}" fill="url(#corona)"/>')
        out.append(f'<circle cx="{sx}" cy="{sy}" r="{mr}" fill="#07060b"/>')
        # perla de Baily: un único punto cálido en el limbo
        bx, by = sx + mr * math.cos(math.radians(-38)), sy + mr * math.sin(math.radians(-38))
        out.append(f'<circle cx="{f(bx)}" cy="{f(by)}" r="10" fill="{GOLD_HI}" opacity="0.6" filter="url(#glowL)"/>')
        out.append(f'<circle cx="{f(bx)}" cy="{f(by)}" r="3.2" fill="#fff6e0"/>')
    else:
        out.append(star_flare(sx, sy, 5.2))

    # ---- suelo
    G = [f'<g mask="url(#groundMask)">',
         f'<rect width="{W}" height="{H}" fill="url(#ground)"/>']
    # tramas de grabado: paralelas al horizonte (siguen la curvatura)
    lines = []
    r = hR - 6
    step = 5.0
    while r > hR - 520:
        lines.append(f'<circle cx="{hc[0]}" cy="{hc[1]}" r="{f(r)}"/>')
        step *= 1.035
        r -= step
    G.append(f'<g fill="none" stroke="{INK}" stroke-width="1" opacity="0.55">{"".join(lines)}</g>')
    # terrazas: escalones concéntricos
    terr = [hR - 34, hR - 92, hR - 172, hR - 286, hR - 440]
    for k, tr in enumerate(terr):
        G.append(f'<circle cx="{hc[0]}" cy="{hc[1]}" r="{f(tr - 8 - k * 3)}" fill="none" stroke="#07060b" '
                 f'stroke-width="{10 + k * 5}" opacity="0.5"/>')
        G.append(f'<circle cx="{hc[0]}" cy="{hc[1]}" r="{f(tr)}" fill="none" stroke="{"#4a4270" if eclipse else "#a79ccc"}" '
                 f'stroke-width="{1 + k * 0.25:.2f}" opacity="{0.5 if eclipse else 0.75}"/>')
    # sombras largas (contraluz): de las estructuras hacia el espectador
    if not eclipse:
        G.append(f'<path d="M640,560 L690,560 L640,1000 L420,1000 Z" fill="#05040a" opacity="0.5"/>')
        G.append(f'<path d="M910,560 L960,560 L1180,1000 L960,1000 Z" fill="#05040a" opacity="0.5"/>')
        G.append(f'<path d="M418,640 L446,640 L180,1000 L60,1000 Z" fill="#05040a" opacity="0.55"/>')
    G.append("</g>")
    out += G

    # luz de contorno en el horizonte (más intensa detrás del arco)
    if not eclipse:
        out.append(f'<path d="M0,{f(hy(0))} A{hR},{hR} 0 0 1 {W},{f(hy(W))}" fill="none" stroke="url(#rimFade)" stroke-width="2.2"/>')
    else:
        out.append(f'<path d="M300,{f(hy(300))} A{hR},{hR} 0 0 1 1300,{f(hy(1300))}" fill="none" stroke="#9d92ff" stroke-width="1" opacity="0.35"/>')

    # ---- grieta: a través de ella se ve el cielo del otro lado
    C = [f'<g clip-path="url(#cleftClip)">',
         f'<rect width="{W}" height="{H}" fill="#07060c"/>',
         stars(random.Random(8), 140, region=(500, top, 1100, H), bright=1.1)]
    # paredes interiores
    lwall = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in left_lip) + " L" + " L".join(f"{f(x)},{f(y)}" for x, y in reversed(lw_in)) + " Z"
    rwall = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in right_lip) + " L" + " L".join(f"{f(x)},{f(y)}" for x, y in reversed(rw_in)) + " Z"
    C.append(f'<path d="{lwall}" fill="{"#161223" if eclipse else "#1d182f"}"/>')
    C.append(f'<path d="{rwall}" fill="{"#1a1529" if eclipse else "#241e3a"}"/>')
    C.append(f'<path d="{lwall}" fill="url(#hatch45)" opacity="0.6"/>')
    C.append(f'<path d="{rwall}" fill="url(#hatch45)" opacity="0.6"/>')
    # escaleras talladas en las paredes
    steps = []
    for side, pts in ((-1, lw_in), (1, rw_in)):
        for i in range(8, 40, 2):
            x, y = pts[i]
            x0, y0 = (left_lip if side < 0 else right_lip)[i]
            mxs = (x + x0) / 2
            wstep = 6 + i * 0.45
            steps.append((mxs - wstep / 2, y - 4 + (y0 - y) * 0.2, wstep, side))
    for (x, y, w_, side) in steps:
        col = REVEAL if eclipse else "#8a80b5"
        op = 0.95 if eclipse else 0.6
        C.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x + w_)}" y2="{f(y)}" stroke="{col}" stroke-width="{1.4 if eclipse else 1}" opacity="{op}"'
                 + (' filter="url(#glowS)"' if eclipse else '') + '/>')
    # puentes de piedra hacia el relicario suspendido
    rx_, ry_, rr_ = 800, 806, 74
    lb = lip(0.62, -1)
    rb = lip(0.62, 1)
    for (x0, y0) in (lb, rb):
        side = -1 if x0 < 800 else 1
        x1 = rx_ + side * (rr_ + 6)
        C.append(f'<path d="M{f(x0)},{f(y0 + 8)} L{f(x1)},{f(ry_ + 2)} L{f(x1)},{f(ry_ + 10)} L{f(x0)},{f(y0 + 22)} Z" fill="#120e1d"/>')
        C.append(f'<path d="M{f(x0)},{f(y0 + 8)} L{f(x1)},{f(ry_ + 2)}" stroke="{REVEAL if eclipse else "#5d5484"}" '
                 f'stroke-width="1" opacity="{0.9 if eclipse else 0.6}"/>')
    # haz de luz del eclipse bajando por la grieta hasta el relicario
    if eclipse:
        C.append(f'<path d="M{sx - 20},{top} L{sx + 20},{top} L{sx + 70},{ry_} L{sx - 70},{ry_} Z" fill="url(#shaft)"/>')
    C.append("</g>")
    out += C

    # labios de la grieta: filo iluminado (contraluz) o apagado
    for pts in (left_lip, right_lip):
        d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)
        out.append(f'<path d="{d}" fill="none" stroke="{"#5b5288" if eclipse else "#cfc6ea"}" stroke-width="1.3" opacity="0.8"/>')

    # relicario suspendido: el disco que guarda el ojo
    if eclipse:
        out.append(f'<circle cx="{rx_}" cy="{ry_}" r="150" fill="url(#relic)"/>')
    out.append(f'<circle cx="{rx_}" cy="{ry_}" r="{rr_ + 8}" fill="#0d0a16"/>')
    ring_col = GOLD if eclipse else "#4b4370"
    out.append(f'<circle cx="{rx_}" cy="{ry_}" r="{rr_ + 4}" fill="none" stroke="{ring_col}" stroke-width="2"/>')
    tk = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        r0, r1 = rr_ + 9, rr_ + (17 if k % 4 == 0 else 13)
        tk.append(f'<line x1="{f(rx_ + math.cos(a) * r0)}" y1="{f(ry_ + math.sin(a) * r0)}" '
                  f'x2="{f(rx_ + math.cos(a) * r1)}" y2="{f(ry_ + math.sin(a) * r1)}"/>')
    out.append(f'<g stroke="{ring_col}" stroke-width="1" opacity="{0.95 if eclipse else 0.6}">{"".join(tk)}</g>')
    if not eclipse:
        # cerrado: una tapa de piedra con una sola rendija vertical
        out.append(f'<circle cx="{rx_}" cy="{ry_}" r="{rr_}" fill="#17122a"/>')
        out.append(f'<circle cx="{rx_}" cy="{ry_}" r="{rr_}" fill="url(#hatch45)" opacity="0.6"/>')
        out.append(f'<path d="M{rx_},{ry_ - rr_ + 10} Q{rx_ + 9},{ry_} {rx_},{ry_ + rr_ - 10} Q{rx_ - 9},{ry_} {rx_},{ry_ - rr_ + 10} Z" fill="#05040a"/>')

    # ---- estelas: losas con un óculo; en el eclipse la luz las atraviesa
    stele = []
    for t in (0.1, 0.22, 0.42):
        for side in (-1, 1):
            x, y = lip(t, side)
            x += side * (34 + 120 * t)
            h = 30 + 190 * t ** 1.05
            w_ = 12 + 46 * t
            stele.append((x, y, w_, h, side, t))
    for (x, y, w_, h, side, t) in stele:
        base = y + 6
        top_y = base - h
        body = (f"M{f(x - w_ / 2)},{f(base)} L{f(x - w_ / 2 * 0.88)},{f(top_y + w_ * 0.3)} "
                f"Q{f(x)},{f(top_y - w_ * 0.12)} {f(x + w_ / 2 * 0.88)},{f(top_y + w_ * 0.3)} L{f(x + w_ / 2)},{f(base)} Z")
        if not eclipse:
            out.append(f'<path d="M{f(x - w_ / 2)},{f(base)} L{f(x + side * 70 * t - w_ * 0.3)},{f(base + 150 * t + 16)} '
                       f'L{f(x + side * 70 * t + w_ * 0.7)},{f(base + 150 * t + 20)} L{f(x + w_ / 2)},{f(base)} Z" fill="#05040a" opacity="0.5"/>')
        out.append(f'<path d="{body}" fill="#120e1d"/>')
        out.append(f'<path d="{body}" fill="url(#hatch45)" opacity="0.4"/>')
        hr = w_ * 0.2
        hy_ = top_y + w_ * 0.62
        if not eclipse:
            ex = x - side * w_ / 2 * 0.88
            out.append(f'<path d="M{f(x - side * w_ / 2)},{f(base)} L{f(ex)},{f(top_y + w_ * 0.3)} Q{f(x - side * w_ * 0.2)},{f(top_y - w_ * 0.06)} {f(x)},{f(top_y - w_ * 0.04)}" '
                       f'stroke="#d9d1f0" stroke-width="1.1" fill="none" opacity="0.85"/>')
            out.append(f'<circle cx="{f(x)}" cy="{f(hy_)}" r="{f(hr)}" fill="#2b2448"/>')
        else:
            out.append(f'<circle cx="{f(x)}" cy="{f(hy_)}" r="{f(hr * 2.2)}" fill="{REVEAL}" opacity="0.35" filter="url(#glowL)"/>')
            out.append(f'<circle cx="{f(x)}" cy="{f(hy_)}" r="{f(hr)}" fill="#e8eeff"/>')
            for k in range(3):
                yy = hy_ + hr * 2.2 + k * (h * 0.12)
                out.append(f'<line x1="{f(x - w_ * 0.16)}" y1="{f(yy)}" x2="{f(x + w_ * 0.16)}" y2="{f(yy)}" '
                           f'stroke="{REVEAL}" stroke-width="{0.8 + t * 1.6:.1f}" opacity="0.8" filter="url(#glowS)"/>')

    # ---- senderos revelados: el suelo se vuelve un iris alrededor de la grieta
    if eclipse:
        vx, vy = 800, top + 2
        g = [f'<g mask="url(#groundMask)" filter="url(#glowS)" fill="none" stroke="{REVEAL}" stroke-linecap="round">']
        # fibras del iris: radiales desde el punto de fuga bajo el arco
        for k in range(-13, 14):
            if k == 0:
                continue
            a = math.radians(90 + k * 6.2)
            x1, y1 = vx + math.cos(a) * 1400, vy + math.sin(a) * 1400
            x0, y0 = vx + math.cos(a) * 70, vy + math.sin(a) * 70
            op = 0.95 if k % 2 else 0.55
            g.append(f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" y2="{f(y1)}" stroke-width="{1.5 if k % 2 else 1}" '
                     f'stroke-dasharray="{"1 9" if k % 2 else "1 14"}" opacity="{op}"/>')
        # anillos del iris en perspectiva (siguen las terrazas)
        for k, tr in enumerate([hR - 92, hR - 172, hR - 286]):
            span = 420 + k * 180
            g.append(f'<path d="M{f(hc[0] - span)},{f(hy(hc[0] - span, tr))} A{tr},{tr} 0 0 1 {f(hc[0] + span)},{f(hy(hc[0] + span, tr))}" '
                     f'stroke-width="{1.3 + k * 0.3:.1f}" opacity="{0.75 - k * 0.12:.2f}" stroke-dasharray="{"4 6" if k == 1 else "none"}"/>')
        g.append("</g>")
        out.append("\n".join(g))

    # ---- aguja (izquierda)
    sbx, sby, stx, sty = 432, 652, 446, 262
    out.append(f'<path d="M{sbx - 17},{sby} L{stx - 7},{sty + 18} L{stx},{sty} L{stx + 7},{sty + 18} L{sbx + 17},{sby} Z" fill="#100d1a"/>')
    if not eclipse:
        out.append(f'<path d="M{sbx + 17},{sby} L{stx + 7},{sty + 18} L{stx},{sty}" stroke="#dcd4f2" stroke-width="1.3" fill="none"/>')
    else:
        out.append(f'<circle cx="{stx}" cy="{sty - 6}" r="12" fill="{REVEAL}" opacity="0.6" filter="url(#glowL)"/>')
        out.append(f'<circle cx="{stx}" cy="{sty - 6}" r="2.6" fill="#eef2ff"/>')
        out.append(f'<path d="M{stx},{sty + 30} V{sby - 20}" stroke="{REVEAL}" stroke-width="1.2" stroke-dasharray="3 9" filter="url(#glowS)"/>')
    out.append(f'<path d="M{sbx - 26},{sby + 6} L{sbx + 26},{sby + 6} L{sbx + 20},{sby - 6} L{sbx - 20},{sby - 6} Z" fill="#0d0a16"/>')

    # ---- arco apuntado: el umbral
    base_y = top + 10
    ax_o, ax_i, apex_o, apex_i = 182, 140, 168, 214
    arch = (f"M{800 - ax_o},{base_y} C{800 - ax_o},{base_y - 200} {800 - 96},{apex_o + 60} 800,{apex_o} "
            f"C{800 + 96},{apex_o + 60} {800 + ax_o},{base_y - 200} {800 + ax_o},{base_y} "
            f"L{800 + ax_i},{base_y} C{800 + ax_i},{base_y - 180} {800 + 74},{apex_i + 50} 800,{apex_i} "
            f"C{800 - 74},{apex_i + 50} {800 - ax_i},{base_y - 180} {800 - ax_i},{base_y} Z")
    out.append(f'<path d="{arch}" fill="#0f0c18"/>')
    out.append(f'<path d="{arch}" fill="url(#hatch45)" opacity="0.35"/>')
    inner_l = f"M{800 - ax_i},{base_y} C{800 - ax_i},{base_y - 180} {800 - 74},{apex_i + 50} 800,{apex_i}"
    inner_r = f"M{800 + ax_i},{base_y} C{800 + ax_i},{base_y - 180} {800 + 74},{apex_i + 50} 800,{apex_i}"
    if not eclipse:
        for d in (inner_l, inner_r):
            out.append(f'<path d="{d}" stroke="{COLD}" stroke-width="2" fill="none" opacity="0.9"/>')
        out.append(f'<path d="M{800 - ax_o},{base_y} C{800 - ax_o},{base_y - 200} {800 - 96},{apex_o + 60} 800,{apex_o} '
                   f'C{800 + 96},{apex_o + 60} {800 + ax_o},{base_y - 200} {800 + ax_o},{base_y}" stroke="#9d93c6" '
                   f'stroke-width="1" fill="none" opacity="0.6"/>')
    else:
        # glifos tallados en el intradós que se encienden
        for d in (inner_l, inner_r):
            out.append(f'<path d="{d}" stroke="{REVEAL}" stroke-width="2.2" fill="none" stroke-dasharray="2 10" '
                       f'transform="translate(0,0)" filter="url(#glowS)"/>')
        for d in (inner_l, inner_r):
            out.append(f'<path d="{d}" stroke="{GOLD_HI}" stroke-width="0.8" fill="none" opacity="0.5"/>')
    # dovelas: juntas radiales
    for k in range(1, 12):
        t = k / 12
        for side in (-1, 1):
            u = 1 - t
            def cb(p0, p1, p2, p3):
                return (u ** 3 * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t ** 3 * p3)
            xo = 800 + side * cb(ax_o, ax_o, 96, 0)
            yo = cb(base_y, base_y - 200, apex_o + 60, apex_o)
            xi = 800 + side * cb(ax_i, ax_i, 74, 0)
            yi = cb(base_y, base_y - 180, apex_i + 50, apex_i)
            out.append(f'<line x1="{f(xo)}" y1="{f(yo)}" x2="{f(xi)}" y2="{f(yi)}" stroke="#2a2340" stroke-width="1"/>')
    # clave
    kcol = GOLD if eclipse else "#1c1729"
    out.append(f'<path d="M786,{apex_o - 6} L814,{apex_o - 6} L808,{apex_i + 4} L792,{apex_i + 4} Z" fill="{kcol}"'
               + (' filter="url(#glowS)"' if eclipse else '') + '/>')
    if not eclipse:
        out.append(f'<path d="M786,{apex_o - 6} L814,{apex_o - 6}" stroke="#d9d1f0" stroke-width="1"/>')
    # zócalos del arco
    for side in (-1, 1):
        x0 = 800 + side * (ax_o + ax_i) / 2
        out.append(f'<path d="M{f(x0 - 34)},{base_y + 10} L{f(x0 + 34)},{base_y + 10} L{f(x0 + 28)},{base_y - 14} L{f(x0 - 28)},{base_y - 14} Z" fill="#0d0a16"/>')

    # ---- luna (aproximación): oscura, sólo un filo creciente hacia la estrella
    if not eclipse:
        out.append(f'<circle cx="{mx}" cy="{my}" r="{mr}" fill="url(#moonDark)"/>')
        dx, dy = sx - mx, sy - my
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        out.append(f'<clipPath id="moonClip"><circle cx="{mx}" cy="{my}" r="{mr}"/></clipPath>')
        out.append(f'<g clip-path="url(#moonClip)"><circle cx="{f(mx)}" cy="{f(my)}" r="{mr}" fill="#cfc6e6"/>'
                   f'<circle cx="{f(mx - ux * 13)}" cy="{f(my - uy * 13)}" r="{mr}" fill="url(#moonDark)"/>'
                   f'<rect x="{mx - mr}" y="{my - mr}" width="{2 * mr}" height="{2 * mr}" fill="url(#hatch45)" opacity="0.35"/></g>')
        for rr_m in (0.35, 0.6, 0.82):
            out.append(f'<circle cx="{mx}" cy="{my}" r="{f(mr * rr_m)}" fill="none" stroke="#ffffff" stroke-width="0.6" opacity="0.07"/>')
        # gesto: chevrons sobre la órbita, de la luna hacia el arco
        for t in (0.52, 0.64, 0.76):
            x, y = bez(t + 0.05, P0, P1, P2, P3)
            x1, y1 = bez(t + 0.06, P0, P1, P2, P3)
            a = math.atan2(y1 - y, x1 - x)
            c1 = (x - 8 * math.cos(a - 0.6), y - 8 * math.sin(a - 0.6))
            c2 = (x - 8 * math.cos(a + 0.6), y - 8 * math.sin(a + 0.6))
            out.append(f'<path d="M{f(c1[0])},{f(c1[1])} L{f(x)},{f(y)} L{f(c2[0])},{f(c2[1])}" fill="none" '
                       f'stroke="#e9e3ff" stroke-width="1.2" opacity="0.75"/>')

    # viñeta inferior
    out.append(f'<rect x="0" y="{H - 220}" width="{W}" height="220" fill="#07060b" opacity="0.0"/>')
    out.append(grain(0.1))
    out.append(plate())
    out.append("</svg>")
    anchors = dict(star=[sx, sy], moon=[mx, my, mr], relic=[rx_, ry_, rr_], arch_apex=[800, apex_o],
                   spire=[stx, sty], horizon=top)
    return "\n".join(out), anchors


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, (svg, anchors) in {"a1": a1(), "a2": scene(False), "a3": scene(True)}.items():
        (OUT / f"{name}.svg").write_text(svg)
        (OUT / f"{name}.json").write_text(json.dumps(anchors, indent=1))
