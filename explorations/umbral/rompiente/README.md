# Umbral · La Rompiente (ronda 5)

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
