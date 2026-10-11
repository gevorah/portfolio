"""B · Distribución geográfica: mapas anotados + corte del fenómeno."""

import math
from pathlib import Path

from paint import Equirect, f, smooth, svg_to_png, write_svg, WORK

OUTD = Path(__file__).resolve().parent.parent / "renders"
W, H = 1600, 1180
MAP_H = 800
FONT = ("<style>@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600"
        "&amp;family=Space+Grotesk:wght@500;600&amp;display=swap');"
        ".l{font-family:'JetBrains Mono',monospace;font-size:15px;fill:#eef2f0}"
        ".s{font-family:'JetBrains Mono',monospace;font-size:12.5px;fill:#b9c4cc}"
        ".t{font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:600;fill:#eef2f0;letter-spacing:.04em}"
        ".k{font-family:'JetBrains Mono',monospace;font-size:12px;fill:#8d98a3;letter-spacing:.08em}"
        "</style>")
INK = "#0e0c13"


def label(x, y, lx, ly, text, sub=None, anchor="start", col="#eef2f0"):
    """Punto + línea guía + rótulo."""
    out = [f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(lx)}" y2="{f(ly)}" stroke="{col}" stroke-width="1" opacity="0.8"/>',
           f'<circle cx="{f(x)}" cy="{f(y)}" r="3" fill="{col}"/>']
    dx = 6 if anchor == "start" else -6
    out.append(f'<text class="l" x="{f(lx + dx)}" y="{f(ly + 5)}" text-anchor="{anchor}" '
               f'style="paint-order:stroke;stroke:{INK};stroke-width:4px">{text}</text>')
    if sub:
        out.append(f'<text class="s" x="{f(lx + dx)}" y="{f(ly + 23)}" text-anchor="{anchor}" '
                   f'style="paint-order:stroke;stroke:{INK};stroke-width:4px">{sub}</text>')
    return "".join(out)


def section_frame(title):
    return (f'<rect x="0" y="{MAP_H}" width="{W}" height="{H - MAP_H}" fill="#111019"/>'
            f'<text class="k" x="40" y="{MAP_H + 40}">CORTE · {title}</text>')


# ------------------------------------------------------------------ I
def dolinas():
    from map_dolinas import DOLINAS
    E = Equirect(1600, 800)
    img = (WORK / "dolinas_albedo.png").resolve()
    b = [FONT, f'<rect width="{W}" height="{H}" fill="{INK}"/>',
         f'<image href="file://{img}" x="0" y="0" width="1600" height="800"/>']
    # recorrido de la umbra: una banda que barre de oeste a este
    track = [E(lo, 24 + 4 * math.sin(math.radians(lo * 2))) for lo in range(-140, 60, 5)]
    b.append(f'<path d="{smooth(track, closed=False)}" fill="none" stroke="#1b1036" stroke-width="64" opacity="0.38" stroke-linecap="round"/>')
    b.append(f'<path d="{smooth(track, closed=False)}" fill="none" stroke="#c9b8ff" stroke-width="1.2" stroke-dasharray="6 8" opacity="0.9"/>')
    x, y = track[-1]
    b.append(f'<path d="M{f(x - 14)},{f(y - 9)} L{f(x)},{f(y)} L{f(x - 14)},{f(y + 9)}" fill="none" stroke="#c9b8ff" stroke-width="1.5"/>')
    # dolinas que se elevan bajo la sombra
    for lo, la, r in DOLINAS:
        cx, cy = E(lo, la)
        rr = E.deg(r) * 1.9 + 6
        b.append(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(rr)}" fill="none" stroke="#c9b8ff" stroke-width="1.4"/>')
    L = []
    L.append(label(*E(-57.5, 28), *E(-75, 52), "El Ojo", "dolina mayor · se eleva"))
    L.append(label(*E(-78, 21.5), *E(-110, 4), "fila de dolinas", "río fósil bajo el banco"))
    L.append(label(*E(10, 13), *E(28, 62), "la Lengua", "cañón ahogado"))
    L.append(label(*E(-40, -22), *E(-30, -62), "cañón del sur"))
    L.append(label(*E(-105, 16), *E(-150, 32), "cañón del oeste", anchor="start"))
    L.append(label(*E(-60, 0), *E(-80, -18), "el Banco", "2–10 m de agua"))
    L.append(label(*E(41, 26), *E(64, 24), "cayos de barlovento", "arena y arbusto"))
    L.append(label(*E(-117, 30), *E(-160, 52), "Isla Larga", "la única tierra alta"))
    L.append(label(*E(120, -10), *E(108, -32), "el Abismo", "agua profunda que no sube"))
    L.append(label(*E(-30, 27), *E(-12, 62), "delta de marea"))
    b += L
    b.append(f'<text class="s" x="{f(E(-135, 18)[0])}" y="{f(E(-135, 18)[1] + 30)}" style="fill:#d9ccff">recorrido de la umbra →</text>')
    # corte: banco, dolina, lente elevada
    y0 = MAP_H
    b.append(section_frame("POR EL OJO, DURANTE LA SOMBRA"))
    g = []
    sea = y0 + 170
    g.append(f'<rect x="80" y="{sea}" width="1440" height="30" fill="#5fc0b8"/>')
    g.append(f'<path d="M80,{sea + 30} H600 L612,{sea + 40} L640,{y0 + 330} L960,{y0 + 330} L988,{sea + 40} L1000,{sea + 30} H1520 V{H} H80 Z" fill="#cdbf9f"/>')
    g.append(f'<path d="M640,{y0 + 330} L960,{y0 + 330} L988,{sea + 40} L1000,{sea + 30} L600,{sea + 30} L612,{sea + 40} Z" fill="#0b2347" opacity="0.0"/>')
    # paredes con estalactitas y repisa
    for xx in range(618, 640, 6):
        g.append(f'<path d="M{xx},{sea + 60} l2,{14 + (xx % 5) * 2}" stroke="#8d7f63" stroke-width="2"/>')
    g.append(f'<rect x="80" y="{sea + 30}" width="520" height="8" fill="#e8e1cb"/><rect x="1000" y="{sea + 30}" width="520" height="8" fill="#e8e1cb"/>')
    # la lente
    g.append(f'<ellipse cx="800" cy="{y0 + 92}" rx="250" ry="34" fill="#0d2a4c"/>')
    g.append(f'<ellipse cx="800" cy="{y0 + 92}" rx="250" ry="6" fill="#d7e4d8" opacity="0.8"/>')
    g.append(f'<ellipse cx="800" cy="{y0 + 112}" rx="210" ry="9" fill="#7fe6d8" opacity="0.45"/>')
    for xx in range(600, 1010, 34):
        g.append(f'<line x1="{xx}" y1="{y0 + 122}" x2="{xx + 4}" y2="{sea}" stroke="#7fb8d8" stroke-width="1" opacity="0.5" stroke-dasharray="3 6"/>')
    g.append(f'<text class="s" x="1080" y="{y0 + 86}">el agua de la dolina sube como una lente</text>')
    g.append(f'<text class="s" x="1080" y="{y0 + 106}">banda lechosa = la capa de azufre del fondo</text>')
    g.append(f'<text class="s" x="1080" y="{sea + 64}" style="fill:#2a2a2a">el banco somero (2–10 m) no se mueve</text>')
    g.append(f'<text class="s" x="660" y="{y0 + 312}">pozo al aire: paredes con estalactitas</text>')
    b += g
    p = write_svg("diag_dolinas", W, H, "".join(b))
    svg_to_png(p, OUTD / "i-b-distribucion.png", W, H)


# ------------------------------------------------------------------ II
def cintura():
    va = (WORK / "cintura_vertiente.png").resolve()
    ti = (WORK / "cintura_tiza.png").resolve()
    b = [FONT, f'<rect width="{W}" height="{H}" fill="{INK}"/>',
         '<defs><clipPath id="ca"><circle cx="420" cy="400" r="340"/></clipPath>'
         '<clipPath id="cb"><circle cx="1180" cy="400" r="300"/></clipPath></defs>']
    # el estrecho: banda que une los dos bordes
    b.append('<path d="M420,60 C800,140 800,140 1180,100 L1180,700 C800,660 800,660 420,740 Z" fill="#1d5f60" opacity="0.6"/>')
    b.append('<path d="M760,90 C790,300 790,500 760,710" fill="none" stroke="#8fd6c9" stroke-width="2" stroke-dasharray="5 6" opacity="0.8"/>')
    b.append(f'<image href="file://{va}" x="80" y="60" width="680" height="680" clip-path="url(#ca)"/>')
    b.append(f'<image href="file://{ti}" x="880" y="100" width="600" height="600" clip-path="url(#cb)"/>')
    # sector que toca la sombra
    def sector(cx, cy, r0, r1, a0, a1):
        p0 = (cx + r0 * math.cos(math.radians(a0)), cy + r0 * math.sin(math.radians(a0)))
        p1 = (cx + r1 * math.cos(math.radians(a0)), cy + r1 * math.sin(math.radians(a0)))
        p2 = (cx + r1 * math.cos(math.radians(a1)), cy + r1 * math.sin(math.radians(a1)))
        p3 = (cx + r0 * math.cos(math.radians(a1)), cy + r0 * math.sin(math.radians(a1)))
        return (f"M{f(p0[0])},{f(p0[1])} L{f(p1[0])},{f(p1[1])} A{r1},{r1} 0 0 1 {f(p2[0])},{f(p2[1])} "
                f"L{f(p3[0])},{f(p3[1])} A{r0},{r0} 0 0 0 {f(p0[0])},{f(p0[1])} Z")
    b.append(f'<path d="{sector(420, 400, 272, 342, -40, 40)}" fill="#1b1036" opacity="0.45" stroke="#c9b8ff" stroke-width="1.4"/>')
    b.append(f'<path d="{sector(1180, 400, 232, 302, 140, 220)}" fill="#1b1036" opacity="0.45" stroke="#c9b8ff" stroke-width="1.4"/>')
    b.append('<path d="M740,330 C790,250 810,250 860,330" fill="none" stroke="#c9b8ff" stroke-width="1.6"/>')
    b.append('<text class="s" x="800" y="235" text-anchor="middle" style="fill:#d9ccff">arco de agua</text>')
    L = [label(420, 400, 230, 120, "la Escarcha", "cima de la Vertiente"),
         label(520, 330, 600, 80, "tierras altas", "basalto"),
         label(300, 560, 150, 700, "praderas de musgo"),
         label(560, 610, 470, 735, "ríos", "todos bajan al estrecho"),
         label(780, 520, 690, 640, "la Cintura", "el estrecho: único mar", anchor="end"),
         label(790, 420, 900, 760, "encuentro de aguas", "oscura · lechosa"),
         label(1180, 400, 1340, 80, "escarcha menor"),
         label(1100, 290, 990, 70, "dunas en media luna"),
         label(1300, 560, 1400, 760, "acantilado de creta", "agua turquesa lechosa")]
    b += L
    b.append('<text class="k" x="40" y="36">LÓBULO MAYOR · LA VERTIENTE — cada disco es un lóbulo visto desde su cima; el borde es la cintura</text>')
    b.append('<text class="k" x="1560" y="36" text-anchor="end">LÓBULO MENOR · LA TIZA</text>')
    y0 = MAP_H
    b.append(section_frame("POR EL CUELLO, DURANTE LA SOMBRA"))
    g = []
    # perfil del cuello: dos lóbulos y el estrecho entre ellos
    g.append(f'<path d="M80,{H} L80,{y0 + 190} C300,{y0 + 150} 560,{y0 + 170} 660,{y0 + 300} C720,{y0 + 330} 880,{y0 + 330} 940,{y0 + 300} '
             f'C1040,{y0 + 190} 1300,{y0 + 160} 1520,{y0 + 200} L1520,{H} Z" fill="#3b4140"/>')
    g.append(f'<path d="M940,{y0 + 300} C1040,{y0 + 190} 1300,{y0 + 160} 1520,{y0 + 200} L1520,{H} L940,{H} Z" fill="#d9d1bd"/>')
    g.append(f'<path d="M80,{y0 + 190} C300,{y0 + 150} 560,{y0 + 170} 660,{y0 + 300}" fill="none" stroke="#6f8a5c" stroke-width="7"/>')
    # nivel normal del mar (discontinuo) y el arco de agua
    g.append(f'<line x1="610" y1="{y0 + 245}" x2="990" y2="{y0 + 245}" stroke="#8fd6c9" stroke-width="1.4" stroke-dasharray="6 6"/>')
    g.append(f'<path d="M640,{y0 + 230} C680,{y0 + 70} 920,{y0 + 70} 960,{y0 + 230} L935,{y0 + 232} C900,{y0 + 110} 700,{y0 + 110} 665,{y0 + 232} Z" '
             f'fill="#2f8f8c" opacity="0.85"/>')
    g.append(f'<path d="M800,{y0 + 80} C820,{y0 + 100} 900,{y0 + 140} 935,{y0 + 232}" fill="none" stroke="#9fe0d2" stroke-width="5" opacity="0.6"/>')
    g.append(f'<text class="s" x="1000" y="{y0 + 110}">el agua del estrecho sube y se queda</text>')
    g.append(f'<text class="s" x="1000" y="{y0 + 130}">colgada entre los dos lóbulos</text>')
    g.append(f'<text class="s" x="300" y="{y0 + 245}" text-anchor="end">nivel normal del mar · · ·</text>')
    g.append(f'<text class="s" x="800" y="{y0 + 362}" text-anchor="middle" style="fill:#eef2f0;paint-order:stroke;stroke:#3b4140;stroke-width:4px">fondo del estrecho al aire: se cruza a pie de un lóbulo al otro</text>')
    b += g
    p = write_svg("diag_cintura", W, H, "".join(b))
    svg_to_png(p, OUTD / "ii-b-distribucion.png", W, H)


# ------------------------------------------------------------------ III
def dosmares():
    E = Equirect(1600, 800)
    img = (WORK / "dosmares_albedo.png").resolve()
    b = [FONT, f'<rect width="{W}" height="{H}" fill="{INK}"/>',
         f'<image href="file://{img}" x="0" y="0" width="1600" height="800"/>']
    cx, cy = E(-14, 9)
    b.append(f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(E.deg(26))}" ry="{f(E.deg(19))}" fill="#1b1036" opacity="0.32" '
             f'stroke="#c9b8ff" stroke-width="1.4" stroke-dasharray="6 6"/>')
    b.append(f'<text class="s" x="{f(cx)}" y="{f(cy - E.deg(19) - 10)}" text-anchor="middle" style="fill:#d9ccff">huella de la umbra · aquí sube el mar ligero</text>')
    L = [label(*E(-12, 9), *E(-40, 52), "el Lago Hondo", "salmuera · no sube"),
         label(*E(48, 30), *E(70, 62), "el Collar", "rift con lagos encadenados"),
         label(*E(-62, -7), *E(-80, -40), "lagos menores"),
         label(*E(1, 13), *E(30, -18), "río de salmuera", "cae de cubeta en cubeta"),
         label(*E(-2, 16), *E(20, 52), "volcanes de lodo"),
         label(*E(52, -30), *E(80, -58), "los Bajos", "la única arena que asoma"),
         label(*E(-40, 34), *E(-110, 58), "lomas claras", "fondo cerca de la luz"),
         label(*E(150, -20), *E(130, -58), "abismo")]
    b += L
    y0 = MAP_H
    b.append(section_frame("POR EL LAGO HONDO, DURANTE LA SOMBRA"))
    g = []
    g.append(f'<path d="M80,{y0 + 300} C300,{y0 + 280} 520,{y0 + 300} 620,{y0 + 318} C700,{y0 + 330} 900,{y0 + 330} 980,{y0 + 318} '
             f'C1100,{y0 + 300} 1300,{y0 + 280} 1520,{y0 + 300} L1520,{H} L80,{H} Z" fill="#3a3c36"/>')
    g.append(f'<path d="M640,{y0 + 322} C720,{y0 + 334} 880,{y0 + 334} 960,{y0 + 322} Z" fill="#4b3893"/>')
    g.append(f'<path d="M640,{y0 + 322} C720,{y0 + 334} 880,{y0 + 334} 960,{y0 + 322}" fill="none" stroke="#e8e0c4" stroke-width="2"/>')
    g.append(f'<line x1="80" y1="{y0 + 150}" x2="1520" y2="{y0 + 150}" stroke="#8fd6c9" stroke-width="1.4" stroke-dasharray="6 6"/>')
    g.append(f'<rect x="80" y="{y0 + 150}" width="420" height="150" fill="#2f7466" opacity="0.5"/>')
    g.append(f'<rect x="1100" y="{y0 + 150}" width="420" height="150" fill="#2f7466" opacity="0.5"/>')
    g.append(f'<path d="M500,{y0 + 300} C520,{y0 + 120} 560,{y0 + 70} 640,{y0 + 60} L960,{y0 + 60} C1040,{y0 + 70} 1080,{y0 + 120} 1100,{y0 + 300} '
             f'L1100,{y0 + 150} C1060,{y0 + 140} 1040,{y0 + 115} 960,{y0 + 110} L640,{y0 + 110} C560,{y0 + 115} 540,{y0 + 140} 500,{y0 + 150} Z" fill="#79b59b" opacity="0.75"/>')
    g.append(f'<text class="s" x="800" y="{y0 + 92}" text-anchor="middle">el mar ligero sube: un techo verde y transparente</text>')
    g.append(f'<text class="s" x="800" y="{y0 + 300}" text-anchor="middle">la salmuera se queda: lagos con orilla en un fondo al aire</text>')
    g.append(f'<text class="s" x="300" y="{y0 + 140}" text-anchor="middle">fuera de la umbra el mar sigue igual</text>')
    b += g
    p = write_svg("diag_dosmares", W, H, "".join(b))
    svg_to_png(p, OUTD / "iii-b-distribucion.png", W, H)


if __name__ == "__main__":
    OUTD.mkdir(exist_ok=True)
    dolinas()
    cintura()
    dosmares()
