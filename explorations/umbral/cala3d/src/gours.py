"""Las Gradas: crecimiento de gours por precipitación en los labios de desborde.

No se dibujan las terrazas. Se parte del suelo de la ronda 6 (una rampa que sube
del nivel de bajamar a +3 m hacia el nordeste, con el canal del tubo volcánico
y la poza madre) y se deja que el agua del manantial haga el resto:

  1. el agua llena las depresiones (priority-flood con épsilon, Barnes 2014);
  2. desborda y corre ladera abajo repartida entre los vecinos más bajos (MFD);
  3. donde la lámina es fina y la superficie del agua se acelera, el carbonato
     precipita: los labios crecen, las pozas se profundizan, los bordes grandes
     avanzan y alcanzan a los pequeños (Goldenfeld et al. 2006; Hammer et al.
     2010; Kerr y Turner 1996).

Coordenadas de Blender, en metros, con origen en el centro de la poza madre
(shader de la ronda 6: B = (72, 404)). x este, y norte, z altura (0 = pleamar,
−24 = bajamar).

Salidas en work/: gours_h.npy (suelo), gours_h0.npy (suelo inicial),
gours_q.npy (caudal), gours_w.npy (agua en bajamar), gours_preview.png
"""

import math
import os
import time

import numpy as np
from numba import njit
from scipy.ndimage import gaussian_filter
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
os.makedirs(WORK, exist_ok=True)

EXT = 64.0                      # medio lado del dominio (m)
CELL = 0.25                     # resolución (m)
N = int(2 * EXT / CELL)
SEA_LOW = -24.0
PHI0 = 0.78                     # el anfiteatro mira al nordeste
TUNNEL_DIR = np.array([177.0, 120.0]) / math.hypot(177.0, 120.0)
TUNNEL_P = np.array([1.8, -2.6])  # punto del eje del tubo más cercano a la poza madre
SPRING = (60.0 * math.cos(PHI0 + 0.05), 60.0 * math.sin(PHI0 + 0.05))

rng = np.random.default_rng(23)
xs = (np.arange(N) + 0.5) * CELL - EXT
X, Y = np.meshgrid(xs, xs)          # fila = y (sur → norte), columna = x


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def value_noise(scale, seed):
    """Ruido suave: rejilla aleatoria interpolada (escala en metros)."""
    r = np.random.default_rng(seed)
    g = int(2 * EXT / scale) + 3
    grid = r.random((g, g))
    gx = (X + EXT) / scale
    gy = (Y + EXT) / scale
    x0, y0 = np.floor(gx).astype(int), np.floor(gy).astype(int)
    fx, fy = gx - x0, gy - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a = grid[y0, x0] * (1 - fx) + grid[y0, x0 + 1] * fx
    b = grid[y0 + 1, x0] * (1 - fx) + grid[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def fbm(scale, octaves, seed):
    s, a, t = 0.0, 1.0, 0.0
    for i in range(octaves):
        s = s + a * value_noise(scale / 2 ** i, seed + i)
        t += a
        a *= 0.5
    return s / t


# --- suelo inicial ----------------------------------------------------------
R = np.hypot(X, Y)
A = np.angle(np.exp(1j * (np.arctan2(Y, X) - PHI0)))
sector = 1 - smoothstep(1.15, 1.6, np.abs(A))

# el anfiteatro no es una rampa: son frentes lobulados de coladas antiguas que el
# travertino tapiza. Cada frente tiene su radio, su salto y su lobulación; algunos se
# acuñan y desaparecen a un lado. Las cotas siguen las de la ronda 6.
FRONTS = [  # (radio, salto, lóbulos por radián, amplitud de lóbulo, acuñamiento hacia +/- ángulo)
    (12.5, 4.2, 1.3, 1.6, 0.0),
    (19.0, 2.4, 1.8, 2.4, +1.0),
    (24.5, 3.0, 1.1, 3.0, 0.0),
    (31.0, 1.8, 2.2, 1.8, -1.0),
    (35.5, 3.4, 1.4, 2.6, 0.0),
    (42.5, 2.6, 1.6, 3.4, +1.0),
    (47.0, 4.6, 1.2, 2.0, 0.0),
    (53.5, 2.9, 1.9, 2.2, 0.0),
]
warp = 5.0 * (fbm(16, 3, 1) - 0.5) * 2
Rw = R + warp
amph = np.full_like(R, -27.0) + 0.015 * np.maximum(Rw - 9, 0)      # bancos casi planos: los labios represan pozas grandes
for k, (fr, jump, nl, amp, pinch) in enumerate(FRONTS):
    lob = np.abs(np.sin(A * nl * 3.0 + k * 1.7 + 2.0 * (fbm(9, 2, 40 + k) - 0.5)))
    front = fr - amp * lob + 1.5 * (fbm(6, 2, 60 + k) - 0.5) * 2
    j = jump * (1 - smoothstep(0.4, 1.2, A * pinch)) if pinch else jump
    j = j * (0.75 + 0.5 * fbm(20, 2, 80 + k))
    amph += j * smoothstep(front - 0.9, front + 0.9, Rw)
amph = np.minimum(amph, np.interp(R, [0, 9, 13], [-27.5, -27.0, -21.0]) + 40 * (R > 11))
amph += 0.6 * (fbm(14, 3, 2) - 0.5) * smoothstep(12, 22, R)
# el pie de la pared del fondo: sube en rampa irregular, no en un arco perfecto
Rb = R + 6.0 * (fbm(11, 3, 90) - 0.5) * 2
amph = np.maximum(amph, np.interp(Rb, [56, 64, 72, 90], [-2.0, 6.0, 13.0, 30.0], left=-1e3))
# el canal del tubo volcánico, con bancos de lava a los lados (cota −20)
rel = np.stack([X - TUNNEL_P[0], Y - TUNNEL_P[1]], -1)
dp = np.abs(rel[..., 0] * TUNNEL_DIR[1] - rel[..., 1] * TUNNEL_DIR[0])
dp += 2.0 * (fbm(10, 2, 3) - 0.5)
along = rel[..., 0] * TUNNEL_DIR[0] + rel[..., 1] * TUNNEL_DIR[1]
# el tubo llega por el oeste (desde la Bóveda); al este quedó enterrado bajo las gradas
dp += 40.0 * smoothstep(-2, 14, along)
tube = -27.5 + 7.0 * smoothstep(5, 9, dp) + 60.0 * smoothstep(13, 22, dp) + 0.6 * (fbm(4, 2, 4) - 0.5)
# fuera del anfiteatro y del tubo, el suelo sube hacia el pie de las paredes
# fuera del anfiteatro: talud de derrumbe y colada que sube suave hacia el pie de las paredes
outside = -21.0 + 0.45 * np.maximum(R - 14, 0) + 1.5 * (fbm(7, 2, 70) - 0.5) * 2
h0 = amph * sector + np.maximum(outside, amph) * (1 - sector)
h0 = np.minimum(h0, tube)
h0 = np.minimum(h0, np.where(R < 12, np.interp(R, [0, 9, 13], [-27.5, -27.0, -22.0]), 1e3))
# rugosidad inicial: coladas antiguas y cantos sobre los que nacen los primeros labios
h0 += 0.25 * (fbm(5, 3, 5) - 0.5) + 0.10 * (fbm(2.0, 2, 6) - 0.5)
nb = 500
bx, by = rng.uniform(-EXT, EXT, nb), rng.uniform(-EXT, EXT, nb)
br, bh = rng.uniform(0.3, 1.2, nb), rng.uniform(0.05, 0.25, nb)
for i in range(nb):
    c0, c1 = int((bx[i] + EXT) / CELL), int((by[i] + EXT) / CELL)
    k = int(br[i] * 2.5 / CELL) + 1
    a0, a1 = max(c1 - k, 0), min(c1 + k, N)
    b0, b1 = max(c0 - k, 0), min(c0 + k, N)
    d2 = (X[a0:a1, b0:b1] - bx[i]) ** 2 + (Y[a0:a1, b0:b1] - by[i]) ** 2
    h0[a0:a1, b0:b1] += bh[i] * np.exp(-d2 / (br[i] ** 2))
h0 = h0.astype(np.float64)


# --- hidrología -------------------------------------------------------------
@njit(cache=True)
def priority_flood(h, outlet, eps):
    """Rellena depresiones: devuelve la superficie del agua (con pendiente épsilon)."""
    n0, n1 = h.shape
    filled = np.full_like(h, 1e9)
    done = np.zeros(h.shape, np.bool_)
    # montículo binario manual (numba no tiene heapq con tuplas eficiente)
    cap = n0 * n1 + 8
    hv = np.empty(cap)
    hi = np.empty(cap, np.int64)
    size = 0
    for i in range(n0):
        for j in range(n1):
            if outlet[i, j]:
                filled[i, j] = h[i, j]
                done[i, j] = True
                # push
                k = size
                size += 1
                hv[k] = h[i, j]
                hi[k] = i * n1 + j
                while k > 0:
                    p = (k - 1) // 2
                    if hv[p] <= hv[k]:
                        break
                    hv[p], hv[k] = hv[k], hv[p]
                    hi[p], hi[k] = hi[k], hi[p]
                    k = p
    while size > 0:
        cv = hv[0]
        ci = hi[0]
        size -= 1
        hv[0] = hv[size]
        hi[0] = hi[size]
        k = 0
        while True:
            l = 2 * k + 1
            r = l + 1
            m = k
            if l < size and hv[l] < hv[m]:
                m = l
            if r < size and hv[r] < hv[m]:
                m = r
            if m == k:
                break
            hv[m], hv[k] = hv[k], hv[m]
            hi[m], hi[k] = hi[k], hi[m]
            k = m
        i0 = ci // n1
        j0 = ci % n1
        for di in range(-1, 2):
            for dj in range(-1, 2):
                if di == 0 and dj == 0:
                    continue
                i = i0 + di
                j = j0 + dj
                if i < 0 or j < 0 or i >= n0 or j >= n1 or done[i, j]:
                    continue
                done[i, j] = True
                v = max(h[i, j], cv + eps)
                filled[i, j] = v
                k = size
                size += 1
                hv[k] = v
                hi[k] = i * n1 + j
                while k > 0:
                    p = (k - 1) // 2
                    if hv[p] <= hv[k]:
                        break
                    hv[p], hv[k] = hv[k], hv[p]
                    hi[p], hi[k] = hi[k], hi[p]
                    k = p
    return filled


@njit(cache=True)
def mfd(filled, src, order, p):
    """Caudal repartido entre todos los vecinos más bajos, en proporción a la pendiente^p."""
    n0, n1 = filled.shape
    q = src.copy()
    for t in range(order.shape[0]):
        c = order[t]
        i0 = c // n1
        j0 = c % n1
        z = filled[i0, j0]
        tot = 0.0
        for di in range(-1, 2):
            for dj in range(-1, 2):
                if di == 0 and dj == 0:
                    continue
                i = i0 + di
                j = j0 + dj
                if i < 0 or j < 0 or i >= n0 or j >= n1:
                    continue
                d = z - filled[i, j]
                if d > 0:
                    tot += (d / (1.0 if di == 0 or dj == 0 else 1.4142)) ** p
        if tot <= 0:
            continue
        for di in range(-1, 2):
            for dj in range(-1, 2):
                if di == 0 and dj == 0:
                    continue
                i = i0 + di
                j = j0 + dj
                if i < 0 or j < 0 or i >= n0 or j >= n1:
                    continue
                d = z - filled[i, j]
                if d > 0:
                    q[i, j] += q[i0, j0] * (d / (1.0 if di == 0 or dj == 0 else 1.4142)) ** p / tot
    return q


def sources():
    """El manantial principal y una franja de rezumes por el borde alto del anfiteatro."""
    s = np.zeros((N, N))
    d2 = (X - SPRING[0]) ** 2 + (Y - SPRING[1]) ** 2
    s += np.exp(-d2 / 1.5 ** 2)
    s /= s.sum()
    seep = smoothstep(4, 0, np.abs(R - 57.5)) * (1 - smoothstep(0.7, 1.05, np.abs(A))) * smoothstep(0.45, 0.75, fbm(9, 2, 7))
    s += 0.7 * seep / max(seep.sum(), 1e-9)
    return s


def simulate(h, iters=420, report=60):
    src = sources()
    outlet = np.zeros_like(h, dtype=bool)          # el único desagüe es el mar
    bio = 0.6 + 0.8 * fbm(3, 2, 9)               # las constructoras no crecen igual en todas partes
    t0 = time.time()
    for it in range(iters):
        outlet_it = outlet | (h <= SEA_LOW)
        filled = priority_flood(h, outlet_it, 1e-5)
        order = np.argsort(-filled, axis=None)
        q = mfd(filled, src, order, 1.2)
        depth = filled - h
        gy, gx = np.gradient(filled, CELL)
        slope = np.minimum(np.hypot(gx, gy), 2.0)
        # convexidad de la lámina: el agua se acelera al pasar el labio
        lap = (np.roll(filled, 1, 0) + np.roll(filled, -1, 0) + np.roll(filled, 1, 1) + np.roll(filled, -1, 1) - 4 * filled) / CELL ** 2
        convex = np.clip(-lap, 0, 8.0)
        thin = np.exp(-depth / 0.06)
        qn = q / src.sum()                           # fracción del caudal total que pasa por la celda
        wq = np.clip((qn / 1e-3) ** 0.5, 0, 4.0)
        near_src = smoothstep(7.0, 3.0, np.sqrt((X - SPRING[0]) ** 2 + (Y - SPRING[1]) ** 2))
        # la precipitación se concentra donde la lámina pasa un labio (convexidad de la
        # superficie del agua) y es casi nula en el plano inclinado y en el agua remansada:
        # así los obstáculos crecen, represan agua y se convierten en presas
        fs = gaussian_filter(filled, 1.0)
        lapw = (np.roll(fs, 1, 0) + np.roll(fs, -1, 0) + np.roll(fs, 1, 1) + np.roll(fs, -1, 1) - 4 * fs) / CELL ** 2
        lip = np.clip(-lapw, 0, 6.0)
        # un labio no puede crecer más que el agua que le llega: las puntas aisladas se frenan
        above = h - gaussian_filter(filled, 6.0)
        calm = np.exp(-np.clip(above, 0, None) / 0.5)
        dep = 0.0035 * wq * (lip ** 1.4 + 0.08 * slope) * thin * bio * calm * (1 - near_src)
        dep[h <= SEA_LOW + 0.5] = 0.0             # bajo el mar no se precipita (agua salada)
        dep += 0.0015 * np.minimum(depth, 1.5) * (q > 1e-9)  # el fondo de las pozas sube despacio
        h = h + gaussian_filter(np.minimum(dep, 0.025), 1.0)   # el precipitado cubre un labio, no una celda
        if (it + 1) % report == 0:
            pools = (depth > 0.05) & (h > SEA_LOW)
            print(f"iter {it + 1}: pozas {pools.mean() * 100:.1f}% · máx. depósito {(h - h0).max():.2f} m · {time.time() - t0:.0f}s", flush=True)
    filled = priority_flood(h, outlet | (h <= SEA_LOW), 1e-5)
    return h, filled, q


def preview(h, w, q, path):
    gy, gx = np.gradient(h, CELL)
    nrm = np.stack([-gx, -gy, np.ones_like(h)], -1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    light = np.array([-0.5, 0.6, 0.62]); light /= np.linalg.norm(light)
    shade = np.clip(nrm @ light, 0, 1)
    dep = np.clip((h - h0) / 1.2, 0, 1)
    rock = np.array([0.28, 0.29, 0.33])
    trav = np.array([0.86, 0.78, 0.62])
    col = rock * (1 - dep[..., None]) + trav * dep[..., None]
    col = col * (0.35 + 0.75 * shade[..., None])
    depth = w - h
    wat = np.clip(depth / 0.6, 0, 1)[..., None]
    col = col * (1 - 0.65 * wat) + np.array([0.20, 0.42, 0.45]) * 0.65 * wat
    sea = (w <= SEA_LOW + 1e-3) & (h < SEA_LOW)
    col[sea] = np.array([0.06, 0.18, 0.22])
    flow = np.clip(np.log10(q * N * N + 1) / 3, 0, 1)[..., None]
    col = col * (1 - 0.35 * flow) + np.array([0.9, 0.95, 1.0]) * 0.35 * flow
    img = (np.clip(col[::-1], 0, 1) * 255).astype(np.uint8)  # norte arriba
    Image.fromarray(img).resize((900, 900), Image.LANCZOS).save(path)


if __name__ == "__main__":
    import sys
    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 420
    h, w, q = simulate(h0.copy(), iters)
    np.save(os.path.join(WORK, "gours_h0.npy"), h0.astype(np.float32))
    np.save(os.path.join(WORK, "gours_h.npy"), h.astype(np.float32))
    np.save(os.path.join(WORK, "gours_w.npy"), w.astype(np.float32))
    np.save(os.path.join(WORK, "gours_q.npy"), q.astype(np.float32))
    preview(h, w, q, os.path.join(WORK, "gours_preview.png"))
