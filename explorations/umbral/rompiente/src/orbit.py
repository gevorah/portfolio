"""Estudio I · Umbral desde la órbita.

El mapa sale de la misma geografía que la escena de La Rompiente: en un mundo
pequeño (radio ≈ 2,6 km) la isla principal, la isleta y el arco del
archipiélago son legibles desde el espacio. La firma a escala planetaria es la
dorsal submarina: una banda de bajíos turquesa que se curva como la propia
ola, con las islas ensartadas en ella.

El mapa no se pinta con máscaras sino con un relieve continuo en metros:
fondo abisal, el lomo de la dorsal, plataformas con su talud, arrecifes,
canales de marea y la tierra. El color del agua es una rampa de profundidad y
la misma altura sirve de mapa de relieve para el sombreado de la esfera.

Salida: work/map_albedo.png, work/map_land.png, work/map_height.png,
work/map_clouds.png, img/r6-orbita.png, img/r6-orbita-escala.png
"""

import math
import os
import time

import numpy as np
from PIL import Image

import globe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
IMG = os.path.join(ROOT, "img")
os.makedirs(WORK, exist_ok=True)
os.makedirs(IMG, exist_ok=True)

MW, MH = 4096, 2048
R = 2600.0                      # radio del planeta, metros
LAT0, LON0 = 18.0, 0.0          # la isla principal
KX = R * math.cos(math.radians(LAT0))      # metros de planta por radián de longitud
T_START = time.time()


def log(msg):
    print(f"[{time.time() - T_START:6.1f}s] {msg}", flush=True)


# --- ruido de gradiente ------------------------------------------------------
# Sin tablas de permutación: un hash entero por vértice de la retícula. Se
# evalúa en coordenadas arbitrarias, así el detalle del archipiélago se calcula
# solo donde hace falta y el ruido 3D sobre la esfera no se pellizca en los polos.
_ANG = np.arange(16) * (2 * np.pi / 16) + 0.2
_G2X, _G2Y = np.cos(_ANG).astype(np.float32), np.sin(_ANG).astype(np.float32)
_G3 = np.array([[1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0], [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
                [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1], [1, 1, 0], [-1, 1, 0], [0, -1, 1], [0, -1, -1]],
               np.float32)


def _hash(seed, *ii):
    h = np.uint32((seed * 0x9E3779B1 + 0x7F4A7C15) & 0xFFFFFFFF)
    for k, i in zip((0x8DA6B343, 0xD8163841, 0xCB1AB31F), ii):
        h = h ^ (np.asarray(i).astype(np.uint32) * np.uint32(k))
    h = h ^ (h >> np.uint32(16))
    h = h * np.uint32(0x7FEB352D)
    h = h ^ (h >> np.uint32(15))
    h = h * np.uint32(0x846CA68B)
    h = h ^ (h >> np.uint32(16))
    return h & np.uint32(15)


def _fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)


def noise2(x, y, seed):
    """Ruido de gradiente 2D, desviación típica ≈ 1."""
    xi, yi = np.floor(x), np.floor(y)
    fx, fy = (x - xi).astype(np.float32), (y - yi).astype(np.float32)
    xi, yi = xi.astype(np.int32), yi.astype(np.int32)
    u, v = _fade(fx), _fade(fy)
    n = 0
    for dx in (0, 1):
        for dy in (0, 1):
            h = _hash(seed, xi + dx, yi + dy)
            g = (fx - dx) * _G2X[h] + (fy - dy) * _G2Y[h]
            n = n + g * (u if dx else 1 - u) * (v if dy else 1 - v)
    return n * 4.65


def noise3(x, y, z, seed):
    """Ruido de gradiente 3D, desviación típica ≈ 1."""
    xi, yi, zi = np.floor(x), np.floor(y), np.floor(z)
    fx, fy, fz = (x - xi).astype(np.float32), (y - yi).astype(np.float32), (z - zi).astype(np.float32)
    xi, yi, zi = xi.astype(np.int32), yi.astype(np.int32), zi.astype(np.int32)
    u, v, w = _fade(fx), _fade(fy), _fade(fz)
    n = 0
    for dx in (0, 1):
        wx = u if dx else 1 - u
        for dy in (0, 1):
            wxy = wx * (v if dy else 1 - v)
            for dz in (0, 1):
                h = _hash(seed, xi + dx, yi + dy, zi + dz)
                g = (fx - dx) * _G3[h, 0] + (fy - dy) * _G3[h, 1] + (fz - dz) * _G3[h, 2]
                n = n + g * wxy * (w if dz else 1 - w)
    return n * 3.7


def fbm2(x, y, octaves, seed, gain=0.5):
    s, a, tot, f = 0, 1.0, 0.0, 1.0
    for i in range(octaves):
        s = s + a * noise2(x * f + 17.3 * i, y * f - 9.1 * i, seed + 101 * i)
        tot += a * a
        a *= gain
        f *= 2.03
    return s / math.sqrt(tot)


def fbm_s(P, scale, octaves, seed, gain=0.5):
    """fbm 3D sobre la esfera; P: puntos unitarios, scale: tamaño del rasgo en metros."""
    k = R / scale
    s, a, tot = 0, 1.0, 0.0
    for i in range(octaves):
        s = s + a * noise3(P[0] * k + 5.1 * i, P[1] * k - 3.7 * i, P[2] * k + 1.9 * i, seed + 101 * i)
        tot += a * a
        a *= gain
        k *= 2.03
    return s / math.sqrt(tot)


# --- utilidades ----------------------------------------------------------------
def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def union(floor, other, k):
    """Une dos fondos: el más alto manda; el redondeo crece con la profundidad (nada en lo somero)."""
    kk = np.clip(-np.maximum(floor, other) / 20, 0.05, 1) * k
    h = np.clip(0.5 + 0.5 * (floor - other) / kk, 0, 1)
    return other * (1 - h) + floor * h + kk * h * (1 - h)


def segd(px, pz, a, b):
    ax, az = a
    bx, bz = b
    vx, vz = bx - ax, bz - az
    h = np.clip(((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz), 0, 1)
    return np.hypot(px - ax - vx * h, pz - az - vz * h)


def polyd(px, pz, pts):
    return np.min([segd(px, pz, a, b) for a, b in zip(pts[:-1], pts[1:])], axis=0)


def wrap_angle(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def _box(a, r, axis):
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)


def blur(a, r):
    """Desenfoque casi gaussiano: tres pasadas de caja de radio r píxeles."""
    r = max(int(r), 1)
    for _ in range(3):
        a = _box(_box(a, r, 0), r, 1)
    return a


def sample(a, px, py):
    """Muestreo bilineal de a en coordenadas de píxel (con borde replicado)."""
    h, w = a.shape
    px = np.clip(px, 0, w - 1.001)
    py = np.clip(py, 0, h - 1.001)
    x0, y0 = px.astype(np.int32), py.astype(np.int32)
    fx, fy = px - x0, py - y0
    top = a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx
    bot = a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx
    return top * (1 - fy) + bot * fy


def lic(field, ux, uy, steps, h=1.0):
    """Convolución a lo largo de líneas de flujo: arrastra field según el campo (ux, uy)."""
    yy, xx = np.mgrid[0:field.shape[0], 0:field.shape[1]].astype(np.float32)
    acc, n = field.copy(), 1
    for sgn in (1.0, -1.0):
        px, py = xx.copy(), yy.copy()
        for i in range(steps):
            px += sgn * h * sample(ux, px, py)
            py += sgn * h * sample(uy, px, py)
            acc += sample(field, px, py) * (1 - i / steps)
            n += 1 - i / steps
    return acc / n


def resize(a, shape):
    """Reescala un campo float con interpolación bilineal."""
    return np.array(Image.fromarray(a.astype(np.float32), "F").resize((shape[1], shape[0]), Image.BILINEAR))


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)], np.float32)


def mix(a, b, t):
    """Interpolación lineal; si a o b son colores, t se extiende al canal."""
    t = np.asarray(t, np.float32)
    if t.ndim and max(np.ndim(a), np.ndim(b)) in (1, t.ndim + 1):
        t = t[..., None]
    return a * (1 - t) + b * t


# --- coordenadas -----------------------------------------------------------------
LON1 = ((np.arange(MW) + 0.5) / MW * 360 - 180).astype(np.float32)
LAT1 = (90 - (np.arange(MH) + 0.5) / MH * 180).astype(np.float32)


def sphere(LON, LAT):
    lo, la = np.radians(LON), np.radians(LAT)
    return np.cos(la) * np.sin(lo), np.sin(la) * np.ones_like(lo), np.cos(la) * np.cos(lo)


def plan(LON, LAT):
    """lon/lat → planta local de la escena (x este, z norte, metros)."""
    X = np.radians(((LON - LON0 + 180) % 360) - 180) * KX
    Z = np.radians(LAT - LAT0) * R
    return X.astype(np.float32), Z.astype(np.float32)


def plan_to_lonlat(x, z):
    return LON0 + math.degrees(x / KX), LAT0 + math.degrees(z / R)


def kx_at(z):
    """Factor planta → metros reales en dirección este a la altura z (la planta estira el este con la latitud)."""
    return math.cos(math.radians(plan_to_lonlat(0, z)[1])) / math.cos(math.radians(LAT0))


class Grid:
    """Trozo del mapa con sus coordenadas: planta, esfera y tamaño real del píxel."""

    def __init__(self, LON, LAT):
        self.LON, self.LAT = LON, LAT
        self.X, self.Z = plan(LON, LAT)
        self.P = sphere(LON, LAT)
        self.kx = (np.cos(np.radians(LAT)) / math.cos(math.radians(LAT0))).astype(np.float32)
        self.dx = (R * np.cos(np.radians(LAT)) * 2 * np.pi / MW).astype(np.float32)
        self.dz = np.float32(R * np.pi / MH)
        self.shape = LON.shape

    def sub(self, sl):
        return Grid(self.LON[sl], self.LAT[sl])

    def box(self, x0, x1, z0, z1):
        """Recorte (filas, columnas) que cubre un rectángulo de la planta."""
        c = np.nonzero((self.X[0] >= x0) & (self.X[0] <= x1))[0]
        r = np.nonzero((self.Z[:, 0] >= z0) & (self.Z[:, 0] <= z1))[0]
        if len(c) == 0 or len(r) == 0:
            return None
        return slice(r[0], r[-1] + 1), slice(c[0], c[-1] + 1)


class Window(Grid):
    """Ventana del mapa (filas contiguas, columnas con vuelta en longitud)."""

    def __init__(self, lon_a, lon_b, lat_a, lat_b):
        c0 = int(math.floor((lon_a + 180) / 360 * MW))
        c1 = int(math.ceil((lon_b + 180) / 360 * MW))
        r0 = max(int(math.floor((90 - lat_b) / 180 * MH)), 0)
        r1 = min(int(math.ceil((90 - lat_a) / 180 * MH)), MH)
        self.ix = np.ix_(np.arange(r0, r1), np.arange(c0, c1) % MW)
        super().__init__(*np.meshgrid(LON1[self.ix[1][0]], LAT1[self.ix[0][:, 0]]))


# --- la dorsal: eje del arco ------------------------------------------------------
# polilínea en planta, de la isla principal hacia el oeste y de vuelta al sur
RIDGE = [(60, 520), (-40, 860), (-120, 1150), (-420, 1500), (-820, 1700),
         (-1250, 1750), (-1700, 1600), (-2100, 1350), (-2420, 980), (-2600, 560), (-2620, 120), (-2450, -260)]


def catmull(pts, n):
    p = np.array([pts[0]] + list(pts) + [pts[-1]], np.float64)
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(p[-2])
    return np.array(out)


# el marco se prolonga por los dos extremos para que no se vuelva polar en las puntas;
# s = 0 sigue siendo la cabeza del arco (60, 520)
SPINE = catmull([(300, -250), (170, 160)] + RIDGE + [(-2250, -620), (-2000, -900)], 12)
_SEGL = np.hypot(*np.diff(SPINE, axis=0).T)
_S0 = np.concatenate([[0], np.cumsum(_SEGL)])
_S0 -= _S0[np.argmin(np.hypot(SPINE[:, 0] - RIDGE[0][0], SPINE[:, 1] - RIDGE[0][1]))]


def arc_frame(X, Z):
    """Marco curvilíneo del arco: s (m a lo largo, desde la cabeza) y q (m, + hacia el interior)."""
    best = np.full(X.shape, 1e12, np.float32)
    s = np.zeros(X.shape, np.float32)
    sg = np.ones(X.shape, np.float32)
    for (ax, az), (bx, bz), L, s0 in zip(SPINE[:-1], SPINE[1:], _SEGL, _S0[:-1]):
        vx, vz = bx - ax, bz - az
        h = np.clip(((X - ax) * vx + (Z - az) * vz) / (L * L), 0, 1)
        dx, dz = X - ax - vx * h, Z - az - vz * h
        d2 = dx * dx + dz * dz
        m = d2 < best
        best[m] = d2[m]
        s[m] = (s0 + h * L)[m]
        sg[m] = np.where(vx * dz - vz * dx >= 0, 1.0, -1.0)[m]    # el arco gira a la izquierda: + es el interior
    return s, sg * np.sqrt(best)


def arc_tangent(x, z):
    """Tangente (en planta) del punto del eje más cercano a (x, z)."""
    i = int(np.clip(np.argmin(np.hypot(SPINE[:, 0] - x, SPINE[:, 1] - z)), 0, len(SPINE) - 2))
    t = SPINE[i + 1] - SPINE[i]
    return t / np.linalg.norm(t)


# --- geografía -------------------------------------------------------------------
# la isla (misma planta que la escena)
A0, A1, A2, A3 = (300, 700), (110, 470), (55, 330), (25, 240)
# cuerpo lobulado: el lóbulo de la escena (600, 820) y otros que abren bahías
LOBES = [(600, 820, 300, 240), (900, 1100, 260, 200), (1050, 700, 180, 150), (760, 1380, 170, 130), (420, 1080, 150, 110)]
SUMMIT = (880, 1090)
ISLETA = (160, 840)
STACKS = [(-20, 440, 9), (-58, 432, 8), (-92, 482, 10), (-130, 542, 7)]      # farallones de la escena
BAR = [(-130, 542), (-70, 650), (30, 760), (110, 822)]                       # barra de arena hacia la isleta

# El arco, con jerarquía: una isla al borde de la plataforma de cabeza, una
# mediana con un gran bajío, un grupo apretado de islotes, la isla de barrera
# con su laguna y luego una cola que se adelgaza hasta quedar en bancos
# ahogados. Semiejes y anchos de arrecife en metros reales.
ISLES = [
    # (x, z, semieje a lo largo, semieje transversal, altura, ancho del bajío, giro, curvatura, semilla)
    (-150, 1130, 170, 92, 55, 150, -12, 0.15, 1),     # I · la vecina, sobre la plataforma de cabeza
    (-430, 1495, 270, 118, 64, 250, 6, 0.30, 2),      # II · la mediana, con su gran bajío
    (-770, 1688, 96, 52, 36, 160, 22, 0.20, 3),       # III · el grupo
    (-868, 1728, 58, 36, 22, 130, -18, 0.0, 4),
    (-832, 1646, 32, 24, 12, 110, 0, 0.0, 5),
    (-1722, 1592, 46, 32, 24, 75, 10, 0.1, 7),        # V · la aislada
    (-2082, 1348, 36, 25, 17, 62, 28, 0.0, 8),        # VI · la pareja
    (-2128, 1302, 22, 17, 9, 52, -20, 0.0, 9),
]
# IV · isla de barrera: anillo de arrecife, laguna, un cerro central y motus
ATOLL = dict(c=(-1268, 1756), ab=(265, 175), ring=40, lagoon=22, isle=(-1300, 1768, 72, 55, 88),
             passes=(1.15, -2.2))
# la cola: bancos ahogados que solo se leen como manchas claras (x, z, radio, techo, cayo)
BANKS = [(-2420, 980, 150, 0.6, True), (-2600, 560, 135, 7.0, False), (-2620, 120, 115, 15.0, False),
         (-2450, -260, 125, 27.0, False)]
# otros bancos lejanos: el resto del planeta no está vacío, pero es océano
FAR = [(4200, -1800, 380, 3.0, True), (-5200, -900, 260, 9.0, False), (6800, 2400, 300, 20.0, False)]

# perfil del lomo a lo largo del arco: ancho de la plataforma y profundidad de su cresta
# s de cada rasgo: I 650 · II 1125 · III 1550 · IV 2020 · V 2505 · VI 2970 · bancos 3445, 3905, 4350, 4765.
# Tras la isla de barrera el lomo es un rosario que adelgaza: cuentas en los
# bancos, collados más hondos y estrechos entre ellos.
RIDGE_W = ([-500, -200, 0, 500, 700, 830, 900, 990, 1120, 1350, 1560, 1700, 1830, 2020, 2200, 2350, 2505, 2700,
            2970, 3200, 3445, 3680, 3905, 4130, 4350, 4560, 4765, 4950, 5150],
           [60, 200, 330, 320, 250, 140, 130, 170, 260, 240, 220, 140, 105, 165, 80, 58, 95, 52, 82, 46, 86, 42, 74,
            38, 64, 34, 56, 20, 0])
RIDGE_D = ([-500, -200, 0, 600, 760, 850, 930, 1020, 1150, 1500, 1660, 1780, 1880, 2020, 2200, 2350, 2505, 2700,
            2970, 3200, 3445, 3680, 3905, 4130, 4350, 4560, 4765, 4950, 5150],
           [200, 20, 8, 9, 15, 36, 32, 12, 7, 8, 9, 18, 26, 15, 28, 40, 22, 44, 28, 50, 30, 56, 40, 62, 50, 72, 60,
            160, 400])


def arm_cx(z):
    """Eje del brazo en x para cada z (como en la escena)."""
    return np.interp(z, [240, 330, 470, 700], [25, 55, 110, 300]) - 30 * np.maximum(240 - z, 0) / 90


def talus(e, inner):
    """Profundidad que se suma fuera del borde de una plataforma (e: metros fuera del borde).

    Lado exterior del arco: el borde cae a pique hasta el abismo. Lado interior:
    una rampa tendida de unos 30 m que se lee como un degradado teal, y sólo
    después el talud.
    """
    e = np.maximum(e, 0)
    outer = 60 * (1 - np.exp(-e / 25)) + 2600 * (1 - np.exp(-e / 220))
    ramp_in = 30 * (1 - np.exp(-e / 70)) + 2600 * (1 - np.exp(-np.maximum(e - 90, 0) / 380))
    return outer * (1 - inner) + ramp_in * inner


def local_uv(g, cx, cz, rot_deg):
    """Coordenadas locales en metros reales alrededor de (cx, cz), con u a lo largo del arco."""
    t = arc_tangent(cx, cz)
    a = math.atan2(t[1], t[0] * kx_at(cz)) + math.radians(rot_deg)
    dx, dz = (g.X - cx) * g.kx, g.Z - cz
    return dx * math.cos(a) + dz * math.sin(a), -dx * math.sin(a) + dz * math.cos(a)


def feature_box(g, cx, cz, ext):
    """Recorte que cubre un rasgo de radio ext (metros reales) centrado en (cx, cz)."""
    ex = ext / max(kx_at(cz + ext), 0.3)
    return g.box(cx - ex, cx + ex, cz - ext, cz + ext)


def dome(dc, h, width, P, seed):
    """Relieve de una isla pequeña: cerro con lomos y vaguadas."""
    base = (1 - np.exp(-dc / width)) ** 1.3
    rid = 1 - np.abs(fbm_s(P, width * 1.6, 3, seed)) * 0.55
    return h * base * (0.55 + 0.45 * rid) * (1 + 0.15 * fbm_s(P, width * 0.7, 2, seed + 7))


# --- el fondo global: llanura abisal y el lomo ancho de la dorsal ------------------
def base_floor():
    """Relieve a gran escala en todo el planeta, a baja resolución y reescalado."""
    cw, ch = MW // 4, MH // 4
    LON, LAT = np.meshgrid(((np.arange(cw) + 0.5) / cw * 360 - 180).astype(np.float32),
                           (90 - (np.arange(ch) + 0.5) / ch * 180).astype(np.float32))
    P = sphere(LON, LAT)
    X, Z = plan(LON, LAT)
    E = -(2050 + 330 * fbm_s(P, 2600, 3, 11))
    # el lomo de la dorsal levanta el fondo bajo el arco
    swell = -(620 + 1550 * (1 - np.exp(-(polyd(X, Z, RIDGE) / 1300) ** 1.6)))
    E = smax(E, swell, 120)
    for bx, bz, br, _, _ in FAR:
        E = smax(E, -(800 + 1400 * (1 - np.exp(-(np.hypot(X - bx, Z - bz) / (br * 2.2)) ** 1.6))), 120)
    return resize(blur(E, 8), (MH, MW))           # sin pliegues: el relieve del fondo también sombrea


# --- el archipiélago en detalle -----------------------------------------------------
class Layers:
    """Elevación (m sobre la media marea) y las capas que el color necesita."""

    def __init__(self, shape):
        z = lambda v=0.0: np.full(shape, v, np.float32)
        self.floor = z(-3000)                     # fondo marino
        self.land = z(-1)                         # tierra (solo donde coast < 0)
        self.coast = z(1e5)                       # distancia firmada a la costa
        self.reef = z(1e5)                        # distancia al borde de los arrecifes
        self.chan, self.bars, self.plume, self.surf = z(), z(), z(), z()
        self.west, self.valley, self.inner, self.head = z(), z(), z(), z()

    def elevation(self):
        return np.where(self.coast < 0, np.maximum(self.land, 0.4), np.minimum(self.floor, -0.15))


def main_island(g, Ly, nE, nF):
    """La isla principal, la isleta, los farallones y la barra: la planta de la escena."""
    X, Z, P = g.X, g.Z, g.P
    inner = Ly.inner
    arm = np.minimum(np.minimum(segd(X, Z, A0, A1) - 64, segd(X, Z, A1, A2) - 62), segd(X, Z, A2, A3) - 50)
    body = np.full(X.shape, 1e9, np.float32)
    for (bx, bz, rx, rz) in LOBES:
        body = smin(body, (np.hypot((X - bx) / rx, (Z - bz) / rz) - 1) * min(rx, rz), 220)
    west = sstep(10, -30, X - arm_cx(Z)) * sstep(640, 520, Z)           # la cara de La Rompiente
    calm = 1 - 0.7 * west                                               # la cara oeste es un frente limpio
    bay = np.hypot(X - 820, (Z - 560) * 1.3) - 120 + 40 * fbm_s(P, 120, 3, 33)   # bahía al este del brazo
    # costa: la forma grande da el relieve; el detalle fino sólo recorta la orilla
    shape = smin(arm, body, 140) - 25 + (26 * fbm_s(P, 320, 2, 31) + 26 * fbm_s(P, 260, 2, 35)) * calm
    shape = np.maximum(shape, -bay)
    coast_main = np.maximum(shape + (9 * fbm_s(P, 70, 2, 36) + 6 * fbm_s(P, 24, 2, 37)) * calm, -bay)
    coast_isleta = np.hypot(X - ISLETA[0], (Z - ISLETA[1]) * 1.4) - 60 + 6 * nF
    coast = np.minimum(coast_main, coast_isleta)
    for (sx, sz, sr) in STACKS:
        coast = np.minimum(coast, np.hypot(X - sx, Z - sz) - sr)

    # relieve: macizo al nordeste, el lomo del brazo bajando hacia la punta
    dc = blur(np.maximum(-shape, 0), 3) * sstep(0, 10, -coast_main)
    r_s = np.hypot(X - SUMMIT[0], Z - SUMMIT[1])
    h_body = 60 + 175 * np.exp(-(r_s / 520) ** 2) + 45 * np.exp(-(np.hypot(X - 600, Z - 820) / 250) ** 2)
    e_body = h_body * (1 - np.exp(-dc / 170)) ** 1.2
    h_arm = np.interp(Z, [200, 300, 450, 600, 780], [34, 58, 78, 96, 120])
    side = 24 + 56 * (1 - west)                   # al oeste el lomo cae en acantilado
    e_arm = h_arm * sstep(0, side, dc) * (0.85 + 0.15 * sstep(0, 90, dc))
    w_arm = sstep(-60, 90, body - arm)
    land = mix(e_body, e_arm, w_arm)
    # vaguadas: ruido fino arrastrado ladera abajo (LIC según la pendiente del macizo).
    # Así los barrancos siguen la forma real de cada lóbulo y del brazo, sin estrella.
    down = blur(land, 10)
    gx, gz = np.gradient(down, axis=1), np.gradient(down, axis=0)
    gn = np.hypot(gx, gz) + 1e-4
    ux, uy = -gx / gn, -gz / gn
    on_land = shape < 30
    fine = lic(fbm_s(P, 34, 2, 43), ux, uy, 30, 1.6)
    broad = lic(fbm_s(P, 90, 2, 45), ux, uy, 40, 2.2)
    fine = fine / (fine[on_land].std() + 1e-6)
    broad = broad / (broad[on_land].std() + 1e-6)
    rel = land / (land.max() + 1e-6)
    # pocas vaguadas anchas que nacen por debajo de las crestas, con afluentes finos
    born = sstep(0.82, 0.55, rel + 0.12 * fbm_s(P, 160, 2, 47))
    valley = np.clip(sstep(-0.45, -1.5, broad) + 0.6 * sstep(-0.7, -1.7, fine) * sstep(-1.0, 0.0, broad), 0, 1) * born
    valley = blur(valley, 2) * sstep(0, 25, dc) * (1 - 0.8 * west)
    incise = valley * (30 * (1 - w_arm) + 14 * w_arm) * (1 - np.exp(-dc / 45)) * sstep(0, 0.3, rel)
    land = land - incise + 0.8 * fbm_s(P, 40, 2, 51) * sstep(0, 40, dc)
    land = np.where(coast_main < 0, land, -1.0)
    land = np.where(coast_isleta < 0, np.maximum(land, 30 * (1 - np.exp(-np.maximum(-coast_isleta, 0) / 18))), land)
    for (sx, sz, sr) in STACKS:
        land = np.where(np.hypot(X - sx, Z - sz) < sr, np.maximum(land, 34.0), land)

    # plataforma de cabeza: ancha hacia el arco, con el agua más honda frente al acantilado
    wplat = 230 + 80 * fbm_s(P, 500, 2, 65) + 140 * inner
    e_h = coast_main - wplat + (28 * nE + 5 * nF) * (0.35 + 0.65 * inner)    # a barlovento, borde más limpio
    # en el lado exterior el borde se rompe en espolones y cañones que entran en la plataforma
    outer = 1 - inner
    nc = fbm_s(P, 130, 2, 73)
    e_h = e_h + (110 * sstep(0.7, 1.6, nc) - 80 * sstep(0.7, 1.6, -nc)) * outer
    bight = sstep(-60, -200, X - arm_cx(Z)) * sstep(760, 600, Z) * sstep(150, 300, Z)
    top = 1.8 + 13 * sstep(-0.9, 1.2, fbm_s(P, 260, 3, 67)) + 24 * bight     # mosaico de bajos y hoyas
    # la orilla: casi siempre roca que entra en agua turquesa; arenales intermareales sólo a trechos
    flats = sstep(0.3, 1.2, fbm_s(P, 180, 2, 71)) * (1 - west)
    near = sstep(0, 14 + 90 * flats, np.minimum(coast_main, coast_isleta))
    # talud graduado hacia fuera: turquesa → teal → petróleo en unos 300 m en vez de un corte
    ee = np.maximum(e_h, 0)
    graded = 50 * (1 - np.exp(-ee / 110)) + 2600 * (1 - np.exp(-np.maximum(ee - 140, 0) / 900)) \
        + 2400 * sstep(280, 650, ee)                 # llega al abismo dentro del recorte de la isla
    drop = mix(talus(e_h, inner), graded, outer)
    floor = -(1.0 + (top - 1.0) * near + 10 * np.clip(1 + e_h / 260, 0, 1) ** 2 * near + drop)
    floor = np.where(bay < 0, np.minimum(floor, -(2.5 + 8 * sstep(0, 70, -bay))), floor)      # la bahía este
    floor = union(Ly.floor, floor, 8)
    # la rasa al pie de La Rompiente, la barra de arena y el anillo de la isleta
    rasa = west * sstep(20, -10, coast - (60 + 50 * sstep(240, 400, Z)) - 10 * nF)
    floor = np.where(rasa > 0, np.maximum(floor, -(6.5 + 1.5 * nF) * rasa - 30 * (1 - rasa)), floor)
    floor = np.maximum(floor, -(0.5 + (polyd(X, Z, BAR) / 9) ** 2 + 0.4 * nF))
    ri = np.hypot(X - ISLETA[0], (Z - ISLETA[1]) * 1.2) - 104 - 10 * nE
    floor = np.maximum(floor, -(4.5 + 22 * sstep(0, 50, ri) + talus(ri - 50, inner)))

    Ly.floor, Ly.coast, Ly.land = floor, np.minimum(Ly.coast, coast), np.maximum(Ly.land, land)
    Ly.reef = np.minimum(Ly.reef, coast_isleta - 44)
    Ly.west = west * sstep(-40, -5, -dc)
    Ly.head = np.maximum(Ly.head, sstep(60, -60, e_h))
    Ly.valley = np.maximum(Ly.valley, np.where(coast_main < 0, valley, 0))


def arc_island(g, Ly, isle, nE, nF):
    """Una isla del arco con su bajío propio, alargada según la tangente del arco."""
    cx, cz, a, b, h, reef, rot, bend, sd = isle
    P, inner = g.P, Ly.inner
    u, v = local_uv(g, cx, cz, rot)
    v = v - bend * b * (u / a) ** 2
    wu = u + 0.22 * a * fbm_s(P, a * 1.2, 2, 200 + sd)
    c = (np.hypot(wu / a, v / b) - 1) * b + 0.18 * b * fbm_s(P, b * 0.8, 3, 210 + sd) + 4 * nF
    # bajío propio: más ancho hacia el interior del arco
    rw = reef * (0.7 + 0.3 * fbm_s(P, a * 2, 2, 220 + sd)) * (0.75 + 0.5 * inner)
    er = c - rw + 30 * nE * np.clip(reef / 200, 0.3, 1)
    flat = 0.4 + 2.6 * sstep(0, 12 + rw * 0.5 * sstep(0.2, 1.2, fbm_s(P, 120, 2, 225 + sd)), c) \
        + 1.6 * sstep(-0.5, 1.5, fbm_s(P, 70, 2, 230 + sd))
    crest = 1.6 * np.exp(-((er + 14) / 12) ** 2)
    fl = -(np.maximum(flat - crest, 0.3) + 8 * np.clip(1 + er / 120, 0, 1) ** 2 * sstep(-rw, 0, er) + talus(er, inner))
    Ly.floor = union(Ly.floor, fl, 8)
    Ly.reef = np.minimum(Ly.reef, er)
    Ly.coast = np.minimum(Ly.coast, c)
    m = c < 0
    if m.any():
        Pm = tuple(p[m] for p in P)
        Ly.land[m] = np.maximum(Ly.land[m], dome(-c[m], h, max(b * 0.6, 14), Pm, 240 + sd))
        Ly.valley[m] = np.maximum(Ly.valley[m], sstep(-0.2, -0.8, -np.abs(fbm_s(Pm, b * 1.1, 2, 240 + sd))))


def barrier_island(g, Ly, nF):
    """IV · anillo de arrecife con pasos, laguna con cabezos, motus y el cerro central."""
    at = ATOLL
    P, inner = g.P, Ly.inner
    u, v = local_uv(g, at["c"][0], at["c"][1], 0)
    A, B = at["ab"]
    phi = np.arctan2(v / B, u / A)
    sd_mid = (np.hypot(u / A, v / B) - 1) * B + 14 * fbm_s(P, 120, 2, 251) + 5 * nF
    ring = np.abs(sd_mid) - at["ring"] / 2 * (0.8 + 0.4 * sstep(-1, 1, fbm_s(P, 90, 2, 253)))
    pas = sum(np.exp(-(wrap_angle(phi - p0) / 0.11) ** 2) for p0 in at["passes"])
    rim = 1.0 + 9 * pas
    lag = rim + (at["lagoon"] - rim) * (1 - np.exp(-np.maximum(ring, 0) / 38))
    lag = lag - 15 * sstep(0.9, 1.5, fbm_s(P, 28, 2, 255)) * sstep(20, 60, ring)        # cabezos en la laguna
    out = rim + 6 * (1 - np.exp(-np.maximum(ring, 0) / 10)) + talus(ring, inner)
    Ly.floor = union(Ly.floor, -np.where(ring < 0, rim, np.where(sd_mid < 0, np.maximum(lag, 0.6), out)), 8)
    Ly.reef = np.minimum(Ly.reef, np.where(sd_mid > 0, ring, 1e5))
    # motus sobre el anillo, sobre todo a barlovento
    motu = ring + 26 - 32 * sstep(0.6, 1.4, fbm_s(P, 60, 2, 257) + 0.5 * np.cos(phi)) * (1 - sstep(0.15, 0.4, pas))
    Ly.coast = np.minimum(Ly.coast, motu)
    Ly.land = np.where(motu < 0, np.maximum(Ly.land, 3.5 * (1 - np.exp(-np.maximum(-motu, 0) / 6))), Ly.land)
    ix, iz, ia, ib, ih = at["isle"]
    ui, vi = local_uv(g, ix, iz, 25)
    ci = (np.hypot(ui / ia, vi / ib) - 1) * ib + 9 * fbm_s(P, 50, 3, 259)
    Ly.coast = np.minimum(Ly.coast, ci)
    Ly.floor = union(Ly.floor, -(0.6 + 3 * sstep(0, 45, ci) + talus(ci - 45, 1.0)), 8)
    m = ci < 0
    if m.any():
        Ly.land[m] = np.maximum(Ly.land[m], dome(-ci[m], ih, 22, tuple(p[m] for p in P), 261))


def drowned_bank(g, Ly, bank, i, nE, nF):
    """Banco de la cola: una mancha clara sobre el lomo; el primero con un cayo."""
    bx, bz, br, btop, cay = bank
    P = g.P
    u, v = local_uv(g, bx, bz, 0)
    eb = np.hypot(u / 1.5, v) - br * (0.7 + 0.3 * sstep(-1.5, 1.5, fbm_s(P, 140, 2, 270 + i))) + 25 * nE
    Ly.floor = union(Ly.floor, -(btop + 5 * sstep(-br, 0, eb) + 3 * sstep(0.4, 1.4, fbm_s(P, 45, 2, 280 + i))
                                 + talus(eb, Ly.inner)), 8)
    if cay:                                       # un cayo de arena apenas emergido
        cc = np.hypot(u / 1.8, v) - 16 + 5 * nF
        Ly.coast = np.minimum(Ly.coast, cc)
        Ly.land = np.where(cc < 0, np.maximum(Ly.land, 1.2), Ly.land)


def on(g, Ly, sl, fn, *args):
    """Aplica fn sobre un recorte de la ventana y devuelve las capas a su sitio."""
    if sl is None:
        return
    sub = Layers((1, 1))
    for k, v in vars(Ly).items():
        setattr(sub, k, v[sl].copy())
    fn(g.sub(sl), sub, *[a[sl] if isinstance(a, np.ndarray) else a for a in args])
    for k, v in vars(sub).items():
        getattr(Ly, k)[sl] = v


def archipelago(g, E0):
    """Relieve fino de la ventana del arco. E0: fondo global recortado."""
    X, Z, P = g.X, g.Z, g.P
    Ly = Layers(g.shape)
    log("marco curvilíneo del arco")
    hs = (slice(None, None, 2), slice(None, None, 2))
    s, q = arc_frame(X[hs], Z[hs])
    # la distancia sin signo se reescala aparte: interpolar q a través de su salto de signo la hundiría a 0
    aq = resize(np.abs(q), g.shape)
    s, q = resize(s, g.shape), resize(q, g.shape)
    hs = (slice(None, None, 4), slice(None, None, 4))
    # 1 en el lado cóncavo del arco; lejos del eje el lado deja de importar (y el signo de q salta)
    Ly.inner = resize(blur(sstep(-60, 60, q[hs]), 10), g.shape)
    Ly.inner = 0.5 + (Ly.inner - 0.5) * sstep(900, 350, aq) * sstep(-700, -300, s) * sstep(5300, 4900, s)
    nE = fbm_s(P, 170, 2, 21)                     # borde ondulado de las plataformas
    nF = fbm_s(P, 40, 2, 23)

    # el lomo del arco, con anchura y cresta que cambian a lo largo
    log("lomo y plataformas")
    wid = np.interp(s, *RIDGE_W) * (1 + 0.22 * noise2(s / 380, np.float32(3.1), 61))
    dep = np.interp(s, *RIDGE_D) * (1 + 0.25 * noise2(s / 300, np.float32(7.7), 63))
    dep = dep * (0.6 + 0.9 * sstep(-1.0, 1.5, fbm_s(P, 260, 2, 69)))            # bajos y hoyas en la plataforma
    qe = aq / (0.85 + 0.45 * Ly.inner)    # más ancho hacia el interior (continuo: inner es suave)
    e = qe - wid + (30 * nE + 5 * nF) * np.clip(wid / 300, 0.4, 1)
    Ly.floor = smax(E0, -(dep + 10 * np.clip(1 + e / 240, 0, 1) ** 2 + talus(e, Ly.inner)), 40)

    on(g, Ly, g.box(-1000, 2400, -600, 2600), main_island, nE, nF)
    log("islas del arco")
    for isle in ISLES:
        ext = max(isle[2], isle[3]) + 2.2 * isle[5] + 350
        on(g, Ly, feature_box(g, isle[0], isle[1], ext), arc_island, isle, nE, nF)
    on(g, Ly, feature_box(g, *ATOLL["c"], 750), barrier_island, nF)
    for i, bank in enumerate(BANKS):
        on(g, Ly, feature_box(g, bank[0], bank[1], bank[2] * 1.6 + 350), drowned_bank, bank, i, nE, nF)

    # la marea: canales que se ramifican y crestas de arena, alineados con el arco
    log("canales, crestas y penachos")
    sw = s + 140 * noise2(s / 520, q / 260, 301)
    qw = q + 60 * noise2(s / 420, q / 210, 303)
    c1 = noise2(sw / 640, qw / 170, 305)
    width = 0.13 * (0.6 + 0.6 * sstep(-1, 1, noise2(s / 300, q / 300, 307)))
    shelf = sstep(-34, -10, Ly.floor)             # solo cortan las plataformas someras
    edge = sstep(-40, 0, e)                       # junto al borde se abren hacia el talud
    main = np.exp(-(c1 / (width * (1 + 1.4 * edge))) ** 2)
    c2 = noise2(sw / 230 + 0.55 * qw / 230 + 0.5 * nE, qw / 85 + 0.3 * nE, 309)
    trib = np.exp(-(c2 / 0.12) ** 2) * np.exp(-(c1 / 0.85) ** 2) * (0.35 + 0.65 * np.exp(-(c1 / 0.45) ** 2))
    # no tocan la orilla ni salen del arco
    keep_off = sstep(25, 80, Ly.coast) * sstep(-100, 150, s) * sstep(520, 360, aq)
    Ly.chan = np.clip(main + 0.55 * trib, 0, 1) * shelf * keep_off
    Ly.floor = Ly.floor - (13 * main + 5 * trib) * shelf * keep_off
    # crestas de arena: largas, sinuosas, en campos
    r1 = noise2(sw / 240 + 0.4 * nE, qw / 34 + 0.5 * nF, 311)
    env = sstep(0.5, 1.6, fbm2(s / 650, q / 420, 2, 313)) * sstep(-16, -3, Ly.floor) * keep_off
    Ly.bars = np.exp(-(r1 / 0.7) ** 2) * env * (1 - np.clip(main * 1.5, 0, 1))
    Ly.floor = np.minimum(Ly.floor + 3.0 * Ly.bars, np.maximum(Ly.floor, -1.0))      # suben, sin aflorar

    # penachos de sedimento: agua más clara y verde que sale de los bajíos con la corriente
    depth = np.maximum(-Ly.floor, 0)
    shallow = sstep(16, 4, depth)
    prox = np.clip(blur(shallow, 220 / float(g.dz)) * 2.4, 0, 1)
    # |q| y no q: el signo salta más allá de las puntas del marco; cada lado se distingue con inner, que es suave
    streak = fbm2((s - 1.4 * aq) / 1100, (aq + 30 * nE) / 140 + 7.3 * Ly.inner, 2, 321)
    Ly.plume = prox * sstep(0.0, 1.6, streak) * (1 - shallow) * (0.65 + 0.35 * Ly.inner)

    # oleaje: borde de los arrecifes de barlovento y el pie de La Rompiente
    gx = np.gradient(Ly.reef, axis=1)
    gz = -np.gradient(Ly.reef, axis=0)
    windward = np.clip(-gx / (np.hypot(gx, gz) + 1e-6) * 0.8 + 0.25, 0, 1)
    Ly.surf = np.exp(-((Ly.reef + 6) / 7) ** 2) * windward * 0.8
    foot = sstep(10, -30, X - arm_cx(Z)) * sstep(640, 520, Z) * sstep(240, 300, Z)
    Ly.surf = np.maximum(Ly.surf, foot * np.exp(-((Ly.coast - 4) / 6) ** 2))
    return Ly


def far_bank(g, E0, bank, seed):
    """Banco lejano: una plataforma redonda con, a veces, un cayo."""
    bx, bz, br, btop, cay = bank
    P = g.P
    Ly = Layers(g.shape)
    Ly.inner[:] = 0.3
    u, v = (g.X - bx) * g.kx, g.Z - bz
    eb = np.hypot(u, v) - br * (0.6 + 0.4 * sstep(-1.5, 1.5, fbm_s(P, 260, 2, 410 + seed))) \
        + 40 * fbm_s(P, 150, 3, 400 + seed)
    Ly.floor = smax(E0, -(btop + 6 * sstep(-br, 0, eb) + talus(eb, 0.3)), 30)
    if cay:
        Ly.coast = np.hypot(u / 1.6, v) - 24 + 8 * fbm_s(P, 30, 2, 420 + seed)
        Ly.land[:] = 1.5
    return Ly


# --- color -----------------------------------------------------------------------
# rampa de profundidad (m → color): abisal, petróleo, teal, turquesa, bajío, arena
RAMP = [(0.0, "d2c39f"), (0.25, "bdd8c0"), (1.0, "a9dcc6"), (2.6, "8acdbb"), (5.0, "6cc0af"), (9.0, "4eaa9f"),
        (14.0, "3f9e98"), (24.0, "2f8a8a"), (40.0, "28777e"), (70.0, "216572"), (140.0, "1f5866"),
        (320.0, "19505f"), (700.0, "13495a"), (1300.0, "0f3b4b"), (2300.0, "0b2633")]
_RD = np.log1p(np.array([d for d, _ in RAMP], np.float32))
_RC = np.array([hexc(c) for _, c in RAMP])


def ramp(depth):
    t = np.log1p(np.maximum(depth, 0))
    return np.stack([np.interp(t, _RD, _RC[:, i]) for i in range(3)], -1).astype(np.float32)


C = {k: hexc(v) for k, v in dict(
    sandwhite="e3e4cf", sand="d2c39f", algae="5b8a72", algae2="4c7a6a", channel="2a7f8c", plume="6db6a3",
    surf="eef3ee", slate="6b706b", basalt="454a4a", basalt2="353a3b", cliff="b9c0c8", cliff2="c9c2b0",
    green="55734a", green2="86a463", green3="3a5236", ochre="8d6c4c").items()}


def colorize(g, Ly):
    """Color de una ventana a partir de su elevación y capas. Devuelve color, máscara de tierra y elevación."""
    E = Ly.elevation()
    depth = np.maximum(-E, 0)
    col = ramp(depth)
    gx = np.gradient(E, axis=1) / g.dx
    gz = np.gradient(E, axis=0) / g.dz
    slope = np.hypot(gx, gz)

    # bajíos: arena blanca en las crestas, manchas de algas oliva-teal en el fondo medio
    m = depth < 20
    if m.any():
        Pm = tuple(p[m] for p in g.P)
        dm = depth[m]
        alg = sstep(0.2, 1.3, fbm_s(Pm, 110, 4, 501)) * sstep(1.4, 3.5, dm) * sstep(17, 7, dm) * (1 - Ly.bars[m])
        tint = mix(C["algae"], C["algae2"], sstep(0, 1.5, fbm_s(Pm, 60, 2, 503)))
        col[m] = mix(col[m], tint, alg * 0.55)
    col = col * (1 - 0.15 * (Ly.head * sstep(14, 4, depth))[..., None])
    white = sstep(1.2, 0.3, depth) * sstep(0, 25, Ly.coast)
    col = mix(col, C["sandwhite"], white * 0.45)
    # canales: un azul-teal más frío que corta los bajíos
    col = mix(col, C["channel"], Ly.chan * sstep(2, 10, depth) * 0.35)
    # talud: el borde exterior se hunde rápido y se lee más oscuro
    steep = sstep(0.6, 3.0, slope) * sstep(15, 60, depth) * sstep(1500, 300, depth) * (1 - Ly.inner)
    col = col * (1 - 0.10 * steep[..., None])
    # penachos de sedimento y oleaje
    col = mix(col, C["plume"], Ly.plume * 0.5 * sstep(4, 30, depth))
    col = mix(col, C["surf"], np.clip(Ly.surf, 0, 1) * 0.55 * sstep(-12, 0, -Ly.coast))

    # --- tierra (solo donde la hay)
    lm = np.clip(0.5 - Ly.coast / float(g.dz), 0, 1)
    m = lm > 0
    if m.any():
        Pm = tuple(p[m] for p in g.P)
        land = np.maximum(E[m], 0)
        sl = slope[m]
        steepL = sstep(0.45, 1.3, sl)
        high = sstep(60, 200, land)
        lee = np.clip(-gx[m] / (sl + 0.05), 0, 1) * sstep(0.05, 0.3, sl)        # laderas que miran al este
        conc = (blur(np.maximum(E, 0), 18) - np.maximum(E, 0))[m]
        valley = np.clip(sstep(2, 14, conc) * 0.5 + Ly.valley[m] * 0.8, 0, 1)
        patch = fbm_s(Pm, 80, 3, 511)
        veg = np.clip(1.5 * valley + 0.7 * lee + 0.35 * (1 - high) - 0.75 * steepL + 0.45 * patch - 0.5, 0, 1)
        veg = sstep(0.1, 0.6, veg)
        gcol = mix(C["green"], C["green3"], np.clip(valley * 1.2 - 0.2, 0, 1))
        gcol = mix(gcol, C["green2"], sstep(0.4, 0.9, lee) * (1 - valley) * sstep(120, 30, land) * (1 - steepL))
        rock = mix(C["slate"], C["basalt"], np.clip(steepL * 0.6 + high * 0.3 + 0.25 * fbm_s(Pm, 50, 2, 513), 0, 1))
        rock = mix(rock, C["basalt2"], valley * 0.4)
        rock = mix(rock, C["ochre"], sstep(1.4, 1.9, fbm_s(Pm, 90, 2, 515)) * sstep(30, 80, land) * (1 - valley) * 0.6)
        lc = mix(rock, gcol, veg * 0.92)
        # La Rompiente: cara oeste del brazo, roca clara expuesta
        cliff = Ly.west[m] * sstep(0.2, 0.7, sl)
        lc = mix(lc, mix(C["cliff"], C["cliff2"], sstep(-0.5, 0.8, fbm_s(Pm, 40, 2, 517))), np.clip(cliff, 0, 1) * 0.85)
        # playas en las orillas tendidas de sotavento y en los cayos
        cm = Ly.coast[m]
        beach = sstep(10, 2, -cm) * sstep(0.6, 0.15, sl) * (1 - Ly.west[m]) * sstep(0.3, 1.1, fbm_s(Pm, 120, 2, 519))
        beach = np.maximum(beach, sstep(4, 0.8, land))
        lc = mix(lc, C["sand"], np.clip(beach, 0, 1) * 0.85)
        low = sstep(7, 2, Ly.land[m]) * sstep(0, 1, -cm)                     # cayos y motus
        lc = mix(lc, mix(C["sand"], C["green"], sstep(1.5, 3.5, land) * sstep(-0.3, 0.6, patch)), low)
        lc = lc * (1 - 0.25 * valley[..., None])                             # oclusión en las vaguadas
        col[m] = mix(col[m], lc, lm[m])
    return col, lm, E


# --- composición del mapa ---------------------------------------------------------
log("fondo global")
E_glob = base_floor()
albedo = ramp(-E_glob)
landmask = np.zeros((MH, MW), np.float32)
height = E_glob * 0.012                           # el fondo apenas modela el agua


def paste(win, Ly):
    col, lm, E = colorize(win, Ly)
    albedo[win.ix] = col
    landmask[win.ix] = lm
    height[win.ix] = np.where(E > 0, E, E * 0.012)


log("archipiélago")
ROI = Window(-92, 58, -14, 84)
paste(ROI, archipelago(ROI, E_glob[ROI.ix]))

log("bancos lejanos")
for i, bank in enumerate(FAR):
    lo, la = plan_to_lonlat(bank[0], bank[1])
    if abs(lo) > 180:
        continue
    span = math.degrees(1600 / (R * max(math.cos(math.radians(la)), 0.2)))
    wb = Window(lo - span, lo + span, la - 36, min(la + 36, 89.9))
    paste(wb, far_bank(wb, E_glob[wb.ix], bank, i))

# casquete: hielo de mar fino en el polo sur, sin protagonismo
log("polo y nubes")
cw_, ch_ = MW // 2, MH // 2
LONc, LATc = np.meshgrid(((np.arange(cw_) + 0.5) / cw_ * 360 - 180).astype(np.float32),
                         (90 - (np.arange(ch_) + 0.5) / ch_ * 180).astype(np.float32))
Pc = sphere(LONc, LATc)
pole = resize(sstep(-74, -80, LATc + 3 * fbm_s(Pc, 300, 3, 601)) * 0.8, (MH, MW))
albedo = mix(albedo, hexc("c9d6df"), pole * 0.85)
landmask = np.maximum(landmask, pole * 0.8)

# nubes: pocas. Un par de sistemas con calles de cúmulos (bandas paralelas al
# viento, onduladas y rotas en cuentas) y algún campo de cúmulos sueltos que se
# aclara hacia el borde. Las coordenadas son metros
# sobre la esfera, con el viento fijo y la ondulación sumada (no girada): sin
# remolinos ni pellizco en el polo.
a_e = np.radians(LONc) * np.cos(np.radians(LATc)) * R                # metros hacia el este
b_n = np.radians(LATc) * R                                           # metros hacia el norte
TILT = math.radians(12)
cross = b_n * math.cos(TILT) - a_e * math.sin(TILT) + 140 * fbm_s(Pc, 800, 2, 615)
along = a_e * math.cos(TILT) + b_n * math.sin(TILT)
region = fbm_s(Pc, 1100, 3, 613)
band = sstep(0.35, 0.95, 0.5 + 0.5 * np.cos(2 * np.pi * cross / 105))
beads = sstep(0.1, 1.0, fbm2(along / 70, cross / 34, 2, 617))
streets = band * beads * sstep(0.8, 1.5, region) * sstep(-0.3, 0.9, fbm2(along / 1100, cross / 350, 2, 619))
cumulus = sstep(0.3, 0.9, fbm_s(Pc, 48, 2, 621, gain=0.4)) * sstep(1.2, 2.0, fbm_s(Pc, 650, 2, 623))
clouds = blur(np.clip(np.maximum(streets * 0.75, cumulus * 0.85), 0, 1), 1)
Xc, Zc = plan(LONc, LATc)
clouds *= 0.35 + 0.65 * sstep(250, 900, polyd(Xc, Zc, RIDGE))       # el arco queda casi despejado
clouds *= sstep(64, 50, np.abs(LATc))
clouds = resize(clouds, (MH, MW))
Image.fromarray((clouds * 255).astype(np.uint8)).save(os.path.join(WORK, "map_clouds.png"))

# sombras de las nubes sobre el mar: desplazadas lejos del sol
VIEW = dict(lon0=-6, lat0=26, roll=-6)
LIGHT = [0.42, 0.40, 0.81]
Mv = globe.view_matrix(VIEW["lon0"], VIEW["lat0"], VIEW["roll"])
Lw = (np.array(LIGHT) / np.linalg.norm(LIGHT)) @ Mv                   # luz en el mundo
lo_c, la_c = math.radians(-18), math.radians(40)                        # centro del archipiélago
east = np.array([math.cos(lo_c), 0, -math.sin(lo_c)])
north = np.array([-math.sin(la_c) * math.sin(lo_c), math.cos(la_c), -math.sin(la_c) * math.cos(lo_c)])
up = np.array([math.cos(la_c) * math.sin(lo_c), math.sin(la_c), math.cos(la_c) * math.cos(lo_c)])
h_cloud = 0.010
sh_e, sh_n = -h_cloud * (Lw @ east) / (Lw @ up), -h_cloud * (Lw @ north) / (Lw @ up)
shift = (int(round(-sh_n * MH / math.pi)), int(round(sh_e / math.cos(la_c) * MW / (2 * math.pi))))
shadow = blur(np.roll(clouds, shift, axis=(0, 1)), 3)
albedo = albedo * (1 - 0.32 * shadow[..., None])

Image.fromarray((np.clip(albedo, 0, 1) * 255).astype(np.uint8)).save(os.path.join(WORK, "map_albedo.png"))
cwt = clouds[..., None] * 0.88
albedo_c = albedo * (1 - cwt) + np.array([0.88, 0.89, 0.93], np.float32) * cwt
Image.fromarray((np.clip(albedo_c, 0, 1) * 255).astype(np.uint8)).save(os.path.join(WORK, "map_albedo_c.png"))
# el agua brilla; la tierra, el hielo y las nubes no
Image.fromarray((np.clip(np.maximum(landmask, clouds * 0.9), 0, 1) * 255).astype(np.uint8)).save(
    os.path.join(WORK, "map_land.png"))
# relieve en unidades del radio; el PNG de 16 bits es solo para inspección
height_r = (height / R).astype(np.float32)
hn = (height - height.min()) / (height.max() - height.min())
Image.fromarray((hn * 65535).astype(np.uint16)).save(os.path.join(WORK, "map_height.png"))
del E_glob, albedo, albedo_c

# --- render de la esfera ------------------------------------------------------------
log("render")
P_SHADE = dict(sun=[1.05, 0.96, 0.88], ambient=[0.012, 0.016, 0.035], term=[0.30, 0.10, 0.22], term_w=0.16,
               wrap=0.10, shine=160, spec=0.35, sheen=0.03, fres=0.35, fres_pow=3.5, sky=[0.30, 0.40, 0.70],
               haze=0.55, haze_pow=2.6, atmo=[0.30, 0.42, 0.85], atmo_rgb=[0.45, 0.55, 0.98], atmo_out=0.75,
               atmo_th=0.045, spec_col=[1.0, 0.9, 0.78])
BUMP = 2.1


def planet(size):
    return globe.render_sphere(os.path.join(WORK, "map_albedo_c.png"), size, VIEW["lon0"], VIEW["lat0"], VIEW["roll"],
                               LIGHT, P_SHADE, land_png=os.path.join(WORK, "map_land.png"), radius=0.86,
                               height=height_r, bump=BUMP, ss=2)


def starfield(w, h, seed=3):
    r = np.random.default_rng(seed)
    px = np.zeros((h, w, 3), np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    base = np.array([0.055, 0.047, 0.075])            # #0e0c13
    glow = np.exp(-(((xx - w * 0.15) / (w * 0.6)) ** 2 + ((yy - h * 0.2) / (h * 0.7)) ** 2))
    px[:] = base
    px += glow[..., None] * np.array([0.05, 0.05, 0.11])
    for _ in range(900):
        x, y = r.integers(0, w), r.integers(0, h)
        b = r.random() ** 3
        px[y, x] += np.array([0.75, 0.78, 0.95]) * (0.25 + 0.75 * b)
    return Image.fromarray((np.clip(px, 0, 1) * 255).astype(np.uint8))


W, H = 1600, 1000
canvas = starfield(W, H).convert("RGBA")
pl = planet(900)
canvas.alpha_composite(pl, (int(W * 0.56 - 450), int(H * 0.52 - 450)))
# la luna: la que levanta las mareas; cara iluminada desde el mismo sol
ms = 150
my, mx = np.mgrid[0:ms, 0:ms].astype(np.float32)
mxx, myy = (mx + 0.5 - ms / 2) / (ms / 2), -(my + 0.5 - ms / 2) / (ms / 2)
mr = np.hypot(mxx, myy)
mz = np.sqrt(np.clip(1 - mr ** 2, 0, 1))
Lv = np.array(LIGHT) / np.linalg.norm(LIGHT)
mn = np.clip(mxx * Lv[0] + myy * Lv[1] + mz * Lv[2], 0, 1)
mt = fbm2(mx / ms * 6, my / ms * 6, 3, 99) * 0.18 + 0.5
mcol = (np.array([0.70, 0.68, 0.74]) * (0.75 + 0.35 * mt[..., None])) * (mn[..., None] ** 0.8 + 0.02)
malpha = np.clip((1 - mr) * ms / 2, 0, 1)
moon = Image.fromarray(np.dstack([np.clip(mcol, 0, 1) * 255, malpha * 255]).astype(np.uint8), "RGBA")
canvas.alpha_composite(moon, (180, 170))
canvas.convert("RGB").save(os.path.join(IMG, "r6-orbita.png"))

# prueba de lectura a escala pequeña: el planeta a 160, 64 y 28 px
log("tira de escala")
strip = Image.new("RGBA", (420, 180), (14, 12, 19, 255))
big = planet(400)
x = 10
for s in (160, 64, 28):
    strip.alpha_composite(big.resize((s, s), Image.LANCZOS), (x, 90 - s // 2))
    x += s + 40
strip.convert("RGB").save(os.path.join(IMG, "r6-orbita-escala.png"))
log("hecho")
