"""Lo vivo alrededor del jameo: raíces que cuelgan hacia la luz y helechos en las repisas.

Las raíces bajan desde el borde del tragaluz buscando el agua de la sala; se
agrupan en mechones, se curvan un poco y se cruzan con el haz de sol. Los
helechos crecen solo donde la roca mira hacia arriba y le llega luz y humedad.
"""

import math
import random

import bmesh
import bpy
import numpy as np
from mathutils import Vector

from geo import J1, K


def vertex_normals(v, f):
    n = np.zeros_like(v)
    fn = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    for k in range(3):
        np.add.at(n, f[:, k], fn)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)


def shaft_coords(v):
    d = v[:, :2] - K
    u = d @ J1
    w = d[:, 0] * -J1[1] + d[:, 1] * J1[0]
    return u, w


def root_material():
    m = bpy.data.materials.new("Raiz")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.06, 0.04, 0.025, 1)
    b.inputs["Roughness"].default_value = 0.7
    return m


def fern_material():
    m = bpy.data.materials.new("Helecho")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.045, 0.11, 0.02, 1)
    b.inputs["Roughness"].default_value = 0.55
    # hojas finas: dejan pasar la luz (a contraluz se encienden en verde)
    b.inputs["Transmission Weight"].default_value = 0.0
    b.inputs["Subsurface Weight"].default_value = 0.0
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    tr.inputs["Color"].default_value = (0.12, 0.30, 0.03, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.4
    out = nt.nodes["Material Output"]
    nt.links.new(b.outputs[0], mix.inputs[1])
    nt.links.new(tr.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def add_roots(v, f, coll, seed=3):
    rnd = random.Random(seed)
    n = vertex_normals(v, f)
    u, w = shaft_coords(v)
    ell = np.sqrt((u / 17.0) ** 2 + (w / 9.5) ** 2)
    cand = np.where((v[:, 2] > 15.0) & (v[:, 2] < 34.0) & (ell > 0.7) & (ell < 1.6) & (n[:, 2] < 0.2))[0]
    rnd.shuffle(cand := list(cand))
    mat = root_material()
    cu = bpy.data.curves.new("Raices", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 1.0
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    count = 0
    for idx in cand[:26]:
        base = Vector(v[idx]) + Vector(n[idx]) * 0.05
        for strand in range(rnd.randint(3, 9)):
            length = rnd.uniform(4.0, 16.0) * (0.5 + 0.5 * rnd.random())
            sp = cu.splines.new("NURBS")
            pts = 7
            sp.points.add(pts - 1)
            off = Vector((rnd.gauss(0, 0.25), rnd.gauss(0, 0.25), 0))
            drift = Vector((rnd.gauss(0, 0.6), rnd.gauss(0, 0.6), 0))
            for k in range(pts):
                t = k / (pts - 1)
                p = base + off + drift * t * t + Vector((0, 0, -length * t))
                p += Vector((math.sin(t * 6 + strand) * 0.15, math.cos(t * 5 + strand) * 0.15, 0))
                sp.points[k].co = (*p, 1.0)
                sp.points[k].radius = (0.045 if strand == 0 else 0.022) * (1.0 - 0.75 * t)
            sp.order_u = 4
            sp.use_endpoint_u = True
            count += 1
    ob = bpy.data.objects.new("Raices", cu)
    ob.data.materials.append(mat)
    coll.objects.link(ob)
    return count


def fern_mesh(seed):
    """Una fronda: raquis curvo con pinnas que se acortan hacia la punta."""
    rnd = random.Random(seed)
    bm = bmesh.new()
    L = rnd.uniform(0.6, 1.3)
    segs = 14
    arch = rnd.uniform(0.25, 0.55)
    prev = None
    for i in range(segs):
        t = i / (segs - 1)
        p = Vector((0, L * t, L * arch * math.sin(t * 2.4) - L * 0.35 * t * t))
        width = 0.22 * L * (1 - t) ** 0.8 * (0.4 + 0.6 * math.sin(min(t * 4, 1) * math.pi / 2))
        for side in (-1, 1):
            a = bm.verts.new(p)
            b = bm.verts.new(p + Vector((side * width, 0.06 * L, -0.03)))
            c = bm.verts.new(p + Vector((side * width * 0.6, 0.11 * L, -0.02)))
            bm.faces.new((a, b, c) if side > 0 else (a, c, b))
    me = bpy.data.meshes.new(f"fronda{seed}")
    bm.to_mesh(me)
    bm.free()
    return me


def add_ferns(v, f, coll, seed=9):
    rnd = random.Random(seed)
    n = vertex_normals(v, f)
    u, w = shaft_coords(v)
    ell = np.sqrt((u / 17.0) ** 2 + (w / 9.5) ** 2)
    cand = np.where((v[:, 2] > 18.0) & (v[:, 2] < 50.0) & (ell > 0.8) & (ell < 2.4) & (n[:, 2] > 0.35))[0]
    cand = list(cand)
    rnd.shuffle(cand)
    mat = fern_material()
    meshes = [fern_mesh(seed + k) for k in range(6)]
    for me in meshes:
        me.materials.append(mat)
    count = 0
    for idx in cand[:420]:
        base = Vector(v[idx])
        nrm = Vector(n[idx])
        for k in range(rnd.randint(3, 7)):              # cada mata, varias frondas en roseta
            ob = bpy.data.objects.new("helecho", rnd.choice(meshes))
            ob.location = base
            rot = nrm.to_track_quat("Z", "Y").to_euler()
            ob.rotation_euler = rot
            ob.rotation_euler.rotate_axis("Z", rnd.uniform(0, 2 * math.pi))
            ob.rotation_euler.rotate_axis("X", rnd.uniform(-0.6, 0.2))
            sc = rnd.uniform(0.7, 1.5)
            ob.scale = (sc, sc, sc)
            coll.objects.link(ob)
            count += 1
    return count


def populate(shell_verts, shell_faces):
    coll = bpy.data.collections.new("Vida")
    bpy.context.scene.collection.children.link(coll)
    nr = add_roots(shell_verts, shell_faces, coll)
    nf = add_ferns(shell_verts, shell_faces, coll)
    print(f"raíces: {nr} · frondas: {nf}")
    return coll
