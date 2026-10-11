"""Siluetas en negro (misma escala y a 64/32 px) y tira a escala de carta."""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import rompiente
from paint import smooth, svg_to_png, write_svg

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "img"
INK = "#0e0c13"


def sil_rompiente(cx, cy, R):
    th0, k, hs = -60, 0.034, 0.15 * R / 330

    def M(x, y):
        th = math.radians(th0 + (x - 1160) * k)
        h = (640 - y) * hs
        return (cx + (R + h) * math.cos(th), cy + (R + h) * math.sin(th))
    prof = rompiente.PROFILE_TOP + rompiente.PROFILE_LIP[1:] + rompiente.PROFILE_UNDER[1:]
    body = smooth([M(x, y) for x, y in prof] + [M(1160, 700), M(2420, 700)], tension=0.25)
    return f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{INK}"/><path d="{body}" fill="{INK}"/>'


def sil_huso(cx, cy, R):
    return f'<ellipse cx="{cx}" cy="{cy}" rx="{R * 1.27}" ry="{R * 0.79}" fill="{INK}" transform="rotate(-18 {cx} {cy})"/>'


def sil_luna(cx, cy, R):
    return (f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="{INK}"/>'
            f'<circle cx="{cx + R * 1.55}" cy="{cy - R * 0.85}" r="{R * 0.5}" fill="{INK}"/>')


def main():
    W, H = 1600, 520
    body = [f'<rect width="{W}" height="{H}" fill="#ece9f2"/>']
    for i, fn in enumerate((sil_rompiente, sil_huso, sil_luna)):
        x0 = 270 + i * 530
        body.append(fn(x0 - 40, 230, 140))
        body.append(fn(x0 - 110, 460, 22))
        body.append(fn(x0 - 20, 460, 11))
        body.append(fn(x0 + 50, 460, 5.5))
    p = write_svg("siluetas", W, H, "".join(body))
    svg_to_png(p, IMG / "siluetas.png", W, H)

    # escala de carta: miniaturas reales de las vistas orbitales (~64 px)
    crops = [("a-rompiente-orbita.png", (330, 180, 1100, 950)),
             ("b-huso-orbita.png", (300, 200, 1220, 840)),
             ("c-luna-orbita.png", (300, 120, 1380, 940))]
    strip = Image.new("RGB", (W, 300), (14, 12, 19))
    d = ImageDraw.Draw(strip)
    for i, (name, box) in enumerate(crops):
        im = Image.open(IMG / name).convert("RGB").crop(box)
        for j, size in enumerate((150, 64, 32)):
            k = size / max(im.size)
            t = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
            x = 120 + i * 530 + [0, 200, 300][j]
            strip.paste(t, (x, 150 - t.height // 2))
    strip.save(IMG / "carta.png")


if __name__ == "__main__":
    main()
