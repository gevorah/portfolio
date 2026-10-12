"""Estudio I · Umbral desde la órbita.

El mapa sale de la misma geografía que la escena de La Rompiente: en un mundo
pequeño (radio ≈ 2,6 km) la isla principal, la isleta y el arco del
archipiélago son legibles desde el espacio. La firma a escala planetaria es la
dorsal submarina: una banda de bajíos turquesa que se curva como la propia
ola, con las islas ensartadas en ella.

Salida: work/map_albedo.png, work/map_land.png, img/i-orbita.png,
img/i-orbita-escala.png
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import globe

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
IMG = os.path.join(ROOT, "img")
os.makedirs(WORK, exist_ok=True)
os.makedirs(IMG, exist_ok=True)

MW, MH = 2048, 1024
R = 2600.0                      # radio del planeta, metros
LAT0, LON0 = 18.0, 0.0          # la isla principal

rng = np.random.default_rng(7)


def value_noise(shape, cells, seed):
    """Ruido de valor periódico en longitud."""
    r = np.random.default_rng(seed)
    gy, gx = cells
    g = r.random((gy + 1, gx))
    h, w = shape
    y = np.linspace(0, gy, h, endpoint=False)
    x = np.linspace(0, gx, w, endpoint=False)
    y0 = np.floor(y).astype(int)
    x0 = np.floor(x).astype(int)
    fy = (y - y0)[:, None]
    fx = (x - x0)[None, :]
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    x1 = (x0 + 1) % gx
    a = g[y0][:, x0] * (1 - fx) + g[y0][:, x1] * fx
    b = g[np.minimum(y0 + 1, gy)][:, x0] * (1 - fx) + g[np.minimum(y0 + 1, gy)][:, x1] * fx
    return a * (1 - fy) + b * fy


def fbm(shape, base, octaves, seed):
    s, a, tot = 0, 0.5, 0
    for i in range(octaves):
        s = s + a * value_noise(shape, (base[0] * 2 ** i, base[1] * 2 ** i), seed + i)
        tot += a
        a *= 0.5
    return s / tot


# --- coordenadas del mapa ---------------------------------------------------
lon = (np.arange(MW) + 0.5) / MW * 360 - 180
lat = 90 - (np.arange(MH) + 0.5) / MH * 180
LON, LAT = np.meshgrid(lon, lat)


def plan_to_lonlat(x, z):
    """Planta local de la escena (x este, z norte, metros) → lon/lat."""
    return LON0 + math.degrees(x / (R * math.cos(math.radians(LAT0)))), LAT0 + math.degrees(z / R)


# coordenadas locales (aprox.) de cada píxel del mapa, en metros
X = np.radians(((LON - LON0 + 180) % 360) - 180) * R * np.cos(np.radians(LAT0))
Z = np.radians(LAT - LAT0) * R


def segd(px, pz, a, b):
    ax, az = a
    bx, bz = b
    vx, vz = bx - ax, bz - az
    h = np.clip(((px - ax) * vx + (pz - az) * vz) / (vx * vx + vz * vz), 0, 1)
    return np.hypot(px - ax - vx * h, pz - az - vz * h)


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


N1 = fbm((MH, MW), (8, 16), 4, 11)
N2 = fbm((MH, MW), (32, 64), 3, 23)
N3 = fbm((MH, MW), (4, 8), 3, 31)
NF = fbm((MH, MW), (256, 512), 2, 61)

# --- la isla (misma planta que la escena) ----------------------------------
A0, A1, A2, A3 = (300, 700), (110, 470), (55, 330), (25, 240)
arm = np.minimum(np.minimum(segd(X, Z, A0, A1) - 64, segd(X, Z, A1, A2) - 62), segd(X, Z, A2, A3) - 50)
# cuerpo lobulado: el lóbulo de la escena (600, 820) y otros que abren bahías
LOBES = [(600, 820, 300, 240), (900, 1100, 260, 200), (1050, 700, 180, 150), (760, 1380, 170, 130), (420, 1080, 150, 110)]
body = np.full_like(X, 1e9)
for (bx, bz, rx, rz) in LOBES:
    body = smin(body, (np.hypot((X - bx) / rx, (Z - bz) / rz) - 1) * min(rx, rz), 220)
bay = np.hypot(X - 820, (Z - 560) * 1.3) - 120 + 90 * (NF - 0.5) + 60 * (N2 - 0.5)                     # bahía al este del brazo
island = smin(arm, body, 140) - 25 + 70 * (N2 - 0.5) + 50 * (N1 - 0.5) + 45 * (NF - 0.5)
island = np.maximum(island, -bay)
isleta = np.hypot(X - 160, (Z - 840) * 1.4) - 60
# archipiélago: el arco de islas sobre la dorsal (mismas posiciones que la escena, prolongadas)
ARC = [(-120, 1150, 130, 90), (-420, 1500, 170, 110), (-820, 1700, 150, 90), (-1250, 1750, 220, 120),
       (-1700, 1600, 160, 90), (-2100, 1350, 120, 70), (-2420, 980, 90, 60), (-2600, 560, 70, 50)]
NM = fbm((MH, MW), (64, 128), 3, 41)
NH = fbm((MH, MW), (160, 320), 2, 53)
arch = np.full_like(X, 1e5)
r2 = np.random.default_rng(5)
for i, (ax, az, rx, rz) in enumerate(ARC):
    sc = [1.0, 1.3, 0.8, 1.15, 0.6, 0.75, 0.45, 0.35][i]
    a = r2.uniform(0, math.pi)
    dx, dz = X - ax, Z - az
    u = (dx * math.cos(a) + dz * math.sin(a)) / (rx * sc * 1.3)
    v = (-dx * math.sin(a) + dz * math.cos(a)) / (rz * sc * 0.8)
    arch = np.minimum(arch, (np.hypot(u, v) - 1.0) * min(rx, rz) * sc)
    # islotes satélite
    for k in range(r2.integers(1, 4)):
        ox, oz = r2.normal(0, rx * 1.2), r2.normal(0, rz * 1.2)
        rr = r2.uniform(14, 34) * sc
        arch = np.minimum(arch, np.hypot(X - ax - ox, Z - az - oz) - rr)
arch = arch + 60 * (NM - 0.5) + 30 * (NH - 0.5)

land = np.minimum(np.minimum(island, isleta), arch)

# --- la dorsal: una banda de bajíos que se curva como la ola -----------------
# polilínea en planta, de la isla principal hacia el oeste y de vuelta al sur
RIDGE = [(60, 520), (-40, 860), (-120, 1150), (-420, 1500), (-820, 1700),
         (-1250, 1750), (-1700, 1600), (-2100, 1350), (-2420, 980), (-2600, 560), (-2620, 120), (-2450, -260)]
rd = np.full_like(X, 1e9)
for a, b in zip(RIDGE[:-1], RIDGE[1:]):
    rd = np.minimum(rd, segd(X, Z, a, b))
# la anchura crece hacia la cabeza (la isla) y se afina en la cola
along = np.clip((Z + 300) / 2200, 0, 1)
width = 340 - 160 * np.clip((-X - 1500) / 1500, 0, 1)
shelf = rd - width * (0.25 + 1.3 * NM) - 140 * (N2 - 0.5) - 40 * (NH - 0.5)
# la plataforma insular rodea la isla principal
shelf = np.minimum(shelf, island - 160 - 160 * NM)
shelf = np.minimum(shelf, arch - 120 - 140 * NM)
# otros bancos lejanos: el resto del planeta no está vacío, pero es océano
for (bx, bz, br) in [(4200, -1800, 380), (-5200, -900, 260), (6800, 2400, 300), (-8200, 3600, 220)]:
    shelf = np.minimum(shelf, np.hypot(X - bx, Z - bz) - br * (0.5 + NM))
    land = np.minimum(land, np.hypot(X - bx, Z - bz) - br * 0.12 * (0.6 + NH))

# --- color -------------------------------------------------------------------
def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


deep = hexc("0b2c38")
ocean = hexc("13495a")
petrol = hexc("1f5866")
shallow = hexc("3f9e98")
shoal = hexc("79c9b8")
sand = hexc("d2c39f")
slate = hexc("4d596a")
basalt = hexc("2e3747")
green = hexc("55734a")
green2 = hexc("86a463")

col = np.zeros((MH, MW, 3))
# océano profundo con grandes cuencas
t = np.clip(N3 * 1.4 - 0.2, 0, 1)[..., None]
col[:] = deep * (1 - t) + ocean * t
# el talud: el océano se aclara cerca de la dorsal
slope = np.clip(1 - shelf / 700, 0, 1)[..., None]
col = col * (1 - 0.6 * slope) + petrol * 0.6 * slope
# bajíos: la topografía se lee bajo el agua
sh = np.clip(1 - (shelf + 40) / 120, 0, 1)[..., None]
col = col * (1 - sh) + (shallow * 0.85 + petrol * 0.15) * sh
very = np.clip(1 - (np.minimum(land, shelf + 160) + 60) / 90, 0, 1)[..., None]
col = col * (1 - very * 0.8) + shoal * very * 0.8
# rasa / franja intermareal: anillo claro alrededor de cada costa
ring = np.clip(1 - np.abs(land + 35) / 45, 0, 1)[..., None]
col = col * (1 - ring * 0.7) + (sand * 0.55 + shoal * 0.45) * ring * 0.7
# tierra
lm = np.clip(-land / 12, 0, 1)[..., None]
rock = slate * (0.7 + 0.5 * N2[..., None]) * 0.7 + basalt * 0.3
inland = np.clip(-land / 120, 0, 1)
veg = np.clip((inland * 1.3 + (N2 - 0.5) * 1.2 - 0.25), 0, 1)[..., None]
g = green * (1 - N1[..., None]) + green2 * N1[..., None]
landc = rock * (1 - veg * 0.75) + g * veg * 0.75
# relieve: sombreado de colinas desde una altura derivada de la distancia a la costa
hgt = np.clip(-land, 0, 400) ** 0.8 * (0.6 + 0.8 * N2) + 60 * NM * np.clip(-land / 40, 0, 1)
gy, gx = np.gradient(hgt)
hs = np.clip(0.85 + (-gx * 0.7 + gy * 0.7) * 0.12, 0.55, 1.2)[..., None]
landc = landc * hs
col = col * (1 - lm) + landc * lm
# La Rompiente: la cara oeste del brazo, roca clara expuesta
rom = np.clip(1 - np.abs(arm + 6) / 14, 0, 1) * ((X - np.interp(Z, [240, 330, 470, 700], [25, 55, 110, 300])) < -20) \
    * np.clip((Z - 230) / 80, 0, 1) * np.clip((620 - Z) / 80, 0, 1)
col = col * (1 - rom[..., None] * 0.7) + hexc("b9c0c8") * rom[..., None] * 0.7

# los polos del mapa se funden en un océano uniforme (evita el pellizco de la proyección)
pf = np.clip((np.abs(LAT) - 62) / 14, 0, 1)[..., None]
col = col * (1 - pf) + (deep * 0.6 + ocean * 0.4) * pf
# casquete: hielo de mar fino en el polo sur, sin protagonismo
pole = np.clip((-LAT - 76 + 10 * (N1 - 0.5) * 2) / 10, 0, 1)[..., None] * 0.8
col = col * (1 - pole * 0.85) + hexc("c9d6df") * pole * 0.85

Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(os.path.join(WORK, "map_albedo.png"))
landmask = np.clip(-land / 12, 0, 1) + pole[..., 0] * 0.8
Image.fromarray((np.clip(landmask, 0, 1) * 255).astype(np.uint8)).save(os.path.join(WORK, "map_land.png"))

# nubes: bandas peinadas y pocas, que no tapan la geografía
cl = fbm((MH, MW), (10, 14), 5, 77)
streak = fbm((MH, MW), (48, 8), 4, 91)
clouds = np.clip((cl * 0.6 + streak * 0.55 - 0.66) * 4.0, 0, 1) ** 1.5
clouds *= np.clip((70 - np.abs(LAT)) / 15, 0, 1) * 0.8
clouds *= np.clip(1 - np.exp(-((LAT - 48) / 12) ** 2) * 0 - 0.0, 0, 1)
cmap = np.zeros((MH, MW, 3))
cmap[:] = 1
Image.fromarray((clouds * 255).astype(np.uint8)).save(os.path.join(WORK, "map_clouds.png"))

# --- render de la esfera -----------------------------------------------------
alb = np.asarray(Image.open(os.path.join(WORK, "map_albedo.png")), np.float32) / 255
cw = clouds[..., None] * 0.85
alb_c = alb * (1 - cw) + np.array([0.88, 0.89, 0.94]) * cw
Image.fromarray((np.clip(alb_c, 0, 1) * 255).astype(np.uint8)).save(os.path.join(WORK, "map_albedo_c.png"))

P = dict(sun=[1.05, 0.96, 0.88], ambient=[0.012, 0.016, 0.035], term=[0.30, 0.10, 0.22], term_w=0.16,
         wrap=0.10, shine=160, spec=0.35, sheen=0.03, fres=0.35, fres_pow=3.5, sky=[0.30, 0.40, 0.70],
         haze=0.55, haze_pow=2.6, atmo=[0.30, 0.42, 0.85], atmo_rgb=[0.45, 0.55, 0.98], atmo_out=0.75,
         atmo_th=0.045, spec_col=[1.0, 0.9, 0.78])
LIGHT = [0.42, 0.40, 0.81]


def planet(size, lon0=-6, lat0=26, roll=-6):
    return globe.render_sphere(os.path.join(WORK, "map_albedo_c.png"), size, lon0, lat0, roll, LIGHT, P,
                               land_png=os.path.join(WORK, "map_land.png"), radius=0.86)


def starfield(w, h, seed=3):
    r = np.random.default_rng(seed)
    im = Image.new("RGB", (w, h))
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
L = np.array(LIGHT) / np.linalg.norm(LIGHT)
mn = np.clip(mxx * L[0] + myy * L[1] + mz * L[2], 0, 1)
mt = fbm((ms, ms), (6, 6), 3, 99)
mcol = (np.array([0.70, 0.68, 0.74]) * (0.75 + 0.35 * mt[..., None])) * (mn[..., None] ** 0.8 + 0.02)
malpha = np.clip((1 - mr) * ms / 2, 0, 1)
moon = Image.fromarray(np.dstack([np.clip(mcol, 0, 1) * 255, malpha * 255]).astype(np.uint8), "RGBA")
canvas.alpha_composite(moon, (180, 170))
canvas.convert("RGB").save(os.path.join(IMG, "i-orbita.png"))

# prueba de lectura a escala pequeña: el planeta a 160, 64 y 28 px
strip = Image.new("RGBA", (420, 180), (14, 12, 19, 255))
big = planet(400)
x = 10
for s in (160, 64, 28):
    strip.alpha_composite(big.resize((s, s), Image.LANCZOS), (x, 90 - s // 2))
    x += s + 40
strip.convert("RGB").save(os.path.join(IMG, "i-orbita-escala.png"))
