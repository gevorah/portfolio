"""La roca que envuelve La Cala Interior: tubo volcánico, sala de derrumbe y jameo.

Se define el aire como un campo (positivo = aire) y se extrae la superficie con
marching cubes. Cada parte responde a un proceso:

- el tubo de lava llega desde la Bóveda con sección de arco; sus paredes
  marcan los bancos de colada (la escoria se vacía, el basalto masivo asoma);
- la sala es un ensanche por derrumbe: el techo cae por planos de estrato, así
  que es escalonado y casi plano en cada tramo, no una cúpula;
- el jameo es el techo hundido: una abertura alargada siguiendo la diaclasa,
  que en el banco masivo se rompe en prismas de basalto de alturas distintas.

Salida: work/shell.npz (vértices, caras) en coordenadas de Blender.
"""

import os
import sys
import time

import numpy as np
from skimage.measure import marching_cubes

from geo import (J1, K, PHI0, TUBE, bed, bed_relief, bed_y, column_cells, fbm3, massive, smoothstep)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
BOX = np.array([[-128.0, 74.0], [-92.0, 74.0], [-42.0, 64.0]])


def seg_dist(p, a, b):
    ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1)
    c = a + t[..., None] * ab
    return p - c, t


def air_tube(x, y, z):
    """Tubo volcánico: sección de arco, más ancha que alta, con el suelo lo da el campo de las gradas."""
    p = np.stack([x, y, z], -1)
    best = np.full(x.shape, -1e9)
    for a, b in zip(TUBE[:-1], TUBE[1:]):
        d, t = seg_dist(p, a, b)
        hor = np.hypot(d[..., 0], d[..., 1])
        ver = d[..., 2]
        wid = 12.5 + 3.0 * (fbm3(x, y, z * 0.3, 30, 2, 11) - 0.5) * 2
        hgt = np.where(ver > 0, 10.5 + 2.5 * (fbm3(x, y, 0 * z, 24, 2, 12) - 0.5) * 2, 20.0)
        v = 1.0 - np.sqrt((hor / wid) ** 2 + (ver / hgt) ** 2)
        # marcas de nivel de la lava en las paredes del tubo ("anillos de bañera")
        rings = 0.5 * np.exp(-((z + 13.0) / 0.5) ** 2) + 0.35 * np.exp(-((z + 9.5) / 0.4) ** 2)
        best = np.maximum(best, v * 11.0 + rings * (hor > wid * 0.6))
    return best


def scoria_bands(x, y, z):
    """Solo los niveles de escoria entre coladas se vacían: dos o tres bandas oscuras, no un apilado."""
    by = bed_y(x, y, z)
    out = 0.0
    for c, w, d in ((-8.0, 1.2, 2.2), (9.0, 0.8, 1.4), (22.0, 1.6, 2.6)):
        out = out + d * np.exp(-((by - c) / w) ** 2)
    return out


def air_chamber(x, y, z):
    """Sala de derrumbe: el techo es un mosaico de cicatrices de bloques caídos."""
    cx, cy = 6.0, 6.0
    r = np.hypot(x - cx, y - cy)
    th = np.angle(np.exp(1j * (np.arctan2(y - cy, x - cx) - PHI0)))
    sector = 1 - smoothstep(0.9, 1.7, np.abs(th))
    rw = 33.0 + 27.0 * sector + 9.0 * (fbm3(x, y, z * 0.35, 30, 3, 21) - 0.5) * 2
    rw *= 1.0 - 0.32 * smoothstep(-6.0, 26.0, z) ** 1.5             # las paredes se cierran hacia el techo
    wall = rw - r + scoria_bands(x, y, z)
    smooth = 24.0 - 0.0045 * ((x - cx) ** 2 + (y - cy) ** 2) + 4.0 * (fbm3(x, y, 0 * z, 26, 2, 22) - 0.5) * 2
    # cicatrices: cada bloque caído deja una cara casi plana, con su propio salto
    edge, cid, _, _ = column_cells(x, y, 7.5, 13)
    rnd = (cid * 2654435761 % 997) / 997.0
    edge2, cid2, _, _ = column_cells(x + 3.1, y - 1.7, 3.2, 17)
    rnd2 = (cid2 * 40503 % 991) / 991.0
    scar = 3.2 * rnd + 1.1 * rnd2 * (rnd > 0.6)
    ceil = smooth + scar - 0.25 * smoothstep(0.15, 0.0, edge) * (rnd > 0.3)   # aristas vivas entre algunos bloques
    return np.minimum(wall, ceil - z)


def air_shaft(x, y, z):
    """El jameo: abertura alargada según la diaclasa, prismas de basalto en el banco masivo."""
    d = np.stack([x - K[0], y - K[1]], -1)
    u = d @ J1
    v = d[..., 0] * J1[1] * -1 + d[..., 1] * J1[0]
    widen = 1.0 + 0.55 * smoothstep(20.0, 44.0, z)                  # se abre en embudo hacia la dolina
    a = (17.0 + 4.0 * (fbm3(x, y, z * 0.6, 14, 2, 31) - 0.5) * 2) * widen
    b = (9.5 + 3.0 * (fbm3(x, y, z * 0.6, 12, 2, 32) - 0.5) * 2) * widen
    ell = 1.0 - np.sqrt((u / a) ** 2 + (v / b) ** 2)
    # segundo hundimiento, más pequeño, unido al primero por la misma grieta
    ell2 = 1.0 - np.sqrt(((u - 21.0) / (a * 0.5)) ** 2 + ((v + 2.0) / (b * 0.75)) ** 2)
    ell = np.maximum(ell, ell2)
    f = ell * 9.0 + 0.8 * scoria_bands(x, y, z)
    # banco masivo: la pared es la de los prismas; cada columna se rompe a su altura
    edge, cid, ccx, ccy = column_cells(x, y, 1.8, 7)
    dc = np.stack([ccx - K[0], ccy - K[1]], -1)
    uc = dc @ J1
    vc = dc[..., 0] * J1[1] * -1 + dc[..., 1] * J1[0]
    ellc = 1.0 - np.sqrt((uc / a) ** 2 + (vc / b) ** 2)
    ellc = np.maximum(ellc, 1.0 - np.sqrt(((uc - 21.0) / (a * 0.5)) ** 2 + ((vc + 2.0) / (b * 0.75)) ** 2))
    rnd = (cid * 2654435761 % 1000) / 1000.0
    broken = z > (16.0 + 22.0 * rnd)                                   # la columna se partió a esta altura
    colf = np.where(ellc + 0.12 * broken > 0, 0.9 - 0.0 * edge, -0.9) + np.where(edge < 0.07, 0.6, 0.0)
    m = massive(x, y, z)
    f = f * (1 - m) + np.where(m > 0.5, colf * 2.5, f) * m
    # bajo el techo de la sala el hueco no existe; arriba se abre hasta el cielo
    return np.where(z > 8.0, f, -1e3 + 0 * f)


def ground_top(x, y):
    """Superficie de la isla con la dolina del jameo."""
    d = np.stack([x - K[0], y - K[1]], -1)
    u = d @ J1
    v = d[..., 0] * J1[1] * -1 + d[..., 1] * J1[0]
    dk = np.sqrt(((u - 7.0) / 1.7) ** 2 + v ** 2)
    top = 56.0 + 6.0 * (fbm3(x, y, 0 * x, 40, 3, 41) - 0.5) * 2
    return top - 24.0 * (1 - smoothstep(14.0, 52.0, dk))


def ledge(x, y, z):
    """Repisa de lava a +2 m en el flanco sur de la boca del tubo: el nivel donde la colada se estancó."""
    cx, cy = 6.0, 6.0
    th = np.arctan2(y - cy, x - cx)
    sw = smoothstep(-2.75, -2.45, th) * (1 - smoothstep(-1.75, -1.45, th))      # entre el SO y el S
    wall = air_chamber(x, y, z * 0 + 1.0)                                         # distancia a la pared a esa cota
    depth = 3.4 + 1.2 * (fbm3(x, y, 0 * z, 6, 2, 71) - 0.5) * 2
    top = 2.1 + 0.25 * (fbm3(x, y, 0 * z, 3, 2, 72) - 0.5) * 2
    inside = np.minimum(np.minimum(depth - wall, top - z), z + 4.0)
    return np.where(sw > 0.5, inside, -1e3)


def air(x, y, z):
    a = np.maximum(air_tube(x, y, z), air_chamber(x, y, z))
    a = np.minimum(a, -ledge(x, y, z))
    a = np.maximum(a, air_shaft(x, y, z))
    a = np.maximum(a, z - ground_top(x, y))
    # rugosidad de basalto a escala de metro, más fuerte en el techo del derrumbe
    a += 0.35 * (fbm3(x, y, z, 3.0, 2, 51) - 0.5) * 2
    return a


if __name__ == "__main__":
    RES = float(sys.argv[1]) if len(sys.argv) > 1 else 0.6
    t0 = time.time()
    xs = np.arange(BOX[0, 0], BOX[0, 1], RES)
    ys = np.arange(BOX[1, 0], BOX[1, 1], RES)
    zs = np.arange(BOX[2, 0], BOX[2, 1], RES)
    vol = np.zeros((len(zs), len(ys), len(xs)), np.float32)
    Y2, X2 = np.meshgrid(ys, xs, indexing="ij")
    for k, z in enumerate(zs):
        vol[k] = air(X2, Y2, np.full_like(X2, z))
        if k % 20 == 0:
            print(f"z {z:.1f} ({k}/{len(zs)}) {time.time() - t0:.0f}s", flush=True)
    # el aire tiene que cerrar por los bordes de la caja para que la malla sea estanca
    for sl in (np.s_[:, :, 0], np.s_[:, :, -1], np.s_[:, 0, :], np.s_[:, -1, :], np.s_[0, :, :]):
        vol[sl] = np.minimum(vol[sl], -1.0)
    verts, faces, normals, _ = marching_cubes(vol, 0.0, spacing=(RES, RES, RES))
    verts = verts[:, ::-1] + BOX[:, 0]                                 # (z, y, x) → (x, y, z)
    faces = faces[:, ::-1]
    np.savez_compressed(os.path.join(WORK, "shell.npz"), verts=verts.astype(np.float32), faces=faces.astype(np.int32))
    print(f"{len(verts)} vértices, {len(faces)} caras, {time.time() - t0:.0f}s")
