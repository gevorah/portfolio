"""Revelado de los renders HDR del trazador.

Lee el formato SWHDR (float32 RGBA lineal), aplica exposición, un tonemap
fílmico suave, un viraje de color por mundo, viñeta, un halo muy contenido en
las luces y grano de película, y reduce al tamaño final.

    python3 post.py entrada.swhdr salida.jpg --exp 1.0 --grade mar --width 1600
    python3 post.py entrada.swhdr mascara.png --mask   # silueta en blanco/negro
"""

import argparse

import numpy as np
from PIL import Image, ImageFilter


def load(path):
    with open(path, "rb") as f:
        head = f.readline().decode().split()
        w, h = int(head[1]), int(head[2])
        data = np.frombuffer(f.read(), dtype=np.float32).reshape(h, w, 4)
    return data.copy()


def aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


# Virajes: color de sombras (lift) y de luces (gain) por mundo. Las sombras
# nunca caen a negro puro: descansan en la tinta de gevorah.
GRADES = {
    "none": dict(lift="#000000", gain="#ffffff", sat=1.0, lift_amt=0.0),
    "mar": dict(lift="#0e0c13", gain="#f2f6ff", sat=0.94, lift_amt=1.0),
    "rev": dict(lift="#0e0c13", gain="#fff7ef", sat=0.96, lift_amt=1.0),
}


def blur(img, r):
    pil = Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8))
    return np.asarray(pil.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--exp", type=float, default=1.0)
    ap.add_argument("--grade", default="mar")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--grain", type=float, default=0.035)
    ap.add_argument("--vignette", type=float, default=0.35)
    ap.add_argument("--halo", type=float, default=0.12)
    ap.add_argument("--mask", action="store_true")
    ap.add_argument("--contrast", type=float, default=1.0)
    a = ap.parse_args()

    d = load(a.inp)
    rgb, alpha = d[..., :3], d[..., 3]
    h, w = alpha.shape
    nh = round(h * a.width / w)

    if a.mask:
        m = Image.fromarray((np.clip(alpha, 0, 1) * 255).astype(np.uint8))
        m.resize((a.width, nh), Image.LANCZOS).save(a.out)
        return

    rgb = np.nan_to_num(rgb, nan=0.0, posinf=50.0, neginf=0.0)
    x = aces(np.clip(rgb * a.exp, 0, 50))
    # tonemap → gamma de pantalla
    x = np.power(x, 1 / 2.2)
    g = GRADES[a.grade]
    lift = hexrgb(g["lift"]) * g["lift_amt"]
    gain = hexrgb(g["gain"])
    x = lift + (gain - lift) * x
    if a.contrast != 1.0:
        x = np.clip(0.5 + (x - 0.5) * a.contrast, 0, 1)
    lum = (x * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    x = lum + (x - lum) * g["sat"]

    # reducir antes del grano para que el grano quede a resolución final
    pil = Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8))
    pil = pil.resize((a.width, nh), Image.LANCZOS)
    x = np.asarray(pil, np.float32) / 255

    if a.halo > 0:
        hi = np.clip(x - 0.72, 0, 1) / 0.28
        x = 1 - (1 - x) * (1 - blur(hi, a.width / 90) * a.halo)

    yy, xx = np.mgrid[0:nh, 0:a.width].astype(np.float32)
    r = np.sqrt(((xx / a.width - 0.5) * 1.25) ** 2 + ((yy / nh - 0.5)) ** 2)
    vig = 1 - a.vignette * np.clip((r - 0.35) / 0.55, 0, 1) ** 1.6
    x = x * vig[..., None]

    rng = np.random.default_rng(7)
    n = rng.normal(0, 1, (nh, a.width, 1)).astype(np.float32)
    lum = (x * [0.2126, 0.7152, 0.0722]).sum(-1, keepdims=True)
    x = x + n * a.grain * (0.35 + 0.65 * (1 - lum)) * 0.5

    out = Image.fromarray((np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8))
    if a.out.endswith(".jpg"):
        out.save(a.out, quality=90, subsampling=0, optimize=True)
    else:
        out.save(a.out)


if __name__ == "__main__":
    main()
