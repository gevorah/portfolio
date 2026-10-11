"""C · La Cintura — estudio cercano: desde lo alto de La Vertiente.

Estamos en el borde de la Vertiente, sobre basalto con musgo. Abajo, el
estrecho está vacío: arena negra de nuestro lado, lodo blanco del otro, y
en la línea donde se mezclaban las aguas, el arrecife del Encuentro. Un río
que antes desembocaba en el mar ahora cae en cascada al fondo seco. Enfrente
se levanta el otro lóbulo, La Tiza, como un monte blanco con dunas. El agua
del estrecho cuelga en una cinta de un lóbulo al otro; al fondo, donde ya
no llega la sombra, el estrecho sigue lleno.

Lenguaje: vector limpio, dos o tres tintas por material, sin texturas de
ruido; la forma la dan las siluetas y los valores.
"""

import math
import random
from pathlib import Path

from paint import f, smooth, svg_to_png, write_svg

OUTD = Path(__file__).resolve().parent.parent / "renders"
W, H = 1600, 1000


def P(pts):
    return smooth(pts)


def build():
    rng = random.Random(5)
    FU = f'filterUnits="userSpaceOnUse" x="-200" y="-200" width="{W + 400}" height="{H + 400}"'
    defs = f"""
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="480" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#101230"/><stop offset="0.75" stop-color="#2c3060"/><stop offset="1" stop-color="#4b4f7e"/>
</linearGradient>
<linearGradient id="tiza" x1="760" y1="0" x2="1600" y2="0" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#9d9a92"/><stop offset="0.35" stop-color="#cfc8b6"/><stop offset="1" stop-color="#ece5d2"/>
</linearGradient>
<linearGradient id="ribbon" x1="0" y1="80" x2="0" y2="520" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#0f474c"/><stop offset="0.6" stop-color="#2a7f7c"/><stop offset="1" stop-color="#6cc6b8"/>
</linearGradient>
<linearGradient id="floor" x1="0" y1="560" x2="0" y2="900" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#5c6260"/><stop offset="1" stop-color="#2f3331"/>
</linearGradient>
<linearGradient id="mud" x1="0" y1="560" x2="0" y2="900" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#c9c6bb"/><stop offset="1" stop-color="#e3dccb"/>
</linearGradient>
<radialGradient id="corona" cx="1300" cy="118" r="66" gradientUnits="userSpaceOnUse">
  <stop offset="0.32" stop-color="#fff" stop-opacity="0"/><stop offset="0.36" stop-color="#fff2df" stop-opacity="0.95"/>
  <stop offset="0.6" stop-color="#cfc8ff" stop-opacity="0.3"/><stop offset="1" stop-color="#8b80d0" stop-opacity="0"/>
</radialGradient>
<filter id="b3" {FU}><feGaussianBlur stdDeviation="3"/></filter>
<filter id="b10" {FU}><feGaussianBlur stdDeviation="10"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.9  0 0 0 0 0.9  0 0 0 0 1  0 0 0 0.7 -0.3"/>
</filter>
"""
    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>']
    for _ in range(120):
        x, y = rng.uniform(0, W), rng.uniform(0, 420)
        b.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{rng.choice([0.5, 0.7, 1.0])}" fill="#e8e6ff" opacity="{rng.uniform(0.2, 0.75):.2f}"/>')
    b.append('<circle cx="1300" cy="118" r="66" fill="url(#corona)"/><circle cx="1300" cy="118" r="20" fill="#0b0c1c"/>')

    # ---- La Tiza: el otro lóbulo, un monte blanco que llena la derecha
    tiza = [(720, 470), (820, 400), (960, 320), (1120, 262), (1300, 228), (1480, 226), (1640, 240), (1640, 700), (720, 700)]
    b.append(f'<path d="{P(tiza)}" fill="url(#tiza)"/>')
    # sombra propia: el lado que mira al cuello queda en penumbra
    b.append(f'<path d="{P([(720, 470), (820, 400), (930, 336), (1000, 420), (980, 600), (720, 600)])}" fill="#7f7d7a" opacity="0.45"/>')
    # dunas en media luna siguiendo la curvatura del lóbulo
    for row in range(5):
        for j in range(9):
            x = 1000 + j * 70 + (row % 2) * 35 + rng.uniform(-8, 8)
            y = 300 + row * 34 + (x - 1300) ** 2 * 0.00012 + rng.uniform(-4, 4)
            if y > 470:
                continue
            s = 14 + row * 3
            b.append(f'<path d="M{f(x - s)},{f(y)} Q{f(x)},{f(y - s * 0.55)} {f(x + s)},{f(y)} Q{f(x)},{f(y - s * 0.2)} {f(x - s)},{f(y)} Z" fill="#c6ab79" opacity="0.8"/>')
    # escarcha en la cima del lóbulo
    b.append(f'<path d="{P([(1380, 232), (1450, 222), (1540, 226), (1600, 236), (1560, 252), (1480, 246), (1420, 250)])}" fill="#f4f7f8"/>')
    # acantilado de creta: cara vertical hacia el estrecho, con bandas de sílex
    cliff = [(720, 470), (760, 520), (840, 560), (980, 590), (1140, 610), (1320, 630), (1640, 650), (1640, 760), (1320, 730),
             (1140, 700), (980, 670), (840, 630), (760, 590), (720, 540)]
    b.append(f'<path d="{P(cliff)}" fill="#efe9d9"/>')
    b.append(f'<path d="{P([(720, 470), (760, 520), (840, 560), (980, 590), (1140, 610), (1320, 630), (1640, 650)] + [(1640, 662), (1320, 642), (1140, 622), (980, 602), (840, 572), (760, 532), (720, 484)])}" fill="#f8f5ec"/>')
    for k in range(3):
        pts = [(x, y + 22 + k * 20 + (x - 720) * 0.012 * k) for x, y in [(740, 520), (840, 575), (980, 606), (1140, 628), (1320, 650), (1640, 672)]]
        b.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#6c6a66" stroke-width="{2 - k * 0.4:.1f}" stroke-dasharray="14 5 3 5" opacity="0.6"/>')
    # cuevas de creta en la base
    for (x, y, w, h) in [(1010, 662, 34, 22), (1230, 690, 46, 28), (1480, 718, 40, 24)]:
        b.append(f'<path d="M{x - w / 2},{y} Q{x},{y - h * 1.5} {x + w / 2},{y} Z" fill="#a49e8f"/>')

    # ---- horizonte de La Vertiente (izquierda, lejos)
    far_v = [(-40, 420), (140, 400), (330, 410), (520, 438), (700, 470), (720, 520), (-40, 520)]
    b.append(f'<path d="{P(far_v)}" fill="#3f4d43"/>')
    b.append(f'<path d="{P([(-40, 420), (140, 400), (330, 410), (520, 438), (700, 470), (690, 478), (520, 448), (330, 420), (140, 412), (-40, 430)])}" fill="#6f8a5c"/>')

    # ---- al fondo, el estrecho sigue lleno: la sombra termina ahí
    wall = [(520, 524), (560, 486), (640, 462), (720, 458), (790, 476), (820, 524)]
    b.append(f'<path d="{P(wall)}" fill="#3aa3a0" opacity="0.9"/>')
    b.append(f'<path d="{smooth([(560, 486), (640, 462), (720, 458), (790, 476)], closed=False)}" stroke="#c9f4ea" stroke-width="3" fill="none"/>')
    b.append(f'<ellipse cx="680" cy="470" rx="160" ry="30" fill="#7fe0d2" opacity="0.25" filter="url(#b10)"/>')

    # ---- el fondo del estrecho, al aire
    floor_dark = [(-40, 520), (300, 520), (560, 520), (650, 520), (700, 540), (760, 600), (820, 680), (880, 780), (900, 1040), (-40, 1040)]
    b.append(f'<path d="{P(floor_dark)}" fill="url(#floor)"/>')
    floor_white = [(650, 520), (720, 540), (840, 600), (1000, 650), (1200, 690), (1640, 740), (1640, 1040), (900, 1040),
                   (880, 780), (820, 680), (760, 600), (700, 540)]
    b.append(f'<path d="{P(floor_white)}" fill="url(#mud)"/>')
    # la cinta de agua proyecta una franja de luz verde sobre el fondo
    b.append(f'<path d="{P([(200, 620), (520, 590), (900, 640), (1250, 720), (1240, 760), (880, 690), (520, 640), (200, 670)])}" fill="#4fb8ad" opacity="0.18"/>')
    # charcas
    for (x, y, rx, ry) in [(420, 600, 90, 10), (1080, 690, 110, 12), (640, 740, 70, 9), (300, 700, 50, 6), (1400, 760, 90, 9)]:
        b.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="#2f8c8b"/>'
                 f'<ellipse cx="{x - rx * 0.25}" cy="{y - ry * 0.2}" rx="{rx * 0.5}" ry="{ry * 0.3}" fill="#8fd6c9" opacity="0.6"/>')
    # algas ámbar tumbadas en el fondo, orientadas por la corriente que se fue
    for i in range(30):
        x0 = rng.uniform(0, W)
        y0 = rng.uniform(540, 880)
        sc = (y0 - 500) / 400
        ln = 50 + 90 * sc
        pts = [(x0 + u * ln / 6, y0 + 4 * math.sin(u * 1.4 + i) * sc + u * 2 * sc) for u in range(7)]
        b.append(f'<path d="{smooth(pts, closed=False)}" stroke="#8e6a33" stroke-width="{1.2 + 2.5 * sc:.1f}" fill="none" stroke-linecap="round" opacity="0.55"/>')
    # el arrecife del Encuentro sobre la línea de mezcla
    seam = [(650, 520), (700, 540), (760, 600), (820, 680), (880, 780), (900, 900)]
    for i in range(80):
        t = i / 80
        k = t * (len(seam) - 1)
        j = int(k)
        fr = k - j
        x = seam[j][0] + (seam[j + 1][0] - seam[j][0]) * fr
        y = seam[j][1] + (seam[j + 1][1] - seam[j][1]) * fr
        s = 2 + 12 * t
        x += rng.uniform(-s * 1.5, s * 1.5)
        col = rng.choice(["#d98c68", "#c97660", "#e8a77e", "#b8675a"])
        b.append(f'<path d="M{f(x - s)},{f(y)} Q{f(x - s)},{f(y - s * 1.3)} {f(x)},{f(y - s * 1.4)} Q{f(x + s)},{f(y - s * 1.3)} {f(x + s)},{f(y)} Z" fill="{col}"/>')
    # escala: una figura caminando por el fondo
    fx, fy = 560, 650
    b.append(f'<path d="M{fx - 3},{fy} L{fx - 2},{fy - 11} Q{fx},{fy - 16} {fx + 2},{fy - 11} L{fx + 3},{fy} Z" fill="#111"/>'
             f'<circle cx="{fx}" cy="{fy - 17}" r="2.4" fill="#111"/>')

    # ---- primer plano: el borde de La Vertiente
    rock = [(-40, 640), (120, 660), (300, 720), (470, 800), (600, 880), (700, 960), (760, 1040), (-40, 1040)]
    b.append(f'<path d="{P(rock)}" fill="#24292b"/>')
    # cara del acantilado con columnas de basalto vista de canto
    face = [(300, 720), (470, 800), (600, 880), (700, 960), (760, 1040), (840, 1040), (780, 940), (690, 860), (560, 780), (400, 700)]
    b.append(f'<path d="{P(face)}" fill="#3a4245"/>')
    for i in range(16):
        t = i / 16
        x = 320 + t * 440
        y = 720 + t * 300
        b.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x + 50 + t * 30)}" y2="{f(y + 6)}" stroke="#1a1e20" stroke-width="2.4" opacity="0.7"/>')
    # musgo en lo alto, con su borde colgando
    moss = [(-40, 630), (120, 650), (300, 708), (470, 788), (600, 868), (700, 948), (760, 1040), (-40, 1040)]
    b.append(f'<path d="{P(moss)}" fill="#5f7a4e"/>')
    b.append(f'<path d="{P([(-40, 680), (140, 700), (320, 760), (480, 840), (560, 920), (600, 1040), (-40, 1040)])}" fill="#4d6640"/>')
    for i in range(26):
        t = i / 26
        x = t * 740
        y = 636 + t * 330 + (t ** 2) * 60
        ln = rng.uniform(10, 34)
        b.append(f'<path d="M{f(x)},{f(y)} q{f(rng.uniform(4, 10))},{f(ln * 0.5)} {f(rng.uniform(6, 14))},{f(ln)}" stroke="#5f7a4e" '
                 f'stroke-width="{rng.uniform(3, 7):.1f}" fill="none" stroke-linecap="round"/>')
    # matas y flores frías del musgo
    for i in range(60):
        x, y = rng.uniform(0, 520), rng.uniform(700, 1000)
        if y < 640 + x * 0.6:
            continue
        b.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{rng.uniform(2, 5):.1f}" fill="{rng.choice(["#86a36a", "#3f5636", "#a9c1a0"])}"/>')
    # el río: llega al borde y cae al estrecho seco
    bank = [(-40, 742), (60, 748), (150, 768), (240, 772), (330, 752), (400, 744), (420, 770), (330, 782), (240, 798), (150, 794), (60, 776), (-40, 776)]
    b.append(f'<path d="{P(bank)}" fill="#2c4a46"/>')
    water = [(-40, 750), (60, 755), (150, 774), (240, 778), (330, 759), (404, 754), (410, 764), (330, 772), (240, 790), (150, 786), (60, 768), (-40, 768)]
    b.append(f'<path d="{P(water)}" fill="#8fc3c3"/>')
    b.append(f'<path d="{smooth([(0, 758), (120, 768), (240, 782), (330, 764)], closed=False)}" stroke="#d6eeee" stroke-width="1.5" fill="none" opacity="0.7"/>')
    # cascada: una cortina que se abre al caer
    fall = [(404, 752), (430, 754), (470, 790), (500, 860), (520, 940), (540, 1040), (440, 1040), (448, 940), (440, 860), (420, 790)]
    b.append(f'<path d="{P(fall)}" fill="#cfe9e6" opacity="0.75"/>')
    for k in range(7):
        x0 = 410 + k * 3
        b.append(f'<path d="M{x0},{760} C{x0 + 30},{770} {x0 + 40 + k * 4},{850} {x0 + 40 + k * 12},{1040}" stroke="#ffffff" stroke-width="{2.5 - k * 0.2:.1f}" fill="none" opacity="0.55"/>')
    b.append(f'<ellipse cx="490" cy="1010" rx="110" ry="28" fill="#eef9f6" opacity="0.55" filter="url(#b10)"/>')

    # ---- la cinta de agua: el estrecho colgado de un lóbulo al otro
    top_e = [(-60, 40), (300, 70), (640, 150), (930, 280), (1120, 400), (1220, 470)]
    bot_e = [(1180, 480), (1060, 420), (880, 330), (620, 230), (300, 170), (-60, 160)]
    rib = smooth(top_e + bot_e)
    b.append(f'<path d="{rib}" fill="url(#ribbon)" opacity="0.86"/>')
    b.append(f'<clipPath id="rc"><path d="{rib}"/></clipPath>')
    rc = ['<g clip-path="url(#rc)">']
    # las dos aguas también se mezclan en el aire
    rc.append(f'<path d="{smooth([(600, 140), (800, 210), (980, 320), (1100, 420), (1060, 430), (920, 330), (760, 240), (590, 180)])}" fill="#9fe0d2" opacity="0.45"/>')
    rc.append(f'<path d="{smooth([(250, 80), (420, 110), (560, 160), (420, 150), (260, 120)])}" fill="#0b3a3f" opacity="0.6"/>')
    # vida que se fue con el agua
    rc.append('<path d="M0,0 C30,-22 60,-22 90,0 C60,8 30,8 0,0 Z M88,0 l44,4" fill="#0a2d31" stroke="#0a2d31" stroke-width="1.6" opacity="0.85" transform="translate(360,120) rotate(10)"/>')
    for i in range(28):
        x, y = 760 + rng.uniform(-60, 60), 250 + rng.uniform(-20, 20) + (rng.uniform(-60, 60)) * 0.4
        rc.append(f'<path d="M0,0 c5,-3 10,-3 14,0 l4,-3 l0,6 l-4,-3 c-4,3 -9,3 -14,0 Z" fill="#0a2d31" opacity="0.75" transform="translate({f(x)},{f(y)}) rotate(24)"/>')
    rc.append("</g>")
    b += rc
    b.append(f'<path d="{smooth(bot_e, closed=False)}" stroke="#d6fbf0" stroke-width="3" fill="none" opacity="0.8"/>')
    b.append(f'<path d="{smooth(top_e, closed=False)}" stroke="#7fc9c0" stroke-width="1.2" fill="none" opacity="0.6"/>')
    for i in range(40):
        t = rng.uniform(0.05, 0.95)
        k = t * (len(bot_e) - 1)
        j = int(k)
        fr = k - j
        x = bot_e[j][0] + (bot_e[j + 1][0] - bot_e[j][0]) * fr
        y = bot_e[j][1] + (bot_e[j + 1][1] - bot_e[j][1]) * fr + 4
        ln = rng.uniform(20, 110)
        b.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x)}" y2="{f(y + ln)}" stroke="#bfe9e0" stroke-width="1" opacity="{rng.uniform(0.25, 0.55):.2f}" '
                 f'stroke-dasharray="{rng.randint(6, 14)} {rng.randint(4, 9)}"/>')
    b.append(f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="0.05"/>')
    return b, defs


if __name__ == "__main__":
    OUTD.mkdir(exist_ok=True)
    body, defs = build()
    p = write_svg("study_cintura", W, H, "".join(body), defs)
    svg_to_png(p, OUTD / "ii-c-estudio.png", W, H)
