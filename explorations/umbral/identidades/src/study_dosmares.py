"""C · Los Dos Mares — estudio cercano: la orilla del Lago Hondo.

El mar ligero ha subido y es un techo verde, translúcido, con peces dentro.
Donde termina la umbra, el techo baja hasta el mar de siempre y deja un
horizonte luminoso: fuera de la sombra sigue siendo de día. Debajo, el
fondo está al aire, pero el Lago Hondo sigue ahí: salmuera violeta, densa,
con olas lentas. Su orilla es una banda de mejillones negros y un encaje de
tapete bacteriano; junto a ella, gusanos de tubo con penachos rojos (el
único cálido). Un río de salmuera cae por un escarpe y un volcán de lodo
suelta burbujas que suben hasta el techo.
"""

import math
import random
from pathlib import Path

from paint import f, smooth, svg_to_png, write_svg

OUTD = Path(__file__).resolve().parent.parent / "renders"
W, H = 1600, 1000


def build():
    rng = random.Random(9)
    FU = f'filterUnits="userSpaceOnUse" x="-200" y="-200" width="{W + 400}" height="{H + 400}"'
    defs = f"""
<linearGradient id="under" x1="0" y1="0" x2="0" y2="560" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#173f3d"/><stop offset="0.7" stop-color="#1d3b45"/><stop offset="1" stop-color="#9fe2c9"/>
</linearGradient>
<linearGradient id="ceil" x1="0" y1="0" x2="0" y2="330" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#2f7468"/><stop offset="1" stop-color="#78c0a4"/>
</linearGradient>
<linearGradient id="lake" x1="0" y1="560" x2="0" y2="780" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#5d4c99"/><stop offset="0.45" stop-color="#3d2f7a"/><stop offset="1" stop-color="#1f1748"/>
</linearGradient>
<linearGradient id="ground" x1="0" y1="540" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#2d3b3a"/><stop offset="1" stop-color="#1b2224"/>
</linearGradient>
<filter id="b3" {FU}><feGaussianBlur stdDeviation="3"/></filter>
<filter id="b12" {FU}><feGaussianBlur stdDeviation="12"/></filter>
<filter id="b30" {FU}><feGaussianBlur stdDeviation="30"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.9  0 0 0 0 0.9  0 0 0 0 1  0 0 0 0.7 -0.3"/>
</filter>
"""
    b = [f'<rect width="{W}" height="{H}" fill="url(#under)"/>']
    # horizonte luminoso: fuera de la umbra es de día
    b.append(f'<ellipse cx="800" cy="548" rx="980" ry="40" fill="#d8ffe9" opacity="0.6" filter="url(#b30)"/>')
    b.append(f'<rect x="0" y="536" width="{W}" height="14" fill="#c9f5df" opacity="0.8"/>')
    # el techo: el mar ligero visto desde abajo, que se curva hasta el horizonte
    ceil = [(-60, -40), (1660, -40), (1660, 520), (1500, 470), (1280, 400), (1000, 360), (800, 352), (600, 360), (320, 400), (100, 470), (-60, 520)]
    b.append(f'<path d="{smooth(ceil)}" fill="url(#ceil)" opacity="0.92"/>')
    # bandas de ola en la cara inferior del techo (en perspectiva)
    for k in range(9):
        t = k / 8
        y = 60 + t * t * 290
        pts = [(x, y + 6 * math.sin(x * 0.012 + k) + (abs(x - 800) / 800) ** 2 * (130 * t + 40))
               for x in range(-60, 1661, 60)]
        b.append(f'<path d="{smooth(pts, closed=False)}" stroke="#bff0dc" stroke-width="{1 + t * 2.5:.1f}" fill="none" opacity="{0.15 + t * 0.25:.2f}"/>')
    # peces y una raya dentro del techo
    for i in range(22):
        x, y = 1050 + rng.uniform(-90, 90), 170 + rng.uniform(-30, 30)
        b.append(f'<path d="M0,0 c5,-3 10,-3 14,0 l4,-3 l0,6 l-4,-3 c-4,3 -9,3 -14,0 Z" fill="#14403b" opacity="0.7" transform="translate({f(x)},{f(y)}) rotate(-6)"/>')
    b.append('<path d="M0,0 C40,-26 80,-26 120,0 C80,10 40,10 0,0 Z M118,0 l56,3" fill="#14403b" stroke="#14403b" stroke-width="2" opacity="0.75" transform="translate(300,140) rotate(-4)"/>')
    b.append('<path d="M0,0 C26,-16 52,-16 78,0 C52,6 26,6 0,0 Z M76,0 l34,2" fill="#14403b" stroke="#14403b" stroke-width="1.5" opacity="0.6" transform="translate(620,250) rotate(6)"/>')
    # gotas que caen del techo
    for i in range(60):
        x = rng.uniform(0, W)
        y0 = 360 + (abs(x - 800) / 800) ** 2 * 140
        ln = rng.uniform(20, 120)
        b.append(f'<line x1="{f(x)}" y1="{f(y0)}" x2="{f(x)}" y2="{f(y0 + ln)}" stroke="#bff0dc" stroke-width="1" opacity="{rng.uniform(0.15, 0.4):.2f}" '
                 f'stroke-dasharray="{rng.randint(5, 14)} {rng.randint(4, 10)}"/>')

    # fondo al aire: lomas oscuras y un escarpe a la izquierda
    hills = [(-40, 560), (120, 520), (260, 470), (360, 470), (420, 540), (700, 560), (980, 548), (1180, 520), (1320, 530), (1640, 560), (1640, 700), (-40, 700)]
    b.append(f'<path d="{smooth(hills)}" fill="#26383a"/>')
    scarp = [(-40, 470), (60, 430), (200, 410), (300, 420), (330, 520), (380, 600), (-40, 620)]
    b.append(f'<path d="{smooth(scarp)}" fill="#1f2c2e"/>')
    b.append(f'<path d="{smooth([(60, 430), (200, 410), (300, 420)], closed=False)}" stroke="#7fae9a" stroke-width="2" fill="none" opacity="0.6"/>')
    # río de salmuera que cae despacio por el escarpe
    fall = [(250, 416), (282, 418), (300, 470), (318, 540), (330, 600), (296, 606), (282, 540), (262, 470)]
    b.append(f'<path d="{smooth(fall)}" fill="#5a43a6"/>')
    b.append(f'<path d="{smooth([(266, 418), (282, 470), (300, 540), (312, 600)], closed=False)}" stroke="#a48be6" stroke-width="3" fill="none" opacity="0.7"/>')
    b.append(f'<path d="{smooth([(150, 410), (200, 412), (250, 416)], closed=False)}" stroke="#5a43a6" stroke-width="6" fill="none"/>')
    # volcán de lodo con su penacho de burbujas
    cone = [(1120, 610), (1190, 520), (1214, 512), (1238, 520), (1310, 610)]
    b.append(f'<path d="{smooth(cone)}" fill="#4a4a42"/>')
    b.append(f'<path d="{smooth([(1190, 520), (1214, 512), (1238, 520), (1214, 526)])}" fill="#2a2a26"/>')
    b.append(f'<path d="{smooth([(1150, 600), (1196, 532), (1206, 560), (1170, 610)])}" fill="#6b6a5e" opacity="0.6"/>')
    for i in range(46):
        t = rng.random()
        y = 510 - t * 290
        x = 1214 + math.sin(t * 9 + i) * (6 + t * 30) + rng.uniform(-4, 4)
        b.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{1.5 + t * 3.5:.1f}" fill="none" stroke="#dff7ec" stroke-width="1" opacity="{0.7 - t * 0.4:.2f}"/>')

    # el Lago Hondo
    lake = [(80, 640), (240, 600), (520, 584), (840, 580), (1140, 592), (1420, 612), (1560, 650), (1470, 690), (1360, 690),
            (1240, 722), (1100, 740), (900, 742), (760, 764), (560, 752), (420, 748), (300, 720), (180, 712)]
    b.append(f'<path d="{smooth(lake)}" fill="url(#lake)"/>')
    b.append(f'<clipPath id="lk"><path d="{smooth(lake)}"/></clipPath>')
    lk = ['<g clip-path="url(#lk)">']
    # reflejo del techo y del horizonte luminoso
    lk.append(f'<rect x="0" y="582" width="{W}" height="16" fill="#c9f5df" opacity="0.35" filter="url(#b3)"/>')
    for k in range(10):
        y = 602 + k * k * 1.6 + k * 4
        pts = [(x, y + 3 * math.sin(x * 0.01 + k * 1.3)) for x in range(0, W + 1, 50)]
        lk.append(f'<path d="{smooth(pts, closed=False)}" stroke="{"#8fd9bd" if k % 3 == 0 else "#7a68c4"}" stroke-width="{1.2 + k * 0.4:.1f}" '
                  f'fill="none" opacity="{0.22 - k * 0.015:.2f}"/>')
    # olas lentas y gruesas
    for k in range(5):
        y = 640 + k * 22
        pts = [(x, y + 5 * math.sin(x * 0.006 + k)) for x in range(0, W + 1, 50)]
        lk.append(f'<path d="{smooth(pts, closed=False)}" stroke="#1a1340" stroke-width="{5 + k * 2}" fill="none" opacity="0.3"/>')
    lk.append("</g>")
    b += lk
    # orilla: tapete bacteriano (encaje claro) y banda de mejillones
    edge = [(180, 712), (300, 720), (420, 748), (560, 752), (760, 764), (900, 742), (1100, 740), (1240, 722), (1360, 690), (1470, 690), (1560, 650)]
    b.append(f'<path d="M-40,{H} L-40,720 ' + " ".join(f"L{x},{y}" for x, y in edge) + f' L1640,640 L1640,{H} Z" fill="url(#ground)"/>')
    for i in range(160):
        t = rng.random()
        k = t * (len(edge) - 1)
        j = int(k)
        fr = k - j
        x = edge[j][0] + (edge[j + 1][0] - edge[j][0]) * fr
        y = edge[j][1] + (edge[j + 1][1] - edge[j][1]) * fr + rng.uniform(2, 12)
        s = rng.uniform(4, 9)
        b.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(s)}" ry="{f(s * 0.55)}" fill="#141320" transform="rotate({rng.uniform(-40, 40):.0f} {f(x)} {f(y)})"/>')
        if rng.random() < 0.35:
            b.append(f'<ellipse cx="{f(x - s * 0.3)}" cy="{f(y - s * 0.2)}" rx="{f(s * 0.4)}" ry="{f(s * 0.15)}" fill="#7d6ccc" opacity="0.6"/>')
    # tapete bacteriano: un encaje claro con bordes festoneados y huecos
    top = [(x, y + 14) for x, y in edge]
    bot = [(x, y + 34 + (x % 7) * 2) for x, y in edge[::-1]]
    band = smooth(top + bot)
    b.append(f'<path d="{band}" fill="#e3dcc1" opacity="0.6"/>')
    b.append(f'<clipPath id="mc"><path d="{band}"/></clipPath>')
    holes = ['<g clip-path="url(#mc)">']
    for i in range(140):
        t = rng.random()
        k = t * (len(edge) - 1)
        j = int(k)
        fr = k - j
        x = edge[j][0] + (edge[j + 1][0] - edge[j][0]) * fr
        y = edge[j][1] + (edge[j + 1][1] - edge[j][1]) * fr + rng.uniform(18, 46)
        r = rng.uniform(2, 7)
        holes.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r * 1.6)}" ry="{f(r * 0.6)}" fill="#25302f"/>')
    holes.append("</g>")
    b += holes
    for i in range(70):
        t = rng.random()
        k = t * (len(edge) - 1)
        j = int(k)
        fr = k - j
        x = edge[j][0] + (edge[j + 1][0] - edge[j][0]) * fr
        y = edge[j][1] + (edge[j + 1][1] - edge[j][1]) * fr + rng.uniform(44, 60)
        b.append(f'<path d="M{f(x - 8)},{f(y)} q4,{rng.uniform(3, 8):.1f} 8,0 q4,{rng.uniform(3, 8):.1f} 8,0" stroke="#e3dcc1" stroke-width="2" fill="none" opacity="0.7"/>')
    # bancos de mejillones en primer plano
    for (cx, cy, n, sc) in [(140, 900, 40, 1.6), (520, 960, 30, 1.8), (1380, 920, 45, 1.7), (1000, 870, 20, 1.3)]:
        for i in range(n):
            x, y = cx + rng.gauss(0, 50 * sc), cy + rng.gauss(0, 14 * sc)
            s_ = rng.uniform(6, 11) * sc
            b.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(s_)}" ry="{f(s_ * 0.5)}" fill="#121119" transform="rotate({rng.uniform(-50, 50):.0f} {f(x)} {f(y)})"/>')
            if rng.random() < 0.4:
                b.append(f'<ellipse cx="{f(x - s_ * 0.3)}" cy="{f(y - s_ * 0.15)}" rx="{f(s_ * 0.45)}" ry="{f(s_ * 0.14)}" fill="#7d6ccc" opacity="0.55"/>')
    # gambas pálidas en enjambre sobre la orilla
    for i in range(40):
        x, y = 700 + rng.gauss(0, 60), 790 + rng.gauss(0, 10)
        b.append(f'<path d="M{f(x)},{f(y)} q3,-3 6,0" stroke="#f0d9c8" stroke-width="1.4" fill="none" opacity="0.8"/>')
    # gusanos de tubo con penacho rojo: el único acento cálido
    for (cx, cy, n, sc) in [(300, 900, 11, 1.2), (1250, 840, 8, 1.0), (620, 960, 6, 1.4)]:
        for i in range(n):
            x = cx + rng.gauss(0, 26 * sc)
            h = rng.uniform(50, 110) * sc
            y = cy + rng.uniform(-8, 8)
            lean = rng.uniform(-14, 14)
            w = 9 * sc
            b.append(f'<path d="M{f(x)},{f(y)} q{f(lean * 0.4)},{f(-h * 0.5)} {f(lean)},{f(-h)}" stroke="#bdb6a3" stroke-width="{f(w + 2)}" fill="none" stroke-linecap="round"/>')
            b.append(f'<path d="M{f(x)},{f(y)} q{f(lean * 0.4)},{f(-h * 0.5)} {f(lean)},{f(-h)}" stroke="#ece7d8" stroke-width="{f(w)}" fill="none" stroke-linecap="round"/>')
            for r in range(3):
                yy = y - h * (0.25 + r * 0.22)
                b.append(f'<line x1="{f(x + lean * (0.25 + r * 0.22) - w / 2)}" y1="{f(yy)}" x2="{f(x + lean * (0.25 + r * 0.22) + w / 2)}" y2="{f(yy + 2)}" stroke="#a9a290" stroke-width="1.2"/>')
            px, py = x + lean, y - h
            for k in range(7):
                ang = -90 + (k - 3) * 22 + lean
                b.append(f'<ellipse cx="{f(px + math.cos(math.radians(ang)) * 7 * sc)}" cy="{f(py + math.sin(math.radians(ang)) * 9 * sc)}" '
                         f'rx="{f(3.2 * sc)}" ry="{f(9 * sc)}" fill="{"#d24b45" if k % 2 else "#e8695a"}" '
                         f'transform="rotate({ang + 90:.0f} {f(px + math.cos(math.radians(ang)) * 7 * sc)} {f(py + math.sin(math.radians(ang)) * 9 * sc)})"/>')
    # escala: una figura en la orilla
    fx, fy = 1060, 776
    b.append(f'<path d="M{fx - 3.5},{fy} L{fx - 2.2},{fy - 13} Q{fx},{fy - 19} {fx + 2.2},{fy - 13} L{fx + 3.5},{fy} Z" fill="#0c0f10"/>'
             f'<circle cx="{fx}" cy="{fy - 20}" r="2.8" fill="#0c0f10"/><ellipse cx="{fx + 9}" cy="{fy + 1}" rx="10" ry="2" fill="#0c0f10" opacity="0.35"/>')
    b.append(f'<path d="M{fx - 4},{fy + 3} L{fx + 4},{fy + 3} L{fx + 2},{fy + 24} L{fx - 2},{fy + 24} Z" fill="#6c56b8" opacity="0.35"/>')
    b.append(f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="0.05"/>')
    return b, defs


if __name__ == "__main__":
    OUTD.mkdir(exist_ok=True)
    body, defs = build()
    p = write_svg("study_dosmares", W, H, "".join(body), defs)
    svg_to_png(p, OUTD / "iii-c-estudio.png", W, H)
