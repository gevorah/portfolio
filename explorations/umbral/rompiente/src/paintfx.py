"""Efectos de acabado compartidos por las vistas: filtro pictórico y figura con farol."""

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def box(x, r):
    """Media en ventana (2r+1)² con imagen integral."""
    p = np.pad(x, ((r + 1, r), (r + 1, r)) + ((0, 0),) * (x.ndim - 2), mode="edge")
    c = p.cumsum(0).cumsum(1)
    k = 2 * r + 1
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def kuwahara(a, r):
    lum = a @ np.array([0.3, 0.59, 0.11], np.float32)
    m = box(a, r)
    m2 = box(lum[..., None] ** 2, r)[..., 0]
    ml = box(lum[..., None], r)[..., 0]
    var = m2 - ml ** 2
    best = None
    bestv = None
    for dy in (-r, r):
        for dx in (-r, r):
            mv = np.roll(np.roll(m, dy, 0), dx, 1)
            vv = np.roll(np.roll(var, dy, 0), dx, 1)
            if best is None:
                best, bestv = mv.copy(), vv.copy()
            else:
                sel = vv < bestv
                best[sel] = mv[sel]
                bestv[sel] = vv[sel]
    return best



def paint(img, r=3, mix=0.55):
    """Agrupa el detalle en manchas, como pinceladas (Kuwahara suave)."""
    a = np.asarray(img.convert("RGB"), np.float32) / 255
    a = a*(1 - mix) + kuwahara(a, r)*mix
    return Image.fromarray((np.clip(a, 0, 1)*255).astype(np.uint8))


def figure(img, bx, by, hp):
    """Silueta con farol: la única luz cálida en la sombra. (bx, by) = pies, hp = altura en píxeles."""
    d = ImageDraw.Draw(img, "RGBA")
    w = hp*0.28
    body = [(bx - w, by), (bx - w*0.7, by - hp*0.78), (bx, by - hp*0.86), (bx + w*0.7, by - hp*0.78), (bx + w, by)]
    d.polygon(body, fill=(24, 22, 30, 255))
    d.ellipse([bx - w*0.55, by - hp*1.08, bx + w*0.55, by - hp*0.84], fill=(24, 22, 30, 255))
    lx, ly = bx + w*1.4, by - hp*0.45
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r_, al in ((22, 40), (11, 80), (5, 170)):
        gd.ellipse([lx - r_, ly - r_, lx + r_, ly + r_], fill=(255, 196, 130, al))
    glow = glow.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    ImageDraw.Draw(img, "RGBA").ellipse([lx - 1.6, ly - 1.6, lx + 1.6, ly + 1.6], fill=(255, 236, 200, 255))
    return img
