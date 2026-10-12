#!/bin/bash
# Renderiza la vista principal de La Cala Interior y los seis fotogramas de la secuencia.
# Uniformes: L marea en la sala · PULSE (fila de origen, frente en filas, rama, intensidad) · STONE · FED
cd "$(dirname "$0")"
export PW_PATH=${PW_PATH:-/opt/node-tools/node_modules/playwright}
W=../../work; mkdir -p $W
C='"CAM":[56,8,382],"TGT":[96,-16,428],"FOV":74'
r(){ node run.mjs cala.frag $W/$1.png $3 "$2" 2>&1 | grep -a "rendered\|rror"; }
r cala_hero_big '{"L":-24,"CAM":[104,1,386],"TGT":[78,-10,430],"FOV":74,"STONE":0,"PULSE":[0,0,0,0],"FED":0}' "2400 1500"
r seq1 "{\"L\":-24,$C,\"STONE\":0,\"PULSE\":[0,0,0,0],\"FED\":0}" "1440 900" & r seq2 "{\"L\":-24,$C,\"STONE\":0,\"PULSE\":[-1,0,1,1],\"FED\":0}" "1440 900"; wait
r seq3 "{\"L\":-24,$C,\"STONE\":0,\"PULSE\":[3,5,1,1],\"FED\":1}" "1440 900" & r seq4 "{\"L\":-24,$C,\"STONE\":0,\"PULSE\":[7,8,1,1],\"FED\":1}" "1440 900"; wait
r seq5 "{\"L\":-24,$C,\"STONE\":1,\"PULSE\":[3,5,0,1],\"FED\":1}" "1440 900" & r seq6 "{\"L\":-12,$C,\"STONE\":0,\"PULSE\":[6,8,1,1],\"FED\":1}" "1440 900"; wait
