"""Tratamiento B — «Instrumento».

Umbral como un instrumento de precisión a escala: un planeta facetado,
sombreado plano y posterizado (como las ilustraciones de gevorah), atravesado
por un gnomon de reloj de sol, con la luna montada sobre el raíl de un orrery.

La geometría es un modelo mínimo hecho a mano (meseta, gnomon, observatorio,
henge, mástil). Este script sólo la proyecta para que los tres estados
compartan exactamente el mismo objeto desde cámaras distintas, y dibuja los
contornos únicamente donde cambia el tono: manchas planas, no malla.

Salida: frames/b{1,2,3}.svg y frames/b{1,2,3}.json (anclas para tipografía
y avatar en la composición HTML).
"""

import json
import math
import random
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "frames"
W, H = 1600, 1000
INK = "#0e0c13"

# ---------------------------------------------------------------- paletas
# Rampas posterizadas de luz a sombra. Sin degradados en los sólidos.
RAMP = {
    "rock": ["#b8a7ec", "#8b72d6", "#5e48a8", "#3b2c78", "#231a4b", "#15112c"],
    "strata": ["#a3a9f2", "#7280dc", "#4c55ad", "#30367c", "#1d2150", "#121430"],
    "mesa": ["#c9d0ff", "#9aa5f2", "#6d76c9", "#4a4f98", "#2e3166", "#1a1c3c"],
    "bone": ["#f1edf9", "#cfc8e6", "#9c93c2", "#665e8e", "#3d375c", "#231f38"],
    "dome": ["#a9c0ff", "#7d98f2", "#5670c8", "#3a4890", "#252d5e", "#161a38"],
    "moon": ["#e4e6f3", "#b5bbdb", "#8189b4", "#545a88", "#32365a", "#1b1d35"],
}
# En la umbra todo pasa a esta rampa y las aristas se encienden.
NIGHT = ["#2b2061", "#231a52", "#1c1544", "#161137", "#110d2b", "#0e0b22"]
NIGHT_MOON = ["#2a2552", "#221e46", "#1b183a", "#15132f", "#100e25", "#0c0a1c"]
GLOW = "#a58cff"
GLOW_HI = "#e7defe"


def norm(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


# ------------------------------------------------------------- geometría
def icosphere(sub):
    t = (1 + 5 ** 0.5) / 2
    verts = [norm(v) for v in [
        (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
        (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
        (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
             (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
             (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
             (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(sub):
        cache, nf = {}, []

        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                verts.append(norm((verts[a] + verts[b]) / 2))
                cache[k] = len(verts) - 1
            return cache[k]

        for a, b, c in faces:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = nf
    return [np.array(v) for v in verts], faces


class Mesh:
    """Polígonos de un mismo objeto. `center` orienta las normales hacia fuera."""

    def __init__(self, name, center=None):
        self.name = name
        self.center = None if center is None else np.array(center, float)
        self.polys, self.mats, self.tags = [], [], []

    def add(self, pts, mat, tag=None):
        self.polys.append(np.array(pts, float))
        self.mats.append(mat)
        self.tags.append(tag)


MESA_Y = 0.6
YAW, PITCH = math.radians(-30), math.radians(26)
# segmento del observatorio que mira a la cámara (rendija y puerta)
_fwd = np.array([[math.cos(YAW), 0, -math.sin(YAW)], [0, 1, 0], [math.sin(YAW), 0, math.cos(YAW)]]) @ np.array([0, 0, 1.0])
FACE_K = int(round(math.atan2(_fwd[2], _fwd[0]) / (2 * math.pi / 10))) % 10
AXIS = norm([0.25, 1.0, 0.15])  # eje de los estratos, ligeramente inclinado


def planet_mesh(rng):
    verts, faces = icosphere(2)
    out = []
    for v in verts:
        r = 1 + rng.uniform(-0.03, 0.03)
        p = v * r
        if p[1] > MESA_Y:  # la cima se aplana como un altar
            p = np.array([p[0] * 0.97, MESA_Y + (p[1] - MESA_Y) * 0.04, p[2] * 0.97])
        out.append(p)
    m = Mesh("planet", [0, 0, 0])
    for f in faces:
        pts = [out[i] for i in f]
        c = np.mean(pts, 0)
        if min(p[1] for p in pts) > MESA_Y - 0.01:
            m.add(pts, "mesa")
        else:
            # estratos: bandas inclinadas, como capas sedimentarias talladas
            h = c @ AXIS + 0.05 * math.sin(7 * c[0] + 3 * c[2])
            band = int(math.floor((h + 1.2) / 0.27))
            m.add(pts, "strata" if band % 2 else "rock")
    return m


def box(name, center, ax, ay, az, mat, segs=1, tag=None):
    c = np.array(center, float)
    ax, ay, az = (np.array(a, float) for a in (ax, ay, az))
    m = Mesh(name, c)

    def P(sx, sy, sz):
        return c + sx * ax + sy * ay + sz * az

    for i in range(segs):
        y0, y1 = -1 + 2 * i / segs, -1 + 2 * (i + 1) / segs
        m.add([P(1, y0, 1), P(1, y1, 1), P(-1, y1, 1), P(-1, y0, 1)], mat, tag)
        m.add([P(-1, y0, -1), P(-1, y1, -1), P(1, y1, -1), P(1, y0, -1)], mat, tag)
        m.add([P(1, y0, -1), P(1, y1, -1), P(1, y1, 1), P(1, y0, 1)], mat, tag)
        m.add([P(-1, y0, 1), P(-1, y1, 1), P(-1, y1, -1), P(-1, y0, -1)], mat, tag)
    m.add([P(1, 1, 1), P(1, 1, -1), P(-1, 1, -1), P(-1, 1, 1)], mat, tag)
    m.add([P(-1, -1, 1), P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1)], mat, tag)
    return m


def observatory(base, radius):
    """Tambor octogonal + cúpula facetada con rendija."""
    c = np.array(base, float)
    m = Mesh("obs", c + [0, radius * 0.6, 0])
    n, hgt = 10, radius * 0.55
    ring = [c + np.array([radius * math.cos(2 * math.pi * k / n), 0,
                          radius * math.sin(2 * math.pi * k / n)]) for k in range(n)]
    up = np.array([0, hgt, 0])
    for k in range(n):
        a, b = ring[k], ring[(k + 1) % n]
        m.add([a, b, b + up, a + up], "bone", "door" if k == (FACE_K + 2) % n else None)
    rings = 3
    pts = []
    top = c + up
    for j in range(rings + 1):
        phi = (math.pi / 2) * j / rings
        y, rr = radius * math.sin(phi), radius * math.cos(phi)
        pts.append([top + np.array([rr * math.cos(2 * math.pi * k / n), y,
                                    rr * math.sin(2 * math.pi * k / n)]) for k in range(n)])
    for j in range(rings):
        for k in range(n):
            a, b = pts[j][k], pts[j][(k + 1) % n]
            cc, d = pts[j + 1][(k + 1) % n], pts[j + 1][k]
            tag = "slit" if k in (FACE_K, (FACE_K + 1) % n) and j < rings - 1 else None
            if j == rings - 1:
                m.add([a, b, cc], "dome", tag)
            else:
                m.add([a, b, cc, d], "dome", tag)
    return m


def moon_mesh(center, radius, rng):
    verts, faces = icosphere(1)
    m = Mesh("moon", center)
    out = [center + v * radius * (1 + rng.uniform(-0.07, 0.07)) for v in verts]
    for f in faces:
        m.add([out[i] for i in f], "moon")
    return m


def shard(center, size, rng):
    verts, faces = icosphere(0)
    m = Mesh("shard", center)
    out = [center + v * size * np.array([1.4, 0.7, 1]) * (1 + rng.uniform(-0.25, 0.25)) for v in verts]
    for f in faces:
        m.add([out[i] for i in f], "rock")
    return m


# ----------------------------------------------------------------- mundo
SUN = norm([1.0, 0.62, -0.42])


def build_world(moon_theta, rail_tilt=1.0):
    rng = random.Random(7)
    meshes = [planet_mesh(rng)]

    obs = np.array([0.02, MESA_Y, 0.12])
    meshes.append(observatory(obs, 0.13))

    # henge: siete piedras alrededor del observatorio
    stones = []
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.35
        p = obs + np.array([0.37 * math.cos(a), 0, 0.37 * math.sin(a)])
        h = 0.05 + 0.022 * ((k * 5) % 3)
        t = np.array([-math.sin(a), 0, math.cos(a)])
        r = np.array([math.cos(a), 0, math.sin(a)])
        meshes.append(box(f"stone{k}", p + [0, h, 0], t * 0.03, [0, h, 0], r * 0.016, "bone"))
        stones.append(p + [0, 0.004, 0])

    # mástil con la única lámpara cálida
    mast_base = obs + np.array([0.2, 0, -0.16])
    mast_h = 0.32
    meshes.append(box("mast", mast_base + [0, mast_h / 2, 0], [0.008, 0, 0], [0, mast_h / 2, 0],
                      [0, 0, 0.008], "bone"))
    lamp = mast_base + [0, mast_h + 0.012, 0]

    # gnomon: una vela triangular de reloj de sol plantada en la meseta
    along = norm([0.97, 0, -0.26])
    A0 = np.array([-0.52, MESA_Y, -0.2])
    B0 = A0 + along * 0.9
    C0 = A0 + np.array([0, 1.08, 0]) + along * 0.06
    thick = norm(np.cross(along, [0, 1, 0])) * 0.035
    g = Mesh("gnomon", (A0 + B0 + C0) / 3)
    tri_f = [A0 + thick, B0 + thick, C0 + thick]
    tri_b = [A0 - thick, B0 - thick, C0 - thick]
    g.add(tri_f, "bone", "gnomon")
    g.add(tri_b[::-1], "bone", "gnomon")
    for i in range(3):
        j = (i + 1) % 3
        g.add([tri_f[i], tri_f[j], tri_b[j], tri_b[i]], "bone", "gnomon")
    meshes.append(g)
    gnomon = dict(A=A0, B=B0, C=C0, thick=thick, along=along)

    # escombros orbitando: dan escala y algo de melancolía
    for k, (pos, s) in enumerate([((-1.55, 0.25, 0.55), 0.06), ((1.45, -0.55, 0.7), 0.045),
                                  ((-1.2, -0.95, 0.4), 0.035), ((1.75, 0.65, -0.4), 0.03)]):
        meshes.append(shard(np.array(pos), s, rng))

    # raíl orbital: plano que contiene el punto de eclipse
    mesa_c = np.array([0, MESA_Y, 0])
    p_ecl = mesa_c + SUN * 2.05
    R = np.linalg.norm(p_ecl)
    u = p_ecl / R
    wh = norm(np.cross(u, [0, 1, 0]))
    wv = norm(np.cross(wh, u))
    w = norm(wh * math.cos(rail_tilt) + wv * math.sin(rail_tilt) * 0.55)

    def rail(th):
        return R * (math.cos(th) * u + math.sin(th) * w)

    moon_c = rail(moon_theta)
    moon_r = 0.3
    meshes.append(moon_mesh(moon_c, moon_r, rng))

    return dict(meshes=meshes, rail=rail, R=R, moon_c=moon_c, moon_r=moon_r, obs=obs,
                stones=stones, lamp=lamp, gnomon=gnomon, p_ecl=p_ecl, mesa_c=mesa_c)


# ------------------------------------------------------------------ cámara
class Camera:
    def __init__(self, yaw, pitch, scale, cx, cy):
        self.R = rot_x(pitch) @ rot_y(yaw)
        self.s, self.cx, self.cy = scale, cx, cy

    def view(self, p):
        return self.R @ p

    def proj(self, p):
        q = self.view(p)
        return np.array([self.cx + self.s * q[0], self.cy - self.s * q[1]]), q[2]


def fmt(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def path_d(pts, close=False):
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    return d + (" Z" if close else "")


def tone(lam):
    """Cuatro tonos con luz + dos de sombra: posterizado duro."""
    if lam <= 0:
        return 5
    for i, t in enumerate([0.8, 0.58, 0.34, 0.12]):
        if lam > t:
            return i
    return 4


def in_umbra(p, world, extra=1.0):
    c, r = world["moon_c"], world["moon_r"] * extra
    oc = c - p
    t = oc @ SUN
    if t < 0:
        return False
    return np.linalg.norm(oc - t * SUN) < r


# ------------------------------------------------------------------ fondo
def starfield(rng, n, avoid):
    out = []
    for _ in range(n):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        if math.hypot(x - avoid[0], y - avoid[1]) < avoid[2]:
            continue
        r = rng.choice([0.5, 0.6, 0.7, 0.8, 1.0, 1.2])
        o = rng.uniform(0.2, 0.75)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#d9d2ff" opacity="{o:.2f}"/>')
    for _ in range(8):
        x, y = rng.uniform(60, W - 60), rng.uniform(60, H - 60)
        if math.hypot(x - avoid[0], y - avoid[1]) < avoid[2] * 1.2:
            continue
        s = rng.choice([4, 5, 6])
        out.append(f'<path d="M{x - s:.1f},{y:.1f} H{x + s:.1f} M{x:.1f},{y - s:.1f} V{y + s:.1f}" '
                   f'stroke="#c9c0ff" stroke-width="0.8" opacity="0.6"/>')
    return "\n".join(out)


def chart_grid(cx, cy, radii, opacity=0.1):
    g = [f'<g fill="none" stroke="#b7adff" opacity="{opacity}">']
    for r in radii:
        g.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" stroke-width="0.8"/>')
    for k in range(24):
        a = math.pi * k / 12
        r0 = radii[0] * 1.02
        r1 = radii[0] * (1.08 if k % 2 else 1.14)
        g.append(f'<line x1="{cx + math.cos(a) * r0:.1f}" y1="{cy + math.sin(a) * r0:.1f}" '
                 f'x2="{cx + math.cos(a) * r1:.1f}" y2="{cy + math.sin(a) * r1:.1f}" stroke-width="0.9"/>')
    for k in range(12):
        a = math.pi * k / 6
        x1, y1 = cx + math.cos(a) * radii[1], cy + math.sin(a) * radii[1]
        x2, y2 = cx + math.cos(a) * 2400, cy + math.sin(a) * 2400
        g.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke-width="0.6" stroke-dasharray="2 7"/>')
    g.append("</g>")
    return "\n".join(g)


def corner_marks():
    s, m = 22, 36
    out = ['<g stroke="#b7adff" stroke-width="1" opacity="0.5" fill="none">']
    for x, y, dx, dy in [(m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)]:
        out.append(f'<path d="M{x},{y + dy * s} V{y} H{x + dx * s}"/>')
    for y in (m - 8, H - m + 8):
        out.append(f'<path d="M{W / 2 - 8},{y} H{W / 2 + 8} M{W / 2},{y - 8} V{y + 8}"/>')
        out.append(f'<circle cx="{W / 2}" cy="{y}" r="4"/>')
    out.append("</g>")
    return "\n".join(out)


# ----------------------------------------------------------------- render
def ekey(p):
    return tuple(np.round(p, 4))


def render(state, cam, moon_theta, out_name, o):
    world = build_world(moon_theta, o.get("rail_tilt", 1.0))
    eclipse = state == 3
    rng = random.Random(11 + state)
    A = {}
    edge = o.get("edge", 1.0)

    mesa2, _ = cam.proj(world["mesa_c"])
    pc2, _ = cam.proj(np.zeros(3))
    A["planet"] = [*pc2.round(1).tolist(), cam.s]
    sun2, _ = cam.proj(world["p_ecl"] + SUN * o.get("sun_dist", 3.0))
    A["sun"] = sun2.round(1).tolist()

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           "<defs>",
           f'<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
           f'<feGaussianBlur stdDeviation="{o.get("glow", 3)}" result="b"/>'
           '<feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
           '<filter id="soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="16"/></filter>',
           '<radialGradient id="lampHalo"><stop offset="0" stop-color="#ffc48f" stop-opacity="0.9"/>'
           '<stop offset="0.22" stop-color="#ff9a52" stop-opacity="0.4"/>'
           '<stop offset="1" stop-color="#ff9a52" stop-opacity="0"/></radialGradient>',
           '<radialGradient id="sunHalo"><stop offset="0" stop-color="#f4f1ff" stop-opacity="0.9"/>'
           '<stop offset="0.1" stop-color="#d9d2ff" stop-opacity="0.45"/>'
           '<stop offset="1" stop-color="#8f7dff" stop-opacity="0"/></radialGradient>',
           '<radialGradient id="corona"><stop offset="0.55" stop-color="#f3eeff" stop-opacity="0"/>'
           '<stop offset="0.62" stop-color="#f3eeff" stop-opacity="0.95"/>'
           '<stop offset="0.7" stop-color="#b9a6ff" stop-opacity="0.45"/>'
           '<stop offset="1" stop-color="#7b63ff" stop-opacity="0"/></radialGradient>',
           "</defs>",
           f'<rect width="{W}" height="{H}" fill="{INK}"/>']

    svg.append(chart_grid(*pc2, o["grid"], 0.13 if eclipse else 0.1))
    svg.append(starfield(rng, o.get("stars", 240), (*pc2, cam.s * 1.05)))

    # eje de alineación sol → meseta: la regla que el visitante debe cumplir
    if eclipse:
        svg.append(f'<line x1="{sun2[0]:.1f}" y1="{sun2[1]:.1f}" x2="{mesa2[0]:.1f}" y2="{mesa2[1]:.1f}" '
                   f'stroke="{GLOW_HI}" stroke-width="1.1" opacity="0.7"/>')
    else:
        svg.append(f'<line x1="{sun2[0]:.1f}" y1="{sun2[1]:.1f}" x2="{mesa2[0]:.1f}" y2="{mesa2[1]:.1f}" '
                   f'stroke="#cfc6ff" stroke-width="0.9" stroke-dasharray="3 7" opacity="0.45"/>')

    sr = o.get("sun_r", 10)
    if eclipse:
        svg.append(f'<circle cx="{sun2[0]:.1f}" cy="{sun2[1]:.1f}" r="{sr * 9:.1f}" fill="url(#sunHalo)" opacity="0.18"/>')
        svg.append(f'<circle cx="{sun2[0]:.1f}" cy="{sun2[1]:.1f}" r="{sr * 0.8:.1f}" fill="none" stroke="#cfc6ff" opacity="0.5"/>')
    else:
        svg.append(f'<circle cx="{sun2[0]:.1f}" cy="{sun2[1]:.1f}" r="{sr * 12:.1f}" fill="url(#sunHalo)" opacity="0.6"/>')
        svg.append(f'<circle cx="{sun2[0]:.1f}" cy="{sun2[1]:.1f}" r="{sr:.1f}" fill="#f7f4ff"/>')
        svg.append(f'<circle cx="{sun2[0]:.1f}" cy="{sun2[1]:.1f}" r="{sr * 2.4:.1f}" fill="none" stroke="#e8e2ff" stroke-width="0.8" opacity="0.6"/>')

    # raíl, partido en tramo trasero y delantero
    rail_pts = [world["rail"](2 * math.pi * k / 720) for k in range(721)]
    proj_rail = [cam.proj(p) for p in rail_pts]

    def rail_svg(front):
        out, cur, segs = [], [], []
        for xy, z in proj_rail:
            if (z > -0.05) == front:
                cur.append(xy)
            elif cur:
                segs.append(cur)
                cur = []
        if cur:
            segs.append(cur)
        op = 0.85 if front else 0.3
        for seg in segs:
            if len(seg) > 1:
                out.append(f'<path d="{path_d(seg)}" fill="none" stroke="#a9a0ef" '
                           f'stroke-width="{o.get("rail_w", 1.2)}" opacity="{op}"/>')
        for k in range(0, 720, 10):
            xy, z = proj_rail[k]
            if (z > -0.05) != front:
                continue
            major = k % 60 == 0
            a2, _ = cam.proj(rail_pts[k] * (1.07 if major else 1.035))
            out.append(f'<line x1="{xy[0]:.1f}" y1="{xy[1]:.1f}" x2="{a2[0]:.1f}" y2="{a2[1]:.1f}" '
                       f'stroke="#a9a0ef" stroke-width="{1.1 if major else 0.8}" opacity="{op}"/>')
        # marca del punto de alineación (θ = 0)
        xy, z = proj_rail[0]
        if (z > -0.05) == front and not eclipse:
            svg_r = o.get("target_r", 9)
            out.append(f'<circle cx="{xy[0]:.1f}" cy="{xy[1]:.1f}" r="{svg_r}" fill="none" stroke="#e7defe" '
                       f'stroke-width="1" stroke-dasharray="2 3" opacity="0.9"/>')
        return "\n".join(out)

    svg.append(rail_svg(False))

    # cono de umbra (eclipse)
    if eclipse:
        mc2, _ = cam.proj(world["moon_c"])
        dirv = mesa2 - mc2
        perp = np.array([-dirv[1], dirv[0]]) / np.linalg.norm(dirv)
        rm = world["moon_r"] * cam.s * 0.98
        rs = world["moon_r"] * 1.45 * cam.s
        a, b = mc2 + perp * rm, mc2 - perp * rm
        c, d = mesa2 - perp * rs * 0.55, mesa2 + perp * rs * 0.55
        svg.append(f'<path d="M{a[0]:.1f},{a[1]:.1f} L{d[0]:.1f},{d[1]:.1f} L{c[0]:.1f},{c[1]:.1f} '
                   f'L{b[0]:.1f},{b[1]:.1f} Z" fill="#7b63ff" opacity="0.07"/>')
        svg.append(f'<path d="M{a[0]:.1f},{a[1]:.1f} L{d[0]:.1f},{d[1]:.1f} M{b[0]:.1f},{b[1]:.1f} '
                   f'L{c[0]:.1f},{c[1]:.1f}" stroke="{GLOW}" stroke-width="0.9" stroke-dasharray="4 4" '
                   f'opacity="0.7" fill="none"/>')
        # corona detrás de la luna (el sol queda tapado en el eje)
        crr = world["moon_r"] * cam.s * 1.9
        svg.append(f'<circle cx="{mc2[0]:.1f}" cy="{mc2[1]:.1f}" r="{crr:.1f}" fill="url(#corona)"/>')

    # ---- caras visibles
    faces = []  # (depth, xy, fill, ti, mesh_id, idx, umbra)
    edge_map = {}
    for mi, mesh in enumerate(world["meshes"]):
        for pi, (pts, mat, tag) in enumerate(zip(mesh.polys, mesh.mats, mesh.tags)):
            wn = np.cross(pts[1] - pts[0], pts[2] - pts[0])
            ln = np.linalg.norm(wn)
            if ln == 0:
                continue
            wn = wn / ln
            cen = pts.mean(0)
            if wn @ (cen - mesh.center) < 0:
                wn = -wn
            vn = cam.R @ wn
            if vn[2] <= 1e-4:
                continue
            lam = float(wn @ SUN)
            ti = tone(lam)
            fill = RAMP[mat][ti]
            umbra = False
            if eclipse and mesh.name != "moon":
                samples = [cen] + [cen * 0.35 + p * 0.65 for p in pts]
                if sum(in_umbra(p, world, 1.45) for p in samples) >= 2:
                    umbra, fill = True, NIGHT[ti]
                elif sum(in_umbra(p, world, 1.85) for p in samples) >= 2:
                    ti = min(ti + 2, 5)
                    fill = RAMP[mat][ti]
                else:
                    ti = min(ti + 1, 5)  # todo el mundo baja un tono
                    fill = RAMP[mat][ti]
            if eclipse and mesh.name == "moon":
                fill, umbra = NIGHT_MOON[ti], True
            if tag == "slit":
                fill = "#ffd6a8" if eclipse else "#0b0a12"
            if tag == "door":
                fill = "#ffb877"  # ventana cálida: hay alguien (o hubo)
            xy = [cam.proj(p)[0] for p in pts]
            depth = float(np.mean([cam.view(p)[2] for p in pts]))
            fid = len(faces)
            # tono para contornos: material + índice
            key_tone = (mat if not umbra else "night", ti, tag)
            faces.append(dict(depth=depth, xy=xy, fill=fill, tone=key_tone, umbra=umbra, mesh=mi))
            for k in range(len(pts)):
                e = tuple(sorted([ekey(pts[k]), ekey(pts[(k + 1) % len(pts)])]))
                edge_map.setdefault((mi, e), []).append((fid, xy[k], xy[(k + 1) % len(pts)]))

    order = sorted(range(len(faces)), key=lambda i: faces[i]["depth"])
    rank = {fid: r for r, fid in enumerate(order)}

    # cada arista se dibuja tras la cara más cercana que la comparte
    edges_after = {}
    for (mi, e), lst in edge_map.items():
        fids = [f for f, _, _ in lst]
        if len(fids) == 1:
            kind = "sil"
        else:
            t0, t1 = faces[fids[0]]["tone"], faces[fids[1]]["tone"]
            if t0 == t1:
                continue
            kind = "tone" if t0[0] == t1[0] else "mat"
        last = max(fids, key=lambda f: rank[f])
        _, a, b = lst[0]
        umb = any(faces[f]["umbra"] for f in fids)
        edges_after.setdefault(last, []).append((kind, a, b, umb))

    body = []
    for fid in order:
        f = faces[fid]
        body.append(f'<polygon points="{fmt(f["xy"])}" fill="{f["fill"]}" stroke="{f["fill"]}" '
                    f'stroke-width="0.7" stroke-linejoin="round"/>')
        for kind, a, b, umb in edges_after.get(fid, []):
            if umb and eclipse:
                col, op = GLOW, 0.75 if kind != "tone" else 0.35
                sw = edge * (1.3 if kind == "sil" else 0.8)
            else:
                col = INK
                sw = edge * {"sil": 2.0, "mat": 1.2, "tone": 0.75}[kind]
                op = {"sil": 1, "mat": 0.9, "tone": 0.55}[kind]
            body.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
                        f'stroke="{col}" stroke-width="{sw:.2f}" stroke-opacity="{op}" stroke-linecap="round"/>')
    svg.append("\n".join(body))

    # ---- sobre la meseta
    gn = world["gnomon"]
    tip = gn["C"]

    def on_mesa(p):
        r = math.hypot(p[0], p[2])
        lim = 0.72
        if r > lim:
            p = np.array([p[0] * lim / r, p[1], p[2] * lim / r])
        return p

    if not eclipse:
        # sombra de la vela sobre la meseta (reloj de sol)
        def drop(p):
            t = (p[1] - MESA_Y - 0.003) / SUN[1]
            return p - SUN * t

        tri = [gn["A"], gn["B"], drop(gn["C"])]
        pts = []
        for i in range(3):
            p, q = tri[i], tri[(i + 1) % 3]
            for t in np.linspace(0, 1, 14, endpoint=False):
                pts.append(on_mesa(p + (q - p) * t))
        sh = [cam.proj(p)[0] for p in pts]
        svg.append(f'<polygon points="{fmt(sh)}" fill="{INK}" opacity="0.42"/>')

    # líneas horarias grabadas en abanico desde el pie de la vela
    hours = []
    foot = gn["A"] + gn["along"] * 0.05
    for k in range(-5, 4):
        a = math.atan2(0.75, -0.1) + k * 0.24
        p0 = foot + np.array([math.cos(a) * 0.12, 0.003, math.sin(a) * 0.12])
        p1 = on_mesa(foot + np.array([math.cos(a) * 1.2, 0.003, math.sin(a) * 1.2]))
        hours.append((cam.proj(p0)[0], cam.proj(p1)[0]))

    st = world["stones"]
    trail = []
    seq = [(i * 3) % 7 for i in range(8)]
    for i in range(7):
        trail.append((st[seq[i]], st[seq[i + 1]]))
    for i in range(7):
        trail.append((st[i], st[(i + 1) % 7]))
    near = min(range(7), key=lambda i: np.linalg.norm(st[i] - gn["A"]))
    trail.append((st[near], foot + [0, 0.004, 0]))

    if eclipse:
        g = [f'<g filter="url(#glow)" stroke="{GLOW}" fill="none" stroke-linecap="round">']
        for p, q in trail:
            seg = [cam.proj(p + (q - p) * t)[0] for t in np.linspace(0, 1, 14)]
            g.append(f'<path d="{path_d(seg)}" stroke-width="{o.get("trail_w", 2.0)}" opacity="0.95"/>')
        for a2, b2 in hours:
            g.append(f'<line x1="{a2[0]:.1f}" y1="{a2[1]:.1f}" x2="{b2[0]:.1f}" y2="{b2[1]:.1f}" '
                     f'stroke-width="1.2" opacity="0.8" stroke-dasharray="1 6"/>')
        for p in st:
            s2, _ = cam.proj(p)
            g.append(f'<circle cx="{s2[0]:.1f}" cy="{s2[1]:.1f}" r="{o.get("node_r", 3.5)}" fill="{GLOW_HI}" stroke="none"/>')
        g.append("</g>")
        svg.append("\n".join(g))
    elif state == 2:
        g = [f'<g stroke="{INK}" fill="none" stroke-width="1.1" stroke-dasharray="1 6" opacity="0.6">']
        for a2, b2 in hours:
            g.append(f'<line x1="{a2[0]:.1f}" y1="{a2[1]:.1f}" x2="{b2[0]:.1f}" y2="{b2[1]:.1f}"/>')
        g.append("</g>")
        svg.append("\n".join(g))

    # escala grabada en la hipotenusa de la vela (el «estilo» del reloj)
    if o.get("gnomon_ticks"):
        g = [f'<g stroke="{GLOW_HI if eclipse else "#d9d2f2"}" stroke-width="1" opacity="{0.85 if eclipse else 0.6}">']
        hyp = gn["B"] - gn["C"]
        nrm_in = norm((gn["A"] - gn["C"]) - hyp * (((gn["A"] - gn["C"]) @ hyp) / (hyp @ hyp)))
        for k in range(1, 24):
            t = k / 24
            p = gn["C"] + hyp * t + gn["thick"] * 1.01
            q = p + nrm_in * (0.07 if k % 6 == 0 else 0.035)
            a2, b2 = cam.proj(p)[0], cam.proj(q)[0]
            g.append(f'<line x1="{a2[0]:.1f}" y1="{a2[1]:.1f}" x2="{b2[0]:.1f}" y2="{b2[1]:.1f}"/>')
        g.append("</g>")
        svg.append("\n".join(g))

    # lámpara cálida: el único acento cálido
    lamp2, _ = cam.proj(world["lamp"])
    lr = o.get("lamp_r", 30)
    svg.append(f'<circle cx="{lamp2[0]:.1f}" cy="{lamp2[1]:.1f}" r="{lr:.1f}" fill="url(#lampHalo)" '
               f'opacity="{0.5 if eclipse else 1}"/>')
    svg.append(f'<circle cx="{lamp2[0]:.1f}" cy="{lamp2[1]:.1f}" r="{max(1.6, lr * 0.08):.1f}" fill="#ffe0bf"/>')
    A["lamp"] = lamp2.round(1).tolist()

    svg.append(rail_svg(True))

    mc2, _ = cam.proj(world["moon_c"])
    A["moon"] = [*mc2.round(1).tolist(), round(world["moon_r"] * cam.s, 1)]
    A["gnomon_tip"] = cam.proj(tip)[0].round(1).tolist()
    obs_top = world["obs"] + [0, 0.13 * 0.55 + 0.13, 0]
    A["obs"] = cam.proj(obs_top)[0].round(1).tolist()
    A["mesa"] = mesa2.round(1).tolist()
    A["rail_target"] = proj_rail[0][0].round(1).tolist()

    if state != 3 and o.get("moon_drag"):
        # gesto: arco discontinuo desde la luna hacia la marca de alineación
        th0 = moon_theta
        arc = [cam.proj(world["rail"](th0 + (0 - th0) * t) * 1.13)[0] for t in np.linspace(0.08, 0.92, 40)]
        svg.append(f'<path d="{path_d(arc)}" fill="none" stroke="#e7defe" stroke-width="1.1" '
                   f'stroke-dasharray="1 5" stroke-linecap="round" opacity="0.8"/>')
        a, b = arc[-2], arc[-1]
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        hx, hy = b
        p1 = (hx - 9 * math.cos(ang - 0.45), hy - 9 * math.sin(ang - 0.45))
        p2 = (hx - 9 * math.cos(ang + 0.45), hy - 9 * math.sin(ang + 0.45))
        svg.append(f'<path d="M{p1[0]:.1f},{p1[1]:.1f} L{hx:.1f},{hy:.1f} L{p2[0]:.1f},{p2[1]:.1f}" '
                   f'fill="none" stroke="#e7defe" stroke-width="1.1" opacity="0.85"/>')

    if eclipse:
        # cámara oscura: la rendija proyecta una imagen sobre el cielo
        o2 = np.array(A["obs"])
        dr = o.get("disc_r", 80)
        disc = o2 + np.array(o.get("disc_off", [0, -240]))
        A["disc"] = [*disc.round(1).tolist(), dr]
        svg.append(f'<path d="M{o2[0] - 3:.1f},{o2[1]:.1f} L{disc[0] - dr:.1f},{disc[1]:.1f} '
                   f'L{disc[0] + dr:.1f},{disc[1]:.1f} L{o2[0] + 3:.1f},{o2[1]:.1f} Z" '
                   f'fill="#c2b3ff" opacity="0.12"/>')
        for sgn in (-1, 1):
            svg.append(f'<line x1="{o2[0] + sgn * 3:.1f}" y1="{o2[1]:.1f}" x2="{disc[0] + sgn * dr:.1f}" '
                       f'y2="{disc[1]:.1f}" stroke="{GLOW}" stroke-width="0.8" opacity="0.55"/>')
        svg.append(f'<circle cx="{disc[0]:.1f}" cy="{disc[1]:.1f}" r="{dr + 6}" fill="{GLOW}" opacity="0.45" filter="url(#soft)"/>')
        svg.append(f'<circle cx="{disc[0]:.1f}" cy="{disc[1]:.1f}" r="{dr}" fill="#120d2a"/>')
        svg.append(f'<circle cx="{disc[0]:.1f}" cy="{disc[1]:.1f}" r="{dr + 12}" fill="none" stroke="{GLOW_HI}" stroke-width="1" opacity="0.8"/>')
        g = [f'<g stroke="{GLOW_HI}" stroke-width="1" opacity="0.7">']
        for k in range(36):
            a = 2 * math.pi * k / 36
            r0, r1 = dr + 18, dr + (30 if k % 9 == 0 else 23)
            g.append(f'<line x1="{disc[0] + math.cos(a) * r0:.1f}" y1="{disc[1] + math.sin(a) * r0:.1f}" '
                     f'x2="{disc[0] + math.cos(a) * r1:.1f}" y2="{disc[1] + math.sin(a) * r1:.1f}"/>')
        g.append("</g>")
        svg.append("\n".join(g))

    svg.append(corner_marks())
    svg.append("</svg>")
    (OUT / f"{out_name}.svg").write_text("\n".join(svg))
    (OUT / f"{out_name}.json").write_text(json.dumps(A, indent=1))
    return A


FRAMES = {
    # 1 · Órbita: el instrumento entero; Umbral pequeño, legible por su silueta
    "b1": (1, Camera(YAW, PITCH, 112, 700, 560), math.radians(110),
           dict(rail_tilt=1.4, grid=[150, 230, 400, 620, 860], stars=320, edge=0.75, lamp_r=16, sun_r=7,
                sun_dist=2.2, rail_w=1.1, glow=2, target_r=7, moon_drag=False)),
    # 2 · Aproximación: el planeta ocupa la parte baja; la luna, descubierta, arriba
    "b2": (2, Camera(YAW, PITCH, 330, 640, 860), math.radians(64),
           dict(rail_tilt=1.4, grid=[365, 520, 760, 1050], stars=230, edge=1.15, lamp_r=40, sun_r=9,
                sun_dist=1.05, gnomon_ticks=True, moon_drag=True)),
    # 3 · Eclipse: misma cámara; la luna alineada entre el sol y la meseta
    "b3": (3, Camera(YAW, PITCH, 330, 640, 860), 0.0,
           dict(rail_tilt=1.4, grid=[365, 520, 760, 1050], stars=230, edge=1.15, lamp_r=40, sun_r=9,
                sun_dist=1.05, trail_w=1.7, node_r=3.4, disc_r=76, disc_off=[-300, -330],
                gnomon_ticks=True)),
}

if __name__ == "__main__":
    import sys
    OUT.mkdir(exist_ok=True)
    names = sys.argv[1:] or list(FRAMES)
    for name in names:
        st, cam, th, opts = FRAMES[name]
        render(st, cam, th, name, opts)
