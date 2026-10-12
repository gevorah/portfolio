"""El cono de derrumbe bajo el jameo: bloques de colada y columnas caídas del tragaluz.

Los bloques son poliedros de fractura (envolvente convexa de puntos en un
elipsoide aplastado: el basalto rompe por planos), con bisel y desconchado. Las
columnas son prismas de 5 o 6 caras irregulares, partidos en los extremos por
planos inclinados, como los que siguen en pie alrededor del jameo.

Se colocan por capas sobre el cono: primero los grandes, luego los medianos en
los huecos, y cada uno se apoya en lo que ya hay debajo (rayo hacia abajo).
"""

import math
import random

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

from geo import K

PILE_TOP = -12.5          # cota de la cima del cono (el tubo corre a −27,5 con bancos a −20)
PILE_R = 20.0


def pile_height(X, Y, rng_seed=5):
    """Altura del cono de derrumbe (para sumar al suelo): asimétrico, más largo hacia la sala."""
    d = np.stack([X - K[0], Y - K[1]], -1)
    toward = np.array([0.72, 0.69])
    along = d @ toward
    r = np.hypot(d[..., 0], d[..., 1]) - 0.35 * np.clip(along, 0, None)
    # cono de derrumbe: ángulo de reposo de los bloques (~30°), cima redondeada
    cone = PILE_TOP - 0.58 * r - 0.012 * np.maximum(r - 8, 0) ** 2
    # superficie de losas: cada bloque es un plano inclinado propio, con juntas entre ellos
    from geo import column_cells
    out = cone.copy()
    for size, amp, seed in ((3.4, 1.4, 61), (1.5, 0.6, 62)):
        edge, cid, cx, cy = column_cells(X, Y, size, seed)
        rnd = lambda k: ((cid * (2654435761 + 7919 * k)) % 1009) / 1009.0
        dcx = np.stack([cx - K[0], cy - K[1]], -1)
        rc = np.hypot(dcx[..., 0], dcx[..., 1]) - 0.35 * np.clip(dcx @ toward, 0, None)
        base = PILE_TOP - 0.58 * rc - 0.012 * np.maximum(rc - 8, 0) ** 2
        tilt = (rnd(1) - 0.5) * 0.9 * (X - cx) + (rnd(2) - 0.5) * 0.9 * (Y - cy)
        slab = base + amp * rnd(3) + tilt - 0.5 * smoothstep_np(0.25, 0.0, edge)
        out = np.maximum(out, slab)
    return out


def smoothstep_np(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def make_block(name, size, flat, seed):
    rnd = random.Random(seed)
    bm = bmesh.new()
    pts = []
    for _ in range(26):
        v = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 1))).normalized()
        pts.append(Vector((v.x * size * rnd.uniform(0.7, 1.0), v.y * size * rnd.uniform(0.55, 1.0), v.z * size * flat * rnd.uniform(0.7, 1.0))))
    for p in pts:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    return ob


def make_column(name, radius, length, sides, seed):
    rnd = random.Random(seed)
    bm = bmesh.new()
    ring = []
    for i in range(sides):
        a = 2 * math.pi * i / sides + rnd.uniform(-0.25, 0.25)
        r = radius * rnd.uniform(0.82, 1.08)
        ring.append((r * math.cos(a), r * math.sin(a)))
    bot = [bm.verts.new((x, y, -length / 2)) for x, y in ring]
    top = [bm.verts.new((x, y, length / 2)) for x, y in ring]
    bm.faces.new(bot[::-1])
    bm.faces.new(top)
    for i in range(sides):
        j = (i + 1) % sides
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    # extremos partidos: planos inclinados de rotura
    for end in (1, -1):
        n = Vector((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), end)).normalized()
        co = Vector((0, 0, end * (length / 2 - rnd.uniform(0.1, 0.5))))
        res = bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=n, clear_outer=True)
        edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if edges:
            bmesh.ops.edgenet_fill(bm, edges=edges)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return bpy.data.objects.new(name, me)


def finish(ob, size, seed, coll):
    """Bisel, subdivisión y desconchado: aristas vivas pero gastadas."""
    coll.objects.link(ob)
    bev = ob.modifiers.new("bisel", "BEVEL")
    bev.width = 0.09 * size
    bev.segments = 2
    bev.limit_method = "ANGLE"
    sub = ob.modifiers.new("sub", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 2
    sub.subdivision_type = "CATMULL_CLARK"
    tex = bpy.data.textures.new(f"desconchado{seed}", "VORONOI")
    tex.noise_scale = 0.35 * size
    tex.distance_metric = "DISTANCE"
    dis = ob.modifiers.new("desconchado", "DISPLACE")
    dis.texture = tex
    dis.strength = 0.12 * size
    dis.mid_level = 0.6
    tex2 = bpy.data.textures.new(f"grano{seed}", "CLOUDS")
    tex2.noise_scale = 0.12 * size
    dis2 = ob.modifiers.new("grano", "DISPLACE")
    dis2.texture = tex2
    dis2.strength = 0.03 * size
    for p in ob.data.polygons:
        p.use_smooth = True


def place_pile(floor_obj, material, seed=11, keep_clear=()):
    """Coloca bloques y columnas por capas sobre el suelo (que ya incluye el cono)."""
    rnd = random.Random(seed)
    coll = bpy.data.collections.new("Derrumbe")
    bpy.context.scene.collection.children.link(coll)
    dg = bpy.context.evaluated_depsgraph_get()
    placed = []

    def bvh_all():
        objs = [floor_obj] + placed
        trees = []
        for o in objs:
            ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
            me = ev.to_mesh()
            mw = o.matrix_world
            verts = [mw @ v.co for v in me.vertices]
            polys = [tuple(p.vertices) for p in me.polygons]
            trees.append(BVHTree.FromPolygons(verts, polys))
            ev.to_mesh_clear()
        return trees

    layers = [  # (cantidad, tamaño mín., tamaño máx., fracción de columnas, radio de reparto)
        (16, 2.6, 5.0, 0.35, 0.75),
        (45, 1.1, 2.4, 0.45, 0.95),
        (110, 0.3, 1.0, 0.3, 1.15),
    ]
    i = 0
    for count, smin, smax, fcol, spread in layers:
        trees = bvh_all()
        for _ in range(count):
            size = rnd.uniform(smin, smax)
            if rnd.random() < fcol:
                ob = make_column(f"columna{i}", 0.85 * min(size / 2.2, 1.0) + 0.15, size * rnd.uniform(1.4, 2.4), rnd.choice((5, 6, 6, 7)), seed + i)
            else:
                ob = make_block(f"bloque{i}", size, rnd.uniform(0.45, 0.8), seed + i)
            finish(ob, size, seed + i, coll)
            ob.data.materials.append(material)
            # reparto: más denso en la cima y hacia la sala
            a = rnd.uniform(0, 2 * math.pi)
            r = PILE_R * spread * math.sqrt(rnd.random())
            x = K[0] + r * math.cos(a) + 0.25 * r * 0.72
            y = K[1] + r * math.sin(a) + 0.25 * r * 0.69
            hit = None
            for t in trees:
                loc, nrm, _, dist = t.ray_cast(Vector((x, y, 60.0)), Vector((0, 0, -1)))
                if loc is not None and (hit is None or loc.z > hit[0].z):
                    hit = (loc, nrm)
            if hit is None:
                bpy.data.objects.remove(ob)
                continue
            loc, nrm = hit
            if any((Vector(c[:2]) - loc.xy).length < c[2] + size for c in keep_clear):
                bpy.data.objects.remove(ob)
                continue
            # tumbado sobre la pendiente, con el eje largo al azar; hundido un tercio
            up = nrm.normalized()
            rot = up.to_track_quat("Z", "Y").to_matrix().to_4x4() @ Matrix.Rotation(rnd.uniform(0, 2 * math.pi), 4, "Z")
            if ob.name.startswith("columna"):
                rot = rot @ Matrix.Rotation(math.radians(rnd.uniform(70, 95)), 4, "X")
            ob.matrix_world = Matrix.Translation(loc + up * size * 0.25) @ rot
            placed.append(ob)
            i += 1
    return coll
