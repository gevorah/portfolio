"""Propuesta III · Los Dos Mares — mapa pintado (equirectangular).

Un océano sin continentes, de agua ligera y muy transparente: desde la
órbita se ve el fondo. En el fondo corre un rift (el Collar) y en sus
cubetas se acumula un segundo líquido, una salmuera densa y violeta que no
se mezcla. Son lagos dentro del mar, con orillas, olas lentas y ríos que
bajan de una cubeta a otra. La sombra de la luna sólo levanta el agua
ligera; la salmuera, pesada, se queda.
"""

import math

from paint import Equirect, blob, f, smooth, svg_to_png, write_svg, WORK

E = Equirect(2048, 1024)

ABYSS = "#082630"
PLAIN = "#0f3d40"
RISE = "#2f7466"
SHALLOW = "#79b59b"
RIFT = "#071f29"
BRINE = "#4b3893"
BRINE_HI = "#7d62c8"
MAT = "#e8e0c4"
MUSSEL = "#17161f"
SHOAL = "#eef0e2"

# eje del Collar: un rift sinuoso que cruza el planeta en diagonal
EJE = [(-170, -40), (-130, -34), (-95, -22), (-62, -8), (-30, 4), (-8, 10), (18, 20), (48, 30), (80, 38),
       (115, 40), (150, 34), (180, 26)]
# lagos de salmuera: (lon, lat, radio°, lóbulos)
LAGOS = [(-12, 9, 8.5, [(2, 0.18, 0.3), (3, 0.14, 1.2), (5, 0.06, 0.2)]),     # el Lago Hondo
         (12, 18, 3.6, [(2, 0.25, 1.0), (3, 0.1, 0.0)]),
         (28, 24, 2.2, [(2, 0.3, 0.5)]),
         (44, 29, 4.2, [(2, 0.2, 2.0), (4, 0.1, 0.5)]),
         (66, 35, 2.6, [(3, 0.2, 0.7)]),
         (-34, 2, 3.0, [(2, 0.3, 0.2)]),
         (-52, -5, 5.0, [(2, 0.22, 1.4), (3, 0.12, 0.3)]),
         (-74, -14, 2.4, [(2, 0.3, 0.9)]),
         (-92, -21, 3.4, [(3, 0.18, 0.4)]),
         (-120, -32, 2.6, [(2, 0.25, 0.1)]),
         (100, 40, 3.0, [(2, 0.2, 0.0)]),
         (140, 36, 2.0, [(2, 0.2, 0.0)])]
BAJOS = [(52, -30, 7, 200), (64, -22, 4, 230), (-100, 32, 5, 40), (150, -10, 6, 120)]


def lake_shape(lon, lat, r, lobes):
    x, y = E(lon, lat)
    k = 1 / max(math.cos(math.radians(lat)), 0.3)
    extra = [(7, 0.05, lon * 0.1), (11, 0.035, lat * 0.2), (17, 0.02, 1.0)]
    pts = blob(0, 0, E.deg(r), lobes + extra, n=120)
    return smooth([(x + px * k, y + py) for px, py in pts])


def build():
    FU = f'filterUnits="userSpaceOnUse" x="-100" y="-100" width="{E.w + 200}" height="{E.h + 200}"'
    defs = f"""
<filter id="edge" {FU}>
  <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="2" result="t"/>
  <feDisplacementMap in="SourceGraphic" in2="t" scale="7" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="soft" {FU}><feGaussianBlur stdDeviation="10"/></filter>
<filter id="softS" {FU}><feGaussianBlur stdDeviation="3"/></filter>
<filter id="wide" {FU}><feGaussianBlur stdDeviation="34"/></filter>
"""
    b = [f'<rect width="{E.w}" height="{E.h}" fill="{PLAIN}"/>']
    # fondos abisales y lomas que suben hacia la luz
    for lo, la, r in [(150, -20, 40), (-150, 30, 35), (60, -55, 40), (-60, 60, 30)]:
        x, y = E(lo, la)
        b.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(E.deg(r) * 1.3)}" ry="{f(E.deg(r))}" fill="{ABYSS}" filter="url(#wide)"/>')
    for lo, la, r, op in [(-40, 32, 18, 0.9), (30, -12, 16, 0.9), (-85, 8, 12, 0.7), (95, 12, 14, 0.7),
                          (55, -30, 10, 1.0), (-100, 32, 8, 1.0)]:
        x, y = E(lo, la)
        b.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(E.deg(r) * 1.25)}" ry="{f(E.deg(r))}" fill="{RISE}" opacity="{op}" filter="url(#wide)"/>')
    for lo, la, r in [(-40, 34, 7), (30, -12, 6), (55, -30, 5)]:
        x, y = E(lo, la)
        b.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(E.deg(r) * 1.3)}" ry="{f(E.deg(r))}" fill="{SHALLOW}" opacity="0.8" filter="url(#soft)"/>')
    # el rift: una fosa oscura con hombros claros
    eje = smooth(E.pts(EJE), closed=False)
    b.append(f'<path d="{eje}" fill="none" stroke="{RISE}" stroke-width="{E.deg(16)}" opacity="0.55" filter="url(#soft)"/>')
    b.append(f'<path d="{eje}" fill="none" stroke="{RIFT}" stroke-width="{E.deg(7)}" filter="url(#soft)"/>')
    # escarpes de falla paralelos al rift
    for off in (-5, -2.5, 3, 6):
        pts = [(lo, la + off + (0.8 if i % 2 else -0.8)) for i, (lo, la) in enumerate(EJE)]
        b.append(f'<path d="{smooth(E.pts(pts), closed=False)}" fill="none" stroke="#5c9a86" stroke-width="1.6" opacity="0.35" filter="url(#edge)"/>')
    # ríos de salmuera entre cubetas
    for i in range(len(LAGOS) - 1):
        a, c = LAGOS[i], LAGOS[i + 1]
        if abs(a[0] - c[0]) > 45:
            continue
        mx, my = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2 + (2 if i % 2 else -2)
        p = smooth(E.pts([(a[0], a[1]), (mx, my), (c[0], c[1])]), closed=False)
        b.append(f'<path d="{p}" fill="none" stroke="{BRINE}" stroke-width="3" opacity="0.9" filter="url(#edge)"/>')
    # lagos: tapete bacteriano claro, banda de mejillones, salmuera
    for lo, la, r, lobes in LAGOS:
        d = lake_shape(lo, la, r, lobes)
        b.append(f'<g filter="url(#edge)"><path d="{d}" fill="none" stroke="{MAT}" stroke-width="{3 + r * 0.6:.1f}" opacity="0.85"/>'
                 f'<path d="{d}" fill="none" stroke="{MUSSEL}" stroke-width="{1.5 + r * 0.3:.1f}"/>'
                 f'<path d="{d}" fill="{BRINE}"/></g>')
        x, y = E(lo, la)
        b.append(f'<ellipse cx="{f(x - E.deg(r) * 0.25)}" cy="{f(y - E.deg(r) * 0.2)}" rx="{f(E.deg(r) * 0.6)}" '
                 f'ry="{f(E.deg(r) * 0.35)}" fill="{BRINE_HI}" opacity="0.55" filter="url(#soft)"/>')
    # el agua ligera tiñe lo que se ve a través
    b.append(f'<rect width="{E.w}" height="{E.h}" fill="#1d5a55" opacity="0.18"/>')
    # volcanes de lodo junto a las orillas
    for lo, la in [(-2, 16), (-24, 4), (18, 13), (-44, -1), (40, 23), (-60, -12)]:
        x, y = E(lo, la)
        b.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="5" fill="#9c9b86"/><circle cx="{f(x)}" cy="{f(y)}" r="2" fill="#3a3a33"/>')
    # los bajos: las únicas arenas que asoman, en media luna
    for lo, la, r, rot in BAJOS:
        x, y = E(lo, la)
        s = E.deg(r)
        d = (f"M{f(x - s)},{f(y)} A{f(s)},{f(s * 0.8)} 0 0 1 {f(x + s)},{f(y)} "
             f"A{f(s * 0.86)},{f(s * 0.6)} 0 0 0 {f(x - s)},{f(y)} Z")
        b.append(f'<g transform="rotate({rot} {f(x)} {f(y)})"><path d="{d}" fill="{SHALLOW}" opacity="0.8" filter="url(#softS)"/>'
                 f'<path d="{d}" fill="{SHOAL}" transform="scale(1)" opacity="0.9"/></g>')
    return b, defs


def build_mask():
    out = [f'<rect width="{E.w}" height="{E.h}" fill="black"/>']
    for lo, la, r, rot in BAJOS:
        x, y = E(lo, la)
        s = E.deg(r)
        d = (f"M{f(x - s)},{f(y)} A{f(s)},{f(s * 0.8)} 0 0 1 {f(x + s)},{f(y)} "
             f"A{f(s * 0.86)},{f(s * 0.6)} 0 0 0 {f(x - s)},{f(y)} Z")
        out.append(f'<path d="{d}" fill="white" transform="rotate({rot} {f(x)} {f(y)})"/>')
    return out


if __name__ == "__main__":
    body, defs = build()
    p = write_svg("dosmares_albedo", E.w, E.h, "".join(body), defs)
    svg_to_png(p, WORK / "dosmares_albedo.png", E.w, E.h)
    p = write_svg("dosmares_land", E.w, E.h, "".join(build_mask()))
    svg_to_png(p, WORK / "dosmares_land.png", E.w, E.h)
