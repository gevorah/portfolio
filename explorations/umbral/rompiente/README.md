# Umbral · La Rompiente (rondas 5 y 6)

Dirección de arte de planeta y entorno para **La Rompiente**, el alero costero
de la isla principal de Umbral. Para evaluación: la dirección no está aprobada.

Página de presentación: `page/index.html` (publicada como artifact privado).

## Entregables

| | Archivo | Qué es |
|---|---|---|
| I | `img/i-orbita.png`, `img/i-orbita-escala.png` | Vista orbital y prueba de lectura a 160, 64 y 28 px |
| II | `img/ii-pleamar.png` | La Rompiente en pleamar (nivel 0 m) |
| III | `img/iii-bajamar.png` | La misma cámara en bajamar (nivel −24 m) |
| IV | `img/iv-continuidad.png` | Planta con las costas de pleamar y bajamar |
| V | `page/index.html` | Crítica artística breve |

## Cómo se construye

Un único modelo para todo el lugar, para que pleamar y bajamar sean de verdad
el mismo sitio:

- `src/shader/rompiente.frag`: el lugar entero como campo de distancias (isla,
  alero, rasa mareal, canal, cueva, farallones, barra, isleta, archipiélago),
  con iluminación estilizada. El uniforme `L` es el nivel del mar.
  Modos de depuración: `DBG=-2` mide la altura en planta (1 px = 1 m),
  `DBG=-1` dibuja la planta con la cámara, `DBG>1.5` corta una sección en z.
- `src/shader/run.mjs`: renderiza el shader en Chromium sin ventana (SwiftShader).
- `src/shader/go.sh`: vista previa de ambas mareas con la misma cámara.
- `src/post.py`: reduce el render supermuestreado, aplica un filtro de
  Kuwahara suave y añade aves y, en bajamar, la figura con farol.
- `src/continuity.py`: construye el esquema IV a partir de la altura medida.
- `src/orbit.py` + `src/globe.py`: mapa equirectangular hecho con la misma
  planta y su proyección sobre la esfera.

Reproducir las vistas finales (cámara `(-200, 7, 220)` → `(10, 30, 430)`, FOV 52°):

```sh
cd src/shader
node run.mjs rompiente.frag ../../work/hi_big.png 2400 1500 '{"L":0,"CAM":[-200,7,220],"TGT":[10,30,430],"FOV":52}'
node run.mjs rompiente.frag ../../work/lo_big.png 2400 1500 '{"L":-24,"CAM":[-200,7,220],"TGT":[10,30,430],"FOV":52}'
node run.mjs rompiente.frag ../../work/height.png 900 900 '{"DBG":-2}'
cd ..
python3 post.py ../work/hi_big.png ../work/height.png 0 ../img/ii-pleamar.png
python3 post.py ../work/lo_big.png ../work/height.png -24 ../img/iii-bajamar.png
python3 continuity.py ../work/height.png
python3 orbit.py
```

(`PW_PATH` debe apuntar a la instalación de Playwright; por defecto
`/opt/node-tools/node_modules/playwright`.)

## Ronda 6 · refinamiento y La Cala Interior

Página: `ronda6/index.html` (artifact privado aparte, para poder comparar con la ronda 5).

| | Archivo | Qué es |
|---|---|---|
| I | `img/r6-orbita.png`, `img/r6-orbita-escala.png` | Vista orbital refinada (batimetría, canales de marea, relieve) |
| II | `img/r6-pleamar.png`, `img/r6-bajamar.png` | La Rompiente con la nueva geología, misma cámara |
| III | `img/r6-cala.png`, `img/cala-corte.png` | La Cala Interior: vista principal y corte de continuidad |
| IV | `img/r6-seq-1.png` … `img/r6-seq-6.png` | Secuencia de descubrimiento |
| V | `ronda6/index.html` | Prototipo interactivo de las Gradas en planta (canvas) |

Novedades en el código:

- `src/shader/common.glsl`: ruido y la **columna estratigráfica** por paquetes
  (61 bancos, búsqueda binaria) que comparten La Rompiente y la Cala.
  `run.mjs` resuelve `#include "archivo"`.
- `src/shader/rompiente.frag`: techo del alero en losas escalonadas con
  cicatrices de caída, farallones como prismas de diaclasas (arco, farallón,
  tocón), rasa calmada, luz cálida al fondo del túnel y la dolina del jameo.
- `src/shader/cala.frag`: La Cala Interior en las mismas coordenadas. Uniformes
  de la interacción: `L` (marea en la sala), `PULSE` (fila de origen, frente,
  rama, intensidad), `STONE` (piedra en el rebosadero norte) y `FED`
  (farolillos alimentados). `DBG ≥ 100` corta la sala a z = DBG; `DBG = 3`
  devuelve la posición de cada píxel.
- `src/cala_section.py`: corte de continuidad a partir de los cortes de ambos
  volúmenes. `src/post_cala.py` y `src/paintfx.py`: acabado pictórico y figura.

Cámaras de la Cala: vista principal `(104, 1, 386) → (78, −10, 430)`, FOV 74°;
secuencia `(60, 0, 396) → (98, −12, 434)`, FOV 72°. Los parámetros de cada
fotograma están en `src/shader/cala_frames.sh`.
