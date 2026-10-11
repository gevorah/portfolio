"""Revela las láminas finales y compone la comparación de siluetas.

Lee out/*.swhdr (de render_all.sh) y escribe renders/*.jpg y
renders/anchors.json (posiciones de los accidentes geográficos en cada
lámina, en fracciones de imagen, para rotular los mapas).
"""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT, REN = ROOT / "out", ROOT / "renders"
POST = ROOT / "src" / "post.py"

FRAMES = [
    # (entrada, salida, viraje, exposición)
    ("a-orbit", "a1-orbita", "mar", 1.4),
    ("a-approach", "a2-aproximacion", "mar", 1.4),
    ("a-transform", "a3-transformacion", "mar", 1.4),
    ("a-discover", "a4-descubrimiento", "mar", 1.25),
    ("a-chart", "a0-mapa", "mar", 1.4),
    ("b-orbit", "b1-orbita", "rev", 1.4),
    ("b-approach", "b2-aproximacion", "rev", 1.4),
    ("b-transform", "b3-transformacion", "rev", 1.5),
    ("b-discover", "b4-descubrimiento", "rev", 1.4),
    ("b-chart", "b0-mapa", "rev", 1.4),
]


def develop():
    REN.mkdir(exist_ok=True)
    for src, dst, grade, exp in FRAMES:
        width = 1200 if "chart" in src else 1600
        subprocess.run(
            [sys.executable, str(POST), str(OUT / f"{src}.swhdr"), str(REN / f"{dst}.jpg"),
             "--grade", grade, "--exp", str(exp), "--width", str(width)],
            check=True,
        )


def silhouettes():
    """Las dos siluetas a la misma escala: tinta sobre papel, sin texto."""
    ink = np.array([0x0E, 0x0C, 0x13], np.float32)
    paper = np.array([0xEE, 0xED, 0xF5], np.float32)
    masks = []
    for name in ("a-sil", "b-sil"):
        tmp = OUT / f"{name}.png"
        subprocess.run([sys.executable, str(POST), str(OUT / f"{name}.swhdr"), str(tmp), "--mask", "--width", "800"],
                       check=True)
        masks.append(np.asarray(Image.open(tmp), np.float32) / 255)
    h, w = masks[0].shape
    pad = 40
    canvas = np.ones((h, w * 2 + pad, 3), np.float32) * paper
    for i, m in enumerate(masks):
        x0 = i * (w + pad)
        canvas[:, x0:x0 + w] = paper + (ink - paper) * m[..., None]
    Image.fromarray(canvas.astype(np.uint8)).save(REN / "siluetas.png", optimize=True)


def anchors():
    data = {}
    for f in sorted(OUT.glob("*.anchors")):
        pts = {}
        for line in f.read_text().splitlines():
            parts = line.split()
            if len(parts) == 4 and parts[0] == "ANCHOR":
                pts[parts[1]] = [round(float(parts[2]), 4), round(float(parts[3]), 4)]
        data[f.stem] = pts
    (REN / "anchors.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    develop()
    silhouettes()
    anchors()
