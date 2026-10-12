"""Geología compartida de La Cala Interior (coordenadas de Blender, metros).

Origen en el centro de la poza madre (ronda 6: B = (72, 404) del shader).
x este, y norte, z altura (0 = pleamar, −24 = bajamar).

La columna estratigráfica se lee del mismo archivo que usan La Rompiente y la
Cala de la ronda 6 (rompiente/src/shader/common.glsl), para que los bancos de
lava sean los mismos en la cara del alero y dentro de la sala.
"""

import math
import os
import re

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.join(HERE, "..", "..", "rompiente", "src", "shader", "common.glsl")

_src = open(COMMON).read()


def _arr(name):
    m = re.search(r"const float %s\[\d+\] = float\[\]\(([^)]*)\)" % name, _src)
    return np.array([float(v) for v in m.group(1).split(",")])


BT, BB, BH, BC = _arr("BT"), _arr("BB"), _arr("BH"), _arr("BC")

# hitos de la ronda 6, pasados a estas coordenadas
SHADER_B = (72.0, 404.0)
K = np.array([-16.0, -14.0])          # centro del jameo (techo hundido)
PHI0 = 0.78                            # el anfiteatro de gours mira al nordeste
SEA_LOW, SEA_HIGH = -24.0, 0.0
SPRING = np.array([60.0 * math.cos(PHI0 + 0.05), 60.0 * math.sin(PHI0 + 0.05), 4.0])
# eje del tubo volcánico, desde la Bóveda (bajo el alero de La Rompiente) hasta la sala
TUBE = np.array([[-118.0, -84.0, -11.0], [-74.0, -54.0, -13.0], [-42.0, -31.0, -15.0], [-14.0, -11.0, -16.5], [4.0, 0.0, -17.5]])
J1 = np.array([0.931, -0.366])         # familia de diaclasas paralela a la costa


# --- ruido ------------------------------------------------------------------
def _hash3(ix, iy, iz, seed):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float64) / float(0xFFFFFF)


def noise3(x, y, z, seed=0):
    xi, yi, zi = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64), np.floor(z).astype(np.int64)
    fx, fy, fz = x - xi, y - yi, z - zi
    fx, fy, fz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                out = out + w * _hash3(xi + dx, yi + dy, zi + dz, seed)
    return out


def fbm3(x, y, z, scale, octaves=3, seed=0):
    s, a, t = 0.0, 1.0, 0.0
    for i in range(octaves):
        f = 2 ** i / scale
        s = s + a * noise3(x * f, y * f, z * f, seed + 17 * i)
        t += a
        a *= 0.5
    return s / t


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# --- estratos -----------------------------------------------------------------
def bed_y(x, y, z):
    """Cota estratigráfica (como bedY del shader, en estas coordenadas)."""
    sx, sz = x + SHADER_B[0], y + SHADER_B[1]
    return z + 0.014 * (sz - 400.0) - 0.012 * sx + 5.0 * (noise3(sx * 0.009, sz * 0.009, 0.0, 91) - 0.5)


def bed(x, y, z):
    """(índice, fracción, espesor, dureza) del banco en cada punto."""
    yy = np.clip(bed_y(x, y, z) + 46.0, 0.0, BB[-1] - 0.01)
    i = np.clip(np.searchsorted(BB, yy, side="right") - 1, 0, len(BT) - 1)
    t = BT[i]
    frac = np.clip((yy - BB[i]) / t, 0, 1)
    hard = np.clip(BH[i] + 0.9 * (noise3(y * 0.012 + i * 3.1, x * 0.012, 0.0, 5) - 0.5), 0, 1)
    return i, frac, t, hard


def bed_relief(x, y, z):
    """Relieve en la pared: los bancos blandos (escoria) se vacían, los duros asoman."""
    i, f, t, hard = bed(x, y, z)
    amp = smoothstep(0.6, 3.0, t)
    soft = (1.0 + 1.0 / np.maximum(t, 0.7)) * np.sin(np.pi * f) ** 0.6
    nose = -0.9 * np.sin(np.pi * f) ** 0.35
    return np.maximum(0.1, amp) * (soft * (1 - smoothstep(0.35, 0.65, hard)) + nose * smoothstep(0.35, 0.65, hard))


def massive(x, y, z):
    """1 en el núcleo de las coladas gruesas y duras: ahí el enfriamiento abre columnas."""
    i, f, t, hard = bed(x, y, z)
    core = smoothstep(0.08, 0.2, f) * (1 - smoothstep(0.8, 0.92, f))
    return smoothstep(2.8, 4.0, t) * smoothstep(0.55, 0.75, hard) * core


# --- columnas -------------------------------------------------------------------
def column_cells(x, y, size=1.7, seed=3):
    """Prismas de basalto: distancia al borde de la celda de Voronoi, id y centro de la celda."""
    gx, gy = x / size, y / size
    ix, iy = np.floor(gx).astype(np.int64), np.floor(gy).astype(np.int64)
    d1 = np.full(x.shape, 1e9)
    d2 = np.full(x.shape, 1e9)
    cid = np.zeros(x.shape, np.int64)
    ccx = np.zeros(x.shape)
    ccy = np.zeros(x.shape)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx, cy = ix + dx, iy + dy
            px = cx + 0.15 + 0.7 * _hash3(cx, cy, 0, seed)
            py = cy + 0.15 + 0.7 * _hash3(cx, cy, 1, seed)
            d = np.hypot(gx - px, gy - py)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            cid = np.where(closer, cx * 100003 + cy, cid)
            ccx = np.where(closer, px * size, ccx)
            ccy = np.where(closer, py * size, ccy)
            d1 = np.where(closer, d, d1)
    return (d2 - d1) * size * 0.5, cid, ccx, ccy
