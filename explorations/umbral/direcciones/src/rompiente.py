"""A · La Rompiente — la monumentalidad del Gancho, hecha geografía.

Un promontorio de basalto que el mar socavó durante siglos hasta dejar un
voladizo curvo, como una ola de roca a punto de romper. No está pegado al
planeta: es el extremo de una cadena de islas, comparte sus estratos y tiene
a sus pies los restos de lo que ya se derrumbó (farallones, un arco).
"""

import math
import random
from pathlib import Path

from common import H, W, along, filters, grain, lerp_pts, stars
from paint import f, smooth, svg_to_png, write_svg

OUT = Path(__file__).resolve().parent.parent / "img"

ROCK = "#2a2539"
ROCK_HI = "#4a4163"
ROCK_SH = "#15121f"
SALT = "#9d93b8"
RIM = "#d8c9ff"
WARM = "#f0b48c"

# perfil de la Rompiente (vista lateral, horizonte en y=640): se usa en la lámina y en la órbita
PROFILE_TOP = [(2420, 642), (2300, 600), (2160, 566), (2020, 534), (1880, 500), (1760, 468), (1660, 440), (1590, 428), (1530, 404), (1480, 388), (1430, 356), (1372, 334), (1312, 304), (1252, 266),
       (1196, 236), (1136, 204), (1076, 178), (1014, 160), (952, 150), (892, 154), (842, 170), (800, 196),
       (768, 228), (750, 262)]
PROFILE_LIP = [(750, 262), (738, 296), (744, 326), (758, 344), (772, 338), (780, 318)]
PROFILE_UNDER = [(780, 318), (832, 300), (892, 302), (952, 320), (1012, 354), (1064, 400), (1102, 458), (1128, 526),
         (1148, 590), (1160, 642)]


def key_art():
    rng = random.Random(4)
    HZ = 640
    defs = filters(f"""
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#07081a"/><stop offset="0.55" stop-color="#17173a"/>
  <stop offset="0.86" stop-color="#3a3168"/><stop offset="1" stop-color="#6b4f86"/>
</linearGradient>
<radialGradient id="sunGlow" cx="1460" cy="{HZ - 10}" r="700" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#f3b48e" stop-opacity="0.75"/><stop offset="0.12" stop-color="#c88aa8" stop-opacity="0.45"/>
  <stop offset="0.45" stop-color="#6c56a8" stop-opacity="0.18"/><stop offset="1" stop-color="#3a2f70" stop-opacity="0"/>
</radialGradient>
<linearGradient id="sea" x1="0" y1="{HZ}" x2="0" y2="{H}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#2b2a55"/><stop offset="0.12" stop-color="#121735"/><stop offset="1" stop-color="#05081a"/>
</linearGradient>
<linearGradient id="rock" x1="0" y1="90" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#3b3352"/><stop offset="0.6" stop-color="{ROCK}"/><stop offset="1" stop-color="#1b1828"/>
</linearGradient>
<linearGradient id="haze" x1="0" y1="380" x2="0" y2="{HZ}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#4b3f82" stop-opacity="0"/><stop offset="1" stop-color="#6a568f" stop-opacity="0.75"/>
</linearGradient>
<radialGradient id="moon" cx="0.68" cy="0.4" r="0.8">
  <stop offset="0" stop-color="#e9e3f2"/><stop offset="0.45" stop-color="#b8b0cc"/><stop offset="1" stop-color="#5d5674"/>
</radialGradient>
""")
    b = [f'<rect width="{W}" height="{H}" fill="url(#sky)"/>', stars(rng, 380, HZ - 40)]
    b.append(f'<rect width="{W}" height="{HZ + 20}" fill="url(#sunGlow)"/>')
    # luna
    b.append('<circle cx="330" cy="200" r="58" fill="url(#moon)"/>')
    b.append('<path d="M330,142 A58,58 0 0 0 330,258 A40,58 0 0 1 330,142 Z" fill="#1b1a33" opacity="0.75"/>')

    # islas lejanas de la misma cadena, hacia la izquierda
    for (x, w, h) in [(80, 160, 22), (300, 90, 14), (470, 130, 26), (640, 60, 18)]:
        b.append(f'<path d="M{x},{HZ + 2} q{w * 0.25},{-h * 1.2} {w * 0.45},{-h} t{w * 0.55},{h} Z" fill="#2c2846" opacity="0.85"/>')

    # la Rompiente: una plataforma de isla cuyo extremo quedó en voladizo
    top, lip, under = PROFILE_TOP, PROFILE_LIP, PROFILE_UNDER
    body_pts = top + lip[1:] + under[1:] + [(2420, HZ + 2)]
    body = smooth(body_pts, tension=0.25)
    b.append(f'<path d="{body}" fill="url(#rock)" filter="url(#rough)"/>')
    b.append(f'<clipPath id="bc"><path d="{body}"/></clipPath>')
    g = ['<g clip-path="url(#bc)">']
    # estratos horizontales (ligeramente buzados): la forma está tallada a través de ellos
    for k in range(30):
        y = 140 + k * 17 + (k % 3) * 3
        x0 = 680
        while x0 < 1680:
            seg = rng.uniform(120, 420)
            pts = [(x, y + (x - 700) * 0.035 + 3 * math.sin(x * 0.02 + k)) for x in range(int(x0), int(min(x0 + seg, 1680)), 30)]
            if len(pts) > 2:
                thick = 3.2 if k % 4 == 0 else 1.4
                col = SALT if k % 5 == 2 else "#0e0c16"
                g.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="{col}" stroke-width="{thick}" '
                         f'opacity="{rng.uniform(0.25, 0.5):.2f}" filter="url(#roughS)"/>')
            x0 += seg + rng.uniform(10, 60)
    # cara frontal iluminada por el cielo del ocaso (modela el volumen)
    g.append(f'<path d="{smooth([(1100, 210), (1300, 300), (1480, 390), (1660, 440), (1660, HZ), (1300, HZ), (1180, 470), (1120, 330)], tension=0.3)}" '
             f'fill="#8e74b0" opacity="0.18" filter="url(#b20)"/>')
    g.append(f'<path d="{smooth([(1150, 330), (1240, 420), (1250, 560), (1200, HZ)], closed=False)}" fill="none" stroke="#0e0c16" stroke-width="30" opacity="0.25" filter="url(#b20)"/>')
    # cara inferior socavada: oscura, con goteras de sal colgando
    g.append(f'<path d="{smooth(lip[2:] + under[1:] + [(1300, HZ + 2), (1300, 470), (1000, 395), (820, 370)], tension=0.3)}" fill="{ROCK_SH}" opacity="0.72"/>')
    for i in range(70):
        t = rng.uniform(0.02, 0.8)
        x, y = along(under, t)
        ln = rng.uniform(6, 22)
        g.append(f'<path d="M{f(x - 2)},{f(y - 4)} L{f(x)},{f(y + ln)} L{f(x + 2)},{f(y - 4)} Z" fill="#8f86ad" opacity="0.5"/>')
    # luz del ocaso: borde superior y el lado derecho
    g.append(f'<path d="{smooth(top, closed=False)}" fill="none" stroke="{RIM}" stroke-width="18" opacity="0.28" filter="url(#b8)"/>')
    g.append(f'<rect x="1250" y="200" width="420" height="{HZ}" fill="{WARM}" opacity="0.13" filter="url(#b50)"/>')
    # neblina en la base: da escala
    g.append(f'<rect x="600" y="380" width="1100" height="{HZ - 380}" fill="url(#haze)"/>')
    g.append("</g>")
    b += g
    b.append(f'<path d="{smooth(top, closed=False)}" fill="none" stroke="{RIM}" stroke-width="2" opacity="0.85" filter="url(#roughS)"/>')
    b.append(f'<path d="{smooth(top[:9], closed=False)}" fill="none" stroke="{WARM}" stroke-width="2.4" opacity="0.65" filter="url(#roughS)"/>')
    # hierba y musgo oscuros en lo alto: es un lugar, no un objeto
    for i in range(120):
        t = rng.uniform(0, 1)
        x, y = along(top, t)
        h = rng.uniform(3, 9)
        b.append(f'<path d="M{f(x)},{f(y + 1)} l{f(rng.uniform(-2, 2))},{f(-h)}" stroke="#1a1626" stroke-width="{rng.uniform(1.2, 2.4):.1f}" stroke-linecap="round"/>')
    # bloques desprendidos sobre el escalón
    for (x, y, s) in [(1380, 336, 10), (1200, 240, 7), (1010, 162, 6)]:
        b.append(f'<path d="M{x - s},{y} l{s * 0.4},{-s} l{s * 1.2},{s * 0.1} l{s * 0.4},{s * 0.9} Z" fill="#2b2540"/>')
    # arco en la base: el mar ya atravesó la roca
    b.append(f'<path d="M1300,{HZ} C1298,580 1330,540 1370,540 C1410,540 1440,580 1442,{HZ} Z" fill="#7d63a6" opacity="0.92"/>')
    b.append(f'<path d="M1314,{HZ} C1316,594 1340,558 1370,558 C1400,558 1424,594 1426,{HZ} Z" fill="#e3a68e" opacity="0.45" filter="url(#b3)"/>')
    # dos cascadas de agua de lluvia que caen desde la meseta
    for (x0, y0, w) in [(1330, 314, 9), (1452, 374, 6)]:
        ln = HZ - y0 - 4
        for k in range(4):
            dx = (k - 1.5) * w * 0.35
            b.append(f'<path d="M{x0 + dx},{y0} C{x0 + dx - 4},{y0 + ln * 0.3} {x0 + dx - 6},{y0 + ln * 0.7} {x0 + dx - 10 - k * 2},{y0 + ln}" '
                     f'stroke="#ece6fa" stroke-width="{w * 0.3:.1f}" fill="none" opacity="{0.35 - k * 0.05:.2f}" filter="url(#b1)"/>')
        b.append(f'<ellipse cx="{x0 - 12}" cy="{HZ - 4}" rx="40" ry="10" fill="#ece6fa" opacity="0.35" filter="url(#b8)"/>')
    # goteo continuo desde el labio y la cara inferior
    for i in range(16):
        t = rng.uniform(0.0, 0.45)
        x, y = along(under, t)
        x += rng.uniform(-4, 4)
        b.append(f'<path d="M{f(x)},{f(y + 6)} L{f(x + rng.uniform(-3, 3))},{f(HZ - 8)}" stroke="#e6e0f6" stroke-width="{rng.uniform(0.6, 1.4):.1f}" '
                 f'opacity="{rng.uniform(0.15, 0.4):.2f}" stroke-dasharray="{rng.randint(10, 30)} {rng.randint(6, 18)}"/>')
    b.append(f'<ellipse cx="880" cy="{HZ - 6}" rx="240" ry="30" fill="#cfc4ee" opacity="0.28" filter="url(#b20)"/>')
    # cueva marina bajo el voladizo
    b.append(f'<path d="M1100,{HZ} C1104,600 1120,580 1136,584 C1150,590 1156,612 1158,{HZ} Z" fill="#0c0a14"/>')
    # farallones: lo que ya cayó
    for (x, w, h, lean) in [(600, 40, 150, 4), (668, 24, 90, -3), (520, 18, 46, 0), (760, 30, 60, 2)]:
        pts = [(x - w / 2, HZ + 2), (x - w * 0.45 + lean * 0.5, HZ - h * 0.6), (x - w * 0.3 + lean, HZ - h), (x + w * 0.25 + lean, HZ - h * 1.04),
               (x + w * 0.45 + lean * 0.4, HZ - h * 0.55), (x + w / 2, HZ + 2)]
        b.append(f'<path d="{smooth(pts, tension=0.3)}" fill="#221e32" filter="url(#rough)"/>')
        b.append(f'<path d="M{f(x + w * 0.25 + lean)},{f(HZ - h * 1.04)} L{f(x + w * 0.45 + lean * 0.4)},{f(HZ - h * 0.55)}" stroke="{RIM}" stroke-width="1.4" opacity="0.6"/>')
    # mar: bandas de mar de fondo, reflejo del resplandor y espuma al pie
    b.append(f'<rect x="0" y="{HZ}" width="{W}" height="{H - HZ}" fill="url(#sea)"/>')
    for k in range(26):
        y = HZ + 3 + k * k * 0.55 + k * 2
        amp = 1 + k * 0.35
        pts = [(x, y + amp * math.sin(x * 0.012 + k * 1.7)) for x in range(-40, W + 41, 40)]
        b.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#5b4f8c" stroke-width="{0.6 + k * 0.08:.2f}" opacity="{0.35 - k * 0.009:.2f}"/>')
    b.append(f'<ellipse cx="1440" cy="{HZ + 60}" rx="140" ry="220" fill="#f0b48c" opacity="0.18" filter="url(#b20)"/>')
    for k in range(18):
        y = HZ + 8 + k * 14
        w = 60 - k * 2
        b.append(f'<rect x="{1440 - w / 2 + rng.uniform(-20, 20):.0f}" y="{y}" width="{w}" height="1.6" fill="#f6c7a4" opacity="{0.6 - k * 0.03:.2f}"/>')
    for (x0, x1) in [(1160, 1640), (570, 790)]:
        pts = [(x, HZ + 2 + 2 * math.sin(x * 0.07)) for x in range(x0, x1, 12)]
        b.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#e8e2f6" stroke-width="2" opacity="0.6"/>')
    # aves diminutas: escala
    for (x, y, s) in [(980, 330, 5), (1010, 318, 4), (1032, 340, 3.5), (900, 360, 3)]:
        b.append(f'<path d="M{x - s},{y - s * 0.4} Q{x - s * 0.4},{y - s * 0.7} {x},{y} Q{x + s * 0.4},{y - s * 0.7} {x + s},{y - s * 0.4}" stroke="#0d0b16" stroke-width="1.2" fill="none"/>')
    b.append(grain())
    return b, defs


def orbital():
    rng = random.Random(9)
    CX, CY, R = 700, 580, 330
    defs = filters(f"""
<radialGradient id="ocean" cx="{CX + 150}" cy="{CY - 170}" r="{R * 1.55}" gradientUnits="userSpaceOnUse">
  <stop offset="0" stop-color="#3d3f7e"/><stop offset="0.3" stop-color="#1b2150"/><stop offset="0.7" stop-color="#0b1029"/><stop offset="1" stop-color="#04050d"/>
</radialGradient>
<radialGradient id="limb" cx="{CX}" cy="{CY}" r="{R}" gradientUnits="userSpaceOnUse">
  <stop offset="0.85" stop-color="#7d70d8" stop-opacity="0"/><stop offset="1" stop-color="#8f80ee" stop-opacity="0.35"/>
</radialGradient>
<radialGradient id="moon" cx="0.7" cy="0.35" r="0.8">
  <stop offset="0" stop-color="#e9e3f2"/><stop offset="0.5" stop-color="#a9a1bf"/><stop offset="1" stop-color="#3f3a55"/>
</radialGradient>
<clipPath id="disc"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>
<mask id="outside"><rect width="{W}" height="{H}" fill="white"/><circle cx="{CX}" cy="{CY}" r="{R - 1}" fill="black"/></mask>
<mask id="lit"><rect width="{W}" height="{H}" fill="black"/><circle cx="{CX + 140}" cy="{CY - 150}" r="{R * 1.25}" fill="white" filter="url(#b50)"/></mask>
""")
    b = [f'<rect width="{W}" height="{H}" fill="#0e0c13"/>', stars(rng, 420, H, avoid=[(CX, CY, R + 40)])]
    # atmósfera fina, sólo en el lado iluminado
    b.append(f'<circle cx="{CX}" cy="{CY}" r="{R + 7}" fill="none" stroke="#9d8eff" stroke-width="10" opacity="0.5" filter="url(#b8)" mask="url(#lit)"/>')
    b.append(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#ocean)"/>')
    g = ['<g clip-path="url(#disc)">']
    # nubes bajas y bandas de niebla: un mundo húmedo
    for (x, y, rx, ry, rot, op) in [(CX - 60, CY - 120, 260, 18, -18, 0.1), (CX + 40, CY + 40, 300, 14, -20, 0.08),
                                    (CX - 120, CY + 170, 200, 12, -16, 0.06), (CX + 170, CY - 40, 150, 10, -24, 0.1)]:
        g.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="#b9b0f0" opacity="{op}" transform="rotate({rot} {x} {y})" filter="url(#b8)"/>')
    # la isla larga corre pegada al limbo: vista desde aquí es una franja estrecha que abraza el borde
    def band(a0, a1, w0, w1, n=60):
        outer_pts, inner_pts = [], []
        for i in range(n + 1):
            t = i / n
            ang = math.radians(a0 + (a1 - a0) * t)
            w = w0 + (w1 - w0) * math.sin(math.pi * t) ** 0.6 + 4 * math.sin(t * 17)
            outer_pts.append((CX + (R + 2) * math.cos(ang), CY + (R + 2) * math.sin(ang)))
            inner_pts.append((CX + (R - w) * math.cos(ang), CY + (R - w) * math.sin(ang)))
        return outer_pts, inner_pts
    o_pts, i_pts = band(-68, 8, 6, 34)
    g.append(f'<path d="{smooth(i_pts, closed=False)}" fill="none" stroke="#dcd6f6" stroke-width="5" opacity="0.45" filter="url(#b1)"/>')
    g.append(f'<path d="{smooth(o_pts + i_pts[::-1], tension=0.3)}" fill="#4a4268"/>')
    # cresta iluminada a lo largo de la isla
    ridge = [(CX + (R - 6) * math.cos(math.radians(a)), CY + (R - 6) * math.sin(math.radians(a))) for a in range(-66, 6, 3)]
    g.append(f'<path d="{smooth(ridge, closed=False)}" fill="none" stroke="#b9a8e6" stroke-width="2" opacity="0.7"/>')
    # islotes que se desprenden hacia el interior del disco
    for (a_, d_, s_) in [(-20, 52, 7), (-8, 64, 5), (-34, 48, 5), (2, 50, 6), (12, 74, 4), (-46, 44, 4)]:
        x = CX + (R - d_) * math.cos(math.radians(a_))
        y = CY + (R - d_) * math.sin(math.radians(a_))
        g.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{s_ * 1.6}" ry="{s_ * 0.8}" fill="#3a3352" stroke="#dcd6f6" stroke-width="1" stroke-opacity="0.5" '
                 f'transform="rotate({a_ + 90} {f(x)} {f(y)})"/>')
    # terminador
    g.append(f'<circle cx="{CX - 230}" cy="{CY + 170}" r="{R * 1.05}" fill="#03030a" opacity="0.6" filter="url(#b50)"/>')
    g.append(f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#limb)" mask="url(#lit)"/>')
    g.append("</g>")
    b += g
    # la Rompiente sobre el limbo: el mismo perfil de la lámina, proyectado sobre la curvatura
    th0, k, hs = -60, 0.034, 0.15

    def M(x, y):
        th = math.radians(th0 + (x - 1160) * k)
        h = (640 - y) * hs
        return (CX + (R + h) * math.cos(th), CY + (R + h) * math.sin(th))
    prof = PROFILE_TOP + PROFILE_LIP[1:] + PROFILE_UNDER[1:]
    base_far = [M(1660, 642), M(1660, 700)]
    body = smooth([M(x, y) for x, y in prof] + [M(1160, 660), M(2420, 660)], tension=0.25)
    b.append(f'<g mask="url(#outside)"><path d="{body}" fill="none" stroke="#9d8eff" stroke-width="16" opacity="0.3" filter="url(#b8)"/>'
             f'<path d="{body}" fill="#2e2844"/></g>')
    b.append(f'<path d="{smooth([M(x, y) for x, y in PROFILE_TOP], closed=False)}" fill="none" stroke="#d8c9ff" stroke-width="2.2" opacity="0.95"/>')
    b.append(f'<path d="{smooth([M(x, y) for x, y in PROFILE_TOP[:9]], closed=False)}" fill="none" stroke="#f0b48c" stroke-width="1.8" opacity="0.7"/>')
    for kk in range(1, 6):
        yy = 180 + kk * 80
        pts = [M(x, yy + (x - 700) * 0.035) for x in range(760, 2400, 30)]
        b.append(f'<path d="{smooth(pts, closed=False)}" fill="none" stroke="#0e0c16" stroke-width="1" opacity="0.4" clip-path="url(#rc)" mask="url(#outside)"/>')
    b.append(f'<clipPath id="rc"><path d="{body}"/></clipPath>')
    # espuma al pie y el arco atravesado
    ax, ay = M(1370, 600)
    b.append(f'<circle cx="{f(ax)}" cy="{f(ay)}" r="4" fill="#7d63a6"/>')
    b.append(f'<path d="{smooth([M(x, 641) for x in range(760, 2400, 40)], closed=False)}" stroke="#e8e2f6" stroke-width="1.5" fill="none" opacity="0.6"/>')
    # luna
    b.append('<circle cx="1290" cy="230" r="42" fill="url(#moon)"/>')
    b.append(grain(0.05))
    return b, defs


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, fn in (("a-rompiente-clave", key_art), ("a-rompiente-orbita", orbital)):
        body, defs = fn()
        p = write_svg(name, W, H, "".join(body), defs)
        svg_to_png(p, OUT / f"{name}.png", W, H)
