# Umbral · La Cala Interior en Blender (prueba de producción 1)

Un único espacio, La Cala Interior y su conexión con La Rompiente, construido en
Blender 5.2 y renderizado con Cycles para medir cuánto puede subir la calidad
ambiental. Para evaluación: no aprobado.

Página: `page/index.html` (artifact privado). Renders en `img/`.

## Qué se conserva de la ronda 6

La planta, las cotas y las relaciones: el tubo desde la Bóveda (bajo el alero),
la poza madre a nivel de bajamar (−24 m), las gradas que suben hacia el
nordeste hasta el manantial (+3 m), el jameo sobre la entrada. Coordenadas de
Blender en metros con origen en la poza madre (= B de `cala.frag`).

## Cómo se construye

| Paso | Archivo | Qué hace |
|---|---|---|
| 1 | `src/gours.py` | Suelo heredado (frentes lobulados de coladas) y simulación de gours: llenado de depresiones, flujo MFD y precipitación en los labios. Salida en `work/gours_*.npy`. |
| 2 | `src/shell.py` | La roca como campo de aire → marching cubes: tubo de lava con anillos de nivel, sala de derrumbe con techo en cicatrices de bloques, jameo de dos lóbulos con columnas de basalto, repisa de lava a +2 m. |
| 3 | `src/build.py` | Monta la escena en Blender: roca, gradas (12,5 cm), agua, cono de derrumbe (`rocks.py`), vida (`life.py`), materiales (`mats.py`), sol, bruma, cámaras. |
| — | `src/geo.py` | Geología compartida: columna estratigráfica leída de `rompiente/src/shader/common.glsl`, ruido y columnas. |
| — | `src/process_fig.py` | Lámina de proceso (antes y después de la simulación). |

```sh
# Blender como módulo: pip install bpy (5.2, Python 3.13) + numpy scipy scikit-image numba
python src/gours.py 1200
python src/shell.py 0.7
python src/build.py final low  A img/bajamar-A.png 1600 1000 128   # [clay|final] [low|high] [A|B]
python src/build.py final high B img/pleamar-B.png 1600 1000 128
```

`build.py` guarda también `work/cala_final.blend` (unos 45 MB), que se puede
abrir en Blender para seguir trabajando a mano. Está en `work/` (no versionado)
porque se regenera con los scripts.

## Límites del entorno

Contenedor sin GPU (Cycles por CPU, ~20 min por imagen a 1600×1000 y 128
muestras). La red bloquea Poly Haven, ambientCG y blender.org, así que todos
los materiales son procedurales.
