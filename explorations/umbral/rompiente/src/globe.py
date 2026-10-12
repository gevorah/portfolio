"""Proyecta un mapa pintado sobre un cuerpo y lo ilumina.

No genera geografía: toda la información de color viene del mapa dibujado a
mano. Sirve para comprobar cómo se lee ese mapa desde la órbita (silueta,
manchas, terminador, brillo del agua). Admite una esfera o un cuerpo de dos
lóbulos (para La Cintura), trazado por campos de distancia. La esfera acepta
además un mapa de alturas que inclina las normales (relieve de la tierra y,
muy atenuado, del fondo visto a través del agua).
"""

import math

import numpy as np
from PIL import Image


def load(path, mode="RGB"):
    im = np.asarray(Image.open(path).convert(mode), dtype=np.float32) / 255.0
    return im


def srgb_to_lin(c):
    return np.power(np.clip(c, 0, 1), 2.2)


def lin_to_srgb(c):
    return np.power(np.clip(c, 0, 1), 1 / 2.2)


def bilinear(tex, u, v):
    """u, v en [0,1]; u envuelve."""
    h, w = tex.shape[:2]
    x = (u % 1.0) * w - 0.5
    y = np.clip(v, 0, 1) * h - 0.5
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    x1 = (x0 + 1) % w
    x0 = x0 % w
    y0c, y1c = np.clip(y0, 0, h - 1), np.clip(y0 + 1, 0, h - 1)
    if tex.ndim == 3:
        fx, fy = fx[..., None], fy[..., None]
    a = tex[y0c, x0] * (1 - fx) + tex[y0c, x1] * fx
    b = tex[y1c, x0] * (1 - fx) + tex[y1c, x1] * fx
    return a * (1 - fy) + b * fy


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def view_matrix(lon0, lat0, roll=0.0):
    """Matriz mundo→vista: el punto (lon0, lat0) queda mirando a cámara."""
    return rot_z(math.radians(roll)) @ rot_x(math.radians(lat0)) @ rot_y(-math.radians(lon0))


def world_lonlat(wn):
    lon = np.degrees(np.arctan2(wn[..., 0], wn[..., 2]))
    lat = np.degrees(np.arcsin(np.clip(wn[..., 1], -1, 1)))
    return lon, lat


def shade(n, albedo, water, light, p, n_geo=None):
    """n: normales en vista (N,3); albedo lineal (N,3); water (N,) 0..1.

    n_geo: normal geométrica (sin relieve). Si se da, n sólo modula la luz
    difusa (el relieve de la tierra y el fondo visto a través del agua) y la
    superficie del mar, que es lisa, usa n_geo para el brillo, el fresnel y la
    neblina del limbo.
    """
    if n_geo is None:
        n_geo = n
    L = np.array(light, dtype=np.float32)
    L = L / np.linalg.norm(L)
    V = np.array([0, 0, 1.0], dtype=np.float32)
    ndl = n @ L
    # terminador suave y algo «envolvente», como luz pintada
    wrap = p.get("wrap", 0.12)
    d = np.clip((ndl + wrap) / (1 + wrap), 0, 1)
    d = d * d * (3 - 2 * d) ** 0.0 if False else d
    lit = np.power(d, p.get("gamma_light", 0.85))
    col = albedo * (lit[:, None] * np.array(p.get("sun", [1.0, 0.97, 0.92]))
                    + np.array(p.get("ambient", [0.02, 0.022, 0.04])))
    # banda del terminador teñida: es luz de la atmósfera, va con la esfera y no con el relieve
    ndl_g = n_geo @ L
    tb = np.exp(-((ndl_g + 0.02) / p.get("term_w", 0.14)) ** 2)
    col += albedo * tb[:, None] * np.array(p.get("term", [0.22, 0.08, 0.16]))
    # agua: brillo especular + reflejo de cielo al rasante (fresnel)
    ndv = np.clip(n_geo[:, 2], 0, 1)
    H = (L + V) / np.linalg.norm(L + V)
    ndh = np.clip(n_geo @ H, 0, 1)
    spec = np.power(ndh, p.get("shine", 90)) * p.get("spec", 0.9) + np.power(ndh, 8) * p.get("sheen", 0.05)
    fres = np.power(1 - ndv, p.get("fres_pow", 4)) * p.get("fres", 0.25)
    sky = np.array(p.get("sky", [0.3, 0.4, 0.6]))
    litf = np.clip(ndl_g * 3 + 0.3, 0, 1)
    col += (water * spec * np.clip(ndl_g * 4, 0, 1))[:, None] * np.array(p.get("spec_col", [1, 0.98, 0.94]))
    col = col * (1 - (water * fres * litf)[:, None]) + (water * fres * litf)[:, None] * sky
    # neblina en el limbo
    haze = np.power(1 - ndv, p.get("haze_pow", 3.0)) * p.get("haze", 0.5) * np.clip(ndl_g + 0.25, 0, 1)
    col += haze[:, None] * np.array(p.get("atmo", [0.35, 0.6, 0.8]))
    return col


def atmosphere_ring(xx, yy, r_px, light, p):
    """Halo fuera del disco (en coordenadas de pantalla normalizadas)."""
    rr = np.sqrt(xx ** 2 + yy ** 2)
    out = rr > 1
    t = np.clip((rr - 1) / p.get("atmo_th", 0.05), 0, 50)
    L = np.array(light[:2])
    L = L / (np.linalg.norm(L) + 1e-6)
    facing = np.clip((xx * L[0] + yy * L[1]) / (rr + 1e-6) * 0.7 + 0.45, 0, 1)
    a = np.exp(-t * 1.6) * facing * p.get("atmo_out", 0.7) * out
    return a


def height_slopes(height):
    """Pendientes de un mapa de alturas equirrectangular (alturas en unidades del radio).

    Devuelve (este, norte): derivada de la altura por radián de arco recorrido
    sobre la superficie, lista para inclinar la normal.
    """
    h = np.asarray(height, np.float32)
    H, W = h.shape
    lat = np.radians(90 - (np.arange(H) + 0.5) / H * 180)
    d_lon = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * (W / (4 * np.pi))
    d_lat = -np.gradient(h, axis=0) * (H / np.pi)
    east = d_lon / np.maximum(np.cos(lat), 0.05)[:, None]
    return east.astype(np.float32), d_lat.astype(np.float32)


def render_sphere(albedo_png, size, lon0, lat0, roll, light, p, land_png=None, radius=0.82,
                  height=None, bump=0.0, ss=1):
    """Esfera iluminada con el mapa dado.

    height: mapa de alturas (array equirrectangular, en unidades del radio) o
    ruta a un PNG de 16 bits normalizado (entonces p["height_range"] = (min, max)).
    bump: exageración del relieve al inclinar las normales (0 = esfera lisa).
    ss: supermuestreo por lado (el disco se calcula a size·ss y se promedia en lineal).
    """
    tex = srgb_to_lin(load(albedo_png))
    land = load(land_png, "L") if land_png else None
    slopes = None
    if height is not None and bump:
        if isinstance(height, str):
            lo, hi = p.get("height_range", (0.0, 1.0))
            height = lo + (hi - lo) * np.asarray(Image.open(height), np.float32) / 65535.0
        slopes = height_slopes(height)
    M = view_matrix(lon0, lat0, roll)
    n_px = size * ss
    ys, xs = np.mgrid[0:n_px, 0:n_px].astype(np.float32)
    xx = (xs + 0.5 - n_px / 2) / (n_px / 2 * radius)
    yy = -(ys + 0.5 - n_px / 2) / (n_px / 2 * radius)
    r2 = xx ** 2 + yy ** 2
    inside = r2 <= 1
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    n = np.stack([xx, yy, z], -1)[inside]
    wn = n @ M  # vista → mundo (M ortonormal: inversa = traspuesta)
    lon, lat = world_lonlat(wn)
    u = (lon + 180) / 360
    v = (90 - lat) / 180
    alb = bilinear(tex, u, v)
    water = 1 - bilinear(land, u, v) if land is not None else np.ones(len(n), np.float32)
    nb = n
    if slopes is not None:
        # relieve: la normal se inclina contra la pendiente, en el marco este/norte local
        se, sn = bilinear(slopes[0], u, v), bilinear(slopes[1], u, v)
        lo_r, la_r = np.radians(lon), np.radians(lat)
        east = np.stack([np.cos(lo_r), np.zeros_like(lo_r), -np.sin(lo_r)], -1)
        north = np.stack([-np.sin(la_r) * np.sin(lo_r), np.cos(la_r), -np.sin(la_r) * np.cos(lo_r)], -1)
        wb = wn - bump * (se[:, None] * east + sn[:, None] * north)
        wb /= np.linalg.norm(wb, axis=-1, keepdims=True)
        nb = wb @ M.T
    col = shade(nb, alb, water, light, p, n_geo=n)
    img = np.zeros((n_px, n_px, 4), np.float32)
    img[inside, :3] = col
    # antialias del borde
    edge = np.clip((1 - np.sqrt(r2)) * n_px / 2 * radius, 0, 1)
    img[..., 3] = np.where(inside, edge, 0)
    a = atmosphere_ring(xx, yy, n_px / 2 * radius, light, p)
    atmo = srgb_to_lin(np.array(p.get("atmo_rgb", [0.5, 0.75, 0.95])))
    img[..., :3] = img[..., :3] * img[..., 3:4] + (a[..., None] * atmo) * (1 - img[..., 3:4])
    img[..., 3] = np.clip(img[..., 3] + a * (1 - img[..., 3]), 0, 1)
    if ss > 1:
        # promedio en lineal y premultiplicado: color y alfa ya van multiplicados
        img = img.reshape(size, ss, size, ss, 4).mean(axis=(1, 3))
    return finish(img)


def finish(img):
    rgb = lin_to_srgb(img[..., :3] / np.maximum(img[..., 3:4], 1e-4))
    out = np.concatenate([rgb, img[..., 3:4]], -1)
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- dos lóbulos
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


class Peanut:
    """Binario de contacto: dos esferas unidas por un cuello suave."""

    def __init__(self, ca=(-0.62, 0, 0), ra=1.0, cb=(0.78, 0, 0), rb=0.74, k=0.32):
        self.ca, self.ra = np.array(ca, np.float32), ra
        self.cb, self.rb = np.array(cb, np.float32), rb
        self.k = k

    def sd(self, p):
        da = np.linalg.norm(p - self.ca, axis=-1) - self.ra
        db = np.linalg.norm(p - self.cb, axis=-1) - self.rb
        return smin(da, db, self.k)

    def normal(self, p, e=1e-3):
        ex = np.array([e, 0, 0], np.float32)
        ey = np.array([0, e, 0], np.float32)
        ez = np.array([0, 0, e], np.float32)
        n = np.stack([self.sd(p + ex) - self.sd(p - ex), self.sd(p + ey) - self.sd(p - ey),
                      self.sd(p + ez) - self.sd(p - ez)], -1)
        return n / np.linalg.norm(n, axis=-1, keepdims=True)


def disc_uv(d, axis, up, theta_max):
    """Dirección local → coordenadas del mapa polar (centro = cima)."""
    axis = axis / np.linalg.norm(axis)
    up = up - axis * (up @ axis)
    up = up / np.linalg.norm(up)
    side = np.cross(axis, up)
    th = np.degrees(np.arccos(np.clip(d @ axis, -1, 1)))
    ph = np.arctan2(d @ side, d @ up)
    t = np.clip(th / theta_max, 0, 0.995)
    return 0.5 + 0.5 * t * np.cos(ph), 0.5 + 0.5 * t * np.sin(ph), th


def render_peanut(body, maps, size, view_rot, light, p, scale=1.0, center=(0.0, 0.0), extent=2.2):
    """maps: dict con 'a','b' (albedo) y 'a_land','b_land'. view_rot: mundo→vista."""
    ta, tb = srgb_to_lin(load(maps["a"])), srgb_to_lin(load(maps["b"]))
    la, lb = load(maps["a_land"], "L"), load(maps["b_land"], "L")
    Rm = np.array(view_rot, np.float32)
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    sx = (xs + 0.5 - size / 2) / (size / 2) * extent / scale + center[0]
    sy = -(ys + 0.5 - size / 2) / (size / 2) * extent / scale + center[1]
    o_view = np.stack([sx, sy, np.full_like(sx, 4.0)], -1).reshape(-1, 3)
    dvec_view = np.array([0, 0, -1.0], np.float32)
    o = o_view @ Rm  # vista → mundo
    dvec = dvec_view @ Rm
    t = np.zeros(len(o), np.float32)
    hit = np.zeros(len(o), bool)
    alive = np.ones(len(o), bool)
    for _ in range(140):
        idx = np.where(alive)[0]
        if len(idx) == 0:
            break
        pp = o[idx] + dvec * t[idx, None]
        d = body.sd(pp)
        t[idx] += d * 0.9
        h = d < 1e-3
        hit[idx[h]] = True
        alive[idx[h]] = False
        alive[idx[t[idx] > 8]] = False
    # cobertura suave para el antialias: distancia mínima a lo largo del rayo
    img = np.zeros((size * size, 4), np.float32)
    hi = np.where(hit)[0]
    pw = o[hi] + dvec * t[hi, None]
    nw = body.normal(pw)
    # mapa por lóbulo y mezcla a través del cuello
    xmid = (body.ca[0] * body.rb + body.cb[0] * body.ra) / (body.ra + body.rb) + 0.07
    wb = np.clip((pw[:, 0] - xmid) / 0.09 * 0.5 + 0.5, 0, 1)
    up = np.array([0, 1.0, 0], np.float32)
    da = (pw - body.ca)
    da /= np.linalg.norm(da, axis=-1, keepdims=True)
    db = (pw - body.cb)
    db /= np.linalg.norm(db, axis=-1, keepdims=True)
    ua, va, tha = disc_uv(da, np.array([-1.0, 0, 0]), up, p.get("thmax_a", 155))
    ub, vb, thb = disc_uv(db, np.array([1.0, 0, 0]), up, p.get("thmax_b", 140))
    ca = bilinear(ta, ua, va)
    cb = bilinear(tb, ub, vb)
    wa_land = bilinear(la, ua, va)
    wb_land = bilinear(lb, ub, vb)
    # encuentro de aguas: dedos de agua lechosa entrando en la oscura
    ang = np.arctan2(pw[:, 2], pw[:, 1])
    wb = np.clip(wb + 0.35 * np.sin(ang * 7 + pw[:, 0] * 9) * wb * (1 - wb) * 4, 0, 1)
    alb = ca * (1 - wb[:, None]) + cb * wb[:, None]
    land = wa_land * (1 - wb) + wb_land * wb
    nv = nw @ Rm.T  # normales en vista
    # sombra proyectada (un lóbulo sobre el otro)
    Lw = np.array(light, np.float32) @ Rm
    Lw /= np.linalg.norm(Lw)
    sh = np.ones(len(pw), np.float32)
    ts = np.full(len(pw), 0.02, np.float32)
    res = np.ones(len(pw), np.float32)
    for _ in range(60):
        d = body.sd(pw + nw * 0.003 + Lw * ts[:, None])
        res = np.minimum(res, 10 * d / ts)
        ts += np.clip(d, 0.01, 0.2)
    sh = np.clip(res, 0, 1)
    col = shade(nv, alb, 1 - land, light, p)
    amb = np.array(p.get("ambient", [0.02, 0.02, 0.04]))
    col = col * (0.15 + 0.85 * sh[:, None]) + alb * amb * (1 - sh[:, None])
    img[hi, :3] = col
    img[hi, 3] = 1
    img = img.reshape(size, size, 4)
    # antialias barato: suaviza el alfa
    a = img[..., 3]
    from PIL import ImageFilter
    am = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7)), np.float32) / 255
    img[..., 3] = np.minimum(am, 1) * (a > 0) + am * (a == 0) * 0.0 + (a == 0) * 0
    img[..., 3] = np.where(a > 0, np.clip(am * 1.3, 0, 1), 0)
    # halo atmosférico a partir de la silueta
    halo = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(size * 0.012)), np.float32) / 255
    halo = np.clip(halo - a, 0, 1) * p.get("atmo_out", 0.6)
    L2 = np.array(light[:2], np.float32)
    gy, gx = np.gradient(halo)
    face = np.clip(-(gx * L2[0] - gy * L2[1]) / (np.sqrt(gx ** 2 + gy ** 2) + 1e-6) * 0.6 + 0.5, 0, 1)
    halo = halo * face
    atmo = srgb_to_lin(np.array(p.get("atmo_rgb", [0.6, 0.8, 0.9])))
    img[..., :3] = img[..., :3] * img[..., 3:4] + halo[..., None] * atmo * (1 - img[..., 3:4])
    img[..., 3] = np.clip(img[..., 3] + halo * (1 - img[..., 3]), 0, 1)
    return finish(img)
