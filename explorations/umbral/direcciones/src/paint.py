"""Herramientas de dibujo compartidas: curvas suaves, mapas equirectangulares
y paso de SVG a PNG con el Chromium de Playwright."""

import math
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
PW = os.environ.get("PW_PATH", "/opt/node-tools/node_modules/playwright")


def f(x):
    return f"{x:.1f}"


def smooth(pts, closed=True, tension=0.5):
    """Catmull-Rom por los puntos dados → path SVG con cúbicas."""
    n = len(pts)
    if n < 3:
        return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts)
    d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed or i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed or i + 2 < n else p2
        t = tension / 3 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * t / 2, p1[1] + (p2[1] - p0[1]) * t / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * t / 2, p2[1] - (p3[1] - p1[1]) * t / 2)
        d += f" C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}"
    return d + (" Z" if closed else "")


class Equirect:
    """Coordenadas de un mapa equirectangular de W×H en grados."""

    def __init__(self, w=2048, h=1024):
        self.w, self.h = w, h

    def __call__(self, lon, lat):
        return ((lon + 180) / 360 * self.w, (90 - lat) / 180 * self.h)

    def pts(self, lonlat):
        return [self(lo, la) for lo, la in lonlat]

    def deg(self, d):
        return d / 360 * self.w


def blob(cx, cy, r, lobes, rot=0.0, n=None):
    """Contorno orgánico diseñado: radio modulado por pocos lóbulos dados
    a mano [(frecuencia, amplitud, fase)], no ruido."""
    n = n or 48
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n + rot
        rr = r * (1 + sum(amp * math.cos(fr * a + ph) for fr, amp, ph in lobes))
        out.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return out


def svg_to_png(svg_path, png_path, w, h, scale=1):
    subprocess.run(["node", str(ROOT / "src" / "render.mjs"), str(svg_path), str(png_path),
                    str(w), str(h), str(scale)], check=True, env={**os.environ, "PW_PATH": PW})


def write_svg(name, w, h, body, defs=""):
    WORK.mkdir(exist_ok=True)
    p = WORK / f"{name}.svg"
    p.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                 f'width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs>{defs}</defs>{body}</svg>')
    return p
