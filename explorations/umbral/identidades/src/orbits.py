"""Renders orbitales finales (comprobación del mapa sobre el cuerpo)."""
import math
from globe import Peanut, render_peanut, render_sphere, rot_x, rot_y, rot_z

OUT = "../work"
LIGHT = [-0.66, 0.48, 0.58]
PD = dict(sun=[1.0, 0.97, 0.9], ambient=[0.006, 0.01, 0.025], term=[0.06, 0.07, 0.2], term_w=0.09,
          shine=70, spec=0.55, sheen=0.04, fres=0.35, sky=[0.55, 0.75, 0.85], haze=0.3, atmo=[0.35, 0.7, 0.85],
          atmo_rgb=[0.55, 0.85, 1.0], atmo_out=0.8, atmo_th=0.045, wrap=0.1)
PC = dict(sun=[1.0, 0.96, 0.9], ambient=[0.012, 0.016, 0.03], term=[0.06, 0.06, 0.18], term_w=0.09,
          shine=80, spec=0.6, sheen=0.05, fres=0.25, sky=[0.45, 0.6, 0.75], haze=0.25, atmo=[0.45, 0.65, 0.7],
          atmo_rgb=[0.62, 0.82, 0.86], atmo_out=0.7, wrap=0.16)
PM = dict(sun=[1.0, 0.97, 0.92], ambient=[0.006, 0.012, 0.02], term=[0.05, 0.08, 0.18], term_w=0.09,
          shine=120, spec=0.8, sheen=0.06, fres=0.7, fres_pow=2.6, sky=[0.62, 0.86, 0.8], haze=0.12,
          atmo=[0.5, 0.8, 0.75], atmo_rgb=[0.6, 0.9, 0.85], atmo_out=0.35, atmo_th=0.03, wrap=0.08)
MAPS = dict(a=f"{OUT}/cintura_vertiente.png", b=f"{OUT}/cintura_tiza.png",
            a_land=f"{OUT}/cintura_vertiente_land.png", b_land=f"{OUT}/cintura_tiza_land.png")
RC = rot_z(math.radians(22)) @ rot_x(math.radians(18)) @ rot_y(math.radians(-14))

if __name__ == "__main__":
    S = 1400
    # esferas: radio 0.82 del semilado; el binario usa extent 2.2 → misma escala si
    # px/unidad coincide: S/2*0.82 = S/2/extent → extent = 1/0.82
    render_sphere(f"{OUT}/dolinas_albedo.png", S, -45, 18, -14, LIGHT, PD, f"{OUT}/dolinas_land.png").save(f"{OUT}/orbit_dolinas.png")
    render_sphere(f"{OUT}/dosmares_albedo.png", S, -10, 12, 16, LIGHT, PM, f"{OUT}/dosmares_land.png").save(f"{OUT}/orbit_dosmares.png")
    render_peanut(Peanut(), MAPS, S, RC, LIGHT, PC, extent=2.2).save(f"{OUT}/orbit_cintura.png")
    render_peanut(Peanut(), MAPS, S, RC, LIGHT, PC, extent=1 / 0.82).save(f"{OUT}/orbit_cintura_samescale.png")
