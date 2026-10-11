"""Piezas comunes de las láminas: cielo, estrellas, filtros y utilidades."""

import math
import random

from paint import f, smooth

W, H = 1600, 1000


def filters(extra=""):
    FU = f'filterUnits="userSpaceOnUse" x="-300" y="-300" width="{W + 600}" height="{H + 600}"'
    return f"""
<filter id="b1" {FU}><feGaussianBlur stdDeviation="1"/></filter>
<filter id="b3" {FU}><feGaussianBlur stdDeviation="3"/></filter>
<filter id="b8" {FU}><feGaussianBlur stdDeviation="8"/></filter>
<filter id="b20" {FU}><feGaussianBlur stdDeviation="20"/></filter>
<filter id="b50" {FU}><feGaussianBlur stdDeviation="50"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%">
  <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="3" result="n"/>
  <feColorMatrix in="n" type="matrix" values="0 0 0 0 0.9  0 0 0 0 0.9  0 0 0 0 1  0 0 0 0.7 -0.3"/>
</filter>
<filter id="rough" {FU}>
  <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="3" seed="6" result="t"/>
  <feDisplacementMap in="SourceGraphic" in2="t" scale="9" xChannelSelector="R" yChannelSelector="G"/>
</filter>
<filter id="roughS" {FU}>
  <feTurbulence type="fractalNoise" baseFrequency="0.08" numOctaves="2" seed="2" result="t"/>
  <feDisplacementMap in="SourceGraphic" in2="t" scale="4" xChannelSelector="R" yChannelSelector="G"/>
</filter>
{extra}"""


def stars(rng, n, y1=H, avoid=None, col="#ece8ff", bright=1.0):
    out = []
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, y1)
        if avoid and any(math.hypot(x - ax, y - ay) < ar for ax, ay, ar in avoid):
            continue
        r = rng.choice([0.5, 0.6, 0.7, 0.9, 1.1, 1.4])
        out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{r}" fill="{col}" opacity="{min(1, rng.uniform(0.25, 0.85) * bright):.2f}"/>')
    return "".join(out)


def lerp_pts(a, b, t):
    return [(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t) for (x0, y0), (x1, y1) in zip(a, b)]


def along(pts, t):
    """Punto a fracción t de una polilínea."""
    k = t * (len(pts) - 1)
    j = min(int(k), len(pts) - 2)
    fr = k - j
    return (pts[j][0] + (pts[j + 1][0] - pts[j][0]) * fr, pts[j][1] + (pts[j + 1][1] - pts[j][1]) * fr)


def grain(op=0.06):
    return f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="{op}"/>'
