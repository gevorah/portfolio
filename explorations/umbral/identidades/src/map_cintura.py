"""Propuesta II · La Cintura — mapas polares de los dos lóbulos.

Umbral es un binario de contacto: dos cuerpos que se tocaron y se quedaron
pegados. El punto más bajo del planeta es la cintura, así que todo el agua
acaba allí: un único estrecho que da la vuelta al cuello. Cada lóbulo se
pinta como un disco: el centro es su cima (la parte más alta y fría, con
escarcha), el borde es el estrecho. Los ríos bajan siempre hacia el borde.

Lóbulo mayor · La Vertiente: basalto y musgo, húmedo, con ríos.
Lóbulo menor · La Tiza: creta blanca y dunas, seco; su costa es un
acantilado blanco que vuelve el agua de su lado lechosa y turquesa.
"""

import math
import random

from paint import blob, f, smooth, svg_to_png, write_svg, WORK

S = 1024
C = S / 2
R = 500  # radio del disco = ángulo máximo (la cintura)


def polar(t, a_deg):
    """t: 0 cima … 1 cintura; a: azimut en grados."""
    a = math.radians(a_deg)
    return C + R * t * math.cos(a), C + R * t * math.sin(a)


def ring_path(t_of_a, n=120):
    return smooth([polar(t_of_a(360 * i / n), 360 * i / n) for i in range(n)])


def river(start_a, t0, t1, wander, rng, steps=14):
    pts = []
    a = start_a
    for i in range(steps + 1):
        t = t0 + (t1 - t0) * i / steps
        a += wander * math.sin(i * 1.3 + start_a) + rng.uniform(-1.2, 1.2)
        pts.append(polar(t, a))
    return pts


FU = f'filterUnits="userSpaceOnUse" x="-50" y="-50" width="{S + 100}" height="{S + 100}"'
DEFS = f"""
<filter id="edge" {FU}>
  <feTurbulence type="fractalNoise" baseFrequency="0.03" numOctaves="3" seed="3" result="t"/>
  <feDisplacementMap in="SourceGraphic" in2="t" scale="12" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="soft" {FU}><feGaussianBlur stdDeviation="8"/></filter>
<filter id="softS" {FU}><feGaussianBlur stdDeviation="2.5"/></filter>
<filter id="wide" {FU}><feGaussianBlur stdDeviation="22"/></filter>
"""


def shore_a(a):
    # costa de La Vertiente: entrantes donde desembocan los ríos
    return 0.80 + 0.025 * math.sin(math.radians(a) * 3 + 0.6) + 0.018 * math.sin(math.radians(a) * 7 + 2.0) \
        - 0.05 * sum(math.exp(-((((a - r) + 180) % 360 - 180) / 5) ** 2) for r in (20, 95, 160, 230, 300))


def shore_b(a):
    return 0.77 + 0.02 * math.sin(math.radians(a) * 4 + 1.1) + 0.012 * math.sin(math.radians(a) * 9)


def vertiente(mask=False):
    rng = random.Random(4)
    b = []
    if mask:
        b.append(f'<rect width="{S}" height="{S}" fill="black"/>')
        b.append(f'<path d="{ring_path(shore_a)}" fill="white" filter="url(#edge)"/>')
        return b
    # estrecho: de aguas someras oscuras a la fosa del cuello
    b.append(f'<rect width="{S}" height="{S}" fill="#0b2a31"/>')
    b.append(f'<circle cx="{C}" cy="{C}" r="{R * 0.93}" fill="#14454a" filter="url(#wide)"/>')
    b.append(f'<path d="{ring_path(lambda a: shore_a(a) + 0.06)}" fill="#1f5f5c" filter="url(#soft)"/>')
    # bosques de algas en las aguas someras (ámbar apagado)
    for i in range(70):
        a = rng.uniform(0, 360)
        t = shore_a(a) + rng.uniform(0.02, 0.07)
        x, y = polar(t, a)
        b.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{rng.uniform(4, 9):.1f}" fill="#7b6a3a" opacity="0.45" filter="url(#softS)"/>')
    # tierra
    land = ring_path(shore_a)
    b.append(f'<g filter="url(#edge)"><path d="{land}" fill="none" stroke="#2a2b2c" stroke-width="7"/>'
             f'<path d="{land}" fill="#5d7651"/></g>')
    # anillo de praderas más claras a media ladera y bosque oscuro junto a los ríos
    b.append(f'<path d="{ring_path(lambda a: 0.62 + 0.04 * math.sin(math.radians(a) * 5))}" fill="none" '
             f'stroke="#809a68" stroke-width="70" opacity="0.6" filter="url(#soft)"/>')
    # tierras altas de basalto
    hl = ring_path(lambda a: 0.42 + 0.05 * math.sin(math.radians(a) * 6 + 1) + 0.03 * math.sin(math.radians(a) * 11))
    b.append(f'<g filter="url(#edge)"><path d="{hl}" fill="#454a4b"/></g>')
    b.append(f'<path d="{hl}" fill="none" stroke="#5d7651" stroke-width="30" opacity="0.5" filter="url(#soft)"/>')
    # crestas radiales en el basalto
    for k in range(18):
        a = k * 20 + rng.uniform(-6, 6)
        p = [polar(t, a + 4 * math.sin(t * 9)) for t in (0.17, 0.25, 0.33, 0.4)]
        b.append(f'<path d="{smooth(p, closed=False)}" fill="none" stroke="#2c3032" stroke-width="5" opacity="0.7" filter="url(#softS)"/>')
    # escarcha en la cima, con dedos por los valles
    cap = ring_path(lambda a: 0.17 + 0.05 * math.cos(math.radians(a) * 5) ** 8 + 0.02 * math.sin(math.radians(a) * 13))
    b.append(f'<g filter="url(#edge)"><path d="{cap}" fill="#e6edf0"/></g>')
    # ríos: bajan desde la escarcha hasta los entrantes de la costa
    for ra in (20, 95, 160, 230, 300):
        main = river(ra - 8, 0.2, shore_a(ra) + 0.01, 2.2, rng)
        main[-1] = polar(shore_a(ra) + 0.01, ra)
        b.append(f'<path d="{smooth(main, closed=False)}" fill="none" stroke="#2c4a46" stroke-width="9" opacity="0.6" filter="url(#softS)"/>')
        b.append(f'<path d="{smooth(main, closed=False)}" fill="none" stroke="#a7c5c6" stroke-width="3.2" stroke-linecap="round"/>')
        for k in range(3):
            t0 = 0.3 + k * 0.13
            trib = river(ra + rng.choice([-1, 1]) * rng.uniform(14, 22), t0, t0 + 0.14, 1.0, rng, steps=5)
            trib.append(polar(t0 + 0.2, ra - 8 + 2.2 * 6))
            b.append(f'<path d="{smooth(trib[:-1], closed=False)}" fill="none" stroke="#a7c5c6" stroke-width="1.6" opacity="0.85"/>')
    # lagos de montaña
    for a, t, r in [(60, 0.5, 9), (200, 0.56, 12), (270, 0.46, 7), (130, 0.66, 8)]:
        x, y = polar(t, a)
        b.append(f'<path d="{smooth(blob(x, y, r, [(2, 0.2, 0.4), (3, 0.12, 1.0)]))}" fill="#2f5c60" stroke="#a7c5c6" stroke-width="1"/>')
    # deltas de los ríos en el estrecho
    for ra in (20, 95, 160, 230, 300):
        x, y = polar(shore_a(ra) + 0.035, ra)
        b.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="16" fill="#6d7c5a" opacity="0.55" filter="url(#softS)"/>')
    return b


def tiza(mask=False):
    rng = random.Random(8)
    b = []
    if mask:
        b.append(f'<rect width="{S}" height="{S}" fill="black"/>')
        b.append(f'<path d="{ring_path(shore_b)}" fill="white" filter="url(#edge)"/>')
        return b
    # agua lechosa de creta
    b.append(f'<rect width="{S}" height="{S}" fill="#2c8c96"/>')
    b.append(f'<path d="{ring_path(lambda a: shore_b(a) + 0.1)}" fill="#55b8b4" filter="url(#wide)"/>')
    b.append(f'<path d="{ring_path(lambda a: shore_b(a) + 0.035)}" fill="#8fd6c9" filter="url(#soft)"/>')
    land = ring_path(shore_b)
    # acantilado blanco
    b.append(f'<g filter="url(#edge)"><path d="{land}" fill="none" stroke="#f7f4ec" stroke-width="14"/>'
             f'<path d="{land}" fill="#ddd5c0"/></g>')
    b.append(f'<path d="{ring_path(lambda a: shore_b(a) - 0.04)}" fill="none" stroke="#c8bea6" stroke-width="10" opacity="0.7" filter="url(#softS)"/>')
    # meseta interior un poco más cálida
    b.append(f'<path d="{ring_path(lambda a: 0.55 + 0.04 * math.sin(math.radians(a) * 3))}" fill="#e3d6b6" opacity="0.7" filter="url(#soft)"/>')
    # campos de dunas en media luna, todas mirando a sotavento
    for (ca, ct, rows, cols) in [(40, 0.42, 4, 6), (170, 0.5, 3, 7), (290, 0.38, 4, 5)]:
        for i in range(rows):
            for j in range(cols):
                a = ca + (j - cols / 2) * 6 + (i % 2) * 3 + rng.uniform(-1.5, 1.5)
                t = ct + (i - rows / 2) * 0.05 + rng.uniform(-0.01, 0.01)
                x, y = polar(t, a)
                rot = a + 90
                s = rng.uniform(7, 11)
                d = (f"M{f(x - s)},{f(y)} Q{f(x)},{f(y - s * 1.1)} {f(x + s)},{f(y)} "
                     f"Q{f(x)},{f(y - s * 0.5)} {f(x - s)},{f(y)} Z")
                b.append(f'<path d="{d}" fill="#c9ad7c" transform="rotate({rot:.1f} {f(x)} {f(y)})"/>')
    # cauces secos y dolinas de creta
    for ra in (100, 220, 340):
        p = river(ra, 0.2, shore_b(ra), 1.6, rng)
        b.append(f'<path d="{smooth(p, closed=False)}" fill="none" stroke="#b9ad93" stroke-width="2" opacity="0.8"/>')
    for i in range(26):
        x, y = polar(rng.uniform(0.25, 0.7), rng.uniform(0, 360))
        b.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{rng.uniform(2, 4.5):.1f}" fill="#a69a80" opacity="0.8"/>')
    cap = ring_path(lambda a: 0.11 + 0.025 * math.sin(math.radians(a) * 6))
    b.append(f'<g filter="url(#edge)"><path d="{cap}" fill="#eef2f3"/></g>')
    return b


if __name__ == "__main__":
    for name, fn in (("vertiente", vertiente), ("tiza", tiza)):
        p = write_svg(f"cintura_{name}", S, S, "".join(fn()), DEFS)
        svg_to_png(p, WORK / f"cintura_{name}.png", S, S)
        p = write_svg(f"cintura_{name}_land", S, S, "".join(fn(mask=True)), DEFS)
        svg_to_png(p, WORK / f"cintura_{name}_land.png", S, S)
