"""Acabado de La Cala Interior: reduce, pinta y pone la escala.

uso: python3 post_cala.py <render.png> <salida.png> [x y alto]   (coordenadas en 1600×1000)
"""

import sys

from PIL import Image

from paintfx import figure, paint

src, out = sys.argv[1], sys.argv[2]
img = paint(Image.open(src).convert("RGB").resize((1600, 1000), Image.LANCZOS))
if len(sys.argv) > 5:
    img = figure(img, float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]))
img.save(out)
