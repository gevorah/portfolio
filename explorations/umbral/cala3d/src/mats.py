"""Materiales de La Cala Interior (nodos de Cycles).

Coordenadas de textura = posición en el mundo (los objetos están en el origen),
así que las bandas de marea y de escoria caen a su cota real.
"""

import bpy


class G:
    """Pequeño ayudante para escribir árboles de nodos legibles."""

    def __init__(self, mat):
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.x = 0

    def n(self, kind, **inputs):
        node = self.nt.nodes.new(kind)
        for k, v in inputs.items():
            if k.startswith("_"):
                setattr(node, k[1:], v)
                continue
            sock = node.inputs[k]
            if isinstance(v, bpy.types.NodeSocket):
                self.nt.links.new(v, sock)
            else:
                if isinstance(v, tuple) and len(v) == 3 and len(sock.default_value) == 4:
                    v = (*v, 1.0)
                sock.default_value = v
        return node

    def link(self, a, b):
        self.nt.links.new(a, b)


def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, G(m)


def _math(g, op, a, b=0.0, clamp=False):
    node = g.nt.nodes.new("ShaderNodeMath")
    node.operation = op
    node.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if isinstance(v, bpy.types.NodeSocket):
            g.link(v, node.inputs[i])
        else:
            node.inputs[i].default_value = v
    return node.outputs[0]


def band(g, z, lo, hi, soft):
    """1 entre las cotas lo y hi, con bordes suaves."""
    a = _math(g, "SUBTRACT", z, lo - soft)
    a = _math(g, "DIVIDE", a, 2 * soft, clamp=True)
    b = _math(g, "SUBTRACT", hi + soft, z)
    b = _math(g, "DIVIDE", b, 2 * soft, clamp=True)
    return _math(g, "MULTIPLY", a, b)


def mix_col(g, fac, a, b):
    node = g.nt.nodes.new("ShaderNodeMix")
    node.data_type = "RGBA"
    node.blend_type = "MIX"
    for sock, v in ((node.inputs[0], fac), (node.inputs[6], a), (node.inputs[7], b)):
        if isinstance(v, bpy.types.NodeSocket):
            g.link(v, sock)
        else:
            sock.default_value = v if len(v) == 4 else (*v, 1.0)
    return node.outputs[2]


def noise(g, vec, scale, detail=4.0, rough=0.55, dist=0.0):
    return g.n("ShaderNodeTexNoise", Vector=vec, Scale=scale, Detail=detail, Roughness=rough, Distortion=dist).outputs["Fac"]


def ramp(g, fac, stops):
    node = g.nt.nodes.new("ShaderNodeValToRGB")
    g.link(fac, node.inputs[0])
    els = node.color_ramp.elements
    while len(els) > len(stops):
        els.remove(els[-1])
    while len(els) < len(stops):
        els.new(0.5)
    for el, (p, c) in zip(els, stops):
        el.position = p
        el.color = (*c, 1.0)
    return node.outputs[0]


def rock_material(sea_level):
    m, g = new_mat("Basalto")
    geo = g.n("ShaderNodeNewGeometry")
    pos = geo.outputs["Position"]
    nrm = geo.outputs["Normal"]
    sep = g.n("ShaderNodeSeparateXYZ", Vector=pos)
    z = sep.outputs["Z"]
    nz = g.n("ShaderNodeSeparateXYZ", Vector=nrm).outputs["Z"]
    # basalto: casi negro azulado, con zonas vidriadas y otras ásperas
    n_big = noise(g, pos, 0.035, 3, 0.5)
    n_mid = noise(g, pos, 0.18, 4, 0.55)
    base = ramp(g, n_big, [(0.30, (0.030, 0.031, 0.036)), (0.55, (0.048, 0.046, 0.050)), (0.75, (0.062, 0.058, 0.058))])
    # escoria oxidada entre coladas: bandas rojizas a su cota (mismas que en la forma)
    zw = _math(g, "ADD", z, _math(g, "MULTIPLY", n_big, 3.0))
    sco = _math(g, "ADD", band(g, zw, -9.5, -6.5, 0.8), band(g, zw, 8.0, 10.0, 0.6))
    sco = _math(g, "ADD", sco, band(g, zw, 20.5, 23.5, 0.9), clamp=True)
    col = mix_col(g, _math(g, "MULTIPLY", sco, 0.85), base, (0.105, 0.045, 0.028))
    # costras minerales en el techo: blancas, en coliflor, solo donde gotea
    ceil = _math(g, "MULTIPLY", _math(g, "MULTIPLY", nz, -1.0), 1.6, clamp=True)
    pop = noise(g, pos, 0.9, 4, 0.65)
    crust = _math(g, "MULTIPLY", ceil, _math(g, "SUBTRACT", _math(g, "MULTIPLY", n_mid, 2.2), 0.95, clamp=True))
    crust = _math(g, "MULTIPLY", crust, band(g, z, -14.0, 40.0, 3.0))
    col = mix_col(g, crust, col, (0.42, 0.40, 0.36))
    # franja intermareal en las paredes del tubo y de la sala
    wet = band(g, z, sea_level - 40.0, 0.4, 0.3)
    col = mix_col(g, _math(g, "MULTIPLY", wet, 0.3), col, (0.014, 0.016, 0.018))
    # sal seca: velo blanquecino en lo que la marea dejó al aire
    salt = _math(g, "MULTIPLY", wet, _math(g, "SUBTRACT", _math(g, "MULTIPLY", n_big, 2.0), 0.7, clamp=True))
    col = mix_col(g, _math(g, "MULTIPLY", salt, 0.35), col, (0.16, 0.16, 0.15))
    barn = _math(g, "MULTIPLY", band(g, z, -3.0, -0.2, 0.4), _math(g, "SUBTRACT", _math(g, "MULTIPLY", pop, 2.0), 0.7, clamp=True))
    col = mix_col(g, barn, col, (0.30, 0.29, 0.26))
    algae = _math(g, "MULTIPLY", band(g, z, -21.0, -12.0, 1.0), _math(g, "SUBTRACT", _math(g, "MULTIPLY", n_mid, 2.4), 1.0, clamp=True))
    col = mix_col(g, _math(g, "MULTIPLY", algae, 0.8), col, (0.035, 0.050, 0.020))
    # musgo y helecho junto al jameo, donde llega el sol
    vd = g.n("ShaderNodeVectorMath", _operation="DISTANCE")
    g.link(pos, vd.inputs[0])
    vd.inputs[1].default_value = (-16.0, -14.0, 30.0)
    dk = vd.outputs["Value"]
    near_k = _math(g, "SUBTRACT", 1.0, _math(g, "DIVIDE", dk, 26.0), clamp=True)
    moss = _math(g, "MULTIPLY", _math(g, "MULTIPLY", near_k, 2.0, clamp=True), _math(g, "MULTIPLY", nz, 3.0, clamp=True))
    moss = _math(g, "MULTIPLY", moss, _math(g, "SUBTRACT", _math(g, "MULTIPLY", n_mid, 2.0), 0.6, clamp=True))
    col = mix_col(g, moss, col, (0.040, 0.075, 0.018))
    rough = _math(g, "ADD", 0.48, _math(g, "MULTIPLY", n_mid, 0.4))
    rough = _math(g, "SUBTRACT", rough, _math(g, "MULTIPLY", wet, 0.12))
    # relieve: vesículas de gas, grietas de enfriamiento, costra
    vor = g.n("ShaderNodeTexVoronoi", Vector=pos, Scale=0.22, Randomness=1.0, _feature="DISTANCE_TO_EDGE")
    cracks = _math(g, "SUBTRACT", 1.0, _math(g, "DIVIDE", vor.outputs["Distance"], 0.05, clamp=True))
    ves = g.n("ShaderNodeTexVoronoi", Vector=pos, Scale=9.0).outputs["Distance"]
    h = _math(g, "ADD", _math(g, "MULTIPLY", n_mid, 0.9), _math(g, "MULTIPLY", ves, 0.08))
    h = _math(g, "SUBTRACT", h, _math(g, "MULTIPLY", _math(g, "MULTIPLY", cracks, n_mid), 0.35))
    h = _math(g, "ADD", h, _math(g, "MULTIPLY", crust, _math(g, "MULTIPLY", pop, 0.8)))
    bump = g.n("ShaderNodeBump", Strength=0.45, Distance=0.25, Height=h)
    bsdf = g.n("ShaderNodeBsdfPrincipled", **{"Base Color": col, "Roughness": rough, "Normal": bump.outputs[0]})
    bsdf.inputs["Specular IOR Level"].default_value = 0.45
    out = g.n("ShaderNodeOutputMaterial")
    g.link(bsdf.outputs[0], out.inputs["Surface"])
    return m


def travertine_material():
    """Gradas: los atributos del suelo vienen de la simulación (dep, flow, depth, lit)."""
    m, g = new_mat("Travertino")
    geo = g.n("ShaderNodeNewGeometry")
    pos = geo.outputs["Position"]
    z = g.n("ShaderNodeSeparateXYZ", Vector=pos).outputs["Z"]
    nz = g.n("ShaderNodeSeparateXYZ", Vector=geo.outputs["Normal"]).outputs["Z"]
    dep = g.n("ShaderNodeAttribute", _attribute_name="dep").outputs["Fac"]
    flow = g.n("ShaderNodeAttribute", _attribute_name="flow").outputs["Fac"]
    depth = g.n("ShaderNodeAttribute", _attribute_name="depth").outputs["Fac"]
    n1 = noise(g, pos, 0.35, 5, 0.6)
    n2 = noise(g, pos, 2.5, 4, 0.6)
    # travertino joven (donde corre el agua) crema; viejo y seco, ocre manchado
    young = _math(g, "MULTIPLY", _math(g, "MULTIPLY", flow, 1.6), 1.0, clamp=True)
    old = ramp(g, n1, [(0.25, (0.24, 0.17, 0.10)), (0.55, (0.36, 0.27, 0.17)), (0.8, (0.30, 0.22, 0.14))])
    fresh = ramp(g, n2, [(0.3, (0.46, 0.40, 0.30)), (0.7, (0.54, 0.47, 0.36))])
    col = mix_col(g, young, old, fresh)
    # roca desnuda donde el travertino apenas tiene espesor
    thin = _math(g, "SUBTRACT", 1.0, _math(g, "DIVIDE", dep, 0.05, clamp=True))
    col = mix_col(g, _math(g, "MULTIPLY", thin, 0.6), col, (0.10, 0.09, 0.08))
    # láminas de crecimiento en las cortinas
    steep = _math(g, "SUBTRACT", 1.0, _math(g, "MULTIPLY", nz, 1.3), clamp=True)
    lam = g.n("ShaderNodeTexWave", Vector=pos, _wave_type="BANDS", _bands_direction="Z", Scale=2.2, Distortion=0.3, **{"Detail": 3.0}).outputs["Fac"]
    # las cortinas: más oscuras y ocres que los labios, sin bandas
    col = mix_col(g, _math(g, "MULTIPLY", steep, 0.35), col, (0.30, 0.22, 0.14))
    # tapetes de algas en el fondo de las pozas: dorados arriba (agua dulce), pardos abajo
    # el labio, donde precipita, queda claro; el fondo de la poza se cubre de biopelícula
    # solo en superficies planas: en las cortinas la interpolación de los atributos dibujaría peines
    flat = _math(g, "MULTIPLY", _math(g, "SUBTRACT", nz, 0.9), 12.0, clamp=True)
    mat_f = _math(g, "MULTIPLY", _math(g, "DIVIDE", depth, 0.03, clamp=True), _math(g, "ADD", 0.55, _math(g, "MULTIPLY", n2, 0.6)))
    mat_f = _math(g, "MULTIPLY", mat_f, flat)
    upper = _math(g, "DIVIDE", _math(g, "ADD", z, 14.0), 12.0, clamp=True)
    algae = mix_col(g, upper, (0.06, 0.05, 0.02), (0.30, 0.17, 0.035))
    algae = mix_col(g, _math(g, "MULTIPLY", n1, 0.6), algae, (0.10, 0.12, 0.03))
    col = mix_col(g, _math(g, "MULTIPLY", mat_f, 0.92), col, algae)
    rim = _math(g, "MULTIPLY", _math(g, "MULTIPLY", flow, 2.5, clamp=True), _math(g, "SUBTRACT", 1.0, _math(g, "DIVIDE", depth, 0.02, clamp=True)))
    col = mix_col(g, _math(g, "MULTIPLY", rim, 0.6), col, (0.80, 0.74, 0.62))
    # mojado: oscurece y abrillanta
    wetf = _math(g, "MAXIMUM", _math(g, "MULTIPLY", flow, 3.0, clamp=True), _math(g, "MULTIPLY", _math(g, "DIVIDE", depth, 0.02, clamp=True), flat))
    col = mix_col(g, _math(g, "MULTIPLY", wetf, 0.45), col, (0.0, 0.0, 0.0))
    rough = _math(g, "SUBTRACT", 0.62, _math(g, "MULTIPLY", wetf, 0.5))
    # microgours: pequeños lóbulos en el fondo de las pozas y crenulación en los labios
    micro = g.n("ShaderNodeTexVoronoi", Vector=pos, Scale=3.5, _feature="SMOOTH_F1").outputs["Distance"]
    h = _math(g, "ADD", _math(g, "MULTIPLY", n2, 0.35), _math(g, "MULTIPLY", lam, _math(g, "MULTIPLY", steep, 0.1)))
    h = _math(g, "ADD", h, _math(g, "MULTIPLY", micro, _math(g, "ADD", 0.15, _math(g, "MULTIPLY", rim, 0.5))))
    bump = g.n("ShaderNodeBump", Strength=0.5, Distance=0.06, Height=h)
    bsdf = g.n("ShaderNodeBsdfPrincipled", **{"Base Color": col, "Roughness": rough, "Normal": bump.outputs[0]})
    bsdf.inputs["Subsurface Weight"].default_value = 0.08
    bsdf.inputs["Subsurface Radius"].default_value = (0.4, 0.3, 0.2)
    out = g.n("ShaderNodeOutputMaterial")
    g.link(bsdf.outputs[0], out.inputs["Surface"])
    return m


def water_material():
    m, g = new_mat("Agua")
    geo = g.n("ShaderNodeNewGeometry")
    pos = geo.outputs["Position"]
    depth = g.n("ShaderNodeAttribute", _attribute_name="depth").outputs["Fac"]
    sea = g.n("ShaderNodeAttribute", _attribute_name="sea").outputs["Fac"]
    # el agua dulce de las pozas apenas tiñe; la del mar es verde y opaca enseguida
    tint_pool = mix_col(g, _math(g, "DIVIDE", depth, 0.8, clamp=True), (0.95, 0.97, 0.95), (0.55, 0.72, 0.62))
    tint = mix_col(g, sea, tint_pool, (0.62, 0.84, 0.92))
    # agua de mar filtrada por la roca: clara cerca, se apaga hacia los 12-14 m (absorción)
    deep = _math(g, "MULTIPLY", sea, _math(g, "POWER", _math(g, "DIVIDE", depth, 14.0, clamp=True), 0.8))
    tint = mix_col(g, deep, tint, (0.05, 0.13, 0.13))
    ripple = noise(g, pos, 1.8, 3, 0.5)
    bump = g.n("ShaderNodeBump", Strength=0.08, Distance=0.02, Height=ripple)
    glass = g.n("ShaderNodeBsdfPrincipled", **{"Base Color": tint, "Roughness": 0.02, "IOR": 1.333, "Transmission Weight": 1.0, "Normal": bump.outputs[0]})
    out = g.n("ShaderNodeOutputMaterial")
    g.link(glass.outputs[0], out.inputs["Surface"])
    return m


def mist_material(density):
    m, g = new_mat("Bruma")
    geo = g.n("ShaderNodeNewGeometry")
    n = noise(g, geo.outputs["Position"], 0.08, 3, 0.5)
    dens = _math(g, "MULTIPLY", _math(g, "ADD", _math(g, "MULTIPLY", n, 1.4), 0.3), density)
    vol = g.n("ShaderNodeVolumePrincipled", Density=dens, Anisotropy=0.35, Color=(0.95, 0.93, 0.90, 1.0))
    out = g.n("ShaderNodeOutputMaterial")
    g.link(vol.outputs[0], out.inputs["Volume"])
    return m


def emission_material(name, color, strength):
    m, g = new_mat(name)
    e = g.n("ShaderNodeEmission", Color=(*color, 1.0), Strength=strength)
    out = g.n("ShaderNodeOutputMaterial")
    g.link(e.outputs[0], out.inputs["Surface"])
    return m
