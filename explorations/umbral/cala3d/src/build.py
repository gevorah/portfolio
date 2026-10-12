"""Monta La Cala Interior en Blender a partir de la roca (shell.npz) y las Gradas (gours_*.npy).

uso: python build.py [clay|final] [low|high] [A|B] salida.png [ancho alto muestras]
     (con bpy instalado como módulo; guarda también work/cala.blend)
"""

import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.path.join(ROOT, "work")
sys.path.insert(0, HERE)

MODE = sys.argv[1] if len(sys.argv) > 1 else "clay"
TIDE = sys.argv[2] if len(sys.argv) > 2 else "low"
CAM = sys.argv[3] if len(sys.argv) > 3 else "A"
OUT = sys.argv[4] if len(sys.argv) > 4 else os.path.join(WORK, "test.png")
RW, RH = (int(sys.argv[5]), int(sys.argv[6])) if len(sys.argv) > 6 else (800, 500)
SPP = int(sys.argv[7]) if len(sys.argv) > 7 else 32

SEA = -24.0 if TIDE == "low" else 0.0
# el sol: tarde baja y cálida en bajamar; en pleamar, mañana más alta y blanca
# (azimut, elevación) elegidos con rayos para que el haz caiga donde cuenta: en bajamar
# sobre las gradas medias; en pleamar, sobre la laguna que cubre las gradas bajas
SUN_AZ_EL = (221.0, 50.0) if TIDE == "low" else (218.0, 66.0)
_a, _e = math.radians(SUN_AZ_EL[0]), math.radians(SUN_AZ_EL[1])
SUN_DIR = Vector((math.cos(_e) * math.cos(_a), math.cos(_e) * math.sin(_a), math.sin(_e)))


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.unit_settings.system = "METRIC"
    return s


def mesh_obj(name, verts, faces, smooth=True):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", np.asarray(verts, np.float32).ravel())
    nf = len(faces)
    me.loops.add(nf * 3)
    me.loops.foreach_set("vertex_index", np.asarray(faces, np.int32).ravel())
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(0, nf * 3, 3, dtype=np.int32))
    me.update(calc_edges=True)
    me.validate()
    if smooth:
        me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def grid_mesh(name, H, ext, cell, mask=None, step=1):
    """Malla de un campo de alturas (fila = y, columna = x); mask recorta celdas."""
    H = H[::step, ::step]
    n = H.shape[0]
    c = cell * step
    xs = (np.arange(n) + 0.5) * c - ext
    X, Y = np.meshgrid(xs, xs)
    verts = np.stack([X.ravel(), Y.ravel(), H.ravel()], -1)
    idx = np.arange(n * n).reshape(n, n)
    a, b, cc, d = idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]
    keep = np.ones(a.shape, bool) if mask is None else mask[::step, ::step][:-1, :-1]
    t1 = np.stack([a[keep], b[keep], cc[keep]], -1)
    t2 = np.stack([a[keep], cc[keep], d[keep]], -1)
    return mesh_obj(name, verts, np.concatenate([t1, t2]))


def set_attr(ob, name, values):
    """Atributo de punto (float) para los materiales."""
    a = ob.data.attributes.new(name, "FLOAT", "POINT")
    a.data.foreach_set("value", np.asarray(values, np.float32).ravel())


def clay(name, color, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return m


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


CAMERAS = {
    # A · llegada: a la salida del tubo, desde el banco sur, las gradas en tres cuartos
    "A": dict(loc=(-8.6, -19.0, 3.9), target=(24.0, 22.0, -13.0), lens=22),
    # B · desde las gradas medias, de vuelta hacia el jameo y el tubo que lleva a La Rompiente
    "B": dict(loc=(36.0, 18.0, None), target=(-22.0, -20.0, -8.0), lens=19),
    # detalle de las gradas (solo para revisar)
    "D": dict(loc=(14.0, 4.0, -12.0), target=(28.0, 22.0, -12.5), lens=24),
}


def build():
    s = reset()
    sh = np.load(os.path.join(WORK, "shell.npz"))
    rock = mesh_obj("Roca", sh["verts"], sh["faces"])
    from scipy.ndimage import zoom
    UP = 2                                          # el suelo se malla a 12,5 cm: cortinas sin dientes de sierra
    CELLF = 0.25 / UP
    h = zoom(np.load(os.path.join(WORK, "gours_h.npy")).astype(np.float64), UP, order=3)
    # el suelo solo existe donde hay aire encima: lo demás queda dentro de la roca
    from scipy.ndimage import gaussian_filter
    import shell as shellmod
    xs_ = (np.arange(h.shape[0]) + 0.5) * CELLF - 64.0
    Xg, Yg = np.meshgrid(xs_, xs_)
    inside = shellmod.air(Xg, Yg, h + 0.4) > -1.5
    from scipy.ndimage import binary_dilation
    inside = binary_dilation(inside, iterations=6)
    h = gaussian_filter(h, 1.0)
    import rocks
    ph = rocks.pile_height(Xg, Yg)
    pile_mask = ph > h + 0.05
    h = np.maximum(h, ph)                              # el cono de derrumbe bajo el jameo
    floor = grid_mesh("Gradas", h, 64.0, CELLF, mask=inside, step=1)
    w = zoom(np.load(os.path.join(WORK, "gours_w.npy")).astype(np.float64), UP, order=1)
    h0 = zoom(np.load(os.path.join(WORK, "gours_h0.npy")).astype(np.float64), UP, order=1)
    q = np.clip(zoom(np.load(os.path.join(WORK, "gours_q.npy")).astype(np.float64), UP, order=1), 0, None)
    # agua: el mar que entra por el tubo y las pozas de las gradas por encima de él
    pools = (w - h > 0.03) & (w > SEA)
    wl = np.where(pools, w, SEA)
    # el agua continúa un poco bajo el travertino: la orilla la dibuja el corte limpio con el suelo
    wmask = binary_dilation(wl - h > 0.005, iterations=4)
    water = grid_mesh("Agua", wl, 64.0, CELLF, mask=wmask, step=1)
    set_attr(floor, "dep", np.clip(h - h0, 0, None))
    set_attr(floor, "flow", np.clip(np.log10(q / q.max() * 1e5 + 1) / 5, 0, 1))
    set_attr(floor, "depth", np.clip(wl - h, 0, None))
    set_attr(water, "depth", np.clip(wl - h, 0, None))
    set_attr(water, "sea", (~pools).astype(np.float32))
    if MODE == "clay":
        rock_mat = clay("roca", (0.32, 0.32, 0.33))
        rock.data.materials.append(rock_mat)
        floor.data.materials.append(clay("suelo", (0.55, 0.52, 0.46)))
        water.data.materials.append(clay("agua", (0.05, 0.12, 0.14), 0.05))
    else:
        import mats
        rock_mat = mats.rock_material(SEA)
        rock.data.materials.append(rock_mat)
        floor.data.materials.append(mats.travertine_material())
        floor.data.materials.append(rock_mat)
        # el cono de derrumbe es basalto, no travertino
        n = h.shape[0]
        cell_pile = (pile_mask[:-1, :-1] | pile_mask[1:, 1:])[inside[:-1, :-1]]
        mi = np.concatenate([cell_pile, cell_pile]).astype(np.int32)
        floor.data.polygons.foreach_set("material_index", mi)
        water.data.materials.append(mats.water_material())
        water.visible_shadow = False              # el sol llega al fondo sumergido (sin cáusticas ruidosas)
        # bruma: el vapor del manantial y el salitre hacen visible el haz del jameo
        bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, 0.0))
        mist = bpy.context.object
        mist.name = "Bruma"
        top, bot = 50.0, SEA + 0.2                # la bruma vive en el aire, no bajo el agua
        mist.scale = (70.0, 70.0, (top - bot) / 2)
        mist.location = (-10.0, -5.0, (top + bot) / 2)
        mist.data.materials.append(mats.mist_material(0.0016 if TIDE == "low" else 0.0032))
        # la Bóveda: al final del tubo, la luz del mar bajo el alero de La Rompiente
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(-112.0, -79.0, -14.0))
        bov = bpy.context.object
        bov.name = "LuzBoveda"
        bov.scale = (40.0, 40.0, 1.0)
        bov.rotation_euler = Vector((1.0, 0.68, 0.0)).normalized().to_track_quat("Z", "Y").to_euler()
        bov.data.materials.append(mats.emission_material("Mar", (0.55, 0.78, 0.85), 2.0))
    clear = [(CAMERAS[CAM]["loc"][0], CAMERAS[CAM]["loc"][1], 6.0)] if CAM == "A" else []
    rocks.place_pile(floor, rock_mat, keep_clear=clear)
    import life
    life.populate(np.asarray(sh["verts"], np.float64), np.asarray(sh["faces"]))
    # sol
    sun_data = bpy.data.lights.new("Sol", "SUN")
    sun_data.energy = 2.4 if TIDE == "low" else 2.6
    sun_data.angle = math.radians(0.6)
    sun_data.color = (1.0, 0.78, 0.55) if TIDE == "low" else (1.0, 0.94, 0.86)
    sun = bpy.data.objects.new("Sol", sun_data)
    s.collection.objects.link(sun)
    sun.rotation_euler = (-SUN_DIR).to_track_quat("-Z", "Y").to_euler()
    # cielo
    world = bpy.data.worlds.new("Cielo")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.22, 0.34, 0.62, 1) if TIDE == "low" else (0.30, 0.48, 0.80, 1)
    bg.inputs["Strength"].default_value = 2.2
    s.world = world
    # cámara
    cd = CAMERAS[CAM]
    cam = bpy.data.objects.new("Cam" + CAM, bpy.data.cameras.new("Cam" + CAM))
    s.collection.objects.link(cam)
    loc = list(cd["loc"])
    if loc[2] is None:                             # de pie sobre el suelo: 1,7 m
        loc[2] = float(h[int((loc[1] + 64) / CELLF), int((loc[0] + 64) / CELLF)]) + 1.7
    target = Vector(cd["target"])
    if loc[2] < SEA + 0.6:                         # en pleamar se llega a nado: ojos sobre el agua
        loc[2] = SEA + 1.2
        target.z = SEA - 4.5                       # la mirada baja hacia las gradas sumergidas
    cam.location = loc
    look_at(cam, target)
    cam.data.lens = cd["lens"]
    cam.data.clip_end = 1000
    s.camera = cam
    # render
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = SPP
    s.cycles.use_denoising = True
    s.cycles.max_bounces = 8
    s.cycles.diffuse_bounces = 4
    s.cycles.glossy_bounces = 3
    s.cycles.transmission_bounces = 6
    s.cycles.volume_bounces = 1
    s.cycles.transparent_max_bounces = 8
    s.cycles.volume_step_rate = 4.0
    s.cycles.sample_clamp_indirect = 8.0
    s.cycles.light_sampling_threshold = 0.01
    s.render.resolution_x, s.render.resolution_y = RW, RH
    s.render.film_transparent = False
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Medium High Contrast" if MODE == "final" else "None"
    s.view_settings.exposure = float(os.environ.get("EXPO", "3.5")) if MODE == "final" else 0.0
    s.render.filepath = OUT
    if MODE == "clay":
        # revisión de forma: iluminación de estudio, sin depender de la luz real de la cueva
        s.render.engine = "BLENDER_WORKBENCH"
        sh_ = s.display.shading
        sh_.light = "STUDIO"
        sh_.color_type = "MATERIAL"
        sh_.show_cavity = True
        sh_.cavity_type = "BOTH"
        sh_.show_shadows = True
        s.display.shadow_focus = 0.4
        s.view_settings.view_transform = "Standard"
    return s


if __name__ == "__main__":
    s = build()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f"cala_{MODE}.blend"), compress=True)
    bpy.ops.render.render(write_still=True)
