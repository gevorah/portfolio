#!/bin/bash
# Vista previa de ambas mareas con la misma cámara.
# uso: go.sh W H "CAMx,y,z" "TGTx,y,z" FOV   → work/hi.png, work/lo.png, work/pair.png
OUT="$(cd "$(dirname "$0")/../.." && pwd)/work"
mkdir -p "$OUT"
export PW_PATH=${PW_PATH:-/opt/node-tools/node_modules/playwright}
cd "$(dirname "$0")"
node run.mjs rompiente.frag "$OUT/hi.png" $1 $2 "{\"L\":0,\"CAM\":[$3],\"TGT\":[$4],\"FOV\":$5}" 2>&1 | grep -a rendered &
node run.mjs rompiente.frag "$OUT/lo.png" $1 $2 "{\"L\":-24,\"CAM\":[$3],\"TGT\":[$4],\"FOV\":$5}" 2>&1 | grep -a rendered &
wait
python3 -c "
from PIL import Image
a=Image.open('$OUT/hi.png');b=Image.open('$OUT/lo.png');c=Image.new('RGB',(a.width,a.height*2));c.paste(a,(0,0));c.paste(b,(0,a.height));c.save('$OUT/pair.png')"
