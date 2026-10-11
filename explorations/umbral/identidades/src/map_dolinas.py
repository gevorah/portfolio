"""Propuesta I · Las Dolinas — mapa pintado (equirectangular).

Casi todo el planeta es un banco de arena somero y claro (una plataforma de
carbonato que antes fue tierra firme). Cuando el mar subió, inundó los
cañones de sus antiguos ríos: hoy son lenguas de agua profunda, ramificadas,
que salen del Abismo y se adentran en el banco. Uno de esos ríos no termina
en su cañón: siguió por debajo del banco, y donde el techo de la cueva se
hundió quedaron las dolinas, en fila, como una línea de puntos.
"""

import math

from paint import Equirect, f, smooth, svg_to_png, write_svg, WORK

E = Equirect(2048, 1024)

DEEP = "#081b38"
ABYSS = "#05122a"
SLOPE = "#12466a"
BANK_LO = "#3aa3a8"
BANK = "#69c6bf"
BANK_HI = "#a9e3d5"
FLAT = "#e8efe1"
GRASS = "#2e7b72"
HOLE = "#04102a"
SAND = "#f5f0e2"
VEG = "#6a946a"
REEF = "#e1907c"

# el banco: un solo cuerpo que cubre el hemisferio visible
BANCO = [(-132, 6), (-126, 22), (-114, 30), (-106, 44), (-88, 50), (-70, 57), (-48, 55), (-30, 60), (-10, 56),
         (6, 58), (20, 50), (30, 41), (40, 30), (36, 18), (42, 6), (34, -8), (40, -20), (30, -34), (12, -42),
         (-6, -46), (-30, -44), (-50, -50), (-72, -44), (-92, -40), (-106, -30), (-120, -26), (-130, -12)]
# bancos menores en la cara oculta
MENORES = [
    [(112, 22), (130, 32), (152, 26), (160, 10), (142, 2), (120, 6)],
    [(150, -26), (166, -22), (172, -36), (156, -42)],
    [(70, 44), (86, 50), (98, 42), (84, 36)],
]

# cañones ahogados: (línea central [(lon,lat)], ancho en la boca, ancho en la cabeza) en grados
CANONES = [
    ([(42, 6), (30, 8), (16, 11), (2, 15), (-12, 19), (-22, 23), (-30, 26)], 6.0, 1.3),   # la Lengua
    ([(16, 11), (12, 0), (6, -10), (-2, -17)], 2.4, 0.7),
    ([(2, 15), (0, 26), (-4, 36), (-10, 42)], 2.2, 0.6),
    ([(-12, 19), (-16, 30), (-24, 37)], 1.3, 0.5),
    ([(-30, -47), (-30, -34), (-36, -24), (-46, -15), (-56, -10)], 5.0, 1.0),           # cañón del sur
    ([(-36, -24), (-26, -16), (-16, -12)], 1.6, 0.5),
    ([(-46, -15), (-52, -2), (-50, 6)], 1.4, 0.5),
    ([(-132, 8), (-118, 10), (-104, 14), (-96, 20)], 4.0, 0.9),                           # cañón del oeste
    ([(-118, 10), (-112, -2), (-104, -8)], 1.5, 0.5),
    ([(30, 41), (18, 40), (8, 46)], 2.6, 0.7),                                             # cañón del norte
]
# el río fósil continúa bajo el banco: dolinas en fila (lon, lat, radio)
DOLINAS = [(-38, 27.5, 1.5), (-47, 28.5, 2.2), (-57.5, 28, 4.6), (-69, 25, 2.0), (-78, 21.5, 1.4),
           (-86, 17.5, 1.0), (-93, 14, 0.7)]
SUELTAS = [(-20, 47, 0.8), (-70, 42, 0.9), (-62, -30, 1.0), (-8, -30, 0.8), (140, 16, 1.2)]
CAYOS = [(37, 34, 1.1, 120), (41, 26, 1.4, 100), (39.5, 18, 1.0, 85), (43, 10, 1.2, 80), (38, -4, 1.0, 70),
         (39, -15, 1.3, 60), (34, -27, 1.0, 40)]
ISLA = [(-122, 26), (-118, 31), (-113, 35), (-112, 34), (-116, 30), (-120.5, 25.5)]


def ribbon(center, w0, w1):
    """Polígono de un cauce que se estrecha de la boca (w0) a la cabeza (w1)."""
    pts = [E(lo, la) for lo, la in center]
    n = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        t = i / (n - 1)
        w = E.deg(w0 + (w1 - w0) * t ** 0.8) / 2
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    tip, a = pts[-1], pts[-2]
    dx, dy = tip[0] - a[0], tip[1] - a[1]
    ln = math.hypot(dx, dy) or 1
    cap = (tip[0] + dx / ln * E.deg(w1) * 0.6, tip[1] + dy / ln * E.deg(w1) * 0.6)
    return smooth(left + [cap] + right[::-1])


def poly(lonlat):
    return smooth(E.pts(lonlat))


def ellipse_deg(lon, lat, r, fill, extra=""):
    x, y = E(lon, lat)
    rx = E.deg(r) / max(math.cos(math.radians(lat)), 0.2)
    return f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx)}" ry="{f(E.deg(r))}" fill="{fill}" {extra}/>'


def cay(lo, la, s, rot, fill_sand, fill_veg):
    x, y = E(lo, la)
    rx, ry = E.deg(s) * 1.2, E.deg(s) * 0.34
    t = f'transform="rotate({rot} {f(x)} {f(y)})"'
    return (f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx)}" ry="{f(ry)}" fill="{fill_sand}" {t}/>'
            + (f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx * 0.6)}" ry="{f(ry * 0.45)}" fill="{fill_veg}" {t}/>' if fill_veg else ""))


def build():
    FU = f'filterUnits="userSpaceOnUse" x="-100" y="-100" width="{E.w + 200}" height="{E.h + 200}"'
    banks = [BANCO] + MENORES
    canyon_paths = [ribbon(c, w0 * 1.7, w1 * 1.6) for c, w0, w1 in CANONES]
    defs = f"""
<filter id="coast" {FU}>
  <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="3" seed="5" result="t"/>
  <feDisplacementMap in="SourceGraphic" in2="t" scale="14" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="coastS" {FU}>
  <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="2" seed="9" result="t"/>
  <feDisplacementMap in="SourceGraphic" in2="t" scale="6" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="soft" {FU}><feGaussianBlur stdDeviation="9"/></filter>
<filter id="softS" {FU}><feGaussianBlur stdDeviation="3.5"/></filter>
<filter id="wide" {FU}><feGaussianBlur stdDeviation="30"/></filter>
<clipPath id="bankClip"><path d="{' '.join(poly(b) for b in banks)}"/></clipPath>
<linearGradient id="bankG" gradientUnits="userSpaceOnUse" x1="{E(-130, 0)[0]}" y1="0" x2="{E(40, 0)[0]}" y2="0">
  <stop offset="0" stop-color="{BANK_LO}"/><stop offset="0.45" stop-color="{BANK}"/><stop offset="1" stop-color="{BANK_HI}"/>
</linearGradient>
<pattern id="ripples" width="24" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(-24)">
  <path d="M0,4 Q6,1 12,4 T24,4" fill="none" stroke="#f3fff8" stroke-width="1.5" opacity="0.6"/>
</pattern>
"""
    b = [f'<rect width="{E.w}" height="{E.h}" fill="{DEEP}"/>']
    for lo, la, r in [(150, 0, 50), (100, -20, 40), (-170, 40, 30), (0, -80, 40), (-40, 82, 40)]:
        b.append(ellipse_deg(lo, la, r, ABYSS, 'filter="url(#wide)"'))
    g = ['<g filter="url(#coast)">']
    for bk in banks:
        g.append(f'<path d="{poly(bk)}" fill="none" stroke="{SLOPE}" stroke-width="34" stroke-linejoin="round" filter="url(#soft)"/>')
    for bk in banks:
        g.append(f'<path d="{poly(bk)}" fill="url(#bankG)"/>')
    g.append("</g>")
    b.append("".join(g))

    # interior: vetas de pradera alineadas con la corriente, arenas a barlovento
    inner = ['<g clip-path="url(#bankClip)">']
    for (lo, la, ln, rot, op) in [(-100, 36, 12, -14, 0.5), (-78, 46, 10, -14, 0.45), (-110, -10, 12, -10, 0.5),
                                  (-80, -28, 14, -10, 0.5), (-20, -32, 10, -10, 0.45), (-36, 46, 8, -14, 0.4),
                                  (14, 30, 7, -20, 0.4), (-66, 8, 9, -12, 0.4), (-90, 0, 8, -12, 0.45),
                                  (130, 16, 8, -14, 0.6)]:
        x, y = E(lo, la)
        inner.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(E.deg(ln))}" ry="{f(E.deg(ln) * 0.12)}" fill="{GRASS}" '
                     f'opacity="{op}" filter="url(#softS)" transform="rotate({rot} {f(x)} {f(y)})"/>')
    east = [(6, 58), (20, 50), (30, 41), (40, 30), (36, 18), (42, 6), (34, -8), (40, -20), (30, -34)]
    inner.append(f'<path d="{smooth(E.pts(east), closed=False)}" fill="none" stroke="{FLAT}" stroke-width="60" '
                 f'filter="url(#soft)" opacity="0.8"/>')
    for lo, la, r in [(-60, 40, 7), (-4, 40, 6), (-104, -16, 6)]:
        inner.append(ellipse_deg(lo, la, r, "#c6ece0", 'filter="url(#soft)" opacity="0.55"'))
    inner.append("</g>")
    b.append("".join(inner))

    # cañones: bajíos blancos en los bordes, talud oscuro y agua profunda
    b.append('<g filter="url(#coastS)">' + "".join(
        f'<path d="{p}" fill="none" stroke="{FLAT}" stroke-width="14" stroke-linejoin="round" filter="url(#softS)" opacity="0.85"/>'
        for p in canyon_paths) + "</g>")
    b.append('<g filter="url(#coastS)">' + "".join(
        f'<path d="{p}" fill="none" stroke="{SLOPE}" stroke-width="7" filter="url(#softS)"/>' for p in canyon_paths)
        + "".join(f'<path d="{p}" fill="{DEEP}"/>' for p in canyon_paths) + "</g>")
    # deltas de marea en la cabeza de los cañones
    for (lo, la, rot) in [(-31, 27.5, 200), (-58, -9, 160), (-95, 21, 210), (-2, -18, 120), (-11, 43, 250)]:
        x, y = E(lo, la)
        s = E.deg(3.4)
        fan = smooth([(x, y), (x + s * 0.9, y - s * 0.7), (x + s * 1.3, y), (x + s * 0.9, y + s * 0.7)])
        b.append(f'<g transform="rotate({rot} {f(x)} {f(y)})"><path d="{fan}" fill="{FLAT}" opacity="0.7" filter="url(#softS)"/>'
                 f'<path d="{fan}" fill="url(#ripples)"/></g>')
    reef = [(lo + 2.5, la) for lo, la in east[2:]]
    b.append(f'<path d="{smooth(E.pts(reef), closed=False)}" fill="none" stroke="{REEF}" stroke-width="3" '
             f'stroke-dasharray="3 5" opacity="0.8" filter="url(#coast)"/>')

    # el río fósil bajo el banco y las dolinas
    river = smooth([E(-30, 26)] + [E(lo, la) for lo, la, _ in DOLINAS], closed=False)
    b.append(f'<path d="{river}" fill="none" stroke="{BANK_LO}" stroke-width="10" opacity="0.6" stroke-linecap="round" filter="url(#softS)"/>')
    for lo, la, r in DOLINAS + SUELTAS:
        b.append(ellipse_deg(lo, la, r * 1.5, FLAT, 'filter="url(#softS)" opacity="0.8"'))
        b.append(ellipse_deg(lo, la, r * 1.18, SLOPE))
        b.append(ellipse_deg(lo, la, r, HOLE))
    b.append(ellipse_deg(-57.5, 28, 3.4, "none", f'stroke="{SLOPE}" stroke-width="6"'))
    b.append(ellipse_deg(-57.5, 28, 2.5, "#020818"))

    for lo, la, s, rot in CAYOS:
        b.append(cay(lo, la, s, rot, SAND, VEG))
    b.append(f'<path d="{poly(ISLA)}" fill="{SAND}"/>')
    b.append(f'<path d="{poly([(-120.5, 26.5), (-117.5, 30.5), (-114, 33.5), (-116.5, 29.5)])}" fill="{VEG}"/>')
    return b, defs


def build_mask():
    out = [f'<rect width="{E.w}" height="{E.h}" fill="black"/>']
    for lo, la, s, rot in CAYOS:
        out.append(cay(lo, la, s, rot, "white", None))
    out.append(f'<path d="{poly(ISLA)}" fill="white"/>')
    return out


if __name__ == "__main__":
    body, defs = build()
    p = write_svg("dolinas_albedo", E.w, E.h, "".join(body), defs)
    svg_to_png(p, WORK / "dolinas_albedo.png", E.w, E.h)
    p = write_svg("dolinas_land", E.w, E.h, "".join(build_mask()))
    svg_to_png(p, WORK / "dolinas_land.png", E.w, E.h)
